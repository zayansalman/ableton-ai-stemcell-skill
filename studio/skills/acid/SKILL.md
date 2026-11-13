---
name: acid
description: Use for the user's Slippery Slope track, the acid instrument (Sting 2): its routing and controller mappings.
---

# Acid: `Slippery Slope`

The acid line. Devices: Sting 2 (Max for Live) and an Instrument Rack.
Track names, routing and mappings are read from the user's **House Home template** (`~/Music/Ableton/User Library/Templates/House Home.als`), the source of truth. Live's API cannot show mappings; regenerate or verify with `python3 "$STEMCELL_HOME/tools/als_track_map.py" "<set>.als"`. The "NN-" prefix in some track names is Live's auto-numbering; use the name Live shows.

- **Type:** MIDI
- **MIDI in:** Ext: All Ins
- **Audio out:** Main
- **Monitoring:** Auto

| Ch | Control # | Device | Control |
|---|---|---|---|
| 3 | CC 29 | Auto Filter | DJ filter |
| 3 | CC 81 | Mixer | Volume |
| 3 | CC 111 | Mixer | Send |
| 3 | CC 112 | Mixer | Send |

- Ch 3 is the controller's second bank: the same CC numbers are used on channel 2 for the drum tracks (e.g. volume CC 81 is Break on ch 2, Slippery Slope on ch 3).
- Sting takes over the Push cleanly, unlike Dyad (the user's own notes in `Dyad Troubleshooting/Dyad Info.md` use it as the good example).
