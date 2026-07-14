from pathlib import Path

from stemcell.selftest import run_selftest


def test_selftest(tmp_path: Path) -> None:
    assert run_selftest(tmp_path / "selftest")
