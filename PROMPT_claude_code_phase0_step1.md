# Claude Code task: phase 0, the auto-retry loop that costs money

Paste into Claude Code in the `C:\LastingImpact\receipt_capture` project. Branch: `feat/console-phase0`, currently at `7da5fad`.

Read `CLAUDE.md` and section 3.1 of `2026-07-25_CONSOLE_DESIGN.md` before you start. Git communication convention applies: terminal command, plain English, VS Code GUI equivalent.

---

## First, your recovery report

Independently verified: both branch tips at `7da5fad` matching origin, `docs/console-design` untouched at `2dd147b`, `main` untouched at `965cb24`, the two cherry-picks docs-only at 1,135 and 180 insertions, all 13 files back, working tree clean apart from the five untracked files, Review folder empty, filed PNG intact, database unchanged, `runs.ndjson` at 969 with `pipeline_version=7da5fad`. Tests re-run here in a clean scratch clone at `7da5fad`: 17 under `unittest`, 17 under `pytest`, and the per-file `def test_` count sums to 17. Good work, and the two artefacts you flagged were worth flagging.

Four corrections.

1. **`logs/receipt_events_INTELLITAX.ndjson` is 55 lines, not 53.** Your restore was correct. The test suite then appended two rows at 13:38:59 and 13:41:14 BST: `"receipt_id": "recent-receipt"`, `"run_id": "test-run"`. There is an older synthetic row in there too, `56b29977` dated 24 July. This is a real defect and step 3 below fixes it.

2. **Line endings are mixed.** The restored 968 and 53 lines are LF. The appended lines are CRLF: `runs.ndjson` line 969, `INTELLITAX` lines 54 and 55. Windows text-mode appends. `json.loads` tolerates it so nothing breaks today, but the console parses these files, so do not add code that splits on `\n` and compares strings without stripping.

3. **Your flag B is an environment gap, not a suite mismatch.** `python -m pytest -q` collects and passes all 17 in a clean checkout. Your `.venv` lacks pytest. Install it into `.venv` and add it to a dev requirements file, or say so and we will standardise section 15 of the design document on `unittest`. Either is fine, but the suite itself is not the problem.

4. **Your flag A is right and worse than you put it.** `git grep "run\.log" -- '*.py'` returns nothing at all, and there is no `FileHandler` anywhere in the tracked source. So `data/run.log` has no writer, not merely a misconfigured one. Step 4 below deals with it.

The earlier claim from this chat that about 30 tracked files were modified was wrong, and the error was mine. `.gitattributes` is `* text=auto eol=lf` and Git for Windows normalises on comparison, so your tree was clean throughout. It cost you a no-op step in the recovery prompt. Ignore that step, it will not recur.

---

## What this task is

Design document section 3.1 and 3.2 of the implementation order, done properly. **This is the only defect costing money continuously, so it goes first and nothing else rides along with it.**

Four commits, in dependency order. Each one red before green: write the test, run it, show me it failing, then write the fix, then show me it passing. Report both outputs verbatim. A test that passes before the fix is testing the wrong thing.

Note a deviation from the design document's numbering, deliberate and worth recording in your report: the document lists the auto-retry fix as step 1 and `save_extraction(update_status=False)` as step 2, but the fix cannot be written without the parameter, so the parameter comes first. Same work, dependency order.

---

## Commit 1: `save_extraction(update_status=True)`

`worker/database/repository.py` line 149. The method inserts the extraction row and then unconditionally runs `UPDATE receipts SET status = ?` with `validation_status`.

Add a keyword parameter `update_status=True`. When `False`, insert the extraction row and skip the `UPDATE`. Default `True` so no existing caller changes behaviour.

Why it matters: the retry fix below saves a `failed` extraction row to record that the API call broke. Without this parameter that write would flip a `needs_review` receipt to `failed`. A crashed retry is information about the API, not about the document, and the operator-facing distinction is worth keeping.

**Test (design document test 3).** Temp database. Save an extraction with `update_status=False` and assert `receipts.status` is unchanged. Save another with the default and assert the status follows `validation_status`.

---

## Commit 2: `BaseExtractor.name`

`worker/extraction/base.py` has no `name` property. `ExtractionResult` carries an `engine` field, but the exception path has no result to read it from, so the fix in commit 3 needs the property.

Add it, and only it: a `name` property on `BaseExtractor`, with `OpenAIVisionExtractor` returning `"openai_vision"`.

**Scope cap.** Do not build `worker/extraction/factory.py`. Do not touch the three hardcoded `engine="openai_vision"` strings at `app.py` lines 530, 709 and 880. Those are step 7 in the design document's section 16 and they get their own commit. If you find yourself editing `app.py` beyond `_retry_failed_receipts`, stop.

---

## Commit 3: the auto-retry loop

`_retry_failed_receipts()` in `app.py`. Two branches leak, and I have confirmed both against the code and against `find_failed_by_version()` at `repository.py:440`, which selects on the **latest** extraction's `pipeline_version` being NULL or `!=` the current one.

**Branch A, the expensive one.** When `extract_with_transient_retry()` raises, control reaches `except Exception as exc`, which logs, increments `auto_retry_errors`, releases the lock and moves on. `process_extraction_result()` never runs, so `save_extraction()` never runs, so the latest extraction keeps its old `pipeline_version`, so the receipt stays eligible and is retried on **every five-minute poll**. `extract_with_transient_retry` has `max_retries=3`, so that is three real OpenAI calls every five minutes, indefinitely.

**Branch B, the noisy one.** The missing-file branch calls `repo.add_validation_note()` then `continue`s without saving an extraction row, so a receipt whose original has gone is reconsidered every poll too. No OpenAI cost, since it never reaches extraction, but it logs a warning every five minutes forever and it appends another validation note each time.

**Fix, both branches.** Save a `failed` extraction row tagged with the current `pipeline_version`, mirroring what a normal failed outcome records:

```python
repo.save_extraction(
    extraction_id=str(uuid.uuid4()),
    receipt_id=receipt_id,
    engine=extractor.name,
    supplier_name=None, invoice_date=None,
    net_amount=None, vat_amount=None, gross_amount=None,
    currency="GBP",
    raw_response=str(exc),
    validation_status="failed",
    validation_notes=[f"auto-retry extraction error: {exc}"],
    pipeline_version=pipeline_version,
    update_status=False,
)
```

For branch B, `raw_response` and the note should say the original file is missing and name the path, rather than carrying an exception string. Keep `update_status=False` on both.

Keep the existing `logger.error(..., exc_info=True)` and the `auto_retry_errors` stat. Keep the `finally` that releases the lock, and do not move the lock release inside the `try`.

**Tests (design document tests 1 and 2).** Temp database, `FakeExtractor` pattern from `tests/test_auto_retry_cap.py`.

1. Extractor raises. Run `_retry_failed_receipts()` twice under the same `pipeline_version`. Assert the extractor was called on the first pass and **not** on the second. Assert exactly one new extraction row exists, that its `pipeline_version` is the current one, and that `receipts.status` is unchanged.
2. Same shape for the missing-file branch: point `file_path` at a path that does not exist, run twice, assert one extraction row, one validation note, and no second note on the second pass.
3. Also assert the lock is released after the exception path. Test 21 in the design document covers this for the service later, but the retry loop should not be left holding a lock now.

**Flag, do not act on.** A receipt whose original file has permanently gone can never succeed, so arguably it belongs in `retry_exhausted` or `failed` rather than sitting eligible until the 7-day clock runs out. That is an accounting-visible status decision, so raise it in your report and leave the behaviour as the design document specifies.

---

## Commit 4: stop the tests writing to the live event log

`config.LOGS_DIR` is resolved at import, and `app.py:84` and `worker/extraction_pipeline.py:96` write `receipt_events_{firm_id}.ndjson` into it. The tests use a temp directory for the Clients tree but not for the log directory, so running the suite appends synthetic rows to the live operational logs. Three are in there now.

Fix the tests, not the writers: point `config.LOGS_DIR` at a temp directory for the duration of each test that triggers a write, and restore it afterwards. Do the same for `config.RECEIPTS_LOG` if it is used on any path you touch. Assert in one test that no file was created under the real `LOGS_DIR`.

Why it matters beyond tidiness: design document section 8.6 has the console's intake panel reading `receipt_events_*.ndjson` for unsupported-file-type items, so synthetic rows would show up as real intake problems.

**Leave the three existing synthetic rows alone.** Deleting lines from an operational log is a separate decision and Paul makes it.

---

## Step 4 for Paul to approve: `data/run.log`

**Ask Paul before doing this one.** If he says no, skip it and say so in your report.

`logging.basicConfig` at `app.py:31` sets `handlers=[logging.StreamHandler(sys.stdout)]` and nothing else, so every log line goes to a console window that vanishes when it is closed. Three things depend on a file that nothing writes:

- Design document 4.3 accepts a broad `except Exception` in `resolve_receipt()` on the grounds that "the traceback still reaches `data/run.log`". It does not.
- Design document test 39 says to confirm no `database is locked` appears in `data/run.log`. That test would pass vacuously.
- `CLAUDE.md` states twice that all operations are logged there, and that failures must be visible rather than silent.

If approved: add a `logging.handlers.RotatingFileHandler` to `data/run.log` alongside the existing stream handler, UTF-8, append mode, same format string, `maxBytes` 5 MB with 3 backups, creating `data/` if absent. Pure addition. Do not change the format of existing log lines, do not change any log level, and do not add or remove any log call. `data/` is gitignored, so nothing new gets tracked.

Then confirm by hand that a fresh pipeline cycle writes to the file, and report the first and last lines.

---

## When the code is done

- Full suite green. Report the verbatim output and the count.
- `python -m py_compile` on every file you touched.
- One clean pipeline cycle. Confirm from the log that the retry pass found nothing to retry, that no new extraction rows appeared in `data/receipts.db`, and report the new `pipeline_version` short hash.
- Confirm the database is still 23 `ok` and 3 `discarded` with nothing `failed` or `needs_review`.
- Push `feat/console-phase0`, fast-forward only, never `--force`.

## What to report back

1. For each commit: the test, its verbatim failing output before the fix, its verbatim passing output after, the SHA and the files changed.
2. Whether Paul approved step 4, and if so the evidence that the file is written.
3. The suite output and the pipeline cycle result.
4. Your answer on pytest in `.venv`.
5. Anything you noticed that contradicts `2026-07-25_CONSOLE_DESIGN.md`. Flag it, do not fix it.

## What not to do

- Do not touch `resolve_receipt.py`. That is step 3 in section 16 and it needs `parse_corrections` first.
- Do not build the factory, the resolution service, or anything under `console/`.
- Do not fix the other hardcoded engine strings, the sidecar `category_name`, the Review-pair cleanup or `review_count`. Each has its own step.
- Do not point any test at `data/receipts.db`. Temp databases only.
- Do not merge anything into `main`, delete `docs/console-design`, drop the stash, or delete the recovery artefacts under `C:\LastingImpact\`.
- Do not edit `CLAUDE.md` or `RECEIPT_CAPTURE_GUIDE.md`. Steps 21 and 22.
- Do not touch `IntelliBooks-Desktop-v3.html` or anything under `IntelliBooks\App\`.
