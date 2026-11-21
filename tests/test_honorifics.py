import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import honorifics as H  # noqa: E402

NM = {"シーヴァス": "Sievas", "ティア": "Tia"}


def test_missing_flags_dropped_honorific():
    assert H.missing("シーヴァス様、こんにちは。", "Hello, Lord Sievas.", NM)
    assert not H.missing("シーヴァス様、こんにちは。", "Hello, Sievas-sama.", NM)
    assert not H.missing("シーヴァス、こんにちは。", "Hello, Sievas.", NM)


def test_name_code_and_non_names():
    assert H.missing("{name:0180}様を見つけました！", "I found {name:0180}!", NM)
    assert not H.missing("天使様！", "Angel!", NM)  # address noun, not a name


def test_propose_auto_drops_title():
    how, new = H.propose_row("シーヴァス様！", "Lord Sievas!", NM)
    assert (how, new) == ("auto", "Sievas-sama!")


def test_propose_titled_keeps_bare_names():
    jp = "シーヴァス！{n}メイド：シーヴァス様、お休みください。"
    en = "Sievas!{n}Maid: Get some rest, Master Sievas."
    how, new = H.propose_row(jp, en, NM)
    assert how == "titled"
    assert new == "Sievas!{n}Maid: Get some rest, Sievas-sama."


def test_propose_mixed_without_title_needs_hand():
    assert H.propose_row("ティアさん？ティア！", "Tia? Tia!", NM) == ("mixed", "?")
