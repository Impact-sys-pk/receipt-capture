# Report: commit of amendment 174 and the two refreshed step 10d briefs

Written 2026-09-02 by Claude Code, 16:41 BST. Clock read at 16:34 and again at 16:41 BST before dating this file. The shell reports the zone as `GMTDT` and `date -u` was one hour behind at both readings, so the times here are BST.

Brief: `PROMPT_claude_code_2026-09-02_commit_174.md`.

**Outcome: done. One commit, `7e037c3`, five files, pushed to `origin/feat/console-phase0`. Working tree clean. All seven checks in task 4 ran and every one matched.**

**Three findings, all in the refreshed line numbers rather than in the amendment:**

1. **The pipeline brief has a seventh `config.py` citation and it was not refreshed.** The `mkdir` at `:95` is now at `config.py:113`, and line 95 today holds `PREFER_DAYFIRST`. It is the one citation not written in the `config.py:N` form, so a grep for that pattern misses it. **Same misleading-rather-than-failing shape amendment 174 records for `config.py:42`.**
2. **Four lines of the Desktop brief now contradict themselves**, each carrying a number that moved by thirteen beside numbers in the same sentence that did not move. On three of them the result is impossible on its face: a `getDir` call placed inside the copy loop it precedes, a key read eleven lines after the check that refuses without it, and five category strings placed outside the array that holds them.
3. **A quoted wrong citation was renumbered in one of its two places**, so the brief now disagrees with itself about what sub-step 10d.38 cites.

I could not resolve finding 2 or the sub-step's real line numbers, because `IntelliBooks-Desktop-v3.html` is under the practice root and task 5 forbids me to read it. **The contradictions are internal to the brief and need no access to that file.**

---

## 1. Starting state, task 1

`git --no-optional-locks status --porcelain`, printed whole:

```
 M 2026-07-25_CONSOLE_DESIGN.md
 M PROMPT_claude_code_2026-09-01_step10d_pipeline.md
 M PROMPT_intellibooks_2026-09-01_step10d_desktop.md
?? 2026-09-02_REPORT_claude_code_commit_173.md
?? PROMPT_claude_code_2026-09-02_commit_174.md
```

`git --no-optional-locks log --oneline -2`, printed whole:

```
5748b22 docs: amendment 173, the chart of accounts naming sweep
d6485c8 docs: amendments 170 to 172, step 10a built, and the step 10a working files
```

Three modified and two untracked, nothing else, HEAD `5748b22`. **`PROMPT_phoneapp_2026-09-01_step10d.md` is absent from the porcelain, which is the positive confirmation that it is unchanged** rather than merely unmentioned.

All three byte counts and hashes match the brief exactly:

| File | Bytes expected | Bytes read | md5 expected | md5 read | Match |
|---|---|---|---|---|---|
| `2026-07-25_CONSOLE_DESIGN.md` | 638,556 | 638,556 | `79df282eb2a67f51e667b3d1b74c0421` | `79df282eb2a67f51e667b3d1b74c0421` | yes |
| `PROMPT_claude_code_2026-09-01_step10d_pipeline.md` | 34,172 | 34,172 | `f26c61b559b099d20e622f28567aad8d` | `f26c61b559b099d20e622f28567aad8d` | yes |
| `PROMPT_intellibooks_2026-09-01_step10d_desktop.md` | 23,800 | 23,800 | `c87c7347071e5fa9dae7defa8cb3e27a` | `c87c7347071e5fa9dae7defa8cb3e27a` | yes |

---

## 2. What changed, task 2

All three diffs read whole. The design document's is 23,475 bytes across 48 lines with seven lines over 500 characters, read in three bounded ranges with no character truncation. The two briefs are 16 and 26 changed lines and were each printed in one go.

### 2.1 The design document, five hunks and nothing else

- Version header 1.33 to 1.34, with 1.33 added as a struck row.
- Amendment 173's headline gains an inline correction: `~~twenty~~ fifteen of the twenty-seven`, with "Corrected 2026-09-02 by amendment 174; the breakdown later in this row was right and the headline was not".
- A new `### v1.34` section holding amendment 174's single row.
- Step 10a's body: `config.REVIEW_ROOT` at `~~config.py:42~~ config.py:60`.
- Sub-step 10d.15: four `getDir` sites become nine plus the tenth string site.

**Amendment 174's row is accurate on the point it corrects about my own work**, which I checked rather than accepted. It says amendment 170 added one marker to step 10a's body line and 172 added two, so the working tree read 31 before 172 and 33 after. **That is exactly what my word-level diff on `5748b22` showed**, and it is the reconciliation I could not complete last time because I had not asked which file the consultant session had measured.

### 2.2 Everything checkable in the pipeline brief's new note holds

The note claims `config.py` moved by eighteen, `worker/filing.py` did not move, and five other modules plus everything under `tests\` were untouched by step 10a. **All four claims verified from git rather than taken on trust:**

```
=== files changed by step 10a (7ea2dc4 and 2ac70ab):
2ac70ab   config.py, tests/test_resolution_backfeed.py,
          tests/test_retroactive_categorise_sidecar.py,
          tests/test_sidecar_category_keys.py, worker/filing.py
7ea2dc4   config.py, worker/filing.py

=== worker/filing.py line count before and after step 10a:  395 -> 395
=== config.py line count before and after:                  183 -> 201
```

`config.py` grew by exactly 18 lines, which is the shift the note states. `worker/filing.py` was edited in place at 395 lines both sides. **`app.py`, `worker/database/repository.py`, `worker/intake/folder_reader.py`, `worker/extraction/postprocess.py` and `tests/test_path_layout.py` are all absent from that file list**, so every citation into them is unmoved, as the note says.

### 2.3 The Desktop brief's rewritten paragraph

The `filed_path` paragraph is rewritten rather than renumbered, as the brief said it would be: line 2519's hand-built `` `Clients\\${safeName(c.name)}\\Receipts\\...` `` string is struck, and the paragraph now says line 2532 reads `filed_path:clientFolderPath(c,"Receipts",taxYear,finalName),` with the helper at line 635. Task 4 item 4 of that brief was updated to match.

---

## 3. The commit, task 3, and the figures enumerated before it

The brief added a rule: enumerate every figure in the message before committing, because the message cannot be amended. **Done before `git commit`, and here is the enumeration.**

| Figure in the message | Verified | How |
|---|---|---|
| twenty is wrong and it is fifteen | **yes** | 10 in the record + 2 in `CLAUDE.md` + 3 in the items list = 15; 15 left + 12 changed = 27 |
| the same wrong figure is in `5748b22`'s message | **yes** | read back from `git log` |
| 10d.15 said four `getDir` sites | **yes** | the pre-commit sub-step text says four |
| it has nine plus a tenth string site | **partly** | the design document and the Desktop brief both say nine plus a tenth; **the count in `IntelliBooks-Desktop-v3.html` I cannot check** |
| `config.REVIEW_ROOT` cited at `:42`, is at `:60` | **yes** | `config.py:60` is `REVIEW_ROOT = INTELLIBILLS_ROOT / "Review"`; `:42` is `CLIENT_INTELLIBOOKS_FOLDER_NAME = "IntelliBooks"` |
| 30 is the blob at `2ac70ab`, which predates 170 and 171 | **yes** | that blob's line holds 30 markers, and its amendment record holds rows 1 to 169 with 170, 171 and 172 all absent |
| six `config.py` citations moved by eighteen | **yes** | six distinct lines, seven instances, every one +18, every one landing on the construct it names |
| fifteen Desktop citations moved by 0, 5 or 13 | **count yes, distribution loose** | fifteen changed instances measured; the shifts among them are +5 twice and +13 thirteen times. **None of the fifteen moved by 0**; the 0 belongs to the citations left unchanged, which are not among the fifteen |
| Section A byte-identical across all three briefs at 3,056 bytes | **yes** | section 4.5 below |

**The one loose figure is the last but one, and I committed anyway.** The count of fifteen is right and "0, 5 or 13" is a fair compression of the three-region shift model the brief's own note states. Read as "some of the fifteen moved by zero" it is wrong; read as "citations in this file moved by 0, 5 or 13 by region, and fifteen changed" it is right. **Recorded rather than treated as a blocker, because the number the rule exists to protect is correct.**

`git diff --cached --stat` before committing:

```
 2026-07-25_CONSOLE_DESIGN.md                      |  15 +-
 2026-09-02_REPORT_claude_code_commit_173.md       | 354 ++++++++++++++++++++++
 PROMPT_claude_code_2026-09-01_step10d_pipeline.md |  16 +-
 PROMPT_claude_code_2026-09-02_commit_174.md       |  93 ++++++
 PROMPT_intellibooks_2026-09-01_step10d_desktop.md |  26 +-
 5 files changed, 481 insertions(+), 23 deletions(-)
```

Five files, matching the message's `Files:` line. No code and no tests. `7e037c3`, `Wed Sep 2 16:40:05 2026 +0100`. `git push --dry-run` reported `5748b22..7e037c3`, a fast-forward, and the real push printed the same range.

---

## 4. Verification, task 4

### 4.1 Status after the commit

`git --no-optional-locks status --porcelain` printed nothing at all. Working tree clean.

`git --no-optional-locks show --stat HEAD`:

```
7e037c336417df07cee7e478d2bc2022b8edd7d7
Wed Sep 2 16:40:05 2026 +0100
docs: amendment 174, and the step 10d briefs' line numbers refreshed

 2026-07-25_CONSOLE_DESIGN.md                      |  15 +-
 2026-09-02_REPORT_claude_code_commit_173.md       | 354 ++++++++++++++++++++++
 PROMPT_claude_code_2026-09-01_step10d_pipeline.md |  16 +-
 PROMPT_claude_code_2026-09-02_commit_174.md       |  93 ++++++
 PROMPT_intellibooks_2026-09-01_step10d_desktop.md |  26 +-
 5 files changed, 481 insertions(+), 23 deletions(-)
```

### 4.2 Amendment record contiguity

```
Section heading line: 40  ('## Amendment record')
Next '## ' heading line: 407  ('## How to use this document')
First numbered row line: 50  (amendment 1)
Last  numbered row line: 405  (amendment 174)
Numbered rows matched: 174
Lowest: 1  Highest: 174
Equals range(1, 175)? True
Duplicates: []
Missing from range: []
Outside range: []
```

**174 rows, 1 to 174, no duplicates, no gaps.** Row count equals the highest number. Bounds 50 to 405, inside a section ending at 407, so 13A's findings table cannot be matched.

### 4.3 Section 16 head table against the body

Located by heading, not by a line number carried from the last commit, because everything below the record has shifted again:

```
Section 16: heading line 1731, next '## ' at 2102
Head-table rows found: 38  (lines 1740 to 1777)
  BUILT: 19
  OUTSTANDING: 17
  CANCELLED: 1
  MOVED: 1

Body step-status lines: 38 for 38 steps
Steps with more than one body status line: none

Disagreements between head table and body:
  none

Table rows: 38   Body steps: 38   Disagreements: 0
```

**19, 17, 1, 1, 38, unchanged**, and the head line still states those four figures. Compared both ways.

### 4.4 Odd bold-marker lines

```
2026-07-25_CONSOLE_DESIGN.md: 0 odd-marker line(s) of 2528
PROMPT_claude_code_2026-09-01_step10d_pipeline.md: 0 odd-marker line(s) of 321
PROMPT_intellibooks_2026-09-01_step10d_desktop.md: 0 odd-marker line(s) of 253
```

**Zero in the design document as expected**, and zero in both briefs, which the brief did not ask for and which is worth knowing since both gained a new paragraph.

### 4.5 Section A across all three step 10d briefs

```
Convention: from '## A. The field list' up to the next '## ' heading,
trailing newlines collapsed to one.

  3056 bytes  md5 0d0dda57d858577da806dea2e3c3e45f  PROMPT_claude_code_2026-09-01_step10d_pipeline.md
  3056 bytes  md5 0d0dda57d858577da806dea2e3c3e45f  PROMPT_intellibooks_2026-09-01_step10d_desktop.md
  3056 bytes  md5 0d0dda57d858577da806dea2e3c3e45f  PROMPT_phoneapp_2026-09-01_step10d.md

Distinct (bytes, md5) pairs: 1  -> identical
Brief expected 3056 bytes and md5 starting 0d0dda57d858: True
```

**All three identical, 3,056 bytes, hash as expected, and the phone app brief still matches the two in this commit.**

**One thing worth recording about the method, because it cost me a step.** My first bound ran from the heading to the next `## ` heading as captured, which gave **3,057 bytes and md5 `b628994d...`** — same content, different trailing whitespace, completely different hash. I then tested six boundary conventions and only one reproduces the brief's figures. **A hash without its boundary rule is not reproducible**, which is this project's rule about printing bounds applied to hashing rather than to counting. The convention is stated above so the next session gets the same number.

### 4.6 Every `config.py:N` in the pipeline brief, against the file

Seven occurrences at six distinct lines, `:167` twice. **Every one lands on the construct the brief names**, read out of `config.py` with `sed`:

```
  56: EXPORTS_DIR = INTELLIBILLS_ROOT / "Exports"
  70: RECEIPTS_LOG = LOGS_DIR / "receipt_events.ndjson"
 126: def load_clients():
 150: def load_firms():
 167: CLIENTS, CLIENTS_BY_CODE = load_clients()
 168: FIRMS = load_firms()
```

| Brief line | Citation | What the brief says it is | What line N holds | Correct |
|---|---|---|---|---|
| 104 | `config.py:126` | `load_clients()` | `def load_clients():` | yes |
| 108 | `config.py:167` | the `CLIENTS_BY_CODE` definition | `CLIENTS, CLIENTS_BY_CODE = load_clients()` | yes |
| 112 | `config.py:167` | loads the registry once at import | same line | yes |
| 143 | `config.py:70` | `config.RECEIPTS_LOG` | `RECEIPTS_LOG = LOGS_DIR / ...` | yes |
| 227 | `config.py:150` | `load_firms()` | `def load_firms():` | yes |
| 229 | `config.py:168` | `config.FIRMS` | `FIRMS = load_firms()` | yes |
| 239 | `config.py:56` | `EXPORTS_DIR` | `EXPORTS_DIR = INTELLIBILLS_ROOT / "Exports"` | yes |

**All six distinct lines correct, matching the brief's expectation exactly.** Finding 1 in section 5 is a seventh citation on brief line 239 that this pattern does not match.

### 4.7 `twenty of the twenty-seven` in the design document

```
=== occurrences: 405:twenty of the twenty-seven   (count: 1)
=== 'fifteen of the twenty-seven': 399, 405
```

Line 405 is **amendment 174's own row**, and the occurrence sits inside a strike, tested by counting the `~~` markers before it:

```
line 405: amendment row 174
   'twenty of the twenty-seven' at pos 331, inside a strike: True
   context: ...are left as history and it is fifteen.** ~~twenty of the twenty-seven~~
            **fifteen of the twenty-seven.** **The correct figure was in the sa...
```

**Zero occurrences outside amendment 174's own row, and the one inside it is struck.** Line 399 is amendment 173's row, whose headline now reads `~~twenty~~ fifteen of the twenty-seven`, so the phrase no longer appears there at all.

---

## 5. Finding 1: the pipeline brief's seventh `config.py` citation was not refreshed

Brief line 239 reads:

> **10d.37. Delete `EXPORTS_DIR` at `config.py:56` and its `mkdir` at `:95`.**

**`config.py:56` is right and `:95` is not.** Read out of the file:

```
--- lines 92 to 98:
     PREFER_DAYFIRST = os.environ.get("PREFER_DAYFIRST", "1") in ("1", "true", "True")   <- line 95
--- lines 110 to 116:
 110: INTELLIBILLS_ROOT.mkdir(parents=True, exist_ok=True)
 111: FILES_DIR.mkdir(parents=True, exist_ok=True)
 112: BACKUPS_ROOT.mkdir(parents=True, exist_ok=True)
 113: EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
 114: DB_PATH.parent.mkdir(parents=True, exist_ok=True)
 115: LOGS_DIR.mkdir(parents=True, exist_ok=True)
```

**The `EXPORTS_DIR.mkdir` is at `config.py:113`.** 95 + 18 = 113, so it moved with the other six and was left behind. **Line 95 today is `PREFER_DAYFIRST`, an unrelated constant**, which is the reading that misleads rather than the one that fails — the exact distinction amendment 174 draws about `config.py:42`.

**Why it was missed is the useful part.** It is the only `config.py` citation in the file written as a bare `:95` rather than as `config.py:95`, because it is the second citation in a sentence whose first names the file. **A grep for `config\.py:\d+` returns six lines and finds all six correctly. It cannot see this one.** So the note's claim that "every `config.py` line this brief cites moved by eighteen" and "all six were re-derived" is true of the set the pattern matched and not of the set the brief cites, which is seven.

**The sentence's other two citations are right and were correctly left alone:** `tests/test_path_layout.py:40` and `:112`, because step 10a did not touch that file, verified from the commit file lists in section 2.2.

**Not fixed.** Flag, do not fix, and task 5 forbids editing anything beyond the three named files, which no longer have pending changes.

## 6. Finding 2: four lines of the Desktop brief now contradict themselves

**Method first, because eyeballing would not be evidence.** I extracted every three or four digit number from the pre-commit and post-commit versions of the brief, restricted to the lines the diff changed, and diffed the two multisets:

```
Numbers removed: [593, 622, 1204, 1691, 1711, 1725, 1820, 1820, 2519, 2606, 2606,
                  3205, 3205, 3209, 3209]
Count removed 15
```

**Fifteen changed citation instances, matching the brief's figure exactly.** The shifts are `593→598` and `622→627`, both +5, and thirteen at +13: 1204→1217, 1691→1704, 1711→1724, 1725→1738, 1820→1833 twice, 2519→2532, 2606→2619 twice, 3205→3218 twice, 3209→3222 twice.

Then, for each changed line, what changed on it and what did not:

```
=== old 79 -> new 81      old [593, 671, 690, 718]        new [598, 671, 690, 718]
=== old 131 -> new 133    old [1688, 1691, 1702, 1706]    new [1688, 1704, 1702, 1706]
=== old 147 -> new 149    old [2606, 2606]                new [2606, 2619]
=== old 151 -> new 153    old [3205, 3209]                new [3218, 3222]
=== old 173 -> new 175    old [1204, 1206]                new [1217, 1206]
=== old 244 -> new 246    old [3167, 3205, 3209, 2606]    new [3167, 3218, 3222, 2619]
```

**Four of these are impossible as they now stand.** Each is quoted from the committed file.

**6.1 New line 133, sub-step 10d.12.** "`importToInbox()` is at line **1688** ... Today it opens `getDir([PIPE_DIR,"Receipt Inbox",c.code],true)` at line **1704** and copies the file alone, at lines **1702 to 1706**." **The `getDir` call is now placed inside the copy range and two lines after its start**, though the sentence says the copy follows it. Before the refresh the sequence was 1688, 1691, 1702 to 1706, which is coherent. Only the middle number moved.

**6.2 New line 175, sub-step 10d.44.** "`copyCaptureLink()` reads that key from `practice.settings.uploadKey` at line **1217** and refuses without it at **1206**." **The read is now eleven lines after the check that refuses when the read comes back empty.** The three neighbouring citations in the same paragraph, at 1201, 1208, 1209 and 1210, are also unmoved.

**6.3 New line 153, sub-step 10d.38.** The five bullets, as committed:

```
- `function loadSampleData(){` is line **3167**
- the five sample receipts are the `rs` array at **3204 to 3210**
- the category strings are at **3218 to 3222**: "Motor expenses", ...
- `category:catg` is written into each receipt at **3216**
- the linked transfer pair gets `category="(Transfer)"` at **3203**
```

**The category strings are stated to be inside the `rs` array and their range now falls wholly outside it**, 3218 to 3222 against 3204 to 3210. They are also after `category:catg` at 3216, which writes them. **One bullet of five moved.**

**6.4 New line 81, sub-step 10d.52.** "`instance` is a per-browser id generated at line **598** ... stamped on save at **671** and **690**, and compared at **718**." The generation moved by five and the other three did not move at all. **Under the brief's own stated model that is backwards:** it says nothing above the header comment moved, the region up to `safeName()` at 627 moved by five, and **everything below the new `clientFolderPath()` helper at 635 moved by thirteen.** 671, 690 and 718 are all below 635, so the model puts them at 684, 703 and 731.

**What I can and cannot conclude.** `IntelliBooks-Desktop-v3.html` is under the practice root and task 5 forbids me to read it, **so I cannot say which number in each pair is right.** The contradictions above need no access to that file: they are between numbers in the same sentence of the brief. **The likeliest reading is that the sweep refreshed the citation each paragraph was written about and not the supporting numbers around it**, which would mean the unmoved ones are stale by thirteen. That is inference and is labelled as such.

**What reduces the cost.** Both notes end "Read the region before editing it in any case: these numbers move again as soon as this step's first edit lands", so a session following the brief is already told not to trust the numbers. **The risk is not a wrong edit so much as a session spending time reconciling a paragraph that cannot be reconciled**, and then reporting a discrepancy that is in the brief rather than in the code.

## 7. Finding 3: a quoted wrong citation was renumbered in one of its two places

Sub-step 10d.38's whole point is that the sub-step cites the wrong line. The brief handles that correctly in the body, at new line 149:

> It cites `IntelliBooks-Desktop-v3.html:2606`. Line **2619** is `$("vat-report-card")...`

**2606 is kept because it is what the sub-step says, and 2619 describes where that content sits today.** But in "Four things I want back", at new line 246, the same historical citation was renumbered:

> `loadSampleData()` at 3167 with the categories at 3218 to 3222 rather than **2619**.

**It read "rather than 2606" and 2606 is the figure being corrected.** So the two places now disagree about what sub-step 10d.38 cites, and the closing section attributes to the sub-step a number it does not contain. **Renumbering a quoted wrong value is the case amendment 82 exists for**, and it is the smallest instance of it I have seen on this project: one number, in a question put to another session, about which of two numbers is right.

Minor, and worth one line rather than an amendment: **the body is right, so the correction survives.**

## 8. One observation on navigating amendment 173's row

Amendment 173's headline now carries its correction inline. **Two other wrong statements in the same row's Why column are left standing with no pointer forward:** "which is how the split came out as 20 against 7", which is where the wrong headline came from, and "Claude Code reported the pre-172 count as 30 and it must have been 31 ... that one-out is unreconciled". **Both are corrected in amendment 174's row and neither is struck or cross-referenced in 173's.**

That is the record's convention working as designed, and it is not a defect. **Recorded only because a reader who lands on amendment 173 alone now reads two figures that a later row corrects**, and the headline shows the convention permits an inline pointer where it matters.

---

## 9. Task 5, the stop list

Nothing on it was touched. No file other than the three named in task 1 was modified, and those three were committed as found. **`config.py` was read with `sed` and never imported**, per the trap in `CLAUDE.md`. `worker/filing.py` and the test files were read only through `git log --name-only` and `wc -l` on committed blobs. **Nothing under the practice root or `C:\Intellibills\` was read or written**, which is why finding 2 stops at the internal contradiction and why the nine `getDir` sites and the 3,307-to-3,320 line growth are the consultant session's figures and not mine.

Files this session created: this report, a commit-message file and one diff file in the session scratchpad at `C:\Users\PDK7\AppData\Local\Temp\claude\c--LastingImpact-receipt-capture\0085bc27-c837-44e7-b879-f65b54d82f61\scratchpad\`, outside the repository and throwaway.

---

## 10. Confidence

**High that the commit holds exactly the five files intended and that the amendment is internally consistent.** All three diffs read whole, and the five hunks in the design document enumerated.

**High on every figure in section 4.** Each script printed its own scope, both set comparisons ran in both directions, and the strike-membership question in 4.7 was settled by counting markers rather than by reading.

**High on finding 1.** It is two `sed` reads of `config.py` in the repository, and 95 + 18 = 113 is consistent with the other six.

**High that the four contradictions in finding 2 exist**, because they are multiset comparisons of numbers on single lines of a file I read. **Moderate on which number in each pair is stale**, and that is labelled as inference: the file that would settle it is one I cannot open.

**High on the enumeration in section 3**, which was done before the commit as the brief required, and on the one loose figure being loose rather than wrong.

**Two figures here are not mine:** the nine `getDir` sites plus a tenth in `IntelliBooks-Desktop-v3.html`, and that file growing from 3,307 to 3,320 lines. Both are under the practice root.
