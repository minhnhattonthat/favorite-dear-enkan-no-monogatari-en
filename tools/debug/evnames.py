"""evnames.py: event ids, GDATA entries and names (game 1's names where the hash matches).

    python -X utf8 tools/debug/evnames.py [--new] [--ids]

The loader (load_event 0x800A161C) keeps no names: event id -> u16 name hash (PSX.EXE table 0x8014FCFC), found in
the 570-hash list at 0x801040E4, whose index + 395 is the GDATA entry. Game 1's 9-byte name table (its PSX.EXE
0x80173640) gives the names: 460 of its 462 hash into this list (443 slots). The 127 unnamed slots are new here or
loaded without an id (no name known: 16-bit hashes collide, so brute force gives junk); ids 462-595 are new to
this game. warp.py takes any entry as eNNN. Prints `entry name ids` per line
(`--new`: only unnamed ones; `--ids`: id -> entry instead).
"""
import argparse
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXE = ROOT / "work/disc/tree/PSX.EXE"
G1EXE = ROOT.parent / "favorite-dear-en/work/disc/tree/PSX.EXE"
IDTAB, NIDS = 0x8014FCFC, 600
HASHES, NHASH, GBASE = 0x801040E4, 570, 395


def name_hash(s):
    total, m = 0, 1
    for c in s.encode():
        total = (total + c * m) & 0xFFFFFFFF
        m = (m * 11) & 0xFFFFFFFF
    return (total + (total >> 16)) & 0xFFFF


def u16s(data, va, n):
    return list(struct.unpack_from("<%dH" % n, data, va - 0x80010000 + 0x800))


def g1_names():
    g = G1EXE.read_bytes()
    o = 0x80173640 - 0x80010000 + 0x800
    return [g[o + 9 * k:o + 9 * k + 9].split(b"\0")[0].decode() for k in range(462)]


def table():
    """[(entry, name or '', [ids])] for the 570 hash-list slots."""
    d = EXE.read_bytes()
    hashes, ids = u16s(d, HASHES, NHASH), u16s(d, IDTAB, NIDS)
    names = {name_hash(n): n for n in g1_names()}
    return [(GBASE + i, names.get(h, ""), [k for k, v in enumerate(ids) if v == h]) for i, h in enumerate(hashes)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--new", action="store_true")
    ap.add_argument("--ids", action="store_true")
    a = ap.parse_args()
    rows = table()
    if a.ids:
        by = {i: (e, n) for e, n, ids in rows for i in ids}
        for i in sorted(by):
            print(f"{i}\te{by[i][0]}\t{by[i][1]}")
        return
    for e, n, ids in rows:
        if n and a.new:
            continue
        print(f"e{e}\t{n or '-'}\t{','.join(map(str, ids))}")


if __name__ == "__main__":
    main()
