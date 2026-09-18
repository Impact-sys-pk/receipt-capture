# Claude Code brief, 2026-09-18: the section 18 citations a person reads

Written by the consultant session, 2026-09-18, 16:13 BST, read off the clock in this reply. Paul's
decision of 2026-09-18, taken on your own flag in
`2026-09-18_REPORT_claude_code_capture_report_to_client_folder.md` section 3.

**Report to `2026-09-18_REPORT_claude_code_section_18_citations.md` in the repository root.**

**One commit. Build it, propose the commit, and wait for a yes.**

---

## Three rules about this brief

**1. `2026-07-25_BUILD_STATUS.md` is not yours to edit.** You report; the consultant session
verifies against the code on Paul's machine and marks the step. Paul's instruction of 2026-09-16.

**2. `2026-07-25_CONSOLE_DESIGN.md` is not yours either.** The mapping line this decision puts into
section 20.7, and the amendment recording it, are the consultant session's and are being written in
the same window as this brief. Do not touch that file.

**3. Everything this brief names has been read this session**, in `config.py`,
`worker\client_copy.py`, `worker\resolution\service.py`, `worker\database\schema.py` and
`worker\extraction\base.py` on Paul's machine, and in section 20.1 of
`2026-07-25_CONSOLE_DESIGN.md`. Where it does not name something, that is deliberate and the place
is yours to find.

---

## What is decided

Your report counted **72 references to section 18 across 16 of the 57 production `.py` files**. The
consultant session enumerated them independently and got the same 72 and the same per-file split.

**Paul's decision splits them.**

**The citations a person reads are repointed. The citations a reader of the source meets are left.**

### The five that go

Each of these is a message that leaves the process and reaches a person, in a log file Paul opens or
in a crash he has to act on. He gets sent to a section that no longer exists and there is nothing
there.

| File | What it says now |
|---|---|
| `config.py` | A `RuntimeError` on a bad client-copy trigger value, ending "writes a document into a client folder, and section 18.2b says a copy is never withdrawn." |
| `worker\client_copy.py` | A log line, "a copy is made once and never withdrawn, per 18.2b". |
| `worker\resolution\service.py` | Three log lines in the discard path, each ending "The document store still holds the archive of record, per 18.2a". |

**Both rules those five cite survive**, in section 20.1 of `2026-07-25_CONSOLE_DESIGN.md`, which the
consultant session read while writing this brief: the archive is "never changed once written", and
the client folder copy is "Written once, never withdrawn, and a repost does not duplicate it."
**What the new citation says is yours to settle.** Read 20.1 and pick it; do not take a section
number from this brief.

**Nothing else about those five changes.** Not the level, not the arguments, not the rest of the
sentence, not when they fire.

### The sixty-seven that stay, and why

Comments and docstrings. **The reasoning is amendment 498's own**, applied to a second place: the
amendment record's 340 references are not repointed because each records a decision taken while
section 18 said something, and rewriting them would falsify the history. A comment saying why a
function is shaped as it is was written the same way and for the same reason.

**And 67 blind edits across 16 files is a change nothing can verify.** No test can catch a citation
repointed at the wrong section 20 paragraph.

**Two of the 67 look like the five and are not.** `worker\database\schema.py` carries two inside
`SCHEMA_SQL`, on `--` comment lines within the SQL, and `worker\extraction\base.py` carries one in a
string that documents an attribute rather than a docstring the parser recognises. **Neither reaches a
person.** They stay. Mentioned so they are not swept in by a search for string constants.

## What must not change

- **The 67.** Comments and docstrings are untouched, including the struck 18.2, 18.2a and 18.2b
  citations you left in `output_dir_for()`'s docstring on purpose.
- **What the five messages do.** Repointing a citation is not a rewording exercise.
- **The suite.** This adds a guard; it removes nothing.

## Evidence

The standard in `CLAUDE.md` applies in full. Four parts this change makes specific:

- **Enumerate the set yourself, from the syntax tree, and report the count.** The consultant session
  makes it five person-facing citations across three files and 72 references in total. **If your
  enumeration disagrees, say so and do not reconcile it to this brief.** One of the two counts is
  wrong and finding out which is worth more than agreement.
- **Red before green.** A guard that fails against today's code because today those five cite a
  retired section.
- **A guard over the set, on the source, and its scope is the whole point.** It must cover the
  message strings a person reads and must not cover comments and docstrings, or it fails on the 67
  that are staying. The set it walks is the string arguments of logging calls and of `raise`
  statements. Parse the syntax tree, not the text.
- **Mutations**, each anchored, asserted unique, diff printed. At minimum: put the citation back into
  one of the log lines, and put it back into the `RuntimeError`. **The second is the one that
  matters**, because a guard written only around logging calls passes it.

**A count that must hold after the change: 72 becomes 67.** Each of the five carries exactly one
reference. If it lands anywhere else, something was swept in or missed.

Run the suite again after the commit if this adds a file.

## What to report

Everything the standard asks, plus:

1. **Your own enumeration** of the person-facing citations, and whether it agrees with five.
2. **The new citation you chose**, and what in section 20.1 you matched it to.
3. **The reference count across the 57 production `.py` files after the change**, counted the same
   way you counted 72.
4. **Anything else in the repository that puts a section number in front of a person** and is not a
   comment, a docstring or a test. The consultant session did not look beyond the `.py` files.
   **Flag it, do not fix it.**

## One disclosure

**The consultant session told Paul, and wrote into the 10ai brief, that section 18's live
cross-references had been repointed in the two design documents and in `CLAUDE.md`, and that only the
Python was uncounted. That was wrong.** Your report repeated the sentence back because the brief
supplied it. Counted on 2026-09-18: `CLAUDE.md` holds none, `2026-07-25_CONSOLE_DESIGN.md`'s body
holds 21 including a banner at its head that still calls section 18 "under review", and
**`2026-07-25_BUILD_STATUS.md` holds 70 live references and was never repointed at all**, though
section 20.7 says it would be.

**Those are the consultant session's to fix and are not in this brief's scope.** It is recorded here
because a brief that hands you a fact you cannot check is how the same error gets repeated twice, and
this one already was.
