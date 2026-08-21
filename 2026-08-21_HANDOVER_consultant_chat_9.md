# Handover to consultant chat 9

**Written 2026-08-21 by consultant chat 8, in a session run by user paul.keating@intellitax.co.uk,
for a new session to be run by user pdk7@hotmail.co.uk.**
**Date read from a file timestamp, not from a session header. Amendment 109.**

**This document points. It does not copy.** Everything decided is in section 16 of
`2026-07-25_CONSOLE_DESIGN.md`. Everything open is in
`2026-08-20_LIST_outstanding_items_and_decisions.md`. Neither is restated here, and this file
must never grow into a third copy of either. **Three carriers have already died of exactly
that**: the two lists at the end of `IntelliBooks\App\Docs\IntelliBooks-Change-Log.md`, deleted
2026-08-20, and section 7 of `2026-08-20_HANDOVER_consultant_chat_8.md`, superseded the same day.

---

## 1. Who you are, and who you can talk to

You are the **consultant session**. You own verification, `2026-07-25_CONSOLE_DESIGN.md`,
`2026-08-18_BOUNDARY_two_products.md`, and the briefs the build sessions work from. **You write
no production code.**

Three sessions work this project and **none can see the others**. A Claude Code session owns the
Python pipeline. A second Cowork session owns `IntelliBooks-Desktop-v3.html`. The Uber statement
parser is worked in its own repository with its own project and is not yours.

**Paul is the only channel between all of them.** Anything you want another session to do, you
write as a brief for Paul to carry. If you are not certain which role you are in, ask before
doing anything.

## 2. Mount these before you read anything

Eight folders were connected to chat 8 on device `xps13-9350-claude-instance2`. **A new session
inherits none of them**, so they have to be granted again:

```
C:\LastingImpact\receipt_capture
C:\Intellibills
C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills
C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliBooks
C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliCharts
C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Clients
C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Scripts
C:\LastingImpact\uber-phase1-ingestion-worker
```

**`C:\Intellibills` and `...\OneDrive - Intellitax Accounting Limited\Intellibills` are two
different folders and both are live.** Name the full path on first mention, every time. The
Uber repository is out of scope. `Scripts` was never opened by chat 8.

**You may or may not have a shell on Paul's machine, and this is not constant between sessions.**
With no shell, git state can still be read by staging `.git\HEAD`, `.git\refs\`, `.git\index`
and the loose objects, which works because the repository has no pack files. That reads the
tracked side exactly and **cannot see untracked files at all**, so list the folder immediately
before predicting them.

## 3. Read in this order

1. **`CLAUDE.md`** in the repository root. Its "How this project is worked" section is the
   induction, and it holds the git conventions and the four traps.
2. **`2026-07-25_CONSOLE_DESIGN.md`**, now v1.23, 443,674 bytes, **121 amendments, verified
   contiguous 1 to 121 on 2026-08-21**. The amendment record at the top carries every decision
   with its reasoning and its superseded wording. **Read section 18, Receipt and transaction
   integrity, before the body**: it supersedes parts of sections 12, 13A, 14, 16 and 17.5.
   Then read **section 16**, starting with the table at its head.
3. **`2026-08-20_LIST_outstanding_items_and_decisions.md`**, 61,341 bytes. **Read the count line
   at the top for the figures**, rather than trusting a number written here, because Paul is
   reducing the list. Section 1 is the items blocking a scheduled step; read that first.
4. **`2026-08-18_BOUNDARY_two_products.md`**, which is the product boundary and the four breaches
   of it found so far.
5. **`IntelliCharts\2026-08-05_NOTE_master_chart_of_accounts.md`**, addendum first, then the
   body, because several decisions changed after the body was written. IntelliCharts is parked.
6. **This project's own document list in Claude**, which is part of the reading and not a filing
   cabinet. `2026-08-15_RUNLOG_coa_august_check.md` exists there and nowhere on disk.

## 4. The two lists, and a standing instruction

**Section 16 and the outstanding items list are the only two lists, and both are to be kept up
to date at all times.** Not at the end of a session, and not when a document is next rewritten.

- A **decision** taken in chat becomes an amendment and a step in section 16 **before the chat
  moves on to anything else**. Amendment 110 exists only because amendment 105 recorded a
  decision and no step was ever added for it.
- **Every step and every sub-step in section 16 carries one of four words at its head: BUILT,
  OUTSTANDING, CANCELLED, MOVED.** Amendment 121. The table at the head of the section carries
  the same status for every step, and **is corrected in the same edit as the step below it**.
  **Nothing is inferred from strikethrough**, which in that section means built, superseded
  wording, suspended or cancelled depending on where it sits. That ambiguity is why the
  convention was introduced, and it had already misled the session that wrote it.
- An **open question** raised in chat goes into the outstanding items list the same way.
- A **closed** item keeps its number, moves to the **Closed** section at the end of that file,
  and the count line at the top is corrected in the same edit. **Numbers are never reused**, so
  the highest number is the count of items ever raised.
- **The count line is the check.** Open plus closed must equal the highest number. If it does
  not, an item was removed without being recorded.
- **Anything agreed in a chat and not written to a file is lost.** That is not a maxim here, it
  is the recorded cause of items 126 to 130.

**Paul's instruction of 2026-08-21, and hold to it:** the outstanding items list is a simple
document he works off. It is not to become a rival to the design document. **Do not add
apparatus to it.** His first task in chat 9 is to reduce the open items substantially; the count line at the top of that file gives the current figure.

## 5. Where the work is

**Read the table at the head of section 16 rather than this paragraph**, because the table is
kept current and this is not. As at 2026-08-21 it reads 18 built, 18 outstanding, 1 cancelled,
1 moved out of this order, 38 steps.

The 2026-08-01 reset is done. **Step 10d is next**: one client registry, plus `capture_token`,
across all three codebases in the same window, **now written as 34 numbered sub-steps `10d.1`
to `10d.34`**, each with its own status. **Step 10a is outstanding and is easy to misread as
built**: its deliverable is config constants for the pipeline's folder names in place of the
string literals at `worker/filing.py:78` and `:103`, and it has never been done.

**The three briefs for step 10d are not written**, one each for the pipeline, IntelliBooks
Desktop and the capture app. **They are not your next task.**

**Your next task is to stand by and follow Paul's directions in reducing the items in the
outstanding list.** That is his instruction of 2026-08-21 and it comes before the briefs. Do not
start drafting them, and do not treat step 10d being next in the build order as licence to begin
work on it.

**Three outstanding items block parts of 10d, and each is named at the sub-step it blocks
rather than only on the other list.** Item 98 blocks `10d.2`, the books files that come across.
Item 1 blocks part of `10d.19`, where an unattributable intake event is logged. And item 6
questions the `processed_attachments` key at `10d.32`.

**One of them is a contradiction in this document and needs Paul's ruling before the largest
brief can be written.** Item 139: amendment 73 and section 18.2b say the pipeline loses
`get_client_directory()` and never writes into `Clients\` at all, sub-step `10d.14` says it
keeps it and repoints it, and the code still files there and did so on 2026-08-20.

**Do not go looking for the chart of accounts inside `receipts.db`.** There is no
`coa_accounts` table and there will not be one. The master is
`IntelliCharts\COA_MASTER_v1.csv`, 122 accounts on four-digit codes. Any three-digit code found
anywhere is legacy.

## 6. How to work here

`CLAUDE.md` holds the method in full. The four that bite hardest:

**Verify against the thing itself, never against a summary of it.** Read the file back, query
the database, count the files on disk. A report saying "done" is a claim. About half the
defects on this project were found by checking a claim made in good faith that was wrong, and
**four items on the outstanding list were corrected or withdrawn on 2026-08-21 by checking
findings a sweep had reported.**

**Flag, do not fix.** Something wrong that the task did not ask about gets reported, not repaired.

**Never state a count about a set you have not enumerated.** A filter is not a reader. A search
for files whose contents match a string is not a list of files that exist.

**Name the file, the function or the window in full, every time.** Not "the prompt", "the file
above" or "the box". Ambiguity costs Paul a round trip every time.

**And say what a confidence level rests on.** "High, because I read it back" and "high, because
it seemed right" are different claims.

## 7. What chat 8 got wrong

**Reasoned from a timestamp instead of reading the file.** Asked whether line 10 of
`C:\LastingImpact\receipt_capture\.env` was still there, I compared its mtime against the plan
file's and concluded the line survived. It had been deleted on 2026-07-31. Reading the file
structurally, printing only variable names and value lengths, took one command and exposed
nothing. **Declining to read a file and then reasoning about its contents is not caution.**

**Asserted an item from a stale header in the one file that would have disproved it.** Item 107
claimed change log items 1 to 11 were on no list, taken from
`IntelliBooks-Change-Log-Original-Items-1-11.md`'s own header. `IntelliBooks-Change-Log.md`
begins at Item 1. One search for `^## Item` settled it. The item is withdrawn.

**Told Paul where the project stood without checking, and was wrong.** Asked what was built,
chat 8 answered "built to 10c, next is 10d". **Step 10a was not built.** Its strikethrough is on
replaced wording, not on completion, and two commands against `config.py` and
`worker/filing.py` settled it. Those commands were run after Paul challenged the answer rather
than before giving it.

**Reported three things as missing after looking for the wrong kind of thing.** Item 129 said
the `docs/console-design` safety net had been deleted; **it is a git branch, not a folder, and
it exists.** Earlier the same day: reasoning about `.env` from a timestamp instead of reading
it, and asserting item 107 from a stale header in the one file that disproved it. **The pattern
is reporting an absence without first confirming what kind of thing was being looked for.**

**Ran away with a question Paul asked simply.** Asked how to tick items off a list, chat 8
produced a four-outcome taxonomy, a status column and a set of validation rules. **Paul had
asked for a simple list and had already said not to add complication.** His words: "Follow my
instructions. Follow my lead." The pattern to avoid is answering a narrow question with a
system.

**And one from earlier in the same session, because it is the same pattern:** chat 8 proposed
restructuring section 16 around two product modules. Paul rejected it: the module split was "a
way of thinking about the design", not a natural grouping. **Do not introduce something new
just for the sake of it.**

## 8. First action

Mount the eight folders, read in the order at section 3, then **confirm your understanding back
to Paul and list every question before doing anything else.**

**Then stand by.** The work is reducing the outstanding items list, at his direction and at his
pace. Do not start anything, do not write to a file, and do not make a change without his
express permission.
