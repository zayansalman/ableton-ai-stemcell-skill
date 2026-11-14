---
name: arrangement-looping
description: Use when the user wants clips in Arrangement view to be longer, matched to the longest clip, or looped. Never fake it with repeated copies; extend the single clip.
---

# Looping / extending arrangement clips

**The user does not want duplicated copies of a loopable clip.** Repeating a clip with `duplicate_to_arrangement`
(what was done once on 2026-10-13) is wrong: it makes several clips where one extended clip is wanted. Extend the clip.

## How Live stores an extended clip (verified on 303 clips the user extended by hand, plus the live set)
One clip, loop unchanged, only the right edge moves. In the .als: `CurrentStart` / `CurrentEnd` are the clip's
arrangement edges; the `<Loop>` block (`LoopStart`, `LoopEnd`, `OutMarker`, `LoopOn`) is the loop and stays put.
Example from the user's own set: `5-Operator` starts 0, ends 32, loop 0-8, looping on. In the live API that is
`end_time` 32 with `loop_start` 0, `loop_end` 8, `looping` true, `length` 8.

## What works now: edit the saved set (Live CLOSED)
```
python3 "$STEMCELL_HOME/tools/als_extend_clips.py" "<set>.als" --out "<new>.als" --length longest    # or a beat count
python3 "$STEMCELL_HOME/tools/als_extend_clips.py" "<set>.als" --out "<new>.als" --length 32 --tracks Low Top
```
- Only looped clips shorter than the target move; each stops at the next clip on its track; never writes in place.
- Tested on a scratch copy: only `CurrentEnd` values changed, all Loop blocks and everything else byte-identical, XML well-formed.
  **Not yet opened in Live**, so say that and have the user open the new file, not their original.
- The user must save the set first (the arrangement they see is the open set, not the file) and reopen the new file afterwards.
  Reopening drops Dyad's Push grid (see the `dyad` skill).

## What is NOT known: doing it through the live API
`Clip.end_time` is documented read-only. `end_marker`, `loop_end`, `loop_start`, `looping` are settable, but nothing documents
whether they change an arrangement clip's right edge. `loop_end` changes the loop (the content), not the edge, so it is probably
the wrong lever. Untested idea: turn looping off, set `end_marker` to the target, restore the loop, turn looping on.
**Do not test on the user's open project.** Test only in a throwaway blank set the user opens for it: place one 8-beat looped
clip, try the idea, re-read `end_time`, and record the result here. Until proven, use the .als method above.

References: [Clip class (Cycling '74 LOM)](https://docs.cycling74.com/apiref/lom/clip/).
