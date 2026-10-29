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
