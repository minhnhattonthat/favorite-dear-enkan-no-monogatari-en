"""release.py: build, gate and package a release (xdelta patch + README.txt in a zip).

    python -X utf8 tools/release.py [--version 1.0] [--force]

Stops at the first failure: build -> tests (tools/check.py) -> fitcheck -> smoke boot -> leftover Japanese
(tools/jpcheck.py) -> qa_gate.py check on every work/qa/**/manifest.tsv plus the named phase-8 manifests (GATES:
visual tour 3, stress saves, review, story pass) -> textcover.py -> no unticked line in docs/polish.md -> no
template placeholder in README.md -> debug tool off -> xdelta patch -> re-apply the patch to the original and compare
-> zip. Output: release/Favorite_Dear_Enkan_no_Monogatari_EN_v<version>.zip (patch + README.txt); the playable image
stays in build/. An existing version is never overwritten without --force. Publishing is the owner's call.
Ported from game 1 (../favorite-dear-en/tools/release.py).
"""
import argparse
import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from skill import SKILL  # noqa: E402

ORIG_BIN = ROOT / "rom" / "Favorite Dear - Enkan no Monogatari (Japan).bin"
BUILT_BIN = ROOT / "build" / "fd3_en.bin"
BUILT_CUE = ROOT / "build" / "fd3_en.cue"
XDELTA = ROOT / "tools" / "xdelta" / "xdelta3-3.1.0-x86_64.exe"
OUT = ROOT / "release"
SCRIPTS = Path(SKILL) / "scripts"
PY = [sys.executable, "-X", "utf8"]
QA = ROOT / "work" / "qa"
# (manifest, verdict dir) gates named other than manifest.tsv (phase 8 kept each tour round's files side by side)
GATES = [(QA / "p8" / "manifest3.tsv", QA / "p8" / "verdicts3"),
         (QA / "p8" / "manifest_stress.tsv", QA / "p8" / "verdicts_stress")]
# text coverage (phase 8): the frozen build's strings + waivers, and the run dirs whose log.txt files count
COVER_STRINGS = QA / "cover_build" / "strings.tsv"
COVER_WAIVE = QA / "cover_build" / "waive.tsv"
COVER_LOGS = [QA / "cover", QA / "force", QA / "force_pilot"]


def step(name, cmd, **kw):
    print(f"== {name}: {' '.join(map(str, cmd))}", flush=True)
    r = subprocess.run([str(c) for c in cmd], cwd=ROOT, **kw)
    if r.returncode:
        sys.exit(f"release stopped: {name} failed (exit {r.returncode})")


def fail(msg):
    sys.exit(f"release stopped: {msg}")


def hashes(path):
    crc, md5, sha1 = 0, hashlib.md5(), hashlib.sha1()
    with open(path, "rb") as f:
        while b := f.read(1 << 24):
            crc = zlib.crc32(b, crc)
            md5.update(b)
            sha1.update(b)
    return {"size": path.stat().st_size, "crc32": f"{crc:08X}", "md5": md5.hexdigest(), "sha1": sha1.hexdigest()}


def gates():
    found = [(m, m.parent / "verdicts") for m in sorted(QA.rglob("manifest.tsv"))]
    if not found:
        fail("no work/qa/**/manifest.tsv")
    for m, v in found + GATES:
        if not m.is_file():
            fail(f"missing gate manifest {m.relative_to(ROOT)}")
        step(f"qa_gate {m.relative_to(ROOT).as_posix()}", PY + [SCRIPTS / "qa_gate.py", "check", m, v])
    with tempfile.TemporaryDirectory() as tmp:  # one dir of every coverage run's log.txt (textcover takes one LOGDIR)
        n = 0
        for d in COVER_LOGS:
            for log in d.rglob("log.txt"):
                dst = Path(tmp) / f"{n:05d}"
                dst.mkdir()
                shutil.copyfile(log, dst / "log.txt")
                n += 1
        step(f"textcover ({n} logs)", PY + [SCRIPTS / "textcover.py", tmp, COVER_STRINGS, "--waive", COVER_WAIVE],
             stdout=subprocess.DEVNULL)
    open_lines = [x for x in (ROOT / "docs" / "polish.md").read_text(encoding="utf-8").splitlines()
                  if x.lstrip().startswith("- [ ]")]
    if open_lines:
        fail(f"docs/polish.md has {len(open_lines)} unticked line(s): {open_lines[0]}")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    ph = re.findall(r"<[A-Za-z][^<>\n]*>", readme)
    if ph:
        fail(f"README.md still has template placeholders: {ph[:5]}")
    print("== polish list, README: ok")


def debug_off():
    """The debug tool (tools/debug/warp.py + warp.lua, tools/lua/*) runs in the emulator: the build must not pull in
    anything from it, and build.py has no debug mode."""
    for f in ("build.py", "insert.py"):
        src = (ROOT / "tools" / f).read_text(encoding="utf-8")
        if re.search(r"tools[/\\]debug|warp\.lua|textforce|textlog|--debug", src):
            fail(f"tools/{f} refers to the debug tool")
    if any("debug" in p.name.lower() for p in (ROOT / "asm").glob("*")):
        fail("asm/ holds a debug patch")
    print("== debug tool: off (emulator-side only, not in the build)")


README_TXT = """Favorite Dear: Enkan no Monogatari - English fan translation v{version}
=======================================================================

Unofficial English patch for Favorite Dear: Enkan no Monogatari (PlayStation, NEC Interchannel, 2001).
Source, tools and bug reports: https://github.com/minhnhattonthat/favorite-dear-enkan-no-monogatari-en

What you need
-------------
Your own dump of the Japanese disc, one .bin + .cue (Redump: "Favorite Dear - Enkan no Monogatari (Japan)",
SLPS-03286):
  Favorite Dear - Enkan no Monogatari (Japan).bin
  size   {o[size]} bytes
  CRC32  {o[crc32]}
  MD5    {o[md5]}
  SHA-1  {o[sha1]}
Any other dump (another revision, an already-patched copy, .iso/.chd conversions) will not patch correctly.

How to patch
------------
1. Apply {patch} to "Favorite Dear - Enkan no Monogatari (Japan).bin" with xdelta3 or a front-end such as
   Delta Patcher (https://github.com/marco-calautti/DeltaPatcher) or the web patcher at
   https://www.marcrobledo.com/RomPatcher.js/ . Command line:
     xdelta3 -d -s "Favorite Dear - Enkan no Monogatari (Japan).bin" {patch} "Favorite Dear - Enkan no Monogatari (English).bin"
2. Copy the .cue, rename it to match, and change the FILE line inside it to the new .bin name.

Patched result: {b[size]} bytes, CRC32 {b[crc32]}, SHA-1 {b[sha1]}

Tested in PCSX-Redux with the SCPH-5500 BIOS. Start from a cold boot: emulator savestates made with
the Japanese game carry its old code and text.

Translation status
------------------
Dialogue and story, Juliana's arc, menus, items, system messages, battle text, endings, the Omake menu
and its Mini Event scenes, staff credits: English.
Graphics with text (menus, labels, tutorial charts, battle name plates): English. The title logo is kept
as released (FAVORITE DEAR with the Japanese subtitle; no official English logo exists).
Name entry: opens on an English letter page; the kana pages are still there.
Left in Japanese: the voice acting and songs; the memory-card titles shown by the console's
memory-card manager.

Known issues: see https://github.com/minhnhattonthat/favorite-dear-enkan-no-monogatari-en/issues

Changes
-------
v1.2 (a bug a player found in the Favorite Dear (1998) translation; same engine)
- Choice menus: in 12 menus (such as "Go along with him / See him off" and "Reiv / Regal") both
  choices were drawn on one line under a single cursor bar; each choice now has its own line.
v1.1 (the same bugs players found in the Favorite Dear (1998) translation; same engine)
- Hero visit, GIFT window: the item stat window's header is readable again ("Equip: No / OK /
  Using"; it showed broken words such as "Unus  le"), with labels matching the status screen.
- Hero status screen: the Equip box now shows the equipped item names (it was blank).
- Hero visit topic menu: one option that was a letter too long now fits on its line.
v1.0
- First release.

Credits
-------
Translation, hacking and tools: minhnhattonthat, with extensive AI assistance (Claude by Anthropic).
Built on the same team's Favorite Dear (1998) translation. Corrections are very welcome.
Bug reports (made on the Favorite Dear translation, fixed here too): ahassmoto-boop, Centurionzo12.
Thank you!

This is an unofficial fan work, not affiliated with NEC Interchannel. Favorite Dear: Enkan no Monogatari
is (c) NEC Interchannel. No game data is included; do not share patched disc images.
"""


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", default="1.0")
    ap.add_argument("--force", action="store_true", help="overwrite this version's files in release/")
    a = ap.parse_args(argv)
    name = f"Favorite_Dear_Enkan_no_Monogatari_EN_v{a.version}"
    patch, zpath = OUT / f"{name}.xdelta", OUT / f"{name}.zip"
    if (patch.exists() or zpath.exists()) and not a.force:
        fail(f"{zpath.name} or {patch.name} exists; pass --force to rebuild this version")
    if not XDELTA.is_file():
        fail(f"missing {XDELTA} (jmacd/xdelta-gpl v3.1.0, AGENTS.md)")

    step("build", PY + ["tools/build.py"])
    step("tests", PY + ["tools/check.py"])
    step("fitcheck", PY + ["tools/fitcheck.py"])
    step("smoke", PY + [SCRIPTS / "emu.py", BUILT_CUE.resolve(), "--out", "work/qa/smoke", "--route",
                        "tools/routes/boot.txt", "--smoke"])
    step("leftover Japanese", PY + ["tools/jpcheck.py"])
    gates()
    debug_off()

    OUT.mkdir(exist_ok=True)
    o, b = hashes(ORIG_BIN), hashes(BUILT_BIN)
    step("patch", [XDELTA, "-e", "-9", "-f", "-B", str(max(o["size"], b["size"])), "-s", ORIG_BIN, BUILT_BIN, patch])
    check = OUT / f"{name}.reapply.bin"
    step("re-apply", [XDELTA, "-d", "-f", "-s", ORIG_BIN, patch, check])  # as README.txt tells players
    got = hashes(check)
    check.unlink()
    if got["sha1"] != b["sha1"]:
        fail(f"re-applied patch gives {got['sha1']}, build is {b['sha1']}")
    print(f"== re-apply: ok ({b['sha1']})")

    readme = README_TXT.format(version=a.version, o=o, b=b, patch=patch.name)
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_STORED) as z:
        z.write(patch, patch.name)
        z.writestr("README.txt", readme.replace("\n", "\r\n"))
    psha = hashlib.sha1(patch.read_bytes()).hexdigest()
    print(f"release: {zpath.relative_to(ROOT)} ({zpath.stat().st_size} bytes); patch {patch.name} "
          f"{patch.stat().st_size} bytes sha1 {psha}; built image {b['sha1']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
