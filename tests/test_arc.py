from pathlib import Path

import pytest

from pbw_romance.arc import Beat, check_beats, parse_beats, resolution_beats
from pbw_romance.cli import main

TABLE = """| ID | Beat | Shows |
|---|---|---|
| B1 | She keeps the shop alone | ch 1 |
| **B2** | He refuses the offer | introduced: Ch. 4 |
| B3 | She says the debt aloud | chapter 20 |
"""


def _plan(tmp: Path, uses: str, table: str = TABLE) -> Path:
    (tmp / "02b_beats.md").write_text(table)
    (tmp / "01_couple_and_resolution.md").write_text(f"Way back: x\nUses beats: {uses}\n")
    return tmp


def test_parse_beats_reads_loose_formatting():
    beats = parse_beats(TABLE)
    assert beats["B2"] == Beat("B2", "He refuses the offer", 4)
    assert beats["B3"].chapter == 20


def test_split_ids_backticks_lowercase_and_indented_rows_parse():
    beats = parse_beats("| B3a | One | ch 4 |\n  | `B3b` | Two | ch 5 |\n| b4 | Three | ch 6 |\n")
    assert sorted(beats) == ["B3a", "B3b", "B4"]
    assert resolution_beats("Uses beats: B3a, b3b and B4\n") == ["B3a", "B3b", "B4"]


@pytest.mark.parametrize("row", ["| B 3 | Spaced | ch 4 |", "| | No ID | ch 5 |", "| B3x2 | Odd | ch 5 |"])
def test_a_near_miss_id_is_an_error(row):
    with pytest.raises(ValueError, match="beat row"):
        parse_beats(TABLE + row + "\n")


def test_duplicates_and_missing_chapter_are_errors():
    with pytest.raises(ValueError, match="B1"):
        parse_beats(TABLE + "| B1 | Again | ch 2 |\n")
    with pytest.raises(ValueError, match="B4"):
        parse_beats(TABLE + "| B4 | No chapter |\n")


def test_header_separator_and_other_tables_are_not_beats():
    assert sorted(parse_beats(TABLE + "| C1 | A cast row | ch 2 |\n")) == ["B1", "B2", "B3"]


def test_the_resolution_on_early_beats_passes(tmp_path):
    result = check_beats(_plan(tmp_path, "B1, B2"))
    assert result["passed"], result["errors"]
    assert result["cutoff"] == 18


def test_a_late_or_unknown_beat_fails_and_errors_carry_no_beat_text(tmp_path):
    result = check_beats(_plan(tmp_path, "B3, B9"))
    assert result["errors"] == ["B3 is used by the way back but first shows in chapter 20 (after 18)",
                                "B9 is used by the way back but is not in the beat table"]
    assert "debt" not in " ".join(result["errors"])


def test_a_beat_with_more_than_one_claim_is_an_error(tmp_path):
    result = check_beats(_plan(tmp_path, "B1", TABLE + "| B5 | She forgives him; he stays | ch 9 |\n"))
    assert "B5 states more than one claim (split it: one claim per beat)" in result["errors"]


def test_no_uses_line_is_an_error():
    with pytest.raises(ValueError, match="Uses beats"):
        resolution_beats("nothing here")


def test_beats_command_exit_codes(tmp_path):
    assert main(["beats", str(_plan(tmp_path, "B1"))]) == 0
    assert main(["beats", str(_plan(tmp_path, "B3"))]) == 1
    assert main(["beats", str(tmp_path / "nope")]) == 2
