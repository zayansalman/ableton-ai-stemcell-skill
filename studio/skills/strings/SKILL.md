---
name: strings
description: Use for the user's Strings group (with the Pyra and Electric tracks): routing and its controller mapping.
---

# Strings

Group with an Auto Filter. Contains the MIDI tracks `24-Pyra` (Pyra, EQ Eight, Utility) and `25-Electric` (Electric).
Track names, routing and mappings are read from the user's **House Home template** (`~/Music/Ableton/User Library/Templates/House Home.als`), the source of truth. Live's API cannot show mappings; regenerate or verify with `python3 "$STEMCELL_HOME/tools/als_track_map.py" "<set>.als"`. The "NN-" prefix in some track names is Live's auto-numbering; use the name Live shows.

- **Type:** Group
- **Audio out:** Main

| Ch | Control # | Device | Control |
|---|---|---|---|
| 4 | CC 13 | Auto Filter | DJ filter |

- `Strings > 24-Pyra` and `Strings > 25-Electric`: MIDI tracks, input Ext: All Ins, output to the group. Not mapped.
- Controller channel 4 is the third bank (same CCs as Freak Out on channel 2).
