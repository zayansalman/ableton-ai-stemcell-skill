---
name: stemsyncsnapshot
description: Use BEFORE the user cuts up the resample clip ("stemsyncsnapshot", "I'm about to cut", "take the snapshot"). Saves a record of the whole Arrangement, asks the user to save the set, and checks it for lane automation. The second half is the `stemsyncarrange` skill.
---

# stemsyncsnapshot: prepare before cutting the resample

Part 1 of 2 of stem sync (the user cuts up the resample clip, then the stems are rebuilt under each cut: part 2 is `stemsyncarrange`). Run this when the user says so, after they have arranged their tracks. Work on the open set.

## Steps
1. **Take the snapshot.** MCP `save_timeline_snapshot` writes every Arrangement clip (track, start-end, loop, warp, file, envelopes) to `snapshots/timeline-YYYYMMDD-HHMMSS.json` in the project and returns a short table. The **newest** file is the current one; older ones are leftovers. Show the user the table and flag clips that run past the end of the others, tracks with no clip, and clips with envelopes. A snapshot is a record only; it cannot restore the arrangement.
2. **Ask the user to save the set (Cmd+S)**, and a copy if they like. I cannot save it myself (no API for it, and no computer use). That saved `.als` is their revert point and the only place Arrangement **lane automation** exists for me. Note its path.
3. **Check for lane automation:** `python3 "$STEMCELL_HOME/tools/als_stem_automation.py" --old "<saved.als>" --check` prints which tracks have lane automation, or "none". Tell the user the result. Clip envelopes (automation inside a clip) are not listed; they travel with the clip.
4. Tell the user to go ahead and cut, and to say "I've cut it" (or `/stemsyncarrange`) afterwards. If lane automation was found, remind them they will be asked to save and close Live in part 2.

## Notes
- The resample track is the audio track whose input is **Resampling** (its name varies; it was once a typo, "WHoel Resample").
- Retake the snapshot if the user edits the arrangement again before cutting.
- Do not change anything in the set in this step. No tracks deleted, no clips moved.
