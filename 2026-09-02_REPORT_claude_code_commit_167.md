# Report: commit brief 167, amendments 166 to 169

**Written 2026-09-02 by Claude Code, at 13:14 BST.** Working from `PROMPT_claude_code_2026-09-02_commit_167.md`.

**The working tree matched task 1 exactly**, nine lines, six modified, two deleted, one untracked, and `Backups/` gone from the status. All eight checks in task 2 pass. Both parts of task 3 pass. **Every one of the six predicted disk blob hashes was right, and every one of the six MD5s.**

**Three findings, all in the brief's own figures rather than in the documents**, and none of them changes an assertion the brief made about the content. They are at the end of each task section and summarised in "What the brief got wrong".

---

## Task 1. The starting state

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

**Exactly the nine lines predicted, and nothing else. No `.py` file is modified**, and no tracked path outside those eight differs from HEAD.

### `Backups/` is ignored

```
$ git --no-optional-locks check-ignore -v Backups/
.gitignore:12:Backups/	Backups/
(exit 0)
```

**Exit 0, and the rule is at `.gitignore:12` as predicted.** Line 12 is the last line of the file, and the whole file reads:

```
     1	.env
     2	.token_cache.json
     3	data/
     4	__pycache__/
     5	*.pyc
     6	*.pyo
     7	.venv/
     8	venv/
     9	.history/
    10	logs/
    11	.claude/settings.local.json
    12	Backups/
```

### The six modified files. All twelve blob hashes and all twelve byte counts match

`git hash-object` on the working tree, and the blob ids out of commit `81aec08`'s tree:

| File | HEAD blob at 81aec08 | HEAD bytes | Disk blob now | Disk bytes | Predicted |
|---|---|---|---|---|---|
| `2026-07-25_CONSOLE_DESIGN.md` | `a67a58bc0b57cdb8e1f8201929537545e538350b` | 593,752 | `247739c9ab5b53e97bf7212dcce2bbea74a76075` | 611,684 | exact |
| `2026-08-03_NOTE_chart_of_accounts_for_paul.md` | `153c5beb6cf7e6b6d14211ed398e197581092601` | 8,891 | `9f9627371c9faf6fdbfd3538f941b4eb2ba19304` | 9,467 | exact |
| `.gitignore` | `e8083e4be42c10f1a8ab0c350c3669432ed9e07e` | 110 | `c6ec49e6d27f17722d170bd6c28351e55872dec6` | 120 | exact |
| `PROMPT_claude_code_2026-09-01_step10d_pipeline.md` | `21c1287c1ee865bcf3ab1f0ddfc6a3c600b0fbd3` | 28,150 | `d9b81266262e35990d5d81794741aaf373095034` | 33,470 | exact |
| `PROMPT_intellibooks_2026-09-01_step10d_desktop.md` | `a5d4647aeec741a009e8297d3a31b4b3e2b32742` | 20,496 | `5959a0eb00b523851104e7fa58b1f03c79a43e8b` | 22,458 | exact |
| `PROMPT_phoneapp_2026-09-01_step10d.md` | `b7cefaabc626930d0fb8128536fca5fd329255aa` | 18,769 | `2a57ed46423b38af171b47917dec72630e8747b7` | 18,949 | exact |

**All six disk blob hashes are right.** They were computed in the consultant session as `sha1("blob " + length + NUL + bytes)` over bytes read back off Paul's machine, not by running `git hash-object`, so they were a genuine prediction and every one held.

### MD5, hashed on Paul's machine. All six match

```
ca3441a9d34c5a0841d7b3800c1ebc1e *2026-07-25_CONSOLE_DESIGN.md
94fd5bbd2f696e5c3756a69f0867b2f3 *2026-08-03_NOTE_chart_of_accounts_for_paul.md
0dabd50c7169e05376c9d6f52fad33af *.gitignore
2a92d0d47c40f65bb9899f8ce6dd87ee *PROMPT_claude_code_2026-09-01_step10d_pipeline.md
bfa7c26b0f371a6fb488c5df9a98465e *PROMPT_intellibooks_2026-09-01_step10d_desktop.md
ed493281198f9976f119b79d6df38285 *PROMPT_phoneapp_2026-09-01_step10d.md
```

### Line endings. Zero CRLF in all six, counted at byte level

```
2026-07-25_CONSOLE_DESIGN.md                         bytes=611684  CRLF=0  bareCR=0  LF=2484  trailingNL=True
2026-08-03_NOTE_chart_of_accounts_for_paul.md        bytes=9467    CRLF=0  bareCR=0  LF=113   trailingNL=True
.gitignore                                           bytes=120     CRLF=0  bareCR=0  LF=12    trailingNL=True
PROMPT_claude_code_2026-09-01_step10d_pipeline.md    bytes=33470   CRLF=0  bareCR=0  LF=318   trailingNL=True
PROMPT_intellibooks_2026-09-01_step10d_desktop.md    bytes=22458   CRLF=0  bareCR=0  LF=250   trailingNL=True
PROMPT_phoneapp_2026-09-01_step10d.md                bytes=18949   CRLF=0  bareCR=0  LF=245   trailingNL=True
```

### The two deletions

Both absent from disk, both reachable in `81aec08`:

```
$ ls chart_of_accounts_DRAFT.csv chart_of_accounts_DRAFT2_2026-08-03.csv
ls: cannot access 'chart_of_accounts_DRAFT.csv': No such file or directory
ls: cannot access 'chart_of_accounts_DRAFT2_2026-08-03.csv': No such file or directory

46c04a03d11c3dd718243c83592614e5f749e38d 1504 bytes  type=blob
0dd8a06d012416f3d7273313d81fd40c27f0a586 8583 bytes  type=blob
```

**1,504 and 8,583, confirming the brief's account of the 8,583-versus-8,626 difference**: 8,583 is the blob and 8,626 was the working-tree size cached in `.git\index`, the 43 bytes being the CRLF line endings that `.gitattributes`'s `* text=auto eol=lf` normalises out.

### Finding 1. The root markdown count in the brief is one out, on both figures

The brief says "The root holds 86 markdown files: 85 tracked, and this brief. All 85 became tracked in `81aec08`. Your report makes 87."

**Measured: 87 on disk, 86 tracked, 1 untracked.** Cross-checked three independent ways:

```
tracked root md via git ls-files : 86
disk root md via os.listdir      : 87
root .md entries in tree 81aec08 : 86
root .md entries in tree 10fd03f : 78
```

78 at the parent plus the 8 files `81aec08` newly added gives 86, not 85. **So this report makes 88, not 87.** Same class of error as the step 10h figure history that amendments 165 and 167 are about: a root count asserted without enumerating it.

---

## Task 2. Nothing lost

### 2a. Amendment rows, HEAD against the working tree

```
working tree count: 169  HEAD count: 165
only in working tree: [166, 167, 168, 169]
only in HEAD        : []
```

**Pass.** All four new, none deleted.

### 2b. Contiguity, by amendment 97's corrected method

Scope bounded to the amendment record's own line span, from `## Amendment record` to the next top-level heading. Boundaries printed with the result, list compared against `range(first, last+1)` element by element, duplicates tested separately. No set difference anywhere.

```
DISK boundaries: record_heading=35, next_heading=372, first_row=45, last_row=370
  "## How to use this document" line: [372]
  rows matched: 169  first: 1  last: 169
  duplicates: []
  equals range(1,170): True

HEAD boundaries: record_heading=32, next_heading=350, first_row=42, last_row=348
  rows matched: 165  first: 1  last: 165
  duplicates: []
  equals range(1,166): True
```

**Pass, and the brief's boundaries are exact:** record bounded to 35 to 371, first row 45, last row 370, `## How to use this document` at 372.

**The version header.** One live version line, `**Version:** 1.29, amended 2026-09-02`, at line 4. **25 struck version lines**, and 1.26, 1.27 and 1.28 are all struck with "Superseded by" notes. No superseded version line is live.

### Finding 2. Two of the three version-block line numbers in the brief are one out

The brief says "`### v1.27` is at line 352, `### v1.28` at 358 and `### v1.29` at 365."

```
347:### v1.26, 2026-09-01
353:### v1.27, 2026-09-02
359:### v1.28, 2026-09-02
365:### v1.29, 2026-09-02
```

**v1.27 is at 353 and v1.28 at 359. v1.29 at 365 is right.** Printed with true line numbers off the file. The blocks are a uniform six lines apart, 347, 353, 359, 365, so the brief's three figures are not mutually consistent with any single offset: two are one early and the third is exact. Nothing follows from it for the contiguity check, which bounds its own scope and passed.

### 2c. Section 16 agrees with itself

Section 16 bounded to lines 1696 to 2058.

```
head table steps: 38
head table statuses: {'BUILT': 18, 'OUTSTANDING': 18, 'MOVED': 1, 'CANCELLED': 1}
body steps found: 38
in head not body: []
in body not head: []
status disagreements head vs body: []
```

**Pass.** 38 steps, identical sets, 18/18/1/1, unchanged by this commit.

```
10d: 58 sub-steps, max=58 contiguous_from_1=True gaps=[] dupes=[] statuses={'OUTSTANDING': 58}
10e: 15 sub-steps, max=15 contiguous_from_1=True gaps=[] dupes=[] statuses={'OUTSTANDING': 9, 'BUILT': 6}
10f: 30 sub-steps, max=30 contiguous_from_1=True gaps=[] dupes=[] statuses={'OUTSTANDING': 30}
10g: 10 sub-steps, max=10 contiguous_from_1=True gaps=[] dupes=[] statuses={'OUTSTANDING': 10}
```

**Pass.** 58, 15, 30, 10, all contiguous from 1, no gaps, no duplicates, every sub-step carrying a status word. 10e is 6 BUILT and 9 OUTSTANDING; the other three wholly OUTSTANDING.

**The word-boundary status pattern was used, not a string pattern**, and all six of 10e's BUILT sub-steps matched across their three shapes:

```
line 1938: 10e.3  **BUILT 2026-08-31.** ...
line 1939: 10e.4  **BUILT 2026-08-31.** ...
line 1940: 10e.5  **BUILT 2026-08-31. Nothing moved, which is the requirement.** ...
line 1942: 10e.7  **BUILT 2026-08-31.** ...
line 1943: 10e.8  **BUILT 2026-08-31.** ...
line 1951: 10e.13 **BUILT 2026-08-31**, as part of 10e.7 rather than on its own ...
```

**10d's counts agree in all three places.** The head-table row at line 1725 reads `| 10d | One client registry, the phone app credential and its settings model, 58 sub-steps | **OUTSTANDING** |`; the body has 58 sub-step headings; and the step's own preamble at line 1794 reads `**58 sub-steps.** ~~52 sub-steps.~~ **Corrected 2026-09-02 by amendment 169, which added 10d.53 to 10d.58.**`

**Section 16's head line states no sub-step total.** It now reads "Below the table, four steps are decomposed into sub-steps: 10d, 10e, 10f and 10g. No sub-step total is stated here, by amendment 166. Six sub-steps are BUILT and every other sub-step of those four steps is OUTSTANDING." Both removed figures are struck on the same line.

### 2d. The removed figures are struck, not deleted

Definition: **live count** is occurrences remaining after every `~~...~~` span is removed; **total** is occurrences in the raw file, strikes included.

| Needle | File | Live | Total | Struck spans |
|---|---|---|---|---|
| `105 sub-steps` | design | 0 | 2 | 2 |
| `52 sub-steps` | design | 0 | 1 | 1 |
| `80 markdown files` | design | 0 | 1 | 1 |
| `nine of its fifteen` | design | 2 | 3 | 1 |
| `is kept as the record` | design | 0 | 1 | 1 |
| ``Extend `chart_of_accounts_DRAFT.csv` `` | design | 0 | 1 | 1 |
| `the only other site` | design | 0 | 1 | 1 |
| `Desktop's six` | design | 0 | 0 | 0 |
| `flip them in 10c` | design | 0 | 1 | 1 |
| `untouched and stays` | note | 0 | 1 | 1 |
| `Companion to` | note | 0 | 1 | 1 |

**Nine of the eleven are zero live with a strike behind them, exactly as the brief predicted. Two needed a qualification, and both resolve in the brief's favour on substance.**

**`nine of its fifteen`, 2 live.** Both are inside amendments 166's and 167's own rows, at lines 357 and 363, quoting the phrase to record what was struck. The brief anticipated this in its own parenthetical. Re-run with lines 353 to 371 excluded, being the v1.27 to v1.29 blocks:

```
nine of its fifteen, live, EXCLUDING amendment 166-169 blocks (lines 353-371): 0
```

**`Desktop's six`, total 0.** The string does not exist in the file in any form, struck or live, so a zero live count proves nothing on its own. **The reason is that the strike is inside the phrase.** Line 1783 reads:

```
... are Paul's and are open.** Desktop's ~~six~~ **nine** `getDir(["Clients", ...])` sites change
in the same window, **at `IntelliBooks-Desktop-v3.html` lines 703, 116...
```

So `six` is struck as a one-word span and `Desktop's ` sits outside it. **The correction was made and the trail is kept**, which is what the check was for. I confirmed it discriminates rather than taking it on trust: the same needle counts **1 live** in the HEAD blob at `81aec08`, where the line read "Desktop's six `getDir([\"Clients\", ...])` sites change in the same window". So the check went 1 to 0 and the change is real; the needle was simply written across a strike boundary.

**The struck span each needle now sits in:**

```
'105 sub-steps'  -- 2 spans
  line  357: ~~105 sub-steps: 6 BUILT and 99 OUTSTANDING.~~
  line 1700: ~~Below the table, 105 sub-steps: 6 BUILT and 99 OUTSTANDING.~~

'52 sub-steps'  -- 1 span
  line 1794: ~~52 sub-steps.~~

'80 markdown files'  -- 1 span
  line  344: ~~**And step 10h's file count is corrected to 80 markdown files, 17 staying and 63
             moving**, the seventeenth being the new document.~~

'nine of its fifteen'  -- 1 span
  line 1700: ~~because nine of its fifteen sub-steps are~~

'is kept as the record'  -- 1 span
  line 1271: ~~`chart_of_accounts_DRAFT.csv` is kept as the record of what the vendor mappings
             produced, per amendment 82's rule that history keeps its old values.~~

'Extend `chart_of_accounts_DRAFT.csv`'  -- 1 span
  line 2096: ~~Extend `chart_of_accounts_DRAFT.csv` with income, equity and remaining balance
             sheet accounts.~~

'the only other site'  -- 1 span
  line 1783: ~~On the pipeline side this is small: `get_client_directory()` at
             `worker/filing.py:64` is the single choke point, and the only other site is the
             `*/Review` glob at `filing.py:297`.~~

"Desktop's six"  -- 0 spans; the strike is inside the phrase, see above
  line 1783: Desktop's ~~six~~ **nine** `getDir(["Clients", ...])` sites

'flip them in 10c'  -- 1 span
  line 1783: ~~and flip them in 10c when there is nothing on disk to migrate.~~

'untouched and stays'  -- 1 span  (2026-08-03_NOTE_chart_of_accounts_for_paul.md)
  line    5: ~~`C:\LastingImpact\receipt_capture\chart_of_accounts_DRAFT.csv` is untouched and
             stays as the record of what the vendor mappings produced.~~

'Companion to'  -- 1 span  (2026-08-03_NOTE_chart_of_accounts_for_paul.md)
  line    3: ~~Companion to `C:\LastingImpact\receipt_capture\chart_of_accounts_DRAFT2_2026-08-03.csv`.~~
```

**Nothing was deleted where it should have been struck.** Every needle with a live count of zero has a struck span holding it, and the one exception has the strike one word narrower than the needle.

### The `_Receipts` family, and Finding 3

**22 live occurrences across the six names, matching the brief's total exactly.** Enumerated per name rather than taken from the brief:

| Name | Live | Total | Live lines |
|---|---|---|---|
| `_Receipts` | 5 | 8 | 118, 135 (x2), 369, 1517 |
| `_Statements` | 5 | 9 | 135 (x3), 145, 2456 |
| `_Review` | 3 | 4 | 118, 135, 1541 |
| `_Handover Pack` | 2 | 3 | 118, 135 |
| `_HMRC Summaries` | 2 | 3 | 118, 135 |
| `_IntelliBooks` | 5 | 7 | 118, 135, 1511, 2202, 2456 |

**13 of the 22 are inside the amendment record**, lines 35 to 371, at rows 118, 135, 145 and 369. Those are amendment rows recording the superseded decision and are correct where they are.

### Finding 3. The body occurrences are six across five lines, not five across four

The brief says "I checked all five body occurrences individually, at lines 1511, 1517, 2202 and 2456", which is four line numbers for five occurrences.

**Enumerated: six body occurrences on five lines. Line 1541 is not in the brief's list, and line 2456 carries two names.**

```
live occurrences in BODY text (outside the amendment record): 6
   _Receipts          line 1517
   _Statements        line 2456
   _Review            line 1541
   _IntelliBooks      line 1511
   _IntelliBooks      line 2202
   _IntelliBooks      line 2456
```

This is CLAUDE.md's own rule: a claim about a set is not verified by verifying its members, and the tell is "the" in front of a plural. "All five body occurrences" is six.

**My judgement on each, having read all six and the nearest heading above each.** I agree with the brief that none is a live instruction, but two are weaker than the other four.

| Line | Name | Section | Verdict |
|---|---|---|---|
| 1511 | `_IntelliBooks` | `## 13A. File reconciliation` | **Superseded record, explicit.** Inside a blockquote opening "this section cannot be built as written", which names `Clients\*\_IntelliBooks\` as the scope that is wrong and ends "Rewrite the findings against 18.2a and 18.2b before building any of this". |
| 1517 | `_Receipts` | `### 13A.1 What it is for` | **Superseded record, by inheritance only. The weakest of the six.** The bullet reads as a plain present-tense fact about where a receipt can be dropped, and nothing on the line itself marks it. It is protected solely by the warning four lines above and by step 10b being MOVED. |
| 1541 | `_Review` | `### 13A.3 The checks` | **Superseded record, by inheritance only.** A check-definition table row, same protection as 1517 and the same weakness. This is the one the brief did not enumerate. |
| 2202 | `_IntelliBooks` | `### 18.2 The three stores` | **Superseded record, explicit.** The sentence itself says amendments 55 and 65 "proposed namespacing it as `_IntelliBooks\`. That is backwards". |
| 2456 | `_Statements` | `### 18.9 What this cancels` | **Superseded record, explicit.** A cancellation table row ending "There is nothing left to namespace." |
| 2456 | `_IntelliBooks` | `### 18.9 What this cancels` | **Superseded record, explicit.** Same row. |

**So: not a defect, and I have struck nothing and changed nothing.** But if a session ever reads an underscored path out of this document as current, it will be line 1517 or line 1541, because those two are the only ones whose own text does not say they are superseded. Recorded as an observation, not raised as a fault.

### 2e. Every table row has its header's pipe count

Definition used: **a table block is any run of two or more consecutive lines whose stripped text begins with a pipe; the first line is its header; every later line must have the same count of pipes not preceded by a backslash.**

```
2026-07-25_CONSOLE_DESIGN.md                         blocks=46  inconsistent_rows=0
2026-08-03_NOTE_chart_of_accounts_for_paul.md        blocks=3   inconsistent_rows=0
.gitignore                                           blocks=0   inconsistent_rows=0
PROMPT_claude_code_2026-09-01_step10d_pipeline.md    blocks=3   inconsistent_rows=0
PROMPT_intellibooks_2026-09-01_step10d_desktop.md    blocks=3   inconsistent_rows=0
PROMPT_phoneapp_2026-09-01_step10d.md                blocks=3   inconsistent_rows=0

TOTAL inconsistent rows across all six files: 0
```

**Pass. Zero inconsistent rows**, and on the same definition my block counts match the brief's exactly: 46 in the design document and 3 in each of the other four markdown files.

### 2f. The three step 10d briefs' field list

Slice from the `## A. The field list` heading to the next line beginning `## `.

```
PROMPT_claude_code_2026-09-01_step10d_pipeline.md    A at line 15  next ## at 54  bytes=3056  md5=0d0dda57d858577da806dea2e3c3e45f
PROMPT_intellibooks_2026-09-01_step10d_desktop.md    A at line 15  next ## at 54  bytes=3056  md5=0d0dda57d858577da806dea2e3c3e45f
PROMPT_phoneapp_2026-09-01_step10d.md                A at line 20  next ## at 59  bytes=3056  md5=0d0dda57d858577da806dea2e3c3e45f

all three identical: True
distinct md5 values: {'0d0dda57d858577da806dea2e3c3e45f'}
```

**Pass. All three identical**, at 3,056 bytes and `0d0dda57d858577da806dea2e3c3e45f`, matching the brief. The section moved from 2,876 bytes and `97ecd1d7…` at the last commit, which is the one sentence added to all three.

### 2g. The outstanding items list is untouched

```
$ git --no-optional-locks diff --stat -- 2026-08-20_LIST_outstanding_items_and_decisions.md
(no output)
disk blob : 185f1a246e7f1d916e6efa7810808502a580e7f9
HEAD blob : 185f1a246e7f1d916e6efa7810808502a580e7f9
count line: ## 87 open, 64 closed, 151 raised
```

**Pass. Byte-identical to HEAD**, established by matching blob ids and not only by an empty diff, and the count line still reads 87 open, 64 closed, 151 raised.

### 2h. Nothing from outside the repository

**Ten intended paths, all plain root filenames**, none containing `IntelliCharts`, `OneDrive` or `Intellibills`, and no `.py` among them. The post-commit `git show --stat` confirmation is in the session reply, because this report is written before staging so that it lands in the same commit.

---

## Task 3. The root markdown count, and step 10h

**Enumerated, not filtered.** `os.listdir` on the root, kept files ending `.md`, cross-referenced against `git ls-files -- '*.md'` restricted to paths with no `/`.

```
root markdown files: 87
  tracked  : 86
  untracked: 1
  untracked names: ['PROMPT_claude_code_2026-09-02_commit_167.md']
```

**One more than the brief predicted on both figures, per Finding 1.** This report makes 88.

**All 17 of step 10h's names are present.**

```
 1 2026-07-25_CONSOLE_DESIGN.md                          PRESENT
 2 2026-07-31_PLAN_reset_and_restructure.md              PRESENT
 3 2026-08-03_NOTE_chart_of_accounts_for_paul.md         PRESENT
 4 2026-08-18_BOUNDARY_two_products.md                   PRESENT
 5 2026-08-18_INSTRUCTION_coa_authority.md               PRESENT
 6 2026-08-20_LIST_outstanding_items_and_decisions.md    PRESENT
 7 2026-08-20_LIST_settings_firm_and_client.md           PRESENT
 8 2026-08-20_NOTE_demo_version.md                       PRESENT
 9 2026-09-01_DESIGN_cloud_multi_firm.md                 PRESENT
10 CATEGORISATION.md                                     PRESENT
11 CLAUDE.md                                             PRESENT
12 EMAIL_PROCESSING_MICROSTEPS.md                        PRESENT
13 MULTIFIRM_EMAIL_FORWARDING_ANALYSIS_AND_FINDINGS.md   PRESENT
14 PAUL_CHECKS_2026-07-30.md                             PRESENT
15 PROMPT_intellibooks_desktop_changes.md                PRESENT
16 RECEIPT_CAPTURE_GUIDE.md                              PRESENT
17 2026-08-24_HANDOVER_consultant_chat_11.md             PRESENT   (the rule, resolved to the current handover)

all 17 present: True   missing: []
```

**Step 10h still states no total.** At line 2026, live "N of M" figures after stripping strikes: `[]`. **I have added no total and not touched the step.** Note that `2026-08-03_NOTE_chart_of_accounts_for_paul.md`, name 3, stays in the root under step 10h while neither CSV it was written about now exists, which is what amendment 167's strikes are for.

---

## What the brief got wrong

Three figures, none of them affecting an assertion about the documents.

1. **The root markdown count**: 86 total and 85 tracked, against an actual 87 and 86, cross-checked three ways. This report makes 88.
2. **Two version-block line numbers**: v1.27 at 352 and v1.28 at 358, against an actual 353 and 359. v1.29 at 365 is right, which makes the three mutually inconsistent.
3. **"All five body occurrences" of the `_Receipts` family**: six across five lines, with `_Review` at line 1541 unnamed.

**All three are set or position claims made without enumerating**, which is the rule at "A claim about a set is not verified by verifying its members" in CLAUDE.md. The brief's 22-occurrence total, its 46 and 3 block counts, its `0d0dda57` hash, its twelve blob hashes, its twelve byte counts, its six MD5s and all four of its line boundaries were exact.

---

## Confidence

**High that task 1 matched and that all eight task 2 checks and both task 3 checks pass.** Each was run and its output printed whole above, not summarised.

**High that all six predicted disk blob hashes and all six MD5s were right**, from `git hash-object` and `md5sum` on the working tree.

**High on the three findings.** The root count was cross-checked three independent ways; the version-block lines were printed with true line numbers; the `_Receipts` body set was enumerated per name and per line and each of the six read individually with its enclosing heading.

**High that `Desktop's six` is a real correction and not a deletion**, because I counted the same needle in the HEAD blob and it was 1 there and 0 now, so the check discriminates. **High that nothing else in task 2d was deleted rather than struck**, because every other needle has its struck span quoted.

**Medium on nothing.** The one judgement rather than measurement in this report is that lines 1517 and 1541 are superseded by inheritance from the 13A warning rather than by their own text. That is a reading of two lines and the heading above them, and it is offered as an observation rather than a finding.

**One thing this report does not settle**, and it is the brief's own disclosure: section 16's head line still says the six sub-steps were built 2026-09-01 while all six read BUILT 2026-08-31. I raised it as finding 4 last commit, nothing on disk decides it, Paul has not ruled, and it is deliberately untouched here.
