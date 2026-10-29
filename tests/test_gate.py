import hashlib
import json
from pathlib import Path

import pytest

from pbw_romance.cli import main
from pbw_romance.gate import advance_plan_read, load_reference, score_checkpoint
from pbw_romance.plan import FIXED


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _setup(tmp: Path):
    plan = tmp / "plan"
    (plan / "digest").mkdir(parents=True)
    for name in FIXED:
        (plan / name).write_text(f"{name}\n")
    for i, (lo, hi) in enumerate([(1, 7), (8, 12), (13, 17), (18, 21), (22, 24)], 1):
        (plan / "digest" / f"batch{i}.md").write_text("\n\n".join(
            f"Chapter {n}: T\n\nAda smiled at Ben in chapter {n}. Ben laughed at Ada in chapter {n}."
            for n in range(lo, hi + 1)) + "\n")
    read = tmp / "read"
    read.mkdir()
    (read / "batch1.md").write_bytes((plan / "digest" / "batch1.md").read_bytes())
    ref = plan / "reference.json"
    ref.write_text(json.dumps({
        "candidate_directory": ".", "reader_folder": "../read",
        "leads": {"A": ["Ada", "Miss Penrose"], "B": ["Ben"]}, "dark_moment_chapter": 19,
        "plan_sha256": {n: _sha(plan / n) for n in FIXED},
        "digest_sha256": {p.name: _sha(p) for p in (plan / "digest").glob("batch*.md")}}))
    gate = plan / "gate.json"
    gate.write_text('{"checkpoints": []}')
    return plan, read, ref, gate


def _spark(pov, n, who="Ada smiled at Ben"):
    return {"pov": pov, "chapter": n, "quote": f"{who} in chapter {n}."}


def _log(read, after, want=7, sure=6, fixes=False, ways=None, sparks=None):
    lo = {7: 1, 12: 8, 17: 13, 21: 18, 24: 22}[after]
    data = {"after_chapter": after, "apart": {"what": "pride", "one_conversation_fixes_it": fixes, "evidence": []},
            "want": {"score": want, "evidence": []}, "sure": sure,
            "ways_back": ways if ways is not None else ([] if after < 12 else
                         [{"route": "a", "p": 0.6}, {"route": "b", "p": 0.4}]),
            "sparks": sparks if sparks is not None else
                      [_spark("Ada", lo), _spark("ben", lo, "Ben laughed at Ada")]}
    (read / f"log_ch{after:02d}.json").write_text(json.dumps(data))


def _grade7(read):
    (read / "grade_ch07.json").write_text(json.dumps({"items": [
        {"id": f"{l}.{f}", "verdict": "stated"} for l in "AB" for f in ("want", "wound")]}))


def _hidden(read, cp, index, inner=True):
    (read / f"rank_ch{cp}.json").write_text(json.dumps({"route_index": index}))
    (read / f"obstacle_ch{cp}.json").write_text(json.dumps({"inner": inner}))


def test_checkpoint_seven_is_clarity_and_releases_the_next_batch(tmp_path):
    plan, read, ref, gate = _setup(tmp_path)
    _log(read, 7)
    with pytest.raises(ValueError, match="grade_ch07.json"):
        advance_plan_read(ref, gate, 7)
    _grade7(read)
    assert advance_plan_read(ref, gate, 7)["passed"] and (read / "batch2.md").exists()


def test_twelve_fails_when_the_way_back_ranks_first_and_then_refuses_to_continue(tmp_path):
    plan, read, ref, gate = _setup(tmp_path)
    _log(read, 7); _grade7(read); advance_plan_read(ref, gate, 7)
    _log(read, 12); _hidden(read, 12, 0)
    record = advance_plan_read(ref, gate, 12)
    assert not record["passed"] and json.loads(gate.read_text())["stage"] == "FAILED_AT_12"
    assert not (read / "batch3.md").exists()
    with pytest.raises(ValueError, match="FAILED_AT_12"):
        advance_plan_read(ref, gate, 12)


def test_an_easy_conversation_fails_the_obstacle_gate(tmp_path):
    plan, read, ref, gate = _setup(tmp_path)
    _log(read, 7); _grade7(read); advance_plan_read(ref, gate, 7)
    _log(read, 12, fixes=True); _hidden(read, 12, 1)
    record = advance_plan_read(ref, gate, 12)
    assert not record["checks"]["obstacle"]["passed"] and record["checks"]["hidden"]["passed"]


def test_plan_hashes_must_cover_every_fixed_plan_file(tmp_path):
    plan, read, ref, gate = _setup(tmp_path)
    data = json.loads(ref.read_text())
    data["plan_sha256"].pop(FIXED[0])
    ref.write_text(json.dumps(data))
    with pytest.raises(ValueError, match=FIXED[0]):
        load_reference(ref)


def test_prose_mode_scores_chemistry_by_any_name_of_the_lead(tmp_path):
    plan, read, ref, gate = _setup(tmp_path)
    for n in range(1, 8):
        (read / f"ch{n:02d}.txt").write_text(f"Chapter {n}: T\n\nAda smiled at Ben in chapter {n}. Ben laughed at Ada in chapter {n}.\n")
    (read / "batch1.md").unlink()
    _grade7(read)
    _log(read, 7, sparks=[_spark("miss penrose", 2), _spark("BEN", 3, "Ben laughed at Ada")])
    assert score_checkpoint(load_reference(ref), 7, "prose")["checks"]["chemistry"]["passed"]
    _log(read, 7, sparks=[_spark("Ada", 2)])
    assert not score_checkpoint(load_reference(ref), 7, "prose")["passed"]


def _stage_prose(read, upto):
    for p in read.glob("batch*.md"):
        p.unlink()
    for n in range(1, upto + 1):
        (read / f"ch{n:02d}.txt").write_text(f"Chapter {n}: T\n\nAda smiled at Ben in chapter {n}. Ben laughed at Ada in chapter {n}.\n")


def test_prose_investment_needs_six_at_twelve(tmp_path):
    plan, read, ref, gate = _setup(tmp_path)
    _stage_prose(read, 12)
    _log(read, 12, want=5); _hidden(read, 12, 1)
    assert not score_checkpoint(load_reference(ref), 12, "prose")["checks"]["investment"]["passed"]


def test_prose_dark_moment_needs_high_want_and_falling_sure(tmp_path):
    plan, read, ref, gate = _setup(tmp_path)
    _stage_prose(read, 17)
    _log(read, 17, sure=6)
    _stage_prose(read, 21)
    _log(read, 21, want=9, sure=6)
    assert not score_checkpoint(load_reference(ref), 21, "prose")["checks"]["investment"]["passed"]
    _log(read, 21, want=9, sure=3)
    assert score_checkpoint(load_reference(ref), 21, "prose")["checks"]["investment"]["passed"]


def test_gate_and_score_commands(tmp_path):
    plan, read, ref, gate = _setup(tmp_path)
    _log(read, 7); _grade7(read)
    assert main(["gate", str(ref), str(gate), "7"]) == 0
    _stage_prose(read, 7)
    assert main(["score", str(ref), "7"]) == 0
