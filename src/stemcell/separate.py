"""Stage: Demucs stem separation.

Splits ctx.input_wav into drums/bass/other/vocals via htdemucs, running on CPU
with a short segment length to bound memory use on long tracks.
"""

from __future__ import annotations

import shutil
import subprocess
import sys

from .ctx import STEMS, Ctx


def run(ctx: Ctx) -> None:
    tmp_out = ctx.outdir / ".demucs"
    if tmp_out.exists():
        shutil.rmtree(tmp_out)
    tmp_out.mkdir(parents=True)

    cmd = [
        sys.executable, "-m", "demucs.separate",
        "-n", "htdemucs", "-d", "cpu", "--segment", "5", "-j", "1",
        "-o", str(tmp_out), str(ctx.input_wav),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        stderr_tail = "\n".join(proc.stderr.strip().splitlines()[-40:])
        raise RuntimeError(
            f"demucs.separate failed (exit {proc.returncode}) on {ctx.input_wav}:\n{stderr_tail}"
        )

    demucs_dir = tmp_out / "htdemucs" / ctx.input_wav.stem
    missing = [stem for stem in STEMS if not (demucs_dir / f"{stem}.wav").exists()]
    if missing:
        raise RuntimeError(
            f"demucs did not produce expected stem(s) {missing} in {demucs_dir}"
        )

    ctx.ensure_dirs()
    for stem in STEMS:
        shutil.move(str(demucs_dir / f"{stem}.wav"), str(ctx.stem_path(stem)))

    shutil.rmtree(tmp_out)
