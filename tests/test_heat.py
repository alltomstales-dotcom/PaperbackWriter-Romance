import pytest

from pbw_romance.cli import main
from pbw_romance.heat import find_heat, report


def test_a_kiss_is_sweet():
    assert find_heat("He kissed her once, and she kissed him back.") == []


@pytest.mark.parametrize("line", [
    "They lay naked in the dark.",
    "She undressed him slowly.",
    "They made love by the fire.",
    "His hand found her bare breast.",
])
def test_explicit_lines_are_flagged(line):
    assert find_heat(line)


@pytest.mark.parametrize("line", [
    "She was her bosom friend from school.",
    "They walked along the breast of the hill.",
    "It could not be seen with the naked eye.",
    "Her heart beat hard in her breast.",
    "The naked truth was worse.",
])
def test_period_phrases_are_not_flagged(line):
    assert find_heat(line) == []


def test_a_quoted_letter_is_still_checked():
    assert find_heat('"My dearest, I dream of you naked," the letter ran.')


def test_report_gives_chapter_line_and_phrase(tmp_path):
    (tmp_path / "ch01.txt").write_text("Chapter 1: T\n\nA kiss.\n\nThey made love.\n")
    assert report(tmp_path) == [{"chapter": 1, "line": 5, "phrase": "made love"}]


def test_heat_command_exit_codes(tmp_path):
    (tmp_path / "ch01.txt").write_text("Chapter 1: T\n\nA kiss.\n")
    assert main(["heat", str(tmp_path)]) == 0
    (tmp_path / "ch02.txt").write_text("Chapter 2: T\n\nThey made love.\n")
    assert main(["heat", str(tmp_path)]) == 1
    assert main(["heat", str(tmp_path / "nope")]) == 2
