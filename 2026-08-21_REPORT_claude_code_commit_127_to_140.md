# Report: commit of amendments 127 to 140, and the settings list rewrite

Written 2026-08-21 by the implementation session, Claude Code, against
`PROMPT_claude_code_2026-08-21_commit_127_to_140.md`.

Documentation only. Nothing was edited, no code was touched, no test was run,
and nothing in amendments 127 to 140 was implemented.

Written before staging, so it lands in the commit it describes. The two facts
that can only exist after the commit, the clean porcelain result and
verification step 6, are in section 8 below, added in a follow-up commit on the
precedent of `f74fbca`, "docs: post-commit evidence for bf59639". That
deviation is disclosed there.

---

## 1. Task 1. The starting state

`git --no-optional-locks status --short`, quoted whole:

```
 M 2026-07-25_CONSOLE_DESIGN.md
 M 2026-07-31_PLAN_reset_and_restructure.md
 M 2026-08-20_LIST_outstanding_items_and_decisions.md
 M 2026-08-20_LIST_settings_firm_and_client.md
 M CLAUDE.md
?? PROMPT_claude_code_2026-08-21_commit_127_to_140.md
```

Five modified, one untracked. Exactly the prediction, and no `.py` file. No
`.git\index.lock` existed, so nothing was deleted.

Refs before the commit:

```
HEAD                            5a201500d2b571e7ac19e6c5490dffe9acc1bc1b
origin/feat/console-phase0      5a201500d2b571e7ac19e6c5490dffe9acc1bc1b
branch                          feat/console-phase0
```

Nothing ahead of the remote, so the push is a plain fast-forward of one commit.

### 1a. The prediction against what git found

**The file list was exactly right. All ten byte figures were exactly right.
Three of the five diff shapes were over-counted, and none of the five hunk
counts matched.**

| File | HEAD bytes | Disk bytes | Predicted +/- | git +/- | Predicted hunks | git hunks, `-U3` | git hunks, `-U0` |
|---|---|---|---|---|---|---|---|
| 2026-07-25_CONSOLE_DESIGN.md | 458,018 ok | 503,998 ok | 97 / 39 | **92 / 34** | 25 | 16 | 30 |
| 2026-07-31_PLAN_reset_and_restructure.md | 73,821 ok | 74,179 ok | 1 / 1 | 1 / 1 ok | 1 | 1 ok | 1 ok |
| 2026-08-20_LIST_outstanding_items_and_decisions.md | 63,268 ok | 69,079 ok | 31 / 24 | **29 / 22** | 11 | 9 | 12 |
| 2026-08-20_LIST_settings_firm_and_client.md | 23,592 ok | 31,974 ok | 143 / 79 | **136 / 74** | 14 | 8 | 18 |
| CLAUDE.md | 49,036 ok | 50,784 ok | 10 / 0 | 10 / 0 ok | 1 | 1 ok | 1 ok |

`git --no-optional-locks diff --numstat`, quoted whole:

```
92      34      2026-07-25_CONSOLE_DESIGN.md
1       1       2026-07-31_PLAN_reset_and_restructure.md
29      22      2026-08-20_LIST_outstanding_items_and_decisions.md
136     74      2026-08-20_LIST_settings_firm_and_client.md
10      0       CLAUDE.md
```

**The over-count is not a diff-algorithm difference.** Python's
`difflib.SequenceMatcher` on the same blob-versus-disk pair, with
`autojunk=False`, returns git's numbers to the line on all five files, and its
change-block count equals git's `-U0` hunk count on all five:

```
2026-07-25_CONSOLE_DESIGN.md                        add=92  rem=34  blocks=30
2026-07-31_PLAN_reset_and_restructure.md            add=1   rem=1   blocks=1
2026-08-20_LIST_outstanding_items_and_decisions.md  add=29  rem=22  blocks=12
2026-08-20_LIST_settings_firm_and_client.md         add=136 rem=74  blocks=18
CLAUDE.md                                           add=10  rem=0   blocks=1
```

So two independent line diffs agree with each other and neither agrees with the
prediction. On the design document and the outstanding items list the predicted
figures are 5 and 2 too high **on both sides at once**, which is the signature
of counting a run of lines as changed where both diffs see it as context. On the
settings list the miss is asymmetric, 7 added and 5 removed, so it is not the
same cause there.

**Nothing was lost or gained by it.** The byte figures came from the same
inflated blobs and are exact, and task 2 proves the content, so the miss is in
how the predicted diff was counted and not in the working tree. Confidence
high, because the byte counts and both diffs were run against the files
themselves.

**Hunk counts are not a stable measure and are best dropped from future
predictions.** The same working tree gives 16 hunks or 30 for the design
document depending only on the context setting, and neither figure is more
correct than the other. Added and removed line counts are stable, and bytes are
stable.

---

## 2. Task 2a. Amendment rows, HEAD against the working tree

Scope bounded to the amendment record's own section, and the row lines printed
with the result rather than the section lines.

```
HEAD:         section lines 26..277; numbered rows on lines 34..276;  count=126; min=1 max=126
WORKING TREE: section lines 26..293; numbered rows on lines 36..292;  count=140; min=1 max=140

only in working tree: [127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140]
only in HEAD:         []
```

Fourteen added, none deleted. Passes.

## 3. Task 2b. Contiguity, by the corrected method

Same boundaries as above, printed with the result. A list equality against
`range(first, last+1)`, plus an explicit duplicate test. No set difference
anywhere.

```
HEAD:         duplicates=[]  equals range(1,127)? True
WORKING TREE: duplicates=[]  equals range(1,141)? True
```

140 rows, no duplicates, contiguous 1 to 140. Passes.

The boundary that makes this safe is `## Amendment record` at line 26 running to
the next `## ` heading at line 293. Section 13A's findings table, numbered 1 to
8, sits at line 1452 and is outside that boundary, so it cannot be absorbed.

**A note on the stored memory for this check.** The memory file
`amendment-record-row-boundaries` says "report rows 21 to 176, not section
bounds 13 to 177". Those line numbers no longer describe the document: the rows
now run 36 to 292 inside a section running 26 to 293. The rule is right, the
numbers in it are stale, and they were recomputed from the file rather than
reused.

## 4. Task 2c. Section 16 agrees with itself, and both decompositions are complete

Section 16 bounded at lines 1614 to 1881. Head table at lines 1623 to 1660,
body steps at lines 1664 to 1876.

```
head table rows: 38    body steps: 38
table counts: BUILT 18, OUTSTANDING 18, MOVED 1, CANCELLED 1
body counts:  BUILT 18, OUTSTANDING 18, MOVED 1, CANCELLED 1
keys only in table: []
keys only in body:  []
status disagreements: {}
```

Both decompositions, matched at line starts:

```
10d: count=35  lines 1716..1768  duplicates=[]  equals range(1,36)? True
10f: count=30  lines 1800..1838  duplicates=[]  equals range(1,31)? True
```

Passes, including the 30 rather than 29 for 10f.

## 5. Task 2d. Every table row has its own header's pipe count

Header relative, counting only pipes not preceded by a backslash, blockquote
`>` prefixes stripped so tables inside quotes are not skipped.

```
2026-07-25_CONSOLE_DESIGN.md
   pipe_lines_total=325  headers=35  lines_checked=325  unattributed=[]  inconsistent_rows=0
2026-08-20_LIST_outstanding_items_and_decisions.md
   pipe_lines_total=194  headers=25  lines_checked=194  unattributed=[]  inconsistent_rows=0
2026-08-20_LIST_settings_firm_and_client.md
   pipe_lines_total=76   headers=10  lines_checked=76   unattributed=[]  inconsistent_rows=0
CLAUDE.md
   pipe_lines_total=80   headers=8   lines_checked=80   unattributed=[]  inconsistent_rows=0
```

Zero inconsistent rows in all four files, over 675 pipe lines, every one of them
attributed to a header and checked.

**Disclosure, and it matters more than the result.** The first version of this
check defined a table as a header line followed by a separator line, and stopped
at the first non-pipe line. It reported `blocks=34, inconsistent_rows=0` for the
design document and **it had silently skipped 29 of that file's 325 pipe
lines**. The amendment record is one logical table broken thirteen times by
intervening prose and blockquotes, so those thirteen fragments have no separator
line of their own, were never the start of a block, and were never compared with
anything. A pass over the rows it declined to read.

The version quoted above carries the last header's pipe count forward across the
gaps, prints `lines_checked` beside `pipe_lines_total` so the two can be seen to
be equal, and prints any line it could not attribute. That is the difference
between a check and a check that cannot fail.

**On the predicted block counts, 47 in the design document.** Three of the four
matched on the first definition tried: 25, 10 and 8. The design document does
not, and the number depends entirely on what is being counted:

| Definition | Design doc |
|---|---|
| Header immediately followed by a separator line | 35 |
| Contiguous runs of pipe lines | 48 |
| Predicted | 47 |

48 is one away from the prediction, which suggests the prediction counted
contiguous runs, but one run is unaccounted for and this session cannot say
which without the original script. **It does not affect the result**: coverage
here is measured in lines, not blocks, and all 325 were checked.

## 6. Task 2e. The outstanding items list adds up

Line 3 reads:

```
## 114 open, 30 closed, 144 raised
```

The Closed section starts at line 355 of 390.

```
open rows=114   closed rows=30   total=144
highest=144     lowest=1
numbers appearing twice anywhere: []
numbers in both open and Closed:  []
missing from 1..144:              []
closed ascending? True
```

114 plus 30 equals 144, the highest number used, no number twice, no number in
both halves, and nothing missing from the run.

**The ordering, checked here rather than taken on trust.** The Closed section is
in strictly ascending order:

```
1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 26, 53, 72, 79, 98, 99,
104, 107, 110, 129, 136, 137, 139, 142, 143, 144
```

Read out of the file in document order and compared with its own sort. The
programmatic sort held. The two misplacements caused by anchoring an insertion
on the following row are gone, and the run 1 to 14 entire sits at the head where
it belongs.

Sections 1 and 2 of that list, "Blocking a scheduled step" and "Waiting on
Paul", are each a heading, a table header and a separator with no data rows.
Empty, as claimed.

## 7. Task 2f. The settings list's own sequences

```
F: count=18  min=1  max=18  lines 76..98    duplicates=[]  equals range(1,19)? True
C: count=20  min=1  max=20  lines 119..148  duplicates=[]  equals range(1,21)? True
S: count=11  min=1  max=11  lines 168..183  duplicates=[]  equals range(1,12)? True
```

No gaps in any of the three. F18 is struck, at line 98:

```
| ~~F18~~ | ~~**Whether entities sit at the same level as the contact or
beneath it**~~ **Struck 2026-08-21 by amendment 138. It has no subject.**
```

Nine sections, `## 1` to `## 9`:

```
39:## 1. Counts
67:## 2. Firm settings
113:## 3. Client settings
152:## 4. System settings
191:## 5. What is excluded, named so the exclusion can be checked
215:## 6. What goes on the Firm Settings page
233:## 7. What the "where it is entered" column found
291:## 8. Where Client Settings should live
326:## 9. Confidence
```

17 live F rows plus 20 C rows equals the 37 live rows the commit message claims.

Passes.

---

## 8. Post-commit evidence

Added after the push, in a follow-up commit. **This is a deviation from the
brief, which asked for one commit and also asked this report to carry the clean
porcelain result and the outcome of verification step 6.** Those two facts do
not exist until the commit exists, so they cannot be inside it. The follow-up
follows the precedent already in the log, `f74fbca`, "docs: post-commit evidence
for bf59639", and it is the only way to satisfy both the clean-tree check and
the request that the evidence live in the repository rather than only in a chat.

Filled in below.

## 9. Confidence, and what was not checked

**High on everything in sections 1 to 7**, because every figure was computed
from the files themselves or from `git show HEAD:<path>`, and every list was
printed whole rather than counted from a description.

Not checked, and not claimed:

- Whether amendments 127 to 140 say what the commit message says they say. The
  checks here are structural. The substance is the consultant session's.
- Whether the cross-references renumbered behind the settings list's new
  section 4 all point at the right place. Not asked for, and not verified.
- Anything under `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\`, or
  `IntelliCharts\`. Not read, not referenced by path, out of scope.
- No test was run. No `.py` file was read or changed.
