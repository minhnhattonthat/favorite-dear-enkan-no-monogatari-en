"""codefind.py: find game 1's functions in this game's PSX.EXE by instruction match.

    python -X utf8 tools/codefind.py VADDR.. [--g1 ../favorite-dear-en/work/disc/tree/PSX.EXE] [--exe work/disc/tree/PSX.EXE] [--len 24]

For each game-1 vaddr, takes --len instruction words and searches this EXE with j/jal targets and the immediates
of lui/addiu/ori/loads/stores masked, so code that only moved matches. Prints the vaddr(s) found here.
(2026-11-21: draw-glyph 0x800FC97C -> 0x800D5888, glyph fetch 0x800FDCA8 -> 0x800D6BB4, EXE printer 0x800FC270 ->
0x800D517C, event printer 0x800CC9EC -> 0x800A5C48, event loader 0x800C7FF0 -> 0x800A13DC.)
"""
import argparse
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASKED = (0x0F, 0x09, 0x0D, 0x20, 0x21, 0x23, 0x24, 0x25, 0x28, 0x29, 0x2B)  # lui addiu ori lb lh lw lbu lhu sb sh sw


def norm(words):
    out = []
    for w in words:
        op = w >> 26
        out.append(w & 0xFC000000 if op in (2, 3) else w & 0xFFFF0000 if op in MASKED else w)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("vaddr", nargs="+")
    ap.add_argument("--g1", default=str(ROOT.parent / "favorite-dear-en/work/disc/tree/PSX.EXE"))
    ap.add_argument("--exe", default=str(ROOT / "work/disc/tree/PSX.EXE"))
    ap.add_argument("--len", type=int, default=24)
    a = ap.parse_args()
    g1, g3 = Path(a.g1).read_bytes(), Path(a.exe).read_bytes()
    b1, b3 = struct.unpack_from("<I", g1, 0x18)[0], struct.unpack_from("<I", g3, 0x18)[0]
    n3 = (len(g3) - 0x800) // 4
    w3 = norm(struct.unpack_from("<%dI" % n3, g3, 0x800))
    for arg in a.vaddr:
        va = int(arg, 0)
        pat = norm(struct.unpack_from("<%dI" % a.len, g1, va - b1 + 0x800))
        hits = [b3 + 4 * i for i in range(n3 - a.len) if w3[i] == pat[0] and w3[i:i + a.len] == pat]
        print(f"{va:#x} -> " + (" ".join(f"{h:#x}" for h in hits) or "not found"))


if __name__ == "__main__":
    main()
