# Report: step 10at, the export reads one latest attempt

Claude Code, 2026-09-16. Worked from
`PROMPT_claude_code_2026-09-16_export_latest_attempt.md`. Step 10at of
`2026-07-25_BUILD_STATUS.md`, amendment 413 of `2026-07-25_CONSOLE_DESIGN.md`,
Paul's decision of 2026-09-13 closing outstanding item 126.

**`2026-07-25_BUILD_STATUS.md` was not touched.** Rule 1 of the brief. Nothing
in this change marks the step built.

**Files changed:** `export_bookkeeping.py`, and `tests/test_export_latest_attempt.py` added.
**Commit:** proposed at the end, not made. Waiting for a yes.

---

## 1. What SQLite's documentation says about bare columns, and which case this was

**Read from the source, not from the brief.** `https://www.sqlite.org/lang_select.html`
section 2.5, "Bare columns in an aggregate query", fetched and read whole on
2026-09-16. Three sentences decide it, quoted verbatim:

> If there is exactly one min() or max() aggregate in the query, then all bare
> columns in the result set take values from an input row which also contains
> the minimum or maximum.

> If there are two or more min() or max() aggregates in the query, then bare
> column values will be taken from one of the rows on which one of the
> aggregates has their minimum or maximum value. The choice of which min() or
> max() aggregate determines the selection of bare column values is arbitrary.
> The choice might be different for different bare columns within the same
> query.

And from section 2.5.1, Notes:

> If the aggregate is composed from one or more input rows, then a bare column
> will take on the value of an arbitrary row from the aggregate's input. The
> particular row chosen might change from one invocation to the the next.

**The old query held three min/max aggregates**, `MIN(e.extracted_at)`,
`MAX(e.validation_status)` and `MAX(e.validation_notes)`, so it was squarely in
the second case. The documentation guarantees nothing about which row the six
bare columns came from, and explicitly permits different bare columns in one
query to come from different rows.

### Arbitrary-but-consistent, or genuinely mixed? Both, in different senses

The brief asked which it is, and the honest answer needs the question split.

**Across the columns of one exported row, it was genuinely mixed**, and that is
the defect. Measured on Python 3.14.2 with SQLite 3.50.4, over a fixture of one
receipt with three attempts:

| attempt | extracted_at | supplier | status | notes |
|---|---|---|---|---|
| E1 | 09:00 | FIRST SUPPLIER | ok | aaa notes |
| E2 | 10:00 | MIDDLE SUPPLIER | needs_review | zzz notes |
| E3 | 11:00 | LATEST SUPPLIER | failed | mmm notes |

The old query exported, in one row: `supplier_name` and the amounts from **E2**,
`first_extracted_at` from **E1**, `latest_validation_status` `'ok'` from **E1**,
and `latest_review_reason` `'zzz notes'` from **E2**. One CSV row describing two
different attempts, with a status from a third source. No attempt in that
receipt's history ever read what that row says.

**For which row the bare columns came from, it was arbitrary but repeatable on
this build.** In the real query and in a reduced two-row case, the bare columns
tracked the **last** min/max in the select list, which here was
`MAX(e.validation_notes)`. Reordering the aggregates in the reduced case moved
the bare columns to the other aggregate's row. **That is an observation of one
SQLite build, not a rule**: the documentation calls the choice arbitrary and
says it "might change from one invocation to the the next", so nothing should
be built on it, and this report does not.

**So the practical statement is this.** Today's export took supplier, dates and
amounts from whichever attempt had the alphabetically greatest
`validation_notes`. That is neither the first attempt nor the latest, except by
coincidence.

### It has already bitten, on the live database

Both queries run read-only against `C:\Intellibills\db\receipts.db` on
2026-09-16, and the outputs compared row by row. 35 receipts, 40 extractions, 6
receipts with more than one attempt, 4 with none.

**Row order is identical and 5 of the 35 rows change values.** Three of them
change `gross_amount` from empty to a figure:

| receipt | what changes |
|---|---|
| `64bd03c7` | `gross_amount` `None` -> `7.5` |
| `a587b166` | `gross_amount` `None` -> `27.5` |
| `a96ab8f7` | `net_amount` `138.46` -> `248.33`, `gross_amount` `None` -> `248.33` |
| `abe4a034` | `invoice_date` `None` -> `'0026-08-30'` |
| `ad870481` | `invoice_date` `None` -> `'2026-09-06'`, `net_amount` `10.0` -> `None`, `vat_amount` `2.5` -> `None` |

All five are receipts a person corrected in Desktop after a failed first read.
The old export was carrying the **failed** attempt's figures, so the single most
important column in a bookkeeping export, the gross, was blank on three receipts
that have a gross.

**`latest_validation_status` changes on none of the 35.** Counted directly: the
number of receipts where `MAX(validation_status)` differs from the latest
attempt's status is **0** today. So on this machine, so far, the sorting fault
has not yet produced a wrong status and the bare-column fault has produced five
wrong rows. Both are fixed; only one had bitten.

---

## 2. The real value set of `extractions.validation_status`

**It is four values, and I got this wrong first and am disclosing it rather than
quietly correcting it.**

My first enumeration walked the syntax tree of the 57 production files for calls
to `save_extraction()`, which is the only writer: `worker/database/schema.py`
declares no CHECK constraint on the column, so the set comes from the writers and
not from the schema. **The brief said to read the permitted values out of
`schema.py`; they are not there, and that is a small fault in the brief rather
than something to work around.**

Nine call sites, enumerated from the tree:

| file | line | function | `validation_status` |
|---|---|---|---|
| `app.py` | 1313, 1404 | `_retry_failed_receipts` | `'failed'` |
| `app.py` | 1669, 1904, 2110 | `process_once` | `'failed'` |
| `worker/extraction_pipeline.py` | 321 | `process_extraction_result` | `validation.status` |
| `worker/resolution/service.py` | 1174 | `resolve_receipt` | `validation.status` |
| `worker/resolution/service.py` | 1212 | `resolve_receipt` | `'ok'` |
| `worker/resolution/service.py` | 2271 | `_apply_filed_note` | `'ok'` |

`worker/validation/rules.py` assigns `status` in five places and its whole range
is `ok`, `needs_review`, `failed`. **So the writers say three values, and I wrote
three into the code comment and the test docstring.**

**Then I read the live database and there were four.**
`SELECT DISTINCT validation_status FROM extractions` returned `failed`,
`needs_review`, `ok` and **`possible_duplicate`**.

**Where the fourth comes from, and why enumerating the call sites missed it.**
`process_extraction_result()` in `worker/extraction_pipeline.py` replaces the
validation result's status with `"possible_duplicate"` at lines 311 to 315,
**after** validation and **before** the `save_extraction()` at line 321. So the
value never appears at a call site as a literal and never appears in
`rules.py`. Only the run-time value differs. The other `validation.status` site,
`service.py:1174`, sits inside `if validation.status != "ok"` and takes its
validation straight from `validate()`, so it cannot carry the fourth.

**The lesson, which is CLAUDE.md's own and which I broke.** Enumerating the call
sites answered "what literals are written here", and the question was "what
values can this column hold". They are different questions when a value is
assigned upstream of the call. The live database answered the second one in one
query and I should have run it first.

### Does amendment 413's `ok` example hold?

**Yes, and it understates the problem.** Alphabetically the set orders:

```
failed  <  needs_review  <  ok  <  possible_duplicate
```

- **Amendment 413's example holds.** A receipt whose attempts are `ok` then
  `failed` exports `MAX(...)` = `'ok'`. Demonstrated in
  `LatestAttemptTest::test_the_status_is_the_latest_attempts_and_not_the_kindest`,
  which failed with `AssertionError: 'ok' != 'failed'` before the change.
- **The second pair is worse and amendment 413 does not name it.**
  `possible_duplicate` sorts above everything. A receipt flagged as a possible
  duplicate on its first read, then read again and returning clean `ok`,
  exported `possible_duplicate` for ever. `PossibleDuplicateTest` holds that
  case.
- The ordering is not severity, and it is not severity inverted either. It is
  just the alphabet. Three of the four values happen to run from worst to best,
  and the fourth sits on the end of that for no reason at all.

---

## 3. The tiebreak, and why

**`ORDER BY extracted_at DESC, rowid DESC`. The later-written row wins.**

Three reasons, in the order they weigh:

1. **It is already `capture_report.py`'s tiebreak.** That file sits beside the
   export, reads the same two tables and answers the same question, "which
   attempt describes this receipt", in `receipts_for_client()`. Two files giving
   two answers to one question is how a report and an export come to disagree
   about the same receipt in front of the same operator. This is the reason that
   settles it; the other two only say the choice is sound.
2. **It is the only ordering left that means anything.** When two rows share an
   `extracted_at` to the stored precision, "latest" has no other content than
   "written later", and `rowid` is assigned in insert order. `extractions` has a
   TEXT primary key rather than an INTEGER one, so it is an ordinary rowid table
   and every row has one. `TiebreakTest::test_extractions_is_a_rowid_table`
   asserts that rather than assuming it, because the tiebreak rests on it.
3. **It is stable.** The same data gives the same row on every run.
   `TiebreakTest::test_the_answer_does_not_move_between_runs` runs the query five
   times and asserts one distinct answer.

**How likely is a tie?** `save_extraction()` stamps
`datetime.now(timezone.utc).isoformat()`, microsecond precision, so a tie needs
two writes for one receipt inside one microsecond. **On the live database today
there are zero ties**, counted. That is a reason to make the choice cheap, not a
reason to leave it undefined: an export that reorders itself between two runs
over unchanged data is worse than one that is arbitrarily but stably wrong, and
the cost of removing the possibility is six characters.

---

## 4. The query shape

**A correlated subquery picking the row, joined on the primary key, plus a
scalar subquery for the aggregate. No `GROUP BY` at all.**

```sql
SELECT
    r.receipt_id, r.firm_id, r.client_id,
    e.supplier_name, e.invoice_date,
    e.net_amount, e.vat_amount, e.gross_amount, e.currency,
    r.status,
    (SELECT MIN(extracted_at) FROM extractions
      WHERE receipt_id = r.receipt_id) as first_extracted_at,
    e.validation_status as latest_validation_status,
    e.validation_notes as latest_review_reason
FROM receipts r
LEFT JOIN extractions e ON e.extraction_id = (
    SELECT extraction_id FROM extractions
    WHERE receipt_id = r.receipt_id
    ORDER BY extracted_at DESC, rowid DESC
    LIMIT 1
)
ORDER BY r.created_at DESC
```

**Why this shape and not another.**

- **The join is on `extraction_id`, the primary key**, so at most one extraction
  row can match a receipt. That is what makes one receipt one row without a
  `GROUP BY`, and removing the `GROUP BY` is what removes the bare columns. There
  is now no column in the query that SQLite gets to choose a row for.
- **`LEFT JOIN` is still a `LEFT JOIN`**, so a receipt with no attempt still
  appears with the extraction columns empty. The subquery returns no
  `extraction_id`, the join finds nothing, and the columns are NULL. `NoExtractionTest`
  holds all three halves of that: the row appears, its extraction columns are
  empty, its own columns are not.
- **`first_extracted_at` is a scalar subquery rather than an aggregate.** This is
  the consequence the brief called out: the query needs an aggregate over every
  attempt and one picked row at the same time, and one `GROUP BY` gives only one
  of them. A scalar subquery is the cheaper of the two ways to have both, the
  other being a window function, and it keeps the column's meaning visible in
  four words rather than in a `PARTITION BY` clause. It returns NULL for a
  receipt with no attempts, which is what `MIN()` over an unmatched `LEFT JOIN`
  gave before, so that case is unchanged.
- **It is `capture_report.py`'s shape**, deliberately. One idiom for one
  question across the two files.

**`ORDER BY r.created_at DESC` is unchanged** and `ShapeTest::test_newest_arrival_first`
holds it. **`OUTPUT_DIR = config.EXPORTS_DIR` is unchanged** and its docstring is
untouched; `ExportPathTest` in `tests/test_london_surfaces.py` already held that
and still passes.

**`first_extracted_at` still means first**, per the consultant session's decision
in the brief. I have no disagreement with it to flag. The column is called
*first*, the mutation `first-becomes-latest` below proves a test is holding it,
and the reasoning is written into the file beside the query.

---

## 5. Evidence

### 5.1 Red before green

`tests/test_export_latest_attempt.py` reads the SQL out of
`export_bookkeeping.py`'s syntax tree and runs it against an in-memory database
built from `worker.database.schema.SCHEMA_SQL`. It does not import the script,
because the script does its work at module scope and importing it would open the
database and write a CSV. `ExportPathTest` reads the same file the same way for
the same reason.

**Against the unchanged query, before any edit to `export_bookkeeping.py`:**

```
FAILED tests/test_export_latest_attempt.py::LatestAttemptTest::test_every_column_describes_the_same_attempt
SUBFAILED(column='supplier_name') ...::test_supplier_dates_and_amounts_come_from_the_latest_attempt
SUBFAILED(column='invoice_date')  ...::test_supplier_dates_and_amounts_come_from_the_latest_attempt
SUBFAILED(column='net_amount')    ...::test_supplier_dates_and_amounts_come_from_the_latest_attempt
SUBFAILED(column='vat_amount')    ...::test_supplier_dates_and_amounts_come_from_the_latest_attempt
SUBFAILED(column='gross_amount')  ...::test_supplier_dates_and_amounts_come_from_the_latest_attempt
SUBFAILED(column='currency')      ...::test_supplier_dates_and_amounts_come_from_the_latest_attempt
FAILED tests/test_export_latest_attempt.py::LatestAttemptTest::test_the_review_reason_is_the_latest_attempts
FAILED tests/test_export_latest_attempt.py::LatestAttemptTest::test_the_status_is_the_latest_attempts_and_not_the_kindest
FAILED tests/test_export_latest_attempt.py::TiebreakTest::test_the_later_written_row_wins
10 failed, 11 passed, 12 subtests passed in 0.19s
```

with, among others:

```
E  AssertionError: 'ok' != 'failed'        (the status, amendment 413's example)
E  AssertionError: 'EUR' != 'USD'          (a bare column, from the wrong attempt)
E  AssertionError: 'zzz middle notes' != 'mmm latest notes'
```

**After the change, the same file:** `16 passed, 18 subtests passed in 0.11s`.

**A disclosure about that red run.** It was taken before I found the fourth
`validation_status` value, so it does not include `PossibleDuplicateTest`, which
was written afterwards. That class fails against the old query for the same
reason as the others and I did not re-take the red run to prove it, because
re-taking it means reverting the change. What is quoted above is what was
actually run and nothing more.

### 5.2 Mutations

Run with `tests/mutation_harness.py`, which refuses an anchor that does not match
exactly once, applies to a pristine copy, runs the **whole** suite, restores and
asserts the restore is byte for byte. Driver in the session scratchpad. Each
mutation reports one hunk and two lines, so each changed one place.

**Every mutation was caught, every prose mutation survived, and every reported
failure was in `tests/test_export_latest_attempt.py` and nowhere else.** That
second half is the "and no others do" the standard asks for: no test outside the
new file noticed any of these four changes, which is expected, because nothing
else in the suite reads this query.

| mutation | change | outcome |
|---|---|---|
| `earliest-instead-of-latest` | `extracted_at DESC, rowid DESC` -> `extracted_at ASC, rowid ASC` | **caught**, 14 failures |
| `no-tiebreak` | drop `, rowid DESC` | **caught**, 1 failure |
| `inner-join` | `LEFT JOIN` -> `JOIN` | **caught**, 3 failures |
| `first-becomes-latest` | `MIN(extracted_at)` -> `MAX(extracted_at)` in the scalar subquery | **caught**, 1 failure |
| `prose-only` | reword one comment line | **survived**, as required |

**`earliest-instead-of-latest`** reads the first attempt instead of the last.
`14 failed, 1504 passed, 1 skipped, 1146 subtests passed`:

```
FAILED ...::LatestAttemptTest::test_every_column_describes_the_same_attempt
FAILED ...::LatestAttemptTest::test_the_review_reason_is_the_latest_attempts
FAILED ...::LatestAttemptTest::test_the_status_is_the_latest_attempts_and_not_the_kindest
FAILED ...::PossibleDuplicateTest::test_the_duplicate_flag_does_not_outlive_the_attempt_that_raised_it
FAILED ...::TiebreakTest::test_the_later_written_row_wins
SUBFAILED(column='supplier_name'|'invoice_date'|'net_amount'|'vat_amount'|'gross_amount'|'currency')
       ...::LatestAttemptTest::test_supplier_dates_and_amounts_come_from_the_latest_attempt
SUBFAILED(receipt_id='R_OLD'|'R_MID'|'R_NEW')
       ...::ShapeTest::test_each_row_carries_its_own_receipts_latest_attempt
```

**`no-tiebreak`** is the one the brief asked for by name. It removes only the
tiebreak, so it can be caught by only one thing:
`1 failed, 1508 passed, 1 skipped, 1155 subtests passed`, and the one is
`TiebreakTest::test_the_later_written_row_wins`. **Worth stating plainly: with
the tiebreak gone, SQLite returned the earlier-written of the two tied rows on
this build.** It answered stably and it answered wrongly, which is exactly why a
test that only checked for stability would have passed.

**`inner-join`** is the other one the brief asked for by name.
`3 failed, 1506 passed, 1 skipped, 1146 subtests passed`, all three in
`NoExtractionTest`: the receipt disappears, so the test that it appears fails,
and so do both tests that read its columns.

**`first-becomes-latest`** proves the decision the consultant session took is
actually held rather than merely written down.
`1 failed, 1508 passed, 1 skipped, 1155 subtests passed`, the one being
`LatestAttemptTest::test_first_extracted_at_is_still_the_earliest_of_every_attempt`.

**`prose-only`** rewords one comment line and must not be noticed.
`1509 passed, 1 skipped, 1155 subtests passed`, nothing caught. So no guard in
the suite is reading this file's comments as though they were code, which
matters here because the change added 48 lines of comment above the query.

**An earlier mutation run is not quoted.** I ran all five once before finding the
fourth `validation_status` value, and those results measured a test file without
`PossibleDuplicateTest`. Everything above is the second run, against the files as
committed. See section 7.

### 5.3 The suite

`./.venv/Scripts/python.exe -m pytest -q` from the repository root.

- **After the change, whole suite: `1509 passed, 1 skipped, 1155 subtests passed`.**
  That is the `prose-only` mutation's run, which changes one comment and nothing
  else, so it is the unmutated suite measured at the end of the mutation set. An
  earlier run before `PossibleDuplicateTest` was added read `1508 passed, 1
  skipped, 1155 subtests passed in 126.01s`; the difference is that one test.
- **No baseline run was taken before the change**, deliberately: the suite was
  green on the working tree when this session started and the red run in 5.1 is
  the evidence that matters.
- **After the commit**, re-run because this change adds a file and two source
  guards sweep the git-tracked set by shelling out to `git ls-files`, so
  `tests/test_export_latest_attempt.py` was invisible to them until it was
  tracked. Section 7.1 of the step 10n report is why that is the run that counts.
  **`1509 passed, 1 skipped, 1155 subtests passed in 113.47s`**, same as before
  the commit. Nothing new went red when the file became visible to the guards.

---

## 6. Flags. Not fixed.

### 6.1 `capture_report.py` does not carry this pattern. It is already right.

The brief asked. `receipts_for_client()` at `capture_report.py:199` already uses
the shape this change adopts, down to the tiebreak:

```sql
LEFT JOIN extractions e ON e.extraction_id = (
    SELECT extraction_id FROM extractions
    WHERE receipt_id = r.receipt_id
    ORDER BY extracted_at DESC, rowid DESC
    LIMIT 1
)
```

**No change needed and none made.** It is where I took the tiebreak from.

### 6.2 Three other places pick "the latest attempt" with no tiebreak

Enumerated from a grep for `FROM extractions` and `JOIN extractions` across the
57 production files, `.history\` excluded, then each read:

| where | what it does | risk |
|---|---|---|
| `worker/database/repository.py:372` `get_extraction_for_receipt()` | `ORDER BY extracted_at DESC LIMIT 1` | on a tie, returns either row |
| `worker/database/repository.py:918` and `:920`, in `find_failed_by_version()` | same, twice, over `pipeline_version` | on a tie, either row's version decides whether the receipt is retried |
| `view_receipts.py:28` | same | display only |

**`get_extraction_for_receipt()` is the one that matters**, because it is what
the pipeline uses to decide what a receipt says. **The obvious fix is one clause:
add `, rowid DESC` to each, which is what this change and `capture_report.py`
already do.** Three edits, no behaviour change except on a tie. I have not made
them: they are outside this brief and they touch the pipeline.

### 6.3 `probe_layer5.py` can return two rows for one receipt

`latest_extractions()` at `probe_layer5.py:40` joins on
`WHERE e.extracted_at = (SELECT MAX(e2.extracted_at) ...)` rather than picking a
row. **Two attempts sharing a timestamp both satisfy that**, so that receipt
appears twice. It is a probe script rather than a pipeline path, and there are no
ties in the live data today, so nothing is currently wrong. **The obvious fix is
to use the same `extraction_id = (SELECT ... LIMIT 1)` shape**, which also makes
the four scripts consistent.

### 6.4 The brief points at `schema.py` for a value set that is not there

Rule 2 of the brief invites this. `extractions.validation_status` is declared
`TEXT` with no CHECK constraint, so `worker/database/schema.py` constrains
nothing and the permitted values live in the writers and, as section 2 shows,
partly upstream of them. **The obvious fix is to say so in the place a reader
will look**, which is `worker/database/schema.py`'s comment beside the column:
four values, three from `rules.py` and `possible_duplicate` from
`process_extraction_result()`. One comment, no behaviour. Not made, because
`schema.py` is not in this brief and a comment there is a claim about five other
files that should be asserted rather than written.

### 6.5 An observation, not a defect: the export will now show `0026-08-30`

Receipt `abe4a034`'s latest attempt holds `invoice_date` `'0026-08-30'`. The old
export showed that column empty, because it was reading a different attempt. The
new export shows what the latest attempt actually read. **That is the change
working**, and `unreadable_year()` in `worker/validation/rules.py` already knows
about years like that. Flagged only so the first run of the new export does not
look like a new fault.

---

## 7. Mistakes I made, disclosed

1. **I wrote the value set of `validation_status` as three and it is four.** I
   enumerated the `save_extraction()` call sites from the syntax tree, which was
   the right method for the wrong question, and did not run
   `SELECT DISTINCT validation_status` until afterwards. The wrong figure reached
   the code comment in `export_bookkeeping.py` and the module docstring of the
   test file before I caught it. Both are corrected and both now say where the
   fourth value comes from. Full account in section 2.
2. **The first mutation run predated that correction**, so it measured a test
   file without `PossibleDuplicateTest` and a source file with the wrong comment.
   I re-ran all five against the final files rather than quoting the first run.
   Section 5.2 is the second run.
3. **The red run in section 5.1 does not cover `PossibleDuplicateTest`**, for the
   reason given there. Stated rather than papered over.

---

## 8. Confidence

- **That the change does what the step asks: high.** Not from reading the query
  but from running it: 16 tests over a fixture built from the real `SCHEMA_SQL`,
  five mutations each caught by the tests that should catch them and by no
  others, and a row-by-row comparison of the old and new output against the live
  database.
- **That the value set of `validation_status` is exactly four: high**, and it
  rests on two independent readings that now agree, the writers from the syntax
  tree and `SELECT DISTINCT` against `C:\Intellibills\db\receipts.db`. I state it
  with more confidence than the three-value version precisely because the first
  reading was wrong.
- **That the old behaviour was genuinely mixed rather than merely arbitrary:
  high**, and it rests on the SQLite documentation quoted verbatim in section 1
  plus a fixture showing one exported row carrying values from two attempts.
- **That bare columns on SQLite 3.50.4 follow the last min/max in the select
  list: low, and nothing is built on it.** Two observations, no documentation,
  and the documentation says the opposite may happen.
- **That nothing else reads this CSV: medium, and it is not my reading.** The
  file's own comment says so and I did not re-verify it. It matters because
  column meanings changing is only safe if nothing downstream parses them.

---

## 9. The commit. Made, on Paul's yes of 2026-09-16.

**`8e58eb6` on `feat/console-phase0`, two files changed, 423 insertions, 5
deletions.** Nothing pushed; no branch created. The suite was run again
afterwards and is green, section 5.3.

**Three files were left alone deliberately.** `2026-07-25_BUILD_STATUS.md`,
`2026-07-25_CONSOLE_DESIGN.md` and `CLAUDE.md` are modified in the working tree
by another session and are not this session's to commit. `git status` after the
commit shows them still modified and unstaged.

**Two files are untracked and I have not committed them**, because the brief
asked for one commit: this report, and
`PROMPT_claude_code_2026-09-16_export_latest_attempt.md`. The brief itself is now
spent, so under the spent-files rule it belongs in `archive\`; it has never been
tracked, so `git mv` does not apply and somebody has to decide whether it is
committed first or simply moved.

The message as committed:

```
fix(export): read one latest extraction attempt, not several

export_bookkeeping.py grouped by receipt over an append-only table, so six
columns were bare with three min/max aggregates in the query and SQLite chose
their row arbitrarily, while MAX() on validation_status and validation_notes
sorted text rather than time. One receipt could export a supplier from one
attempt, a gross from another and a status from a third. On the live database
five of 35 rows carried a failed attempt's figures, three of them with an empty
gross.

The picked row is now joined on extraction_id, ordered extracted_at DESC then
rowid DESC, which is capture_report.py's tiebreak over the same two tables.
There is no GROUP BY, so no bare columns remain. first_extracted_at keeps its
meaning and is a scalar subquery over every attempt. The LEFT JOIN, the row
order and OUTPUT_DIR are unchanged.

validation_status holds four values and not three: possible_duplicate is set on
the validation result inside process_extraction_result(), so it appears at no
save_extraction() call site and sorts above every other value under MAX().

Step 10at, amendment 413, Paul's decision of 2026-09-13 closing outstanding
item 126.

Files: export_bookkeeping.py, tests/test_export_latest_attempt.py

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

**That is the message as committed, read back with `git log -1 --format=%B`, not
the one proposed.** The proposal shown to Paul had no `validation_status`
paragraph, because the fourth value was found after the proposal was drafted,
and it carried a `Suggested branch:` line that a commit made on that branch does
not need. **Both differences are mine and are recorded here rather than left for
somebody to notice.**
