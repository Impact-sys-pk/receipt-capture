# Handover to the next consultant chat

**Written 2026-08-24 09:52 BST by consultant chat 10 and revised 2026-09-01 by the consultant session that followed it. Where a figure carries a date, that date is when it was checked.**

This document points. It does not copy. Everything decided is in section 16 of `2026-07-25_CONSOLE_DESIGN.md`. Everything open is in `2026-08-20_LIST_outstanding_items_and_decisions.md`. **The chart of accounts workstream is finished, and section 9 says where its record is.** Do not restate any of the three here. Five carriers have already died of exactly that.

---

## Read this, then start work. Do not run an induction.

A previous session lost about an hour to ceremony before doing anything useful. Do not repeat it. Read section 3, then section 10, then ask Paul what he wants first.

**Do not do any of the following.** Re-verify a decision Paul has already made. Re-read a document this handover has already summarised. Write out a plan of what you are about to do. Read anything else until the task in front of you needs it.

---

## 1. Who you are, and what you are picking up

You are the consultant session. You own verification, `2026-07-25_CONSOLE_DESIGN.md`, `2026-08-18_BOUNDARY_two_products.md` and the briefs the build sessions work from. **You also write `IntelliBooks-Desktop-v3.html`.** You write no Python: the pipeline is Claude Code's.

**Your task is the one chat 10 was created for and then spent almost none of its time on: working through `2026-08-20_LIST_outstanding_items_and_decisions.md` and the section 16 schedule, at Paul's direction and at his pace.**

**Two sessions work this project and neither can see the other.** A Claude Code session owns the Python pipeline. This one owns `IntelliBooks-Desktop-v3.html` and the documents. **Paul is the only channel between them.** You draft the briefs he pastes.

**Every brief to Claude Code names the file its report is written to.** Full path, repository root, the existing convention: `{date}_REPORT_claude_code_{what}.md`, as in `2026-08-23_REPORT_claude_code_commit_141_to_160.md`. **A brief with a "what to report" section and no file path is the fault that lost a real finding once already, and it is in section 8.**

**Then check for that file yourself and tell Paul what it says.** You will not be notified, so look for it when the work has had time to run, read it, and respond to him on it. **He pastes the brief and should not have to paste the report back.**

**How `IntelliBooks-Desktop-v3.html` is worked.** One file, about 199 KB, no test suite. Four rules, and they held through ten changes on 2026-08-31 and 2026-09-01:

1. Copy the file to `IntelliBooks-Desktop-v3.html.bak-before-{what}` before any edit, and check the copy matches.
2. Print the whole diff afterwards and read it. Every hunk must belong to the change.
3. Extract the single `<script>` block and pass `node --check` on it.
4. Pull the changed function out of the saved file and run it in node against real data before calling it done. Reading the code is not checking it.

Every change gets an item in `IntelliBooks\App\Docs\IntelliBooks-Change-Log.md` saying what changed, what was checked and how, the backup name, and what was flagged and not fixed.

---

## 2. Mount these before you read anything

A new session inherits none of them.

```
C:\LastingImpact\receipt_capture
C:\Intellibills
C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills
C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliBooks
C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliCharts
C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Clients
C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Scripts
```

`C:\Intellibills` and `...\OneDrive - Intellitax Accounting Limited\Intellibills` are two different folders and both are live. **Name the full path on first mention, every time.**

You may or may not have a shell on Paul's machine and this is not constant between sessions. Chat 10 had one. **A mount listing is not a folder listing:** print the path you actually listed.

---

## 3. Read in this order

**Sections, not whole documents. These six files are 909 KB together and reading them end to end is the hour.**

1. **`CLAUDE.md`**, the "How this project is worked" section only. It is the induction and holds the git conventions and the four traps.
2. **`2026-07-25_CONSOLE_DESIGN.md`**, section 18 and the head table of section 16 only. Not the body and not the 162 amendments. v1.24, amendments contiguous 1 to 162, checked 2026-09-01.
3. **`2026-08-20_LIST_outstanding_items_and_decisions.md`**, the count line and sections 1 to 5. **98 open, 53 closed, 151 raised** as at 2026-09-01. Sections 1, 2 and 4 are empty; section 3 holds three items, 145, 150 and 151. **Sections 8, 9 and 10 are 73 findings from document sweeps: read one when you work it, not now.**
4. **`IntelliBooks\App\Docs\IntelliBooks-Change-Log.md`**, items 40 to 49 only. They are every change made to `IntelliBooks-Desktop-v3.html` on 2026-08-31 and 2026-09-01.
5. **This project's own document list in Claude**, which is part of the reading. `2026-08-15_RUNLOG_coa_august_check.md` exists there and nowhere on disk.

**When the task needs them and not before:** `2026-08-18_BOUNDARY_two_products.md`, the product boundary; `2026-08-20_LIST_settings_firm_and_client.md`, nine sections, F1 to F18 with F18 struck, C1 to C20 with C11 struck, S1 to S11.

---

## 4. The lists, and a standing instruction

**Two, as at 2026-09-01.** Both are kept current at all times, not at the end of a session.

- **Section 16 of `2026-07-25_CONSOLE_DESIGN.md`** is the chronological build order: everything decided. A decision taken in chat becomes an amendment and a step in section 16 before the chat moves on.
- **`2026-08-20_LIST_outstanding_items_and_decisions.md`** is everything not decided, not scheduled, or waiting on somebody.
- **Section 8 of `IntelliCharts\2026-08-05_NOTE_master_chart_of_accounts.md` is closed. 0 open, 20 closed, 20 raised.** Its section 9 build order is **11 built, 0 outstanding, 2 cancelled, 13 steps.** The receipt project's list carries one pointer at item 50 and nothing else.

Every step and sub-step in section 16 carries BUILT, OUTSTANDING, CANCELLED or MOVED at its head, and the table at the head of the section carries the same status and is corrected in the same edit. **Nothing is inferred from strikethrough.**

A closed item keeps its number, moves to the Closed section, and the count line is corrected in the same edit. **Open plus closed must equal the highest number ever used. That is the check.**

**Paul's instruction of 2026-08-21, and hold to it: the outstanding items list is a simple document he works off. Do not add apparatus to it.**

---

## 5. Where the work is

Read the table at the head of section 16 rather than this paragraph. As at **2026-09-01** it is **38 steps: 18 BUILT, 18 OUTSTANDING, 1 CANCELLED, 1 MOVED.**

**Step 10d is next.** One client registry plus `capture_token` across all three codebases in the same window, **50 sub-steps**, each with a status. **Its three briefs are not written**: the pipeline, `IntelliBooks-Desktop-v3.html`, and the capture app, which is a separate Netlify deployment only Paul can release. All three must be written against the same field list and the flip happens in one sitting or receipts stop arriving.

**Step 10e has 15 sub-steps, 6 BUILT and 9 OUTSTANDING. 10f has 30 and 10g has 10, all outstanding.** 10g was decomposed on 2026-08-23 and was the last step whose parts could not carry a status.

**Step 10a is outstanding and is easy to misread as built.** Its deliverable is config constants for the pipeline's folder names in place of the string literals at `worker/filing.py:78` and `:103`. It has never been done.

**Step 10h has not started.** It moves the spent markdown files out of the repository root into `archive\` with `git mv`. **The root holds 80 markdown files as at 2026-09-01 and there is no `archive\` directory.** The step's own figure reads 59 of 75 and is stale again; correcting it is Paul's call. The rule behind it is in `CLAUDE.md` under "Spent files leave the root", and it matters because a spent brief reads as an instruction: **`PROMPT_claude_code_step10a_and_10b.md` must never be sent.**

**Do not go looking for the chart of accounts inside `receipts.db`.** There is no `coa_accounts` table and there will not be one. Step 12 stays CANCELLED with its number reserved.

---

## 6. Git state

**HEAD is `10fd03f`, "docs: amendments 141 to 160, step 10g decomposed, and twenty items closed", committed 2026-08-23 14:04:17 +0100 on `feat/console-phase0`, and pushed.** `refs/remotes/origin/feat/console-phase0` points at it.

**Three tracked files are dirty**, listed by mtime and not by `git status`:

```
2026-09-01 11:19 2026-08-20_LIST_outstanding_items_and_decisions.md
2026-08-25 11:03 CLAUDE.md
2026-09-01 11:51 2026-07-25_CONSOLE_DESIGN.md
```

plus this handover, which is new and untracked.

They carry **amendments 161 and 162**, the correction to line 5 of the outstanding items list, and the two new `CLAUDE.md` bullets, **plus 2026-09-01: the section 16 head line, sub-steps 10e.3, 10e.4, 10e.5, 10e.7, 10e.8 and 10e.13 marked BUILT, items 146, 147 and 148 closed, and items 148 to 151 raised.** Two commit briefs from 2026-08-23 are the pattern to follow: `PROMPT_claude_code_2026-08-23_commit_141_to_160.md` and, before it, the two from 2026-08-21. All are spent and move to `archive\` at step 10h.

**An mtime is not a diff.** To establish whether a file differs without touching the index, compare `git rev-parse HEAD:<file>` against `git hash-object <file>`. Both are object-database reads. **Do not run `git status` from the Linux sandbox**: line-ending normalisation shows around thirty phantom modifications and it takes the index lock even though it looks like a read. `git log`, `git show`, `git cat-file` and `git ls-files` never touch the index and are safe unconditionally.

---

## 7. One thing waiting on Paul

**Item 145, the MTD ITSA quarterly export, needs his ruling and it is small:** does this session build the second export now, or is it deferred with a date? He parked it on 2026-08-22 until the chart of accounts work was finished. **That work finished on 2026-09-01, so item 145 is unblocked and unanswered.**

---

## 8. What earlier sessions got wrong

**Chat 10.** Fourteen errors, of which these are the classes worth carrying forward. Every one was a claim that looked fine on the page.

**Wrote the wrong date for eighteen hours.** The session ran from 2026-08-22 into 2026-08-24, crossing midnight twice, and the reply header was produced by copying the previous reply rather than by reading a clock. **32 dates in three files had to be corrected and two amendments cannot be dated at all.** Amendments 160 and 161 record it. Paul then changed the organisation instruction so the header carries the time and zone, which makes a copied header visibly wrong on the next reply. **Read the clock in the reply you are writing. Never carry a date forward.**

**Searched for a dash and called it a search for variants.** Asked which master accounts are confusable, chat 10 searched for names containing " - ", found four, and reported that as the class. Done properly there are **44 pairs of expense accounts sharing a significant word and 31 Sage headings holding more than one account.** A filter is not a reader.

**Stated counts about sets it had not enumerated, three times.** "The seven `open(...)` calls" when there are six. "Eight firm standards" when there are six policies and two lists. And it left its own commit brief off its own commit brief's file list, so the message described nine files and the `git add` line staged eight.

**Reasoned from a figure it never checked.** Said registration "comes into view" for a client whose turnover was 17 per cent of the VAT threshold. The threshold is £90,000 and had not been looked up.

**Wrote 34 unverified rows into a reference table and asked afterwards.** Section 13 of the design document already says import as proposal, nothing enters until dispositioned.

**Asked for a report and gave it nowhere to go.** A brief with a "what to report" section and no file path means the report reaches Paul's screen and not the session that asked for it. That report contained a real finding the session's own verification had missed.

**Attributed its own argument to Paul.** Amendment 142 credited him with the accounting reason for deleting `vatScheme` when the argument was the session's and he had been argued out of keeping the field. Corrected by amendment 162.

**Relitigated a settled decision twice**, after Paul had chosen from three options it had itself put to him.

**Invented a category to explain a failure** rather than looking at what happened, in a reply about inventing explanations.

**Answered with reference numbers instead of plain statements**, making Paul look up what item 9 or amendment 15 was, repeatedly, after being asked not to.

**Drifted from the objective.** Told three times that the purpose was to design the automation, it kept returning to the client's chart.

**The consultant session, 2026-08-31 and 2026-09-01.** Four, all found by Paul or disclosed at the time.

**Reported an absence after searching two folders.** Said the Client Settings tab was scheduled nowhere. It is sub-step 10e.3, recorded in the Closed section of the same list the session was quoting from, which it had not searched.

**Took a closed item's reasoning at face value.** Said step 13 needed no code because the export already writes a file. `exportHMRC()` writes box totals and not one account.

**Generalised from a table.** Said section 16 had never held IntelliBooks work, having read its 38 rows and the first dozen sub-steps. Step 10e is nothing else.

**Wrote reams where a yes would do**, and used language Paul called a builder justifying an inflated quote. Raised by him twice in one day.

---

## 9. Out of scope, and where it went

**The chart of accounts workstream is finished.** Section 8 of the note is 0 open, 20 closed, 20 raised; its section 9 build order is 11 built, 0 outstanding, 2 cancelled. Its last handover is **`IntelliCharts\2026-08-30_HANDOVER_intellicharts.md`**, with the process design at `IntelliCharts\2026-08-24_INTERIM_client_chart_process.md` and the run log beside them.

`IntelliCharts\` is not in any repository and that is a decision, amendment 30 of the note, not an oversight. **Do not `git init` it and do not add any part of it to this repository.**

The Uber statement parser at `C:\LastingImpact\uber-phase1-ingestion-worker` has its own project and is not yours either.

---

## 10. First action

1. Mount the folders and read in the order at section 3.
2. **Establish two things yourself rather than trusting section 6 of this document:** HEAD, and the count line at the top of the outstanding items list.
3. Ask Paul what he wants first. **The standing work is reducing the outstanding items list, at his direction and at his pace. He settled the order on 2026-09-01: the outstanding items list before section 16, accepting that working it will deal with some section 16 items on the way.** Do not start anything, do not write to a file, and do not make a change without his express permission.
