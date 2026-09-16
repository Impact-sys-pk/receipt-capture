# Brief: a document attached from the Bank Transactions tab

**Written 2026-09-11 by the consultant session, from Paul's requirement of 2026-09-10 and his
decisions of 2026-09-11. Sub-step 10f.38 of `2026-07-25_CONSOLE_DESIGN.md`, created by amendment
315 and designed by amendment 320.**

**Read first, in this order:** `CLAUDE.md`, the section "How this project is worked" and the seven
traps. Then 18.1, 18.2, 18.2a and 18.2b of `2026-07-25_CONSOLE_DESIGN.md`, then section 12, the
resolution back-feed contract, then sub-steps 10f.11, 10f.13 and 10f.37 in section 16.

---

## 1. What this is

Paul is looking at a bank line and has the document for it in his hand. Today the only route in is
the Receipts tab and the pipeline, so he has to send it, wait, and come back. **10f.38 lets him
attach it to the bank transaction there and then.**

**IntelliBooks attaches it immediately, so Attach means Attach.** It then hands the document to
Intellibills to archive and to file.

Four conditions, all Paul's and none negotiable:

- **Not extracted and not validated.** The transaction already carries the date, the amount and the
  description, and a document that is not a receipt would otherwise fail into Review.
- **Never published back.**
- **Never in the receipts list.**
- **The client folder copy happens on the same trigger as 10f.37**, which is at Post, through the
  `attached` note that already exists.

**This brief is the pipeline half only.** The IntelliBooks Desktop half is the consultant session's
and is written from your report. **The two halves land together or not at all.**

---

## 2. The thing that decides the shape, established before this brief was written

The pipeline's own record of a document is a row in `receipts`. The client folder copy path reads
that row and its extraction row, and `filed_path` lives on the row, so an attached document needs
one or the copy has to be reimplemented.

**But a plain row breaks Paul's third condition.** `_publish_unpublished_receipts()` in `app.py`
calls `get_unpublished_ok_receipts()`, which offers every `ok` receipt with no `published` row.
An attached document would look exactly like a receipt that never made it across, so the sweep
would publish it, Desktop would drain it, and it would appear in the receipts list.

**Paul's decision, 2026-09-11: the row carries a marker saying the document came from a bank line,
and every sweep that offers receipts for publishing excludes it.**

**Enumerate before you build.** The sweep above is the one this session found by reading. **Find
every place that selects receipts rows and could act on this one**, from the syntax tree rather
than by grep, print the set whole, and say which of them had to change. A claim about a set is not
verified by verifying its members.

---

## 3. Deliverable 1: the pipeline accepts an attached document

**A document arrives from Desktop with no extraction behind it, and the pipeline archives it,
records it, and files it on the firm's trigger.**

**The handoff is yours to name and you must state it in the report, because the Desktop half is
written from what you choose.** Desktop cannot write into `Intellibills\Documents\`: that is the
archive of record and it has one writer, per 18.2. So Desktop needs somewhere to put the file and a
message naming it. **Say what the folder is called, what the message carries, and why**, and hold
to 10f.37's rule that a path composed by Desktop is not trusted for anything the pipeline composes
itself.

**What the message has to be able to say**, and no more: which client, which transaction, and which
file. **It is not a resolution note about a receipt**, because there is no receipt yet. Say plainly
whether you are extending `NOTE_ACTIONS` again or using a different channel, and why.

**What the pipeline does with it.**

- **Archives the document into `Intellibills\Documents\{client_id}\{year}\{month}\`** through the
  existing store, so the archive of record holds it like everything else.
- **Writes the row, marked.** Not `ok`, not `failed`, not a lie about a validation that never ran.
  The marker is what the sweeps exclude.
- **No extraction row, no categorisation row, no `publish_events` row.**
- **Nothing reaches `IntelliBooks\Incoming\`.**

**The client folder copy is NOT written when the document arrives.** It is written when Desktop
reports the transaction posted, through the `attached` note built at 10f.37, on the firm's trigger.
On `publish` and on `never` the same rules apply as they do to a receipt.

---

## 4. The filename in the client folder

A receipt copy is named from its extracted date, supplier and gross. **An attached document has
none of those**, so nothing composes that name.

**Paul's decision, 2026-09-11: name it from the transaction**, being the transaction date, the
description normalised the same way a supplier name is, and the amount, so the client folder reads
the same way whether the document came from a receipt or from a bank line.

**The pipeline composes it, not Desktop**, for 10f.37's reason: a collision puts a `-2` on the name
and nothing on the other side can tell one from the other. **So the message carries the three
values and not a filename.**

**If that cannot be done without changing the one writer into `Clients\`, stop and report rather
than adding a second writer.**

---

## 5. What must not change

- **`write_client_copy()` stays the only writer into `Clients\`.**
- **The receipt path.** Nothing about extraction, validation, categorisation or publishing moves.
- **10f.37's behaviour**, which was proved live on 2026-09-11 and is what this rides on.
- **F16's value**, which is now `post` on Paul's firm record. Do not change it and do not suggest a
  default.
- **`Intellibills\Documents\` is never deleted from.**

---

## 6. Evidence

- **Red before green**, with the failing output quoted, driven through a real `process_once()`
  rather than asserted on a function, because the value of this change is that a file appears in
  two folders and does not appear in a third.
- **A test that the document never reaches `IntelliBooks\Incoming\`**, and a test that the
  publishing sweep leaves it alone, driven over at least two polls rather than one.
- **A test for each trigger**, `publish`, `post` and `never`.
- **Mutations** through the harness, each anchored once and printing its diff: drop the marker;
  drop the sweep's exclusion; write the client copy on arrival instead of at Post; and a prose-only
  control that survives.
- **Enumerate from the syntax tree** anything you assert about a set, and print it whole.
  `.history\` excluded.
- **Nothing run against the live practice root.**
- **Never `import config` to read a value.** `CLAUDE.md`'s fourth trap.
- **Flag, do not fix. Disclose your own mistakes. State a confidence level and say what it is
  about.**

---

## 7. Committing and reporting

**Commit on `feat/console-phase0`.** Do not push, do not create a branch, and do not commit
`2026-07-25_CONSOLE_DESIGN.md`, any `PROMPT_*` or `HANDOVER_*` file, or anything under
`Test Receipts\`.

**Write the report to
`C:\LastingImpact\receipt_capture\2026-09-11_REPORT_claude_code_attached_document.md`** and carry
the commit hashes in it.

**Four things the Desktop half is written from, so put them in one section at the top.**

1. The handoff folder, the message, and every field it must carry.
2. What the pipeline does on each of the three triggers, so Desktop knows whether to send at all.
3. What Desktop can honestly tell Paul at the moment he attaches the document, given the pipeline
   reads the message on its next poll.
4. What Desktop has to send when he detaches the document or deletes the transaction.
   **Paul's decision, 2026-09-11: it asks, with the same dialogue and the same wording as the
   receipt Delete, and the copy goes only if he ticks the box.** 18.2b says a copy is never
   withdrawn and 10f.27 says an operator may delete anything, and this is where those two meet; he
   has ruled for 10f.27's side, with the choice put to him each time. **The removal itself already
   exists** and nothing about it is to be rebuilt. Say in the report what the message must carry
   for that case.
