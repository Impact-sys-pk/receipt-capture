# Report: a receipt that arrives for review publishes its vendor key

Written 2026-11-13 by Claude Code, for the consultant session. It implements
the fix in section 5.1 of `2026-11-13_REPORT_claude_code_vendor_key_on_item.md`,
on Paul's decision of 2026-11-13. Sub-step 10bs.10.

`2026-07-25_BUILD_STATUS.md` is not touched.

---

## 1. What was done

One commit, `5859469`, on `feat/console-phase0`, after `8f084ab`. Four files:

| File | Change |
|---|---|
| `worker\extraction_pipeline.py` | The non-`ok` branch of `process_extraction_result()` sets `uncategorised_vendor_key = categorisation_engine.vendor_key_for(extraction.supplier_name)` and passes it to `extra_for()` |
| `worker\publish.py` | `extra_for()` takes `vendor_key=None`; raises `ValueError` if given both a categorisation and a key; the constant's comment strikes the old wording |
| `tests\test_item_vendor_key.py` | One test rewritten, four added: 18 tests in all |
| `tests\fixtures\published_item_needs_review.json` | Regenerated: `"vendor_key": null` becomes `"vendor_key": "apcoa parking"` |

**Nothing is categorised and nothing is written.** `vendor_key_for()` is
`extract_vendor_key(normalise_description(name), self.aliases) or None`.
`self.aliases` is `dict(DEFAULT_ALIASES)`, a constant in
`worker\categorisation\engine.py`, so the call reads no file and no database.
The test asserts no `categorisations` row exists, the item's
`category_code` is still `null` and `category_unconfirmed` is still `false`.

**Why refuse both arguments.** `extra_for()` now has two sources for the key.
The poll's `ok` branch and the recovery sweep pass the categorisation; the
non-`ok` branch passes the key. Refusing both at once means no caller can
publish a key that disagrees with the categorisation it also passed.
`process_extraction_result()` sets at most one of the two.

**Every caller passes an engine.** `process_extraction_result()`'s
`categorisation_engine` parameter defaults to `None`, and before this change
the non-`ok` branch never used it. All eight calls (four in `app.py`, four in
tests) pass one, enumerated from the syntax tree. A future caller passing
none would now raise on a review receipt, where it used to raise only on an
`ok` one.

---

## 2. What test pins it

**`tests\test_item_vendor_key.py`,
`OnThePollTest.test_a_receipt_that_is_not_ok_carries_its_key_and_is_not_categorised`.**
It drives a real email poll for a `needs_review` and a `failed` receipt, as
subtests. It asserts the item's `vendor_key` equals the engine's own
`vendor_key_for("Apcoa Parking")`, and that nothing was categorised.

**Red first, for the right reason**: before the change, both subtests failed
with `AssertionError: None != 'apcoa parking'`.

The other half: `test_a_receipt_with_no_supplier_name_carries_null` drives a
receipt with no supplier name and asserts the key is present and `null`.
`test_null_is_spelt_null_in_the_file` now drives that receipt too, because a
`failed` receipt with a name no longer publishes `null`.

**Mutations**, each against the whole suite through
`tests\mutation_harness.py`, each restored byte for byte. Script at
`C:\Users\PDK7\AppData\Local\Temp\claude\43687783b5645321\c06fa307-c485-4b69-9e2e-96335aeb0cf3\scratchpad\mut_review_key.py`.

| Mutation | Caught by |
|---|---|
| the review-branch key not computed | both subtests and the review seam fixture guard |
| computed for `needs_review` only | the `failed` subtest |
| both sources accepted | `test_a_categorisation_and_a_key_together_are_refused` |

**Not pinned on its own: `possible_duplicate`.** It runs through the same
`else` branch and the same line, but no test drives one. A mutation that
excluded only `possible_duplicate` would survive.

**Suite after the commit**: 1695 passed, 2 skipped, 1277 subtests.

---

## 3. What the live figure becomes

Read-only on `C:\Intellibills\db\receipts.db`, the same measure as before:
each receipt's first extraction that is not a manual correction. **13 of 64
arrived not `ok`. Under this change 8 of them would publish a key and 5
`null`.** All 5 nulls are `failed` receipts with no supplier name.

| Arrived as | Supplier | Key |
|---|---|---|
| failed (5) | none | `null` |
| failed | `LA BELLA RESTAURANT` | `la` |
| failed | `LBB CIVIC CENTRE CAR P` | `lbb` |
| failed | `Octopus Energy` | `octopus energy` |
| needs_review | `IMO CAR WASH` (twice) | `imo` |
| needs_review | `TaxiPlus` | `taxiplus` |
| possible_duplicate | `London Borough of Camden` | `borough camden` |
| possible_duplicate | `Scc Cars` | `scc cars` |

The keys were computed with the real engine. The script imports
`tests\live_paths.py` first, so `config` resolved both roots to a temp
directory and created nothing under the live ones; it asserts that. The
script is at
`C:\Users\PDK7\AppData\Local\Temp\claude\43687783b5645321\c06fa307-c485-4b69-9e2e-96335aeb0cf3\scratchpad\live_key_figure.py`.

**That figure describes receipts, not the items on disk.** Nothing
republishes. Every item in `Intellibills\Published\` today was written before
`8f084ab` and carries no `vendor_key` at all, which the reader sees as
absent. Only items published from now on carry the key.

---

## 4. The `getattr` question: I agree it is the same hazard, in both places

**`extra_for()`.** After this change the read is
`if categorisation is not None: vendor_key = getattr(categorisation, "vendor_key", None)`.
`None` is handled before the `getattr`, so its default can fire for one reason
only: the object has no such attribute. Every object reaching it is a
`CategorisationResult`, where `vendor_key` is a declared dataclass field with
a default. **So the default can do nothing except turn a rename into `null` on
every `ok` item, with no error and no log line.**
`TheTwoLearningBranchesReadTheFieldTheSameWay` in
`tests\test_vendor_key_naming.py` describes exactly that and bans it in
`service.py`. My change made it slightly purer: before, the `getattr` also
covered `categorisation is None`; now an explicit check does.

**`category_is_unconfirmed()`.** Same shape: it returns `False` for `None`
first, then `getattr(categorisation, "match_source", None)`. A rename of
`match_source` would make it return `False` for everything. **That fails open:
no guessed category would be held, and guesses would drain into the books with
nothing on screen.** That is the more serious of the two, because nothing
reports it.

**One difference from the `service.py` case, which lowers the risk but does
not remove the hazard.** Both reads are now covered by tests that drive the
real engine. `test_an_unmatched_ok_receipt_carries_its_key` compares against
`vendor_key_for()`, and `TheKeyTest` in `tests\test_category_hold.py` asserts
`True` for a fuzzy match. So a rename would go red in the suite instead of
passing silently. The `service.py` read had no such cover when it was banned.

**The fix, not done, as instructed.** Read both as plain attributes,
`categorisation.vendor_key` and `categorisation.match_source`. The `None` checks
stay. Then extend the guard's file list to `worker\publish.py`. The guard
should also move from its current line-text match to the syntax tree,
which `CLAUDE.md` asks of every source guard. As written, the guard would also
flag the struck wording in a comment if that comment did not start with `#`
on its own line. **I can do it in one commit if you want it.** Before
changing these, I would check that no test passes `extra_for()` or
`category_is_unconfirmed()` a stand-in object without those attributes. The
search I ran found only `None` and real `CategorisationResult`s, but I did not
enumerate it from the syntax tree.

---

## 5. Other flags

- **`LA BELLA RESTAURANT` keys on `la`.** `extract_vendor_key()` keeps only the
  first word of a name of three or more words. So any supplier whose name
  starts with "La" or "LA", such as an LA council, shares one key. Under
  10bs.9 a shared key with disagreeing codes fails safe, so this does not
  answer wrongly. But the reader will show unrelated names as "on the same
  key" at the tick. This is the key rule itself, not this change. No fix
  offered; it is a decision about the key builder.
- **The review seam fixture changed again**, so the Desktop harness owner needs
  telling a second time today. The value the harness reads is now
  `"apcoa parking"`, no longer `null`.

---

## 6. Confidence

- **High that a review receipt with a supplier name now publishes its key and
  is still not categorised.** That rests on the poll test, red before green
  for the right reason, and three caught mutations.
- **High on the 8 of 13 figure as a count of receipts.** That rests on the
  real engine run read-only against the live database. It is not a count of
  items on disk; see section 3.
- **High that the `getattr` reads are the banned shape.** That rests on
  reading both functions and the guard's own docstring. **Medium that no test
  relies on the `getattr` default**: I searched by name and did not enumerate
  from the syntax tree.
