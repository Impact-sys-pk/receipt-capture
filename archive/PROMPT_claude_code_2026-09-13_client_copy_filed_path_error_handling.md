# Claude Code brief, 2026-09-13: `mark_receipt_filed()` has no error handling in `copy_for_published_receipt()`

Section 16, new step 10ax, amendment 446 of `2026-07-25_CONSOLE_DESIGN.md`. One file, one commit.

**Report to `2026-09-13_REPORT_claude_code_client_copy_filed_path_error_handling.md` in the repository
root.**

---

## Where this came from

Found this session while checking whether the pipeline's client-folder writer shared a defect
17.4 of the design document recorded against IntelliBooks Desktop, a partial filing window where an
image write commits before a second write and a failure of the second leaves an orphan. It does
not: `write_client_copy()` writes one file only, the image, nothing beside it. That question is
closed.

Reading `worker/client_copy.py` to answer it surfaced a different, smaller gap, not previously
recorded anywhere. This brief is about that gap, not about 17.4.

## The gap

**Where.** `worker/client_copy.py`, `copy_for_published_receipt()`, as read 2026-09-13:

```python
try:
    result = write_client_copy(
        source_file=Path(source_file),
        client_folder_name=client_folder_name,
        tax_year=determine_tax_year(invoice_date),
        supplier=supplier or "unknown",
        gross=gross if gross is not None else 0.0,
        invoice_date=invoice_date,
    )
except Exception as error:
    logger.error(
        "the client folder copy for receipt %s failed: %s: %s. The receipt "
        "is unaffected: it is published and the document store holds the "
        "archive of record. Nothing retries this copy.",
        receipt_id, type(error).__name__, error)
    return None

...

repo.mark_receipt_filed(receipt_id, str(result.path))
```

Line numbers as at 2026-09-13: the `write_client_copy()` call is at line 544, its `except` at 553,
and `repo.mark_receipt_filed(...)` at line 568. **Confirm these against the file as you find it**,
this document's own rule is that a cited line number decays the moment anyone edits above it.

The file write has error handling. The database write immediately after it does not. The
function's own docstring says "**This never raises.**" As written, it can: an exception out of
`mark_receipt_filed()` propagates uncaught.

## Why it matters, and why it might matter less than it sounds

If `write_client_copy()` succeeds, or finds an identical file already there and correctly declines
to write a second one, and the following `mark_receipt_filed()` call then fails, for whatever
reason, the document is correctly sitting in the client's folder and the database's
`receipts.filed_path` stays NULL.

**This is likely self-healing, and here is the reasoning, verify it rather than take it on
trust.** `write_client_copy()` compares against every file already under the composed name by
bytes, not by name alone (`_existing_under()`, `_same_bytes()`). So on the pipeline's next poll,
this receipt is offered again by whatever selects on `filed_path IS NULL`, `write_client_copy()`
runs again, finds the identical bytes already there, and returns `written=False` rather than
writing a second copy. If the database is healthy on that later attempt, `mark_receipt_filed()`
succeeds and the receipt is correctly recorded from then on.

**What is not established, and is this brief's real question.** What happens to the *caller* of
`copy_for_published_receipt()` when this exception is raised uncaught. Does it abort only this one
receipt's publish, or does it abort a whole batch or poll cycle, taking other receipts down with
it? That depends on code this brief has not read. **Read the caller(s), enumerated from the syntax
tree, before deciding the fix is purely cosmetic.**

## What to do

1. Enumerate every caller of `copy_for_published_receipt()` from the syntax tree, and read enough of
   each to say what happens above it if the function raises. Report what you find, whichever way it
   goes.
2. Wrap `repo.mark_receipt_filed(receipt_id, str(result.path))` in its own `try/except`, matching
   the shape and tone of the `except` already above it: log an ERROR naming the receipt, the path
   the document is actually at, and that the copy exists but is not yet recorded; return `None`,
   the same as the existing failure branch, rather than let the exception propagate. Make the
   function's own docstring claim, "this never raises", true rather than aspirational.
3. Do not touch `write_client_copy()`, the byte-comparison logic, or anything else in the file.
   This is one function's error handling, nothing else.
4. A test that drives `mark_receipt_filed()` raising, and asserts `copy_for_published_receipt()`
   returns `None` rather than propagating, and that the ERROR is logged. Reuse whatever fixture
   pattern `tests/test_stage4_client_copy.py` already uses for this module, named in the module's
   own docstring as the place the callers are held.

## Evidence expected in the report

Per `CLAUDE.md`'s standard of evidence:

1. The caller enumeration from step 1, printed whole, and what each caller does if this function
   raises, today, before your fix.
2. The suite before and after, pass counts, not "green".
3. Anything this brief gets wrong. It has not been checked against a second reading.
4. Your own mistakes, including ones you caught and corrected.
5. A confidence level, saying what it rests on.

**One thing this brief deliberately does not decide.** Whether the retry-on-next-poll behaviour
this brief relies on is fast enough in practice, once a minute, once an hour, whatever the pipeline's
actual cadence is, is not evaluated here. If your reading of the callers turns up a reason the
self-healing story in this brief does not hold, stop and report rather than building around it.
