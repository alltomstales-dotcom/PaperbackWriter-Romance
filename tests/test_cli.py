import subprocess

import pytest

from pbw_romance.cli import main


@pytest.mark.parametrize("command", ["exposition", "pointers"])
def test_passthrough_checks_refuse_an_empty_folder(tmp_path, command):
    assert main([command, str(tmp_path)]) == 2


def test_spoilers_passthrough_scans_tracked_files(tmp_path, capsys):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    (repo / "a.md").write_text("the Widget\n")
    subprocess.run(["git", "-C", str(repo), "add", "a.md"], check=True)
    terms = tmp_path / "terms.txt"
    terms.write_text("\\bwidget\\b\n")
    assert main(["spoilers", "--terms", str(terms), "--repo", str(repo)]) == 1
    assert "Widget" not in capsys.readouterr().out
    assert main(["spoilers", "--terms", str(tmp_path / "nope"), "--repo", str(repo)]) == 2


def test_romance_exposition_defaults_to_the_calibrated_400(tmp_path, capsys):
    from pbw_romance import EXPOSITION_THRESHOLD
    assert EXPOSITION_THRESHOLD == 400
    run = " ".join(["word"] * 350) + "."
    (tmp_path / "ch01.txt").write_text(f"Chapter 1: T\n\n{run}\n")
    assert main(["exposition", str(tmp_path)]) == 0
    assert main(["exposition", str(tmp_path), "--threshold", "300"]) == 1
