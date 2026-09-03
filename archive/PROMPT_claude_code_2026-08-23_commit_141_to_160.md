# AUTOMATIC task: commit amendments 141 to 160, step 10g decomposed, and twenty items closed

**Written 2026-08-23 by the consultant session, for Claude Code. Paste this whole file in.**

Runs under AUTOMATIC Task Mode in `CLAUDE.md`. Its "stop and ask" list is unchanged and outranks this file.

Documentation only. No code, no tests, nothing for you to edit. Write your report, then one commit, a push, a verification.

**Position.** HEAD is `a02fbff`, "docs: post-commit evidence for 8d5c345", on `feat/console-phase0`, committed 2026-08-21 23:21:14 +0100. **Amendments 1 to 140 are in.** This commit carries **141 to 160**, twenty amendments, from two consultant sessions.

---

## Why

**Amendments 141 to 156 are the previous consultant session's**, 2026-08-21 into 2026-08-22: the phone app's settings model, the practice root separated from the client top folder, four leftovers of the chart adoption scheduled at last, the three findings step 6b never took, and the establishment of which of the master's four tax mapping columns anything actually reads.

**Amendments 157 to 160 are this session's**, 2026-08-23: four stale figures corrected, the client chart creation model reversed on Paul's ruling, step 10g decomposed, and a date correction that is a disclosure rather than an improvement. See amendment 160 and read it before the others.

**On the lists.** Twenty items closed, so the outstanding items list goes from 114 open, 30 closed, 144 raised to **95 open, 50 closed, 145 raised**. Item 145 is raised, the MTD ITSA quarterly export. **Sections 1 to 4 of that list are now all empty.** A new section 11, Currently unused fields, holds one row and forces no decision.

**And step 10g is decomposed into 10 sub-steps**, of which two are new. It was the last step in section 16 whose parts could not carry a status.

---

## What I verified, and what I did not

I have a shell on Paul's machine. **I ran no git command that touches the index.** Everything below came from `git log`, `git show`, `git cat-file`, `git rev-parse` and `git hash-object`, all object-database reads, each with `--no-optional-locks`.

**"Modified" below is established, not inferred.** For each of the five tracked files I compared `git rev-parse HEAD:<file>` against `git hash-object <file>`. All five differ. **And no CRLF exists in any of them**, counted rather than assumed: zero occurrences in all five, so the byte figures are directly comparable.

**I have not predicted hunk counts and you should not expect any.** That is your own finding from 2026-08-21, that `difflib.unified_diff` uses `SequenceMatcher` with autojunk on and gives 16 or 30 for the same tree depending on the context setting, and the recommendation adopted was to stop predicting them.

**I did not check the 173 other tracked entries**, being everything under `worker\`, `tests\`, `docs\` and `.claude\` and the root `.py` files, which are stored LF and held CRLF. **Task 1 is the gate over the part I could not see, and any modified `.py` file means you stop.**

---

## Task 1. Confirm the starting state

```
git --no-optional-locks status --short
```

**Expect exactly five modified and three untracked.** Your own report is a fourth untracked file and does not exist yet.

```
 M 2026-07-25_CONSOLE_DESIGN.md
 M 2026-08-18_BOUNDARY_two_products.md
 M 2026-08-20_LIST_outstanding_items_and_decisions.md
 M 2026-08-20_LIST_settings_firm_and_client.md
 M CLAUDE.md
?? 2026-08-22_HANDOVER_consultant_chat_10.md
?? PROMPT_claude_code_2026-08-22_coa_conflict_copy_guard.md
?? PROMPT_claude_code_2026-08-23_commit_141_to_160.md
```

**The third untracked file is this brief.** The root holds **77 markdown files, of which 74 are tracked**, counted rather than assumed.

**Stop and report anything else, in particular any `.py` file.**

Use `--no-optional-locks` on every read. If `.git\index.lock` exists, check `tasklist /FI "IMAGENAME eq git.exe"` reports no tasks, then `del .git\index.lock`.

**The five, by byte count, for `--numstat` and `--stat` to agree with:**

| File | HEAD bytes | Disk bytes |
|---|---|---|
| `2026-07-25_CONSOLE_DESIGN.md` | 503,998 | 576,536 |
| `2026-08-18_BOUNDARY_two_products.md` | 15,673 | 15,839 |
| `2026-08-20_LIST_outstanding_items_and_decisions.md` | 69,079 | 80,007 |
| `2026-08-20_LIST_settings_firm_and_client.md` | 31,974 | 33,580 |
| `CLAUDE.md` | 50,784 | 53,529 |

**The two smallest are the two easiest to misread, so here is what is in them.** `2026-08-18_BOUNDARY_two_products.md` has **one changed line**, section 9's, where two em dashes became commas. `CLAUDE.md` has **two insertions**: two bullets in the standard of evidence, on answering a why question out of the Why column and on stating the date from a file, and a new section, "Spent files leave the root".

---

## Task 2. Prove nothing has been lost, before staging

Seven checks, all programmatic, all quoted whole in your report.

**a. Amendment rows.** Compare the numbered rows of the amendment record in HEAD against the working tree. Expect **only in the working tree `[141 ... 160]`, all twenty, and only in HEAD empty.** A non-empty second list means an amendment has been deleted and you stop.

**b. Contiguity, by amendment 97's corrected method.** Bound the scope to the amendment record's own line boundaries, print those boundaries with the result, assert the list equals `range(first, last+1)`, and test duplicates explicitly. **Never a set difference.** I get **160 rows, no duplicates, equals `range(1,161)`, bounded to lines 30 to 332 on disk** and lines 26 to 293 in HEAD.

**c. Section 16 agrees with itself, and all four decompositions are complete.** Extract the head table and the body statuses and diff them: expect **38 steps, identical, 18 BUILT, 18 OUTSTANDING, 1 CANCELLED, 1 MOVED.** Then the sub-steps: **10d has 50, 10e has 15, 10f has 30, and 10g has 10**, each contiguous from 1 with no gaps and each line carrying one of the four status words. **10g is new in this commit and had none before it**, so a check written from HEAD will not look for it.

**d. Every table row has the pipe count its own header row has.** Header-relative, counting only pipes **not** preceded by a backslash. Expect **0 inconsistent rows** across **50 blocks** in the design document, **26** in the outstanding items list, **10** in the settings list, **8** in `CLAUDE.md` and **1** in the boundary document.

**e. The outstanding items list adds up.** The count line at line 3 must read `95 open, 50 closed, 145 raised`. Open plus closed equals the highest number, no number twice, no number in both the open sections and the Closed section, **and the Closed section in ascending order**. I get 95 and 50 against a highest of 145, no overlap, and the Closed section ascending, 50 ids ending `141, 142, 143, 144`.

**f. The settings list's own sequences.** `F1` to `F18` with **F18 struck**, `C1` to `C20` with **C11 struck**, `S1` to `S11`, no gaps in any of the three, and nine sections `## 1` to `## 9`. The counts table at line 43 now reads 13 firm and 16 client existing, against a total of 17 and 19.

**g. Nothing from outside the repository is in the commit.** `git show --stat` on your own commit must name **nine files and no path containing `IntelliCharts`**. See the section below on why that matters here more than usual.

---

## Task 3. Write the report, then one commit

**Write the report before staging**, so it lands in the same commit.

```
git add 2026-07-25_CONSOLE_DESIGN.md 2026-08-18_BOUNDARY_two_products.md 2026-08-20_LIST_outstanding_items_and_decisions.md 2026-08-20_LIST_settings_firm_and_client.md CLAUDE.md 2026-08-22_HANDOVER_consultant_chat_10.md PROMPT_claude_code_2026-08-22_coa_conflict_copy_guard.md PROMPT_claude_code_2026-08-23_commit_141_to_160.md 2026-08-23_REPORT_claude_code_commit_141_to_160.md
```

**Nine files. Check every one is named or described in the message below before you commit.**

Message:

```
docs: amendments 141 to 160, step 10g decomposed, and twenty items closed

Two consultant sessions. 141 to 156 are the previous one's, 157 to 160
this one's. Read amendment 160 first: it is a date correction and a
disclosure, and it changes the dates on several of the rows above it.

  141: three defects Paul decided on 2026-08-21, two scheduled as
  sub-steps 10d.36 and 10d.37. send_unknown_sender_alert() takes the
  firm's name, and EXPORTS_DIR is deleted while its folder stays. Items
  16 and 25 closed.

  142: vatScheme is deleted rather than carried onto the new Client
  Settings tab, at step 10e. Five places in the HTML and the field in
  IntelliBooks-Practice.json. All six clients held an empty string. The
  reason is accounting: the box looked like the system knew the scheme.
  Item 23 closed.

  143: bankFilter() searches the category name as well as the code, at
  step 10g. Since the chart adoption t.category holds the four-digit
  code, so 7300 finds the row and Fuel and oil does not, while the name
  is what the screen shows. Item 19 closed.

  144: two more of the chart-adoption family get a step. loadSampleData()
  writes category names into a field holding codes, at 10d.38, and
  renderReports() and the VAT report stop being keyed on the name, at
  step 10g. Items 21 and 55 closed.

  145: delCategory()'s in-use guard compares the code instead of the
  name, at step 10g. All three of its counts are always zero today, so a
  category with transactions posted to it deletes with no warning. Item
  15 closed, and with it the last of the four chart-adoption leftovers.

  146: categorisations_firm_vendors gains a nullable firm_id, written and
  never read, at 10d.39. The unique key does not change, so the pool
  stays shared and behaviour does not move. The column exists so the
  provenance of a learned mapping is captured while it still can be.
  Items 17 and 47 closed.

  147: receipts.source has four values and no others, email, phone,
  desktop, other, at 10d.40 and 10d.11. Each writer declares it, the
  reader reads it, the sidecar stops using its own vocabulary, and a file
  with no sidecar gets other and goes to Review. Item 18 closed.

  148: an unused field is not a defect and is not to be flagged as one.
  Paul's instruction. The outstanding items list gains section 11 and it
  forces no decision. Items 24 and 102 closed, 102 merged into 24.

  149: a two-digit year that resolves into the future is rejected rather
  than pivoted, and the three-digit branch is deleted, at 10d.41. No
  century pivot, because a cutoff tight enough to turn 99 into 1999 turns
  28 into 1928. Item 140 closed, and findings 3 and 4 of the 10.2 note
  are scheduled at last.

  150: identifying the gross figure. Assume the figure is the gross,
  verify the implied rate against a recognised rate within a rounding
  allowance, and route to Review if it does not verify, at 10d.42.
  Nothing in it is a VAT question and the naming stops saying it is.
  Item 141 closed, and finding 5 of the 10.2 note with it.

  151: the practice root and the client top folder are separated and only
  one of them is a setting. Step 10e becomes 15 sub-steps. The practice
  root is the pipeline's configuration and appears on no page;
  pipeline-status.json gains it; F17 is two stored fields checked against
  each other. Item 27 closed.

  152: the phone app's settings model. Sub-steps 10d.43 to 10d.50. Who
  owns each setting, how it reaches the phone, and what the client is
  told. Confirm mode is the client's alone and off by default; the PHV
  platforms and the week ending day are the firm's and shown read-only.
  "Capture" stops meaning the phone app. Items 28 and 29 closed.

  153: spent files leave the repository root, and it becomes a standing
  rule rather than a one-off. Step 10h, and a new section in CLAUDE.md
  because the rule applies to every session. Item 32 closed.

  154: IntelliCharts has its own design document and this document keeps
  only the consumer side. The chart leaves both products, so it is a
  third thing rather than a module of the console. Item 30 closed.

  155: IntelliCharts' section 8 becomes its only list, with numbering and
  closure discipline. Item 50 of this list is the single pointer to it
  and nothing about the chart is duplicated here. Item 33 stays, because
  the chart cannot decide which account a receipt goes to.

  156: which of the master's four tax mapping columns each consumer reads
  and why. sa103f_box is read in five places in IntelliBooks-Desktop-v3
  and the other three are read by nothing, for two different reasons.
  mtd_itsa_category has no reader because the export was never built,
  which is raised as item 145. No selection event ever happened. Three
  wrong answers were given before the right one, which was in amendment
  100's own Why column.

  157: four stale figures corrected, each found by enumerating the set
  rather than reading the sentence. Step 10d said 35 sub-steps and it is
  50. Step 10h said 58 of 74 markdown files and it is 59 of 75. Item 50
  said seven items open in IntelliCharts' list and there are eleven. And
  item 50's claim that all three unread mapping columns are parked by
  decision is narrowed to two. Three dated statements were deliberately
  left alone.

  158: a client's chart is imported rather than copied from a parent, and
  13.1's one-rule model is superseded. Paul's ruling. Three routes:
  onboarding designs the chart and it is imported, a library chart is
  imported, or it is built from the master by selection. The library is
  flat with four chart types, so "one per business_type" cannot stand.
  chartFor() handing a new client 120 accounts, all active, is recorded
  as the temporary state rather than the design. The chart design itself
  is not recorded here.

  159: step 10g is decomposed into 10 numbered sub-steps, each carrying a
  status word, and two are new. 10g.9 is an in-use guard on the
  per-account status dropdown, for not_adopted only, because archived
  must be permitted precisely when references exist. 10g.10 makes the
  SA103F box dropdown read-only, because a mapping column belongs to the
  master. 10g was the last step whose parts could not carry a status.

  160: a date correction and a disclosure. Amendments 158 and 159 and
  everything they changed were written on 2026-08-23 and were first dated
  2026-08-22, by a session that read the clock once at 2026-08-22 18:16
  UTC and then ran eighteen hours. 32 dates corrected across three files.
  Amendment 157 and the v1.23 header may belong to either day and are
  left as written. Same failure as amendments 122 to 155, and the second
  after a rule was written to prevent it.

Also in this commit:

  2026-08-20_LIST_outstanding_items_and_decisions.md: 114 open, 30
  closed, 144 raised becomes 95 open, 50 closed, 145 raised. Twenty items
  closed, item 145 raised, sections 1 to 4 now all empty, and a new
  section 11, Currently unused fields, holding one row.

  2026-08-20_LIST_settings_firm_and_client.md: C11 struck and its
  numbers not reused, the counts table corrected to 16 client settings
  and 29 in total, ownership settled on rows C4 to C7, and finding eight
  of section 7 reduced from two inert fields to one.

  2026-08-18_BOUNDARY_two_products.md, one line: section 9's em dashes
  removed, and vatScheme struck from the list of book-only attributes.

  CLAUDE.md: two bullets in the standard of evidence, on answering a why
  question out of the Why column and on stating the date from a file
  rather than a session header, and a new section, "Spent files leave the
  root". Both bullets were added by breaking them.

  2026-08-22_HANDOVER_consultant_chat_10.md, the previous session's
  handover, and PROMPT_claude_code_2026-08-22_coa_conflict_copy_guard.md,
  a brief for a change to a file outside this repository, committed here
  because the brief belongs to this repository even though its target
  does not.

  PROMPT_claude_code_2026-08-23_commit_141_to_160.md, this brief, and
  2026-08-23_REPORT_claude_code_commit_141_to_160.md, your report.
```

Then push. Branch `feat/console-phase0`. `git push --dry-run` first, fast-forward only, never `--force`.

---

## Verify, and quote the output

1. `git --no-optional-locks status --porcelain` returns nothing. Quote it.
2. One commit on the branch, parent `a02fbff`, pushed fast-forward.
3. Amendment numbering contiguous 1 to 160 by task 2b's method, with the boundaries printed.
4. **No `.py` file in the commit, and no path containing `IntelliCharts`.** `git show --stat` on your own commit.
5. Section 16's table and body still agree, and 10d, 10e, 10f and 10g still have 50, 15, 30 and 10 sub-steps with no gaps.
6. Read the commit message back against `git show --stat`. **Nine files and a long message, so check every committed filename is either named or described.**

---

## Stop and ask about

- Anything on the Destructive Git Operations list.
- **Any edit to any file.** This task stages and commits what is already there.
- Any modified `.py` file.
- Anything outside `C:\LastingImpact\receipt_capture`.
- Any write to `receipts.db`.
- Starting the pipeline.
- A push that is not a fast-forward.
- The working tree not matching task 1.

---

## Not in this commit, and this one is unusual

**`IntelliCharts\2026-08-05_NOTE_master_chart_of_accounts.md` took ten amendments in the same two sessions, 19 to 28, and none of them is in this commit.** That folder is **not a repository and is not inside one**, checked with `git rev-parse --show-toplevel`, which found nothing up to the mount point. So there is nothing to commit and nothing you can do about it.

**Do not `git init` it, do not add it, and do not copy any part of it into this repository.** Whether it should be versioned is an open question Paul has not settled. Several amendments in this commit refer to that file by path; **that is a reference, not an instruction to go and look.**

The same goes for everything else under `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\`.

**And `PROMPT_claude_code_2026-08-22_coa_conflict_copy_guard.md` is in this commit but is not this task.** It is a brief for a separate job on a file in that OneDrive folder. Committing it is not executing it. **Do not act on it, do not read `build_coa.py`, and do not touch anything in `IntelliCharts\`.** If Paul wants that job done he will paste that brief in on its own.

**Nothing in amendments 141 to 160 is built.** They are decisions and corrections to documents. Step 10g is now 10 outstanding sub-steps and committing the document that describes them is not starting them.

**Do not send or act on `PROMPT_claude_code_step10a_and_10b.md`**, written against a folder scheme abandoned in July, or touch `PROMPT_intellibooks_desktop_changes.md`, which is another session's standing brief.

---

## Report to a file

`C:\LastingImpact\receipt_capture\2026-08-23_REPORT_claude_code_commit_141_to_160.md`, written before staging per task 3.

Include the full output of task 1, all seven outputs from task 2 with the line boundaries and block counts printed, the porcelain result, and what verification step 6 returned.

**And three things I want back.**

**Was the starting-state prediction right?** It came from blob-hash comparison rather than from `git status`, so it establishes that all five differ and says nothing about how. Tell me what `git status` found that I did not, including anything in the 173 tracked entries I could not check.

**Does task 2c find 10g?** It is new in this commit, so a check carried over from your last run will look for 10d, 10e and 10f and pass while missing a whole step. I would like to know whether the check you actually ran was written from this brief or from the last one.

**And the file count in step 10h.** It reads 59 of 75, which was true when amendment 157 corrected it earlier on 2026-08-23. **The root now holds 77 and your report makes 78.** **Tell me what you count after your commit rather than correcting the step**, which is Paul's to decide. Three of those four extra files are spent on delivery, so the 16 that stay does not move and the number that would go to `archive\` does. It is a figure that goes stale every time anyone writes a file, and I would rather know how fast than pretend otherwise.

**One disclosure about this brief.** Its first version predicted two untracked files and left itself off both the status list and the `git add` line, which would have committed eight files against a message describing nine. Caught by counting the root's markdown files after writing it, and corrected before it reached you. The count of 77 and 74 tracked is enumerated, not inferred.
