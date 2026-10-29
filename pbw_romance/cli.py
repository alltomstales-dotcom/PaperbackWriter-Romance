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


def cmd_beats(a):
    from .arc import check_beats
    return _print(check_beats(Path(a.plan), a.chapters))


def cmd_heat(a):
    from .heat import report
    hits = report(Path(a.chapters_dir))
    for h in hits:
        print(f"ch{h['chapter']:02d}:{h['line']}  {h['phrase']!r}")
    print(f"{len(hits)} heat hits (sweet label: kissing only)")
    return 1 if hits else 0


def cmd_period(a):
    from pbw_scifi.spoilers import load_terms
    from .period import find_banned
    hits = find_banned(Path(a.chapters_dir), load_terms(Path(a.banned)))
    for h in hits:
        print(f"ch{h['chapter']:02d}:{h['line']}  #{h['pattern']}  {h['match']!r}")
    print(f"{len(hits)} anachronisms")
    return 1 if hits else 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in PASSTHROUGH:
        from pbw_scifi.cli import main as scifi
        return scifi(argv)
    p = argparse.ArgumentParser(prog="paperbackwriter-romance", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("beats", help="earned check: the way back uses only beats shown by 75%%")
    s.add_argument("plan")
    s.add_argument("--chapters", type=int, default=24)
    s.set_defaults(func=cmd_beats)

    s = sub.add_parser("heat", help="sweet-heat lint: nothing past a kiss on the page")
    s.add_argument("chapters_dir")
    s.set_defaults(func=cmd_heat)

    s = sub.add_parser("period", help="anachronism lint against the series' banned list")
    s.add_argument("chapters_dir")
    s.add_argument("--banned", required=True, help="BANNED.txt: one case-insensitive regex per line")
    s.set_defaults(func=cmd_period)

    a = p.parse_args(argv)
    try:
        return a.func(a)
    except (ValueError, FileNotFoundError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
