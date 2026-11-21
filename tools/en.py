"""en.py: encode English text for the game's printers (docs/re/text.md §English). Game 1's, unchanged.

English letters go two per halfword: code = first | second << 8, both bytes in the font_en range (0x20-0x84), so
every code is >= 0x2020 and < 0xFF00: above the Japanese font (< 0x6F0) and below the printer codes (0xFFxx). The
glyph hook (asm/font.asm) draws both letters into one 12x12 cell, so the engine's column and line logic is unchanged
and a line holds 2x as many English letters as Japanese ones. An odd letter before a control code or the end gets a
space as its partner (invisible at a line end; mid-line it shows as a half-cell gap).

Markup: control codes as in the extracted TSVs ({n}, {wait}, {spk:XXXX}...), encoded with the printer's table;
`[XX]` escapes are raw bytes (keep them halfword-aligned)."""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import font_en  # noqa: E402
from tbl import TOKEN  # noqa: E402

CHARS = {ch: code for code, ch in font_en.chars().items()}
CODES = {code: ch for ch, code in CHARS.items()}
LO = 0x2020  # smallest pair code


def is_pair(hw):
    return LO <= hw < 0xFF00 and (hw & 0xFF) in CODES and (hw >> 8) in CODES


def pairs(text):
    """halfwords for a plain run of English (no markup)"""
    out = []
    for i in range(0, len(text), 2):
        a, b = text[i], text[i + 1] if i + 1 < len(text) else " "
        for ch in (a, b):
            if ch not in CHARS:
                raise ValueError(f"no English glyph for {ch!r} in {text!r}")
        out.append(CHARS[a] | CHARS[b] << 8)
    return out


def encode(text, table):
    """bytes for `text`; `table` is the tbl.Table whose control codes the target printer uses."""
    out, run, i = bytearray(), [], 0

    def flush():
        for hw in pairs("".join(run)):
            out.extend(struct.pack("<H", hw))
        run.clear()

    while i < len(text):
        m = TOKEN.match(text, i)
        if m:
            flush()
            out.extend(table.encode(m[0]))
            i = m.end()
            continue
        run.append(text[i])
        i += 1
    flush()
    if len(out) % 2:
        raise ValueError(f"odd byte count encoding {text!r}")
    return bytes(out)


def decode_pairs(data):
    """readable form of English halfwords (pairs -> letters, other halfwords -> <XXXX>), for checks and debugging"""
    out = []
    for (hw,) in struct.iter_unpack("<H", data):
        out.append(CODES[hw & 0xFF] + CODES[hw >> 8] if is_pair(hw) else f"<{hw:04X}>")
    return "".join(out)


if __name__ == "__main__":
    from tbl import Table
    t = Table(["F0FF={n}", "FFFF={end}", "F1FF={spk:2}"])
    b = encode("{spk:0100}Hi you!{n}Even{end}", t)
    assert decode_pairs(b) == "<FFF1><0001>Hi you! <FFF0>Even<FFFF>", decode_pairs(b)
    assert all(is_pair(hw) for (hw,) in struct.iter_unpack("<H", encode("…—♥♪é ~", t)))
    print("selftest ok")
