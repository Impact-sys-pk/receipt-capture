# Report: a status test on `is_recorded_and_filed()`, 2026-09-22

Written by the implementation session, Claude Code, 2026-09-22, 16:27 BST, read off the clock in the
reply that states it.

Worked from `PROMPT_claude_code_2026-09-22_is_recorded_and_filed_status_test.md`, under AUTOMATIC
Task Mode.

**Nothing in `2026-07-25_BUILD_STATUS.md` or `2026-07-25_CONSOLE_DESIGN.md` was touched.**

**The live database was not opened at all in this task**, read-only or otherwise, and nothing was
written to it. Every test runs against a temp database. **The live row is untouched**, per Paul's
decision of 2026-09-22.

---

## 1. The callers, re-enumerated in this task

**Walked from the syntax tree over all 161 git-tracked `.py` files**, 58 production and 103 tests,
matching on the call's unparsed target rather than on text, with the enclosing function computed from
the tree. `.history\` is excluded by construction, being gitignored.

| Kind | Count | Where |
|---|---|---|
| Definitions | **1** | `worker/database/repository.py:1091` |
| **Production call sites** | **3** | `app.py:1623`, `app.py:1940`, `app.py:2154`, all in `process_once()` |
| Test call sites | 9 | across `test_attached_document.py`, `test_discard_client_copy.py`, `test_stage4_client_copy.py`, `test_step10f_duplicates.py` |
| Mentions inside a docstring or string, which are **not** calls | 28 | 6 in production, 22 in tests |

**This agrees with my report of earlier today**, which named the same three production sites. **The
28 non-call mentions are why the walk matters**: a text search for the name returns 40 hits and 28 of
them are prose, which on this project is guaranteed by the convention of keeping superseded wording
beside every correction.

**Each of the three production sites is the file-hash duplicate check for one intake route**, read
rather than assumed: `app.py:1623` the embedded-image path, `app.py:1940` the folder-intake path,
which is the one that calls `_move_inbox_pair_to_processed()`, and `app.py:2154` the email-attachment
path. All three ask the same question: this document's bytes have been seen before, so is the arrival
a duplicate or a resend.

---

## 2. The change

**One SQL statement, in `is_recorded_and_filed()`.**

```
-  "SELECT filed_path FROM receipts WHERE receipt_id = ?"
+  "SELECT filed_path FROM receipts WHERE receipt_id = ? AND status <> 'discarded'"
```

**This is the shape the brief specified and my own enumeration found no reason not to build it.**

**It NARROWS rather than widens**, which is the whole reason it is safe. The docstring's existing
paragraph records that 10f.24 deliberately did not widen this function, because amendment 293 gives
every validation status a `published` row and a widened answer would make a resent review item look
like a duplicate. **A change that only ever returns False in more cases cannot cause that.** The
docstring now carries both the old reasoning and the new, with the old left as written.

---

## 3. Red before green

**The new class seeds the state the live database is actually in**: `status = 'discarded'` with
`filed_path` still populated. Written directly rather than through `discard_receipt()`, because that
function clears the column and the point is the row where the clearing did not stick.

**Every test that already existed asserted the case where the clearing worked.**
`FiledPathIsClearedOnEveryDiscardTest` and `ADiscardedReceiptDoesNotBlockAResendTest` both discard
through `apply_resolution_note()` and then read a NULL column, so **neither could ever have seen
this**. That is why the defect reached the live database with the suite green.

**Red, against unchanged production code:**

```
FAILED ...::test_a_discarded_receipt_with_a_filed_path_is_not_recorded_and_filed
E  AssertionError: True is not false : a discarded receipt counted as filed because its
   filed_path outlived the discard, so the identical document cannot be sent again

FAILED ...::test_the_identical_file_can_be_sent_again_even_though_the_column_stuck
E  AssertionError: 0 != 1 : the resend was swallowed as a duplicate of a receipt the operator deleted
   Captured log: WARNING app:app.py:2155 hash duplicate of r-1, skipping shared.pdf

2 failed, 3 passed, 7 subtests passed
```

**The captured warning is the defect itself**, produced by a real `process_once()` rather than by
reasoning: the resent document is skipped as a hash duplicate of a receipt the operator deleted.

**Green after the change:** the whole class passes, and so do the five most-affected files together,
195 tests and 102 subtests.

### The five tests, and why each is there

| Test | What it holds |
|---|---|
| `test_a_discarded_receipt_with_a_filed_path_is_not_recorded_and_filed` | The defect. The first red |
| `test_an_ok_receipt_with_a_filed_path_still_counts_as_filed` | **The control.** Without it the change could be "always return False" and both red tests would pass |
| `test_a_needs_review_receipt_is_still_not_filed` | Section 5 |
| `test_every_other_status_answers_exactly_as_the_column_does` | 7 subtests, one per remaining status, so the query is shown to change the answer for one status and no other |
| `test_the_identical_file_can_be_sent_again_even_though_the_column_stuck` | The consequence, through a real poll. The second red |

---

## 4. The discrimination result

**Put the old query back; caught by exactly the two tests written for it.**

```
=== is_recorded_and_filed-loses-its-status-test ===  expects: caught
one place changed: 1 hunk(s), 3 line(s)
    -            "SELECT filed_path FROM receipts "
    -            "WHERE receipt_id = ? AND status <> 'discarded'",
    +            "SELECT filed_path FROM receipts WHERE receipt_id = ?",
last line: 2 failed, 1609 passed, 2 skipped, 1208 subtests passed in 100.66s
caught by 2 reported failure(s):
  FAILED ...::test_a_discarded_receipt_with_a_filed_path_is_not_recorded_and_filed
  FAILED ...::test_the_identical_file_can_be_sent_again_even_though_the_column_stuck
verdict: OK: caught, as expected
restored, byte for byte
```

**The three controls passed under the mutation**, which is what makes the result mean something: they
assert the behaviour the change must not alter, and the old query does not alter it either.

---

## 5. `_move_inbox_pair_to_processed()` is unchanged, and how I established it

**Read its docstring, which states the dependency in terms:**

> Anything left behind is found by `find_by_hash()` on the next poll, **is not
> `is_recorded_and_filed()` because `filed_path` is NULL**, and is then deliberately reprocessed.

**The dependency is on the column being NULL, not on the status.** This change does not touch what
happens when `filed_path` is NULL: the row is still returned by the SELECT for any status but
`discarded`, and `row[0] is not None` is still False. **A narrowing change cannot turn a False into a
True.**

**Asserted rather than argued**, three ways:

1. `test_a_needs_review_receipt_is_still_not_filed` seeds a `needs_review` receipt, asserts its
   `filed_path` really is NULL so the test is measuring something, and asserts the answer is False.
2. `test_every_other_status_answers_exactly_as_the_column_does` covers `needs_review` among seven
   statuses **carrying a `filed_path`**, and asserts every one still reads as filed.
3. `tests/test_inbox_processed_move.py` passes unchanged, 195 tests in that group.

**`SettledMeansPublishedTest` passes**, in `tests/test_step10f_duplicates.py`. The distinction it
holds between settled and filed is untouched: `is_published()` reads `publish_events` and was not
modified.

---

## 6. Suite totals

| | Passed | Skipped | Subtests |
|---|---|---|---|
| Before, commit `caf9489` | 1606 | 2 | 1201 |
| After | **1611** | 2 | **1208** |

**+5 tests and +7 subtests, which is exactly the new class**: five test methods, one of which
subtests seven statuses.

---

## 7. Flagged, not fixed

**The five things flagged in this morning's report are all still open and none was touched**: the
`.png`/`.pdf` stem collision, the 21 orphan `.json` sidecars, the four client-folder documents with
no row, the `26-27` folder holding a file dated `0026-08-30`, and the live row itself.

**The live row is deliberately still wrong.** Correcting it would destroy the only instance of a
fault whose mechanism nobody has established. **This change makes the row harmless rather than
absent**, which is the right order.

**One thing I noticed in this task and did not act on.** The three production call sites each pair
`find_by_hash()` with `is_recorded_and_filed()`, and the pairing is written out three times rather
than being one helper. That is not a defect and it is not in this brief.

---

## 8. Mistakes I made, disclosed

**Two.**

1. **I wrote the new class using an `all_receipts()` helper that belongs to a different class**, so
   the second test errored with `AttributeError` on its first run instead of failing on its
   assertion. **Caught by the red run, which is what red-before-green is for.** Fixed by giving the
   new class its own copy, with a comment saying why I did not hoist it onto `DiscardTestCase`: that
   base class has six other subclasses and this brief does not ask for it.
2. **A shell heredoc failed on quoting for the fourth time this week**, so no file was written and I
   used the file tool instead. Nothing partial reached the disk, established from `git status`
   rather than assumed. **The lesson has now cost four round trips and I should have stopped using
   heredocs for content containing quotes after the first.**

---

## 9. Confidence

- **That there are three production callers: high.** Walked from the syntax tree in this task, and it
  agrees with an independent walk this morning.
- **That the change fixes the reported consequence: high.** The second test drives a real
  `process_once()` and the resend now lands.
- **That nothing else changed behaviour: high.** 1611 green, and the mutation is caught only by the
  two tests written for it, so nothing else in the suite depends on the old answer.
- **That `_move_inbox_pair_to_processed()` is unchanged: high**, from its stated dependency on the
  NULL column plus three assertions.
- **That the live row's mechanism is still unexplained: high, and that is unchanged by this work.**
  This makes the symptom harmless; it does not explain it.

---

## 10. The commit

Proposed, not made. Awaiting a yes.

```
fix(dedup): a discarded receipt does not count as filed

is_recorded_and_filed() answered on filed_path alone, so its answer depended on
the clearing in discard_receipt() having worked rather than on the status that
decides. The live database holds one row where it did not stick: status is
discarded, filed_path is populated, and the audit row, the log and the deleted
client copy all say the clearing ran.

One stale column meant a document the operator deleted could never be sent
again, at all three intake routes, which is the opposite of what a96627a
decided: "a discarded receipt gives up its client folder copy and stops
blocking a resend".

The query gains AND status <> 'discarded'. It narrows rather than widens, so
10f.24's reasoning for not widening it is undisturbed, and
_move_inbox_pair_to_processed() depends on filed_path being NULL rather than on
the status, which this does not touch.

Every existing test discarded through apply_resolution_note() and then read a
NULL column, so none could see this. The new class seeds the live row's shape.
Putting the old query back is caught by two tests, with three controls passing.

The live row is deliberately not corrected: its mechanism is not established and
an UPDATE would destroy the only instance of the fault.

No behaviour changes for any status but discarded. 1611 passed, 2 skipped,
1208 subtests.

Files: worker/database/repository.py, tests/test_discard_client_copy.py
Suggested branch: feat/console-phase0 (current)
```

**No push and no PR proposed.** `feat/console-phase0` is the current branch and two other sessions
commit to it.

**The suite will be run again after the commit.** This change adds no file, so the source guards that
sweep the git-tracked set are at low risk, and it will be run regardless.
