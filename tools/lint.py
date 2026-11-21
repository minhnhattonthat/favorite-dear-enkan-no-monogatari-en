"""lint.py: width/overflow and control-code lint over the text the English build inserts (phase 7 gate; check.py
runs it). Checks what goes on the disc, `script/*.tsv`, not the translator batches (tools/batches.py check).

    python -X utf8 tools/lint.py

- Event rows (`script/events/`): the control codes match the JP's in order, where wrap.py's continuation pages may
  add `{wait}{clear}` and repeat the page's `{spk:X}`; every line fits 20 cells (40 letters, docs/windows.tsv
  dialogue) and every page holds no more text lines than max(3, the JP's); every character is in the font.
- EXE rows (`script/exe.tsv`): codes match; every line (split at {n}, {wait}, {clear}) fits 40 letters (hub_help,
  dialogue); the measured slots in SLOTS fit their window.
- Staff roll (`script/staff.tsv`): every line (split at '|') fits 28 letters with its indent (credits) and uses only
  font_en.FIN_CHARSET.
- Rows with an empty `en` (insert keeps the JP bytes) fail unless the JP is codes only, the notes say "glyph soup",
  or the id is in `docs/jp_kept.tsv` (id, reason). A `-` in an event `en` fails (insert would print it).
- Event lines using a name slot filled from an op-0xDE list (LIST_ROWS) are measured with the list's longest line.
Exit 1 on any finding."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import batches  # noqa: E402
import extract  # noqa: E402
import font_en  # noqa: E402
import wrap  # noqa: E402

RAW = re.compile(r"(?:\[[0-9A-F]{2}\]){2}")  # a raw glyph code (FULL: full-width space, braces): one cell
LETTERS = 40
STAFF_LETTERS = 28
# docs/windows.tsv rows measured on single EXE strings: id -> letters (incl. the hidden leading cells' padding)
SLOTS = {"PSX.135E38": 11,                                    # hub_location
         "PSX.133FFC": 10, "PSX.13400C": 10,                  # fairy names: week_nametag (hub_list shows 12)
         "PSX.133E3C": 22,                                    # confirm_prompt
         "PSX.134438": 8, "PSX.134444": 10,                   # confirm_choice: 3 / 4 hidden + 5 / 6
         "PSX.141C2C": 12, "PSX.141C38": 12, "PSX.141C40": 12, "PSX.141C4C": 12, "PSX.141C58": 12,  # save_menu
         "PSX.141F44": 42, "PSX.141F70": 42}  # packed pool fields, 21 cells each, padded field by field (notes)
# List strings by PSX.EXE address range: (first id offset, last id offset, letters, docs/windows.tsv variant). The
# caps are game 1's (glossary "PSX.EXE strings"), not yet measured here: lint enforces them and says so.
RANGES = [(0x132404, 0x132C30, 14, "place_name"),
          (0x134960, 0x13551C, 16, "item_name"), (0x135E50, 0x135F24, 16, "item_name"),
          (0x136420, 0x136460, 16, "item_name"),
          (0x1355D0, 0x1357E8, 12, "rank"),
          (0x135FE4, 0x136398, 16, "mission_title"), (0x1363C0, 0x136414, 16, "mission_title")]


def range_cap(rid):
    if rid.startswith("PSX."):
        off = int(rid[4:], 16)
        for lo, hi, cap, variant in RANGES:
            if lo <= off <= hi:
                return cap, variant
    return None


# op-0xDE list rows (handler 0x800CB770 copies line N into a {name:..} slot): (file, slot) -> list row. Lines of
# that file using the slot are measured with the list's longest line, not the 12-letter default.
LIST_ROWS = {("e396", "0380"): "e396.1558",   # fairy gift advice: item names
             ("e833", "0380"): "e833.10C4", ("e834", "0380"): "e834.17DA"}  # mission reports: mission titles
KEEP = Path(__file__).parent.parent / "docs" / "jp_kept.tsv"  # id<TAB>reason: rows whose Japanese ships on purpose


def kept():
    """ids allowed to keep their Japanese (docs/jp_kept.tsv), plus rule-based ones: glyph soup (notes say so)"""
    ids = set()
    for line in KEEP.read_text(encoding="utf-8").splitlines()[1:]:
        if line.strip():
            rid, reason = line.split("\t")[:2]
            if not reason.strip():
                raise ValueError(f"{KEEP.name}: {rid} has no reason")
            ids.add(rid)
    return ids


def untranslated(rid, jp, en, notes, keep):
    """a row whose JP prints text but whose en is empty (insert would keep the JP bytes), unless kept on purpose"""
    if en or rid in keep or (rid.startswith("e") and "(glyph soup in game 1)" in notes):
        return []
    if not wrap.has_text(wrap.tokens(RAW.sub("", jp))):
        return []  # codes only
    return [f"{rid}: empty en (Japanese would ship): list it in docs/jp_kept.tsv with a reason or translate it"]


def text_of(s):
    return re.sub(r"\{[^}]*\}", "", s)


def core(codes):
    """codes without page breaks and without a {spk:X} that repeats the last one (a continuation page's header)"""
    out, spk = [], None
    for c in codes:
        if c in ("{wait}", "{clear}"):
            continue
        if c.startswith("{spk:"):
            if c == spk:
                continue
            spk = c
        out.append(c)
    return out


def list_slots():
    """(event file, name slot) -> cells of the longest line an op-0xDE list row of that file copies into the slot"""
    out = {}
    for (f, slot), rid in LIST_ROWS.items():
        row = next(r for r in extract.read_tsv(extract.SCRIPT / "events" / f"{f}.tsv") if r["id"] == rid)
        body = row["en"].split("{fc}")[0] if f == "e396" else row["en"].replace("{fc}", "")  # e396: greeting follows
        lines = body.split("{n}")
        out[(f, slot)] = max(wrap.cells(wrap.tokens(ln)) for ln in lines)
    return out


def event_row(rid, jp, en, slots=None):
    errs = []
    a, b = wrap.codes(jp), wrap.codes(en)
    if core(a) != core(b) or b.count("{wait}") < a.count("{wait}"):
        errs.append(f"{rid}: control codes differ from the JP\n    jp {''.join(a)}\n    en {''.join(b)}")
    norm = RAW.sub("　", en)
    for (f, slot), n in (slots or {}).items():
        if rid.split(".")[0] == f:
            norm = norm.replace(f"{{name:{slot}}}", f"{{name:W{n}}}")
    for cells, ln in wrap.lines_report(norm):
        if cells > wrap.CELLS:
            errs.append(f"{rid}: line of {cells} cells > {wrap.CELLS}: {ln}")
    limit = max(wrap.LINES, wrap.page_lines(jp))
    for page in norm.split("{clear}"):
        n = sum(1 for ln in page.split("{n}") if wrap.has_text(wrap.tokens(ln)))
        if n > limit:
            errs.append(f"{rid}: page of {n} text lines > {limit}")
    bad = sorted(set(text_of(RAW.sub("", en))) - batches.ALLOWED - set(batches.FULL))
    if bad:
        errs.append(f"{rid}: characters not in the font: {''.join(bad)!r}")
    return errs


def exe_row(rid, jp, en):
    errs = []
    if wrap.codes(jp) != wrap.codes(en):
        errs.append(f"{rid}: control codes differ from the JP")
    cap = range_cap(rid)
    limit, why = (cap[0], f" ({cap[1]}, game 1's cap, unmeasured)") if cap and rid not in SLOTS else \
        (SLOTS.get(rid, LETTERS), "")
    for ln in re.split(r"\{n\}|\{wait\}|\{clear\}", en):
        t = text_of(ln)
        if len(t) > limit:
            errs.append(f"{rid}: {len(t)} letters > {limit}{why}: {t!r}")
    bad = sorted(set(text_of(en)) - batches.ALLOWED)
    if bad:
        errs.append(f"{rid}: characters not in the font: {''.join(bad)!r}")
    return errs


def staff_row(rid, en):
    errs = []
    for part in en.split("|"):
        body = part.lstrip("#%\\&")
        if len(body) > STAFF_LETTERS:
            errs.append(f"{rid}: {len(body)} letters > {STAFF_LETTERS}: {body!r}")
        bad = sorted(set(body) - set(font_en.FIN_CHARSET))
        if bad:
            errs.append(f"{rid}: characters not in the FIN font: {''.join(bad)!r}")
    return errs


def lint():
    errs, n = [], 0
    keep, slots = kept(), list_slots()
    for path in sorted((extract.SCRIPT / "events").glob("e*.tsv")):
        for row in extract.read_tsv(path):
            if row["en"] == batches.SKIP:
                errs.append(f"{row['id']}: en is the translator's '-' (insert would print it): empty it and keep-list it")
            elif row["en"]:
                n += 1
                errs += event_row(row["id"], row["jp"], row["en"], slots)
            else:
                errs += untranslated(row["id"], row["jp"], row["en"], row["notes"], keep)
    for name in ("exe.tsv", "sjis.tsv"):
        for row in extract.read_tsv(extract.SCRIPT / name):
            if row["en"]:
                n += 1
                if name == "exe.tsv":
                    errs += exe_row(row["id"], row["jp"], row["en"])
            else:
                errs += untranslated(row["id"], row["jp"], row["en"], row["notes"], keep)
    for row in extract.read_tsv(extract.SCRIPT / "staff.tsv"):
        if row["en"]:
            n += 1
            errs += staff_row(row["id"], row["en"])
        else:
            errs += untranslated(row["id"], row["jp"], row["en"], row["notes"], keep)
    return errs, n


if __name__ == "__main__":
    found, rows = lint()
    for e in found:
        print(e)
    print(f"lint: {rows} rows, {len(found)} findings")
    sys.exit(1 if found else 0)
