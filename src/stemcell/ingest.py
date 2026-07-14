"""Ingest stage: validate and normalize the input audio file to input.wav."""

from __future__ import annotations

import json
import shutil
import subprocess

from .ctx import Ctx

MAX_WARN_SEC = 480.0
MAX_HARD_SEC = 900.0


def _ffprobe(ctx: Ctx) -> dict:
    if shutil.which("ffprobe") is None:
        raise RuntimeError("ffprobe not found on PATH")

    proc = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration:stream=codec_type",
            "-of", "json",
            str(ctx.audio_in),
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe failed on {ctx.audio_in}: {proc.stderr.strip()}")

    return json.loads(proc.stdout)


def _validate(ctx: Ctx, probe: dict) -> None:
    streams = probe.get("streams", [])
    if not any(s.get("codec_type") == "audio" for s in streams):
        raise RuntimeError(f"not an audio file: {ctx.audio_in}")

    duration_str = probe.get("format", {}).get("duration")
    if duration_str is None:
        return
    duration_sec = float(duration_str)

    if duration_sec > MAX_HARD_SEC and not ctx.allow_long:
        raise RuntimeError(
            f"input audio is {duration_sec / 60:.1f} min, exceeds the 15 min limit; "
            "pass --allow-long to process it anyway"
        )
    if duration_sec > MAX_WARN_SEC:
        print(f"warning: input audio is {duration_sec / 60:.1f} min, this may take a while")


def _normalize(ctx: Ctx) -> None:
    proc = subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(ctx.audio_in),
            "-ac", "2", "-ar", "44100", "-c:a", "pcm_s16le",
            str(ctx.input_wav),
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        stderr_tail = "\n".join(proc.stderr.strip().splitlines()[-20:])
        raise RuntimeError(f"ffmpeg normalization failed for {ctx.audio_in}:\n{stderr_tail}")


def run(ctx: Ctx) -> None:
    ctx.ensure_dirs()
    probe = _ffprobe(ctx)
    _validate(ctx, probe)
    _normalize(ctx)
