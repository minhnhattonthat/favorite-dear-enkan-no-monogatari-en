"""qa_carry.py: carry visual-QA verdicts from an earlier tour to a re-tour's sheets that are pixel-identical.

    python -X utf8 tools/qa_carry.py OLD_MANIFEST OLD_VERDICTS_DIR NEW_MANIFEST NEW_VERDICTS_DIR

Writes NEW_VERDICTS_DIR/carried_<new manifest stem>.tsv: one `id<TAB>ok<TAB>carried: ...` line for every id of the
new manifest (`$SKILL/scripts/qa_gate.py init` format: id, path, sha1, changed) whose sheet has the same sha1 as a
sheet of the old manifest whose latest verdict is ok/fixed. Run it right after `qa_gate.py init` on the new manifest:
the verdict file is then newer than every sheet's change time. Same pixels = same screen, so the verdict still holds;
everything else is left to `qa_gate.py todo`.
"""
import argparse
import os
from pathlib import Path


def manifest(path):
    out = {}
    for ln in Path(path).read_text(encoding="utf-8").splitlines():
        f = ln.split("\t")
        if len(f) >= 3 and not ln.startswith("#"):
            out[f[0]] = f[2]
    return out


def verdicts(d):
    """latest verdict per id, reading every *.tsv oldest first (qa_gate.py's rule)."""
    out = {}
    files = sorted(Path(d).glob("*.tsv"), key=os.path.getmtime)
    for p in files:
        for ln in p.read_text(encoding="utf-8").splitlines():
            f = ln.split("\t")
            if len(f) >= 2 and f[1] in ("ok", "issue", "fixed"):
                out[f[0]] = (f[1], f[2] if len(f) > 2 else "")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("old_manifest")
    ap.add_argument("old_verdicts")
    ap.add_argument("new_manifest")
    ap.add_argument("new_verdicts")
    a = ap.parse_args()
    old, new, ver = manifest(a.old_manifest), manifest(a.new_manifest), verdicts(a.old_verdicts)
    good = {}
    for i, h in old.items():
        v = ver.get(i)
        if v and v[0] in ("ok", "fixed"):
            good.setdefault(h, (i, v[1]))
    lines = []
    for i, h in new.items():
        if h in good:
            oid, note = good[h]
            lines.append(f"{i}\tok\tcarried: same pixels as {oid} ({Path(a.old_manifest).name}): {note}")
    Path(a.new_verdicts).mkdir(parents=True, exist_ok=True)
    out = Path(a.new_verdicts) / f"carried_{Path(a.new_manifest).stem}.tsv"
    out.write_text("".join(x + "\n" for x in lines), encoding="utf-8")
    print(f"{len(lines)} of {len(new)} sheets carried -> {out}")


if __name__ == "__main__":
    main()
