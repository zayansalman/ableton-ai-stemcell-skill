# Studio tools and skills

Arrangement-side tooling that sits on top of the Stemcell pipeline and the
[ableton-mcp](https://github.com/ahujasid/ableton-mcp) Remote Script. Written while rebuilding
tracks in Ableton Live 12 from stems.

Set `STEMCELL_HOME` to this `studio/` folder; the skills refer to `$STEMCELL_HOME/tools/...`.

## Tools

| Tool | What it does | Needs |
|---|---|---|
| `hat_split.py` | Split a hat stem into open and closed hats by ring time. Parts sum back to the input. | numpy, soundfile |
| `drum_split.py` | Split a drum loop into kick / rest, kick / snare / hats, hats / snare-clap, or your own groups. Parts sum back to the loop. | torch, numpy, soundfile, plus an external DrumSep wrapper (`PROLINK_DEVICE_DIR`) and checkpoint (`DRUMSEP_CKPT`) |
| `als_copy_tracks.py` | Copy tracks between two `.als` sets, keeping devices, clips, mappings and routing. | standard library |
| `als_build_arrangement.py` | Lay Session clips onto the Arrangement as one extended clip per block. | standard library |
| `als_extend_clips.py` | Extend looped Arrangement clips the way dragging the right edge does. | standard library |
| `als_stem_automation.py` | Carry track lane automation from a pre-cut set onto the stems of the cut-up set. | standard library |
| `als_midi_mappings.py` | List the MIDI controller mappings stored in a set. | standard library |
| `als_apply_midi_mappings.py` | Copy a group's MIDI mappings from one set onto another. | standard library |
| `als_track_map.py` | Write a Markdown map of a set: tracks, routing and every controller mapping. | standard library |
| `stems_place.py` | After the resample is cut up in Arrangement, rebuild every stem clip under each piece. | Live running with an ableton-mcp build that includes `stemsync.py` and `arrangement_clip_ops` (`ABLETON_MCP_DIR`) — not in upstream ableton-mcp |
| `install_desktop_mcp.py` | Register ableton-mcp with the Claude Desktop app (macOS). | `uv` on PATH, `ABLETON_MCP_DIR` |

Every tool prints its full usage with `--help` (or in its docstring).

### Working on `.als` files safely
- Close Live first. Live keeps the set in memory and will overwrite file edits when it saves.
- The tools write a new copy or keep a backup; they never silently overwrite your only copy.
- They were verified on scratch copies. Open the written copy in Live and check it before relying on it.

## Skills

Claude Code skills (`skills/<name>/SKILL.md`). Copy the ones you want into `~/.claude/skills/`.

- **Workflow:** `stemsyncsnapshot`, `stemsyncarrange` (stem sync), `drumsplit`, `arrangement`,
  `arrangement-looping`, `arm-inputs`, `cutfat`, `prepstudio`, `drum-rack-pad-tracks`.
- **Instrument notes** (`acid`, `bass`, `cue`, `dyad`, `freak`, `maschine-drums`, `namratac-granulator`,
  `retur`, `strings`): describe one person's hardware, template and controller mappings. They are
  examples to adapt, not general guidance. Regenerate yours with `als_track_map.py`.

## Known limits
- Live's Python API cannot create warp markers (`Clip.add_warp_marker` accepts only Live's own marker objects),
  so warp points cannot be copied between clips from a script; edit the `.als` instead.
- `hat_split.py` is an energy-decay heuristic, not a model: check the hit list it prints.

## Tests
`tests/test_studio_tools.py` covers the parts that need no Live, model or external checkout
(`.als` parsing, mapping scan, hat split sums back to the input).
