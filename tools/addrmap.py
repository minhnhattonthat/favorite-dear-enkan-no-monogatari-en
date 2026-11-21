"""addrmap.py: map a game-1 data address to this game's PSX.EXE through the code that uses it.

    python -X utf8 tools/addrmap.py ADDR.. [--g1 ../favorite-dear-en/work/disc/tree/PSX.EXE] [--exe work/disc/tree/PSX.EXE]
                                     [--win 10] [--exe3-only]

For every game-1 site that builds ADDR with lui + addiu/ori/load/store (retools xref), takes the instruction window
around the site, finds it here with immediates and jump targets masked (codefind's normalisation), and reads the
address the matched code builds at the same spot. Prints each candidate with its vote count (how many game-1 sites
agree): a high count is a strong match, a single vote a lead to check in RAM. Addresses inside a table keep their
offset: give the address the code builds (the table base), then add the offset yourself.
"""
import argparse
import struct
from collections import Counter
from pathlib import Path

from codefind import norm
from retools import Exe

ROOT = Path(__file__).resolve().parents[1]
LOAD_STORE = (0x09, 0x23, 0x21, 0x20, 0x24, 0x25, 0x2B, 0x29, 0x28)


def built_at(e, lo_va):
    """Address built by the lui/lo pair whose lo half is at lo_va (searching back 16 words for the lui)."""
    w2 = e.word(lo_va)
    rs = (w2 >> 21) & 31
    for k in range(1, 17):
        w = e.word(lo_va - 4 * k)
        if w >> 26 == 0x0F and (w >> 16) & 31 == rs:
            hi = (w & 0xFFFF) << 16
            imm = w2 & 0xFFFF
            if w2 >> 26 == 0x0D:
                return hi | imm
            return (hi + (imm - 0x10000 if imm & 0x8000 else imm)) & 0xFFFFFFFF
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("addr", nargs="+")
    ap.add_argument("--g1", default=str(ROOT.parent / "favorite-dear-en/work/disc/tree/PSX.EXE"))
    ap.add_argument("--exe", default=str(ROOT / "work/disc/tree/PSX.EXE"))
    ap.add_argument("--win", type=int, default=10, help="instructions each side of the site to match (default 10)")
    a = ap.parse_args()
    g1, g3 = Exe(a.g1), Exe(a.exe)
    n3 = (len(g3.data) - 0x800) // 4
    w3 = norm(struct.unpack_from("<%dI" % n3, g3.data, 0x800))
    for arg in a.addr:
        target = int(arg, 0)
        votes = Counter()
        sites = g1.xref(target)
        for site, _ in sites:
            for win in (a.win, a.win // 2):
                lo = max(g1.base, site - 4 * win)
                n = (site - lo) // 4 + win + 1
                o = g1.off(lo)
                pat = norm(struct.unpack_from("<%dI" % n, g1.data, o))
                hits = [g3.base + 4 * i for i in range(n3 - n) if w3[i] == pat[0] and w3[i:i + n] == pat]
                if len(hits) == 1:
                    v = built_at(g3, hits[0] + (site - lo))
                    if v is not None:
                        votes[v] += 1
                    break
        print(f"{target:08x}: {len(sites)} game-1 sites ->",
              ", ".join(f"{v:08x} x{c}" for v, c in votes.most_common(5)) or "no match")


if __name__ == "__main__":
    main()
