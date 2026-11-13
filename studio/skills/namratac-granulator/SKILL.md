---
name: namratac-granulator
description: Use for the user's Namratac Granulator track (26-Namratac Granulator): its routing and controller mappings.
---

# Namratac Granulator: `26-Namratac Granulator`

MIDI track with Arpeggiator, **Namratac Granulator** (Max for Live) and Auto Filter.
Track names, routing and mappings are read from the user's **House Home template** (`~/Music/Ableton/User Library/Templates/House Home.als`), the source of truth. Live's API cannot show mappings; regenerate or verify with `python3 "$STEMCELL_HOME/tools/als_track_map.py" "<set>.als"`. The "NN-" prefix in some track names is Live's auto-numbering; use the name Live shows.

- **Type:** MIDI
- **MIDI in:** Ext: All Ins
- **Audio out:** Main
- **Monitoring:** Auto

| Ch | Control # | Device | Control |
|---|---|---|---|
| 4 | CC 19 | Mixer | Send |
| 4 | CC 35 | Mixer | Send |
| 4 | CC 55 | Auto Filter | DJ filter |
| 4 | CC 59 | Namratac Granulator (Max for Live) | (Max for Live control) |
| 4 | CC 91 | Namratac Granulator (Max for Live) | (Max for Live control) |
| 4 | CC 110 | Mixer | Volume |

- Controller **channel 4** is the third bank: the same CCs are used on channel 2 for Freak Out (sends 19 / 35, DJ filter 55, volume 110).
