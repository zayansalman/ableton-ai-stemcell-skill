"""Extend looped arrangement clips in an Ableton Live set (.als) the way dragging a clip's
right edge does: ONE clip, its loop unchanged, only its right edge (CurrentEnd) moves.

    python3 als_extend_clips.py SET.als --out NEW.als --length longest
    python3 als_extend_clips.py SET.als --out NEW.als --length 32 --tracks Low Top

Verified against 303 clips the user extended by hand: Live keeps LoopStart/LoopEnd/OutMarker
(the loop) and moves only CurrentEnd. A clip that already runs past the loop is simply
"extended"; this tool changes nothing else.

Rules
  * Only clips with Loop on and a loop shorter than the target are touched.
  * --length longest = the longest clip extent (CurrentEnd - CurrentStart) among the selected tracks.
  * A clip is never extended into the next clip on its track; it stops at that clip's start.
  * Never writes in place: --out is required. Run it with Live CLOSED on a copy, then open the copy.
"""

from __future__ import annotations

import argparse
import gzip
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from als_copy_tracks import track_blocks  # noqa: E402

CLIP = re.compile(r"<(MidiClip|AudioClip) Id=\"\d+\"[^>]*>")


def val(block: str, tag: str):
    m = re.search(rf'<{tag} Value="([^"]+)"', block)
    return m.group(1) if m else None


def clips_in_events(block: str, start: int):
    """Yield (start, end, text) for each arrangement clip, scanning from just after the
    track's <Events>. Clips can hold their own nested <Events> (automation), so stop only at
    the </Events> that follows a clip boundary."""
    pos = start
    while True:
        nxt = re.compile(r"\s*<(/Events|MidiClip|AudioClip)\b").match(block, pos)
        if not nxt or nxt.group(1) == "/Events":
            return
        m = CLIP.match(block, nxt.start(1) - 1)
        close = f"</{m.group(1)}>"
        end = block.index(close, m.end()) + len(close)
        yield m.start(), end, block[m.start():end]
        pos = end


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("als")
    ap.add_argument("--out", required=True)
    ap.add_argument("--length", required=True, help="beats, or 'longest'")
    ap.add_argument("--tracks", nargs="*", help="track names (default: every track with arrangement clips)")
    a = ap.parse_args()
    if os.path.abspath(a.out) == os.path.abspath(a.als):
        sys.exit("refusing to overwrite the source; give a different --out")

    xml = gzip.open(a.als).read().decode("utf-8")
    plan = []  # (track name, absolute clip span, new CurrentEnd, old CurrentEnd, capped?)
    longest = 0.0
    per_track = []
    for t in track_blocks(xml):
        if a.tracks and t["name"] not in a.tracks:
            continue
        ev = re.search(r"<ArrangerAutomation>\s*<Events>", t["block"])
        if not ev:
            continue
        clips = []
        for s, e, text in clips_in_events(t["block"], ev.end()):
            cs, ce = float(val(text, "CurrentStart")), float(val(text, "CurrentEnd"))
            lp = re.search(r"<Loop>(.*?)</Loop>", text, re.S)
            if not lp:
                continue
            ls, le = float(val(lp.group(1), "LoopStart")), float(val(lp.group(1), "LoopEnd"))
            on = val(lp.group(1), "LoopOn") == "true"
            clips.append(dict(cs=cs, ce=ce, loop_len=le - ls, on=on,
                              abs_start=t["start"] + s, abs_end=t["start"] + e))
            longest = max(longest, ce - cs)
        per_track.append((t["name"], sorted(clips, key=lambda c: c["cs"])))

    target = longest if a.length == "longest" else float(a.length)
    for name, clips in per_track:
        for i, c in enumerate(clips):
            if not c["on"] or c["loop_len"] <= 0 or (c["ce"] - c["cs"]) >= target - 1e-6:
                continue
            new_end, capped = c["cs"] + target, False
            if i + 1 < len(clips) and clips[i + 1]["cs"] < new_end:
                new_end, capped = clips[i + 1]["cs"], True
            if new_end > c["ce"] + 1e-6:
                plan.append((name, c, new_end, capped))

    out = xml
    for name, c, new_end, capped in sorted(plan, key=lambda p: -p[1]["abs_start"]):  # back to front keeps spans valid
        seg = out[c["abs_start"]:c["abs_end"]]
        seg2 = re.sub(r'(<CurrentEnd Value=")[^"]+(")', rf"\g<1>{new_end:g}\g<2>", seg, count=1)
        out = out[:c["abs_start"]] + seg2 + out[c["abs_end"]:]

    print(f"target length {target:g} beats; extending {len(plan)} clip(s)")
    for name, c, new_end, capped in sorted(plan, key=lambda p: (p[0], p[1]["cs"])):
        print(f"  {name[:28]:28s} {c['cs']:g}: loop {c['loop_len']:g}, end {c['ce']:g} -> {new_end:g}" + ("  (stopped at next clip)" if capped else ""))
    with gzip.open(a.out, "wb") as f:
        f.write(out.encode("utf-8"))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
