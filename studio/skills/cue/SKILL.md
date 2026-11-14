---
name: cue
description: Use for the user's Max for Live cue device and its controller mappings. It is saved on the Main (master) track, the Main bus.
---

# Cue (Max for Live cue device)

The user's **Max for Live cue device**. It is **saved on the Main bus**, the Main (master) track, not on a separate track.

**4 mappings, all on controller channel 3:**

| Ch | Control # | Device |
|---|---|---|
| 3 | CC 101 | cue device (Max for Live) |
| 3 | CC 102 | cue device (Max for Live) |
| 3 | CC 103 | cue device (Max for Live) |
| 3 | CC 104 | cue device (Max for Live) |

The file stores no control names for it, so don't invent any; the channel and CC numbers are exact.

Read from the user's Verse set and `DJM Home` template (`~/Music/Ableton/User Library/Templates/DJM Home.als`). To check or regenerate, run `python3 "$STEMCELL_HOME/tools/als_midi_mappings.py" "<set>.als"` and look under the Main track.
