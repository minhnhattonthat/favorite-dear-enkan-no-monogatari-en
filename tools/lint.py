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
Rows with an empty `en` (kept Japanese: glyph soup, name grids; reasons in the notes) are skipped.
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
         "PSX.141C2C": 12, "PSX.141C38": 12, "PSX.141C40": 12, "PSX.141C4C": 12, "PSX.141C58": 12}  # save_menu


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


def event_row(rid, jp, en):
    errs = []
    a, b = wrap.codes(jp), wrap.codes(en)
    if core(a) != core(b) or b.count("{wait}") < a.count("{wait}"):
        errs.append(f"{rid}: control codes differ from the JP\n    jp {''.join(a)}\n    en {''.join(b)}")
    norm = RAW.sub("　", en)
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
    for ln in re.split(r"\{n\}|\{wait\}|\{clear\}", en):
        t = text_of(ln)
        if len(t) > SLOTS.get(rid, LETTERS):
            errs.append(f"{rid}: {len(t)} letters > {SLOTS.get(rid, LETTERS)}: {t!r}")
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
    for path in sorted((extract.SCRIPT / "events").glob("e*.tsv")):
        for row in extract.read_tsv(path):
            if row["en"] and row["en"] != batches.SKIP:
                n += 1
                errs += event_row(row["id"], row["jp"], row["en"])
    for row in extract.read_tsv(extract.SCRIPT / "exe.tsv"):
        if row["en"]:
            n += 1
            errs += exe_row(row["id"], row["jp"], row["en"])
    for row in extract.read_tsv(extract.SCRIPT / "staff.tsv"):
        if row["en"]:
            n += 1
            errs += staff_row(row["id"], row["en"])
    return errs, n


if __name__ == "__main__":
    found, rows = lint()
    for e in found:
        print(e)
    print(f"lint: {rows} rows, {len(found)} findings")
    sys.exit(1 if found else 0)
