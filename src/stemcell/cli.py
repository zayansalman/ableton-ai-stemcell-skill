"""stemcell CLI: dissect a song into stems, tempo/key, drum one-shots, and MIDI.

Subcommands:
  run <audio> --out <dir>   run the full pipeline (or a --stages subset)
  bootstrap                  pre-download models (htdemucs, CLAP) with disk-free guardrail
  selftest                   offline synthetic check, no copyrighted audio, no model downloads
"""

from __future__ import annotations

import argparse
import importlib
import shutil
import sys
from pathlib import Path

from .ctx import Ctx

STAGE_ORDER = ["ingest", "separate", "analyze", "drums", "transcribe", "report"]


def _stage_module(name: str):
    return importlib.import_module(f"stemcell.{name}")


def run_pipeline(ctx: Ctx, stages: list[str]) -> None:
    ctx.ensure_dirs()
    for name in stages:
        if ctx.stage_done(name):
            print(f"[skip] {name} (cached)")
            continue
        print(f"[run ] {name}")
        _stage_module(name).run(ctx)
        print(f"[done] {name}")


def cmd_run(args: argparse.Namespace) -> None:
    audio_in = Path(args.audio).expanduser().resolve()
    if not audio_in.exists():
        print(f"error: input file not found: {audio_in}", file=sys.stderr)
        sys.exit(2)

    stages = args.stages.split(",") if args.stages else list(STAGE_ORDER)
    unknown = set(stages) - set(STAGE_ORDER)
    if unknown:
        print(f"error: unknown stage(s): {sorted(unknown)} (valid: {STAGE_ORDER})", file=sys.stderr)
        sys.exit(2)

    ctx = Ctx(
        audio_in=audio_in,
        outdir=Path(args.out).expanduser().resolve(),
        force=args.force,
        allow_long=args.allow_long,
    )
    run_pipeline(ctx, stages)
    print(f"\nDone. Report: {ctx.report_md}")


def cmd_bootstrap(_args: argparse.Namespace) -> None:
    _, _, free_before = shutil.disk_usage(Path.home())
    print(f"Disk free before: {free_before / 2**30:.1f} GiB")

    for exe in ("ffmpeg", "ffprobe"):
        if shutil.which(exe) is None:
            print(f"error: {exe} not found on PATH", file=sys.stderr)
            sys.exit(2)
    print("ffmpeg/ffprobe: OK")

    from basic_pitch import ICASSP_2022_MODEL_PATH

    if not Path(ICASSP_2022_MODEL_PATH).exists():
        print(f"error: basic-pitch CoreML model missing at {ICASSP_2022_MODEL_PATH}", file=sys.stderr)
        sys.exit(2)
    print(f"basic-pitch CoreML model: OK ({ICASSP_2022_MODEL_PATH})")

    print("Downloading htdemucs weights (~80MB)...")
    from demucs.pretrained import get_model

    get_model("htdemucs")
    print("htdemucs: OK")

    print("Downloading CLAP weights (laion/clap-htsat-unfused, ~615MB)...")
    from transformers import pipeline as hf_pipeline

    hf_pipeline("zero-shot-audio-classification", model="laion/clap-htsat-unfused")
    print("CLAP: OK")

    _, _, free_after = shutil.disk_usage(Path.home())
    print(
        f"Disk free after: {free_after / 2**30:.1f} GiB "
        f"(used {(free_before - free_after) / 2**20:.0f} MiB)"
    )


def cmd_selftest(args: argparse.Namespace) -> None:
    from .selftest import run_selftest

    outdir = (
        Path(args.out).expanduser().resolve()
        if args.out
        else Path.home() / ".stemcell" / "selftest"
    )
    ok = run_selftest(outdir)
    sys.exit(0 if ok else 1)


def cmd_chop(args: argparse.Namespace) -> None:
    from .vocalchop import NOTE_NAMES, write_chop_kit

    audio_in = Path(args.audio).expanduser().resolve()
    if not audio_in.exists():
        print(f"error: vocal file not found: {audio_in}", file=sys.stderr)
        sys.exit(2)
    root_pitch = _parse_root(args.root)
    out = Path(args.out).expanduser().resolve()
    summary = write_chop_kit(
        audio_in, out, root_pitch=root_pitch, scale=args.scale,
        tempo_bpm=args.tempo, bars=args.bars, progression=args.progression,
    )
    root_name = NOTE_NAMES[root_pitch % 12]
    if summary["n_slices"] > 64:
        print(
            f"note: {summary['n_slices']} slices is a lot — chop a 1-2 bar vocal phrase for a "
            f"tighter, more playable kit (Todd mode addresses the first ~24 slices).",
            file=sys.stderr,
        )
    print(
        f"Chopped {summary['n_slices']} slices at {args.tempo} BPM, {root_name} {args.scale}.\n"
        f"  MK pattern:   {summary['mk_notes']} notes (mk.notes.json, Simpler Classic, load {summary['mk_pick']})\n"
        f"  Todd pattern: {summary['todd_notes']} notes (todd.notes.json, Simpler Slice)\n"
        f"See {out / 'README.txt'} for the one-drag Ableton setup."
    )


def _parse_root(root: str) -> int:
    from .vocalchop import NOTE_NAMES

    root = root.strip()
    if root.isdigit():
        return int(root)
    name = root[:-1].upper() if root[-1].isdigit() else root.upper()
    octave = int(root[-1]) if root[-1].isdigit() else 3
    if name not in NOTE_NAMES:
        print(f"error: bad --root '{root}' (use a MIDI number or note like 'C', 'F#3')", file=sys.stderr)
        sys.exit(2)
    # Ableton convention: C3 = MIDI 60. Bare "C" defaults to C3 = 60.
    return NOTE_NAMES.index(name) + 12 * (octave + 2)


def main() -> None:
    parser = argparse.ArgumentParser(prog="stemcell")
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="Dissect an audio file")
    p_run.add_argument("audio", help="Path to the input audio file (mp3/wav/...)")
    p_run.add_argument("--out", required=True, help="Output directory")
    p_run.add_argument("--force", action="store_true", help="Re-run all stages, ignore cache")
    p_run.add_argument(
        "--stages", default=None, help=f"Comma-separated subset of {STAGE_ORDER}"
    )
    p_run.add_argument(
        "--allow-long", action="store_true", help="Allow input audio longer than 15 minutes"
    )
    p_run.set_defaults(func=cmd_run)

    p_boot = sub.add_parser("bootstrap", help="Pre-download models (htdemucs, CLAP)")
    p_boot.set_defaults(func=cmd_bootstrap)

    p_self = sub.add_parser("selftest", help="Offline synthetic self-check (no models, no copyrighted audio)")
    p_self.add_argument("--out", default=None, help="Output dir (default: ~/.stemcell/selftest)")
    p_self.set_defaults(func=cmd_selftest)

    p_chop = sub.add_parser("chop", help="Chop a vocal + generate MK/Todd chop patterns (MIDI) for Ableton")
    p_chop.add_argument("audio", help="Path to the vocal audio file")
    p_chop.add_argument("--out", required=True, help="Output directory for the chop kit")
    p_chop.add_argument("--tempo", type=float, required=True, help="Track tempo in BPM")
    p_chop.add_argument("--root", default="C", help="Root note: MIDI number or name like 'C', 'F#3' (default C=C3)")
    p_chop.add_argument("--scale", default="minor", choices=["minor", "major"], help="Scale (default minor)")
    p_chop.add_argument("--bars", type=int, default=4, help="Pattern length in bars (default 4)")
    p_chop.add_argument("--progression", default="i-VII-VI-VII",
                        help="Chord progression for MK mode (default i-VII-VI-VII)")
    p_chop.set_defaults(func=cmd_chop)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
