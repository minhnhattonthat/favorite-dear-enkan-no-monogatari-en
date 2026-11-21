"""Review pairs: one file per translation batch, JP and EN side by side with control codes stripped.

    python -X utf8 tools/pairs.py [bNNN ...]     write work/qa/review/pairs/bNNN.txt (all batches if none given)
    python -X utf8 tools/pairs.py --chapters     story-pass files work/qa/story/chapters/chNN[a-z].txt, chapters
                                                 from docs/synopsis.md (regenerate after every script edit)

Each entry is `>> id` then `JP: ...` and `EN: ...`; ` ¦ ` marks a new text box, `<name>` a runtime name.
Rows kept as `-` (not text / glyph soup) are skipped. Read by the phase-6 review pass (qa_gate manifest in
work/qa/review/).
"""
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "work" / "qa" / "review" / "pairs"


def flat(s: str) -> str:
    s = s.replace("{wait}{clear}", " ¦ ").replace("{wait}", " ¦ ")
    s = re.sub(r"\{name:[0-9A-F]+\}", "<name>", s)
    s = re.sub(r"\{n\}", " ", s)
    s = re.sub(r"\{[^}]*\}", "", s)
    s = re.sub(r"\[[0-9A-F]{2}\]", "", s)
    return re.sub(r"\s+", " ", s).strip(" ¦")


def load(path: Path) -> dict:
    with path.open(encoding="utf-8", newline="") as f:
        r = csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
        next(r)
        return {row[0]: row[-1] for row in r if row}


SEEN: set = set()


def write(b: str) -> int:
    """Boxes (JP, EN) already shown in an earlier entry are dropped (gender twins, repeated stock lines); an entry
    with nothing new left is skipped. Box lists of unequal length are shown whole."""
    jp = load(ROOT / "trans" / "batches" / f"{b}.tsv")
    en = load(ROOT / "trans" / "en" / f"{b}.tsv")
    lines, n = [], 0
    for i, j in jp.items():
        e = en.get(i, "-")
        if e.strip() == "-":
            continue
        jb, eb = flat(j).split(" ¦ "), flat(e).split(" ¦ ")
        if len(jb) == len(eb):
            keep = [(x, y) for x, y in zip(jb, eb) if (x, y) not in SEEN]
            SEEN.update(zip(jb, eb))
            if not keep:
                continue
            jb, eb = [x for x, _ in keep], [y for _, y in keep]
        lines += [f">> {i}", f"JP: {' ¦ '.join(jb)}", f"EN: {' ¦ '.join(eb)}", ""]
        n += 1
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{b}.txt").write_text("\n".join(lines), encoding="utf-8")
    return n


STORY = ROOT / "work" / "qa" / "story" / "chapters"
PART_MAX = 160_000  # bytes per story-pass file (one reviewer reads one file)


def chapters() -> list:
    """Chapter batch ranges from docs/synopsis.md `## Chapters` (`N. bAAA-bBBB: ...`)."""
    text = (ROOT / "docs" / "synopsis.md").read_text(encoding="utf-8")
    out = []
    for m in re.finditer(r"^(\d+)\. b(\d{3})(?:-b(\d{3}))?:", text, re.M):
        a = int(m.group(2))
        out.append((int(m.group(1)), a, int(m.group(3) or a)))
    return out


def story() -> None:
    """Story-pass files: one per chapter (split at batch boundaries into a, b, ... above PART_MAX bytes)."""
    if STORY.exists():
        for p in STORY.glob("*.txt"):
            p.unlink()
    STORY.mkdir(parents=True, exist_ok=True)
    files = 0
    for ch, a, b in chapters():
        parts, cur = [], []
        for n in range(a, b + 1):
            name = f"b{n:03d}"
            if not (ROOT / "trans" / "en" / f"{name}.tsv").exists():
                continue
            write(name)
            body = (OUT / f"{name}.txt").read_text(encoding="utf-8")
            if not body.strip():
                continue
            block = f"## batch {name}\n\n{body}\n"
            if cur and sum(len(x.encode()) for x in cur) + len(block.encode()) > PART_MAX:
                parts.append(cur)
                cur = []
            cur.append(block)
        if cur:
            parts.append(cur)
        for i, blocks in enumerate(parts):
            suffix = chr(ord("a") + i) if len(parts) > 1 else ""
            head = f"# Chapter {ch}{suffix} (b{a:03d}-b{b:03d}, part {i + 1}/{len(parts)})\n\n"
            (STORY / f"ch{ch:02d}{suffix}.txt").write_text(head + "".join(blocks), encoding="utf-8")
            files += 1
    print(f"{files} story-pass files -> {STORY.relative_to(ROOT)}")


def main(argv):
    if argv == ["--chapters"]:
        return story()
    names = argv or sorted(p.stem for p in (ROOT / "trans" / "en").glob("b*.tsv"))
    total = sum(write(b) for b in names)
    print(f"{len(names)} pair files, {total} entries -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main(sys.argv[1:])
