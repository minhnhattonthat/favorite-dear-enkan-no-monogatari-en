"""cover_sweep.py: text-coverage sweep, one `warp.py --event eNNN` (or --battle) run per GDATA script entry, resumable.
Port of game 1's tool.

    python -X utf8 tools/cover_sweep.py freeze [--build work/qa/cover_build]
        copies build/fd3_en.bin/.cue there and writes strings.tsv (textcover_map.py strings, with the waivers of
        unloaded entries in waive.tsv) and entries.txt (every entry with a translated row that some event id loads).
        Freeze before a sweep: rebuilds then don't disturb it (coverage is by row id).
    python -X utf8 tools/cover_sweep.py run [--build ..] [--root work/qa/cover] [-j 2] [--frames 30000]
              [--only e453,e747] [--battle] [--todo]
        runs every entry of entries.txt with no finished run under --root (a line starting with "exit" in
        <root>/ev_eNNN/emu.txt; --battle: bt_eNNN, run as `warp.py --battle eNNN`), with tools/lua/textlog.lua, shots
        every 1500 frames, then converts each log (textcover_map.convert). --todo: only entries with a row no run
        under --root has shown yet. Re-run after a crash: it picks up where it stopped.
    python -X utf8 $SKILL/scripts/textcover.py <root> <build>/strings.tsv --waive <build>/waive.tsv
"""
import argparse
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import textcover_map  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def done(root, name):
    p = Path(root) / name / "emu.txt"
    if not p.exists():
        return False
    return any(x.startswith("exit") for x in p.read_text(encoding="utf-8", errors="replace").splitlines())


def shown_keys(root):
    out = set()
    for log in Path(root).glob("*/log.txt"):
        for x in log.read_text(encoding="utf-8", errors="replace").splitlines():
            if x.startswith("TEXT "):
                out.add(int(x.split()[1], 16))
    return out


def cmd_freeze(a):
    build = ROOT / a.build
    build.mkdir(parents=True, exist_ok=True)
    for ext in ("bin", "cue"):
        shutil.copyfile(ROOT / f"build/fd3_en.{ext}", build / f"fd3_en.{ext}")
    ns = argparse.Namespace(out=str(build / "strings.tsv"), waive=str(build / "waive.tsv"))
    textcover_map.cmd_strings(ns)
    exe, offs = textcover_map.row_table()
    ids, _ = textcover_map.id_entries(exe)
    loaded = set(ids.values())
    ents = [e for e, v in sorted(offs.items()) if e in loaded and any(r for _, r in v)]
    (build / "entries.txt").write_text("".join(f"e{e}\n" for e in ents), encoding="utf-8")
    print(f"{len(ents)} entries -> {build / 'entries.txt'}")


def cmd_run(a):
    build = ROOT / a.build
    root = ROOT / a.root
    cue = str(build / "fd3_en.cue").replace("\\", "/")
    ents = [x.strip() for x in (build / "entries.txt").read_text(encoding="utf-8").splitlines() if x.strip()]
    if a.only:
        ents = [e for e in ents if e in a.only.split(",")]
    pre = "bt_" if a.battle else "ev_"
    if a.todo:
        keys = {}
        for ln in (build / "strings.tsv").read_text(encoding="utf-8").splitlines():
            rid, k = ln.split("\t")
            keys.setdefault(rid.split(".")[0], set()).add(int(k, 16))
        seen = shown_keys(root)
        ents = [e for e in ents if keys.get(e, set()) - seen]
    todo = [e for e in ents if not done(root, pre + e)]
    print(f"{len(ents) - len(todo)} done, {len(todo)} to run", flush=True)
    exe, offs = textcover_map.row_table()

    def run(e):
        cmd = [sys.executable, "-X", "utf8", str(ROOT / "tools/debug/warp.py"), "--battle" if a.battle else "--event",
               e, "--cue", cue, "--root", str(root), "--frames", str(a.frames), "--shot-every", "1500", "-j", "1",
               "--lua", str(ROOT / "tools/lua/textlog.lua")]
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
        n = textcover_map.convert([root / (pre + e)], exe, offs, quiet=True)
        print(f"{e}\t{r.returncode}\t{n} rows", flush=True)

    with ThreadPoolExecutor(a.j) as ex:
        list(ex.map(run, todo))
    left = [e for e in ents if not done(root, pre + e)]
    print(f"finished; {len(left)} without an exit line: {' '.join(left[:40])}", flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("freeze")
    f.add_argument("--build", default="work/qa/cover_build")
    r = sub.add_parser("run")
    r.add_argument("--build", default="work/qa/cover_build")
    r.add_argument("--root", default="work/qa/cover")
    r.add_argument("-j", type=int, default=2)
    r.add_argument("--frames", type=int, default=30000)
    r.add_argument("--only")
    r.add_argument("--battle", action="store_true")
    r.add_argument("--todo", action="store_true")
    a = ap.parse_args()
    {"freeze": cmd_freeze, "run": cmd_run}[a.cmd](a)


if __name__ == "__main__":
    main()
