"""Identity build (phase 3): unpack + repack with no edits gives the original .bin byte for byte; an edited file
reaches the disc through the layout's source= override and changes only its own sector."""
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build  # noqa: E402

SECTOR = 2352
need_disc = pytest.mark.skipif(
    not build.ROM_BIN.is_file() or not build.MKPSXISO_DIR.is_dir(), reason="no dump in rom/ or no mkpsxiso")


def differing_sectors(a, b, chunk=SECTOR * 4096):
    out = []
    with open(a, "rb") as fa, open(b, "rb") as fb:
        base = 0
        while True:
            x, y = fa.read(chunk), fb.read(chunk)
            assert len(x) == len(y)
            if not x:
                return out
            if x != y:
                for i in range(0, len(x), SECTOR):
                    if x[i:i + SECTOR] != y[i:i + SECTOR]:
                        out.append((base + i) // SECTOR)
            base += len(x)


@need_disc
def test_identity_build_is_byte_identical():
    binf = build.build(identity=True)
    assert build.sha1(binf) == build.sha1(build.ROM_BIN)


@need_disc
def test_edit_changes_only_its_sector():
    orig = (build.DISC / "tree" / "SYSTEM.CNF").read_bytes()
    edited = orig[:-1] + bytes([orig[-1] ^ 0x20])
    binf = build.build(changes={"SYSTEM.CNF": edited}, name="test_edit")
    try:
        assert len(differing_sectors(build.ROM_BIN, binf)) == 1
    finally:
        for ext in (".bin", ".cue", ".xml"):
            binf.with_suffix(ext).unlink(missing_ok=True)
        shutil.rmtree(build.BUILD / "files_test_edit", ignore_errors=True)


def test_unknown_edit_path_is_refused(tmp_path):
    if not (build.DISC / "layout.xml").is_file():
        pytest.skip("disc not unpacked")
    with pytest.raises(SystemExit):
        build.write_layout({"NOPE.BIN": tmp_path / "x"}, tmp_path / "x")
