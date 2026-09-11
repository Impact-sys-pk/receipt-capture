# Brief: store UTC, show London. And one output path that follows the working directory

**Written 2026-09-11 by the consultant session, from Paul's decision the same day. Flags 5 and 6 of
`2026-09-11_REPORT_claude_code_capture_report.md`.**

**HELD behind `PROMPT_claude_code_2026-09-11_category_hold.md`. One brief per session at a time.**

**Read first, in this order:** `CLAUDE.md`, the section "How this project is worked" and the seven
traps, including the two rules added on 2026-09-11. Then 18.2a of `2026-07-25_CONSOLE_DESIGN.md` for
where the archive path comes from.

---

## 1. The decision

**Paul, 2026-09-11: store UTC, show London.**

Every timestamp stays in the database exactly as it is. **Every timestamp a person reads is converted
to Europe/London first, and says which zone it is showing.**

**Why storage does not change, so nobody proposes it.** On the last Sunday in October London has
01:30 twice. A timestamp stored in local time for that hour cannot be told apart from the other one,
and this is an audit trail. These timestamps are also compared as text, so one zone is what makes
sorting work.

**What is already correct and must not be touched.** A document date, `extractions.invoice_date`, is
a date with no time and no zone, and the tax year is derived from it. **The tax year scope has no
timezone question in it at all.** Do not convert a document date. Do not touch
`determine_tax_year()`.

---

## 2. The scope, and it is every surface at once

**Half of this change is worse than none of it.** If one report shows London and a log shows UTC, the
two disagree about which day something happened and both look authoritative. **So the conversion is
applied to every human-facing surface in one change**, or it is not applied.

**Enumerate the surfaces from the syntax tree before you start, and print the enumeration whole.**
Do not take a list from this brief; this brief has not read them. What counts as a surface: anything
that renders a stored timestamp for a person to read, which includes at least the four process logs,
the capture report, and the CLI output of the root scripts. **Say in the report what the full set
was and how you found it.**

**What is NOT a surface.** Anything machine-readable keeps UTC, and say which ones you decided are
machine-readable and why: the database, `runs.ndjson`, the per-firm event logs, resolution notes and
handoff messages, the published item, and any CSV a machine reads. **A file that both a person and a
machine read is a decision, not a default. Report it rather than choosing quietly.**

---

## 3. The dependency, and Paul has already been asked

**`zoneinfo` is in the standard library, but on Windows it reads its data from the `tzdata` package
rather than from the operating system.** `requirements.txt` holds three lines and `tzdata` is not one
of them, read on 2026-09-11.

**Add `tzdata` to `requirements.txt`. APPROVED BY PAUL, 2026-09-11.** It is a pure-data package from
the Python core team with no code in it.

**Do not hand-roll the BST rule instead.** "Last Sunday in March to last Sunday in October" is
correct today and is a rule that has changed before and is periodically proposed for change again. A
hard-coded version is a check that silently becomes wrong.

**Fail loudly if the zone is unavailable**, naming `tzdata`, rather than falling back to UTC and
printing a London label over a UTC time.

---

## 4. The second thing, and it is unrelated except that it is operator output

**`export_bookkeeping.py` writes to `Path("exports/bookkeeping_export.csv")`, relative to the working
directory.** Run from anywhere but the repository root it creates an `exports\` wherever the shell
was standing. **`capture_report.py` already does the right thing**, deriving from `config.BASE_DIR`.

**Make `export_bookkeeping.py` match it.** Flag 5 of the step 10n report, and Paul's decision of
2026-09-11.

---

## 5. The archive folder path takes the London date too

**`worker\storage\store.py` builds the archive folder from the UTC year and month**, in
`save_file()` and `save_inbox_file()`. So a receipt arriving at 00:30 on 1 July British time is filed
under June. **That folder is browsed by a person, so it is one of the surfaces in section 2 and takes
the London date with the rest.**

**Nothing migrates and nothing existing moves. Paul's instruction, 2026-09-11: this is for the
future, and he does not care about the existing test data.** So historic files keep the folder they
are in and the change applies from the moment it lands.

**Why that is safe rather than two conventions in one tree, established here rather than left for you
to work out.** Only two places in the production tree build this path, both in
`worker\storage\store.py`, and both build it to WRITE. **Nothing recomputes it to read.** Every
reader takes the stored path off the row, for example `Path(receipt["file_path"])` in
`worker\resolution\service.py`. The third mention of `config.FILES_DIR` in the tree is a log line.
**Enumerated from the syntax tree on 2026-09-11 by the consultant session; re-run it and print it
whole rather than trusting this paragraph.** That is 18.2c's first rule doing its job: a path is
copied at handoff and never referenced afterwards.

**18.2a's reason for the arrival date is untouched.** It uses arrival rather than the document date
so that no file ever has to move when an invoice date is corrected. Which arrival day it is does not
bear on that.

---

## 6. What must not change

- **No stored value moves.** Nothing is rewritten, no migration, no backfill.
- **`determine_tax_year()` and every document date** are untouched.
- **Nothing is published, re-processed, and no receipt's status moves.**
- **Nothing is written into `Clients\`, `IntelliBooks\` or `Intellibills\Documents\`.**
- **F16's value** is `post` on Paul's firm record and nothing here touches it.

---

## 7. Evidence

- **Red before green**, with the failing output quoted.
- **A test at the boundary in both directions**: a stored UTC timestamp that is the previous day in
  London, and one that is the same day, asserted to render and to filter as the London day. The
  23:00-to-midnight UTC hour in summer is the case that matters.
- **A test on the October repeated hour**, showing that the two 01:30s stay distinguishable in
  storage and that whatever is shown for them is stated rather than ambiguous.
- **A test that a document date is NOT converted.**
- **A test that the machine-readable outputs are unchanged**, driven from the set you enumerated.
- **Mutations** through the harness, each anchored once and printing its diff: the conversion is
  dropped and UTC shown under a London label; the conversion is applied to a document date; the
  range filter converts but the displayed column does not; and a prose-only control that survives.
- **Enumerate from the syntax tree** anything you assert about a set, and print it whole. `.history\`
  excluded.
- **Run the suite again AFTER committing**, per the rule added to `CLAUDE.md` on 2026-09-11: this
  change may add a file, and two source guards sweep the git-tracked set.
- **Nothing run against the live practice root. Never `import config` to read a value.**
- **Flag, do not fix. Every flag carries the obvious fix**, per the rule added to `CLAUDE.md` on
  2026-09-11. **Disclose your own mistakes. State a confidence level and say what it is about.**

---

## 8. Committing and reporting

**Commit on `feat/console-phase0`.** Do not push, do not create a branch, and do not commit
`2026-07-25_CONSOLE_DESIGN.md`, any `PROMPT_*` or `HANDOVER_*` file, or anything under
`Test Receipts\`.

**Write the report to
`C:\LastingImpact\receipt_capture\2026-09-11_REPORT_claude_code_london_time.md`** and carry the
commit hashes in it.

**One section at the top for Paul.** The full set of surfaces that now show London time, and the set
that deliberately still shows UTC and why.
