# AUTOMATIC task: commit amendments 101 to 108 and the boundary document

**Written 2026-08-18 by the consultant session, for Claude Code. Paste this whole file in.**

Runs under AUTOMATIC Task Mode in `CLAUDE.md`. Its "stop and ask" list is unchanged and outranks this file.

Documentation only. No code, no tests, nothing edited by you. Write your report, then one commit, a push, a verification.

---

## Why

`2026-07-25_CONSOLE_DESIGN.md` carries **eight uncommitted amendments, 101 to 108**, and two version-header moves. Two new documents are untracked, one of which is now an authority above the design document itself. Amendments 101 and 102 have been sitting since 16:11; the rest were written this evening.

---

## Read this before task 1: what I verified, and what I could not

This consultant session has no shell on Paul's machine. I read the repository's own files instead, checking each git object's SHA-1 against its own filename before trusting it.

| Read from | Result |
|---|---|
| `.git/refs/heads/feat/console-phase0` | `055a6167f595b5d651ddbb2b56d0afd29821696e` |
| `.git/index` | version 2, **165 entries** |
| index entry for the design document | blob `092489b0b1419c238165c1eee44642e5b727aea3`, **350,596 bytes** |
| the working tree file | **371,192 bytes** |

**I inflated that blob and diffed it.** The real numbers, which you should get from `--numstat`:

```
15 added, 2 removed
```

Four hunks, and nothing else in the file differs:

| Hunk | What |
|---|---|
| `4c4,6` | version header: 1.9 replaced by 1.11, with 1.10 and 1.9 struck through beneath |
| `176a179,186` | **eight amendment rows, 101 to 108** |
| `1958c1968` | one row of section 18.9's cancellation table amended in place |
| `1962a1973,1975` | **three rows added** to that table |

**Untracked, confirmed absent from the index:**

- `2026-08-18_BOUNDARY_two_products.md`, 12,158 bytes
- `PROMPT_intellibooks_2026-08-18_menu_and_duplicates.md`, 6,055 bytes
- this brief

**Confirmed clean:** `2026-08-18_REPORT_claude_code_drop_legacy_vendor_mappings.md` and `PROMPT_claude_code_2026-08-18_drop_legacy_vendor_mappings.md`, both matching the index byte for byte.

**What I could not do, stated plainly: I did not enumerate the whole working tree.** I compared five of 165 tracked files. A blanket size comparison is not valid here, because `.gitattributes` is `* text=auto eol=lf` and every `.py` file is stored LF and held CRLF on disk, so sizes differ by design on about thirty files. **Task 1 is therefore a real gate, and its expected output is a prediction rather than a measurement.**

The markdown files carry no CRLF, which is why the design document's diff is clean.

---

## Task 1. Confirm the starting state

```
git --no-optional-locks status --short
```

Expect exactly one modified and three untracked:

```
 M 2026-07-25_CONSOLE_DESIGN.md
?? 2026-08-18_BOUNDARY_two_products.md
?? PROMPT_claude_code_2026-08-18_commit_boundary_and_101_to_108.md
?? PROMPT_intellibooks_2026-08-18_menu_and_duplicates.md
```

**Stop and report on anything else**, in particular any `.py` file, and in particular `CLAUDE.md`, which I have not touched and which was byte-identical to its blob this afternoon.

Use `--no-optional-locks` for every read. Plain `git status` takes a lock the shell cannot release.

If `.git\index.lock` exists, check `tasklist /FI "IMAGENAME eq git.exe"` reports no tasks, then `del .git\index.lock`.

---

## Task 2. Prove nothing has been lost, before staging

Four checks, all programmatic, all quoted in your report.

**a. Amendment rows.** Compare the numbered rows of the amendment record in HEAD against the working tree. Expect **only in the working tree `[101, 102, 103, 104, 105, 106, 107, 108]`, only in HEAD empty**. A non-empty second list means an amendment has been deleted and you stop.

**b. Contiguity, by the corrected method.** Bound the scope to the amendment record's own line boundaries, print those boundaries with the result, assert the list equals `range(first, last+1)`, and test duplicates explicitly. **Never a set difference.**

I ran this on the working tree. **State the boundaries the way you taught me to, because it says what was actually counted:** the `## Amendment record` heading is at line **15**, the section ends at line **187**, and **the numbered rows themselves run line 23 to line 186**. 108 rows, no duplicates, equals `range(1,109)`.

**Note that these boundaries have moved twice today**, because both version-header edits added lines above them. Anything quoting 13 and 177, or 14 and 180, is stale.

**c. The diff is the four hunks and nothing else.**

```
git --no-optional-locks diff --numstat -- 2026-07-25_CONSOLE_DESIGN.md
```

Must report **15 added, 2 removed**. Then confirm the four hunks above and no others.

**d. Cell count on the eight new rows.** Each must have **six** cells when split on the pipe, matching row 100. A row with the wrong count renders as broken markdown and is the easiest thing to get wrong in a table this wide.

---

## Task 3. Write the report, then one commit

**Write the report before staging**, so it lands in the same commit. Path and contents are at the end of this file. It will appear as a fifth untracked file, which is expected and is not a reason to stop.

```
git add 2026-07-25_CONSOLE_DESIGN.md 2026-08-18_BOUNDARY_two_products.md PROMPT_intellibooks_2026-08-18_menu_and_duplicates.md PROMPT_claude_code_2026-08-18_commit_boundary_and_101_to_108.md 2026-08-18_REPORT_claude_code_commit_boundary_and_101_to_108.md
```

Message:

```
docs: amendments 101 to 108, and the boundary between two products

2026-08-18_BOUNDARY_two_products.md is new and is an authority above the
design document on one question only: which of the two products a thing
belongs to. Where the two disagree it decides and the design document is
corrected. Its home in this repository is provisional and it says so,
because this is Intellibills' repository and the document governs both
products, which is the same category error it exists to prevent.

101: the console has no implemented reader for the master chart, and the
fallback it stood on is now empty. Not fixed; the fix is a CSV reader.

102: amendment 97's 4200 finding is closed. The fix takes the direction of
a figure from the SA103F box rather than from the account's type.

103: two products. Intellibills sellable standalone, IntelliBooks never
sold alone. The boundary: Intellibills owns the document and everything
read from it, IntelliBooks owns the books. The rule: no function may live
only in the other product. An earlier form of the boundary said it was the
publish step and is recorded as rejected, because it equated "after
publish" with "bookkeeping" and those are not the same.

104: the publish step and the inbox. One destination per client held on the
client record, each destination's address held separately. One inbox
folder, not one per client, with the client identity inside the item. One
JSON file per receipt with the image embedded, written by temp-and-rename.
Drain on opening a client, plus a manual control with a waiting count.

105: one client registry owned by Intellibills, and four fields where there
were seven overlapping ones: client_id, client_name, client_folder_name and
capture_token. There is no client_code. business_type becomes trade and
clientType becomes entity_type. Firm level implemented now.

106: the copy into Clients\ becomes Intellibills' own function with two
triggers set per firm, on successful publish or at Post. One writer, so
fileReviewReceipt() stops writing there. The Review queue stops touching
the pipeline's folders. The Post write and the handoff closure land
together.

107: semantic duplicates. Detected on the extracted values rather than the
file hash, routed to Review and never published; the client folder handles
its own name collision; duplicates marked as such on the Receipts tab; and
deleting one removes its copy from the client folder, logged. Review and
stop, not warn and proceed, because no warning mechanism exists.

108: settings given a structure. Firm Settings and Client Settings, each
with Intellibills and IntelliBooks sub-headings, and no system level on any
page. Bank Accounts, Categories and Learned Statement Rules are not
settings and their tab is renamed Client Data.

Section 18.9's cancellation table corrected and extended. Its row about
Intellibills writing into Clients\ was amended rather than contradicted,
because what is cancelled is writing on arrival and not writing at all.
Three rows it was missing were added: fileReviewReceipt() as a second
writer, the Review queue's three crossings, and client_code as a field.

Also committed, untracked until now:

  PROMPT_intellibooks_2026-08-18_menu_and_duplicates.md, the Desktop brief
  for the menu groups, the Client Data rename, an empty Firm Settings page,
  and marking possible duplicates. It records two decisions taken and
  withdrawn the same day.
```

Then push. Branch `feat/console-phase0`. `git push --dry-run` first, fast-forward only, never `--force`.

---

## Verify, and quote the output

1. `git --no-optional-locks status --porcelain` returns nothing. Quote it.
2. One commit on top of `055a616`, pushed fast-forward. Confirm the parent.
3. Amendment numbering contiguous 1 to 108 by task 2b's method, with the boundaries printed.
4. **No `.py` file in the commit.** `git show --stat` on your own commit.
5. `git diff HEAD~1 -- 2026-07-25_CONSOLE_DESIGN.md` shows the four hunks and nothing else.
6. Read the commit message back against `git show --stat` and `git diff HEAD~1`, and report what that found. **Five files in this commit and a long message, so check every committed filename is either named or described. Last time this check found a filename the message omitted; that is the class of thing to look for.**

---

## Stop and ask about

- Anything on the Destructive Git Operations list.
- **Any edit to any file.** This task stages and commits what is already there.
- Any modified `.py` file.
- `CLAUDE.md` appearing as modified.
- Anything outside `C:\LastingImpact\receipt_capture`.
- Any write to `receipts.db`.
- Starting the pipeline.
- A push that is not a fast-forward.
- The working tree not matching task 1. **My prediction rests on five files out of 165 and I have said so.**

---

## Not in this commit, and do not go looking

**`IntelliCharts\`** is outside this repository and outside your scope. Do not read it, add it, or reference it by path.

**The IntelliBooks Desktop work briefed in `PROMPT_intellibooks_2026-08-18_menu_and_duplicates.md`** is for a different session. Committing the brief is not starting the work.

**The settings list** named as outstanding in the boundary document has not been produced. Do not produce it.

**And nothing in amendments 103 to 108 is built.** They are decisions, recorded so they are not lost. Do not implement any of them, and do not report them as outstanding work in a way that reads as a to-do list you might start.

---

## Report to a file

`C:\LastingImpact\receipt_capture\2026-08-18_REPORT_claude_code_commit_boundary_and_101_to_108.md`, written before staging per task 3.

Include: the full output of task 1; all four outputs from task 2, with the line boundaries printed and the cell counts shown; the porcelain result; and what verification step 6 returned.

**And one thing I want back.** My starting-state prediction in task 1 comes from `.git/index` and one inflated blob, not from git, and it covers five files out of 165. **Tell me whether it was right.** Last time it missed one untracked file because my directory listing was ninety minutes stale; this time I listed the folder immediately before writing. If it missed something again, that tells us the method needs more than a fresh listing.
