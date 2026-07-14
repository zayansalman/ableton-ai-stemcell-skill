"""Shared pipeline context and output-directory contract.

Every stage module exposes a single ``run(ctx: Ctx) -> None`` function.
Stages are pure with respect to disk: they read prior-stage outputs from
``ctx.outdir`` and write their own outputs there. Nothing is passed in
memory between stages so a stage can be skipped (cache hit) or re-run in
isolation.

Output directory contract (see report.py for the authoritative report.json
schema):

    <outdir>/
      input.wav                      # normalized 44.1kHz stereo source
      stems/{drums,bass,other,vocals}.wav
      oneshots/<label>_<NN>.wav      # label in ONESHOT_LABELS
      loops/drums_bars_<AAA>-<BBB>.wav
      midi/<stem>.mid                # stem in TONAL_STEMS, present unless skipped
      midi/<stem>.notes.json
      midi/manifest.json
      analysis.json                  # internal cache, stage "analyze"
      drums.json                     # internal cache, stage "drums"
      report.json                    # authoritative machine-readable output
      report.md                      # human-readable summary
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

SAMPLE_RATE = 44100

STEMS = ("drums", "bass", "other", "vocals")
TONAL_STEMS = ("bass", "other", "vocals")

ONESHOT_LABELS = (
    "kick", "snare", "clap", "hat_closed", "hat_open", "crash", "ride",
    "tom", "shaker", "tamb", "rim", "snap", "cowbell", "perc",
)

# CLAP zero-shot candidate prompts for primary drum-hit labeling.
CLAP_DRUM_LABELS = {
    "kick": "kick drum",
    "snare": "snare drum",
    "clap": "handclap",
    "hat_closed": "closed hi-hat",
    "hat_open": "open hi-hat",
    "crash": "crash cymbal",
    "ride": "ride cymbal",
    "tom": "tom drum",
    "shaker": "shaker",
    "tamb": "tambourine",
    "rim": "rimshot",
    "snap": "finger snap",
    "cowbell": "cowbell",
    "perc": "percussion hit",
}

CLAP_CHARACTER_HINTS = (
    "808 drum machine", "909 drum machine",
    "acoustic drum kit", "electronic drums",
)

SCHEMA_VERSION = 1


@dataclass
class Ctx:
    """Per-run paths and lazily-loaded prior-stage state."""

    audio_in: Path
    outdir: Path
    force: bool = False
    allow_long: bool = False
    skip_clap: bool = False  # selftest sets this True: no model download, no classification
    _analysis: dict | None = field(default=None, repr=False)
    _drums: dict | None = field(default=None, repr=False)

    # ---- canonical paths -------------------------------------------------
    @property
    def input_wav(self) -> Path:
        return self.outdir / "input.wav"

    @property
    def stems_dir(self) -> Path:
        return self.outdir / "stems"

    def stem_path(self, stem: str) -> Path:
        return self.stems_dir / f"{stem}.wav"

    @property
    def oneshots_dir(self) -> Path:
        return self.outdir / "oneshots"

    @property
    def loops_dir(self) -> Path:
        return self.outdir / "loops"

    @property
    def midi_dir(self) -> Path:
        return self.outdir / "midi"

    @property
    def analysis_json(self) -> Path:
        return self.outdir / "analysis.json"

    @property
    def drums_json(self) -> Path:
        return self.outdir / "drums.json"

    @property
    def midi_manifest_json(self) -> Path:
        return self.midi_dir / "manifest.json"

    @property
    def report_json(self) -> Path:
        return self.outdir / "report.json"

    @property
    def report_md(self) -> Path:
        return self.outdir / "report.md"

    # ---- cached prior-stage state -----------------------------------------
    @property
    def analysis(self) -> dict:
        if self._analysis is None:
            self._analysis = json.loads(self.analysis_json.read_text())
        return self._analysis

    @property
    def drums(self) -> dict:
        if self._drums is None:
            self._drums = json.loads(self.drums_json.read_text())
        return self._drums

    # ---- stage done-predicates (file-existence caching) -------------------
    def stage_done(self, name: str) -> bool:
        if self.force:
            return False
        checks = {
            "ingest": lambda: self.input_wav.exists(),
            "separate": lambda: all(self.stem_path(s).exists() for s in STEMS),
            "analyze": lambda: self.analysis_json.exists(),
            "drums": lambda: self.drums_json.exists(),
            "transcribe": lambda: self.midi_manifest_json.exists(),
            "report": lambda: self.report_json.exists(),
        }
        return checks[name]()

    def ensure_dirs(self) -> None:
        for d in (self.outdir, self.stems_dir, self.oneshots_dir, self.loops_dir, self.midi_dir):
            d.mkdir(parents=True, exist_ok=True)


def seconds_to_beats(start_s: float, end_s: float, tempo_bpm: float, grid_offset_sec: float) -> tuple[float, float]:
    """Convert a (start, end) time in seconds to (start_time, duration) in beats.

    Matches the ``add_notes_to_clip`` note contract used by the ableton-mcp
    connector: pitch/start_time/duration/velocity/mute, start_time and
    duration in beats. No quantization — raw floats.
    """
    start_beats = max(0.0, (start_s - grid_offset_sec) * tempo_bpm / 60.0)
    duration_beats = max(0.05, (end_s - start_s) * tempo_bpm / 60.0)
    return start_beats, duration_beats
