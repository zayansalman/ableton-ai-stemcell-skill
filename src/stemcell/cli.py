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

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
