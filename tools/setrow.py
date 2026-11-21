"""setrow.py: set the `en` (and optionally `notes`) of script rows from a patch TSV, through extract's TSV writer
(keeps every column; refuses unknown ids). The patch file has the columns `id`, `en`, `notes` (notes may be empty:
then the row's notes are kept).

    python -X utf8 tools/setrow.py PATCH.tsv      # rows go to script/events/eNNN.tsv, script/exe.tsv (PSX.*/OMK.*),
                                                  # script/staff.tsv (FIN.*), script/sjis.tsv (anything else found)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import extract  # noqa: E402


def target(rid):
    if rid.startswith("e") and "." in rid:
        return extract.SCRIPT / "events" / f"{rid.split('.')[0]}.tsv"
    if rid.startswith(("PSX.", "OMK.")):
        return extract.SCRIPT / "exe.tsv"
    if rid.startswith("FIN."):
        return extract.SCRIPT / "staff.tsv"
    return extract.SCRIPT / "sjis.tsv"


def main(patch):
    lines = Path(patch).read_text(encoding="utf-8").split("\n")
    head = lines[0].rstrip("\r").split("\t")
    if head[:2] != ["id", "en"]:
        sys.exit(f"{patch}: header must start id<TAB>en")
    todo = {}
    for n, line in enumerate(lines[1:], 2):
        if not line.strip():
            continue
        rec = dict(zip(head, line.rstrip("\r").split("\t")))
        todo.setdefault(target(rec["id"]), {})[rec["id"]] = rec
    for path, recs in todo.items():
        rows = extract.read_tsv(path)
        seen = set()
        for r in rows:
            if r["id"] in recs:
                rec = recs[r["id"]]
                r["en"] = rec["en"]
                if rec.get("notes"):
                    r["notes"] = rec["notes"]
                seen.add(r["id"])
        missing = set(recs) - seen
        if missing:
            sys.exit(f"{path}: unknown ids {sorted(missing)}")
        extract.write_tsv(path, rows)
        print(f"{path.name}: {len(seen)} rows set")


if __name__ == "__main__":
    main(sys.argv[1])
