# Brief: step 10f, the six duplicate sub-steps that do not need the publish step

**Written 2026-09-07 by the consultant session, on Paul's decision the same day.**
**Report to `2026-09-07_REPORT_claude_code_step10f_duplicates.md` in this repository root.**

---

## 1. What this is, and what it is not

Six sub-steps of step 10f of `2026-07-25_CONSOLE_DESIGN.md`: **10f.18, 10f.19, 10f.20,
10f.21, 10f.22 and 10f.23**.

They are split out of step 10f on Paul's decision of 2026-09-07, because none of them
depends on the publish step or on the client folder copy. **The other 24 sub-steps of
step 10f are out of scope and must not be touched.** Named specifically, because each is
one line away from something here:

- **Nothing in this brief creates, reads or writes `IntelliBooks\Inbox\`.** That is 10f.4
  to 10f.7 and it is unbuilt.
- **Nothing in this brief changes where a receipt is filed**, or when. 10f.11 to 10f.17
  are out of scope, and the on-arrival write into the client folder stays exactly as it is.
- **10f.24 is out of scope.** This brief changes what is *detected* as a duplicate. Where
  a `possible_duplicate` then goes is unchanged.
- **Section 18.2b's freeze stands.** `get_client_directory()`, `file_receipt()` and
  `make_enriched_sidecar()` are frozen and nothing here touches any of them.

## 2. Read before starting

1. Section 16 of `2026-07-25_CONSOLE_DESIGN.md`, sub-steps 10f.18 to 10f.23. That is the
   specification and this brief does not replace it.
2. Amendments 136 and 137 of the same document, which carry the reasoning.
3. `CLAUDE.md`, "How this project is worked", and the seven traps.

**Line numbers are deliberately absent from this brief.** Amendment 247 for `config.py`,
and the same now holds for `app.py`. Functions are named where the consultant session has
read them; find the call sites yourself and print the enumeration in the report.

---

## 3. The six

### 10f.18 The receipt hash lookup takes the client

`find_by_hash()` in `worker/database/repository.py` runs two queries, one against
`processed_attachments` and one against `receipts`, and **both filter on the hash alone**.

**What it has to do:** match a hash only within one client. Two clients who send the same
document are not duplicates of each other.

**Why it matters now rather than later.** Today the second client's receipt is discarded
and credited to the first, and nothing reports it. One capture mailbox serves every client,
and a Congestion Charge receipt or a licence renewal arrives byte-identical for two drivers.

**Every caller changes with it.** There are three, and all three are in `app.py`: the
embedded-image path, the folder-intake path and the attachment path. Each already holds the
client at the point of the call, or can reach it without a new lookup; establish that and
say so in the report rather than adding a parameter that gets `None`.

### 10f.19 The semantic duplicate lookup takes the client

`find_by_transaction_loose()` in `worker/database/repository.py` matches on supplier, date
and amount within a tolerance and **does not filter on the client**. One caller, in
`worker/extraction_pipeline.py`.

**What it has to do:** the same as above. Two clients buying the same thing on the same day
for the same amount are not a duplicate.

**This is amendment 107's "same client" and it was dropped from step 10f when it was
written.** Without it two clients sending one document reach Review instead of being no
duplicate at all.

### 10f.20 The third hash call site gains the guard the other two have

Of the three `find_by_hash()` call sites in `app.py`, **two check
`is_recorded_and_filed()` before treating the match as a duplicate and one does not.** The
one without it is the embedded-image path.

**What it has to do:** all three behave the same way. A hash matching a receipt that was
never filed is not a reason to skip.

**Read the docstring on `_move_inbox_pair_to_processed()` in `app.py` before changing this.**
It explains what an unfiled hash match is for, and the change must not make that
reprocessing rule unreachable.

### 10f.21 Nothing gets deleted

`_remove_inbox_pair()` in `app.py` calls `.unlink()` on the inbox file and its sidecar. It
has **two callers**, being the duplicate-statement path and the duplicate-receipt path in
the folder-intake loop.

**What it has to do:** both callers move the pair into `Processed\` instead.

**The function that does this already exists.** `_move_inbox_pair_to_processed()` in
`app.py` is the shape every other outcome already uses, including the `ok` path, which step
9c changed from a delete to a move on the no-data-loss rule. It handles the missing folder,
the name collision and the image-and-sidecar pairing. **Use it. Do not write a second one.**

**`_remove_inbox_pair()` is then deleted**, once no caller remains.

**One test exists to prove the delete and it must be rewritten, not made to pass.**
`tests/test_capture_inbox_cleanup.py` calls `app._remove_inbox_pair(intake)` directly and
asserts the two files are gone, in both of its tests. It is the same class as
`tests/test_logging_setup.py` in section 18.2a: a test whose whole subject is the behaviour
being changed. Rewrite it against the new behaviour and say in the report what it now
asserts.

### 10f.22 The duplicate decision is identical on every arrival route

Email, phone and **Add Receipts**. **What differs is only the disposal of the thing that
arrived**: an email is moved to `INBOX.Duplicates`, an inbox file is moved to `Processed\`,
and in both cases it is kept.

**This is the acceptance criterion for 10f.18, 10f.19, 10f.20 and 10f.21 together rather
than a change of its own.** After those four, the three routes should reach the same verdict
on the same document for the same client. **Prove it in a test that drives all three routes
over one document, and print the verdict from each.**

### 10f.23 Two dead functions go

`find_by_transaction()` and `find_by_transaction_no_date()` in
`worker/database/repository.py`.

**Confirm before deleting**, and print the enumeration whole in the report. The consultant
session's own search on 2026-09-07 found no caller in production or in `tests\`, excluding
`.history\`. **Run it again yourself rather than taking that**, and exclude `.history\`:
it is VS Code local history, it is gitignored, and it holds a dated copy of every file
you have edited.

---

## 4. Amendment 1: the statement hash lookup is IN SCOPE

**Amended 2026-09-07 19:35 BST, after this brief was sent and after work had started.**
Paul's ruling. The consultant session's error is disclosed at the end of this section.

**`find_statement_by_hash()` in `worker/database/repository.py` takes the client.**

It filters on the hash alone in exactly the way `find_by_hash()` does, so a statement sent
by two clients collides the same way and the second client's statement is credited to the
first. **No sub-step of step 10f covers it**, which is why it is here as an amendment
rather than as a seventh sub-step. It was found by the consultant session on 2026-09-07
while reading for this brief.

**What it has to do:** match a statement hash only within one client, the same rule and the
same reasoning as 10f.18.

**Its one caller** is the duplicate-statement path in `app.py`'s folder-intake loop, and it
already holds the client at that point. That caller is in scope twice over: 10f.21 also
names it as one of `_remove_inbox_pair()`'s two callers, so its disposal changes to a move
into `Processed\` in the same edit.

**`statements` holds 0 rows**, so nothing on disk is affected and no migration arises.

**Report it under the same headings as the other six.**

> **Superseded wording, kept rather than deleted.** This section read
> "`find_statement_by_hash()` is NOT in this brief ... Leave it alone. If he rules it in, it
> arrives as an amendment to this brief and not as your judgement." He ruled it in.

> **The consultant session's mistake, disclosed.** This brief was written with an open
> question inside it and was sent before the question was answered, so work started against
> a scope that changed twenty minutes later. The question should have been put to Paul and
> answered before the brief was written. Recorded here because a brief amended mid-run costs
> a round trip through the only channel between the sessions.

---

## 5. Standard of evidence

- **Red before green**, with the failing output quoted. Where a test cannot come first,
  mutate the behaviour from a pristine copy and show which tests catch each mutation and
  that no others do.
- **Enumerate a set before asserting a count about it.** Every "there are N call sites" in
  this brief was counted by the consultant session and every one of them should be re-run
  and printed whole. This project has had four wrong set claims and each one read as
  confident.
- **Flag, do not fix.** Anything wrong that this brief did not ask about gets reported.
- **Disclose your own mistakes**, including ones you caught and corrected.
- **State a confidence level and say what it rests on**, and what it is about.
- **Commit after each sub-step**, per section 16.

## 6. What the report has to carry

`2026-09-07_REPORT_claude_code_step10f_duplicates.md`, in this repository root.

1. The enumeration of every call site you changed, printed whole rather than counted.
2. The red output for each test, before the change.
3. The mutation results for anything that could not be red first.
4. The full suite result, with the before and after counts.
5. What `tests/test_capture_inbox_cleanup.py` now asserts.
6. The 10f.22 three-route test and the verdict each route returned.
7. Anything you flagged.
8. Anything this brief got wrong.
