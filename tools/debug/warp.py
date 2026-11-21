"""warp.py: boot the disc cold and land on a scene from tools/debug/scenes.tsv (no save, no savestate).

    python -X utf8 tools/debug/warp.py SCENE [SCENE..] [--cue build/fd3_en.cue] [-j 3] [--state]
    python -X utf8 tools/debug/warp.py --all [-j 3] [--state]      regenerate every scene (shots + optional states)
    python -X utf8 tools/debug/warp.py --event NAME                any event script: a game-1 name (MYH16, SEND01..)
                                                                   or eNNN, its GDATA entry (395-964; `gdata.py events`)
    python -X utf8 tools/debug/warp.py --battle NAME               a battle by its event (T0101, T0702..)
    python -X utf8 tools/debug/warp.py --list

Each run writes work/qa/warp/<scene>/ (shots every 150 frames, sheet.png, log.txt) and, with --state,
work/states/<scene>.sstate (60 frames after arrival). Exit 1 if any scene was not reached ("WARP OK" missing in the
log) or, for scenes with AFTER=mash, the screen never changed after arrival (a stuck script). Results go to
work/qa/warp/results.tsv. The Lua side is tools/debug/warp.lua; how it works: docs/re/debug.md."""
import argparse
import csv
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, "tools"))
from skill import SKILL  # noqa: E402

sys.path.insert(0, os.path.join(SKILL, "scripts"))
import sheet  # noqa: E402

ORIG_CUE = os.path.join(REPO, "rom", "Favorite Dear - Enkan no Monogatari (Japan).cue")
SCENES = os.path.join(HERE, "scenes.tsv")
COLS = ["scene", "kind", "arg", "after", "frames", "card", "post", "proof", "note"]
# arg: the event name or eNNN (kind event; NAME:HERO also sets the current hero, e.g. SS0204:2 for a battle),
# program name (kind exec: OMK GOVER FD_BALL EPILOG FIN FD_MOV PS_MOV) or save number on the card (kind save), or a
# battle's own event (kind battle: T0101, T0206, TM02ALL.., any id in the battle table at 0x8015060C; started from
# SS0204's battle with the stage entry rewritten, docs/re/debug.md). card: a memory card image (repo-relative)
# given to the emulator as a copy.
# post: presses after arrival (route steps joined by ';'), shot as post.png. proof: frames from arrival to
# arrived.png (default 30).
ARG_VAR = {"event": "EVENT", "exec": "EXE", "save": "SAVE"}
NUMERIC = {"SAVE"}
EXTRA = []  # extra emu.py args from --lua / --debugger / --var (hooks riding along a warp)
SHOT_EVERY = 150  # --shot-every
ROOT = os.path.join(REPO, "work", "qa", "warp")  # --root (a tour: work/qa/tour, its Japanese twin work/qa/tour_jp)


def load_scenes():
    with open(SCENES, encoding="utf-8", newline="") as f:
        rows = [r for r in csv.reader(f, delimiter="\t") if r and not r[0].startswith("#")]
    head, rows = rows[0], rows[1:]
    assert head == COLS, f"scenes.tsv header {head} != {COLS}"
    out = {}
    for r in rows:
        assert len(r) == len(COLS), f"scenes.tsv row has {len(r)} columns, want {len(COLS)}: {r}"
        d = dict(zip(COLS, r))
        assert d["scene"] not in out, f"duplicate scene {d['scene']}"
        out[d["scene"]] = d
    return out


def frame_of(log, tag):
    for line in log.splitlines():
        if line.startswith(tag):
            return int(line.rsplit(" f", 1)[1])
    return None


def run(sc, cue, state, timeout):
    out = os.path.join(ROOT, sc["scene"])
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        if f.endswith(".png"):
            os.remove(os.path.join(out, f))
    lua = [f"KIND='{sc['kind']}'", f"AFTER='{sc['after'] or 'mash'}'"]
    if sc["kind"] == "battle":  # a battle's own event (T0101..): host SS0204 for hero 2 starts it (warp.lua BATTLE)
        lua = ["KIND='event'", "EVENT='SS0204'", "HERO=2", f"BATTLE='{sc['arg']}'", lua[1]]
    elif sc["arg"]:
        var = ARG_VAR[sc["kind"]]
        arg = sc["arg"]
        if sc["kind"] == "event" and ":" in arg:  # NAME:HERO runs the event for that hero (warp.lua HERO)
            arg, hero = arg.split(":")
            lua.append(f"HERO={int(hero)}")
        if sc["kind"] == "exec" and ":" in arg:  # EPILOG:N plays ending N (warp.lua ENDING, docs/re/debug.md)
            arg, ending = arg.split(":")
            lua.append(f"ENDING={int(ending)}")
        lua.append(f"{var}={int(arg)}" if var in NUMERIC else f"{var}='{arg}'")
    if sc.get("post"):
        lua.append(f"POST='{sc['post']}'")
    if sc.get("proof"):
        lua.append(f"PROOF={int(sc['proof'])}")
    card = []
    if sc.get("card"):
        src = os.path.join(REPO, sc["card"])
        assert os.path.exists(src), f"{sc['scene']}: card {src} missing (tools/debug/save.py, docs/re/debug.md)"
        dst = os.path.join(out, "card.mcd")
        shutil.copyfile(src, dst)
        card = ["--sav", dst]
    if state:
        p = os.path.join(REPO, "work", "states", sc["scene"] + ".sstate").replace("\\", "/")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        lua.append(f"STATE='{p}'")
    cmd = [sys.executable, "-X", "utf8", os.path.join(SKILL, "scripts", "emu.py"), os.path.abspath(cue),
           "--out", out, "--script", os.path.join(HERE, "warp.lua"), "--frames", sc["frames"] or "16000",
           "--shot-every", str(SHOT_EVERY), "--timeout", str(timeout)] + card
    for v in lua:
        cmd += ["--var", v]
    cmd += EXTRA
    if sc["kind"] == "exec" and sc["arg"].startswith("FIN") and "--debugger" not in cmd:
        # FIN.EXE (staff roll) crashes PCSX-Redux's dynarec ~1800 frames in (heap corruption, exit 0xC0000374);
        # the interpreter plays it through (docs/re/debug.md)
        cmd.append("--debugger")
    with open(os.path.join(out, "emu.txt"), "w", encoding="utf-8") as fo:
        rc = subprocess.call(cmd, stdout=fo, stderr=subprocess.STDOUT)
    logp = os.path.join(out, "log.txt")
    log = open(logp, encoding="utf-8", errors="replace").read() if os.path.exists(logp) else ""
    ok_at = frame_of(log, "WARP OK")
    verdict, distinct = "ok", 0
    if rc != 0:
        verdict = f"emu exit {rc}"
    elif ok_at is None:
        verdict = "not reached"
    else:
        shots = sorted(f for f in os.listdir(out) if f[0] == "f" and f[1:7].isdigit() and f.endswith(".png")
                       and int(f[1:7]) >= ok_at + 150)
        imgs = [sheet.read_png(os.path.join(out, f)) for f in shots]
        seen = []
        for im in imgs:
            if not any(sheet.diff(im, s) < 0.002 for s in seen):
                seen.append(im)
        distinct = len(seen)
        if (sc["after"] or "mash") == "mash" and distinct < 2:
            verdict = "stuck"
        proof = os.path.join(out, "arrived.png")
        if not os.path.exists(proof):
            verdict = "no arrived.png"
        elif sheet.is_blank(sheet.read_png(proof)):
            verdict = "blank"
        sheet.make(out, lo=max(0, ok_at - 300), limit=16, changed=0.002)
    return sc["scene"], verdict, ok_at, distinct


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scenes", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--event", action="append", default=[], help="ad-hoc event name (no scenes.tsv row needed)")
    ap.add_argument("--battle", action="append", default=[],
                    help="ad-hoc battle by its event name (T0101, T0206, TM02ALL..; the 0x80174A84 table)")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--cue", default=ORIG_CUE)
    ap.add_argument("--state", action="store_true", help="also save work/states/<scene>.sstate")
    ap.add_argument("-j", type=int, default=3)
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--lua", action="append", default=[], help="extra Lua hook appended after warp.lua (repeatable)")
    ap.add_argument("--var", action="append", default=[], help="extra NAME=LUA global (repeatable)")
    ap.add_argument("--debugger", action="store_true", help="interpreter mode (needed for L.on_exec hooks)")
    ap.add_argument("--shot-every", type=int, default=150, help="frames between shots (default 150)")
    ap.add_argument("--root", default=None, help="output directory (default work/qa/warp)")
    ap.add_argument("--name", default=None, help="run folder name for a single --event/--battle run")
    ap.add_argument("--frames", type=int, default=None,
                    help="run length for --event/--battle runs (default 16500/17500; text coverage sweeps use more), "
                         "or overriding a named scene's (e.g. omake_mini read through with --var 'AFTER=\"mash\"')")
    a = ap.parse_args()
    global SHOT_EVERY, ROOT
    SHOT_EVERY = a.shot_every
    if a.root:
        ROOT = os.path.abspath(a.root)
    for f in a.lua:
        EXTRA.extend(["--script", os.path.abspath(f)])
    for v in a.var:
        EXTRA.extend(["--var", v])
    if a.debugger:
        EXTRA.append("--debugger")
    table = load_scenes()
    if a.list:
        for s in table.values():
            print(f"{s['scene']:<16} {s['kind']:<8} {s['arg']:<9} {s['note']}")
        return 0
    todo = list(table.values()) if a.all else []
    for name in a.scenes:
        if name not in table:
            sys.exit(f"unknown scene {name}; --list shows them")
        todo.append(dict(table[name], frames=str(a.frames)) if a.frames else table[name])
    for ev in a.event:
        todo.append({"scene": "ev_" + ev.replace(":", "_"),"kind": "event", "arg": ev, "after": "mash", "frames": str(a.frames or 16500),
                     "card": "", "post": "", "proof": "", "note": ""})
    for ev in a.battle:
        todo.append({"scene": "bt_" + ev, "kind": "battle", "arg": ev, "after": "mash", "frames": str(a.frames or 17500),
                     "card": "", "post": "", "proof": "1200", "note": ""})
    if not todo:
        ap.error("name a scene, --event NAME, --battle NAME or --all")
    if a.name:
        if len(todo) != 1:
            ap.error("--name takes exactly one run")
        todo[0]["scene"] = a.name
    with ThreadPoolExecutor(max_workers=a.j) as ex:
        res = list(ex.map(lambda s: run(s, a.cue, a.state, a.timeout), todo))
    os.makedirs(ROOT, exist_ok=True)
    with open(os.path.join(ROOT, "results.tsv"), "a", encoding="utf-8") as f:
        for r in res:
            f.write("\t".join(str(x) for x in r) + "\n")
    bad = 0
    for name, verdict, at, distinct in res:
        print(f"{name:<16} {verdict:<12} arrived f{at}  distinct shots after arrival: {distinct}")
        bad += verdict != "ok"
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
