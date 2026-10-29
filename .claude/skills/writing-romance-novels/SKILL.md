---
name: writing-romance-novels
description: Use when planning, drafting, reading or releasing a sweet historical romance with PaperbackWriter-Romance (blind-read gates on the obstacle, investment, chemistry and the hidden way back)
---

# Writing romance novels

**Core principle:** romance readers know the couple ends together. The suspense is how they get there, and whether the thing keeping them apart is real. Both are designed in the plan and measured by a reader who has never seen it. Prose passes can't add them.

The method is carried over from the mystery and sci-fi engines. The rules below are the ones those engines paid for.

## Where files go (private books repo)

```
series/<slug>/SERIES_BIBLE.md        place, year, series shape, tone; no resolution in it
series/<slug>/BANNED.txt             anachronisms: one case-insensitive regex per line
series/<slug>/bookN/plan/            the plan files (plan-files.md) + reference.json
series/<slug>/bookN/WRITER_BRIEF.md
series/<slug>/bookN/chapters/chNN.txt
series/<slug>/bookN/blind_read/<date>-<what>/   logs, grader files, verdict
series/<slug>/bookN/release/
private/spoiler_terms.txt            every name and resolution term, for the public repo's pre-push scan
```

Tag every iteration in the books repo: `bN-plan-vK`, `bN-planread-vK-pass|fail`, `bN-draft-1`, `bN-read-K`, `bN-fix-1`, `bN-proof`, `bN-final-read`, `bN-release`.

## Stages

| # | Stage | Who | Gate before moving on |
|---|---|---|---|
| 0 | Intake | You and the author | Subgenre, heat and series shape agreed |
| 1 | Series bible | You (Opus) | Place and year told to the author. Names added to the spoiler terms |
| 2 | Book plan | You, one file per turn | `check-plan`, `beats`, `pointers` on the skeleton. **Facts the obstacle rests on, checked against sources** |
| 3 | Plan read | A fresh Opus reader on the digest, plus graders | `gate` passes at 7, 12 and 17 |
| 4 | Draft | Sonnet agents, five chapters each, in order | `heat`, `period`, `exposition`, `pointers` |
| 5 | Prose read | A fresh Opus reader, staged, plus graders | `check-read`, `score` at each checkpoint, `verdict` |
| 6 | One fix pass | Sonnet agents from one order list | Read again |
| 7 | Proofread | A fresh Opus agent | Hard errors fixed by exact-string edits |
| 8 | Final read and release | A fresh Opus reader on the exact text, then export | Every target met, or the misses recorded |
| 9 | Record | You | `howitisbuilt.md`, JOURNAL, CALIBRATION, memory |

## Rules that outrank the stages

1. **The obstacle is inner.** A wound or a false belief keeps them apart, and the external obstacle only presses on it. A reader must be able to say why one honest conversation wouldn't fix it.
2. **Both leads change, on the page, in steps.** Each step is a growth beat in the table. The resolution uses only beats shown by ch 18.
3. **The way back is hidden like a culprit.** It shares the page with at least three other ways back that feel just as likely. Its beats sit inside scenes about something else. Each one also does a job for a wrong way back, or comes after the last hiding checkpoint.
4. **What causes the dark moment plays no part in getting past it.** The cause and the cure share no object.
5. **Chemistry in every batch, for both leads.** A spark is an exchange, not a description of a face.
6. **No narrator winks.** "She didn't know yet how much that would matter" points as hard as a clue in bold. `pointers` runs on the skeleton and on every draft.
7. **Each book stands alone.** Book 2's reader has never read Book 1. The previous couple is background and never carries the plot.
8. **The promise is kept.** A happy ending, sweet heat, and the advertised tropes on the page.

## Stop rules

- A plan read that fails means redesign the plan and read it again. Don't draft.
- One fix pass per book. After it, read again and stop fixing.
- Any edit after a read means the score no longer describes the text. Read again before release.
- After a read, add no piece of the way back before ch 17. Moving one earlier is how the sci-fi Book 1 lost its hiding.

## Commands (`paperbackwriter-romance`)

| Stage | Command |
|---|---|
| Plan | `check-plan PLAN`; `beats PLAN`; `pointers` on a folder of the skeleton text |
| Plan read | `gate REFERENCE GATE CHECKPOINT` after each grader file |
| Draft | `heat CHAPTERS`; `period CHAPTERS --banned BANNED.txt`; `exposition CHAPTERS --threshold <CALIBRATION>`; `pointers CHAPTERS` |
| Prose read | `check-read LOG`; `score REFERENCE CHECKPOINT`; `verdict verdict.json` |
| Every push | `spoilers --terms PRIVATE` (the pre-push hook does it) |

Staging, digests, proofreading and export use the mystery engine's `paperbackwriter` (`stage`, `reader`, `digest`, `proof`, `export`).

## Who does what

| Job | Model |
|---|---|
| Bible, plan, fix orders | Opus (you) |
| Drafting, fix pass | Sonnet agents |
| Readers, graders, proofread | Fresh Opus agents |

Agents die at the output limit with nothing saved. Write one chapter per Write call, and one plan file per turn.

See `plan-files.md`, `blind-read.md` and `writer-brief.md`.
