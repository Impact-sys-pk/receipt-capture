# Handover: consultant session 29

**Written 2026-09-14 by the consultant session. It covers everything since
`2026-09-14_HANDOVER_consultant_session_28.md`, which is now spent.**

**You are the consultant session in Cowork.** You own verification, `2026-07-25_CONSOLE_DESIGN.md`,
`2026-07-25_BUILD_STATUS.md`, the `PROMPT_*.md` briefs, and `IntelliBooks-Desktop-v3.html` on Paul's
standing instruction of 2026-09-06. You do not write the Python pipeline; Claude Code does. Paul is
the only channel between you.

---

## 0. THE STANDING INSTRUCTIONS, INCLUDING TWO NEW ONES

1. **Every instruction to Claude Code is drafted by you**, not typed by Paul. Standing from
   2026-09-14, session 28.
2. **NEW. Send commands without being asked.** A PowerShell block, a Claude Code message: hand it
   over as part of the reply rather than offering to. His words: "Please do not bother me with your
   own admin. Just do it."
3. **NEW, and it changes how you write. Paul reads section 16 of `2026-07-25_BUILD_STATUS.md` and
   nothing else.** He said so plainly. **The amendment record is a file he never opens**, so
   "recorded at amendment N" is not the same as telling him. Anything he needs goes in the chat in
   plain words or into section 16. The amendment record still carries the reasoning, because that is
   what stops two sessions rebuilding one decision.
4. **Do not end a reply with an extra item he did not ask about.** He said so directly.
5. **You keep the queue of briefs for Claude Code** and hand him the next one when the previous
   reports. He should not have to remember what is owed.

---

## 1. THE STATE, IN ONE PLACE

**Section 16: 53 built, 23 outstanding, 3 cancelled, 1 moved, 80 steps.** Four steps went BUILT this
session: **10az** and **10r** by Claude Code, **10au** and **10ak** by the consultant session.

**Amendment record: 472 rows, 1 to 472, sequential, no gaps, no duplicates.** Amendments 458 to 472
are this session's.

**Git, `feat/console-phase0`:** commits through `ce520f7`. Pushes have been running behind the work
all day; check rather than assume.

---

## 2. Read these, in this order

1. This file, in full.
2. **`CLAUDE.md`**, "How this project is worked" and its traps. It gained a new section this session:
   **section 16 states every status twice and `check_build_status.py` is how you check they agree.**
3. **`2026-07-25_BUILD_STATUS.md`**, section 16.
4. **`2026-07-25_CONSOLE_DESIGN.md`**, amendments 458 to 472.

---

## 3. The queue for Claude Code, in order

Four briefs are written and waiting. **Hand him the next one when the previous reports.**

| # | Brief | What it is |
|---|---|---|
| 1 | `PROMPT_claude_code_2026-09-14_filed_path_on_delete.md` | Clear `filed_path` when 10f.27 deletes the client folder copy. SENT 2026-09-14. |
| 2 | `PROMPT_claude_code_2026-09-14_schema_drift_check.md` | Refuse to start when the database is missing a declared column. |
| 3 | `PROMPT_claude_code_2026-09-14_two_year_flags.md` | The year rule covers `transaction_date`; the three-digit refusal tests the digits. |
| 4 | `PROMPT_claude_code_2026-09-14_mkdir_membership.md` | Assert which folders `config.py`'s mkdir block creates. |

**Four steps are Claude Code's and have no brief yet**: 10at, 10ai, 10aj, 10aw. 10at and 10ai both
follow step 10r, which has now landed.

---

## 4. What happened, in order

**1. Step 10az, the delivery-log writer.** Claude Code's report read in full and checked against the
code: the two constants in `config.py`, both new functions in `worker/client_copy.py`, the single
call site, the five callers of `copy_for_published_receipt()` and the 33 tests, all enumerated from
the syntax tree. **Its one departure from the brief was right**: the moment field is `timestamp`,
matching `receipt_events`, not amendment 456's `posted_at`. Amendment 458 corrected the amendment.
Commit `f9f81ec`. Amendment 459.

**2. Flag 4 of that report closed by counting rather than by deciding.** 33 receipts, 26 with a
`filed_path`, every one of them a test client, so step 10i clears both sides of the reconciliation
together and there is nothing to backfill. Read through a shell, write-ahead log 0 bytes.

**3. Step 10au, the delivery-log reconciliation check, specified and built.** Amendments 463 and 464.
A **Check Delivered Documents** button on the **Client Data** tab, two directions and no more,
read-only. Ten cases driven in node against fake directory handles, five anchored mutations, all
caught, one of which survived its first run because the harness had no case for it. **Run on screen
by Paul the same day**, amendment 465, on a client with no log yet, so the absent-log path is proved
live and the two-direction comparison still is not.

**4. A LIVE FAULT, AND IT WAS THE MOST IMPORTANT THING OF THE DAY.** Paul's `run.log` showed
`table extractions has no column named line_items`. **Step 10p added that column to `schema.py` on
2026-09-12 and nothing added it to the live database**, because `CREATE TABLE IF NOT EXISTS` never
alters an existing table and sub-step 10d.34 removed the migrations. `save_extraction()` names the
column unconditionally, from nine call sites, **so no receipt could have been extracted and recorded
for two days**. Only an empty inbox and an empty mailbox hid it. Every column of all eleven tables
compared before and after: exactly one mismatch, and zero after. Fixed by Paul with one
`ALTER TABLE`, backup taken first. Amendment 466. **The suite cannot see this class of fault**,
because every test builds a database from the current `schema.py`. Brief 2 in the queue is the guard.

**5. Ten stale notes found under it.** `Intellibills\Resolutions\failed\` holds ten notes for one
receipt from 2026-09-11, rejected because the pipeline did not yet accept `action: corrected`. It
does now. **They are test saves of one correction with the net moving between 6.67, 6.68, 9.00 and
0.67**, which is the arithmetic gate of change log item 87 being exercised. Paul's decision: leave
them, they go at step 10i.

**6. Step 10ak, and it was not what its row said.** The row read as though the phone app's Statements
screen needed building. **It existed.** `worker/intake/folder_reader.py`, which no session had ever
opened, sets `is_statement` from the sidecar's `type` key; `upload.js` writes that key; the phone app
has the checklist screen. Amendment 470. **Then the deeper finding: the live site was still running
the July build**, version 5, so every phone-side change of step 10d had never been deployed while
step 10d was recorded BUILT across all three codebases. Paul deployed version 6, sent one Uber
statement from the phone, and it filed correctly with `source = phone`. Amendment 471.

**7. The phone shortcut fault Paul has reported for weeks, fixed.** `manifest.webmanifest` set
`start_url` to `"./"`, so the iOS home screen icon opened the app with no token and showed
**Set up your app** with no way to recover. **It was never a storage problem**, which is where every
previous look went, including session 28's. One `<link rel="manifest">` line removed. Confirmed
working by Paul on the phone and in desktop Chrome.

**8. Section 16 was disagreeing with itself about nineteen steps.** Seventeen paragraphs read
OUTSTANDING under a table row reading BUILT, and two steps had a row and no paragraph. **The
consultant session proposed deleting the word from the paragraphs and Paul refused it, rightly**: he
reads the paragraphs. The word stays, the nineteen are corrected, and the check is written down as
`check_build_status.py` and named in `CLAUDE.md`. Amendment 469.

**9. Step 10r.** Claude Code, commit `ce520f7`. `config.EXPORTS_DIR` is
`INTELLIBILLS_ROOT / "Exports"`. **The finding in its report is worth more than the step**: the brief
named two sites, Claude Code's independent sweep of all 151 tracked files agreed, and both were
wrong. The site that broke contains the word `exports` nowhere. **Two sweeps agreeing is not the same
as the set being closed when both sweep the same term.** Amendment 472.

---

## 5. Paul's decisions this session

| What | Decision |
|---|---|
| The delivery log's moment field | `timestamp`, matching `receipt_events`, not `posted_at` |
| Backfilling the delivery log | Neither a backfill nor a start date. Step 10i clears both sides |
| Step 10au, where it appears | Client Data tab, one client |
| Step 10au, what it reports | Two directions only, read-only |
| The implausible year bound | 2000 to the current year plus one, taken from Desktop's shipped rule |
| An implausible year with no supplier | `failed`, the same as an invalid date |
| Claude Code's flags 8.2 and 8.3 | Both taken |
| Flag 8.4, the mkdir membership | Taken, as its own brief |
| Clearing `filed_path` on delete | Yes |
| The start-up schema check | Build it |
| The nineteen stale statuses | The word stays; correct them and write down the check |
| Deploying the phone app | Yes, version 6, done |

---

## 6. My own mistakes, disclosed

1. **I proposed removing the status word from section 16's paragraphs.** Paul refused it and his
   reason was better than mine: it is the copy he reads, and I was deleting the useful copy to
   protect the one nobody checked.
2. **I repeated "never deployed" from session 28's handover into amendment 470 without checking it.**
   It was Paul's two words about what he could see on a screen, and the cause was a hidden card.
3. **Amendment 465 carried an objection that was wrong.** I took a comment about an `ok` receipt and
   applied it to a discarded one without opening the query. Corrected in place.
4. **Sub-step 10d.41 has named `_parse_numeric_date()` since 2026-08-21 and no such function
   exists.** It is `parse_ambiguous_date()`. I carried the wrong name into a brief and an amendment
   from the document rather than from the code. Amendment 467.
5. **I marked step 10au BUILT in the table and left its paragraph OUTSTANDING**, in the same hour as
   telling Paul about sixteen other steps with that exact fault. `check_build_status.py` found it on
   its first run.
6. **The times at the head of my replies were wrong for part of the afternoon**, carried forward
   rather than read. The container clock and Paul's machine agree; I simply stopped reading it.

---

## 7. What this handover does not claim

- **Step 10au's two-direction comparison has never run.** `IntelliBooks\Delivery\` does not exist
  yet, so no document has been copied since the log writer landed. It proves itself on the first
  client folder copy.
- **`2021-09-04_ringgo_5.17.png` is recorded with a `filed_path` and is not on disk**, and its
  receipt is `ok`. Nothing explains it. Not diagnosed.
- **No test suite was run by this session.** Every figure is Claude Code's, relayed and spot-checked
  against the files it names.
- **The phone app is now an iPhone arrangement.** An Android client needs the manifest back and a
  static manifest cannot carry a per-client token.
- **Claude Code reports the Git Bash clock on Paul's machine names the zone wrongly**, an hour out.
  Its flag 8.5. Nobody has picked that up and it is not in `CLAUDE.md`.

---

## 8. Where the next chat starts

**Ask Paul first, the order is his.**

1. **PROVE STEP 10au'S SECOND HALF. Paul asked for this to be remembered, 2026-09-14.** The two-direction comparison has never run: send one receipt from the phone, let the pipeline publish and copy it into the client folder, then press **Check Delivered Documents** on the **Client Data** tab. Until that run, half of 10au is code nobody has seen work. Step 10au's own paragraph in section 16 says so too.
2. **Hand him the next brief in the queue** when Claude Code reports on `filed_path`.
3. **Step 10an**, `handoverPack()`'s six files run against a real client's books. The only one of the
   consultant session's four steps that needs nothing from Paul.
4. **Steps 10al and 10ao**, Desktop checks written for Paul to run on screen.
5. **Step 10am**, a synthetic test forcing a receipt through the Review seam.
6. **Step 10t**, the reports set, scoped generally on Paul's instruction until it is taken up.
