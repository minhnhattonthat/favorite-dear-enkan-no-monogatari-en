"""Story pass through `codex exec` (no subagents in an Orca worker): one read-only review per chapter file.

    python -X utf8 tools/story_review.py ch01 [ch02 ...]   reports -> work/qa/story/reports/<ch>.md
    python -X utf8 tools/story_review.py --todo            chapters the manifest says still need a verdict

The prompt is the brief + chapter + synopsis + style reference + glossary on stdin (codex's read-only sandbox can't
start processes, so it gets everything inline). Then write `<ch><TAB>ok|issue|fixed<TAB>note` into
work/qa/story/verdicts/<ch>.tsv from the report's Assessment, and its Minors into docs/polish.md.
"""
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STORY = ROOT / "work" / "qa" / "story"


def prompt(ch: str) -> str:
    parts = [(STORY / "brief.md").read_text(encoding="utf-8"),
             f"\n\n=== CHAPTER FILE {ch}.txt ===\n", (STORY / "chapters" / f"{ch}.txt").read_text(encoding="utf-8")]
    for name in ("docs/synopsis.md", "docs/style-reference.md", "glossary.md"):
        parts += [f"\n\n=== {name} ===\n", (ROOT / name).read_text(encoding="utf-8")]
    return "".join(parts)


def run(ch: str) -> str:
    out = STORY / "reports" / f"{ch}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()  # a failed run must not leave the last run's report behind
    codex = shutil.which("codex")
    r = subprocess.run([codex, "exec", "-s", "read-only", "--skip-git-repo-check", "-C", str(ROOT), "-o", str(out), "-"],
                       input=prompt(ch), text=True, encoding="utf-8", capture_output=True)
    ok = out.exists() and out.stat().st_size > 0
    return f"{ch}: {'ok' if ok else 'FAILED rc=' + str(r.returncode) + ' ' + r.stderr[-300:]}"


def main(argv):
    if argv == ["--todo"]:
        subprocess.run([sys.executable, "-X", "utf8", str(Path(__import__("skill").SKILL) / "scripts" / "qa_gate.py"),
                        "todo", str(STORY / "manifest.tsv"), str(STORY / "verdicts"), "--size", "1"])
        return
    with ThreadPoolExecutor(max_workers=4) as ex:
        for line in ex.map(run, argv):
            print(line, flush=True)


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main(sys.argv[1:])
