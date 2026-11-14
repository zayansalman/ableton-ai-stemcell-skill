# `/dissect` — Claude Code skill

A [Claude Code](https://claude.com/claude-code) skill that drives Stemcell end to end: run the pipeline, read `report.json`, identify the gear behind each sound, build Splice queries, generate melodies/vocal-chops, and rebuild the track in Ableton — from a single prompt like *"dissect this track"* or *"find sounds like this song"*.

## Install

Copy the skill into your Claude Code skills directory and register a trigger:

```bash
mkdir -p ~/.claude/skills/dissect
cp SKILL.md ~/.claude/skills/dissect/SKILL.md
```

Then add a pointer to your `~/.claude/CLAUDE.md` so it triggers reliably:

```markdown
# dissect
- **dissect** (`~/.claude/skills/dissect/SKILL.md`) — dissect an audio file into stems/tempo/key/drums/MIDI, source on Splice, rebuild in Ableton. Trigger: `/dissect`
When the user types `/dissect`, invoke the Skill tool with `skill: "dissect"` before doing anything else.
```

## Prerequisites

- **Stemcell** installed and `bootstrap`-ed (see the repo root README).
- Optional: the [`ableton-mcp`](https://github.com/ahujasid/ableton-mcp) connector (to rebuild in Live) and a Splice MCP connector (to source samples).

## Paths

`SKILL.md` runs `uv run stemcell` from `$STEMCELL_REPO` (default `~/projects/ableton-ai-stemcell-skill`). If you cloned elsewhere, set `STEMCELL_REPO` to your clone, e.g. `export STEMCELL_REPO=~/code/ableton-ai-stemcell-skill` in your shell profile. The skill body documents the full workflow, the honest limitations, and the gear-ID and vocal-chop flows.
