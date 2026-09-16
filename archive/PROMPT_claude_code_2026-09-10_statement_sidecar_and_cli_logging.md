# Brief: stop writing the statement sidecar, and make the two discard scripts log

**Written 2026-09-10 by the consultant session, from Paul's decisions the same
afternoon on flags 4 and 1 of
`2026-09-10_REPORT_claude_code_sidecar_and_cli_output.md`.**

**Read first, in this order:** `CLAUDE.md`, the section "How this project is
worked" and the seven traps. Then **18.2a and 18.2b** of
`2026-07-25_CONSOLE_DESIGN.md`, because deliverable 1 is 18.2b applied to a
folder it was not written against.

Two deliverables, unrelated to each other. Do them as two commits.

---

## 1. Deliverable 1: `file_statement()` stops writing the sidecar

**What happens today.** Every statement filed writes the document into
`Clients\{client}\IntelliBooks\Statements\{tax year}\{platform}\` and writes a
second file beside it, the same name with `.json` appended.

**Paul's decision: stop writing it.**

**Why.** 18.2b's Image only rule is written about the receipt copy, and its
reasoning is about the client folder, not about receipts: *"No data file beside
it. The sidecar existed to carry figures between the two modules, and 18.3
replaces that. The copy is a document for a person and a portal, so nothing needs
to parse it."* A statement copy in `Clients\` is the same kind of thing, for the
same two readers. Your own report established that nothing in the pipeline reads
it; the consultant session enumerated every `.json` reference in
`IntelliBooks-Desktop-v3.html` and nothing there reads it either.

**Scope, exactly.**

- **Only the sidecar beside the client folder copy stops.** The statement
  document itself is still written, unchanged, to the same path.
- **Existing sidecars are left alone.** Do not delete them, do not sweep for
  them, do not write a migration. They are inert.
- **`Intellibills\Documents\` is never written to or deleted from**, and nothing
  in Intellibills' own storage changes. If a sidecar or a data file lives there,
  it stays.
- **Say in the report whether any other function writes a `.json` beside a file
  under `Clients\`**, and enumerate rather than assert. If one does, **flag it
  and do not touch it**: Paul's decision today was about the statement one.

---

## 2. Deliverable 2: the two discard scripts write real log files

**What happens today.** `logging.basicConfig` is called in `app.py`,
`check_missing_categorisation.py` and `retroactive_categorise.py`, and in neither
`discard_receipt.py` nor `resolve_receipt.py`. Both of those attach a handler and
neither sets a level, so the root logger stays at WARNING and their log files are
effectively empty. **Confirm this from the code before you change anything** and
quote what you find; it is my reading, not yours.

**Paul's decision: fix it, and fix it once.**

**Set the level inside the shared `attach_log_handler()`**, rather than adding a
`basicConfig` call to each script. Two entry points behave one way and two
another because of a line that was copied into some of them; putting it where the
handler already goes makes all four the same by construction, and a fifth script
written next month inherits it.

**What to establish and report, rather than assume.**

1. **That the two currently silent files start filling**, shown by running each
   script once and quoting the log file's size before and after.
2. **That the other two entry points are unchanged.** `app.py` already sets a
   level. Say what happens when both run, which one wins, and whether the level
   the pipeline runs at today is the level it runs at after this change. **If it
   would change, stop and report it rather than changing it.**
3. **Whether anything is now logged that should not be.** A level lowered on the
   root logger can bring a third-party library's chatter with it. Name any that
   appear.

---

## 3. Evidence, both deliverables

- **Red before green**, with the failing output quoted.
- **Mutations** through the harness, each anchored once and printing its diff:
  for deliverable 1, restore the sidecar write and show the test fails; for
  deliverable 2, remove the level and show the log file is empty again. **And a
  prose-only control that survives**, so the harness is shown to be capable of
  passing.
- **Enumerate from the syntax tree** anything asserted about a set of call sites
  or files, and print it whole. **`.history\` excluded.**
- **Never `import config` to read a value.** `CLAUDE.md`'s fourth trap.
- **Nothing run against the live practice root.**
- **Flag, do not fix.** **Disclose your own mistakes, including corrected ones.**
- **State a confidence level and say what it rests on**, for each deliverable
  separately.

---

## 4. Committing and reporting

**Two commits on `feat/console-phase0`.** Do not push and do not create a branch.
Do not commit `2026-07-25_CONSOLE_DESIGN.md`, any `PROMPT_*` or `HANDOVER_*`
file, or anything under `Test Receipts\`.

**Write the report to
`C:\LastingImpact\receipt_capture\2026-09-10_REPORT_claude_code_statement_sidecar_and_cli_logging.md`**
and carry both commit hashes in it.
