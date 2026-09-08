# Brief: source guards parse the tree, and the mutation harness gets a tracked home

**Written 2026-09-08 by the consultant session, on Paul's decision the same day.**
**Report to `2026-09-08_REPORT_claude_code_source_guards_and_harness.md` in this repository root.**

---

## 0. Read the induction first, and it is not this brief

**`CLAUDE.md`, the section "How this project is worked", and the seven traps.** It is the working
method: who does what, what standard of evidence is expected, and how to write for the operator.
**Six rules were added to its standard-of-evidence section on 2026-09-08 and four of them come from
this week's own failures.** They are the practices this work is measured against, and the first item
below is one of them.

**Then `2026-07-25_CONSOLE_DESIGN.md`. Read section 18 before the body**, then section 16, the build
order. The amendment record at the top carries every decision with its reasoning.

**This brief is small on purpose.** Nothing in it changes the pipeline's behaviour.

## 1. Source guards parse the syntax tree rather than string-matching the source

**This is the flag from `2026-09-08_REPORT_claude_code_embedded_unknown_sender_event.md`, and it is
the third instance of one pattern in two days.** `tests/test_default_firm_id.py`'s guard
string-matches `app.py` for `config.DEFAULT_FIRM_ID` and **failed on a comment explaining why that
constant is deliberately not used.** The comment was reworded to get past it, which is the wrong way
round. The other two instances were guards that failed on their own docstrings, quoting the sentence
they were asserting absent.

**Why it keeps happening here rather than anywhere else.** This project's convention is that
superseded wording is kept beside the correction rather than deleted, and every rule carries the
incident that produced it. **So the prose is always a few lines from the code, and a check on what
the code does must never read prose about that code.**

**What has to be true when you are done.** Every test that asserts something about `app.py`'s source
does it by parsing, not by matching text.

**Enumerate the set before you change any of it, and print the enumeration whole.** Do not take a
count from me: I ran a grep for `app.py` across `tests\` and it matched files that only mention it in
a docstring, which is the same fault this item is about. **Exclude `.history\`**, which is gitignored
VS Code local history and holds a dated copy of every file you have edited.

**Some of this week's guards already parse the tree.** Say which did and which did not, so the report
records the shape of the problem rather than only the fix.

**One judgement is yours.** A guard that genuinely is about the text, if there is one, stays as it
is. **Say which you left and why.**

## 2. The mutation harness gets a tracked home

**It does not exist on disk.** `scratchpad/` is absent and nothing under it is tracked, so the next
session that needs a mutation rebuilds it from nothing. **It has been rebuilt at least five times
already**, judging by the name `scratchpad/mutate5.py` in your own report of 2026-09-08.

**What it has to do, which is what `CLAUDE.md` now requires of every mutation:** apply to a pristine
copy, anchor on something unique, **assert the anchor matches exactly once and refuse if it does
not**, print the unified diff beside the result, run the whole suite, restore, and assert the restore
is byte for byte.

**Give it a tracked path and commit it.** Where it lives is yours; `tests\` is the obvious candidate
and it is not the only one. **Say where you put it and why**, and make sure `.gitignore` does not
already cover that path: it ignores `data/`, `logs/`, `exports/`, `Claude outputs/`, `Backups/`,
`.history/` and `.claude/settings.local.json`.

**Its own commit, separate from section 1's.**

## 3. Out of scope

- **Item 174** of `2026-08-20_LIST_outstanding_items_and_decisions.md`, the missing
  `is_duplicate(message_id, att_id)` check on the embedded-image path. It stays absent.
- **Every outstanding sub-step of step 10f.** Twenty-five are outstanding and none is in this brief.
- **Section 18.2b's freeze stands.** `get_client_directory()`, `file_receipt()` and
  `make_enriched_sidecar()` are not edited.
- **No pipeline behaviour changes at all.** If a guard's rewrite would need one, stop and report it.

## 4. Housekeeping, and it needs `git mv`

**The Cowork sandbox cannot run git writes**, per the third trap in `CLAUDE.md`, so this is yours.

**Spent files leave the root with `git mv` so their history follows them**, per `CLAUDE.md`. Spent
means executed and superseded: a report is spent on delivery, and a handover once its successor
exists.

- **The Claude Code reports in the repository root.** Enumerate them and move the spent ones.
- **`2026-09-06_HANDOVER_consultant_session_15.md` and
  `2026-09-07_HANDOVER_consultant_session_16.md`** both have successors and are spent.
- **`2026-09-07_HANDOVER_consultant_session_17.md` stays.** Its successor does not exist yet.
- **The eighteen files named in step 10h stay**, and `2026-09-05_DESIGN_receipt_accounts.md` joined
  that list on 2026-09-08 by amendment 276. **Check the root against those eighteen names and stop if
  one of them is missing**, which is what that step requires.

**Its own commit.**

## 5. Standard of evidence

- **Red before green** where a test can be red. A guard that already passes for the wrong reason
  cannot be, so **mutate instead**: put a plausible piece of prose into `app.py` and show the
  string-matching guard fails and the parsing one does not.
- **Print every enumeration whole rather than counting it.**
- **Mutations anchored to one place with the diff printed.** The harness from section 2 is what does
  this, so section 2 lands first and section 1 uses it.
- **Quote passes and subtests separately.** Two findings this week came from a subtest count moving
  while the pass count rose.
- **Flag, do not fix.** Anything wrong this brief did not ask about gets reported. **If it is small
  and obviously right, say so and offer to do it in the same reply.**
- **Disclose your own mistakes, including ones you caught and corrected.**
- **State a confidence level, say what it rests on, and say what it is about.**

## 6. What the report has to carry

`2026-09-08_REPORT_claude_code_source_guards_and_harness.md`, in this repository root.

1. The enumeration of every test asserting something about `app.py`'s source, printed whole, with
   which parsed and which matched text.
2. Any guard you left as a text match, and why.
3. The prose mutation showing the old guard fails and the new one does not.
4. Where the harness now lives, why there, and its commit.
5. The root checked against step 10h's eighteen names, and what moved.
6. The suite, passes and subtests, measured both ends.
7. Anything you flagged, and anything this brief got wrong.
