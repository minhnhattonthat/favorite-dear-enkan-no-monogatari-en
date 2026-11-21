"""Text coverage for the event scripts (phase 8 gate, `$SKILL/scripts/textcover.py`). Port of game 1's tool.

    python -X utf8 tools/textcover_map.py strings [--out build/strings.tsv] [--waive docs/text_unshown.tsv]
        one `row id<TAB>hex key` per translated row of the event scripts in the English build; key = GDATA entry << 16
        | byte offset of the row in the built file. Rows of entries that no event id loads come last.
    python -X utf8 tools/textcover_map.py convert LOGDIR [LOGDIR..]
        reads each run's log.txt (written by tools/lua/textlog.lua), maps every printer index to the row that holds it
        and appends `TEXT <hex key>` lines (the row's start key) to the same log.txt, once per key.
    python -X utf8 tools/textcover_map.py report LOGDIR [LOGDIR..]
        per entry: rows shown / rows (after convert).

How the map works: the loaded-event table at 0x80148C6C lists (event id, halfword offset into the buffer 0x80148CBC)
per slot (docs/re/debug.md); a printer index (halfword index into that buffer) belongs to the slot with the greatest
offset <= index; the event id names the GDATA entry through its u16 name hash (PSX.EXE 0x8014FCFC + 2 * id) and the
570-hash list (index + 395 = entry; tools/debug/evnames.py). warp.lua --event writes a target's hash into id 32's slot
("WARP patched slot 32 -> NAME"), so convert re-reads those lines.
"""
import argparse
import bisect
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "debug"))
import en  # noqa: E402
import evnames  # noqa: E402
import evscript  # noqa: E402
import extract  # noqa: E402
import gdata  # noqa: E402
import insert  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def id_entries(exe):
    """({event id: GDATA entry} for every id whose hash is in the list, {hash: entry})."""
    hashes = evnames.u16s(exe, evnames.HASHES, evnames.NHASH)
    ids = evnames.u16s(exe, evnames.IDTAB, evnames.NIDS)
    by_hash = {}
    for i, h in enumerate(hashes):
        by_hash.setdefault(h, evnames.GBASE + i)
    return {k: by_hash[h] for k, h in enumerate(ids) if h in by_hash}, by_hash


def entry_of(name, by_hash):
    """warp.lua's EVENT: eNNN or a game-1 name (hashed)."""
    m = re.fullmatch(r"e(\d+)", name)
    if m:
        return int(m[1])
    return by_hash.get(evnames.name_hash(name.upper()))


def row_table():
    """(original PSX.EXE, {entry: [(new byte offset, row id or None)] sorted}) for the English build."""
    tree = ROOT / "work/disc/tree"
    exe = (tree / "PSX.EXE").read_bytes()
    table = extract.event_table()
    out = {}
    for ent, sec, cnt, kd, data in gdata.entries(tree):
        ent_rows = extract.EVENT_ALIASES.get(ent, ent)
        path = extract.SCRIPT / "events" / f"e{ent_rows}.tsv"
        if kd != "script" or not path.exists():
            continue
        sc = evscript.Script(data)
        rows = extract.read_tsv(path)
        repl = {}
        for row in rows:
            text = insert.row_text(row, "en")
            if text is not None:
                repl[(int(row["id"].split(".")[1], 16) - sc.code_off) // 2] = en.encode(text, table)
        new, newpos = insert.rebuild_map(sc, repl)
        lst = []
        for row in rows:
            pc = (int(row["id"].split(".")[1], 16) - sc.code_off) // 2
            lst.append((sc.code_off + 2 * newpos(pc), row["id"] if row["en"] else None))  # None: kept JP
        out[ent] = sorted(lst)
    return exe, out


def cmd_strings(a):
    exe, offs = row_table()
    ids, _ = id_entries(exe)
    loaded = set(ids.values())
    lines, orphan, seen = [], [], set()
    for ent, v in sorted(offs.items()):
        for off, rid in v:
            if rid and rid not in seen:  # an alias entry repeats its rows: count them once, under the first entry
                seen.add(rid)
                (lines if ent in loaded else orphan).append(f"{rid}\t{ent << 16 | off:X}")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text("".join(x + "\n" for x in lines + orphan), encoding="utf-8")
    print(f"{len(lines) + len(orphan)} rows -> {a.out}; {len(orphan)} in entries no event id loads")
    if a.waive:
        why = "entry in no event id's load path (id -> hash table x 570-hash list): unused leftover"
        out = [f"{x.split(chr(9))[0]}\t{why}\n" for x in orphan]
        proven = ROOT / "docs/text_unshown_proven.tsv"  # rows proven unreachable by hand (id<TAB>proof)
        if proven.exists():
            out += [x + "\n" for x in proven.read_text(encoding="utf-8").splitlines()
                    if x.strip() and not x.startswith("#")]
        Path(a.waive).write_text("".join(out), encoding="utf-8")
        print(f"{len(out)} waivers ({len(orphan)} unloaded) -> {a.waive}")


def convert(logdirs, exe, offs, quiet=False):
    """Append TEXT lines to each run's log.txt; offs = row_table()[1] of the build the runs played."""
    ids0, by_hash = id_entries(exe)
    starts = {ent: [o for o, _ in v] for ent, v in offs.items()}
    alias = {a: b for a, b in extract.EVENT_ALIASES.items()}
    total = 0
    for d in logdirs:
        log = Path(d) / "log.txt"
        if not log.exists():
            continue
        lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
        lines = [x for x in lines if not x.startswith("TEXT ")]
        slots, keys, ids = {}, [], dict(ids0)
        for x in lines:
            m = re.search(r"WARP (?:patched slot|swapped id) (\d+) -> (\S+)", x)
            if m:
                e = entry_of(m[2], by_hash)
                if e is not None:
                    ids[int(m[1])] = e
                continue
            m = re.search(r"SCR (\d+) (\d+) (\d+)", x)
            if m:
                slots[int(m[1])] = (int(m[2]), int(m[3]))
                continue
            m = re.search(r"PIDX (\d+)", x)
            if not m:
                continue
            idx = int(m[1])
            best = None
            for eid, hoff in slots.values():
                if hoff <= idx and eid in ids and (best is None or hoff > best[1]):
                    best = (eid, hoff)
            if best is None:
                continue
            eid, hoff = best
            ent = alias.get(ids[eid], ids[eid])
            st = starts.get(ent)
            if not st:
                continue
            boff = 2 * (idx - hoff)
            k = bisect.bisect_right(st, boff) - 1
            if k < 0:
                continue
            key = ent << 16 | st[k]
            if key not in keys:
                keys.append(key)
        log.write_text("\n".join(lines + [f"TEXT {k:X}" for k in keys]) + "\n", encoding="utf-8")
        total += len(keys)
        if not quiet:
            print(f"{d}: {len(keys)} rows")
    return total


def cmd_convert(a):
    exe, offs = row_table()
    convert(a.logdirs, exe, offs)


def cmd_report(a):
    _, offs = row_table()
    keyrow = {ent << 16 | off: rid for ent, v in offs.items() for off, rid in v if rid}
    shown = set()
    for d in a.logdirs:
        log = Path(d) / "log.txt"
        if log.exists():
            for x in log.read_text(encoding="utf-8", errors="replace").splitlines():
                if x.startswith("TEXT "):
                    k = int(x.split()[1], 16)
                    if k in keyrow:
                        shown.add(keyrow[k])
    for ent, v in sorted(offs.items()):
        rids = [r for _, r in v if r]
        if rids:
            n = sum(r in shown for r in rids)
            if n:
                print(f"e{ent}\t{n}/{len(rids)}")
    print(f"total {len(shown)} rows shown")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("strings")
    s.add_argument("--out", default=str(ROOT / "build/strings.tsv"))
    s.add_argument("--waive", help="also write the rows of unloaded entries as textcover.py waivers (id<TAB>reason)")
    c = sub.add_parser("convert")
    c.add_argument("logdirs", nargs="+")
    r = sub.add_parser("report")
    r.add_argument("logdirs", nargs="+")
    a = ap.parse_args()
    {"strings": cmd_strings, "convert": cmd_convert, "report": cmd_report}[a.cmd](a)


if __name__ == "__main__":
    main()
