# Report: the capture report, one client, by tax year or by dates

**Written 2026-09-11 at 15:52 BST by Claude Code**, from
`PROMPT_claude_code_2026-09-11_capture_report.md`, md5 `41afd85e97e84a767ac4ce215fba2c3f`,
verified before reading. Step 10n of `2026-07-25_CONSOLE_DESIGN.md`, amendments 319 and 327.

**Commit `e02fe8f` on `feat/console-phase0`.** Two files, both new:
`capture_report.py` and `tests/test_capture_report.py`. Not pushed. Nothing else committed.

**The suite: 1222 passed, 1 skipped, 848 subtests, in 88 seconds**, run at 15:47 BST on
2026-09-11. The baseline immediately before this work was **1186 passed, 1 skipped, 821
subtests**, so the new file is exactly 36 tests and 27 subtests and nothing else moved.

---

## 1. The three things for Paul

### 1.1 The two commands

**One client and one tax year.** Selects on the **document date**, because that is the
accounting question.

```
cd C:\LastingImpact\receipt_capture
.\.venv\Scripts\python.exe capture_report.py --client Client_004 --tax-year 2025-26
```

**One client and a range of dates.** Selects on **arrival**, because "I sent it last week"
is a question about when it was sent.

```
cd C:\LastingImpact\receipt_capture
.\.venv\Scripts\python.exe capture_report.py --client Client_004 --from 2026-09-01 --to 2026-09-11
```

`--client` takes the `client_id` exactly as it appears in `Intellibills\clients.json`.
`UNKNOWN` works and is worth knowing about: it holds the receipts whose sender matched no
client record, and those are receipts somebody is going to ring about.

The range is **inclusive at both ends**. The two scopes cannot be given together, and giving
neither is refused rather than guessed at.

**It prints to the screen and writes the same text to a file**, at
`C:\LastingImpact\receipt_capture\exports\capture-report_{client}_{scope}_{timestamp}.txt`.
The screen carries one extra line at the bottom naming that file.

### 1.2 The full set of outcomes, and the words chosen for each

**Eight, not the seven `CLAUDE.md` lists.** `bank_attachment` was added on 2026-09-11 by the
attached-document work and `CLAUDE.md` has not caught up. See flag 1.

The set is **enumerated from the syntax tree on every test run**, not copied from the brief
and not written by hand. The enumeration is printed whole in section 4.

| Status in the database | The word on the page | What it means |
|---|---|---|
| `pending` | **Received, not yet read** | It arrived and the reader has not run on it. |
| `ok` | **Read and filed** | Read successfully and recorded. |
| `needs_review` | **Waiting on a check** | Read, but something did not add up, so a person has to look. |
| `possible_duplicate` | **Held as a possible duplicate** | Same supplier, date and amount as one already recorded. |
| `failed` | **Could not be read** | Nothing usable came off the document. |
| `retry_exhausted` | **Could not be read, and retrying has stopped** | Tried again on a later build and still did not read. |
| `discarded` | **Deleted** | Somebody removed it deliberately. The original document is still in the archive. |
| `bank_attachment` | **Attached to a bank transaction** | Handed over from the books as evidence, so it is never read or published on its own. |

**The words are deliberately not the status names.** `possible_duplicate` and
`retry_exhausted` mean nothing to a client, and `ok` reads as the opposite of what it says to
somebody who has been waiting for a receipt to appear. The meanings above are printed under
every report as a legend, for the outcomes that report actually used.

**A status with no word is loud, not blank.** If the pipeline ever writes something this file
does not know, the row reads `Unrecognised status: <whatever it was>`. A test keeps the
mapping complete; that is what happens on the day it is not.

**Where a receipt went nowhere, the row says why**, on its own line underneath. A discard
carries the reason the operator typed. A failure or a review carries the validation notes. A
possible duplicate names the receipt it looks like. An attached document names the bank line.
A receipt with no extraction says so. **A failure with no reason given is the thing this
report exists to stop**, so every status that is not `ok` produces something, even if that
something is "no reason was recorded".

### 1.3 What the report cannot tell you

These four are printed at the foot of every report, so they travel with it rather than living
only here.

- **A receipt that never arrived leaves no row anywhere, so it cannot appear.** This is the
  important one. An absence here means nothing reached the mailbox or the inbox folder under
  that client. It does **not** mean something was lost after it arrived, and it does not mean
  the client is wrong; the commonest cause is a receipt sent to the wrong address or from an
  address not on the client's record, in which case it is under `UNKNOWN`. **Run the same
  command against `UNKNOWN` before telling a client nothing arrived.**
- **Arrived is when the pipeline captured the document, not when the client pressed send.**
  Email is polled, so the two differ by up to one poll interval, five minutes by default.
- **Times are UTC.** Between late March and late October that is an hour behind the clock, so
  something sent at 00:30 on a British summer evening is dated the previous day in the report.
  This matters only at the edges of a date range.
- **Only receipts are listed.** A platform statement is a row on a different table and is not
  in this report.

And one more that is not printed, because it is about the two products rather than about one
client: **the report says what the pipeline knows, not what IntelliBooks did next.** A row
saying "Read and filed, and not yet handed to the books" means exactly that; once it has been
handed over, what happens to it in Desktop is Desktop's record.

---

## 2. What was built

**`capture_report.py`**, a root script, 470 lines. **`tests/test_capture_report.py`**, 36
tests and 27 subtests.

### 2.1 The two scopes read different columns, and it is visible

The brief's section 2 asks that the difference be on the page rather than left to be inferred.
It is in three places: the `Scope` line, a `Selected on` line naming the column, and a `*` on
the column header in the table itself.

Tax year scope:

```
Scope    tax year 2025-26
Selected on the DOCUMENT DATE, extractions.invoice_date, marked * in the table below

Arrived (UTC)     How       Document date *   Supplier                        Amount  What became of it
```

Date range scope:

```
Scope    arrived 2025-08-19 to 2025-09-04 inclusive, UTC
Selected on ARRIVAL, receipts.created_at, marked * in the table below

Arrived (UTC) *   How       Document date     Supplier                        Amount  What became of it
```

### 2.2 A worked example

Rendered against a temporary database seeded with six receipts, one per interesting outcome.
This is real output, copied from the run, not a mock-up.

```
================================================================================================
CAPTURE REPORT: everything captured for this client, and what became of it
================================================================================================
Client   Client_004  Test Sole Trader
Scope    tax year 2025-26
Selected on the DOCUMENT DATE, extractions.invoice_date, marked * in the table below
Run at   2026-09-11 14:42 UTC
Source   ...\db\receipts.db, opened read-only
================================================================================================

Arrived (UTC)     How       Document date *   Supplier                        Amount  What became of it
-------------------------------------------------------------------------------------------------------
2025-09-01 07:12  email     2025-08-30        Costa Coffee                     £4.85  Deleted
                  file a1b2c3d4-0005-4000-8000-000000000005.pdf   receipt a1b2c3d4-0005-4000-8000-000000000005
                  why: deleted: personal, not a business expense
2025-08-20 09:30  email     2025-08-18        Shell Service Station           £62.40  Held as a possible duplicate
                  file a1b2c3d4-0004-4000-8000-000000000004.pdf   receipt a1b2c3d4-0004-4000-8000-000000000004
                  why: looks like receipt a1b2c3d4-0003-4000-8000-000000000003; matches a1b2c3d4... (supplier, date, amount)
2025-08-19 11:02  email     2025-08-18        Shell Service Station           £62.40  Waiting on a check
                  file a1b2c3d4-0003-4000-8000-000000000003.pdf   receipt a1b2c3d4-0003-4000-8000-000000000003
                  why: gross mismatch: 50.0 + 10.0 = 60.0, got 62.4
2025-06-12 08:14  email     2025-06-10        Apcoa Parking                   £96.00  Read and filed
                  file a1b2c3d4-0001-4000-8000-000000000001.pdf   receipt a1b2c3d4-0001-4000-8000-000000000001
                  why: read and filed, and not yet handed to the books

4 receipt(s) in this scope.

Captured for this client, with no usable document date, so in no tax year
-------------------------------------------------------------------------
These arrived and were captured. No date could be read off
them, so no tax year can claim them, and they would be
invisible in a report that listed the year alone.

2025-09-04 14:00  desktop   -                 -                                    -  Attached to a bank transaction
                  file a1b2c3d4-0006-4000-8000-000000000006.pdf   receipt a1b2c3d4-0006-4000-8000-000000000006
                  why: attached to the bank line TFL TRAVEL CHARGE of 2025-09-03
2025-07-02 17:41  email     -                 -                                    -  Could not be read
                  file IMG_4821.jpeg   receipt a1b2c3d4-0002-4000-8000-000000000002
                  why: nothing was read from this document: missing gross_amount, missing supplier_name

2 receipt(s) with no document date.
```

### 2.3 The decision in that output worth knowing about

**The second section is a decision, and it is the one thing here the brief did not ask for.**

A tax year selects on the document date. **A receipt whose extraction failed before it read a
date has no document date**, so no tax year can claim it, and a report that selected on that
column alone would silently drop it.

**That is precisely the receipt the client is ringing about.** A report built to answer "why
is it not in the file?" that omits the documents nothing could be read from would answer the
question by hiding the answer.

So those receipts are listed in their own section, under a heading that says they belong to no
tax year. **They are not counted into the year** and the two counts are printed separately, so
nothing about the tax year's own figure changes. The section does not appear on the arrival
scope, because every row has an arrival and nothing is undatable there.

I have flagged this rather than assumed it is wanted: **if you would rather the tax year
report showed the year and nothing else, it is a four-line change.** My view is that it should
stay, because without it the headline case is invisible.

### 2.4 Where the output goes, and why

**`C:\LastingImpact\receipt_capture\exports\`**, alongside `export_bookkeeping.py`'s output.

- **Not `Clients\`.** 18.2b has one writer into the client folder and the brief says nothing
  new appears there. A guard already in the suite proves it is not one: see section 5,
  mutation 3.
- **Not `Intellibills\Documents\`.** That is the archive of record, per 18.2, and a report is
  not a document that arrived.
- **Not the unsynced root.** `C:\Intellibills\` holds the database, the logs and the lock,
  which are process state per 18.2a. A report is an operator's working output, not state.
- **`exports\` is already gitignored**, by the line added on 2026-09-04 for exactly this
  reason: an untracked file there would trip `config.check_git_status_on_startup()`'s
  clean-tree warning before every pipeline start.

The path is derived from `config.BASE_DIR`, not written relative to the working directory, so
running the command from somewhere else still writes here rather than scattering an `exports\`
wherever the shell happened to be.

**A second run does not overwrite the first.** The filename carries a UTC timestamp to the
second, and a collision within that second takes a `-2` suffix, which is
`worker.filing._unique_path`'s convention.

### 2.5 Printing as well as writing

The brief said printing to the screen as well as writing a file is worth considering, because
the common case is reading one line back to a client. **Both**, and the text is identical, so
what you read out is what you can forward. A test asserts the file's whole content appears in
the screen output.

---

## 3. What it does not touch

- **The database is opened `mode=ro`** on a file URI. A write raises
  `sqlite3.OperationalError: attempt to write a readonly database`, proved by a test that
  tries one through the report's own opener.
- **No receipt's status moved**, asserted by comparing every row's status before and after a
  run that rendered one receipt of every status.
- **Nothing is published and nothing is re-processed.** The module imports `config`,
  `worker.attached` for its four event keys, and `worker.filing.determine_tax_year`. It calls
  no writer.
- **Nothing was written into `Clients\`, `IntelliBooks\` or `Intellibills\Documents\`**,
  asserted by snapshotting every file under the test root before and after a run.
- **F16 is untouched.** `capture_report.py` does not read or write `client_copy_trigger`, and
  nothing in this change goes near `worker/client_copy.py`.

**One disclosure on the read-only claim, and it is real.** Opening a WAL database `mode=ro`
**creates `receipts.db-wal` and `receipts.db-shm` beside it if they are not already there, and
leaves them behind on close.** Measured, not assumed: a zero-length `-wal` and a 32 KB `-shm`.
That is SQLite's read machinery rather than a write to the database, and the database file
itself is byte-identical afterwards, which is its own test. Those two files live in
`C:\Intellibills\db\` during every pipeline run anyway, and nowhere near the practice root.
**I found this because a test I had written asserted exactly one new file and it failed.**

---

## 4. The status set, enumerated from the syntax tree

`CLAUDE.md`'s rule: a claim about a set is not verified by verifying its members, and the tell
is the word "the" in front of a plural. So the set is derived on every test run, and printed
whole below.

**54 production files swept**: every `*.py` at the repository root and everything under
`worker\`. `.history\` is excluded by construction, because the root glob is not recursive and
the worker glob is rooted inside `worker\`, and a test asserts it anyway.

### 4.1 The premise: three writers and no more

The enumeration only works if it follows every route into the column. Every SQL statement in
the production tree that writes `receipts.status`, found by walking string constants out of
the syntax tree rather than grepping the text:

```
worker\database\repository.py:407
    INSERT INTO receipts (receipt_id, firm_id, client_id, source, message_id, ...)
worker\database\repository.py:453
    UPDATE receipts SET status = ? WHERE receipt_id = ?
worker\database\repository.py:1077
    UPDATE receipts SET status = ? WHERE receipt_id = ?
```

**Three, all in one module.** `test_only_three_statements_write_receipts_status` asserts both
the count and the location, so a fourth writer anywhere makes the enumeration go red rather
than silently incomplete.

**The two `UPDATE` strings are byte-identical**, which is the substring trap
`tests/mutation_harness.py` documents. Nothing here anchors on either.

### 4.2 The three sweeps, each printed whole

```
INSERT literal             : ['pending']
handed to the two writers  : ['bank_attachment', 'discarded', 'failed', 'ok', 'retry_exhausted']
bound to a status name     : ['failed', 'needs_review', 'ok', 'possible_duplicate']
```

The first reads the literal sitting in the `status` position of `save_receipt()`'s `INSERT`,
by column name rather than by counting question marks.

The second walks every `Call` node in the tree and takes the string literals handed to
`update_receipt_status()` and to `save_extraction(validation_status=...)`, resolving a
`config.NAME` by reading `config.py`'s own tree. That is where `bank_attachment` comes from.

The third takes every string literal assigned to a name `status` or passed as a `status=`
keyword. **This is how `possible_duplicate` reaches the column**: it is never handed to
`update_receipt_status()` at all, it is put onto a `ValidationResult` in
`worker\extraction_pipeline.py` and travels through `save_extraction()`.

**That third sweep is deliberately a little wide.** Bounding it to the two modules that do
this today would make it exact and make it miss the third module that does it next. A value
collected that never reaches the column costs one extra word in the mapping; a value missed
costs a receipt the report cannot explain. The reasoning is written into the test module's
docstring so the next reader does not narrow it for tidiness.

### 4.3 The union, and the mapping

```
the union, 8 statuses          capture_report.OUTCOMES
    bank_attachment                bank_attachment      -> Attached to a bank transaction
    discarded                      discarded            -> Deleted
    failed                         failed               -> Could not be read
    needs_review                   needs_review         -> Waiting on a check
    ok                             ok                   -> Read and filed
    pending                        pending              -> Received, not yet read
    possible_duplicate             possible_duplicate   -> Held as a possible duplicate
    retry_exhausted                retry_exhausted      -> Could not be read, and retrying has stopped

symmetric difference: set()
```

**A check that cannot fail is not a check.** If every sweep returned nothing and the mapping
were emptied to match, the equality above would hold and nothing would be tested. So a second
test names seven statuses and `config.BANK_ATTACHMENT_STATUS` and asserts each is in the
enumerated set, as eight subtests.

---

## 5. Evidence

### 5.1 Red before green

`tests/test_capture_report.py` was written and run before `capture_report.py` existed:

```
tests\test_capture_report.py:73: in <module>
    import capture_report
E   ModuleNotFoundError: No module named 'capture_report'
=========================== short test summary info ===========================
ERROR tests/test_capture_report.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.20s
```

**A collection error is a weak red and I am not claiming otherwise.** The second red is the
one worth quoting, because it caught a wrong belief of mine rather than a missing file:

```
    def test_nothing_is_written_outside_the_output_path(self):
...
>           self.assertEqual(
                len(new), 1,
                f"one new file was expected, the report itself. Got: {new}")
E           AssertionError: 3 != 1 : one new file was expected, the report itself. Got:
E           ['exports\\capture-report_CLIENT001_2026-09-01_to_2026-09-11_20260911-143854.txt',
E            'receipts.db-shm', 'receipts.db-wal']

1 failed, 32 passed, 27 subtests passed in 3.60s
```

That is the SQLite behaviour in section 3. I measured it in isolation before changing the
test, rather than loosening the test to make it pass: a fresh WAL database, closed, then
opened `mode=ro` and closed again, produced `t.db-shm 32768` and `t.db-wal 0` with the main
file byte-identical. The test now names the two companions and a separate test asserts the
database file itself does not change.

Green, and the whole suite:

```
1222 passed, 1 skipped, 848 subtests passed in 88.13s (0:01:28)
```

### 5.2 The scope tests, which are the point of having two scopes

Two receipts arranged so each falls in exactly one scope:

- `doc-in-year` arrived 2026-09-01 carrying a document dated 2025-06-10. In tax year 2025-26,
  outside an arrival range of 2026-09-05 to 2026-09-11.
- `arrived-in-range` arrived 2026-09-08 carrying a document dated 2024-06-10. In that arrival
  range, outside tax year 2025-26.

Each is asserted present in its own scope and **absent from the other**. A report reading one
column for both scopes would put both in both, or neither in either, and neither mistake can
pass both tests. Two more cover the inclusive ends of the range and that another client's
receipts never appear.

### 5.3 Mutations

Five, through `tests/mutation_harness.py`, each anchored once, each measured against the whole
suite, each restored byte for byte. The harness refuses before touching the disk if an anchor
matches any number of places other than one.

| Mutation | Expected | Result |
|---|---|---|
| Both scopes read the document date | caught | **caught**, 29 failures, including `test_the_date_range_scope_selects_on_arrival` |
| `retry_exhausted` dropped from the mapping | caught | **caught**, 2 failures |
| The report writes into `Clients\` | caught | **caught**, 2 failures |
| The database opened read-write | caught | **caught**, 1 failure |
| A docstring sentence reworded, prose only | survives | **survived**, 0 failures |

The diffs, printed by the harness beside each result:

```
=== both-scopes-read-the-document-date ===  expects: caught
one place changed: 1 hunk(s), 2 line(s)
    -                    if self.first <= arrival_date(row) <= self.last]
    +                    if self.first <= (row.get('invoice_date') or '') <= self.last]
verdict: OK: caught, as expected

=== drop-retry-exhausted-from-the-mapping ===  expects: caught
one place changed: 1 hunk(s), 4 line(s)
    -    "retry_exhausted": Outcome(
    -        "Could not be read, and retrying has stopped",
    -        "Could not be read, and retrying has stopped: it was tried again on a "
    -        "later build and still did not read."),
caught by 2 reported failure(s):
  FAILED StatusEnumerationTest::test_every_status_the_database_can_hold_has_a_word
  SUBFAILED(status='retry_exhausted') EveryStatusAppearsTest::test_every_enumerated_status_renders_its_word
verdict: OK: caught, as expected

=== write-the-report-into-the-client-folder ===  expects: caught
one place changed: 1 hunk(s), 2 line(s)
    -OUTPUT_DIR = config.BASE_DIR / "exports"
    +OUTPUT_DIR = config.CLIENTS_ROOT / "exports"
caught by 2 reported failure(s):
  FAILED ReadsOnlyTest::test_the_output_folder_is_not_the_client_folder
  FAILED test_stage4_client_copy.py::ClientFolderWritersTest::test_the_set_of_routes_into_the_client_folder_is_the_allowed_set
verdict: OK: caught, as expected

=== open-the-database-read-write ===  expects: caught
one place changed: 1 hunk(s), 2 line(s)
    -    conn = sqlite3.connect(f"{uri}?mode=ro", uri=True)
    +    conn = sqlite3.connect(f"{uri}", uri=True)
caught by 1 reported failure(s):
  FAILED ReadsOnlyTest::test_the_connection_refuses_a_write
verdict: OK: caught, as expected

=== prose-only-control ===  expects: survives
one place changed: 1 hunk(s), 2 line(s)
    -    None covers three real cases and they are not distinguished: no extraction,
    +    None covers three real cases and they are not told apart: no extraction,
caught by 0 reported failure(s):
verdict: OK: survived, as expected
```

**The third mutation is the interesting one.** It was caught by a guard I did not write:
`ClientFolderWritersTest::test_the_set_of_routes_into_the_client_folder_is_the_allowed_set`
enumerates every route into `Clients\` across the production tree and holds it to an allowed
set of four. The mutation added a fifth and that test said so. **That is a guard over the set
doing exactly what a guard over a set is for**, and it means the new module is watched by it
from the day it was added rather than from the day somebody remembers to add it.

### 5.4 The discard reason is read from the row the pipeline writes

`test_a_discarded_receipt_carries_the_reason_the_operator_gave` calls the real
`worker.resolution.service.discard_receipt()` rather than inserting an audit row by hand.
Seeding it by hand would have proved the report reads a row the test invented.

---

## 6. Flags. Reported, not fixed

Six. The first two are small and obviously right, and I will do either or both in one edit if
you say so; the rest are yours to decide.

### Flag 1: `CLAUDE.md` says seven statuses and there are eight

The Database Schema section reads: "**The seven statuses, each verified at its write site.**
`pending` ... `discarded` from `worker\resolution\service.py:832`". **`bank_attachment` is
missing.** It was added on 2026-09-11 by the attached-document work, sub-step 10f.38, and
`config.BANK_ATTACHMENT_STATUS` is written by `worker\attached.py`'s
`record_attached_document()`.

Small, one sentence, and the enumeration above is the evidence. **Offered.**

### Flag 2: three stale line numbers in that same paragraph

Checked by reading each line rather than trusting the citation.

| `CLAUDE.md` says | What is actually there | Where it is now |
|---|---|---|
| `retry_exhausted` from `app.py:650` | a `logger.warning` about a receipt marked ok with no extraction | `app.py:1186` |
| `discarded` from `worker\resolution\service.py:832` | a docstring about the ordering of steps 7 and 8 | `service.py:1481` |
| `filed` is the default status of a `statements` row, `worker\database\repository.py:92` | the start of `save_statement()`'s signature is at 117 | `repository.py:119` |

**This is the same fault `CLAUDE.md` already records a rule against**, under "Do not cite a
line number in `config.py`", and its own closing sentence there: "This is the same fault as
`app.py:775`". The rule was written about `config.py` and the fault is not confined to it.

The fix I would suggest is the one that rule already prescribes: **name the function, not the
line.** `_retry_failed_receipts()`, `discard_receipt()`, `save_statement()`. A name does not
move. **Offered**, as three edits in one paragraph.

### Flag 3: `CLAUDE.md`'s schema section has drifted from `schema.py` on two column names

Not offered, because it needs a decision about which is right rather than an edit.

- The `categorisations` table is documented with a `vendor_key` column. `schema.py` creates
  `mapping_id`.
- `categorisations_client_rules` is documented with a `vendor_code` column. `schema.py`
  creates `vendor_key`.
- `categorisations_client_vendors` and `categorisations_firm_vendors` are documented with
  `vendor_key` as the primary key and `vendor_code` beside it. `schema.py` creates
  `mapping_id` as the primary key and `vendor_key` as the code.

These look like the 2026-09-06 `vendor_key` rename, `migrate_2026_09_06_vendor_key_naming.py`,
reaching the code and not the document. The section already says `schema.py` is the authority
and this is a reading of it, so the reading is out of date rather than the code being wrong.
**Worth a step of its own rather than a patch**, because it is four tables.

### Flag 4: the suite figure in `CLAUDE.md` is stale, as that section predicts

It reads "944 passed, 670 subtests on 2026-09-09". It is **1222 passed, 848 subtests on
2026-09-11**. The section already tells the reader to measure before quoting, so this is
reported rather than treated as a defect.

### Flag 5: two different conventions for where a root script writes its output

`export_bookkeeping.py` writes to `Path("exports/bookkeeping_export.csv")`, **relative to the
working directory**. `capture_report.py` writes to `config.BASE_DIR / "exports"`, **absolute**.

Mine is the safer of the two: run from another folder, `export_bookkeeping.py` creates an
`exports\` wherever the shell was standing. I did not change it, because the brief did not ask
and because it is a behaviour change to a script you may have a habit around. **One line if
you want them the same.**

### Flag 6: the arrival scope reads a UTC date, and you think in London time

`receipts.created_at` is ISO 8601 UTC. The range selects on the UTC date, so between late
March and late October a receipt captured at 00:30 BST is dated the previous day in the
report. **The report says so at the foot of every run** rather than silently converting,
because converting is a decision about behaviour that you have not made.

It matters only at the edges of a range, and the obvious mitigation costs nothing: **ask for a
day either side.** If you would rather it converted to London time I will do it, but the
column would then disagree with every other timestamp in the system, which is why I have not.

---

## 7. My own mistakes

Three, all caught here rather than by anyone else.

1. **I asserted a read-only database open writes nothing, and it creates two files.** The test
   I had written for that requirement failed, which is how it surfaced. Quoted in full in
   section 5.1. I then measured the behaviour in isolation before touching the test, rather
   than widening the test to make it green, which would have been the wrong way round.

2. **A first draft of `test_each_scope_says_which_column_it_read` contained a meaningless
   expression**, an `if False else` construction left behind while I changed my mind about
   what to assert. It never reached disk: the shell refused the write for an unrelated reason
   and I rewrote the file. Recorded because catching it by accident is not the same as not
   making it.

3. **I mangled a scratchpad file twice with `sed`** while trying to insert a Windows path
   containing backslashes, producing a file that would not parse, and only then wrote it
   properly with a file tool. No repository file was involved, and no time was lost that
   matters, but it is the same class as the "a filter is not a reader" rule: I was editing a
   file through a tool that was transforming what I gave it.

---

## 8. What I did not do, and why

- **Nothing was run against the live practice root.** The samples in this report were rendered
  against a temporary database with both roots redirected by `tests/live_paths.py` before
  `config` was imported.
- **I did not `import config` to read a value outside pytest**, per the corrected fourth trap.
  The status enumeration reads `config.BANK_ATTACHMENT_STATUS` out of `config.py`'s syntax
  tree rather than by importing the module, and that is written into the test as the reason.
- **I did read the live database, read-only**, to establish which statuses actually occur on
  your machine and that eleven tables are present. `C:\Intellibills\db\receipts.db` is in the
  unsynced root, not the practice root, and the connection was `mode=ro`; a write attempt
  through it was refused. What it holds today: `ok` 24, `discarded` 7, `bank_attachment` 1,
  `possible_duplicate` 1, across `Client_001` 10, `Client_002` 1, `Client_004` 19,
  `Client_005` 1 and `UNKNOWN` 2.
- **I did not commit** `2026-07-25_CONSOLE_DESIGN.md`, any `PROMPT_*` or `HANDOVER_*` file, or
  anything under `Test Receipts\`. Three such changes were in the working tree when I started
  and are still there, untouched: a modified design document, a handover moved into `archive\`,
  and `PROMPT_claude_code_2026-09-11_category_hold.md`, which appeared during the session and
  is not mine.
- **I did not push** and did not create a branch. The commit is `e02fe8f` on
  `feat/console-phase0`.

---

## 9. Confidence

**High that the report reads only, and it rests on three separate things rather than on my
reading of the code**: the connection refuses a write under test, the database file is
byte-identical after a run, and every receipt's status is compared before and after. The
mutation that opened the database read-write was caught.

**High that the two scopes select on different columns**, because two receipts are arranged so
each is in exactly one, each is asserted absent from the other, and the mutation that made
both read the document date was caught by 29 failures.

**High that the eight statuses are the complete set that `receipts.status` can hold today**,
and this is the claim I would most want challenged, so here is exactly what it rests on: three
SQL statements write the column, all in one module, asserted by count and location; the
literals reaching those three are collected from the syntax tree by three sweeps, each printed
whole above; and dropping one status from the mapping was caught. **What it does not cover:** a
status written by something that is not Python in this repository, or by a hand-edited
database. Nothing like that exists today and nothing here would notice it.

**Medium on whether the "no document date" section is what you want.** The reasoning in 2.3 is
mine, not yours, and it is the one place I went past the brief. It is separated, separately
counted, and four lines to remove.

**High that the suite figures are right**: 1186 before, 1222 after, both measured in this
session, and the difference is exactly the 36 tests added.

**I have not seen the report run against your live database**, because the brief said nothing
was to be run against the live practice root and I took the conservative reading. The commands
in section 1.1 are the ones the tests drive, argument for argument.
