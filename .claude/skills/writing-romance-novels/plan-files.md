# Plan files

Each file is under 2,000 words, and written in its own turn. `paperbackwriter-romance check-plan` checks that they exist and the cap. `beats` checks fair play.

## 01_couple_and_resolution.md

- **Lead A and lead B:** name, age and station, and for each:
  - **want** (what they're after when the book opens);
  - **wound** (what happened to them);
  - **false belief** (what the wound taught them that isn't true).
- **The external obstacle:** a period fact (law, money, inheritance, duty, distance) that presses on both wounds. It is sourced in file 02.
- **The dark moment:** chapter, cause, and why it hurts.
- **The intended way back:** one paragraph, its means stated plainly (who acts, what changes). It ends with the line `Uses beats: B2, B7, B11`.
- **Three or more decoy ways back.** Each must be plausible on the page, with its own beats or scenes and its own support.
- **The hiding rules, checked here:**
  - What causes the dark moment plays no part in getting past it.
  - Every beat the way back uses either does a job in a wrong way back, or first shows after ch 17.
  - No beat the way back uses is the loudest thing in its scene.

## 02_world_and_period.md

- The place and the year, and what daily life is.
- **Every constraint the obstacle rests on, each with a source:** what a widow could inherit, what a marriage contract needed, what a journey took, how long a letter took, what things cost. These are checked against the source **before the plan read**. In sci-fi, a single wrong number survived from plan to release.
- A pointer to `BANNED.txt` and anything the period forbids on the page.

## 02b_beats.md

A table with one beat per row: `| B4 | one step of change, or one fact the way back needs | ch 11 |`.
- One claim per row (the `beats` check rejects a semicolon).
- Split compound steps as `B4a`, `B4b`.
- Both leads change. A one-sided arc reads as a rescue.

## 03_cast.md

Who is on the page and what each one wants. Include the previous book's couple when there is one: background only, never the plot. Give every decoy way back someone who argues for it.

## canon.md

Names, dates, ages, distances, money, objects, and the weather on the days that matter. Writers obey it and log anything they invent in `invented.md`.

## audit.md

Your own pass before the plan read:
- the hiding rules from file 01, checked line by line;
- `pointers` run on the skeleton text;
- the fact check of file 02, with a source per line;
- the stakes, re-checked: does waiting, or one conversation, solve it?

## 04_chapters_01-12.md and 04_chapters_13-24.md (the skeleton)

Chapter by chapter:
- POV;
- the scene's job;
- the beat it carries, if any;
- the spark: what passes between them.

Use the mystery engine's outline format, so that `paperbackwriter reader` and `paperbackwriter digest` can build the reader-safe digest in `reader/digest/`.

**Strip pointers from the skeleton.** Writers copy a skeleton's similes into prose, and a planner's wink becomes a narrator's wink.

## reference.json (private; never shown to a reader)

```json
{"candidate_directory": ".", "reader_folder": "../blind_read/<date>-plan-vK",
 "leads": {"A": ["first name", "surname", "how others address her"], "B": ["…"]},
 "dark_moment_chapter": 19,
 "plan_sha256": {"<every FIXED plan file>": "sha256"},
 "digest_sha256": {"batch1.md": "sha256", "…": "…"}}
```
`gate` refuses a reference whose hashes don't cover every plan file, and any plan or digest file that changed after the reference was written.
