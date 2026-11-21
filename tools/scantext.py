"""scantext.py: find dialogue strings (16-bit font codes ending in 0xFFFF) in a binary.

    python -X utf8 tools/scantext.py FILE [--min 3] [--regions] [--show N]

A string is a halfword-aligned run of font codes (< NCODES) or 0xFFFE/0xFFFC/0xFFFD/0xFFFB, ended by 0xFFFF, with at least
--min codes of which at least one is kana or kanji (0x023-0x5CC) to keep zero runs and code out. --regions merges
strings closer than 64 bytes into regions and prints them; default prints each string's offset and decoded text.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from tbl import Table  # noqa: E402

TBL = Path(__file__).resolve().parents[1] / "tbl" / "jp.tbl"
CTRL = {0xFFFE, 0xFFFC, 0xFFFD, 0xFFFB, 0xFF00, 0xFF10, 0xFF90}  # args are small values, so they pass as codes
NCODES = 0x6F0  # font cells (tools/fontmatch.py; game 1 had 0x66C)
KANA_KANJI = [(0x23, 0x5CC), (0x5E1, 0x6EF)]


def scan(data, minlen=3):
    """[(start, end)] byte ranges, end exclusive and including the FFFF."""
    out = []
    n = len(data) // 2
    hw = memoryview(data)[:n * 2].cast("H")
    start = 0
    for i in range(n):
        v = hw[i]
        if v == 0xFFFF:
            run = hw[start:i]
            if len(run) >= minlen and any(lo <= c <= hi for c in run for lo, hi in KANA_KANJI):
                out.append((start * 2, i * 2 + 2))
            start = i + 1
        elif v < NCODES or v in CTRL:
            continue
        else:
            start = i + 1
    return out


def regions(strings, gap=64):
    reg = []
    for s, e in strings:
        if reg and s - reg[-1][1] <= gap:
            reg[-1][1] = e
            reg[-1][2] += 1
        else:
            reg.append([s, e, 1])
    return reg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--min", type=int, default=3)
    ap.add_argument("--regions", action="store_true")
    ap.add_argument("--show", type=int, default=0)
    a = ap.parse_args()
    data = Path(a.file).read_bytes()
    strings = scan(data, a.min)
    if a.regions:
        for s, e, k in regions(strings):
            print(f"{s:08X}-{e:08X} {e - s:7d} B {k:5d} strings")
        print(f"total {len(strings)} strings, {sum(e - s for s, e in strings)} B")
        return
    t = Table.load(TBL)
    for s, e in strings[:a.show or None]:
        print(f"{s:08X}\t{t.decode(data[s:e], 0)[0]}")


if __name__ == "__main__":
    main()
