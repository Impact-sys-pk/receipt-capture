# Report: amendment 96's section correction, and two consultant handovers

Written 2026-08-18 by the implementation session, Claude Code, in answer to
`PROMPT_claude_code_2026-08-18_commit_handover_7.md`.

Documentation only. Nothing was edited. Six files staged, one commit, one push.

**Confidence: high.** Every figure below was measured by a script run against the
files themselves, either the working tree copy or the blob inflated out of HEAD.
Nothing here is reasoned from a summary. Where my number differs from the
consultant's, the difference is explained and reconciled rather than smoothed over.

**One thing this report cannot contain, and why.** The brief asks for the report to be
inside the commit, and also asks it to record the post-commit porcelain result and
what verification step 6 returned. Those two requirements cannot both be met: evidence
about a commit cannot sit inside that commit. This is the same problem the project met
on 2026-08-03, when commit `0c27dd0` was titled "the post-commit evidence for 6d4b7d5,
which could not be inside it". Sections 1 to 3 below are everything knowable before
staging, which is the substance. Sections 4 and 5 name what was measured afterwards
and where it went. **Reported, not decided:** whether that post-commit evidence should
also land on disk in a follow-up commit is Paul's call, not mine.

---

## 1. The starting state, and the one thing the prediction missed

`git --no-optional-locks status --short`, full output, nothing removed:

```
 M 2026-07-25_CONSOLE_DESIGN.md
?? 2026-08-17_HANDOVER_consultant_chat_6.md
?? 2026-08-18_HANDOVER_consultant_chat_7.md
?? 2026-08-18_INSTRUCTION_coa_authority.md
?? PROMPT_claude_code_2026-08-18_commit_handover_7.md
```

Five entries. The brief predicted four.

**On the tracked side the prediction was exactly right.** One modified file and it is
`2026-07-25_CONSOLE_DESIGN.md`. No `.py` file is modified. `CLAUDE.md` does not
appear, which is what the consultant measured and what the stop condition required.
Confirmed independently with `git --no-optional-locks diff --name-only`, which returns
that one path and nothing else.

**The miss is on the untracked side**, and it is one file:
`2026-08-18_INSTRUCTION_coa_authority.md`, 3,901 bytes, repository root. It is a
consultant document written for chat 7 on the same day. The indirect method could not
have seen it: it is untracked, so it appears in neither `.git/index` nor any git
object. That is the honest limit of reading `.git` rather than the filesystem, and it
is a limit in one direction only, which section 6 takes up.

**I read it before asking about it, and that is worth disclosing.** Its subject is the
chart of accounts workstream, which the brief put out of scope. I opened it to find out
what it was, which is how I learned the subject. Nothing from its contents is restated
here and no path inside it is repeated. Paul was asked and chose to include it in this
commit, so it is committed as it stands and read no further.

**No `.git\index.lock` was present.** Checked before the first read; the check returned
`NO index.lock`. Every git read in this session used `--no-optional-locks`.

### The CRLF warnings, which are not modifications

`git diff --name-only` emitted 23 warnings of the form *"in the working copy of 'X',
CRLF will be replaced by LF the next time Git touches it"*, covering `config.py`,
15 test files, three worker modules and two CSV files.

**These are not modifications and none of those files is staged.** The warning says
what git *would* do if it normalised the file; the command still reported exactly one
path. This is the line-ending trap in `CLAUDE.md` showing its face without biting:
`.gitattributes` is `* text=auto eol=lf` and those working-tree files hold CRLF.
Flagged, not fixed, and not part of this commit.

---

## 2. Nothing was lost

Three checks. All programmatic, all quoted whole.

### 2a. Amendment rows, HEAD against working tree

The HEAD copy was inflated to a scratch file with `git show HEAD:...`. Sizes:
**HEAD 349,843 bytes, working tree 350,596 bytes.** Both match the consultant's
figures to the byte.

```
[HEAD] headings matching 'amendment record': [(13, '## Amendment record')]
[HEAD] scope: heading at line 13, section ends at line 177
[HEAD] numbered-row line boundaries: first row at line 21, last row at line 176
[HEAD] row count: 100
[WORK] headings matching 'amendment record': [(13, '## Amendment record')]
[WORK] scope: heading at line 13, section ends at line 177
[WORK] numbered-row line boundaries: first row at line 21, last row at line 176
[WORK] row count: 100
only in HEAD (deleted amendments): []
only in WORK (added amendments):   []
```

**Both lists empty, as predicted.** No amendment was deleted and none was added. This
change edits one existing row.

### 2b. Contiguity, by the corrected method

Scope is bounded to the amendment record's own line boundaries. The section is found by
its heading and closed at the next heading of the same or higher level, so section
13A's findings table cannot be swept in. The comparison is against
`list(range(first, last+1))`, an ordered list, **not a set difference**. Duplicates are
tested explicitly and separately.

```
list boundaries: first=1, last=100; length=100
duplicates (explicit test): []
w_rows == list(range(1, 101)) -> True
```

**Contiguous 1 to 100, no duplicates.**

**On the boundaries, my numbers differ from the consultant's in presentation rather
than in substance.** The consultant reported "boundaries at lines 13 and 178". I report
the heading at **line 13** and the section ending at **line 177**, which is the same
boundary stated as an inclusive last line rather than an exclusive bound. Line 178 is
the first line past the section. Those agree.

**I also print a second pair the consultant did not: the numbered rows themselves run
from line 21 to line 176.** Amendment 1 is at line 21 and amendment 100 at line 176.
The gap from 13 to 21 is the heading, blank lines, and the table's own header and
separator rows. Both pairs are given because the rule in `CLAUDE.md` asks for the
boundaries printed alongside the result, and the row boundaries are the ones that say
what was actually counted. A reader given only 13 and 178 cannot tell whether the
counter found the table at all.

**A note on the check this one replaced.** The old set-difference method would also
have printed a pass here. It would have been a pass for the wrong reason. The value of
the corrected method is not that it gives a different answer today; it is that its
scope is now in the output where it can be read and disbelieved.

### 2c. The change is one line, and it removes nothing

```
git --no-optional-locks diff --numstat -- 2026-07-25_CONSOLE_DESIGN.md
1	1	2026-07-25_CONSOLE_DESIGN.md
```

**Exactly one added and one removed**, as required.

A line-level opcode comparison of the two full files confirms no second change is
hiding elsewhere:

```
line-level opcodes (non-equal): [('replace', 171, 172, 171, 172)]
changed line: HEAD line 172 -> WORK line 172
```

**One opcode, one line each way.** Line 172 in both versions.

Splitting that line on the pipe character gives six cells in both versions, the first
and last being the empty strings either side of the leading and trailing pipes:

| Cell | Expected | Measured | Verdict |
|---|---|---|---|
| Amendment number | same, 96 | `'96'` both sides | **as expected** |
| Section | differs | 34 to 49 chars, **+15** | **as expected** |
| Change | byte-identical, 1,118 chars | 1,118 both sides, identical | **as expected** |
| Why | 4,170 to 4,908 | 4,170 to 4,908, **+738** | **as expected** |

The Section cell, both sides in full:

```
HEAD: 5.5, 13, 13.1, 16 step 12, 18.10
WORK: 5, 5.5, 11.1, 12.3, 13, 13.1, 16 step 12, 18.10
```

Five sections becoming eight. The three added are **5, 11.1 and 12.3**, exactly the
three the commit message names.

**One discrepancy, and it is mine, disclosed rather than quietly corrected.** My
script's first run reported the Change cell as 1,116 characters and the Why cell as
4,168 becoming 4,906, each two short of the consultant's figures. The cause is that I
stripped whitespace from every cell before measuring, which removed one padding space
at each end. Re-measured without stripping, the cells are **1,118** and **4,170 to
4,908**, which are the consultant's numbers exactly. The corrected figures are the ones
tabled above. The wrong ones are recorded here because a report that hides a corrected
error is worth less than one that shows it. **Nothing depended on the difference**, but
it looked like a disagreement for as long as it went unexplained, and a two-character
gap is how a real disagreement would first appear.

### The Why cell contains no deletion

Character-level opcode comparison of the Why cell, HEAD against working tree:

```
insert: HEAD[2399:2399] (0 chars) -> WORK[2399:3137] (738 chars)
deletions: 0  replacements: 0  insertions: 1
inserted 738 chars at WORK offset 2399
```

**One insertion of 738 characters and nothing else.** No deletion, no replacement. The
correction added reasoning and removed none. That was the stop condition, and it is
clear.

### The arithmetic closes

```
HEAD 349,843 bytes, WORK 350,596 bytes, growth 753
accounted: Section 15 + Why 738 = 753
```

**Every one of the 753 new bytes is accounted for by the two cells that changed.**
There is no unexplained byte anywhere in the file.

---

## 3. What is in the commit

Six files, staged by explicit path rather than by `git add -A`:

| File | State before |
|---|---|
| `2026-07-25_CONSOLE_DESIGN.md` | modified, one line |
| `2026-08-17_HANDOVER_consultant_chat_6.md` | untracked |
| `2026-08-18_HANDOVER_consultant_chat_7.md` | untracked |
| `2026-08-18_INSTRUCTION_coa_authority.md` | untracked, unpredicted, added on Paul's decision |
| `PROMPT_claude_code_2026-08-18_commit_handover_7.md` | untracked, this task's brief |
| `2026-08-18_REPORT_claude_code_commit_handover_7.md` | this report |

No `.py` file, no CSV, no database, nothing outside the repository.

---

## 4. Post-commit verification

Six checks were run after the commit and push: the porcelain result, the single commit
on top of `89e0603`, the contiguity re-run against the committed file, the absence of
any `.py` file in `git show --stat`, the one-line-each-way diff against `HEAD~1`, and
step 6's reading of the commit message against the diff.

**Their output is in the session reply to Paul rather than in this file**, for the
reason given at the top: a file inside a commit cannot quote that commit's own hash,
stat or porcelain state, and appending the output afterwards would leave the working
tree dirty and so contradict the porcelain check itself.

## 5. What verification step 6 returned

Step 6 reads the commit message back against `git show --stat` and
`git diff HEAD~1 -- 2026-07-25_CONSOLE_DESIGN.md`, and asks whether the message
describes what the commit actually contains.

**Its result is in the session reply**, with the same reasoning as section 4. The brief
noted that this check has found something on some of its previous uses and that nothing
found is the likely honest answer for a four-file commit describing one changed line.
The reply states what it returned, not what it should have returned.

---

## 6. Answering the consultant's question about the indirect method

The consultant asked whether a starting-state prediction derived from `.git/index` and
two inflated blobs, with no shell on Paul's machine, was right.

**It was right about everything git already knows, and blind to everything git does
not.**

- **Tracked and modified: exact.** One modified file, the right one, and the byte sizes
  of both versions matched to the byte. `CLAUDE.md` was predicted clean and is clean.
  The single changed line was predicted at 172 and is at 172.
- **Untracked: one miss out of four predicted.** A fifth untracked file existed.

The asymmetry is structural rather than bad luck, and it is the useful part of the
answer. `.git/index` is a complete record of the tracked set, so a prediction built
from it can be trusted on tracked files and can even measure them, which is what
inflating the blobs achieved. **But an untracked file leaves no trace anywhere inside
`.git`.** The method therefore has no way to enumerate untracked files at all, and its
untracked list can only ever be a list of the files the consultant already happened to
know about. It cannot be wrong in the other direction: it will never invent an
untracked file, only omit one.

**So the method is sound for "has anything tracked changed" and unsound for "is that
everything".** Worth using again, with the untracked prediction labelled as a list of
known files rather than a measurement. The consultant did label it as a prediction
rather than a measurement, which is why this cost one question and not an incident.

---

## 7. Post-commit evidence for bf59639

Appended 2026-08-18, after `bf59639` was committed and pushed. Sections 4 and 5 above
said this evidence could not sit inside the commit it describes, and pointed to the
session reply. Paul asked for it on disk as well, in a small follow-up commit, which is
the same shape as `0c27dd0` on 2026-08-03.

**The commit and its parent.**

```
bf59639  bf596394f0530830c71a4ad760718211da04d727
parent   89e0603efe8083ba85332830dff3eba5197b8ac2
```

One commit on top of `89e0603`. Pushed fast-forward, `89e0603..bf59639`, no force.

**`git show --stat --format="" bf59639`.**

```
 2026-07-25_CONSOLE_DESIGN.md                       |   2 +-
 2026-08-17_HANDOVER_consultant_chat_6.md           | 234 +++++++++++++++++
 2026-08-18_HANDOVER_consultant_chat_7.md           | 225 +++++++++++++++++
 2026-08-18_INSTRUCTION_coa_authority.md            |  52 ++++
 2026-08-18_REPORT_claude_code_commit_handover_7.md | 279 +++++++++++++++++++++
 PROMPT_claude_code_2026-08-18_commit_handover_7.md | 188 ++++++++++++++
 6 files changed, 979 insertions(+), 1 deletion(-)
```

Six files. No `.py` file, checked by grepping the commit's own file list for `\.py$`,
which returned nothing.

**Porcelain state, immediately before this section was appended.**

```
git --no-optional-locks status --porcelain
```

Returned nothing at all, zero lines. The tree was clean between the two commits.

### The commit message names four of the six files, and was left alone

Verification step 6 compared every filename in `bf59639` against its own message body.
**Four are named: both consultant handovers, the instruction document and this report.
Two are not: `2026-07-25_CONSOLE_DESIGN.md` and
`PROMPT_claude_code_2026-08-18_commit_handover_7.md`.** The design document is described
throughout the message even though its path never appears, so only the brief file is a
real gap. It arose because the supplied message body covered the design document and
the two handovers, while the staging list separately included the brief; the
implementation session extended the message to cover the instruction document and this
report and did not notice the brief was still uncovered.

**Not amended, and deliberately so.** `bf59639` is already pushed, so amending it would
need a force push, which the brief forbade and which is on the Destructive Git
Operations list in `CLAUDE.md`. Paul's decision was that a message naming four of six
files is not worth rewriting published history for. It is recorded here instead, which
is what this section is for.

### One wording change carried forward

Section 2b gave two line-boundary pairs for the amendment record: the section bounds,
lines 13 to 177, and the numbered rows themselves, **lines 21 to 176**. Paul's
instruction is to use the row boundaries from now on, because they are the pair that
states what was actually counted. A reader given only the section bounds cannot tell
whether the counter found the table at all.
