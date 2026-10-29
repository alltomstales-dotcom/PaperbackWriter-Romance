# Blind read (plan read, prose reads, final read) and the graders

The acceptance test. A reader who does not know the book, and cannot read ahead, writes down at fixed points what keeps the couple apart, how much they want them together, and how they think the couple will find their way back. Every claim carries an exact quote.

## Set-up

- **A fresh agent** on a strong model. It has never seen the plan, the bible's book sections or an earlier draft.
- **Staged release:**
  - For prose: `paperbackwriter stage bookN/chapters bookN/blind_read/<date> <checkpoint>`.
  - For a plan read: `paperbackwriter-romance gate`, which releases the next digest batch on a pass.
  - Later text never exists in the folder early.
- **Checkpoints:** 7, 12, 17, 21 and 24 for 24 chapters.
- **Continue the same reader** with SendMessage at each checkpoint: "Released now: chapters X to Y. Read them in full, write log_chNN.json, then stop."
- **Verify and score every log:**
  - `paperbackwriter-romance check-read <log>`;
  - then `gate` for a plan read, or `score` for a prose read, once the grader files exist.

## Reader prompt (use verbatim)

```
You are a reader who loves sweet historical romance, and an honest editor. You are reading
a novel you have never seen, in batches. You do NOT know how it ends, and the later
chapters do not exist yet on disk, so do not look for them.

The text is in <outdir> (chNN.txt files, or batchN.md outline batches). The first line of
each chapter is its title as a reader sees it. Read everything released so far, in full.

At each checkpoint write <outdir>/log_chNN.json (NN = last chapter read):
{
  "after_chapter": N,
  "apart": {"what": "what keeps these two apart right now, in your own words",
            "one_conversation_fixes_it": true or false,
            "evidence": [{"chapter": n, "quote": "exact words from the text"}]},
  "want": {"score": 1-10, "evidence": [{"chapter": n, "quote": "the line that moved it"}]},
  "sure": 1-10,
  "ways_back": [{"route": "how you think they will get past what keeps them apart",
                 "p": 0.0-1.0,
                 "evidence": [{"chapter": n, "quote": "..."}]}],
  "sparks": [{"pov": "the name of the lead whose point of view this moment is in",
              "chapter": n, "quote": "a moment of chemistry that worked on you"}],
  "skimmed": [{"chapter": n, "quote": "where you started skimming", "why": "..."}],
  "confusion": [{"chapter": n, "quote": "...", "question": "what you could not follow"}],
  "what_gave_it_away": "if you already know how they will get back together, the moments, quoted; else 'nothing yet'",
  "craft_problems": [{"chapter": n, "quote": "...", "problem": "..."}]
}
"want" is how much you want them together. "sure" is how sure you are that they will get
there. They are different numbers. From chapter 12 on, list every way back you can
imagine, at least three if you can; p across them sums to 1. Before chapter 12 the list
may be empty. "one_conversation_fixes_it" is true only if one honest talk between them
would clear the way.
Every quote must be copied exactly from the text. It will be verified by string search,
and an invented quote voids the log. Leave a list empty rather than invent an entry.
Judge honestly: if you can see how it ends, say so and say when you knew.
Then STOP and reply with a two-line summary. The next batch will be released.

After the final chapter also write <outdir>/verdict.json:
{"overall": 1-10, "earned": 1-10, "chemistry": 1-10, "prose": 1-10, "character": 1-10,
 "satisfying": 1-10, "hea": true or false,
 "obvious_at": chapter or null,
 "earned_notes": "did the way back use only change you watched happen? quote the steps",
 "too_late": [{"chapter": n, "quote": "a step or fact that arrived too late"}],
 "top_5_fixes": ["...concrete, with chapter numbers..."],
 "notes": {"overall": "...", "earned": "...", "chemistry": "...", "prose": "...",
           "character": "...", "satisfying": "..."}}
"hea" is true if the book ends with the couple together and happy.
```

For a **plan read**, the reader gets outline batches instead of chapters. Drop `skimmed` and `craft_problems`, since an outline has no prose. Sparks may quote the outline's description of a moment.

## Grader prompts (a separate fresh agent, never the reader)

**Clarity, checkpoint 7.** Give the grader:
- each lead's want, wound and false belief, and the external obstacle, from file 01 as plain sentences;
- the reader's `apart` and the first log's text.

```
Here is what a story has set up for its two leads, A and B: each one's want, wound, and the
obstacle between them. Here is a reader's account after the first chapters. For each item,
say whether the reader's account states it (in any words), misses it, or states it wrongly.
"Stated" means the reader captured its substance; "wrong" only if the reader asserts
something that contradicts it. Do not reward vague statements.
Write <outdir>/grade_ch07.json:
{"items": [{"id": "A.want", "verdict": "stated|missing|wrong", "note": "..."},
           {"id": "A.wound", ...}, {"id": "A.obstacle", ...},
           {"id": "B.want", ...}, {"id": "B.wound", ...}, {"id": "B.obstacle", ...}]}
```

**Obstacle, checkpoints 12 and 17.** Give the grader:
- both wounds and false beliefs from file 01;
- the external obstacle;
- the reader's `apart`.

```
Here are the inner wounds and false beliefs of a story's two leads, and the outside
obstacle between them. Here is what a reader says keeps them apart. Is the reader naming
an inner obstacle (a wound or false belief, in any words), or only the outside one, a
misunderstanding, or a plot device?
Write <outdir>/obstacle_chNN.json: {"inner": true or false, "why": "two sentences"}
```

**Rank, checkpoints 12 and 17 (always).** Give the grader the intended way back (one paragraph, its means stated plainly, from file 01) and the reader's `ways_back` list:

```
Which one of these routes, if any, is the same way back as the one described? "The same
way back" means the route gets its essential means right (who acts, and what changes),
not merely that they reconcile. If none does, answer null; if several do, choose the most
complete one. Never answer with more than one.
Write <outdir>/rank_chNN.json: {"route_index": n or null, "why": "two sentences"},
where n is the 0-based position of the route in the log's ways_back list (the first route is 0).
```

## Targets

| Measure | Target |
|---|---|
| Ch 7 | Clarity: at least 2 of 3 per lead, nothing wrong |
| Ch 12 and 17 | Obstacle inner, and one conversation does not fix it |
| Ch 12 | Intended way back not first (ties count as first) |
| Ch 17 | Intended way back at .35 or less |
| Prose: every batch | At least one spark per lead |
| Prose: ch 12 | Want at least 6 |
| Prose: the dark moment's checkpoint | Want at least 8, and sure lower than at the checkpoint before |
| Verdict | Overall, earned, chemistry, prose, character, satisfying all at least 7; hea true |
| Obvious at | No earlier than one chapter before the turn |

The calibration anchors, which say what a 7 means for this reader, are in `CALIBRATION.md`.

## Reading the result

- "What gave it away" is the finding. The scores only say which stage to go back to.
- **Clarity fails:** a wound is told late or only in backstory. Show it in action in the first act.
- **One conversation would fix it:** either the obstacle is a misunderstanding, or the beliefs have stopped showing.
  - **A misunderstanding:** go back to file 01. An inner obstacle survives the truth being told.
  - **The beliefs have stopped showing:** after the midpoint, every beat weakened a belief and nothing re-confirmed one. Add an event per lead, between the midpoint and the dark moment, in which the belief wins.
- **Way back first at ch 12:** it has all the support, or it was spotlit. Give each decoy a scene and a quote.
- **Want flat:** the sparks are descriptions, not exchanges. Fix the skeleton, not the prose.
- **Sure doesn't fall at the dark moment:** the reader doesn't believe the break. The cause is too small, or it's mended in the same chapter.

Record each read: date, the text read, scores, the checkpoint ranks, and what gave it away. Public files get scores only.
