"""jpcheck.py: release gate for Japanese left in the English build (`$SKILL/scripts/jp_left.py` plus the row sources).

    python -X utf8 tools/jpcheck.py [--build build/files_fd3_en]

1. Rows: every row in script/ whose JP has kana/kanji must have an English `en` with no kana/kanji, unless the row
   is in docs/text_unshown_proven.tsv (code that can't reach it) or docs/jp_kept.tsv (kept on purpose, with the
   reason), or sits in a GDATA entry no event id loads (unused leftovers, textcover_map.id_entries).
2. Binaries: `jp_left.py --orig` on the built PSX.EXE and OMK.EXE limited to the spans of the script/exe.tsv rows
   (the EXE's text; the rest holds SDK and kana-conversion tables that only look like text; OMK's copies sit at
   extract.omk_delta). Event scripts, FIN.EXE credits and OMK mini events are rebuilt from rows (step 1).
Exit 1 when anything unintended is left. Ported from game 1 (../favorite-dear-en/tools/jpcheck.py)."""
import argparse
import csv
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from skill import SKILL  # noqa: E402

JP = re.compile(r"[぀-ヿ一-鿿]")
WAIVES = ["docs/text_unshown_proven.tsv", "docs/jp_kept.tsv"]


def ids(path):
    p = ROOT / path
    if not p.is_file():
        return set()
    return {line.split("\t", 1)[0].strip() for line in p.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")}


def rows():
    for p in sorted((ROOT / "script").rglob("*.tsv")):
        with p.open(encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
                yield p, r


def loaded_entries():
    import textcover_map
    exe = (ROOT / "work" / "disc" / "tree" / "PSX.EXE").read_bytes()
    return set(textcover_map.id_entries(exe)[0].values())


def check_rows():
    import extract
    waived = set().union(*(ids(w) for w in WAIVES))
    loaded = loaded_entries()
    alias_of = {}  # entry whose rows live in another file (e902 -> e520): loaded if either loads
    for a, b in extract.EVENT_ALIASES.items():
        alias_of.setdefault(b, set()).add(a)
    bad, unloaded = [], 0
    for p, r in rows():
        jp, en = r.get("jp") or "", (r.get("en") or "").strip()
        if not JP.search(re.sub(r"\{[^}]*\}", "", jp)):
            continue
        if r["id"] in waived:
            continue
        if p.parent.name == "events":
            ent = int(p.stem[1:])
            if ent not in loaded and not (alias_of.get(ent, set()) & loaded):
                unloaded += 1
                continue
        if not en or en == "-" or JP.search(re.sub(r"\{[^}]*\}", "", en)):
            bad.append(f"{p.relative_to(ROOT).as_posix()} {r['id']}: en={en[:40]!r}")
    print(f"rows: {unloaded} Japanese rows skipped in entries no event id loads (unused leftovers)")
    return bad


def jp_left(*args):
    cmd = [sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts" / "jp_left.py"), *map(str, args)]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    return res.returncode, res.stdout.strip()


def main(argv=None):
    import extract
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", default=str(ROOT / "build" / "files_fd3_en"))
    a = ap.parse_args(argv)
    build, orig = Path(a.build), ROOT / "work" / "disc" / "tree"
    fail = 0
    bad = check_rows()
    print(f"rows: {len(bad)} with Japanese and no English (not waived)")
    for line in bad[:50]:
        print("  " + line)
    fail |= bool(bad)

    kept = ids("docs/jp_kept.tsv")
    spans = []  # (start, rough end, translated): each span is cut at the next row's start
    for p, r in rows():
        if p.name == "exe.tsv" and r["id"].startswith("PSX."):
            o = int(r["id"].split(".")[1], 16)
            spans.append((o, o + 2 * len(r["jp"]) + 2, (r.get("en") or "").strip() not in ("", "-")
                          and r["id"] not in kept))
    spans.sort()
    ranges = []
    for i, (o, end, live) in enumerate(spans):
        if live:
            nxt = spans[i + 1][0] if i + 1 < len(spans) else end
            ranges.append((o, min(end, nxt)))
    for exe in ("PSX.EXE", "OMK.EXE"):
        args = [build / exe, "--tbl", ROOT / "tbl" / "jp.tbl", "--orig", orig / exe, "--limit", 20]
        for lo, hi in ranges:
            d = 0
            if exe == "OMK.EXE":
                try:
                    d = extract.omk_delta(lo)
                except KeyError:
                    continue
            args += ["--range", f"{lo + d:X}-{hi + d:X}"]
        rc, out = jp_left(*args)
        print(f"{exe} text rows: " + (out.splitlines()[-1] if out else "no output"))
        if rc:
            print(out)
        fail |= rc != 0
    print("jpcheck: " + ("FAIL" if fail else "ok"))
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
