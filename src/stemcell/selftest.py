"""Offline synthetic self-check: no copyrighted audio, no model downloads.

Generates a synthetic click track (drums) + sine arpeggio (bass) at a known
tempo/key, writes them directly as ``stems/drums.wav`` / ``stems/bass.wav``
(bypassing demucs entirely — we already know the ground-truth separation for
synthetic audio), then runs the ``analyze`` and ``drums`` stages for real and
asserts the measured tempo/key/onset-count match what we synthesized.
"""

from __future__ import annotations

import importlib
import shutil
from pathlib import Path

import numpy as np
import soundfile as sf

from .ctx import SAMPLE_RATE, Ctx

TEMPO_BPM = 120.0
DURATION_SEC = 30.0
BEAT_SEC = 60.0 / TEMPO_BPM
N_BEATS = int(DURATION_SEC / BEAT_SEC)  # 60 beats over 30s at 120 BPM

# A minor triad register notes for the arpeggio (A2, C3, E3)
ARPEGGIO_HZ = [110.00, 130.81, 164.81]


def _click_burst(rng: np.random.Generator, n: int, kind: str) -> np.ndarray:
    """~80ms exponential-decay noise burst; 'kick' is low-passed & louder, 'snare' is broadband & softer."""
    t = np.arange(n) / SAMPLE_RATE
    decay = np.exp(-t / 0.02)
    noise = rng.standard_normal(n)
    if kind == "kick":
        # crude low-pass: 4-sample moving average, applied twice
        k = np.ones(4) / 4
        noise = np.convolve(np.convolve(noise, k, mode="same"), k, mode="same")
        amp = 0.9
    else:
        amp = 0.45
    return (amp * decay * noise).astype(np.float32)


def _drum_track(rng: np.random.Generator) -> np.ndarray:
    n_samples = int(DURATION_SEC * SAMPLE_RATE)
    sig = np.zeros(n_samples, dtype=np.float32)
    burst_len = int(0.08 * SAMPLE_RATE)
    for i in range(N_BEATS):
        start = int(i * BEAT_SEC * SAMPLE_RATE)
        end = min(start + burst_len, n_samples)
        kind = "kick" if i % 2 == 0 else "snare"
        burst = _click_burst(rng, end - start, kind)
        sig[start:end] += burst
    return sig


def _arpeggio_track() -> np.ndarray:
    n_samples = int(DURATION_SEC * SAMPLE_RATE)
    sig = np.zeros(n_samples, dtype=np.float32)
    note_len = int(BEAT_SEC * SAMPLE_RATE)
    t_note = np.arange(note_len) / SAMPLE_RATE
    # short attack, gentle decay so notes read as discrete events, not a drone
    envelope = np.minimum(t_note / 0.005, 1.0) * np.exp(-t_note / (BEAT_SEC * 0.6))
    for i in range(N_BEATS):
        start = i * note_len
        end = min(start + note_len, n_samples)
        freq = ARPEGGIO_HZ[i % len(ARPEGGIO_HZ)]
        tone = np.sin(2 * np.pi * freq * t_note[: end - start])
        sig[start:end] += 0.5 * envelope[: end - start] * tone
    return sig


def _write_stereo(path: Path, mono: np.ndarray) -> None:
    stereo = np.stack([mono, mono], axis=1)
    sf.write(str(path), stereo, SAMPLE_RATE, subtype="PCM_16")


def run_selftest(outdir: Path) -> bool:
    print(f"selftest output dir: {outdir}")
    if outdir.exists():
        shutil.rmtree(outdir)

    rng = np.random.default_rng(seed=42)
    drums = _drum_track(rng)
    arpeggio = _arpeggio_track()
    mix = np.clip(drums + arpeggio, -1.0, 1.0)

    ctx = Ctx(audio_in=outdir / "input.wav", outdir=outdir, skip_clap=True)
    ctx.ensure_dirs()

    _write_stereo(ctx.input_wav, mix)
    _write_stereo(ctx.stem_path("drums"), drums)
    _write_stereo(ctx.stem_path("bass"), arpeggio)
    _write_stereo(ctx.stem_path("other"), np.zeros_like(mix))
    _write_stereo(ctx.stem_path("vocals"), np.zeros_like(mix))

    analyze = importlib.import_module("stemcell.analyze")
    drums_mod = importlib.import_module("stemcell.drums")

    analyze.run(ctx)
    drums_mod.run(ctx)

    ok = True

    bpm_candidates = [ctx.analysis["tempo"]["bpm"]] + [
        c["bpm"] for c in ctx.analysis["tempo"].get("candidates", [])
    ]
    bpm_ok = any(118.0 <= b <= 122.0 for b in bpm_candidates)
    print(f"tempo: primary={ctx.analysis['tempo']['bpm']:.2f} BPM, candidates={bpm_candidates} -> {'PASS' if bpm_ok else 'FAIL (expected one in [118,122])'}")
    ok &= bpm_ok

    key = ctx.analysis["key"]
    key_ok = (key["tonic"] == "A" and key["mode"] == "minor") or (
        key["tonic"] == "C" and key["mode"] == "major"
    )
    print(f"key: {key['name']} -> {'PASS' if key_ok else 'FAIL (expected A minor or its relative C major)'}")
    ok &= key_ok

    onset_count = ctx.drums["onset_count"]
    onset_ok = abs(onset_count - N_BEATS) <= 2
    print(f"onsets: {onset_count} (expected {N_BEATS}±2) -> {'PASS' if onset_ok else 'FAIL'}")
    ok &= onset_ok

    print("SELFTEST " + ("PASSED" if ok else "FAILED"))
    return ok
