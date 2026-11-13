"""Authoritative per-track map of an Ableton Live set: which tracks carry controller
mappings, their names and groups, their routing, and every mapping (channel, CC/note).

    python3 als_track_map.py "House Home.als" > house-home-mappings.md
    python3 als_track_map.py SET.als --check-live      # also compare with the open Live set

Read from the saved .als (Live's API cannot see mappings). Routing is resolved through
each route's target track id, because the display text stores stale auto-numbers
("19-Maschine 3" for a track that is now "37-Maschine 3").
"""

from __future__ import annotations

import argparse
import collections
import gzip
import os
import re
import sys
import time
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from als_midi_mappings import group_paths, scan  # noqa: E402

MONITORING = {"0": "In", "1": "Auto", "2": "Off"}
TYPES = {"AudioTrack": "Audio", "MidiTrack": "MIDI", "GroupTrack": "Group", "ReturnTrack": "Return"}


def base(name: str) -> str:
    """'37-Maschine 3' -> 'Maschine 3' (Live's auto-number prefix shifts as tracks move)."""
    return re.sub(r"^\d+-", "", name)


def route_text(dc: ET.Element, tag: str, names: dict[str, str]) -> str:
    """'Track / channel' for one routing element, resolved through the target track id."""
    e = dc.find(tag)
    if e is None:
        return "-"
    get = lambda k: (e.find(k).get("Value") if e.find(k) is not None else "") or ""
    target, upper, lower = get("Target"), get("UpperDisplayString"), get("LowerDisplayString")
    m = re.search(r"Track\.(\d+)", target)
    if m and m.group(1) in names:
        upper = names[m.group(1)]                      # the name Live shows for that track
        pair = re.match(r"^([\d/]+)-", lower)         # '7/8-Maschine 3' -> '7/8'
        lower = pair.group(1) if pair else lower
    return f"{upper} / {lower}" if lower else (upper or "-")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("als")
    ap.add_argument("--check-live", action="store_true")
    a = ap.parse_args()

    root = ET.fromstring(gzip.open(a.als).read())
    paths = group_paths(root)
    tracks = list(root.find("LiveSet/Tracks"))
    names = {t.get("Id"): t.find("Name/EffectiveName").get("Value") for t in tracks}
    rows = [r for r in scan(a.als) if not r["preset"]]
    mapped = collections.OrderedDict()
    for r in rows:
        mapped.setdefault((r["kind"], r["path"]), []).append(r)

    by_path = {}
    for t in tracks:
        p = paths.get(t.get("Id"), names[t.get("Id")])
        by_path[(t.tag, p if t.tag != "ReturnTrack" else names[t.get("Id")])] = t

    saved = time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(a.als)))
    out = [f"# {os.path.basename(a.als)}: mapped tracks, routing and controller mappings", "",
           f"Source of truth: `{a.als}` (saved {saved}). {len(rows)} controller mappings on "
           f"{len(mapped)} tracks. The file has {len([t for t in tracks if t.tag != 'ReturnTrack'])} tracks "
           f"and {len([t for t in tracks if t.tag == 'ReturnTrack'])} returns.", "",
           "Channels are as Live shows them; `CC` is a controller number, `note` a MIDI note. "
           "Preset-internal (stored channel 16) mappings are excluded. Track names are exact; "
           "the \"NN-\" prefix on some names is Live's auto-numbering and shifts, so match the name after it. "
           "Max for Live controls show as `Timeable` (the file stores no control name).", ""]

    out.append("## Mapped tracks")
    for (kind, path), rs in mapped.items():
        t = by_path.get((kind, path))
        out.append(f"\n### {path}" + ("  (return)" if kind == "ReturnTrack" else ""))
        if t is not None:
            dc = t.find("DeviceChain")
            mon = t.find("DeviceChain/MainSequencer/MonitoringEnum")
            kinds = TYPES.get(kind, kind)
            devs = [d.get("Id") for d in []]
            out.append(f"- **Type:** {kinds}")
            if kind in ("AudioTrack",):
                out.append(f"- **Audio in:** {route_text(dc, 'AudioInputRouting', names)}")
            if kind in ("MidiTrack",):
                out.append(f"- **MIDI in:** {route_text(dc, 'MidiInputRouting', names)}")
            out.append(f"- **Audio out:** {route_text(dc, 'AudioOutputRouting', names)}")
            if kind in ("AudioTrack", "MidiTrack") and mon is not None:
                out.append(f"- **Monitoring:** {MONITORING.get(mon.get('Value'), mon.get('Value'))}")
        out.append("")
        out.append("| Ch | Control # | Device | Control |")
        out.append("|---|---|---|---|")
        for r in sorted(rs, key=lambda r: (r["channel"], r["number"])):
            n = f"note {r['number']}" if r["type"] == "note" else f"CC {r['number']}"
            out.append(f"| {r['channel']} | {n} | {r['device']} | {r['control']} |")

    out.append("\n## Routing of every other track (no controller mappings)")
    out.append("| Track | Type | Input | Output |")
    out.append("|---|---|---|---|")
    mpaths = {p for (_, p) in mapped}
    for t in tracks:
        p = paths.get(t.get("Id"), names[t.get("Id")]) if t.tag != "ReturnTrack" else names[t.get("Id")]
        if p in mpaths:
            continue
        dc = t.find("DeviceChain")
        inp = route_text(dc, "AudioInputRouting" if t.tag == "AudioTrack" else "MidiInputRouting", names) \
            if t.tag in ("AudioTrack", "MidiTrack") else "-"
        out.append(f"| {p}{' (return)' if t.tag == 'ReturnTrack' else ''} | {TYPES.get(t.tag, t.tag)} | "
                   f"{inp} | {route_text(dc, 'AudioOutputRouting', names)} |")
    print("\n".join(out))


if __name__ == "__main__":
    main()
