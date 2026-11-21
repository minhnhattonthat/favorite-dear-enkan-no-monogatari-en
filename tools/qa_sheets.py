"""qa_sheets.py: full-size review sheets for a warp tour (the warp's own sheet.png is half size).

    python -X utf8 tools/qa_sheets.py work/qa/tour [--max 9]

For every <tour>/<scene>/ with a "WARP OK" in log.txt, writes <scene>/qa_sheet.png (+ qa_sheet_2.png ...): the
frames from 300 before arrival on, near-duplicates dropped (--changed 0.01), div 1. Then:
    qa_gate.py init work/qa/p8/manifest.tsv work/qa/p8/tour --glob "qa_sheet*.png" --build build/fd3_en.bin
(game 1's tool, ../favorite-dear-en)
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from skill import SKILL  # noqa: E402

sys.path.insert(0, os.path.join(SKILL, "scripts"))
import sheet  # noqa: E402


def arrival(log):
    for line in log.splitlines():
        if line.startswith("WARP OK"):
            return int(line.rsplit(" f", 1)[1])
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tour")
    ap.add_argument("--max", type=int, default=9)
    ap.add_argument("--changed", type=float, default=0.01, help="drop frames differing by less (sheet.py)")
    a = ap.parse_args()
    n = 0
    for scene in sorted(os.listdir(a.tour)):
        d = os.path.join(a.tour, scene)
        logp = os.path.join(d, "log.txt")
        if not os.path.isfile(logp):
            continue
        at = arrival(open(logp, encoding="utf-8", errors="replace").read())
        if at is None:
            print(f"{scene}: not reached, skipped")
            continue
        for f in os.listdir(d):
            if f.startswith("qa_sheet"):
                os.remove(os.path.join(d, f))
        try:
            sheet.make(d, cols=3, lo=max(0, at - 300), limit=a.max, changed=a.changed, div=1,
                       out=os.path.join(d, "qa_sheet.png"))
        except SystemExit as e:  # no frames (a run in progress)
            print(f"{scene}: {e}")
            continue
        n += 1
    print(f"{n} scenes")


if __name__ == "__main__":
    main()
