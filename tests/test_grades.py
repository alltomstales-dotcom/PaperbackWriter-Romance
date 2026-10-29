import json

import pytest

from pbw_romance.cli import main
from pbw_romance.grades import clarity, obstacle, route_choice, verdict


def _write(tmp_path, name, data):
    p = tmp_path / name
    p.write_text(json.dumps(data))
    return p


def _items(**verdicts):
    return {"items": [{"id": k.replace("_", "."), "verdict": v} for k, v in verdicts.items()]}


def test_clarity_needs_two_of_three_per_lead_and_nothing_wrong(tmp_path):
    g = _write(tmp_path, "grade_ch07.json", _items(A_want="stated", A_wound="stated", A_obstacle="missing",
                                                   B_want="stated", B_wound="Stated ", B_obstacle="missing"))
    assert clarity(g)["passed"]
    g = _write(tmp_path, "grade_ch07.json", _items(A_want="stated", A_wound="stated", B_want="stated", B_wound="missing"))
    assert not clarity(g)["passed"]
    g = _write(tmp_path, "grade_ch07.json", _items(A_want="stated", A_wound="stated", B_want="stated",
                                                   B_wound="stated", B_obstacle="WRONG"))
    assert clarity(g)["wrong"] == ["B.obstacle"]


@pytest.mark.parametrize("bad", [
    {"items": [{"id": "A.want", "verdict": "incorrect"}]},
    {"items": [{"id": "A.want", "verdict": "stated"}, {"id": "A.want", "verdict": "wrong"}]},
    {"items": [{"verdict": "stated"}]},
])
def test_clarity_refuses_a_grade_it_cannot_read(tmp_path, bad):
    with pytest.raises(ValueError):
        clarity(_write(tmp_path, "grade_ch07.json", bad))


def test_obstacle_needs_an_inner_obstacle_and_no_easy_fix(tmp_path):
    g = _write(tmp_path, "obstacle_ch12.json", {"inner": True})
    assert obstacle(g, {"apart": {"one_conversation_fixes_it": False}})["passed"]
    assert not obstacle(g, {"apart": {"one_conversation_fixes_it": True}})["passed"]
    with pytest.raises(ValueError, match="inner"):
        obstacle(_write(tmp_path, "obstacle_ch12.json", {"inner": "yes"}), {"apart": {"one_conversation_fixes_it": False}})


WAYS = [{"route": "a", "p": 0.5}, {"route": "b", "p": 0.3}, {"route": "c", "p": 0.2}]


def test_route_choice_ranks_the_chosen_way_back_and_ties_count_as_first(tmp_path):
    assert route_choice(_write(tmp_path, "r.json", {"route_index": 1}), WAYS) == {"rank": 2, "p": 0.3, "index": 1}
    assert route_choice(_write(tmp_path, "r.json", {"route_index": None}), WAYS)["rank"] == 4
    tie = [{"route": "a", "p": 0.5}, {"route": "b", "p": 0.5}]
    assert route_choice(_write(tmp_path, "r.json", {"route_index": 1}), tie)["rank"] == 1


@pytest.mark.parametrize("index", [-1, 3, 1.0, True, "0", [0, 1]])
def test_route_choice_refuses_anything_but_one_zero_based_index(tmp_path, index):
    with pytest.raises(ValueError, match="route_index"):
        route_choice(_write(tmp_path, "r.json", {"route_index": index}), WAYS)


GOOD = {"overall": 8, "earned": 7, "chemistry": 8, "prose": 8, "character": 7, "satisfying": 8, "hea": True}


def test_verdict_targets(tmp_path):
    assert verdict(_write(tmp_path, "v.json", GOOD))["passed"]
    assert verdict(_write(tmp_path, "v.json", {**GOOD, "earned": 6}))["below"] == ["earned"]
    assert not verdict(_write(tmp_path, "v.json", {**GOOD, "hea": False}))["passed"]
    with pytest.raises(ValueError, match="hea"):
        verdict(_write(tmp_path, "v.json", {**GOOD, "hea": "yes"}))
    with pytest.raises(ValueError, match="prose"):
        verdict(_write(tmp_path, "v.json", {**GOOD, "prose": "8"}))


def test_verdict_command(tmp_path):
    assert main(["verdict", str(_write(tmp_path, "v.json", GOOD))]) == 0
    assert main(["verdict", str(_write(tmp_path, "v.json", {**GOOD, "overall": 6}))]) == 1
