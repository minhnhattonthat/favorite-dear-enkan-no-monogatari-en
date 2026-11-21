"""tests/test_insert.py: the English path (tools/en.py, font_en.py, insert.py, asm/font.asm)."""
import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import en  # noqa: E402
import evscript  # noqa: E402
import extract  # noqa: E402
import font_en  # noqa: E402
import gdata  # noqa: E402
import insert  # noqa: E402

TREE = ROOT / "work" / "disc" / "tree"
need_disc = pytest.mark.skipif(not (TREE / "PSX.EXE").is_file(), reason="work/disc/tree missing")


def test_font_pairs_msb_first():
    """'A' then 'B': A in pixels 0-4, B in 6-10, bit 7 of byte 0 = leftmost (this game's order)"""
    rows = font_en.pair_rows(ord("A"), ord("B"))
    bits = ["".join("#" if (a << 8 | b) & (0x8000 >> x) else "." for x in range(12)) for a, b in rows]
    assert bits[3] == ".###..####.."
    assert bits[7] == "#####.#...#."
    assert all(r == "." * 12 for r in bits[:3])
    for c, g in font_en.glyphs().items():  # every glyph stays inside its 5-px half (bits 7..3)
        assert all(r & 0x07 == 0 for r in g), hex(c)


def test_encode_pairs():
    t = extract.event_table()
    b = en.encode("{spk:0100}Hi you!{n}Even{end}", t)
    assert en.decode_pairs(b) == "<FFF1><0001>Hi you! <FFF0>Even<FFFF>"
    assert all(en.is_pair(hw) for (hw,) in struct.iter_unpack("<H", en.encode("…—♥♪é ~", t)))
    assert min(font_en.chars()) * 0x101 >= evscript.EN_LO > gdata.NCODES


def test_marker_keeps_codes_and_width():
    jp = "あいう{n}えお{wait}{end}"
    m = insert.marker("e520.01A4", jp)
    assert m.startswith("[e520.1A4]") and m.endswith("{wait}{end}")
    assert [p for t, p in insert.runs(m) if not t] == ["{n}", "{wait}", "{end}"]
    assert len(insert.runs(m)[2][1]) == 4  # second run: 2 glyphs -> 4 letters


@need_disc
def test_identity_rebuild():
    """replacing every segment with its own bytes rebuilds every script byte-exact (rebuild/remap is sound)"""
    table = extract.event_table()
    for ent, data in extract.script_entries(TREE)[::7]:
        sc = evscript.Script(data)
        repl = {a: sc.seg_bytes((a, b)) for a, b in sc.segments}
        assert insert.script_bytes(sc, len(data), repl) == data, ent
    assert table


@need_disc
def test_marker_edits():
    """the marker build: every script still parses with its text as pair codes, nothing relocates, EXE strings
    land in PSX.EXE and OMK.EXE alike, the hook is in both, and the staff roll keeps its size"""
    rep = []
    out = insert.edits("marker", rep)
    assert set(out) == {"GDATA.BIN", "DATA/FIN.EXE"} | set(insert.EXE_DIRS)  # two scripts move: every directory
    gd = out["GDATA.BIN"]
    dirs = {name: out[name][o:o + 4 * gdata.GCOUNT] for name, o in insert.EXE_DIRS.items()}
    assert len(set(dirs.values())) == 1  # the six directories stay identical
    orig_dir = gdata.directory((TREE / "PSX.EXE").read_bytes())
    new_dir = gdata.directory(out["PSX.EXE"])
    moved = [i for i, (a, b) in enumerate(zip(orig_dir, new_dir)) if a != b]
    assert moved and all(new_dir[i][0] * 2048 >= len((TREE / "GDATA.BIN").read_bytes()) for i in moved)
    for i, (sec, cnt) in enumerate(new_dir):
        if i in moved or i % 5 == 0:
            data = gd[sec * 2048:(sec + cnt) * 2048]
            if gdata.kind(data) == "script":
                sc = evscript.Script(data)  # raises if the rebuilt script doesn't sweep
                assert sc.segments or i not in moved, i
    psx, omk = out["PSX.EXE"], out["OMK.EXE"]
    for name, exe in (("PSX.EXE", psx), ("OMK.EXE", omk)):
        h = insert.HOOKS[name]
        at = h["GLYPH"] - extract.EXE_VA
        op = struct.unpack_from("<I", exe, at)[0]
        assert op >> 26 == 2 and (op & 0x3FFFFFF) << 2 == h["FREE"] & 0x0FFFFFFF, name  # j FREE
    orig = (TREE / "PSX.EXE").read_bytes()
    for row in extract.read_tsv(extract.SCRIPT / "exe.tsv")[::20]:
        if "name-entry grid" in row["notes"]:
            continue
        off = int(row["id"][4:], 16)
        n = len(extract.exe_table().encode(row["jp"]))
        assert psx[off:off + n] == omk[off + extract.omk_delta(off):off + extract.omk_delta(off) + n] != orig[off:off + n]
    fin = (TREE / "DATA" / "FIN.EXE").read_bytes()
    assert len(out["DATA/FIN.EXE"]) == len(fin) and extract.fin_block(out["DATA/FIN.EXE"]) != extract.fin_block(fin)


@need_disc
def test_hook_space_is_zero():
    """the free runs the hook is assembled into are zero in the original EXEs"""
    for name, h in insert.HOOKS.items():
        exe = (TREE / name).read_bytes()
        a, b = h["FREE"] - extract.EXE_VA, h["FREE_END"] - extract.EXE_VA
        assert not any(exe[a:b]), name
        g = h["GLYPH"] - extract.EXE_VA
        assert exe[g:g + 8] == bytes.fromhex("c0ffbd273400b7af"), name  # addiu sp,-0x40 / sw s7,0x34(sp)
