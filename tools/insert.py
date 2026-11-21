"""insert.py: put the English (or marker) text into the EXEs and the GDATA event scripts. build.py calls edits().
Game 1's (../favorite-dear-en/tools/insert.py), adapted: u16 GDATA directories, OMK.EXE as a second EXE text site,
the staff roll inside DATA/FIN.EXE.

    python -X utf8 tools/insert.py stats [--mode en|marker|ruler|torture]   scripts changed and the tightest files

Modes: 'en' writes each row's `en` cell (rows with an empty `en` stay Japanese); 'marker' writes `[id]` + filler
into every row (the phase 5 marker build), keeping each row's control codes and its glyph count x 2 letters, so a
line keeps its width; 'ruler' puts RULER (44 letters) in each row's first line for the width gate (a script it
doesn't fit gets markers); 'torture' puts TORTURE (every glyph, three lines) in each event row the same way.

Event scripts (docs/re/events.md): a row is a text segment; new text may grow or shrink it. The script's code is
rebuilt piece by piece and every reference argument (Script.refs, incl. the pc-0 goto) is remapped to the new pc of
its target. A file that outgrows its sectors moves to the end of GDATA.BIN and its (u16 sector, u16 count) directory
entries are rewritten in every EXE that carries the directory (EXE_DIRS); no file may pass EVENT_BUFFER bytes.
EXE strings are written in place (FFFF-terminated, the rest of the slot zero-filled) in PSX.EXE and, at
extract.omk_delta, in OMK.EXE. The pair-glyph hook is assembled into both by armips (asm/font.asm) and into
TITLE/EPILOG.EXE, the endings, which has its own renderer (asm/epilog.asm)."""
import argparse
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import en  # noqa: E402
import evscript  # noqa: E402
import extract  # noqa: E402
import font_en  # noqa: E402
import gdata  # noqa: E402
from tbl import TOKEN  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TREE = ROOT / "work" / "disc" / "tree"
ARMIPS = ROOT / "tools" / "armips" / "armips.exe"
FILLER = "The quick brown fox jumps over the lazy dog. "
SECTOR = 2048


class FitError(ValueError):
    pass


# --- text -----------------------------------------------------------------------------------------------------------


def runs(jp):
    """split a row's markup into [(is_text, piece)]: text = glyph characters, else one control/escape token"""
    out, i, buf = [], 0, []
    while i < len(jp):
        m = TOKEN.match(jp, i)
        if m:
            if buf:
                out.append((True, "".join(buf)))
                buf = []
            out.append((False, m[0]))
            i = m.end()
        else:
            buf.append(jp[i])
            i += 1
    if buf:
        out.append((True, "".join(buf)))
    return out


def tag(row_id):
    """the marker id: 'e520.01A4' -> [e520.1A4], 'PSX.132398' -> [132398], 'FIN.012' -> [F12]"""
    kind, off = row_id.split(".")
    if kind == "PSX":
        return f"[{off}]"
    if kind == "FIN":
        return f"[F{int(off)}]"
    return f"[{kind}.{int(off, 16):X}]"


def marker(row_id, jp):
    """`[id]` + filler in place of the row's glyphs: each run of k glyphs becomes 2k letters (the same cells), the
    first run at least long enough for the id; control codes stay."""
    t = tag(row_id)
    out, first, k = [], True, 0
    for is_text, piece in runs(jp):
        if not is_text:
            out.append(piece)
            continue
        n = 2 * len(piece)
        if first:
            s = (t + FILLER * 4)[:max(n, len(t))]
            first = False
        else:
            s = (FILLER * 4)[k % len(FILLER):][:n]
            k += n
        out.append(s)
    return "".join(out)


RULER = "1234567890ABCDEFGHIJ1234567890abcdefghij+-*/"  # 44 letters: the last one visible = the line's limit

# every glyph of fonts/en6x12.txt plus double spaces, as three 40-letter dialogue lines (the glyph torture line)
TORTURE = ("{n}".join([" !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFG",
                       "HIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmno",
                       "pqrstuvwxyz{|}~…—♥♪é  A  B   C  Ww Mm"]))


def ruler(row_id, jp, first=RULER):
    """the width gate: the row's first text run becomes RULER (one full line), the rest as in marker()"""
    out, done = [], False
    for is_text, piece in runs(marker(row_id, jp)):
        if is_text and not done:
            piece, done = first, True
        out.append(piece)
    return "".join(out)


def row_text(row, mode):
    if mode == "marker":
        return marker(row["id"], row["jp"])
    if mode == "ruler":
        return ruler(row["id"], row["jp"])
    if mode == "torture":
        return ruler(row["id"], row["jp"], TORTURE)
    return row["en"] or None


# --- event scripts --------------------------------------------------------------------------------------------------


def rebuild(sc, repl):
    """new code halfwords for Script `sc` with segments replaced: repl = {segment start pc: new bytes}."""
    return rebuild_map(sc, repl)[0]


def rebuild_map(sc, repl):
    """(new code halfwords, newpos) where newpos(old pc) is that pc's index in the new code."""
    code, n = sc.code, sc.n
    seg_end = dict(sc.segments)
    pieces, pc, new = [], 0, []  # (old start, old end, new start, replaced)
    for s in sorted(repl):
        e = seg_end[s]
        if s > pc:
            pieces.append((pc, s, len(new), False))
            new.extend(code[pc:s])
        data = repl[s]
        pieces.append((s, e, len(new), True))
        new.extend(struct.unpack("<%dH" % (len(data) // 2), data))
        pc = e
    if pc < n:
        pieces.append((pc, n, len(new), False))
        new.extend(code[pc:n])

    def newpos(t):
        for a, b, ns, replaced in pieces:
            if a <= t < b:
                if replaced and t != a:
                    raise FitError(f"reference to pc {t:#x} inside a replaced segment {a:#x}-{b:#x}")
                return ns + (t - a)
        raise FitError(f"reference to pc {t:#x} outside the code")

    for op, i, t in sc.refs:
        new[newpos(op) + 1 + i] = 0x8000 | newpos(t)
    if len(new) > 0x7FFF:
        raise FitError("code past the 15-bit reference range")
    return new, newpos


def script_bytes(sc, size, repl):
    new = rebuild(sc, repl)
    out = sc.data[:sc.code_off] + struct.pack("<%dH" % len(new), *new)
    if len(out) > size:
        raise FitError(f"{len(out):#x} bytes > its {size:#x}-byte slot")
    return out + bytes(size - len(out))


# The loader (0x800A13DC) reads a script into the buffer at 0x80148CBC, which runs to the end of the zero run at
# 0x8014FCBC (docs/re/space.md): 0x7000 bytes, the same cap as game 1 (whose loader capped at 0x3800 halfwords).
EVENT_BUFFER = 0x7000
# Every EXE that carries the GDATA directory (u16 sector, u16 count) x gdata.GCOUNT (found by byte match).
EXE_DIRS = {"PSX.EXE": 0x170244, "OMK.EXE": 0x16EA04, "GOVER.EXE": 0x69230, "FD_BALL.EXE": 0x65C4C,
            "PS_MOV.EXE": 0xE598C, "TITLE/EPILOG.EXE": 0x80944}


def event_edits(gd, exe, mode, table, report=None, relocs=None):
    """GDATA with the new scripts. A script that outgrows its sectors (en/marker) is moved to the end of GDATA.BIN
    when `relocs` is a list: each move is appended as (old sector, old count, new sector, new count) for repoint()."""
    rows_by_ent = {}
    for path in sorted((extract.SCRIPT / "events").glob("e*.tsv")):
        rows_by_ent[int(path.stem[1:])] = extract.read_tsv(path)
    out = bytearray(gd)
    out += bytes(-len(out) % SECTOR)
    hi = 0
    seen = set()
    for ent, sec, cnt, kd, data in gdata.entries(TREE):
        if kd != "script" or sec in seen:
            continue
        seen.add(sec)
        size = cnt * SECTOR
        sc = evscript.Script(data)

        def replacements(m):
            repl = {}
            for row in rows_by_ent.get(ent, []):
                text = row_text(row, m)
                if text is not None:
                    repl[(int(row["id"].split(".")[1], 16) - sc.code_off) // 2] = en.encode(text, table)
            return repl

        repl = replacements(mode)
        if not repl:
            continue
        try:
            try:
                new = script_bytes(sc, size, repl)
            except FitError:
                if mode not in ("ruler", "torture"):
                    raise
                repl = replacements("marker")  # ruler doesn't fit: this file gets markers
                new = script_bytes(sc, size, repl)
        except FitError as e:
            if relocs is not None and "slot" in str(e):
                body = script_bytes(sc, EVENT_BUFFER, repl).rstrip(b"\0")
                ncnt = -(-len(body) // SECTOR)
                nsec = len(out) // SECTOR
                out += body + bytes(ncnt * SECTOR - len(body))
                relocs.append((sec, cnt, nsec, ncnt))
                if report is not None:
                    report.append((ent, ncnt * SECTOR, sc.code_off + 2 * sc.n, len(body)))
                continue
            else:
                raise FitError(f"e{ent}: {e}") from None
        if report is not None:
            report.append((ent, size, sc.code_off + 2 * sc.n, len(new.rstrip(b"\0"))))
        out[sec * SECTOR:sec * SECTOR + size] = new
        hi = max(hi, sec * SECTOR + size)
    if not relocs:
        out = out[:max(len(gd), hi)]  # nothing moved: no sector padding
    return bytes(out)


def repoint(exe, relocs, name):
    """`exe` with every directory entry of each moved script rewritten (aliases share a sector: all of them move)"""
    out = bytearray(exe)
    base = EXE_DIRS[name]
    for sec, cnt, nsec, ncnt in relocs:
        if nsec > 0xFFFF:
            raise FitError("GDATA.BIN past the u16 sector range")
        hits = 0
        for i in range(gdata.GCOUNT):
            if struct.unpack_from("<HH", out, base + 4 * i) == (sec, cnt):
                struct.pack_into("<HH", out, base + 4 * i, nsec, ncnt)
                hits += 1
        if not hits:
            raise FitError(f"{name}: no directory entry for sector {sec:#x}")
    return bytes(out)


# --- EXE strings (PSX.EXE and OMK.EXE) ------------------------------------------------------------------------------


def fit_slot(row, mode, size, table):
    """marker/ruler text for an in-place EXE slot of `size` bytes: shorten the first text run two letters at a
    time; every control code and its arguments stay (a byte cut once dropped the {wait}{end} and hung game 1's
    opening)"""
    pieces = runs(row_text(row, mode))
    first = next(i for i, (is_text, _) in enumerate(pieces) if is_text)
    while True:
        new = en.encode("".join(p for _, p in pieces), table)
        if len(new) <= size or not pieces[first][1]:
            break
        pieces[first] = (True, pieces[first][1][:-2])
    if len(new) > size:
        raise FitError(f"{row['id']}: control codes alone need {len(new)} bytes > {size}")
    return new


def exe_text(exe, omk, mode, table):
    """(PSX.EXE, OMK.EXE) with the strings in place; a string longer than its slot is cut (marker modes) or refused
    (en: repointing comes in phase 7)."""
    out, out_omk = bytearray(exe), bytearray(omk)
    mode = "marker" if mode == "torture" else mode  # torture: event dialogue only
    for row in extract.read_tsv(extract.SCRIPT / "exe.tsv"):
        if "name-entry grid" in row["notes"]:
            continue  # fixed cells, not a string (phase 8: Latin grid)
        text = row_text(row, mode)
        if text is None:
            continue
        off = int(row["id"].split(".")[1], 16)
        old = table.encode(row["jp"])
        new = en.encode(text, table)
        if len(new) > len(old):
            if mode == "en":
                raise FitError(f"{row['id']}: {len(new)} bytes > its {len(old)}-byte slot (no repointing yet)")
            new = fit_slot(row, mode, len(old), table)
        new += bytes(len(old) - len(new))
        o2 = off + extract.omk_delta(off)
        if exe[off:off + len(old)] != old or omk[o2:o2 + len(old)] != old:
            raise FitError(f"{row['id']}: the EXE bytes don't match the row's jp")
        out[off:off + len(old)] = new
        out_omk[o2:o2 + len(old)] = new
    return bytes(out), bytes(out_omk)


# --- DATA/FIN.EXE staff roll ----------------------------------------------------------------------------------------


def fullwidth(s):
    """ASCII -> Shift-JIS full-width forms"""
    return "".join(chr(ord(c) + 0xFEE0) if "!" <= c <= "~" else "　" if c == " " else c for c in s)


def staff_marker(row):
    """the row's line with its leading full-width indent kept and the rest replaced by a full-width [Fn] + filler,
    padded to the original byte length (the roll is written in place)"""
    jp = row["jp"]
    body = jp.lstrip("　 #%\\&")
    indent = jp[:len(jp) - len(body)]
    raw = jp.encode("cp932")
    room = (len(raw) - len(indent.encode("cp932"))) // 2
    text = (indent + fullwidth((tag(row["id"]) + FILLER * 2)[:room])).encode("cp932")
    return text + b" " * (len(raw) - len(text))


def staff_edit(fin, mode):
    """FIN.EXE with the staff-roll lines replaced (marker modes only until the credits are engineered)"""
    if mode == "en":
        return fin
    block = extract.fin_block(fin)
    lines = extract.staff_lines(block)
    for row in extract.read_tsv(extract.SCRIPT / "staff.tsv"):
        n = int(row["id"].split(".")[1])
        new = staff_marker(row)
        if len(new) != len(lines[n]):
            raise FitError(f"{row['id']}: marker is {len(new)} bytes, line is {len(lines[n])}")
        lines[n] = new
    new_block = extract.FIN_NL.join(lines)
    out = bytearray(fin)
    out[extract.FIN_TEXT:extract.FIN_TEXT + len(new_block)] = new_block
    return bytes(out)


# --- assembly -------------------------------------------------------------------------------------------------------


def assemble(exe, asm, defs=()):
    """EXE bytes with asm/<asm> applied; `defs` = extra (name, value) -equ pairs"""
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "in.exe").write_bytes(exe)
        (d / "font.bin").write_bytes(font_en.binary())
        cmd = [str(ARMIPS), str(ROOT / "asm" / asm), "-strequ", "EXE_IN", str(d / "in.exe"),
               "-strequ", "EXE_OUT", str(d / "out.exe"), "-strequ", "FONT_BIN", str(d / "font.bin")]
        for k, v in defs:
            cmd += ["-equ", k, str(v)]
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT / "asm")  # .include resolves from the cwd
        if r.returncode != 0:
            raise RuntimeError(f"armips failed:\n{r.stdout}\n{r.stderr}")
        return (d / "out.exe").read_bytes()


# PSX.EXE / OMK.EXE: the glyph fetch (docs/re/text.md §Font) and the free run the hook lives in (docs/re/space.md)
HOOKS = {"PSX.EXE": dict(GLYPH=0x800D6BB4, FREE=0x80192A6C, FREE_END=0x80193D2C),
         "OMK.EXE": dict(GLYPH=0x800D976C, FREE=0x8019122C, FREE_END=0x801924EC)}


def hooked(name, exe):
    return assemble(exe, "font.asm", HOOKS[name].items())


def edits(mode="en", report=None):
    exe = (TREE / "PSX.EXE").read_bytes()
    omk = (TREE / "OMK.EXE").read_bytes()
    gd = (TREE / "GDATA.BIN").read_bytes()
    relocs = []
    new_gd = event_edits(gd, exe, mode, extract.event_table(), report, relocs)
    psx, omk2 = exe_text(exe, omk, mode, extract.exe_table())
    out = {"PSX.EXE": hooked("PSX.EXE", psx), "OMK.EXE": hooked("OMK.EXE", omk2),
           "TITLE/EPILOG.EXE": assemble((TREE / "TITLE" / "EPILOG.EXE").read_bytes(), "epilog.asm")}
    if relocs:
        for name in EXE_DIRS:
            out[name] = repoint(out[name] if name in out else (TREE / name).read_bytes(), relocs, name)
    if new_gd != gd:
        out["GDATA.BIN"] = new_gd
    fin = (TREE / "DATA" / "FIN.EXE").read_bytes()
    new_fin = staff_edit(fin, mode)
    if new_fin != fin:
        out["DATA/FIN.EXE"] = new_fin
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["stats"])
    ap.add_argument("--mode", choices=["en", "marker", "ruler", "torture"], default="en")
    a = ap.parse_args()
    rep = []
    edits(a.mode, rep)
    rep.sort(key=lambda r: r[3] - r[1], reverse=True)
    print(f"{len(rep)} scripts changed")
    for ent, size, old, used in rep[:10]:
        print(f"  e{ent}: slot {size:#06x}, was {old:#06x}, now {used:#06x} ({size - used:+#x} left)")
