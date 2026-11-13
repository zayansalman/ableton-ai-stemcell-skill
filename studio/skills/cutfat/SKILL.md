---
name: cutfat
description: Use when the user says "cutfat", cut the fat, or wants every empty/unused track removed from the open Live set. Deletes every track that has no clip in Arrangement (Maschine included, Dyad and returns kept), removes empty groups, and ungroups lone tracks, after showing the preview and getting a yes.
---

# cutfat: remove every track with no Arrangement clip

The user wants the set trimmed to only what is on the Arrangement. **Any track with no clip in Arrangement view is fat**, including the Maschine tracks (`Maschine Drums` pad tracks, `Maschine 3`, `Maschine Control`): what is needed from Maschine is usually mixed down to audio by then. This overrides the older "keep Maschine for live playability" note for this skill only.

Deleting is destructive, so the order is fixed: **find, preview, back up, confirm, delete, tidy groups, report**.

## 1. Find the fat
- Work from the open set and re-read it; indices shift. Use MCP `get_track_meters` once for the track list with `group` and `is_group`.
- For every non-group track call `get_arrangement_clips(track_index)`. `clip_count == 0` means fat. Ignore Session clips, meters and arm state: a track that is armed or sounding is still fat if the Arrangement has nothing on it.
- **Groups** hold no clips. A group is kept if **any** child is kept; a group whose children are all fat is fat. Deleting a group deletes every child.
- **Keep regardless:**
  - **Return tracks** (A-Romb, B-Retur, C, D...): never touch them. The `retur` audio track that records B-Retur is return-capture, so keep it too.
  - **Dyad, intact**: keep the `DYAD` group, `Flerp`, `melodic`, **and the Dyad MIDI instrument tracks** (e.g. `30-Dyad`, `34-Dyad`; Live renumbers the `NN-` prefix) even with no Arrangement clip. The user may go back to sound-design, and they feed the kept audio tracks (Low, Top, the Audio 3 tracks). Dyad is the only instrument kept this way; Maschine and everything else goes.

## 2. Preview (no changes yet)
Show what stays (with clip counts) and what goes, by group, with Maschine flagged. Also list **lone-child groups** (see step 5) and any **armed** track that would go. Call `delete_tracks` **without** `confirm` for the Live-side preview. Entries need both the index and the exact current name.

## 3. Back up
Live cannot undo this through the API. Ask the user to **save the set (and a copy) first**, or confirm they have a backup. Do not delete until they say yes in chat.

## 4. Delete
After the explicit yes: `delete_tracks(tracks=[{index,name},...], confirm=true)`.
- **List a group before its children.** The Remote Script deletes groups first (verified 2026-10-18); a group takes its children with it. Before this, deleting a group's last child alone failed with "Couldn't delete track".
- Delete in **small batches (about 5)**. After ANY error stop, re-read the full list, and rebuild from names: a failed call can leave some tracks deleted and shift every index (and renumber `NN-` names).
- Use MCP `delete_tracks`: it deletes one track per call internally (groups first, re-finding each track after Live renumbers `NN-` names, stopping if the number of returns changes). A raw bulk call to the Remote Script failed once on 2026-10-18. After ANY error stop, re-read the list and rebuild from names.
- After each batch check the returns count did not change (a past run ended with 2 returns instead of 4; the cause was never found).

## 5. Tidy groups (lone children)
**Do not finish the run with a lone-child group still in the set.** The user has had to ungroup these by hand twice (Perc, then Hat in `Maschine Drums`). After the deletes, check every group; if one has a single child, ungrouping it is part of the job. Try the computer-use route below first; if that is blocked, make it the **first line** of the final report, not a footnote.

A group with a **single child** is pointless: the user wants it ungrouped (e.g. `Perc` left alone inside `Maschine Drums`). Exceptions: `DYAD` (holds Flerp and melodic) and any group with 2+ children stay.
- **There is no ungroup command in the Live API or ableton-mcp.** Do not delete the group (that deletes the child, and a lone child usually has the clip).
- Tell the user to select the group and press **Cmd+Shift+G** (Edit > Ungroup Tracks). **Do not use computer use** (the user finds it clunky, and Live's full-screen Space makes the screen stale); there is no ungroup command in the Live API or ableton-mcp.
- After it, re-read the track list and confirm the group is gone.

## 6. Report
Re-read the list; report what was removed and what remains. Remind the user that arming is lost on deleted tracks (re-run `/arm-inputs`).
