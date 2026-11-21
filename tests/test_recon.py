"""Phase 1 recon facts as tests (docs/re/): font table, EXE strings, GDATA directory, event-script grammar.
Skip when the unpacked disc (work/disc/tree) is absent."""
import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TREE = ROOT / "work/disc/tree"
sys.path.insert(0, str(ROOT / "tools"))

need_disc = pytest.mark.skipif(not (TREE / "PSX.EXE").is_file(), reason="disc not unpacked (dumpsxiso, docs/re/disc.md)")


def test_table_unique():
    from tbl import Table
    lines = [ln for ln in (ROOT / "tbl/jp.tbl").read_text(encoding="utf-8").splitlines()
             if ln and not ln.startswith("#") and "={" not in ln]
    vals = [ln.split("=", 1)[1] for ln in lines]
    assert len(vals) == len(set(vals)) > 1700
    Table.load(ROOT / "tbl/jp.tbl")


@need_disc
def test_exe_strings_decode():
    """a known menu string decodes and re-encodes byte-exact (PSX.EXE 0x141E82, memory-card error)"""
    from scantext import scan
    from tbl import Table
    t = Table.load(ROOT / "tbl/jp.tbl")
    exe = (TREE / "PSX.EXE").read_bytes()
    strs = dict(scan(exe, 3))
    s, e = 0x141E82, strs[0x141E82]
    text = t.decode(exe[s:e], 0)[0]
    assert text == "メモリーカードのアクセスに失敗しました。{end}"
    assert t.encode(text) == exe[s:e]


@need_disc
def test_gdata_directory_tiles_file():
    import gdata
    exe = (TREE / "PSX.EXE").read_bytes()
    size = (TREE / "GDATA.BIN").stat().st_size
    cov = bytearray((size + 2047) // 2048)
    for sec, cnt in gdata.directory(exe):
        assert sec + cnt <= len(cov)
        cov[sec:sec + cnt] = b"\1" * cnt
    assert cov.count(0) == 80  # the three known holes: 0x2D90-0x2DDC, 0x3690-0x3692, 0x39A1-0x39A3
    s3, c3 = gdata.directory((TREE / "SDATA.BIN").parent.joinpath("PSX.EXE").read_bytes(), gdata.SDIR, gdata.SCOUNT)[-1]
    assert s3 + c3 == ((TREE / "SDATA.BIN").stat().st_size + 2047) // 2048


@need_disc
def test_event_scripts_parse():
    """game 1's event grammar sweeps every script of this game end to end"""
    import evscript
    files = evscript.script_files(str(TREE))
    assert len(files) == 568
    nseg = sum(len(evscript.Script(data).segments) for _, _, data, _ in files)
    assert nseg == 13261
