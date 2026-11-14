---
name: retur
description: Use for the user's dub delay, the B-Retur return (Retur device) and the "retur" audio track that records it: routing, controller mappings, capturing it, and the other return tracks.
---

# Retur (dub delay)

`B-Retur | Variations | Glue Compressor | Limiter | EQ Eight` is the user's **dub delay** return. Devices: Retur, Variations, Glue Compressor, Limiter, EQ Eight.
Track names, routing and mappings are read from the user's **House Home template** (`~/Music/Ableton/User Library/Templates/House Home.als`), the source of truth. Live's API cannot show mappings; regenerate or verify with `python3 "$STEMCELL_HOME/tools/als_track_map.py" "<set>.als"`. The "NN-" prefix in some track names is Live's auto-numbering; use the name Live shows.

## The return
- **Type:** Return
- **Audio out:** Master
- The Max for Live mappings below belong to the Retur and/or Variations devices; the file does not say which.

| Ch | Control # | Device | Control |
|---|---|---|---|
| 2 | CC 20 | Retur / Variations (Max for Live) | (Max for Live control) |
| 2 | CC 39 | Retur / Variations (Max for Live) | (Max for Live control) |
| 2 | CC 56 | Retur / Variations (Max for Live) | (Max for Live control) |
| 2 | CC 84 | Mixer | Volume |
| 3 | CC 60 | Retur / Variations (Max for Live) | (Max for Live control) |
| 3 | CC 92 | Retur / Variations (Max for Live) | (Max for Live control) |

## The `retur` audio track (records the return)
- **Type:** Audio
- **Audio in:** B-Retur | Variations | Glue Compressor | Limiter | EQ Eight / Post Mixer
- **Audio out:** Main
- **Monitoring:** Off
- It is an **audio track**, not a return. Audio From is **B-Retur, Post Mixer**, monitoring **Off** (intended). It has **no mappings**; the return does.
- Its source is the B-Retur return's track id, so a checker that only looks at ordinary tracks will wrongly call that route "dangling".
- To capture the return: arm `retur`, record, then disarm.

## Other returns
- `A-Romb` (device Romb): output Master, not mapped.
- `C-Kick to Maschine` and `D-Maschine Cue`: see the `maschine-drums` skill.

## Tool limits
- ableton-mcp has **no command to create or delete return tracks**; if the user wants returns removed they do it by hand.
- `get_track_meters` reports returns too. A return can be fed by another track, so quiet is not proof it is unused.
- For a project where the user says "no need for return tracks": don't create or route to them, and skip A-Reverb / B-Delay / Main when listing input channels.
