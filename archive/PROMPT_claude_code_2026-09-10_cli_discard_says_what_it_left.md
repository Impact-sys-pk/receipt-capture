# Brief: the orphaned sidecar, and the CLI saying what it left behind

**Written 2026-09-10 by the consultant session. Paul's decisions the same day.
Amended the same afternoon to add deliverable 1, which is the larger of the two
and was found on his machine after the first version of this brief was written.**

**Two small things. Deliverable 1 was found as a real orphan on Paul's machine
this afternoon and he has since deleted it by hand. Deliverable 2 is flag 5 of your own
`2026-09-10_REPORT_claude_code_discard_and_client_copy.md`.**

---

## 1. Deliverable 1: a deleted client folder copy leaves its data file behind

**Found on Paul's machine at 14:30 today**, by listing
`Clients\Test Sole Trader\IntelliBooks\Receipts\` whole. One document had been
removed and its data file was still there:

```
2026-08-15_octopus-energy_248.33.jpeg        gone
2026-08-15_octopus-energy_248.33.jpeg.json   still there
```

**PAUL DELETED THAT ORPHAN BY HAND AT 14:31, so do not go looking for it.** The
pair is recorded here because it is what the change is for, and the folder was
re-listed after he deleted it to keep the rest of this section true.

**Eight such data files remain in that client's tree**, all beside receipts filed
before 2026-09-09, and each still has its document: two in `2022-23\`, one in
`2024-25\`, two in `2025-26\` and three in `2026-27\`. Counted from the listing
at 14:33, not estimated. **Receipts filed
since sub-step 10f.11 have none**, because the client folder copy is the image
alone under 18.2b, so this is a finite legacy set rather than something that keeps
growing.

**Why the deletion misses it.** `remove_client_copy()` deletes exactly the file
`filed_path` names and nothing else, which is right and which the consultant
session verified this morning. `filed_path` names the document, so the data file
beside it is out of scope.

**What to build.** After a successful deletion, delete the receipt's data file if
it is there.

- **The name is derivable exactly and must not be composed or guessed.** Section
  3 of `IntelliBooks-System-Specification.md` states the convention: a filed
  receipt's sidecar is the full filename with `.json` **appended**, so
  `x.pdf` pairs with `x.pdf.json`. That is a different convention from the inbox
  sidecar, which replaces the extension, and this is the appended one.
- **Same containment rules as the document.** It resolves inside
  `config.CLIENTS_ROOT`, it is a file and not a directory, and anything else is
  refused.
- **Its absence is normal and is not a failure.** Everything filed since
  2026-09-09 has no sidecar at all.
- **It is never deleted on its own**, only after the document it belongs to has
  actually been deleted. An `already_gone` document must not take a sidecar with
  it: if the document was removed by something else, this change has no business
  guessing that the sidecar is stale.
- **Report it separately from the document** in whatever the outcome carries, so
  the log and the audit row can say the document went, the sidecar went, or the
  document went and there was no sidecar.

**Not in scope: the eight that remain.** Each still has its document, so none of
them is an orphan. Whether to tidy them is Paul's, and he has not asked.

---

## 2. Deliverable 2: the CLI says what it left behind

`filed_path` is now cleared on **every** discard, which is Paul's decision and is
right. The back-feed can also ask for the client folder copy to be deleted. **The
two command-line callers cannot ask, and that is correct.**

**What is not correct is that they say nothing about the consequence.** Discarding
a filed receipt from `discard_receipt.py` or `resolve_receipt.py` clears the
column, leaves the file in the client folder, and prints nothing about either. The
operator is left with a document in `Clients\` that nothing can now find, because
the path it was known by has just been forgotten.

**What to build.** The discard outcome carries the path that was cleared, and both
command-line callers print it.

- The path is the one that was in `filed_path` before it was cleared. Where there
  was none, nothing is printed.
- Where the copy was deleted, that is a different sentence and the operator should
  be able to tell the two apart.
- The wording is yours, but it names the file in full and says plainly that it has
  been left.

**Neither script gains a way to ask for the deletion**, which is the same decision
the previous brief recorded.

---

## 3. What must not change

- **`Intellibills\Documents\` is never written to or deleted from.**
- **The note, the flag, the clearing and the resend behaviour**, all landed this
  morning, are untouched.
- **`remove_client_copy()` still deletes exactly one document.** Deliverable 1
  adds one companion file with a derived name, not a pattern, not a glob, and not
  a directory sweep.

---

## 4. Evidence

- **Red before green** for both deliverables, with the failing output quoted.
- **Tests for the shapes**: a document with a sidecar, a document without one, a
  document already gone with a sidecar still present, which must leave the sidecar
  alone, and a sidecar path that resolves outside the root.
- **Mutations**, each anchored on one place and each printing its diff: delete the
  sidecar without the document; delete a sidecar for an `already_gone` document;
  drop the new information from the CLI outcome; and a prose-only control that
  survives.
- **Enumerate the callers of the discard outcome from the syntax tree** before
  adding to it, and print the enumeration.
- **Nothing run against the live practice root.** `TempEnvironment`, as before.
- **Never `import config` to read a value.** `CLAUDE.md`'s fourth trap.
- **Flag, do not fix**, and **disclose your own mistakes**.

---

## 5. Committing and reporting

**Commit on `feat/console-phase0`.** Do not push, do not create a branch, and do
not commit `2026-07-25_CONSOLE_DESIGN.md`, any `PROMPT_*` or `HANDOVER_*` file, or
anything under `Test Receipts\`.

**Write the report to
`C:\LastingImpact\receipt_capture\2026-09-10_REPORT_claude_code_sidecar_and_cli_output.md`**
and carry the commit hashes in it.

**Two questions to answer in it.**

1. With the path printed but no longer stored, is there any route by which an
   operator can find and remove that file later, or is the printed line the only
   record it ever existed?
2. Does anything else in either product still write a sidecar into `Clients\`, or
   read one from there? The eight on Paul's machine are legacy, and it matters
   whether they are the end of it.
