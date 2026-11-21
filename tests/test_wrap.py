import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import wrap  # noqa: E402

# game 1's tests/test_wrap.py (wrap parts; the batch-check and phase-8 lint tests come with batches.py in phase 6)


def test_space_before_name_kept():
    # an odd run before {name} keeps its space ("My name isRaviel" in phase 8); before {n} it still goes
    assert wrap._fix_odd(["My name is ", "{name:0080}"]) == ["My name is ", "{name:0080}"]
    assert wrap._fix_odd(["Hello there ", "{n}"]) == ["Hello there ", "{n}"]  # even: untouched
    assert wrap._fix_odd(["Hi there ", "{wait}"]) == ["Hi there", "{wait}"]


def test_no_one_word_last_line():
    lines = wrap.wrap_line(["Together we overcame many hardships, and I was able to watch them grow."])
    texts = ["".join(ln) for ln in lines]
    assert len(texts) == 2 and " " in texts[-1], texts
    assert all(wrap.cells(ln) <= wrap.CELLS for ln in lines)


def test_page_break_at_clause_not_mid_sentence():
    en = ("{e0:E0FF}{spk:E783}{fa:0080}{n}{f7:0080}Bandit:{n}{f7:0380}{n}Tch... I finally get a fine batch of goods"
          " together, and some meddler shows up.{n}{wait}{clear}{end}")
    out = wrap.wrap(en)
    assert "together,{n}{wait}{clear}{spk:E783}{n}and some meddler shows up." in out, out
    for cells, _ in wrap.lines_report(out):
        assert cells <= wrap.CELLS


def test_page_break_moves_whole_sentence_when_no_clause_fits():
    en = ("{spk:0001}{n}Alpha beta.{n}Gamma delta.{n}Whose story would you like to hear today, my dear friend"
          " Angel?{n}{wait}{clear}{end}")
    out = wrap.wrap(en)
    assert "delta.{n}{wait}{clear}{spk:0001}{n}Whose story would you like to hear{n}today, my" in out, out


def test_simplify_drops_only_soft_breaks():
    jp = "{e0:1600}{spk:0080}{n}よく来ましたね。{n}何か？{n}{wait}{clear}{end}"
    assert wrap.simplify(jp) == "{e0:1600}{spk:0080}{n}よく来ましたね。何か？{n}{wait}{clear}{end}"


def test_wrap_fits_and_continues_with_speaker():
    en = "{e0:0001}{spk:0002}{n}" + " ".join(["word"] * 40) + "{n}{wait}{clear}{end}"
    out = wrap.wrap(en)
    for cells, _ in wrap.lines_report(out):
        assert cells <= wrap.CELLS
    assert "{n}{wait}{clear}{spk:0002}{n}word" in out
    assert wrap.codes(out) != wrap.codes(en)  # a continuation page was added
    assert out.endswith("{n}{wait}{clear}{end}")


def test_limits_match_the_measured_dialogue_box():
    """docs/windows.tsv dialogue: 40 letters (20 pair cells) x 3 lines, measured in this game's ruler build"""
    root = Path(__file__).resolve().parent.parent
    rows = [ln.split("\t") for ln in (root / "docs" / "windows.tsv").read_text(encoding="utf-8").splitlines()]
    dlg = next(r for r in rows if r[0] == "dialogue")
    assert dlg[3] == "measured" and int(dlg[1]) == 2 * wrap.CELLS and int(dlg[2]) == wrap.LINES
