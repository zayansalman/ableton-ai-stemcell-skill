"""Carry Arrangement LANE automation (track-level) from the pre-cut set onto the stems of the cut-up set.

    python3 tools/als_stem_automation.py --old PRECUT.als --new CUTUP.als --out FIXED.als [--resample NAME]
    python3 tools/als_stem_automation.py --old PRECUT.als --check      # which tracks have lane automation

Live's API cannot read or write Arrangement lane automation, so this edits the saved files (run with Live
CLOSED, open the --out copy; never writes in place). Clip envelopes (automation inside a clip) travel with the
clip when it is copied, so they are not touched here.

How: in the CUT-UP set the resample track's arrangement clips are the pieces. Each piece plays original beats
[src, src+length) at position [start, end). For every other track that has lane automation in the PRE-CUT set,
each envelope is rebuilt: per piece, a point at `start` holding the value at `src`, the original points inside
the window shifted to the piece's position, and a point at `end` holding the value at the window's end (two
points at the same time make a step, as Live does itself). Everything else in that envelope is dropped, so
nothing plays outside the pieces. Tracks are matched by name ignoring Live's "NN-" prefix.

Assumes the stems and the resample all began at beat 0 (so a piece's start marker is its original position).
Interpolation is linear between points; curve shapes inside a window are not preserved.
"""
from __future__ import annotations

import argparse
import gzip
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from als_copy_tracks import base_name, track_blocks  # noqa: E402

ENV = re.compile(r'<AutomationEnvelope Id="(\d+)">(.*?)</AutomationEnvelope>', re.S)
EVENT = re.compile(r'<(FloatEvent|BoolEvent|EnumEvent) Id="\d+" Time="([^"]+)" Value="([^"]+)" />')
NEG = "-63072000"


def val(block, tag):
    m = re.search(rf'<{tag} Value="([^"]+)"', block)
    return m.group(1) if m else None


def track_envelopes(block):
    """Track-level lane envelopes: {pointee_id: (kind, [(time, value)])} from the first <AutomationEnvelopes>."""
    i = block.find("<AutomationEnvelopes>")
    if i < 0:
        return {}
    j = block.find("</AutomationEnvelopes>", i)
    out = {}
    for m in ENV.finditer(block[i:j]):
        body = m.group(2)
        pid = re.search(r'<PointeeId Value="(\d+)"', body).group(1)
        evs = EVENT.findall(body)
        if evs:
            out[pid] = (evs[0][0], [(float(t), float(v)) for _, t, v in evs])
    return out


def value_at(events, kind, t):
    """Right-continuous value at time t (the last point at or before t; floats interpolate toward the next)."""
    prev = None
    for k, (et, ev) in enumerate(events):
        if et <= t:
            prev = k
        else:
            break
    if prev is None:
        return events[0][1]
    et, ev = events[prev]
    if kind != "FloatEvent" or prev + 1 >= len(events):
        return ev
    nt, nv = events[prev + 1]
    return ev if nt == et else ev + (nv - ev) * (t - et) / (nt - et)


def remap(events, kind, pieces):
    out = []
    for start, end, src in pieces:
        length = end - start
        out.append((start, value_at(events, kind, src)))
        out += [(start + (t - src), v) for t, v in events if src < t < src + length]
        out.append((end, value_at(events, kind, src + length)))
    return out


def fmt(x):
    return repr(int(x)) if float(x) == int(x) else repr(round(x, 9))


def envelope_xml(eid, pid, kind, events, indent):
    first = events[0][1]
    pts = [(NEG, first)] + [(fmt(t), v) for t, v in events]
    rows = "".join(f'{indent}\t\t\t\t\t<{kind} Id="{n}" Time="{t}" Value="{fmt(v)}" />\n' for n, (t, v) in enumerate(pts))
    return (f'{indent}<AutomationEnvelope Id="{eid}">\n{indent}\t<EnvelopeTarget>\n{indent}\t\t<PointeeId Value="{pid}" />\n'
            f'{indent}\t</EnvelopeTarget>\n{indent}\t<Automation>\n{indent}\t\t<Events>\n{rows}{indent}\t\t</Events>\n'
            f'{indent}\t\t<AutomationTransformViewState>\n{indent}\t\t\t<IsTransformPending Value="false" />\n'
            f'{indent}\t\t\t<TimeAndValueTransforms />\n{indent}\t\t</AutomationTransformViewState>\n{indent}\t</Automation>\n'
            f'{indent}</AutomationEnvelope>\n')


def resample_pieces(block):
    a = block.find("<ArrangerAutomation>")
    seg = block[a:block.find("</ArrangerAutomation>", a)]
    out = []
    for m in re.finditer(r'<AudioClip Id="\d+".*?</AudioClip>', seg, re.S):
        c = m.group(0)
        start, end = float(val(c, "CurrentStart")), float(val(c, "CurrentEnd"))
        src = float(val(c, "LoopStart")) + float(val(c, "StartRelative"))
        out.append((start, end, src))
    return sorted(out)


def set_envelopes(block, new_envs):
    """Replace/insert envelopes (pid -> (kind, events)) in the track-level <AutomationEnvelopes>."""
    i = block.find("<AutomationEnvelopes>")
    j = block.find("</AutomationEnvelopes>", i)
    seg = block[i:j]
    indent = re.search(r"\n(\t*)<AutomationEnvelopes>", block[:i + 30]).group(1) if False else "\t\t\t\t"
    existing = {re.search(r'<PointeeId Value="(\d+)"', m.group(2)).group(1): m for m in ENV.finditer(seg)}
    next_id = 1 + max([int(m.group(1)) for m in existing.values()] + [-1])
    for pid, (kind, events) in new_envs.items():
        if pid in existing:
            m = existing[pid]
            eid = m.group(1)
            seg = seg.replace(m.group(0), envelope_xml(eid, pid, kind, events, "").strip("\n"))
        else:
            add = envelope_xml(next_id, pid, kind, events, indent)
            next_id += 1
            if "<Envelopes />" in seg:
                seg = seg.replace("<Envelopes />", "<Envelopes>\n" + add + indent + "</Envelopes>")
            else:
                k = seg.rfind("</Envelopes>")
                seg = seg[:k] + add + seg[k:]
    return block[:i] + seg + block[j:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", required=True)
    ap.add_argument("--new")
    ap.add_argument("--out")
    ap.add_argument("--check", action="store_true", help="only list tracks with lane automation in --old")
    ap.add_argument("--resample", help="resample track name (default: the track whose name contains 'Resample')")
    a = ap.parse_args()
    if a.check:
        old = gzip.open(a.old, "rt", encoding="utf-8").read()
        found = [(t["name"], len(track_envelopes(t["block"]))) for t in track_blocks(old)]
        found = [f for f in found if f[1]]
        print("lane automation on:", found if found else "none")
        return
    if not a.new or not a.out:
        sys.exit("--new and --out are required (or use --check)")
    if os.path.abspath(a.out) in (os.path.abspath(a.old), os.path.abspath(a.new)):
        sys.exit("--out must be a new file")
    old = gzip.open(a.old, "rt", encoding="utf-8").read()
    new = gzip.open(a.new, "rt", encoding="utf-8").read()
    old_tracks = {base_name(t["name"]): t for t in track_blocks(old)}
    new_tracks = track_blocks(new)
    rs = [t for t in new_tracks if (a.resample and base_name(t["name"]) == base_name(a.resample))
          or (not a.resample and "resample" in t["name"].lower())]
    if len(rs) != 1:
        sys.exit("resample track not found/unique; pass --resample NAME")
    pieces = resample_pieces(rs[0]["block"])
    print("pieces:", [(s, e, o) for s, e, o in pieces])
    changed, repl = 0, []
    for t in new_tracks:
        if t is rs[0] or base_name(t["name"]) not in old_tracks:
            continue
        envs = track_envelopes(old_tracks[base_name(t["name"])]["block"])
        if not envs:
            continue
        rebuilt = {pid: (kind, remap(evs, kind, pieces)) for pid, (kind, evs) in envs.items()}
        repl.append((t["start"], t["end"], set_envelopes(t["block"], rebuilt)))
        changed += len(rebuilt)
        print("  %-28s %d envelope(s) rebuilt" % (t["name"], len(rebuilt)))
    for s, e, b in sorted(repl, reverse=True):
        new = new[:s] + b + new[e:]
    ET.fromstring(new.encode("utf-8"))  # must stay well-formed XML
    with gzip.open(a.out, "wt", encoding="utf-8") as f:
        f.write(new)
    print("wrote", a.out, "| envelopes rebuilt:", changed)
    if not changed:
        print("no lane automation found on the stems in the pre-cut set; nothing to do")


if __name__ == "__main__":
    main()
