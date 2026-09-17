# Report: step 10aj, a statement arrives and is filed

Claude Code, 2026-09-16. Worked from
`PROMPT_claude_code_2026-09-16_statement_end_to_end.md`. Step 10aj of
`2026-07-25_BUILD_STATUS.md`, amendment 389 of `2026-07-25_CONSOLE_DESIGN.md`,
Paul's decision of 2026-09-13 closing outstanding item 74.

**`2026-07-25_BUILD_STATUS.md` was not touched.** Rule 1 of the brief.

**Files changed:** `tests/test_statement_end_to_end.py` added. **Nothing else.**
No production code moved, which is the answer to report question 3 and is
expanded in section 4.

**Commit:** proposed at the end, not made.

---

## The headline, before anything else

**The seam works.** A sidecar on disk reaches `file_statement()` carrying what it
needs, and the tax year comes from the end date. Sixteen tests, six mutations.

**And the intake side has a defect the output side does not.** Three branches out
of the statement path leave the file pair sitting in the Receipt Inbox, and two of
them write a fresh copy into `Intellibills\Review\` on **every poll, for ever**.
Three polls, three copies. At a five-minute interval that is 288 copies a day per
stuck statement. Section 5.1, with the measurement. **Flagged, not fixed.**

That is what amendment 389's Why column predicted in as many words: the output
side has had real attention and the input side had had none.

---

## 1. The phone app, read field for field

**Yes, I could read it.** `C:\Users\PDK7\OneDrive - Intellitax Accounting
Limited\Intellibills\PhoneApp\netlify\functions\upload.js`, 166 lines, read whole
on 2026-09-16, along with `index.html` beside it.

**The sidecar is not what `upload.js` computes. It is `meta` passed through.**
Line 147:

```js
const sidecar = Object.assign({}, meta, { client_id: client.client_id, source: "phone" });
```

So every key the phone put in `meta` survives, plus those two. `meta` for a
statement is built at `index.html:405`:

```js
const meta={schema:2,type:"statement",id:newItemId(),platform,week_ending:week,
  captured:new Date().toISOString(),app:APP_VERSION};
```

**Field for field, what a deployed phone would write, against what the test
crafts:**

| Field | `upload.js` / `index.html` | The test fixture | Read by `scan_inbox()`? |
|---|---|---|---|
| `schema` | `2` | `2` | no |
| `type` | `"statement"`, verbatim from `meta` | `"statement"` | **yes**, and it decides |
| `id` | `newItemId()`, `Date.now().toString(36)+"_"+6 random chars` | `"ab12cd_x9"` | no |
| `platform` | one of `uber`, `bolt`, `freenow` | `"uber"` | **yes** |
| `week_ending` | `^\d{4}-\d{2}-\d{2}$`, rejected with a 400 otherwise | `"2026-04-08"` | **yes** |
| `captured` | `new Date().toISOString()` | `"2026-04-09T07:15:00.000Z"` | no |
| `app` | `APP_VERSION`, `"IntelliBooks Receipts v6"` | the same string | no |
| `client_id` | resolved from `clients.json` by `capture_token` | `"CLIENT001"` | **yes** |
| `source` | `"phone"`, hardcoded at line 147 | `"phone"` | **yes** |

**It matches.** Nine fields, same names, same types, same shapes.

**Two things worth recording that I did not expect.**

**One, `type` reaches the sidecar unnormalised.** Line 52 computes
`const type = meta.type === "statement" ? "statement" : "receipt"`, and that
local is used for the **filename** at line 64 and for the validation at 61 to 63.
It is **not** what goes in the sidecar: `Object.assign` copies `meta.type` raw.
So a phone sending `type: "Statement"` would produce a file named `rcpt_...` and
a sidecar saying `"Statement"`. **Both sides then agree it is a receipt**, because
`scan_inbox()` compares exactly, so nothing is wrong, but the two are arrived at
independently rather than from one value. `test_the_comparison_is_exact_and_not_a_case_fold`
pins the pipeline half.

**Two, the platform allowlist is on the phone side only.** `upload.js:61` rejects
anything outside `["uber","bolt","freenow"]` with a 400. `scan_inbox()` and the
statement branch check only that `platform` is truthy, and `file_statement()`
uses it as a **folder name**. Not a defect today, because the only producer
validates. Recorded because the validation lives in a file this repository does
not contain and has never deployed.

**The kept extra fields are deliberate.** `schema`, `id`, `captured` and `app` are
in the fixture although `scan_inbox()` reads none of them. A fixture holding
exactly the keys the reader wants cannot catch a reader that starts wanting a
fifth.

**Never deployed.** Paul has not deployed that function, so nothing has ever put
a real statement sidecar in the inbox. That is why this seam was unproven rather
than merely untested.

---

## 2. The straddling week: which date decides the tax year

**Report question 2, answered with the dates.**

| | Date | `determine_tax_year()` |
|---|---|---|
| Week ending, which is the rule | **2026-04-08** | **2026-27** |
| Period start, which is the other rule | 2026-04-02 | 2025-26 |

The statement filed to
`Clients\Test Client\IntelliBooks\Statements\**2026-27**\uber\uber_2026-04-08.pdf`.

**Why 8 April and not the obvious date, and this took working out.** A Monday to
Sunday week **cannot** demonstrate this rule in 2026. 5 April 2026 is a Sunday, so
a Mon-Sun week either ends on the 5th and lies wholly in 2025-26, or starts on the
6th and lies wholly in 2026-27. **The week ending 2026-04-05 that the two existing
statement fixtures both use straddles nothing**, and a test written with it would
have passed against either rule.

8 April 2026 is a **Wednesday**. `statement_week_ending_day` on a client record is
0 to 6 with 0 meaning Sunday, from `d.getDay()` at `index.html:353`, so a
Wednesday week is a configuration a real client can have and not an invented one.
No client in the live `clients.json` sets it today: all five records have it
absent, read read-only on 2026-09-16, and the phone then defaults to 0.

**The premise is asserted, not assumed.**
`test_the_two_dates_would_give_different_years` checks that the two dates really
do give different years before the case that depends on it. Without it the
straddle test passes on a week that straddles nothing, which is exactly the trap
the existing fixtures fell into.

**And the boundary is pinned from both sides.** 2026-04-05 files under 2025-26 and
2026-04-06 files under 2026-27. Either alone passes against a rule that is off by
a day; together they do not. The `boundary-off-by-one` mutation in section 3.2
proves that.

---

## 3. Evidence

### 3.1 Red before green

**There is no red run, because nothing was built.** This is a test of existing
behaviour, so the red is the mutation set, as the brief directs. The 16 tests
passed on their first run against unmodified production code, which is the
correct outcome and is also the reason the mutations below are the whole of the
evidence that they assert anything.

Whole suite with the file added, before the mutations:
**`1525 passed, 1 skipped, 1165 subtests passed in 130.39s`.**

### 3.2 Mutations

Run with `tests/mutation_harness.py`, which refuses an anchor that does not
match exactly once, applies to a pristine copy, runs the **whole** suite,
restores and asserts the restore is byte for byte. Every mutation reports one
hunk and two lines, so each changed one place.

| Mutation | File | Change | Outcome |
|---|---|---|---|
| `never-a-statement` | `folder_reader.py` | `is_statement = False` | **caught**, 17 failures |
| `always-a-statement` | `folder_reader.py` | `is_statement = True` | **caught**, 29 failures |
| `tax-year-from-period-start` | `app.py` | file by `week_ending` minus six days | **caught**, 4 failures |
| `boundary-off-by-one` | `filing.py` | `dt.day >= 6` becomes `>= 5` | **caught**, 6 failures |
| `week-ending-key-typo` | `folder_reader.py` | read `weekEnding` instead of `week_ending` | **caught**, 14 failures |
| `prose-only` | `folder_reader.py` | reword one comment line | **survived**, as required |

**The brief asked for the first three by name.** The other three are mine:
`boundary-off-by-one` because the two 5-and-6-April cases exist for it, and
`week-ending-key-typo` because a carry-through assertion that nothing can break
is not an assertion.

**On "and no others do".** Four of the five real mutations are caught by tests
outside this file as well as by tests inside it, and that is correct rather than
noise: they break shared production code that the suite already covered. What
matters is which tests are **uniquely** this file's, so the table says which
mutations only it catches.

**`tax-year-from-period-start` is caught by four tests and all four are in this
file.** Nothing else in the suite noticed a statement filing under the wrong tax
year, which is the gap step 10aj existed to close:

```
FAILED tests/test_statement_end_to_end.py::AStatementIsFiledTest::test_a_copy_is_in_the_client_folder_under_the_year_platform_and_name
FAILED tests/test_statement_end_to_end.py::AStatementIsFiledTest::test_both_paths_are_on_the_row_and_they_are_different_copies
FAILED tests/test_statement_end_to_end.py::TheTaxYearComesFromTheEndDateTest::test_a_straddling_week_files_under_the_end_dates_year
FAILED tests/test_statement_end_to_end.py::TheTaxYearComesFromTheEndDateTest::test_the_sixth_of_april_is_the_new_year
1521 passed, 1 skipped, 1165 subtests passed
```

**`always-a-statement` is the one the negative cases exist for.** It is caught 29
times, but the only three that assert the classifier's negative answer as a
property in its own right are this file's:

```
FAILED tests/test_statement_end_to_end.py::TheClassifierCanSayNoTest::test_a_sidecar_with_no_type_key_is_a_receipt
FAILED tests/test_statement_end_to_end.py::TheClassifierCanSayNoTest::test_a_sidecar_with_another_type_is_a_receipt
FAILED tests/test_statement_end_to_end.py::TheClassifierCanSayNoTest::test_the_comparison_is_exact_and_not_a_case_fold
```

The other 26 are receipt tests failing because their receipts stopped being
receipts, which catches the mutation for the right reason and describes it
wrongly: a reader of that output would go looking in the receipt path.

**`never-a-statement`** is caught 17 times, 11 of them in this file, and the six
elsewhere are the two neighbours named in 3.3 plus
`test_a_statement_sidecar_still_carries_its_metadata`.

**`boundary-off-by-one` is the one with the most coverage outside this file, and
that is worth saying plainly.** `determine_tax_year()` is shared with the receipt
path and with `capture_report.py`, so it is caught six times, four of them
pre-existing, including `test_determine_tax_year_is_untouched_by_any_of_this` in
`tests/test_london_time.py`. **The one contribution this file makes to it is
`test_the_fifth_of_april_is_the_old_year`**, which is the only test in the suite
asserting the boundary from **inside the statement path**.

**`week-ending-key-typo`** is caught 14 times, 8 in this file. It routes the
statement to Review for missing metadata rather than filing it, which is the
correct production behaviour and is why it is caught so widely.

### A mistake in the mutation set, disclosed

**The prose mutation did not apply on the first run.** Its anchor matched **zero
times**, because I wrote it across a line break that does not exist: the comment
wraps after "tells a statement", and I typed the two halves as one line. **The
harness refused before writing anything**, which is exactly what it is for, and
the refusal named the likely cause. I took the corrected anchor off the file with
`sed` rather than retyping it and re-ran that one mutation on its own:

```
=== prose-only ===  expects: survives
one place changed: 1 hunk(s), 2 line(s)
    -# from a receipt by the SIDECAR'S `type` key, which is what that amendment
    +# from a receipt by the sidecar's `type` key, which is the thing amendment
last line: 1525 passed, 1 skipped, 1165 subtests passed in 113.04s
caught by 0 reported failure(s)
verdict: OK: survived, as expected
```

So no guard in the suite reads this file's comments as code, which matters
because that comment block is the tombstone for the deleted filename-prefix
constants and names the very key the classifier compares.

### 3.3 What the file adds over its two neighbours

Named rather than duplicated, because two of the four assertions the brief lists
already have a home:

| Already covered | Where |
|---|---|
| A real poll files a statement and writes a row | `StatementCopyTest`, `tests/test_step10d_routing.py` |
| `file_path` and `filed_path` mean what they mean on `receipts` | same |
| The client folder holds the document alone | `ThroughTheRealPipelineTest`, `tests/test_statement_client_copy.py` |
| An unresolvable client goes to Review | `StatementCopyTest` |

| New here | Why it was missing |
|---|---|
| What `scan_inbox()` itself concluded, driven on its own | both neighbours assert consequences, so a reader that got `platform` from the filename would pass them |
| The tax year against a **straddling** week | both neighbours use 2026-04-05, which straddles nothing |
| The boundary from both sides | nothing tested 5 versus 6 April |
| **The classifier saying no**, three ways | nothing did; every statement assertion in the suite was satisfied by a classifier that says yes to everything |
| The phone app's real sidecar shape | both neighbours craft a four-key or five-key sidecar |
| `file_hash`, `source` and `status` on the row | neither asserted them |

**The third row of that second table is the one that matters.** Before this file,
`always-a-statement` would have broken the receipt path and been caught for that
reason; nothing asserted the classifier's negative answer as a property in its
own right.

---

## 4. Production code: none changed

**Report question 3, answered plainly: I changed no production code.** The 16
tests pass against `app.py`, `worker/intake/folder_reader.py`, `worker/filing.py`
and `worker/database/schema.py` exactly as committed at `8e58eb6`. Nothing was
needed. `git status` shows one new file and nothing modified.

---

## 5. Flags. Not fixed.

### 5.1 Three statement branches leave the file pair in the inbox, and two of them write into Review on every poll, for ever

**This is the finding of the step.** Measured, not read.

The folder-intake loop at `app.py:1744` has five `continue` statements.
`_move_inbox_pair_to_processed()` runs on a `finally` at `:1947`, on the `try`
spanning `1877..1947`, and the statement branch `continue`s long before that
`try` is entered. Enumerated from the syntax tree, asking for each `continue`
whether a move call is a **direct statement** on the path that reaches it:

| `continue` | Branch | Moved? |
|---|---|---|
| 1762 | statement, duplicate by hash | **yes**, explicitly at 1759 |
| 1773 | statement, client cannot be resolved | **no** |
| 1779 | statement, no `platform` or no `week_ending` | **no** |
| 1819 | **statement filed successfully** | **no** |
| 1839 | receipt, duplicate of a filed receipt | **yes**, explicitly at 1836 |

**All three unmoved branches are in the statement path. Every branch outside it
is covered.**

**Measured over repeated polls, in a throwaway probe using the real fixtures**
(written, run, and deleted before the commit):

- **The success path self-corrects after one wasted poll.** Poll 1 files the
  statement and leaves the pair in the inbox. Poll 2 re-reads it, hits
  `find_statement_by_hash()`, moves the pair to `Processed\` and counts it as a
  duplicate. So `duplicates_skipped` and `inbox_duplicates_removed` are each
  inflated by one for **every statement the system ever files**. Nothing is
  filed twice and no second row is written.
- **The two review paths never correct.** The pair stays in the inbox and
  `file_review()` writes a fresh copy on every poll, with `_unique_path()`
  giving `-2`, `-3` and onwards. Observed directly over three polls:

  ```
  AFTER POLL 1  review: stmt_uber_2026-04-08_ab12cd_x9.pdf  (+ .review.json)
  AFTER POLL 2  review: ... plus -2.pdf  (+ .review.json)
  AFTER POLL 3  review: ... plus -3.pdf  (+ .review.json)
  inbox, all three polls: unchanged, both files still there
  ```

  `review_flags_issued` climbs by one per poll with it. **At the 5-minute default
  interval that is 288 copies and 288 sidecars a day, per stuck statement, until
  somebody removes the file by hand.**

**The obvious fix, and it is one sentence: the statement branch's three
uncovered `continue`s should move the inbox pair, the way the receipt path's
`finally` at `:1947` already does for every receipt outcome.** The mechanism
exists, is called `_move_inbox_pair_to_processed()`, and is already called
explicitly at two other points in the same loop. **Whether the two review paths
should move the pair at all is a decision and not a default** — a statement whose
metadata is missing might be meant to stay put until a person fixes the
sidecar — which is exactly why this is flagged rather than fixed.

**No test was written for it.** A test asserting the current behaviour would
enshrine it, and one asserting the fixed behaviour would fail. The brief says
flag and stop.

### 5.2 The `file_review()` asymmetry the brief asks about

The brief's enumeration is **correct**, verified from the syntax tree over the
committed copies: `file_review()` at `app.py:1769`, `:1777`, `:1919` and
`worker/extraction_pipeline.py:483`; `file_statement()` at `app.py:1796` and
nowhere else.

**Nothing about the asymmetry itself is wrong, and I do not recommend changing
it.** Review is an outcome that many paths reach and filing a statement is one
path, so four against one is what you would expect. Two of the four `file_review()`
sites are inside the statement branch, and they are `:1769` and `:1777` — **the
same two branches as flag 5.1**. The asymmetry is not the problem; what those two
branches do afterwards is.

### 5.3 The platform string is a folder name and is validated nowhere in this repository

Noted in section 1 and repeated here so it is not lost in prose.
`file_statement()` puts `platform` straight into a path segment. The only check
that it is one of `uber`, `bolt` or `freenow` is at `upload.js:61`, in a file this
repository does not contain and which has never been deployed. The statement
branch checks only that it is truthy.

**The obvious fix is one constant and one guard**: the three platform names
already exist as a list in `upload.js` and as `phv` on each client record in
`clients.json`; the branch could refuse a platform that is not on the client's
`phv` list and route it to Review, which is the same treatment missing metadata
already gets. **Not made**: which list is authoritative, the fixed three or the
client's own `phv`, is a decision.

### 5.4 The two existing statement fixtures use a week ending that straddles nothing

Both `StatementCopyTest` and `ThroughTheRealPipelineTest` use
`week_ending: "2026-04-05"`, and `StatementCopyTest` writes `platform` as
`"Uber"` with a capital, which `upload.js` would reject with a 400. Neither is a
defect: those tests assert other things and pass correctly. Recorded because
anyone reading them for the shape of a real sidecar would take away a wrong one,
which is how I nearly chose 5 April myself.

**No change recommended.** Editing a passing test's fixture to be more realistic
is churn, and this file now carries the realistic one.

### 5.5 One correction to the brief

`file_statement()` is imported at **`app.py:43`**, not `:41`. `:41` is the
`from worker.filing import (` line that opens the block. Every other reference in
the brief checked out exactly: `scan_inbox` imported at `:32`, called once at
`:1505`, `file_statement()` called once at `:1796`, `is_statement` set at
`worker/intake/folder_reader.py:128`, `platform` and `week_ending` at `:133` and
`:134`, and the `statements` table at `worker/database/schema.py:134`.

---

## 6. Mistakes I made, disclosed

**I got the `continue` enumeration wrong twice before getting it right, and the
probe caught both.**

1. **Version one asked whether a move call appeared within 25 lines above each
   `continue`.** That is proximity, not control flow. It reported the two
   statement review branches as covered, by the move call in the **duplicate**
   branch above them, which is a different branch. The probe run had already
   shown those branches leaving files in the inbox, so the two disagreed and I
   had to work out which was wrong.
2. **Version two asked whether any statement earlier in the same block contained
   a move call anywhere inside it.** That counts a call nested inside an `if`
   that was not taken, so it reported **all five** as covered, including the
   success path the probe had directly observed leaving the pair behind.
3. **Version three asks whether a move call is a direct statement of a block on
   the path**, at or before the statement leading to the `continue`, or in an
   enclosing `finally`. It agrees with the probe exactly: 1773, 1779 and 1819.

**The lesson is the one `CLAUDE.md` already records and I would have missed
without the probe:** a static claim about a set needs a measurement to check it
against, and the two versions that were wrong were wrong in **opposite
directions**, so either one alone would have read as confirmation. The only
reason I know version three is right is that an empirical run and a static walk
now say the same thing.

---

## 7. Confidence

- **That the seam carries a sidecar through to a row: high**, and it rests on
  running it rather than reading it. Sixteen tests through a real
  `app.process_once()` with only the mailbox and the extractor stubbed.
- **That the tax year comes from the end date: high.** Three cases, a straddling
  week and both sides of the boundary, plus two mutations that break it in
  different directions.
- **That the crafted sidecar matches the phone app field for field: high.** Both
  files read whole on 2026-09-16 and compared key by key in section 1. **What I
  cannot verify is that the deployed version matches these files**, because there
  is no deployment.
- **That three branches leave the pair in the inbox: high**, from a probe run and
  an independent syntax-tree walk that now agree, after two that did not.
- **That the Review copies grow without bound in real running: medium.** I proved
  three polls. I have not proved that nothing else sweeps the inbox on a longer
  cycle; I looked and found nothing, but I did not enumerate every scheduled path
  in `app.py`.
- **That I changed no production code: high**, from `git status` rather than from
  memory.

---

## 8. The commit. Made, on Paul's approval.

**`8af9b8f` on `feat/console-phase0`, one file, 428 insertions.** Nothing pushed,
no branch created.

**It was approved at 15:31 and not made at the time.** The approval did not reach
this session, and the next brief arrived first, so the file sat untracked through
the whole of the inbox-pair work. Paul said so on 2026-09-16 and it was committed
then. **`tests/test_statement_inbox_pair.py` was deliberately written
self-contained rather than importing from this file**, for exactly this
possibility, so the later work was never blocked by it.

**The suite was run again afterwards**, because this adds a file and two source
guards sweep the git-tracked set: **`1539 passed, 1 skipped, 1175 subtests passed
in 148.12s`**. That figure includes the inbox-pair change, which was still
uncommitted at that moment; it was green before and after, so nothing here is
resting on which of the two was in the tree.

**One difference from the message proposed below**, recorded rather than left to
be noticed: the `Suggested branch:` line was dropped, because a commit made on
that branch does not need it. Everything else is as proposed.

The message as committed:

```
test(statement): prove a sidecar in the inbox reaches file_statement()

The filing side has had real attention since 10d.55. The intake side had had
none: scan_inbox() classifies on one sidecar key and nothing asserted that a
file pair on disk reaches file_statement() carrying the platform and week
ending it cannot file without.

Sixteen tests through a real process_once(). The sidecar is the phone app's
own shape, read field for field from netlify/functions/upload.js and
index.html, which write it and have never been deployed. The tax year is
asserted over a week whose seven days straddle 5 April, because the week
ending 2026-04-05 the existing fixtures use lies wholly inside one tax year
and proves nothing about the rule. Three negative cases hold the classifier
to saying no, which nothing in the suite did.

No production code changed.

Files: tests/test_statement_end_to_end.py

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

**One file, and the working tree was otherwise clean of documents.** The three
that were modified when this task started were committed by the consultant
session at `7c097b6` while the mutations were running, which also marked step
10at built. This report is untracked and is not in the commit; this task's brief
was committed by the consultant session at `459709d`.
