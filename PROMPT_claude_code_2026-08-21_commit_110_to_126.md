# AUTOMATIC task: commit amendments 110 to 126, and four untracked documents

**Written 2026-08-21 by the consultant session, for Claude Code. Paste this whole file in.**

Runs under AUTOMATIC Task Mode in `CLAUDE.md`. Its "stop and ask" list is unchanged and outranks this file.

Documentation only. No code, no tests, nothing for you to edit. Write your report, then one commit, a push, a verification.

---

## Why, and this one is worse than the usual backlog

`2026-07-25_CONSOLE_DESIGN.md` at HEAD is **v1.12 with 109 amendments**. On disk it is **v1.21 with 126**. So **seventeen amendments, 110 to 126, exist in one place only**, and that place is a working tree.

What is in those seventeen matters more than the count. **Amendment 121 rebuilt section 16 so Paul can read it**, giving every step one of four status words, adding the table at the head, and decomposing step 10d into 34 numbered sub-steps. Checked against the HEAD copy: it holds **no status words, no head table and no `10d.1`**. The one change made because Paul said "the document is readable by you but not by me" is uncommitted.

**And `2026-08-20_LIST_outstanding_items_and_decisions.md` has never been committed at all.** It is one of the two lists the project runs on, it carries 142 numbered items, and it is untracked. Losing that working tree loses all of it.

Outstanding item 8 says "files uncommitted in git" and reads like housekeeping. It is not.

---

## What I verified, and what I did not

I have a shell on Paul's machine this session. **I ran no git command.** I read `.git/HEAD`, `.git/config`, `.git/refs/` and `.git/index` as files, and inflated loose objects with zlib, checking each object's SHA-1 against its own filename before trusting the bytes. The repository has no `packed-refs` and no pack files, so every object needed was loose.

| Read from | Result |
|---|---|
| `.git/HEAD` | `ref: refs/heads/feat/console-phase0` |
| `.git/index` | version 2, header says **170 entries**, parsed 170 |
| index blob for the design document | `f2f3b362`, **373,756 bytes**, inflated and SHA-1 verified |
| the design document on disk | **457,470 bytes** |
| `.git/config` | remote `origin` is `https://github.com/Impact-sys-pk/receipt-capture.git`, and `feat/console-phase0` has an upstream |

**Coverage, stated plainly.** I compared **all 66 tracked root-level `.md` files** against their blobs, byte for byte. That comparison is valid because **not one of the 70 markdown files at root contains a single CRLF**, which I counted rather than assumed, so the usual line-ending trap does not apply to them.

**I did not check the other 104 tracked entries.** Those are the `.py` files and everything under `worker\`, `tests\`, `docs\` and `.claude\`, and they are exactly the files `.gitattributes` stores LF and Windows holds CRLF, so a size comparison would be meaningless. **Task 1 is therefore a real gate over the part I could not see.**

---

## Task 1. Confirm the starting state

```
git --no-optional-locks status --short
```

Expect exactly four modified and five untracked. The fifth untracked is your own report, which does not exist yet.

```
 M 2026-07-25_CONSOLE_DESIGN.md
 M 2026-07-31_PLAN_reset_and_restructure.md
 M 2026-08-18_BOUNDARY_two_products.md
 M CLAUDE.md
?? 2026-08-20_LIST_outstanding_items_and_decisions.md
?? 2026-08-20_LIST_settings_firm_and_client.md
?? 2026-08-20_NOTE_demo_version.md
?? 2026-08-21_HANDOVER_consultant_chat_9.md
?? PROMPT_claude_code_2026-08-21_commit_110_to_126.md
```

**Stop and report anything else, in particular any `.py` file.** My prediction covers 66 of 170 tracked entries and I have said which 104 it does not.

Use `--no-optional-locks` on every read. Plain `git status` takes a lock this project has twice been unable to release.

If `.git\index.lock` exists, check `tasklist /FI "IMAGENAME eq git.exe"` reports no tasks, then `del .git\index.lock`.

---

## Task 2. Prove nothing has been lost, before staging

Five checks, all programmatic, all quoted in your report.

**a. Amendment rows.** Compare the numbered rows of the amendment record in HEAD against the working tree. Expect **only in the working tree `[110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126]`, only in HEAD empty**. A non-empty second list means an amendment has been deleted and you stop.

**b. Contiguity, by the corrected method.** Bound the scope to the amendment record's own line boundaries, print those boundaries with the result, assert the list equals `range(first, last+1)`, and test duplicates explicitly. **Never a set difference.**

I ran this on the working tree. Stating the boundaries because they say what was counted: `## Amendment record` is at line **26**, the section ends at line **277**, and the numbered rows run inside that. **126 rows, no duplicates, equals `range(1,127)`.**

Note the boundaries have moved several times this week. Anything quoting 15 and 187, or 16 and 189, is stale.

**c. Section 16's table agrees with its own body.** Amendment 121's convention is that every step carries one of `BUILT`, `OUTSTANDING`, `CANCELLED`, `MOVED` at its head, and the table at the top of the section carries the same word for the same step. Extract both sets and diff them. Expect **38 steps, identical, 18 BUILT, 18 OUTSTANDING, 1 CANCELLED, 1 MOVED**, and **34 sub-steps `10d.1` to `10d.34`, all OUTSTANDING, no gaps**.

**d. Every table row has the pipe count its own header row has.** Amendment 126 escaped seven unescaped pipes as `\|` across two documents. Write the check against **each table block's own header row**, not against a fixed number, and count only pipes **not preceded by a backslash**. Expect **47 table blocks in the design document and 0 inconsistent rows**, and **25 blocks and 0 inconsistent** in `2026-08-20_LIST_outstanding_items_and_decisions.md`.

**A naive version of this check over-reports.** Mine did, on amendment 94, whose pipe is already escaped inside a `grep -n "for email_msg in\|for msg in"` pattern. If your check flags a row, confirm the pipe is genuinely unescaped before calling it a fault.

**e. The outstanding items list adds up.** Its count line at line 3 must read `133 open, 9 closed, 142 raised`, open plus closed must equal the highest number used, no number may appear twice, and no number may appear in both the open sections and the Closed section. Enumerate both sides separately.

---

## Task 3. Write the report, then one commit

**Write the report before staging**, so it lands in the same commit. Path and contents are at the end of this file.

```
git add 2026-07-25_CONSOLE_DESIGN.md 2026-07-31_PLAN_reset_and_restructure.md 2026-08-18_BOUNDARY_two_products.md CLAUDE.md 2026-08-20_LIST_outstanding_items_and_decisions.md 2026-08-20_LIST_settings_firm_and_client.md 2026-08-20_NOTE_demo_version.md 2026-08-21_HANDOVER_consultant_chat_9.md PROMPT_claude_code_2026-08-21_commit_110_to_126.md 2026-08-21_REPORT_claude_code_commit_110_to_126.md
```

**Ten files. Check every one of them is named or described in the message below before you commit**, because the last commit of this shape had a filename the message omitted and the check that found it was reading the message back against `git show --stat`.

**One commit, not two, and the reason is a judgement you should know about.** The design document's diff is 20 hunks carrying two sessions' work, chat 8's amendments 110 to 121 and this session's 122 to 126, interleaved in the amendment record and in section 16. Splitting them would mean staging hunks by hand in the one file where a mistake loses a decision. Paul can ask for a split; nobody should attempt one to be tidy.

Message:

```
docs: amendments 110 to 126, section 16 made readable, and the two lists tracked

Seventeen amendments existed only in the working tree, and one of the two
lists this project runs on had never been committed at all. This commit is
two sessions' work because the design document's hunks interleave and
splitting them by hand risks losing a decision.

110 to 121, from the session of 2026-08-20 and 2026-08-21:

  110: step 10d takes its position in the build order, after the reset and
  before every console step.

  111: the field list for the one client registry, clients.json.

  112: the inbox carries the client identity inside the item, so the folder
  name becomes decoration.

  113: capture_token joins step 10d, which widens to three codebases, and
  the 18.2b freeze is narrowed so get_client_directory() can be repointed.

  114 to 117: the UNKNOWN client stops arriving as a fallback and becomes a
  recorded conclusion, DEFAULT_FIRM_ID stops being a fallback, the database
  is rebuilt rather than migrated, and the Firm Settings page is scheduled
  as step 10e.

  118: the VAT work of 18.4 and 18.5 becomes step 10g. Decided, unbuilt,
  and found by sweeping the document for decisions with no step.

  119 and 120: eight documents are scheduled for reconciliation as step
  10h, and five corrections from reading files a sweep had recorded as
  unread.

  121: section 16 is made readable. Every step and sub-step carries one of
  BUILT, OUTSTANDING, CANCELLED or MOVED, a table at the head carries the
  same, and step 10d becomes 34 numbered sub-steps. Nothing is inferred
  from strikethrough, which in that section meant four different things.
  Paul's words were that the document was readable by the session and not
  by him.

122 to 126, from the session of 2026-08-21:

  122: Paul rules outstanding item 139. The copy into Clients\ is
  Intellibills' function with two triggers set per firm, get_client_directory()
  stays and 10d.14 is unblocked, and step 10f gains the removal of the
  write on arrival that amendment 73 decided and no step ever scheduled.
  The claim that the function is lost was made in four places in the
  document, not the two the amendment first named, and all four are struck.

  123: the version header is corrected to 2026-08-21, and the missing
  v1.10, v1.11 and v1.12 headings are restored so amendments 96 to 109 no
  longer all sit under v1.9.

  124: coa_accounts leaves step 11. Loading the chart into the database
  stays cancelled until Paul says otherwise, so step 12 keeps its status
  and its number stays reserved.

  125: step 18 stops naming clients.csv. Whether 8.6's reload mechanism
  applies to clients.json is raised as outstanding item 142.

  126: seven table rows held an unescaped pipe and rendered with extra
  columns, so text in the file was not on Paul's screen. All seven escaped.
  Worst was amendment 95, which lost the words after app_default, being
  the sentence that defines the four chart-of-accounts scopes.

Also in this commit:

  2026-07-31_PLAN_reset_and_restructure.md, modified: three sentences
  corrected under amendment 122, in section 0.4, in 0.5.2, and in the
  stage 5 path table where the entry for worker/filing.py:64-65 read
  "18.2b deletes it". That table is read line by line while changing
  filing.py, so it was instructing a deletion of a function the build
  keeps. The interim in section 0.5 and its acceptance test are unchanged.

  2026-08-18_BOUNDARY_two_products.md, modified: the fourth breach found
  on 2026-08-20, being client creation living only on IntelliBooks'
  screen, Paul's resolution of it, what standalone Intellibills' own shell
  has to carry, and the settings list marked done.

  2026-08-20_LIST_outstanding_items_and_decisions.md, new and previously
  untracked: 142 items raised, 133 open, 9 closed. One of the project's
  two lists.

  2026-08-20_LIST_settings_firm_and_client.md, new: 38 rows, 30 existing
  and 8 proposed. All 18 firm settings belong to Intellibills.

  2026-08-20_NOTE_demo_version.md, new: the parked demo version.

  2026-08-21_HANDOVER_consultant_chat_9.md, new: the handover chat 8 wrote
  for chat 9.

  CLAUDE.md, modified at line 402 only: the note asking Paul to update the
  Claude project instructions is struck through, because he has.

  PROMPT_claude_code_2026-08-21_commit_110_to_126.md, this brief, and
  2026-08-21_REPORT_claude_code_commit_110_to_126.md, your report.
```

Then push. Branch `feat/console-phase0`. `git push --dry-run` first, fast-forward only, never `--force`.

---

## Verify, and quote the output

1. `git --no-optional-locks status --porcelain` returns nothing. Quote it.
2. One commit on the branch, pushed fast-forward. Confirm the parent commit.
3. Amendment numbering contiguous 1 to 126 by task 2b's method, with the boundaries printed.
4. **No `.py` file in the commit.** `git show --stat` on your own commit.
5. Section 16's table and body still agree after the commit, by task 2c.
6. Read the commit message back against `git show --stat`. **Nine files and a long message, so check every committed filename is either named or described.** The last commit of this shape had one omitted; that is the class of thing to look for.

---

## Stop and ask about

- Anything on the Destructive Git Operations list.
- **Any edit to any file.** This task stages and commits what is already there.
- Any modified `.py` file.
- Anything outside `C:\LastingImpact\receipt_capture`.
- Any write to `receipts.db`.
- Starting the pipeline.
- A push that is not a fast-forward.
- The working tree not matching task 1. **My prediction covers 66 of 170 tracked entries and I have named the 104 it does not.**

---

## Not in this commit, and do not go looking

**Do not send or act on `PROMPT_claude_code_step10a_and_10b.md`.** It was written against a folder scheme abandoned in July. It is already tracked and it is not being changed.

**Do not touch `PROMPT_intellibooks_desktop_changes.md`.** Another session's brief.

**`IntelliCharts\` and everything under `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\` are outside this repository and outside your scope.** Do not read them, add them, or reference them by path.

**Nothing in amendments 110 to 126 is built.** They are decisions and corrections to documents. **Step 10d in particular is 34 outstanding sub-steps and three unwritten briefs**, and committing the document that describes it is not starting it. Do not implement any of it, and do not present it back as a to-do list you might begin.

---

## Report to a file

`C:\LastingImpact\receipt_capture\2026-08-21_REPORT_claude_code_commit_110_to_126.md`, written before staging per task 3.

Include: the full output of task 1; all five outputs from task 2, with the line boundaries printed and the table-block counts shown; the porcelain result; and what verification step 6 returned.

**And two things I want back.**

**Was my starting-state prediction right?** It comes from `.git/index` and inflated loose objects, not from git, and it covers 66 of 170 tracked entries. Tell me what `git status` found that I did not. I compared every root-level markdown file rather than a sample, and counted CRLF rather than assuming, so if it still missed something the method needs more than that.

**And tell me whether task 2d's pipe check found anything I missed.** I fixed seven rows across two documents and then ran the check over all 72 table blocks in both. If your version finds an eighth, say which, because that would mean my check and my fix were built from the same wrong assumption.
