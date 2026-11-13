"""List the MIDI-controller mappings stored in an Ableton Live set (.als).

    python3 als_midi_mappings.py SET.als                 # grouped by track
    python3 als_midi_mappings.py SET.als --by-channel    # grouped by controller channel
    python3 als_midi_mappings.py SET.als --json          # raw rows

A control is mapped when its <KeyMidi> block has NoteOrController >= 0. Channels
are printed the way Live's UI shows them (stored value + 1).

Stored channel 16 (shown as 17) is not a real MIDI channel. It only appears on
controls inside racks and presets (Drum Rack pads, Drift/Operator/Sting presets),
so it is most likely the preset's own macro wiring rather than your controller.
Those rows are flagged "preset" and left out unless --all is given.

Max for Live parameters (Dyad, Variations, Retur ...) have no readable name in the
file; they show as "Timeable". Their CC numbers are still exact.
"""

from __future__ import annotations

import argparse
import collections
import gzip
import json
import xml.etree.ElementTree as ET

TRACK_TAGS = ("AudioTrack", "MidiTrack", "GroupTrack", "ReturnTrack", "MainTrack", "PreHearTrack")
PRESET_CHANNEL_DISPLAY = 17


def group_paths(root) -> dict[str, str]:
    """Track node Id -> 'Group > Subgroup > Track', from TrackGroupId links."""
    info = {}
    tracks = root.find("LiveSet/Tracks")
    for t in tracks if tracks is not None else []:
        name = t.find("Name/EffectiveName")
        gid = t.find("TrackGroupId")
        info[t.get("Id")] = (name.get("Value") if name is not None else "?",
                             gid.get("Value") if gid is not None else "-1")
    paths = {}
    for tid in info:
        chain, cur = [], tid
        while cur in info and cur not in chain:
            chain.append(cur)
            cur = info[cur][1]
        paths[tid] = " > ".join(info[c][0] for c in reversed(chain))
    return paths


def scan(path: str) -> list[dict]:
    root = ET.fromstring(gzip.open(path).read())
    parent = {c: p for p in root.iter() for c in p}
    paths = group_paths(root)
    rows = []
    for kb in root.iter("KeyMidi"):
        number = int(kb.find("NoteOrController").get("Value"))
        if number < 0:
            continue
        channel = int(kb.find("Channel").get("Value")) + 1
        owner = parent[kb]
        device = track = kind = tpath = None
        node = owner
        while node is not None:
            if device is None and parent.get(node) is not None and parent[node].tag == "Devices":
                device = node
            if node.tag in TRACK_TAGS:
                name = node.find("Name/EffectiveName")
                track, kind = (name.get("Value") if name is not None else "?"), node.tag
                tpath = paths.get(node.get("Id"), track) if node.tag != "ReturnTrack" else track
                break
            node = parent.get(node)
        label = owner.tag
        for key in ("Name", "ParameterName", "UserName"):
            e = owner.find(key)
            if e is not None and e.get("Value"):
                label += f" [{e.get('Value')}]"
                break
        dev_name = "(mixer)"
        if device is not None:
            user = device.find("UserName")
            dev_name = device.tag + (f" {user.get('Value')}" if user is not None and user.get("Value") else "")
        rows.append(dict(track=track or "?", path=tpath or track or "?", kind=kind or "?", device=dev_name, control=label,
                         channel=channel, number=number,
                         type="note" if kb.find("IsNote").get("Value") == "true" else "CC",
                         preset=channel == PRESET_CHANNEL_DISPLAY))
    return rows


def markdown(rows: list[dict], source: str) -> str:
    """One section per track, in set order, with group path and every mapping."""
    order, groups = [], collections.defaultdict(list)
    for r in rows:
        k = (r["kind"], r["path"])
        if k not in groups:
            order.append(k)
        groups[k].append(r)
    out = [f"Source: `{source}`. Channels as Live shows them. CC unless noted.", ""]
    for kind, path in order:
        rs = sorted(groups[(kind, path)], key=lambda r: (r["channel"], r["number"]))
        label = {"ReturnTrack": "Return", "MainTrack": "Main"}.get(kind, "")
        out.append(f"### {path}" + (f"  ({label})" if label else ""))
        out.append("| Ch | # | Device | Control |")
        out.append("|---|---|---|---|")
        for r in rs:
            kindmark = "note " if r["type"] == "note" else ""
            out.append(f"| {r['channel']} | {kindmark}{r['number']} | {r['device']} | {r['control']} |")
        out.append("")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("als")
    ap.add_argument("--by-channel", action="store_true")
    ap.add_argument("--all", action="store_true", help="include preset-internal (channel 17) rows")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--markdown", action="store_true", help="per-track tables with group paths")
    a = ap.parse_args()

    rows = scan(a.als)
    controller = [r for r in rows if not r["preset"]]
    shown = rows if a.all else controller
    if a.json:
        print(json.dumps(shown, indent=1))
        return
    if a.markdown:
        print(markdown(shown, a.als))
        return
    print(f"{a.als}\n  {len(controller)} controller mappings, {len(rows) - len(controller)} preset-internal")
    key = (lambda r: f"ch{r['channel']}") if a.by_channel else (lambda r: f"{r['kind'][:5]} {r['track']}")
    groups = collections.defaultdict(list)
    for r in shown:
        groups[key(r)].append(r)
    for g, rs in sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        print(f"\n{g}  ({len(rs)})")
        for r in sorted(rs, key=lambda r: (r["channel"], r["number"])):
            where = f"{r['track'][:22]:22s} " if a.by_channel else ""
            print(f"  ch{r['channel']:<2d} {r['type']:4s} {r['number']:3d}  {where}{r['device'][:30]:30s} {r['control']}")


if __name__ == "__main__":
    main()
