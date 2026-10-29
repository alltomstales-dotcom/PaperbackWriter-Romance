"""Romance blind reads: verify a reader's checkpoint log.

At each checkpoint the reader writes log_chNN.json:
  apart      what keeps the couple apart now; would one honest conversation fix it; quotes
  want       1-10: how much the reader wants them together, with the line that moved it
  sure       1-10: how sure the reader is that they will get there
  ways_back  from ch 12: the ways past the final obstacle, probabilities summing to one
  sparks     quoted moments of chemistry, each tagged with the lead whose point of view it is in
Every quote is checked by exact string search; an invented quote voids the log.
"""
from __future__ import annotations

from pathlib import Path

from pbw_scifi.reads import _load, _quotes, _staged_text

WAYS_BACK_FROM = 12


def _is_score(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 1 <= value <= 10


def check_log(path: Path, finished: bool = False) -> dict:
    path = Path(path)
    data = _load(path)
    checkpoint = int(data["after_chapter"])
    chapters = _staged_text(path.parent)
    if finished:
        chapters = {n: t for n, t in chapters.items() if n <= checkpoint}
    errors: list[str] = []
    if set(chapters) != set(range(1, checkpoint + 1)):
        errors.append("Staged chapters must be exactly chapters 1 through the checkpoint")
    apart = data.get("apart")
    if not isinstance(apart, dict) or not str(apart.get("what", "")).strip():
        errors.append("apart.what is required")
    elif not isinstance(apart.get("one_conversation_fixes_it"), bool):
        errors.append("apart.one_conversation_fixes_it must be true or false")
    want = data.get("want")
    if not isinstance(want, dict) or not _is_score(want.get("score")):
        errors.append("want.score must be a whole number from 1 to 10")
    if not _is_score(data.get("sure")):
        errors.append("sure must be a whole number from 1 to 10")
    ways = data.get("ways_back") or []
    if checkpoint >= WAYS_BACK_FROM or ways:
        ps = [w.get("p") if isinstance(w, dict) else None for w in ways]
        if not ways or not all(isinstance(w, dict) and isinstance(w.get("route"), str) and w["route"].strip() for w in ways):
            errors.append("ways_back needs at least one route, each with a text 'route'")
        elif not all(isinstance(p, (int, float)) and not isinstance(p, bool) and 0 <= p <= 1 for p in ps):
            errors.append("Every way back needs a p between 0 and 1")
        elif abs(sum(ps) - 1) > 1e-6:
            errors.append("Way-back probabilities do not sum to one")
    for i, s in enumerate(data.get("sparks") or [], 1):
        if not isinstance(s, dict) or not str(s.get("pov", "")).strip():
            errors.append(f"Spark {i}: needs a 'pov' naming the lead")
    evidence = list(_quotes(data))
    for i, item in enumerate(evidence, 1):
        if not item.get("quote") or item["quote"] not in chapters.get(item.get("chapter"), ""):
            errors.append(f"Evidence {i}: quotation absent from cited chapter")
    return {"log": str(path), "checkpoint": checkpoint, "evidence_count": len(evidence),
            "passed": not errors, "errors": errors}
