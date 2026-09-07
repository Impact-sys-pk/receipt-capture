# Report: the pipeline half of the learning switch

**Sub-step 10j.11, pipeline half. Claude Code, 2026-09-05, 20:50 BST.** Written from
`PROMPT_claude_code_2026-09-05_desktop_learning_pipeline.md`, which is now spent.

**Built and green.** All four tasks. Two files changed: `worker\resolution\service.py` and
`tests\test_desktop_learning.py`, which is new. **`upsert_firm_vendor()` is not called on this route
and there is a test that fails if it ever is.** `IntelliBooks-Desktop-v3.html` was not opened.

---

## The suite, before and after

| When | Command | Result |
|---|---|---|
| Before any change | `.\.venv\Scripts\python.exe -m pytest -q` | **487 passed, 324 subtests passed, 0 skipped**, 11.63s |
| After the source change, before the new tests | same | **487 passed, 324 subtests passed**, 13.39s |
| After the new tests | same | **513 passed, 328 subtests passed, 0 skipped**, 14.14s |

The middle row is the one worth reading: **the three source changes moved no existing test.** The
26 new tests and 4 new subtests are the whole of the difference between the first and last rows.

**One correction to the brief's figure, disclosed.** It said the baseline was 487 passed, 324
subtests. That is what the run gave, so the figure was right; I state it because I checked it rather
than repeating it.

---

## Task 1. The note gains two fields

`ResolutionNote` now carries `category_code: Optional[str] = None` and
`remember_gl_for_supplier: bool = False`. **`NOTE_SCHEMA` is still `1`** and a test asserts it.

- **`values.category_code`**, text or absent, stripped, empty string becomes `None`. A non-string is
  a `ResolutionNoteError`, in the shape of the `category_name` check beside it.
- **`remember_gl_for_supplier`** is read from the **top level** of the note, not from `values`. Absent
  means `False`. A non-boolean is a `ResolutionNoteError`. It is parsed before the `discarded` early
  return, so a discard note carrying a malformed flag fails the same way a filed note does.
- **A note that puts the tick inside `values` has not set it**, and there is a test that says so. The
  contract states it at the top level and half-reading it would be worse than ignoring it.

**The comment above the `category_name` parse is replaced.** It said "A name, never a code: Desktop
has no codes." It now says what is true: Desktop sends the code in `category_code` and the name in
`category_name`; every note written before the Desktop half of 10j.11 ships carries a four-digit code
in `category_name` and no `category_code` at all; both cases are handled.

**The older-note rule, and when it can be removed.** If `category_code` is absent and `category_name`
matches `^\d{4}$`, the value is read as the code and `category_name` becomes `None`, with an INFO
line naming the receipt. The docstring says it can go **once no unapplied note predates the Desktop
change**, and says why that is checkable rather than a matter of judgement: nothing in `Resolutions\`
is ever deleted, so when the oldest file in `Intellibills\Resolutions\` postdates the Desktop
release, no note needing the rule can still arrive.

**The rule is deliberately narrow.** Four digits only, so a three-digit legacy code per amendment 96
is left as a name, and a code sent explicitly wins over a four-digit name. Both have tests.

## Task 2. `_resolve_category()` stops returning None

It now takes `(note, client_id)` and returns a `_CategoryDecision` dataclass rather than a 3-tuple:
`code`, `name`, `validation_note`, **`chart_confirmed`**. The reader is
`get_chart_accounts_for_client()` through `load_accounts()`. **`get_eligible_accounts_for_client()`
gained no caller** and is named in the docstring only, to say why it is not the reader here.

| Branch | Result |
|---|---|
| No code and no name | `(None, None, None)`, as today |
| A code the chart holds | The code, and **the name from the chart**, `chart_confirmed=True` |
| A code the chart does not hold | **No code**, the note's name if it has one, and a validation note naming the rejected code and saying it is not in the client's chart. **The fallback table is not applied** |
| A name and no code | As today, wording unchanged, so the existing backfeed test still holds it |
| **The chart could not be read** | **See below. Not in the brief, and it had to be decided** |

**The fifth branch, flagged rather than assumed.** `get_chart_accounts_for_client()` returns an empty
mapping both when the chart is empty and when the bundle is missing, so without a fifth branch the
third one fires for every code whenever OneDrive has not synced. **I followed the ruling already made
for the identical situation**: `resolve_against_chart()` in `worker\categorisation\fallback.py` says
in as many words that an empty read is not evidence of absence, and leaves the code standing rather
than stripping every category in the practice at once. So the code stands, with a validation note
saying it was stored unchecked, and **`chart_confirmed` is False, so nothing is learned from it.**
That is the reason the decision carries a separate `chart_confirmed` field instead of the caller
testing `code`. **If Paul would rather an unreadable chart rejected the code, it is a one-line change
and one test.**

**On not applying the fallback, which I agree with and did not build either way.** The brief invited
disagreement. I have none: `fallback_accounts.csv` substitutes for an account the classifier
proposed, and this code came out of the operator's own dropdown, which `catOptions()` builds from the
client's adopted chart. A code that has since left that chart is an inconsistency between two of
Paul's own artefacts, and substituting would hide it. There is a test that fails if a fallback is
ever applied here, with a fallback row present in the bundle so the test cannot pass by accident.

## Task 3. `_apply_filed_note()` learns, on the tick and to one table

Where the removed branch was:

```
if note.remember_gl_for_supplier and code and category.chart_confirmed:
```

then `repo.upsert_client_vendor()` with the receipt's `client_id`, the categorisation's
`vendor_code`, the resolved code and **the chart's name for it**. No vendor code means nothing is
learned and a WARNING is logged, in the shape of the one at the same point in `resolve_receipt()`.

**The stale comment is gone.** It said 11.3 and 12.3 step 6 disagree and that nothing here decides
it. Replaced with what was decided: 12.3 step 6's learning clause was struck on 2026-07-28, "11.3
wins: a back-feed note never learns a mapping", "learning stays opt-in from an operator who ticked a
box", confirmed by Paul on 2026-09-05 in amendment 231. The replacement says the comment was what
amendment 230 took its word from, so the next reader knows why the wording is struck rather than
deleted.

**Nothing writes the firm table.** The comment at the branch says so and names item 166.

## Task 4. The audit trail. Proposed and built, flagged here

**A learned mapping writes its own `resolution_events` row.** `action='learn_vendor'`,
`outcome='learned'`, `actor='desktop'`, `source='desktop'`, `gl_override_code` the code, and
`corrections_json` holding the tick, the client, the vendor code, the vendor name and both the code
and the account name. Written by `_record_vendor_learned()`, directly rather than through
`_record_event()`.

**Why this shape.** The precedent is amendment 227: the chart substitution became an event of its own
rather than a value in the `categorisations` correction columns, because those columns mean "a person
changed the category" and anything else written into them is indistinguishable from a correction. The
same argument applies here. **The one difference from amendment 227 is `actor`**: the substitution
writes `pipeline` precisely because no person decided it, and here a person ticked a box, so the
operator is on the record, which is the whole point of 11.3's opt-in. **11.3 also says "record the
choice in `resolution_events.corrections_json`", and this row is where it is recorded.**

**Not written through `_record_event()`**, whose docstring says one row per resolution outcome and
which writes the `filed` row beside this one. Learning is not an outcome of the resolution; it is a
second thing the same note asked for, and it can fail to happen while the filing succeeds.

**What is deliberately not recorded, so it is a decision and not an omission.** A tick that taught
nothing, because there was no code or no vendor code, leaves a WARNING in the log and no event row.
The brief asked for the warning and not for a row. **Say the word and it becomes a row with
`outcome='not_learned'`**, which would make "the operator asked and nothing happened" queryable
rather than only greppable.

---

## Red before green, by mutation

The tests were written after the code, so the suite was made to discriminate rather than to pass.
**Every mutation was applied to a pristine copy of `service.py`, the whole suite was run, the file was
restored, and the restore was checked byte for byte at the end.** The harness is in the scratchpad,
not in the repository.

| Mutation | Suite | What went red |
|---|---|---|
| Branch 1 invents a name when nothing was supplied | 2 failed | `ResolveCategoryTest::test_no_code_and_no_name_decides_nothing`, and `test_resolution_backfeed.py::CategoryLookupTest::test_a_blank_category_is_not_looked_up_and_not_stored_as_a_name` |
| Branch 2 stores the note's name instead of the chart's | 1 failed | `test_a_code_in_the_chart_is_stored_with_the_charts_own_name` |
| Branch 2 does not mark an in-chart code confirmed | 6 failed | that one, plus all five learning tests |
| Branch 3 stores a code the chart lacks | 3 failed | `test_a_code_the_chart_does_not_hold_is_rejected_and_named`, `test_the_fallback_table_is_not_applied_to_a_code_a_person_chose`, `test_a_code_the_chart_does_not_hold_teaches_nothing_even_with_the_tick` |
| Branch 3 applies the fallback table | 1 failed | `test_the_fallback_table_is_not_applied_to_a_code_a_person_chose` |
| Branch 4 leaves no validation note | 2 failed | `test_a_name_and_no_code_is_stored_as_a_name`, and the existing `CategoryLookupTest::test_a_name_with_no_chart_of_accounts_stores_the_name_and_learns_nothing` |
| Branch 5 strips the code on an unreadable chart | 1 failed | `test_a_chart_that_cannot_be_read_leaves_the_code_standing_unconfirmed` |
| Learning no longer needs the tick | 2 failed | `test_without_the_tick_the_same_note_learns_nothing`, `test_no_audit_row_and_no_learning_when_the_tick_is_off` |
| Learning no longer needs a confirmed chart | 1 failed | `test_an_unreadable_chart_teaches_nothing_even_with_the_tick` |
| **`upsert_firm_vendor()` called as well** | 1 failed | **`test_the_firm_table_is_never_written_on_this_route`** |
| The learned mapping leaves no audit row | 2 failed | `test_learning_leaves_its_own_audit_row`, `test_the_tick_writes_one_client_vendor_row` |
| **`vendor_key` written where `vendor_code` belongs** | 5 failed | every learning test, including `test_what_is_written_is_the_vendor_code_layer_one_looks_up` |
| The tick defaults to on when absent | 4 failed | two parse tests and two learning tests |
| A non-boolean tick is coerced rather than refused | 4 subtests failed | `test_a_non_boolean_tick_is_a_note_error` |
| The older-note rule is dropped | 1 failed | `test_an_older_note_puts_the_code_in_category_name_and_is_read_as_a_code` |
| The older-note rule fires on three digits too | 1 failed | `test_a_three_digit_legacy_code_in_category_name_is_left_as_a_name` |
| `category_code` is never read off the note | 11 failed | eleven, across all three test classes |

**No unrelated test went red on any mutation.** In every row the failures are the tests whose subject
the mutation was, plus in two rows an existing backfeed test that holds the same behaviour, which is
the right answer and not a stray.

**Three mutations survived the first pass, and I am reporting all three because one was a real hole.**

1. **A real hole. "Learning no longer needs a confirmed chart" passed the whole suite.** The only way
   to hold a code that is not confirmed is the unreadable-chart branch, and I had a unit test for the
   branch and no end-to-end test that took the tick through it. **Fixed by adding
   `test_an_unreadable_chart_teaches_nothing_even_with_the_tick`**, and the mutation then fails
   exactly that test and nothing else. **Without the mutation pass this would have shipped: the
   branch was tested and the consequence of the branch was not.**
2. **A weak mutation of mine, not a hole.** My first attempt at branch 4 changed half the sentence
   and left "chart of accounts" in it, so both tests that assert on that phrase still passed.
   Re-run with the validation note removed entirely: 2 failed, as the table shows.
3. **A hole in my harness, not in the suite.** The non-boolean tick mutation printed "4 failed" and
   my regex read only `FAILED` and `ERROR` lines, so it reported nothing red. pytest-subtests writes
   `SUBFAILED`. The four subtests of `test_a_non_boolean_tick_is_a_note_error` had caught it all
   along. **A harness that cannot see a failure reports a passing mutation, which is the
   check-that-cannot-fail rule wearing a different hat.**

## The row count, printed

`test_the_row_count_before_and_after`, run with `-s` against a temporary database:

```
categorisations_client_vendors in C:\Users\PDK7\AppData\Local\Temp\tmpbbbf6vul\receipts.db: before=0 after=1
```

**No test in this file touches `data\receipts.db` or anything under OneDrive.** Every one runs inside
`TempEnvironment` and `TempChartBundle`.

---

## Flags. Reported, not fixed

**1. `vendor_code` is right and `vendor_key` is wrong, and the brief's Task 3 wording says "the
vendor key".** `resolve_receipt():773` reads `getattr(categorisation, "vendor_code", None)` and that
is correct. `upsert_client_vendor()`'s `vendor_code` parameter fills the column the schema describes
as the normalised merchant code, which is what layer 1 looks up. `CategorisationResult.vendor_key` is
the UUID primary key of a mapping that **already exists**. **Counted from
`worker\categorisation\engine.py` rather than asserted, and I got it wrong the first time, which is
disclosed here because the count is the argument.** `categorise()` has **nine** `return
CategorisationResult(...)` paths, counted programmatically. **Seven set `vendor_code`**, from
`extract_vendor_key()` at `:266`. **Four set `vendor_key`**, the four where a learned mapping
matched. **Two set neither**, the early returns at `:258` and `:269` for no supplier name and no
extractable vendor code. ~~all seven return paths~~ I first wrote seven as the total, having counted
the paths that carry `vendor_code` and reused that as the count of the paths. **`vendor_key` is None
on exactly the receipts worth learning from, the ones nothing matched**, and that is the point the
count supports. So I wrote `vendor_code`. The
`getattr` with a default is defensive rather than wrong, since the field is on the dataclass; I used
the attribute directly in the new code and left `:773` alone.

**2. Amendment 231 says the firm table "has no writer anywhere in the repository". There is one, and
it is dead code that would raise if it were ever called.**
`CategorisationEngine.learn_from_correction()` at `worker\categorisation\engine.py:527` writes both
tables. **Enumerated rather than asserted:** `grep -rn learn_from_correction --include=*.py`,
excluding `.venv` and `.history`, gives **5 lines**, printed whole: four in
`docs\specs\categorisation_engine.py`, which is a specification and not production, and one the
definition itself. **Nothing calls it.** And it could not work if it did: it calls
`self.repo.upsert_client_vendor(client_id=..., vendor_key=..., ...)`, and that method takes
`vendor_code` and has no `vendor_key` parameter, so the call raises `TypeError` before reaching the
firm write. **This does not change any decision in the brief**, because a dead writer is not a live
one and the firm table still holds 0 rows. It is flagged because the design document states a
negative about a set, and the set was not enumerated. **The fix is one of "delete it" or "fix the
keyword", and it is a decision, not an obvious repair, so it is left.**

**3. The tick is not recorded anywhere on the CLI route.** `_record_event()` builds
`corrections_json` from `corrections.values` only, so `resolve_receipt()`'s
`remember_gl_for_supplier` never reaches an audit row even when it learns. 11.3 says to record the
choice. **Out of scope: the brief says not to change `resolve_receipt()`'s existing learning.** The
new route records it. Small and obviously right if Paul wants it: pass the flag into `_record_event()`
and add one key.

**4. Read this before deciding whether the tick has been proved end to end.** Everything above is
tested against notes this session wrote. **No note written by IntelliBooks Desktop has been through
this code**, because the Desktop half is not built and `Intellibills\Resolutions\processed\` is
empty. The old-note rule is the one part of this that runs against real Desktop output, and it is
tested against a synthetic note in the shape amendment 231 read out of
`IntelliBooks-Desktop-v3.html`. I did not open that file.

---

## Confidence

**High that the suite is green at 513 passed, 328 subtests, 0 skipped, and that the three source
changes moved no existing test**, because I ran it before, in between and after, and read the
summary line each time rather than the exit code.

**High that `upsert_firm_vendor()` is not called on this route**, because a mutation that calls it
turns a test red, and because the grep above enumerates every occurrence in the repository.

**High that `learn_from_correction()` has no caller**, because the grep is printed whole and counted,
and the count is 5.

**Moderate on the fifth branch being what Paul wants.** High that it is consistent with
`resolve_against_chart()`, which I read; the ruling it follows was made about the classifier's
suggestion and not about an operator's pick, and nobody has been asked about this case.

**Not claimed: anything about `IntelliBooks-Desktop-v3.html`.** I did not open it. Every statement
here about `catOptions()` and `fileReviewReceipt()` is quoted from amendment 231 of
`2026-07-25_CONSOLE_DESIGN.md`, which says the consultant session read the file on 2026-09-05.
