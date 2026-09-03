# Claude Code task: phase 0 step 6b, the four defects the move exposed

Paste into Claude Code in the `C:\LastingImpact\receipt_capture` project. Branch `feat/console-phase0`, currently at `bf1976d`.

Read the 2026-07-27 note in section 10.2 of `2026-07-25_CONSOLE_DESIGN.md`. It lists all seven findings from your step 6 report. **This task fixes findings 1, 2, 6 and 7. Findings 3, 4 and 5 stay recorded and untouched.** Git communication convention applies.

---

## First, your step 6 report

Verified independently at `bf1976d` in a fresh scratch clone: 94 tests under `unittest`, 94 under `pytest`. `git show --name-only` on the commit lists exactly three files, so the two existing test files were provably untouched, and they pass on their own, 4 passed. Design document test 12 is met and I have recorded it as met.

I reproduced two of your findings rather than taking them on trust. `parse_ambiguous_date("2026-05-09", True)` returns `None`, and so does the `False` case, so finding 2 is real. `resolve_invoice_date("2026-05-09", "2026-05-09", None, True)` returns the note `ambiguous_invoice_date_no_raw(model_iso=2026-05-09)` with a raw string plainly present, so finding 1 is real. `grep` confirms no logger in `postprocess.py`, so finding 6 is real.

**The mechanical diff was the right way to evidence a move**, and better than the reading I would have accepted. Eighty-two code lines out, eighty-seven in, eleven differing, all eleven structural and each one accounted for. That is the difference between "I moved it carefully" and "it is the same code". The subprocess dependency-direction test is also stronger than the import-line check I asked for, for the three reasons you gave. Both are now the standard I will hold later steps to.

**Your test-side correction is noted and it was the right call**: `1.33 / (8.00 - 1.33)` is 0.1994, your assertion said `0.200`, and you fixed the assertion rather than the formatting. Disclosing it is what makes the rest of the report credible.

**Your flag on 10.2's line numbers is correct and 10.2 is fixed.** "98-214" began eleven lines early, at the `except json.JSONDecodeError` of the JSON parse. The actual ranges, 109-149, 151-184 and 186-218, are now in the document with your reason recorded: the next person may use the range to check the move was complete and wrongly conclude something was left behind.

All seven findings are now in 10.2. Paul has read them and decided: **fix 1, 2, 6 and 7 now, before step 7.** His reasoning matches yours on finding 2. A fix that silently does not apply to a whole class of receipt is worse than a fix that fails loudly, and nobody would have found it without reading the code.

---

## Commit 1: an ISO-shaped `invoice_date_raw` must parse

Finding 2. `parse_ambiguous_date("2026-05-09", ...)` splits to `2026, 5, 9`, treats `9` as a two-digit year, normalises it to 2009, then fails both branches and returns `None`. So for a receipt that prints its date in ISO form, and whose raw string the model therefore returns in ISO form, the deterministic path does nothing and the receipt falls through to the ambiguity annotation.

**Fix.** Detect an ISO-shaped raw string before the ambiguity logic: a four-digit first component followed by two components of one or two digits. Parse it as year, month, day, with no reference to `prefer_dayfirst`, because there is nothing ambiguous about it. Everything else keeps its current behaviour.

Be precise about what counts as ISO-shaped. Four digits first is the discriminator, and a real date must still come out the other side: `2026-13-01` returns `None` as it does today, through the same `date()` construction that already guards this.

**One consequence you must handle, and it is a deliberate behaviour change.** With this fix, an ISO raw string that parses to the value the model already gave will newly append `auto_parsed_invoice_date_from_raw(raw=2026-05-09 -> 2026-05-09)` to `details`. That is an audit note recording a change that did not happen, which is the same class of problem as finding 1. **So append the note only when the parsed value differs from the `invoice_date` already held.** When it agrees, take the parsed value and say nothing. Flag this in your report as the one behaviour change in this commit beyond the fix itself.

**Tests.** ISO raw parsing to a date, both values of `prefer_dayfirst`, giving the same answer. An ISO raw agreeing with the model's date, appending no note. An ISO raw disagreeing with the model's date, winning and appending the note. `2026-13-01` returning `None`. And the existing day-first cases still behaving: `09/05/26` and `9-5-2026` must be unaffected, since neither starts with four digits.

---

## Commit 2: the ambiguity note must not claim there was no raw string

Finding 1. The guard `if not parsed_from_raw and invoice_date` is true both when there was no raw string and when there was one that could not be parsed. In the second case the note says `no_raw` when a raw string existed.

**Fix.** Three cases, three honest outcomes, and the value stays unchanged in all of them:

- No raw string at all, and an ambiguous ISO date: keep `ambiguous_invoice_date_no_raw(model_iso=...)` **exactly as it is**. `tests/test_date_disambiguation.py` asserts that string and must keep passing untouched.
- A raw string that failed to parse: a new note naming both, for example `ambiguous_invoice_date_unparsed_raw(raw=..., model_iso=...)`.
- A raw string that parsed: unchanged from commit 1.

The point of the note is that an operator reads it to decide whether to trust the date. "We had nothing to work from" and "we had something and could not read it" call for different judgements, and the second is also the only signal that would have exposed finding 2 in the field.

**Tests.** Each of the three cases produces the right note and leaves `invoice_date` alone where it should. One asserting the existing `no_raw` string is byte-identical, so a future tidy-up cannot silently change what the older test depends on.

---

## Commit 3: the silent handlers get a log line

Finding 6. Three `try/except Exception: pass` blocks, one nested, and no logger in the module. Keep every one of them, and keep the `pass` semantics: a failure must still leave the values untouched rather than fail the extraction. Add a module-level logger and a `logger.warning(..., exc_info=True)` in each handler.

**Nothing on the happy path changes**, and that is the test: assert the log is silent for a normal call and warns once for a call that raises inside a handler.

**Do not log the document.** Log the exception and which field was being processed. `raw_response` and the full parsed payload do not belong in `data/run.log`, both because it is noise and because a receipt is client data.

---

## Commit 4: stop the two test files leaking `PREFER_DAYFIRST`

Finding 7. `tests/test_date_disambiguation.py:27` and `tests/test_vat_swap.py:22` set `config.PREFER_DAYFIRST = True` in `setUp` and never restore it, so the value leaks to every test that runs afterwards. Harmless today only because `True` is also the default at `config.py:41`.

Both files already have a `tearDown`. Capture the original in `setUp` and restore it there. **Two lines each, and nothing else in those files changes.** Do not touch an assertion, a fixture, a name or a comment.

These are the files step 6 had to leave untouched. That criterion was met and the evidence is captured at `bf1976d`, so editing them now is fine. Say in your report that the step 6 evidence is historical and where it lives, so nobody later reads a modified file and thinks the criterion was broken.

---

## When the code is done

- Full suite green under both runners, verbatim output and count. 94 before.
- `python -m py_compile` on every file touched.
- One clean pipeline cycle. Live database unchanged: 23 `ok`, 3 `discarded`, 49 extraction rows, nothing locked.
- Push `feat/console-phase0`, fast-forward only, never `--force`.

## What to report back

1. Per commit: the test, verbatim red, verbatim green, SHA, files changed.
2. The one behaviour change in commit 1, stated plainly, and confirmation that nothing else in these four commits changes behaviour on a path that worked before.
3. Whether findings 3, 4 or 5 turned out to interact with any of these fixes. They should not, but you will be in the same forty lines.
4. Anything that contradicts the design document at v1.3. Flag it, do not fix it.

## What not to do

- Do not fix findings 3, 4 or 5: the two-digit year century, the dead `elif c < 1000`, or the absolute VAT tolerance. Recorded in 10.2, deliberately deferred.
- Do not change the call order in `extract()`. VAT swap first, then date resolution, because `details` is threaded through both.
- Do not move anything else out of `openai_vision.py`.
- Do not build the factory or touch the three hardcoded `engine="openai_vision"` strings at `app.py` lines 530, 709 and 880. Step 7, next.
- Do not add anything from 4.2, retire `add_validation_note()`, or start the console.
- Do not edit `CLAUDE.md`, `RECEIPT_CAPTURE_GUIDE.md` or `2026-07-25_CONSOLE_DESIGN.md`.
- Do not merge into `main`, delete `docs/console-design`, or edit anything under `IntelliBooks\App\`.
