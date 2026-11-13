"""Copy the MIDI-controller mappings of a group (and its tracks) from one Live set (.als) onto the same-named tracks of another.

    python3 als_apply_midi_mappings.py SOURCE.als TARGET.als --group "Rekordbox Loops" [--alias "Drums=Rest of Drums"] \
        [-o OUT.als] [--dry-run]

Live cannot change MIDI mappings in a running set, so this edits the set FILE. By default it writes a COPY of TARGET ("<TARGET name> (MIDI from
<SOURCE name>).als" next to it; TARGET itself is never touched). With --in-place it rewrites TARGET itself, after saving a backup of it as
"Backup/<name> [before MIDI mapping <time>].als". Live keeps the set in memory: after an --in-place run, close the set choosing "Don't Save"
and reopen it (saving first would overwrite the change).

For the group track and every track in it:
  * the mappings the TARGET track has now are removed (a control without a <KeyMidi> block is unmapped)
  * the SOURCE track of the same name (the leading "NN-" auto-number is ignored) is read, and each of its mapped controls (channel, CC / note,
    and the mapped range) is written onto the control at the same place in the target track: mixer Volume / Pan / Sends, and device controls
    at the same device position. A control the target track has no counterpart for (e.g. an Auto Filter that is not on that track)
    is reported and skipped.
  --alias TARGETNAME=SOURCENAME pairs tracks whose names differ (e.g. an old "Drums" with the source's "Rest of Drums").

The check at the end: apart from <KeyMidi> blocks and the mapped ranges, the copy must be identical to the target, or nothing is written.
"""

from __future__ import annotations

import argparse
import copy
import gzip
import re
import shutil
import sys
from datetime import datetime
import xml.etree.ElementTree as ET
from pathlib import Path

TRACK_TAGS = ("AudioTrack", "MidiTrack", "GroupTrack")


def base_name(name: str) -> str:
    return re.sub(r"^\d+-", "", name)


def load(path: str):
    raw = gzip.open(path).read().decode("utf-8")
    head = raw[: raw.index("<Ableton")]
    return head, ET.fromstring(raw)


def tracks_of(root):
    out = {}
    for t in root.find("LiveSet/Tracks"):
        if t.tag in TRACK_TAGS:
            out[t.get("Id")] = t
    return out


def tname(t) -> str:
    return t.find("Name/EffectiveName").get("Value")


def group_members(root, group_name: str):
    """(group track, [member tracks in set order]) for the group with this name (auto-number ignored)."""
    ts = tracks_of(root)
    g = next((t for t in ts.values() if t.tag == "GroupTrack" and base_name(tname(t)) == base_name(group_name)), None)
    if g is None:
        raise SystemExit(f"no group track named '{group_name}' in the set")
    gid = g.get("Id")
    members = [t for t in ts.values() if t.find("TrackGroupId") is not None and t.find("TrackGroupId").get("Value") == gid]
    return g, members


def signature(track, el, parent):
    """Where `el` sits inside the track: [(tag, index among same-tag siblings), ...] from just below the track down to el."""
    chain = []
    cur = el
    while cur is not track:
        p = parent[cur]
        same = [c for c in p if c.tag == cur.tag]
        chain.append((cur.tag, same.index(cur)))
        cur = p
    return tuple(reversed(chain))


def resolve(track, sig):
    cur = track
    for tag, idx in sig:
        same = [c for c in cur if c.tag == tag]
        if idx >= len(same):
            return None
        cur = same[idx]
    return cur


def mapped_controls(track, parent):
    """[(signature of the mapped control, its <KeyMidi>, its <MidiControllerRange> or None, label)]"""
    rows = []
    for kb in track.iter("KeyMidi"):
        if int(kb.find("NoteOrController").get("Value")) < 0:
            continue
        owner = parent[kb]
        sig = signature(track, owner, parent)
        label = " > ".join(t for t, _ in sig[-3:]) if sig else owner.tag
        rows.append((sig, kb, owner.find("MidiControllerRange"), label))
    return rows


def strip_mappings(track, parent) -> int:
    n = 0
    for kb in list(track.iter("KeyMidi")):
        if int(kb.find("NoteOrController").get("Value")) >= 0:
            n += 1
        parent[kb].remove(kb)
    return n


def put_mapping(owner, kb, rng):
    """Give `owner` a copy of the <KeyMidi> block (right after <LomId> when there is one) and the mapped range."""
    new = copy.deepcopy(kb)
    new.tail = None
    pos = 0
    for i, c in enumerate(owner):
        if c.tag == "LomId":
            pos = i + 1
            break
    owner.insert(pos, new)
    new.tail = owner[pos - 1].tail if pos else owner.text
    own_rng = owner.find("MidiControllerRange")
    if rng is not None and own_rng is not None:
        for tag in ("Min", "Max"):
            own_rng.find(tag).set("Value", rng.find(tag).get("Value"))


def without_midi(root):
    """The set as text with every KeyMidi block and mapped range removed, for the 'only mappings changed' check."""
    r = copy.deepcopy(root)
    parent = {c: p for p in r.iter() for c in p}
    for kb in list(r.iter("KeyMidi")):
        parent[kb].remove(kb)
    for rng in list(r.iter("MidiControllerRange")):
        parent[rng].remove(rng)
    return ET.tostring(r, encoding="unicode")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source")
    ap.add_argument("target")
    ap.add_argument("--group", required=True, help="group whose tracks (and the group itself) get the source's mappings")
    ap.add_argument("--alias", action="append", default=[], metavar="TARGET=SOURCE", help="pair differently named tracks")
    ap.add_argument("-o", "--out")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--in-place", action="store_true", help="rewrite TARGET itself (a backup is saved first)")
    a = ap.parse_args()

    _, src_root = load(a.source)
    head, tgt_root = load(a.target)
    original_text = ET.tostring(tgt_root, encoding="unicode")
    sparent = {c: p for p in src_root.iter() for c in p}
    tparent = {c: p for p in tgt_root.iter() for c in p}
    sg, smembers = group_members(src_root, a.group)
    tg, tmembers = group_members(tgt_root, a.group)
    alias = dict(x.split("=", 1) for x in a.alias)
    by_src = {base_name(tname(t)): t for t in [sg] + smembers}

    print(f"source: {Path(a.source).name}   target: {Path(a.target).name}   group: {a.group}")
    plan, problems = [], []
    for t in [tg] + tmembers:
        name = base_name(tname(t))
        sname = alias.get(name, name)
        s = by_src.get(sname)
        if s is None:
            print(f"  {name:16} no track '{sname}' in the source: its mappings are cleared and nothing is added")
        rows = mapped_controls(s, sparent) if s is not None else []
        before = sum(1 for kb in t.iter("KeyMidi") if int(kb.find("NoteOrController").get("Value")) >= 0)
        todo = []
        for sig, kb, rng, label in rows:
            todo.append((sig, kb, rng, label))
        plan.append((t, name, sname, todo, before))

    # source tracks that have no home in the target (e.g. a Kick track the saved target does not have yet)
    tnames = {base_name(tname(t)) for t in [tg] + tmembers}
    reverse_alias = {v: k for k, v in alias.items()}
    for sname_, s in by_src.items():
        if reverse_alias.get(sname_, sname_) not in tnames and mapped_controls(s, sparent):
            problems.append(f"'{sname_}' is mapped in the source but has no track in the target's '{a.group}' group, so nothing was added for it "
                            f"(add/save that track in the target first)")
    # simulate on a copy so the report is honest, then do it for real on the output
    final_use = {}
    for t, name, sname, todo, before in plan:
        got, missed = [], []
        for sig, kb, rng, label in todo:
            owner = resolve(t, sig)
            ch, cc = int(kb.find("Channel").get("Value")) + 1, int(kb.find("NoteOrController").get("Value"))
            kind = "note" if kb.find("IsNote").get("Value") == "true" else "CC"
            if owner is None:
                missed.append(f"ch{ch} {kind} {cc} ({label})")
            else:
                got.append(f"ch{ch} {kind} {cc} ({label})")
                final_use.setdefault((ch, kind, cc), []).append(name)
        arrow = f" (from '{sname}')" if sname != name else ""
        print(f"  {name:16}{arrow} clears {before} old, adds {len(got)}: " + ", ".join(got))
        for m in missed:
            problems.append(f"{name}: {m} has no matching control in the target track (skipped)")
    for key, who in sorted(final_use.items()):
        if len(who) > 1:
            problems.append(f"ch{key[0]} {key[1]} {key[2]} is mapped {len(who)} times in the group: {who}")
    # same channel/CC already used elsewhere in the target (outside the group)?
    group_ids = {t.get("Id") for t, *_ in plan}
    for t in tracks_of(tgt_root).values():
        if t.get("Id") in group_ids:
            continue
        for kb in t.iter("KeyMidi"):
            cc = int(kb.find("NoteOrController").get("Value"))
            if cc < 0:
                continue
            ch, kind = int(kb.find("Channel").get("Value")) + 1, ("note" if kb.find("IsNote").get("Value") == "true" else "CC")
            if (ch, kind, cc) in final_use:
                problems.append(f"ch{ch} {kind} {cc} is also mapped on '{tname(t)}' (outside the group)")
    if problems:
        print("\nthings to know:")
        for p in problems:
            print("  - " + p)
    if a.dry_run:
        print("\n(dry run: nothing written)")
        return 0

    # do it
    for t, name, sname, todo, before in plan:
        strip_mappings(t, tparent)
    for t, name, sname, todo, before in plan:
        for sig, kb, rng, label in todo:
            owner = resolve(t, sig)
            if owner is not None:
                put_mapping(owner, kb, rng)

    # the check: nothing but mappings changed
    if without_midi(tgt_root) != without_midi(load(a.target)[1]):
        sys.exit("refusing to write: something other than MIDI mappings changed")

    target = Path(a.target)
    if a.in_place:
        backup_dir = target.parent / "Backup"
        backup_dir.mkdir(exist_ok=True)
        backup = backup_dir / f"{target.stem} [before MIDI mapping {datetime.now():%Y-%m-%d %H%M%S}].als"
        shutil.copy2(target, backup)
        out = target
        print(f"\nbacked up the target to {backup}")
    else:
        out = Path(a.out) if a.out else target.with_name(f"{target.stem} (MIDI from {Path(a.source).stem}).als")
        if out.resolve() == target.resolve():
            sys.exit("refusing to overwrite the target; use --in-place (keeps a backup) or give a different -o")
    tmp = out.with_name(out.name + ".tmp")
    with gzip.open(tmp, "wb") as f:
        f.write((head + ET.tostring(tgt_root, encoding="unicode")).encode("utf-8"))
    gzip.open(tmp).read()                                   # it must read back as a valid gzip before it replaces anything
    tmp.replace(out)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
