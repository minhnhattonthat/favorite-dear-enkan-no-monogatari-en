"""Hero status Equip box (asm/equip.inc, game 1's issue #2): every equippable item's English name renders in the
caps4x7 font within the 76 px between x 77 and the box's inner edge (x 152), with no character the font lacks."""
import re
import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import btname  # noqa: E402

EXE = btname.TREE / "PSX.EXE"
ITEMS, ITEM_SIZE = 0x8018E478, 20      # item records: +1 type (0-18 = equipment); game 1 0x800213D0
NAMES = 0x80145CBC                     # u32 string pointers, index from 0x80099208 (below); game 1 0x80169778
CODES = 0xFF                           # u8 item codes (the bag stores bytes; 0xFFFF = empty slot)
ROOM = 152 - 77 + 1


def off(va):
    return va - 0x80010000 + 0x800


def name_index(code):
    """0x80099208: the string-table entry of an item code"""
    return code + (0x8C if code < 0xED else 0x100 if code < 0xF9 else 0x144)


def equipment_names():
    exe = EXE.read_bytes()
    rows = {}
    for line in (ROOT / "script" / "exe.tsv").read_text(encoding="utf-8").splitlines()[1:]:
        cols = line.split("\t")
        rows[cols[0]] = cols
    names = []
    for code in range(CODES):
        if exe[off(ITEMS + ITEM_SIZE * code) + 1] > 18:
            continue
        ptr = struct.unpack_from("<I", exe, off(NAMES + 4 * name_index(code)))[0]
        row = rows.get(f"PSX.{off(ptr):X}")
        names.append((code, re.sub(r"\{[^}]*\}", "", row[2]).rstrip() if row else ""))
    return names


@pytest.mark.skipif(not EXE.is_file(), reason="no unpacked disc")
def test_equipment_names_fit_caps_font():
    f = btname.font()
    names = equipment_names()
    assert len(names) > 150
    assert all(n for c, n in names), [c for c, n in names if not n]
    bad = [(c, n, btname.width(n, f) if all(ch in f for ch in n.upper()) else None) for c, n in names
           if any(ch not in f for ch in n.upper()) or btname.width(n, f) > ROOM]
    assert bad == []
