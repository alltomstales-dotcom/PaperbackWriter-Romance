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
