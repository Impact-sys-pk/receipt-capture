# Brief: two places an attached document reaches and should not

**Written 2026-09-12 by the consultant session, from Paul's decisions the same day.** Amendment 345
of `2026-07-25_CONSOLE_DESIGN.md`. **Both items were carried as open from session 22 and both are now
decided.**

**Read first, in this order:** `CLAUDE.md`, the section "How this project is worked" and the seven
traps. Then amendment 345. Then sub-step 10f.38 and whatever it records about the status a handed-over
document carries, because both items turn on it.

**Two items. Neither is a step and neither needs a design decision.**

---

## 1. `count_processed_today()` counts what the pipeline actually read

**Today it counts every `receipts` row created today, with no status filter.** So it counts documents
handed over from the books and never processed by the pipeline, discarded ones, and ones still
waiting to be read. It also counts arrivals rather than work finished, which is not what the name
says.

**Make it count what the pipeline actually read today.** An attached document is not one: it was
never read, never extracted and never published.

**Establish rather than assume, and print each enumeration whole:**

- **Every status a `receipts` row can hold**, and which of them mean the pipeline read the document.
  There is a recent enumeration of this set in `2026-09-11_REPORT_claude_code_capture_report.md`
  section 4; **re-run it rather than quoting it**, and say if it has moved.
- **Every reader of `processed_today`.** I counted nought in `IntelliBooks-Desktop-v3.html` on
  2026-09-12 and the console is not built. **If you find a reader, stop and say so**, because the
  field's meaning would then be a contract rather than a free choice.

**Two things to decide and report rather than choose quietly.**

- **Whether a discarded receipt counts.** It was read before it was discarded, so there is an argument
  both ways. Say which you took and why.
- **Whether the day is the UTC day or the London day.** The field lives in `pipeline-status.json`,
  which the London time work deliberately left in UTC, and the figure is a count rather than a
  timestamp. **Do not change it silently either way.**

**The comment above the call in `app.py` is half wrong and is corrected with this.** It says the
figure is not what the field is called or what IntelliBooks shows. The first half is right. **The
second is not: IntelliBooks shows nothing from that field.** Strike the wrong half rather than
rewriting the paragraph.

**`pipeline-status.json` keeps all five of its keys.** Nothing is removed.

---

## 2. The filename fallback excludes an attached document, at the caller

**`find_receipts_by_filename()` matches on filename with no status filter.** The back-feed uses it
when a resolution note carries no receipt id, so an attached document can be a candidate and, if it
is the only one, the note is applied to it.

**Leave the method alone.** Its docstring says it returns every match and that refusing an ambiguous
one is the caller's problem rather than its own to guess at. **Putting a status filter in the query
would make a general-purpose lookup carry one caller's rule.**

**Exclude the attached document where the rule lives, in the caller.** An attached document is not
something a back-feed note can be about: it came from the books rather than from capture, and it has
no review sidecar for a note to have come from.

**The existing ambiguity guard stays exactly as it is.** More than one candidate is still not a
match, and it still logs. **Work out and report what happens when excluding an attached document
turns two candidates into one**: that is now a match where before it was a refusal, and whether that
is right is worth a sentence rather than a silent change of behaviour.

---

## 3. What must not change

- **No stored value moves.** No migration, no backfill, no rewrite.
- **`pipeline-status.json` keeps its five keys and its shape.**
- **Nothing published, re-processed, re-extracted, and no receipt's status moves.**
- **Nothing written into `Clients\`, `IntelliBooks\` or `Intellibills\Documents\`.**
- **Never `import config` to read a value.**

---

## 4. Evidence

- **Red before green**, with the failing output quoted, for both items.
- **A test that a handed-over document is not counted**, driven through the real writer that creates
  one rather than by inserting a row by hand. **Seeding it by hand would prove the test reads a row
  the test invented.**
- **A test that a note with no receipt id does not match an attached document**, and one that the
  ambiguity refusal still fires.
- **Mutations**, each anchored once and printing its own diff: the status filter dropped from the
  count; the count counting arrivals again; the exclusion dropped from the caller; the ambiguity
  guard removed; and a prose-only control that survives.
- **Enumerate from the syntax tree** anything you assert about a set, and print it whole.
  `.history\` excluded.
- **Run the suite again AFTER committing** if the change adds a file.
- **Flag, do not fix. Every flag carries the obvious fix, and if the fix is to remove something, say
  so first.** Disclose your own mistakes. State a confidence level and say what it is about.

---

## 5. Committing and reporting

**Commit on `feat/console-phase0`.** Do not push and do not create a branch. Do not commit
`2026-07-25_CONSOLE_DESIGN.md`, any `PROMPT_*` or `HANDOVER_*` file, or anything under
`Test Receipts\`.

**Commit by naming your own paths and check the index afterwards**, and say so in the report.

**Write the report to
`C:\LastingImpact\receipt_capture\2026-09-12_REPORT_claude_code_attached_documents.md`** and carry the
commit hashes in it.

**One section at the top for Paul.** What the `processed_today` figure will read now that it did not
before, on his own database, and what a back-feed note can no longer match.
