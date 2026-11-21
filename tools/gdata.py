"""gdata.py: the GDATA.BIN / SDATA.BIN directories in PSX.EXE and what each entry holds.

    python -X utf8 tools/gdata.py list   [--disc work/disc/tree]     one line per GDATA entry: index, sector, sectors, kind, text estimate
    python -X utf8 tools/gdata.py events [--disc work/disc/tree]     script entries only + totals
    python -X utf8 tools/gdata.py text N [--disc work/disc/tree]     decoded text runs of GDATA entry N
    python -X utf8 tools/gdata.py gaps   [--disc work/disc/tree]     GDATA sector ranges no entry covers

Directory format (verified 2026-11-21: entries tile GDATA.BIN and line up with TIM / LZSS / script headers): unlike
game 1's `(u32 sector, u32 byte size)` tables, this game has one array of `(u16 sector, u16 sector count)` at
PSX.EXE 0x170244 (965 entries, ends at 0x171158 where pointers start) for GDATA.BIN, and one at 0x1700E4 (88
entries) for SDATA.BIN. Sizes are whole sectors, so a file's exact length is not stored here.
Recon-grade text estimate: runs of >= 3 non-zero font codes (< NCODES) holding >= 2 kana (game 1's events.py rule).
"""
import argparse
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from tbl import Table  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
GDIR, GCOUNT = 0x170244, 965
SDIR, SCOUNT = 0x1700E4, 88
NCODES = 0x6F0


def directory(exe, off=GDIR, count=GCOUNT):
    return [struct.unpack_from("<HH", exe, off + 4 * i) for i in range(count)]


def kind(data):
    if len(data) < 8:
        return "empty"
    a, v, c = struct.unpack_from("<HHH", data)
    if a == 6 and 6 < v < 0x400 and v < c < len(data):  # 4 scripts have a code offset > 0x2000 (big data areas)
        return "script"
    if data[:4] == b"\x10\0\0\0":
        return "tim"
    if not any(data[:64]):
        return "zero"
    return "other"


def text_runs(data):
    """[(byte offset, [codes])] of plausible text runs."""
    n = len(data) // 2
    hw = struct.unpack_from("<%dH" % n, data)
    runs, cur, start = [], [], 0
    for i, v in enumerate(hw + (0xFFFF,)):
        if 0 < v < NCODES and i < n:
            if not cur:
                start = i
            cur.append(v)
            continue
        if len(cur) >= 3 and sum(0x23 <= c <= 0xBD for c in cur) >= 2:
            runs.append((start * 2, cur))
        cur = []
    return runs


def entries(disc):
    exe = (Path(disc) / "PSX.EXE").read_bytes()
    g = (Path(disc) / "GDATA.BIN").read_bytes()
    out = []
    for i, (sec, cnt) in enumerate(directory(exe)):
        data = g[sec * 2048:(sec + cnt) * 2048]
        out.append((i, sec, cnt, kind(data), data))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["list", "events", "text", "gaps"])
    ap.add_argument("n", nargs="?", type=int)
    ap.add_argument("--disc", default=str(ROOT / "work/disc/tree"))
    a = ap.parse_args()
    es = entries(a.disc)
    if a.cmd in ("list", "events"):
        tot, k = 0, 0
        for i, sec, cnt, kd, data in es:
            if a.cmd == "events" and kd != "script":
                continue
            chars = sum(len(c) for _, c in text_runs(data)) if kd == "script" else 0
            tot += chars
            k += 1
            print(f"{i}\t{sec:#06x}\t{cnt:#x}\t{kd}\t{chars}")
        print(f"# {k} entries, ~{tot} text characters in scripts")
    elif a.cmd == "text":
        t = Table.load(ROOT / "tbl/jp.tbl")
        for off, codes in text_runs(es[a.n][4]):
            b = struct.pack("<%dH" % len(codes), *codes)
            print(f"{off:05X}\t{t.decode(b, 0, len(b))[0]}")
    else:
        size = (Path(a.disc) / "GDATA.BIN").stat().st_size
        cov = bytearray((size + 2047) // 2048)
        for _, sec, cnt, _, _ in es:
            cov[sec:sec + cnt] = b"\1" * cnt
        s = None
        for i, v in enumerate(list(cov) + [1]):
            if not v and s is None:
                s = i
            elif v and s is not None:
                print(f"{s:#06x}-{i:#06x} ({i - s} sectors)")
                s = None


if __name__ == "__main__":
    main()
