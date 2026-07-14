from stemcell.melody import MINOR_INTERVALS
from stemcell.vocalchop import (
    BEATS_PER_BAR,
    SLICE_ROOT_NOTE,
    generate_mk_pattern,
    generate_todd_pattern,
)


def test_mk_pattern_offbeats_and_chord_tones():
    notes = generate_mk_pattern(root_pitch=60, scale="minor", bars=4, progression="i-VII-VI-VII")
    # 4 offbeat stabs + 1 ghost per bar, 4 bars
    assert len(notes) == 4 * 5
    # every note within one octave of the root (compact hook range)
    assert all(48 <= n["pitch"] <= 72 for n in notes)
    # bar 1 is the tonic chord: its stabs are diatonic C-minor triad tones (C, Eb, G pitch classes)
    bar1 = [n for n in notes if n["start_time"] < BEATS_PER_BAR]
    tonic_pcs = {(60 + MINOR_INTERVALS[d]) % 12 for d in (0, 2, 4)}
    assert {n["pitch"] % 12 for n in bar1} <= tonic_pcs
    # notes are time-sorted and non-negative
    assert notes == sorted(notes, key=lambda n: n["start_time"])
    assert all(n["start_time"] >= 0 for n in notes)


def test_todd_pattern_triggers_slice_notes_in_range():
    n_slices = 8
    notes = generate_todd_pattern(n_slices, bars=2, density=10)
    assert len(notes) == 20  # 10 hits/bar * 2 bars
    # every note is a slice-trigger note in [C1, C1 + n_slices)
    assert all(SLICE_ROOT_NOTE <= n["pitch"] < SLICE_ROOT_NOTE + n_slices for n in notes)
    # contour is an arch: reaches the top slice somewhere in the middle
    assert max(n["pitch"] for n in notes) == SLICE_ROOT_NOTE + n_slices - 1


def test_todd_pattern_empty_when_no_slices():
    assert generate_todd_pattern(0) == []


def test_swing_pushes_offbeats_late():
    straight = generate_todd_pattern(4, bars=1, density=16, swing_pct=50.0)
    swung = generate_todd_pattern(4, bars=1, density=16, swing_pct=60.0)
    # the offbeat 16ths (odd positions) should be later under swing; downbeats unchanged
    s0 = {round(n["start_time"], 3) for n in straight}
    w0 = {round(n["start_time"], 3) for n in swung}
    assert s0 != w0
