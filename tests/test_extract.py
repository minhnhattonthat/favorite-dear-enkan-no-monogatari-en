"""Phase 4 gate: script/*.tsv against the original disc (work/disc/tree; skipped when absent).

- roundtrip: every row's `jp` re-encodes to the original bytes at its id's address (and at the OMK.EXE copy);
- coverage: every event script sweeps end to end (ops, messages, padding), every message halfword with a glyph is in
  exactly one row, the PSX.EXE text regions hold nothing but rows, codes-only strings, 0x0000 and EXE_DATA, and
  the FIN.EXE staff roll rebuilds from its lines;
- the TSVs on disk list exactly the rows tools/extract.py produces (a stale or hand-damaged jp column fails).
"""
import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import evscript  # noqa: E402
import extract  # noqa: E402
import gdata  # noqa: E402

TREE = ROOT / "work" / "disc" / "tree"
pytestmark = pytest.mark.skipif(not (TREE / "PSX.EXE").is_file(), reason="disc not unpacked to work/disc/tree")
SCRIPT = ROOT / "script"


@pytest.fixture(scope="module")
def exe():
    return (TREE / "PSX.EXE").read_bytes()


@pytest.fixture(scope="module")
def events():
    return extract.event_rows(TREE)


def test_script_entries():
    ents = [i for i, sec, cnt, kd, data in gdata.entries(TREE) if kd == "script"]
    assert len(ents) == 568
    secs = {i: sec for i, sec, cnt, kd, data in gdata.entries(TREE)}
    for alias, ent in extract.EVENT_ALIASES.items():
        assert secs[alias] == secs[ent]
    assert len(extract.script_entries(TREE)) == 568 - len(extract.EVENT_ALIASES)
    assert len({secs[i] for i, _ in extract.script_entries(TREE)}) == 566
    # OMK.EXE's own copy of the directory (docs/re/disc.md) lists the same entries, so the same rows serve it
    psx, omk = (TREE / "PSX.EXE").read_bytes(), (TREE / "OMK.EXE").read_bytes()
    assert gdata.directory(psx) == gdata.directory(omk, 0x16EA04)


def test_event_coverage(events):
    rows, scripts = events
    for ent, sc in scripts.items():
        pc = sc.start
        for kind, s, e in sc.items:  # contiguous from the first op to the last used halfword
            assert s == pc, (ent, kind, s)
            pc = e
        assert pc == sc.n
        assert sc.code[sc.n:] == (0,) * (len(sc.code) - sc.n)
        msgs = [(s, e) for kind, s, e in sc.items if kind == "msg"]
        segs = sc.segments
        assert [a for a, _ in segs if a in {s for s, _ in msgs}] == [s for s, _ in msgs]
        assert sum(b - a for a, b in segs) == sum(e - s for s, e in msgs)  # segments tile the messages
        ids = {r["id"] for r in rows[ent]}
        for a, b in segs:
            rid = f"e{ent}.{sc.byte(a):04X}"
            assert (rid in ids) == extract.has_text(sc.code[a:b]), rid


def test_event_tsv_roundtrip(events):
    rows, scripts = events
    table = extract.event_table()
    on_disk = sorted((SCRIPT / "events").glob("*.tsv"))
    assert {int(p.stem[1:]) for p in on_disk} == {ent for ent, r in rows.items() if r}
    for p in on_disk:
        ent = int(p.stem[1:])
        sc = scripts[ent]
        ends = {sc.byte(a): sc.byte(b) for a, b in sc.segments}
        tsv = extract.read_tsv(p)
        assert [r["id"] for r in tsv] == [r["id"] for r in rows[ent]], p.name
        for r in tsv:
            off = int(r["id"].split(".")[1], 16)
            assert table.encode(r["jp"]) == sc.data[off:ends[off]], r["id"]


def test_exe_coverage_and_roundtrip(exe):
    omk = (TREE / "OMK.EXE").read_bytes()
    table = extract.exe_table()
    rows = extract.exe_rows(exe)
    tsv = extract.read_tsv(SCRIPT / "exe.tsv")
    assert [r["id"] for r in tsv] == [r["id"] for r in rows]
    spans = []
    for r in tsv:
        off = int(r["id"].split(".")[1], 16)
        raw = table.encode(r["jp"])
        assert exe[off:off + len(raw)] == raw, r["id"]
        o2 = off + extract.omk_delta(off)
        assert omk[o2:o2 + len(raw)] == raw, ("OMK", r["id"])
        spans.append((off, off + len(raw)))
    for lo, hi in extract.EXE_REGIONS:
        cov = bytearray(hi - lo)
        for s, e in extract.exe_strings(exe, lo, hi):  # rows plus codes-only strings ({end} alone, blanks)
            cov[s - lo:e - lo] = b"\1" * (e - s)
        for s, e in extract.EXE_DATA:
            if lo <= s < hi:
                cov[s - lo:e - lo] = b"\1" * (e - s)
        loose = [lo + i for i in range(0, hi - lo, 2) if not cov[i] and exe[lo + i:lo + i + 2] != b"\0\0"]
        assert not loose, [hex(x) for x in loose[:10]]
    allowed = extract.EXE_REGIONS + extract.EXE_GRIDS + [(o, o + 0x100) for o in extract.EXE_LOOSE]
    for s, e in spans:  # every string row is in a region, a grid or a listed loose string
        assert any(lo <= s and e <= hi for lo, hi in allowed), hex(s)


def test_exe_data_tables_are_pointers(exe):
    """EXE_DATA spans hold u32 words, mostly vaddrs into the EXE (records of pointers + small fields)"""
    for lo, hi in extract.EXE_DATA:
        words = struct.unpack_from("<%dI" % ((hi - lo) // 4), exe, lo)
        ptrs = sum(0x80010000 <= w < 0x80200000 for w in words)
        assert ptrs * 2 >= len(words), hex(lo)


def test_staff_roundtrip():
    fin = (TREE / "DATA/FIN.EXE").read_bytes()
    block = extract.fin_block(fin)
    lines = extract.staff_lines(block)
    assert len(lines) == 563 and lines[-1] == b""  # 562 CRLF-ended lines + the empty tail before 0xFF
    assert extract.FIN_NL.join(x.decode("cp932").encode("cp932") for x in lines) == block
    tsv = extract.read_tsv(SCRIPT / "staff.tsv")
    assert [r["id"] for r in tsv] == [r["id"] for r in extract.staff_rows(fin)]
    for r in tsv:
        assert r["jp"].encode("cp932") == lines[int(r["id"].split(".")[1])], r["id"]


def test_sjis_titles():
    tsv = extract.read_tsv(SCRIPT / "sjis.tsv")
    assert len(tsv) == len(extract.SJIS)
    for (name, off), r in zip(extract.SJIS, tsv):
        raw = r["jp"].encode("cp932")
        data = (TREE / name).read_bytes()
        assert data[off:off + len(raw) + 1] == raw + b"\0", r["id"]
        if name == "PSX.EXE":
            o2 = off + extract.omk_delta(off)
            assert (TREE / "OMK.EXE").read_bytes()[o2:o2 + len(raw) + 1] == raw + b"\0"


def test_tsv_columns():
    for p in SCRIPT.rglob("*.tsv"):
        extract.read_tsv(p)  # raises on a wrong column count or header


def test_known_lines(events):
    rows, _ = events
    # docs/re/text.md: GDATA entry 397's greeting
    assert any("よう、天使様！" in r["jp"] for r in rows[397])
    exe_jp = [r["jp"] for r in extract.read_tsv(SCRIPT / "exe.tsv")]
    assert "リメール海{n}{end}" in exe_jp and "ユリアナ{n}{end}" in exe_jp
    staff = extract.read_tsv(SCRIPT / "staff.tsv")
    assert any(r["jp"] == "シーヴァス・フォルクガング" for r in staff)
