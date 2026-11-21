"""Battle name plates (asm/btname.inc, tools/btname.py, trans/btname.tsv)."""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import btname  # noqa: E402
import insert  # noqa: E402

VA = 0x8000F800


def test_rows_fit():
    assert btname.errors(btname.read_rows()) == []


def test_tables_are_the_jp_names():
    """the re-found tables decode to the extracted names (a wrong address would decode to garbage)"""
    exe = (insert.TREE / "PSX.EXE").read_bytes()
    jp = dict(btname.jp_names(exe))
    rows = {r["id"]: r["jp"] for r in btname.read_rows()}
    assert jp == rows
    assert jp["H01"] == "シーヴァス" and jp["E216"] == "サイレン"


def test_routine_replaced_in_place():
    exe = (insert.TREE / "PSX.EXE").read_bytes()
    out = insert.assemble(exe, "btname.asm")
    assert struct.unpack_from("<I", exe, 0x8001A680 - VA)[0] == 0x27BDFFC0  # original: addiu sp, sp, -0x40
    assert struct.unpack_from("<I", out, 0x8001A680 - VA)[0] == 0x27BDFFD0  # ours: addiu sp, sp, -0x30
    assert out[0x8001A840 - VA:] [:64] == exe[0x8001A840 - VA:][:64]  # the next function is untouched
    hero = out[0x80115C64 + 96 + 96 * 7 - VA:][:19 * 16]
    assert hero[16:32].rstrip(b"\0") == b"SIEVAS"
