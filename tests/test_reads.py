import json

import pytest

from pbw_romance.cli import main
from pbw_romance.reads import check_log


def _folder(tmp_path, upto=12):
    for n in range(1, upto + 1):
        (tmp_path / f"ch{n:02d}.txt").write_text(f"Chapter {n}: T\n\nAda smiled at Ben in chapter {n}.\n")
    return tmp_path


def _log(folder, after=12, **over):
    data = {"after_chapter": after,
            "apart": {"what": "pride", "one_conversation_fixes_it": False,
                      "evidence": [{"chapter": 2, "quote": "Ada smiled at Ben in chapter 2."}]},
            "want": {"score": 7, "evidence": [{"chapter": 3, "quote": "Ada smiled at Ben in chapter 3."}]},
            "sure": 6,
            "ways_back": [{"route": "a letter", "p": 0.6}, {"route": "a rescue", "p": 0.4}],
            "sparks": [{"pov": "Ada", "chapter": 4, "quote": "Ada smiled at Ben in chapter 4."}]}
    data.update(over)
    path = folder / f"log_ch{after:02d}.json"
    path.write_text(json.dumps(data))
    return path


def test_a_good_log_passes(tmp_path):
    assert check_log(_log(_folder(tmp_path)))["passed"]


def test_an_invented_quote_voids_the_log(tmp_path):
    path = _log(_folder(tmp_path), sparks=[{"pov": "Ada", "chapter": 4, "quote": "Never written."}])
    assert "Evidence 3: quotation absent from cited chapter" in check_log(path)["errors"]


@pytest.mark.parametrize("value", ["no", "false", 0, None])
def test_one_conversation_must_be_a_real_bool(tmp_path, value):
    path = _log(_folder(tmp_path), apart={"what": "pride", "one_conversation_fixes_it": value, "evidence": []})
    assert "apart.one_conversation_fixes_it must be true or false" in check_log(path)["errors"]


@pytest.mark.parametrize("score", [0, 11, 7.5, True, "7"])
def test_scores_are_whole_numbers_from_one_to_ten(tmp_path, score):
    assert "sure must be a whole number from 1 to 10" in check_log(_log(_folder(tmp_path), sure=score))["errors"]


def test_ways_back_are_required_from_chapter_twelve(tmp_path):
    assert check_log(_log(_folder(tmp_path, 7), after=7, ways_back=[]))["passed"]
    errors = check_log(_log(_folder(tmp_path), ways_back=[]))["errors"]
    assert "ways_back needs at least one route, each with a text 'route'" in errors


def test_way_back_probabilities_must_sum_to_one(tmp_path):
    path = _log(_folder(tmp_path), ways_back=[{"route": "a", "p": 0.6}, {"route": "b", "p": 0.6}])
    assert "Way-back probabilities do not sum to one" in check_log(path)["errors"]


def test_a_spark_names_its_lead(tmp_path):
    path = _log(_folder(tmp_path), sparks=[{"chapter": 4, "quote": "Ada smiled at Ben in chapter 4."}])
    assert "Spark 1: needs a 'pov' naming the lead" in check_log(path)["errors"]


def test_the_staged_folder_must_stop_at_the_checkpoint_unless_finished(tmp_path):
    folder = _folder(tmp_path, 14)
    assert not check_log(_log(folder))["passed"]
    assert check_log(_log(folder), finished=True)["passed"]


def test_check_read_command(tmp_path):
    path = _log(_folder(tmp_path))
    assert main(["check-read", str(path)]) == 0
    assert main(["check-read", str(_log(tmp_path, sure=0))]) == 1


@pytest.mark.parametrize("pov", [["Ada"], 3])
def test_a_spark_pov_must_be_text(tmp_path, pov):
    path = _log(_folder(tmp_path), sparks=[{"pov": pov, "chapter": 4, "quote": "Ada smiled at Ben in chapter 4."}])
    assert "Spark 1: needs a 'pov' naming the lead" in check_log(path)["errors"]
