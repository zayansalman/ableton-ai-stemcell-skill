"""Slice the drum stem into one-shots, dedupe/classify them, and export bar-aligned loops."""

from __future__ import annotations

import json

import librosa
import numpy as np
import soundfile as sf

from .ctx import CLAP_CHARACTER_HINTS, CLAP_DRUM_LABELS, Ctx

SILENCE_THRESH_LINEAR = 10 ** (-60 / 20)
MIN_SLICE_SEC = 0.03
FADE_OUT_SEC = 0.005
CLUSTER_SIM_THRESHOLD = 0.92
CLAP_SAMPLE_RATE = 48000


def _spectral_descriptors(y: np.ndarray, sr: int) -> dict:
    centroid = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
    rolloff = float(np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr)))
    flatness = float(np.mean(librosa.feature.spectral_flatness(y=y)))

    spec = np.abs(np.fft.rfft(y))
    freqs = np.fft.rfftfreq(len(y), d=1.0 / sr)
    total_energy = float(np.sum(spec**2)) + 1e-12
    lowband_energy = float(np.sum(spec[freqs < 120] ** 2))
    lowband_ratio = lowband_energy / total_energy

    return {
        "centroid_hz": centroid,
        "rolloff_hz": rolloff,
        "flatness": flatness,
        "lowband_ratio": lowband_ratio,
    }


def _attack_time_sec(y: np.ndarray, sr: int) -> float:
    if len(y) == 0:
        return 0.0
    abs_y = np.abs(y)
    peak_idx = int(np.argmax(abs_y))
    peak_val = abs_y[peak_idx]
    if peak_val <= 0:
        return 0.0
    threshold = 0.9 * peak_val
    above = np.where(abs_y[: peak_idx + 1] >= threshold)[0]
    attack_samples = above[0] if len(above) else peak_idx
    return float(attack_samples) / sr


def _crest_factor(y: np.ndarray) -> float:
    if len(y) == 0:
        return 0.0
    peak_linear = float(np.max(np.abs(y)))
    rms_linear = float(np.sqrt(np.mean(y.astype(np.float64) ** 2))) + 1e-12
    return peak_linear / rms_linear


def _spectral_tags(spectral: dict, y: np.ndarray, sr: int) -> list[str]:
    tags = []
    if spectral["centroid_hz"] > 4000:
        tags.append("bright")
    if spectral["centroid_hz"] < 1000:
        tags.append("warm/dark")
    if spectral["lowband_ratio"] > 0.5:
        tags.append("sub-heavy")
    if _attack_time_sec(y, sr) < 0.02 and _crest_factor(y) > 4:
        tags.append("punchy")
    if spectral["flatness"] > 0.3:
        tags.append("noisy/textured")
    return tags


def _splice_query_hints(label: str, tags: list[str]) -> list[str]:
    base = label.replace("_", " ")
    hints = [f"{' '.join(tags[:2])} {base}".strip() if tags else base]
    hints.append(f"{base} one shot")
    if tags:
        hints.append(f"{tags[0]} {base} sample")
    return hints[:3]


def _peak_db(y: np.ndarray) -> float:
    peak = float(np.max(np.abs(y))) if len(y) else 0.0
    return float(20 * np.log10(peak + 1e-9))


def _trim_and_fade(y: np.ndarray, sr: int) -> np.ndarray:
    end = len(y)
    while end > 0 and abs(y[end - 1]) < SILENCE_THRESH_LINEAR:
        end -= 1
    end = min(len(y), end + int(0.002 * sr))
    y = y[:end]

    fade_len = min(len(y), int(FADE_OUT_SEC * sr))
    if fade_len > 0:
        fade_curve = np.linspace(1.0, 0.0, fade_len, dtype=y.dtype)
        y = y.copy()
        y[-fade_len:] *= fade_curve
    return y


def _mfcc_feature(y: np.ndarray, sr: int) -> np.ndarray:
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=20)
    return np.concatenate([mfcc.mean(axis=1), mfcc.std(axis=1)])


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-12
    return float(np.dot(a, b) / denom)


def _classify_exemplar(y: np.ndarray, sr: int, ctx: Ctx) -> tuple[str, float, list[dict], list[dict]]:
    if ctx.skip_clap:
        return "perc", 0.0, [], []

    from transformers import pipeline as hf_pipeline

    try:
        clf = hf_pipeline(
            "zero-shot-audio-classification",
            model="laion/clap-htsat-unfused",
            local_files_only=True,
        )
    except Exception as e:
        raise RuntimeError("CLAP model not cached -- run: stemcell bootstrap") from e

    y_48k = librosa.resample(y.astype(np.float32), orig_sr=sr, target_sr=CLAP_SAMPLE_RATE)

    reverse_lookup = {v: k for k, v in CLAP_DRUM_LABELS.items()}
    candidate_labels = list(CLAP_DRUM_LABELS.values())
    drum_results = clf(y_48k, candidate_labels=candidate_labels)
    drum_results = sorted(drum_results, key=lambda r: r["score"], reverse=True)

    label = reverse_lookup[drum_results[0]["label"]]
    clap_confidence = float(drum_results[0]["score"])
    alt_labels = [
        {"label": reverse_lookup[r["label"]], "confidence": float(r["score"])}
        for r in drum_results[1:3]
    ]

    character_results = clf(y_48k, candidate_labels=list(CLAP_CHARACTER_HINTS))
    character_results = sorted(character_results, key=lambda r: r["score"], reverse=True)
    character_hints = [
        {"label": r["label"], "confidence": float(r["score"])} for r in character_results[:2]
    ]

    return label, clap_confidence, alt_labels, character_hints


def _extract_oneshots(y: np.ndarray, sr: int, onset_samples: np.ndarray) -> tuple[int, list[dict]]:
    onset_count = len(onset_samples)

    min_samples = int(MIN_SLICE_SEC * sr)
    max_len_samples = int(1.5 * sr)

    slices = []
    for i, onset in enumerate(onset_samples):
        next_boundary = onset_samples[i + 1] if i + 1 < len(onset_samples) else len(y)
        slice_end = min(next_boundary, onset + max_len_samples, len(y))
        raw_slice = y[onset:slice_end]
        trimmed = _trim_and_fade(raw_slice, sr)
        if len(trimmed) < min_samples:
            continue
        slices.append({"onset_sample": int(onset), "audio": trimmed})

    return onset_count, slices


def _dedupe_cluster(slices: list[dict], sr: int) -> list[dict]:
    clusters: list[dict] = []
    for s in slices:
        feature = _mfcc_feature(s["audio"], sr)
        peak = float(np.max(np.abs(s["audio"]))) if len(s["audio"]) else 0.0

        best_idx = -1
        best_sim = -1.0
        for idx, c in enumerate(clusters):
            sim = _cosine_similarity(feature, c["feature"])
            if sim > best_sim:
                best_sim = sim
                best_idx = idx

        if best_idx >= 0 and best_sim > CLUSTER_SIM_THRESHOLD:
            c = clusters[best_idx]
            c["count"] += 1
            if peak > c["peak"]:
                c["feature"] = feature
                c["peak"] = peak
                c["exemplar"] = s
        else:
            clusters.append(
                {"feature": feature, "peak": peak, "exemplar": s, "count": 1}
            )

    return clusters


def _extract_loops(y: np.ndarray, sr: int, ctx: Ctx, onset_samples: np.ndarray) -> list[dict]:
    tempo = ctx.analysis["tempo"]
    bpm = tempo["bpm"]
    grid_offset = tempo["grid_offset_sec"]
    bar_sec = 4 * 60.0 / bpm

    duration_sec = len(y) / sr

    bar_starts = []
    n = 0
    while True:
        start = grid_offset + n * bar_sec
        if start >= duration_sec:
            break
        bar_starts.append(start)
        n += 1

    num_bars = len(bar_starts)
    if num_bars == 0:
        return []

    bar_rms = []
    for start in bar_starts:
        end = min(start + bar_sec, duration_sec)
        start_sample = int(start * sr)
        end_sample = int(end * sr)
        window = y[start_sample:end_sample]
        rms = float(np.sqrt(np.mean(window.astype(np.float64) ** 2))) if len(window) else 0.0
        bar_rms.append(rms)

    onset_times = onset_samples / sr

    loops = []

    loudest_bar_idx = int(np.argmax(bar_rms))
    loops.append(_make_loop(y, sr, ctx, bar_starts, loudest_bar_idx, num_bars=1, bar_sec=bar_sec, duration_sec=duration_sec))

    if num_bars >= 8:
        best_idx = -1
        best_density = -1.0
        for i in range(num_bars):
            lo = max(0, i - 4)
            hi = min(num_bars, i + 4)
            window_start = bar_starts[lo]
            window_end = bar_starts[hi] if hi < num_bars else duration_sec
            density = float(np.sum((onset_times >= window_start) & (onset_times < window_end)))
            if density > best_density:
                best_density = density
                best_idx = i
        if best_idx >= 0:
            loops.append(
                _make_loop(y, sr, ctx, bar_starts, best_idx, num_bars=2, bar_sec=bar_sec, duration_sec=duration_sec)
            )

    return loops


def _make_loop(y, sr, ctx: Ctx, bar_starts: list[float], start_idx: int, num_bars: int, bar_sec: float, duration_sec: float) -> dict:
    start_sec = bar_starts[start_idx]
    end_sec = min(start_sec + num_bars * bar_sec, duration_sec)
    start_sample = int(start_sec * sr)
    end_sample = int(end_sec * sr)
    window = y[start_sample:end_sample]

    start_bar = start_idx + 1
    end_bar = start_bar + num_bars - 1
    filename = f"drums_bars_{start_bar:03d}-{end_bar:03d}.wav"
    out_path = ctx.loops_dir / filename
    sf.write(str(out_path), window, sr)

    rms = float(np.sqrt(np.mean(window.astype(np.float64) ** 2))) if len(window) else 0.0
    rms_db = 20 * np.log10(rms + 1e-9)

    return {
        "file": out_path.relative_to(ctx.outdir).as_posix(),
        "start_bar": start_bar,
        "num_bars": num_bars,
        "start_sec": float(start_sec),
        "duration_sec": float(end_sec - start_sec),
        "rms_db": float(rms_db),
    }


def run(ctx: Ctx) -> None:
    if not ctx.analysis_json.exists():
        raise RuntimeError(
            f"drums stage requires analysis.json (run the 'analyze' stage first): {ctx.analysis_json}"
        )
    ctx.ensure_dirs()

    y, sr = librosa.load(str(ctx.stem_path("drums")), sr=None, mono=True)
    onset_samples = librosa.onset.onset_detect(y=y, sr=sr, backtrack=True, units="samples")

    onset_count, slices = _extract_oneshots(y, sr, onset_samples)
    clusters = _dedupe_cluster(slices, sr)
    unique_hits = len(clusters)

    labeled_clusters = []
    for c in clusters:
        exemplar_audio = c["exemplar"]["audio"]
        label, clap_confidence, alt_labels, character_hints = _classify_exemplar(exemplar_audio, sr, ctx)
        labeled_clusters.append(
            {
                "label": label,
                "clap_confidence": clap_confidence,
                "alt_labels": alt_labels,
                "character_hints": character_hints,
                "peak": c["peak"],
                "count": c["count"],
                "exemplar": c["exemplar"],
            }
        )

    by_label: dict[str, list[dict]] = {}
    for lc in labeled_clusters:
        by_label.setdefault(lc["label"], []).append(lc)

    oneshots = []
    for label, items in by_label.items():
        items_sorted = sorted(items, key=lambda lc: lc["peak"], reverse=True)
        for idx, lc in enumerate(items_sorted, start=1):
            audio = lc["exemplar"]["audio"]
            filename = f"{label}_{idx:02d}.wav"
            out_path = ctx.oneshots_dir / filename
            sf.write(str(out_path), audio, sr)

            spectral = _spectral_descriptors(audio, sr)
            tags = _spectral_tags(spectral, audio, sr)
            splice_query_hints = _splice_query_hints(label, tags)

            oneshots.append(
                {
                    "file": out_path.relative_to(ctx.outdir).as_posix(),
                    "label": label,
                    "clap_confidence": lc["clap_confidence"],
                    "alt_labels": lc["alt_labels"],
                    "character_hints": lc["character_hints"],
                    "source_time_sec": float(lc["exemplar"]["onset_sample"]) / sr,
                    "duration_sec": len(audio) / sr,
                    "count_in_song": lc["count"],
                    "peak_db": _peak_db(audio),
                    "spectral": spectral,
                    "tags": tags,
                    "splice_query_hints": splice_query_hints,
                }
            )

    loops = _extract_loops(y, sr, ctx, onset_samples)

    drums_data = {
        "onset_count": onset_count,
        "unique_hits": unique_hits,
        "oneshots": oneshots,
        "loops": loops,
    }

    ctx.drums_json.write_text(json.dumps(drums_data, indent=2))
