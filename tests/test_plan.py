from pbw_romance.cli import main
from pbw_romance.plan import FIXED, check_plan


def test_an_empty_plan_reports_the_romance_files_not_the_mystery_ones(tmp_path):
    errors = check_plan(tmp_path)["errors"]
    for name in FIXED:
        assert f"Missing {name}" in errors
    assert not any("solution_and_suspects" in e or "02b_clues" in e for e in errors)


def test_an_oversized_plan_file_is_an_error(tmp_path):
    (tmp_path / "02b_beats.md").write_text("word " * 2100)
    assert "02b_beats.md must contain fewer than 2,000 words" in check_plan(tmp_path)["errors"]


def test_the_parent_still_reports_missing_outlines_and_brief(tmp_path):
    errors = check_plan(tmp_path)["errors"]
    assert "Missing chapter outline files (0N_chapters_*.md)" in errors and "Missing writer brief" in errors


def test_check_plan_command(tmp_path):
    assert main(["check-plan", str(tmp_path)]) == 1
