"""Merge analysis.json + drums.json + midi/manifest.json into report.json / report.md."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import soundfile as sf

from .ctx import Ctx, SCHEMA_VERSION

FOOTER = (
    "Sliced hits from commercial recordings are for reference and learning; use the "
    "Splice-matched licensed equivalents in released music."
)


def _build_warnings(analysis: dict, midi_manifest: dict) -> list[str]:
    warnings: list[str] = []
    if analysis["tempo"]["tempo_stability"] < 0.7:
        warnings.append("tempo may be unstable / rubato")
    if analysis["key"]["confidence"] < 0.15:
        warnings.append("key detection confidence is low")
    for stem, entry in midi_manifest.items():
        if entry.get("skipped"):
            warnings.append(f"{stem} MIDI transcription skipped: {entry.get('skip_reason')}")
    return warnings


def _build_report_json(ctx: Ctx) -> dict:
    info = sf.info(str(ctx.input_wav))
    analysis = ctx.analysis
    drums = ctx.drums
    midi_manifest = json.loads(ctx.midi_manifest_json.read_text())

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "path": str(ctx.audio_in),
            "duration_sec": info.duration,
            "sample_rate": info.samplerate,
            "channels": info.channels,
        },
        "tempo": analysis["tempo"],
        "key": analysis["key"],
        "stems": analysis["stems"],
        "drums": drums,
        "midi": midi_manifest,
        "warnings": _build_warnings(analysis, midi_manifest),
    }


def _fmt(value: float, spec: str = ".2f") -> str:
    return format(value, spec)


def _stems_table(stems: dict) -> list[str]:
    lines = ["| stem | rms_db | activity_ratio | silent | tags |", "| --- | --- | --- | --- | --- |"]
    for stem, s in stems.items():
        tags = ", ".join(s["tags"])
        lines.append(
            f"| {stem} | {_fmt(s['rms_db'])} | {_fmt(s['activity_ratio'])} | {s['silent']} | {tags} |"
        )
    return lines


def _drums_table(oneshots: list[dict]) -> list[str]:
    lines = [
        "| label | clap_confidence | count_in_song | tags | splice_query_hints |",
        "| --- | --- | --- | --- | --- |",
    ]
    for o in oneshots:
        tags = ", ".join(o["tags"])
        hints = "; ".join(o["splice_query_hints"])
        lines.append(
            f"| {o['label']} | {_fmt(o['clap_confidence'])} | {o['count_in_song']} | {tags} | {hints} |"
        )
    return lines


def _loops_table(loops: list[dict]) -> list[str]:
    lines = ["| file | start_bar | num_bars |", "| --- | --- | --- |"]
    for loop in loops:
        lines.append(f"| {loop['file']} | {loop['start_bar']} | {loop['num_bars']} |")
    return lines


def _midi_table(midi_manifest: dict) -> list[str]:
    lines = [
        "| stem | note_count | pitch_range | clip_length_beats | beat_alignment_score |",
        "| --- | --- | --- | --- | --- |",
    ]
    for stem, entry in midi_manifest.items():
        if entry.get("skipped"):
            lines.append(f"| {stem} | skipped: {entry.get('skip_reason')} | | | |")
        else:
            pitch_range = entry["pitch_range"]
            lines.append(
                f"| {stem} | {entry['note_count']} | {pitch_range[0]}-{pitch_range[1]} | "
                f"{_fmt(entry['clip_length_beats'])} | {_fmt(entry['beat_alignment_score'])} |"
            )
    return lines


def _build_report_md(report: dict) -> str:
    tempo = report["tempo"]
    key = report["key"]
    source = report["source"]

    lines: list[str] = []
    lines.append("# stemcell report")
    lines.append("")
    lines.append(
        f"**Tempo:** {_fmt(tempo['bpm'])} BPM (confidence {_fmt(tempo['confidence'])})  "
    )
    lines.append(f"**Key:** {key['name']} (confidence {_fmt(key['confidence'])})  ")
    lines.append(f"**Duration:** {_fmt(source['duration_sec'])}s")
    lines.append("")

    lines.append("## Stems")
    lines.extend(_stems_table(report["stems"]))
    lines.append("")

    lines.append("## Drum-hit inventory")
    lines.extend(_drums_table(report["drums"]["oneshots"]))
    lines.append("")

    lines.append("## Loops")
    lines.extend(_loops_table(report["drums"]["loops"]))
    lines.append("")

    lines.append("## MIDI summary")
    lines.extend(_midi_table(report["midi"]))
    lines.append("")

    if report["warnings"]:
        lines.append("## Warnings")
        for w in report["warnings"]:
            lines.append(f"- {w}")
        lines.append("")

    lines.append(FOOTER)
    lines.append("")

    return "\n".join(lines)


def run(ctx: Ctx) -> None:
    if not ctx.analysis_json.exists():
        raise RuntimeError(f"report stage requires analysis.json at {ctx.analysis_json}, run analyze first")
    if not ctx.drums_json.exists():
        raise RuntimeError(f"report stage requires drums.json at {ctx.drums_json}, run drums first")
    if not ctx.midi_manifest_json.exists():
        raise RuntimeError(
            f"report stage requires midi manifest at {ctx.midi_manifest_json}, run transcribe first"
        )

    report = _build_report_json(ctx)
    ctx.report_json.write_text(json.dumps(report, indent=2))
    ctx.report_md.write_text(_build_report_md(report))
