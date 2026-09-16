# Brief: a discarded receipt gives up its client folder copy, and stops blocking a resend

**Written 2026-09-10 by the consultant session, from Paul's decisions taken the same
morning. Read this whole file before starting.**

**Read first, in this order:** `CLAUDE.md`, the section "How this project is worked" and
the seven traps. Then section 18 of `2026-07-25_CONSOLE_DESIGN.md`, in particular 18.2a,
18.2b and 18.6. Then section 12 of that document, the resolution back-feed contract.

---

## 1. What this is for

**An operator deletes a receipt from the books in IntelliBooks Desktop.** Today that
removes a row from one file and nothing else. The document stays in the client folder,
and the pipeline is never told, so the database goes on saying the receipt is `ok` and
filed. The two products disagree about one receipt, which is what amendment 306 exists to
stop.

**Paul's decisions, 2026-09-10, four of them:**

1. Deleting a receipt asks the operator whether to delete the copy in the client folder
   as well.
2. On discard, `filed_path` is cleared.
3. A discarded receipt no longer blocks a resend of the same document.
4. The delete writes a note back so the pipeline knows.

**This brief is the pipeline half only.** The IntelliBooks Desktop half, being the
control, the second question and the note itself, is the consultant session's and is
being written separately. **The two halves land together or not at all**, and the reason
is the first consequence in `CLAUDE.md`: a contract built by two sessions that cannot see
each other is compatible by luck until somebody checks.

**One thing to notice before you start, because it removes work rather than adding it.**
The pipeline already knows which file to delete: `filed_path` on the receipt row is the
path `copy_for_published_receipt()` recorded when it wrote the copy. **Desktop does not
need to know it and must not have to guess it**, which matters because the composed name
carries a `-2` on a collision and nothing on Desktop's side can tell one from the other.
So no path travels in the published item and no publish ordering changes.

---

## 2. Deliverable 1: a `discarded` note may ask for the client folder copy to go

**The note gains one optional boolean.** Name it as you see fit and state the name in the
report, because the Desktop half will be written to match whatever you choose. Its
meaning: the operator asked for the copy in the client folder to be deleted as well.
**Absent or false means today's behaviour**, which is that nothing in the client folder is
touched.

**Where the note is handled already exists.** `NOTE_ACTIONS` in
`worker\resolution\service.py` already carries `discarded`, `apply_resolution_note()`
already routes on it, and `discard_receipt()` already sets the status and records a
`resolution_events` row. **What it does not do is touch any file**, and its own docstring
says so: "Never deletes the original file or any extraction row."

**What has to be true of the deletion:**

- **It deletes exactly the file `filed_path` names, and nothing else.** Not a composed
  name, not a glob, not a directory. If `filed_path` is NULL there is nothing to delete
  and that is a normal outcome, not an error.
- **It never touches `Intellibills\Documents\`.** That is the archive of record per 18.2a
  and it is the reason this deletion is safe at all. Nor the inbox's `Processed\` copy,
  nor any extraction row.
- **A file that is already gone is not a failure.** Log it and carry on.
- **A deletion that fails is logged as an ERROR and does not fail the note.** The status
  change is the point; a file left behind is untidy and recoverable, a note stuck in
  `Resolutions\failed\` is the disagreement this work exists to remove.
- **The path is validated before use.** It must resolve inside the client folder root. A
  `filed_path` that resolves anywhere else is refused and reported, and the note still
  applies.

**Confirm and report, rather than assume:** that a `discarded` note applies to a receipt
whose status is `ok`, not only to one awaiting review. Nothing I read imposes such a
precondition, and the Desktop half depends on it.

---

## 3. Deliverable 2: `filed_path` is cleared on discard

**Paul's decision.** After the copy is deleted, the column would otherwise name a file
that is not there, and this project has been caught more than once by a stored value that
outlived what it described.

**Clear it on every discard, not only where a copy was deleted.** A discarded receipt is
not filed, whatever became of the file. **The `resolution_events` row is where the history
lives**, so record the path that was cleared, and the path that was deleted if one was, in
whatever part of that row already carries this kind of detail.

**This has a second effect and it is intended.** `is_recorded_and_filed()` in
`worker\database\repository.py` is `SELECT filed_path ... is not None`, and it is what the
file-hash duplicate check asks. **So clearing the column is what lets the identical file
be sent again**, which is deliverable 3's case for the hash arm and needs no separate
change.

---

## 4. Deliverable 3: a discarded receipt does not block a resend

**Paul's decision, and the case is his own:** the operator deletes a receipt, decides it
was a mistake, and sends the document again.

**The hash arm is deliverable 2 and needs nothing more.** The semantic arm does.

`Repository._PUBLISHED` asks whether a `publish_events` row with outcome `published`
exists, and a discarded receipt keeps that row for ever. So a re-photographed resend, with
bytes the hash check cannot recognise, would still come back `possible_duplicate` against
a receipt the operator deliberately deleted.

**A discarded receipt must not be found as the earlier half of a semantic duplicate.**
`find_by_transaction_loose()`'s docstring says the marker has to be in the query as well
as at the call site, so satisfy both, and say in the report how you established that you
found every place it has to hold.

**What this gives up, and it is Paul's decision rather than an oversight.** A discarded
receipt stops protecting against anything at all. Say so plainly in the report if you find
a case where that costs more than he has allowed for.

---

## 5. What must not change

- **`Intellibills\Documents\` is never written to or deleted from by any of this.**
- **`is_recorded_and_filed()` keeps its existing callers and its existing meaning.** Its
  docstring records that it was deliberately not widened by 10f.24 and why; deliverable 2
  changes the data it reads, not the function.
- **The publish step, the item's shape, the publish ordering and the client folder copy on
  the way in.** Nothing in this brief touches them.
- **`discard_receipt()`'s existing callers**, being the CLI and the back-feed. A new
  parameter defaults to today's behaviour so neither moves.

---

## 6. Evidence

**The standard is `CLAUDE.md`'s and it is not relaxed for a small change.**

- **Red before green**, with the failing output quoted. A deletion is testable against a
  temporary directory; do not exercise it against anything under the live practice root.
- **Mutations through the harness**, each anchored on one place, each asserting its anchor
  matches exactly once, each printing its own diff and running the whole suite. **Include
  a mutation that deletes something other than the file `filed_path` names**, and one that
  clears `filed_path` without deleting. **And a prose-only control that survives.**
- **Enumerate from the syntax tree, not by grepping**, anything you assert about a set of
  call sites, and print the enumeration whole. `.history\` excluded.
- **Never `import config` to read a value.** Read the constant out of the file or run it
  under pytest. The fourth trap in `CLAUDE.md` says why, and it bit on 2026-09-09.
- **Suite figures before and after**, and say what "before" means.
- **Flag, do not fix.** Anything wrong that this brief did not ask about is reported.
- **Disclose your own mistakes**, including ones you caught and corrected.
- **State a confidence level and say what it is about**, not only what it rests on.

---

## 7. Committing and reporting

**Commit on `feat/console-phase0`.** Do not push and do not create a branch. Do not commit
`2026-07-25_CONSOLE_DESIGN.md` or any `PROMPT_*` or `HANDOVER_*` file: those are the
consultant session's.

**Write the report to
`C:\LastingImpact\receipt_capture\2026-09-10_REPORT_claude_code_discard_and_client_copy.md`**
and carry the commit hashes in it.

**Say in the report, because the Desktop half is written from it:**

1. The name and the exact shape of the new field on the note.
2. What the pipeline does when `filed_path` is NULL and the note asks for a deletion.
3. What the operator's toast should be able to say happened, in your words, so the two
   halves describe one thing.
