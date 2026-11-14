# Report: the published item carries the receipt's vendor key

Written 2026-11-13 by Claude Code, for the consultant session. Brief:
`PROMPT_claude_code_2026-11-13_vendor_key_on_item.md`. Sub-step 10bs.10,
second and last piece of its pipeline half, amendment 555.

`2026-07-25_BUILD_STATUS.md` is not touched. Marking the step is the
consultant session's.

---

## 1. What was done

One commit, `8f084ab`, on `feat/console-phase0`. Three files:

| File | Change |
|---|---|
| `worker\publish.py` | New constant `VENDOR_KEY_KEY`, added to `ITEM_ONLY_KEYS`; `extra_for()` writes it |
| `tests\test_item_vendor_key.py` | New, 14 tests, one with two subtests |
| `tests\fixtures\published_item_needs_review.json` | Regenerated; see section 4 |

This report is not in the commit.

**Nothing else moved.** Nothing is taught, nothing is re-categorised, and the
other four keys `extra_for()` builds are unchanged. `test_nothing_else_moves`
asserts the whole dict `extra_for()` returns.

---

## 2. The constant

**`worker.publish.VENDOR_KEY_KEY = "vendor_key"`**, beside
`CATEGORY_UNCONFIRMED_KEY`, `NOTES_KEY` and `DUPLICATE_OF_KEY`, and a member of
`ITEM_ONLY_KEYS`.

**The value matches `config.MAPPING_VENDOR_KEY_FIELD`**, which is also
`"vendor_key"`, and a test pins the two equal. The join the reader makes is on
the values, so the names do not have to match. They do match so that the
reader uses one word for one thing across the two files it opens.

**Where the value comes from.** `categorisation.vendor_key`, the same object
`category_unconfirmed` is read from, so the poll and the recovery sweep cannot
publish different keys for one receipt. It is the key `categorise()` computed
from the extracted supplier name with `vendor_key_for()`. **`resolve_against_chart()`
does not change it**: read in `worker\categorisation\fallback.py`, all five of
its outcomes mutate the result in place and none assigns `vendor_key`.

---

## 3. What the item carries where there is no key, and why

**The key is on every item. Its value is a string or `null`. It is never
absent on an item written from now on, and never an empty string.**

| On the item | Means |
|---|---|
| a string, `"shell"` | the key the engine computed for this receipt's supplier name |
| `null` | the pipeline says there is no key: the receipt was never categorised, or its name normalised to nothing |
| absent | an item written before this change; the pipeline said nothing |

**Why `null` and not absent.** In JavaScript `item.vendor_key === null` and
`item.vendor_key === undefined` are different tests. Publishing "no key" as
`null` keeps all three states apart for the reader: no key, an old item, and a
key the mappings file does not hold, which is a string that matches no
mapping. Leaving the key off, which is how `DUPLICATE_OF_KEY` works, would merge
"no key" with "old item". **If the reader does not need that distinction, it
can test `== null`, which covers both.**

**Why not an empty string.** `""` is falsy like `null` but `typeof` says
`"string"`, so a reader asking "is there a key" one way and "what is the key"
the other would get two answers. The engine does not produce one today:
`vendor_key_for()` returns `None` for an empty name and for one that
normalises to nothing. `extra_for()` turns `""` into `null` anyway, so that
"never an empty string" is guaranteed by `extra_for()` itself, whatever the
engine does later. `test_an_empty_string_is_published_as_null` pins it.

**On the `category_unconfirmed` care the brief points to.** That key is
designed so an absent value reads safe. This one has no safe default, because
it carries information rather than a decision. So it is stated on every item
and the reader is not left to infer anything from a missing key.

**Which receipts carry `null`.** Every receipt published with a validation
status other than `ok`. `process_extraction_result()` in
`worker\extraction_pipeline.py` categorises only on its `ok` branch, and
`categorisation` is `None` on the other. See flag 5.1: this matters more than
the brief assumed.

---

## 4. A committed fixture was regenerated, and the Desktop harness owner needs telling

**`tests\test_review_seam.py`'s
`test_a_fresh_poll_produces_the_committed_item` went red on the first full
run**, which is it working. It compares a fresh poll's item against
`tests\fixtures\published_item_needs_review.json`. Its message says to
regenerate the fixture **and tell the session that owns the Desktop harness,
because the item is a contract between two products.** This is me telling you.

I regenerated it with the command the test names,
`REGENERATE_REVIEW_FIXTURE=1 .\.venv\Scripts\python.exe -m pytest tests/test_review_seam.py -q`,
restricted with `-k RegenerateTheFixture`. **The diff, read in full**: one
added line, `"vendor_key": null`, and the four fields the test already treats
as volatile (`receipt_id`, `pipeline_receipt_id`, `capture_date`,
`archive_path`). The fixture is a `needs_review` item, so its key is `null`.
That is correct, and the reader's test of it should expect `null`.

Git warned that the regenerated file is CRLF and will be normalised to LF.
That is the line-ending handling this repository already does.

---

## 5. Flags

### 5.1 Review items carry `null`, and the tick is offered on them

**The brief says "a receipt that was never categorised has none". That is true
of the pipeline. It is a gap for the reader.**

`IntelliBooks-Desktop-v3.html`, read at
`C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliBooks\App\IntelliBooks-Desktop-v3.html`,
offers the tick in two places:

- line 5053, the edit dialog, whenever `pipelineKnowsReceipt(r.id)`
- line 4825, the bulk category dialog, when the selection holds one supplier name

Nothing in either condition limits the tick to receipts that arrived `ok`.
**A receipt that arrived for review is exactly one the operator is editing**,
and its item will carry `null`. So for those receipts the reader has nothing to
show.

**The size of it, read-only on `C:\Intellibills\db\receipts.db`.** By each
receipt's first non-correction extraction: 51 `ok`, 8 `failed`, 3
`needs_review`, 2 `possible_duplicate`. **13 of 64, about one in five, would
publish `null`.** That is first extractions only. An auto-retry that succeeds
republishes with a key, so the true figure is at most 13.

**The obvious fix, and it needs a decision.** Compute the key on the non-`ok`
branch too: `categorisation_engine.vendor_key_for(extraction.supplier_name)` is
a pure function of the name and the alias table. It categorises nothing and
writes nothing. `extra_for()` would take the key alongside the categorisation.
It is about five lines and one test. **I have not done it** because the brief
states the opposite in terms, so it is a change to agreed behaviour. A
`failed` receipt with no supplier name would still carry `null`, which is
right.

### 5.2 Nothing republishes the item on a correction (the brief's section 3)

**Established from the syntax tree, not by searching text.** `publish_receipt()`
has exactly two callers: `process_extraction_result()` and
`_publish_unpublished_receipts()` in `app.py`. `process_extraction_result()` has
four callers, all in `app.py`: three in `process_once()`, which are intake, and
one in `_retry_failed_receipts()`, which is the auto-retry of a new extraction.
`worker\resolution\service.py` imports neither `worker.publish` nor
`worker.extraction_pipeline` (read from its import block).

**So a correction made through a resolution note, the route the Remember tick
uses, never republishes the item.** After the operator corrects a supplier
name, the item keeps the key computed from the name as extracted. Behaviour is
left as found.

**One thing the consultant session may want for that decision.** In
`2026-11-13_REPORT_claude_code_vendor_lookup.md`'s work (10bs.11), a correction
teaches a row keyed on the CORRECTED name, through `vendor_key_for()`. So after
a correction with the tick:

- the mappings file holds the corrected name's key
- the item still holds the extracted name's key

Where the two names key differently, the reader will not find the
just-taught row under the item's key. That is the stale case. **What I would
check before deciding**: the reader knows the corrected name already, because
the operator typed it into that dialog. But it cannot compute that name's key,
which is the same reason option B was refused.

### 5.3 Tests written before the code, but all failed for one reason

The 14 tests were written first and all failed, but every failure was an
`AttributeError` on the missing constant, which shows only that the constant
was missing. **The six mutations in section 6 are the evidence that the tests
discriminate.**

---

## 6. Evidence

**Suite after the commit**: 1691 passed, 2 skipped, 1267 subtests. The
previous report recorded 1677 passed and 1265 subtests after `b600b8a`; the
difference is exactly this change: 14 new tests, and the 2 subtests of
`test_a_receipt_that_is_not_ok_carries_null`. **I first wrote "15 tests" in this
report**, having taken the count from the red run's "15 failed", which counts
two subtest failures and one test separately. Corrected after counting with
`--collect-only`.

**Before the commit**: 1 failed, 1690 passed, 2 skipped, 1267 subtests. The
one failure was the fixture guard in section 4. Once the fixture was
regenerated, the review seam file passed.

**Mutations**, each against the whole suite through `tests\mutation_harness.py`,
each anchor unique, file restored byte for byte. The script is at
`C:\Users\PDK7\AppData\Local\Temp\claude\43687783b5645321\c06fa307-c485-4b69-9e2e-96335aeb0cf3\scratchpad\mut_vendor_key_item.py`.

| Mutation | Caught by |
|---|---|
| key left off the item | 14 failures: 12 tests in the new file, `test_item_only_keys_is_exactly_what_the_item_adds`, and the review seam fixture guard |
| `""` published as itself | 1: `test_an_empty_string_is_published_as_null` |
| absent instead of `null` | 8, including both non-`ok` subtests, the JSON bytes test and the fixture guard |
| `matched_vendor` published in place of `vendor_key` | 5 |
| key case-folded | 6 |
| dropped from `ITEM_ONLY_KEYS` | 3, including `test_sidecar_category_keys.py`'s four-call-site comparison |

All six were caught. **One gap the mutations showed**: under the
`matched_vendor` mutation, `test_a_matched_receipt_carries_the_same_key`
passed. That is expected, because on a layer 1 match `matched_vendor` equals
`vendor_key`. The unmatched and sweep tests are the ones that tell the two
apart, and they did.

---

## 7. Confidence

- **High that every published item now carries the key as described in
  section 3.** It rests on tests driving the real poll and the real sweep, the
  JSON bytes asserted, and the mutations in section 6.
- **High that nothing republishes on a correction.** It rests on enumerating
  the call sites from the syntax tree and reading the resolution service's
  imports. A future caller would change this answer.
- **Medium on the size of flag 5.1.** It rests on a first-extraction count,
  which overstates the number of items left with `null` by however many
  auto-retries later succeeded. I did not count those.
- **Not checked: how the Desktop reader will behave.** I read the two tick
  sites and nothing else in Desktop.
