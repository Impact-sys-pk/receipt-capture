# Handover to consultant chat 10

**Written 2026-08-22 by consultant chat 9, in a session run by user pdk7@hotmail.co.uk.**
**Date read from this repository's own file timestamps, not from a session header, and read
again before writing it.** Chat 9 got this wrong: see section 7.

**This document points. It does not copy.** Everything decided is in section 16 of
`2026-07-25_CONSOLE_DESIGN.md`. Everything open is in
`2026-08-20_LIST_outstanding_items_and_decisions.md`. Everything about the chart of accounts is
in `IntelliCharts\2026-08-05_NOTE_master_chart_of_accounts.md`. **None of the three is restated
here and this file must never grow into a copy of any of them.** Four carriers have already died
of exactly that: the two lists at the end of `IntelliBooks\App\Docs\IntelliBooks-Change-Log.md`,
deleted 2026-08-20, section 7 of `2026-08-20_HANDOVER_consultant_chat_8.md`, superseded the same
day, and the loose IntelliCharts material now folded into that folder's own note.

---

## 1. Who you are, and who you can talk to

You are the **consultant session**. You own verification, `2026-07-25_CONSOLE_DESIGN.md`,
`2026-08-18_BOUNDARY_two_products.md`, `IntelliCharts\2026-08-05_NOTE_master_chart_of_accounts.md`
and the briefs the build sessions work from. **You write no production code.**

Three sessions work this project and **none can see the others**. A Claude Code session owns the
Python pipeline. A second Cowork session owns `IntelliBooks-Desktop-v3.html`. The Uber statement
parser is worked in its own repository with its own project and is not yours.

**Paul is the only channel between all of them.** Anything you want another session to do, you
write as a brief for Paul to carry. He runs the commits: you draft the prompt, Claude Code
executes it. If you are not certain which role you are in, ask before doing anything.

## 2. Mount these before you read anything

Eight folders were connected to chat 9. **A new session inherits none of them**, so they have to
be granted again:

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
different folders and both are live.** Name the full path on first mention, every time. The Uber
repository is out of scope.

**You may or may not have a shell on Paul's machine, and this is not constant between sessions.**
Chat 9 had one and used it throughout. **A mount listing is not a folder listing:** chat 9 once
presented the sandbox mount root, which contains `outputs`, `uploads` and `receipt_capture`, as
the contents of a OneDrive folder. Print the path you actually listed.

## 3. Read in this order

1. **`CLAUDE.md`** in the repository root, 53,529 bytes. Its "How this project is worked" section
   is the induction, and it holds the git conventions and the four traps. **Two bullets were
   added on 2026-08-22**, on answering a why question out of the Why column and on reading the
   date from a file. Both were added by breaking them.
2. **`2026-07-25_CONSOLE_DESIGN.md`**, now **v1.22, 563,159 bytes, 156 amendments, verified
   contiguous 1 to 156 with no duplicates on 2026-08-22.** The check was bounded to the amendment
   record's own line boundaries, lines 27 to 315, which is amendment 97's corrected method; an
   unbounded regex over this file matches other numbered tables and passes for the wrong reason.
   **Read section 18, Receipt and transaction integrity, before the body**: it supersedes parts
   of sections 12, 13A, 14, 16 and 17.5. Then read **section 16**, starting with the table at its
   head.
3. **`2026-08-20_LIST_outstanding_items_and_decisions.md`**, 79,320 bytes. **Read the count line
   at the top for the figures** rather than trusting a number written here, because Paul is
   reducing the list. **Sections 1 to 4 are empty**, which is the work of 2026-08-21 and
   2026-08-22, so the first section with anything in it is 5, Decisions not taken, and every one
   of those needs Paul.
4. **`2026-08-18_BOUNDARY_two_products.md`**, 15,839 bytes, the product boundary and the breaches
   of it found so far. **Read it against Paul's reframing of 2026-08-22:** IntelliBooks Desktop
   is an optional addon to Intellibills, not a second product, and the only separation that
   matters is being able to market Intellibills without it.
5. **`IntelliCharts\2026-08-05_NOTE_master_chart_of_accounts.md`**, 44,899 bytes. **This is no
   longer a parked note. It is IntelliCharts' design document**, by amendment 154, with its own
   amendment record of 18 entries and its own list at section 8. Read the amendment record first,
   then the unnumbered section "What IntelliCharts is intended to become", then section 4, then
   the body, then the addendum. Several decisions changed after the body was written.
6. **`2026-08-20_LIST_settings_firm_and_client.md`**, 33,580 bytes, rewritten 2026-08-22 into
   nine sections with a new system settings section `S1` to `S11`.
7. **This project's own document list in Claude**, which is part of the reading and not a filing
   cabinet. `2026-08-15_RUNLOG_coa_august_check.md` exists there and nowhere on disk.

## 4. The three lists, and a standing instruction

**There are three lists and no others, and all three are to be kept up to date at all times.**
Not at the end of a session, and not when a document is next rewritten.

- **Section 16** of `2026-07-25_CONSOLE_DESIGN.md` is the chronological build order: everything
  decided. A decision taken in chat becomes an amendment **and** a step in section 16 before the
  chat moves on. Amendment 110 exists only because amendment 105 recorded a decision and no step
  was ever added.
- **`2026-08-20_LIST_outstanding_items_and_decisions.md`** is everything not decided, not
  scheduled, or waiting on somebody. If an item becomes a decision it leaves that file and
  becomes a step in section 16.
- **Section 8 of the IntelliCharts note** is IntelliCharts' own list, given numbering and closure
  discipline by amendment 12 of that document. **Nothing about IntelliCharts goes on the receipt
  project's list**, which carries one pointer at item 50. The line that decides what belongs
  where: IntelliCharts owns the chart, and how a receipt is assigned to an account is the
  consumer's problem.

Three conventions that apply to all of them:

- **Every step and every sub-step in section 16 carries one of four words at its head: BUILT,
  OUTSTANDING, CANCELLED, MOVED.** Amendment 121. The table at the head of the section carries
  the same status and **is corrected in the same edit as the step below it**. **Nothing is
  inferred from strikethrough**, which in that section means built, superseded, suspended or
  cancelled depending on where it sits.
- **A closed item keeps its number, moves to the Closed section of its own file, and the count
  line is corrected in the same edit.** Numbers are never reused, so the highest number is the
  count ever raised, and **open plus closed must equal it**. That is the check.
- **When you close an item, ask the two questions at the top of the outstanding items list.**
  Does anything live still point at it as open, and is the answer somewhere the question will
  next be asked. The Closed section is not that place.

**Paul's instruction of 2026-08-21, and hold to it:** the outstanding items list is a simple
document he works off. **Do not add apparatus to it.**

## 5. Where the work is

**Read the table at the head of section 16 rather than this paragraph**, because the table is
kept current and this is not.

**Step 10d is next**, one client registry plus `capture_token` across all three codebases in the
same window, now written as **50 numbered sub-steps** with a status each. Step 10e has 15 and
step 10f has 30. **Step 10a is outstanding and is easy to misread as built**: its deliverable is
config constants for the pipeline's folder names in place of the string literals at
`worker/filing.py:78` and `:103`, and it has never been done.

**The three briefs for step 10d are not written, and they are not your next task.**

**Step 10h moves 58 spent markdown files out of the repository root into `archive\`, with
`git mv`.** As at 2026-08-22 the root still holds 74 and there is no `archive\` directory, so
this is scheduled and not done. **The rule behind it is in `CLAUDE.md`** under "Spent files leave
the root", and it matters because a spent brief reads as an instruction:
`PROMPT_claude_code_step10a_and_10b.md` must never be sent.

**Do not go looking for the chart of accounts inside `receipts.db`.** There is no `coa_accounts`
table and there will not be one; step 12 stays CANCELLED with its number reserved. The master is
`IntelliCharts\COA_MASTER_v1.csv`, 122 accounts on four-digit codes. Any three-digit code found
anywhere is legacy.

## 6. How to work here

`CLAUDE.md` holds the method in full. The ones that bite hardest:

**Verify against the thing itself, never against a summary of it.** About half the defects on
this project were found by checking a claim made in good faith that was wrong.

**Flag, do not fix.** Something wrong that the task did not ask about gets reported, not
repaired. **And do not dress a flag up as a risk assessment.** Paul's instruction of 2026-08-21:
whether an unused field is a risk is his call, and it is not to be raised as though it were a
fault.

**Never state a count about a set you have not enumerated.** A filter is not a reader. The tell
is the word "the" in front of a plural: "the email paths", "the four call sites". Every one of
those on this project has been wrong at least once.

**Name the file, the function or the window in full, every time.** Not "the prompt", "the report"
or "the box". Chat 9 wrote "the report was never built" about a report that does not exist and
cost a round trip finding out which one it meant.

**Answer a why question out of the Why column.** The amendment record has four columns and the
reasoning is in the last one.

**Say what a confidence level rests on.** "High, because I read it back" and "high, because it
seemed right" are different claims.

**Do not answer a narrow question with a system.** Chat 8 was told "Follow my instructions.
Follow my lead" after producing a taxonomy in answer to a question about ticking items off a
list. Chat 9 did the same thing twice and was told "something simple is becoming overcomplicated
too quickly".

## 7. What chat 9 got wrong

**Answered a why question from the What column, three times running.** Asked why `sa103f_box` is
carried in `IntelliBooks-Desktop-v3.html` when `mtd_itsa_category` is not, chat 9 answered from
what the code does, then invented a scope rationale, then a submission rationale that
distinguished nothing, before finding the answer in amendment 100's Why column. **It had been
quoting the What column of that same amendment in support.** Paul's words: "You are either
getting lazy your answers or flippant or both", and "you have guessed your way through". Full
record at amendment 156.

**Dated 34 amendments from a session header.** Amendments 122 to 155 are all dated 2026-08-21 and
the session ran past midnight, so some belong to 2026-08-22. Found only by reading file
timestamps for another purpose. **Amendment 109 already required the date to come from a file.**
Which rows are wrong is not reconstructable and none was changed. Noted in the version header.

**Flagged a discrepancy that was not one.** Chat 9 doubted change log item 8's "both
discrete-quarter and cumulative year-to-date totals" because `exportHMRC()` writes one period.
MTD IT quarterly updates are cumulative year to date, so the phrase describes the quarter picker.
**Paul settled it in one sentence.** The lesson is to ask what a document means before reporting
it as inconsistent with code.

**Cited line numbers that were wrong.** `exportHMRC()` was cited at 1646 and 1665 and is at 2310.
**And found stale ones it did not write:** amendment 100 cites `hmrcPeriods()` at 2058 and it is
at 2276. `IntelliBooks-Desktop-v3.html` moves, so quote a line number with the date you read it.

**Asserted a set size four times without enumerating it.** Amendment 122 said a superseded claim
appeared in two places; it was four, then six after Claude Code found two more, then ten. Every
correction was made by grepping, and every wrong figure was stated before grepping.

**Predicted git diff hunk counts and was wrong on three of five files.** Claude Code diagnosed
it: `difflib.unified_diff` uses `SequenceMatcher` with autojunk on, and only `autojunk=False`
matches git. **Its recommendation, adopted: do not predict hunk counts at all**, since the same
tree gives 16 or 30 depending on the context setting.

**Presented a sandbox mount listing as a OneDrive folder's contents.** It included `outputs` and
`uploads`, which are not in OneDrive.

**Inserted six things above rather than below their predecessor**, in the amendment record, the
sub-step lists and two Closed sections. Anchor on the row that should follow yours, then sort and
print the result.

## 8. Uncommitted work, and the commit brief you need to draft

**HEAD is `a02fbff`, "docs: post-commit evidence for 8d5c345", on branch `feat/console-phase0`,
committed 2026-08-21 at 23:21.** Amendments 110 to 140 are in. **Amendments 141 to 156 are not,
and neither is anything else below.**

Files in the repository with an mtime after that commit, listed by mtime and not by git status:

```
2026-08-22 08:43  2026-08-18_BOUNDARY_two_products.md
2026-08-22 13:44  2026-08-20_LIST_settings_firm_and_client.md
2026-08-22 19:05  2026-07-25_CONSOLE_DESIGN.md
2026-08-22 19:06  2026-08-20_LIST_outstanding_items_and_decisions.md
2026-08-22 19:07  CLAUDE.md
```

plus this handover, which is new and untracked.

**`IntelliCharts\2026-08-05_NOTE_master_chart_of_accounts.md` changed at 19:07 on 2026-08-22 and
that folder has no `.git` at all.** It is not in any repository and nothing versions it. Whether
it should be is not decided and is not on any list.

**An mtime is not a diff.** That list is the candidate set, not a statement that all five differ
in content. **Do not confirm it with `git status` from the Linux sandbox**: line-ending
normalisation shows around thirty phantom modifications there, and `git status` takes the index
lock even though it looks like a read. Chat 9 left `.git\index.lock` behind twice in one day
doing exactly that. Use `git --no-optional-locks` if you must, run anything that writes on
Windows, and note that `git log`, `git show` and `git ls-files` never touch the index and are
safe unconditionally.

**Draft the third commit brief as a `PROMPT_claude_code_2026-08-__commit_141_to_156.md` in the
repository root**, on the same pattern as the two chat 9 wrote, both of which Claude Code
executed without a query. Those two are
`PROMPT_claude_code_2026-08-21_commit_110_to_126.md` and
`PROMPT_claude_code_2026-08-21_commit_127_to_140.md`, and both are now spent, so they move to
`archive\` at step 10h rather than being read as live instructions.

## 9. First action

**Do not open with the outstanding items list.** Chat 9 ended mid-conversation on the chart of
accounts and Paul's instruction is that chat 10 picks that up.

1. **Mount the eight folders and read in the order at section 3.**
2. **Confirm one thing back to Paul before anything else**, because it is the conclusion he had
   to drag out of chat 9 and he wants it confirmed rather than restated: `sa103f_box` is carried
   in `IntelliBooks-Desktop-v3.html` because `exportHMRC()` computes the HMRC summary from it;
   `mtd_itsa_category` is absent **not because MTD is out of scope but because the export that
   would read it was never built**, which amendment 100 states and item 145 now tracks; and
   `frs102_1a_line` and `frs105_line` are absent because IntelliBooks does not produce statutory
   accounts, which reach their formats through `coa_map_sage_final_accounts.csv`. **The source is
   section 4 of the IntelliCharts note and amendment 156. Read them rather than this paragraph.**
3. **Then take up industry charts**, which is where the conversation was going twice over.
   Amendment 15 of the IntelliCharts note settles that the first version of an industry chart is
   written by interrogating the master, and item 9 of its section 8 is that the mechanism is not
   decided. Item 7 is the five PHV accounts becoming a `PHV_DRIVER` industry chart. Item 5 is
   whether the master replaces `chart_of_accounts_DRAFT2_2026-08-03.csv` or sits above it.
4. **Item 145 needs a ruling** and it is small: does the MTD quarterly export go into
   `PROMPT_intellibooks_desktop_changes.md` now, or is it deferred with a date.
5. **Then stand by.** The standing work is reducing the outstanding items list, at his direction
   and at his pace. Do not start anything, do not write to a file, and do not make a change
   without his express permission.
