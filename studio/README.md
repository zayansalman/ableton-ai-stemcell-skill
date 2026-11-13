# Studio tools and skills

Arrangement-side tooling that sits on top of the Stemcell pipeline and the
[ableton-mcp](https://github.com/ahujasid/ableton-mcp) Remote Script. Written while rebuilding
tracks in Ableton Live 12 from stems.

Set `STEMCELL_HOME` to the folder holding these tools; the skills refer to it in their paths.

## `tools/`
- `stems_place.py`: after the resample clip is cut up in Arrangement, rebuild every stem clip under each piece, with the same play-from points.
- `drum_split.py`, `hat_split.py`: split a drum loop into kick / rest, kick / snare / hats, or hats / snare-clap, and open / closed hats. Parts sum back to the loop.
- `als_*.py`: edit a saved `.als` directly, for what Live's API cannot reach (lane automation, copying tracks between sets, MIDI mappings, extending clips, track maps). Live must be closed; each writes a new copy or a backup.
- `install_desktop_mcp.py`: register ableton-mcp with Claude Desktop.

## `skills/`
Claude Code skills (`SKILL.md` each) for the stem-sync workflow (`stemsyncsnapshot`, `stemsyncarrange`),
`drumsplit`, arrangement helpers, and per-instrument routing notes. The instrument skills describe one
person's hardware and are examples to adapt, not general guidance.

## Known limits
- Live's Python API cannot create warp markers (`Clip.add_warp_marker` accepts only Live's own marker objects), so warp points cannot be copied between clips from a script; edit the `.als` instead.
- The `.als` tools were verified on scratch copies. Open the written copy in Live and check it before relying on it.
