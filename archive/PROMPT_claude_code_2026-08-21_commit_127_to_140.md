# AUTOMATIC task: commit amendments 127 to 140, and the settings list rewrite

**Written 2026-08-21 by the consultant session, for Claude Code. Paste this whole file in.**

Runs under AUTOMATIC Task Mode in `CLAUDE.md`. Its "stop and ask" list is unchanged and outranks this file.

Documentation only. No code, no tests, nothing for you to edit. Write your report, then one commit, a push, a verification.

**This is the second commit of the day.** The first was `5a201500`, amendments 110 to 126, and your report on it is already committed. Nothing here revisits that.

---

## Why

Fourteen amendments, 127 to 140, and one document rewritten from four sections to nine. **Two of the fourteen exist because of your last report**, which is worth saying plainly: amendment 134 records the three corrections you flagged, and it is the reason the count of places carrying one struck claim went from seven to nine.

The substance is a working session with Paul on duplicate handling and on the settings list. **Nine outstanding items closed, sections 1 and 2 of that list are now empty**, and step 10f went from a prose paragraph to 30 numbered sub-steps after it turned out to describe about a third of what three amendments had decided.

---

## What I verified, and what I did not

I have a shell on Paul's machine. **I ran no git command.** I read `.git/HEAD`, `.git/refs/`, `.git/index` and `.git/logs/HEAD` as files, and inflated loose objects with zlib, checking each object's SHA-1 against its own filename before trusting the bytes.

| Read from | Result |
|---|---|
| `.git/refs/heads/feat/console-phase0` | `5a201500` |
| `.git/refs/remotes/origin/feat/console-phase0` | `5a201500`, so the last commit is pushed and nothing is ahead |
| `.git/index` | version 2, **176 entries**, up from 165 |

**Coverage.** I compared **every tracked root-level `.md` file** against its blob, byte for byte, which is valid because **not one root markdown file contains a CRLF**, counted rather than assumed. **I did not check the other 106 tracked entries**, being the `.py` files and everything under `worker\`, `tests\`, `docs\` and `.claude\`, because those are stored LF and held CRLF and a size comparison would be meaningless. **Task 1 is the gate over the part I could not see.**

---

## Task 1. Confirm the starting state

```
git --no-optional-locks status --short
```

Expect exactly five modified and two untracked. The second untracked is your own report, which does not exist yet.

```
 M 2026-07-25_CONSOLE_DESIGN.md
 M 2026-07-31_PLAN_reset_and_restructure.md
 M 2026-08-20_LIST_outstanding_items_and_decisions.md
 M 2026-08-20_LIST_settings_firm_and_client.md
 M CLAUDE.md
?? PROMPT_claude_code_2026-08-21_commit_127_to_140.md
```

**Stop and report anything else, in particular any `.py` file.**

Use `--no-optional-locks` on every read. If `.git\index.lock` exists, check `tasklist /FI "IMAGENAME eq git.exe"` reports no tasks, then `del .git\index.lock`.

**The five diffs I measured, for `--numstat` to agree with:**

| File | HEAD bytes | Disk bytes | Added | Removed | Hunks |
|---|---|---|---|---|---|
| `2026-07-25_CONSOLE_DESIGN.md` | 458,018 | 503,998 | 97 | 39 | 25 |
| `2026-07-31_PLAN_reset_and_restructure.md` | 73,821 | 74,179 | 1 | 1 | 1 |
| `2026-08-20_LIST_outstanding_items_and_decisions.md` | 63,268 | 69,079 | 31 | 24 | 11 |
| `2026-08-20_LIST_settings_firm_and_client.md` | 23,592 | 31,974 | 143 | 79 | 14 |
| `CLAUDE.md` | 49,036 | 50,784 | 10 | 0 | 1 |

---

## Task 2. Prove nothing has been lost, before staging

Six checks, all programmatic, all quoted in your report.

**a. Amendment rows.** Compare the numbered rows of the amendment record in HEAD against the working tree. Expect **only in the working tree `[127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140]`, only in HEAD empty.** A non-empty second list means an amendment has been deleted and you stop.

**b. Contiguity, by the corrected method.** Bound the scope to the amendment record's own line boundaries, print those boundaries with the result, assert the list equals `range(first, last+1)`, and test duplicates explicitly. **Never a set difference.** I get **140 rows, no duplicates, equals `range(1,141)`.**

**c. Section 16 agrees with itself, and both decompositions are complete.** Extract the head table and the body statuses and diff them: expect **38 steps, identical, 18 BUILT, 18 OUTSTANDING, 1 CANCELLED, 1 MOVED.** Then **step 10d has 35 sub-steps, `10d.1` to `10d.35`, no gaps**, and **step 10f has 30, `10f.1` to `10f.30`, no gaps.** 10f was 29 and gained one the same day, so a check written against 29 is stale.

**d. Every table row has the pipe count its own header row has.** Header-relative, and counting only pipes **not** preceded by a backslash. Expect **0 inconsistent rows** across **47 blocks** in the design document, **25** in the outstanding items list, **10** in the settings list and **8** in `CLAUDE.md`.

**e. The outstanding items list adds up.** Count line at line 3 must read `114 open, 30 closed, 144 raised`. Open plus closed equals the highest number, no number twice, no number in both the open sections and the Closed section, **and the Closed section in ascending order**. I got that wrong twice today by anchoring an insertion on the row that should follow rather than the one that should precede, so it is worth checking rather than assuming.

**f. The settings list's own sequences.** `F1` to `F18` present with **F18 struck**, `C1` to `C20`, and `S1` to `S11` new. No gaps in any of the three. Nine sections, `## 1` to `## 9`.

---

## Task 3. Write the report, then one commit

**Write the report before staging**, so it lands in the same commit.

```
git add 2026-07-25_CONSOLE_DESIGN.md 2026-07-31_PLAN_reset_and_restructure.md 2026-08-20_LIST_outstanding_items_and_decisions.md 2026-08-20_LIST_settings_firm_and_client.md CLAUDE.md PROMPT_claude_code_2026-08-21_commit_127_to_140.md 2026-08-21_REPORT_claude_code_commit_127_to_140.md
```

**Seven files. Check every one is named or described in the message below before you commit.**

Message:

```
docs: amendments 127 to 140, step 10f decomposed, and the settings list rewritten

A working session with Paul on duplicate handling and on the settings
list. Nine outstanding items closed, and sections 1 and 2 of that list,
blocking a scheduled step and waiting on Paul, are now both empty.

Two of these amendments exist because of the implementation session's last
report, and that is the useful part of the day rather than an aside.

  127: matchScore() read for the first time. An app-found match cannot
  disagree on the amount by more than half a penny, tighter than 18.4's
  penny, so 18.5b's stated residual case cannot arise. The real one is the
  supplier: the same function allows a match with no supplier agreement at
  all. Step 10g reworded. Item 5 closed.

  128: an unattributable intake event goes to a reserved firm id,
  receipt_events_UNATTRIBUTED.ndjson, at sub-step 10d.19. config.RECEIPTS_LOG
  is deleted rather than revived, because 8.6's intake panel reads
  receipt_events_*.ndjson and the dead constant's name does not match that
  glob. Items 1 and 72 closed.

  129: the processed_attachments key stays (message_id, attachment_id). A
  message_id is unique by design, so adding firm_id would loosen a
  uniqueness constraint rather than tighten one. Item 6 closed.

  130: Client Settings gets its own tab in the centre menu group beside
  Client Data. Creating a client keeps the entity type in the Edit window;
  the period lock date stays on Client Data. Item 2 closed.

  131: find_by_hash() filters on the file hash and nothing else, so two
  clients of one firm who send the same file collide and the second is
  discarded and credited to the first. Three call sites and app.py:724 has
  no guard. Raised as item 143 and it corrects item 47, which said there
  was only one cross-firm leak.

  132: 8.6's marker file is struck. The pipeline re-reads the registry on
  modification time instead, at sub-step 10d.35. The marker could not be
  built, because it needs a console that is steps 11 to 22 away, and after
  10d the registry has more than one writer. Item 142 closed.

  133: the settings list stays one document and gains a System settings
  section. Item 3 closed.

  134: three corrections to amendment 122, all three found by the
  implementation session and reported rather than repaired. A wrong section
  number, a fifth instance of the struck claim inside 18.2b itself, and a
  fourth in the reset plan. The count of places carrying that claim went
  two, four, seven, nine.

  135: a client with several entities is deleted from 18.2c rather than
  deferred. Seven paragraphs out, one line kept, being amendment 44's rule
  that a client is never derived from a folder path, which sub-step 10d.11
  rests on. Paul had asked whether it was possible and it came back as a
  design with three rules protecting it.

  136: the file-hash duplicate check takes the client, and app.py:724 gains
  the is_recorded_and_filed() guard the other two call sites have. Scoping
  removes the case rather than deprioritising it. The risk was concentrated
  in PDFs, because the same PDF is the same bytes while two photographs of
  one receipt never match. Item 143 closed.

  137: step 10f becomes 29 numbered sub-steps. It named amendments 104, 106
  and 107 and described none of 104's ten parts, none of 106's five and two
  of 107's four, so a brief written from it would have built about a third
  of what was decided. Four decisions inside it: the values check takes the
  client, nothing gets deleted, the duplicate decision is the same on every
  arrival route, and two dead methods go. Item 144 closed.

  138: the settings list rewritten. Four sections, eleven system settings as
  S1 to S11, and three columns on all 37 live rows: whether the store can
  hold more than one value, whether the value is held externally, and
  whether the row is identity or setting. F18 struck, because amendment 135
  had already removed its subject. Item 4 closed.

  139: no test client survives step 10d. The books files were read before
  advising and it reversed the advice: zero receipts in all seven, zero
  transactions in six of seven, and the 18 KB is the chart of accounts that
  chartFor() writes on creation. The entire cost of recreating all seven is
  one transaction and two statement rules. Items 11, 12, 79, 98 and 99
  closed, and amendment 111 point three superseded.

  140: seven items leave the list and sub-step 10f.30 is added, being the
  live checks that were waiting for the Receipts tab to settle. Three
  answers move into CLAUDE.md, because a closed item does not stop the next
  session asking: the logon task is not set until go-live, a leftover
  pipeline.lock is normal, and commit before a run whose pipeline_version
  matters. Items 7, 8, 9, 10, 13, 26 and 104 closed.

Also in this commit:

  2026-08-20_LIST_settings_firm_and_client.md, rewritten: four sections
  becomes nine, S1 to S11 added, three columns added to every row, F18
  struck, and every internal cross-reference renumbered behind the new
  section 4.

  2026-08-20_LIST_outstanding_items_and_decisions.md: 114 open, 30 closed,
  144 raised. It also gains two questions to ask when closing an item,
  because three items had to be answered a second time in CLAUDE.md after
  being closed here.

  2026-07-31_PLAN_reset_and_restructure.md, one line: section 0.5 said the
  interim "contradicts 18.2b, which says Intellibills never writes into
  Clients\ at all", citing a sentence amendment 122 struck. The
  implementation session flagged it.

  CLAUDE.md, ten lines: a new section, "Before starting the pipeline",
  holding the three answers from amendment 140.

  PROMPT_claude_code_2026-08-21_commit_127_to_140.md, this brief, and
  2026-08-21_REPORT_claude_code_commit_127_to_140.md, your report.
```

Then push. Branch `feat/console-phase0`. `git push --dry-run` first, fast-forward only, never `--force`.

---

## Verify, and quote the output

1. `git --no-optional-locks status --porcelain` returns nothing. Quote it.
2. One commit on the branch, parent `5a201500`, pushed fast-forward.
3. Amendment numbering contiguous 1 to 140 by task 2b's method, with the boundaries printed.
4. **No `.py` file in the commit.** `git show --stat` on your own commit.
5. Section 16's table and body still agree, and 10d and 10f still have 35 and 30 sub-steps with no gaps.
6. Read the commit message back against `git show --stat`. **Seven files and a long message, so check every committed filename is either named or described.**

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

## Not in this commit, and do not go looking

**Nothing in amendments 127 to 140 is built.** They are decisions and corrections to documents. **Step 10f is now 30 outstanding sub-steps and step 10d is 35**, and committing the document that describes them is not starting them. Do not implement any of it.

**Do not send or act on `PROMPT_claude_code_step10a_and_10b.md`**, written against a folder scheme abandoned in July, or touch `PROMPT_intellibooks_desktop_changes.md`, which is another session's brief.

**`IntelliCharts\` and everything under `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\` are outside this repository and outside your scope.** Do not read them, add them or reference them by path. The settings list and the reset plan in this commit refer to files there; that is a reference, not an instruction to go and look.

---

## Report to a file

`C:\LastingImpact\receipt_capture\2026-08-21_REPORT_claude_code_commit_127_to_140.md`, written before staging per task 3.

Include the full output of task 1, all six outputs from task 2 with the line boundaries and block counts printed, the porcelain result, and what verification step 6 returned.

**And two things I want back.**

**Was the starting-state prediction right, including the five diff shapes?** It comes from `.git/index` and inflated blobs, not from git, and it covers every root markdown file but none of the 106 other tracked entries. Tell me what `git status` found that I did not.

**And check task 2e's ordering yourself rather than trusting me.** I put a closed item in the wrong position in the Closed section twice today, both times by anchoring the insertion on the row that should come after it. I fixed it by sorting the rows programmatically, and I would like to know whether that held.
