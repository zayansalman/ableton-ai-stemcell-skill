"""Stage: polyphonic MIDI transcription of tonal stems (bass, other, vocals)."""

from __future__ import annotations

import json
import math

import numpy as np

from .ctx import Ctx, TONAL_STEMS, seconds_to_beats


def _skipped_entry() -> dict:
    return {
        "skipped": True,
        "skip_reason": "silent stem",
        "midi_file": None,
        "notes_file": None,
        "note_count": 0,
        "pitch_range": [0, 0],
        "median_velocity": 0,
        "clip_length_beats": 0.0,
        "beat_alignment_score": 0.0,
    }


def _beat_alignment_score(notes: list[dict]) -> float:
    if not notes:
        return 0.0
    hits = 0
    for n in notes:
        start = n["start_time"]
        nearest = round(start / 0.25) * 0.25
        if abs(start - nearest) <= 0.1:
            hits += 1
    return hits / len(notes)


def _transcribe_stem(ctx: Ctx, stem: str) -> dict:
    from basic_pitch.inference import predict

    _model_output, midi_data, note_events = predict(str(ctx.stem_path(stem)))

    midi_path = ctx.midi_dir / f"{stem}.mid"
    midi_data.write(str(midi_path))

    tempo_bpm = ctx.analysis["tempo"]["bpm"]
    grid_offset = ctx.analysis["tempo"]["grid_offset_sec"]

    notes = []
    for ev in note_events:
        start_s, end_s, pitch, amplitude = ev[0], ev[1], ev[2], ev[3]
        start_beats, duration_beats = seconds_to_beats(start_s, end_s, tempo_bpm, grid_offset)
        velocity = int(np.clip(round(amplitude * 127), 1, 127))
        notes.append(
            {
                "pitch": int(round(pitch)),
                "start_time": start_beats,
                "duration": duration_beats,
                "velocity": velocity,
                "mute": False,
            }
        )
    notes.sort(key=lambda n: n["start_time"])

    clip_length_beats = max(
        4.0,
        math.ceil(max((n["start_time"] + n["duration"] for n in notes), default=0.0) / 4.0) * 4.0,
    )

    notes_path = ctx.midi_dir / f"{stem}.notes.json"
    notes_path.write_text(
        json.dumps(
            {
                "stem": stem,
                "tempo_bpm": tempo_bpm,
                "grid_offset_sec": grid_offset,
                "clip_length_beats": clip_length_beats,
                "note_count": len(notes),
                "notes": notes,
            },
            indent=2,
        )
    )

    if notes:
        pitches = [n["pitch"] for n in notes]
        pitch_range = [min(pitches), max(pitches)]
        median_velocity = int(np.median([n["velocity"] for n in notes]))
    else:
        pitch_range = [0, 0]
        median_velocity = 0

    return {
        "skipped": False,
        "skip_reason": None,
        "midi_file": "midi/" + midi_path.name,
        "notes_file": "midi/" + notes_path.name,
        "note_count": len(notes),
        "pitch_range": pitch_range,
        "median_velocity": median_velocity,
        "clip_length_beats": clip_length_beats,
        "beat_alignment_score": float(_beat_alignment_score(notes)),
    }


def run(ctx: Ctx) -> None:
    if not ctx.analysis_json.exists():
        raise RuntimeError(
            f"transcribe stage requires analysis.json (run the 'analyze' stage first): {ctx.analysis_json}"
        )
    ctx.ensure_dirs()

    manifest: dict[str, dict] = {}
    for stem in TONAL_STEMS:
        if ctx.analysis["stems"][stem]["silent"]:
            manifest[stem] = _skipped_entry()
            continue
        try:
            manifest[stem] = _transcribe_stem(ctx, stem)
        except Exception as exc:
            raise RuntimeError(f"transcribe: failed on stem '{stem}': {exc}") from exc

    ctx.midi_manifest_json.write_text(json.dumps(manifest, indent=2))
