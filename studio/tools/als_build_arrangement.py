"""Lay Session clips onto the Arrangement of an Ableton Live set (.als) as ONE extended clip per block.

    python3 als_build_arrangement.py SET.als --out NEW.als --plan plan.json

plan.json: {"Track name": {"slot": 0, "blocks": [[start_bar, end_bar], ...]}, ...}
Bars are 1-based and end-exclusive (4/4): [9, 65] = bars 9-64. Each block becomes a single arrangement
clip copied from the track's Session clip in `slot`; its loop is untouched and only CurrentStart /
CurrentEnd are set (how Live stores a clip dragged longer). Existing arrangement clips on the listed
tracks are replaced. Never writes in place.
"""

from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from als_copy_tracks import track_blocks  # noqa: E402

BEATS_PER_BAR = 4


def session_clip(block: str, slot: int) -> tuple[str, str]:
    """(clip XML, "AudioClip" | "MidiClip") for the Session clip in `slot` of this track block."""
    m = re.search(r'<ClipSlot Id="%d">' % slot, block)
    if not m:
        sys.exit(f"no slot {slot}")
    c = re.compile(r"<(AudioClip|MidiClip) Id=\"\d+\"[^>]*>").search(block, m.end())
    nxt = block.find("<ClipSlot Id=", m.end())
    if not c or (nxt != -1 and c.start() > nxt):
        sys.exit(f"slot {slot} is empty")
    close = f"</{c.group(1)}>"
    end = block.index(close, c.end()) + len(close)
    return block[c.start():end], c.group(1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("als")
    ap.add_argument("--out", required=True)
    ap.add_argument("--plan", required=True)
    a = ap.parse_args()
    if os.path.abspath(a.out) == os.path.abspath(a.als):
        sys.exit("refusing to overwrite the source set")
    plan = json.load(open(a.plan))
    xml = gzip.open(a.als, "rt", encoding="utf-8").read()

    edits = []
    seen = set()
    for t in track_blocks(xml):
        if t["name"] not in plan:
            continue
        seen.add(t["name"])
        cfg = plan[t["name"]]
        clip, tag = session_clip(t["block"], cfg["slot"])
        if re.search(r'<LoopOn Value="false"', clip):
            sys.exit(f"{t['name']}: session clip has loop off")
        ev = re.search(r"<ArrangerAutomation>\s*<Events\s*/?>", t["block"])
        if not ev:
            sys.exit(f"{t['name']}: no arranger events")
        out_clips = []
        for i, (b0, b1) in enumerate(cfg["blocks"]):
            s, e = (b0 - 1) * BEATS_PER_BAR, (b1 - 1) * BEATS_PER_BAR
            c = re.sub(r'^<(\w+) Id="\d+" Time="[^"]*"', rf'<\1 Id="{i}" Time="{s}"', clip, count=1)
            c = re.sub(r'(<CurrentStart Value=")[^"]+(")', rf"\g<1>{s}\g<2>", c, count=1)
            c = re.sub(r'(<CurrentEnd Value=")[^"]+(")', rf"\g<1>{e}\g<2>", c, count=1)
            c = re.sub(r"<LomId Value=\"\d+\" />", '<LomId Value="0" />', c, count=1)
            out_clips.append(c)
        body = "<ArrangerAutomation>\n<Events>\n" + "\n".join(out_clips) + "\n</Events>"
        # replace "<ArrangerAutomation><Events />" or the populated Events element
        if ev.group(0).rstrip().endswith("/>"):
            span_end = t["start"] + ev.end()
        else:
            span_end = t["start"] + t["block"].index("</Events>", ev.end()) + len("</Events>")
        edits.append((t["start"] + ev.start(), span_end, body))
        print(f"{t['name']}: {len(out_clips)} clip(s) from slot {cfg['slot']} ({tag})")
    missing = set(plan) - seen
    if missing:
        sys.exit(f"tracks not found: {missing}")

    for s, e, body in sorted(edits, reverse=True):
        xml = xml[:s] + body + xml[e:]
    with gzip.open(a.out, "wb") as f:
        f.write(xml.encode("utf-8"))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
