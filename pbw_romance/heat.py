"""Heat lint for the sweet label: kissing on the page and nothing past it.

Checks narration, dialogue and letters alike. A hit gives chapter, line and the phrase.
The list is deliberately narrow: period prose uses "breast", "bosom" and "naked" in
innocent senses, and those are excluded by the patterns rather than by a stop list.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from pbw_scifi.exposition import _chapter_files

PATTERNS = [
    r"\bnaked\b(?! (?:eye|truth|flame|blade|sword|light|fact|ambition))",
    r"\bnude\b",
    r"\bundress(?:ed|es|ing)? (?:him|her|them|each other)\b",
    r"\bmade love\b|\bmaking love\b",
    r"\bbare (?:breasts?|thighs?)\b",
    r"\bnipples?\b",
    r"\b(?:erection|orgasm\w*)\b",
    r"\b(?:his|her) (?:thighs?) (?:parted|apart)\b",
    r"\btongue (?:in|into) (?:her|his) mouth\b",
    r"\btook (?:her|him) to (?:his|her|their) bed\b",
]
_RX = re.compile("|".join(f"(?:{p})" for p in PATTERNS), re.IGNORECASE)


@dataclass(frozen=True)
class HeatHit:
    line: int
    phrase: str


def find_heat(text: str) -> list[HeatHit]:
    return [HeatHit(n, m.group(0)) for n, line in enumerate(text.splitlines(), 1) for m in _RX.finditer(line)]


def report(chapters_dir: Path) -> list[dict]:
    return [{"chapter": n, "line": h.line, "phrase": h.phrase}
            for n, text in _chapter_files(chapters_dir) for h in find_heat(text)]
