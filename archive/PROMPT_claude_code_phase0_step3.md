# Claude Code task: phase 0 step 3, parse_corrections and the zero-value defects

Paste into Claude Code in the `C:\LastingImpact\receipt_capture` project. Branch `feat/console-phase0`, currently at `3bd84e9`.

Read sections 3.2, 3.3 and 4.2 of `2026-07-25_CONSOLE_DESIGN.md` before you start. Git communication convention applies.

---

## First, your phase 0 step 1 report

Verified independently, in a fresh scratch clone at `3bd84e9`: 27 tests under `unittest`, 27 under `pytest`, and the per-file `def test_` count sums to 27. After a full suite run in that clone, `logs\` is empty and `data\` holds only `files`, so the isolation in commit 4 and the handler placement in `285ed63` both do what you say. Five commits, scope held, `main` and `docs/console-design` untouched, tip matches origin.

I read `tests/test_auto_retry_no_loop.py` line by line rather than taking the summary. It asserts the right things, including `extractor.calls` staying at 3 on the second pass, the new row carrying the current version, `engine == "fake_raiser"` from `extractor.name`, status staying `needs_review`, `locked_at` NULL, and the seed row's notes untouched. That is a real red-before-green test, not one that asserts the wrong thing.

Three of your judgement calls were right and I want them on the record.

- **Branch B's note moving into the new row.** `add_validation_note()` at `repository.py:571` does `UPDATE extractions SET validation_notes = ?` on an existing row. So the old behaviour mutated an append-only row on every poll. Your deviation is the correct side of that line.
- **Moving the handler into `main()`.** 29 lines of synthetic activity in the operational log would have been worse than the problem it fixed.
- **The nested-failure gap.** Implementing the design document's snippet as written and flagging it beats improvising.

Four corrections and additions.

1. **`data/run.log` is 311 lines now, not 272.** Your figures were mid-session. Today's block is 35 lines, starting at 14:12:05 with a real cycle at `pipeline_version=2d19521`, then the synthetic block at 14:12:36 to 14:12:37, then the real cycle at 14:16:34. The synthetic lines are identifiable by `recent-receipt`, `r-file-gone`, `test-receipt-00X`, `Recovered Supplier`, `test-supplier` and `C:\Users\PDK7\AppData\Local\Temp\`. **Strip exactly those lines**, leave every other line alone, and paste the removed lines into your report so there is a record. Paul has approved this specific edit and nothing else in that file.

2. **`run.log` is only half fixed, and the design document is wrong until it is finished.** `attach_run_log_handler()` is called from `app.main()` only. `resolve_receipt.py:34` calls `logging.basicConfig` with no handlers argument, so it logs to stderr and nothing else. Design document 4.3 justifies the resolution service's broad `except` on the traceback reaching `data/run.log`, and there are four callers of that service: the CLI, the console, the back-feed consumer and a future API. Only the consumer, running inside `app.py`, will get the file. Do not fix this now. It belongs with step 9, and I am amending the design document to require a shared `worker/logging_setup.py` called from every entry point.

3. **A trap for whoever does that.** Two processes attaching a `RotatingFileHandler` to the same file on Windows will collide on rollover, because the loser cannot rename a file the winner holds open. The pipeline and the console are designed to run at the same time. When step 9 comes, it is either one file per entry point or a single writer, not the same rotating handler in three processes. Noting it now so it is not discovered at 5 MB.

4. **Your missing-file flag: no change needed, and here is why.** Leaving the status alone is right. `retry_exhausted` means "we stopped retrying because of age" and would be a lie. `failed` would erase a `needs_review` receipt's real finding. Because the status is untouched, the receipt still appears in the console queue, where the note explains that the original has gone, which is exactly where an operator should see it. The cost is one extraction row per version change and no API calls. Leave it.

Your other two flags stand and I have recorded them: `config.RECEIPTS_LOG` at `config.py:15` is referenced nowhere in tracked source, and `config.RUNS_LOG` resolves at import so redirecting `LOGS_DIR` alone does not move it.

---

## What this task is

Design document section 16 step 3. Two live defects in `resolve_receipt.py`, both confirmed against the code, plus the coercion function the console and the back-feed will both need.

Same discipline: red before green, one commit per logical unit, verbatim failing and passing output for each.

---

## Commit 1: `parse_corrections`

Create `worker/resolution/__init__.py` and `worker/resolution/service.py`. **This commit adds only `CORRECTABLE_FIELDS`, the `Corrections` dataclass and `parse_corrections`.** The rest of the service API in design document 4.2 is step 8 and must not appear yet.

```python
CORRECTABLE_FIELDS = (
    "supplier_name", "invoice_date", "net_amount",
    "vat_amount", "gross_amount", "receipt_ref_number", "receipt_time",
)

def parse_corrections(raw: dict) -> tuple[Corrections, dict[str, str]]:
    """Normalise operator input. Returns (corrections, field_errors). Never raises."""
```

Rules, from design document 4.2:

- A key absent from `raw`, or `None`, is omitted from `values`. Key presence, never truthiness.
- An empty string means "clear this field", stored as `None`, and is distinct from omission. An operator must be able to remove a wrongly extracted reference number.
- Amounts coerce to float. **Reject** thousands separators, currency symbols and more than two decimal places as field errors rather than guessing. `"0"` and `"0.00"` are valid and become `0.0`.
- `invoice_date` must be `YYYY-MM-DD` and a real calendar date. Do not reparse other formats. Guessing here would undo the day-first work in `openai_vision.py`.
- Never raises. Bad input becomes a field error keyed by field name.

**`service.py` must not import Flask, `argparse`, anything under `worker/email/`, or anything that prints or reads input.** That constraint is what makes it reusable by the console, the back-feed and a cloud API later.

**Tests, design document 10 and 11.**

- Omitted field absent from `values`; `"0"` present as `0.0`; `""` records an explicit clear.
- Rejects `"1,234.56"`, `"£10"`, `"10.999"`, `"25/12/2026"`, each with a field error and no exception.
- A float `0.0` passed directly, not as a string, is preserved.

---

## Commit 2: wire `resolve_receipt.py` to it

Three defects in one file, verified at the lines below.

**A. The mode-selection guard, line 192.**

```python
if any([args.supplier, args.invoice_date, args.net, args.vat, args.gross, args.ref_number, args.time]):
```

`--vat 0` alone is falsy, so it drops into interactive mode and asks the operator to type everything again. Test presence, not truthiness: build the raw dict from arguments that are `is not None` and take the flags path if that dict is non-empty.

**B. The merge, lines 209 to 216.**

```python
'vat_amount': corrections.get('vat_amount') or extraction.get('vat_amount'),
```

`0.0` is falsy, so `--vat 0` keeps the wrong extracted VAT. Correcting VAT to zero is routine for zero-rated and exempt supplies and currently cannot be done at all. Merge by key presence over the existing extraction.

**C. The types, `get_corrections_interactive()` at line 81.**

It returns `input().strip()`, so strings, while the flags path uses `type=float`. `validate()` in `worker/validation/rules.py` then does `round(result.net_amount + result.vat_amount, 2)`, which raises `TypeError` on a string, and the broad `except` at line 353 surfaces it as a bare "ERROR:". The T3 test passed on 25 July only because it used the typed flags path.

Route both paths through `parse_corrections`. Print field errors and exit non-zero rather than proceeding with bad input.

**Do not change the CLI's documented behaviour.** In interactive mode a blank answer still means "keep existing", so the CLI must **omit** that key, not pass `""`. `""` means clear, and the CLI has no way to express clear today. Flag that in your report as an open question for Paul, do not invent a sentinel.

Everything in `RECEIPT_CAPTURE_GUIDE.md` must keep working verbatim, except that zero now works and string amounts no longer crash.

**Tests, design document 4, 5, 6.**

- Correct a non-zero extracted VAT to `0`; assert the stored row has `vat_amount = 0.0`.
- `--vat 0` alone takes the flags path and does not fall through to interactive mode.
- All amounts supplied as strings: coerced or field errors, never a `TypeError`.

Use a temp database and the existing patterns in `tests/test_resolve_receipt_ordering.py`. Never point a test at `data/receipts.db`, and keep the `config.LOGS_DIR` and `config.RUNS_LOG` redirection you added in `2d19521`.

---

## When the code is done

- Full suite green under both runners. Verbatim output and the count.
- `python -m py_compile` on every file touched.
- One clean pipeline cycle, and confirm the database is still 23 `ok`, 3 `discarded`, 49 extraction rows, nothing `failed` or `needs_review`.
- Push `feat/console-phase0`, fast-forward only, never `--force`.

Note that the live end-to-end check of a correction, design document test 40, cannot be done yet. There is no `needs_review` receipt in the database and creating one is Paul's task, not yours. Say so rather than inventing one.

## What to report back

1. Per commit: the test, verbatim red output, verbatim green output, SHA, files changed.
2. The lines you stripped from `data/run.log`, pasted in full.
3. Your recommendation on how the CLI should express "clear this field", if at all.
4. Whether `export_bookkeeping.py` reads a category anywhere. Report only, change nothing. Design document 11.2 asks the question and it is easier to answer while you are in this area.
5. Anything that contradicts `2026-07-25_CONSOLE_DESIGN.md`. Flag it, do not fix it.

## What not to do

- Do not add any other function from design document 4.2. No `get_resolution_view`, no `resolve_receipt`, no `discard_receipt`, no `apply_resolution_note`. Step 8.
- Do not build `discard_receipt.py`. Step 9.
- Do not touch the Review-pair cleanup, `review_count`, the sidecar `category_name`, the postprocess move or the extractor factory. Steps 4 to 7, each its own commit.
- Do not change `add_validation_note`, or any other caller of it, in this commit.
- Do not fix the run.log entry-point gap or the rotation trap. Step 9.
- Do not edit `CLAUDE.md`, `RECEIPT_CAPTURE_GUIDE.md` or `2026-07-25_CONSOLE_DESIGN.md`. Steps 21 and 22, and the design document is owned by the Cowork session.
- Do not merge into `main`, delete `docs/console-design`, or touch anything under `IntelliBooks\App\`.
