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
import btname  # noqa: E402
import en  # noqa: E402
import evscript  # noqa: E402
import extract  # noqa: E402
import font_en  # noqa: E402
import gdata  # noqa: E402
import gfx  # noqa: E402
from tbl import TOKEN  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TREE = ROOT / "work" / "disc" / "tree"
ARMIPS = ROOT / "tools" / "armips" / "armips.exe"
FILLER = "The quick brown fox jumps over the lazy dog. "
SECTOR = 2048


class FitError(ValueError):
    pass


def put(buf, off, data, log=None, writer=""):
    """buf[off:off+len(data)] = data (extending buf with zeros if needed); with a `log` list, first record
    (off, the bytes there before (0xFF past the end), data, writer): romdiff.check's write-log entries"""
    end = off + len(data)
    if log is not None:
        old = bytes(buf[off:end])
        log.append((off, old + b"\xff" * (len(data) - len(old)), bytes(data), writer))
    if end > len(buf):
        buf.extend(bytes(end - len(buf)))
    buf[off:end] = data


def log_diff(log, before, after, writer):
    """log every run of bytes where `after` differs from `before` (a tool's output, e.g. armips) as one write"""
    if log is None:
        return
    i, n = 0, len(after)
    while i < n:
        if i < len(before) and before[i] == after[i]:
            i += 1
            continue
        j = i
        while j < n and not (j < len(before) and before[j] == after[j]):
            j += 1
        old = before[i:j]
        log.append((i, old + b"\xff" * (j - i - len(old)), after[i:j], writer))
        i = j


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
# rows the warps show first: ev_kaiwa1's dialogue box, battle_t0101's top box
TORTURE_ROWS = {"e835.1F2A", "e727.13B8"}


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


def event_edits(gd, exe, mode, table, report=None, relocs=None, log=None):
    """GDATA with the new scripts. A script that outgrows its sectors (en/marker) is moved to the end of GDATA.BIN
    when `relocs` is a list: each move is appended as (old sector, old count, new sector, new count) for repoint().
    `log` gets the writes (put)."""
    rows_by_ent = {}
    for path in sorted((extract.SCRIPT / "events").glob("e*.tsv")):
        rows_by_ent[int(path.stem[1:])] = extract.read_tsv(path)
    out = bytearray(gd)
    pad = bytes(-len(out) % SECTOR)
    out += pad
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
            for i, row in enumerate(rows_by_ent.get(ent, [])):
                # torture: the file's first row and TORTURE_ROWS only (on every row the file outgrows its sectors)
                torture = m == "torture" and (i == 0 or row["id"] in TORTURE_ROWS)
                text = row_text(row, "ruler" if m == "torture" and not torture else m)
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
                put(out, len(out), body + bytes(ncnt * SECTOR - len(body)), log, f"insert:e{ent} moved")
                relocs.append((sec, cnt, nsec, ncnt))
                if report is not None:
                    report.append((ent, ncnt * SECTOR, sc.code_off + 2 * sc.n, len(body)))
                continue
            else:
                raise FitError(f"e{ent}: {e}") from None
        if report is not None:
            report.append((ent, size, sc.code_off + 2 * sc.n, len(new.rstrip(b"\0"))))
        put(out, sec * SECTOR, new, log, f"insert:e{ent}")
        hi = max(hi, sec * SECTOR + size)
    if not relocs:
        out = out[:max(len(gd), hi)]  # nothing moved: no sector padding
    elif log is not None and pad:
        log.append((len(gd), b"\xff" * len(pad), pad, "insert:GDATA sector padding"))
    return bytes(out)


def repoint(exe, relocs, name, log=None):
    """`exe` with every directory entry of each moved script rewritten (aliases share a sector: all of them move)"""
    out = bytearray(exe)
    base = EXE_DIRS[name]
    for sec, cnt, nsec, ncnt in relocs:
        if nsec > 0xFFFF:
            raise FitError("GDATA.BIN past the u16 sector range")
        hits = 0
        for i in range(gdata.GCOUNT):
            if struct.unpack_from("<HH", out, base + 4 * i) == (sec, cnt):
                put(out, base + 4 * i, struct.pack("<HH", nsec, ncnt), log, f"repoint:{name} entry {i}")
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


# Grown EXE strings move here (PSX.EXE RAM; OMK.EXE at OMK_SHIFT): the part of the font hook's zero run between the
# hook's scratch (ends 0x8019315C) and QA_AREA. freewatch and the post-load RAM dumps saw no game write to it
# (docs/re/space.md); HOOKS' FREE_END stops the hook at REPOINT[0].
REPOINT = (0x80193200, 0x80193600)
# English name-entry code and buffers (asm/name.inc, PSX.EXE only), the rest of that run up to QA_AREA
NAME_SPACE = (REPOINT[1], 0x80193800)  # 0x80193800 = QA_AREA[0]


def exe_text(exe, omk, mode, table, report=None, logs=(None, None)):
    """(PSX.EXE, OMK.EXE) with the strings in place. In `en` mode a string longer than its slot moves to REPOINT
    and every aligned u32 pointing at it (table entries; the same count in both EXEs) is rewritten; its old slot
    keeps a cut copy. A grown string with no u32 pointer is refused (code-addressed: fit it to its slot). Marker
    modes cut to the slot. `report` gets one line per move."""
    out, out_omk = bytearray(exe), bytearray(omk)
    mode = "marker" if mode == "torture" else mode  # torture: event dialogue only
    cursor = REPOINT[0]
    for row in extract.read_tsv(extract.SCRIPT / "exe.tsv"):
        if "name-entry grid" in row["notes"]:
            continue  # fixed cells, not a string (phase 8: Latin grid)
        text = row_text(row, mode)
        if text is None:
            continue
        off = int(row["id"].split(".")[1], 16)
        old = table.encode(row["jp"])
        new = en.encode(text, table)
        o2 = off + extract.omk_delta(off)
        if exe[off:off + len(old)] != old or omk[o2:o2 + len(old)] != old:
            raise FitError(f"{row['id']}: the EXE bytes don't match the row's jp")
        if len(new) > len(old):
            if mode == "en":
                ptrs = u32_refs(exe, off + extract.EXE_VA)
                ptrs_omk = u32_refs(omk, o2 + extract.EXE_VA)
                if not ptrs or len(ptrs) != len(ptrs_omk):
                    raise FitError(f"{row['id']}: {len(new)} bytes > its {len(old)}-byte slot and no u32 pointer "
                                   f"to move it ({len(ptrs)} in PSX.EXE, {len(ptrs_omk)} in OMK.EXE)")
                moved = new + bytes(-len(new) % 4)
                if cursor + len(moved) > REPOINT[1]:
                    raise FitError(f"{row['id']}: repoint space 0x{REPOINT[0]:08X}-0x{REPOINT[1]:08X} is full")
                for buf, refs, shift, log in ((out, ptrs, 0, logs[0]), (out_omk, ptrs_omk, OMK_SHIFT, logs[1])):
                    at = cursor + shift - extract.EXE_VA
                    put(buf, at, moved, log, f"exe_text:{row['id']} moved")
                    for p in refs:
                        put(buf, p, struct.pack("<I", cursor + shift), log, f"exe_text:{row['id']} pointer")
                if report is not None:
                    report.append(f"{row['id']} -> 0x{cursor:08X} ({len(new)} bytes, {len(ptrs)} pointer(s))")
                cursor += len(moved)
            new = fit_slot(row, mode, len(old), table)
        new += bytes(len(old) - len(new))
        put(out, off, new, logs[0], f"exe_text:{row['id']}")
        put(out_omk, o2, new, logs[1], f"exe_text:{row['id']}")
    return bytes(out), bytes(out_omk)


# QA overrides go to the tail of the font hook's free run, past the hook, its font and its 288-byte scratch (which end
# near 0x80193160); OMK.EXE -0x1840. Not 0x801956D0: a memory-card load overwrites that (docs/re/space.md).
QA_AREA = (0x80193800, 0x80193D2C)
OMK_SHIFT = -0x1840


def u32_refs(exe, target):
    """file offsets of every aligned u32 equal to `target`"""
    return [i for i in range(0, len(exe) - 3, 4) if struct.unpack_from("<I", exe, i)[0] == target]


def qa_override(psx, omk, qa, table):
    """(PSX.EXE, OMK.EXE) with each {row id: text} string written to QA_AREA and every u32 pointer to the original
    repointed there (the width gate's single-string test: the ruler build cuts EXE strings to their slot)"""
    out, out_omk = bytearray(psx), bytearray(omk)
    rows = {r["id"]: r for r in extract.read_tsv(extract.SCRIPT / "exe.tsv")}
    at = QA_AREA[0]
    for rid, text in qa.items():
        if rid not in rows:
            raise FitError(f"--qa {rid}: no such row in script/exe.tsv")
        off = int(rid.split(".")[1], 16)
        new = en.encode(text, table)
        new += bytes(-len(new) % 4)
        if at + len(new) > QA_AREA[1]:
            raise FitError("--qa: overrides past the spare area")
        for buf, shift in ((out, 0), (out_omk, extract.omk_delta(off))):
            refs = u32_refs(buf, off + shift + extract.EXE_VA)
            if not refs:
                raise FitError(f"--qa {rid}: no u32 pointer to it (lui/addiu or record-addressed)")
            dest = at + (0 if buf is out else OMK_SHIFT)
            for r in refs:
                struct.pack_into("<I", buf, r, dest)
            fo = dest - extract.EXE_VA
            if any(buf[fo:fo + len(new)]):
                raise FitError("--qa: the spare area is not zero")
            buf[fo:fo + len(new)] = new
        at += len(new)
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


STAFF_CODES = "#%\\&"  # leading single-byte line codes FIN.EXE reads (docs/re/text.md §Credits): kept as they are


def staff_en(row):
    """an English credits row -> FIN.EXE line bytes: the jp line's leading single-byte codes, then the `en` cell as
    FIN pair codes (asm/fin.asm; leading spaces pair up into 12-px cells like the full-width indent); '|' splits
    the row into several lines"""
    jp = row["jp"]
    code = jp[:len(jp) - len(jp.lstrip(STAFF_CODES))]
    body = row["en"][len(code):] if row["en"].startswith(code) else row["en"]
    lines = [font_en.fin_pairs(part) for part in body.split("|")]
    return code.encode("ascii") + extract.FIN_NL.join(lines)


def staff_edit(fin, mode, log=None):
    """FIN.EXE with the staff-roll lines replaced: marker modes in place (same byte length); en = staff_en lines,
    the block rewritten up to the original 0xFF (a table follows it: the block may shrink, never grow), the bytes
    after the new 0xFF zeroed. The pair hook itself is asm/fin.asm (edits)."""
    block = extract.fin_block(fin)
    lines = extract.staff_lines(block)
    for row in extract.read_tsv(extract.SCRIPT / "staff.tsv"):
        n = int(row["id"].split(".")[1])
        if mode == "en":
            if row["en"]:
                lines[n] = staff_en(row)
            continue
        new = staff_marker(row)
        if len(new) != len(lines[n]):
            raise FitError(f"{row['id']}: marker is {len(new)} bytes, line is {len(lines[n])}")
        lines[n] = new
    new_block = extract.FIN_NL.join(lines) + b"\xff"
    if len(new_block) > len(block) + 1:
        raise FitError(f"FIN.EXE staff roll: {len(new_block)} bytes > the original {len(block) + 1}")
    new_block += bytes(len(block) + 1 - len(new_block))
    out = bytearray(fin)
    put(out, extract.FIN_TEXT, new_block, log, "staff_edit")
    return bytes(out)


# --- assembly -------------------------------------------------------------------------------------------------------


def assemble(exe, asm, defs=()):
    """EXE bytes with asm/<asm> applied; `defs` = extra (name, value) -equ pairs"""
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        (d / "in.exe").write_bytes(exe)
        (d / "font.bin").write_bytes(font_en.fin_binary() if asm == "fin.asm" else font_en.binary())
        cmd = [str(ARMIPS), str(ROOT / "asm" / asm), "-strequ", "EXE_IN", str(d / "in.exe"),
               "-strequ", "EXE_OUT", str(d / "out.exe"), "-strequ", "FONT_BIN", str(d / "font.bin")]
        if asm == "btname.asm":  # battle name plates: data from trans/btname.tsv (tools/btname.py)
            bt = btname.read_rows()
            for name, data in (("BTFONT_BIN", btname.font_bin()), ("BTHERO_BIN", btname.hero_bin(bt)),
                               ("BTENEMY_BIN", btname.enemy_bin(bt))):
                (d / f"{name}.bin").write_bytes(data)
                cmd += ["-strequ", name, str(d / f"{name}.bin")]
        for k, v in defs:
            cmd += ["-equ", k, str(v)]
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT / "asm")  # .include resolves from the cwd
        if r.returncode != 0:
            raise RuntimeError(f"armips failed:\n{r.stdout}\n{r.stderr}")
        return (d / "out.exe").read_bytes()


# PSX.EXE / OMK.EXE: the glyph fetch (docs/re/text.md §Font) and the free run the hook lives in (docs/re/space.md)
HOOKS = {"PSX.EXE": dict(GLYPH=0x800D6BB4, FREE=0x80192A6C, FREE_END=REPOINT[0]),
         "OMK.EXE": dict(GLYPH=0x800D976C, FREE=0x8019122C, FREE_END=REPOINT[0] + OMK_SHIFT)}


def hooked(name, exe):
    return assemble(exe, "font.asm", HOOKS[name].items())


def name_entry(exe):
    """PSX.EXE with asm/name.asm applied (code and buffers in NAME_SPACE)"""
    return assemble(exe, "name.asm", (("NAME_FREE", NAME_SPACE[0]), ("NAME_FREE_END", NAME_SPACE[1])))


def edits(mode="en", report=None, qa=None, moves=None, writes=None):
    """{disc path: new bytes}; `qa` = {EXE row id: text} single-string overrides (qa_override); `moves` gets one
    line per repointed EXE string; `writes` (a dict) gets {disc path: [romdiff write-log entries]} for every write
    insert makes, armips' changes logged as diffs (tests/test_enbuild.py checks them with romdiff.check)"""
    lg = (lambda name: writes.setdefault(name, [])) if writes is not None else (lambda name: None)
    exe = (TREE / "PSX.EXE").read_bytes()
    omk = (TREE / "OMK.EXE").read_bytes()
    gd = (TREE / "GDATA.BIN").read_bytes()
    relocs = []
    new_gd = event_edits(gd, exe, mode, extract.event_table(), report, relocs, lg("GDATA.BIN"))
    if mode == "en":  # graphics text, gfx/*.tsv (each image in its own slot; tools/gfx.py)
        before = new_gd
        new_gd = gfx.gdata_edit(new_gd, exe)
        log_diff(lg("GDATA.BIN"), before, new_gd, "gfx")
    psx, omk2 = exe_text(exe, omk, mode, extract.exe_table(), moves, (lg("PSX.EXE"), lg("OMK.EXE")))
    for name in ("PSX.EXE", "OMK.EXE"):
        before = psx if name == "PSX.EXE" else omk2
        after = hooked(name, before)
        log_diff(lg(name), before, after, "armips:font.asm")
        psx, omk2 = (after, omk2) if name == "PSX.EXE" else (psx, after)
    if mode == "en":  # battle name plates (asm/btname.inc; PSX.EXE only: OMK.EXE has no battle code)
        after = assemble(psx, "btname.asm")
        log_diff(lg("PSX.EXE"), psx, after, "armips:btname.asm")
        psx = after
        # hero status skill names in the main font (asm/skill.inc; PSX.EXE only: the Omake menu has no status screen)
        after = assemble(psx, "skill.asm")
        log_diff(lg("PSX.EXE"), psx, after, "armips:skill.asm")
        psx = after
        after = name_entry(psx)  # English name entry (asm/name.inc; the new-game name entry runs only in PSX.EXE)
        log_diff(lg("PSX.EXE"), psx, after, "armips:name.asm")
        psx = after
    if qa:  # after the hook: qa_override refuses to write over non-zero bytes
        psx, omk2 = qa_override(psx, omk2, qa, extract.exe_table())
    epi = (TREE / "TITLE" / "EPILOG.EXE").read_bytes()
    out = {"PSX.EXE": psx, "OMK.EXE": omk2, "TITLE/EPILOG.EXE": assemble(epi, "epilog.asm")}
    log_diff(lg("TITLE/EPILOG.EXE"), epi, out["TITLE/EPILOG.EXE"], "armips:epilog.asm")
    if relocs:
        for name in EXE_DIRS:
            out[name] = repoint(out[name] if name in out else (TREE / name).read_bytes(), relocs, name, lg(name))
    if new_gd != gd:
        out["GDATA.BIN"] = new_gd
    if mode == "en":  # title-screen PSS text (gfx/TTL_*.tsv), each within its own sectors
        for name, blob in gfx.pss_files(exe, gd).items():
            log_diff(lg(name), (TREE / name).read_bytes(), blob, "gfx")
            out[name] = blob
    fin = (TREE / "DATA" / "FIN.EXE").read_bytes()
    new_fin = staff_edit(fin, mode, lg("DATA/FIN.EXE"))
    if mode == "en":
        hooked_fin = assemble(new_fin, "fin.asm")
        log_diff(lg("DATA/FIN.EXE"), new_fin, hooked_fin, "armips:fin.asm")
        new_fin = hooked_fin
    if new_fin != fin:
        out["DATA/FIN.EXE"] = new_fin
    if writes is not None:
        for name in [n for n in writes if n not in out]:
            del writes[name]
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
