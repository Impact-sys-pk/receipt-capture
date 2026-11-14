# Claude Code brief, 2026-09-18: step 10ai, the capture report goes to the client's folder

Written by the consultant session, 2026-09-18, 13:06 BST, read off the clock in this reply. Step
10ai of `2026-07-25_BUILD_STATUS.md`, amendment 388, Paul's decision of 2026-09-13, confirmed again
by him on 2026-09-18 with the portal question below put to him first.

**Report to `2026-09-18_REPORT_claude_code_capture_report_to_client_folder.md` in the repository
root.**

**One commit. Build it, propose the commit, and wait for a yes.**

---

## Two rules about this brief

**1. `2026-07-25_BUILD_STATUS.md` and `2026-07-25_CONSOLE_DESIGN.md` are not yours to edit.** You
report; the consultant session verifies against the code on Paul's machine, marks the step and writes
the amendment.

**2. Everything this brief names has been read this session**, in `capture_report.py` and
`worker\filing.py` on Paul's machine. Where it does not name something, that is deliberate and the
place is yours to find.

---

## What is decided

**`capture_report.py`'s output file moves out of `Intellibills\Exports\` and into the client's own
folder under `Clients\`.**

**`export_bookkeeping.py` does not move and is not touched.** It writes one whole-database CSV across
every client and firm with no client filter, so there is no client to file it with.

**Nothing about the report itself changes**: not what it selects, not the two scopes, not the
columns, not the text, not the `--client`, `--tax-year`, `--from` and `--to` arguments. **Only where
the file lands.**

## Where, exactly, is yours to settle

The step says "matching where receipts and statements already live". Read those two and follow them
rather than inventing a third convention. **Say in the report which path you chose and what you
matched it to.**

**The folder name comes off the client record's `client_folder_name` and never off `client_name`.**
`get_client_directory()` in `worker\filing.py` carries that rule and its reason: the folder name is
fixed once a folder exists and the display name is freely editable. `capture_report.py` already
reads that client record: `render()` looks the client up in `config.CLIENTS_BY_ID` for the display
name, and `client_folder_name` is a field on the same record.

## Three things to decide and report rather than choose silently

1. **A client the registry does not know.** `render()` already handles this for the heading, printing
   a stand-in where the record is missing. With no record there is no folder name. **Decide what the
   command does then and say why.** Falling back to the old folder and refusing outright are both
   defensible; choosing one without saying so is not.
2. **A client folder that does not exist on disk.** Whether the command creates it or refuses is the
   same kind of choice.
3. **Whether `config.EXPORTS_DIR` still has a user** after this. Enumerate it rather than assume.
   **Flag it, do not act on it.**

## The comment that argues the opposite, and it must be struck rather than deleted

`capture_report.py` carries a block at lines 60 to 79 explaining where the output goes. It says
`Clients\` is excluded because the report is not a client-facing document, citing **section 18.2b**,
and names **18.2** and **18.2a** alongside it.

**That reasoning is superseded by Paul's decision and the block must say so**, keeping the old wording
struck beside the new, which is this project's convention and is already how that same block records
step 10r superseding what came before it.

**And section 18 was retired entire on 2026-09-16 by amendment 498.** Its live cross-references were
counted and repointed in `2026-07-25_CONSOLE_DESIGN.md`, `2026-07-25_BUILD_STATUS.md` and
`CLAUDE.md`. **Nobody counted the Python.** Fixing that generally is not this brief's job.
**Enumerate the references to section 18 across the production `.py` files and report the count.
Flag it, do not fix it**, beyond the block you are already editing.

## What Paul weighed, so you do not re-open it

`Clients\{name}\...` is the client's own records and is what a portal would show, per amendment 70.
Amendment 73's reasoning says a client looking at a capture-fed folder "sees a dump of files", and
this report names receipts that failed, duplicated or were discarded. **Paul was shown that conflict
on 2026-09-18 and decided the move anyway**, on the grounds that no portal exists and that a portal
will need an explicit rule about what it shows regardless. **The consultant session is recording, in
the step, that this file is on the list of what a portal must not show.** Nothing for you to build
from that; it is here so the placement is not re-litigated in your report.

## What must not change

- **`_next_free_path()`'s behaviour.** Two runs in the same second must still not overwrite each
  other, and nothing this system writes is overwritten.
- **The output being derived from a config constant rather than from the working directory**, so
  running the command from anywhere writes to one place. That reason survives the move.
- **`make_output_safe()`** and the read-only database connection.
- **What is printed to the screen.** It is the same text as the file and stays that way.

## Evidence

The standard in `CLAUDE.md` applies in full. Three parts this change makes specific:

- **Red before green.** A test that asserts where the file lands, failing against today's code
  because today it lands in the export folder.
- **A test for each of the three decisions above**, whichever way you settle them. The registry-miss
  case especially: it is the one a person will hit first and the one most likely to be silently
  wrong.
- **Mutations**, each anchored, asserted unique, diff printed. At minimum: send the output back to
  the old folder, and compose the path from `client_name` instead of `client_folder_name`. **The
  second is the one that matters**, because it passes for every client whose two names happen to
  match.

Run the suite again after the commit if this adds a file.

## What to report

Everything the standard asks, plus:

1. **The path you chose**, written out in full for one real client, and what you matched it to.
2. **Your answers to the three decisions**, each with its reason.
3. **The count of section 18 references across the production `.py` files.** Flag, do not fix.
