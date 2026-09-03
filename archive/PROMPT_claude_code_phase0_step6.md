# Claude Code task: phase 0 step 6, move the post-processing out of the OpenAI extractor

Paste into Claude Code in the `C:\LastingImpact\receipt_capture` project. Branch `feat/console-phase0`, currently at `96a5c5a`.

Read section 10.2 of `2026-07-25_CONSOLE_DESIGN.md`. It is four lines and the whole task is in them. Git communication convention applies.

---

## First, your step 5 report

Verified independently at `96a5c5a` in a fresh scratch clone: 73 tests under `unittest`, 73 under `pytest`, nothing written to `data\` or `logs\` by the suite. Live database unchanged at 23 `ok`, 3 `discarded`, 49 extraction rows, nothing locked. Zero sidecars under `Clients\*\Receipts\` modified today, checked by mtime myself. `git worktree list` shows only the main checkout, so your throwaway is gone. I read the new `make_enriched_sidecar()` and confirmed the three keys, and I ran `git grep` for writers of the `category` key independently: `worker/filing.py:372` and `retroactive_categorise.py:75`, both now writing the name. Your inventory is complete.

I also read the Desktop source before your report arrived and reached the same place, lines 1785 to 1793, so we agree from independent reads rather than one of us taking the other's word.

**Removing the mutation was the right call and your reasoning is the right frame:** a post-hoc mutation is another writer wearing a different hat. Your point that setting three keys after the fact would be three chances to update two of them is exactly why. Recorded.

**Two things you caught in your own work are worth naming**, because they are the difference between a report and evidence. The test-side seed bug, where you seeded `vendor_code="apcoa"` while the engine normalises to `"apcoa parking"`, then re-ran the corrected file against unmodified code rather than presenting a red run you knew was wrong. And the mtime check that first reported 32 of 32 changed because `json.load` returns lists and a fresh tuple never compares equal. Both were caught by you and disclosed rather than quietly fixed. Keep doing that.

**Your `parseSidecar()` finding is the most useful thing in the report** and it changes a downstream plan. Because step 5 keeps the legacy `category` key holding the **name**, and `parseSidecar()` at line 1141 already tolerates a string, an object with `.name`, or `asserted.category`, Desktop reads the new sidecars correctly with no change at all. So the `parseSidecar` change in `PROMPT_intellibooks_resolution_backfeed.md` is an improvement, not a prerequisite. Recorded in 12.4, and it means that session can be scheduled on its own merits rather than blocking anything.

**Your discriminator observation is recorded too**: `corrected_by` appears only in Desktop's sidecar, `capture_date` only in the pipeline's, so "make every reader tolerant of both shapes" is a small testable rule rather than an open-ended one. That materially cheapens the step 10 decision in 17.4.

**Both your flags are accepted and recorded in 3.7, one with more precision than you had.**

Flag 1, a code with no name. I checked every layer. Layers 0 to 4 take `account_name` from a rule row or a vendor row, at `engine.py:229`, `243`, `256`, `275` and `294`, so they always have a name. **Layer 5 is the only nullable source**: `engine.py:307` sets `suggested_name=ai_result.get("name")`, which is `None` whenever the model omits the key. And `enable_ai_fallback=False` at both call sites, `app.py:489` and `retroactive_categorise.py:91`, so it cannot happen today, as you said. The rule now written into 3.7: whoever enables the AI layer must require a name alongside a code or refuse the suggestion, and `suggested_code` and `suggested_name` must not be treated as independently optional.

Flag 2, the review path writing three nulls. Confirmed as intended, and 3.7 now says so along with your reason: an identical key set across all four call sites is the property that stops the format diverging again, and a reader should take three nulls as "categorisation has not run" rather than "categorisation failed".

---

## What this task is

Design document 10.2. `_parse_ambiguous_date`, the `PREFER_DAYFIRST` logic and the VAT-inclusive-total swap all live inside `OpenAIVisionExtractor.extract()`. A second provider would silently not inherit any of it, so the day-first fix and the VAT fix would stop applying the moment the engine changed. Both fixes cost real debugging to get right and neither is provider-specific.

**This is a pure move. Behaviour must not change and the existing tests must pass unmodified.** `tests/test_date_disambiguation.py` and `tests/test_vat_swap.py` both drive `OpenAIVisionExtractor` through `extract()`, so they exercise the moved code through its new home without knowing it moved. **If either test needs editing, something was changed that should not have been.** That is design document test 12 and it is the acceptance criterion for the whole step.

### What you are moving

I have read the code so the boundaries are not a guess.

**`_parse_ambiguous_date`, `openai_vision.py:109` to `149`.** A nested function defined inside `extract()`. It closes over nothing from the enclosing scope: its only external references are `config.PREFER_DAYFIRST` and `date`, both module level. It also does `import re` inside the function body, which belongs at the top of the new module. So it lifts cleanly.

**The VAT-inclusive-total swap, `openai_vision.py:151` to `183`.** The `try` block that fires when `gross is None and net is not None and vat is not None`, computes implied rates against 0.2 and 0.05 with a 0.03 tolerance, and swaps net to gross when the gross reading matches and the net reading does not. It appends `auto_treated_amount_as_gross(...)` to `details`.

**The date resolution block, `openai_vision.py:185` to `215`.** Prefers `invoice_date_raw` parsed deterministically, appends `auto_parsed_invoice_date_from_raw(...)`, and otherwise annotates `ambiguous_invoice_date_no_raw(...)` on an ambiguous ISO date **without** changing it.

### Shape for `worker/extraction/postprocess.py`

Pure functions, no `ExtractionResult`, no OpenAI, no logging of document content:

```python
def parse_ambiguous_date(raw: str, prefer_dayfirst: bool) -> str | None: ...
def apply_vat_inclusive_swap(net, vat, gross, details) -> tuple: ...   # net, vat, gross, details
def resolve_invoice_date(invoice_date, invoice_date_raw, details, prefer_dayfirst) -> tuple: ...  # invoice_date, details
```

**One permitted deviation from a literal move:** take `prefer_dayfirst` as a parameter rather than reading `config` inside. The caller passes `config.PREFER_DAYFIRST`, so behaviour is identical, and the functions become testable without patching module state. Nothing else changes.

**Keep the broad `try/except` blocks exactly as they are**, including the bare `pass`. They are load-bearing: a numeric coercion failure is meant to leave the values untouched rather than fail the extraction. Changing that is not a move. Note in your report that these swallow silently and are now in a module a second provider will inherit, so a future error there will be harder to see. Flag it, do not fix it.

### Tests

- `tests/test_date_disambiguation.py` and `tests/test_vat_swap.py` **unmodified**, still passing. Confirm with `git status` that neither file is touched, and say so.
- New direct unit tests on the three functions. Cover at minimum: `09/05/26` with `prefer_dayfirst` true and false, giving different dates; a three-part date with a day over 12 resolving unambiguously either way round; junk that returns `None`; the VAT swap firing and the note it appends; the VAT swap **not** firing when the net reading also matches a common rate; an ambiguous ISO date being annotated and **left unchanged**.
- One test asserting `worker/extraction/postprocess.py` imports nothing from `worker.extraction.openai_vision`, so the dependency cannot quietly reverse.

---

## When the code is done

- Full suite green under both runners, verbatim output and count. 73 before.
- `git status` on the two existing test files, showing them unmodified.
- `python -m py_compile` on every file touched.
- One clean pipeline cycle. Live database unchanged: 23 `ok`, 3 `discarded`, 49 extraction rows, nothing locked.
- Push `feat/console-phase0`, fast-forward only, never `--force`.

## What to report back

1. The test, verbatim red, verbatim green, SHA, files changed.
2. Confirmation that the two existing test files are untouched, with the `git status` output.
3. A line-by-line statement of what moved and what, if anything, you had to change to make it move. If the answer is "nothing", say so plainly, because that is the expected answer and it is worth stating.
4. Anything in those three blocks that looks wrong to you. You will be reading them closely for the first time, which is the best chance anyone has had. Two I noticed and deliberately left in the move, so do not fix them: the final `return` does `invoice_date=invoice_date or parsed.get("invoice_date")`, which re-reads the key that initialised the variable and so can never supply anything new; and `engine="openai_vision"` is hardcoded in that same return, which is correct in this file but will read oddly once `self.name` exists.
5. Anything that contradicts the design document at v1.3. Flag it, do not fix it.

## What not to do

- Do not change any behaviour. This step's whole value is that it changes none.
- Do not edit `tests/test_date_disambiguation.py` or `tests/test_vat_swap.py`. If you believe you must, stop and say why.
- Do not build the factory or touch the three hardcoded `engine="openai_vision"` strings at `app.py` lines 530, 709 and 880. Step 7, next.
- Do not retire `add_validation_note()`, add anything further from 4.2, or start the console. Steps 8 onwards.
- Do not edit `CLAUDE.md`, `RECEIPT_CAPTURE_GUIDE.md` or `2026-07-25_CONSOLE_DESIGN.md`.
- Do not merge into `main`, delete `docs/console-design`, or edit anything under `IntelliBooks\App\`.
