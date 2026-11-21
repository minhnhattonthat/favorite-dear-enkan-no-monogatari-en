"""Graphics text (tools/gfx.py): every redrawn image decompresses to what was drawn, fits its slot and changes no
pixel outside its declared rects."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import gfx  # noqa: E402
import lzss  # noqa: E402

need_disc = pytest.mark.skipif(not (gfx.TREE / "GDATA.BIN").is_file(), reason="no unpacked disc")


def test_rows_parse():
    for e in gfx.entries():
        for r in gfx.rows(e):
            assert r["en"] and r["jp"], (e, r)


@need_disc
def test_images_fit_and_stay_in_rects():
    exe = (gfx.TREE / "PSX.EXE").read_bytes()
    gdata = (gfx.TREE / "GDATA.BIN").read_bytes()
    for e, (off, size, block) in gfx.images(exe, gdata).items():
        if e not in gfx.entries():  # a pack holding a mirrored copy: test_mirrored_packs
            continue
        img, new = gfx.redraw(exe, gdata, e)
        pix, w, h = img.pix, img.w, img.h
        assert len(block) <= size and img.decode(block) == img.raw(new)
        inside = set()
        for r in gfx.rows(e):
            x, y, rw, rh = (int(r[k]) for k in "xywh")
            assert x + rw <= w and y + rh <= h
            inside |= {yy * w + xx for yy in range(y, y + rh) for xx in range(x, x + rw)}
        assert [i for i in range(len(pix)) if pix[i] != new[i] and i not in inside] == []
    assert gfx.gdata_edit(gdata, exe) != gdata


@need_disc
def test_mirrored_packs():
    """e207 block 3 (the battle's copy of the status stamps) decodes to the redrawn e243; the other blocks are
    unchanged and the pack keeps its slot size"""
    exe = (gfx.TREE / "PSX.EXE").read_bytes()
    gdata = (gfx.TREE / "GDATA.BIN").read_bytes()
    out = gfx.images(exe, gdata)
    for e, places in gfx.MIRRORS.items():
        img, new = gfx.redraw(exe, gdata, e)
        for pack, index in places:
            off, size, blob = out[pack]
            assert len(blob) == size
            old = gfx.pack_blocks(gdata[off:off + size])
            got = gfx.pack_blocks(blob)
            assert len(got) == len(old)
            assert lzss.decompress(got[index] + bytes(16))[0] == img.raw(new)
            for i in range(len(old) - 1):
                if i != index:
                    assert got[i] == old[i], (pack, i)
            end = lzss.decompress(old[-1] + bytes(16))[1]
            assert got[-1][:end] == old[-1][:end]


def test_repack_shifts_offsets():
    blocks = [b"A" * 5, b"B" * 7, b"C" * 3 + bytes(9)]
    blob = bytes([12, 0, 0, 0, 17, 0, 0, 0, 24, 0, 0, 0]) + b"".join(blocks)
    out = gfx.repack(blob, 1, b"bb")
    assert len(out) == len(blob)
    assert gfx.pack_blocks(out)[:2] == [b"A" * 5, b"bb"]
    assert gfx.pack_blocks(out)[2].startswith(b"C" * 3)


@need_disc
def test_pss_files_fit_their_sectors_and_stay_in_rects():
    files = gfx.pss_files()
    assert files
    for e in [e for e in gfx.entries() if gfx.is_pss(e)]:
        img, new = gfx.redraw(None, None, e)
        block = files[gfx.pss_path(e)]
        orig = (gfx.TREE / gfx.pss_path(e)).read_bytes()
        assert img.kind == "pss4" and img.decode(orig) == img.raw(img.pix)  # the reader roundtrips the original
        assert -(-len(block) // gfx.SECTOR) <= -(-len(orig) // gfx.SECTOR) and img.decode(block) == img.raw(new)
        inside = {(yy, xx) for r in gfx.rows(e) for yy in range(int(r["y"]), int(r["y"]) + int(r["h"]))
                  for xx in range(int(r["x"]), int(r["x"]) + int(r["w"]))}
        assert [i for i in range(len(new)) if new[i] != img.pix[i] and divmod(i, img.w) not in inside] == []


def test_optimal_lzss_roundtrips_and_beats_greedy():
    import random
    rnd = random.Random(5)
    raw = bytes(rnd.choice(b"\0\0\0\x11\x12\x21") for _ in range(6000)) + bytes(3000)
    opt = lzss.compress_optimal(raw)
    assert lzss.decompress(opt + bytes(16))[0] == raw and len(opt) <= len(lzss.compress(raw))


@need_disc
def test_ink_erase_leaves_no_japanese():
    """bg `ink` rows: after redraw, every ink-coloured pixel in a rect belongs to the English letters"""
    exe = (gfx.TREE / "PSX.EXE").read_bytes()
    gdata = (gfx.TREE / "GDATA.BIN").read_bytes()
    for e in gfx.entries():
        img = gfx.Image(exe, gdata, e)
        rs = [r for r in gfx.rows(e) if r["bg"] == "ink"]
        if not rs:
            continue
        cleared = list(img.pix)
        for r in rs:
            gfx.clear(img.w, cleared, r)
        for r in rs:
            x, y, rw, rh = (int(r[k]) for k in "xywh")
            left = [(xx, yy) for yy in range(y, y + rh) for xx in range(x, x + rw)
                    if cleared[yy * img.w + xx] == int(r["ink"])]
            assert left == [], (e, r["jp"], left[:5])


def test_outline_index_erase_and_copy():
    """e203's ops on a synthetic 40x20 image: `i:` erase (with a texture offset), `oN` outline, `copy`"""
    w = 40
    pix = [1] * (w * 20)
    for xx in range(5, 9):  # "Japanese": fill 7 with outline 8, rows 3-4
        pix[3 * w + xx], pix[4 * w + xx] = 8, 7
    pix[17 * w + 6] = 2  # texture under the offset source
    row = dict(x="4", y="2", w="20", h="16", font="label", ink="7", shadow="o8", bg="i:7,8@0,14", align="l",
               jp="x", en="-")
    gfx.clear(w, pix, row)
    assert 7 not in pix and 8 not in pix and pix[3 * w + 6] == 2
    gfx.draw(w, pix, dict(row, en="I"))
    ink = {(i % w, i // w) for i, p in enumerate(pix) if p == 7}
    ring = {(i % w, i // w) for i, p in enumerate(pix) if p == 8}
    assert ink and all((x + dx, y + dy) in ink | ring for x, y in ink for dx in (-1, 0, 1) for dy in (-1, 0, 1))
    assert min(y for _, y in ring) == 2 and min(x for x, _ in ring) == 4  # the outline starts at the rect corner
    gfx.copy(w, pix, dict(x="30", y="0", w="2", h="20", en="4,0"))
    assert [pix[y * w + 30] for y in range(20)] == [pix[y * w + 4] for y in range(20)]


def test_label_font_has_every_letter():
    import labelfont
    for e in gfx.entries():
        for r in gfx.rows(e):
            if r["font"] == "label":
                assert labelfont.columns(r["en"])
