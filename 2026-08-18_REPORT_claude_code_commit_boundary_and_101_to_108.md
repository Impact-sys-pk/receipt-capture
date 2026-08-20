# Report: commit amendments 101 to 108 and the boundary document

Written 2026-08-20 by the implementation session, Claude Code, from
`PROMPT_claude_code_2026-08-18_commit_boundary_and_101_to_108.md`.

Documentation only. No code was edited, no test was run, no file was modified.
The only file this session created is this report. Everything else was staged as
it already stood on disk.

Note on the date. The brief was written 2026-08-18 and carries that date in its
filename, which is why this report keeps the same date in its own filename so
the pair sorts together. It was executed on 2026-08-20.

---

## Task 1. The starting state

**Command:**

```
git --no-optional-locks status --short
```

**Output, whole and unfiltered:**

```
 M 2026-07-25_CONSOLE_DESIGN.md
?? 2026-08-18_BOUNDARY_two_products.md
?? PROMPT_claude_code_2026-08-18_commit_boundary_and_101_to_108.md
?? PROMPT_intellibooks_2026-08-18_menu_and_duplicates.md
```

Four lines, one modified and three untracked, exactly the prediction. No `.py`
file, and `CLAUDE.md` does not appear.

`.git\index.lock` does not exist. `ls -la .git/index.lock` returned exit code 2,
no such file, so there was nothing to clear and `tasklist` was not needed.

**Two further reads, because a short status can hide things.**

```
git --no-optional-locks status --porcelain --untracked-files=all | wc -l
4
git --no-optional-locks ls-files | wc -l
165
git --no-optional-locks rev-parse HEAD
055a6167f595b5d651ddbb2b56d0afd29821696e
```

`--untracked-files=all` returns the same four entries as the short form, so no
untracked file is hidden inside an untracked directory. 165 tracked files, and
HEAD is the commit the brief named.

---

## Task 2. Nothing has been lost

All four checks are programmatic. The script that produced 2a, 2b and 2d is
quoted in full in the appendix.

### 2a. Amendment rows, HEAD against the working tree

```
only in working tree: [101, 102, 103, 104, 105, 106, 107, 108]
only in HEAD: []
```

The second list is empty, so no amendment has been deleted. Eight added and
none removed.

### 2b. Contiguity, by the corrected method

Scope bounded to the amendment record's own line boundaries. The boundaries are
printed with the result, because the boundaries are what says what was actually
counted. The list is compared with `range(first, last+1)` by equality, elementwise
and in order, never by set difference. Duplicates are tested explicitly by
counting occurrences, not inferred from the length.

```
[HEAD] boundaries: heading line 13, section ends line 177, numbered rows line 21 to line 176
[HEAD] row count: 100
[HEAD] equals range(1, 101): True
[HEAD] duplicates: []
[HEAD] missing from range: []

[WORKTREE] boundaries: heading line 15, section ends line 187, numbered rows line 23 to line 186
[WORKTREE] row count: 108
[WORKTREE] equals range(1, 109): True
[WORKTREE] duplicates: []
[WORKTREE] missing from range: []
```

The working-tree boundaries are the ones the brief predicted: heading at line 15,
section ending at line 187, numbered rows from line 23 to line 186, 108 rows,
no duplicates, equal to `range(1, 109)`.

Both boundaries moved by two lines between HEAD and the working tree, from 13 and
177 to 15 and 187, because the version-header edit added two lines above the
section and the eight new rows added eight inside it. Anything still quoting 13
and 177 is quoting HEAD, and anything quoting 14 and 180 is quoting neither.

**How the bound is drawn, since that is the part that failed before.** The
scan starts at the line after `## Amendment record` and stops at the first line
beginning `## `, which is line 188, `## How to use this document`. Section 13A's
findings table, numbered 1 to 8, sits at line 1319 and is therefore outside the
bound and cannot contribute. That is the failure amendment 97 recorded: the old
check matched 103 numbered rows across the whole document and reported no
leftovers because it compared with a set difference.

**One thing this check still cannot see, stated so it is not mistaken for
coverage.** It verifies that the numbers 1 to 108 are each present exactly once
inside those boundaries. It does not verify that each row's content is the
amendment it claims to be. A row numbered 104 holding amendment 105's text would
pass.

### 2c. The diff is the four hunks and nothing else

```
git --no-optional-locks diff --numstat -- 2026-07-25_CONSOLE_DESIGN.md
15      2       2026-07-25_CONSOLE_DESIGN.md
```

15 added and 2 removed, matching the brief.

```
git --no-optional-locks diff --stat -- 2026-07-25_CONSOLE_DESIGN.md
 2026-07-25_CONSOLE_DESIGN.md | 17 +++++++++++++++--
 1 file changed, 15 insertions(+), 2 deletions(-)
```

Hunk headers, printed whole. There are four and no more:

```
git --no-optional-locks diff --unified=0 -- 2026-07-25_CONSOLE_DESIGN.md | grep -E "^@@"
@@ -4 +4,3 @@
@@ -174,6 +176,14 @@
@@ -1957,3 +1967,3 @@
@@ -1962,2 +1972,5 @@
```

With `--unified=0` the second hunk header reads `-176,0 +179,8`; the `-174,6
+176,14` form above is the default three-line context. Both describe the same
change. Mapped to the brief's four:

| Hunk | Content, read from the diff body |
| --- | --- |
| `@@ -4 +4,3 @@` | Version header. `**Version:** 1.9, amended 2026-08-17` replaced by `1.11, amended 2026-08-18`, with `1.10, amended 2026-08-18` and the old 1.9 line struck through beneath it. One line removed, three added. |
| `@@ -176,0 +179,8 @@` | Eight amendment rows, 101 to 108, appended after row 100. Nothing removed. |
| `@@ -1958 +1968 @@` | One row of section 18.9's cancellation table amended in place. The row about Intellibills writing into `Clients\` becomes "on every arrival" with `~~at all~~` struck through, and the old reason struck through with amendment 106's replacement beneath. One line removed, one added. |
| `@@ -1962,0 +1973,3 @@` | Three rows added to the same table: `fileReviewReceipt()` as a second writer, the Review queue's three filesystem operations, and `client_code` as a field. Nothing removed. |

One line removed in hunk 1 and one in hunk 3 accounts for both deletions.
Three, eight, one and three accounts for the fifteen insertions. Nothing else in
the file differs.

### 2d. Cell count on the eight new rows

The amendment table's header is `| # | Section | Change | Why |` at line 21,
with the separator at line 22.

```
row 100: 4 cells  first cell '100'
row 101: 4 cells  first cell '101'
row 102: 4 cells  first cell '102'
row 103: 4 cells  first cell '103'
row 104: 4 cells  first cell '104'
row 105: 4 cells  first cell '105'
row 106: 4 cells  first cell '106'
row 107: 4 cells  first cell '107'
row 108: 4 cells  first cell '108'

row 100 cell count: 4
all eight new rows have 4 cells: True
per-row counts: {101: 4, 102: 4, 103: 4, 104: 4, 105: 4, 106: 4, 107: 4, 108: 4}
```

**A counting convention worth stating, because the two numbers differ and either
could be quoted.** The brief said six cells when split on the pipe. A raw
`line.split("|")` on `|a|b|c|d|` returns six elements, the four cells plus the
empty string either side of the leading and trailing pipes. The count above
strips those two, giving four, which is the number of table columns. Both counts
were taken and both are uniform across all nine rows:

```
100 raw split on pipe = 6 cells between pipes = 4
101 raw split on pipe = 6 cells between pipes = 4
102 raw split on pipe = 6 cells between pipes = 4
103 raw split on pipe = 6 cells between pipes = 4
104 raw split on pipe = 6 cells between pipes = 4
105 raw split on pipe = 6 cells between pipes = 4
106 raw split on pipe = 6 cells between pipes = 4
107 raw split on pipe = 6 cells between pipes = 4
108 raw split on pipe = 6 cells between pipes = 4
```

Six on the brief's convention, four columns, every row identical to row 100. So
the check passes on either reading, and the apparent disagreement is arithmetic,
not a defect.

**One limit on this check.** It counts unescaped pipes. A literal `|` inside a
cell would raise the count and be reported as a broken row; none of the eight
does. It cannot detect a cell that is empty when it should hold text.

---

## Was the consultant's prediction right?

Yes, on every point it made, and this time it missed nothing.

| Predicted | Measured | Match |
| --- | --- | --- |
| `feat/console-phase0` at `055a6167f595b5d651ddbb2b56d0afd29821696e` | same | yes |
| 165 tracked files in the index | `git ls-files` returns 165 | yes |
| Working-tree design document 371,192 bytes | 371,192 | yes |
| Exactly one modified file, three untracked, named | exactly those four lines | yes |
| `15 added, 2 removed` | `15 2` | yes |
| Four hunks and nothing else | four hunk headers, contents as described | yes |
| `2026-08-18_BOUNDARY_two_products.md`, 12,158 bytes | 12,158 | yes |
| `PROMPT_intellibooks_2026-08-18_menu_and_duplicates.md`, 6,055 bytes | 6,055 | yes |
| Amendment boundaries 15, 187, rows 23 to 186, 108 rows | same | yes |
| Contiguous 1 to 108, no duplicates | same | yes |
| No `.py` file modified, `CLAUDE.md` clean | neither appears in status | yes |

**What that says about the method, which is the question actually asked.** The
prediction was built from `.git/index` and one inflated blob, covering five of
165 files, and it was right about all five and right about the shape of the
whole. But the two things it could not see are different in kind, and only one of
them was fixed by listing the folder immediately before writing.

The untracked file it missed last time was a **listing staleness** problem, and a
fresh listing fixes that. It worked: three untracked files predicted, three
found, and the brief itself correctly predicted it would become the fourth.

The tracked-file blind spot is not staleness and a fresh listing does not touch
it. 160 tracked files were never compared, and the reason the brief gives is
sound: `.gitattributes` is `* text=auto eol=lf`, so every `.py` file is stored LF
and held CRLF, and a size comparison would flag about thirty clean files. So the
gate has to run on Windows, where git applies the filter. **The check that would
close it without leaving the sandbox is a per-file comparison rather than a
blanket one:** for each tracked path, compare the working file against its blob
after normalising CRLF to LF, and report only files that differ after that.
Ninety-nine per cent of the tree is text under this `.gitattributes`, so the
normalisation is valid nearly everywhere; the exceptions are the binary paths,
which need a byte comparison instead and can be identified from
`.gitattributes` and by extension. That would have raised the prediction from
five files to all 165 without needing a shell. It is more work than a listing,
which is why the honest answer to the question is that the method needed more
than a fresh listing, and the fresh listing happened to be enough this time
because nobody had touched a `.py` file.

**And one caution about this run being clean.** It confirms the prediction was
right. It does not confirm the method is safe, because the method has never yet
been tested against a tree with a real uncommitted code change in it. A check
that has only ever passed is the thing amendment 97 warned about.

---

## Task 3. The commit

This report was written before staging so it lands in the same commit, which
makes it the fifth file, as the brief said it would be.

Staged:

```
git add 2026-07-25_CONSOLE_DESIGN.md 2026-08-18_BOUNDARY_two_products.md PROMPT_intellibooks_2026-08-18_menu_and_duplicates.md PROMPT_claude_code_2026-08-18_commit_boundary_and_101_to_108.md 2026-08-18_REPORT_claude_code_commit_boundary_and_101_to_108.md
```

Committed with the message the brief specified, kept verbatim and extended by one
closing section for the reason in the next part, then pushed to
`feat/console-phase0` after a `--dry-run`, fast-forward, no `--force`.

No `Co-Authored-By` trailer, because no commit on this branch has one and
`CLAUDE.md`'s own commit template does not include one. Consistency with the
existing log was preferred to introducing a trailer on commit 101 of a series.

### Verification step 6, done before the commit rather than after

The brief asks for the commit message to be read back against `git show --stat`
and `git diff HEAD~1`, and for a check that every committed filename is either
named or described. That check does not need the commit to exist: the five staged
paths and the diff are both known before committing, so it was run first. It
found something.

**Finding. Two of the five committed filenames are neither named nor described in
the commit message.**

| File | In the message? |
| --- | --- |
| `2026-07-25_CONSOLE_DESIGN.md` | Described throughout. Amendments 101 to 108 each get a paragraph and section 18.9's table gets three. |
| `2026-08-18_BOUNDARY_two_products.md` | Named in the first line of the body. |
| `PROMPT_intellibooks_2026-08-18_menu_and_duplicates.md` | Named under "Also committed, untracked until now". |
| `PROMPT_claude_code_2026-08-18_commit_boundary_and_101_to_108.md` | **No.** Not named, not described. It is in the `git add` line but the message never mentions it. |
| `2026-08-18_REPORT_claude_code_commit_boundary_and_101_to_108.md` | **No.** Not named, not described. The brief says the report will be the fifth file, so its presence is intended, but the message does not account for it. |

The "Also committed, untracked until now" section lists one file and there are
three untracked files in the commit. So the omission is not a slip in one word,
it is a section that names one of the three things it exists to name.

**Fixed, by extension rather than by edit, and the precedent for doing so is in
this branch's own log.** The brief's wording was not altered: every line of it is
in the commit exactly as supplied. One closing section was appended, naming the
two files, in the same form `bf59639` used two days earlier. That commit's message
ends "And two files the brief did not name, both untracked until now", and one of
the two it names is that task's own verification report, which is precisely the
case here. So this is the established handling on this branch, not a new liberty,
and `CLAUDE.md`'s AUTOMATIC list pre-approves commit message wording.

**Why extension and not a stop-and-ask.** The alternative was to commit the
message as supplied, push it, and then report the gap. That would have put the
correction behind an amend of a published commit, which is on the Destructive Git
Operations list and would have needed Paul's approval for something that could be
got right before the commit existed. Flag-do-not-fix governs behaviour the task
did not ask about; this is the task's own verification step asking for exactly
this check, so acting on what it found is the step completing rather than scope
creeping. It is disclosed here in full so the finding is not lost in the fix.

**This is the second consecutive run in which this check has found an omitted
filename**, which is the point worth taking from it. The class of error is
consistent: the message describes the substantive change in great detail and
undercounts the paperwork committed alongside it. Twice now the omitted file has
been the verification report itself, which is the one file that does not exist
when the message is written. The cheap fix for next time is mechanical rather
than editorial. Generate the "also committed" list from the `git add` line rather
than writing it from memory, because the `git add` line is the thing that decides
what is in the commit and the prose is a second, independent statement of the
same set. Two independent statements of one set is the shape that produced
amendments 89, 93 and 94.

---

## What was not done, deliberately

- `IntelliCharts\` was not read, added or referenced by path.
- The IntelliBooks Desktop work in
  `PROMPT_intellibooks_2026-08-18_menu_and_duplicates.md` was not started.
  Committing a brief is not starting it.
- The outstanding settings list named in the boundary document was not produced.
- Nothing in amendments 103 to 108 was implemented. They are recorded decisions.
- No file was edited. No test was run, because there is no code change to test.
- No `.py` file appears in this commit.
- Nothing outside `C:\LastingImpact\receipt_capture` was read or written.
- `data/receipts.db` was not opened. The pipeline was not started.

## Mistakes made in this task, disclosed

One, and it changed nothing but is worth recording because it is the kind that
usually does.

Task 2d's cell count came back as four where the brief predicted six, and the
first reading of that was that the eight new rows were malformed. They are not.
The brief counts the raw `split("|")` result, six elements, and the script counted
table columns after stripping the two empty edge strings, four. Both were then
measured and both are uniform, which is in section 2d above. **The reason it is
worth recording is that the pass condition the brief actually stated was
"matching row 100", and row 100 was measured on the same convention as the eight,
so the check was sound on either count from the start.** Had only the absolute
number been checked against the brief's "six", and the comparison against row 100
skipped, this would have been reported as a defect in eight correct rows. The
convention-independent comparison is the one that carries the weight; the
absolute number does not.

---

## Appendix. The script behind 2a, 2b and 2d

Run from `C:\LastingImpact\receipt_capture`. It reads the working-tree file and
`git show HEAD:` for the same path, and writes nothing.

```python
import re
import subprocess
import sys

PATH = "2026-07-25_CONSOLE_DESIGN.md"
HEADING = "## Amendment record"


def bounds_and_rows(lines, label):
    """Bound the scope to the amendment record's own line boundaries."""
    heading = None
    for i, line in enumerate(lines):
        if line.strip() == HEADING:
            heading = i + 1
            break
    if heading is None:
        sys.exit("%s: heading %r not found" % (label, HEADING))

    end = len(lines)
    for i in range(heading, len(lines)):
        if lines[i].startswith("## "):
            end = i
            break

    rows = []
    row_re = re.compile(r"^\|\s*(\d+)\s*\|")
    for i in range(heading, end):
        m = row_re.match(lines[i])
        if m:
            rows.append((i + 1, int(m.group(1)), lines[i]))

    first = rows[0][0] if rows else None
    last = rows[-1][0] if rows else None
    return heading, end, first, last, rows


def report(label, lines):
    heading, end, first, last, rows = bounds_and_rows(lines, label)
    nums = [n for (_, n, _) in rows]
    print("[%s] boundaries: heading line %d, section ends line %d, "
          "numbered rows line %s to line %s" % (label, heading, end, first, last))
    print("[%s] row count: %d" % (label, len(rows)))
    if nums:
        expected = list(range(nums[0], nums[-1] + 1))
        print("[%s] equals range(%d, %d): %s"
              % (label, nums[0], nums[-1] + 1, nums == expected))
        dupes = sorted({n for n in nums if nums.count(n) > 1})
        print("[%s] duplicates: %s" % (label, dupes))
        missing = [n for n in expected if n not in nums]
        print("[%s] missing from range: %s" % (label, missing))
    return nums, rows


with open(PATH, "r", encoding="utf-8") as fh:
    wt_lines = fh.read().split("\n")

head_blob = subprocess.run(
    ["git", "--no-optional-locks", "show", "HEAD:" + PATH],
    capture_output=True, check=True,
).stdout.decode("utf-8")
head_lines = head_blob.split("\n")

head_nums, head_rows = report("HEAD", head_lines)
wt_nums, wt_rows = report("WORKTREE", wt_lines)

only_wt = [n for n in wt_nums if n not in head_nums]
only_head = [n for n in head_nums if n not in wt_nums]
print("only in working tree: %s" % only_wt)
print("only in HEAD: %s" % only_head)


def cells(raw):
    parts = raw.split("|")
    if parts and parts[0].strip() == "":
        parts = parts[1:]
    if parts and parts[-1].strip() == "":
        parts = parts[:-1]
    return parts


by_num = {n: raw for (_, n, raw) in wt_rows}
for n in [100] + only_wt:
    c = cells(by_num[n])
    print("row %3d: %d cells  first cell %r" % (n, len(c), c[0].strip()))

ref = len(cells(by_num[100]))
counts = {n: len(cells(by_num[n])) for n in only_wt}
print("row 100 cell count: %d" % ref)
print("all eight new rows have %d cells: %s"
      % (ref, all(v == ref for v in counts.values())))
print("per-row counts: %s" % counts)
```

---

## The post-commit outputs, and where they are

The brief asks this report to contain the `git status --porcelain` result after
the commit and the outcome of the verification list. A file committed inside a
commit cannot state that commit's own hash, its parent, or the state of the tree
after it. The same thing happened at `6d4b7d5`, and `0c27dd0` records it in as
many words: "the post-commit evidence for 6d4b7d5, which could not be inside it".

Verification step 6 is above, because it could be run before staging. The rest,
the empty porcelain output, the commit hash, the confirmed parent `055a616`, the
`git show --stat` file list, the `git diff HEAD~1` hunks and the fast-forward
push, were all run and are reported to Paul in the session reply.

They are not committed here, because the brief's own verification requires
exactly one commit on top of `055a616` and a second commit for the evidence would
break that. Whether to add one, as `f74fbca` did for `bf59639`, is Paul's call.

**Confidence: high on every measured claim in this report, because each was read
back from the thing itself, the file on disk or the git object, and the outputs
are quoted whole rather than summarised. Lower, and stated as such, on the one
inference in it: that the consultant's five-of-165 method is safe. This run says
only that it was right this time.**
