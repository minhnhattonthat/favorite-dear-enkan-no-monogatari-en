"""textforce.py: text coverage by forcing every message of each event file through the game's printer.
Port of game 1's tool (../favorite-dear-en/tools/textforce.py); files are GDATA entries here, not sectors.

A mash sweep (`cover_sweep.py`) plays one branch per event and shows a row or two of each file. This driver runs
`warp.py --event eNNN` with tools/lua/textforce.lua, which moves the printer's index to the next row still to show
each time the scene starts a message, so the scene's own print ops play the whole file. Resumable, in passes.

    python -X utf8 tools/textforce.py freeze [--build work/qa/cover_build]
        writes rows.json ({entry: [[start byte, row id or null]..], ends: {entry: used bytes}, choice: [row ids]})
        and sigs.json into the frozen build (`cover_sweep.py freeze` made it: fd3_en.bin/.cue, strings.tsv).
    python -X utf8 tools/textforce.py run [--build ..] [--root work/qa/force] [-j 2] [--frames 16000] [--only e453,..]
        one pass: every entry with a text row no log under --root (or --also dirs, e.g. work/qa/cover) shows yet
        gets a run into <root>/p<N>/<run> (N = the first pass number with no directory yet, or --pass N to resume).
        Battle entries (the battle table 0x8015060C) run as `warp.py --battle eNNN` with FORCE_ID = their id;
        TxxSEN (hero xx's battle lines, id xx) in a battle with hero xx in front; SSxxyy as an event for hero xx.
        Game 1's best settings: `--keypatch --var SKIPKEY=1 --var ADOPT=1 --var PRINTPATCH=1 --var RECHOICE=1
        --var NOBATTLE=1 --var MASH_ROTATE=3`; then `--choices` for choice menus. Other textforce.lua vars: ENTRYGO,
        EG_ID, STARTPATCH (game 1 docstring).
    python -X utf8 tools/textforce.py left [--build ..] [--root ..] [--also ..]
        rows still unshown per entry.
Then: python -X utf8 $SKILL/scripts/textcover.py work/qa <build>/strings.tsv --waive <build>/waive.tsv
"""
import argparse
import json
import re
import struct
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "debug"))
import evnames  # noqa: E402
import evscript  # noqa: E402
import extract  # noqa: E402
import gdata  # noqa: E402
import textcover_map  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TEXT = re.compile(r"^TEXT ([0-9A-Fa-f]+)", re.M)
BATTLE_TABLE = 0x8015060C  # {u16 key, u16 event id} .., key 0xFFFF ends it (game 1 0x80174A84)


def load(build):
    rows = json.loads((build / "rows.json").read_text(encoding="utf-8"))
    offs = {int(s): [(o, r) for o, r in v] for s, v in rows["rows"].items()}
    ends = {int(s): v for s, v in rows["ends"].items()}
    sigs = {int(s): v for s, v in json.loads((build / "sigs.json").read_text(encoding="utf-8")).items()}
    return offs, ends, set(rows["choice"]), sigs


def entry_info(exe):
    """({entry: first event id that loads it}, {entry: game-1 name}, {entry: id} for battle-table entries)"""
    ids, _ = textcover_map.id_entries(exe)
    first = {}
    for i, e in sorted(ids.items()):
        first.setdefault(e, i)
    names = {e: n for e, n, _ in evnames.table() if n}
    bt = {}
    o = BATTLE_TABLE - 0x80010000 + 0x800
    while True:
        key, eid = struct.unpack_from("<HH", exe, o)
        if key == 0xFFFF:
            break
        if eid in ids:
            bt[ids[eid]] = first[ids[eid]]
        o += 4
    return first, names, bt


SEN = re.compile(r"T(\d\d)SEN")
BHERO = re.compile(r"T(\d\d)\d\d")
SS = re.compile(r"SS(\d\d)\d+")


def how_to_run(ent, names, bt, hero=None):
    """(warp.py args, run dir name)"""
    nm = names.get(ent, "")
    e = f"e{ent}"
    if hero:
        return ["--event", f"{e}:{hero}", "--name", f"ev_{e}_h{hero}"], f"ev_{e}_h{hero}"
    m = SEN.fullmatch(nm)
    if m:
        h = int(m[1])
        swap = []
        if h == 1:  # game 1: a hero-1 battle loads no SEN file: load T01SEN as T03SEN in a hero-3 one
            h, swap = 3, ["--var", f"SWAP='3={e}'"]
        return ["--battle", "T0101", "--name", "bt_" + e, "--var", f"HERO={h}", "--var", f"FORCE_ID={h}",
                *swap], "bt_" + e
    if nm.startswith("TM"):  # in the battle table, but heroes talking, no fight
        return ["--event", e, "--name", "ev_" + e], "ev_" + e
    if ent in bt:
        m = BHERO.match(nm)
        hv = ["--var", f"HERO={int(m[1])}"] if m and 1 <= int(m[1]) <= 12 else []
        return ["--battle", e, "--name", "bt_" + e, "--var", f"FORCE_ID={bt[ent]}", *hv], "bt_" + e
    m = SS.fullmatch(nm)
    if m and 1 <= int(m[1]) <= 12:
        return ["--event", f"{e}:{int(m[1])}", "--name", "ev_" + e], "ev_" + e
    return ["--event", e, "--name", "ev_" + e], "ev_" + e


def shown(roots):
    out = set()
    for root in roots:
        for log in Path(root).rglob("log.txt"):
            out.update(int(a, 16) for a in TEXT.findall(log.read_text(encoding="utf-8", errors="replace")))
    return out


def wanted(offs, loaded, seen, skip=()):
    out = {}
    for ent, v in offs.items():
        if ent not in loaded:
            continue
        miss = [rid for o, rid in v if rid and rid not in skip and (ent << 16 | o) not in seen]
        if miss:
            out[ent] = miss
    return out


def signatures():
    """{entry: 'pos:value ..'} code words (file halfword index: value) at pc 0, 1 and the first ops after the
    variable area: textforce.lua patches a file only once these are in the buffer (not the last file's data)."""
    out = {}
    for ent, sec, cnt, kd, data in gdata.entries(ROOT / "work/disc/tree"):
        if kd != "script":
            continue
        try:
            sc = evscript.Script(data)
        except Exception:
            continue
        base = sc.code_off // 2
        pcs = [0, 1] + list(range(sc.start, min(sc.start + 6, len(sc.code))))
        out[ent] = " ".join(f"{base + p}:{sc.code[p]}" for p in pcs)
    return out


def cmd_freeze(a):
    build = Path(a.build)
    ends = {}
    _, offs = textcover_map.row_table(ends)
    choice = []  # choice menus (｛..｝ items)
    for p in sorted((ROOT / "script/events").glob("*.tsv")):
        choice += [r["id"] for r in extract.read_tsv(p) if r["en"] and "｛" in r["jp"]]
    (build / "rows.json").write_text(json.dumps({"rows": offs, "ends": ends, "choice": choice}), encoding="utf-8")
    (build / "sigs.json").write_text(json.dumps(signatures()), encoding="utf-8")
    print(f"frozen into {build}: {len(offs)} files, {len(choice)} choice rows")


def cmd_run(a):
    build, root = Path(a.build).resolve(), Path(a.root).resolve()
    offs, ends, choice, sigs = load(build)
    exe = (ROOT / "work/disc/tree/PSX.EXE").read_bytes()
    first, names, bt = entry_info(exe)
    roots = [root] + [Path(x).resolve() for x in a.also or ()]
    seen = shown(roots)
    want = wanted(offs, first, seen, () if a.choices else choice)
    extra = list(a.var or [])
    if a.choices:
        extra.append("FORCECHOICE=1")
    chmiss = set(choice) - {rid for e, v in offs.items() for o, rid in v if rid in choice and (e << 16 | o) in seen}
    if a.only:
        keep = {int(x.lstrip("e")) for x in a.only.split(",")}
        want = {e: v for e, v in want.items() if e in keep}
    if a.rows:
        ids = set(a.rows.split(","))
        want = {e: [r for r in v if r in ids] for e, v in want.items()}
        want = {e: v for e, v in want.items() if v}
    n = a.pass_no or 1
    while not a.pass_no and (root / f"p{n}").exists():
        n += 1
    out = root / f"p{n}"
    out.mkdir(parents=True, exist_ok=True)

    def finished(ent):
        p = out / how_to_run(ent, names, bt, a.hero)[1] / "emu.txt"
        return p.exists() and any(x.startswith("exit") for x in p.read_text(errors="replace").splitlines())

    want = {e: v for e, v in want.items() if not finished(e)}
    cue = str(build / "fd3_en.cue").replace("\\", "/")
    print(f"pass {n}: {len(want)} files, {sum(map(len, want.values()))} rows unshown", flush=True)

    def run(ent):
        miss = set(want[ent])
        v = offs[ent]
        cells = []
        for k, (o, rid) in enumerate(v):
            e = v[k + 1][0] if k + 1 < len(v) else ends[ent]
            cells.append(f"{o // 2},{e // 2},{1 if rid in miss else 2 if rid in chmiss else 0}")
        how, dname = how_to_run(ent, names, bt, a.hero)
        cmd = [sys.executable, "-X", "utf8", str(ROOT / "tools/debug/warp.py"), *how, "--cue", cue,
               "--root", str(out), "--frames", str(min(a.frames + 400 * len(miss), 200000)), "-j", "1",
               "--shot-every", str(a.shot_every), "--timeout", "3600", "--var", f"MASH_EVERY={a.mash}",
               "--lua", str(ROOT / "tools/lua/textforce.lua"), "--var", f"TARGETS='{' '.join(cells)}'"]
        if ent in sigs:
            cmd += ["--var", f"SIG='{sigs[ent]}'"]
        for x in extra:
            cmd += ["--var", x]
        if a.keypatch:
            cmd += ["--var", "KEYPATCH=1"]
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
        d = out / dname
        textcover_map.convert([d], exe, offs, quiet=True)  # the frozen build's rows
        log = (d / "log.txt").read_text(encoding="utf-8", errors="replace") if (d / "log.txt").exists() else ""
        got = len(set(TEXT.findall(log)))
        print(f"e{ent}\t{names.get(ent, '')}\trc {r.returncode}\tforced {log.count('FORCE ') - log.count('FORCE rows')}"
              f"\tshown {log.count('SHOWN ')}/{len(miss)}\ttext {got}\tskip {log.count('SKIP ')}"
              f"\tdone {'FORCE done' in log}", flush=True)

    with ThreadPoolExecutor(a.j) as ex:
        list(ex.map(run, sorted(want)))
    left = wanted(offs, first, shown(roots), choice)
    print(f"pass {n} finished: {sum(map(len, left.values()))} rows unshown in {len(left)} files (choice menus not "
          f"counted)", flush=True)


def cmd_left(a):
    offs, _, choice, _ = load(Path(a.build))
    exe = (ROOT / "work/disc/tree/PSX.EXE").read_bytes()
    first, names, _ = entry_info(exe)
    seen = shown([Path(a.root)] + [Path(x) for x in a.also or ()])
    left = wanted(offs, first, seen)
    total = sum(len([1 for _, r in v if r]) for e, v in offs.items() if e in first)
    for e in sorted(left):
        print(f"e{e}\t{len(left[e])}\t{names.get(e, '')}")
    nch = sum(1 for v in left.values() for r in v if r in choice)
    print(f"{sum(map(len, left.values()))} of {total} loaded rows unshown in {len(left)} files ({nch} choice menus)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("freeze", "run", "left"):
        s = sub.add_parser(name)
        s.add_argument("--build", default=str(ROOT / "work/qa/cover_build"))
        s.add_argument("--root", default=str(ROOT / "work/qa/force"))
        s.add_argument("--also", action="append", help="other run roots whose logs count as shown (work/qa/cover)")
        if name == "run":
            s.add_argument("-j", type=int, default=2)
            s.add_argument("--frames", type=int, default=16000, help="base frames; +400 per unshown row (cap 200000)")
            s.add_argument("--mash", type=int, default=20, help="frames between circle presses (warp.lua MASH_EVERY)")
            s.add_argument("--only", help="comma-separated entries (e453,e747)")
            s.add_argument("--hero", type=int, help="run each file as an event for this current hero")
            s.add_argument("--rows", help="comma-separated row ids: force only these")
            s.add_argument("--shot-every", type=int, default=1500, help="frames between shots")
            s.add_argument("--var", action="append", help="extra textforce.lua variable, NAME=LUA")
            s.add_argument("--pass", dest="pass_no", type=int, help="resume pass N (default: start the next one)")
            s.add_argument("--keypatch", action="store_true", help="patch 0x90 keyed prints on load (KEYPATCH)")
            s.add_argument("--choices", action="store_true", help="force unshown choice-menu rows too (FORCECHOICE)")
    a = ap.parse_args()
    {"freeze": cmd_freeze, "run": cmd_run, "left": cmd_left}[a.cmd](a)


if __name__ == "__main__":
    main()
