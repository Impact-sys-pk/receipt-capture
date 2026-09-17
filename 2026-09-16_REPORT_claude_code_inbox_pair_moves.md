# Report: the statement branch leaves the inbox pair behind

Claude Code, 2026-09-16. Worked from
`PROMPT_claude_code_2026-09-16_inbox_pair_moves.md`, which is Paul's decision of
2026-09-16 on the finding in
`2026-09-16_REPORT_claude_code_statement_end_to_end.md`.

**`2026-07-25_BUILD_STATUS.md` was not touched.**

**Files changed:** `app.py`, and `tests/test_statement_inbox_pair.py` added.

**Commit:** proposed at the end, not made.

---

## 1. The mechanism, and how "exactly once" is held

**A `try/finally` around the statement branch, opened after the
duplicate-by-hash check.**

```python
if intake.is_statement:
    statement_client_id = intake.client_id or config.UNKNOWN_CLIENT_ID
    if repo.find_statement_by_hash(intake.file_hash, statement_client_id):
        ...
        _move_inbox_pair_to_processed(intake)      # unchanged, still the only
        ...                                        # call on this path
        continue

    try:
        ...  the three branches, unchanged  ...
    finally:
        _move_inbox_pair_to_processed(intake)
```

**Why a `finally` and not three calls.** The receipt path already uses one and
its comment gives two reasons: the failure branch copies the original into Review
first so the move has to come after it, and a `finally` covers both branches
without repeating the call. **The first reason applies here** — both Review
branches call `file_review()` before they leave. **The second is the one that
decided it**: three explicit calls would be correct today and silently wrong the
day somebody adds a fourth branch, which is exactly how this defect arrived.
There were two branches when 10d.55 was written and three when I found it.

**How "exactly once" is held: the `try` opens below the duplicate check, so that
branch never enters it.** `continue` runs an enclosing `finally` on its way out,
so a `try` wrapped round the whole statement branch would have moved the
duplicate's pair twice.

**And that could not have been caught by looking at the files.**
`_move_inbox_pair_to_processed()` returns early when neither the document nor the
sidecar still exists, so a second call writes nothing and leaves an identical
folder. `ExactlyOnceTest` replaces the function with a spy that records the call
and then calls the real one, and asserts the recorded list is exactly one
filename. Four tests, one per branch.

`test_the_processed_folder_holds_one_pair_and_not_two` sits beside them as the
observable half. It cannot catch a double call on its own, and it can catch a
mechanism that moves the file and then copies it back, which the call count
cannot.

### The diff is a pure reindent plus the wrap, and that is checked rather than claimed

`app.py` is CRLF throughout, and the change reindents 56 lines, so it was applied
with a script that asserts both anchors match exactly once and writes the file
back in its own line-ending convention. A second script then compared the removed
and added lines with their leading whitespace stripped:

```
removed lines: 54
added lines:   95
every removed line reappears, in order, with only its indentation changed
added lines that are genuinely new: 41   (39 comment lines, `try:`, `finally:`
                                          and one call)
reappearing lines whose indent did not grow by exactly four: 0
```

**No existing line changed other than its indentation.**

### One consequence of choosing `finally`, stated rather than left implicit

**An exception inside the branch now moves the pair before it propagates.** That
is the same guarantee the receipt path's `finally` gives, and it is a change from
today, where an exception left the pair behind.

**It is an improvement rather than a cost, and here is the case.** If
`file_statement()` succeeded and `repo.save_statement()` then raised, the old
behaviour left the pair in the inbox with no `statements` row, so the next poll
found no hash match, re-filed it, and `_unique_path()` wrote `uber_2026-04-05-2.pdf`
into the client folder. Every poll, for ever. The same unbounded growth this
change is fixing, in a different folder. The new behaviour leaves both copies on
disk, no row, and no retry, which is a thing an operator can find.

**Nothing swallows the exception.** No `except` was added: the poll still dies
the way it does today.

---

## 2. Does anything outside the statement branch share the gap?

**Report question 2. Inside the folder-intake loop, no: every exit is now
covered.** Enumerated from the syntax tree of the changed file, asking for each
exit whether a move call is a direct statement on the path that reaches it, or in
the `finally` of an enclosing `try`:

```
continue at 1762: moved at line 1759, directly on this path      (duplicate)
continue at 1808: moved by the finally of the try at line 1798   (unresolved client)
continue at 1814: moved by the finally of the try at line 1798   (missing metadata)
continue at 1854: moved by the finally of the try at line 1798   (filed)
continue at 1880: moved at line 1877, directly on this path      (receipt duplicate)
end of the loop body: moved by its own finally at line 1988      (receipt path)
uncovered exits: none
```

There are no `break` and no `return` statements in that loop.

### The email side: one thing worth flagging, and it is milder

The analogous question is whether a message can leave a branch without being
moved out of INBOX, because `fetch_new_messages()` searches `ALL` on every poll
and deduplicates on the header `message_id`, so an unmoved message comes back
every five minutes.

**I flagged five candidates and four of them are not exits at all.** They are
`continue` statements of the **inner attachment loop**, which my first walk
attributed to the enclosing message loop. Read individually: `app.py:1591`,
`:2067`, `:2078` and `:2097` all end one attachment and carry on with the next,
appending to `email_outcomes`, which is then ranked once per message. That is
10f.33 working as designed.

**The two conditional `move_email_to_folder(uid, outcome_folder)` calls are
deliberately conditional** and both carry a comment saying so: `None` means do
not move, because either the duplicate branch has already moved the email or the
unknown-sender branch moves it itself.

**The one that survives reading is `app.py:1719`:**

```python
if repo.has_alert_been_sent(message_id, "no_attachment"):
    logger.info(f"alert already sent for {message_id}, skipping")
    continue
```

**That branch neither alerts nor moves.** It is reached only when a previous poll
recorded the alert and the message is still in INBOX, which means the
`move_email_to_folder(uid, "INBOX.No Attachments")` at the end of that branch
failed. That function **returns `False` and logs a warning rather than raising**,
at `worker/email/reader.py:205`, and its return value is not checked at the call
site. So the message is stranded: never re-alerted, which is right, and never
re-moved, which is not.

**It is much milder than what this change fixes.** One email sits in INBOX with
one log line per poll. No file is written, nothing accumulates, and no count
climbs.

**The obvious fix is one line: move the email in that branch too, before the
`continue`.** The alert has already been sent, so the destination is the same
`INBOX.No Attachments`, and the guard's purpose, not alerting twice, is
untouched. **Not made, and it is a decision rather than a default**: silently
retrying a move that failed once is a different policy from reporting it, and
neither is in this brief.

---

## 3. Evidence

### 3.1 Red before green

`tests/test_statement_inbox_pair.py`, 14 tests, driven through a real
`app.process_once()` with only the mailbox and the extractor replaced.

**The red was taken twice and only the second is quoted.** The first was taken
before I corrected three assertions that compared a file list against a
hand-written order: `files_under()` sorts, and a sidecar sorts before its
document. So the first red describes a file that no longer exists. The second was
taken by putting `app.py` back to its committed state, running, restoring, and
asserting the restore was byte for byte:

```
=== app.py reverted to HEAD ===
FAILED tests/test_statement_inbox_pair.py::EveryStatementExitMovesThePairTest::test_a_filed_statement_leaves_the_inbox
FAILED ...::EveryStatementExitMovesThePairTest::test_a_statement_whose_client_cannot_be_resolved_leaves_the_inbox
FAILED ...::EveryStatementExitMovesThePairTest::test_a_statement_with_no_platform_leaves_the_inbox
FAILED ...::EveryStatementExitMovesThePairTest::test_a_statement_with_no_week_ending_leaves_the_inbox
FAILED ...::EveryStatementExitMovesThePairTest::test_the_duplicate_branch_still_leaves_the_inbox
FAILED ...::ExactlyOnceTest::test_a_filed_statement_moves_the_pair_once
FAILED ...::ExactlyOnceTest::test_a_missing_metadata_branch_moves_the_pair_once
FAILED ...::ExactlyOnceTest::test_a_review_branch_moves_the_pair_once
FAILED ...::ExactlyOnceTest::test_the_processed_folder_holds_one_pair_and_not_two
FAILED ...::TheReviewCopiesStopAccumulatingTest::test_a_filed_statement_is_not_counted_as_its_own_duplicate
FAILED ...::TheReviewCopiesStopAccumulatingTest::test_a_statement_missing_metadata_is_reviewed_once
FAILED ...::TheReviewCopiesStopAccumulatingTest::test_an_unresolvable_statement_is_reviewed_once_and_not_once_a_poll
FAILED ...::TheReviewCopiesStopAccumulatingTest::test_the_flag_is_counted_once_rather_than_once_a_poll
13 failed, 1 passed in 0.97s

=== app.py restored, byte for byte ===
```

**The one that passes is `test_the_duplicate_branch_moves_the_pair_once`**, and
it is the one branch that was already right. That is the shape a correct red
should have here: every test that asserts the new property fails, and the test
that asserts the unchanged property does not.

Two of the failure messages are the behaviour itself rather than a path
comparison:

```
AssertionError: 3 != 1 : 3 polls wrote 3 copies into Review:
  ['UNKNOWN/stmt_uber_2026-04-05_ab12cd-2.pdf',
   'UNKNOWN/stmt_uber_2026-04-05_ab12cd-2.pdf.review.json',
   'UNKNOWN/stmt_uber_2026-04-05_ab12cd-3.pdf',
   'UNKNOWN/stmt_uber_2026-04-05_ab12cd-3.pdf.review.json',
   'UNKNOWN/stmt_uber_2026-04-05_ab12cd.pdf',
   'UNKNOWN/stmt_uber_2026-04-05_ab12cd.pdf.review.json']

AssertionError: 1 != 0 : the second poll flagged the same statement again
```

**After the change: `14 passed`.**

### 3.2 Mutations

Run with `tests/mutation_harness.py`, which refuses an anchor that does not match
exactly once, applies to a pristine copy, runs the **whole** suite, restores and
asserts the restore is byte for byte.

| Mutation | What it does | Outcome |
|---|---|---|
| `unresolved-client-branch-not-covered` | slides `try:` down past the first Review branch | **caught**, 4 failures |
| `both-review-branches-not-covered` | slides `try:` down past both Review branches | **caught**, 8 failures |
| `no-branch-covered` | the `finally`'s call becomes `pass` | **caught**, 13 failures |
| `duplicate-branch-moved-twice` | a second explicit call in the duplicate branch | **caught**, 1 failure |
| `prose-only` | rewords one comment line | **survived**, as required |

**Every failure across all five, without exception, is in
`tests/test_statement_inbox_pair.py`.** That is the "and no others do" the
standard asks for, and it is an unusually clean answer: **nothing else in the
1,539-test suite notices any of these**, which is why the defect survived from
10d.55 until yesterday.

**The count scales with how much coverage is removed**, 4 then 8 then 13, and the
tests that drop out are the right ones each time. Removing coverage from the
first Review branch alone fails exactly the four tests about that branch;
removing it from both fails those four plus the four about the second; removing
it everywhere fails all thirteen that assert the new property. **The one test that
never fails in the first three is
`test_the_duplicate_branch_moves_the_pair_once`**, because that branch's call is
untouched by all of them.

**`duplicate-branch-moved-twice` is caught by exactly one test in the whole
suite**, and it is the one the brief asked for by name:

```
=== duplicate-branch-moved-twice ===  expects: caught
one place changed: 1 hunk(s), 1 line(s)
    +                    _move_inbox_pair_to_processed(intake)
last line: 1 failed, 1538 passed, 1 skipped, 1175 subtests passed
caught by 1 reported failure(s):
  FAILED tests/test_statement_inbox_pair.py::ExactlyOnceTest::test_the_duplicate_branch_moves_the_pair_once
verdict: OK: caught, as expected
```

**That is the whole argument for counting calls rather than looking at the
folder.** The mutated code moves the pair, then moves it again; the second call
returns early and writes nothing, so every path, file and row is identical and
only the call count differs. One test in 1,539 can tell.

**`prose-only` survived**, so no guard reads this file's comments as code, which
matters because the change added 39 comment lines.

### Two notes on the mutation set, stated rather than glossed

**The first two report two hunks, not one.** Sliding `try:` past a block is a
removal and an insertion, so `difflib` sees two hunks for one logical edit. The
harness's uniqueness refusal still did its job: each is a single
`replace_once()` on one anchor, and the anchor was asserted to match exactly once
before anything was written.

**Two anchors had to carry neighbouring text, and that is the trap `CLAUDE.md`
records twice.** The statement duplicate branch and the receipt duplicate branch
are byte-identical for three lines including
`_move_inbox_pair_to_processed(intake)`, at the same indentation, and the
`finally`'s call sits at that indentation too: the bare line appears **three
times** in `app.py`, counted rather than assumed. The unique text is the word
"statement" in the duplicate branch's log message, and the `# moves.` comment
above the `finally`'s call. All five anchors were counted before the run rather
than discovered by a refusal mid-run.

### 3.3 The suite

Whole suite with the change and the new file, before the mutations:
**`1539 passed, 1 skipped, 1175 subtests passed in 143.01s`**, up from 1525 by
the 14 new tests.

---

## 4. What did not change

- **The duplicate-by-hash branch.** Not inside the `try`, not edited, and
  `test_the_duplicate_branch_still_leaves_the_inbox` and
  `test_the_duplicate_branch_moves_the_pair_once` hold both halves of it.
- **What `file_review()` writes.** Untouched. This change is about the pair in
  the inbox; the Review copy is the same copy it always was, and there is now one
  of it instead of one per poll.
- **The receipt branch.** Untouched, and the whole-suite run is the evidence:
  `tests/test_inbox_processed_move.py` has eight tests over it and all pass.

---

## 5. Mistakes I made, disclosed

1. **Three assertions compared a sorted file list against a hand-written order**,
   so the first green run failed on the order rather than on the behaviour. The
   fix was `sorted()` round the expected list, and it invalidated the first red,
   which I re-took rather than quoted. Section 3.1.
2. **My first walk of the email loops reported five uncovered exits and four of
   them were not exits.** I selected "innermost loops containing a move", then
   used `ast.walk` to find `continue` statements inside them, which returns the
   ones belonging to nested loops that contain no move. I found it by reading
   each of the five rather than by trusting the output, which is the habit step
   10aj's report says I only acquired because a probe disagreed with me.
3. **The same walk reported the end of the folder-intake loop body as uncovered**,
   which is the receipt path's own `try`. My test for "covered" never asked
   whether the statement itself was a `try` whose `finally` moves the pair.
   Patched, and the corrected run is what section 2 quotes.

**The pattern in all three is the same and it is worth naming**: I wrote a check,
read its output as a finding, and had to be argued out of it by the code. Two of
the three were caught only because the output looked surprising enough to read.

---

## 6. Confidence

- **That every exit from the statement branch now moves the pair exactly once:
  high.** Fourteen tests through a real poll, a syntax-tree walk over every exit
  of that loop, and a mutation per branch.
- **That no existing line of `app.py` changed except its indentation: high**, and
  it is measured rather than eyeballed: every removed line reappears in order and
  every one gained exactly four spaces.
- **That the Review copies stop accumulating: high**, from a three-poll test that
  failed with three copies before the change and passes with one after.
- **That nothing outside the statement branch shares the gap: medium.** I
  enumerated the folder-intake loop exhaustively and the two email loops by hand
  after my walk misled me. **I did not enumerate every other loop in the
  pipeline**, and `app.py` is 2,200 lines. What I claim is about the intake loop
  and the two email loops, not about the file.
- **That `app.py:1719` strands an email: medium.** The code path is plain and
  `move_email_to_folder()` returning `False` without raising is read off its own
  docstring and body. **I have not seen it happen**, and a failed IMAP move may be
  rare enough never to have occurred.

---

## 7. The commit. Made, on Paul's approval of 2026-09-16.

**`0982ed9` on `feat/console-phase0`, two files, 456 insertions and 54
deletions.** Nothing pushed, no branch created.

**Step 10aj went in first, as `8af9b8f`**, on Paul's instruction: it had been
approved at 15:31 and the approval never reached this session, so its file had
been sitting untracked. The two commits are independent and were made in that
order because 10aj's work came first.

**The suite was run again after each**, because both add a file and two source
guards sweep the git-tracked set rather than the working tree:
**`1539 passed, 1 skipped, 1175 subtests passed`** after `8af9b8f`, and the same
after `0982ed9`.

**One difference from the message proposed below**: the `Suggested branch:` line
was dropped, because a commit made on that branch does not need it. Everything
else is as proposed.

The message as committed:

```
fix(statement): every exit from the statement branch moves the inbox pair

Three of the five continue statements in the folder-intake loop left the
document and its sidecar in the Receipt Inbox, and all three were in the
statement branch: the two Review branches and the success path. The receipt
path's try/finally is below them and is never entered from there.

Two of the three never corrected themselves. file_review() uses
_unique_path(), so a statement whose client cannot be resolved, or whose
sidecar carries no platform or week ending, wrote a fresh copy into Review on
every poll, -2, -3 and onwards, 288 a day on the five-minute default, with
review_flags_issued climbing beside them. The third left the pair behind and
the next poll matched its own hash, which counted every statement the system
ever filed as its own duplicate.

A try/finally around the branch, opened after the duplicate-by-hash check so
that branch's explicit call stays the only one on its path. A finally rather
than three calls, which is the receipt path's shape and the half of its
reasoning that matters here: a fourth branch is covered without anybody
remembering. Exactly once cannot be seen on disk, because the mover returns
early when neither file is left, so the tests count the calls.

No existing line changed other than its indentation.

Files: app.py, tests/test_statement_inbox_pair.py
Suggested branch: feat/console-phase0 (the current branch)

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

**Two files, and step 10aj's is not one of them.** That file went in separately as
`8af9b8f`. **`tests/test_statement_inbox_pair.py` was written self-contained and
imports nothing from it**, deliberately, because at the time this was built 10aj
had not landed and might not have. That decision is recorded in the new file's
own module docstring and it is the reason this work was never blocked by the
missed approval.

**The reports and the two later briefs are untracked and are not in either
commit.**
