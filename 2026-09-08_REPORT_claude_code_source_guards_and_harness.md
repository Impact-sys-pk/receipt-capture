# Report: source guards parse the tree, and the mutation harness gets a tracked home

**Written 2026-09-08, 13:38 BST (12:38 UTC), by the implementation session in Claude Code.**
**Branch `feat/console-phase0`.**
**Brief: `PROMPT_claude_code_2026-09-08_source_guards_and_harness.md`.**

**All three done. Three commits, none pushed.** `996f65b` the harness, `7edd484` the guards,
`cc6d653` the housekeeping. **No pipeline behaviour changed**, which the brief required: `app.py`,
`config.py` and everything under `worker\` are untouched across all three.

---

## 1. The suite

| When | Result |
|---|---|
| Before, the committed tree at `c5ebfef` | **694 passed, 522 subtests** |
| After all three, at `cc6d653` | **713 passed, 522 subtests** |

**Both measured, at 13:02 and 13:36 BST.**

**Nineteen more passes and the subtest count is unchanged, which is worth a line rather than a
shrug**, because two findings this week came from that number moving. It moved twice here and
returned:

- the harness added 16 tests and 3 subtests, taking it to 710 and 525
- the guard rewrite added 3 tests and removed 3 subtests, taking it to 713 and 522

The three subtests lost are `test_all_three_hash_call_sites_read_the_same_way`'s, which used
`subTest` per call site to run a text window over each. The rewrite asserts once over a collected
list, so the three become one assertion naming every offender. **A subtest per member is the right
shape when each member is checked independently and the wrong one when the claim is about the set.**

---

## 2. Every test that reads `app.py`'s source

**Found by parsing each test module rather than by grepping for `app.py`.** A grep returns the name from
docstrings, which is the fault this whole item is about, and the brief said as much about its own
count.

A module reads `app.py`'s source if it calls `.read_text()` on a path expression naming `app.py` or
`APP_PY`. **Six modules do, at nine places.** Printed whole, before:

```
module                                     reads app.py at   ast.parse at   verdict
test_capture_inbox_cleanup.py              [219]             [218]          PARSES
test_default_firm_id.py                    [218, 232]        []             TEXT MATCH
test_embedded_shared_pipeline.py           [184, 282]        [183, 281]     PARSES
test_one_ranking_both_paths.py             [379, 353]        [352, 381]     PARSES
test_step10f_duplicates.py                 [355]             [357]          PARSES
test_unknown_sender_above_loop.py          [225]             [224]          PARSES
```

**That first pass was not good enough and I nearly stopped there.** `ast.parse()` appearing in the
same function does not mean the **assertion** rests on the tree. So I listed every assertion in every
one of the nine, and one of the six "PARSES" is a hybrid:

| Test | What it asserts on | Verdict |
|---|---|---|
| `test_capture_inbox_cleanup.py::test_nothing_in_app_unlinks_anything_that_arrived_from_outside` | a list of `.unlink()` call nodes | parses |
| `test_default_firm_id.py::test_app_py_passes_no_firm_id_literal` | `source.count('firm_id="INTELLITAX"')` | **text** |
| `test_default_firm_id.py::test_the_count_is_looking_at_the_right_file` | three `in source` / `assertNotIn` checks | **text** |
| `test_embedded_shared_pipeline.py::_loop_calls` | a set of call names from the tree | parses |
| `test_embedded_shared_pipeline.py::test_every_intake_path_uses_the_retry_wrapper` | two lists of call line numbers | parses |
| `test_one_ranking_both_paths.py::test_neither_email_loop_moves_the_email_on_an_outcome` | a list of call nodes inside two loops | parses |
| `test_one_ranking_both_paths.py::test_both_loops_feed_one_outcome_list` | a count of call nodes | parses |
| `test_step10f_duplicates.py::test_all_three_hash_call_sites_read_the_same_way` | call sites from the tree, then `assertIn(..., window)` over three lines of text | **hybrid, counted as text** |
| `test_unknown_sender_above_loop.py::_positions` | comparison nodes inside two loops | parses |

**So three of nine were converted and six already parsed.** After:

```
test_capture_inbox_cleanup.py              [219]             [218]          PARSES
test_default_firm_id.py                    [239]             [239, 317]     PARSES
test_embedded_shared_pipeline.py           [184, 282]        [183, 281]     PARSES
test_one_ranking_both_paths.py             [379, 353]        [352, 381]     PARSES
test_step10f_duplicates.py                 [371]             [370]          PARSES
test_unknown_sender_above_loop.py          [225]             [224]          PARSES
```

### What each conversion does now

**`test_app_py_passes_no_firm_id_literal`** walks the tree for any call passing a **string literal**
as `firm_id`. **Wider than the text it replaces**, which looked only for `firm_id="INTELLITAX"`: the
fault was one firm's intake history landing in two files because two writers were handed different
words, and a second literal would do it again.

**`test_the_count_is_looking_at_the_right_file`** becomes four tests, because it was doing four
things. The tree defines `_log_receipt`; `config.UNATTRIBUTED_FIRM_ID` is read somewhere;
`config.DEFAULT_FIRM_ID` is read nowhere; and a fourth asserting directly that **a comment naming the
constant is not a use**, so a future rewrite back to a string match fails on the thing that went
wrong rather than on a technicality. It is renamed to `test_the_tree_is_the_right_file_and_is_not_empty`,
since there is no count any more.

**`test_all_three_hash_call_sites_read_the_same_way`** now requires the **statement following** each
`find_by_hash()` assignment to contain an `is_recorded_and_filed()` call. One rule covers both shapes
`app.py` uses: `if existing and repo.is_recorded_and_filed(existing):` on the two email paths, and
`if existing:` with the check nested inside on the folder-intake path. Searching the whole following
statement rather than only its condition is what makes one rule do both.

### One guard left as a text match, and why

**None over `app.py`.** All nine now parse.

**But `test_default_firm_id.py` holds a second class, `DeadResolverIsGoneTest`, which text-matches
`worker/database/repository.py`** for `resolve_client_by_code`. **It is out of this brief**, which
asked about `app.py`, and I have left it. It is flag 1.

---

## 3. The prose mutation, before and after

**Run with the new harness, which is what section 2 of the brief is for.** Two mutations, each a
comment of exactly the kind this project writes: one naming `config.DEFAULT_FIRM_ID` to say it is
deliberately not used, one quoting `firm_id="INTELLITAX"` to record what a line used to say. Both
inserted at the embedded unknown-sender branch, where the real incident happened.

**Against the old guards:**

```
=== prose-names-default-firm-id ===
one place changed: 1 hunk(s), 2 line(s)
    +                    # An earlier version passed config.DEFAULT_FIRM_ID here and it
    +                    # was wrong; see amendment 128.
last line: 1 failed, 709 passed, 525 subtests passed
caught by 1 reported failure(s):
  FAILED tests/test_default_firm_id.py::NoHardcodedFirmIdTest::test_the_count_is_looking_at_the_right_file

=== prose-quotes-the-firm-literal ===
    +                    # This used to read firm_id="INTELLITAX", which split the
    +                    # intake event log into two files for one firm.
last line: 1 failed, 709 passed, 525 subtests passed
caught by 1 reported failure(s):
  FAILED tests/test_default_firm_id.py::NoHardcodedFirmIdTest::test_app_py_passes_no_firm_id_literal
```

**Against the new ones, both prose mutations pass:** `713 passed, 522 subtests`, `NOTHING CAUGHT IT`.

**"Nothing caught it" is the pass condition here and the harness reports it as a failure**, exiting
1, because for every other mutation it is the alarm. Worth knowing before reading the output: for a
prose mutation the alarm and the answer are the same line.

**The control, because a guard that stops noticing prose must not stop noticing use.** Three real
mutations against the new guards:

| Mutation | Caught by |
|---|---|
| `_unused = config.DEFAULT_FIRM_ID` added as code | `test_app_py_does_not_read_the_fallback_firm_id` |
| `firm_id="INTELLITAX"` passed to `_log_receipt()` | `test_app_py_passes_no_firm_id_literal`, plus five behavioural tests |
| `firm_id` passed instead of `UNATTRIBUTED` | five behavioural tests |

**The third is caught by behaviour and not by the presence guard, and that is correct rather than a
gap.** `test_app_py_names_the_unattributed_firm_id` asks whether the constant is read **anywhere**,
and `app.py` reads it in more than one place, so removing one use leaves it satisfied. Its own
comment says it exists so the absence test cannot be satisfied by a file naming neither. **A presence
check is not a per-site check and should not be read as one.**

---

## 4. Where the harness lives, and why there

**`tests/mutation_harness.py`, committed at `996f65b`, with `tests/test_mutation_harness.py` beside
it.**

**Why `tests\`.** It is test infrastructure, and that directory already holds three non-collected
helpers on the same basis: `live_paths.py`, `resolution_fixtures.py` and `chart_fixtures.py`. **The
name is not `test_*`**, so pytest does not collect it and `tests/test_logs_isolation.py`'s
process_once guard, which globs `test_*.py`, does not sweep it either. **`.gitignore` covers none of
`tests\`**, checked against its eight entries rather than assumed.

**What it does, which is what `CLAUDE.md` now requires of every mutation.** Applies to a pristine
copy, refuses an anchor that does not match exactly once, prints the unified diff beside the result,
runs the whole suite, restores, and asserts the restore is byte for byte inside a `finally`.

**`replace_once()` is the load-bearing part and its message distinguishes the two failures**, because
they have different fixes. Nothing matched usually means the code moved, and the message says to read
the file rather than loosen the anchor. Two matched usually means indentation, and the message says
so: a line indented n spaces is a substring of the identical line indented more. **That is the trap
`app.py`'s two email loops set, and it caught this project twice on 2026-09-08 alone.**

**It is tested, because this is the one piece of infrastructure whose failure would be invisible in
the reports it produces.** Sixteen tests: the refusal on nought and on two matches, the indentation
trap by name, that nothing is written before the anchor is checked (asserted on the modification
time, since a write-then-restore leaves the content identical), that the file comes back byte for
byte even when the command exits non-zero, that a callable edit changing nothing is refused, and that
the harness imports nothing from the pipeline. **None of them runs the real suite**: each passes its
own trivial command, so they cost milliseconds and cannot recurse into pytest.

**It was used for real in this brief**, for the five mutations in section 3, which is the first thing
I did with it.

---

## 5. The root, checked against step 10h's eighteen names

**All eighteen present before anything moved**, which is what that step requires: a name on the list
that is not in the root means a file has been moved or renamed and the step stops. Enumerated one by
one from the folder listing rather than counted, and `2026-09-05_DESIGN_receipt_accounts.md` is the
eighteenth, added on 2026-09-08 by amendment 276. The eighteenth entry is a rule rather than a name,
the consultant handover with no successor, which is session 17.

**The root held 32 markdown files. Fourteen were not on the list**, classified by kind:

- **eleven Claude Code reports**, spent on delivery
- **two consultant handovers**, sessions 15 and 16, both with successors
- **one brief**, this one, spent on delivery of this report

**Thirteen moved with `git mv` in `cc6d653`.** Two of the thirteen were untracked, so `git add` ran
first and they show as additions rather than renames; the other eleven show `R100`. **No name
collided with anything already in `archive\`**, checked before the move.

**The root now holds 19: the eighteen and this brief**, which goes with the report.

**This report is itself spent on delivery** and is the obvious candidate for the next pass. I have
left it in the root because the brief names that path for it and because the consultant session reads
it next; archiving a document in the same turn that writes it would contradict the instruction that
put it there.

---

## 6. My own mistakes

**Three, all caught by my own runs.**

1. **My first enumeration would have reported the wrong answer.** It classified a module as parsing
   if `ast.parse()` appeared in the same function, which is true of
   `test_all_three_hash_call_sites_read_the_same_way` and tells you nothing: that test parses to find
   the call sites and then asserts on **three lines of text**. **Presence of a parse is not the same
   claim as an assertion resting on one**, and I nearly reported five text matches as six parsers. It
   was caught by listing every assertion rather than every `ast.parse`, which is the enumerate-the-set
   rule applied to what the assertions do rather than to which files they are in.
2. **My first rewrite of that guard counted one call site eleven times.** `ast.walk()` reports a call
   against every enclosing compound statement, so the `for`, the `with` and the `try` all claimed it:
   `[1053, 1077, 1106, 1339, 1544, 1116, 1424, 1609, 1157, 1639, 1175]` where three were expected.
   The rewrite now excludes a statement's nested blocks when asking whether the statement itself holds
   the call. **The test failing loudly with eleven line numbers is what a good failure message buys.**
3. **A docstring in the harness had an invalid escape sequence**, `` `tests\` ``, which pytest
   surfaced as a `SyntaxWarning` rather than an error. Fixed before the commit and confirmed with
   `python -W error::SyntaxWarning`.

**And one habit corrected rather than a mistake.** I stopped using shell heredocs for content
containing backslash escapes after they mangled Python string literals three times yesterday, and
used the editing tools throughout today. Nothing was mangled.

---

## 7. Flags

### Flag 1: `DeadResolverIsGoneTest` text-matches `repository.py`, which is the same fault one file over

`tests/test_default_firm_id.py`'s second class reads `worker/database/repository.py` as a string and
counts `resolve_client_by_code`, then checks `'def resolve_client_info(' in source` and
`'def resolve_client_id(' in source` to prove it is reading the right file.

**It is out of this brief**, which asked about `app.py`, and I left it deliberately rather than by
oversight. **It has the same weakness**: a comment in `repository.py` mentioning
`resolve_client_by_code`, which is exactly the kind of comment this project writes when it deletes
something, would fail it. `worker/filing.py` already carries such a comment about two other deleted
functions, and `worker/database/repository.py` carries one about `find_by_transaction()`.

**Small and obviously right: the same conversion, three or four lines**, and the class's own docstring
already says "a text count is the only available assertion", which is no longer true. **Say the word.**

### Flag 2: the harness's exit code inverts for a prose mutation

`main()` returns 1 when nothing caught a mutation, which is right for every mutation whose point is
to be caught. **A prose mutation's point is to pass**, so the harness reports success as failure.

**Not fixed**, because a flag on the mutation would be a design decision about the harness's contract
and this brief asked me to build the harness rather than to design a taxonomy for it. **Reported so
the next reader of that output is not misled**, which section 3 also says in place.

---

## 8. What the brief got wrong

**Nothing.** Its account of the three incidents matched what I found, its warning about its own grep
was well placed, and `.gitignore` covers none of the path it suggested.

**One thing to add.** The brief asks which guards already parsed "so the report records the shape of
the problem rather than only the fix". **The shape is more interesting than a count of six against
three**: every guard written this week parses, and every one written before this week matches text.
The convention changed partway through and nothing went back over the older ones. The hybrid is the
transitional case, written on 2026-09-07, which parses to find its subjects and then falls back to
text for the assertion.

---

## 9. Confidence

**High that every guard over `app.py`'s source now parses.** It rests on the enumeration being taken
from each test module's syntax tree rather than from a grep, on listing every assertion in all nine
rather than trusting the presence of `ast.parse()`, and on two prose mutations that failed before and
pass after.

**High that the conversions did not weaken anything**, and it rests on three real mutations still
being caught, one of them by the converted guard specifically.

**High that the harness does what `CLAUDE.md` requires**, and it rests on sixteen tests over its own
behaviour, including that nothing is written before a bad anchor is refused and that the file returns
byte for byte when the command exits non-zero.

**High that the root is correct after the move**, and it rests on checking all eighteen names one by
one before moving anything and listing the root afterwards.

**This says nothing about guards over files other than `app.py`.** Flag 1 is the one I know of, found
in the same file I was already editing, and I have not swept the other test modules for text matches
against `config.py`, `repository.py` or anything under `worker\`.
