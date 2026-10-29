# How PaperbackWriter-Romance is built

A running history of the build: what was tried, what the gates found, and what changed because of it. Plot never appears here; the books are read cold.

## 2026-10-29 · Starting from what sci-fi taught

The sci-fi engine finished its two-book validation the same day. Its second book hid its solution in all three blind reads, on a frozen engine, because of three plan rules each bought with a first-book failure. The romance engine starts with those rules instead of rediscovering them:

- **Hide the answer like a culprit.** In romance the "answer" is the way back from the dark moment. It shares the page with at least three other plausible ways back, and each of its pieces does a job for a wrong one.
- **The cause and the cure share nothing.** What breaks the couple apart plays no part in mending it.
- **No narrator winks**, checked by machine on the skeleton as well as the prose.

Two more lessons go in before any plot exists:
- **The spoiler scan ships on day one.** The sci-fi build leaked solution terms into its own public history and only a final review caught it.
- **The facts the obstacle rests on get checked before the plan read.** In sci-fi a single wrong number survived from the first plan to the release.

The author chose the target: historical, sweet (closed door), and a linked series with a new couple in each book. The calibration book is Austen's *Persuasion*, which is all three.

## 2026-10-29 · The engine, in nine test-first steps

The author approved the spec the same morning. The build plan has thirteen tasks: nine build the engine, one writes the method, and three run the calibration read and the two books. Each engine task started as a failing test.

**What the engine reuses, and what it adds.** Staging chapters, building the reader-safe digest, proofreading and export come from the mystery engine, pinned at v0.1.0. The three genre-neutral checks come from the sci-fi engine, pinned at engine-v1.1: long exposition runs, narrator pointers, and the spoiler scan. The romance engine adds:
- **Growth beats** (`beats`). This is fair play for romance. The way back from the dark moment may use only change the reader has watched happen, by 75% of the book. It's the sci-fi rules table re-keyed, including the strict row parser the sci-fi review demanded.
- **Heat** (`heat`). The sweet label checked by machine. Period prose says "bosom friend", "the breast of the hill" and "the naked eye", so the patterns exclude those senses rather than banning words.
- **Period** (`period`). Anachronisms, against a banned list the series bible owns.
- **The romance reader log.** At each checkpoint the reader says:
  - what keeps the couple apart, and whether one honest conversation would fix it;
  - how much they want the couple together, and, as a separate number, how sure they are it will happen;
  - from chapter 12, every way back they can imagine, with probabilities;
  - the moments of chemistry, quoted and tagged with whose point of view they're in.
- **Graders.** A fresh grader agent decides what code can't: whether the obstacle the reader names is inner, and which of the reader's routes is the intended way back. Every grader file is read strictly. The sci-fi review found that a gate which is quiet on bad input looks exactly like a gate that passed.
- **Two kinds of read.** A plan read gates on clarity, the obstacle and hiding. A prose read adds chemistry in every batch, and investment: want rising, and sure falling at the dark moment.

Two of the sci-fi review's deferred minors are built in from the start. The plan-read gate refuses to keep scoring after a failure, and it refuses a reference whose plan hashes miss a plan file. The suite has 78 tests.

**First numbers from the calibration book.** *Persuasion* imports as 24 chapters and 83,305 words. The narrator-pointer check finds nothing in Austen, which is what a check for planner winks should find in a classic. The heat check finds one hit: "making love", in Austen's sense of courting. Exposition runs are long: the 90th percentile is 548 words, against 225 for the sci-fi reference. Both findings go to the calibration read.

## 2026-10-29 · Calibration: what *Persuasion* says a 7 means

A fresh Opus reader read Austen's *Persuasion* under the full romance protocol. It got the chapters in five staged batches, wrote a log at each checkpoint, and graders scored those logs. All 163 quotes were found in their chapters. The reader recognised the book, as expected for a model, and was told to judge only from the page. So the scores are usable anchors, and the hiding numbers are soft.

**Scores:** overall 9, earned 8, chemistry 8, prose 9, character 9, satisfying 9. The classic clears every bar of 7 by one or two points, so the bars stay at 7.

**What the read changed:**
- **Exposition threshold: 400 words.** The usual rule takes the calibration book's 90th-percentile run. For Austen that's 548 words, which would have let through two of the four long narration passages this reader actually skimmed: a guidebook paragraph about the scenery, a list of a character's pleasures, a long letter, and summary piled on summary. All four ran 404 words or more, so the threshold sits at 400. The other skims were long speeches inside dialogue, which the check doesn't measure yet.
- **The obstacle in the plan must be true on the page now.** The clarity check failed the classic, and the fault was mine. My grader key said the family's pride still stood between the couple at chapter 7. On the page it barely does: he's rich now, and her family is cutting back. The reader was right, and the grader marked the correct reading "wrong". So the plan's statement of the outside obstacle has to describe chapter 7, not the backstory.
- **Chemistry per lead needs both points of view.** Austen tells it all from Anne's side, so every spark is hers. Our books alternate, so the check stands.

**What the classic couldn't test.** The reader's want rose almost steadily, 7, 8, 7, 9, 10, and sure moved with it. Sure fell once, when the hero was offstage, not at a break. *Persuasion* has no dark moment in our sense, so the "sure falls at the dark moment" check is untested here, not proven wrong; Book 1 will be its first test. Austen's ending was plain three chapters before its turn. Our books aim for one.
