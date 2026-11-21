"""Debug tool (phase 2): scene list shape, the event id/hash tables the warp patches, the save editor, the card helper.
Ported from game 1's tests/test_debug.py; facts re-found for this game (docs/re/debug.md)."""
import importlib.util
import struct
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXE = ROOT / "work/disc/tree/PSX.EXE"
G1EXE = ROOT.parent / "favorite-dear-en/work/disc/tree/PSX.EXE"
KINDS = {"title", "load", "option", "newgame", "week", "week2", "map", "event", "exec", "save", "battle"}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def scene_rows():
    rows = (ROOT / "tools/debug/scenes.tsv").read_text(encoding="utf-8").splitlines()
    assert rows[0].split("\t") == ["scene", "kind", "arg", "after", "frames", "card", "post", "proof", "note"]
    return [r.split("\t") for r in rows[1:] if r and not r.startswith("#")]


def test_scenes_tsv_shape():
    names = set()
    for c in scene_rows():
        assert len(c) == 9, c
        assert c[0] not in names, c[0]
        names.add(c[0])
        assert c[1] in KINDS, c
        assert (c[1] in {"event", "exec", "save", "battle"}) == bool(c[2]), c
        if c[1] == "event" and ":" in c[2]:  # NAME:HERO
            name, hero = c[2].split(":")
            assert name and 1 <= int(hero) <= 255, c
        if c[1] == "battle":
            assert 1 <= len(c[2]) <= 8 and ":" not in c[2], c
        if c[1] == "exec":
            prog, _, ending = c[2].partition(":")  # EPILOG:N = ending N (warp.lua ENDING)
            assert prog in {"OMK", "GOVER", "FD_BALL", "EPILOG", "FIN", "FD_MOV", "PS_MOV"}, c
            assert not ending or (prog == "EPILOG" and 0 <= int(ending) <= 0xFE), c
        if c[1] == "save":
            assert c[2] in {"1", "2", "3"} and c[5], c
        assert c[3] in {"hold", "mash"}, c
        assert int(c[4]) > 0
        assert not c[7] or int(c[7]) > 0, c


def test_name_hash():
    """The loader's hash (0x8001392C): "MYH16" -> 0x354E, the value in event id 32's slot (the warp's host)."""
    ev = load("evnames", ROOT / "tools/debug/evnames.py")
    assert ev.name_hash("MYH16") == 0x354E


@pytest.mark.skipif(not EXE.exists() or not G1EXE.exists(), reason="unpacked discs not present")
def test_event_tables():
    ev = load("evnames", ROOT / "tools/debug/evnames.py")
    d = EXE.read_bytes()
    assert ev.u16s(d, ev.IDTAB + 64, 1) == [0x354E]  # id 32 = MYH16 (warp.lua SLOT_HASH)
    assert struct.unpack_from("<H", d, 0x8015D6D4 - 0x80010000 + 0x800)[0] == ev.GBASE  # hash index + 395 = entry
    assert struct.unpack_from("<H", d, 0x8015D6D6 - 0x80010000 + 0x800)[0] == ev.NHASH
    rows = ev.table()
    named = {n: e for e, n, _ in rows if n}
    assert named["MYH16"] - ev.GBASE == ev.u16s(d, ev.HASHES, ev.NHASH).index(0x354E)
    gd = load("gdata", ROOT / "tools/gdata.py")
    kinds = {i: k for i, _, _, k, _ in gd.entries(ROOT / "work/disc/tree")}
    assert all(kinds[e] == "script" for e, _, _ in rows if e in kinds and kinds[e] != "empty")
    for c in scene_rows():
        if c[1] in {"event", "battle"}:
            name = c[2].split(":")[0]
            if name.startswith("e") and name[1:].isdigit():
                assert ev.GBASE <= int(name[1:]) < ev.GBASE + ev.NHASH, c
            else:
                assert name in named, f"scene {c[0]}: no event {name} in this game"


def test_save_editor_roundtrip():
    """save.py on a synthetic card: edits land in both copies, checksums verify, --bad-sum is caught."""
    mcd = load("mcd", ROOT / "tools/debug/mcd.py")
    save = load("save", ROOT / "tools/debug/save.py")
    card = bytearray(mcd.blank())
    o = 1 * mcd.FRAME
    card[o:o + 4] = (0x51).to_bytes(4, "little")
    card[o + 4:o + 8] = (16384).to_bytes(4, "little")
    card[o + 10:o + 30] = (save.PRODUCT + "00").encode().ljust(20, b"\0")
    card[o + 127] = mcd.xor(card[o:o + 127])
    f = bytearray(16384)
    f[0x204:0x210] = b"\xff" * 12
    save.fix(f)
    card[mcd.BLOCK:mcd.BLOCK + 16384] = f
    enc, dec = save.table()
    assert [n for n, _ in save.saves(card)] == [1]
    g = bytearray(f)
    save.set_name(g, "ラビエル", enc)
    assert save.name_of(g, dec) == "ラビエル"
    assert g[0x204:0x20C] == bytes.fromhex("b600a1007900b800") and g[0x19AE:0x19B6] == g[0x204:0x20C]
    save.fix(g)
    assert tuple(save.sums(g)) == tuple(int.from_bytes(g[0x200 + i:0x202 + i], "little") for i in (0, 2))
    save.fix(g, bad=True)
    assert save.sums(g)[0] != int.from_bytes(g[0x200:0x202], "little")


@pytest.mark.skipif(not (ROOT / "work/saves/week2.mcd").exists(), reason="game-written cards not present")
def test_game_written_cards():
    """Game-written week-1/week-2 saves: both sums as save.py computes them; week and AP where save.py reads them."""
    save = load("save", ROOT / "tools/debug/save.py")
    for name, week, ap in (("week1", 1, 100), ("week2", 2, 150)):
        card = (ROOT / f"work/saves/{name}.mcd").read_bytes()
        (_, at), = save.saves(card)
        f = card[at:at + 16384]
        assert tuple(save.sums(f)) == struct.unpack_from("<HH", f, 0x200), name
        assert save.get(f, "week") == week and f[0x215] == week and save.get(f, "ap") == ap, name


def test_blank_card():
    mcd = load("mcd", ROOT / "tools/debug/mcd.py")
    d = mcd.blank()
    assert len(d) == mcd.SIZE and d[:2] == b"MC"
    assert all(ok and state == 0xA0 for _, state, _, _, _, ok in mcd.entries(d))
