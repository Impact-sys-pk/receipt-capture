# Report: every latest-attempt pick gets the same tiebreak

Claude Code, 2026-09-16. Worked from
`PROMPT_claude_code_2026-09-16_latest_attempt_tiebreaks.md`, which is Paul's
decision of 2026-09-16 on four flags in
`2026-09-16_REPORT_claude_code_export_latest_attempt.md`.

**`2026-07-25_BUILD_STATUS.md` was not touched.**

**Files changed:** `worker/database/repository.py`, `view_receipts.py`,
`check_test41.py`, `probe_layer5.py`, and `tests/test_latest_attempt_tiebreak.py`
added.

**Commit:** proposed at the end, not made.

---

## The headline

**The brief named four. There are five.** `check_test41.py` is the fifth and was
in nobody's list, including my own report that raised the flags. It was found by
enumerating the set from the syntax tree instead of taking it from the brief,
which is what the brief asked for.

---

## 1. The enumerated set, printed whole

**How it was enumerated.** From the syntax tree of every production file,
collecting **string constants only and excluding docstrings**, because a grep for
`extracted_at` returns it from comments and docstrings too, and on this project
superseded wording is kept beside every correction so the prose is always a few
lines away. `CLAUDE.md`, 2026-09-08.

**Concatenated SQL is collected whole as well.** `find_by_transaction_loose()`
builds its query from a triple-quoted head, a shared predicate constant and a
triple-quoted tail, so a pick could span three constants and be invisible to a
per-constant scan. Every `.execute()`, `.executescript()` and `.executemany()`
call has its first argument unparsed whole and checked too.

**Scope:** `app.py`, the root scripts and everything under `worker\`, **57
files**. Not an `rglob` from the repository root, which reaches `.venv\` and
`.history\`; the latter holds a dated copy of every file ever edited and would
report code that no longer exists.

**A pick is** a query mentioning `extractions` that either orders by
`extracted_at DESC` and takes one row, or matches on `MAX(extracted_at)`. That
is the brief's definition and it is the one used.

### Seven picks in production

| # | Where | Shape | Before |
|---|---|---|---|
| 1 | `capture_report.py` `receipts_for_client()` | orders DESC, takes one | **already right**, the pattern |
| 2 | `export_bookkeeping.py` module scope | orders DESC, takes one | **already right**, step 10at |
| 3 | `worker/database/repository.py` `get_extraction_for_receipt()` | orders DESC, takes one | no tiebreak |
| 4 | `worker/database/repository.py` `find_failed_by_version()` | **two** subqueries, each orders DESC and takes one | no tiebreak, twice |
| 5 | `view_receipts.py` module scope | orders DESC, takes one | no tiebreak |
| 6 | `check_test41.py` `main()` | orders DESC, takes one | no tiebreak. **Not in the brief** |
| 7 | `probe_layer5.py` `latest_extractions()` | matches on `MAX(extracted_at)` | different shape |

**Five needed changing**, counting `find_failed_by_version()` once as a function
and twice as subqueries.

### Two that rank but do not pick, left alone

Both order `extractions` by `extracted_at DESC` and return **every** row, so
neither answers "which attempt describes this receipt". They are outside the
brief's definition and are flagged in section 4 rather than changed.

- `query_receipts.py` module scope, the `needs_review` listing.
- `worker/database/repository.py` `get_extractions_for_receipt()`, the whole
  history for the resolution view.

### One in the tests

`latest_manual_extraction()` in `tests/test_resolve_receipt_zero_and_types.py`.
Flagged in section 4, not changed.

### How `check_test41.py` was missed the first time

**It was missed by me, in the report that raised the four flags.** That report's
section 6.2 said "Enumerated from a grep for `FROM extractions` and
`JOIN extractions` across the 57 production files". **The grep was right and the
reading of it was not**: `check_test41.py:42` reads
`FROM extractions WHERE receipt_id = ?` and appears in that grep's output, which
is quoted in full in this session. I listed four files in a table and did not
count the grep's lines against them.

**That is `CLAUDE.md`'s enumerate-the-set rule broken in the exact way it
describes**: the members were verified and the claim that the list was complete
was not, and the tell was the word "the" in front of a plural, "three other
places".

---

## 2. Is `rowid DESC` sound on `extractions`?

**Report question 2, confirmed here and not carried across from step 10at.** Four
questions, each answered against the thing itself on 2026-09-16.

| Question | Answer | How |
|---|---|---|
| Is `extractions` a rowid table? | **Yes** | No `WITHOUT ROWID` in the declaration, read out of `sqlite_master` in a database built from `schema.py`'s own `SCHEMA_SQL` **and** in the live `C:\Intellibills\db\receipts.db` |
| Is `extraction_id` an INTEGER PRIMARY KEY, aliasing the rowid? | **No**, `TEXT PRIMARY KEY` | Same reading, both databases |
| Does the later insert get the higher rowid? | **Yes** | Two rows inserted with one `extracted_at`; rowids 1 then 2, and the tiebreak returned the second |
| Can a rowid be reused? | **No** | Nothing deletes from `extractions`: no `DELETE FROM extractions` in any non-docstring string constant across the 57 production files, and the live table's rowids run **1 to 40 with no gap** |

**That last one is the question step 10at did not ask.** SQLite assigns a rowid as
`max(rowid) + 1`, so a deleted row frees its value and a later insert can take it,
which would break "the later row has the higher rowid". It cannot happen here
because nothing deletes, and the repository's own tombstone records why:
`add_validation_note()` was removed at step 9 precisely because `extractions` is
append-only.

**Two further readings of the live database, both read-only:**

- **Receipts with two attempts sharing an `extracted_at`: 0.** There are no ties
  today, so this change is invisible in current data. That is the brief's point
  rather than an objection to it.
- **Pairs where rowid order and `extracted_at` order disagree: 0**, across all 40
  rows. The two orderings agree everywhere they can be compared, which is what
  you would expect if rowid tracks insert order and `extracted_at` is stamped at
  insert.

---

## 3. Evidence

### 3.1 Red before green, with a real tie

The fixture is one receipt with **two attempts carrying the identical
`extracted_at`** to the stored precision, `2026-09-01T10:00:00.000000+00:00`,
differing in `supplier_name`, `validation_status`, `gross_amount` and
`pipeline_version`. **Without a real tie none of these tests can fail**, and a
test that cannot fail is not a test. Amendment 97.

Against the unchanged code, `10 failed, 2 passed`:

```
FAILED ...::ScriptQueryTest::test_check_test41_shows_the_later_attempt
FAILED ...::ScriptQueryTest::test_view_receipts_shows_the_later_attempt
FAILED ...::RepositoryTest::test_it_returns_the_later_attempt
FAILED ...::AutoRetryTest::test_a_receipt_whose_later_attempt_is_current_is_not_retried
FAILED ...::AutoRetryTest::test_the_earlier_attempts_version_does_not_decide
FAILED ...::ProbeTest::test_a_receipt_with_no_attempt_still_appears
FAILED ...::ProbeTest::test_a_tie_returns_the_receipt_once
FAILED ...::ProbeTest::test_it_is_the_later_attempt
FAILED ...::TheWholeSetTest::test_every_pick_orders_by_extracted_at_then_rowid
FAILED ...::TheWholeSetTest::test_no_pick_matches_on_max_extracted_at
```

**That red covers 12 of the 13 tests.** The thirteenth,
`test_the_is_null_half_of_the_condition_picks_the_later_attempt_too`, was written
after the mutation run and the red was not re-taken, because re-taking it means
reverting four production files. It fails against the unchanged code for the same
reason as its neighbours, and the mutation in 3.3 is the evidence that it bites.
Stated rather than left for somebody to notice the counts differ.

**The two that pass are correct to pass.**
`test_a_receipt_whose_later_attempt_is_stale_is_retried` is true under either
behaviour and is there so its neighbour cannot pass by returning nothing
whatever it is asked. `test_there_is_at_least_one_and_the_guard_is_looking_somewhere`
is the set guard's own check that it is looking anywhere at all.

**After the five changes: `12 passed`.** A thirteenth was added later, for the
reason in section 3.3, so the file now has 13. Whole suite: **`1552 passed, 1
skipped, 1175 subtests passed in 162.42s`**, up from 1539 by the thirteen.

### 3.2 The probe fails differently, and the test says so

`probe_layer5.py` matched on the **value** rather than picking a row, so on a tie
**both** attempts satisfied `WHERE e.extracted_at = (SELECT MAX(...))` and the
receipt came back twice. A tiebreak cannot fix that. It now joins on
`extraction_id`, the primary key, which is `capture_report.py`'s shape.

**`OR e.extraction_id IS NULL` went with it and nothing was lost.** It existed to
keep a receipt with no extraction in the result; a `LEFT JOIN` on a key that
simply fails to match does that on its own.
`test_a_receipt_with_no_attempt_still_appears` holds it, and it was red before the
change for the right reason: the tied receipt appeared twice, so the id list had
three entries instead of two.

**I know the difference between a probe and production**, which the brief asked
me to say. `probe_layer5.py` is a one-off diagnostic that its own docstring tells
you to archive or delete after reading. It is in scope because `main()` prints
`receipts: {len(rows)}` and then makes **one OpenAI call per row**, so a
double-counted receipt is both a wrong number in a report somebody will quote and
a duplicated cost.

### 3.3 Mutations

Run with `tests/mutation_harness.py`, which refuses an anchor that does not match
exactly once, applies to a pristine copy, runs the **whole** suite, restores and
asserts the restore is byte for byte. All seven anchors were counted before the
run rather than discovered by a refusal mid-run.

| Mutation | Outcome | Caught by |
|---|---|---|
| `repository-pick-no-tiebreak` | **caught**, 2 | `RepositoryTest` + the set guard |
| `retry-both-subqueries-no-tiebreak` | **caught**, 3 | two `AutoRetryTest` + the set guard |
| `retry-ONE-subquery-no-tiebreak` | **caught**, 2 | `AutoRetryTest` + the set guard |
| `view-receipts-no-tiebreak` | **caught**, 2 | `ScriptQueryTest` + the set guard |
| `check-test41-no-tiebreak` | **caught**, 2 | `ScriptQueryTest` + the set guard |
| `probe-back-to-matching-on-max` | **caught**, 4 | three `ProbeTest` + the set guard |
| `prose-only` | **survived**, as required | nothing |

**Every failure across all seven is in `tests/test_latest_attempt_tiebreak.py`.**
Nothing else in the 1,552-test suite notices any of them, which is why five
queries could disagree with each other for weeks.

### The one-subquery mutation earned its place, and then changed the tests

**On its first run it was caught by the set guard and by nothing else.**

```
=== retry-ONE-subquery-no-tiebreak ===
last line: 1 failed, 1550 passed, 1 skipped, 1175 subtests passed
caught by 1 reported failure(s):
  FAILED ...::TheWholeSetTest::test_every_pick_orders_by_extracted_at_then_rowid
```

**That mutation had already paid for itself before it ran**, because writing it
is what showed that the first version of the set guard would have passed it: that
version searched for `extracted_at DESC, rowid DESC` anywhere in the query and
`find_failed_by_version()` holds two picks, so one of two was enough. The guard
was strengthened to require **every** `extracted_at DESC` to carry the tiebreak.

**But a guard catching what no behavioural test can is a thin result**, so the
next question was why `AutoRetryTest` missed it. **Because the fixture could not
tell.** That condition has two halves, `IS NULL` and `!= ?`, and with both
attempts carrying a `pipeline_version` the `IS NULL` half answers False whichever
row it picks. The mutation only touched that half.

`test_the_is_null_half_of_the_condition_picks_the_later_attempt_too` was added,
with the earlier attempt's `pipeline_version` set to NULL so the two rows differ
in the thing that half actually tests. **Re-run against the strengthened tests:**

```
=== retry-ONE-subquery-no-tiebreak ===
last line: 2 failed, 1550 passed, 1 skipped, 1175 subtests passed
caught by 2 reported failure(s):
  FAILED ...::AutoRetryTest::test_the_is_null_half_of_the_condition_picks_the_later_attempt_too
  FAILED ...::TheWholeSetTest::test_every_pick_orders_by_extracted_at_then_rowid
verdict: OK: caught, as expected
```

**So the table above is the first run for six of the seven and the second run for
that one**, and the figures quoted for it are the second. The other six were not
re-run: nothing that changed affects them, and saying so is cheaper than
pretending otherwise.

### `probe-back-to-matching-on-max` is the one that shows the shape mattered

Putting `WHERE extracted_at = (SELECT MAX(...))` back fails **four** tests, and
three of them are behavioural: the receipt comes back twice, the supplier is
wrong, and the receipt with no attempt disappears. **The fourth is
`test_no_pick_matches_on_max_extracted_at`**, which exists because a tiebreak
cannot fix that shape and a guard looking only for `, rowid DESC` would have
passed a query that had gone back to it.

---

## 4. Flags. Not fixed.

### 4.1 Two queries rank by `extracted_at` without picking, and a tie leaves their order arbitrary

Both return every row rather than one, so neither is a latest-attempt pick and
both are outside the brief's definition. **A tie still leaves the order of two
rows undefined**, which is a display question rather than a correctness one.

| Where | What a tie does |
|---|---|
| `query_receipts.py` module scope | two `needs_review` extractions for one receipt list in arbitrary order |
| `worker/database/repository.py` `get_extractions_for_receipt()` | the resolution view's attempt history shows two attempts in arbitrary order, and its docstring says "newest first" |

**The obvious fix is the same two words**, `, rowid DESC`, on each. It changes
nothing when there is no tie and makes the displayed order stable when there is.
**Not made**, because the brief's set is picks and these are not picks, and
widening a brief's scope on my own judgement is what the flag rule exists to
stop. **If you want them, they are one line each and the set guard already has
the shape to hold them.**

### 4.2 A test helper picks a latest attempt without the tiebreak

`latest_manual_extraction()` in `tests/test_resolve_receipt_zero_and_types.py`
runs `ORDER BY extracted_at DESC LIMIT 1` over `extractions`. It is test
infrastructure rather than something a user reads, and its own fixture controls
the timestamps, so it cannot be surprised today.

**The obvious fix is the same two words.** **Not made**, because editing a test
the brief does not name risks changing what that test asserts, and I would rather
say so than find out.

### 4.3 Nothing picks a latest attempt by any other means

**Report question 3.** The sweep looked for two shapes, ordering by
`extracted_at DESC` with a `LIMIT 1`, and matching on `MAX(extracted_at)`. **I
also looked for what else could express "the latest" and found none of it**: no
window function anywhere in the repository, no `MAX(rowid)`, no
`ORDER BY extraction_id`, and no Python-side selection of a latest row from a
list of attempts. `get_extractions_for_receipt()` returns the whole history and
its two callers in the resolution service display it rather than pick from it.

**One thing that is not a latest-attempt pick but reads like one**, recorded so
it is not mistaken for a gap later: `export_bookkeeping.py` also carries
`(SELECT MIN(extracted_at) ...)` for `first_extracted_at`. That is deliberately
an **earliest** pick, is an aggregate over every attempt rather than a row, and
step 10at's brief settled that it stays as it is.

---

## 5. Mistakes I made, disclosed

1. **I missed `check_test41.py` when I raised these flags**, in
   `2026-09-16_REPORT_claude_code_export_latest_attempt.md` section 6.2. The grep
   I ran returned it and I did not count the output against the table I wrote.
   Section 1 has the detail. **This is the third time in two days I have written
   a set claim and had it turn out short**, after the `validation_status` value
   set and the email-loop exits.
2. **My first enumeration script double-counted every query.** It collects both
   the unparsed `.execute()` argument and the raw string constant, which is
   deliberate so concatenated SQL is seen whole, and it deduplicated on the text
   with non-alphanumerics stripped. **A repr spells a newline as backslash-n and
   `n` is alphanumeric**, so the two spellings of one query differed by one `N`
   per line and neither collapsed. It reported 15 units where there are 7. Fixed
   by collapsing the escapes before stripping.
3. **The first version of the set guard could be satisfied by half a query.** It
   searched for `extracted_at DESC, rowid DESC` anywhere in the SQL and passed if
   it appeared once, and `find_failed_by_version()` holds **two** subqueries that
   each pick a latest attempt. Removing the tiebreak from one would have passed.
   **Found by writing the mutation that does exactly that**, before running it.
   The guard now counts every `extracted_at DESC` and requires each to carry the
   tiebreak.

**The third is the one worth keeping.** The mutation set found a hole in the test
the mutation set was written to measure, and it found it while being written
rather than when it ran.

---

## 6. Confidence

- **That the set is seven picks and five needed changing: high.** Enumerated from
  the syntax tree over 57 files, printed whole, deduplicated on normalised text,
  and the same set is re-derived independently by `TheWholeSetTest` at every run.
  **My confidence in the method is higher than my confidence in any list I write
  by hand**, which is the point of the guard.
- **That `rowid DESC` is sound: high**, and it rests on four separate checks
  including the one step 10at did not make, that no rowid can be reused.
- **That the change is invisible in current data: high**, from a read-only count:
  zero ties across 40 extraction rows.
- **That nothing picks a latest attempt by other means: medium.** I searched for
  the shapes I could think of and named them in 4.3. **A shape I did not think of
  would not appear in that list**, and the guard only holds the two shapes it
  knows.
- **That the two rank-only queries are display-only: medium.**
  `get_extractions_for_receipt()`'s callers are in the resolution service and I
  read what they do with the list; I did not trace it into IntelliBooks Desktop,
  which is where a resolution view is actually rendered.

---

## 7. The commit. Made on 2026-09-17, on Paul's approval.

**`e4c7435` on `feat/console-phase0`, five files, 493 insertions and 10
deletions.** Nothing pushed, no branch created.

**The suite was run again afterwards**, because this adds a file and two source
guards sweep the git-tracked set rather than the working tree:
**`1552 passed, 1 skipped, 1175 subtests passed in 182.12s`**.

**The work was done on 2026-09-16 and the commit was made on 2026-09-17, and the
date was read off the clock rather than carried forward.** This session ran past
midnight, which is the case `CLAUDE.md` records as having misdated 34 amendments
in one batch. The report's own date, its filename and every "Paul's decision of
2026-09-16" in it are correct as written: those things happened on the 16th. Only
the commit is on the 17th.

**Two docs commits landed overnight from the consultant session**, `75cc486`
marking step 10aj built and `db66081` adding step 10bb for `0982ed9`. Both touch
`2026-07-25_BUILD_STATUS.md` and `2026-07-25_CONSOLE_DESIGN.md` only, checked
before committing, and neither touches anything here.

**One difference from the message proposed below**: none. The `Suggested branch:`
line was already absent from this one.

The message as committed:

```
fix(extractions): one tiebreak for every latest-attempt pick

Five queries picked a receipt's latest extraction attempt without a
tiebreak, so on two attempts sharing an extracted_at they could disagree with
capture_report.py and export_bookkeeping.py, and with each other, about which
attempt describes the receipt. Four were flagged at step 10at; the fifth,
check_test41.py, was found by enumerating the set from the syntax tree rather
than taking the list from the brief.

get_extraction_for_receipt(), which is what the pipeline reads, both
subqueries in find_failed_by_version(), where the answer decides whether a
real OpenAI call is made, view_receipts.py and check_test41.py all now order
extracted_at DESC then rowid DESC.

probe_layer5.py needed its shape changing rather than a tiebreak adding. It
matched on WHERE extracted_at = (SELECT MAX(...)), so a tie satisfied both
rows and the receipt came back twice, which is a wrong count and a duplicated
OpenAI call. It now joins on extraction_id, and the OR extraction_id IS NULL
that kept a receipt with no attempt in the result is no longer needed, because
the LEFT JOIN does that on its own.

extractions is an ordinary rowid table with a TEXT primary key, nothing
deletes from it, and the live table's rowids run 1 to 40 with no gap, so the
later-written row has the higher rowid. There are no ties in the live data
today: this is invisible until there are.

TheWholeSetTest enumerates the picks from the syntax tree and asserts every
ordering carries the tiebreak, because only a guard over the set catches the
sixth one.

Files: worker/database/repository.py, view_receipts.py, check_test41.py,
probe_layer5.py, tests/test_latest_attempt_tiebreak.py

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

**Five files.** The three reports and the `failed_email_moves` brief are
untracked and are not in the commit; this task's own brief was committed by the
consultant session.
