"""subrow.py: substring edits to script rows' `en`, applied through setrow.py (the TSV writer).

    python -X utf8 tools/subrow.py EDITS.tsv [--dry]

EDITS.tsv: `id<TAB>old<TAB>new` lines (no header; `#` lines skipped). `old` must occur exactly once in the row's raw
`en` (control codes included, e.g. `{n}`); `\\t` is not allowed in either. Writes work/subrow_patch.tsv and runs
setrow.py on it, so every column of the script TSVs is kept. --dry prints the results instead.
"""
import csv
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from showrow import row  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def main(argv):
    edits = [ln.rstrip("\r\n").split("\t") for ln in Path(argv[0]).read_text(encoding="utf-8").splitlines()
             if ln.strip() and not ln.startswith("#")]
    new = {}
    for e in edits:
        if len(e) != 3:
            sys.exit(f"bad line (need id<TAB>old<TAB>new): {e}")
        rid, old, rep = e
        r = row(rid)
        if r is None:
            sys.exit(f"{rid}: no such row")
        cur = new.get(rid, r["en"])
        if cur.count(old) != 1:
            sys.exit(f"{rid}: {old!r} occurs {cur.count(old)} times")
        new[rid] = cur.replace(old, rep)
    if "--dry" in argv:
        for rid, en in new.items():
            print(f"{rid}\t{en}")
        return
    out = ROOT / "work" / "subrow_patch.tsv"
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", quoting=csv.QUOTE_NONE, lineterminator="\n", escapechar=None)
        w.writerow(["id", "en", "notes"])
        for rid, en in new.items():
            w.writerow([rid, en, ""])
    subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "tools" / "setrow.py"), str(out)], check=True)


if __name__ == "__main__":
    main(sys.argv[1:])
