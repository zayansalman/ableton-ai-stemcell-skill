---
name: stemsyncarrange
description: Use AFTER the user has cut up the resample clip in Arrangement ("stemsyncarrange", "I've cut it", "bring the stems"). Rebuilds every stem track under each resample piece so muting the resample sounds the same. Part 1 is `stemsyncsnapshot`.
---

# stemsyncarrange: stems follow the cuts of the resample

Part 2 of 2 of stem sync. The user kept the parts they like from the mixdown (the **resample** clip) and cut it up in Arrangement; now the **stems** (every other track with a clip) are rebuilt under each cut. No audio analysis: each cut piece knows where in the original it plays from. Works on the open set. The user works on saved copies and may revert, but say what you are about to overwrite.

## Steps
1. **Read the pieces.** MCP `arrangement_clip_ops(track_index=<resample>)` (no ops) returns every resample clip with `start`, `end` and `start_marker`. `start_marker` is where the piece plays from in the original; the stems' content lines up with it because they all began at beat 0. The resample track is the audio track whose input is **Resampling** (name varies). Show the user the table (piece, position, plays original a-b) before changing anything.
2. **Check the stems.** Stems keep their place relative to the resample, whatever they are: any clip on a stem track (any start, any length, looping or not, MIDI or audio, one clip or many) is mapped through the pieces by where it sat in the ORIGINAL timeline, so a clip that sat at 560 ends up under whichever piece plays original 560. Parts of a clip in a cut-out stretch are dropped. A track that already has its clips exactly where the pieces would put them is skipped as "already placed". A **non-looped audio clip that is not warped** cannot be mapped in beats: it is skipped with a message (warp it first); nothing changes.
3. **Run MCP `stemsync_place`** (or `only_track="<name>"` for one track; `python3 "$STEMCELL_HOME/tools/stems_place.py"` is the same code as a script). Per track: every original clip is copied to its own scratch time far past the arrangement and the originals deleted; then every part is placed in time order (copy to its place under the piece, set where it plays from, trim its end by overwriting the tail with a copy and deleting it); then the scratch copies are deleted. Looped clips get their play-from through `start_marker`, non-looped through `loop_start` (Live ignores `start_marker` on a non-looped clip; `loop_start` sets it and moves the clip's end). This **overwrites the original stem clips**, as the user wants.
4. **Verify** by re-reading each track's clips with `arrangement_clip_ops` (empty ops): every stem clip must sit where the plan puts it (the tool reports OK/CHECK per track) and play from the right place. This checks positions and markers only; **say you did not listen**, and ask the user to mute the resample and check a few seams.
5. **Lane automation (only if `stemsyncsnapshot` found some).** Live's API cannot move it, so use the saved file. Tell the user, in this order: save the set, **close Live**, tell me. Then run
   `python3 "$STEMCELL_HOME/tools/als_stem_automation.py" --old "<pre-cut.als>" --new "<the set they just saved>.als" --out "<new name>.als"`
   and tell them to **open the --out copy** (not the original; reopening drops Dyad's Push grid, see the `dyad` skill). It rebuilds each lane per piece, so nothing plays outside the pieces. It never writes in place. After they reopen, verify with `arrangement_clip_ops` that the clips are still where they should be.
6. Remind the user that the song end marker may stay far past the last piece (the scratch copies far past the arrangement); they can pull it back.

## Rules and limits
- **Automation:** moved and trimmed with the clip. **Clip envelopes** (inside the clip) are copied with it when the clip is duplicated (assumed, not yet confirmed on a real stem); **lane automation** (on the track) goes through the saved file (step 5). The tool was verified only on a synthetic lane in a scratch copy, **never opened in Live**: say so and have the user check. The user's sets so far had no lane automation.
- **MIDI trigger clips** (for example the one triggering the MicroBrute) are placed the same way; their audio is already in the resample.
- **Trimming** a clip's end is overwrite-and-delete (see the `studio-method-stems` memory). Never use `Clip.end_time` (read-only) or "looping off + end_marker" (collapses clips).
- **Gaps between pieces** are handled per piece (the piece is trimmed as soon as it is placed), but this is **untested**; check a track that has a gap.
- Pieces may be moved, reordered or duplicated: each carries its own `start_marker`.
- **Verified 2026-10-19** on a throwaway track in the live set: a looped clip and a non-looped clip (one starting before a piece, so with a non-zero play-from), 888 sample points checked against the original, 0 mismatches. Real stems: look at one and listen to a few seams.
- If a tool says unknown command, the Remote Script predates it: the user restarts Live.
- Do not delete tracks here (`cutfat` does that). Do not touch returns.
