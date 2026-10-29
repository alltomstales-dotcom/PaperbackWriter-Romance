"""Heat lint for the sweet label: kissing on the page and nothing past it.

Checks narration, dialogue and letters alike. A hit gives chapter, line and the phrase.
The list is narrow on purpose. Period prose uses "breast", "bosom", "naked" and "bed" in
innocent senses, so a word is flagged only in a context that is past a kiss: "naked"
except before eye, truth and the like; "breast" only after his hand or mouth; "bed" only
when he draws her down to it. Words such as "bosom" and "bare shoulders" are never
flagged alone.
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
    r"\bhis (?:hand|hands|mouth|lips)\b[^.]{0,20}\bher breasts?\b",
    r"\bkissed (?:her|his) bare \w+",
    r"\b(?:he (?:unlaced|unbuttoned|unhooked) her|she (?:unlaced|unbuttoned) his) (?:bodice|stays|corset|chemise|gown|dress|shirt)\b",
    r"\bdrew (?:her|him) down (?:onto|on|into|to) (?:the|his|her) bed\b",
    r"\b(?:lay|slept) with (?:her|him)\b(?=\s*[.,;:!?\u2014])",
    r"\bbedded (?:her|him)\b",
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
