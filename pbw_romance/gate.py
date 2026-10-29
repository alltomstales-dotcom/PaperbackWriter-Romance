"""Score a checkpoint, and run the staged plan read that releases digest batches.

Plan reads (mode "plan") gate on clarity at 7, and on the obstacle and the hidden way
back at 12 and 17. Prose reads (mode "prose") add chemistry in every batch and
investment: want at least 6 by ch 12, at least 8 at the dark moment, and sure falling there.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from paperbackwriter.outline import checkpoints
from pbw_scifi.reads import _load

from .grades import clarity, obstacle, route_choice
from .plan import FIXED
from .reads import check_log


def _sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_reference(path: Path) -> dict:
    path = Path(path)
    ref = _load(path)
    for key in ("candidate_directory", "reader_folder", "leads", "dark_moment_chapter", "plan_sha256"):
        if key not in ref:
            raise ValueError(f"{path.name}: {key} is required")
    if sorted(ref["leads"]) != ["A", "B"] or not all(ref["leads"][k] for k in "AB"):
        raise ValueError(f"{path.name}: leads must list names for A and B")
    missing = [n for n in FIXED if n not in ref["plan_sha256"]]
    if missing:
        raise ValueError(f"{path.name}: plan_sha256 must cover every plan file; missing {', '.join(missing)}")
    ref["candidate"] = (path.parent / ref["candidate_directory"]).resolve()
    ref["folder"] = (path.parent / ref["reader_folder"]).resolve()
    for name, h in ref["plan_sha256"].items():
        if _sha(ref["candidate"] / name) != h:
            raise ValueError(f"plan file changed since the reference was written: {name}")
    return ref


def _lead_of(pov: str, leads: dict) -> str | None:
    p = pov.strip().lower()
    return next((k for k, names in leads.items() if p in (n.lower() for n in names)), None)


def score_checkpoint(ref: dict, checkpoint: int, mode: str, n_chapters: int = 24) -> dict:
    if mode not in ("plan", "prose"):
        raise ValueError("mode must be plan or prose")
    points = checkpoints(n_chapters)
    if checkpoint not in points:
        raise ValueError(f"checkpoint must be one of {points}")
    i = points.index(checkpoint)
    folder = ref["folder"]
    log_path = folder / f"log_ch{checkpoint:02d}.json"
    checked = check_log(log_path)
    if not checked["passed"]:
        raise ValueError(f"log failed verification: {checked['errors']}")
    log = _load(log_path)

    def need(name: str) -> Path:
        p = folder / name
        if not p.exists():
            raise ValueError(f"checkpoint {checkpoint} needs {name} from a grader agent")
        return p

    checks: dict[str, dict] = {}
    record = {"checkpoint": checkpoint, "want": log["want"]["score"], "sure": log["sure"],
              "exact_quotes": checked["evidence_count"]}
    if i == 0:
        checks["clarity"] = clarity(need(f"grade_ch{checkpoint:02d}.json"))
    if i in (1, 2):
        checks["obstacle"] = obstacle(need(f"obstacle_ch{checkpoint:02d}.json"), log)
        choice = route_choice(need(f"rank_ch{checkpoint:02d}.json"), log["ways_back"])
        record.update(rank=choice["rank"], probability=choice["p"])
        checks["hidden"] = {"passed": choice["rank"] > 1 if i == 1 else choice["p"] <= 0.35}
    if mode == "prose":
        lo = points[i - 1] if i else 0
        counts = {k: 0 for k in ref["leads"]}
        for s in log.get("sparks", []):
            lead = _lead_of(s["pov"], ref["leads"])
            if lead and lo < s.get("chapter", 0) <= checkpoint:
                counts[lead] += 1
        checks["chemistry"] = {"passed": all(c >= 1 for c in counts.values()), "sparks": counts}
        dark = next(p for p in points if p >= ref["dark_moment_chapter"])
        if i == 1:
            checks["investment"] = {"passed": log["want"]["score"] >= 6}
        elif checkpoint == dark and i > 0:
            before = _load(folder / f"log_ch{points[i - 1]:02d}.json")["sure"]
            checks["investment"] = {"passed": log["want"]["score"] >= 8 and log["sure"] < before,
                                    "sure_before": before}
    record["checks"] = checks
    record["passed"] = all(c["passed"] for c in checks.values())
    return record


def advance_plan_read(reference: Path, gate_path: Path, checkpoint: int, n_chapters: int = 24) -> dict:
    reference, gate_path = Path(reference), Path(gate_path)
    ref = load_reference(reference)
    gate = _load(gate_path)
    if str(gate.get("stage", "")).startswith("FAILED_AT_"):
        raise ValueError(f"plan read already failed ({gate['stage']}); redesign and start a new read")
    candidate, folder = ref["candidate"], ref["folder"]
    digest = candidate / "reader" / "digest" if (candidate / "reader" / "digest").is_dir() else candidate / "digest"
    for name, h in ref.get("digest_sha256", {}).items():
        if _sha(digest / name) != h or ((folder / name).exists() and _sha(folder / name) != h):
            raise ValueError(f"digest batch changed since the reference was written: {name}")
    points = checkpoints(n_chapters)
    record = score_checkpoint(ref, checkpoint, "plan", n_chapters)
    index = points.index(checkpoint)
    if len(gate["checkpoints"]) != index:
        raise ValueError("checkpoints must be scored in order")
    gate["checkpoints"].append(record)
    gate["gate_passed"] = len(gate["checkpoints"]) >= 3 and all(r["passed"] for r in gate["checkpoints"][:3])
    if not record["passed"]:
        gate["stage"] = f"FAILED_AT_{checkpoint}"
    elif checkpoint < points[-1]:
        name = f"batch{index + 2}.md"
        if (folder / name).exists():
            raise ValueError("next batch was already released")
        shutil.copy2(digest / name, folder / name)
        record["released_through"] = points[index + 1]
        gate["stage"] = "EARLY_GATE_PASSED" if gate["gate_passed"] else "RUNNING"
    else:
        gate["stage"] = "READ_COMPLETE"
    gate_path.write_text(json.dumps(gate, indent=2) + "\n", encoding="utf-8")
    return record
