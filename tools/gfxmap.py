"""gfxmap.py: map game 1's graphics-text sources to this disc, and list images that are new in this game.

    python -X utf8 tools/gfxmap.py [--g1 ../favorite-dear-en]

Game 1 (`../favorite-dear-en/docs/re/graphics.md`) surveyed and redrew every Japanese-lettered image. This game
re-uses most of game 1's GDATA.BIN byte for byte (39.5k of 43.2k sectors), so each game-1 source is looked up here
by content: a GDATA directory entry (game 1 table PSX.EXE 0x4C50, u32 sector + u32 size) or a TIM found by
game 1's sector scan, matched against this disc's directory entries (tools/gdata.py) and sector starts.
Then every image in this game's GDATA (directory TIMs + LZSS images + scanned TIMs) whose bytes are not in game 1's
GDATA is listed: those are the ones to look at by eye for new Japanese lettering.
"""
import argparse
import hashlib
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import gdata  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
# game-1 graphics-text sources (graphics.md): ('e', directory index) or ('s', sector of a scanned TIM)
G1_SOURCES = [("e", 8), ("e", 9), ("e", 12), ("e", 13), ("e", 14), ("e", 15), ("e", 16), ("e", 142), ("e", 143),
              ("e", 144), ("e", 145), ("e", 203), ("e", 204), ("e", 205), ("e", 206), ("e", 207), ("e", 243),
              ("s", 40127), ("s", 40203), ("s", 40279), ("s", 15228), ("s", 41039), ("s", 41115)]


def tim_size(d, o=0):
    """byte size of a TIM at d[o:], or 0 if it isn't one"""
    if d[o:o + 4] != b"\x10\0\0\0":
        return 0
    flags = struct.unpack_from("<I", d, o + 4)[0]
    if flags & ~0xF or (flags & 7) > 3:
        return 0
    p = o + 8
    if flags & 8:
        n = struct.unpack_from("<I", d, p)[0]
        if n < 12 or p + n > len(d):
            return 0
        p += n
    n = struct.unpack_from("<I", d, p)[0]
    if n < 12 or p + n > len(d):
        return 0
    return p + n - o


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--g1", default=str(ROOT.parent / "favorite-dear-en"))
    a = ap.parse_args()
    t1 = Path(a.g1) / "work/disc/tree"
    exe1, g1 = (t1 / "PSX.EXE").read_bytes(), (t1 / "GDATA.BIN").read_bytes()
    es3 = gdata.entries(ROOT / "work/disc/tree")
    g3 = (ROOT / "work/disc/tree/GDATA.BIN").read_bytes()
    print("## game-1 graphics-text sources on this disc")
    for kind, n in G1_SOURCES:
        if kind == "e":
            sec, size = struct.unpack_from("<II", exe1, 0x4C50 + 8 * n)
            data = g1[sec * 2048:sec * 2048 + size]
            label = f"game-1 e{n:03d}"
        else:
            sec = n
            size = tim_size(g1, sec * 2048)
            data = g1[sec * 2048:sec * 2048 + size]
            label = f"game-1 s{n}"
        hits = [i for i, s3, c3, _, d3 in es3 if d3[:size] == data]
        pos = g3.find(data)
        while pos >= 0 and pos % 2048:
            pos = g3.find(data, pos + 1)
        where = f"entries {hits}" if hits else ("no directory entry" + (f", sector {pos // 2048}" if pos >= 0 else ""))
        print(f"{label}\t{size:#x} B\t{'SAME' if pos >= 0 else 'CHANGED/ABSENT'}\t{where}")
    # images new in this game
    h1 = {hashlib.md5(g1[s * 2048:(s + 1) * 2048]).digest() for s in range(len(g1) // 2048)}
    print("## images in this GDATA whose first sector is not in game 1's GDATA")
    seen = set()
    for i, sec, cnt, kd, d in es3:
        if kd == "script":
            continue
        if hashlib.md5(d[:2048]).digest() not in h1:
            seen.add(sec)
            print(f"entry {i}\tsector {sec}\t{kd}\t{cnt} sectors")
    for s in range(len(g3) // 2048):
        if s in seen:
            continue
        n = tim_size(g3, s * 2048)
        if n >= 0x1000 and hashlib.md5(g3[s * 2048:(s + 1) * 2048]).digest() not in h1:
            w, h = struct.unpack_from("<HH", g3, s * 2048 + 8 + (struct.unpack_from("<I", g3, s * 2048 + 8)[0]
                                                             if g3[s * 2048 + 4] & 8 else 0) + 8)
            print(f"scan\tsector {s}\ttim\t{n:#x} B\t{w}x{h} halfwords")


if __name__ == "__main__":
    main()
