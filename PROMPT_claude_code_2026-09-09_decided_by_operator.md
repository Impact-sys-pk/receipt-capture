# Brief: a receipt settled from a Desktop note reaches `ok`, and the failed checks are recorded rather than used to block

**Written 2026-09-09 by the consultant session. This is flag 1 of
`2026-09-09_REPORT_claude_code_desktop_note.md`. Paul decided it on 2026-09-09: build it.
Amendment 307 of `2026-07-25_CONSOLE_DESIGN.md` records the decision and its reasoning.**

**Read amendment 307 first.** It also records what this brief does not cover and why.

---

## 1. What the flag is, and your diagnosis is accepted in full

`_apply_filed_note()` forces `validation_status="ok"` on the reasoning that a person filed it, and
appends the failures to the extraction row. `resolve_receipt()` does not. So a note without a
`filed_path` now takes `_settle_note()`, and a note whose values do not validate lands in
`Resolutions\failed\` as `still_invalid` while its row is already in the books in IntelliBooks
Desktop.

**That is the disagreement between the two products that amendment 306 exists to stop.** It is
reachable, as your report says, because `fileReviewReceipt()` checks only a supplier, a valid date
and a gross above nought.

**It was not what stopped receipt `a587b166-35a1-473c-aa5a-409749f7b642`.** That note carries
`net_amount: null`, `vat_amount: null` and `gross_amount: 27.5`, and `validate()` in
`worker\validation\rules.py` compares net plus VAT against gross only when all three are present, so
it validated `ok` on its own. It settled at 18:19:57 today. **This work is for the next note, not
that one.**

---

## 2. What to build

**Deliverable 1. The shape you proposed: a keyword on `resolve_receipt()` that only `_settle_note()`
passes.**

- Default False. The console and the CLI must not move.
- `_settle_note()` passes True.
- When True and the merged values do not validate, the receipt reaches `ok` and the failures are
  recorded on the extraction row, in the same manner `_apply_filed_note()` already records them.
- **The name is yours.** `decided_by_operator` is what you suggested and it reads well. Say what you
  chose.

**Deliverable 2. The log says what happened.**

A receipt that reaches `ok` carrying failed checks must be visible in `run.log` as exactly that, with
the failures named. **Paul reads `run.log`. A receipt that silently turns green is worse than the
fault being fixed.**

**Deliverable 3. Say what the resolution event records.**

`_apply_filed_note()` and `resolve_receipt()` differ in what they write to `resolution_events` on
this path. Say which outcome a settled-despite-failures receipt gets, and why it is the honest one.

---

## 3. What must not change

- **The console and the CLI.** Same behaviour, and prove it rather than assert it.
- **A discard.** `discard_receipt()` is not on this path.
- **A note that carries a `filed_path`.** `_apply_filed_note()` is untouched.
- **`validate()`'s rules.** Nothing in `worker\validation\rules.py` moves. The checks still run and
  still produce their notes; only what is done with the result changes, and only on this one path.
- **No schema change.**
- **Nothing in the run summary.**

---

## 4. Standard of evidence

- **Red before green**, with the failing output quoted. The red case is a settle note whose net plus
  VAT does not equal its gross, which today lands in `Resolutions\failed\`.
- **Drive a real note through a real `process_once()`.** Assert the receipt ends `ok`, has a
  `resolution_events` row, and that the failed checks are readable afterwards on the extraction row.
- **Assert the default holds.** A `resolve_receipt()` call that does not pass the keyword still
  produces `still_invalid` on the same values. This is the guard that the console and the CLI did not
  move.
- **Assert the log line exists** and names the failures.
- **Mutations anchored to one place**, each asserted to match exactly once, each printing its own
  diff. **Include one that flips the default to True**, and it must be caught by a test driving the
  console or CLI path.
- **Do not cite a line number in `config.py` or `app.py`.**
- **Flag, do not fix. Disclose your own mistakes. Say what each confidence rests on and what it is
  about.**

---

## 5. Two things from your last report that are answered here, and one that is not

- **Push to `feat/console-phase0`, no PR: yes.** That was Paul's answer to your last question and it
  stands for this work too.
- **`action` staying `filed` rather than becoming `settle`: your reasoning is accepted and the route
  you named is recorded in amendment 307.** Do not do it in this brief. It needs the Desktop half and
  Paul's word.
- **Not answered, and not part of this brief: whether a settled receipt should be re-published.**
  While IntelliBooks Desktop is the only writer of a note, it already holds the row, so nothing is
  lost. Leave it.

---

## 6. Where to write the report

**`C:\LastingImpact\receipt_capture\2026-09-09_REPORT_claude_code_decided_by_operator.md`.**

Carry in it: what was built, the name you chose and why, the commit, the suite before and after,
every mutation and its result, the log line as it actually appears, what the resolution event
records, any flag, and your own mistakes.
