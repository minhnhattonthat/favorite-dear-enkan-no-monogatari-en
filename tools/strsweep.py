"""strsweep.py: EXE offsets that code or data reference (u32 vaddr, or lui + addiu/ori/load/store within 16 words)
and that start a valid FFFF-terminated font-code string with at least one glyph. Finds strings no scan or region
covers (docs/re/text.md "EXE text map"); most hits outside the text regions are code tables (glyph soup).

    python -X utf8 tools/strsweep.py [EXE] [--min-off 0x100000] [--outside]   (--outside: skip extract.py regions)
"""
import argparse
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import extract  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
VA = extract.EXE_VA
OPS = (0x09, 0x0D, 0x20, 0x21, 0x23, 0x24, 0x25, 0x28, 0x29, 0x2B)  # addiu ori lb lh lw lbu lhu sb sh sw


def references(d):
    """{file offset: set('p' u32 | 'c' code)}"""
    words = struct.unpack_from("<%dI" % ((len(d) - 0x800) // 4), d, 0x800)
    out = {}
    for i, w in enumerate(words):
        f = w - VA
        if 0x800 <= f < len(d) and f % 2 == 0:
            out.setdefault(f, set()).add("p")
        op = w >> 26
        if op not in OPS:
            continue
        rs = (w >> 21) & 31
        for j in range(i - 1, max(0, i - 16) - 1, -1):
            v = words[j]
            if v >> 26 == 0x0F and (v >> 16) & 31 == rs:
                imm = w & 0xFFFF
                va = (v & 0xFFFF) << 16 | imm if op == 0x0D else ((v & 0xFFFF) << 16) + (imm ^ 0x8000) - 0x8000
                f = (va & 0xFFFFFFFF) - VA
                if 0x800 <= f < len(d) and f % 2 == 0:
                    out.setdefault(f, set()).add("c")
                break
    return out


def string_at(d, o, limit=1200):
    """(end, glyph count) of a valid string at o, else (None, 0)"""
    j, glyph = o, 0
    while j < min(len(d), o + limit):
        v = struct.unpack_from("<H", d, j)[0]
        if v == 0xFFFF:
            return j + 2, glyph
        if v < extract.evscript.NCODES:
            glyph += v not in (0, 0x5E9)
            j += 2
        elif v in extract.EXE_ARGS:
            j += 2 + 2 * extract.EXE_ARGS[v]
        else:
            return None, 0
    return None, 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe", nargs="?", default=str(ROOT / "work/disc/tree/PSX.EXE"))
    ap.add_argument("--min-off", type=lambda s: int(s, 0), default=0x800)
    ap.add_argument("--outside", action="store_true")
    a = ap.parse_args()
    d = Path(a.exe).read_bytes()
    t = extract.exe_table()
    skip = extract.EXE_REGIONS + extract.EXE_GRIDS if a.outside else []
    for f, kinds in sorted(references(d).items()):
        if f < a.min_off or any(lo <= f < hi for lo, hi in skip):
            continue
        e, g = string_at(d, f)
        if e and g:
            print("%06X\t%06X\t%s\t%s" % (f, e, "".join(sorted(kinds)), t.decode(d[f:e], 0, e - f)[0][:60]))


if __name__ == "__main__":
    main()
