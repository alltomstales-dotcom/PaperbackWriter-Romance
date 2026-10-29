# PaperbackWriter-Romance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a sweet historical romance engine (`pbw_romance`), then validate it by writing Books 1 and 2 of a linked series through staged blind-read gates.

**Architecture:** A Python package that pins the mystery engine (`paperbackwriter` v0.1.0) for staging, proofreading and export. It also pins the sci-fi engine (`pbw-scifi` at `engine-v1.1`) for exposition, pointers, spoilers and the log helpers. The romance checks live in `pbw_romance`:
- `arc` (growth beats)
- `heat`
- `period`
- `reads` (the romance log)
- `grades` (grader files and the verdict)
- `gate` (checkpoint scoring)
- `plan`
- `calibrate`

The method lives in a skill. Books live in a private repo.

**Tech Stack:** Python ≥ 3.10, setuptools, pytest; git and gh (account `alltomstales-dotcom`). Agents: Opus for planning, reading and grading; Sonnet 5.5 for drafting and the fix pass.

**Spec:** `docs/superpowers/specs/2026-10-29-romance-engine-design.md`

## Global Constraints

- Dependencies are pinned exactly:
  - `paperbackwriter @ git+https://github.com/alltomstales-dotcom/PaperbackWriter@v0.1.0`
  - `pbw-scifi @ git+https://github.com/alltomstales-dotcom/PaperbackWriter-SciFi@engine-v1.1`
- Exit codes: 0 pass, 1 check failed, 2 bad input. Every unreadable input raises `ValueError`, which `cli.main` turns into 2.
- Plan files are each under 2,000 words. The checkpoints are 7, 12, 17, 21 and 24 of 24 chapters.
- Hiding: the intended way back is not ranked first at ch 12 and is at .35 or less at ch 17. Ties count as first.
- Blind-read targets: overall, earned, chemistry, prose, character and satisfying are each at least 7, and the reader confirms a happy ending.
- Stop rules:
  - a plan read that fails means a redesign;
  - one fix pass per book;
  - any edit after a read means reading again;
  - after a read, no way-back piece is added before ch 17.
- The public repo carries no plot, names or resolution terms. The pre-push spoiler scan runs on every push, against the private term list in `PaperbackWriter-Romance-Books/private/spoiler_terms.txt`.
- Public commits: `git -c user.name=alltomstales-dotcom -c user.email=327489623+alltomstales-dotcom@users.noreply.github.com commit …`, with the session trailer.
- Byline "PaperbackWriter-Romance (validation build)". Ask the author before any public release.
- **Ruling (spec deviation):** the plan uses `canon.md` and chapter outlines named `04_chapters_*.md`, not the spec's `05_canon.md` and `04_skeleton.md`. The mystery engine's `check_plan`, `reader` and `digest` tools require those names. Cost if wrong: renaming two files.

## Review Focus

1. **A grader's free-text answer to "would one conversation fix it?"** The log field must be a JSON bool. The string "no" is refused, not read as true. (Task 5)
2. **A way back that blends two decoys.** The grader must pick one 0-based index or null. A list or a 1-based index is refused. (Task 6)
3. **Heat words inside a quoted letter, or in a period phrase.** A letter is still checked, but "bosom friend", "the breast of the hill" and "the naked eye" are not flagged. (Task 3)
4. **Banned words that are also everyday words.** Entries are the author's case-insensitive regexes, matched exactly. `\bphone\b` does not hit "telephone". (Task 4)
5. **A spark whose `pov` names a lead by surname or nickname.** It matches any of the names listed for that lead, ignoring case. (Task 7)

---

### Task 1: Repos, scaffold, pass-through commands, spoiler hook

**Files:**
- Create: `pyproject.toml`, `.gitignore`, `pbw_romance/__init__.py`, `pbw_romance/__main__.py`, `pbw_romance/cli.py`, `scripts/install_hooks.sh`, `tests/test_reuse.py`, `tests/test_cli.py`
- Create (private repo): `PaperbackWriter-Romance-Books/private/spoiler_terms.txt`, `README.md`

**Interfaces:**
- Produces: `pbw_romance.cli.main(argv: list[str] | None) -> int`. Its pass-through commands are `exposition`, `pointers`, `spoilers` and `calibrate-threshold`, which go to `pbw_scifi.cli.main`. Also `_print(result) -> int`. Later tasks add subparsers inside `main` before `parse_args`.

- [ ] **Step 1: Write the failing tests**

`tests/test_reuse.py`:
```python
"""Everything this project borrows from its two pinned parents, called once.
If an upgrade of either breaks one, this fails first."""


def test_borrowed_from_the_mystery_engine(tmp_path):
    from paperbackwriter.outline import batches, checkpoints, sections
    from paperbackwriter.plan import FIXED, WORD_CAP, check_plan
    assert checkpoints(24) == (7, 12, 17, 21, 24)
    assert batches(24)[0] == (1, 7)
    assert sections("Chapter 1: A\n\nx\n") == {1: ("Chapter 1: A", "x")}
    assert WORD_CAP == 2000 and "canon.md" in FIXED and "audit.md" in FIXED
    assert "Missing 01_solution_and_suspects.md" in check_plan(tmp_path)["errors"]


def test_borrowed_from_the_scifi_engine(tmp_path):
    from pbw_scifi.calibrate import write_chapters
    from pbw_scifi.exposition import DEFAULT_THRESHOLD, _chapter_files
    from pbw_scifi.reads import _load, _quotes, _staged_text
    from pbw_scifi.spoilers import load_terms
    assert DEFAULT_THRESHOLD == 300
    assert write_chapters([(1, "I", "Prose.")], tmp_path) == 1
    assert _chapter_files(tmp_path) == [(1, "Chapter 1: I\n\nProse.\n")]
    assert _staged_text(tmp_path)[1].startswith("Chapter 1: I")
    assert list(_quotes({"a": [{"quote": "q", "chapter": 1}]})) == [{"quote": "q", "chapter": 1}]
    (tmp_path / "t.txt").write_text("# c\n\\bx\\b\n")
    assert load_terms(tmp_path / "t.txt") == [r"\bx\b"]
    (tmp_path / "j.json").write_text('{"a": 1}')
    assert _load(tmp_path / "j.json") == {"a": 1}
```

`tests/test_cli.py`:
```python
import subprocess

import pytest

from pbw_romance.cli import main


@pytest.mark.parametrize("command", ["exposition", "pointers"])
def test_passthrough_checks_refuse_an_empty_folder(tmp_path, command):
    assert main([command, str(tmp_path)]) == 2


def test_spoilers_passthrough_scans_tracked_files(tmp_path, capsys):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    (repo / "a.md").write_text("the Widget\n")
    subprocess.run(["git", "-C", str(repo), "add", "a.md"], check=True)
    terms = tmp_path / "terms.txt"
    terms.write_text("\\bwidget\\b\n")
    assert main(["spoilers", "--terms", str(terms), "--repo", str(repo)]) == 1
    assert "Widget" not in capsys.readouterr().out
    assert main(["spoilers", "--terms", str(tmp_path / "nope"), "--repo", str(repo)]) == 2
```

- [ ] **Step 2: Write the project files and venv, then run the tests and watch them fail**

`pyproject.toml`:
```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "pbw-romance"
version = "0.1.0"
description = "Sweet historical romance engine for PaperbackWriter."
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.10"
dependencies = [
  "paperbackwriter @ git+https://github.com/alltomstales-dotcom/PaperbackWriter@v0.1.0",
  "pbw-scifi @ git+https://github.com/alltomstales-dotcom/PaperbackWriter-SciFi@engine-v1.1",
]

[project.optional-dependencies]
dev = ["pytest", "fpdf2>=2.7"]

[project.scripts]
paperbackwriter-romance = "pbw_romance.cli:main"

[tool.setuptools]
packages = ["pbw_romance"]
```
`.gitignore`: `.superpowers/`, `__pycache__/`, `*.egg-info/`, `.pytest_cache/`.
`pbw_romance/__init__.py`: `"""Sweet historical romance engine for PaperbackWriter."""`

Run:
```bash
python3 -m venv ~/venvs/pbw-romance && ~/venvs/pbw-romance/bin/pip install -q -e '.[dev]'
~/venvs/pbw-romance/bin/python -m pytest -q
```
Expected: test_reuse passes (the parents are installed); test_cli fails to import with `ModuleNotFoundError: pbw_romance.cli`.

- [ ] **Step 3: Write `pbw_romance/cli.py` and `__main__.py`**

```python
"""Command line: `paperbackwriter-romance <command>` (or `python -m pbw_romance <command>`).

Staging chapters, outline digests, proofreading and export use the mystery package's
`paperbackwriter` command. exposition, pointers, spoilers and calibrate-threshold are
the sci-fi engine's genre-neutral checks, passed through unchanged. Exit codes: 0 pass,
1 a check failed, 2 bad input.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PASSTHROUGH = ("exposition", "pointers", "spoilers", "calibrate-threshold")


def _print(result) -> int:
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not isinstance(result, dict) or result.get("passed", True) else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in PASSTHROUGH:
        from pbw_scifi.cli import main as scifi
        return scifi(argv)
    p = argparse.ArgumentParser(prog="paperbackwriter-romance", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)
    # Task 2+ subparsers go here.
    a = p.parse_args(argv)
    try:
        return a.func(a)
    except (ValueError, FileNotFoundError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
```
`pbw_romance/__main__.py`: `import sys\nfrom .cli import main\nsys.exit(main())`

- [ ] **Step 4: Run the tests**

Run: `~/venvs/pbw-romance/bin/python -m pytest -q`. Expected: 5 passed.

- [ ] **Step 5: Create the private books repo, the term list and the hook**

```bash
B=/mnt/c/Users/tbmye/Downloads/PaperbackWriter-Romance-Books
mkdir -p $B/private && cd $B && git init -q -b main
printf '# One case-insensitive regex per line. Add names and resolution terms as the plans create them.\n' > private/spoiler_terms.txt
printf '# PaperbackWriter-Romance books (private)\n\nSeries, plans, reads and releases. Read cold: no plot in commit messages either.\n' > README.md
git add -A && git -c user.name=alltomstales-dotcom -c user.email=327489623+alltomstales-dotcom@users.noreply.github.com commit -qm "Private books repo"
~/.local/bin/gh repo create alltomstales-dotcom/PaperbackWriter-Romance-Books --private --source . --remote origin --push
~/.local/bin/gh repo view alltomstales-dotcom/PaperbackWriter-Romance-Books --json visibility   # must say PRIVATE
```
`scripts/install_hooks.sh`:
```sh
#!/bin/sh
# Install the local pre-push spoiler scan.
# Usage: PYTHON=~/venvs/pbw-romance/bin/python scripts/install_hooks.sh /path/to/private/spoiler_terms.txt
set -e
terms=$(realpath "$1")
py=${PYTHON:-$(command -v python3)}
hook="$(git rev-parse --git-path hooks)/pre-push"
cat > "$hook" <<EOF
#!/bin/sh
exec "$py" -m pbw_romance spoilers --terms "$terms" --repo "\$(git rev-parse --show-toplevel)"
EOF
chmod +x "$hook"
echo "installed $hook"
```
Run it with the private term list. Then run `~/venvs/pbw-romance/bin/python -m pbw_romance spoilers --terms <terms>`; expected: `0 spoiler hit(s)`.

- [ ] **Step 6: Commit and push**

```bash
git add -A && git -c user.name=alltomstales-dotcom -c user.email=327489623+alltomstales-dotcom@users.noreply.github.com commit -m "Scaffold: pinned parents, pass-through checks, pre-push spoiler hook"
git push   # the hook runs the scan
```

---

### Task 2: `arc.py`, growth beats and the earned check

**Files:**
- Create: `pbw_romance/arc.py`, `tests/test_arc.py`
- Modify: `pbw_romance/cli.py` (the `beats` command)

**Interfaces:**
- Produces:
  - `Beat(id: str, text: str, chapter: int)`;
  - `parse_beats(text: str) -> dict[str, Beat]`;
  - `resolution_beats(text: str) -> list[str]`;
  - `check_beats(plan_dir: Path, n_chapters: int = 24) -> dict`, which returns the keys `passed`, `errors`, `beats`, `resolution_beats` and `cutoff`;
  - the constants `BEATS = "02b_beats.md"` and `RESOLUTION = "01_couple_and_resolution.md"`.

- [ ] **Step 1: Write the failing tests** in `tests/test_arc.py`

```python
from pathlib import Path

import pytest

from pbw_romance.arc import Beat, check_beats, parse_beats, resolution_beats
from pbw_romance.cli import main

TABLE = """| ID | Beat | Shows |
|---|---|---|
| B1 | She keeps the shop alone | ch 1 |
| **B2** | He refuses the offer | introduced: Ch. 4 |
| B3 | She says the debt aloud | chapter 20 |
"""


def _plan(tmp: Path, uses: str, table: str = TABLE) -> Path:
    (tmp / "02b_beats.md").write_text(table)
    (tmp / "01_couple_and_resolution.md").write_text(f"Way back: x\nUses beats: {uses}\n")
    return tmp


def test_parse_beats_reads_loose_formatting():
    beats = parse_beats(TABLE)
    assert beats["B2"] == Beat("B2", "He refuses the offer", 4)
    assert beats["B3"].chapter == 20


def test_split_ids_backticks_lowercase_and_indented_rows_parse():
    beats = parse_beats("| B3a | One | ch 4 |\n  | `B3b` | Two | ch 5 |\n| b4 | Three | ch 6 |\n")
    assert sorted(beats) == ["B3a", "B3b", "B4"]
    assert resolution_beats("Uses beats: B3a, b3b and B4\n") == ["B3a", "B3b", "B4"]


@pytest.mark.parametrize("row", ["| B 3 | Spaced | ch 4 |", "| | No ID | ch 5 |", "| B3x2 | Odd | ch 5 |"])
def test_a_near_miss_id_is_an_error(row):
    with pytest.raises(ValueError, match="beat row"):
        parse_beats(TABLE + row + "\n")


def test_duplicates_and_missing_chapter_are_errors():
    with pytest.raises(ValueError, match="B1"):
        parse_beats(TABLE + "| B1 | Again | ch 2 |\n")
    with pytest.raises(ValueError, match="B4"):
        parse_beats(TABLE + "| B4 | No chapter |\n")


def test_header_separator_and_other_tables_are_not_beats():
    assert sorted(parse_beats(TABLE + "| C1 | A cast row | ch 2 |\n")) == ["B1", "B2", "B3"]


def test_the_resolution_on_early_beats_passes(tmp_path):
    result = check_beats(_plan(tmp_path, "B1, B2"))
    assert result["passed"], result["errors"]
    assert result["cutoff"] == 18


def test_a_late_or_unknown_beat_fails_and_errors_carry_no_beat_text(tmp_path):
    result = check_beats(_plan(tmp_path, "B3, B9"))
    assert result["errors"] == ["B3 is used by the way back but first shows in chapter 20 (after 18)",
                                "B9 is used by the way back but is not in the beat table"]
    assert "debt" not in " ".join(result["errors"])


def test_a_beat_with_more_than_one_claim_is_an_error(tmp_path):
    result = check_beats(_plan(tmp_path, "B1", TABLE + "| B5 | She forgives him; he stays | ch 9 |\n"))
    assert "B5 states more than one claim (split it: one claim per beat)" in result["errors"]


def test_no_uses_line_is_an_error():
    with pytest.raises(ValueError, match="Uses beats"):
        resolution_beats("nothing here")


def test_beats_command_exit_codes(tmp_path):
    assert main(["beats", str(_plan(tmp_path, "B1"))]) == 0
    assert main(["beats", str(_plan(tmp_path, "B3"))]) == 1
    assert main(["beats", str(tmp_path / "nope")]) == 2
```

- [ ] **Step 2: Run them and watch them fail**

Run: `~/venvs/pbw-romance/bin/python -m pytest -q tests/test_arc.py`. Expected: a collection error, `No module named 'pbw_romance.arc'`.

- [ ] **Step 3: Implement `pbw_romance/arc.py`**

```python
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
```
In `cli.py`, add above `main`:
```python
def cmd_beats(a):
    from .arc import check_beats
    return _print(check_beats(Path(a.plan), a.chapters))
```
and inside `main`:
```python
    s = sub.add_parser("beats", help="earned check: the way back uses only beats shown by 75%%")
    s.add_argument("plan")
    s.add_argument("--chapters", type=int, default=24)
    s.set_defaults(func=cmd_beats)
```

- [ ] **Step 4: Run the suite.** Expected: all pass (5 + 11).
- [ ] **Step 5: Commit and push** with the message "arc: growth-beat table and the earned check".

---

### Task 3: `heat.py`, the sweet-heat promise

**Files:**
- Create: `pbw_romance/heat.py`, `tests/test_heat.py`
- Modify: `pbw_romance/cli.py` (the `heat` command)

**Interfaces:**
- Consumes: `pbw_scifi.exposition._chapter_files(dir) -> list[tuple[int, str]]`, which raises `ValueError` on an empty folder.
- Produces:
  - `HeatHit(line: int, phrase: str)`;
  - `find_heat(text: str) -> list[HeatHit]`;
  - `report(chapters_dir: Path) -> list[dict]`, whose items have the keys `chapter`, `line` and `phrase`.

- [ ] **Step 1: Write the failing tests** in `tests/test_heat.py`

```python
import pytest

from pbw_romance.cli import main
from pbw_romance.heat import find_heat, report


def test_a_kiss_is_sweet():
    assert find_heat("He kissed her once, and she kissed him back.") == []


@pytest.mark.parametrize("line", [
    "They lay naked in the dark.",
    "She undressed him slowly.",
    "They made love by the fire.",
    "His hand found her bare breast.",
])
def test_explicit_lines_are_flagged(line):
    assert find_heat(line)


@pytest.mark.parametrize("line", [
    "She was her bosom friend from school.",
    "They walked along the breast of the hill.",
    "It could not be seen with the naked eye.",
    "Her heart beat hard in her breast.",
    "The naked truth was worse.",
])
def test_period_phrases_are_not_flagged(line):
    assert find_heat(line) == []


def test_a_quoted_letter_is_still_checked():
    assert find_heat('"My dearest, I dream of you naked," the letter ran.')


def test_report_gives_chapter_line_and_phrase(tmp_path):
    (tmp_path / "ch01.txt").write_text("Chapter 1: T\n\nA kiss.\n\nThey made love.\n")
    assert report(tmp_path) == [{"chapter": 1, "line": 5, "phrase": "made love"}]


def test_heat_command_exit_codes(tmp_path):
    (tmp_path / "ch01.txt").write_text("Chapter 1: T\n\nA kiss.\n")
    assert main(["heat", str(tmp_path)]) == 0
    (tmp_path / "ch02.txt").write_text("Chapter 2: T\n\nThey made love.\n")
    assert main(["heat", str(tmp_path)]) == 1
    assert main(["heat", str(tmp_path / "nope")]) == 2
```

- [ ] **Step 2: Run them and watch them fail** (`No module named 'pbw_romance.heat'`).

- [ ] **Step 3: Implement `pbw_romance/heat.py`**

```python
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
```
CLI:
```python
def cmd_heat(a):
    from .heat import report
    hits = report(Path(a.chapters_dir))
    for h in hits:
        print(f"ch{h['chapter']:02d}:{h['line']}  {h['phrase']!r}")
    print(f"{len(hits)} heat hits (sweet label: kissing only)")
    return 1 if hits else 0
```
```python
    s = sub.add_parser("heat", help="sweet-heat lint: nothing past a kiss on the page")
    s.add_argument("chapters_dir")
    s.set_defaults(func=cmd_heat)
```

- [ ] **Step 4: Run the suite.** All pass.
- [ ] **Step 5: Commit and push** with the message "heat: sweet-label lint, period phrases excluded".

---

### Task 4: `period.py`, the anachronism lint

**Files:**
- Create: `pbw_romance/period.py`, `tests/test_period.py`
- Modify: `pbw_romance/cli.py` (the `period` command)

**Interfaces:**
- Consumes:
  - `pbw_scifi.spoilers.load_terms(path) -> list[str]`, which raises `ValueError` when the file is missing;
  - `_chapter_files`.
- Produces: `find_banned(chapters_dir: Path, patterns: list[str]) -> list[dict]`, whose items have the keys `chapter`, `line`, `pattern` (1-based) and `match`.

- [ ] **Step 1: Write the failing tests** in `tests/test_period.py`

```python
import pytest

from pbw_romance.cli import main
from pbw_romance.period import find_banned


def _ch(tmp_path, text):
    (tmp_path / "ch01.txt").write_text(f"Chapter 1: T\n\n{text}\n")
    return tmp_path


def test_reports_chapter_line_pattern_and_match(tmp_path):
    hits = find_banned(_ch(tmp_path, "She checked her wristwatch."), [r"\bwrist ?watch\w*"])
    assert hits == [{"chapter": 1, "line": 3, "pattern": 1, "match": "wristwatch"}]


def test_entries_match_exactly_as_written_and_ignore_case(tmp_path):
    folder = _ch(tmp_path, "The Telephone rang. A phone-like sound.")
    assert [h["match"] for h in find_banned(folder, [r"\btelephone\b"])] == ["Telephone"]
    assert [h["match"] for h in find_banned(folder, [r"\bphone\b"])] == ["phone"]  # not inside "Telephone"


def test_an_anachronism_inside_dialogue_still_counts(tmp_path):
    assert find_banned(_ch(tmp_path, '"Okay," she said.'), [r"\bokay\b"])


def test_period_command_exit_codes(tmp_path):
    banned = tmp_path / "BANNED.txt"
    banned.write_text("# devices\n\\btelephone\\b\n")
    chapters = tmp_path / "chapters"
    chapters.mkdir()
    (chapters / "ch01.txt").write_text("Chapter 1: T\n\nA letter came.\n")
    assert main(["period", str(chapters), "--banned", str(banned)]) == 0
    (chapters / "ch02.txt").write_text("Chapter 2: T\n\nThe telephone rang.\n")
    assert main(["period", str(chapters), "--banned", str(banned)]) == 1
    assert main(["period", str(chapters), "--banned", str(tmp_path / "nope")]) == 2
```

- [ ] **Step 2: Run them and watch them fail.**

- [ ] **Step 3: Implement `pbw_romance/period.py`**

```python
"""Anachronism lint: words, objects and ideas the series' period doesn't have yet.

The banned list lives with the series bible (BANNED.txt): one case-insensitive regex per
line, written by the author with the word boundaries they mean. Dialogue counts too.
"""
from __future__ import annotations

import re
from pathlib import Path

from pbw_scifi.exposition import _chapter_files


def find_banned(chapters_dir: Path, patterns: list[str]) -> list[dict]:
    compiled = [re.compile(p, re.IGNORECASE) for p in patterns]
    hits = []
    for n, text in _chapter_files(chapters_dir):
        for line_no, line in enumerate(text.splitlines(), 1):
            for i, rx in enumerate(compiled, 1):
                for m in rx.finditer(line):
                    hits.append({"chapter": n, "line": line_no, "pattern": i, "match": m.group(0)})
    return hits
```
CLI:
```python
def cmd_period(a):
    from pbw_scifi.spoilers import load_terms
    from .period import find_banned
    hits = find_banned(Path(a.chapters_dir), load_terms(Path(a.banned)))
    for h in hits:
        print(f"ch{h['chapter']:02d}:{h['line']}  #{h['pattern']}  {h['match']!r}")
    print(f"{len(hits)} anachronisms")
    return 1 if hits else 0
```
```python
    s = sub.add_parser("period", help="anachronism lint against the series' banned list")
    s.add_argument("chapters_dir")
    s.add_argument("--banned", required=True, help="BANNED.txt: one case-insensitive regex per line")
    s.set_defaults(func=cmd_period)
```

- [ ] **Step 4: Run the suite.** All pass.
- [ ] **Step 5: Commit and push** with the message "period: anachronism lint".

---

### Task 5: `reads.py`, the romance reader log

**Files:**
- Create: `pbw_romance/reads.py`, `tests/test_reads.py`
- Modify: `pbw_romance/cli.py` (the `check-read` command)

**Interfaces:**
- Consumes: `pbw_scifi.reads._load`, `_quotes` and `_staged_text`.
- Produces:
  - `check_log(path: Path, finished: bool = False) -> dict`, which returns the keys `log`, `checkpoint`, `evidence_count`, `passed` and `errors`;
  - the constant `WAYS_BACK_FROM = 12`.

Log schema (`log_chNN.json`):
```json
{"after_chapter": 12,
 "apart": {"what": "text", "one_conversation_fixes_it": false, "evidence": [{"chapter": 9, "quote": "…"}]},
 "want": {"score": 7, "evidence": [{"chapter": 11, "quote": "…"}]},
 "sure": 6,
 "ways_back": [{"route": "text", "p": 0.5}],
 "sparks": [{"pov": "lead's name", "chapter": 10, "quote": "…"}]}
```

- [ ] **Step 1: Write the failing tests** in `tests/test_reads.py`

```python
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
```

- [ ] **Step 2: Run them and watch them fail.**

- [ ] **Step 3: Implement `pbw_romance/reads.py`**

```python
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
```
CLI:
```python
def cmd_check_read(a):
    from .reads import check_log
    return _print(check_log(Path(a.log), a.finished))
```
```python
    s = sub.add_parser("check-read", help="verify a reader's checkpoint log")
    s.add_argument("log")
    s.add_argument("--finished", action="store_true", help="audit a completed read")
    s.set_defaults(func=cmd_check_read)
```

- [ ] **Step 4: Run the suite.** All pass.
- [ ] **Step 5: Commit and push** with the message "reads: romance checkpoint log (apart, want, sure, ways back, sparks)".

---

### Task 6: `grades.py`, the grader files and the verdict

**Files:**
- Create: `pbw_romance/grades.py`, `tests/test_grades.py`
- Modify: `pbw_romance/cli.py` (the `verdict` command)

**Interfaces:**
- Produces:
  - `clarity(grade_path: Path, leads=("A", "B")) -> dict`, with the keys `passed`, `stated` (lead → list of fields) and `wrong`;
  - `obstacle(grade_path: Path, log: dict) -> dict`, with the keys `passed`, `inner` and `one_conversation_fixes_it`;
  - `route_choice(rank_path: Path, ways_back: list[dict]) -> dict`, with the keys `rank`, `p` and `index`;
  - `verdict(path: Path) -> dict`, with the keys `passed`, `below`, `hea` and `scores`;
  - the constants `FIELDS = ("want", "wound", "obstacle")` and `TARGETS`.

Grader file schemas:
- `grade_ch07.json`: `{"items": [{"id": "A.want", "verdict": "stated|missing|wrong"}, …]}`, with ids from `A`/`B` × `FIELDS`.
- `obstacle_chNN.json`: `{"inner": true, "why": "two sentences"}`.
- `rank_chNN.json`: `{"route_index": 0, "why": "…"}`. This is a 0-based position in the log's `ways_back`, or null when the intended way back is absent.
- `verdict.json`: `{"overall": 8, "earned": 7, "chemistry": 8, "prose": 8, "character": 7, "satisfying": 8, "hea": true, …}`.

- [ ] **Step 1: Write the failing tests** in `tests/test_grades.py`

```python
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
```

- [ ] **Step 2: Run them and watch them fail.**

- [ ] **Step 3: Implement `pbw_romance/grades.py`**

```python
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
```
CLI:
```python
def cmd_verdict(a):
    from .grades import verdict
    return _print(verdict(Path(a.verdict)))
```
```python
    s = sub.add_parser("verdict", help="a finished read's scores against the targets")
    s.add_argument("verdict")
    s.set_defaults(func=cmd_verdict)
```

- [ ] **Step 4: Run the suite.** All pass.
- [ ] **Step 5: Commit and push** with the message "grades: clarity, obstacle, route choice and verdict, read strictly".

---

### Task 7: `gate.py`, checkpoint scoring for plan reads and prose reads

**Files:**
- Create: `pbw_romance/gate.py`, `tests/test_gate.py`
- Modify: `pbw_romance/cli.py` (the `gate` and `score` commands)

**Interfaces:**
- Consumes: `check_log` (Task 5); `clarity`, `obstacle` and `route_choice` (Task 6); `paperbackwriter.outline.checkpoints`; `pbw_romance.plan.FIXED` (Task 8). Write this task's own `FIXED` import as `from .plan import FIXED`. If Task 8 isn't done yet, create `pbw_romance/plan.py` now with just the `FIXED` tuple from Task 8; Task 8 adds the rest.
- Produces:
  - `load_reference(path: Path) -> dict`, which adds the resolved `candidate` and `folder` paths;
  - `score_checkpoint(ref: dict, checkpoint: int, mode: str, n_chapters: int = 24) -> dict`, where `mode` is `"plan"` or `"prose"`;
  - `advance_plan_read(reference: Path, gate_path: Path, checkpoint: int, n_chapters: int = 24) -> dict`.

`reference.json` (private, in the books repo, next to the plan):
```json
{"candidate_directory": ".", "reader_folder": "../blind_read/2026-11-01-plan-v1",
 "leads": {"A": ["Ada", "Miss Penrose"], "B": ["Ben", "Tregarthen"]},
 "dark_moment_chapter": 19,
 "plan_sha256": {"01_couple_and_resolution.md": "…", "…": "…"},
 "digest_sha256": {"batch1.md": "…"}}
```

Scoring at checkpoint index i of (7, 12, 17, 21, 24):
- **i = 0:** `clarity` from `grade_ch07.json`.
- **i = 1:** `obstacle` from `obstacle_ch12.json`, plus hidden (rank > 1, via `rank_ch12.json`).
- **i = 2:** `obstacle` and hidden (p ≤ .35), using the ch 17 files.
- **In prose mode only, every checkpoint** also scores chemistry: each lead has at least one spark whose chapter falls in this batch and whose `pov` matches one of the lead's names, ignoring case.
- **In prose mode only, investment:**
  - at i = 1, want must be at least 6;
  - at the first checkpoint at or after `dark_moment_chapter`, want must be at least 8 and sure must be below the previous checkpoint's sure.
- **Plan reads** don't score chemistry or investment, because digest summaries have no prose sparks.
- **The plan-read gate** passes when the first three checkpoints pass. It refuses to score after a `FAILED_AT_` stage, and it refuses a `plan_sha256` that doesn't cover every name in `plan.FIXED`. Those two refusals fix sci-fi minors M2 and M8.

- [ ] **Step 1: Write the failing tests** in `tests/test_gate.py`

```python
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
```

- [ ] **Step 2: Run them and watch them fail.**

- [ ] **Step 3: Implement `pbw_romance/gate.py`**

```python
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
```
CLI:
```python
def cmd_gate(a):
    from .gate import advance_plan_read
    return _print(advance_plan_read(Path(a.reference), Path(a.gate), a.checkpoint, a.chapters))


def cmd_score(a):
    from .gate import load_reference, score_checkpoint
    return _print(score_checkpoint(load_reference(Path(a.reference)), a.checkpoint, "prose", a.chapters))
```
```python
    s = sub.add_parser("gate", help="plan read: score a checkpoint; release the next batch on a pass")
    s.add_argument("reference"); s.add_argument("gate"); s.add_argument("checkpoint", type=int)
    s.add_argument("--chapters", type=int, default=24)
    s.set_defaults(func=cmd_gate)

    s = sub.add_parser("score", help="prose read: score a checkpoint (chemistry and investment included)")
    s.add_argument("reference"); s.add_argument("checkpoint", type=int)
    s.add_argument("--chapters", type=int, default=24)
    s.set_defaults(func=cmd_score)
```

- [ ] **Step 4: Run the suite.** All pass.
- [ ] **Step 5: Commit and push** with the message "gate: plan-read and prose-read checkpoint scoring".

---

### Task 8: `plan.py`, the plan structure check

**Files:**
- Create or complete: `pbw_romance/plan.py`, `tests/test_plan.py`
- Modify: `pbw_romance/cli.py` (the `check-plan` command)

**Interfaces:**
- Consumes: `paperbackwriter.plan` (`check_plan`, `FIXED`, `WORD_CAP`) and its exact error format, `"Missing <name>"`.
- Produces:
  - `FIXED = ("01_couple_and_resolution.md", "02_world_and_period.md", "02b_beats.md", "03_cast.md", "canon.md", "audit.md")`;
  - `check_plan(root: Path, n_chapters: int = 24) -> dict`.

- [ ] **Step 1: Write the failing tests** in `tests/test_plan.py`

```python
from pbw_romance.cli import main
from pbw_romance.plan import FIXED, check_plan


def test_an_empty_plan_reports_the_romance_files_not_the_mystery_ones(tmp_path):
    errors = check_plan(tmp_path)["errors"]
    for name in FIXED:
        assert f"Missing {name}" in errors
    assert not any("solution_and_suspects" in e or "02b_clues" in e for e in errors)


def test_an_oversized_plan_file_is_an_error(tmp_path):
    (tmp_path / "02b_beats.md").write_text("word " * 2100)
    assert "02b_beats.md must contain fewer than 2,000 words" in check_plan(tmp_path)["errors"]


def test_the_parent_still_reports_missing_outlines_and_brief(tmp_path):
    errors = check_plan(tmp_path)["errors"]
    assert "Missing chapter outline files (0N_chapters_*.md)" in errors and "Missing writer brief" in errors


def test_check_plan_command(tmp_path):
    assert main(["check-plan", str(tmp_path)]) == 1
```

- [ ] **Step 2: Run them and watch them fail.**

- [ ] **Step 3: Implement `pbw_romance/plan.py`** (keep `FIXED` if Task 7 created it)

```python
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
```
CLI:
```python
def cmd_check_plan(a):
    from .plan import check_plan
    return _print(check_plan(Path(a.plan), a.chapters))
```
```python
    s = sub.add_parser("check-plan", help="structure check of a plan folder (no spoilers printed)")
    s.add_argument("plan"); s.add_argument("--chapters", type=int, default=24)
    s.set_defaults(func=cmd_check_plan)
```

- [ ] **Step 4: Run the suite.** All pass.
- [ ] **Step 5: Commit and push** with the message "plan: romance plan structure check".

---

### Task 9: `calibrate.py`, importing *Persuasion*

**Files:**
- Create: `pbw_romance/calibrate.py`, `tests/test_calibrate.py`
- Modify: `pbw_romance/cli.py` (the `import-reference` command)

**Interfaces:**
- Consumes: `pbw_scifi.calibrate.write_chapters(chapters, out_dir) -> int`.
- Produces: `split_gutenberg(text: str) -> list[tuple[int, str, str]]`, which handles untitled `CHAPTER I.` headings. The title is the Roman numeral.

- [ ] **Step 1: Write the failing test** in `tests/test_calibrate.py`

```python
from pbw_romance.calibrate import split_gutenberg
from pbw_romance.cli import main

SAMPLE = ("Header\r\n*** START OF THE PROJECT GUTENBERG EBOOK PERSUASION ***\r\n\r\n"
          "Contents\r\n\r\n CHAPTER I.\r\n CHAPTER II.\r\n\r\n"
          "CHAPTER I.\r\n\r\n\r\nSir Walter Elliot, of _Kellynch_\r\nHall, was vain.\r\n\r\nHe read.\r\n\r\n"
          "CHAPTER II.\r\n\r\n\r\nMr Shepherd spoke.\r\n\r\n"
          "*** END OF THE PROJECT GUTENBERG EBOOK PERSUASION ***\r\nLicence")


def test_untitled_chapters_split_and_the_contents_are_skipped():
    assert split_gutenberg(SAMPLE) == [
        (1, "I", "Sir Walter Elliot, of *Kellynch* Hall, was vain.\n\nHe read."),
        (2, "II", "Mr Shepherd spoke."),
    ]


def test_import_reference_command(tmp_path):
    src = tmp_path / "pg105.txt"
    src.write_text(SAMPLE)
    assert main(["import-reference", str(src), str(tmp_path / "out")]) == 0
    assert (tmp_path / "out" / "ch02.txt").read_text() == "Chapter 2: II\n\nMr Shepherd spoke.\n"
```

- [ ] **Step 2: Run it and watch it fail.**

- [ ] **Step 3: Implement `pbw_romance/calibrate.py`**

```python
"""Import an untitled-chapter Project Gutenberg novel (Persuasion, #105) as chNN.txt files.

The sci-fi importer reads the line after each heading as a chapter title; Austen's
chapters have none, so the title is the Roman numeral and the prose starts at once.
Contents lines are indented in the Gutenberg text and so don't match the heading.
"""
from __future__ import annotations

import re

HEADING = re.compile(r"(?m)^CHAPTER ([IVXLC]+)\.?\s*$")


def split_gutenberg(text: str) -> list[tuple[int, str, str]]:
    text = text.replace("\r\n", "\n")
    start, end = text.find("*** START OF"), text.find("*** END OF")
    body = text[text.find("\n", start) + 1: end if end != -1 else None]
    marks = list(HEADING.finditer(body))
    out = []
    for i, m in enumerate(marks):
        chunk = body[m.end(): marks[i + 1].start() if i + 1 < len(marks) else len(body)]
        paras = [" ".join(p.split()) for p in re.split(r"\n\s*\n", chunk) if p.strip()]
        prose = "\n\n".join(re.sub(r"_([^_]+)_", r"*\1*", p) for p in paras)
        out.append((i + 1, m.group(1), prose))
    return out
```
CLI:
```python
def cmd_import_reference(a):
    from pbw_scifi.calibrate import write_chapters
    from .calibrate import split_gutenberg
    n = write_chapters(split_gutenberg(Path(a.source).read_text(encoding="utf-8")), Path(a.out))
    print(f"wrote {n} chapters to {a.out}")
    return 0
```
```python
    s = sub.add_parser("import-reference", help="untitled-chapter Gutenberg .txt -> chNN.txt files")
    s.add_argument("source"); s.add_argument("out")
    s.set_defaults(func=cmd_import_reference)
```

- [ ] **Step 4: Run the suite, then the real import.** All tests pass. Then:
```bash
curl -s https://www.gutenberg.org/cache/epub/105/pg105.txt -o /tmp/pg105.txt
~/venvs/pbw-romance/bin/paperbackwriter-romance import-reference /tmp/pg105.txt calibration/persuasion/chapters
```
Expected: `wrote 24 chapters`. The `calibration/` folder goes in the **books** repo, not this one; *Persuasion* is public domain, but the book text stays out of the engine repo.
- [ ] **Step 5: Commit and push** with the message "calibrate: untitled-chapter Gutenberg import (Persuasion)".

---

### Task 10: The method: skill, prompts, templates, docs. Tag `engine-v0.1`

**Files:**
- Create: `.claude/skills/writing-romance-novels/SKILL.md`, `plan-files.md`, `blind-read.md`, `writer-brief.md`; `templates/STATUS.md`; `CALIBRATION.md`; `JOURNAL.md`
- Modify: `README.md` (commands table), `howitisbuilt.md`

- [ ] **Step 1: SKILL.md.** It carries:
  - the stage table: intake, bible, plan, plan read, draft, prose read, one fix pass, proofread, final read and release, record;
  - the eight "rules that outrank the stages" from spec §4, verbatim;
  - the stop rules;
  - the model roles;
  - where the files go (the books repo layout from spec §2);
  - the commands, in stage order:
    - `check-plan`, `beats`, `pointers` on the skeleton, `gate` (×5);
    - after drafting: `heat`, `period`, `exposition` and `pointers`;
    - `check-read` and `score` (×5), and `verdict`;
    - the release gate, which requires all of them.
- [ ] **Step 2: plan-files.md.** One section per file in `FIXED`, plus `04_chapters_*.md` and `reader/digest/`:
  - `01_couple_and_resolution.md`: what it holds, including the `Uses beats:` line;
  - the beat-table format;
  - the hiding rules: three decoy ways back, each way-back beat with a job in a wrong way back or placed after ch 17, and cause and cure sharing nothing;
  - the sourced period constraints in `02_world_and_period.md`;
  - the `reference.json` schema from Task 7.
- [ ] **Step 3: blind-read.md.** The reader prompt is fixed text, used verbatim for every read. It gives:
  - the role ("a reader who loves sweet historical romance and has never seen this book");
  - "Released now: chapters X to Y";
  - the log schema from Task 5, with the instruction to quote exactly and cite the chapter;
  - the rule that the way-back list starts at ch 12 and covers every route the reader can imagine, probabilities summing to 1;
  - sparks tagged by the lead's name;
  - at 24, `verdict.json` with the Task 6 keys plus `obvious_at` (the chapter where the way back became obvious), `hea`, and one paragraph per score.

  It also gives the three grader prompts, each with a schema from Task 6:
  - **clarity**, at 7;
  - **obstacle**, at 12 and 17: "is the obstacle the reader names an inner wound or false belief from the plan's file 01, true or false";
  - **rank**, at 12 and 17: "the 0-based position in the log's `ways_back` of the plan's intended way back, or null".
- [ ] **Step 4: writer-brief.md and templates/STATUS.md.**
  - The writer brief covers POV per chapter from the skeleton, the canon file, logging inventions, no narrator winks, sweet heat, the banned list, and one chapter per Write call.
  - The STATUS template is a row per stage: date, book, stage, scores, tag.
- [ ] **Step 5: CALIBRATION.md, JOURNAL.md, README.**
  - CALIBRATION gets the first row: "Initial gates from the spec", with the pass bars from Global Constraints.
  - JOURNAL gets a dated entry.
  - The README lists the commands and exit codes.
  - `howitisbuilt.md` gets the engine section: what was built, how it reuses the parents, and the M2 and M8 fixes carried over from the sci-fi review.
- [ ] **Step 6: Run the suite and a spoiler scan, then commit, tag `engine-v0.1` and push.**
```bash
~/venvs/pbw-romance/bin/python -m pytest -q
~/venvs/pbw-romance/bin/python -m pbw_romance spoilers --terms <private terms>
git tag -a engine-v0.1 -m "engine-v0.1: romance checks and method, before calibration" && git push && git push origin engine-v0.1
```

---

### Task 11: The calibration read of *Persuasion*

**Files (books repo):** `calibration/persuasion/chapters/` (from Task 9) and `calibration/persuasion/blind_read/<date>/`
**Files (engine repo):** `CALIBRATION.md`, `howitisbuilt.md`, `JOURNAL.md`

- [ ] **Step 1:** Write `calibration/persuasion/reference.json`. The leads are A = Anne / Miss Elliot / Anne Elliot and B = Wentworth / Captain Wentworth / Frederick. The dark moment is the chapter where Anne believes Wentworth is lost to Louisa; read it off the text and record the chapter number. The plan hashes are not applicable here, so use a calibration-only reference without `plan_sha256`, and score with `check-read` plus graders by hand.
  - **Ruling for the ledger:** the calibration read uses `check-read` and `verdict` only, not `score`, because a public-domain book has no plan to hash.
- [ ] **Step 2:** Stage chapters 1–7 with `paperbackwriter stage`.
  - Start a fresh Opus reader with the blind-read prompt verbatim. Continue it with SendMessage at 12, 17, 21 and 24.
  - At each checkpoint, run `check-read` and graders for clarity at 7, obstacle at 12 and 17, and rank at 12 and 17. The graders use a short hand-written key for Austen: Anne's want, wound and false belief; Wentworth's; and the way back, which is the letter.
- [ ] **Step 3:** Run `heat` (expect 0), `period` with an empty list (no-op), and `calibrate-threshold`.
- [ ] **Step 4:** Record the results in CALIBRATION.md:
  - the exposition threshold;
  - whether a classic clears the 7s (if Persuasion scores under 7 on prose or chemistry, the bar is too high for this reader, so lower it to the classic's score minus 1 and note why);
  - whether the hidden-at-12 and ≤ .35-at-17 bars are passable. For a book whose ending readers half-know, record the values; don't move the bar.
  - the want, sure and sparks curves.
- [ ] **Step 5:** Write the calibration section of `howitisbuilt.md`, spoiler-free (Austen's plot is public, so naming the letter is fine). Commit and push both repos.

---

### Task 12: Series bible and Book 1 (builds the engine). Tag `engine-v1`

The stages are the same as the sci-fi Book 1, with romance gates. The books repo holds `series/<slug>/SERIES_BIBLE.md`, `BANNED.txt` and `book1/…`. Tag every iteration: `b1-bible-v1`, `b1-plan-vN`, `b1-planread-vN-pass|fail`, `b1-draft-1`, `b1-read-N`, `b1-fix-1`, `b1-proof`, `b1-final-read`, `b1-release`.

- [ ] **Step 1: Bible.**
  - Choose the place and year: a real small place in a real period, sweet tone, and a three-book linked-series shape.
  - Write the banned list in `BANNED.txt`.
  - Source the period constraints.
  - Add every character and place name to `private/spoiler_terms.txt`.
  - Tell the author the place and year only.
- [ ] **Step 2: Plan v1.** Write the files one per turn, each under 2,000 words. Then:
  - **fact-check every constraint the obstacle rests on** against a source, before any read;
  - run `check-plan`, `beats`, and `pointers` on the skeleton text;
  - write `reference.json` and the digest (`paperbackwriter reader`, `paperbackwriter digest`).
- [ ] **Step 3: Plan read.** A fresh Opus reader works on the digest. Score with `gate` at 7, 12, 17, 21 and 24, with graders. A fail means redesign the plan, version it, and run a new read in a new folder. Each read's lesson goes in `notes_from_reads.md`.
- [ ] **Step 4: Draft.** Sonnet agents write chapters 1–5, 6–10, 11–15, 16–20 and 21–24 in order from `WRITER_BRIEF.md`. Between agents, strip decoration off planted lines. Then run `heat`, `period`, `exposition --threshold <calibrated>` and `pointers`.
- [ ] **Step 5: Prose read 1.** Stage with `paperbackwriter stage`. A fresh reader; `check-read` and `score` at each checkpoint, then `verdict`.
- [ ] **Step 6: One fix pass.** Shared decisions go in a single order list. Parallel Sonnet agents make exact-string edits by chapter group. After the fix pass, run prose read 2.
- [ ] **Step 7: Proofread.** A fresh Opus agent reports hard errors only. Write `proof_fixes.json`, do a dry run, then `paperbackwriter proof`.
- [ ] **Step 8: Final read and release.** A fresh read of the exact text. Export with `paperbackwriter export … --author "PaperbackWriter-Romance (validation build)"` to EPUB, PDF and RTF, then make a GitHub release on the **private** repo.
- [ ] **Step 9: Freeze.** Every engine or method change made during Book 1 must already be a CALIBRATION.md row. Tag `engine-v1`. Write the `howitisbuilt.md` sections and JOURNAL entries for each stage, with scores and stages only. Log the milestone to memory.

---

### Task 13: Book 2 on the frozen engine

- [ ] **Step 1:** Confirm `git diff engine-v1 -- pbw_romance .claude templates` is empty. It must stay empty until Book 2's release.
- [ ] **Step 2:** Run Task 12, Steps 1–8, for Book 2:
  - new couple, same place;
  - Book 1's couple stays in the background;
  - Book 2's reader has never read Book 1.
- [ ] **Step 3:** In JOURNAL.md and `howitisbuilt.md`, add a Book 1 vs Book 2 table: overall, earned, chemistry, hidden at 17, obvious at, want and sure curves. Then give the validation verdict.
- [ ] **Step 4:** The final whole-branch review and its one fix pass, per the executing-plans skill.
