---
name: freak
description: Use for the user's MicroFreak, the Freak Out audio track and the related Freak Midi tracks: routing and controller mappings.
---

# Freak: `Freak Out`

The Freak (MicroFreak) audio track. Devices: Gate, Utility, Shifter, Limiter, DJ Filter Soft Clip, Glue Compressor.
Track names, routing and mappings are read from the user's **House Home template** (`~/Music/Ableton/User Library/Templates/House Home.als`), the source of truth. Live's API cannot show mappings; regenerate or verify with `python3 "$STEMCELL_HOME/tools/als_track_map.py" "<set>.als"`. The "NN-" prefix in some track names is Live's auto-numbering; use the name Live shows.

- **Type:** Audio
- **Audio in:** Ext. In / 6
- **Audio out:** Main
- **Monitoring:** In

| Ch | Control # | Device | Control |
|---|---|---|---|
| 2 | CC 19 | Mixer | Send |
| 2 | CC 35 | Mixer | Send |
| 2 | CC 55 | DJ Filter Soft Clip (Auto Filter) | DJ filter |
| 2 | CC 110 | Mixer | Volume |

## Related Freak tracks (not mapped)
- `Freak Midi IN` (MIDI): in Midihub MH-2NYYE3C (D) / All Channels, out Main
- `Freak MidiOut` (MIDI): in All Ins / All Channels, out Main
- `Freak MidiOut 2` (MIDI): in All Ins / All Channels, out Main
- `Freak Midi out 2` (Audio): in Ext. In / 8, out Main
