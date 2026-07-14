"""Stage "analyze": tempo/beatgrid, key, and per-stem loudness/spectral stats.

Reads stems/{drums,bass,other,vocals}.wav (written by the "separate" stage)
and writes analysis.json = {"tempo": {...}, "key": {...}, "stems": {...}}.
"""

from __future__ import annotations

import json

import librosa
import numpy as np

from .ctx import STEMS, Ctx

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Krumhansl-Kessler key profiles, index 0 = C.
MAJOR_PROFILE = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
MINOR_PROFILE = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]

_TAG_ADJECTIVES = {
    "bright": ("bright", "crisp"),
    "warm/dark": ("warm", "moody"),
    "sub-heavy": ("sub-heavy", "deep"),
    "punchy": ("punchy", "snappy"),
    "noisy/textured": ("gritty", "textured"),
}

_STEM_NOUNS = {
    "drums": ("drum loop", "drum break"),
    "bass": ("bass loop", "bass one shot"),
    "other": ("synth loop", "melodic loop"),
    "vocals": ("vocal loop", "vocal chop"),
}


def spectral_tags(centroid_hz: float, lowband_ratio: float, attack_time: float, crest_factor: float, flatness: float) -> list[str]:
    tags = []
    if centroid_hz > 4000:
        tags.append("bright")
    if centroid_hz < 1000:
        tags.append("warm/dark")
    if lowband_ratio > 0.5:
        tags.append("sub-heavy")
    if attack_time < 0.02 and crest_factor > 4:
        tags.append("punchy")
    if flatness > 0.3:
        tags.append("noisy/textured")
    return tags


def _stem_query_hints(stem: str, tags: list[str]) -> list[str]:
    primary_adjs = [_TAG_ADJECTIVES[t][0] for t in tags if t in _TAG_ADJECTIVES]
    secondary_adjs = [_TAG_ADJECTIVES[t][1] for t in tags if t in _TAG_ADJECTIVES]
    nouns = _STEM_NOUNS[stem]

    lead = " ".join(primary_adjs[:2])
    first = f"{lead} {nouns[0]}".strip()

    alt_adj = secondary_adjs[0] if secondary_adjs else (primary_adjs[0] if primary_adjs else "")
    second = f"{alt_adj} {nouns[1]}".strip()

    hints = []
    for hint in (first, second):
        hint = " ".join(hint.split())
        if hint not in hints:
            hints.append(hint)
    return hints


def _analyze_tempo(ctx: Ctx) -> dict:
    y, sr = librosa.load(str(ctx.stem_path("drums")), sr=None, mono=True)
    tempo_arr, beat_frames = librosa.beat.beat_track(y=y, sr=sr, units="frames")
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)

    if len(beat_times) < 2:
        tempo_val = np.asarray(tempo_arr)
        bpm = float(tempo_val) if tempo_val.size == 1 else 120.0
        # librosa can return 0 BPM on a near-silent/beatless drums stem; floor to a
        # sane fallback so downstream stages never divide by zero (drums bar math)
        # or collapse all note timing to beat 0 (transcribe seconds_to_beats).
        if not bpm > 0:
            bpm = 120.0
        return {
            "bpm": bpm,
            "confidence": 0.0,
            "candidates": [],
            "grid_offset_sec": 0.0,
            "beat_count": len(beat_times),
            "tempo_stability": 0.0,
            "assumed_meter": "4/4",
        }

    intervals = np.diff(beat_times)
    median_interval = float(np.median(intervals))
    bpm = 60.0 / median_interval if median_interval > 0 else 120.0
    grid_offset_sec = float(beat_times[0])
    beat_count = len(beat_times)

    iqr = float(np.percentile(intervals, 75) - np.percentile(intervals, 25))
    tempo_stability = float(np.clip(1 - iqr / median_interval, 0.0, 1.0)) if median_interval > 0 else 0.0

    candidates = [{"bpm": bpm, "relation": "primary"}]
    for rel, mult in [("half", 0.5), ("double", 2.0)]:
        cand_bpm = bpm * mult
        if 60.0 <= cand_bpm <= 190.0:
            candidates.append({"bpm": cand_bpm, "relation": rel})

    return {
        "bpm": bpm,
        "confidence": tempo_stability,
        "candidates": candidates,
        "grid_offset_sec": grid_offset_sec,
        "beat_count": beat_count,
        "tempo_stability": tempo_stability,
        "assumed_meter": "4/4",
    }


def _load_key_mix(ctx: Ctx) -> tuple[np.ndarray, int]:
    y_bass, sr_bass = librosa.load(str(ctx.stem_path("bass")), sr=None, mono=True)
    y_other, sr_other = librosa.load(str(ctx.stem_path("other")), sr=None, mono=True)

    sr = sr_bass
    if sr_other != sr_bass:
        y_other = librosa.resample(y_other, orig_sr=sr_other, target_sr=sr)

    n = max(len(y_bass), len(y_other))
    y_bass = np.pad(y_bass, (0, n - len(y_bass)))
    y_other = np.pad(y_other, (0, n - len(y_other)))
    return y_bass + y_other, sr


def _analyze_key(ctx: Ctx) -> dict:
    mix, sr = _load_key_mix(ctx)

    chroma = librosa.feature.chroma_cqt(y=mix, sr=sr)
    profile = chroma.mean(axis=1)
    total = float(profile.sum())
    profile = profile / total if total > 0 else profile

    scores: dict[tuple[int, str], float] = {}
    for root in range(12):
        for mode, template in (("major", MAJOR_PROFILE), ("minor", MINOR_PROFILE)):
            rotated = np.roll(np.asarray(template, dtype=np.float64), root)
            corr = np.corrcoef(profile, rotated)[0, 1]
            scores[(root, mode)] = 0.0 if np.isnan(corr) else float(corr)

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    (tonic_idx, mode), best_score = ranked[0]
    second_score = ranked[1][1] if len(ranked) > 1 else 0.0
    confidence = (best_score - second_score) / best_score if best_score > 0 else 0.0

    tonic = NOTE_NAMES[tonic_idx]
    name = f"{tonic} {mode}"

    if mode == "minor":
        relative_idx, relative_mode = (tonic_idx + 3) % 12, "major"
    else:
        relative_idx, relative_mode = (tonic_idx - 3) % 12, "minor"
    relative_name = f"{NOTE_NAMES[relative_idx]} {relative_mode}"
    relative_score = scores[(relative_idx, relative_mode)]

    parallel_mode = "minor" if mode == "major" else "major"
    parallel_name = f"{NOTE_NAMES[tonic_idx]} {parallel_mode}"
    parallel_score = scores[(tonic_idx, parallel_mode)]

    return {
        "tonic": tonic,
        "mode": mode,
        "name": name,
        "confidence": confidence,
        "alternates": [
            {"name": relative_name, "relation": "relative", "score": relative_score},
            {"name": parallel_name, "relation": "parallel", "score": parallel_score},
        ],
        "chroma_profile": [float(x) for x in profile],
    }


def _activity_ratio(y: np.ndarray, sr: int) -> float:
    hop = int(0.1 * sr)
    if hop <= 0 or len(y) == 0:
        return 0.0
    frame_rms = librosa.feature.rms(y=y, frame_length=hop, hop_length=hop)[0]
    if len(frame_rms) == 0:
        return 0.0
    frame_db = 20 * np.log10(frame_rms + 1e-9)
    return float(np.mean(frame_db > -45))


def _attack_time(y: np.ndarray, sr: int) -> float:
    if len(y) == 0:
        return 0.05
    onset_samples = librosa.onset.onset_detect(y=y, sr=sr, units="samples")
    if len(onset_samples) == 0:
        return 0.05
    onset_idx = int(onset_samples[0])
    window_end = min(onset_idx + int(0.05 * sr), len(y))
    segment = np.abs(y[onset_idx:window_end])
    if len(segment) == 0:
        return 0.05
    peak_idx = int(np.argmax(segment))
    return float(peak_idx / sr)


def _spectral_stats(y: np.ndarray, sr: int) -> dict:
    centroid_hz = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))) if len(y) else 0.0
    rolloff_hz = float(np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr, roll_percent=0.85))) if len(y) else 0.0
    flatness = float(np.mean(librosa.feature.spectral_flatness(y=y))) if len(y) else 0.0

    if len(y) == 0:
        lowband_ratio = 0.0
    else:
        magnitude = np.abs(np.fft.rfft(y))
        freqs = np.fft.rfftfreq(len(y), d=1.0 / sr)
        energy = magnitude**2
        total_energy = float(np.sum(energy))
        lowband_energy = float(np.sum(energy[freqs < 120.0]))
        lowband_ratio = lowband_energy / total_energy if total_energy > 0 else 0.0

    return {
        "centroid_hz": centroid_hz,
        "rolloff_hz": rolloff_hz,
        "flatness": flatness,
        "lowband_ratio": lowband_ratio,
    }


def _stem_stats(ctx: Ctx, stem: str) -> dict:
    path = ctx.stem_path(stem)
    y, sr = librosa.load(str(path), sr=None, mono=True)

    rms = librosa.feature.rms(y=y)[0]
    mean_rms = float(np.mean(rms)) if len(rms) else 0.0
    rms_db = float(20 * np.log10(mean_rms + 1e-9))

    peak = float(np.max(np.abs(y))) if len(y) else 0.0
    peak_db = float(20 * np.log10(peak + 1e-9))

    activity_ratio = _activity_ratio(y, sr)
    silent = activity_ratio < 0.02 or rms_db < -50

    spectral = _spectral_stats(y, sr)
    attack_time = _attack_time(y, sr)
    crest_factor = peak / (mean_rms + 1e-9)

    tags = spectral_tags(
        spectral["centroid_hz"], spectral["lowband_ratio"], attack_time, crest_factor, spectral["flatness"]
    )
    hints = _stem_query_hints(stem, tags)

    return {
        "path": path.relative_to(ctx.outdir).as_posix(),
        "rms_db": rms_db,
        "peak_db": peak_db,
        "activity_ratio": activity_ratio,
        "silent": silent,
        "spectral": spectral,
        "tags": tags,
        "splice_query_hints": hints,
    }


def run(ctx: Ctx) -> None:
    ctx.ensure_dirs()

    missing = [s for s in STEMS if not ctx.stem_path(s).exists()]
    if missing:
        raise RuntimeError(
            f"analyze: missing stem file(s) {[ctx.stem_path(s).name for s in missing]} in {ctx.stems_dir} "
            "-- run the 'separate' stage first"
        )

    try:
        tempo = _analyze_tempo(ctx)
        key = _analyze_key(ctx)
        stems = {stem: _stem_stats(ctx, stem) for stem in STEMS}
    except Exception as e:
        raise RuntimeError(f"analyze: failed to analyze {ctx.outdir}: {e}") from e

    analysis = {"tempo": tempo, "key": key, "stems": stems}
    ctx.analysis_json.write_text(json.dumps(analysis, indent=2))
