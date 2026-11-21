"""font.py: the game's 12x12 1bpp dialogue font in PSX.EXE.

Layout (verified 2026-11-21 by disassembling the glyph fetch 0x800D6BB4 and pixel read 0x800D6CFC, the same
routines as game 1's 0x800FDCA8 / 0x800FDDF0): one 1bpp image, 192 px wide (16 glyphs x 12 px), 24 bytes per pixel
row. Glyph for code c sits at cell (c & 15, c >> 4). Font pointer: draw-glyph 0x800D5888 passes 0x80109EC0 =
PSX.EXE file offset 0xFA6C0. Unlike game 1 (`../favorite-dear-en`, 0x1213C0, bit 0 = leftmost pixel) this game
reads bits MSB-first (bit 7 = leftmost: `1 << (7 - (px & 7))` at 0x800D6D1C).

    python -X utf8 tools/font.py sheet EXE OUT.png [count]   labelled sheet of every glyph cell
"""
import sys

FONT_OFF = 0xFA6C0
ROW_BYTES = 24
CELL = 12
COLS = 16
MSB_FIRST = True


def glyph(exe, code, off=FONT_OFF, msb=MSB_FIRST):
    """12x12 list of rows (0/1) for a code."""
    gx, gy = (code & 15) * CELL, (code >> 4) * CELL
    rows = []
    for y in range(CELL):
        row = []
        for x in range(CELL):
            px = (gy + y) * ROW_BYTES * 8 + gx + x
            sh = 7 - (px & 7) if msb else px & 7
            row.append((exe[off + (px >> 3)] >> sh) & 1)
        rows.append(row)
    return rows


def sheet(exe, out, count, zoom=2):
    from PIL import Image, ImageDraw
    cw = (CELL + 2) * zoom
    lab = 34
    per = 32
    nrows = (count + per - 1) // per
    im = Image.new("L", (per * cw + lab, nrows * cw), 255)
    dr = ImageDraw.Draw(im)
    for c in range(count):
        r, k = divmod(c, per)
        if k == 0:
            dr.text((1, r * cw + 2), f"{c:03x}", fill=0)
        g = glyph(exe, c)
        for y in range(CELL):
            for x in range(CELL):
                if g[y][x]:
                    dr.rectangle([lab + k * cw + x * zoom, r * cw + y * zoom,
                                  lab + k * cw + x * zoom + zoom - 1, r * cw + y * zoom + zoom - 1], fill=0)
    im.save(out)


if __name__ == "__main__":
    if sys.argv[1] == "sheet":
        exe = open(sys.argv[2], "rb").read()
        sheet(exe, sys.argv[3], int(sys.argv[4], 0) if len(sys.argv) > 4 else 0x5E0)
