"""Smoke tests for the studio/ tools that need no Ableton Live, model or external checkout."""
import gzip
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

TOOLS = Path(__file__).resolve().parent.parent / "studio" / "tools"
sys.path.insert(0, str(TOOLS))

from als_copy_tracks import base_name, track_blocks  # noqa: E402

MINI_SET = """<?xml version="1.0" encoding="UTF-8"?>
<Ableton><LiveSet><NextPointeeId Value="10" /><Tracks>
\t<AudioTrack Id="3"><Name><EffectiveName Value="12-Kick" /></Name><TrackGroupId Value="-1" /></AudioTrack>
\t<MidiTrack Id="5"><Name><EffectiveName Value="Bass" /></Name><TrackGroupId Value="3" /></MidiTrack>
</Tracks></LiveSet></Ableton>
"""


def test_track_blocks_parses_tracks():
    tracks = track_blocks(MINI_SET)
    assert [(t["tag"], t["id"], t["name"], t["group"]) for t in tracks] == [
        ("AudioTrack", 3, "12-Kick", -1),
        ("MidiTrack", 5, "Bass", 3),
    ]
    assert base_name("12-Kick") == "Kick"


def test_midi_mappings_lists_mapped_controls(tmp_path):
    from als_midi_mappings import scan

    xml = MINI_SET.replace(
        '<TrackGroupId Value="-1" />',
        '<TrackGroupId Value="-1" /><Volume><KeyMidi><Channel Value="1" /><NoteOrController Value="81" />'
        '<IsNote Value="false" /></KeyMidi></Volume>',
    )
    als = tmp_path / "mini.als"
    with gzip.open(als, "wt", encoding="utf-8") as f:
        f.write(xml)
    rows = scan(str(als))
    assert len(rows) == 1
    assert rows[0]["track"] == "12-Kick" and rows[0]["channel"] == 2 and rows[0]["number"] == 81


def test_hat_split_parts_sum_to_input(tmp_path):
    sr = 44100
    t = np.arange(sr) / sr
    x = np.zeros(sr)
    rng = np.random.default_rng(0)
    for k, start in enumerate(np.arange(0.05, 0.95, 0.125)):
        decay = 0.15 if k % 2 else 0.01  # alternate open (long ring) and closed (short) hats
        i = int(start * sr)
        x[i:] += 0.5 * rng.standard_normal(sr - i) * np.exp(-(t[: sr - i]) / decay)
    src = tmp_path / "loop - hh.wav"
    sf.write(src, x, sr, subtype="PCM_24")
    out = subprocess.run([sys.executable, str(TOOLS / "hat_split.py"), str(src)],
                         capture_output=True, text=True, check=True)
    info = json.loads(out.stdout)
    assert info["sum_error"] < 1e-6
    parts = {h["part"] for h in info["hits"]}
    assert parts == {"open", "closed"}
    for key in ("open", "closed"):
        y, ysr = sf.read(info[key])
        assert ysr == sr and len(y) == sr
