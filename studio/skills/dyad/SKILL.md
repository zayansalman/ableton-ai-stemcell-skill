---
name: dyad
description: Use for the user's two Fors Dyad instruments, the drums Dyad (Flerp group: 28-Dyad, Low, Top) and the melodic Dyad (melodic group: 32-Dyad, 33-30-Audio 3, 34-31-Audio 3), including their Variations devices, controller mappings, multi-out routing, recording them, and the Push 3 grid fix.
---

# Dyad (two instances)

Fors Dyad is a Max for Live sequencer + synth. The user has two, each with its own **Variations** device:
- **`Flerp`** is the **drums** Dyad.
- **`melodic`** is the **melodic** Dyad.

Both groups sit at the top level (no wrapper group). Each Dyad's audio comes out of two multi-out pairs (3/4 and 5/6)
into two audio tracks in the same group; those audio tracks monitor **In** and carry the sound.
Track names, routing and mappings are read from the user's **House Home template** (`~/Music/Ableton/User Library/Templates/House Home.als`), the source of truth. Live's API cannot show mappings; regenerate or verify with `python3 "$STEMCELL_HOME/tools/als_track_map.py" "<set>.als"`. The "NN-" prefix in some track names is Live's auto-numbering; use the name Live shows.

## Drums Dyad: `Flerp` group

### `28-Dyad` (the Dyad itself)
- **Type:** MIDI
- **MIDI in:** Ext: All Ins
- **Audio out:** Sends Only
- Dyad's sound leaves through its multi-outs, never the track, so this track's own monitoring is irrelevant.
- Devices: Dyad, Variations (the user has one Variations on each Dyad).

| Ch | Control # | Device | Control |
|---|---|---|---|
| 3 | CC 8 | Dyad | (Max for Live control) |
| 3 | CC 36 | Dyad | (Max for Live control) |
| 3 | CC 42 | Variations | (Max for Live control) |
| 3 | CC 49 | Dyad | (Max for Live control) |
| 3 | CC 50 | Dyad | (Max for Live control) |
| 3 | CC 73 | Variations | (Max for Live control) |

### `Low` (receives the audio)
- **Type:** Audio
- **Audio in:** 28-Dyad / 3/4
- **Audio out:** Group
- **Monitoring:** In

| Ch | Control # | Device | Control |
|---|---|---|---|
| 3 | CC 77 | Mixer | Volume |

### `Top` (receives the audio)
- **Type:** Audio
- **Audio in:** 28-Dyad / 5/6
- **Audio out:** Group
- **Monitoring:** In

| Ch | Control # | Device | Control |
|---|---|---|---|
| 3 | CC 14 | Mixer | Send |
| 3 | CC 37 | Mixer | Send |
| 3 | CC 78 | Mixer | Volume |


## Melodic Dyad: `melodic` group

### `32-Dyad` (the Dyad itself)
- **Type:** MIDI
- **MIDI in:** Ext: All Ins
- **Audio out:** Sends Only
- Dyad's sound leaves through its multi-outs, never the track, so this track's own monitoring is irrelevant.
- Devices: Dyad, Variations (the user has one Variations on each Dyad).

| Ch | Control # | Device | Control |
|---|---|---|---|
| 3 | CC 5 | Dyad | (Max for Live control) |
| 3 | CC 23 | Dyad | (Max for Live control) |
| 3 | CC 24 | Dyad | (Max for Live control) |
| 3 | CC 42 | Variations | (Max for Live control) |
| 3 | CC 74 | Variations | (Max for Live control) |
| 3 | CC 83 | Dyad | (Max for Live control) |

### `33-30-Audio 3` (receives the audio)
- **Type:** Audio
- **Audio in:** 32-Dyad / 3/4
- **Audio out:** Group
- **Monitoring:** In

| Ch | Control # | Device | Control |
|---|---|---|---|
| 3 | CC 85 | Mixer | Volume |

### `34-31-Audio 3` (receives the audio)
- **Type:** Audio
- **Audio in:** 32-Dyad / 5/6
- **Audio out:** Group
- **Monitoring:** In

| Ch | Control # | Device | Control |
|---|---|---|---|
| 3 | CC 80 | Mixer | Volume |
| 3 | CC 93 | Mixer | Send |
| 3 | CC 94 | Mixer | Send |


## Facts that stop wasted effort
Background notes: `$HOME/Documents/Claude/Dyad Troubleshooting/` (`Dyad Info.md`, `Dyad Findings.md`, `140 Bhoot Bass.adv`, `dyad-pattern-01..06.mid`).
- **Dyad has no MIDI output.** Don't try to capture MIDI from it. MIDI seen going to hardware is Live's Remote parameter feedback (uncheck **Remote** on that output port to stop it). To get notes, decode a saved `.adv` (gzip XML; step data is hex-encoded JSON); pipeline in `Dyad Findings.md` section 6.
- **Push 3 handshake bug:** loading a set containing Dyad, loading an `.adv` into a track, or power-cycling the Push can drop Dyad's sequencer grid. Fix without losing anything: drag the default `Dyad.amxd` from the browser **onto the existing Dyad instance** (parameter retention keeps the sound and pattern). Reopening a set (so any Live restart) can drop the grid; warn the user before a restart.
- Dyad's sound is global to the instance; an `.adv` saves sound + pattern together.
- **Recording:** arm the four audio tracks (not the Dyad MIDI tracks), record, then **disarm** and set them to **Auto** monitoring so the recording plays (an armed Auto track plays its input, not its clips). Tools: `set_track_arm`, `set_track_monitoring`, `get_track_meters`.
