# Claude Code task: phase 0 step 5, the sidecar category field

Paste into Claude Code in the `C:\LastingImpact\receipt_capture` project. Branch `feat/console-phase0`, currently at `25c6665`.

**Read the 2026-07-27 note in section 3.7 of `2026-07-25_CONSOLE_DESIGN.md` before anything else.** The document is now at v1.3. That note is longer than the section it amends, because the field has drifted in more ways than the original section describes. The sidecars on disk are all test data, so this is about the writers, not about repairing anything.

Git communication convention applies.

---

## First, your step 4 report

Verified independently at `25c6665` in a fresh scratch clone: 64 tests under `unittest`, 64 under `pytest`, no writes to `data\` or `logs\` from the suite. Live state unchanged: 23 `ok`, 3 `discarded`, 49 extraction rows, nothing locked. Both Review folders empty, all 32 filed sidecars present, and I confirmed independently that every one of the 32 carries a top-level `receipt_id`, so your "fallback is theoretical" conclusion holds on the same evidence. `pipeline-status.json` reads exactly as you quoted it.

I read `remove_review_pair()` and its helpers rather than the summary. The `-2` test does discriminate, and your four implementation decisions are all sound. Two are now recorded in 3.5: leaving both files in place when the image deletion fails, and requiring exactly one candidate for the filename fallback. Your point about `write_review_file()`'s naming scheme producing a derived image path of `{stem}.review` that never existed, and that being handled by the already-gone branch, is the kind of detail that shows the code was actually reasoned about.

**Your flag 1 was right and it was my drafting error.** The two rules did contradict each other on the same input. Corrected in 3.5, with your ordering recorded as the resolution and the reason a different implementer would have got it wrong. Thank you for not silently picking one.

**Your flag 2 is wrong on the facts, and it matters that you know why.** Section 8.2's first line reads: "Default filter: `needs_review`, `possible_duplicate`, `failed`, `retry_exhausted`." So `retry_exhausted` does have a stated home in the console queue, and `RECEIPT_CAPTURE_GUIDE.md:396` is consistent with that rather than in tension with it. The real point underneath your flag is a good one and I have recorded it in 3.6: `review_count` feeds `pipeline-status.json`, which IntelliBooks Desktop reads, and it is not what the console shows an operator. The two counts answer different questions and are allowed to differ. Nothing to build.

**Your note on `_count_review_items()`'s name is accepted.** It no longer counts items and no longer touches the folder, so the name will mislead. Recorded in 3.6 as a deliberate deferral: rename it at step 15, when the console's read queries land and `_write_pipeline_status()` is in scope anyway. Your reason for not doing it now was the right one.

**Your caveat about the cleanup being untested against a live pair is recorded in 3.5.** It is the honest limit of the evidence and it should not be lost in a chat log.

---

## What this task is

Design document step 5, section 3.7. The sidecar writes a nominal code into a field IntelliBooks Desktop matches by name, so the receipt arrives uncategorised, and "Post to cashbook" copies that across into a real transaction. **This one reaches the books, which is why it is in phase 0 rather than being cosmetic.**

I did some of the groundwork before writing this, because the section as drafted describes one failure mode and there are more. Take these as findings to work from, and correct me if the code says otherwise.

**The field holds four different kinds of value across the 32 filed sidecars.** Eighteen say the literal string `"unmatched"`, ten are `null` of which six carry `"confidence": "high"`, two carry nominal codes, and two carry a category name with no `confidence` key at all. The full table is in the 3.7 note.

**`make_enriched_sidecar()` is not the only writer.** I found `retroactive_categorise.py:150`:

```python
code = categorisation_data.get('suggested_code') or "unmatched"
```

It then calls `update_sidecar_json()`, which writes `sidecar["category"] = category` directly into a filed sidecar on disk. That is the source of the eighteen. It bypasses `make_enriched_sidecar()` entirely, it can still be run by hand, and if it is run after this step it will undo it. **So it is in scope.**

---

## Commit 1: `make_enriched_sidecar()` carries code and name

Per 3.7, the sidecar carries **both**: `category_code` for the nominal code and `category_name` for the Desktop-compatible name. The existing `category` key stays, populated with the **name**, for readers of sidecars already on disk.

Until the Default CoA CSV is loaded, which is step 12, there is no code-to-name mapping, so `category_name` comes from `categorisation.suggested_name`, which is `account_name` off the vendor mapping and is what the engine already returns.

Change the signature from `category` to `category_code` and `category_name`, and update **all four call sites**:

- `app.py:229`, currently `category=categorisation.suggested_code`
- `resolve_receipt.py:328`, currently `category=categorisation.suggested_code`
- `worker/extraction_pipeline.py:184`, the ok path, currently `category=None`
- `worker/extraction_pipeline.py:257`, the review path, currently `category=None`

And `worker/extraction_pipeline.py:232`, which overwrites `sidecar_payload['category']` after the payload is built. That post-hoc mutation should set all three keys or be removed in favour of passing the values in properly. Your call which, but say which and why.

**No value may ever be a `match_source`.** When the engine returns no code, all three keys are `null`. `null` fails honestly. `"unmatched"` looks like a category name that Desktop will fail to match, and then someone posts it to the cashbook.

Do not touch `confidence`. It is a separate key with separate semantics and it is not part of this defect.

**Tests, design document test 9.**

- A matched receipt: `category_code` is the code, `category_name` is the name, `category` equals the name. Use a seeded client vendor mapping so the engine returns a real pair.
- An unmatched receipt: all three keys present and all three `null`. Assert explicitly that no key equals `"unmatched"`. This is the live bug and it deserves a test that would catch it coming back.
- **All four call sites produce the same key set.** Build a sidecar through each path and assert the sorted key lists are identical. Four writers of one file format is how it diverged in the first place, and this is the test that stops it.
- The `resolve_receipt.py` path writes the three keys after a manual correction.

---

## Commit 2: `retroactive_categorise.py` stops writing a match_source

Same rules as commit 1. `update_sidecar_json()` should write `category_code`, `category_name` and `category` as the name, and write `null` where the engine returned nothing. Remove the `or "unmatched"` and the `or "none"` fallbacks: they invent values that were not measured.

It reads `categorisation_data` from either an existing categorisation row or a fresh `engine.categorise()` result, and the existing-row branch only carries `suggested_code` and `confidence`, so it needs `suggested_name` too. Check both branches.

**Test it.** A temp database, a filed sidecar on disk, a receipt with no categorisation: assert the sidecar ends with three `null` keys and not the string `"unmatched"`.

---

## Investigation, one item, report only

**Paul has confirmed that every filed receipt and sidecar on disk is test data**, on test clients and his own record, not a third party's books. So the four value kinds are evidence of how the format drifted, not a data problem to repair, and the question of backfilling them is closed: **do not**. That also means one of the two investigations I had drafted is not worth your time, and I have dropped it: the six sidecars with `category: null` and `"confidence": "high"` disagree with the database, but they are disposable rows from a path that may no longer exist, and chasing them buys nothing.

One remains, because it is a question about the **format** rather than the data, and it survives the data being disposable.

**Two sidecars carry `"category": "Parking and tolls"` and no `confidence` key at all.** Every writer in this repository always writes `confidence`, so these came from somewhere else. My hypothesis is IntelliBooks Desktop's own filing flow, change log item 19, which writes names because Desktop has no codes. Those two files are also the pair with swapped dates, `2026-05-09` and `2026-09-05`, so they predate the day-first fix.

**You may read `IntelliBooks-Desktop-v3.html` to check whether it writes a sidecar when it files, and what shape. Read only. Do not edit it or anything else under `IntelliBooks\App\`.** It is 2,229 lines, so search it rather than reading it end to end.

Why it matters: if Desktop writes its own sidecar, then after step 10 a receipt filed in Desktop keeps Desktop's sidecar while the database is updated by the note, so two sidecar shapes will coexist for the same receipt population. Report what you find and I will amend section 12 before the back-feed is built.

## Explicitly not in this task

**Do not rewrite any sidecar already on disk.** Fixing the writer changes nothing already filed, and that is expected and correct. If those files are ever in the way they can be deleted rather than repaired, but not in this task.

---

## When the code is done

- Full suite green under both runners, verbatim output and count.
- `python -m py_compile` on every file touched.
- One clean pipeline cycle. Confirm the live database is unchanged at 23 `ok`, 3 `discarded`, 49 extraction rows, nothing locked.
- Confirm no sidecar under `Clients\*\Receipts\` was modified: report the count of files whose mtime changed, which should be zero.
- Push `feat/console-phase0`, fast-forward only, never `--force`.

## What to report back

1. Per commit: the test, verbatim red, verbatim green, SHA, files changed.
2. Which way you took the `extraction_pipeline.py:232` mutation, and why.
3. Whether IntelliBooks Desktop writes its own sidecar when it files, with the evidence.
4. Whether any other writer of the `category` key exists that I have not found. `git grep` for it across tracked files rather than trusting my list.
5. Anything that contradicts the design document at v1.3. Flag it, do not fix it.

## What not to do

- Do not retire `add_validation_note()`. Decided, but step 8.
- Do not add any further function from 4.2, and do not build the CoA load. Steps 8 and 12.
- Do not touch the postprocess move or the extractor factory. Steps 6 and 7.
- Do not change `export_bookkeeping.py`, `write_review_file()`, or `_count_review_items()`'s name.
- Do not rewrite any sidecar already on disk.
- Do not edit `CLAUDE.md`, `RECEIPT_CAPTURE_GUIDE.md` or `2026-07-25_CONSOLE_DESIGN.md`.
- Do not merge into `main`, delete `docs/console-design`, or edit anything under `IntelliBooks\App\`.
