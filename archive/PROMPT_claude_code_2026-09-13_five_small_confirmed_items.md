# Claude Code brief, 2026-09-13: six small, independent, already-decided items

Section 16, steps 10ag, 10ah, 10ap, 10ar, 10as and 10ay of `2026-07-25_CONSOLE_DESIGN.md`. Each
closes one item from `2026-08-20_LIST_outstanding_items_and_decisions.md` or, for 10ay, a finding
made verifying step 10ax's report. Each is Paul's decision already made.

**Added after the first five, on Paul's instruction: combine rather than send separately.** Item
10ay is a runtime behaviour change, not a deletion or a small correction like the other five; it
carries its own test requirement below. It is added here rather than as a seventh brief because
Paul asked for the two to be combined instead of scheduled apart.

**Read this whole brief before starting.** One item, 10ah, is wider than the design document's own
entry for it: read that section for why.

**Six commits, one per item**, so any one can be reverted without the others.

**Report to `2026-09-13_REPORT_claude_code_five_small_items.md` in the repository root**, covering
all six items despite the filename.

---

## Item 10ag. The `RESOLUTIONS_DIR` environment override is removed

**Where.** `config.py`, as read 2026-09-13: the comment at lines 209-210 and the assignment at line
211.

```python
# ...on a machine that has never run the back-feed. An empty RESOLUTIONS_DIR in .env
# means "use the default", not "use the current directory".
RESOLUTIONS_DIR = Path(os.environ.get("RESOLUTIONS_DIR") or (INTELLIBILLS_ROOT / "Resolutions"))
```

Also `.env.example` line 54, a bare `RESOLUTIONS_DIR=` entry with nothing after the `=`.

**Why.** IntelliBooks Desktop hardcodes this same folder and cannot read the pipeline's `.env` at
all. If the environment variable were ever set on the pipeline's side, the two would silently
disagree about where resolution notes live. Removing the override leaves one fixed location that
both sides necessarily agree on.

**What to do.**

1. Change line 211 to `RESOLUTIONS_DIR = INTELLIBILLS_ROOT / "Resolutions"`.
2. Correct or delete the comment at lines 209-210: it describes the override's behaviour, which no
   longer exists once this lands.
3. Remove the `RESOLUTIONS_DIR=` line from `.env.example`.
4. Enumerate every read of `RESOLUTIONS_DIR` from the syntax tree before you finish. As read
   2026-09-13, `app.py`, `worker/attached.py` and `tests/test_failure_path_engine.py` all read
   `config.RESOLUTIONS_DIR` as a module attribute, not the environment variable directly, so none
   of them should need a change; confirm that rather than assume it, and report what you find.
5. Do not touch `ATTACHED_DIR` or anything else in `config.py`. One constant.

---

## Item 10ah. The stale three-digit test fixture becomes a real four-digit example

**Where.** `tests/test_vendor_import_requires_client_id.py`, as read 2026-09-13.

**The design document's own entry for this item is narrower than the file actually is, and that
changes the work. Read this section before starting.** Amendment 387 names one fixture, the
`SEED_CSV` constant at line 40:

```python
SEED_CSV = """103 Fuel,,,
Date,Description,Debit,Credit
2026-01-15,Shell Garage Dartford,50.00,
"""
```

**There is a second three-digit value in the same file, not named by amendment 387.** The
`IMPORT_CSV` constant at line 35 carries a `nominal_code` column of `103` as well:

```python
IMPORT_CSV = """vendor_code,vendor_name,detail,nominal_code,account_name
shell,Shell UK,Fuel purchase,103,Fuel
"""
```

This project's own rule, stated in `CLAUDE.md`, is that any three-digit code found anywhere is
legacy. Leaving `IMPORT_CSV`'s `103` in place while changing `SEED_CSV`'s would fix one three-digit
code and leave a second one sitting in the same file, in the same commit. **Change both** to a real
four-digit example. Any value that is a genuine four-digit code in `COA_MASTER_v2.xlsx`'s numbering
will do; the two fixtures do not need to use the same number as each other, only each be
four digits.

**What to do.**

1. Change the `103` in `SEED_CSV` (line 40) and the `103` in `IMPORT_CSV` (line 35) to four-digit
   values.
2. Both fixtures feed a manual CSV parser (`seed_client_vendors.py` for `SEED_CSV`,
   `import_vendor_csv.py` for `IMPORT_CSV`) that accepts a GL code of any digit length, confirmed by
   reading both parsers: the three digits were never a real constraint on either, only a stale
   example value on both.
3. Run the file's own test class after the change and confirm it still passes for the reason it did
   before: the fixtures are only ever read back as strings, not validated for length.
4. Change nothing else in this file. Whether `seed_client_vendors.py` itself stays in use is a
   separate question, left to Paul and not part of this item.

---

## Item 10ap. `setup_auth.py` deleted, `RECEIPT_CAPTURE_GUIDE.md`'s two references corrected

**Where.** `setup_auth.py`, the whole file, as read 2026-09-13. `RECEIPT_CAPTURE_GUIDE.md`, the
"Setup and Auth Scripts" entry at lines 427-437, and the troubleshooting bullet at line 592.

**Confirmed, read directly.** `setup_auth.py` imports `get_token` from `worker.email.reader`.
`worker/email/reader.py`, as read 2026-09-13, defines no `get_token` anywhere in the file: the
import fails before the script can do anything. It also reads `config.SHARED_MAILBOX`, which does
not exist anywhere in `config.py`, confirmed by the same reading. The script is written for the old
Microsoft Graph route; the live pipeline reads email over IMAP.

**What to do.**

1. Delete `setup_auth.py`.
2. In `RECEIPT_CAPTURE_GUIDE.md`, remove the "Setup and Auth Scripts" entry at lines 427-437 in
   full, including its heading, command block and purpose bullets.
3. In the same file, remove or rewrite the troubleshooting bullet at line 592, `` Run `python
   setup_auth.py` to test connection ``, so the guide no longer tells Paul to run a script that no
   longer exists.
4. Enumerate every other mention of `setup_auth` in the repository from the syntax tree and grep
   both, excluding `.history\`, before you finish, in case a third reference exists that this brief
   has not found. Report what you find either way.
5. Change nothing else in either file.

---

## Item 10ar. `claimed_client_id` removed from `make_enriched_sidecar()` and its call sites

**Where.** `worker/filing.py`, `make_enriched_sidecar()`, the `def` at line 379 and the
`claimed_client_id` parameter at line 397, as read 2026-09-13. Its own docstring, lines 415-429,
already records that the field is dead and is passed `None` "at all four call sites."

**Confirmed, read directly.** The function's own docstring is the source for "four call sites"; this
brief has confirmed one of them, `app.py` line 741, and not the other three. **Enumerate all
callers from the syntax tree before changing anything**, per this project's standing rule, rather
than trusting the docstring's count or grepping for the name. If the count is not four, or if any
call site does something with `claimed_client_id` other than pass `None`, stop and report rather
than removing it.

**Why removed rather than left.** The phone can no longer claim a client at all since
`capture_token` replaced a phone-supplied code under step 10d; the mismatch this field existed to
catch has no source left to produce it. This project's own practice with other confirmed-dead
fields, at items 114 to 116, is to delete rather than carry them.

**What to do.**

1. Enumerate every call site of `make_enriched_sidecar()` from the syntax tree. Print the
   enumeration whole in your report.
2. Remove the `claimed_client_id` parameter from `make_enriched_sidecar()`'s signature and from the
   dict it returns (line 435 as read 2026-09-13).
3. Remove `claimed_client_id=None` from every call site the enumeration finds.
4. Update the function's own docstring: the paragraph at lines 426-429 describes the field as dead
   and pending Paul's decision under outstanding item 117. Item 117 is now closed, per amendment 407
   of `2026-07-25_CONSOLE_DESIGN.md`: Paul's decision is to remove it. Rewrite or delete that
   paragraph accordingly rather than leave it describing a decision that has since been made.
5. Check whether any sidecar-reading code, in the pipeline or recorded elsewhere in the design
   document as read by Desktop, expects a `claimed_client_id` key to be present. If you find one,
   stop and report rather than removing the key from the dict.
6. Change nothing else in `make_enriched_sidecar()`: not the category keys, not the filename
   convention, not any other field.

---

## Item 10as. The toothless duplicate test in `test_extractor_name.py` is deleted

**Where.** `tests/test_extractor_name.py`, as read 2026-09-13.

**Confirmed, read directly.** `test_name_matches_engine_recorded_on_a_result`, lines 28-31, and
`test_openai_vision_reports_its_name`, lines 25-26, assert exactly the same thing:
`OpenAIVisionExtractor().name == "openai_vision"`. The comment above the second test claims it
covers a failure path; it does not exercise any failure path, only the same success-path property
already checked above it. The real regression coverage for the failure path, confirmed by reading
it, is `tests/test_failure_path_engine.py`'s `test_email_attachment_failure_records_the_running_engine`,
which drives a stub extractor through a simulated failure and asserts the engine string it records.

**What to do.**

1. Delete `test_name_matches_engine_recorded_on_a_result` from `tests/test_extractor_name.py`.
2. Leave `test_openai_vision_reports_its_name`, `test_base_declares_name_so_subclasses_must_provide_it`
   and `test_a_custom_extractor_can_supply_its_own_name` exactly as they are.
3. Change nothing in `tests/test_failure_path_engine.py`.

---

## Item 10ay. `_retry_failed_receipts()`'s failure handler assumes no extraction row was written, and it can be wrong

**Where.** `app.py`, `_retry_failed_receipts()`. The `try` at line 1207, `except Exception as exc` at
line 1271, its comment at lines 1274-1279, and `repo.save_extraction(...)` at lines 1282-1294, as
read 2026-09-13.

**Confirmed, read directly.** The comment says "process_extraction_result() never ran, so no
extraction row was written." That is false whenever the exception is raised from inside
`process_extraction_result()` after its own `repo.save_extraction()` call at
`worker/extraction_pipeline.py:321`, which runs near the top of that function, before
categorisation, publish or the client-folder copy. Found verifying step 10ax's report: before that
fix, `copy_for_published_receipt()`, called much later in the same function at
`worker/extraction_pipeline.py:545`, could raise past every guard between there and this handler. By
that point the extraction row for this attempt already existed, with the current `pipeline_version`
and a genuine `ok` status, and this handler would write a second row over it marked `failed`.

**Why it still matters after 10ax.** Step 10ax stopped the one call site this was found through
from raising. The assumption in this handler's own comment is about `process_extraction_result()` in
general, not about that one call site, and nothing guards the assumption itself: any other exception
raised after `worker/extraction_pipeline.py:321` and before that function returns would trigger the
same wrong write. Confirm this from the function's own body rather than take it on this brief's
say-so.

**The tool already exists.** `worker/database/repository.py:372`,
`get_extraction_for_receipt(receipt_id)`, returns the latest extraction row for a receipt, ordered by
`extracted_at DESC`. Confirm this reads as expected before relying on it.

**What to do.**

1. Before writing the `failed` extraction row in the `except` block at `app.py:1271`, call
   `repo.get_extraction_for_receipt(receipt_id)` and compare its `pipeline_version` against the
   `pipeline_version` this attempt is running under (already a local variable in this function).
2. **If they match**, an extraction row for this attempt already exists, whatever it says, so do not
   write a second one. Log the error as today (`app.py:1272`), still increment
   `stats['auto_retry_errors']`, and leave the existing row as the record of what happened.
3. **If they do not match, or no row exists**, nothing was written this attempt: keep today's
   behaviour and write the `failed` row exactly as now, so `find_failed_by_version()` still stops
   re-selecting this receipt on every poll.
4. Correct the comment at lines 1274-1279 so it describes both branches rather than assumes only
   one.
5. Two tests: one where `process_extraction_result()` fails before its own `save_extraction()` call
   (for example `extract_with_transient_retry()` raising), asserting the `failed` row is written as
   today; one where it fails after (the same style of induced failure step 10ax's test used),
   asserting no second row is written and the existing one is left alone. Each reads back the
   `extractions` table rather than trusting the return value.
6. Change nothing else in `_retry_failed_receipts()`.

---

## Evidence expected in the report

Per `CLAUDE.md`'s standard of evidence, and none of it is optional:

1. **The caller enumeration for item 10ar, printed whole**, from the syntax tree rather than from a
   grep, with `.history\` excluded. A claim about a set is not verified by verifying its members.
2. **The syntax-tree/grep sweep for item 10ap's step 4**, printed whole, whichever way it comes out.
3. **The suite before and after each commit.** Pass counts, not "green".
4. **Anything this brief gets wrong.** It has been checked against the files directly for each item,
   but not against a second reading.
5. **Your own mistakes, including ones you caught and corrected.**
6. **A confidence level per item, saying what it rests on.**

**Do not touch anything else while you are in these files.** Several of them sit beside live code
that is in the middle of other work.
