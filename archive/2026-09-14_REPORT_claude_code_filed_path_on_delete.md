# Claude Code report, 2026-09-14: clear `filed_path` when the client folder copy is deleted

Brief: `PROMPT_claude_code_2026-09-14_filed_path_on_delete.md`. Paul's decision, amendment 465.

Times read from the Windows clock, Europe/London.

---

## STOPPED. NOTHING BUILT, AND NO COMMIT PROPOSED

**This change already exists. It shipped on 2026-09-10 in commit `a96627a`, four days before the
brief was written.** `discard_receipt()` sets the status to `discarded`, deletes the copy, then calls
`repo.clear_receipt_filed_path()` and records `filed_path_cleared` in the audit row. All three tests
the brief asks for are already in `tests/test_discard_client_copy.py`.

**The objection does not hold, and Paul's reading of the query is right.** I checked it directly
rather than taking it, which section 3 sets out. **The delete path cannot leave a receipt at `ok`
with the copy gone**, so the brief's stop condition is not met: the fix as written would have been
correct. It is simply already made.

**There is a separate finding that is real and that I cannot explain**, at section 5: the live row
the brief cites disagrees with the code that produced it. Its audit row says `filed_path` was
cleared, and the column holds a value today. **I have not invented a cause for it**, which is the
discipline the brief itself applies to the `ringgo` receipt.

**Nothing was written to the repository and nothing was written to the database.** The working tree
is unchanged and the suite stands at **1458 passed, 1 skipped, 1116 subtests**, the same figure as
before this work.

---

## 1. The deletion site, enumerated from the syntax tree

The brief says it has not read the code and does not name the site, and that
`tests/test_attached_document.py` mentions a `delete_client_copy` as 10f.27's mechanism.

**`delete_client_copy` is not a function.** It is `NOTE_DELETE_CLIENT_COPY_KEY` at
`worker/resolution/service.py:119`, the string `"delete_client_copy"`, which is both the field
IntelliBooks Desktop writes into a discard note and the keyword parameter on `discard_receipt()`. The
test file's sentence is about the note field.

**The real chain, off the tree over all 58 tracked production files:**

| Layer | Where |
| --- | --- |
| The unlink itself | `remove_client_copy()`, `worker/client_copy.py:238`. Owns `Clients\` and does the deciding. |
| The reporting wrapper | `_delete_the_client_copy()`, `worker/resolution/service.py:1654`, calling the above at `:1680`. |
| The only caller of that | `discard_receipt()`, `worker/resolution/service.py:1796`. |

**`remove_client_copy()` has exactly one production caller and 15 test call sites.**
`_delete_the_client_copy()` has exactly one caller anywhere. Enumerated by walking every `ast.Call`
and taking its enclosing function, not by grep.

### Every route that reaches it

**Three, and all three are `discard_receipt()`:**

| Route | Call site |
| --- | --- |
| CLI, `discard_receipt.py` | `discard_receipt.py:86`, inside `main()` |
| CLI, `resolve_receipt.py` | `resolve_receipt.py:293`, inside `main()` |
| The IntelliBooks Desktop back-feed note | `worker/resolution/service.py:2850`, inside `apply_resolution_note()` |

**There is no route to the deletion that is not a discard.** That is the fact the whole objection
turns on, and it is a property of the call graph rather than of any one path's behaviour.

---

## 2. The fix, already present

`worker/resolution/service.py`, inside `discard_receipt()`, in this order:

```python
repo.update_receipt_status(receipt_id, "discarded")      # the status moves FIRST
...
if delete_client_copy and filed_path:
    detail.update(_delete_the_client_copy(receipt_id, filed_path))
...
if filed_path:
    repo.clear_receipt_filed_path(receipt_id)
    detail[EVENT_FILED_PATH_CLEARED_KEY] = str(filed_path)
```

**`filed_path` is cleared on every discard, not only when the copy is deleted.** The brief asks for
the narrower thing; the code does the wider one, on the reasoning that a discarded receipt is not
filed whatever became of the file.

`clear_receipt_filed_path()` is at `worker/database/repository.py:427`, is
`UPDATE receipts SET filed_path = NULL WHERE receipt_id = ?`, and commits. Its docstring is dated to
**Paul's decision of 2026-09-10** and already carries the objection this brief raises, in the same
terms.

**`filed_at` is deliberately left alone**, which that docstring states and attributes: the decision
named one column.

### The three deliverables, and where each already is

| The brief asks for | It exists as |
| --- | --- |
| A test that a deleted receipt ends with `filed_path` NULL | `TheDeletionTest::test_the_copy_is_deleted_and_filed_path_is_cleared`, `tests/test_discard_client_copy.py:261` |
| A test that clearing it does not re-queue the receipt | `FiledPathIsClearedOnEveryDiscardTest::test_the_discarded_receipt_is_not_offered_to_the_client_copy_sweep`, `:665` |
| ~~and the same through a real poll~~ not asked for, and present anyway | `::test_the_copy_is_not_rewritten_by_a_real_poll`, `:695` |

**No red-before-green output is quoted in this report, and that is not an omission.** There is no
change to be red about. A test written now would be green on the first run, which proves nothing,
and `CLAUDE.md`'s own rule is that a check that cannot fail is not a check.

---

## 3. The objection, checked rather than taken

The brief says to check this myself because the whole fix rests on it.

**The query, read directly out of `worker/database/repository.py:344`:**

```sql
SELECT receipt_id, client_id, file_path, filename, filed_path
FROM receipts
WHERE status = 'ok'
  AND filed_path IS NULL
  AND created_at >= (SELECT MIN(created_at) FROM publish_events)
  AND EXISTS (
```

**Paul's reading is correct. `status = 'ok'` is there, and a discarded receipt fails it.**

**And the ordering is what makes that filter enough**, which is the part worth stating separately
because the filter alone would not do it. `discard_receipt()` sets the status to `discarded` **before**
it deletes anything and **before** it clears the column. So there is no window in which the row is
`ok` with a NULL `filed_path` and a deleted file. Had the clear come first and the status second, a
poll landing between them could have written the copy back.

**`get_unpublished_ok_receipts()` is the other queue and it is covered too**, asserted in the same
test, which checks both lists come back empty.

**The stop condition in the brief is therefore not met.** The delete path cannot leave a receipt at
`ok` with the copy gone.

---

## 4. Why the brief exists: the evidence it was written from

The brief cites `Client_004` with 14 rows carrying a `filed_path` and two naming a file that is not
there, one of them the discarded `2026-08-15_octopus-energy_248.33.jpeg`.

**That reading is right, and it is what a reader of the database would conclude.** Read from
`C:\Intellibills\db\receipts.db` with `sqlite3` in read-only mode on 2026-09-14:

```
receipt_id  a96ab8f7-3af1-42e7-bd98-dee8be2529b8
client_id   Client_004
status      discarded
filed_path  ...\Clients\Test Sole Trader\IntelliBooks\Receipts\2026-27\2026-08-15_octopus-energy_248.33.jpeg
filed_at    2026-09-09T11:22:50.935653+00:00
```

**It is the only discarded receipt in the whole database still carrying a `filed_path`.** Checked
over every row, not over this client's.

**So the symptom is real and the diagnosis in the brief is the natural one: the delete path does not
clear the column. It is not the right one, and section 5 is why.**

---

## 5. The finding I cannot explain, left open rather than filled in

**That row's own audit trail says the column WAS cleared.**

```
resolution_events, action=discard, created_at 2026-09-10T13:27:40.744701+00:00
  actor desktop, source desktop, outcome discarded
  corrections_json keys: client_copy_deleted, filed_path_cleared, note_resolved_at
```

`filed_path_cleared` is set on the line immediately after `repo.clear_receipt_filed_path()` and
inside the same `if filed_path:` block, and `_record_event()` runs after both, so the presence of
that key means the clear was called and did not raise.

**What I ruled out, each by checking rather than by reasoning:**

- **That it ran on older code.** The commit is `a96627a`, `2026-09-10 12:21:04 +0100`; the discard is
  `13:27:40 UTC`, which is `14:27:40 BST`, an hour and six minutes later. **And both halves shipped in
  that one commit**: `git log -S` on `clear_receipt_filed_path` and on `EVENT_FILED_PATH_CLEARED_KEY`
  each name `a96627a` as the first, so a process running older code could not have written that key.
- **That the code at that commit was a different shape.** Read `a96627a`'s own
  `worker/resolution/service.py`: status at `:1287`, delete at `:1297`, clear and key at `:1313-1314`.
  The same order.
- **That something re-filed it.** The only writer of a VALUE into `filed_path` is
  `mark_receipt_filed()`, enumerated from the tree over every `UPDATE`/`INSERT` string constant in the
  58 production files: two writers, that one and `clear_receipt_filed_path()`, plus `save_receipt()`'s
  INSERT. **`mark_receipt_filed()` sets `filed_at` in the same statement, and `filed_at` is still
  2026-09-09T11:22:50**, 26 hours before the discard, so it has not run since.
- **That a later event did it.** The receipt has exactly one `resolution_event` and one
  `publish_event`, the latter from 2026-09-09.
- **That `apply_resolution_note()` does something afterwards.** It `return`s `discard_receipt(...)`
  directly.
- **That the log shows more.** `C:\Intellibills\logs\run.log` has four lines for this receipt at
  14:27:40 BST and nothing after: the deletion, two review files removed, the discard, the note
  applied.
- **That a backup would show it cleared.** The three backups predating the discard do not contain the
  receipt at all; the one from today, 12:24, shows the same state as the live file.

**So: the clear was called, it commits, and the column holds a value. I cannot account for it, and I
am not going to invent a cause.** The brief's own words about the `ringgo` receipt are the right
standard here and I am applying them to this one: nothing explains it and inventing an explanation is
worse than leaving it open.

**What it is not.** It is not a hole in the delete path as the brief describes, because the code and
the audit row agree that the clear happened. **The disagreement is between the audit row and the
receipts row, not between the code and the decision.**

**What would settle it, and none of it is mine to do.** Discarding a receipt today with the copy
deleted and reading the column back would show whether the path works now; that needs Paul, because
it needs the pipeline and Desktop. Whether that row was edited or restored outside the pipeline is
not answerable from inside the repository.

---

## 6. No commit

**There is nothing to commit.** The working tree is unchanged, verified with `git status --porcelain`
before and after this work, and no file in the repository was created or edited except this report.

**I did not write a duplicate test.** All three the brief asks for exist and are named at section 2.
Adding a fourth assertion of the same property would add a maintenance burden and no information,
and would make this step look built when it was built on 2026-09-10.

**Recommendation: mark the pipeline half of this decision BUILT at `a96627a` rather than scheduling
it**, and treat section 5 as a separate question about one live row.

---

## 7. My own mistakes in this session, disclosed

1. **I nearly reported "already built" after reading only `discard_receipt()`.** That would have been
   right by luck. The claim needs the call graph, not the function: what makes the objection hold is
   that no route reaches the deletion except through a discard, and I had not established that when I
   first believed the answer. I enumerated it afterwards, and it is section 1.

2. **My first explanation of the live row was wrong and I held it for several minutes.** I assumed the
   row simply predated the fix, which is the comfortable answer. The discard is timestamped an hour
   after the commit, and the audit row carries the key that only the new code writes. **I found that by
   converting the event's UTC timestamp to BST before comparing it with the commit date**, which is
   `CLAUDE.md`'s rule about the two sessions' clocks differing by an hour, applied to a database
   column and a git log for once rather than to two chat messages.

3. **I proposed a second wrong cause after that**, that an old long-running process held the old
   module in memory, which is a real effect on this project because the pipeline runs for hours. It
   does not survive the fact that the audit key shipped in the same commit as the clear. Disclosed
   because it was plausible, and because two wrong causes in a row is the pattern `CLAUDE.md` records
   under answering from the next hypothesis rather than going back to the file.

---

## 8. Confidence

**High that the fix is present and that nothing needs building**, because I read
`discard_receipt()` and `clear_receipt_filed_path()` in the working tree, read the same functions out
of commit `a96627a`, and named the three existing tests by line number.

**High that the objection does not hold**, because I read the SQL of
`get_published_receipts_without_client_copy()` directly rather than the comment about it, and because
the ordering that makes the filter sufficient is visible in `discard_receipt()` itself.

**High that no route reaches the deletion except a discard**, because the call graph was enumerated
from the syntax tree across all 58 tracked production files, taking each call's enclosing function.

**High that the live row is in the state I describe**, because it was read on Windows with `sqlite3`
in read-only mode against `C:\Intellibills\db\receipts.db` directly, not through any staging layer,
and cross-checked against `resolution_events`, `publish_events`, `run.log` and four database files.

**None at all on why that row is in that state.** I have ruled out six mechanisms and I have no
seventh to offer. That is a confidence about the exclusions, not about a cause, and there is no cause
in this report.
