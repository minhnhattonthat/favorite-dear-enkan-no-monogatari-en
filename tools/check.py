"""check.py: the repo's one-command check (tests + text lint). The pre-commit hook runs it.

    python -X utf8 tools/check.py

Runs pytest over tests/ (slow emulator / full-disc tests are marked `slow` and left out; run them with
`pytest -m slow`), then tools/lint.py over script/ once it exists. Exit 0 only if every step passes.
ROM-dependent tests skip when rom/ is absent."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    rc = subprocess.run([sys.executable, "-X", "utf8", "-m", "pytest", "-q", "-m", "not slow", str(ROOT / "tests")],
                        cwd=ROOT).returncode
    lint = ROOT / "tools" / "lint.py"
    if lint.is_file():
        rc = rc or subprocess.run([sys.executable, "-X", "utf8", str(lint)], cwd=ROOT).returncode
    sys.exit(rc)
