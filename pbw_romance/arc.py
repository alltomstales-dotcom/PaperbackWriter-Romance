"""Growth beats, and fair play for romance: the way back uses only change already shown.

Beats live in a Markdown table, one per row: | B4 | the step | ch 11 |. The third column
is the chapter where the beat first shows on the page. The resolution file names the beats
the way back uses: "Uses beats: B2, B4". Reports carry IDs and chapter numbers only.
The row parser is the sci-fi engine-v1.1 rules parser, re-keyed from R to B.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

BEAT_ID = re.compile(r"[Bb](\d+)([A-Za-z]?)")
LOOKS_LIKE_ID = re.compile(r"[Bb]\s*\d")
WHEN = re.compile(r"(?:introduced:\s*)?ch(?:apter)?\.?\s*(\d+)", re.I)
USES = re.compile(r"(?mi)^\W*uses beats:?\**\s*(.+)$")
BEATS = "02b_beats.md"
RESOLUTION = "01_couple_and_resolution.md"


@dataclass(frozen=True)
class Beat:
    id: str
    text: str
    chapter: int


def parse_beats(text: str) -> dict[str, Beat]:
    beats: dict[str, Beat] = {}
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        first = cells[0].strip("*` ")
        m = BEAT_ID.fullmatch(first)
        if not m:
            # Header, separator and other tables' rows are skipped; a near-miss ID is not.
            if LOOKS_LIKE_ID.match(first) or (not first and any(cells[1:])):
                raise ValueError(f"beat row with no clean ID (use B3 or B3a): {first or '(empty)'!r}")
            continue
        bid = f"B{m.group(1)}{m.group(2).lower()}"
        when = WHEN.fullmatch(cells[2]) if len(cells) > 2 else None
        if len(cells) < 2 or not cells[1] or not when:
            raise ValueError(f"{bid}: row needs '| {bid} | beat | ch N |'")
        if bid in beats:
            raise ValueError(f"duplicate beat ID {bid}")
        beats[bid] = Beat(bid, cells[1], int(when.group(1)))
    return beats


def resolution_beats(text: str) -> list[str]:
    m = USES.search(text)
    ids = [f"B{n}{s.lower()}" for n, s in re.findall(r"\b[Bb](\d+)([A-Za-z]?)\b", m.group(1))] if m else []
    if not ids:
        raise ValueError("no 'Uses beats: B1, B2' line in the resolution file")
    return ids


def check_beats(plan_dir: Path, n_chapters: int = 24) -> dict:
    plan_dir = Path(plan_dir)
    cutoff = int(n_chapters * 0.75)
    beats = parse_beats((plan_dir / BEATS).read_text(encoding="utf-8"))
    errors = [f"{b.id} states more than one claim (split it: one claim per beat)"
              for b in beats.values() if ";" in b.text]
    uses = resolution_beats((plan_dir / RESOLUTION).read_text(encoding="utf-8"))
    for bid in uses:
        if bid not in beats:
            errors.append(f"{bid} is used by the way back but is not in the beat table")
        elif beats[bid].chapter > cutoff:
            errors.append(f"{bid} is used by the way back but first shows in chapter {beats[bid].chapter} (after {cutoff})")
    return {"passed": not errors, "errors": errors, "beats": len(beats), "resolution_beats": uses, "cutoff": cutoff}
