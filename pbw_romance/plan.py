"""Structure check for a romance plan folder.

Wraps the mystery engine's check_plan (outline coverage, digest batches, writer brief,
the 2,000-word cap) and swaps its fixed file names for the romance ones. Chapter
outlines keep the parent's 04_chapters_*.md naming so its reader and digest tools work.
"""
from __future__ import annotations

from pathlib import Path

from paperbackwriter import plan as mystery

FIXED = ("01_couple_and_resolution.md", "02_world_and_period.md", "02b_beats.md",
         "03_cast.md", "canon.md", "audit.md")
_MYSTERY_ONLY = sorted(set(mystery.FIXED) - set(FIXED))


def check_plan(root: Path, n_chapters: int = 24) -> dict:
    root = Path(root).resolve()  # the parent looks for the writer brief in root.parent
    result = mystery.check_plan(root, n_chapters)
    drop = {f"Missing {name}" for name in _MYSTERY_ONLY}
    errors = [e for e in result["errors"] if e not in drop]
    for name in FIXED:
        if name in mystery.FIXED:
            continue  # already checked by the mystery engine
        path = root / name
        if not path.is_file():
            errors.append(f"Missing {name}")
            continue
        words = len(path.read_text(encoding="utf-8").split())
        result["word_counts"][name] = words
        if not 0 < words < mystery.WORD_CAP:
            errors.append(f"{name} must contain fewer than 2,000 words")
    result["errors"] = errors
    result["passed"] = not errors
    return result
