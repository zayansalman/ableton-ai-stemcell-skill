"""Vocal chopping + genre-authentic chop-pattern MIDI generation for house/garage.

Two production idioms, two Simpler setups (see the README emitted by write_chop_kit):

  MK mode  — one vocal chop played CHROMATICALLY to follow the chords (the "vocal
             as organ stab" of Marc Kinchen's dubs). Load ONE chop into Simpler in
             CLASSIC mode; the generated MIDI is real pitches (transpositions),
             placed on offbeats, following a minor chord progression.

  Todd mode — the whole vocal in Simpler SLICE mode, each MIDI note (from C1 = 36)
             triggers a different slice; the generated MIDI is a swung 16th-grid
             mosaic that sequences slice indices into a melodic contour (the Todd
             Edwards micro-cut approach).

Both emit notes in the notes.json schema used across this project
({"pitch","start_time","duration","velocity","mute"}, times in beats), so the
pattern drops straight into ableton-mcp's add_notes_to_clip.
"""

from __future__ import annotations

import json
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

from .melody import MAJOR_INTERVALS, MINOR_INTERVALS, _scale_intervals

SLICE_SILENCE_LINEAR = 10 ** (-60 / 20)
MIN_CHOP_SEC = 0.04
FADE_SEC = 0.004
SLICE_ROOT_NOTE = 36  # Ableton Simpler Slice mode maps slice 0 -> C1 (MIDI 36)
MAX_TODD_SLICES = 24  # cap addressable slices so trigger notes stay in MIDI range and stay musical
BEATS_PER_BAR = 4.0

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Chord progressions as scale-degree roots (0 = tonic). Soulful/deep-house staples.
PROGRESSIONS = {
    "i-VII-VI-VII": [0, 6, 5, 6],
    "i-VI-III-VII": [0, 5, 2, 6],
    "ii-v-i": [1, 4, 0, 0],
    "i-iv-VII-III": [0, 3, 6, 2],
}


def _degree_pitch(root_pitch: int, intervals: list[int], degree: int) -> int:
    octave, deg = divmod(degree, 7)
    return root_pitch + 12 * octave + intervals[deg]


def _chord_tones(root_pitch: int, intervals: list[int], chord_degree: int) -> list[int]:
    # Diatonic triad (1-3-5) built on the chord's scale degree, then FOLDED into one
    # octave above the root so MK-style stabs move with the chords but stay compact
    # (a hook lives within ~an octave — voicing inversion is fine for a stab).
    raw = [_degree_pitch(root_pitch, intervals, chord_degree + step) for step in (0, 2, 4)]
    return [root_pitch + ((p - root_pitch) % 12) for p in raw]


def _swing(beat_pos: float, swing_pct: float) -> float:
    """Delay the offbeat 16th of each 8th-note pair. 50% = straight, ~58% = house shuffle."""
    sixteenth = round(beat_pos / 0.25)
    if sixteenth % 2 == 1:  # the 'e'/'a' offbeat 16ths
        return beat_pos + (swing_pct / 100.0 - 0.5) * 0.5
    return beat_pos


# -- chopping ------------------------------------------------------------------
def chop_vocal(audio_path: Path, out_dir: Path, min_chop_sec: float = MIN_CHOP_SEC) -> list[dict]:
    y, sr = librosa.load(str(audio_path), sr=None, mono=True)
    onsets = librosa.onset.onset_detect(y=y, sr=sr, backtrack=True, units="samples")
    if len(onsets) == 0:
        onsets = np.array([0])

    slices_dir = out_dir / "slices"
    slices_dir.mkdir(parents=True, exist_ok=True)

    min_samples = int(min_chop_sec * sr)
    fade = int(FADE_SEC * sr)
    meta: list[dict] = []
    idx = 0
    for i, onset in enumerate(onsets):
        end = onsets[i + 1] if i + 1 < len(onsets) else len(y)
        seg = y[onset:end]
        tail = len(seg)
        while tail > 0 and abs(seg[tail - 1]) < SLICE_SILENCE_LINEAR:
            tail -= 1
        seg = seg[:tail]
        if len(seg) < min_samples:
            continue
        if fade > 0 and len(seg) > fade:
            seg = seg.copy()
            seg[-fade:] *= np.linspace(1.0, 0.0, fade, dtype=seg.dtype)

        pitch_hz = _estimate_pitch(seg, sr)
        fname = f"chop_{idx:02d}.wav"
        sf.write(str(slices_dir / fname), seg, sr)
        meta.append(
            {
                "index": idx,
                "file": f"slices/{fname}",
                "source_time_sec": float(onset) / sr,
                "duration_sec": len(seg) / sr,
                "pitch_hz": pitch_hz,
                "pitch_midi": _hz_to_midi(pitch_hz) if pitch_hz else None,
                "rms": float(np.sqrt(np.mean(seg.astype(np.float64) ** 2))),
            }
        )
        idx += 1
    return meta


def _estimate_pitch(y: np.ndarray, sr: int) -> float | None:
    if len(y) < sr // 20:
        return None
    try:
        f0 = librosa.yin(y, fmin=80, fmax=1000, sr=sr)
        f0 = f0[np.isfinite(f0)]
        return float(np.median(f0)) if len(f0) else None
    except Exception:
        return None


def _hz_to_midi(hz: float) -> int:
    return int(round(69 + 12 * np.log2(hz / 440.0)))


def most_tonal_slice(meta: list[dict]) -> dict | None:
    """Pick the best single chop for MK mode: has a clear detected pitch, loudest."""
    pitched = [m for m in meta if m["pitch_midi"] is not None]
    pool = pitched or meta
    return max(pool, key=lambda m: m["rms"]) if pool else None


# -- MK mode: one chop, Classic-mode transposition, offbeat pitched stabs -------
def generate_mk_pattern(
    root_pitch: int,
    scale: str | list[int],
    bars: int = 4,
    progression: str = "i-VII-VI-VII",
    swing_pct: float = 56.0,
    velocity: int = 100,
) -> list[dict]:
    intervals = _scale_intervals(scale) if isinstance(scale, str) else scale
    prog = PROGRESSIONS[progression]

    notes: list[dict] = []
    for bar in range(bars):
        chord_deg = prog[bar % len(prog)]
        tones = _chord_tones(root_pitch, intervals, chord_deg)
        # MK signature: stabs on the OFFBEATS (the 'and' of each beat), sparse, chord tones.
        for j, ob in enumerate([0.5, 1.5, 2.5, 3.5]):
            pitch = tones[j % len(tones)]
            start = bar * BEATS_PER_BAR + _swing(ob, swing_pct)
            notes.append(_note(pitch, start, 0.4, velocity))
        # one syncopated ghost on the 'a' of beat 2, softer
        ghost = bar * BEATS_PER_BAR + _swing(1.75, swing_pct)
        notes.append(_note(tones[0], ghost, 0.2, velocity - 20))

    notes.sort(key=lambda n: n["start_time"])
    return notes


# -- Todd mode: many slices, Slice-mode triggering, swung 16th mosaic ----------
def generate_todd_pattern(
    n_slices: int,
    bars: int = 2,
    swing_pct: float = 58.0,
    density: int = 10,
    velocity: int = 100,
) -> list[dict]:
    if n_slices <= 0:
        return []
    usable = min(n_slices, MAX_TODD_SLICES)  # Simpler addresses slices from C1 up; keep in MIDI range
    steps = _contour_steps(density, bars)
    notes: list[dict] = []
    for k, step in enumerate(steps):
        frac = k / max(1, len(steps) - 1)
        arch = 1.0 - abs(2 * frac - 1.0)  # 0 -> 1 -> 0, an arch melodic contour
        slice_idx = int(round(arch * (usable - 1)))
        note_pitch = SLICE_ROOT_NOTE + slice_idx
        bar = step // 16
        within = (step % 16) * 0.25
        start = bar * BEATS_PER_BAR + _swing(within, swing_pct)
        vel = velocity if step % 4 == 0 else velocity - 15  # accent the downbeat 16ths
        notes.append(_note(note_pitch, start, 0.22, vel))
    notes.sort(key=lambda n: n["start_time"])
    return notes


def _contour_steps(density: int, bars: int) -> list[int]:
    # Choose 16th-grid steps favouring offbeats/syncopation (the garage skip):
    # weight 'e'/'and'/'a' over the plain downbeat, deterministic top-N per bar.
    weight = {0: 0.6, 1: 1.0, 2: 0.9, 3: 1.0}
    per_bar = max(1, min(density, 16))
    chosen: list[int] = []
    for b in range(bars):
        lo = b * 16
        order = sorted(range(lo, lo + 16), key=lambda s: (-weight[s % 4], s))
        chosen.extend(sorted(order[:per_bar]))
    return chosen


def _note(pitch: int, start: float, duration: float, velocity: int) -> dict:
    return {
        "pitch": int(pitch),
        "start_time": round(float(max(0.0, start)), 4),
        "duration": float(duration),
        "velocity": int(np.clip(velocity, 1, 127)),
        "mute": False,
    }


# -- output --------------------------------------------------------------------
def write_chop_kit(
    audio_path: Path,
    out_dir: Path,
    root_pitch: int,
    scale: str,
    tempo_bpm: float,
    bars: int = 4,
    progression: str = "i-VII-VI-VII",
) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    slices = chop_vocal(audio_path, out_dir)

    mk = generate_mk_pattern(root_pitch, scale, bars=bars, progression=progression)
    todd = generate_todd_pattern(len(slices), bars=min(bars, 2))
    pick = most_tonal_slice(slices)

    _write_notes(
        out_dir / "mk.notes.json", mk, tempo_bpm, bars, mode="mk",
        extra={"progression": progression, "root_pitch": root_pitch, "scale": scale,
               "simpler_mode": "Classic", "load_slice": pick["file"] if pick else None},
    )
    _write_notes(
        out_dir / "todd.notes.json", todd, tempo_bpm, min(bars, 2), mode="todd",
        extra={"n_slices": len(slices), "simpler_mode": "Slice", "load": "the whole vocal"},
    )
    (out_dir / "slices.json").write_text(json.dumps(slices, indent=2))
    _write_readme(out_dir, len(slices), tempo_bpm, root_pitch, scale, pick)
    return {"n_slices": len(slices), "mk_notes": len(mk), "todd_notes": len(todd),
            "mk_pick": pick["file"] if pick else None}


def _write_notes(path: Path, notes: list[dict], tempo_bpm: float, bars: int, mode: str, extra: dict) -> None:
    path.write_text(json.dumps(
        {"mode": mode, "tempo_bpm": tempo_bpm, "clip_length_beats": float(bars) * BEATS_PER_BAR,
         "note_count": len(notes), **extra, "notes": notes}, indent=2))


def _write_readme(out_dir: Path, n_slices: int, tempo_bpm: float, root_pitch: int, scale: str, pick: dict | None) -> None:
    root = NOTE_NAMES[root_pitch % 12]
    pick_name = pick["file"] if pick else "the most tonal slice in slices/"
    (out_dir / "README.txt").write_text(
        f"""Vocal chop kit — {n_slices} slices, {tempo_bpm:.1f} BPM, {root} {scale}

MK MODE (pitched stabs, mk.notes.json):
  1. Drag ONE chop ({pick_name}) onto a MIDI track -> Simpler.
  2. Leave Simpler in Classic mode. Tune it so the chop sounds at {root} (Transpose).
  3. Load mk.notes.json into a clip (ableton-mcp add_notes_to_clip). The notes are real
     pitches following the {scale} progression; Classic mode transposes the chop to each.

TODD MODE (rhythmic mosaic, todd.notes.json):
  1. Drag the WHOLE vocal onto a MIDI track -> Simpler. Set playback mode to Slice.
  2. Simpler maps slice 0 -> C1 (MIDI 36), slice 1 -> C#1 (37), ... chromatically.
  3. Load todd.notes.json; its notes ({SLICE_ROOT_NOTE}..{SLICE_ROOT_NOTE + max(0, n_slices - 1)})
     trigger slices in a swung 16th mosaic. Set Simpler's slice count to ~{n_slices} to match.
""")
