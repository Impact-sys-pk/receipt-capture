# Report: the AI layer's matched vendor, and the line item count on published items

Claude Code, 2026-11-14, finished 10:54 GMT (the Windows shell's `GMTST`, which is GMT in November). Branch `feat/console-phase0`. The brief was pasted into the chat by Paul. It has no `PROMPT_*` file. This report is not committed.

**`2026-07-25_BUILD_STATUS.md` was not touched.** Another session has uncommitted changes to `2026-07-25_CONSOLE_DESIGN.md`, `2026-07-25_BUILD_STATUS.md` and `CLAUDE.md`. I staged only my own files by name, so none of those changes is in either commit.

## The suite

| When | Result |
|---|---|
| Before these two items | 1743 passed, 2 skipped, 1342 subtests |
| After both commits | **1757 passed, 2 skipped, 1347 subtests** |

That is 14 more tests, and 14 were added: 1 for item 1 and 13 in the new `tests\test_item_line_item_count.py`. A new test file was committed, so the suite was run again after the last commit. That run is the one quoted above.

## Item 1. The AI layer records no matched vendor, commit `1b6e2f5`

| File | Lines |
|---|---|
| `worker\categorisation\engine.py` | +5 −1. The layer 5 branch of `categorise()` sets `matched_vendor=None`. Before, it set `matched_vendor=vendor_key` |
| `tests\test_firm_vendor_writer.py` | +6 −2. `TheShapeTest` now expects `"None"`, and the `ai_result()` copy is updated to match |
| `tests\test_vendor_lookup_by_name.py` | +13. New `test_layer_five_records_nothing`. The model is stubbed, so it makes no real call |

**The two tests that were red before the change:**

- `test_layer_five_records_nothing` failed with `AssertionError: 'shell' is not None`.
- `TheShapeTest::test_the_shape_matches_what_layer_five_builds` failed with `AssertionError: 'vendor_key' != 'None'`. This is the test the brief named.

**What did not change.** The key is still on the result as `vendor_key`, and the new test asserts that. Layer 0 still records `rule_name`.

## Item 2. The line item count, commit `da054c4`

| File | Lines |
|---|---|
| `worker\publish.py` | +22 −1 |
| `worker\extraction_pipeline.py` | +5 −1 |
| `app.py` | +6 −2 |
| `tests\test_item_line_item_count.py` | +148, new |
| `tests\test_item_vendor_key.py` | +3 −1 |
| `tests\fixtures\published_item_needs_review.json` | regenerated |

**`worker\publish.py`:**

- New constant `LINE_ITEM_COUNT_KEY = "line_item_count"`, with a comment, added to `ITEM_ONLY_KEYS`.
- `extra_for()` takes `line_items=None` and writes `len(line_items) if line_items else None`.

**The callers.** `extra_for()` has two callers, and both now pass the line items:

- **The poll, in `worker\extraction_pipeline.py`**, passes `extraction.line_items`. That is the `ExtractionResult` that produced the item. It is passed on both branches, so a receipt for review carries the count.
- **The recovery sweep, in `app.py`**, reads the stored `extractions.line_items` once into `stored_lines`. The same value now goes both to the classifier, as it did before, and to `extra_for()`.

Nothing is re-extracted and no image is read. Only the count is published, and a test checks that neither the `line_items` key nor any line's description appears in the item's bytes.

**`tests\test_item_vendor_key.py`.** `test_nothing_else_moves` compares the whole dictionary `extra_for()` returns, so it had to gain the new key.

**`tests\fixtures\published_item_needs_review.json`.** Regenerated with `REGENERATE_REVIEW_FIXTURE=1`. The diff is `"line_item_count": null`, plus the receipt id, capture date and archive path, which change on every regeneration.

**Red before green.** The new file failed 15 times, counting subtests, on the missing constant and on `extra_for()` not accepting `line_items`. One test passed before the change: `test_the_lines_themselves_are_not_published`, which was already true and is there to guard against a later change.

**The Desktop side** already declares `const LINE_ITEM_COUNT_KEY="line_item_count";` at line 2012 of `IntelliBooks-Desktop-v3.html`, so the spelling matches. I read that line and nothing else in that file.

### One published item, showing the new key

This item was produced by the real poll, in a temporary environment. The extraction held two line items, and the receipt went to review on a gross mismatch:

```json
{
  "receipt_id": "24adf5a1-ff16-4f2d-ab4f-90254d35abe7",
  "client_id": "CLIENT001",
  "client_name": "Test Client",
  "source": "email",
  "capture_date": "2026-11-14T10:54:12.761893+00:00",
  "invoice_date": "2026-04-01",
  "supplier": "Apcoa Parking",
  "net": 10.0,
  "vat": 2.0,
  "gross": 99.0,
  "currency": "GBP",
  "category_code": null,
  "category_name": null,
  "category": null,
  "confidence": "none",
  "validation_status": "needs_review",
  "asserted": null,
  "original_filename": "shared.pdf",
  "pipeline_receipt_id": "24adf5a1-ff16-4f2d-ab4f-90254d35abe7",
  "validation_notes": [
    "gross mismatch: 10.0 + 2.0 = 12.0, got 99.0"
  ],
  "category_unconfirmed": false,
  "vendor_key": "apcoa parking",
  "line_item_count": 2,
  "image_media_type": "application/pdf",
  "archive_path": "Intellibills\\Documents\\CLIENT001\\2026\\11\\24adf5a1-ff16-4f2d-ab4f-90254d35abe7_shared.pdf"
}
```

To produce it, I wrote a throwaway test file, `tests\_tmp_show_item.py`, so the run went through `tests\conftest.py` and never touched the live roots. I deleted it straight after, and `git status` shows nothing of it.

## Flag, with a recommendation: line items have never been stored

**Step 10p added `extractions.line_items` on 2026-09-12, but none of the 9 production calls to `save_extraction()` passes it.** I enumerated them from the syntax tree across `app.py`, the root scripts and `worker\`:

- 5 in `app.py`
- 1 in `worker\extraction_pipeline.py`
- 3 in `worker\resolution\service.py`

Commit `4c90130` added the parameter to `save_extraction()` but did not change `worker\extraction_pipeline.py`, which is the poll that holds the lines.

**The live database confirms it.** I read it read-only. **None of the 47 `openai_vision` extractions since 2026-09-12 holds any line items**, and none of the 37 `manual_correction` rows does either.

**What it means:**

- **For item 2:** on the poll, the count is right, because it is taken from the `ExtractionResult` in hand. **An item published by the recovery sweep will always say `null`**, even when the model read lines, because the sweep reads them from the column and the column is always empty.
- **More widely:** the classifier on the sweep, and on every re-categorisation, sees no lines. Step 10p existed to fix exactly that, so step 10p part one is not in effect.

**Recommendation: pass `line_items=extraction.line_items` in the poll's `save_extraction()` call in `worker\extraction_pipeline.py`.** That is one line and one test, and **I can do it now**. The other 8 call sites need to be checked one by one before changing any of them, because some write a correction rather than a fresh read. That needs its own brief. Nothing can be backfilled, which agrees with Paul's instruction recorded in `schema.py`.

**Confidence: high that both items do what is described.** It rests on red tests before each change, quoted above, a full green run after the last commit, and the item above produced by the real poll. **High on the flag too**, because it rests on the syntax tree enumeration and the live database count, both read today.
