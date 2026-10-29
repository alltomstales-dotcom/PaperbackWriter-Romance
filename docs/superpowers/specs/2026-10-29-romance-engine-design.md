# PaperbackWriter-Romance: design

Status: draft for the author's review, 2026-10-29.

## 1. Goal

A romance engine for PaperbackWriter: a separate project that plans, gates, drafts and reads a sweet historical romance. It's validated the way the sci-fi engine was: a two-book series, where Book 1 builds the engine and Book 2 runs on it frozen.

The mystery engine measures one reader belief: who did it. The sci-fi engine measures how the central problem gets solved. Romance readers know the couple ends together, because the genre promises it. The suspense is **how they get there, and whether the thing keeping them apart is real.** So the romance engine measures three things:
- what the reader thinks keeps the couple apart;
- how much the reader wants them together;
- which way back from the dark moment the reader expects.

### What the author said

On 2026-10-28:
- A separate child project per genre; leave the mystery engine alone.
- Validate each genre with a pair of books.
- Commit and push as you build, so the history shows the process.

On 2026-10-29:
- "Go for it romance!"
- Historical, sweet (closed door), and the pair is Books 1 and 2 of a linked series with a new couple in each book.
- Document the build in `howitisbuilt.md`.

### Assumed (from the sci-fi run, not restated by the author)

- 24 chapters and 50,000–60,000 words per book.
- Third person, past tense. Point of view alternates between the two leads, by chapter or by scene.
- The author reads cold: no plot in messages or in the public repo.
- Model roles: Opus plans, reads and grades; Sonnet drafts and does the fix pass.
- Byline "PaperbackWriter-Romance (validation build)". Nothing is published without asking.

### Non-goals

- Open-door heat, romantasy, and any subgenre other than sweet historical.
- Changes to the mystery engine or the sci-fi engine.
- Market and listing work (KDP categories, covers). That's the release skill's job, later.

## 2. Architecture

The approach that worked for sci-fi:
- **`PaperbackWriter-Romance`**, a public repo with the code, method and history. It holds no book text and no plot.
- **`PaperbackWriter-Romance-Books`**, a private repo with the series, every plan version, every read and the releases. Each iteration gets an annotated tag.
- The package **`pbw_romance`** depends on two pinned packages:
  - `paperbackwriter` (the mystery engine) at `v0.1.0`, for staging, proofreading and export;
  - `paperbackwriter-scifi` at `engine-v1.1`, for its three genre-neutral checks: `exposition`, `pointers` and `spoilers`.

  Everything romance-specific lives in `pbw_romance`.
- **The cost:** a fix in either parent doesn't reach romance until its pin is raised. That's deliberate, because a frozen engine has to stay frozen while Book 2 is written.

### Repository layout

```
pbw_romance/
  arc.py         the growth-beat list and the "earned" check
  heat.py        heat-level lint (sweet = nothing past a kiss on the page)
  period.py      banned-word (anachronism) lint for the series' period
  reads.py       reader log checks, the gates, grader files
  calibrate.py   reference-book import
  plan.py        plan structure check
  cli.py         paperbackwriter-romance <command>
tests/
.claude/skills/writing-romance-novels/   the method: SKILL.md, plan-files.md, blind-read.md, writer-brief.md
templates/      STATUS.md, plan skeletons
howitisbuilt.md  JOURNAL.md  CALIBRATION.md  README.md
```

## 3. Components

### arc.py: the growth beats, and fair play for romance

Fair play in romance means the way back from the dark moment is earned: it uses only change the reader has watched happen. The plan keeps a table of **growth beats**, one per row:

`| B4 | She admits the debt was hers, not her father's | ch 11 |`

Each row is one step in a lead's change, or one fact the resolution needs, tagged with the chapter where it first shows on the page.

The plan's resolution file has a line `Uses beats: B2, B4, B9`. The check fails if:
- a beat the resolution uses first appears after 75% (ch 18);
- the resolution uses a beat that isn't in the table;
- a beat states more than one claim.

The parser is the engine-v1.1 rules parser re-keyed to `B`. It inherits that version's strict IDs, the near-miss error, and reports that carry IDs and chapter numbers only.

### heat.py: the promise on the label

The label says sweet: kissing on the page and nothing past it. A word and phrase list flags anything explicit, in narration and dialogue alike. Each hit gives chapter, line and the phrase, so the author can see what tripped it. A hit fails the release gate. The list ships with the repo and is tuned during the calibration read.

### period.py: no anachronisms

The series bible holds a banned list for its period: words, objects and ideas that don't exist yet. The check scans the chapters for them. Real facts the plot leans on get a source or are replaced with invented ones. That's the mystery engine's period rule.

**New, from the sci-fi Book 2 lesson.** The constraints the obstacle rests on, such as law, inheritance, money, travel times and the post, get checked against a source **before the plan read**. In sci-fi, one canon number was wrong from the first plan to the release, and only a reader with a calculator found it.

### reads.py: logs, checkpoints and gates

These are the sci-fi engine's mechanics:
- staged batches at chapters 7, 12, 17, 21 and 24;
- quotes verified against the cited chapter by string search;
- the intended answer locked by hashes before the read;
- grader files that are authoritative at the hiding checkpoints;
- every unreadable input refused (engine-v1.1).

The reader's log changes for romance. At each checkpoint the reader records:
- **Apart:** what keeps them apart now, and "would one honest conversation fix it?" (yes or no, with quotes).
- **Want:** how much the reader wants them together, 1–10, with the line that moved it.
- **Sure:** how sure the reader is that they'll get there, 1–10.
- **Ways back:** from 12 on, the ways the couple might get past the final obstacle, with probabilities summing to 1. This is romance's version of the suspect list.
- **Sparks:** moments of chemistry, quoted, for each lead.

### calibrate.py: the reference book

The reference is Austen's *Persuasion* (Project Gutenberg #105): historical, sweet, a second-chance romance in 24 chapters. A fresh reader runs the full romance protocol on it. That tells us what a 7 means, and sets the exposition threshold for this genre before any score is trusted.

### cli.py

`paperbackwriter-romance` with these commands:
- `beats`, `check-plan`, `heat`, `period`, `check-read`, `gate`, `import-reference`;
- `exposition`, `pointers` and `spoilers`, passed through from the sci-fi engine.

Exit codes: 0 pass, 1 check failed, 2 bad input.

## 4. The method

### Plan files (`bookN/plan/`, each under 2,000 words)

| File | Holds |
|---|---|
| `01_couple_and_resolution.md` | The two leads; each one's want, wound and false belief; the external obstacle; the dark moment; the intended way back (`Uses beats:`); at least three decoy ways back, each plausible on the page |
| `02_world_and_period.md` | Place, year, the period constraints the obstacle uses (each sourced), the banned list |
| `02b_beats.md` | The growth-beat table |
| `03_cast.md` | Who's on the page, including the previous book's couple when there is one |
| `04_skeleton.md` | Chapter by chapter: POV, the scene's job, the beat it carries, the spark |
| `05_canon.md` | Names, dates, distances, money, objects. Writers obey it and log anything they invent |
| `reader/digest/` | Reader-safe batch summaries for the plan read |

### Rules that outrank the stages

1. **The obstacle is inner.** A wound or a false belief keeps them apart, and the external obstacle only presses on it. A reader must be able to say why one honest conversation wouldn't fix it.
2. **Both leads change, on the page, in steps.** Each step is a growth beat in the table. The resolution uses only beats shown by ch 18.
3. **The way back is hidden like a culprit.** It shares the page with at least three other ways back that feel just as likely. Its beats sit inside scenes about something else. Each one also does a job for a wrong way back, or comes after the last hiding checkpoint. That's the sci-fi Book 2 rule that made hiding work.
4. **What causes the dark moment plays no part in getting past it.** This is the sci-fi rule "the cause and the cure share no object", carried over.
5. **Chemistry in every batch, for both leads.** A spark is an exchange, not a description of a face.
6. **No narrator winks.** "She didn't know yet how much that would matter" points as hard as a clue in bold. The `pointers` check runs on the skeleton and on every draft.
7. **Each book stands alone.** Book 2's reader has never read Book 1. The previous couple appears as background and never carries Book 2's plot.
8. **The promise is kept.** A happy ending, sweet heat, and the advertised tropes on the page.

### Gates

| When | Gate | Pass bar (draft, set by calibration) |
|---|---|---|
| Plan read, ch 7 | Clarity | The grader finds both leads' want, wound and the external obstacle stated correctly (at least 2 of 3 each, none wrong) |
| ch 12, 17 | Obstacle is real | The reader names an inner obstacle and answers "no" to "would one conversation fix it?" |
| ch 12 | Way back hidden | The intended way back isn't ranked first |
| ch 17 | Way back hidden | Intended way back at .35 or less |
| Across checkpoints | Investment | Want rises or holds: at least 6 by ch 12 and at least 8 at the dark moment. Sure falls at the dark moment |
| Every batch | Chemistry | At least one quoted spark per lead |
| End | Earned, satisfying | Earned at least 7, ending satisfying at least 7, the reader confirms the happy ending |
| Release | Python | `beats`, `heat`, `period`, `exposition`, `pointers` and `spoilers` all pass |
| Blind-read verdict | Scores | Overall, earned, chemistry, prose and character all at least 7 |

The way back must not become obvious before the dark moment. The target is no earlier than one chapter before the turn, as in sci-fi.

### Stop rules (carried over unchanged)

- A plan read that fails means redesign the plan. Don't draft.
- One fix pass per book.
- Any edit after a read means reading again before release.
- After a read, add no piece of the way back before the last hiding checkpoint.

## 5. Validation protocol

1. **Calibration:** the romance protocol run on *Persuasion*. Thresholds go in CALIBRATION.md before Book 1's plan read.
2. **Book 1 builds the engine.** Every gate or method change is a CALIBRATION.md line with its evidence. At release, the engine is tagged `engine-v1`.
3. **Book 2 runs frozen** on `engine-v1`: no code, prompt or method change. If it passes its gates, the engine is validated.
4. **A final whole-branch review** by a fresh Opus reviewer, then one fix pass, as for sci-fi.

## 6. Privacy and the public history

- The spoiler scan and pre-push hook go in on **day one**, before the first plan exists. That's the fix for sci-fi's leak (review C1). The term list lives in the private books repo and grows with each plan: character names, setting names and resolution terms.
- Public docs describe plot only in abstract terms: "the way back used a beat from ch 9", never the beat itself.
- Public commits use the `alltomstales-dotcom` noreply identity.

## 7. Testing

- Test-driven: every check gets a test that fails first.
- Review focus, the inputs most likely to slip past a gate:
  - a grader's free-text answer to the "one conversation" question;
  - a way-back route that blends two decoys;
  - heat words inside a quoted letter or a period phrase;
  - banned words that are also everyday words ("phone" as a sound);
  - a beat table with split IDs.

## 8. Cost

About the sci-fi run's cost:
- one calibration read;
- per book, two or three plan reads, two or three prose reads, one fix pass, one proofread and one final read;
- graders at each checkpoint.

Opus does the reading and grading. Sonnet does the drafting.

## 9. Order of work

1. Repos, scaffold, spoiler scan and hook. First commit.
2. Engine: `arc`, `heat`, `period`, `reads` (the romance log and gates), `plan`, `cli`, each test-first. Tag `engine-v0.1`.
3. Calibration read of *Persuasion*; thresholds recorded.
4. Series bible: setting, period, banned list, the series shape (three linked books, a new couple each). I'll propose the setting and tell you what I chose; you can overrule it without seeing plot.
5. Book 1, in order: plan, plan read, draft, prose reads, fix pass, proofread, final read, release. Then tag `engine-v1`.
6. Book 2 on the frozen engine, the same stages.
7. Final review and fixes. Verdict in JOURNAL.md and `howitisbuilt.md`.
