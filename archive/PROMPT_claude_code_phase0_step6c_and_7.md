# Claude Code task: phase 0 step 6c and step 7

Paste into Claude Code in the `C:\LastingImpact\receipt_capture` project. Branch `feat/console-phase0`, currently at `dc2e2ae`.

Read section 3.11 of `2026-07-25_CONSOLE_DESIGN.md`, which is new, then section 10.1 and 3.8. Git communication convention applies.

**Paul: if you would rather defer step 6c, delete the first section and the branch is unaffected. My recommendation is to do it, and the reason is below.**

---

## First, your step 6b report

Verified independently at `dc2e2ae` in a fresh scratch clone: 116 tests under `unittest`, 116 under `pytest`. `git show --stat` on `dc2e2ae` confirms two insertions in each of the two test files and no deletions. Worktree gone. Live database unchanged.

I reproduced your edge table rather than reading it. Every row matches, including `0026/05/09` moving from `2009-05-26` to `0026-05-09` and `1999/01/01` moving from `None` to `1999-01-01`. All four notes behave as you describe: agreement is silent, disagreement names the change, no raw gives the byte-identical old string, and an unparseable raw now names both. The VAT probe is unchanged on all four inputs, `implied_rate=0.199` included.

**Naming the `0026/05/09` case as a date-to-different-date change rather than hiding it inside "previously returned None" is the right instinct.** So is declining to add a plausible-year bound that was not specified. If you want it later, 1900 to 2100 on the first component is the right shape and I would take it.

**Your point about the inner handler's most common trigger is well made and I have not asked you to change it.** `date.fromisoformat()` raising on a non-ISO model date is not an error, and warning about it duplicates a signal `validate()` already records as `invalid date: ...`. If that warning turns out to be the noisy one, the honest fix is to test the shape rather than catch the exception, and you were right to call that a behaviour question for another step.

**Your flag understates the problem, and finding out why is the reason step 6c exists.** You said the new `ambiguous_invoice_date_unparsed_raw` note has no stated consumer and 8.4 should commit to showing `details`. Correct, and 8.4 now does. But `details` has no **writer** either.

`extractions` has a `details` column at `schema.py:120`, with a `PRAGMA table_info` migration at `165-168`, so it was added deliberately. `save_extraction()` takes no `details` parameter and its `INSERT` lists sixteen columns without it. Nothing anywhere passes `details` to it. The sidecar has no `details` key. I queried all 49 rows for `auto_treated` or `auto_parsed` across `validation_notes` and `raw_response`: zero hits.

And it is a regression rather than an omission. Two of the 49 rows do hold a value, both from 19 July with `pipeline_version` NULL, one reading `auto_parsed_invoice_date_from_raw(raw=09/05/26 -> 2026-05-09)`. So the write worked once and was lost. `git log -S"details" -- worker/database/repository.py` points at `799cead` and `10d5742`.

So the functional half of 6b landed, because an ISO raw date now produces the right `invoice_date` and that column is written. The notes half lands in a column nothing writes. Full write-up is 3.11.

---

## Step 6c, one commit: write `extractions.details`

**Why this is worth a commit of its own rather than a footnote.** `apply_vat_inclusive_swap()` rewrites `net` and `gross` on the strength of an implied VAT rate. That is an automatic change to two financial figures, it is the right change to make, and there is currently no record anywhere that it happened. `CLAUDE.md` says this is a capture and audit system whose job is to read, extract, validate and store, not to clean or normalise, and that there must be a full audit trail. An unrecorded amendment to an amount is the one kind of gap that matters most here.

- Add `details=None` to `save_extraction()` and to the `INSERT` column list.
- Pass it from every caller that has an `ExtractionResult` to hand. Find them yourself with `git grep`; my read is `worker/extraction_pipeline.py` and the failure paths in `app.py`, but check rather than trust the list. The manual-correction path in `resolve_receipt.py` builds its own `ExtractionResult` with no `details`, so `None` is correct there and should stay explicit.
- **Do not fold it into `validation_notes`.** Those record validation outcomes; `details` records amendments the system made. Merging them makes both harder to read, and 8.4 now displays them as separate things.
- Keep `details` out of the sidecar for now. That is a format change to a file IntelliBooks reads, and it needs its own decision.

**Tests.** A VAT-inclusive extraction saved and read back with `auto_treated_amount_as_gross(...)` in `details`. An extraction with no amendments storing `NULL`, not an empty string. A manual correction storing `NULL`. And one that reads the column back out of a temp database rather than asserting on the object passed in, because the whole defect was a value that existed in memory and never reached a row.

Also report, and change nothing: whether `count_processed_today()` or any other read path would now benefit from selecting `details`, and which commit dropped the write, if `git log -S` on the `INSERT` makes it obvious.

---

## Step 7, two commits: the extractor factory

Design document 10.1 and 3.8. Line numbers have moved since the document was written; these are current at `dc2e2ae` and I have checked them.

### Commit A: `worker/extraction/factory.py`

```python
_REGISTRY = {"openai_vision": OpenAIVisionExtractor}

def get_extractor(name: str | None = None) -> BaseExtractor: ...
def available_engines() -> list[str]: ...
```

`get_extractor(None)` returns the configured default. Read it from config rather than hardcoding the key, and if config names an engine that is not in the registry, **fail loudly at startup with the name it did not recognise and the list it does**. A silent fallback to OpenAI would mean a provider switch appearing to work while nothing changed, which is the failure this whole step exists to prevent.

Replace `extractor = OpenAIVisionExtractor()` at **`app.py:488`** with `get_extractor()`. `BaseExtractor.name` already exists from `117fb1b`, so nothing is needed there.

**Tests.** `get_extractor()` returns an `OpenAIVisionExtractor` whose `.name` is `openai_vision`. An unknown name raises with both the bad name and the available list in the message. `available_engines()` returns the registry keys. A stub extractor registered into `_REGISTRY` in a test is returned by name, which proves the registry is the mechanism rather than decoration.

### Commit B: the three hardcoded engine strings

`engine="openai_vision"` at **`app.py:612`, `791` and `962`**, all on failure paths. Replace with `extractor.name`. These would misreport after any provider change, which is 3.8.

Check the extractor is in scope at each of the three. If one of them is on a path with no extractor to hand, say so and stop rather than threading a parameter through three call sites on your own judgement.

**Test.** A stub extractor whose `name` is not `openai_vision`, driven through each of the three failure paths, asserting the stored row carries the stub's name. That is the test that would have caught the original defect.

**Out of scope, and 10.3 says why:** no `settings` table, no switching from the UI, and no composite `pipeline_version`. Phase 2. Do not touch `find_failed_by_version()` or the retry cap.

---

## When the code is done

- Full suite green under both runners, verbatim output and count. 116 before.
- `python -m py_compile` on every file touched.
- One clean pipeline cycle. Live database unchanged: 23 `ok`, 3 `discarded`, 49 extraction rows, nothing locked. Note that the cycle will now write `details` on any new extraction, though with nothing to process there should be none.
- Push `feat/console-phase0`, fast-forward only, never `--force`.

## What to report back

1. Per commit: the test, verbatim red, verbatim green, SHA, files changed.
2. The full list of `save_extraction()` callers and what each now passes for `details`.
3. Which commit dropped the `details` write, if `git log -S` shows it plainly. Do not spend long on it.
4. Whether the extractor was in scope at all three hardcoded strings.
5. Anything that contradicts the design document, now at v1.3 with 3.11 added. Flag it, do not fix it.

## What not to do

- Do not add `details` to the sidecar, or fold it into `validation_notes`.
- Do not fix findings 3, 4 or 5 from 10.2: the two-digit year century, the dead `elif c < 1000`, the absolute VAT tolerance.
- Do not add the plausible-year bound to `parse_ambiguous_date` unless Paul asks.
- Do not build the `settings` table, UI switching, or the composite `pipeline_version`.
- Do not retire `add_validation_note()`, add anything from 4.2, or start the console. Steps 8 onwards.
- Do not edit `CLAUDE.md`, `RECEIPT_CAPTURE_GUIDE.md` or `2026-07-25_CONSOLE_DESIGN.md`.
- Do not merge into `main`, delete `docs/console-design`, or edit anything under `IntelliBooks\App\`.
