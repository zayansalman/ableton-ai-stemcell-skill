---
name: bass
description: Use for the user's MicroBrute bass (the MicroBrute audio track): its audio input, routing and controller mappings.
---

# Bass: `MicroBrute`

The MicroBrute hardware synth, as an audio track. Devices: Gate, Glue Compressor, EQ Eight, Auto Filter, Tuner.
Track names, routing and mappings are read from the user's **House Home template** (`~/Music/Ableton/User Library/Templates/House Home.als`), the source of truth. Live's API cannot show mappings; regenerate or verify with `python3 "$STEMCELL_HOME/tools/als_track_map.py" "<set>.als"`. The "NN-" prefix in some track names is Live's auto-numbering; use the name Live shows.

- **Type:** Audio
- **Audio in:** Ext. In / 5
- **Audio out:** Main
- **Monitoring:** In

| Ch | Control # | Device | Control |
|---|---|---|---|
| 3 | CC 10 | Mixer | Send |
| 3 | CC 12 | Mixer | Send |
| 3 | CC 13 | Auto Filter | DJ filter |
| 3 | CC 82 | Mixer | Volume |

- The unmapped `td3` audio track also reads **Ext. In / 5** (the same input as MicroBrute).
- Channel 3 is the controller's second bank; the same CCs are on channel 2 for the drum tracks and Shaker (sends 10 / 12, filter 13, volume 82).
