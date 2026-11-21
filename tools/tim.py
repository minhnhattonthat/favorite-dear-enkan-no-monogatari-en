"""tim.py: decode PS1 TIM images (4/8/16 bpp, with or without CLUT) to PNG, and dump every image in GDATA.BIN.

    python -X utf8 tools/tim.py png FILE.TIM OUT.png [--clut N]
    python -X utf8 tools/tim.py dump OUTDIR [--disc work/disc/tree] [--only 8,9,143]
                                     every GDATA directory entry that is a TIM (raw or LZSS) -> OUTDIR/eNNN.png + index.tsv

TIM: u32 0x10, u32 flags (bits 0-1 pmode 0=4bpp 1=8bpp 2=16bpp, bit 3 = has CLUT), [CLUT block], image block;
block = u32 length, u16 x, u16 y, u16 w (halfwords), u16 h, data. 16-bit colour: bit 15 STP, 5:5:5 BGR.
Colour 0x0000 is transparent on PS1 and drawn as magenta here so text on it stays readable.
"""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
ROOT = Path(__file__).resolve().parents[1]


def rgb(c):
    if c == 0:
        return (255, 0, 255)
    return ((c & 31) << 3, (c >> 5 & 31) << 3, (c >> 10 & 31) << 3)


def parse(data, off=0):
    """-> dict(bpp, w, h, pix (list of ints), cluts (list of lists)) or None if not a TIM."""
    if len(data) < off + 20:
        return None
    magic, flags = struct.unpack_from("<II", data, off)
    if magic != 0x10 or flags & ~0xF or (flags & 3) == 3:
        return None
    p = off + 8
    cluts = []
    if flags & 8:
        ln, x, y, w, h = struct.unpack_from("<IHHHH", data, p)
        if ln != 12 + w * h * 2 or not w or not h:
            return None
        cl = struct.unpack_from("<%dH" % (w * h), data, p + 12)
        cluts = [list(cl[i:i + w]) for i in range(0, w * h, w)]
        p += ln
    ln, x, y, w, h = struct.unpack_from("<IHHHH", data, p)
    if ln != 12 + w * h * 2 or not w or not h or p + ln > len(data):
        return None
    raw = data[p + 12:p + ln]
    mode = flags & 3
    if mode == 0:
        pix = [b >> s & 15 for b in raw for s in (0, 4)]
        width = w * 4
    elif mode == 1:
        pix = list(raw)
        width = w * 2
    else:
        pix = list(struct.unpack_from("<%dH" % (w * h), raw))
        width = w
    return {"bpp": (4, 8, 16)[mode], "w": width, "h": h, "pix": pix, "cluts": cluts, "end": p + ln, "vram": (x, y)}


def to_image(t, clut=0):
    from PIL import Image
    im = Image.new("RGB", (t["w"], t["h"]))
    if t["bpp"] == 16:
        im.putdata([rgb(c) for c in t["pix"]])
    else:
        pal = t["cluts"][clut % len(t["cluts"])] if t["cluts"] else [i * 0x421 for i in range(256)]
        im.putdata([rgb(pal[i] if i < len(pal) else 0) for i in t["pix"]])
    return im


def dump(outdir, disc, only=None):
    """every GDATA directory entry (tools/gdata.py: u16 sector, u16 count) that is a raw or LZSS TIM"""
    from lzss import decompress
    import gdata
    exe = (Path(disc) / "PSX.EXE").read_bytes()
    g = (Path(disc) / "GDATA.BIN").read_bytes()
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for i, (sec, cnt) in enumerate(gdata.directory(exe)):
        if only is not None and i not in only:
            continue
        size = cnt * 2048
        blob = g[sec * 2048:sec * 2048 + size]
        kind, t = "raw", parse(blob)
        if t is None:
            try:
                raw, _ = decompress(g[:sec * 2048 + size + 16], sec * 2048)
                kind, t = "lzss", parse(raw)
            except Exception:
                t = None
        if t is None:
            continue
        to_image(t).save(out / f"e{i:03d}.png")
        rows.append(f"{i}\t{sec:#x}\t{kind}\t{t['bpp']}\t{t['w']}x{t['h']}\t{len(t['cluts'])}")
    (out / "index.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(len(rows), "images")


if __name__ == "__main__":
    if sys.argv[1] == "png":
        d = Path(sys.argv[2]).read_bytes()
        c = int(sys.argv[sys.argv.index("--clut") + 1]) if "--clut" in sys.argv else 0
        to_image(parse(d), c).save(sys.argv[3])
    elif sys.argv[1] == "dump":
        only = ({int(x) for x in sys.argv[sys.argv.index("--only") + 1].split(",")} if "--only" in sys.argv else None)
        dump(sys.argv[2], sys.argv[sys.argv.index("--disc") + 1] if "--disc" in sys.argv else ROOT / "work/disc/tree",
             only)
