"""tests/test_lint.py: the phase 7 gates (tools/lint.py, the FIN credits hook, EXE repointing)."""
import struct
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import extract  # noqa: E402
import font_en  # noqa: E402
import insert  # noqa: E402
import lint  # noqa: E402

TREE = ROOT / "work" / "disc" / "tree"
need_disc = pytest.mark.skipif(not (TREE / "PSX.EXE").is_file(), reason="work/disc/tree missing")


def test_event_row_ok_with_continuation_page():
    jp = "{spk:0001}{n}あいう{n}{wait}{clear}{end}"
    en = "{spk:0001}{n}Hello.{n}{wait}{clear}{spk:0001}{n}More.{n}{wait}{clear}{end}"
    assert lint.event_row("x", jp, en) == []


def test_event_row_catches_lost_code_wide_line_and_tall_page():
    jp = "{spk:0001}{n}{name:0080}あ{n}{wait}{clear}{end}"
    assert any("control codes" in e for e in lint.event_row("x", jp, "{spk:0001}{n}Hi{n}{wait}{clear}{end}"))
    wide = "{spk:0001}{n}{name:0080}" + "x" * 50 + "{n}{wait}{clear}{end}"
    assert any("cells" in e for e in lint.event_row("x", jp, wide))
    tall = "{spk:0001}{n}{name:0080}a{n}b{n}c{n}d{n}{wait}{clear}{end}"
    assert any("text lines" in e for e in lint.event_row("x", jp, tall))


def test_event_row_counts_raw_glyph_as_one_cell():
    jp = "{f7:0080}　｛行きたい　　｝{n}{end}"
    en = "{f7:0080}[00][00][DA][05]Go to them[00][00][00][00][00][00][DB][05]{n}{end}"
    assert lint.event_row("x", jp, en) == []


def test_angel_menu_question_stays_one_short_line():
    jp = "{fb:3C80}{n}{spk:E783}{n}今、なにかしたい事はありますか？{n}{wait}{clear}{spk:0080}{n}さあ。{n}{wait}{clear}{end}"
    ok = "{fb:3C80}{n}{spk:E783}{n}Anything you'd like to do right now?{n}{wait}{clear}{spk:0080}{n}Who knows.{n}" \
         "{wait}{clear}{end}"
    assert lint.event_row("x", jp, ok) == []
    two = ok.replace("do right now?", "do{n}right now?")
    assert any("menu question" in e for e in lint.event_row("x", jp, two))
    wide = ok.replace("Anything", "Is there anything really")
    assert any("menu question" in e for e in lint.event_row("x", jp, wide))


def test_exe_slot_limits():
    assert lint.exe_row("PSX.135E38", "ベテル宮{n}{end}", "Bethel{n}{end}") == []
    assert lint.exe_row("PSX.135E38", "ベテル宮{n}{end}", "Bethel Palace{n}{end}")
    assert lint.exe_row("PSX.134D00", "バラの花束{n}{end}", "Bouquet of Red Roses{n}{end}")  # item_name range cap 16


def test_empty_en_needs_a_keep_list_entry():
    keep = {"PSX.18A93C"}
    assert lint.untranslated("e396.1558", "クッキー{n}{end}", "", "", keep)
    assert lint.untranslated("e396.1558", "クッキー{n}{end}", "", "g1:3498.0000 untranslated there (glyph soup in game 1)",
                             keep) == []
    assert lint.untranslated("e478.178C", "{fc}{n}{end}", "", "", keep) == []  # codes only
    assert lint.untranslated("PSX.18A93C", "フェイバリット", "", "", keep) == []
    assert lint.untranslated("PSX.141F44", "贈りますか？", "", "(glyph soup in game 1)", keep)  # rule is events-only
    assert all(rid and reason for rid, reason in (ln.split("\t")[:2] for ln in
               lint.KEEP.read_text(encoding="utf-8").splitlines()[1:]))


def test_list_slot_lines_measured_with_the_longest_entry():
    slots = lint.list_slots()
    assert slots[("e834", "0380")] >= 10  # "Fallen Angel Apollyon"
    long = "{f7:0180}the calamity that befell {name:0380}{n}{end}"
    assert lint.event_row("e834.1776", long, long, slots)
    assert lint.event_row("e834.1776", long, long, {}) == []  # the 12-letter default would have passed it


def test_glossary_avoid_spellings_caught_as_whole_words():
    pats = {a: rx for _, a, rx in lint.avoid_patterns()}
    assert "Rave" in pats and "Cain" in pats
    assert pats["Rave"].search("Rave's sword") and not pats["Rave"].search("Raven flew. Braver")
    assert pats["Cain"].search("Cain!") and not pats["Cain"].search("Caine")


def test_staff_row():
    assert lint.staff_row("FIN.005", "          Yuichiro Ogawa") == []
    assert lint.staff_row("FIN.005", " " * 20 + "Yuichiro Ogawa")
    assert lint.staff_row("FIN.005", "Ogawa~")


def test_fin_pairs_decode():
    """the hook's arithmetic (asm/fin.asm) turns each pair code back into its two letters"""
    text = "Kazuhiko Watanabe"
    codes = font_en.fin_pairs(text)
    n_chars = len(font_en.FIN_CHARSET)
    out = ""
    for lead, trail in zip(codes[::2], codes[1::2]):
        assert 0xE0 <= lead <= 0xFC and 0x40 <= trail <= 0xFC
        n = (lead - 0xE0) * 189 + (trail - 0x40)
        out += font_en.FIN_CHARSET[n // n_chars] + font_en.FIN_CHARSET[n % n_chars]
    assert out == text + " "
    assert len(font_en.fin_binary()) == 11 * n_chars


@need_disc
def test_roll_never_uses_the_glyphs_the_hook_overwrites():
    """asm/fin.asm sits over SJIS 0x8440-0x84BE (Cyrillic, box drawing): the original roll has none of them"""
    fin = (TREE / "DATA" / "FIN.EXE").read_bytes()
    text = extract.fin_block(fin).decode("cp932")
    assert not [c for c in text if len(c.encode("cp932")) == 2 and 0x8440 <= int.from_bytes(c.encode("cp932"), "big") <= 0x84BE]


@need_disc
def test_fin_hook_target_is_glyph_addr():
    """0x80013CE8 starts with game 1's glyph_addr prologue (addiu sp,-0x18 / sw ra,0x14(sp)) that fin_orig redoes"""
    fin = (TREE / "DATA" / "FIN.EXE").read_bytes()
    o = 0x80013CE8 - 0x8000F800
    assert struct.unpack_from("<2I", fin, o) == (0x27BDFFE8, 0xAFBF0014)


@need_disc
def test_english_roll_fits_and_ends_with_ff():
    fin = (TREE / "DATA" / "FIN.EXE").read_bytes()
    new = insert.staff_edit(fin, "en")
    assert len(new) == len(fin)
    end = len(extract.fin_block(fin)) + extract.FIN_TEXT
    assert new[end + 1:] == fin[end + 1:]  # the table after the roll is untouched
    assert b"\xff" in new[extract.FIN_TEXT:end + 1]


@need_disc
def test_exe_repoint_moves_grown_strings_in_both_exes():
    exe = (TREE / "PSX.EXE").read_bytes()
    omk = (TREE / "OMK.EXE").read_bytes()
    moves = []
    psx, omk2 = insert.exe_text(exe, omk, "en", extract.exe_table(), moves)
    assert moves
    first = int(moves[0].split(" -> ")[1].split()[0], 16)
    assert first == insert.REPOINT[0]
    off = int(moves[0].split()[0].split(".")[1], 16)
    for buf, old, shift in ((psx, exe, 0), (omk2, omk, insert.OMK_SHIFT)):
        o = off + (extract.omk_delta(off) if shift else 0)
        for p in insert.u32_refs(old, o + extract.EXE_VA):
            assert struct.unpack_from("<I", buf, p)[0] == first + shift
