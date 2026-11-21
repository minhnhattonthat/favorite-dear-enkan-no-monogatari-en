"""fitcheck.py: romdiff every file the English build edits against its allowed write ranges (the phase 7 gate).
Game 1's (../favorite-dear-en/tools/fitcheck.py), adapted: two EXE text sites, u16 GDATA directories, the staff roll
inside DATA/FIN.EXE.

    python -X utf8 tools/fitcheck.py [--build build/files_fd3_en]

Allowed ranges, derived from the inputs rather than the build output:
- PSX.EXE and OMK.EXE (OMK at extract.omk_delta): each `script/exe.tsv` string slot (the JP string's byte length;
  the name-entry grid is skipped), the u32 pointers to each slot (a grown string is repointed: insert.exe_text),
  insert.REPOINT (where grown strings go), the bytes armips changes when asm/font.asm (and, PSX.EXE only,
  asm/btname.asm and asm/skill.asm) is assembled onto the untouched EXE, and the directory entries of moved scripts;
  OMK.EXE also its Mini Event script code (extract.OMK_MINI_CODE, script/omk.tsv).
- TITLE/EPILOG.EXE: the bytes asm/epilog.asm changes on the untouched EXE (incl. its appended sector), directory
  entries of moved scripts.
- DATA/FIN.EXE: the staff-roll block up to and including its 0xFF, and the bytes asm/fin.asm changes.
- GOVER/FD_BALL/PS_MOV.EXE: directory entries of moved scripts only.
- GDATA.BIN: the sectors of every script that has rows in `script/events/`, plus the appended tail (moved scripts),
  plus each redrawn image's slot (tools/gfx.py, gfx/*.tsv, and the pack copies in gfx.MIRRORS).
- TITLE/*.PSS: the whole file, for the title screens gfx/TTL_*.tsv redraws (size kept).
Exit 1 when any file has a changed byte outside its ranges (romdiff.check) or a file the build edits has no rule."""
import argparse
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import extract  # noqa: E402
import gdata  # noqa: E402
import gfx  # noqa: E402
import insert  # noqa: E402
import romdiff  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TREE = insert.TREE


def diff_ranges(a, b):
    """inclusive-exclusive ranges where a and b differ (b may be longer)"""
    out, start = [], None
    n = max(len(a), len(b))
    for i in range(n):
        same = i < len(a) and i < len(b) and a[i] == b[i]
        if not same and start is None:
            start = i
        elif same and start is not None:
            out.append(range(start, i))
            start = None
    if start is not None:
        out.append(range(start, n))
    return out


def moved(orig_psx, new_psx):
    """the (u16 sector, u16 count) entries of PSX.EXE's GDATA directory that the build changed (moved scripts)"""
    base = insert.EXE_DIRS["PSX.EXE"]
    return {orig_psx[base + 4 * i:base + 4 * i + 4] for i in range(gdata.GCOUNT)
            if orig_psx[base + 4 * i:base + 4 * i + 4] != new_psx[base + 4 * i:base + 4 * i + 4]}


def dir_entries(name, exe, patterns):
    base = insert.EXE_DIRS.get(name)
    if base is None:
        return []
    return [range(base + 4 * i, base + 4 * i + 4) for i in range(gdata.GCOUNT)
            if exe[base + 4 * i:base + 4 * i + 4] in patterns]


def exe_ranges(name, orig):
    """string slots, their u32 pointers, REPOINT and the font hook in PSX.EXE or OMK.EXE"""
    table = extract.exe_table()
    omk = name == "OMK.EXE"
    r = []
    for row in extract.read_tsv(extract.SCRIPT / "exe.tsv"):
        if "name-entry grid" in row["notes"]:
            continue
        off = int(row["id"].split(".")[1], 16)
        if omk:
            off += extract.omk_delta(off)
        r.append(range(off, off + len(table.encode(row["jp"]))))
        r += [range(p, p + 4) for p in insert.u32_refs(orig, off + extract.EXE_VA)]
    shift = insert.OMK_SHIFT if omk else 0
    r.append(range(insert.REPOINT[0] + shift - extract.EXE_VA, insert.REPOINT[1] + shift - extract.EXE_VA))
    r += diff_ranges(orig, insert.hooked(name, orig))
    if omk:  # the Omake Mini Event script, rebuilt in place (script/omk.tsv; insert.omk_mini_edit)
        r.append(range(*extract.OMK_MINI_CODE))
    if not omk:  # battle name plates (asm/btname.inc): its routine, data and enemy names, PSX.EXE only
        r += diff_ranges(orig, insert.assemble(orig, "btname.asm"))
        r += diff_ranges(orig, insert.assemble(orig, "skill.asm"))  # hero status skill names (asm/skill.inc)
        r += diff_ranges(orig, insert.name_entry(orig))  # English name entry (asm/name.inc)
    return r


def allowed(name, orig, orig_psx, patterns):
    """the allowed ranges of `name`, or None when the gate has no rule for it"""
    if name == "GDATA.BIN":
        secs = {}
        for ent, sec, cnt, kd, _ in gdata.entries(TREE):
            secs.setdefault(ent, (sec, cnt))
        r = []
        for p in (extract.SCRIPT / "events").glob("e*.tsv"):
            sec, cnt = secs[int(p.stem[1:])]
            r.append(range(sec * insert.SECTOR, (sec + cnt) * insert.SECTOR))
        for e in gfx.entries():  # redrawn images (gfx/*.tsv), each in its own slot, and pack copies (MIRRORS)
            if gfx.is_pss(e):
                continue
            for x in [e] + [p for p, _ in gfx.MIRRORS.get(e, [])]:
                off, size = gfx.slot(orig_psx, x, orig)
                r.append(range(off, off + size))
        return r + [range(len(orig), len(orig) + (1 << 30))]
    if name.startswith("TITLE/") and name.endswith(".PSS"):  # gfx/TTL_*.tsv: the whole file, same size
        return [range(0, len(orig))] if name in {gfx.pss_path(e) for e in gfx.entries() if gfx.is_pss(e)} else None
    r = dir_entries(name, orig, patterns)
    if name in ("PSX.EXE", "OMK.EXE"):
        return r + exe_ranges(name, orig)
    if name == "TITLE/EPILOG.EXE":
        return r + diff_ranges(orig, insert.assemble(orig, "epilog.asm"))
    if name == "DATA/FIN.EXE":
        block = extract.fin_block(orig)
        r.append(range(extract.FIN_TEXT, extract.FIN_TEXT + len(block) + 1))
        return r + diff_ranges(orig, insert.assemble(orig, "fin.asm"))
    if name in insert.EXE_DIRS:
        return r
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--build", default=str(ROOT / "build" / "files_fd3_en"))
    a = ap.parse_args()
    build = Path(a.build)
    orig_psx = (TREE / "PSX.EXE").read_bytes()
    patterns = moved(orig_psx, (build / "PSX.EXE").read_bytes())
    print("moved scripts: " + (" ".join("%04X" % struct.unpack("<H", p[:2])[0] for p in sorted(patterns)) or "none"))
    bad = 0
    for path in sorted(p for p in build.rglob("*") if p.is_file()):
        name = path.relative_to(build).as_posix()
        orig, new = (TREE / name).read_bytes(), path.read_bytes()
        rng = allowed(name, orig, orig_psx, patterns)
        if rng is None:
            print(f"{name}: FAIL (no rule for this file)")
            bad += 1
            continue
        errs, ok = romdiff.check(orig, new, rng, [])
        print(f"{name}: {'FAIL' if errs else 'ok'} ({ok} allowed diffs, {len(new) - len(orig):+d} bytes)")
        for e in errs[:10]:
            print("   ", e)
        bad += bool(errs)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
