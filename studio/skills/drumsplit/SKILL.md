---
name: drumsplit
description: Use when the user wants a drum loop/clip in the open Live set split into parts ("drum split", "drum separation on the 10th track", "split the drums on track N", "<top> split this"). Default is the GRAB split, KICK and REST OF DRUMS; with a context tag like <top> (a top loop with hats and snare/clap) it gives HATS and SNARE_CLAP instead. Each part goes on its own track as a warped, looped clip of the same length as the original.
---

# drumsplit: split a drum loop the way GRAB does, and bring it in warped and looped

Tool: `$STEMCELL_HOME/tools/drum_split.py` (DrumSep, from the Prolink Sync repo's `device/drumsplit.py`). Run it with the Prolink Grab venv python:

```bash
"$HOME/Library/Application Support/Prolink Grab/venv/bin/python" \
  "$STEMCELL_HOME/tools/drum_split.py" "<loop.wav>" "<out dir>" [--mode grab|top|kit] [--group NAME=inst,inst ...]
```

## What the user can add: context tags
The user may add context in `<...>` tags (or the same as JSON, e.g. `{"mode":"top"}`) anywhere in the request. Read them before choosing the mode:

| tag | mode | result |
|---|---|---|
| none, `<kick>`, `<grab>` | `--mode grab` (default) | **Kick** and **Rest of Drums**, exactly what GRAB produces (kick-transient boost keeps the kick's top end; verified identical to the stems GRAB writes). kick + rest = the loop. |
| `<top>`, `<top loop>`, `<hats>` | `--mode top` | **Hats** and **Snare-Clap** for a loop with no kick: hats = hh, ride, crash, kick, toms (the "rest" always goes with the hats, never the snare/clap), snare_clap = snare. The two add back up to the loop (error ~1e-7). |
| `<groups name=inst,inst; name=inst>` | `--group name=inst,inst ...` | Their own groups. Instruments DrumSep gives: `kick snare toms hh ride crash`. Any instrument not named joins the last group, so the groups still sum to the loop. |
| `<track=N>`, `<clip=name>` | | which track/clip (N is the number in the track name, i.e. index + 1). |
| `<note ...>` | | free-form context: use it, e.g. to pick a mode when the tag says "top loop" in words. |

No tag but the clip name says top / hat / perc / shaker loop? Say which mode you picked and why in the report; don't ask. Tags the skill does not know: tell the user and use the default.

## Steps
1. **Find the clip.** `get_track_meters` for the track list (the number in the user's words is the `NN-` prefix in the name = index + 1), then `get_track_info(index)` for the clip name and its **length in beats**. Keep both.
2. **Find the file.** The API gives no path: `mdfind -name "<clip name>"` (usually `~/Music/Ableton/User Library/Samples/Splice/<name>.wav`; ignore `.asd`). More than one match: ask which. Never modify the source file. The input must be 44.1 kHz.
3. **Split** into a NEW folder `~/Documents/Samples/Drum Splits/<clip name>/` (add ` v2`... when a clip in the set already uses files there; never overwrite those). Run it while Live is stopped. Check `sum_error` is tiny; `rms` ~40 dB below the other part means stray bits: mention it. (Grab mode on a loop with no kick gives an almost silent Kick: that is expected, say so and suggest `<top>`.)
4. **Bring it in.** `create_audio_track` per part (index -1; `NN-Audio` in the answer = index NN-1), `create_audio_clip(track, 0, path)`, `set_track_name`. Then **always** `set_clip_warp_loop(slots, warp_mode="beats", beats=<original clip length>)`: warped AND looped, the same length as the original clip. Never leave imported clips unwarped or unlooped. Confirm with `get_track_info` that each new clip has the original's length.
5. **Report**: the parts, the folder, what the mode was and why, and that the parts sum to the original. Don't mute or remove the source track unless asked.

## Kick, snare, hats: `--mode kit` (user's preferred full-kit split, 2026-10-30)
For "split the kick, snare and hats" of a full drum loop use `--mode kit` (not `--group` with kick/snare/hh: that masks the mix and was audibly worse). It gives **KICK, SNARE, HATS** (open and closed together; the user preferred that to separate open/closed stems), which add back up to the loop (error ~1e-7):
- **KICK** is rebuilt from the loop's own hits: the median of the "clean" hits (nothing else on the beat) laid on every hit. A mask lets a snare/clap on the same beat leak into the kick, which made its top end swing between hits ("phasing"). Measured: top-end spread 18 dB with the model kick, ~1 dB rebuilt. A kick hit cut off by the loop start is handled. No repeatable kick: falls back to the GRAB kick step.
- **SNARE / HATS**: DrumSep runs a second time on the loop with the kick removed. The snare part is then gated to the neighbourhood of real snare hits, found by TONE (average frequency of the first 80 ms below `--snare-centroid`, default 5200 Hz; clap/snare ~4-5 kHz, leaked hats 5.7-8 kHz), not by loudness: leaked open hats were as loud as the snare. Everything of the snare part outside those windows (`--tail` 150 ms) moves to the HATS. Measured: hat leakage in the snare stem fell to silence at every hat hit.
- **The kick must not carry anything that is not the kick** (found 2026-10-30): a median of clean hits also keeps an off-beat open hat that follows every kick, so the template keeps the kick's low end (< 400 Hz) for the whole window but its top end only until the click has decayed (`top_end_kept_ms` in the output). Measured: open-hat energy in the kick fell from +14 dB to below -23 dB. Anything the kick does not own is left in the HATS.
- **If the user approves one part, keep it:** build the others around it (e.g. HATS = loop - new kick - the approved SNARE file) so the three still sum; never re-run a mode that would change the approved part. Hats can exceed full scale: the tool writes a part as 32-bit float when 24-bit would clip.
- The tool prints the kick hits it used and each snare candidate's centroid: show the user that list, and say it is a heuristic (a hat under a snare hit stays in the snare; a very different loop may need `--snare-centroid` / `--tail`). Always listen.
- Do NOT overwrite files a clip uses: write to a new ` vN` folder, then swap the clips (`delete_clip`, `create_audio_clip`, `set_clip_warp_loop`) in the user's own tracks, keeping their grouping.
- Open vs closed hats separately (only if asked): `tools/hat_split.py` on the HATS file (ring time >= 60 ms = open). Heuristic; the user found the plain split worse than hats together.

## If a tool says `Ableton Remote Script missing capability ...`
Live loaded an older Remote Script than the one on disk (`~/Music/Ableton/User Library/Remote Scripts/AbletonMCP`). **No Live restart needed** (verified 2026-10-24): ask the user to open Preferences > Link, Tempo & MIDI, set the AbletonMCP control surface slot to None and back to AbletonMCP. **Then call `get_remote_script_info` once**: the MCP server caches its capability check and keeps failing until that call refreshes it (the first calls after the reload still said "missing capability"; after `get_remote_script_info` showed `up_to_date: true` everything worked). Do not click through Live with computer use (the user finds it clunky; Live's full-screen Space makes screenshots stale). Meanwhile do the split and file work, and leave the Live steps for after the reload, saying so.

## Don't
- Don't overwrite or delete the source sample or files a clip in the set uses; old split files go to the Trash only after their clips are gone.
- Don't run Demucs first: the clip is already drums, DrumSep works on it directly.
