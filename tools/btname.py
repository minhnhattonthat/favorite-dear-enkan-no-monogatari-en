"""btname.py: battle name plates (docs/re/graphics.md §Battle name plates) -> the data asm/btname.inc draws from.
Game 1's (../favorite-dear-en/tools/btname.py), addresses re-found here with tools/codefind.py (2026-11-22).

    python -X utf8 tools/btname.py extract      PSX.EXE name tables -> trans/btname.tsv (keeps `en`)
    python -X utf8 tools/btname.py check        every `en` fits a plate (64 px in fonts/caps4x7.txt); exit 1 if not
    python -X utf8 tools/btname.py png OUT.png  preview of every plate, 3x zoom

The game draws each unit's name (heroes: 8 one-byte codes at the start of the record that 0x80120FE8[unit id]
points to; enemies: 8 codes at 0x80115C64 + type*8) from the 8x8 kana font bt_font1-3.pss (GDATA e204-e206) into a
64x8 VRAM label per unit slot. asm/btname.inc replaces that routine: it renders the English name (upper case,
proportional, 1 px gaps) with caps4x7 into a RAM buffer and LoadImages it to the same label."""
import argparse
import csv
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TREE = ROOT / "work" / "disc" / "tree"
FONT = ROOT / "fonts" / "caps4x7.txt"
TSV = ROOT / "trans" / "btname.tsv"
EXE_VA = 0x8000F800  # RAM address of PSX.EXE file offset 0
ENEMY_VA, N_ENEMY = 0x80115C64, 254  # E000-E253 (game 1: 0x8013BFCC, same 254 names); E254 (0x80116454) is all
# zero (end). Bosses and dragons sit in E201-E253 (Siren = type 0xD8 = 216).
HERO_TABLE, N_HERO = 0x80120FE8, 19  # game 1: 0x80146210
GLYPHS = 0x801310FC  # game 1: 0x80154CF4. code -> descriptor (u32 page, u32 u, u16 v, ...): the 8x8 font cell a code draws
PLATE_W, ROWS, REC = 64, 7, 16
FIELDS = ["id", "jp", "en", "notes"]
# The 192 cells of bt_font1-3 (64 per image, 32 per 8-px row), read from the images (gfx.py png 204 205 206).
CELLS = (" ABCDEFGHIJKLMNOPQRSTUVWXYZシスセソタ" "0123456789ヲァィゥェォャュョッー" "アイウエオカキクケコサ"
         "チツテトナニヌネノハヒフヘホマミ" "ンガギグゲゴザジズゼゾ" "あいうえお" "ムメモヤユヨラリルレロワ"
         "ダヂヅデドバビブベボパピプペポ" "かきくけこさしすせそまみむめもやゆよらりるれろわんがぎぐげござじずぜゃゅょ"
         "たちつてとなにぬねのはひふへほだ" "っづでどばびぶべぼぱぴぷぺぽヴぞ")


def font(path=FONT):
    """{char: (width, [7 row ints, bit 0 = leftmost pixel])}"""
    out = {}
    for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        ch, *rows = line.split()
        ch = " " if ch == "sp" else ch
        w = len(rows[0]) if rows else 0
        if len(ch) != 1 or len(rows) != ROWS or any(len(r) != w or set(r) - set(".#") for r in rows) or ch in out:
            raise ValueError(f"{path}:{n}: want a character and {ROWS} equal-width rows of . and #")
        out[ch] = (w, [sum(1 << x for x, c in enumerate(r) if c == "#") for r in rows])
    return out


def width(text, f=None):
    """plate pixels `text` takes (upper-cased): glyph widths plus a 1-px gap between glyphs"""
    f = f or font()
    ws = [f[c][0] for c in text.upper()]
    return sum(ws) + max(0, len(ws) - 1)


def u32(exe, va):
    return struct.unpack_from("<I", exe, va - EXE_VA)[0]


def decode(exe, codes):
    """Japanese for 8x8-font codes, through the game's own code -> cell descriptors"""
    out = []
    for c in codes:
        p = u32(exe, GLYPHS + 4 * c)
        page, u = u32(exe, p), u32(exe, p + 4)
        v = struct.unpack_from("<H", exe, p + 8 - EXE_VA)[0]
        out.append(CELLS[page * 64 + (v - 240) // 8 * 32 + u // 8])
    return "".join(out)


def jp_names(exe):
    """[(id, jp)]: heroes H00-H18 (empty where the table has no record), enemies E000-E253"""
    out = []
    for i in range(N_HERO):
        p = u32(exe, HERO_TABLE + 4 * i)
        name = exe[p - EXE_VA:p - EXE_VA + 8].split(b"\0")[0] if p else b""
        out.append((f"H{i:02d}", decode(exe, name)))
    for i in range(N_ENEMY):
        a = ENEMY_VA + 8 * i - EXE_VA
        out.append((f"E{i:03d}", decode(exe, exe[a:a + 8].split(b"\0")[0])))
    return out


def read_rows(path=TSV):
    with open(path, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t", quoting=csv.QUOTE_NONE))
    for r in rows:
        if None in r or any(r[k] is None for k in FIELDS):
            raise ValueError(f"{path}: row {r.get('id')} does not have {len(FIELDS)} columns")
    return rows


def write_rows(rows, path=TSV):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, FIELDS, delimiter="\t", quoting=csv.QUOTE_NONE, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def errors(rows, f=None):
    f = f or font()
    errs = []
    for r in rows:
        en = r["en"]
        bad = sorted({c for c in en.upper() if c not in f})
        if bad:
            errs.append(f"{r['id']}: no glyph for {''.join(bad)!r}")
        elif width(en, f) > PLATE_W:
            errs.append(f"{r['id']}: {en!r} is {width(en, f)} px (plate {PLATE_W})")
        elif len(en) >= REC:
            errs.append(f"{r['id']}: {en!r} is over {REC - 1} letters")
        elif r["jp"] and not en:
            errs.append(f"{r['id']}: {r['jp']} has no English")
    return errs


def font_bin(f=None):
    """96 widths (ASCII 0x20-0x7F, 0 = no glyph) then 96 x 7 row bytes"""
    f = f or font()
    ws, rs = bytearray(96), bytearray(96 * ROWS)
    for ch, (w, rows) in f.items():
        i = ord(ch) - 0x20
        ws[i] = w
        rs[i * ROWS:(i + 1) * ROWS] = bytes(rows)
    return bytes(ws + rs)


def names_bin(rows, prefix):
    """REC-byte NUL-padded upper-case records for the rows whose id starts with `prefix`, in id order"""
    out = bytearray()
    for r in rows:
        if r["id"].startswith(prefix):
            out += r["en"].upper().encode("ascii").ljust(REC, b"\0")
    return bytes(out)


def hero_bin(rows=None):
    return names_bin(rows or read_rows(), "H")


def enemy_bin(rows=None):
    return names_bin(rows or read_rows(), "E")


def png(out, rows):
    from PIL import Image
    f = font()
    img = Image.new("RGB", ((PLATE_W + 8) * 4, ((len(rows) + 3) // 4) * 10), (60, 20, 20))
    px = img.load()
    for n, r in enumerate(rows):
        ox, oy, x = (n % 4) * (PLATE_W + 8), (n // 4) * 10 + 1, 0
        for c in r["en"].upper():
            w, glyph = f[c]
            for y, bits in enumerate(glyph):
                for dx in range(w):
                    if bits >> dx & 1 and x + dx < PLATE_W:
                        px[ox + x + dx, oy + y] = (255, 255, 255)
            x += w + 1
        for y in range(8):
            px[ox + PLATE_W, oy + y] = (255, 200, 0)  # plate edge
    img.resize((img.width * 3, img.height * 3), Image.NEAREST).save(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["extract", "check", "png"])
    ap.add_argument("out", nargs="?")
    a = ap.parse_args()
    if a.cmd == "extract":
        exe = (TREE / "PSX.EXE").read_bytes()
        old = {r["id"]: r for r in read_rows()} if TSV.exists() else {}
        rows = [{"id": i, "jp": jp, "en": old.get(i, {}).get("en", ""), "notes": old.get(i, {}).get("notes", "")}
                for i, jp in jp_names(exe)]
        write_rows(rows)
        print(f"{TSV.relative_to(ROOT)}: {len(rows)} rows")
        return 0
    rows = read_rows()
    if a.cmd == "png":
        png(a.out, rows)
        return 0
    errs = errors(rows)
    for e in errs:
        print(e)
    print(f"btname: {len(rows)} rows, {len(errs)} errors")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
