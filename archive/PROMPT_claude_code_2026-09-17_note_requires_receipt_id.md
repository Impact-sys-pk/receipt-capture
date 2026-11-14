# Claude Code brief, 2026-09-17: a resolution note must carry a receipt_id

Written by the consultant session, 2026-09-17, **11:12 BST**. ~~12:20 BST~~ **Corrected 2026-09-17**: the first figure was an estimate and this one is the file's own modification time. The consultant session had been stating times without reading a clock, which is the rule it had corrected Claude Code for twice the same day. **Paul's decision, 2026-09-17**, taken on
the consultant session's finding while preparing a brief for step 10aw. It replaces what step 10aw
was scheduled to do.

**Report to `2026-09-17_REPORT_claude_code_note_requires_receipt_id.md` in the repository root.**

**One commit. Build it, propose the commit, and wait for a yes.**

---

## Three rules about this brief

**1. `2026-07-25_BUILD_STATUS.md` is not yours to edit.** You report; the consultant session verifies
against the code on Paul's machine and marks the step. Paul's instruction of 2026-09-16.

**2. `2026-07-25_CONSOLE_DESIGN.md` is not yours either.** This changes 12.3 step 2, and the
amendment recording that is the consultant session's to write.

**3. You already found this, on 2026-09-09, and nobody acted on it.** Flag 3 of
`2026-09-09_REPORT_claude_code_desktop_note.md`, and the field comment you wrote on
`ResolutionNote.original_review_files` that still stands in the file. The consultant session found it
again this morning without having read either. Section "One disclosure" below.

---

## What is decided

**A resolution note that carries no `receipt_id` is refused, and the filename fallback is removed.**

Two things, and the second is why the first is safe.

### The fallback goes

`_receipt_for_note()` in `worker\resolution\service.py` keeps its `receipt_id` lookup and loses
everything after it: the loop over `note.original_review_files`, the
`repo.find_receipts_by_filename()` calls, the bank-attachment exclusion inside that loop, and the
ambiguity guard that follows.

**`find_receipts_by_filename()` in `worker\database\repository.py` is its only caller as far as the
consultant session read, and reading is not enumerating. Enumerate its callers yourself and say what
you found.** If it has no caller left, whether it goes too is a finding to report, not a decision to
take.

### The note contract requires the id

`parse_resolution_note()` refuses a note with no `receipt_id`, the same way it already refuses a
missing `resolved_at`, and the reason names the missing field. The refusal must be readable by a
person opening the `.error.txt` beside the note in `Intellibills\Resolutions\failed\`.

**Today a note without an id fails later and less usefully**, as `outcome: not_found` with
"no receipt matched by id or by review filename", which names two ways of matching when only one
exists.

## Why this is safe, and it is not a judgement call

**The fallback cannot run.** It is reached only when `note.receipt_id` is falsy. Every producer sends
one:

- IntelliBooks Desktop is the only writer into `Intellibills\Resolutions\`. The pipeline reads that
  folder and never writes a note into it.
- Its two writers that send `original_review_files` take the id from a Review row, and the function
  that builds those rows skips any tray item without an id.

**And if it ran it could not match.** `original_review_files` now carries the tray item's name,
`{receipt_id}.json`. `receipts.filename` holds the document's original filename. The two can never
be equal. **That is your flag 3 of 2026-09-09, unchanged and still true.**

**Checked against Paul's own data**, `Intellibills\Resolutions\`: every note in `processed\` and
`failed\` carries a `receipt_id`. The one note from 2026-09-06 carries the old shape,
`["TESTFIXTURE_car_wash_3_teach.png", "TESTFIXTURE_car_wash_3_teach.png.review.json"]`; this
morning's carries `["b4952efa-39d5-4ad7-b877-3600c402b4ac.json"]`.

## What must not change

- **`original_review_files` stays in the contract and stays parsed.** It is still carried on the
  note, still rejected when it is not a list of strings, and still named in the messages that report
  a failure. Retiring it was considered by Paul on 2026-09-17 and decided against for now.
- **The two message strings that name it.** They are useful exactly when a note fails.
- **Every other reason a note can be refused.** This adds one; it removes none.
- **The idempotency behaviour.** `resolved_at` is untouched.

## The other half, so you know it is coming and do not build it

IntelliBooks Desktop stops writing a note it knows will be refused: where the id is missing it writes
no note and says so on screen, rather than sending `receipt_id: null`. **That half is the consultant
session's and is not yours.** It is in `IntelliBooks-Desktop-v3.html`, which is not in this
repository.

## Evidence

The standard in `CLAUDE.md` applies in full. Four parts this change makes specific:

- **Red before green.** A note with no `receipt_id` is refused by the contract check with the new
  reason, and the test fails against today's code because today it parses.
- **A test that the fallback is gone rather than merely unused.** A note with no id whose
  `original_review_files` names a filename that really does match a receipt in the fixture. Today
  that resolves; after this change it is refused. **Without a genuinely matching filename in the
  fixture the test cannot tell the fallback was removed**, and a test that cannot fail is not a test.
- **A guard over the set, on the source.** `_receipt_for_note()` makes no call that matches on a
  filename. Parse the syntax tree, not the text: this file keeps superseded wording beside every
  correction and the `ResolutionNote` field comment names the fallback in prose.
- **Mutations**, each anchored, asserted unique, diff printed. At minimum: put the fallback back, and
  make the contract check accept a missing id again.

Run the suite again after the commit if this adds a file.

## What to report

Everything the standard asks, plus:

1. **The callers of `find_receipts_by_filename()`, enumerated by you**, and whether any remain.
2. **What a note with no `receipt_id` now produces**, quoted as it appears in the `.error.txt` file a
   person would open.
3. **Anything else that reads `original_review_files`** beyond the contract check and the two message
   strings. The consultant session found none in `worker\resolution\service.py`. **Flag it, do not
   fix it.**

## One disclosure

**The consultant session rediscovered your own flag and presented it to Paul as new.** Flag 3 of
`2026-09-09_REPORT_claude_code_desktop_note.md` says, on 2026-09-09, what was put to him this
morning as a finding: Desktop sends `{receipt_id}.json`, it can never match an attachment name, and
the fallback is dead for a Desktop note. You also wrote it into the `ResolutionNote` field comment,
where it has stood ever since.

**Step 10aw was then scheduled on 2026-09-13 by amendment 444 to fix a suffix problem in that same
fallback**, four days after the comment saying the fallback no longer runs was already in the file.
Nobody read it, twice.

**This is recorded here because it is the argument for the decision**, not only an embarrassment: a
flag that is raised, written into the code and left unacted becomes a step scheduled against a
defect that cannot happen.
