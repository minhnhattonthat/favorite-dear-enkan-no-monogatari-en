"""menuopts.py: the angel's topic choices in hero visits, and the English ones that do not fit the choice menu.

    python -X utf8 tools/menuopts.py            list overflowing option rows (exit 1 if any)

Ported from game 1 (`../favorite-dear-en/tools/menuopts.py`, its issue #4). How the menu works (op 0x90,
docs/re/events.md): a script runs `00D4` then `0090 <value> <table>` once per option. 00D4 puts the printer in
menu mode, so each 0x90 prints the first page (up to {wait}) of the table message keyed `value` as one menu line,
indented one cell for the cursor; the chosen one is then printed again as the angel's line. The menu has one line
per option and 19 cells after the indent (JP options are at most 19 glyphs), so an English option must be one line
of at most 19 cells: a second line pushes the next option down under the wrong cursor slot, and letters past
cell 19 are cut (game 1 issue #4: "If there's anything I can do, I'll hel").

Option rows = every message of a table that a 00D4-prefixed 0x90 reads, whose first page is the angel's (spk E783);
the hero's "anything else?" rows in the same tables are printed normally, never as options. Rows are matched by
(sector, byte offset), so GDATA entries that share a sector (extract.EVENT_ALIASES) resolve to the same rows.
"""
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import evscript  # noqa: E402
import gdata  # noqa: E402
import wrap  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CELLS = 19
OP_MENU, OP_PRINT_KEYED = 0xD4, 0x90
csv.field_size_limit(10 ** 8)


def option_keys(disc=ROOT / "work/disc/tree"):
    """{(sector, byte offset)} of every message in a table that a menu-mode 0x90 reads"""
    out = set()
    for sec, size, data, where in evscript.script_files(disc):
        sc = evscript.Script(data)
        its = sc.items
        msgs = [(s, e) for kind, s, e in its if kind == "msg"]
        for k, (kind, s, e) in enumerate(its):
            if not (kind == "op" and sc.code[s] == OP_PRINT_KEYED and k and its[k - 1][0] == "op"
                    and sc.code[its[k - 1][1]] == OP_MENU):
                continue
            table = sc.code[s + 2] & 0x7FFF
            for ms, me in msgs:  # the 0x90 scan runs from the table reference to the first 0xFFFC
                if ms < table:
                    continue
                if ms > table and sc.code[ms] == 0xFFFC:
                    break
                out.add((sec, sc.byte(ms)))
    return out


def option_lines(markup):
    """text lines of the first page of an angel row (None when the first page is not the angel's)"""
    page = markup.split("{wait}")[0]
    if "{spk:E783}" not in page:
        return None
    return [ts for ts in (wrap.tokens(ln) for ln in page.split("{n}")) if wrap.has_text(ts)]


def overflows(disc=ROOT / "work/disc/tree"):
    """[(id, problem, en first page)] for option rows whose English does not fit the menu; also the option count"""
    keys = option_keys(disc)
    sector = {i: sec for i, sec, cnt, kd, data in gdata.entries(disc)}
    bad, n = [], 0
    for p in sorted((ROOT / "script/events").glob("*.tsv")):
        with open(p, encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
                ent, off = r["id"][1:].split(".")
                if (sector[int(ent)], int(off, 16)) not in keys or not r["en"]:
                    continue
                lines = option_lines(r["en"])
                if lines is None:
                    continue
                n += 1
                first = r["en"].split("{wait}")[0]
                if len(lines) != 1:
                    bad.append((r["id"], f"{len(lines)} lines", first))
                elif wrap.cells(lines[0]) > CELLS:
                    bad.append((r["id"], f"{wrap.cells(lines[0])} cells", first))
    return bad, n


def main():
    bad, n = overflows()
    for rid, why, first in bad:
        print(f"{rid}\t{why}\t{re.sub(r'^{fb:[0-9A-F]+}', '', first)}")
    print(f"{n} option rows, {len(bad)} overflow", file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
