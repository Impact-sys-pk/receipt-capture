# Report: the section 18 citations a person reads, 2026-09-18

Written by the implementation session, Claude Code, 2026-09-18, 16:38 BST, read off the clock in the
reply that states it. Zone established rather than assumed: `date` gave `GMTDT`, `date -u` gave
`15:38 UTC`, so this shell's local time is Europe/London and needs no conversion.

Worked from `PROMPT_claude_code_2026-09-18_section_18_citations_in_python.md`.

**Nothing in `2026-07-25_BUILD_STATUS.md` or `2026-07-25_CONSOLE_DESIGN.md` was touched.** Both are
the consultant session's.

---

## 1. My own enumeration, and it agrees with five

**Agreed: five person-facing citations across three files.** Enumerated from the syntax tree, not
from the brief, and not from a text search.

The set walked is the string arguments of logging calls and of `raise` statements, across every
production `.py` file git tracks. The output of my own enumerator, run against the tree before any
edit:

```
config.py:807 [raise] 'section 18' in '. There is no default: a trigger the pipeline does not
    understand, read as one it does, writes a document into a client folder, and section 18.2b says
    a copy is never withdrawn. The case is exact. '
worker/client_copy.py:671 [log] '18.2b' in 'receipt %s already has a client folder copy at %s, so
    none is written: a copy is made once and never withdrawn, per 18.2b'
worker/resolution/service.py:1722 [log] '18.2a' in '... The document store still holds the archive
    of record, per 18.2a'
worker/resolution/service.py:1729 [log] '18.2a' in '... The document store still holds the archive
    of record, per 18.2a'
worker/resolution/service.py:1739 [log] '18.2a' in '... The document store still holds the archive
    of record, per 18.2a'
TOTAL person-facing citations: 5
```

**The total of 72 also agrees, and so does the per-file split.** Counted over the whole file text,
comments and docstrings included, which is how the previous report counted it:

| File | Before | After |
|---|---|---|
| `config.py` | 17 | **16** |
| `worker/client_copy.py` | 13 | **12** |
| `worker/resolution/service.py` | 10 | **7** |
| `worker/filing.py` | 6 | 6 |
| `capture_report.py` | 6 | 6 |
| `app.py`, `worker/line_items.py`, `worker/publish.py` | 3 each | 3 each |
| `worker/attached.py`, `worker/database/schema.py`, `worker/validation/rules.py` | 2 each | 2 each |
| `worker/categorisation/fallback.py`, `worker/database/repository.py`, `worker/extraction/base.py`, `worker/extraction_pipeline.py`, `worker/storage/store.py` | 1 each | 1 each |
| **Total** | **72** | **67** |

**72 became 67, and the five that went are the five named.** Each carried exactly one reference, so
nothing was swept in and nothing was missed.

**One disagreement, and it is about the file count rather than the reference count.**
`git ls-files "*.py"` excluding `tests/` returns **58 files, not 57**. The difference is
`docs/specs/categorisation_engine.py`, which is a specification rather than production code and holds
no section 18 reference, so the 72 and the 67 are the same number either way. Reported rather than
reconciled.

**Every match was read whole rather than counted.** All 72 are genuine section 18 citations; the
regex caught no version number or money amount masquerading as one.

---

## 2. The new citation, and what in section 20.1 it was matched to

**`section 20.1` in all five.** The sentence around it is unchanged in every case.

| Rule | Where it now lives, read in `2026-07-25_CONSOLE_DESIGN.md` on 2026-09-18 |
|---|---|
| The copy is never withdrawn, ex `18.2b`. `config.py` and `worker/client_copy.py` | Section 20.1, the bullet list headed **The Clients folder copy, in full**: "**Unposting does not withdraw the copy.** Written once, never withdrawn, and a repost does not duplicate it." |
| The archive of record, ex `18.2a`. The three discard log lines in `worker/resolution/service.py` | Section 20.1, the paragraph headed **The archive**: "Intellibills. One file per document, never changed once written." |

**Why `20.1` and not something finer.** Section 20.1 has named paragraphs and no numbered rules, so
there is no sub-number to cite. A person sent to 20.1 finds both rules stated in terms.

**Why `section 20.1` rather than bare `20.1`.** `config.py`'s message already read "section 18.2b",
so that one is like for like. The other four read "per 18.2a" or "per 18.2b", and "per section 20.1"
was chosen over "per 20.1" for the same reason the brief gives for repointing at all: the message is
read in a log file by someone who is not looking at the source, and a bare number is harder to act on.

**What the messages do not say, and it is unchanged.** None of the five names the document. They
said "18.2b" before and they say "section 20.1" now. Changing that would be rewording, which the
brief forbids. Flagged in section 5 below.

---

## 3. What changed, in full

**Five message strings, one new test file, one addition to the shared AST helper.** Nothing else.

| File | Change |
|---|---|
| `config.py` | One f-string part in the `RuntimeError` on a bad `client_copy_trigger`: `section 18.2b` to `section 20.1` |
| `worker/client_copy.py` | The "already has a client folder copy" log line: `per 18.2b` to `per section 20.1` |
| `worker/resolution/service.py` | Three discard log lines: `per 18.2a` to `per section 20.1` |
| `tests/source_guards.py` | Two functions added, `tracked_production_files()` and `person_facing_messages()`. Nothing existing was changed |
| `tests/test_retired_section_citations.py` | New. The guard and four scope assertions |

**One thing I did beyond a like-for-like swap, disclosed rather than buried.** The
`worker/client_copy.py` log line came to 81 characters once `18.2b` became `section 20.1`, so I
rewrapped it across three string literals instead of two. **The message a person reads is byte for
byte what the swap produced**; only where Python joins the adjacent literals moved. The file already
holds 40 lines over 79 characters, so this was tidiness and not a rule.

**The 67 are untouched**, including the struck-through 18.2, 18.2a and 18.2b citations in
`output_dir_for()`'s docstring in `capture_report.py`, and including `config.py`'s two docstrings that
cite 18.2b in `_client_copy_trigger()` and `_classifier_enabled()`. **The second of those is asserted
by the guard's own scope test**, so a later sweep that removed them would turn that test red rather
than pass quietly.

**The two the brief named as looking person-facing and not being so are untouched and are not in the
guarded set**, checked: `worker/database/schema.py`'s two inside `SCHEMA_SQL` are `--` comments
within the SQL string, and `worker/extraction/base.py`'s is an attribute-documenting string. Neither
is a logging argument nor a raise.

---

## 4. Evidence

### 4.1 Red before green

The guard was written first and run against the unchanged tree. Its failure named all five and was
produced by the AST walk rather than by my grep:

```
E  AssertionError: 5 message(s) a person reads cite a retired section of
   2026-07-25_CONSOLE_DESIGN.md. Section 18 was retired entire on 2026-09-16 by amendment 498, so
   there is nothing at the other end. Repoint it at the section that carries the rule today, or move
   the sentence into a comment, which is not covered here and is not meant to be:
     config.py:807 cites 'section 18' in '...'
     worker/client_copy.py:671 cites '18.2b' in '...'
     worker/resolution/service.py:1722 cites '18.2a' in '...'
     worker/resolution/service.py:1729 cites '18.2a' in '...'
     worker/resolution/service.py:1739 cites '18.2a' in '...'
FAILED tests/test_retired_section_citations.py::NoRetiredSectionReachesAPersonTest
FAILED tests/test_retired_section_citations.py::WhatTheGuardCoversTest::test_a_docstring_citing_a_retired_section_is_not_covered
2 failed, 3 passed in 0.33s
```

After the five edits: `5 passed in 0.21s`.

### 4.2 The suite

`.\.venv\Scripts\python.exe -m pytest -q`

**1592 passed, 1 skipped, 1191 subtests passed in 126.71s**, on 2026-09-18 after the change. The
five new tests are in that figure. **Nothing was removed and no existing test changed.**

**This is the count before the commit, and the brief is right that it is the weaker claim**, because
this change adds a file and `tracked_production_files()` shells out to `git ls-files`. The guard
sweeps production files and the file it adds is a test, so it cannot miss itself, but the rule is
there for a reason and the post-commit run is reported in section 7.

### 4.3 Mutations

Four, through `tests/mutation_harness.py`, each anchored, each asserted unique before anything was
written, each run against the whole suite, each restored byte for byte. Diffs as printed by the
harness.

**1. `citation-back-in-the-client-copy-log-line`. Expected caught, and was.**

```
one place changed: 1 hunk(s), 2 line(s)
    -            "per section 20.1",
    +            "per 18.2b",
last line: 1 failed, 1591 passed, 1 skipped, 1191 subtests passed
caught by 1 reported failure(s):
  FAILED tests/test_retired_section_citations.py::NoRetiredSectionReachesAPersonTest
verdict: OK: caught, as expected
restored, byte for byte
```

**2. `citation-back-in-the-runtimeerror`. Expected caught, and was. This is the one that matters**,
because a guard written around logging calls alone passes it, and because the citation sits inside an
f-string rather than a plain literal.

```
one place changed: 1 hunk(s), 2 line(s)
    -            f"folder, and section 20.1 says a copy is never withdrawn. The "
    +            f"folder, and section 18.2b says a copy is never withdrawn. The "
last line: 2 failed, 1590 passed, 1 skipped, 1191 subtests passed
caught by 2 reported failure(s):
  FAILED tests/test_retired_section_citations.py::NoRetiredSectionReachesAPersonTest
  FAILED tests/test_retired_section_citations.py::WhatTheGuardCoversTest::test_a_docstring_citing_a_retired_section_is_not_covered
verdict: OK: caught, as expected
restored, byte for byte
```

**3. `citation-back-in-a-discard-log-line`. Expected caught, and was.**

```
one place changed: 1 hunk(s), 2 line(s)
    -                "of record, per section 20.1",
    +                "of record, per 18.2a",
last line: 1 failed, 1591 passed, 1 skipped, 1191 subtests passed
verdict: OK: caught, as expected
restored, byte for byte
```

**4. `citation-added-to-a-comment-must-survive`. Expected to survive, and did. This one measures the
scope**, which is the whole point of the split: the guard must be blind to the 67 that stay.

```
one place changed: 1 hunk(s), 3 line(s)
    -            # REFUSED or FAILED on the data file alone. The document is already
    +            # REFUSED or FAILED on the data file alone. Section 18.2a, 18.2b.
    +            # The document is already
last line: 1592 passed, 1 skipped, 1191 subtests passed
caught by 0 reported failure(s):
verdict: OK: survived, as expected
restored, byte for byte
```

### 4.4 The guard cannot pass by covering nothing

`CLAUDE.md`'s rule that a check which never returns anything but a pass has stopped being a check.
`WhatTheGuardCoversTest` holds four assertions open, and they are assertions rather than prose:

- **The docstring citations in `config.py` are present and are invisible to the guard.** It asserts
  both halves, so if somebody later sweeps those docstrings the test fails saying it is measuring
  nothing.
- **A logging call is read**, checked against the `worker/client_copy.py` line this change repointed.
- **An f-string inside a `raise` is read**, checked against `config.py`'s `RuntimeError`.
- **`parser.error()` is not mistaken for a logger.** argparse's method shares a name with
  `logging.error` and this project calls it five times. See section 5.

---

## 5. Flagged, not fixed: other places a section number reaches a person

**The brief asked for anything else in the repository that puts a section number in front of a person
and is not a comment, a docstring or a test. There are four, and none cites section 18, so nothing
here is broken.** Enumerated from the syntax tree over every non-docstring string constant in all 58
tracked production `.py` files, then each one read.

| Where | What it says | State |
|---|---|---|
| `config.py`, three `RuntimeError` messages in the firm readers | "see amendment 117 and section 1 of 2026-09-01_DESIGN_cloud_multi_firm.md" | Live, and it names its document, which the five repointed ones do not |
| `worker/resolution/service.py:527`, a `logger.warning` | "which 12.2 says is absent for a {action} note" | Section 12.2 exists, "Location and format". Live |
| `worker/resolution/service.py:425`, inside a `raise ResolutionNoteError` | "12.2 forbids strings for amounts." | Live. In the guarded set already, so a retirement of section 12 would be caught by adding `"12"` to `RETIRED_SECTIONS` |
| `worker/client_copy.py:306`, a `ClientCopyRemoval` refusal detail | "this function does not resolve 12.2's practice-root convention" | Live. **Outside the guarded set**, because it is a returned value that a log line later prints rather than a logging argument |

**The last row is the finding worth acting on and I have not acted on it.** The guard reads logging
calls and raises, which is the set the brief names. A refusal detail string is neither, and it
reaches `run.log` all the same, through the caller that logs it. **The obvious fix, offered rather
than made:** nothing, for now. Widening the set to every string constant would sweep the 67 comments
and docstrings straight back in, and there is no cheap way to tell a returned message from a returned
value. The narrow alternative is to add the `ClientCopyRemoval` and `ResolutionNote` detail
constructors to `person_facing_messages()` by name, which is two lines and would be worth doing if a
section they cite is ever retired. **Your call.**

**One more surface, with nothing wrong in it.** `parser.error()` is called five times across the root
scripts and reaches a person on stderr. None of the five carries a section number. It is deliberately
outside the guarded set, and the test above records that as a decision rather than an accident.

**Nothing outside the `.py` files.** The 25 tracked non-Python, non-Markdown files are test fixtures,
`requirements*.txt`, dotfiles, `.claude/settings.json` and one CSV. None puts a section number in
front of anybody. `IntelliBooks-Desktop-v3.html` and `IntelliBooks.bat` are not in this repository and
I did not read them.

**The Markdown files were not swept**, because they are documents rather than running messages, and
because the brief's disclosure already records what is in them.

---

## 6. Mistakes I made, disclosed

**One, and it changed nothing in the result.** I first tried to write the new test file with a shell
heredoc and the shell rejected it with an unmatched-quote error at line 156, so I wrote it with the
file tool instead. **I did not check whether a partial file reached the disk**, and I should have.
The failure was a parse error, which happens before any redirection runs, so nothing should have been
written; that is reasoning rather than a reading. What is established is that the file written
afterwards is the whole file, because the suite imports it and the guard runs.

**And a near miss worth naming.** My first scratch enumerator was called `enum.py` and shadowed the
standard library's `enum`, so `import re` failed inside `subprocess`. It was renamed. Had it run and
silently produced a short list I would have had a count I could not trust, which is this project's
truncation rule in a different costume.

---

## 7. Confidence

- **That the five person-facing citations are the complete set: high.** Enumerated from the syntax
  tree across all 58 tracked production files, not from a grep, and the guard that now holds it open
  found the same five independently of the enumerator. The residual risk is the scope decision itself
  rather than the enumeration: a message that reaches a person by some fourth route is outside the set
  by design, and section 5 names the one I found.
- **That 72 became 67, and that the five that went are the five named: high.** Counted the same way
  before and after, per file, and the three per-file drops are exactly 1, 1 and 3.
- **That the five messages are otherwise unchanged: high**, from reading the diff, which is five
  lines plus the rewrap disclosed in section 3.
- **That section 20.1 carries both rules: high, because I read section 20.1 of
  `2026-07-25_CONSOLE_DESIGN.md` on 2026-09-18** and quoted both sentences in section 2 above. **What
  this confidence is about is that the wording is there today**, not that 20.1 is the citation you
  would have chosen; that part is my judgement and it is section 2's to argue.
- **That the file count is 58 and not 57: high**, from `git ls-files`. **What I cannot settle is
  which of us means what by "production"**, and it makes no difference to the reference count.
- **That the guard covers what it claims and not more: high**, from the four mutations, three caught
  and one surviving, each restored byte for byte.
- **That the suite is green at 1592 passed, 1 skipped, 1191 subtests: high** before the commit;
  section 8 carries the run after it.

---

## 8. The commit, and the run after it

Proposed, not made. Awaiting a yes, per the brief.

```
fix(citations): the five section 18 references a person reads point at 20.1

Section 18 was retired entire on 2026-09-16 by amendment 498. 72 references
remained in production Python. Paul's decision of 2026-09-18 splits them: the
five that reach a person in a log line or a traceback are repointed at section
20.1, which carries both rules; the 67 in comments and docstrings stay, because
each records a decision taken while section 18 said something.

A new guard walks the string arguments of logging calls and raise statements
across every tracked production file and refuses a retired-section citation. It
does not read comments or docstrings, which is the whole of the scope.

Files: config.py, worker/client_copy.py, worker/resolution/service.py,
tests/source_guards.py, tests/test_retired_section_citations.py
Suggested branch: feat/console-phase0 (current)
```

**No push and no PR proposed.** `feat/console-phase0` is the current branch and two other sessions
commit to it.

**The suite will be run again immediately after the commit and this section updated with the
result**, because the change adds a file and `tracked_production_files()` reads the git-tracked set.
