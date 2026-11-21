"""save.py: read and edit Favorite Dear: Enkan no Monogatari saves on a PS1 memory card image (.mcd), fixing both checksums.

    python -X utf8 tools/debug/save.py ls CARD.mcd                       saves on the card: week, AP, name, sums ok?
    python -X utf8 tools/debug/save.py set CARD.mcd OUT.mcd [--save 1] [--week N] [--ap N] [--name ラビエル]
                                       [--poke 0x199C=9600 ...] [--bad-sum]
    python -X utf8 tools/debug/save.py check CARD.mcd                    exit 1 if any save's c0/c1 is wrong

Always start from a game-written card (work/saves/week1.mcd, week2.mcd), never from zeros. --save picks the Nth
save file on the card (1-3, in directory order). --poke writes raw hex bytes at a save-file offset (repeatable).
--bad-sum writes a deliberately wrong c0 (negative test: the game must reject it).

Save file (16 KB, two card blocks; offsets from the file start; docs/re/debug.md "Save file layout"):
  0x200 u16 c0 = sum(bytes 0x204..0x3FFF) & 0x0FFF      0x202 u16 c1 = sum(bytes 0x204..0x22B) & 0x0FFF
  0x204 angel name, 6 u16 font codes (tbl/jp.tbl), 0xFFFF padded    0x215 u8 week (header copy)
  0x199C u16 angel AP    0x19AE angel name again (same codes, 0xFFFF padded)    0x2838 u8 week
(Enkan no Monogatari: game 1's layout and sums, the second week copy moved from 0x275C to 0x2838; product code
BISLPS-03286. Mapped 2026-11-21 by diffing game-written week-1 and week-2 saves.)"""
import argparse
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import mcd  # noqa: E402

PRODUCT = "BISLPS-03286"  # game 1: BISLPS-01759
FILE = 16384
NAME_LEN = 6
FIELDS = {"week": [(0x215, 1), (0x2838, 1)], "ap": [(0x199C, 2)]}  # game 1: second week copy at 0x275C
NAME_AT = (0x204, 0x19AE)


def table():
    enc, dec = {}, {}
    for line in open(os.path.join(REPO, "tbl", "jp.tbl"), encoding="utf-8"):
        line = line.rstrip("\n")
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        if len(k) != 4 or len(v) != 1:
            continue
        code = int(k[2:4] + k[0:2], 16)
        dec.setdefault(code, v)
        enc.setdefault(v, code)
    return enc, dec


def saves(card):
    """[(n, offset of the save file in the card image)] for every first-block directory entry."""
    out = []
    for slot, state, size, nxt, name, ok in mcd.entries(card):
        if state == 0x51 and name.startswith(PRODUCT):
            out.append((len(out) + 1, slot * mcd.BLOCK))
    return out


def sums(f):
    # both 12-bit: a game-written 1-halfword name (header sum 0x10E9) stores c1 0x0E9 (tests/test_debug.py)
    return sum(f[0x204:FILE]) & 0x0FFF, sum(f[0x204:0x22C]) & 0x0FFF


def fix(f, bad=False):
    c0, c1 = sums(f)
    if bad:
        c0 = (c0 + 1) & 0x0FFF
    struct.pack_into("<HH", f, 0x200, c0, c1)


def get(f, field):
    off, n = FIELDS[field][-1]
    return int.from_bytes(f[off:off + n], "little")


def name_of(f, dec):
    out = []
    for i in range(NAME_LEN):
        c = struct.unpack_from("<H", f, NAME_AT[0] + 2 * i)[0]
        if c == 0xFFFF:
            break
        out.append(dec.get(c, f"[{c:04X}]"))
    return "".join(out)


def set_name(f, name, enc):
    assert 1 <= len(name) <= NAME_LEN, f"name must be 1-{NAME_LEN} characters"
    codes = []
    for ch in name:
        assert ch in enc, f"{ch!r} has no font code in tbl/jp.tbl"
        codes.append(enc[ch])
    codes += [0xFFFF] * (NAME_LEN - len(codes))
    for at in NAME_AT:
        for i, c in enumerate(codes):
            struct.pack_into("<H", f, at + 2 * i, c)


def set_name_en(f, name):
    """English name as pair codes (tools/en.py, as asm/name.inc commits them): 2 letters per halfword, 10 letters
    from the name screen (12 fit the 6 halfwords: a stress case)"""
    sys.path.insert(0, os.path.join(REPO, "tools"))
    import en
    codes = en.pairs(name)
    assert 1 <= len(codes) <= NAME_LEN, f"name must be 1-{2 * NAME_LEN} letters"
    codes += [0xFFFF] * (NAME_LEN - len(codes))
    for at in NAME_AT:
        for i, c in enumerate(codes):
            struct.pack_into("<H", f, at + 2 * i, c)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["ls", "set", "check"])
    ap.add_argument("card")
    ap.add_argument("out", nargs="?")
    ap.add_argument("--save", type=int, default=1)
    ap.add_argument("--week", type=int)
    ap.add_argument("--ap", type=int)
    ap.add_argument("--name")
    ap.add_argument("--name-en", help="English name, stored as pair codes (e.g. WWWWWWWWWW)")
    ap.add_argument("--poke", action="append", default=[], help="OFFSET=HEXBYTES, e.g. 0x199C=e803")
    ap.add_argument("--bad-sum", action="store_true")
    a = ap.parse_args()
    card = bytearray(open(a.card, "rb").read())
    assert len(card) == mcd.SIZE, f"{a.card}: {len(card)} bytes, want {mcd.SIZE}"
    enc, dec = table()
    found = saves(card)
    if a.cmd in ("ls", "check"):
        bad = 0
        for n, at in found:
            f = card[at:at + FILE]
            want, have = sums(f), struct.unpack_from("<HH", f, 0x200)
            ok = tuple(want) == tuple(have)
            bad += not ok
            if a.cmd == "ls":
                print(f"save {n}: week {get(f, 'week')}  AP {get(f, 'ap')}  name {name_of(f, dec)}  "
                      f"sums {'ok' if ok else f'BAD (have {have[0]:#x}/{have[1]:#x}, want {want[0]:#x}/{want[1]:#x})'}")
        return 1 if bad else 0
    if not a.out:
        ap.error("set needs OUT.mcd")
    saves_by_n = dict(found)
    if a.save not in saves_by_n:
        sys.exit(f"no save {a.save} on {a.card} (has {sorted(saves_by_n)})")
    at = saves_by_n[a.save]
    f = card[at:at + FILE]
    for field in ("week", "ap"):
        v = getattr(a, field)
        if v is not None:
            for off, n in FIELDS[field]:
                assert 0 <= v < 256 ** n, f"{field} {v} does not fit {n} byte(s)"
                f[off:off + n] = v.to_bytes(n, "little")
    if a.name:
        set_name(f, a.name, enc)
    if a.name_en:
        set_name_en(f, a.name_en)
    for p in a.poke:
        off, hx = p.split("=")
        b = bytes.fromhex(hx)
        off = int(off, 0)
        assert 0x204 <= off and off + len(b) <= FILE, f"poke {p} outside the checksummed data"
        f[off:off + len(b)] = b
    fix(f, a.bad_sum)
    card[at:at + FILE] = f
    open(a.out, "wb").write(card)
    print(f"wrote {a.out}: save {a.save} week {get(f, 'week')} AP {get(f, 'ap')} name {name_of(f, dec)}"
          f"{'  (c0 deliberately wrong)' if a.bad_sum else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
