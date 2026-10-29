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

    a = p.parse_args(argv)
    try:
        return a.func(a)
    except (ValueError, FileNotFoundError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
