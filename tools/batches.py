"""batches.py: translation batches for the event scripts (docs/translator-brief.md).

    python -X utf8 tools/batches.py split            write trans/batches/bNNN.tsv (refuses if any exist)
    python -X utf8 tools/batches.py check b001 [..]  validate trans/en/bNNN.tsv against its batch; prints OK or errors
    python -X utf8 tools/batches.py merge            check every trans/en/*.tsv, wrap, write `en` into script/events
    python -X utf8 tools/batches.py todo             batches without an output file

Rows are grouped in families: rows whose simplified JP (tools/wrap.simplify) is equal once code arguments are
blanked share one translation; only the first (in sector order) goes into a batch, and merge copies its English to
the others with their own code arguments put back position by position. Batch input: `id<TAB>jp` (simplified, soft
line breaks removed). Output: `id<TAB>en` in the same simplified form with every code kept in order.
"""
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import font_en  # noqa: E402
import wrap  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
EVENTS = ROOT / "script" / "events"
BATCHES = ROOT / "trans" / "batches"
OUT = ROOT / "trans" / "en"
GLOSSARY = ROOT / "glossary.md"
BUDGET = 3500  # JP glyphs per batch (one Read)
csv.field_size_limit(10 ** 8)
ALLOWED = set(font_en.chars().values())
KATA = "ァ-ヴー"


def read_tsv(p):
    with open(p, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))


def write_tsv(p, rows, cols):
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write("\t".join(cols) + "\n")
        for r in rows:
            vals = [r.get(c, "") for c in cols]
            assert not any("\t" in v or "\n" in v for v in vals), r
            f.write("\t".join(vals) + "\n")


def event_files():
    return sorted(EVENTS.glob("e*.tsv"), key=lambda p: int(p.stem[1:]))


def glyphs(s):
    return len(re.sub(r"\{[^}]*\}", "", s))


def family_key(jp):
    return re.sub(r"\{(\w+):[0-9A-Fa-f]*\}", r"{\1}", wrap.simplify(jp))


def all_rows():
    """[(file, row)] in sector order, rows with glyph text only"""
    out = []
    for p in event_files():
        for r in read_tsv(p):
            if glyphs(r["jp"]):
                out.append((p, r))
    return out


def families():
    """{key: [rows]} in first-seen order"""
    fam = {}
    for p, r in all_rows():
        fam.setdefault(family_key(r["jp"]), []).append(r)
    return fam


def is_soup(r):
    return "soup" in r.get("notes", "")


def split():
    """batches of the families no row of which has English yet (game-1 seeds and glyph soup excluded); each entry
    carries `g1`, game 1's simplified English of the game-1 row sharing most of its text (tools/g1hint.py), or ''"""
    if BATCHES.exists() and any(BATCHES.glob("b*.tsv")):
        sys.exit("trans/batches already has batches; refusing to overwrite")
    import g1hint  # noqa: E402
    hint = g1hint.Hints()
    batches, cur, n = [], [], 0
    for key, rows in families().items():
        if any(r["en"] for r in rows) or all(is_soup(r) for r in rows):
            continue
        rep = rows[0]
        g = glyphs(rep["jp"])
        if cur and n + g > BUDGET:
            batches.append(cur)
            cur, n = [], 0
        sj = wrap.simplify(rep["jp"])
        cur.append({"id": rep["id"], "jp": sj, "g1": hint.get(sj)})
        n += g
    if cur:
        batches.append(cur)
    for i, b in enumerate(batches, 1):
        write_tsv(BATCHES / f"b{i:03d}.tsv", b, ["id", "jp", "g1"])
    print(f"{len(batches)} batches, {sum(len(b) for b in batches)} entries, "
          f"{sum(bool(e['g1']) for b in batches for e in b)} with a game-1 hint")


# --- glossary -----------------------------------------------------------------------------------------------------


def glossary():
    """[(jp, en, avoid)] from the glossary tables (rows with a JP and EN cell)"""
    out = []
    for line in GLOSSARY.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and line.startswith("|") and cells[0] not in ("JP", "") and not set(cells[0]) <= set("-"):
            avoid = [a.strip() for a in cells[4].split(",")] if len(cells) > 4 and cells[4] else []
            out.append((cells[0], cells[1], avoid))
    return out


def term_in(term, jp):
    """whole-run match: a katakana term must not sit inside a longer katakana run"""
    for m in re.finditer(re.escape(term), jp):
        a, b = m.start(), m.end()
        if re.fullmatch(f"[{KATA}]+", term):
            if (a and re.match(f"[{KATA}]", jp[a - 1])) or (b < len(jp) and re.match(f"[{KATA}]", jp[b])):
                continue
        return True
    return False


# --- check --------------------------------------------------------------------------------------------------------


# full-width glyphs kept as raw halfwords: the choice-box frame (set B), and 〔 (0x0E), the page marker on its own
# line in the ending epilogue narration (3B6B-3B76)
FULL = {"　": "[00][00]", "｛": "[DA][05]", "｝": "[DB][05]", "〔": "[0E][00]"}
SKIP = "-"  # translator's mark for a row that is not text to translate (kept Japanese, reason in the glossary)


def to_printer(en):
    """final `en` markup: full-width choice glyphs become raw halfword escapes for tools/en.py"""
    return "".join(FULL.get(c, c) for c in en)


def check_row(rid, jp, en, terms):
    if en == SKIP:
        return []
    errs = []
    if wrap.codes(jp) != wrap.codes(en):
        errs.append(f"{rid}: codes differ\n    jp {''.join(wrap.codes(jp))}\n    en {''.join(wrap.codes(en))}")
    text = re.sub(r"\{[^}]*\}", "", en)
    bad = sorted(set(text) - ALLOWED - set(FULL))
    if bad:
        errs.append(f"{rid}: characters not in the font: {''.join(bad)!r}")
    if re.search(r"[A-Za-z]{30,}", text):
        errs.append(f"{rid}: a word too long to wrap")
    if re.search(r"\{name:\w+\}(st|nd|rd|th|s)\b", en):
        errs.append(f"{rid}: suffix glued to a name code")
    if text.strip() == "":
        errs.append(f"{rid}: empty English")
    jpt = re.sub(r"\{[^}]*\}", "", jp)
    for tj, te, avoid in terms:
        if term_in(tj, jpt) and te.split(" (")[0] not in text:
            errs.append(f"{rid}: glossary {tj} -> {te} missing")
        for a in avoid:
            if a and re.search(r"\b" + re.escape(a) + r"\b", text):
                errs.append(f"{rid}: avoided spelling {a!r} (use {te})")
    import honorifics  # noqa: E402 (imports this module)
    nm = {tj: te.split(" (")[0] for tj, te, _ in terms if re.fullmatch(f"[{KATA}]+", tj)}
    errs += [f"{rid}: {e}" for e in honorifics.missing(jp, en, nm)]
    try:
        for c, ln in wrap.lines_report(wrap.wrap_for(jp, en)):
            if c > wrap.CELLS:
                errs.append(f"{rid}: line over {wrap.CELLS} cells after wrap: {ln}")
    except Exception as e:  # noqa: BLE001
        errs.append(f"{rid}: wrap failed: {e}")
    return errs


def check(name, terms=None):
    terms = glossary() if terms is None else terms
    src = read_tsv(BATCHES / f"{name}.tsv")
    outp = OUT / f"{name}.tsv"
    if not outp.exists():
        return [f"{name}: no output file {outp}"]
    out = read_tsv(outp)
    errs = []
    ids = [r["id"] for r in out]
    want = [r["id"] for r in src]
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        errs.append(f"{name}: duplicate ids {sorted(dup)}")
    if set(ids) != set(want):
        errs.append(f"{name}: missing {sorted(set(want) - set(ids))} extra {sorted(set(ids) - set(want))}")
    en = {r["id"]: r.get("en") or "" for r in out}
    for r in src:
        if r["id"] in en:
            errs += check_row(r["id"], r["jp"], en[r["id"]], terms)
    return errs


def with_args(rep_en, rep_jp, jp):
    """the representative's English with this row's code arguments"""
    mine = iter(wrap.codes(jp))
    return "".join(next(mine) if wrap.is_code(t) and t != "{n}" else t for t in wrap.tokens(rep_en))


def merge():
    terms = glossary()
    trans, failed = {}, []
    for p in sorted(OUT.glob("b*.tsv")):
        errs = check(p.stem, terms)
        if errs:
            failed.append(p.stem)
            print(f"{p.stem}: {len(errs)} errors, skipped")
            continue
        src = {r["id"]: r["jp"] for r in read_tsv(BATCHES / p.name)}
        for r in read_tsv(p):
            trans[r["id"]] = r["en"]
    en_by_id = {}
    for key, rows in families().items():
        rep = rows[0]
        if rep["id"] not in trans or trans[rep["id"]] == SKIP:
            continue
        for r in rows:
            en = with_args(trans[rep["id"]], rep["jp"], r["jp"])
            en_by_id[r["id"]] = to_printer(wrap.wrap_for(r["jp"], en))
    changed = 0
    for p in event_files():
        rows = read_tsv(p)
        cols = list(rows[0].keys()) if rows else ["id", "jp", "en", "notes"]
        dirty = False
        for r in rows:
            new = en_by_id.get(r["id"])
            if new is not None and r.get("en") != new:
                r["en"] = new
                dirty = True
                changed += 1
        if dirty:
            write_tsv(p, rows, cols)
    print(f"merged {len(trans)} translations -> {changed} rows changed; failed batches: {failed or 'none'}")
    return 1 if failed else 0


def main(argv):
    if not argv or argv[0] not in ("split", "check", "merge", "todo"):
        print(__doc__)
        return 2
    if argv[0] == "split":
        split()
        return 0
    if argv[0] == "merge":
        return merge()
    if argv[0] == "todo":
        todo = [p.stem for p in sorted(BATCHES.glob("b*.tsv")) if not (OUT / p.name).exists()]
        print(f"{len(todo)} to do: {' '.join(todo[:40])}{' ...' if len(todo) > 40 else ''}")
        return 0
    bad = 0
    for name in argv[1:]:
        errs = check(name)
        print(f"{name}: OK" if not errs else "\n".join(errs))
        bad += bool(errs)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
