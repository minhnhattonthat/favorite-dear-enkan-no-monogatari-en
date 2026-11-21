"""fontmatch.py: proposed character for each cell of the game's 12x12 font, by matching MS Gothic 12 px bitmaps.

    python -X utf8 tools/fontmatch.py EXE OUT.tsv [--sheet OUT.png]

The game font is MS Gothic's 12 px embedded bitmap (verified 2026-11-20: almost every cell matches a rendered
character exactly), so each cell takes the best Dice overlap (shifts of -1..1 px) over all Shift-JIS characters.
Output TSV: code, char, score, runner-up char, runner-up score. Ties (壺/壼) and scores < 1 need an eye; the
hand-checked result lives in tbl/jp.tbl, which is what the tools use.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from font import glyph  # noqa: E402

NCODES = 0x6F0  # this game: 0x6EF 築 is the last glyph, 0x6F0+ is other data (game 1: 0x66C)
FONT = "C:/Windows/Fonts/msgothic.ttc"


def sjis_chars(lead_lo, lead_hi):
    out = []
    for lead in range(lead_lo, lead_hi + 1):
        if 0xA0 <= lead <= 0xDF:
            continue
        for trail in list(range(0x40, 0x7F)) + list(range(0x80, 0xFD)):
            try:
                ch = bytes([lead, trail]).decode("cp932")
            except UnicodeDecodeError:
                continue
            if len(ch) == 1:
                out.append(ch)
    return out


def render(chars):
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype(FONT, 12, index=0)
    arr = np.zeros((len(chars), 12, 12), np.float32)
    for i, ch in enumerate(chars):
        im = Image.new("1", (12, 12), 0)
        d = ImageDraw.Draw(im)
        d.fontmode = "1"
        d.text((0, 0), ch, font=f, fill=1)
        arr[i] = np.array(im, np.float32)
    return arr


def dice(game, cand):
    """Dice overlap of binary bitmaps, best over candidate shifts of -1..1 px."""
    g = game.reshape(len(game), -1)
    gs = g.sum(1, keepdims=True)
    best = np.zeros((len(game), len(cand)), np.float32)
    p = np.pad(cand, ((0, 0), (1, 1), (1, 1)))
    for dy in range(3):
        for dx in range(3):
            c = p[:, dy:dy + 12, dx:dx + 12].reshape(len(cand), -1)
            best = np.maximum(best, 2 * (g @ c.T) / np.maximum(gs + c.sum(1)[None, :], 1))
    return best


def match(exe):
    """[(code, char, score, char2, score2)] for every non-empty cell."""
    game = np.array([glyph(exe, c) for c in range(NCODES)], np.float32)
    chars = sjis_chars(0x81, 0xEA)
    S = dice(game, render(chars))
    out = []
    for c in range(NCODES):
        if game[c].sum() == 0:
            out.append((c, "", 0.0, "", 0.0))
            continue
        o = np.argsort(-S[c])[:2]
        out.append((c, chars[o[0]], float(S[c, o[0]]), chars[o[1]], float(S[c, o[1]])))
    return game, out


def sheet(game, res, out, per=32, z=3):
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype(FONT, 24, index=0)
    sf = ImageFont.truetype(FONT, 11, index=0)
    cw, ch = 12 * z + 6, 12 * z + 34
    rows = (len(game) + per - 1) // per
    im = Image.new("RGB", (per * cw + 40, rows * ch), "white")
    d = ImageDraw.Draw(im)
    for c, txt, sc, _, _ in res:
        r, k = divmod(c, per)
        x0, y0 = 40 + k * cw, r * ch
        if k == 0:
            d.text((0, y0 + 4), f"{c:03X}", fill="blue", font=sf)
        for y in range(12):
            for x in range(12):
                if game[c, y, x]:
                    d.rectangle([x0 + x * z, y0 + y * z, x0 + x * z + z - 1, y0 + y * z + z - 1], fill="black")
        d.text((x0 + 4, y0 + 12 * z + 1), txt, fill="red" if sc < 0.99 else "darkgreen", font=f)
    im.save(out)


def main():
    exe = open(sys.argv[1], "rb").read()
    game, res = match(exe)
    with open(sys.argv[2], "w", encoding="utf-8", newline="\n") as fh:
        for r in res:
            fh.write("%04X\t%s\t%.3f\t%s\t%.3f\n" % r)
    if "--sheet" in sys.argv:
        sheet(game, res, sys.argv[sys.argv.index("--sheet") + 1])


if __name__ == "__main__":
    main()
