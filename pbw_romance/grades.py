"""Grader files: what a fresh grader agent decides that the code can't.

A grader compares the reader's words with the private plan and writes small JSON files.
Every one is read strictly: an unexpected spelling or type is refused, never guessed at,
because a gate that is quiet on bad input looks exactly like a gate that passed.
"""
from __future__ import annotations

from pathlib import Path

from pbw_scifi.reads import _load

FIELDS = ("want", "wound", "obstacle")
VERDICTS = ("stated", "missing", "wrong")
TARGETS = {"overall": 7, "earned": 7, "chemistry": 7, "prose": 7, "character": 7, "satisfying": 7}


def _verdicts(grade: dict, name: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in grade.get("items", []):
        iid = item.get("id") if isinstance(item, dict) else None
        v = str(item.get("verdict", "")).strip().lower() if isinstance(item, dict) else ""
        if not isinstance(iid, str) or v not in VERDICTS:
            raise ValueError(f"{name}: each item needs an id and a verdict of stated, missing or wrong")
        if iid in out:
            raise ValueError(f"{name}: item {iid} graded twice")
        out[iid] = v
    return out


def clarity(grade_path: Path, leads=("A", "B")) -> dict:
    """Ch 7: each lead's want and wound, and the obstacle, as the reader states them."""
    v = _verdicts(_load(grade_path), Path(grade_path).name)
    stated = {lead: [f for f in FIELDS if v.get(f"{lead}.{f}") == "stated"] for lead in leads}
    wrong = sorted(k for k, x in v.items() if x == "wrong")
    return {"passed": not wrong and all(len(s) >= 2 for s in stated.values()), "stated": stated, "wrong": wrong}


def obstacle(grade_path: Path, log: dict) -> dict:
    """Ch 12 and 17: the grader judges the named obstacle inner; the reader says a talk won't fix it."""
    inner = _load(grade_path).get("inner")
    if not isinstance(inner, bool):
        raise ValueError(f"{Path(grade_path).name}: inner must be true or false")
    fixes = log["apart"]["one_conversation_fixes_it"]
    return {"passed": inner and not fixes, "inner": inner, "one_conversation_fixes_it": fixes}


def route_choice(rank_path: Path, ways_back: list[dict]) -> dict:
    """The grader's pick of the intended way back among the reader's routes."""
    name = Path(rank_path).name
    data = _load(rank_path)
    if "route_index" not in data:
        raise ValueError(f"{name}: route_index is required (null when the way back is absent)")
    i = data["route_index"]
    if i is None:
        return {"rank": len(ways_back) + 1, "p": 0.0, "index": None}
    if isinstance(i, bool) or not isinstance(i, int) or not 0 <= i < len(ways_back):
        raise ValueError(f"{name}: route_index must be null or a 0-based index into the log's "
                         f"{len(ways_back)} ways back")
    p = ways_back[i]["p"]
    return {"rank": 1 + sum(w["p"] > p for w in ways_back), "p": p, "index": i}


def verdict(path: Path) -> dict:
    """The finished read's scores against the blind-read targets, plus the happy ending."""
    name = Path(path).name
    v = _load(path)
    for key in TARGETS:
        if isinstance(v.get(key), bool) or not isinstance(v.get(key), int) or not 1 <= v[key] <= 10:
            raise ValueError(f"{name}: {key} must be a whole number from 1 to 10")
    if not isinstance(v.get("hea"), bool):
        raise ValueError(f"{name}: hea must be true or false")
    below = [k for k, t in TARGETS.items() if v[k] < t]
    return {"passed": not below and v["hea"], "below": below, "hea": v["hea"],
            "scores": {k: v[k] for k in TARGETS}}
