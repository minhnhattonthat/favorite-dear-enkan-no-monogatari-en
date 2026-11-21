"""The English build's ROM-level gates (phase 7), on edits built fresh into memory (never a stale build/ dir):
- every changed byte is inside fitcheck's allowed ranges, and every changed byte has a logged write behind it, no
  write overlaps another or expects bytes the original doesn't hold (romdiff.check with insert's write log);
- the six u16 GDATA directories agree, every entry keeps its kind, no entry runs past GDATA.BIN or overlaps another
  entry's sectors (aliases share whole entries), moved scripts land on a script header;
- no branch or jump in the original EXEs lands inside a hook span other than its first word."""
import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fitcheck  # noqa: E402
import gdata  # noqa: E402
import insert  # noqa: E402
import romdiff  # noqa: E402

TREE = insert.TREE
pytestmark = pytest.mark.skipif(not (TREE / "PSX.EXE").is_file() or not insert.ARMIPS.is_file(),
                                reason="needs work/disc/tree and armips")


@pytest.fixture(scope="module")
def built():
    writes = {}
    out = insert.edits("en", writes=writes)
    return out, writes


def orig(name):
    return (TREE / name).read_bytes()


def test_writes_inside_allowed_ranges(built):
    out, writes = built
    orig_psx = orig("PSX.EXE")
    patterns = fitcheck.moved(orig_psx, out["PSX.EXE"])
    for name, new in out.items():
        o = orig(name)
        rng = fitcheck.allowed(name, o, orig_psx, patterns)
        assert rng is not None, f"{name}: fitcheck has no rule"
        errs, _ = romdiff.check(o, new, rng, [])
        assert not errs, f"{name}: outside allowed ranges: {errs[:5]}"


def test_every_change_has_a_logged_write(built):
    out, writes = built
    for name, new in out.items():
        assert writes.get(name), f"{name}: changed with no write logged"
        errs, _ = romdiff.check(orig(name), new, [], writes[name])
        assert not errs, f"{name}: {errs[:5]}"


def test_directories(built):
    out, _ = built
    exes = {n: out.get(n, orig(n)) for n in insert.EXE_DIRS}
    dirs = {n: gdata.directory(e, insert.EXE_DIRS[n]) for n, e in exes.items()}
    first = dirs["PSX.EXE"]
    for n, d in dirs.items():
        assert d == first, f"{n}: GDATA directory differs from PSX.EXE's"
    gd_old, gd_new = orig("GDATA.BIN"), out.get("GDATA.BIN", orig("GDATA.BIN"))
    old_dir = gdata.directory(orig("PSX.EXE"))
    spans = {}
    for i, ((sec, cnt), (osec, ocnt)) in enumerate(zip(first, old_dir)):
        lo, hi = sec * insert.SECTOR, (sec + cnt) * insert.SECTOR
        assert hi <= len(gd_new) or cnt == 0, f"entry {i} runs past GDATA.BIN"
        k_old = gdata.kind(gd_old[osec * insert.SECTOR:(osec + ocnt) * insert.SECTOR])
        k_new = gdata.kind(gd_new[lo:hi])
        assert k_new == k_old, f"entry {i}: kind {k_old} -> {k_new}"
        if (sec, cnt) != (osec, ocnt):
            assert k_new == "script", f"entry {i} moved onto a non-script"
        if cnt:
            spans.setdefault((sec, cnt), i)
    ordered = sorted(spans)
    for (s1, c1), (s2, c2) in zip(ordered, ordered[1:]):
        assert s1 + c1 <= s2, f"entries {spans[(s1, c1)]} and {spans[(s2, c2)]} overlap"


def branch_target(word, va):
    op = word >> 26
    if op in (2, 3):  # j, jal
        return ((va + 4) & 0xF0000000) | ((word & 0x03FFFFFF) << 2)
    if op in (1, 4, 5, 6, 7):  # regimm, beq, bne, blez, bgtz
        imm = word & 0xFFFF
        return va + 4 + ((imm - 0x10000 if imm & 0x8000 else imm) << 2)
    return None


# Functions an asm file replaces whole, in place: their own old branches (sources inside) are dead code.
REPLACED = {"PSX.EXE": [(0x8001A680, 0x8001A840),  # asm/btname.inc
                        (0x8009BD04, 0x8009BE4C)]}  # asm/skill.inc (old small-font skill drawer)


def test_no_branch_into_a_hook(built):
    _, writes = built
    for name, log in writes.items():
        hooks = [(off & ~3, off + len(new)) for off, _, new, by in log if by.startswith("armips:")]
        if not hooks:
            continue
        o = orig(name)
        base = struct.unpack_from("<I", o, 0x18)[0]
        n = len(o) // 4 * 4
        bad = []
        for lo, hi in hooks:
            if lo >= n:
                continue  # appended to the file: no original code points there
            for p in range(max(0x800, lo - 0x1000), min(n, hi + 0x1000), 4):
                if any(a <= p - 0x800 + base < b for a, b in REPLACED.get(name, [])):
                    continue
                w = struct.unpack_from("<I", o, p)[0]
                t = branch_target(w, p - 0x800 + base)
                if t is not None and lo - 0x800 + base < t < hi - 0x800 + base and not (lo <= p < hi):
                    bad.append(f"{name}: 0x{p - 0x800 + base:08X} -> 0x{t:08X} inside hook 0x{lo:X}-0x{hi:X}")
        assert not bad, bad[:5]
