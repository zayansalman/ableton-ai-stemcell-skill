"""Grounded methodology and generator for catchy, memorable melodic hooks.

This module turns a specific body of music-cognition research into two usable tools:
`score_catchiness`, a heuristic rubric for judging an existing melody, and
`generate_hook_melody`, a generator that applies the same principles to write a new
one. Both operate on the notes.json schema used across this project
({"pitch", "start_time", "duration", "velocity", "mute"}, all times in beats), so a
generated hook can be passed straight to ableton-mcp's add_notes_to_clip.

THE METHODOLOGY

David Huron's ITPRA theory (Imagination-Tension-Prediction-Reaction-Appraisal, from
"Sweet Anticipation", 2006) is the backbone: catchiness is not about being pleasant
throughout, it is about setting up a prediction and then confirming or gently
violating it in a controlled way. A melody that is 100% predictable never engages
the Imagination/Tension machinery and bores; one that is 100% unpredictable never
lets Prediction lock on, so there is nothing to confirm or subvert, and it fails to
stick. Catchy hooks live in the narrow band between the two.

That band is defined relative to a listener's internalized statistics. Statistical
learning / schema-expectation research shows listeners absorb genre-typical pitch
and rhythm distributions (which intervals are common, which beats carry onsets) just
from exposure. Melodies that are mostly prototypical for the schema but carry a few
salient deviations -- "prototypicality with a twist" -- are rated more memorable than
either fully generic or fully novel melodies, because the deviations are exactly the
ITPRA violations that get appraised and remembered.

Kelly Jakubowski's 2017 study "Dissecting an earworm" (self-reported stuck-song data
matched against melodic corpora) found that involuntary-earworm melodies share three
traits: faster tempo, a common overall pitch-contour shape, and -- critically -- small
unusual/unexpected intervals set against otherwise simple, mostly stepwise (conjunct)
motion. Catchiness is not pure stepwise smoothness; it is smoothness punctuated by a
few well-placed leaps.

Range matters too: hook melodies are typically compact, within about an octave. A
narrow tessitura makes a tune singable and makes repetition easy for the ear to
track, since register alone does not distract from the recurring shape.

That recurring shape usually takes one of a few contour archetypes: the arch
(rise then fall), the wave (undulating), and especially the terraced contour, which
steps up or down in plateaus. Terracing in particular gives a phrase a distinctive
silhouette that survives compression, transposition and variation, which is what
makes it recognizable on a second hearing.

The single highest-leverage technique, though, is motif economy with
repetition-with-variation: one or two short rhythmic/melodic cells reused across the
phrase, varied by transposition (sequence), inversion, or rhythmic augmentation
rather than constantly introducing new material. Pop and dance hooks build this into
antecedent-consequent (call-and-response) phrase structure -- a 2-bar "question" that
is answered by a 2-bar "response" resolving more strongly toward the tonic -- which
is the standard 4- or 8-bar unit of the genre.

Rhythmically, hooks anchor to strong beats (beat 1 and the backbeat) rather than
staying busy throughout, with 1-2 syncopated "hook points" set against an otherwise
on-grid rhythm -- not constant syncopation. Melodically, phrases that end on scale
degree 1 or 3 read as resolved and closed; ending on 2 or 7 reads as open,
unresolved tension, useful mid-phrase or in a pre-chorus but wrong for a hook's final
landing. Finally, pop convention places the hook in the first ~10 seconds of a song,
and often introduces its rhythmic motif (the pattern of onsets) before its full
melodic content arrives, since rhythm is recognized faster than pitch content --
rhythm-first recognition.

score_catchiness operationalizes range/stepwise-ratio/motif-repetition/beat-anchoring
/resolution as five independent 0..1 proxies grounded in the paragraphs above.
generate_hook_melody builds a 4-bar antecedent-consequent hook directly from the same
rules: a 1-3-5 motif with one deliberate leap, sequenced and varied across the
phrase, anchored to strong beats with a single accented hook point per 2-bar phrase,
and resolved to the tonic or third on the final downbeat.
"""

from __future__ import annotations

import difflib

import numpy as np

MAJOR_INTERVALS = [0, 2, 4, 5, 7, 9, 11]
MINOR_INTERVALS = [0, 2, 3, 5, 7, 8, 10]

# Krumhansl-Kessler key profiles (index 0 = C), used to infer a melody's own key
# when the caller of score_catchiness does not supply root_pitch/scale. Inlined here
# rather than imported from analyze.py so this module stays usable without the audio
# stack (librosa etc.).
_KK_MAJOR = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
_KK_MINOR = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]


def _infer_key(pitches: list[int]) -> tuple[int, list[int]]:
    """Estimate (root_pitch_class, scale_intervals) from a melody's pitch-class
    histogram via Krumhansl-Schmuckler correlation, so `resolution` can be scored
    against the melody's own implied key instead of a hardcoded C major.
    """
    hist = np.zeros(12)
    for p in pitches:
        hist[int(p) % 12] += 1
    if hist.sum() == 0:
        return 0, MAJOR_INTERVALS
    hist = hist / hist.sum()

    best_score = -2.0
    best_pc = 0
    best_intervals = MAJOR_INTERVALS
    for template, intervals in ((_KK_MAJOR, MAJOR_INTERVALS), (_KK_MINOR, MINOR_INTERVALS)):
        for r in range(12):
            rotated = np.roll(template, r)
            if np.std(rotated) == 0 or np.std(hist) == 0:
                continue
            score = float(np.corrcoef(hist, rotated)[0, 1])
            if score > best_score:
                best_score = score
                best_pc = r
                best_intervals = intervals
    return best_pc, best_intervals

_MOTIF_DEGREES = (0, 1, 2, 4, 3)
_MOTIF_DURATIONS = (1.0, 0.5, 0.5, 1.0, 1.0)
_MOTIF_VELOCITIES_ACCENTED = (101, 95, 105, 101, 95)
_MOTIF_VELOCITIES_PLAIN = (101, 95, 95, 101, 95)

_BAR2_DEGREE_OFFSETS = (0, -2, -3, -4)
_BAR2_LOCAL_ROOT_DEGREE = 7
_BAR2_DURATIONS = (1.5, 0.5, 1.0, 1.0)
_BAR2_VELOCITIES = (101, 105, 101, 95)

_BAR3_DEGREES_TONIC = (4, 0)
_BAR3_DEGREES_THIRD = (4, 2)
_BAR3_DURATIONS = (2.0, 2.0)
_BAR3_VELOCITIES = (101, 101)

_BEATS_PER_BAR = 4.0


def _scale_intervals(scale: str) -> list[int]:
    normalized = scale.strip().lower()
    if normalized == "major":
        return MAJOR_INTERVALS
    if normalized == "minor":
        return MINOR_INTERVALS
    raise RuntimeError(f"generate_hook_melody: unknown scale '{scale}', expected 'major' or 'minor'")


def _degree_pitch(root_pitch: int, intervals: list[int], degree: int) -> int:
    octave, degree_in_scale = divmod(degree, 7)
    return root_pitch + 12 * octave + intervals[degree_in_scale]


def _bar_notes(
    degrees: tuple[int, ...],
    durations: tuple[float, ...],
    velocities: tuple[int, ...],
    root_pitch: int,
    intervals: list[int],
    bar_offset_beats: float,
) -> list[dict]:
    notes = []
    t = 0.0
    for degree, dur, vel in zip(degrees, durations, velocities):
        notes.append(
            {
                "pitch": _degree_pitch(root_pitch, intervals, degree),
                "start_time": bar_offset_beats + t,
                "duration": dur,
                "velocity": vel,
                "mute": False,
            }
        )
        t += dur
    return notes


def generate_hook_melody(root_pitch: int, scale: str, tempo_bpm: float, bars: int = 4) -> list[dict]:
    """Generate an antecedent-consequent melodic hook, ready for add_notes_to_clip.

    Bar 1: the motif (scale degrees 1-2-3-5-4, mostly stepwise with one deliberate
    leap from the 3rd to the 5th) with a single accented syncopated hook point.
    Bar 2: the same motif sequenced up to scale degree 4 (subdominant), same rhythm
    so it reads as a clear repeat, ending on the leading tone -- the question left
    open. Bar 3: a rhythmic variation of the motif (fewer, longer notes) carrying its
    own hook point, descending from the octave tonic. Bar 4: the response, resolving
    to the tonic (or, on a repeated unit's final bar, the third for variety) on
    sustained strong-beat notes.
    """
    if bars < 1:
        raise RuntimeError(f"generate_hook_melody: bars must be >= 1, got {bars}")

    intervals = _scale_intervals(scale)

    bar0_degrees = _MOTIF_DEGREES
    bar1_degrees = tuple(d + 3 for d in _MOTIF_DEGREES)
    bar2_degrees = tuple(_BAR2_LOCAL_ROOT_DEGREE + off for off in _BAR2_DEGREE_OFFSETS)

    unit = [
        (bar0_degrees, _MOTIF_DURATIONS, _MOTIF_VELOCITIES_ACCENTED),
        (bar1_degrees, _MOTIF_DURATIONS, _MOTIF_VELOCITIES_PLAIN),
        (bar2_degrees, _BAR2_DURATIONS, _BAR2_VELOCITIES),
        (_BAR3_DEGREES_TONIC, _BAR3_DURATIONS, _BAR3_VELOCITIES),
    ]
    final_bar_varied = (_BAR3_DEGREES_THIRD, _BAR3_DURATIONS, _BAR3_VELOCITIES)

    resolving_bar = unit[3]  # (_BAR3_DEGREES_TONIC) — lands on the tonic downbeat

    notes: list[dict] = []
    for bar_idx in range(bars):
        is_last = bar_idx == bars - 1
        if is_last:
            # The final bar of ANY phrase length must resolve (tonic for <=4 bars,
            # the third for a repeated multi-unit hook so the repeat has variety).
            degrees, durations, velocities = final_bar_varied if bars > 4 else resolving_bar
        else:
            degrees, durations, velocities = unit[bar_idx % 4]
        notes.extend(
            _bar_notes(degrees, durations, velocities, root_pitch, intervals, bar_idx * _BEATS_PER_BAR)
        )
    return notes


def _range_compactness_score(pitches: list[int]) -> float:
    if len(pitches) < 2:
        return 1.0
    span = max(pitches) - min(pitches)
    if span <= 12:
        return 1.0
    if span >= 24:
        return 0.0
    return 1.0 - (span - 12) / 12.0


def _stepwise_ratio_score(pitches: list[int]) -> float:
    # Peak in the 60-85% stepwise band, not at 100%: per Jakubowski, a few larger
    # leaps against mostly stepwise motion aid memorability more than pure steps.
    if len(pitches) < 2:
        return 1.0
    intervals = [abs(b - a) for a, b in zip(pitches, pitches[1:])]
    ratio = sum(1 for iv in intervals if iv <= 2) / len(intervals)
    if 0.60 <= ratio <= 0.85:
        return 1.0
    if ratio < 0.60:
        return ratio / 0.60
    return max(0.0, 1.0 - (ratio - 0.85) / 0.15)


def _note_bar_signature(bar_notes: list[dict]) -> list[tuple[str, float]]:
    ordered = sorted(bar_notes, key=lambda n: n["start_time"])
    if len(ordered) == 1:
        # A one-note bar has no pairwise interval; represent it by its duration alone
        # so two identical sustained bars still match instead of being dropped from
        # the comparison pool (which would floor a maximally-repetitive melody to 0).
        return [("single", round(ordered[0]["duration"] * 4) / 4)]
    signature = []
    for prev, curr in zip(ordered, ordered[1:]):
        interval = curr["pitch"] - prev["pitch"]
        direction = "up" if interval > 0 else ("down" if interval < 0 else "same")
        size = "leap" if abs(interval) > 2 else "step"
        duration_bucket = round(curr["duration"] * 4) / 4
        signature.append((f"{size}_{direction}", duration_bucket))
    return signature


def _motif_repetition_score(notes: list[dict]) -> float:
    # Simple (non-ML) sequence matching over categorical interval+duration cells,
    # grouped per 4-beat bar. Categorical (step/leap + direction) rather than exact
    # semitone deltas so a diatonic sequence (same motif transposed) still matches --
    # diatonic step sizes vary (whole/half steps), so exact intervals drift under
    # transposition even though the shape is clearly repeated.
    bars: dict[int, list[dict]] = {}
    for n in notes:
        if n.get("mute", False):
            continue
        bar_idx = int(n["start_time"] // _BEATS_PER_BAR)
        bars.setdefault(bar_idx, []).append(n)

    signatures = [sig for sig in (_note_bar_signature(bn) for bn in bars.values()) if sig]
    if len(signatures) < 2:
        return 0.0

    best_matches = []
    for i, sig_a in enumerate(signatures):
        best = 0.0
        for j, sig_b in enumerate(signatures):
            if i == j:
                continue
            best = max(best, difflib.SequenceMatcher(None, sig_a, sig_b).ratio())
        best_matches.append(best)
    return float(np.clip(np.mean(best_matches), 0.0, 1.0))


def _beat_anchoring_score(notes: list[dict]) -> float:
    if not notes:
        return 0.0
    hits = 0
    for n in notes:
        phase = n["start_time"] % _BEATS_PER_BAR
        if phase <= 0.1 or abs(phase - 2.0) <= 0.1:
            hits += 1
    fraction = hits / len(notes)
    if 0.70 <= fraction <= 0.90:
        return 1.0
    if fraction < 0.70:
        return fraction / 0.70
    return 1.0 - (fraction - 0.90) / 0.10 * 0.15


def _resolution_score(notes: list[dict], root_pitch: int, scale: list[int]) -> float:
    sounding = [n for n in notes if not n.get("mute", False)] or notes
    last_note = max(sounding, key=lambda n: n["start_time"])
    pitch_class = (last_note["pitch"] - root_pitch) % 12
    tonic, third, fifth = scale[0] % 12, scale[2] % 12, scale[4] % 12
    if pitch_class in (tonic, third):
        return 1.0
    if pitch_class == fifth:
        return 0.4
    return 0.0


def score_catchiness(
    notes: list[dict],
    tempo_bpm: float,
    root_pitch: int | None = None,
    scale: str | list[int] | None = None,
) -> dict:
    """Heuristic 0..1 proxy scores for a melody's catchiness.

    notes: notes.json-shaped note dicts (pitch/start_time/duration/velocity/mute),
    start_time and duration in beats, 4/4 assumed.
    tempo_bpm: accepted for interface symmetry with the rest of the pipeline and
    because tempo is part of Jakubowski's earworm profile, but none of the five
    sub-scores below are tempo-dependent, so it is not folded into `overall`.
    root_pitch/scale: key context for `resolution`, which notes.json does not carry
    on its own. `scale` accepts the same "major"/"minor" string generate_hook_melody
    takes, or an explicit interval list. When either is omitted it is inferred from
    the melody's own pitch-class distribution, so scoring a non-C-major hook the
    obvious way (no key args) no longer silently reports it as unresolved.
    """
    if not notes:
        return {
            "range_compactness": 0.0,
            "stepwise_ratio": 0.0,
            "motif_repetition": 0.0,
            "beat_anchoring": 0.0,
            "resolution": 0.0,
            "overall": 0.0,
        }

    ordered = sorted(notes, key=lambda n: n["start_time"])
    pitches = [n["pitch"] for n in ordered]

    if isinstance(scale, str):
        scale = _scale_intervals(scale)
    if root_pitch is None or scale is None:
        inferred_root, inferred_scale = _infer_key(pitches)
        if root_pitch is None:
            root_pitch = inferred_root
        if scale is None:
            scale = inferred_scale

    scores = {
        "range_compactness": _range_compactness_score(pitches),
        "stepwise_ratio": _stepwise_ratio_score(pitches),
        "motif_repetition": _motif_repetition_score(ordered),
        "beat_anchoring": _beat_anchoring_score(ordered),
        "resolution": _resolution_score(ordered, root_pitch, scale),
    }
    scores = {k: float(np.clip(v, 0.0, 1.0)) for k, v in scores.items()}
    scores["overall"] = float(np.clip(np.mean(list(scores.values())), 0.0, 1.0))
    return scores
