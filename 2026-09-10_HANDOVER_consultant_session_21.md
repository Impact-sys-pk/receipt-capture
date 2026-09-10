# Handover: consultant session 21, chat 21

**Written 2026-09-10 by the consultant session, at Paul's instruction. It covers the session that ran
from 2026-09-10 morning to 2026-09-10 late afternoon.**

**You are the consultant session in Cowork. You own verification, this project's design document and
the prompts, and since 2026-09-06 you also write `IntelliBooks-Desktop-v3.html` on Paul's standing
instruction. You do not write the pipeline; Claude Code does.**

---

## 1. Read these, in this order, before doing anything

1. **This file, in full.**
2. **`CLAUDE.md`**, section "How this project is worked", and the traps. **The traps live there and
   nowhere else.** Section 7 of this file adds only the ones this session actually hit.
3. **`2026-07-25_CONSOLE_DESIGN.md`**, the amendment record from **307 to 316**. **312 to 316 is this
   session's own work. 307 to 311 is the session before it, and it is included because that session's
   handover is now in `archive\` and you are told not to read it**, so the design document is the only
   place those five survive. Then section 18, receipt and transaction integrity, before the body.
4. **`IntelliBooks\App\Docs\IntelliBooks-Change-Log.md`**, items **74 to 78**, which are this
   session's Desktop work.
5. **The two Claude Code reports of today**, both in the repository root:
   `2026-09-10_REPORT_claude_code_sidecar_and_cli_output.md` and
   `2026-09-10_REPORT_claude_code_statement_sidecar_and_cli_logging.md`.

**Do not read the handovers in `archive\`. They are superseded.**

**Do not state what any of these contains unless you have opened it.**

---

## 2. What is in flight

**Nothing is executing.** Claude Code reported its last brief and the tree is clean.

**One brief is written and held, and it is the next piece of work.**
`PROMPT_claude_code_2026-09-10_post_time_client_copy.md`, in the repository root, md5
`6fd42678dc4d3bd496c28d36245e645e`. **It carries "HOLD UNTIL THE CURRENT BRIEF IS REPORTED" at the
top, and that condition is now satisfied, so the line is stale and should be removed before it is
sent.**

**It is sub-step 10f.37, the pipeline half only.** The IntelliBooks Desktop half is yours and is not
started. **The two halves land together or not at all**, which is why this session did not send it
late in the day.

**Nothing else is half-built.**

---

## 3. What this session did, and the state to verify

**Verify at least three rows of this table against the code, the file or the disk before you act on
any of it. Say which three and what you found.**

| # | Claim | Where to check it |
|---|---|---|
| 1 | `file_statement()` writes the document alone. No `enriched_sidecar` parameter, one return value, no `.json` write. | `worker\filing.py`. Parse it, do not grep it. Amendment 316. |
| 2 | `app.py`'s statement branch takes one return value and builds no sidecar dict, and the receipt branch still builds and uses one. | `app.py`, the `file_statement(` call and `make_enriched_sidecar(`. Two different branches. |
| 3 | `worker\logging_setup.py` holds `LOG_LEVEL = logging.INFO` and a raise-only guard placed **before** the already-attached early return. | Same file. The guard and the return are about six lines apart. |
| 4 | Step 10f has 38 sub-steps, 33 built, 3 outstanding (10f.27, 10f.37, 10f.38) and 2 moved (10f.1, 10f.3). | Parse them out of `2026-07-25_CONSOLE_DESIGN.md` section 16. Do not count by hand and do not trust this row. |
| 5 | `IntelliBooks-Desktop-v3.html` is 366,037 bytes, md5 `e1cf5a56408a6e5e03fa488b12e15ea1`. | Stage it from Paul's machine and compare. |
| 6 | `2026-07-25_CONSOLE_DESIGN.md` holds 316 amendments, ascending and contiguous. | Parse the amendment table, which ends at the heading "How to use this document". A naive row regex also catches other tables in the document and returns 317. |
| 7 | `2026-08-20_LIST_outstanding_items_and_decisions.md` holds 178 items, contiguous, of which 78 are marked "Closed". | Parse it. **This session asserted "96 open, 82 closed" earlier in the day and that was wrong.** See section 7. |

**Amendments 312 to 316, in one line each.**

- **312.** The two stale IntelliBooks documents reconciled with the code.
- **313.** Check 5 of sub-step 10f.30 closed, and honestly: the case path was not exercised.
- **314.** 10f.1 and 10f.3 moved out of step 10f to items 177 and 178. 10f.27 unblocked and widened.
- **315.** 10f.37 and 10f.38 created. The 10f.12 to 10f.16 circular pointer defect.
- **316.** The statement data file stops being written. The two discard CLIs get a logging level.

**Change log items 74 to 78**, all built and only one confirmed live: the Client Settings card, the
flip checkbox, the closing balance, the delete dialogue, and the Edit button on Bank Transactions.

---

## 4. Step 10f, and what is left of it

**38 sub-steps, 1 to 38, no gaps, no duplicates, parsed out of the document on 2026-09-10. 33 built,
3 outstanding, 2 moved.**

| Outstanding | State |
|---|---|
| 10f.27 | **Both halves built today and never run together.** The pipeline half is committed and the Desktop half is change log item 77. **It is marked IN PROGRESS and should stay so until Paul deletes a real receipt and the copy in `Clients\` goes.** |
| 10f.37 | **The Post-time message from IntelliBooks Desktop.** Briefed and held. Section 2. |
| 10f.38 | **A document attached from the Bank Transactions tab**, attached instantly by Desktop and handed to Intellibills to archive and file. Not extracted, not published back, never in the receipts list. Designed in amendment 315 and not started. It follows 10f.37. |

**10f.1 and 10f.3 are no longer sub-steps.** They are items 177 and 178 of
`2026-08-20_LIST_outstanding_items_and_decisions.md`. **Item 178 is recorded as raised without a
purpose**: Paul could not remember what the always-on CSV export switch was for, and that is written
into the item rather than guessed at.

---

## 5. The decision that shapes the next piece of work

**Paul decided on 2026-09-10 that the client folder copy moves from the `publish` trigger to the
`post` trigger.** This is the reason 10f.37 exists and it is larger than the sub-step.

**His requirement, in his words:** `Clients\{client}\IntelliBooks\Receipts\{tax year}\` should hold
the receipts relating to that client's transactions and make sense to him and to the client years
later.

- **On `publish`** the folder holds whatever the pipeline succeeded on, including duplicates that got
  through, strays and documents that turned out to be personal, and nothing removes them.
- **On `post`** a document reaches the folder because it was attached to a transaction, so the folder
  is curated by construction.

**F16 on Firm Settings still reads `publish` and must not be changed.** 10f.16 records what happens
if the trigger moves before the message exists: the client folders go quiet with nothing reporting
it. **Paul switches it himself, deliberately, after 10f.37 lands.**

**One cost he raised himself and it is parked, not solved.** On `post` the client loses the only view
they had of what they sent, which today they get by accident because everything published lands in a
folder they can see. **He has agreed the answer is a list of what was received rather than a folder
of files. Its form is undecided and he asked to settle it immediately after 10f.37.**

---

## 6. What else is open

- **The console is up for review and nothing about it is decided.** Paul's words on 2026-09-10:
  "Forget about the console for now." **It no longer blocks 10f.27**, which amendment 314 unblocked.
- **Item 168, clearing the test estate.** Not started. Sample data stays.
- **Four flags from Claude Code's last report, none fixed.** Three copies of one log format string,
  which is small and obviously right if Paul wants it; `console.log` named and unattached, which is
  correct until step 14; the log files will never rotate at this volume; and two root scripts calling
  `basicConfig` at import.
- **Two flags from the report before it.** Three places now derive one data-file naming convention
  independently, and `retroactive_categorise.py` is a spent one-off still in the repository root.

---

## 7. Traps this session hit, on top of `CLAUDE.md`'s

- **No `device_bash` in this session.** Everything on Paul's machine is done by staging a file,
  editing it here, sending it, committing it back with `device_commit_files`, and staging it again to
  compare the md5. **Always read the file back and compare.**
- **Parse the right table.** A regex for `^| <number> |` over the whole design document returns 317
  amendments, because other tables in the document start rows with a number. Split on the heading
  after the amendment record first.
- **Do not carry a count forward from an earlier session.** See the mistakes below.
- **A test harness bug can prove nothing and look like a pass.** `let` inside an `eval` is scoped to
  the eval, so a harness that sets a variable that way is not setting the one the code reads. Expose
  it on `globalThis`.
- **Amendment 286 forbids new `confirm()` and `alert()` calls** in the Desktop file. A modal browser
  dialogue blocks every later event in the page. Build an in-page dialogue.
- **Ask Paul rather than deriving.** He is the operator. He knows what he clicked and what the toast
  said.
- **Name what is on screen.** This session named an "Import Receipts" button that does not exist and
  built two replies on it. `ingestReceiptFiles()` has no caller.

**This session's own mistakes, all disclosed to Paul at the time.**

1. **"96 open, 82 closed" for the outstanding items list.** The file holds 178 items of which 78 are
   marked "Closed". Found while writing this handover, by parsing the file rather than repeating the
   figure. **Row 7 of section 3 exists because of it.**
2. **A commit message naming amendments 312 to 316** when the commit carried 307 to 316. Claude Code
   caught it and used the wording verbatim as instructed; the message was amended.
3. **Amendment 316 said it changed 18.2b's rules table and it had not.** Found on re-reading the row
   and fixed in the same edit as the built marker.
4. **Called IntelliBooks writing into `Clients\` a boundary breach.** It is not. Standalone
   Intellibills is unaffected. The real objection is two processes naming files in one folder with no
   shared record.
5. **Argued from 18.2b as an authority independent of Paul** when it is this session's wording of his
   own earlier decision. He corrected it.
6. **Said "build 10f.16" before reading it.** It is marked BUILT. That reading is what found the
   circular pointer, so the mistake was productive, but it was still a claim made before opening the
   thing. Recorded in amendment 315.
7. **Left Category and VAT out of the Edit Transaction window.** Paul put them back. His call.
8. **Designed a re-run of check 5 from yesterday's method** without asking what made yesterday's
   failure possible. It was a model misreading and cannot be arranged, so the check could not fail
   for the reason being tested. Recorded in amendment 313.

---

## 8. Files this session changed, with their md5 as read back from Paul's machine

| File | Bytes | md5 |
|---|---|---|
| `C:\LastingImpact\receipt_capture\2026-07-25_CONSOLE_DESIGN.md` | 1,260,060 | `9e6985228360fa800039cc3b3ba426a1` |
| `C:\LastingImpact\receipt_capture\2026-08-20_LIST_outstanding_items_and_decisions.md` | 141,513 | `6f4db94f390e4fefff31a46a8c694e99` |
| `...\IntelliBooks\App\IntelliBooks-Desktop-v3.html` | 366,037 | `e1cf5a56408a6e5e03fa488b12e15ea1` |
| `...\IntelliBooks\App\Docs\IntelliBooks-Change-Log.md` | 244,229 | `98c37ec0dea76313bb5ee8802a51d02a` |
| `...\IntelliBooks\App\Docs\IntelliBooks-System-Specification.md` | 56,378 | `fc49e701199bc01544d1e7053e9e8ae7` |
| `...\IntelliBooks\App\Docs\IntelliBooks-System-Overview.md` | 24,905 | `18981958bf9339017f87006080d56c9c` |

**Briefs this session wrote, all in the repository root.**

| File | State |
|---|---|
| `PROMPT_claude_code_2026-09-10_discard_deletes_client_copy.md` | Executed |
| `PROMPT_claude_code_2026-09-10_cli_discard_says_what_it_left.md` | Executed |
| `PROMPT_claude_code_2026-09-10_statement_sidecar_and_cli_logging.md` | Executed |
| `PROMPT_claude_code_2026-09-10_post_time_client_copy.md` | **Written and held. Section 2.** |

**Test fixtures written this session**, both under `Test Receipts\` and both committed:
`TESTFIXTURE_bank_statement_2026-27.csv`, 22 rows, and `TESTFIXTURE_bank_statement_2026-09.csv`,
8 rows. Both were driven through `parseCSV()`, `parseDate()`, `parseAmount()` and `guessCol()`
extracted verbatim from the Desktop file before Paul imported them.

**Commits, all on `feat/console-phase0` and none pushed.**

| Commit | What |
|---|---|
| `2bdbe7d` | The discard change: `remove_client_copy()`, `filed_path` cleared, the resend unblocked |
| `5540787` | Its report |
| `25db035` | `file_statement()` stops writing the data file |
| `e580f81` | The CLI log level in the shared helper |
| `f5c11c2` | Its report |
| `493670f` | The consultant session's markdown, eleven files, 1,090 insertions, 11 deletions. **It replaces `93bbc1d`, amended for a wrong amendment range in its message. Claude Code proved the contents unchanged by the tree object, `93f47622`, identical before and after, and checked no remote branch held the original before rewriting it.** |

**`feat/console-phase0` was pushed at the end of this session**, `d4b5094..20080a2`, a fast-forward
of twelve commits, no force. **Origin is at `20080a2c4b012c746c3cd685c0cc3830cc336acd`**, read with
`git ls-remote` from the remote rather than from the tracking ref. Local and remote agree, zero
commits ahead, working tree clean.

**`493670f` is published from this point on.** Amending or rebasing anything at or below it is a
rewrite of shared history and needs Paul's explicit say-so.

---

## 9. Where the next chat starts

**Paul's instruction: the new chat begins precisely on the message below, which is the last
substantive message of this session, reproduced word for word.** Read it as the state of play and
wait for his answer to it. **Do not restate it back to him.**

---

**2026-09-10 16:04 BST (V=2)**

**My mistake**

The commit message range is wrong and it is mine. I wrote 312-316 without checking what HEAD's design
document ended at. Claude Code is right: the commit carries 307 to 316, ten amendments. It used my
wording verbatim, which is what I asked it to do.

**On its second observation**

It is right that the brief is unworked, and its numbering is one step behind.
`PROMPT_claude_code_2026-09-10_post_time_client_copy.md` is **sub-step 10f.37**, given its own number
today by amendment 315. `10f.16` is marked BUILT and names 10f.37 now, as does 10f.12. The warning in
`worker\client_copy.py` still names 10f.16 and is corrected when 10f.37 is built; that is written
into the brief.

**The choice, and it is the one I flagged earlier**

The tree is clean and everything is in git. That is the resting point I said to hand over at. Two
ways to go:

1. **Hand over now.** I write `2026-09-10_HANDOVER_consultant_session_21.md` naming commit hashes
   rather than describing files. Nothing is left half-done.
2. **Send the 10f.37 brief first.** It is written and held. It would open the pipeline half of the
   Post-time trigger, and its Desktop half is mine and not started, so a handover during it splits
   one piece of work across two sessions.

My recommendation: **hand over now**. 10f.37 is the largest thing left on step 10f and starting it
late in a session is how the two halves get separated.

---

## 10. What this handover does not claim

**It does not claim the state table is right.** Section 3 exists to be verified and one of its rows
carries a figure this session got wrong earlier the same day.

**It does not claim 10f.27 works.** Both halves are built, neither has been run against the other,
and until Paul deletes a real receipt and watches the copy leave `Clients\`, it is two pieces of code
that have never met.

**It does not claim the five Desktop changes work.** Only one was confirmed live, the closing balance
on a remembered mapping. The other four were driven over extracted functions and were not clicked.

**It does not claim the commit hashes were read from the repository.** Every one of them was reported
by Claude Code and none was read off the log by this session, which cannot run git. Check them.

**Confidence.** High on sections 4 and 8, because every figure was parsed out of the document or
hashed from a file staged back off Paul's machine while this file was being written. High on section
3's rows 1 to 3, read in the named source files at 15:50 BST today. **Section 5 is the weakest**: it
records a decision taken in chat, and the wording of Paul's requirement is his, but the reasoning
around it is this session's summary of a long conversation.
