# PaperbackWriter-Romance

A sweet historical romance engine for [PaperbackWriter](https://github.com/alltomstales-dotcom/PaperbackWriter), built the same way as [PaperbackWriter-SciFi](https://github.com/alltomstales-dotcom/PaperbackWriter-SciFi): a separate project per genre, validated by writing Books 1 and 2 of a series, with every gate measured by a blind reader who never sees the plan.

Romance readers know the couple ends together. The engine measures what they can't know: what really keeps the couple apart, how much the reader wants them together, and whether the way back from the dark moment stays hidden until it arrives — and still feels earned.

**Status:** engine built (`engine-v0.1`); calibration next. Spec in `docs/superpowers/specs/`, plan in `docs/superpowers/plans/`, history in `howitisbuilt.md`, every gate change in `CALIBRATION.md`.

## Install

```bash
python3 -m venv ~/venvs/pbw-romance
~/venvs/pbw-romance/bin/pip install -e '.[dev]'
```

It pins [PaperbackWriter](https://github.com/alltomstales-dotcom/PaperbackWriter) v0.1.0 (staging, digests, proofreading, export) and [PaperbackWriter-SciFi](https://github.com/alltomstales-dotcom/PaperbackWriter-SciFi) engine-v1.1 (the exposition, pointer and spoiler checks).

## Commands

`paperbackwriter-romance <command>`. Exit codes: 0 pass, 1 a check failed, 2 bad input.

| Command | What it checks |
|---|---|
| `check-plan PLAN` | The plan files exist, each under 2,000 words, outlines and digest cover every chapter |
| `beats PLAN` | The way back uses only growth beats shown by 75% of the book, one claim per beat |
| `heat CHAPTERS` | Sweet label: nothing past a kiss on the page |
| `period CHAPTERS --banned FILE` | No anachronisms from the series' banned list |
| `check-read LOG [--finished]` | A reader's checkpoint log: every quote found in its chapter, scores and probabilities well-formed |
| `gate REFERENCE GATE CHECKPOINT` | Plan read: score a checkpoint, release the next batch only on a pass |
| `score REFERENCE CHECKPOINT` | Prose read: the same, plus chemistry and investment |
| `verdict FILE` | A finished read against the targets, and the happy ending |
| `import-reference SOURCE OUT` | A Project Gutenberg novel with untitled chapters, as `chNN.txt` |
| `exposition`, `pointers`, `spoilers`, `calibrate-threshold` | The sci-fi engine's genre-neutral checks, passed through |

The method (stages, rules, reader and grader prompts) is the skill in `.claude/skills/writing-romance-novels/`.

License: MIT.
