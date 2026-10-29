import pytest

from pbw_romance.cli import main
from pbw_romance.period import find_banned


def _ch(tmp_path, text):
    (tmp_path / "ch01.txt").write_text(f"Chapter 1: T\n\n{text}\n")
    return tmp_path


def test_reports_chapter_line_pattern_and_match(tmp_path):
    hits = find_banned(_ch(tmp_path, "She checked her wristwatch."), [r"\bwrist ?watch\w*"])
    assert hits == [{"chapter": 1, "line": 3, "pattern": 1, "match": "wristwatch"}]


def test_entries_match_exactly_as_written_and_ignore_case(tmp_path):
    folder = _ch(tmp_path, "The Telephone rang. A phone-like sound.")
    assert [h["match"] for h in find_banned(folder, [r"\btelephone\b"])] == ["Telephone"]
    assert [h["match"] for h in find_banned(folder, [r"\bphone\b"])] == ["phone"]  # not inside "Telephone"


def test_an_anachronism_inside_dialogue_still_counts(tmp_path):
    assert find_banned(_ch(tmp_path, '"Okay," she said.'), [r"\bokay\b"])


def test_period_command_exit_codes(tmp_path):
    banned = tmp_path / "BANNED.txt"
    banned.write_text("# devices\n\\btelephone\\b\n")
    chapters = tmp_path / "chapters"
    chapters.mkdir()
    (chapters / "ch01.txt").write_text("Chapter 1: T\n\nA letter came.\n")
    assert main(["period", str(chapters), "--banned", str(banned)]) == 0
    (chapters / "ch02.txt").write_text("Chapter 2: T\n\nThe telephone rang.\n")
    assert main(["period", str(chapters), "--banned", str(banned)]) == 1
    assert main(["period", str(chapters), "--banned", str(tmp_path / "nope")]) == 2
