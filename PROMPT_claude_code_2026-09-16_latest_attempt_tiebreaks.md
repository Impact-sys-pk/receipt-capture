# Claude Code brief, 2026-09-16: every latest-attempt pick gets the same tiebreak

Written by the consultant session, 2026-09-16, 15:42 BST. From your own four flags in
`2026-09-16_REPORT_claude_code_export_latest_attempt.md`, each verified by the consultant session
against the code on Paul's machine. **Paul's decision, 2026-09-16: fix them.**

**Report to `2026-09-16_REPORT_claude_code_latest_attempt_tiebreaks.md` in the repository root.**

**One commit. Build it, propose the commit, and wait for a yes.**

---

## Two rules about this brief

**1. `2026-07-25_BUILD_STATUS.md` is not yours to edit.** You report; the consultant session verifies
and marks it.

**2. Your four flags were right and were checked rather than taken.** Read in the files this session:
`get_extraction_for_receipt()` and the two subqueries inside `find_failed_by_version()`, both in
`worker/database/repository.py`; the extraction query in `view_receipts.py`; and
`latest_extractions()` in `probe_layer5.py`.

---

## What is decided

**Every query in this repository that picks a receipt's latest extraction attempt answers the
question the same way.** `capture_report.py` and `export_bookkeeping.py` already do:
`ORDER BY extracted_at DESC, rowid DESC LIMIT 1`.

**The point is not that ties are common. It is that two files answering "which attempt describes this
receipt" must not be able to disagree.** You made that argument yourself when you chose the tiebreak
for step 10at, and it applies to the rest of the set.

## The set, and you prove it rather than take it from here

Four are named above. **They came from your report and from one reading, not from an enumeration.**

**Enumerate the set from the syntax tree before you change anything**, and print it whole. A latest-
attempt pick is any query that orders `extractions` by `extracted_at` descending and takes one row,
or that matches on `MAX(extracted_at)`. **Say in the report how many there are and how you found
them**, and if the answer is more than four, that is the finding.

`CLAUDE.md`'s rule applies and this project breaks it more than any other: a claim about a set is not
verified by verifying its members, and the tell is the word "the" in front of a plural.

## What to build

**Three of the four take the same two words.** The fourth is a different shape:
`latest_extractions()` in `probe_layer5.py` joins on `WHERE e.extracted_at = (SELECT MAX(...))`, so a
tie does not pick wrongly, it **returns the receipt twice**. That needs the shape changing, not a
tiebreak adding.

**`probe_layer5.py` is a probe and not production.** It is in scope because a probe that double-counts
is a probe that will be believed. Say in the report that you know the difference.

## What must not change

- **`capture_report.py` and `export_bookkeeping.py`.** They are already right and are the pattern.
- **What any of these queries returns when there is no tie**, which is every case in the live data
  today. This change is invisible until two attempts share an `extracted_at`.

## Evidence

The standard in `CLAUDE.md` applies in full. Two parts this change makes specific:

- **Red before green, and the red has to be a real tie.** A fixture with two attempts carrying the
  same `extracted_at` to the stored precision, where the two differ in something the query returns.
  **Without a tie in the fixture these tests cannot fail**, and a test that cannot fail is not a test.
- **`probe_layer5.py` needs its own case**: the same tie, asserting one row back rather than two.

Run the suite again after the commit if this adds a file.

## What to report

Everything the standard asks, plus:

1. The enumerated set, printed whole, and how you enumerated it.
2. Whether `rowid DESC` is sound on `extractions` for every one of them. It was sound for step 10at
   because `extractions` has a TEXT primary key and is therefore an ordinary rowid table. **Confirm
   that rather than carry it across from the other brief.**
3. Anything you found that picks a latest attempt by some other means entirely. **Flag it, do not fix
   it.**
