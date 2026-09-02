# AUTOMATIC task: commit amendments 166 to 169, two file deletions, `Backups/` gitignored, and six new sub-steps

**Written 2026-09-02 by the consultant session, for Claude Code. Paste this whole file in.**

Runs under AUTOMATIC Task Mode in `CLAUDE.md`. Its "stop and ask" list is unchanged and outranks this file.

Documentation only. No code, no tests, nothing for you to edit. Write your report, then one commit, a push, a verification.

**This file is named `commit_167` and covers amendments 166 to 169.** It was rewritten in place after amendments 168 and 169 were written, rather than reissued under a new name, because another stale brief in the root is worse than one named discrepancy. **The name understates the range. Nothing else about it is stale.**

**It is also the follow-up to your commit `81aec08` and clears the three things you left in the working tree on Paul's instruction.** The two CSV deletions now have an amendment behind them, so they are staged this time. `Backups/` is gitignored.

**Position.** HEAD is `81aec084457da8c48073655d96527fef27c3c4d4`, "docs: amendments 161 to 165, the cloud design document, the three step 10d briefs, and eleven items closed", on `feat/console-phase0`, committed 2026-09-02 and pushed, with `origin/feat/console-phase0` at the same commit. **Amendments 1 to 165 are in.** This commit carries **166, 167, 168 and 169**.

---

## Why

**Amendment 166 fixes what amendment 164 broke.** Section 16's head line said "Below the table, 105 sub-steps: 6 BUILT and 99 OUTSTANDING". Both figures were right until amendment 164 added sub-steps 10d.51 and 10d.52 and became 107 and 101. **The total leaves the line:** the four decomposed steps are named, the six BUILT sub-steps stay named, and no total is stated. **You found it as finding 3 of `2026-09-01_REPORT_claude_code_commit_164.md`.**

**Amendment 167 is your findings 1 and 5, plus three older strikes and one line of `.gitignore`.** `chart_of_accounts_DRAFT.csv` and `chart_of_accounts_DRAFT2_2026-08-03.csv` are deleted and the five live sentences saying they are kept are struck, along with two in `2026-08-03_NOTE_chart_of_accounts_for_paul.md`. **Three of those strikes were not caused by the deletion at all**: 17.4's note, its "Extend" bullet and 18.7's clause were already false when amendment 96 closed the extension question on 2026-08-17. Amendment 163's own row still asserted the markdown figure amendment 165 removed, and is struck. And "nine of its fifteen sub-steps" goes the same way as the 105.

**Amendment 168 is step 10a, and it could not have been built from its own text.** Four wrong statements struck: the two subfolder literals are `worker/filing.py:78` and `:103`, not `get_client_directory()` at `:64`; two constants are needed, not three, because Review already has `config.REVIEW_ROOT`; the values carry no underscore; and the subfolder set includes `IntelliBooks`, which no list held. **Desktop has nine `getDir(["Clients", ...])` sites, not six, plus a tenth built as a string.**

**The failure step 10a would have caused is the one that already happened.** Landing the constants at `_Receipts` while `IntelliBooks-Desktop-v3.html` reads `Receipts` is one product writing a path the other does not read, which is what hid four TESTST receipts from the Receipts tab on 2026-09-01. **A step that promises to change no behaviour would have caused it.**

**Amendment 168 also writes down the reasoning for `Intellibills\Documents\` for the first time.** `worker/storage/store.py` has no docstring at all, where `worker/filing.py:156` explains the Review move at length.

**Amendment 169 adds six sub-steps to step 10d, taking it from 52 to 58**, and the first two are a hole in `PROMPT_claude_code_2026-09-01_step10d_pipeline.md`. That brief deletes `client_code` from the file, every table and every payload, and **its text did not mention `store.py`, `save_file`, `save_inbox_file`, `storage`, `FILES_DIR`, `Documents`, `REVIEW_ROOT` or `_review_dir_for_client_code` once**, searched for all eight. Two folder layouts were keyed on the field being deleted. **Paul found it by asking whether the client code was going.** The remaining four are a statement's missing copy in the document store, the `file_path` column meaning two different things, and two IntelliBooks outputs carrying the client code.

**All three step 10d briefs are modified by this commit**, and their section A is still byte-identical. **Nothing in step 10d is executed here.**

---

## What I verified, and what I did not

**I have no shell on Paul's machine this session.** Everything below came off the object database and the file system through the folder bridge.

**Your commit `81aec08` was verified independently.** I decompressed the commit and both root trees, recomputed their SHA-1s, and diffed the two trees entry by entry: 8 added, 3 modified, 0 removed, eleven paths, and **no subtree pointer changed**, which establishes that nothing under `worker\`, `tests\`, `docs\`, `.claude\` or `Test Receipts\` moved.

**"Modified" below is established, not inferred.** For each of the six files I took the HEAD blob id out of commit `81aec08`'s tree and computed the git blob SHA-1 of the file now on disk. All six differ, and both are in the table.

**Every file I wrote was read back off Paul's machine and hashed there**, not hashed from what I sent.

**Zero CRLF in all six, counted at byte level.** All six end with a newline.

**I did not check the 179 other tracked entries.** **Task 1 is the gate over the part I could not see, and any modified `.py` file means you stop.**

---

## Task 1. Confirm the starting state

```
git --no-optional-locks status --short
```

**Expect exactly six modified, two deleted and one untracked.** Your own report is a second untracked file and does not exist yet.

```
 M .gitignore
 M 2026-07-25_CONSOLE_DESIGN.md
 M 2026-08-03_NOTE_chart_of_accounts_for_paul.md
 M PROMPT_claude_code_2026-09-01_step10d_pipeline.md
 M PROMPT_intellibooks_2026-09-01_step10d_desktop.md
 M PROMPT_phoneapp_2026-09-01_step10d.md
 D chart_of_accounts_DRAFT.csv
 D chart_of_accounts_DRAFT2_2026-08-03.csv
?? PROMPT_claude_code_2026-09-02_commit_167.md
```

**`?? Backups/` must be gone**, because `.gitignore` now covers it. Confirm it and quote the output:

```
git --no-optional-locks check-ignore -v Backups/
```

**Expect exit 0 and `.gitignore:12:Backups/  Backups/`.** Line 12 is the last line of the file. **If it still exits 1, stop**: the `.gitignore` on disk is not the one I wrote.

**Stop and report anything else, in particular any `.py` file.**

Use `--no-optional-locks` on every read. If `.git\index.lock` exists, check `tasklist /FI "IMAGENAME eq git.exe"` reports no tasks, then `del .git\index.lock`.

**The six modified files.**

| File | HEAD blob at `81aec08` | HEAD bytes | Disk blob now | Disk bytes |
|---|---|---|---|---|
| `2026-07-25_CONSOLE_DESIGN.md` | `a67a58bc0b57cdb8e1f8201929537545e538350b` | 593,752 | `247739c9ab5b53e97bf7212dcce2bbea74a76075` | 611,684 |
| `2026-08-03_NOTE_chart_of_accounts_for_paul.md` | `153c5beb6cf7e6b6d14211ed398e197581092601` | 8,891 | `9f9627371c9faf6fdbfd3538f941b4eb2ba19304` | 9,467 |
| `.gitignore` | `e8083e4be42c10f1a8ab0c350c3669432ed9e07e` | 110 | `c6ec49e6d27f17722d170bd6c28351e55872dec6` | 120 |
| `PROMPT_claude_code_2026-09-01_step10d_pipeline.md` | `21c1287c1ee865bcf3ab1f0ddfc6a3c600b0fbd3` | 28,150 | `d9b81266262e35990d5d81794741aaf373095034` | 33,470 |
| `PROMPT_intellibooks_2026-09-01_step10d_desktop.md` | `a5d4647aeec741a009e8297d3a31b4b3e2b32742` | 20,496 | `5959a0eb00b523851104e7fa58b1f03c79a43e8b` | 22,458 |
| `PROMPT_phoneapp_2026-09-01_step10d.md` | `b7cefaabc626930d0fb8128536fca5fd329255aa` | 18,769 | `2a57ed46423b38af171b47917dec72630e8747b7` | 18,949 |

**The disk column is a prediction of what `git hash-object` will return**, computed here as `sha1("blob " + length + NUL + bytes)` over each file read back off Paul's machine. **Run `git hash-object` on all six and quote it.** A mismatch on any row means the file changed after I wrote it and you stop.

**MD5, hashed on Paul's machine after each write:**

```
ca3441a9d34c5a0841d7b3800c1ebc1e  2026-07-25_CONSOLE_DESIGN.md
94fd5bbd2f696e5c3756a69f0867b2f3  2026-08-03_NOTE_chart_of_accounts_for_paul.md
0dabd50c7169e05376c9d6f52fad33af  .gitignore
2a92d0d47c40f65bb9899f8ce6dd87ee  PROMPT_claude_code_2026-09-01_step10d_pipeline.md
bfa7c26b0f371a6fb488c5df9a98465e  PROMPT_intellibooks_2026-09-01_step10d_desktop.md
ed493281198f9976f119b79d6df38285  PROMPT_phoneapp_2026-09-01_step10d.md
```

**The two deletions.** Both are absent from disk and both are in HEAD at `81aec08`: `chart_of_accounts_DRAFT.csv` at `46c04a03d11c3dd718243c83592614e5f749e38d`, 1,504 bytes, and `chart_of_accounts_DRAFT2_2026-08-03.csv` at `0dd8a06d012416f3d7273313d81fd40c27f0a586`, 8,583 bytes. **They are staged in this commit, unlike last time.**

**The root holds 86 markdown files: 85 tracked, and this brief.** All 85 became tracked in `81aec08`. **Your report makes 87.**

---

## Task 2. Prove nothing has been lost, before staging

Eight checks, all programmatic, all quoted whole in your report.

**a. Amendment rows.** Compare the numbered rows of the amendment record in HEAD against the working tree. Expect **only in the working tree `[166, 167, 168, 169]`, all four, and only in HEAD empty.** A non-empty second list means an amendment has been deleted and you stop.

**b. Contiguity, by amendment 97's corrected method.** Bound the scope to the amendment record's own line boundaries, print those boundaries with the result, assert the list equals `range(first, last+1)`, and test duplicates explicitly. **Never a set difference.** I get **169 rows, no duplicates, equals `range(1,170)`, the record bounded to lines 35 to 371 on disk, the first numbered row at line 45 and the last at line 370, and `## How to use this document` at line 372.**

**Four version blocks are added by this commit, not one.** 1.26 becomes 1.27 for amendment 166, 1.28 for 167, and 1.29 for 168 and 169 together, all dated 2026-09-02. `### v1.27` is at line 352, `### v1.28` at 358 and `### v1.29` at 365. Every superseded version line is struck in the header.

**c. Section 16 agrees with itself.** Extract the head table and the body statuses and diff them: expect **38 steps, identical, 18 BUILT, 18 OUTSTANDING, 1 CANCELLED, 1 MOVED**, unchanged by this commit. Then the sub-steps: **10d has 58, 10e has 15, 10f has 30, 10g has 10**, each contiguous from 1 with no gaps and each line carrying a status word. **10e is 6 BUILT and 9 OUTSTANDING**; the other three are wholly OUTSTANDING.

**10d's head-table row changed with it** and now reads `| 10d | One client registry, the phone app credential and its settings model, 58 sub-steps | **OUTSTANDING** |`. **The number in the row and the count of sub-step headings in the body must both be 58.** The prose count in the step's own preamble also reads 58, with 52 struck.

**Use the word-boundary status pattern you wrote for the last brief, not a string pattern.** Your own finding stands: 10e.13 reads `**BUILT 2026-08-31**` with no full stop before the closing asterisks and the other five have one, so there are three shapes and only a word-boundary anchor catches all six.

**And section 16's head line needed no change for any of this**, because amendment 166 removed the total two days after it was written. **Confirm the head line states no sub-step total.**

**d. The figures amendments 166 to 169 removed are gone from the live text, and present in strikes.** Strip every `~~...~~` span and count in what remains. I get **zero** for each of these:

```
"105 sub-steps"                        live: 0
"52 sub-steps"                         live: 0
"80 markdown files"                    live: 0
"nine of its fifteen"                  live: 0   (outside amendments 166 to 169's own rows, which quote it)
"is kept as the record"                live: 0
"Extend `chart_of_accounts_DRAFT.csv`" live: 0
"the only other site"                  live: 0
"Desktop's six"                        live: 0
"flip them in 10c"                     live: 0
```

And in `2026-08-03_NOTE_chart_of_accounts_for_paul.md`, **"untouched and stays" live: 0** and **"Companion to" live: 0**.

**Report the struck span each one now sits in.** A zero with no strike behind it means text was deleted rather than struck, and this project keeps superseded wording visible.

**`_Receipts` and the rest of that family still appear live and that is correct.** I counted them: `_Receipts` 5, `_Statements` 5, `_Review` 3, `_Handover Pack` 2, `_HMRC Summaries` 2, `_IntelliBooks` 5. **Every one is either inside an amendment row that records the superseded decision, or inside body text that already says the section cannot be built as written.** I checked all five body occurrences individually, at lines 1511, 1517, 2202 and 2456. **Do not strike any of them and do not report them as a defect.**

**e. Every table row has the pipe count its own header row has.** Header-relative, counting only pipes **not** preceded by a backslash. I get **0 inconsistent rows** in all six files. **Block counts on my definition** (any run of two or more consecutive lines whose stripped text begins with a pipe): 46 in `2026-07-25_CONSOLE_DESIGN.md`, 3 in `2026-08-03_NOTE_chart_of_accounts_for_paul.md`, and 3 in each of the three step 10d briefs. **Report your own with the definition you used. The 0 is the assertion; the block count is context.**

**f. The three step 10d briefs still carry the same field list.** Extract the section from the `## A. The field list` heading to the next line beginning `## ` in each of the three, and hash it. **All three must be identical.** I get **3,056 bytes and MD5 `0d0dda57d858577da806dea2e3c3e45f` in all three.** **Your MD5 will differ if you take the boundary differently; the assertion is that the three match each other.** **Three different values means the briefs have drifted and you stop rather than choosing one.**

**Section A changed in this commit**, from 2,876 bytes and `97ecd1d77f3459a7c314b75408490fdf`, by one sentence added identically to all three.

**g. `2026-08-20_LIST_outstanding_items_and_decisions.md` is not in this commit and must not be modified.** Confirm it is unchanged from HEAD, and confirm its count line still reads `87 open, 64 closed, 151 raised`. **No item is opened or closed by any of the four amendments.**

**h. Nothing from outside the repository is in the commit.** `git show --stat` on your own commit must name **ten files and no path containing `IntelliCharts`, `OneDrive` or `Intellibills`.**

---

## Task 3. Count the root markdown files, and do not correct anything

**Enumerate the markdown files in the repository root after your commit** and report three numbers: the total, how many are tracked, how many untracked. Enumerate them; do not filter a search and count the hits.

**Step 10h states no total, by amendment 165, and it must stay that way.** It names the 17 files that stay. **Check all 17 are present and report any that are not. Do not add a total and do not touch step 10h.**

---

## Task 4. Write the report, then one commit

**Write the report before staging**, so it lands in the same commit.

```
git add .gitignore 2026-07-25_CONSOLE_DESIGN.md 2026-08-03_NOTE_chart_of_accounts_for_paul.md PROMPT_claude_code_2026-09-01_step10d_pipeline.md PROMPT_intellibooks_2026-09-01_step10d_desktop.md PROMPT_phoneapp_2026-09-01_step10d.md chart_of_accounts_DRAFT.csv chart_of_accounts_DRAFT2_2026-08-03.csv PROMPT_claude_code_2026-09-02_commit_167.md 2026-09-02_REPORT_claude_code_commit_167.md
```

**`git add` on a path whose file is gone stages the deletion.** After staging, run `git --no-optional-locks status --short` again and **confirm both CSVs read `D ` in the first column, staged, not ` D` unstaged.** If either is still unstaged, stop and report it rather than reaching for `git rm`.

**Ten files. Check every one is named or described in the message below before you commit.**

Message:

```
docs: amendments 166 to 169, the two draft CSVs deleted, Backups
gitignored, and six new step 10d sub-steps

All four amendments are the consultant session's, 2026-09-02, and three
of the four fix things that session broke or missed. Amendments 166, 167
and 168 were all found by Claude Code or by Paul, not by the session that
wrote the text.

  166: the sub-step total leaves section 16's head line. It said 105
  sub-steps, 6 BUILT and 99 OUTSTANDING, which was correct until
  amendment 164 added 10d.51 and 10d.52 and made it 107 and 101. The
  four decomposed steps are named, the six BUILT sub-steps stay named,
  and no total is stated. Amendment 164 updated 10d's head-table row
  without striking the line that stated the total, which is what the
  head of the amendment record instructs. Amendment 165 then removed a
  stale total from step 10h sixteen lines below and did not look up. The
  38 steps and the 18/18/1/1 split stay, because every commit brief
  diffs the head table against the body statuses, so those two fail
  loudly rather than silently. Claude Code's finding 3.

  167: chart_of_accounts_DRAFT.csv and
  chart_of_accounts_DRAFT2_2026-08-03.csv are deleted from disk, and the
  sentences saying they are kept are struck. Paul deleted both on
  2026-09-01. Nothing is lost: 46c04a03 at 1,504 bytes and 0dd8a06d at
  8,583 stay reachable through this commit's parent. Five sentences in
  2026-07-25_CONSOLE_DESIGN.md are struck, at amendment 90's row, in
  section 13, twice in 17.4's 2026-07-30 note and in 18.7's
  PKPH-books.json entry, and two in
  2026-08-03_NOTE_chart_of_accounts_for_paul.md, which stays in the root
  under step 10h while neither CSV does. Three of those strikes were not
  caused by the deletion: 17.4 and 18.7 were already false when
  amendment 96 closed the extension question on 2026-08-17 and were not
  struck then. Amendment 163's own row still asserted step 10h's
  80-markdown-file figure that amendment 165 removed from step 10h and
  from item 32, and is struck. "Nine of its fifteen sub-steps" on 16's
  head line goes on the same ground as the 105. Backups/ is added to
  .gitignore as line 12, on Paul's decision: 19 markdown files, 1.74
  MiB, written by the previous consultant session between 2026-08-31
  20:54 and 2026-09-01 13:45 BST, eleven of them drafts of
  2026-08-24_HANDOVER_consultant_chat_11.md. Nothing in it is committed
  and nothing is deleted from it. On the byte figure: 8,583 is the blob
  and 8,626 is the working-tree size cached in .git/index, because
  .gitattributes is * text=auto eol=lf and the file had CRLF on disk, so
  the 43 line endings are the difference. Claude Code corrected it and
  the consultant session confirmed it by decompressing the blob. Claude
  Code's findings 1 and 5.

  168: four wrong statements in step 10a are struck, and the reasoning
  behind Intellibills\Documents\ is written down for the first time. The
  two subfolder literals are worker/filing.py:78 and :103, not
  get_client_directory() at :64, which holds no subfolder name at all.
  Two constants are needed, not three, because Review left the client
  folder and already has config.REVIEW_ROOT at config.py:42. The values
  carry no underscore: the literals are "Receipts" and "Statements". The
  subfolder set includes IntelliBooks, written by
  IntelliBooks-Desktop-v3.html at lines 703 and 3105, which no list
  held. And Desktop has nine getDir(["Clients", ...]) sites, not six,
  plus a tenth at 2519 built as a string; step 10f already carried nine.
  The failure the step would have caused is the one that happened on
  2026-09-01: landing the constants at _Receipts while
  IntelliBooks-Desktop-v3.html reads Receipts is one product writing a
  path the other does not read, which is what hid four TESTST receipts
  from the Receipts tab. There is no */Review glob at filing.py:297;
  that line is removed = _delete_review_pair(sidecar). Two questions in
  10a are left open because they are Paul's: whether amendment 55's
  namespaced underscore form is still wanted, and where the flip lives
  now that 10c is BUILT. The recorded reasoning for the document store,
  which worker/storage/store.py has no docstring for at all: it is keyed
  on client, then arrival year, then arrival month, because the save at
  app.py:733, :918 and :1097 happens before extraction so no invoice
  date exists yet, because an arrival date never needs correcting where
  an invoice date does, and because month buckets bound a store that
  only grows. And the thing that reverses a conclusion the session had
  already drawn: Intellibills\Documents\ is not a backup of the client
  folder, it is the original and the working file. receipts.file_path
  holds its path, the extractor reads it at app.py:949,
  worker/filing.py:88 copies from it, and app.py:362 skips the receipt
  if it has gone.

  169: six sub-steps, taking step 10d from 52 to 58, and all three step
  10d briefs change with them. 10d.53 keys Intellibills\Documents\ on
  client_id, at worker/storage/store.py lines 23 and 37 and their three
  callers. 10d.54 keys Intellibills\Review\ on client_id, renaming
  _review_dir_for_client_code() at worker/filing.py:155 and changing
  file_review()'s parameter at :118. Those two are a hole in
  PROMPT_claude_code_2026-09-01_step10d_pipeline.md, which deletes
  client_code everywhere and mentioned store.py, save_file,
  save_inbox_file, storage, FILES_DIR, Documents, REVIEW_ROOT and
  _review_dir_for_client_code not once between them; Paul found it by
  asking whether the client code was going. 10d.55 gives a statement a
  copy in Intellibills\Documents\ before it is filed, which it has never
  had, so today Clients\<name>\Statements\ is the only copy and cannot
  be reconstructed where Clients\<name>\Receipts\ can. 10d.56 gives
  statements a filed_path so that file_path means the document store's
  copy on both tables and filed_path means the client folder's copy on
  both; today statements.file_path holds the filed copy and
  receipts.file_path holds the original. 10d.57 and 10d.58 stop the HMRC
  summary filenames and the archive JSON's code field carrying the
  client code, both read off disk in Clients\Test Sole Trader\HMRC
  Summaries\. Section 16's head line needed no change for any of it,
  which is amendment 166 paying for itself two days after it was
  written.

Also in this commit:

  2026-07-25_CONSOLE_DESIGN.md: version 1.26 becomes 1.29 through three
  blocks, v1.27 holding amendment 166, v1.28 holding 167 and v1.29
  holding 168 and 169, with every superseded version line struck in the
  header.

  2026-08-03_NOTE_chart_of_accounts_for_paul.md: its line 3 companion
  reference and its line 5 record claim struck, and its one other
  mention of the file marked as now in git only.

  .gitignore: one line, Backups/, at the end.

  PROMPT_claude_code_2026-09-01_step10d_pipeline.md gains sub-steps
  10d.53 to 10d.56, two verification steps and one report question.
  PROMPT_intellibooks_2026-09-01_step10d_desktop.md gains a section for
  10d.57 and 10d.58 and its later sections are relettered.
  PROMPT_phoneapp_2026-09-01_step10d.md changes only in section A. That
  section is byte-identical in all three, 3,056 bytes, and every brief
  instructs its reader to stop if it is not. None of the three is
  executed by this commit.

  PROMPT_claude_code_2026-09-02_commit_167.md, the brief this commit was
  worked from. Its name understates its range: it covers 166 to 169,
  having been rewritten in place after amendments 168 and 169 rather
  than reissued under a new name.

  2026-09-02_REPORT_claude_code_commit_167.md, the report on this
  commit.

Not in this commit: 2026-08-20_LIST_outstanding_items_and_decisions.md
is untouched and no item is opened or closed. The date on section 16's
head line is untouched and remains an open contradiction: it says the
six sub-steps were built 2026-09-01 and all six read BUILT 2026-08-31.
Claude Code found it as finding 4, nothing on disk settles it, and Paul
has not ruled.
```

Then push. Branch `feat/console-phase0`. `git push --dry-run` first, fast-forward only, never `--force`.

---

## Verify, and quote the output

1. `git --no-optional-locks status --porcelain` returns nothing at all. **This time it can, and if it does not, quote what is left.**
2. One commit on the branch, parent `81aec08`, pushed fast-forward.
3. Amendment numbering contiguous 1 to 169 by task 2b's method, with the boundaries printed.
4. **No `.py` file in the commit, and no path containing `IntelliCharts`, `OneDrive` or `Intellibills`.** `git show --stat` on your own commit.
5. Section 16's table and body still agree at 38 steps, and 10d, 10e, 10f and 10g still have 58, 15, 30 and 10 sub-steps with no gaps.
6. **Both CSVs are gone from the tree.** `git ls-files -- 'chart_of_accounts_*'` returns nothing, and `git cat-file -s 46c04a03` and `git cat-file -s 0dd8a06d` still return 1504 and 8583, proving the content survived the removal.
7. `git --no-optional-locks check-ignore -v Backups/` still exits 0.
8. The three step 10d briefs' section A still hashes the same in all three, run again after the commit.
9. Read the commit message back against `git show --stat`. **Ten files, so check every committed filename is either named or described.**

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
- **Any suggestion to restore either CSV.** They are deleted deliberately and this commit records the decision.

---

## Not in this commit

**None of the four amendments builds anything.** All four are corrections and decisions recorded in documents.

**Step 10d is not started here, and the six new sub-steps are not worked here.** `PROMPT_claude_code_2026-09-01_step10d_pipeline.md` is a separate task Paul will send when he is ready, and **this commit modifying it is not being given it**. Do not create `_step10d_clients.json`, `_step10d_firms.json` or `_step10d_rebuild.py`, do not touch `clients.csv` or `firms.csv`, do not rebuild `receipts.db`, and do not change `worker/storage/store.py` or `worker/filing.py`.

**Nothing under `Intellibills\Documents\` is touched.** Sub-step 10d.53 records that `PKPH` and `TESTST` hold five files between them and that Paul removes them. **That is not this task.**

**Step 10h is not this task.** No file moves and there is no `archive\` directory.

**Nothing in `Backups\` is committed, moved or deleted.** It is gitignored and left as it is. **Whether the folder belongs inside the working tree at all is Paul's decision and is not taken here.**

**Do not `git init` anything under `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\` and do not add any part of it.** The three step 10d briefs name paths under that root, and naming them is not a licence to touch them.

**Do not send or act on `PROMPT_claude_code_step10a_and_10b.md`**, written against a folder scheme abandoned in July, or touch `PROMPT_intellibooks_desktop_changes.md`, which is another session's standing brief.

---

## Report to a file

`C:\LastingImpact\receipt_capture\2026-09-02_REPORT_claude_code_commit_167.md`, written before staging per task 4.

Include the full output of task 1 including the six `git hash-object` results and the `check-ignore` line, all eight outputs from task 2 with the line boundaries, block counts, struck spans and hashes printed, task 3's three numbers and its 17-name check, the porcelain result, and what verification step 9 returned.

**And four things I want back.**

**Were the six disk blob hashes right?** They were computed here from the bytes read back off Paul's machine rather than by running `git hash-object`, so they are a real prediction. Tell me if any differs.

**Did the deletions stage cleanly with `git add`?** I have asserted that `git add` on a missing path records the removal. If it did not, say what you did instead and whether it needed a stop.

**Are the nine figures in task 2d struck rather than deleted?** Quote the struck span each one sits in. **This is the check I care about most**, because striking and deleting look identical in a live-text count and only one of them keeps the trail.

**And the `_Receipts` family.** I have told you 22 live occurrences across six names are all legitimate and named where the five body ones are. **Tell me whether you agree, one line each for the five body occurrences.** If you think any is a live instruction rather than a superseded record, that is a finding and I want it.

**Three disclosures about this session.**

**Amendments 164 and 165 were both mine and each broke or missed something the other should have caught.** 164 made section 16's head line wrong. 165 removed a stale total sixteen lines below it and did not look up. Both were found by you.

**I twice repeated step 10a's prose to Paul without opening the files it describes**, including the `*/Review` glob at `filing.py:297` that does not exist. Amendment 168 exists because he asked a plain question about it and I finally read `worker/filing.py`.

**And I broke the byte-identical field list while editing these briefs.** I added a sentence to section A of `PROMPT_intellibooks_2026-09-01_step10d_desktop.md` alone, which is the one thing all three briefs tell their reader to stop over. **Caught by hashing the three sections before sending, which is the check task 2f asks you to run.** The sentence is now in all three, identically, and section A's hash moved from `97ecd1d7` to `0d0dda57` as a result. **This is the second time this session has broken that invariant and the second time hashing caught it.**
