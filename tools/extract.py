"""extract.py: dump every Japanese string on the disc to script/*.tsv (columns: id, jp, en, notes).

    python -X utf8 tools/extract.py [--disc work/disc/tree] [--force] [--no-seed]

Sources (docs/re/text.md):
    script/events/eNNN.tsv  event-script text, one file per GDATA script entry NNN (decimal, as `warp.py --event eNNN`),
                            id eNNN.<file byte offset>. Entries 902 and 932 share entry 520's and 739's sectors
                            (EVENT_ALIASES): their text is the same rows.
    script/exe.tsv          PSX.EXE strings (two text regions, a few code-addressed strings, the name-entry grids),
                            id PSX.<offset>. OMK.EXE holds the same bytes at PSX offset + omk_delta(offset): one row
                            covers both sites.
    script/staff.tsv        staff roll in DATA/FIN.EXE (plain Shift-JIS lines, CRLF), id FIN.<line>
    script/sjis.tsv         Shift-JIS memory-card titles in the EXEs, id <EXE>.<offset>
    script/omk.tsv          OMK.EXE's Omake "Mini Event" script (event grammar, run in place), id omk.<file offset>
Ids are original addresses and never change. Re-running keeps `en` and `notes` of existing rows; it refuses to drop a
row that has an `en` unless --force. The `jp` column round-trips byte-exact through the codecs here, which
tests/test_extract.py checks for every row, along with coverage of the text ranges.

Seed: a row whose `jp` is verbatim a game-1 row (`../favorite-dear-en/script`) gets game 1's `en` when its own `en`
is empty, with `g1:<game-1 id>` in notes (docs/decisions.md D9). Seeded rows still need the translation pass to
check them in context.
"""
import argparse
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import evscript  # noqa: E402
import gdata  # noqa: E402
from tbl import Table  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "script"
G1 = ROOT.parent / "favorite-dear-en"
COLS = ["id", "jp", "en", "notes"]

# --- tables ---------------------------------------------------------------------------------------------------------


def _lines(path):
    return Path(path).read_text(encoding="utf-8-sig").splitlines()


def exe_table():
    return Table.load(ROOT / "tbl/jp.tbl")


def event_table():
    """jp.tbl glyphs + tbl/ev.tbl printer codes (the two printers give FFxx different meanings)."""
    glyphs = [ln for ln in _lines(ROOT / "tbl/jp.tbl") if not ln.startswith("#") and "={" not in ln]
    return Table(glyphs + _lines(ROOT / "tbl/ev.tbl"))


def has_text(codes):
    """at least one font code that isn't a blank: rows without any are codes-only and stay out of the TSVs"""
    return any(0 < c < evscript.NCODES and c != 0x5E9 for c in codes)


# --- event scripts --------------------------------------------------------------------------------------------------

EVENT_ALIASES = {902: 520, 932: 739}  # same sector in the directory (verified: gdata.entries)


def script_entries(disc):
    """[(entry, data)] GDATA script entries, one per sector (aliases left out)"""
    out = [(i, data) for i, sec, cnt, kd, data in gdata.entries(disc) if kd == "script"]
    return [(i, d) for i, d in out if i not in EVENT_ALIASES]


def event_rows(disc, table=None):
    """{entry: [row]} with row = dict(id, jp, raw, notes); raw = original bytes. Also returns the parsed scripts."""
    table = table or event_table()
    out, scripts = {}, {}
    for ent, data in script_entries(disc):
        sc = evscript.Script(data)
        scripts[ent] = sc
        msg_starts = {s for kind, s, e in sc.items if kind == "msg"}
        rows = []
        for seg in sc.segments:
            a, b = seg
            if not has_text(sc.code[a:b]):
                continue
            raw = sc.seg_bytes(seg)
            text, used = table.decode(raw, 0, len(raw))
            notes = []
            if a not in msg_starts:
                notes.append("entry point inside the previous row's message")
            alias = [k for k, v in EVENT_ALIASES.items() if v == ent]
            if alias:
                notes.append(f"also GDATA entry {alias[0]} (same sector)")
            rows.append(dict(id=f"e{ent}.{sc.byte(a):04X}", jp=text, raw=raw, notes="; ".join(notes)))
        out[ent] = rows
    return out, scripts


# OMK.EXE's Omake "Mini Event" script (docs/re/text.md §OMK mini events): no GDATA entry. It sits pre-loaded in OMK's
# copy of the script buffer (file 0x13B708 = RAM 0x8014AF08, pc 0 = `0x28` goto) and runs in place (RAM dumps,
# work/qa/p8/omkmini); its argument table is OMK's own at 0x13B4C4 (234 entries; "sample.bmp" follows). The code
# ends at 0x13EB86 and PSX.EXE's post-buffer data follows at 0x13EB8A, so the code has no room to grow.
OMK_MINI_TAB = (0x13B4C4, 234)
OMK_MINI_CODE = (0x13B708, 0x13EB86)


def omk_mini_script(omk):
    """evscript.Script of the mini-event code, with a synthetic header (6, vars, code) over OMK's argument table.
    Script byte offsets b map to OMK.EXE file offsets b - code_off + OMK_MINI_CODE[0]."""
    tab = omk[OMK_MINI_TAB[0]:OMK_MINI_TAB[0] + 2 * OMK_MINI_TAB[1]]
    head = struct.pack("<3H", 6, 6 + len(tab), 6 + len(tab))
    return evscript.Script(head + tab + omk[OMK_MINI_CODE[0]:OMK_MINI_CODE[1]])


def omk_rows(omk, table=None):
    """rows of the mini-event script, id omk.<OMK.EXE file offset>"""
    table = table or event_table()
    sc = omk_mini_script(omk)
    rows = []
    for a, b in sc.segments:
        if not has_text(sc.code[a:b]):
            continue
        raw = sc.seg_bytes((a, b))
        rows.append(dict(id=f"omk.{OMK_MINI_CODE[0] + 2 * a:06X}", jp=table.decode(raw, 0, len(raw))[0], raw=raw,
                         notes="Omake Mini Event (OMK.EXE)"))
    return rows


# --- PSX.EXE --------------------------------------------------------------------------------------------------------

# docs/re/text.md. Game 1's two regions, moved (game 1 0x155F3C -> 0x132398). Before region 2, 0x1409A4-0x141C2C is
# the event-name/code tables that decode as glyph soup (game 1 0x164E7A-0x1660E0; writing there broke game 1).
EXE_REGIONS = [(0x132398, 0x139030), (0x141C2C, 0x142278)]
EXE_GRIDS = [(0x184EA4, 0x184F0A), (0x184F64, 0x18511A)]  # name-entry character grids (fixed layout; game 1 0x17DA4)
# Non-text inside EXE_REGIONS (u32 pointer tables, layout records): the coverage test allows these only.
# Game 1's three tables (0x156818, 0x159F78, 0x15C7D8), found here as the only non-string halfwords in the regions.
EXE_DATA = [(0x132C74, 0x132EF0), (0x1364BC, 0x136DD0), (0x138D50, 0x138EE0)]
# Strings outside the regions that code addresses with lui/addiu (found by sweeping every lui+immediate and u32 pointer
# into the EXE for a valid string start; the rest of the hits are code tables). Address-built: moving one means
# patching the instruction pair, so they stay in place or get repointed in code.
EXE_LOOSE = {
    0x1322B0: "code-addressed (lui/addiu at 0x800DA168, pointer stored to +0x574 of a record; name, see PSX.1322BC)",
    0x1322BC: "code-addressed (addiu at 0x800DA1C4, pointer stored to +0x578 of the same record)",
    0x14F670: "code-addressed (lui/addiu at 0x80099388)",
    0x14F68C: "code-addressed (lui/addiu at 0x800E9F24); with the next row a 2-entry table, 4 bytes per entry",
    0x14F690: "second entry of the table at 0x14F68C (no reference of its own)",
}
EXE_ARGS = {0xFFFE: 0, 0xFFFC: 0, 0xFFFD: 0, 0xFFFB: 0, 0xFF00: 1, 0xFF10: 1, 0xFF20: 1, 0xFF90: 2, 0xFFE0: 2}
EXE_VA = 0x80010000 - 0x800  # vaddr = file offset + EXE_VA
# OMK.EXE copy of each PSX.EXE text range (verified: byte-identical, tests/test_extract.py): (lo, hi, delta)
OMK_DELTAS = [(0x1322B0, 0x139030, 0x224C), (0x141C2C, 0x142278, -0x1934), (0x14F670, 0x14F694, -0x18FC),
              (0x184EA4, 0x18511A, -0x1840), (0x18A93C, 0x18A980, -0x1840)]


def omk_delta(off):
    for lo, hi, d in OMK_DELTAS:
        if lo <= off < hi:
            return d
    raise KeyError(hex(off))


def table_pointers(exe, off):
    """file offsets of the u32 entries in the EXE_DATA pointer tables that point straight at the string at `off`"""
    va = struct.pack("<I", off + EXE_VA)
    return [p for lo, hi in EXE_DATA for p in range(lo, hi, 4) if exe[p:p + 4] == va]


def exe_strings(exe, lo, hi):
    """[(start, end)] FFFF-terminated strings in exe[lo:hi]. A string that ends 2 bytes off a 4-byte boundary is
    followed by one 0x0000 pad (game 1, verified there). Non-string halfwords are skipped."""
    hw = struct.unpack_from("<%dH" % ((hi - lo) // 2), exe, lo)
    out, i, s = [], 0, 0
    while i < len(hw):
        v = hw[i]
        if v == 0xFFFF:
            out.append((lo + 2 * s, lo + 2 * i + 2))
            i += 1
            if (lo + 2 * i) % 4 == 2 and i < len(hw) and hw[i] == 0:
                i += 1
            s = i
        elif v < evscript.NCODES:
            i += 1
        elif v in EXE_ARGS:
            i += 1 + EXE_ARGS[v]
        else:
            i += 1
            s = i
    return out


def exe_pointers(exe):
    """{file offset: [offsets of u32 words pointing at it]} for targets in the text regions"""
    out = {}
    spans = EXE_REGIONS + EXE_GRIDS + [(o, o + 2) for o in EXE_LOOSE]
    for o in range(0x800, len(exe) - 3, 4):
        f = struct.unpack_from("<I", exe, o)[0] - EXE_VA
        if any(lo <= f < hi for lo, hi in spans):
            out.setdefault(f, []).append(o)
    return out


def loose_end(exe, off):
    i = off
    while struct.unpack_from("<H", exe, i)[0] != 0xFFFF:
        i += 2
    return i + 2


def exe_rows(exe, table=None):
    table = table or exe_table()
    ptrs = exe_pointers(exe)
    rows = []
    for lo, hi in EXE_REGIONS:
        for s, e in exe_strings(exe, lo, hi):
            codes = struct.unpack_from("<%dH" % ((e - s) // 2), exe, s)
            if not has_text(codes):
                continue
            raw = exe[s:e]
            text, _ = table.decode(raw, 0, len(raw))
            rows.append(dict(id=f"PSX.{s:06X}", jp=text, raw=raw, notes="" if s in ptrs else "no direct pointer"))
    for s, note in EXE_LOOSE.items():
        raw = exe[s:loose_end(exe, s)]
        text, _ = table.decode(raw, 0, len(raw))
        rows.append(dict(id=f"PSX.{s:06X}", jp=text, raw=raw, notes=note))
    for lo, hi in EXE_GRIDS:  # one row each: {end} here marks an empty cell, not the end of a string
        raw = exe[lo:hi]
        text, _ = table.decode(raw, 0, len(raw))
        rows.append(dict(id=f"PSX.{lo:06X}", jp=text, raw=raw,
                         notes=f"name-entry grid: exactly {len(raw) // 2} cells, {{end}} = empty cell"))
    rows.sort(key=lambda r: int(r["id"][4:], 16))
    return rows


# --- DATA/FIN.EXE staff roll ----------------------------------------------------------------------------------------

FIN_TEXT = 0xF440  # plain Shift-JIS lines, CRLF, ended by `\` CRLF 0xFF (docs/re/text.md)
FIN_NL = b"\r\n"


def fin_block(fin):
    """the staff-roll bytes up to (not including) the 0xFF terminator"""
    return fin[FIN_TEXT:fin.index(b"\xff", FIN_TEXT)]


def staff_lines(block):
    return block.split(FIN_NL)


def staff_rows(fin):
    rows = []
    for n, line in enumerate(staff_lines(fin_block(fin))):
        text = line.decode("cp932")
        if text.strip("　 #%\\"):
            rows.append(dict(id=f"FIN.{n:03d}", jp=text, raw=line, notes=""))
    return rows


# --- Shift-JIS memory-card titles -----------------------------------------------------------------------------------

# PSX.EXE's title also sits in OMK.EXE (omk_delta). The TEST titles are debug leftovers (game 1 had them too).
SJIS = [("PSX.EXE", 0x18A93C), ("TITLE/EPILOG.EXE", 0x46180), ("TITLE/EPILOG.EXE", 0x46968), ("FD_BALL.EXE", 0x40678),
        ("PS_MOV.EXE", 0x3F254), ("TITLE/EPILOG.EXE", 0x11A4), ("FD_BALL.EXE", 0x11A4), ("PS_MOV.EXE", 0x11A4)]


def sjis_rows(tree):
    rows = []
    for name, off in SJIS:
        data = (Path(tree) / name).read_bytes()
        end = data.index(b"\0", off)
        raw = data[off:end]
        note = "memory-card title, Shift-JIS, at most 64 bytes"
        if "ＴＥＳＴ" in raw.decode("cp932"):
            note += "; debug leftover (save title of a test build)"
        if name == "PSX.EXE":
            note += f"; also OMK.EXE 0x{off + omk_delta(off):06X}"
        rows.append(dict(id=f"{Path(name).stem}.{off:06X}", jp=raw.decode("cp932"), raw=raw, notes=note))
    return rows


# --- TSV ------------------------------------------------------------------------------------------------------------


def read_tsv(path):
    """plain tab-separated, no quoting; every row must have len(COLS) fields"""
    lines = Path(path).read_text(encoding="utf-8").split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    head = lines[0].split("\t")
    if head != COLS:
        raise ValueError(f"{path}: header {head} != {COLS}")
    rows = []
    for n, line in enumerate(lines[1:], 2):
        rec = line.rstrip("\r").split("\t")
        if len(rec) != len(COLS):
            raise ValueError(f"{path}:{n}: {len(rec)} columns, want {len(COLS)}")
        rows.append(dict(zip(COLS, rec)))
    return rows


def write_tsv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    out = ["\t".join(COLS)]
    for r in rows:
        rec = [r.get(c, "") for c in COLS]
        if any("\t" in v or "\n" in v or "\r" in v for v in rec):
            raise ValueError(f"{r['id']}: tab or newline in a field")
        out.append("\t".join(rec))
    Path(path).write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")


def g1_memory():
    """{jp: (en, game-1 id)} from game 1's script TSVs (first translated row wins; en "" when no game-1 row with
    that jp has one: game 1's ~1,200 glyph-soup rows, see its glossary "Decisions from earlier batches")"""
    mem = {}
    if not (G1 / "script").is_dir():
        return mem
    for p in sorted((G1 / "script").rglob("*.tsv")):
        for r in read_tsv(p):
            if r["jp"] not in mem or (r["en"] and not mem[r["jp"]][0]):
                mem[r["jp"]] = (r["en"], r["id"])
    return mem


def merge(path, rows, force, mem=None):
    """keep en/notes of existing rows; refuse to lose a translated row unless force; seed empty en from `mem`"""
    old = {r["id"]: r for r in read_tsv(path)} if path.exists() else {}
    new_ids = {r["id"] for r in rows}
    lost = [i for i, r in old.items() if i not in new_ids and r["en"]]
    if lost and not force:
        raise SystemExit(f"{path}: would drop translated rows {lost[:5]}... (use --force)")
    out, seeded = [], 0
    for r in rows:
        o = old.get(r["id"])
        en = o["en"] if o else ""
        notes = o["notes"] if o and o["notes"] else r["notes"]
        if not en and mem and r["jp"] in mem and not o:
            en, gid = mem[r["jp"]]
            tag = f"g1:{gid}" if en else f"g1:{gid} untranslated there (glyph soup in game 1)"
            notes = "; ".join(x for x in (notes, tag) if x)
            seeded += bool(en)
        out.append(dict(id=r["id"], jp=r["jp"], en=en, notes=notes))
    write_tsv(path, out)
    return len(out), seeded


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--disc", default=str(ROOT / "work/disc/tree"))
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--no-seed", action="store_true", help="don't fill empty en from game 1's identical rows")
    a = ap.parse_args()
    tree = Path(a.disc)
    exe = (tree / "PSX.EXE").read_bytes()
    mem = {} if a.no_seed else g1_memory()
    ev, _ = event_rows(tree)
    n = s = 0
    for ent, rows in ev.items():
        if rows:
            k, j = merge(SCRIPT / "events" / f"e{ent}.tsv", rows, a.force, mem)
            n, s = n + k, s + j
    print(f"events: {n} rows in {sum(1 for r in ev.values() if r)} files, {s} seeded from game 1")
    for name, rows in (("exe", exe_rows(exe)), ("staff", staff_rows((tree / "DATA/FIN.EXE").read_bytes())),
                       ("sjis", sjis_rows(tree)), ("omk", omk_rows((tree / "OMK.EXE").read_bytes()))):
        k, j = merge(SCRIPT / f"{name}.tsv", rows, a.force, mem)
        print(f"{name}: {k} rows, {j} seeded from game 1")


if __name__ == "__main__":
    main()
