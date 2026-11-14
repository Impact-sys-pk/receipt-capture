# Claude Code brief, 2026-09-19: the Review seam, the Python half

Written by the consultant session, 2026-09-19, 16:39 BST, read off the clock in this reply. Step
10am of `2026-07-25_BUILD_STATUS.md`, Paul's decision of 2026-09-13 at amendment 399, and his
decision of 2026-09-19 to split the step between the two sessions.

**Report to `2026-09-19_REPORT_claude_code_review_seam.md` in the repository root.**

**One commit. Build it, propose the commit, and wait for a yes.**

---

## Three rules about this brief

**1. `2026-07-25_BUILD_STATUS.md` is not yours to edit.** You report; the consultant session
verifies against the code on Paul's machine and marks the step. Paul's instruction of 2026-09-16.

**2. `2026-07-25_CONSOLE_DESIGN.md` is not yours either.** The amendment recording this is the
consultant session's.

**3. Everything this brief names has been read this session** on Paul's machine: the test names in
`tests\test_publish_trigger.py` and `tests\test_publish_item.py`, and in `worker\`,
`publish.py`'s `build_item()`, `write_item()`, `archive_address()` and `media_type_for()`,
`filing.py`'s `make_enriched_sidecar()`, `resolution\service.py`'s `discard_receipt()` and its note
handling, and `database\schema.py`'s `receipts` table. Where this brief does not name a file or a
function, that is deliberate and the place is yours to find.

---

## What is already covered, so that you do not build it again

`tests\test_publish_trigger.py` drives a real `app.process_once()` with only the mailbox and the
extractor replaced. Four of its tests already cover the first half of the seam:
`test_needs_review_publishes_one_item`, `test_a_failed_extraction_publishes_one_item`,
`test_a_possible_duplicate_publishes_too` and `test_an_extraction_that_raised_publishes_nothing`.
`tests\test_publish_item.py` covers the item's shape in 30 tests.

**Do not repeat any of that.** If your own enumeration of the suite disagrees with the four names
above, say so in the report and work from yours rather than from this brief.

## What is not covered, and it is the join

Nothing proves that an item the pipeline produced is taken up on the other side, resolved, and
applied back. The two ends have been exercised separately and never in one run. On 2026-09-19 the
consultant session ran the Desktop end on Paul's screen against inbox items it wrote **by hand**,
which is recorded as a limitation of that test in step 10ao.1.

## What this half has to do

**One. A published item produced by the pipeline is kept where the other session can read it.**

The Desktop half of this step is a node harness the consultant session runs against
`IntelliBooks-Desktop-v3.html`, which lives in OneDrive and cannot import anything from this
repository. It needs one real published item as a fixture: the JSON the pipeline writes into the
publish folder for a receipt it has flagged for review.

- The fixture is written by production code, not typed. It comes out of the same path the four
  tests above exercise.
- It lives in the repository, committed, so the harness can read it without running Python.
- **A committed fixture goes stale, so it has to be guarded.** A test regenerates it and fails when
  what the pipeline produces today differs from what is committed. That guard is the point of the
  fixture, not an extra.
- The receipt behind it carries a validation status that is not `ok`, so the item is one the
  Review queue will hold.

Choose the path and the name. Say in the report what you chose and why.

**Two. The note round trip is tested end to end, in one test rather than two.**

Start from a receipt the pipeline has flagged and published. Write the resolution note the other
product writes when the operator deletes that receipt from the Review queue. Run the pipeline again.
Assert what the run did to the receipt, to the note file and to the document in the archive.

The note the other product writes has this shape, read off `Intellibills\Resolutions\` on Paul's
machine on 2026-09-19 after a real delete:

```json
{
 "schema": 1,
 "receipt_id": "<the receipt id>",
 "client_id": "Client_004",
 "action": "discarded",
 "resolved_by": "desktop",
 "resolved_at": "2026-09-19T08:48:50.970Z",
 "original_review_files": ["<the receipt id>.json"]
}
```

**Do not take those field names from this brief.** Read them out of the note contract in the worker
and say in your report whether the shape above matches it. A brief that supplies a fact gets it
repeated back, and then one session's error looks like two sessions agreeing.

**Three. The document in the archive survives the discard, and a test says so.**

`discard_receipt()`'s docstring says the original file in the document store is never deleted on any
path. That was confirmed on Paul's machine on 2026-09-19: after a real delete from the Review queue
the archived document was byte for byte unchanged. Assert it, so the docstring has a test behind it.

## What not to do

- **No production code changes.** If a test cannot be written without one, stop and report it.
- **No real OpenAI call**, and nothing that makes one more likely.
- Nothing outside `C:\LastingImpact\receipt_capture`.

## How to report

- Say what your own enumeration of the suite found, and where it disagreed with this brief.
- Prove the suite discriminates: mutate the behaviour each new test covers and show which test
  catches it. Red before green where you can, and the mutation where you cannot.
- Give the suite totals before and after.
- Disclose your own mistakes, including ones you caught and corrected.
