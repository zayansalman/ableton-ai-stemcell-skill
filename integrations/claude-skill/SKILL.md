---
name: dissect
description: Use when the user gives an audio file (mp3/wav) of a song and wants it broken down — stems, tempo, key/scale, drum one-shots, MIDI of the parts — and/or wants matching sounds sourced from Splice or the parts rebuilt into an Ableton Live project. Triggers on "dissect this track", "what's in this song", "get me the samples/drums/MIDI from this", "recreate this in Ableton", "find sounds like this song".
trigger: /dissect
---

# /dissect

Turn an audio file into its component parts (from the audio itself, not web lookups), then optionally source similar licensed sounds on Splice and rebuild the arrangement in Ableton Live.

Backed by the local `stemcell` pipeline at `$STEMCELL_REPO` (default `~/projects/ableton-ai-stemcell-skill`; uv project, Python 3.11) plus two MCP connectors: **Splice** (`describe_a_sound`, `download_asset` — text search + credit-metered download) and **ableton-mcp** (`set_tempo`, `create_midi_track`, `add_notes_to_clip`, `create_audio_clip`, `load_instrument_or_effect`, `get_browser_tree`).

## Usage

```
/dissect <path-to-audio>                 # full analysis → report.md summary
/dissect <path> --splice                 # + generate Splice search queries from the analysis
/dissect <path> --ableton                # + rebuild into the currently-open Live set (asks first)
/dissect <path> --out <dir>              # custom output dir (default ~/dissections/<slug>)
```

## Workflow

### 1. Run the pipeline
```bash
cd "${STEMCELL_REPO:-$HOME/projects/ableton-ai-stemcell-skill}" && uv run stemcell run "<path>" --out <outdir>
```
First run on a machine needs `stemcell bootstrap` once (~700 MB: htdemucs + CLAP). Demucs separation is the slow stage (~2 min/audio-minute on M2 CPU) — run it backgrounded with a Monitor watching for `Done. Report` / `error` / `Traceback`. Stages cache by file-existence; re-running skips completed stages.

### 2. Read the analysis — never re-derive by ear
Read `<outdir>/report.json` (authoritative) and `report.md` (human summary). Everything downstream comes from measured values in `report.json`:
- `tempo.bpm` + `tempo.candidates` (half/double) + `tempo.tempo_stability` (low = rubato warning)
- `key.name` + `key.confidence` + `key.alternates` (relative/parallel)
- `stems[*].tags` + `stems[*].splice_query_hints` (pre-built)
- `drums.oneshots[*]` — CLAP `label`, `count_in_song`, `tags`, `character_hints` (808/909 — **hint-grade, state as such**), `splice_query_hints`
- `midi[*].notes_file` → `<outdir>/midi/<stem>.notes.json` — already in beats, ready for `add_notes_to_clip`

### 3. `--splice` — source similar licensed sounds
Before querying, **identify the likely gear source** of each drum/synth element using `references/dance-gear-fingerprints.md` in the stemcell repo — map the measured spectral fingerprint (`centroid_hz`, `lowband_ratio`, `flatness`, decay) + CLAP `character_hints` to a probable machine/preset, with a confidence tier (Documented / Strong-inference / Ambiguous). A specific source ("909 kick", "Korg M1 house organ") makes a far better Splice query than a generic label. State confidence honestly — audio-based gear ID is inference, and CLAP's "909" axis is really a "punchy/has-a-click" flag, so distrust it where the spectral tell (e.g. the 909 kick's bright click transient) is absent.

Then run `describe_a_sound` with the gear-informed query (optionally `bpm_min`/`bpm_max` around `tempo.bpm`, plus key). Present results; let the user pick. **`download_asset` spends a credit on first download — always confirm before downloading.** Save to `~/Music/Ableton/User Library/Samples/`.

### 4. `--ableton` — rebuild in Live
`get_session_info` first. **The tools mutate whatever Live set is open — confirm with the user before writing to a real project; offer a blank set.** Then: `set_tempo(report.tempo.bpm)` → per element `create_midi_track` + `set_track_name` → `create_clip(track, 0, notes.clip_length_beats)` + `add_notes_to_clip(track, 0, notes.notes)` (pass the notes.json array verbatim) → `create_audio_clip` for downloaded loops/one-shots → `load_instrument_or_effect` via `get_browser_tree` for built-ins.

## Honest limits (state these, don't paper over)
- Constant-tempo + 4/4 assumed; `tempo_stability` is the honesty signal.
- CLAP gear-ID (808 vs 909) is a hint, not proof.
- No synth-preset reverse-engineering. For a synth part, the move is: load the right built-in (subtractive→Analog/Drift, FM→Operator, wavetable→Wavetable) + closest stock preset + a manual parameter recipe. ableton-mcp cannot set device parameters or reach inside a Drum Rack pad chain.
- Serum presets can't be loaded programmatically (upstream issue) — source the sound as audio from Splice instead.
- Sliced hits from a commercial recording are for reference/learning — released music should use the Splice-matched licensed equivalents.

## Writing catchy MIDI
When generating or filling in a melody (e.g. an empty section), use `stemcell.melody`:
```python
from stemcell.melody import generate_hook_melody, score_catchiness
notes = generate_hook_melody(root_pitch, "minor", tempo_bpm, bars=4)  # notes[] → add_notes_to_clip
score_catchiness(notes, tempo_bpm)  # 5 sub-scores + overall; infers key if not passed
```
Its docstring holds the grounded methodology (Huron ITPRA, Jakubowski earworm contour, motif economy + repetition-with-variation, antecedent-consequent phrasing, strong-beat anchoring, resolution to tonic/third).

## Vocal chops (MK / Todd Edwards style)
When the user gives a vocal sample and wants playable chops or an auto-made chop loop:
```bash
stemcell chop <vocal.wav> --out <dir> --tempo <bpm> --root <C|F#3|…> --scale minor --bars 4
```
Chop a **short (1–2 bar) vocal phrase**, not a whole track (Todd mode addresses ~24 slices). Emits `slices/`, `mk.notes.json`, `todd.notes.json` (both `add_notes_to_clip`-ready), and `README.txt` with the one-drag setup. Two idioms, two Simpler setups — see `references/house-vocal-chop-craft.md` for the grounded craft (MK Akai S1100 key-groups → Classic; Todd S6000 → Slice):
- **MK mode** (`mk.notes.json`): one chop (the `load_slice` field names the most tonal one) → Simpler **Classic** mode, tuned to the root. The MIDI is pitched offbeat stabs following the progression. **The user must drag that one chop in + set the transpose** (Live API can't load a sample into Simpler — the one manual step).
- **Todd mode** (`todd.notes.json`): the whole vocal → Simpler **Slice** mode. The MIDI (notes from C1=36) triggers slices in a swung 16th mosaic.
After the user does the one drag, load the pattern via `add_notes_to_clip` verbatim.
