# Report: commit amendments 110 to 126, and four untracked documents

Written 2026-08-21 by the implementation session, Claude Code, against `PROMPT_claude_code_2026-08-21_commit_110_to_126.md`.

Documentation only. No code was read for change, no test was run, no file was edited. The nine files in this commit are exactly what was already on disk, plus this report.

**Written before staging, per task 3, so it lands in the same commit.** The post-commit sections at the end were added by `git commit --amend --no-edit` on the same unpushed commit, before the push. That is disclosed because it is the only way a report inside a commit can carry the porcelain result of that commit, and because amending is a thing this project asks to be told about. The commit was not published at the time of the amend.

---

## Task 1. Starting state

`git --no-optional-locks status --short`, run first, output whole:

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

Nine entries, four modified and five untracked. **Identical to the prediction, line for line and in the same order.** No `.py` file, nothing under `worker\`, `tests\`, `docs\` or `.claude\`, and nothing outside the repository.

`.git\index.lock` does not exist. `ls -la .git/index.lock` returned `No such file or directory`, so no lock had to be cleared and no `tasklist` check was needed.

`--no-optional-locks` was used on every git read in this task, without exception.

**One wording note on the prediction, and it changes nothing.** The brief says "expect exactly four modified and five untracked. The fifth untracked is your own report, which does not exist yet". Five untracked were already present before the report was written, so the report is the sixth. The listed set is what the tree held and it is what the prediction named; only the sentence counting it is off by one.

---

## Task 2. Nothing has been lost

Five checks, all programmatic, all outputs quoted whole rather than summarised.

### 2a and 2b. Amendment rows, and contiguity by the corrected method

The HEAD copy was extracted with `git --no-optional-locks show HEAD:2026-07-25_CONSOLE_DESIGN.md` into the scratchpad, so both files were parsed by the same code.

The check bounds itself to the amendment record's own line boundaries: it finds the line equal to `## Amendment record`, then the next line starting `## `, and matches numbered rows only inside that range. It prints the boundaries with the result, asserts the list equals `range(first, last+1)`, and tests duplicates by counting occurrences. **No set difference is used anywhere in the contiguity test.**

```
=== WORKING TREE : 2026-07-25_CONSOLE_DESIGN.md ===
  amendment record line boundaries: heading at line 26, section ends at line 277 (file has 2247 lines)
  numbered rows matched: 126 ; first row at line 34 ; last row at line 276
  min=1 max=126
  duplicates: []
  equals range(1, 127): True
=== HEAD : HEAD_CONSOLE_DESIGN.md ===
  amendment record line boundaries: heading at line 16, section ends at line 189 (file has 1997 lines)
  numbered rows matched: 109 ; first row at line 24 ; last row at line 188
  min=1 max=109
  duplicates: []
  equals range(1, 110): True

=== 2a comparison ===
  only in the working tree: [110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126]
  only in HEAD           : []
```

**2a passes.** Seventeen amendments exist only in the working tree, exactly 110 to 126. The second list is empty, so no amendment has been deleted.

**2b passes.** The working tree holds 126 rows, no duplicates, equal to `range(1, 127)`. Boundaries printed: heading at line 26, section ends at line 277. That agrees with the consultant's figures. HEAD is separately contiguous 1 to 109 on the same test, which is worth having because it shows the check discriminates: the same code returns two different, correct answers on two different files.

The boundary lines are 26 and 277 in the working tree and 16 and 189 in HEAD. **Both of the pairs `CLAUDE.md` and the older notes warn are stale, 15 and 187 and 16 and 189, are HEAD-era or older**, which is why the numbers are printed rather than quoted from memory.

### 2c. Section 16's table agrees with its own body

Section 16 boundaries found the same way, and printed. Table rows are matched as `| step | text | **STATUS** |`, body steps as `N[a-z]. **STATUS.**` at the left margin, sub-steps as indented `10d.N **STATUS.**`.

```
section 16 boundaries: heading at line 1598, section ends at line 1817
table rows with a status: 38
body steps with a status: 38
10d sub-steps with a status: 34
table step ids duplicated: []
body  step ids duplicated: []
in table not in body: []
in body not in table: []
same order: True
status disagreements (step, table, body): []
status tally from the table: {'BUILT': 18, 'OUTSTANDING': 18, 'MOVED': 1, 'CANCELLED': 1}
status tally from the body : {'BUILT': 18, 'OUTSTANDING': 18, 'MOVED': 1, 'CANCELLED': 1}
total steps: table 38, body 38
10d sub-step numbers: min=1 max=34 count=34
  duplicates: []
  equals range(1, 35): True
  sub-step status tally: {'OUTSTANDING': 34}
  all OUTSTANDING: True
```

**2c passes on every part of the prediction.** 38 steps, present in both places, in the same order, with no step id duplicated and no status disagreement. 18 BUILT, 18 OUTSTANDING, 1 CANCELLED, 1 MOVED. 34 sub-steps `10d.1` to `10d.34`, contiguous with no gaps and no duplicates, every one OUTSTANDING.

Amendment 121's convention holds throughout. Only the four permitted words appear: the regex admits `BUILT`, `OUTSTANDING`, `CANCELLED` and `MOVED` and nothing else, and every one of the 38 steps and 34 sub-steps matched, so no step carries a fifth word and none is missing a status.

### 2d. Every table row has the pipe count its own header row has

Written against each table block's own header row, not against a fixed column count. A table block is a contiguous run of lines beginning with `|`, and fenced code blocks are excluded so their pipes are never read as table syntax. Pipes are counted by a character scan that skips any pipe preceded by a backslash, so `\|` is text and not a separator.

```
2026-07-25_CONSOLE_DESIGN.md
  table blocks: 47   inconsistent rows: 0

2026-08-20_LIST_outstanding_items_and_decisions.md
  table blocks: 25   inconsistent rows: 0
```

**2d passes with the predicted block counts: 47 blocks here and 25 there, 0 inconsistent in each.** Amendment 126's seven escapes hold.

**The same check was run over the other seven files in this commit, because the cost was nothing:**

```
2026-07-31_PLAN_reset_and_restructure.md      13 blocks   0 inconsistent
2026-08-18_BOUNDARY_two_products.md            1 block    0 inconsistent
CLAUDE.md                                      8 blocks   0 inconsistent
2026-08-20_LIST_settings_firm_and_client.md    7 blocks   0 inconsistent
2026-08-20_NOTE_demo_version.md                1 block    0 inconsistent
2026-08-21_HANDOVER_consultant_chat_9.md        0 blocks   0 inconsistent
PROMPT_...2026-08-21_commit_110_to_126.md       1 block    0 inconsistent
```

**And a second, independent check was written, because task 2d cannot find every instance of the fault it was written for.** Comparing a row against its own header catches a row whose column count is wrong. It cannot catch a pipe that is meant to be text but sits in a row whose count happens to agree with the header, and it cannot catch a table whose header row is itself wrong. The second check looks for the underlying fault directly: an unescaped pipe inside a backtick code span, on a line inside a table block. In GitHub-flavoured markdown a code span does not protect a pipe, so every one of those renders as an extra column.

```
2026-07-25_CONSOLE_DESIGN.md: 305 table lines scanned, 0 rows with an unescaped pipe inside a code span
2026-08-20_LIST_outstanding_items_and_decisions.md: 192 table lines scanned, 0 rows with an unescaped pipe inside a code span
2026-07-31_PLAN_reset_and_restructure.md: 127 table lines scanned, 0
2026-08-18_BOUNDARY_two_products.md: 6 table lines scanned, 0
CLAUDE.md: 80 table lines scanned, 0
2026-08-20_LIST_settings_firm_and_client.md: 56 table lines scanned, 0
2026-08-20_NOTE_demo_version.md: 9 table lines scanned, 0
2026-08-21_HANDOVER_consultant_chat_9.md: 0 table lines scanned, 0
PROMPT_...2026-08-21_commit_110_to_126.md: 7 table lines scanned, 0
```

**No eighth row.** Neither check finds anything in either of the two documents amendment 126 covered, nor in the other seven files. Answer to the consultant's second question is at the end of this report.

### 2e. The outstanding items list adds up

Both sides enumerated separately. The file is split at every `## ` heading so each numbered row is attributed to a named section and the counts can be read rather than trusted.

```
count line, line 3: ## 133 open, 9 closed, 142 raised
  parsed: open=133 closed=9 raised=142
  open + closed == raised: True

numbered rows by section (heading, first line, last line):
  L25-36    ## 1. Blocking a scheduled step                                7 rows
  L37-49    ## 2. Waiting on Paul                                          8 rows
  L50-67    ## 3. Defects flagged and not fixed                           13 rows
  L68-77    ## 4. Firm and client settings the firm cannot see or control  3 rows
  L78-91    ## 5. Decisions not taken                                      9 rows
  L92-115   ## 6. Cloud only                                               9 rows
  L116-125  ## 7. Deferred by decision                                     5 rows
  L126-205  ## 8. Found by the four-part document sweep of 2026-08-20     38 rows
  L206-253  ## 9. Found on 2026-08-21, by opening what ... had not opened 16 rows
  L254-333  ## 10. Found on 2026-08-21 by reading everything ... unread   25 rows
  L369-383  ## Closed                                                      9 rows

=== enumerated ===
open sections: 133 numbered rows
Closed section: 9 numbered rows -> [26, 53, 104, 107, 110, 129, 136, 137, 139]
duplicates within the open sections: []
duplicates within Closed: []
numbers appearing in both open and Closed: []
duplicates across the whole file: []
highest number used: 142
total distinct numbers: 142

open count matches stated 133: True
closed count matches stated 9: True
open + closed == highest number used (142): True
sequence 1..142 complete: True
missing numbers: []
```

**2e passes on every part.** The count line reads 133 open, 9 closed, 142 raised. 133 plus 9 equals 142, which is the highest number used. No number appears twice anywhere in the file, and no number appears in both the open sections and Closed. The sequence 1 to 142 is complete with nothing missing.

The section tally is printed rather than summed silently, so it can be checked by eye: 7 + 8 + 13 + 3 + 9 + 9 + 5 + 38 + 16 + 25 = 133. The Confidence section at L334-368 holds no numbered rows, so it did not contribute and did not need excluding by hand.

---

## Three things flagged, none fixed

None of these was asked about. All three were found while checking the commit message against the diffs, which the brief asked for. Per `CLAUDE.md`, they are reported and not repaired.

### Flag 1. The section number is wrong, in the commit message and in amendment 122

The commit message says the reset plan's three corrections are "in section 0.4, in 0.5.2, and in the stage 5 path table". **Amendment 122 of the design document says the same, that "its section 0.4 read 'Intellibills never writes into `Clients\` at all'".**

The corrected sentence is at `2026-07-31_PLAN_reset_and_restructure.md:30`, and line 30 is under `### 0.1 Stage 5 is much larger than "change the code, both sides"`, which begins at line 19. **Section 0.4, `### 0.4 The decisions needed before stage 3 begins`, spans lines 59 to 80 and does not contain the sentence.** Established by mapping each changed line to the nearest preceding heading programmatically:

```
line 30  is under -> 19: ### 0.1 Stage 5 is much larger than "change the code, both sides"
line 120 is under -> 106: ### 0.5.2 The frozen touchpoints
line 642 is under -> 628: ### The pipeline sites, read from the files today
```

The other two are right. 0.5.2 is right, and "the stage 5 path table" is right, being the path table under `### The pipeline sites, read from the files today` inside stage 5.

**The message was committed as dictated rather than corrected**, because the brief supplied it verbatim and a commit message cannot be changed later without rewriting history. This report is in the same commit, so the record carries its own correction. **Amendment 122 in the design document is the copy that should be corrected**, because that is the one a future session will read.

### Flag 2. A fifth instance of the struck claim, in the design document, not struck

Amendment 122 enumerated four places in the design document that carried the claim and struck all four. There is a fifth, and it is inside 18.2b itself.

`2026-07-25_CONSOLE_DESIGN.md:2040`, the amendment 75 block quote, ends: **"The simplification below is deferred, not cancelled."** The simplification below it, at line 2053, is now struck through by amendment 122 with the words "Intellibills keeps all three". So it is cancelled, not deferred, and the sentence pointing at it still says the opposite.

**What makes this more than a stray sentence is that its twin was corrected.** The reset plan's 0.5.2 read "18.2b's own list of what Intellibills loses is therefore deferred, not cancelled" and was struck through and replaced on 2026-08-21, at line 120. **The same sentence in the same words survives at the place it came from.** The correction was applied to the copy and not to the original.

### Flag 3. A fourth instance in the reset plan, deliberately excluded, and now stale for a second reason

`2026-07-31_PLAN_reset_and_restructure.md:85`, in section 0.5, reads: "This contradicts 18.2b, which says Intellibills never writes into `Clients\` at all."

The commit message says "the interim in section 0.5 and its acceptance test are unchanged", so this was left knowingly. **But it cites as current a sentence that amendment 122 struck**, at design document line 2036, and it frames the interim as a contradiction of 18.2b when under the ruling the write is permanent and correct. What still closes is the trigger, which is what 0.5.2's replacement text at line 122 now says. **So 0.5 and 0.5.2 describe the same thing two different ways in the same document.**

Enumerated rather than asserted. `grep -n "never writes into\|Intellibills loses\|18.2b deletes\|get_client_directory"` across both files returns 16 hits, printed whole. In the reset plan, lines 30 and 85 carry the "never writes" claim, 120 and 122 the "loses" claim struck and replaced, 642 the "deletes it" claim struck, and 114 and 624 are consistent with the ruling and need nothing. **So the set in that file is four claims, not three: 30, 85, 120 and 642.** Amendment 122's total of "seven across two documents" becomes nine, counting flag 2 and flag 3.

That is amendment 122's own lesson landing a third time, and it is worth saying plainly: the amendment that says "a contradiction is not established until every document that speaks to it has been enumerated" first named two places, was corrected to four, and is now nine.

---

## Task 3. The commit

Ten files staged, no more and no fewer:

```
2026-07-25_CONSOLE_DESIGN.md
2026-07-31_PLAN_reset_and_restructure.md
2026-08-18_BOUNDARY_two_products.md
CLAUDE.md
2026-08-20_LIST_outstanding_items_and_decisions.md
2026-08-20_LIST_settings_firm_and_client.md
2026-08-20_NOTE_demo_version.md
2026-08-21_HANDOVER_consultant_chat_9.md
PROMPT_claude_code_2026-08-21_commit_110_to_126.md
2026-08-21_REPORT_claude_code_commit_110_to_126.md
```

One commit, not two, per the brief's instruction and its reasoning. No hunk was staged by hand. `git add` named the ten paths and nothing else.

The message is the brief's, verbatim, with the section 0.4 error at flag 1 left in it.

### Message checked back against the file list

Every one of the ten committed filenames is either named in the message or described in it. Checked one at a time against the message text rather than by eye over the whole thing, because the brief says the last commit of this shape omitted one.

| File | Where the message accounts for it |
| --- | --- |
| `2026-07-25_CONSOLE_DESIGN.md` | Not named as a filename, but it is the subject of the whole message. Named in the second paragraph as "the design document" and its amendments 110 to 126 are itemised |
| `2026-07-31_PLAN_reset_and_restructure.md` | Named, "modified: three sentences corrected under amendment 122" |
| `2026-08-18_BOUNDARY_two_products.md` | Named, "modified: the fourth breach found on 2026-08-20" |
| `CLAUDE.md` | Named, "modified at line 402 only" |
| `2026-08-20_LIST_outstanding_items_and_decisions.md` | Named, "new and previously untracked: 142 items raised, 133 open, 9 closed" |
| `2026-08-20_LIST_settings_firm_and_client.md` | Named, "new: 38 rows, 30 existing and 8 proposed" |
| `2026-08-20_NOTE_demo_version.md` | Named, "new: the parked demo version" |
| `2026-08-21_HANDOVER_consultant_chat_9.md` | Named, "new: the handover chat 8 wrote for chat 9" |
| `PROMPT_claude_code_2026-08-21_commit_110_to_126.md` | Named, "this brief" |
| `2026-08-21_REPORT_claude_code_commit_110_to_126.md` | Named, "your report" |

**Ten of ten accounted for. Nothing omitted.**

The one that is described rather than named is the design document, and that is the right call: it is what amendments 110 to 126 are amendments to, and the message's first line names them. Worth noting because a mechanical check for "does each filename appear as a string in the message" would fail on that one file and pass on every other, which is the check that would have been run had this table not been written out.

### The message's own factual claims, spot-checked against the diffs

Three claims in the message are specific enough to be wrong, so all three were checked.

- **"`CLAUDE.md`, modified at line 402 only."** True. `git --no-optional-locks diff -U0 CLAUDE.md` shows one hunk, `@@ -402 +402 @@`, one line changed, the strike-through of the note asking Paul to update the project instructions.
- **"three sentences corrected" in the reset plan.** True as to the count and the substance. Three hunks, at lines 30, 120 and 642. The section label for the first is wrong, per flag 1.
- **"38 rows, 30 existing and 8 proposed"** in the settings list, and **"142 items raised, 133 open, 9 closed"** in the outstanding items list. The second is confirmed by check 2e above. The first was not checked; it is outside the five checks the brief asked for.

---

## Verification, after the commit

**Read this first, on the hash.** The figures below were measured against commit `e3aa7aa`, the commit created before this section was written. Adding this section and running `git commit --amend --no-edit` gives that commit a new hash, so **the hash of the commit this report sits in cannot be stated from inside it.** The parent can, and it is stable. The pre-amend hash and the final hash are both in the session reply.

### 1. The working tree is clean

`git --no-optional-locks status --porcelain`, with a marker echoed after it so an empty result is distinguishable from a command that did not run:

```
[porcelain output ended]
```

Nothing before the marker. The porcelain output is empty.

### 2. One commit on the branch, and its parent

```
commit e3aa7aa3490a839bd75eb441ea7761627b389d92
parent 3e7592dd2c1d135e982d6e019c6195efbcca55ec
subject docs: amendments 110 to 126, section 16 made readable, and the two lists tracked
```

`git --no-optional-locks log --oneline -3`:

```
e3aa7aa docs: amendments 110 to 126, section 16 made readable, and the two lists tracked
3e7592d docs: amendment 109, the date correction, and consultant handover 8
4981f48 docs: amendments 101 to 108, and the boundary between two products
```

**The parent is `3e7592d`, which is what HEAD was at task 1.** One commit, sitting directly on the previous documentation commit, with nothing interleaved.

`git push --dry-run origin feat/console-phase0`:

```
To https://github.com/Impact-sys-pk/receipt-capture.git
   3e7592d..e3aa7aa  feat/console-phase0 -> feat/console-phase0
```

**A fast-forward.** The range separator is `..` and not `...`, there is no leading `+`, and no `forced update` marker. `--force` was not used at any point.

### 3. Amendment numbering still contiguous, after the commit

2b's method re-run against the committed file, boundaries printed with the result:

```
=== WORKING TREE : 2026-07-25_CONSOLE_DESIGN.md ===
  amendment record line boundaries: heading at line 26, section ends at line 277 (file has 2247 lines)
  numbered rows matched: 126 ; first row at line 34 ; last row at line 276
  min=1 max=126
  duplicates: []
  equals range(1, 127): True
```

Contiguous 1 to 126, no duplicates, boundaries 26 and 277, unchanged by the commit.

### 4. No `.py` file in the commit

`git --no-optional-locks show --stat HEAD`, quoted whole:

```
 2026-07-25_CONSOLE_DESIGN.md                       | 330 +++++++++++++++---
 2026-07-31_PLAN_reset_and_restructure.md           |   8 +-
 2026-08-18_BOUNDARY_two_products.md                |  23 +-
 2026-08-20_LIST_outstanding_items_and_decisions.md | 383 +++++++++++++++++++++
 2026-08-20_LIST_settings_firm_and_client.md        | 304 ++++++++++++++++
 2026-08-20_NOTE_demo_version.md                    | 167 +++++++++
 2026-08-21_HANDOVER_consultant_chat_9.md           | 201 +++++++++++
 2026-08-21_REPORT_claude_code_commit_110_to_126.md | 318 +++++++++++++++++
 CLAUDE.md                                          |   2 +-
 PROMPT_claude_code_2026-08-21_commit_110_to_126.md | 253 ++++++++++++++
 10 files changed, 1940 insertions(+), 49 deletions(-)
```

Ten files, and every one of the ten ends `.md`. Checked programmatically rather than by eye, twice, because reading a ten-line list and calling it clean is the kind of check that never fails:

- `git show --name-only --format="" HEAD | grep -c "\.py$"` returns `0`.
- `git show --name-only --format="" HEAD | grep -v "\.md$"` returns nothing at all, which is the stronger statement: not just no `.py`, but no file of any other kind either.

The report's own line count in that diffstat is 318, measured before this section was appended. The amend raises it. That is the one figure in this section the amend invalidates, and it is stated rather than left to be noticed.

### 5. Section 16's table and body still agree, after the commit

2c re-run against the committed file:

```
section 16 boundaries: heading at line 1598, section ends at line 1817
table rows with a status: 38
body steps with a status: 38
10d sub-steps with a status: 34
table step ids duplicated: []
body  step ids duplicated: []
in table not in body: []
in body not in table: []
same order: True
status disagreements (step, table, body): []
status tally from the table: {'BUILT': 18, 'OUTSTANDING': 18, 'MOVED': 1, 'CANCELLED': 1}
status tally from the body : {'BUILT': 18, 'OUTSTANDING': 18, 'MOVED': 1, 'CANCELLED': 1}
total steps: table 38, body 38
10d sub-step numbers: min=1 max=34 count=34
  duplicates: []
  equals range(1, 35): True
  sub-step status tally: {'OUTSTANDING': 34}
  all OUTSTANDING: True
```

Byte for byte the same output as the pre-commit run at 2c. The commit changed nothing.

### 6. The message read back against the file list

Done, in the table under task 3 above. **Ten of ten accounted for, nothing omitted.** The one file described rather than named is the design document, which is what amendments 110 to 126 amend.

## The two questions

### Was the starting-state prediction right?

**Yes, exactly, and `git status` found nothing the prediction did not.** Nine entries, four modified and five untracked, the same nine paths in the same order. No `.py` file appeared, and none of the 104 tracked entries the prediction did not cover turned up modified.

Worth being precise about what that does and does not prove. It confirms the prediction; it does not fully validate the method, because the method's stated blind spot is the 104 CRLF-normalised entries and the answer for those came back "no change", which is the result a blind spot returns when there is nothing to see. Had one of those files been modified, the method would have missed it and `git status` would have caught it. This run cannot tell the two apart.

**One thing the method got that a size comparison would not have.** Counting CRLF rather than assuming is what made the 66-file byte comparison sound, and it is the reason the prediction could be stated as a byte-for-byte match rather than as a guess. That part of it held.

**And one off-by-one in the prose, not in the method:** the brief says the fifth untracked file is the report, and five untracked files existed before the report was written. The set was right; the sentence counting it was not.

### Did task 2d's pipe check find an eighth?

**No, and a second, differently-shaped check did not either.**

Task 2d as specified, header-relative and backslash-aware, returns 0 inconsistent rows across 47 blocks in the design document and 25 in the outstanding items list, both counts matching the prediction. Run over the other seven files in this commit it returns 0 across a further 31 blocks.

Because a check that only compares a row against its own header has a blind spot, a second check was written against the fault itself: an unescaped pipe inside a backtick code span, anywhere in a table line. That is the shape all seven of amendment 126's faults had. It scans 497 table lines across the two documents and 285 across the other seven, and finds nothing.

Amendment 94's already-escaped pipe, inside the `grep -n "for email_msg in\|for msg in"` pattern, is correctly not flagged by either check. It is the case the consultant's first version over-reported, and it is the one worth confirming, because a check that no longer over-reports there is a check that could have started under-reporting elsewhere. It has not: both checks still find the fault when the escape is absent, which is why the second check was written to look for the fault directly rather than for its symptom.

**So the answer is that the seven were the seven.** No evidence here that the check and the fix were built from the same wrong assumption.

---

## Confidence

**High that nothing was lost.** Every claim in this report rests on output that was printed whole and is quoted whole. The amendment comparison parsed HEAD and the working tree with one piece of code, and the only difference is the seventeen new rows.

**High on the three flags.** Each was established by mapping lines to headings programmatically or by grepping both files and printing every hit, not by reading a summary. Flag 1 in particular was found by checking the commit message against the diff, which is the step the brief asked for and the reason it asked for it.

**Moderate on the completeness of the flags.** Three stale sentences were found while checking three specific claims in the commit message. The design document is 2,247 lines and no sweep of it was asked for or run, so there may be more. The pattern is clear enough to state: amendment 122's set has grown from two to four to nine, and each growth came from someone grepping rather than reading.

**No pipeline was started, no database was touched, no file outside the repository was read or written, and no `.py` file was staged.**
