"""showrow.py: print script rows' JP and EN with control codes flattened (pairs.flat), for review and polish.

    python -X utf8 tools/showrow.py ID [ID ...] [--raw]     ids like e924.1A9C, PSX.141F44, FIN.278, omk.13B86E
    python -X utf8 tools/showrow.py ID --grep TEXT          only the boxes (¦-separated) containing TEXT
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import pairs  # noqa: E402
from setrow import target  # noqa: E402


def row(rid):
    with target(rid).open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            if r["id"] == rid:
                return r
    return None


def main(argv):
    raw = "--raw" in argv
    grep = argv[argv.index("--grep") + 1] if "--grep" in argv else None
    ids = [a for i, a in enumerate(argv) if not a.startswith("--") and not (i and argv[i - 1] == "--grep")]
    for rid in ids:
        r = row(rid)
        if r is None:
            print(f"{rid}: not found")
            continue
        jp, en = (r["jp"], r["en"]) if raw else (pairs.flat(r["jp"]), pairs.flat(r["en"]))
        if grep:
            jb, eb = jp.split(" ¦ "), en.split(" ¦ ")
            hits = [i for i, b in enumerate(eb) if grep in b] or [i for i, b in enumerate(jb) if grep in b]
            jp = " ¦ ".join(jb[i] for i in hits if i < len(jb))
            en = " ¦ ".join(eb[i] for i in hits if i < len(eb))
        print(f">> {rid}\nJP: {jp}\nEN: {en}\n")


if __name__ == "__main__":
    main(sys.argv[1:])
