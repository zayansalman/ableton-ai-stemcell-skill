---
name: arrangement
description: Use when the user says to drag, move or put the playing clips into Arrangement view, or "take everything that is playing to arrangement". Copies every clip currently playing in Session view into Arrangement at bar 1 on its own track, and makes them the same length.
---

# Playing Session clips to Arrangement

Work from the **open set**. Re-read everything: track indices shift when a track is inserted, so look tracks up by name each time.

## 1. Find the playing clips
- `sample_track_meters` (MCP; a few samples is enough, and the clips must be playing) lists tracks with `playing_slot_index >= 0`, meaning a Session clip is playing. Or `get_track_meters` once.
- `get_track_info` per track gives the clip slots with `length` and `is_playing`. The playing slot is the one with `is_playing` true.
- Skip groups and returns (they hold no clips). Include MIDI and audio tracks alike, and the resample tracks.

## 2. Place them
- `duplicate_to_arrangement(track_index, playing_slot, 0)` for each, so all start at bar 1.
- Then `switch_to_arrangement_view`, and check each track with `get_arrangement_clips`.

## 3. Same size
- The user wants all the playing clips the **same length**, but **never repeated copies**: extend the single clip and keep its loop (see `arrangement-looping`; edits the saved .als with Live closed).
- Lengths can differ wildly (4, 32 and 876 beats in one set). **Ask the user for the target length** before extending; do not default to the longest take, and never shorten or trim a recorded take without being told.
- **Making them shorter** is possible in the live set: `trim_arrangement_clip(track_index, clip_index, end_time)` (overwrite-and-delete; keeps start and loop; refuses an audio trim if a later clip would be overwritten). **Making them longer** still needs the saved-file tool above.
- If the user only wants the clips placed for now, stop after step 2 and report the lengths.

## 4. Layout
- Keep clip-bearing tracks adjacent (group hierarchy first).
- This skill does not arm anything; use `arm-inputs` for that.
