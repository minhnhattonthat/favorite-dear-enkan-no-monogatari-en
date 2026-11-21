"""build.py: rebuild the disc from the unpacked tree, with this project's edits.

    python -X utf8 tools/build.py              -> build/fd3_en.bin/.cue
    python -X utf8 tools/build.py --identity   -> no edits; exit 1 unless the .bin is byte-identical to rom/

Steps: check the dump against rom.sha1; unpack it with dumpsxiso into work/disc/ if that is missing; collect the
edited files (`edits()`: tools/insert.py; `--mode marker|ruler|torture` for the phase-5 builds) into build/files_<name>/; write build/<name>.xml, a copy of
work/disc/layout.xml with absolute paths and a `source=` on every edited file; run mkpsxiso on it.
work/disc/tree is never written to, so the identity build stays an identity build. Adapted from game 1's
tools/build.py (../favorite-dear-en)."""
import argparse
import hashlib
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_rom  # noqa: E402

ROM_CUE = ROOT / "rom" / "Favorite Dear - Enkan no Monogatari (Japan).cue"
ROM_BIN = ROOT / "rom" / "Favorite Dear - Enkan no Monogatari (Japan).bin"
DISC = ROOT / "work" / "disc"
MKPSXISO_DIR = ROOT / "tools" / "mkpsxiso" / "mkpsxiso-2.30-win64"
BUILD = ROOT / "build"
NAME = "fd3_en"


def exe(name):
    path = MKPSXISO_DIR / (name + (".exe" if sys.platform == "win32" else ""))
    if not path.is_file():
        sys.exit(f"missing {path}: get mkpsxiso v2.30 from github.com/Lameguy64/mkpsxiso/releases (AGENTS.md)")
    return path


def unpack():
    """work/disc/tree + layout.xml from the original disc (once)."""
    if (DISC / "layout.xml").is_file() and (DISC / "tree" / "SYSTEM.CNF").is_file():
        return
    DISC.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(exe("dumpsxiso")), "-x", "tree", "-s", "layout.xml", str(ROM_BIN)], cwd=DISC, check=True)


def edits(mode="en", qa=None):
    """{disc path ('PSX.EXE'): new bytes} from tools/insert.py."""
    import insert
    return insert.edits(mode, qa=qa)


def file_paths(directory, prefix=""):
    """(disc path, <file> element) for every file under a <directory_tree>/<dir> element."""
    for el in directory:
        if el.tag == "file":
            yield prefix + el.get("name"), el
        elif el.tag == "dir":
            yield from file_paths(el, prefix + el.get("name") + "/")


def write_layout(changed, out):
    """build/<name>.xml: the unpacked layout with absolute paths; edited files point at build/files_<name>/."""
    tree = ET.parse(DISC / "layout.xml")
    proj = tree.getroot()
    proj.set("image_name", str(out.with_suffix(".bin")))
    proj.set("cue_sheet", str(out.with_suffix(".cue")))
    track = proj.find("track")
    lic = track.find("license")
    if lic is not None:
        lic.set("file", str((DISC / lic.get("file")).resolve()))
    dtree = track.find("directory_tree")
    dtree.set("source", str((DISC / dtree.get("source")).resolve()))
    known = dict(file_paths(dtree))
    for path, src in changed.items():
        if path not in known:
            sys.exit(f"edit for {path}: not a file on the disc")
        known[path].set("source", str(src))
    layout = out.with_suffix(".xml")
    tree.write(layout, encoding="utf-8", xml_declaration=True)
    return layout


def sha1(path):
    with open(path, "rb") as f:
        return hashlib.file_digest(f, "sha1").hexdigest()


def build(identity=False, changes=None, name=None, mode="en", qa=None):
    """Build the disc; `changes`/`name` replace edits() and the output name (tests); `qa` = {EXE row id: text}
    single-string overrides -> build/fd3_en_<mode>_qa.*"""
    check_rom.check()
    unpack()
    BUILD.mkdir(exist_ok=True)
    name = name or (NAME + "_identity" if identity else NAME if mode == "en" else f"{NAME}_{mode}")
    if qa and not identity:
        name += "_qa"
    files = BUILD / ("files_" + name)
    if files.exists():
        shutil.rmtree(files)
    changed = {}
    if changes is None:
        changes = {} if identity else edits(mode, qa)
    for path, data in changes.items():
        dst = files / path
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(data)
        changed[path] = dst.resolve()
    out = BUILD / name
    layout = write_layout(changed, out.resolve())
    r = subprocess.run([str(exe("mkpsxiso")), "-y", "-q", str(layout)], cwd=BUILD, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"mkpsxiso failed ({r.returncode}):\n{r.stdout}\n{r.stderr}")
    binf = out.with_suffix(".bin")
    digest = sha1(binf)
    print(f"{binf.relative_to(ROOT)}: {binf.stat().st_size} bytes, sha1 {digest}, {len(changed)} files edited")
    if identity:
        want = sha1(ROM_BIN)
        if digest != want:
            sys.exit(f"identity build differs from rom/ (sha1 {want})")
        print("identity: byte-identical to rom/")
    return binf


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--identity", action="store_true", help="build with no edits and require a byte-identical .bin")
    ap.add_argument("--mode", choices=["en", "marker", "ruler", "torture"], default="en",
                    help="insert.py mode: marker/ruler/torture -> build/fd3_en_<mode>.* (phase 5 width gate)")
    ap.add_argument("--qa", action="append", default=[], metavar="ID=TEXT",
                    help="EXE string override (repeatable), e.g. 'PSX.138F10=1234567890{end}'; builds *_qa")
    a = ap.parse_args()
    qa = dict(s.split("=", 1) for s in a.qa)
    build(a.identity, mode=a.mode, qa=qa)
