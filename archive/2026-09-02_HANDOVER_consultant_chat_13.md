# Handover, consultant session, chat 13

Written 2026-09-02, 17:15 BST, by the consultant session that ran 2026-09-02 14:57 to 17:15 BST. For the consultant session that comes next.

**This file is never changed.** Paul's ruling of 2026-09-01: "it should NEVER be changed. That would be attempting to rewrite history." If something in it is wrong, correct it in the file that properly holds the fact and say so; do not edit this.

---

## 0. Do this first, before reading anything

**The machine is `xps13-9350-claude-instance2` and the Windows user is `PDK7`.** Every path below is on it.

**You start with no folder access. Request these five in one call**, with `device_request_folder_access`:

```
C:\LastingImpact\receipt_capture
C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliBooks\App
C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Clients
C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills
C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliCharts
```

**Do not ask for the practice root itself.** This session asked for `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited` and Paul declined it on the device. The five above were then granted without argument. **One prompt appears on his machine per call, so ask once for the whole set.**

**`C:\Intellibills\` is not grantable through this bridge and holds the live database and the process logs.** You cannot read `receipts.db` or `run.log`. Ask Claude Code or Paul.

**This session had no shell on Paul's machine.** No `device_bash`. That is not constant between sessions; check your tool list rather than assuming either way.

**Paul wants to be moving immediately.** Do the folder request in your first turn, and start on section 3 below rather than opening with a state summary he already has.

---

## 1. Read this much and no more before starting

`CLAUDE.md`, the whole of "How this project is worked". It is the induction and it is not optional.

`2026-07-25_CONSOLE_DESIGN.md`: the version header, then amendments **163 to 174**, then section 16's head line and the head table, then step 10d. **Not the whole amendment record.** Rows 1 to 162 are settled history and reading them cost this session forty minutes it later needed. Read an earlier row when something points you at it.

`2026-08-20_LIST_outstanding_items_and_decisions.md`: the count line and sections 1 to 7. Sections 8 to 11 are sweep findings; read a row when it is cited.

This file.

---

## 2. Where the build stands

Branch `feat/console-phase0`. **HEAD `2bfe47d`, pushed.** Working tree clean apart from `2026-09-02_REPORT_claude_code_commit_175.md`, untracked, and this handover once it lands.

**Design document v1.34, amendments 1 to 174, contiguous, verified by Claude Code at `2bfe47d`.**

**Step 10a is BUILT.** Head table **19 BUILT, 17 OUTSTANDING, 1 CANCELLED, 1 MOVED, 38 steps**. That is the first change to those counts since 2026-08-21.

Today's commits, in order: `7ea2dc4` 10a.1, `2ac70ab` 10a.2 pipeline, `d6485c8` amendments 170 to 172, `5748b22` amendment 173, `7e037c3` amendment 174, `2bfe47d` the step 10d briefs' second refresh.

**Sub-step 10a.2 landed in three parts and all three are done:** the pipeline line in `2ac70ab`; the Desktop side as change log items **50 and 51** of `IntelliBooks\App\Docs\IntelliBooks-Change-Log.md`; and `_step10a_move.py --apply`, run by Paul at about 15:33 BST, which moved five folders.

**Four checks passed, two could not be run.** Passed: the five folders moved with every file present; a receipt added through the Receipts tab filed to `Clients\Test Sole Trader\IntelliBooks\Receipts\2022-23\`, a tax year folder that did not exist before; an HMRC summary and its archive landed in `Clients\Test Sole Trader\IntelliBooks\HMRC Summaries\`. **Not run: filing from Review, because `Intellibills\Review\` holds only an empty `TEST3\`; and the legacy books migration, because no client has a books file at the old location.**

**The Review one is the gap that matters.** It is the only thing that writes `filed_path` into a resolution note, which `worker/resolution/service.py:351` reads back and `:940` refuses. It will be exercised by the first real review item.

---

## 3. Next: step 10d, and the briefs are ready

Paul's build order: **10a, then 10d, 10e, 10f, 10h, 18.** 10a is done.

**Three briefs, all current, all in the repository root:**

- `PROMPT_claude_code_2026-09-01_step10d_pipeline.md`
- `PROMPT_intellibooks_2026-09-01_step10d_desktop.md`
- `PROMPT_phoneapp_2026-09-01_step10d.md`

**All 58 sub-steps are covered across the three, checked by enumerating `10d.N` in each and taking the union: none missing, 28 named in more than one.**

**Section A is byte-identical in all three, 3,056 bytes, md5 `0d0dda57d858577da806dea2e3c3e45f`.** **The boundary rule, which none of the three briefs states and should:** from the `## A.` line inclusive to the line before the next `## B.` line, joined with `\n`, no trailing newline, UTF-8. Claude Code's first attempt gave 3,057 bytes and a different hash because the rule was not written down. **Adding the rule to all three is one edit repeated identically inside section A, and it is not done.**

**Line numbers were refreshed twice today**, at 16:30 and 16:55 BST, and the second pass is the one to trust. Seven `config.py` citations in the pipeline brief, all now landing on the construct they name. Forty-one distinct Desktop line references. **They will move again the moment step 10d's first edit lands, which both briefs now say at the top.**

**The Desktop half is the consultant session's own work, not the third session's.** Line 3 of `PROMPT_intellibooks_2026-09-02_step10a_desktop.md` records Paul's instruction that `IntelliBooks-Desktop-v3.html` is yours for step 10a, and the step 10d Desktop brief is written the same way. **The pipeline brief goes to Claude Code and the phone app brief needs a Netlify deploy only Paul can release.** All three flip in one sitting or receipts stop arriving.

---

## 4. What Paul is still waiting to rule on

- **The date on section 16's head line.** It says the six BUILT sub-steps of 10e were built 2026-09-01; all six sub-steps and the commit message of `81aec08` say 2026-08-31. Nothing on disk settles it. Ask which evening he tested the ten IntelliBooks changes.
- **`worker/categorisation/coa.py` and layer 4**, items 92 to 96. Three options put to him 2026-09-01 and no ruling. `enable_ai_fallback` defaults False and layer 4 has never run. **Item 92's comparison was run against `COA_MASTER_v1.csv`, which is now in `IntelliCharts\Cockups\`**, and the item now says to run it again against `Chart Library\Master_COA.csv`.
- **Item 145**, the MTD ITSA quarterly export. Raised 2026-08-23, unanswered.
- **Whether `Backups\` sits inside the working tree at all**, separately from being gitignored.
- **Whether "a handover is never changed" goes into `CLAUDE.md`.** Still only in the handovers and an amendment row.

---

## 5. Owed and not done

- **Per-firm folder naming into `2026-09-01_DESIGN_cloud_multi_firm.md`, as a question.** Owed by chat 11's handover, owed again by this one. The two conditions that make it more than a settings row: the names describe folders already on disk, so changing one is a migration; and both products write those folders, so IntelliBooks would have to read `firms.json`, which it does not read at all today.
- **The section A boundary rule into all three step 10d briefs.**
- **`PROMPT_claude_code_step10a_and_10b.md` is still in the root and must never be sent.** It moves at step 10h with every other spent file.
- **Change log item 51's flag:** the handover pack README at `IntelliBooks-Desktop-v3.html:2018` tells the client receipts and statements come as folders named `Receipts\` and `Statements\`. Left deliberately, because it describes what the recipient is handed rather than a path in the firm's tree.
- **Item 66's other half:** the comment at `IntelliBooks-Desktop-v3.html:2331` cites amendment 53 as open when section 18.9 lists it cancelled. **Item 84's other half:** `exportHMRC()`'s unmapped-categories warning at `:2835` fires synchronously while the success toast at `:2833` fires from a promise, so the warning is overwritten. Item 64 is the same defect from the other side.

---

## 6. What this session got wrong, and the first one is the expensive one

**It burned about ninety per cent of Paul's session credit on round trips with Claude Code, and he had to tell me.** Five commit briefs between 15:50 and 17:05. **Three of the five existed only to correct the one before, and two of those corrections were my own arithmetic.** The build work was a small part of the spend.

Three causes, and they compound:

**Every brief I wrote said "stop if the porcelain shows anything else".** So while one was out with Paul I could not touch another tracked file, and the next piece of work had to become its own commit. **I built the constraint that then forced the round trips.** Write task 1 as "stop if any `.py` file is modified, or anything under the practice root, or anything you did not expect", and batch the rest.

**The briefs were two thousand words each**, with tables, a full commit message and six or seven verification tasks. Each one fills Claude Code's context and comes back as a long report, and Paul pastes both ways. **Half a page is enough for a documentation commit.**

**The verification I set generated work rather than confirming it.** Contiguity, marker counts, hash boundaries, occurrence counts, on every commit. Each report found something, which produced another brief. **A loop that feeds itself, and I did not notice it running.** Run the full battery on a commit that touches code. On a documentation commit, check the diff and the amendment number.

**Do this instead: one commit at the end of a block of work, one brief of half a page, amendments batched into one row rather than four.**

**Three figure errors in one afternoon, all mine, none caught by me.**

- Amendment 173's headline said twenty references left as history. It is fifteen, and my own breakdown four sentences later said so.
- The same figure went into the commit message of `5748b22` and is permanent. **Amendment 174 adds the rule that came out of it: a commit message stating a figure needs that figure enumerated before the commit, because the message is the one artefact here that cannot be amended.**
- The commit message for `2bfe47d` said twenty-three numbers moved and it is twenty-six, which is what the same brief's task 2 listed. **Caught by Claude Code applying the rule 174 had just added**, before the commit this time.

**Two set failures of the classic shape.**

- `grep -c` counts lines and `grep -o | wc -l` counts occurrences. My first count of `build_coa` came back as 4 where it is 6, because two lines carry two each.
- The first line-number refresh found six `config.py` citations with a grep for `config.py:N` and missed a seventh written as a bare `:95`. **My own pattern could not match a member of the set, and the sentence I then wrote claimed the set was complete.**
- **And the fix for that one is the transferable part.** Claude Code reported four self-contradicting sentences in the Desktop brief. Patching those four would have left nineteen wrong and looked finished. **Enumerating every three and four digit number in the brief found twenty-six values, not four.** When a reviewer reports N instances of a class, the number of instances is the one thing their report does not establish.

**Two smaller ones, both caught by reading back rather than by the script.** A Python string concatenation swallowed two apostrophes in a comment I wrote into `IntelliBooks-Desktop-v3.html`, so it first read "She Runs It!" and "Pauls instruction". And the first version of my node check cut the path out of each message with a regex that stopped at the first space, so it reported six correct messages as failures. **My own filter hiding my own evidence, in the same hour I wrote an amendment about that failure.**

---

## 7. Three things Claude Code flagged on `2bfe47d` that are recorded nowhere else

- **"Thirty-eight" in that commit message reconciles only under a rule the message does not state.** 41 distinct Desktop line references minus `2519`, which is struck; minus `2606`, which is the design document's citation and not a line in the current file; minus `635`, `clientFolderPath()`, which did not exist before 10a.2 and so cannot be derived by the method the message describes. **The third exclusion is Claude Code's inference, not something the message says.**
- **The Desktop brief's note still opens "Line numbers refreshed 2026-09-02, 16:30 BST"** and is corrected by its own paragraph two sentences later. The pipeline note was rewritten to say "twice, at 16:30 and 16:55". Flagged, not fixed.
- **`PROMPT_claude_code_2026-09-02_commit_175.md` is headed 17:05 BST and Claude Code's clock read 16:55 when it opened the file.** The pipeline brief's own note says 16:55, which matches. Nothing turns on it, and it is the two-clocks bullet in `CLAUDE.md` in a new place.

---

## 8. Method notes for this environment

**Writing a file on Paul's machine, with no shell.** Stage it, edit locally, `SendUserFile` to get a `file_uuid`, `device_commit_files` with the `expectedMtimeMs` you staged at, then stage it again and hash what came back. **Hash what came back, not what you sent.** Every file this session wrote was verified that way and none differed.

**Every replacement script asserts its own occurrence count and writes nothing if any assertion fails.** That caught a reordering problem in the `config.py` refresh, where replacing 132 with 150 would have collided with the original 150 if the pairs had run in ascending order. **Descending by old value, and count with `grep -o` before writing the list.**

**Do not write a script through a shell heredoc if it contains backslashes or apostrophes.** Two of this session's errors came from that. Write the script to a file and run the file.

**Do not write to `2026-07-25_CONSOLE_DESIGN.md` while a commit brief is out that predicts its byte count.** That is real, but see section 6: the answer is fewer briefs, not more waiting.

**`_step10a_move.py` is in the root, has been run, and is idempotent.** A folder already moved is no longer where it looks, so it produces no move and no clash. Do not run it again; it is not anyone's task now.
