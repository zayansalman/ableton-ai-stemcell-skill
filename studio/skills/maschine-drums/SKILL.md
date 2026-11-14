---
name: maschine-drums
description: Use for the user's Maschine 3 drums in Ableton: the Maschine Drums group and its Kick, Snare, Perc, Hat, Break and Shaker tracks, Maschine 3 / Maschine Control, the C-Kick to Maschine and D-Maschine Cue returns, their multi-out routing and controller mappings, or when drum tracks show No Input.
---

# Maschine Drums

The user plays Maschine 3 **live**. Its tracks look silent whenever Maschine isn't being played.
Track names, routing and mappings are read from the user's **House Home template** (`~/Music/Ableton/User Library/Templates/House Home.als`), the source of truth. Live's API cannot show mappings; regenerate or verify with `python3 "$STEMCELL_HOME/tools/als_track_map.py" "<set>.als"`. The "NN-" prefix in some track names is Live's auto-numbering; use the name Live shows.

**Correction from the user:** Shaker's two sends and DJ filter are in the template on controller **channel 6**. That was
a mapping mistake; they are meant to be on **channel 2**, like every other drum track. The tables below show the
intended channel 2. (The saved template still contains channel 6 until the user remaps it.)
**Kick** is meant to have **only its fader (CC 77)**. The saved template also holds a stray note-7 mapping on Kick's on/off ("Speaker", channel 2); that is unintended and not part of the layout.

## How the sound gets in
Maschine 3 plays through multi-out pairs into audio tracks. Every drum track below takes its pair as audio input,
outputs to the `Maschine Drums` group, and monitors **In**.

### `37-Maschine 3` (the plugin)
- **Type:** MIDI
- **MIDI in:** Ext: All Ins
- **Audio out:** Main
- **Monitoring:** Auto
- Not mapped. Its own track output is silent; sound leaves through the pairs.

### `Maschine Control`
- **Type:** MIDI
- **MIDI in:** All Ins / All Channels
- **Audio out:** Main
- **Monitoring:** Auto
- Not mapped. The control-surface link.

## `Maschine Drums` (group)
- **Type:** Group
- **Audio out:** Main
- Devices: DJ Filter Soft Clip, Glue Compressor, Limiter, Microfillz, Semisubtle, Airpusher.

| Ch | Control # | Device | Control |
|---|---|---|---|
| 2 | CC 8 | Mixer | Send |
| 2 | CC 8 | Glue Compressor | Threshold |
| 2 | CC 36 | Mixer | Send |
| 2 | CC 36 | Glue Compressor | Makeup |
| 2 | CC 43 | Beat Repeat | On |
| 2 | CC 49 | DJ Filter Soft Clip (Auto Filter) | DJ filter |
| 2 | CC 75 | Beat Repeat | On |
| 2 | CC 76 | Beat Repeat | On |

### `Kick` (Maschine 3 output 7/8)
- **Type:** Audio
- **Audio in:** 37-Maschine 3 / 7/8
- **Audio out:** Group
- **Monitoring:** In

| Ch | Control # | Device | Control |
|---|---|---|---|
| 2 | CC 77 | Mixer | Volume |

### `Snare` (Maschine 3 output 9/10)
- **Type:** Audio
- **Audio in:** 37-Maschine 3 / 9/10
- **Audio out:** Group
- **Monitoring:** In

| Ch | Control # | Device | Control |
|---|---|---|---|
| 2 | CC 14 | Mixer | Send |
| 2 | CC 37 | Mixer | Send |
| 2 | CC 50 | DJ Filter Soft Clip (Auto Filter) | DJ filter |
| 2 | CC 78 | Mixer | Volume |

### `Hat` (Maschine 3 output 11/12)
- **Type:** Audio
- **Audio in:** 37-Maschine 3 / 11/12
- **Audio out:** Group
- **Monitoring:** In

| Ch | Control # | Device | Control |
|---|---|---|---|
| 2 | CC 5 | DJ Filter Soft Clip (Auto Filter) | DJ filter |
| 2 | CC 80 | Mixer | Volume |
| 2 | CC 93 | Mixer | Send |
| 2 | CC 94 | Mixer | Send |

### `Break` (Maschine 3 output 13/14)
- **Type:** Audio
- **Audio in:** 37-Maschine 3 / 13/14
- **Audio out:** Group
- **Monitoring:** In

| Ch | Control # | Device | Control |
|---|---|---|---|
| 2 | CC 29 | DJ Filter Soft Clip (Auto Filter) | DJ filter |
| 2 | CC 42 | Multiband Beat Repeat Echo (rack) | On |
| 2 | CC 46 | Beat Repeat | On |
| 2 | CC 73 | Beat Repeat | On |
| 2 | CC 74 | Beat Repeat | On |
| 2 | CC 81 | Mixer | Volume |
| 2 | CC 111 | Mixer | Send |
| 2 | CC 112 | Mixer | Send |

### `Shaker` (Maschine 3 output 15/16)
- **Type:** Audio
- **Audio in:** 37-Maschine 3 / 15/16
- **Audio out:** Group
- **Monitoring:** In

| Ch | Control # | Device | Control |
|---|---|---|---|
| 2 | CC 82 | Mixer | Volume |
| 2 | CC 10 | Mixer | Send |
| 2 | CC 12 | Mixer | Send |
| 2 | CC 13 | DJ Filter Soft Clip (Auto Filter) | DJ filter |

### `Perc` (Maschine 3 output 17/18)
- **Type:** Audio
- **Audio in:** 37-Maschine 3 / 17/18
- **Audio out:** Group
- **Monitoring:** In

| Ch | Control # | Device | Control |
|---|---|---|---|
| 2 | CC 23 | Mixer | Send |
| 2 | CC 24 | Auto Filter | DJ filter |
| 2 | CC 83 | Mixer | Send |
| 2 | CC 85 | Mixer | Volume |

## Related, not mapped
- **`maschine Bass`** (in the `Bass` group): also fed by Maschine 3, output pair 19/20.
- **Returns:** `C-Kick to Maschine` outputs **into** `37-Maschine 3` (input 11/12). `D-Maschine Cue` outputs to **Ext. Out 7/8**. Both have no devices and look silent when idle.

## Restoring and checking
- To bring drum tracks back from another set use `"$STEMCELL_HOME/tools/als_copy_tracks.py"` (Live closed): it keeps devices, clips and mappings and rewires each input to the Maschine track of the same name. Live's browser cannot import tracks from another .als.
- After any restore check each track's `Audio From` with `get_track_input_routing`: a wrong or missing pair shows as No Input. Then play Maschine and check `get_track_meters`.
