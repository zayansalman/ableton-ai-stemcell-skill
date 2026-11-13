"""Copy tracks from one Ableton Live set (.als) into another, keeping devices,
clips, MIDI mappings and input routing.

    python3 als_copy_tracks.py SOURCE.als TARGET.als --tracks Kick Break Shaker Perc \
        --group "Maschine Drums" --after Hat [--dry-run]

What gets rewritten in each copied track:
  * the track Id: a fresh one, unique among the target's tracks
  * LomId: reset to 0 so Live assigns a new one on load
  * TrackGroupId: the target's group track of the same name
  * "AudioIn/Track.<id>/..." and "MidiIn/Track.<id>/..." routing targets: mapped from
    the source track id to the target track with the same name (the leading "NN-"
    auto-number is ignored, since Live renumbers tracks)
  * every pointee-scoped Id (AutomationTarget, *ModulationTarget, Pointee) and the
    PointeeId references to them: renumbered from the target's NextPointeeId,
    which is then advanced

The target is backed up next to itself before it is written.
"""

from __future__ import annotations

import argparse
import gzip
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

TRACK_TAGS = ("AudioTrack", "MidiTrack", "GroupTrack")
POINTEE_TAGS = re.compile(r"<((?:\w*ModulationTarget)|AutomationTarget|Pointee) Id=\"(\d+)\"")


def base_name(name: str) -> str:
    """Strip Live's auto-number prefix: '38-Maschine 3' -> 'Maschine 3'."""
    return re.sub(r"^\d+-", "", name)


def track_blocks(xml: str) -> list[dict]:
    tracks_start = xml.index("<Tracks>")
    tracks_end = xml.index("</Tracks>", tracks_start)
    out = []
    pos = tracks_start
    pattern = re.compile(r"\t*<(%s) Id=\"(\d+)\"" % "|".join(TRACK_TAGS))
    while True:
        m = pattern.search(xml, pos, tracks_end)
        if not m:
            break
        tag, tid = m.group(1), m.group(2)
        close = "</%s>" % tag
        end = xml.index(close, m.end()) + len(close)
        block = xml[m.start():end]
        name = re.search(r'<EffectiveName Value="([^"]*)"', block).group(1)
        group = int(re.search(r'<TrackGroupId Value="(-?\d+)"', block).group(1))
        out.append(dict(tag=tag, id=int(tid), name=name, group=group,
                        start=m.start(), end=end, block=block))
        pos = end
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("target")
    ap.add_argument("--tracks", nargs="+", required=True)
    ap.add_argument("--group", required=True, help="target group track to put them in")
    ap.add_argument("--after", required=True, help="insert after this target track")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    src = gzip.open(args.source).read().decode("utf-8")
    tgt_path = Path(args.target)
    tgt = gzip.open(tgt_path).read().decode("utf-8")

    src_tracks = track_blocks(src)
    tgt_tracks = track_blocks(tgt)
    src_by_id = {t["id"]: t for t in src_tracks}
    tgt_by_base = {}
    for t in tgt_tracks:
        tgt_by_base.setdefault(base_name(t["name"]), t)

    existing = {base_name(t["name"]) for t in tgt_tracks}
    clash = [n for n in args.tracks if n in existing]
    if clash:
        sys.exit(f"target already has track(s) {clash}; refusing to duplicate")

    group = next((t for t in tgt_tracks if t["name"] == args.group and t["tag"] == "GroupTrack"), None)
    after = next((t for t in tgt_tracks if t["name"] == args.after), None)
    if group is None or after is None:
        sys.exit(f"target is missing group '{args.group}' or anchor track '{args.after}'")

    next_pointee = int(re.search(r'<NextPointeeId Value="(\d+)"', tgt).group(1))
    next_track_id = max(t["id"] for t in tgt_tracks) + 1
    # Return tracks share the track id space; stay above them too.
    for rid in re.findall(r"<ReturnTrack Id=\"(\d+)\"", tgt):
        next_track_id = max(next_track_id, int(rid) + 1)

    new_blocks = []
    for name in args.tracks:
        t = next((x for x in src_tracks if x["name"] == name), None)
        if t is None:
            sys.exit(f"source has no track named '{name}'")
        b = t["block"]

        # 1. pointee-scoped ids -> fresh range
        remap = {}
        for _tag, old in POINTEE_TAGS.findall(b):
            if old not in remap:
                remap[old] = str(next_pointee)
                next_pointee += 1
        b = POINTEE_TAGS.sub(lambda m: f'<{m.group(1)} Id="{remap[m.group(2)]}"', b)
        b = re.sub(r'<PointeeId Value="(\d+)"',
                   lambda m: f'<PointeeId Value="{remap.get(m.group(1), m.group(1))}"', b)

        # 2. routing to other tracks -> same-named track in target
        def fix_route(m):
            kind, sid, rest = m.group(1), int(m.group(2)), m.group(3)
            src_t = src_by_id.get(sid)
            if src_t is None:
                sys.exit(f"{name}: routing points at unknown source track {sid}")
            dst = tgt_by_base.get(base_name(src_t["name"]))
            if dst is None:
                sys.exit(f"{name}: routing source '{src_t['name']}' not in target")
            return f'"{kind}/Track.{dst["id"]}/{rest}"'
        b = re.sub(r'"(AudioIn|MidiIn)/Track\.(\d+)/([^"]*)"', fix_route, b)

        # 3. identity + group
        b = re.sub(r'^(\t*<%s) Id="\d+"' % t["tag"], rf'\1 Id="{next_track_id}"', b, count=1)
        b = re.sub(r'<LomId Value="\d+" />', '<LomId Value="0" />', b, count=1)
        b = re.sub(r'<TrackGroupId Value="-?\d+"', f'<TrackGroupId Value="{group["id"]}"', b, count=1)
        print(f"{name}: track id {t['id']} -> {next_track_id}, {len(remap)} pointee ids remapped, "
              f"routes {sorted(set(re.findall(r'(?:AudioIn|MidiIn)/Track[^\"]*', b)))}")
        next_track_id += 1
        new_blocks.append(b)

    # keep indentation consistent with the anchor
    indent = re.match(r"\t*", after["block"]).group(0)
    insert = "".join("\n" + indent + b.lstrip("\t") for b in new_blocks)
    out = tgt[:after["end"]] + insert + tgt[after["end"]:]
    out = re.sub(r'<NextPointeeId Value="\d+"', f'<NextPointeeId Value="{next_pointee}"', out, count=1)

    # sanity: re-parse and confirm
    check = track_blocks(out)
    names = [c["name"] for c in check]
    for n in args.tracks:
        assert names.count(n) == 1, n
    ids = [c["id"] for c in check]
    assert len(ids) == len(set(ids)), "duplicate track ids"
    import xml.etree.ElementTree as ET
    ET.fromstring(out)  # well-formed

    print(f"target tracks: {len(tgt_tracks)} -> {len(check)}; NextPointeeId -> {next_pointee}")
    if args.dry_run:
        print("dry run: nothing written")
        return
    backup = tgt_path.with_name(f"{tgt_path.stem} (before track copy {datetime.now():%H%M%S}).als")
    shutil.copy2(tgt_path, backup)
    with gzip.open(tgt_path, "wb") as f:
        f.write(out.encode("utf-8"))
    print(f"wrote {tgt_path}\nbackup {backup}")


if __name__ == "__main__":
    main()
