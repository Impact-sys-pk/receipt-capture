# Handover: consultant session 26

**Written 2026-09-13 by the consultant session. It covers everything since
`2026-09-12_HANDOVER_consultant_session_25.md`, which is now spent.**

**You are the consultant session in Cowork.** You own verification, `2026-07-25_CONSOLE_DESIGN.md`,
the `PROMPT_*.md` briefs, and `IntelliBooks-Desktop-v3.html` on Paul's standing instruction of
2026-09-06. You do not write the Python pipeline; Claude Code does. Paul is the only channel between
you.

---

## 1. THE ENVIRONMENT, AND SESSION 25's HANDOVER WAS WRONG ABOUT IT

**You have a shell on Paul's machine. `device_bash` works.** Session 25's handover said this session
has file-bridge tools only and no shell, and that claim cost this session an exchange with Paul
before it was tested. **Test it, do not carry this paragraph either.**

What it is, established by running `uname -a` on 2026-09-12: **a Linux VM on Paul's machine** with
the connected folders mounted under `$HOME/mnt/`. `python3`, `node`, `git` and `md5sum` are on it.

**What it still cannot do, and this half of session 25's handover was right.** It is not a Windows
shell. It cannot run `.\.venv\Scripts\python.exe`, cannot run pytest, cannot start the pipeline, and
cannot drive IntelliBooks Desktop. **So a suite count reported by Claude Code cannot be independently
confirmed. Say so rather than repeating it as fact.** Git is read-only from here in practice: `git
log`, `git show` and `git ls-files` are safe; everything that writes goes to Paul.

**NO FOLDER IS CONNECTED WHEN YOU START.** Request these five with
`device_request_folder_access`, and do it first, because nothing else works until you have:

```
C:\LastingImpact\receipt_capture
C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliCharts
C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliBooks
C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills
C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Clients
```

`C:\Intellibills\`, holding the live database and the logs, is NOT mountable and was never needed
this session.

---

## 2. Read these, in this order, before doing anything

1. **This file, in full.**
2. **`CLAUDE.md`**, the section "How this project is worked" and the seven traps. The traps live
   there and nowhere else.
3. **`2026-07-25_CONSOLE_DESIGN.md`**, **amendments 358 to 369**, which are this session's, then
   **section 16**, then **section 18**.
4. **`2026-08-20_LIST_outstanding_items_and_decisions.md`**, the header block and sections 3 and 7.
5. **`IntelliBooks\App\Docs\IntelliBooks-System-Specification.md` section 8**, the pilot procedure,
   if 10i comes up.
6. **`2026-08-15_RUNLOG_coa_august_check.md`** is NOT on disk. It is reachable only through the
   Projects tool, `project_read` with path `claude/2026-08-15_RUNLOG_coa_august_check.md`. It opened
   first time this session.

---

## 3. What is in flight, and it is your first task

**One brief is written and NOT yet sent.**
`PROMPT_claude_code_2026-09-12_exports_leave_the_repository.md`, md5
`d81b1305681bca65e0ed886a8a917a51`. It is step 10r: a config constant derived from
`INTELLIBILLS_ROOT`, both export scripts repointed, and the repository's `exports\` and empty `logs\`
folders removed. **Paul was told to send it after the dead-code report landed. That report has
landed, so it can go.**

**When it lands, the file move is yours**: `exports\bookkeeping_export.csv` into
`Intellibills\Exports\`, and the two empty folders go. **Do not move it before the code changes**, or
the scripts will recreate the folder.

**Claude Code's flag 2 is approved by Paul and not yet briefed.** About eight lines in
`tests/test_london_surfaces.py` that write a real review pair and assert `file_review()`'s
`reviewed_at` ends `+00:00`. It replaces the test deleted at item 114, which covered dead code.
Send it with the exports brief.

---

## 4. What this session did

**Amendments 358 to 369.** Twelve, and the list went from 87 open to 68.

- **358.** Five step bodies in section 16 said `OUTSTANDING` while their table rows said BUILT, and
  10q had no body at all. All six fixed. **A check that parses the table and the bodies and compares
  them is in this session's history; rebuild it rather than eyeballing, and prove it discriminates
  against the backup.**
- **359, step 10r.** Item 37 closed. Exports leave the repository for `Intellibills\Exports\`.
- **360, step 10s, BUILT.** `attachReceipt()` carries nothing from the receipt to the transaction.
  18.5's opening rule, written 2026-07-30, which **step 10g closed COMPLETE without building**.
- **361.** Item 38 deferred by decision. `2026-08-20_NOTE_demo_version.md` corrected: its section 7
  argued from root fallbacks that `_required_root()` removed on 2026-09-06.
- **362.** Item 50 closed. IntelliCharts' own lists are empty and have been since 2026-09-01.
- **363.** Renamed to **Receipt publishing destination**. The stored `publish_destinations` field is
  NOT renamed.
- **364.** Item 168 to section 7. Section 5 emptied.
- **365.** **All ten of section 9 closed.** Section 9 emptied.
- **366.** Items 150, 172, 174 and 176 from section 3 to section 7: each already carried Paul's
  ruling.
- **367.** Items 114, 115, 116, 118 and 179 closed. Four were Claude Code's, verified here by reading
  the files.
- **368 and 369, step 10t.** Item 145 reframed as a reports job and closed into it.

---

## 5. Paul's decisions this session

| What | Decision |
|---|---|
| The pilot, 10i | **Not being started yet.** Do not schedule it |
| The 10 failed notes in `Intellibills\Resolutions\failed\` | **Leave them.** Test Sole Trader's, stale, from step 10k's two halves landing minutes apart |
| Item 37 | Exports move to `Intellibills\Exports\` |
| Item 35 | Attach carries nothing. Built same hour |
| Item 38 | Deferred until the demo is real work |
| Item 50 | Close it |
| Item 145 | **A reports job, not an MTD job, and near-term** |
| Claude Code's flag 2 | Yes |
| Working style | **"Do not bother me with admin like this. Just fix it."** Filing, stale documents and obvious corrections are done, not raised |
| The goal | **Clear every section of the outstanding list until only section 7, Deferred by decision, remains** |

---

## 6. The state, counted from the files on 2026-09-13

**Section 16**: 32 built, 14 outstanding, 1 cancelled, 1 moved, **48 steps**. The fourteen
outstanding are 10r, 10t, 10i, 11, 13, 14, 15, 16, 17, 18, 19, 20, 21 and 22.

**The outstanding list**: **68 open, 111 closed, 179 raised.**

| Section | Open |
|---|---|
| 1, 2, 4, 5, 6, 9, 11 | **empty** |
| 3. Defects flagged and not fixed | **3**: 151, 153, 162 |
| 7. Deferred by decision | 13 |
| 8. Found by the sweep of 2026-08-20 | **32** |
| 10. Found on 2026-08-21 | **20** |

**Sections 8 and 10 hold 52 of the 68.** They are the bulk and neither has been touched.

---

## 7. Two defects flagged this session and NOT fixed

1. **`renderReports()` counts uncategorised transactions as expenditure.**
   `catType[ln.category]||"expenses"` makes a blank category an expense, so Profit and Loss adds them
   into Total expenses while Category Totals on the same screen excludes them and says so. **On
   `Client_004-books.json`, 24 of 30 transactions carry no category.** Counted across the whole books
   file, not the period on screen, so the on-screen figure may be smaller. Obvious fix: the P&L
   excludes them and says how many.
2. **F15 sits under a card headed "Decided and not built yet" on Firm Settings**, and its own text
   says nothing has been decided about what the CSV holds. One line, and it is the heading that is
   wrong, not the entry.

---

## 8. Traps this session hit, on top of `CLAUDE.md`'s

- **Restating an item's own wording as fact, twice.** Item 50 said IntelliCharts was "under active
  design"; this session repeated it and Paul asked "until WHAT?" There is no such work. Item 145 said
  the HMRC card offers MTD quarters; this session repeated it and **Paul corrected it from the
  screen**. `hmrcPeriods()` builds quarters only inside `if(client.mtd)` and no client has it.
  **Both were greps that found a name, reported as readings of a thing.**
- **`&&` is not a statement separator in Paul's PowerShell.** Give multi-command blocks as separate
  lines.
- **A `git add` line and a `git commit` line in separate blocks leaves a staged-and-uncommitted
  window.** Paul ran the first without the second and Claude Code's next commit swept two of this
  session's documents into `441dcab`. **Give them as one pasteable block.** The history was
  deliberately left alone: by the time a repair was proposed the tip had moved.
- **A parameter name is not a field name.** `business_type` is the engine's parameter; the client
  record's field is `trade`. This session nearly raised a false item on the difference.
- **A line number in a brief was wrong**, 41 against 42, and Claude Code caught it.

---

## 9. Files this session changed, md5 read back from Paul's machine on 2026-09-13

| File | md5 |
|---|---|
| `2026-07-25_CONSOLE_DESIGN.md` | `2f17e3aa3bc357b993cf69fbab2b0b1c` |
| `2026-08-20_LIST_outstanding_items_and_decisions.md` | `bc2c97519f4cfc4ee901070a3c202b28` |
| `2026-08-20_LIST_settings_firm_and_client.md` | `ad15c272b66f0d580f25a9af55af4902` |
| `2026-08-20_NOTE_demo_version.md` | `9892c25f1d55f8f1f4ff4ce94fabb3a9` |
| `IntelliBooks\App\IntelliBooks-Desktop-v3.html` | `9255b9ca9339eda207135ea9d880ea9b` |
| `IntelliBooks\App\Docs\IntelliBooks-Change-Log.md` | `e2369514a05898a14961206a62f17400` |

**Git tip `a4a4974`**, "docs(16): amendments 368 and 369, new step 10t the reports set, item 145
closed into it". **Verify every hash before trusting it. They go stale the moment anyone edits.**

Every edit this session was made with a `.bak-before-<change>` copy proved byte-identical first,
unique anchors asserted to match exactly once, the diff hunks printed, and the result read back.
**Both Desktop edits were driven in Node with negative controls.** Keep that.

---

## 10. Where the next chat starts

**Ask Paul first.** The obvious candidates, and the order is his:

1. **Send the exports brief and flag 2's brief to Claude Code**, then move
   `exports\bookkeeping_export.csv` when the code lands.
2. **Finish section 3**: items 151, 153 and 162. Each needs a decision from him.
3. **Sections 8 and 10, 52 items.** This is the real bulk of the goal and neither has been started.
4. **Step 10t, the reports set**, when he wants the detail. **It is deliberately scoped and not
   designed**, on his instruction of 2026-09-13.

---

## 11. What this handover does not claim

- **No suite was run.** Every pass count in it is Claude Code's claim, relayed.
- **Nothing was run on the live system.** The pipeline was not started and the database was never
  read; per `CLAUDE.md`'s sixth trap a staged copy of `receipts.db` is not evidence anyway.
- **Sections 8 and 10 of the outstanding list were not read**, only counted. The 52 items in them
  are unexamined and, on this session's experience with sections 3, 9 and 10, **a good number will
  describe a state the system has left.** Check each against the code before acting on it.
- **The digital links ground for keeping an MTD export as issued is Paul's stated reason and is not
  verified.** Check it against HMRC before designing on it.
