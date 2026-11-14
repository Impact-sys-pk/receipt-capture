# Report: a failed email move stops being silent

Claude Code. Worked from `PROMPT_claude_code_2026-09-16_failed_email_moves.md`,
written 2026-09-16, which is Paul's decision of 2026-09-16 on the flag in
`2026-09-16_REPORT_claude_code_inbox_pair_moves.md`.

**The work was done on 2026-09-17**, read off the clock. This session has run
past midnight and the brief and its decisions are dated the 16th, which is
correct for them. Nothing here is back-dated. `CLAUDE.md` records a batch of 34
amendments misdated by exactly this.

**`2026-07-25_BUILD_STATUS.md` was not touched.**

**Files changed:** `app.py`, and `tests/test_email_move_failures.py` added.

**Commit:** `fa57195`, made on Paul's approval. Section 10.

---

## 1. What a failed move now causes

**Report question 3, in one sentence a person could act on:**

> **The email stays in INBOX, the run's `email_moves_failed` count goes up by one
> in `runs.ndjson`, and the next run tries the move again.**

Before: the email stayed in INBOX, one warning was written to `run.log`, nothing
counted it, and if it was a no-attachment email it was never moved again.

---

## 2. The mechanism, and how it was held to one

**Report question 1.** `app._move_email(uid, folder, stats)`, a module-level
helper beside `_worst_outcome_folder()`. It is **the only caller** of
`move_email_to_folder()`:

```python
def _move_email(uid, folder: str, stats: dict) -> bool:
    moved = move_email_to_folder(uid, folder)
    if not moved:
        stats["email_moves_failed"] = stats.get("email_moves_failed", 0) + 1
    return moved
```

**Why a helper rather than five treatments**, which is the brief's constraint and
my own report's argument about the statement branch: five explicit treatments
are correct today and silently wrong at the sixth call site. This is the pattern
`extract_with_transient_retry()` already follows, and `CLAUDE.md` records what
happened without it: that wrapper was used by three of the four intake paths for
weeks, and every per-path test passed.

**How it is held, on the source rather than by intention.** `TheCallSitesTest`
walks the syntax tree over the 57 production files and asserts four things:

1. `move_email_to_folder()` is called in **exactly one place**.
2. That one place is inside `_move_email()`.
3. **No call to it discards the result** as a bare expression statement.
4. **The number of `_move_email()` calls is five**, listed in the failure
   message, so a sixth is a decision rather than an accident.

**A fifth test asserts the helper takes `stats`**, because without it the helper
could log and count nothing and the first three would still pass.

### `stats` is the mechanism, and the counter is stated up front

`"email_moves_failed": 0` goes into the initial `stats` dict with the other
counters, and `_log_run()` writes `**stats` into `runs.ndjson`. **Stated rather
than left to appear on first use**, for the reason sub-step 10f.38 already gives
for `attached_recorded`: a run summary with a fixed shape lets a reader tell
nought from a field this version of the code does not write.
`test_a_clean_run_reports_nought_rather_than_omitting_the_key` holds it and the
`counter-not-initialised` mutation proves it bites.

### It does not log the failure a second time

`move_email_to_folder()` already logs each failure with the uid and the folder.
What was missing is the run's own account of itself, and a second line per
failure would double the noise for no new information.

### One correction to my own guard

**The first version of `test_no_call_to_the_raw_function_discards_the_result`
asked about the helper as well as the raw function, and that is the wrong rule.**
The helper exists precisely so the five sites do not each have to listen, and
none of them needs the answer: every one either `continue`s or ends its branch,
and there is nothing useful to do differently in the moment. Requiring each to
take the bool would be five treatments again, which is the thing the helper
replaced. **The brief says it about `move_email_to_folder()` and the brief is
right.**

---

## 3. Is the count five?

**Report question 2, from my own enumeration and not from the brief: yes, five.**

Walked from the syntax tree over `app.py`, the root scripts and everything under
`worker\`, 57 files, printing the enclosing function, the enclosing loop and
**how the result is used**:

| Where | Loop | Folder | Result |
|---|---|---|---|
| `app.py:1555` | 1511, no-attachment | `INBOX.Unknown Sender` | **discarded** |
| `app.py:1712` | 1511, no-attachment | `outcome_folder` | **discarded** |
| `app.py:1738` | 1511, no-attachment | `INBOX.No Attachments` | **discarded** |
| `app.py:2045` | 1990, message | `INBOX.Unknown Sender` | **discarded** |
| `app.py:2184` | 1990, message | `outcome_folder` | **discarded** |

**Five calls, five discarded**, which is the brief's count and its claim. The
enclosing-loop column is there because `CLAUDE.md` records that a call inside a
loop and outside one are two different behaviours; here all five are inside one
of the two email loops.

**One call in the tests**, `tests/test_email_dedup_identity.py:68`, and it
already assigns the result. Not touched.

**After the change: one production call**, `app.py:208`, inside `_move_email()`,
assigned to `moved`.

**Deliverable one added no sixth site.** The already-alerted branch was written
as an `if/else` with the move below both, rather than as a second call before a
`continue`. One site, and the `no-retry` mutation shows the behaviour is really
there.

---

## 4. Deliverable one: how the retry is shaped

```python
if repo.has_alert_been_sent(message_id, "no_attachment"):
    logger.info(f"alert already sent for {message_id}, retrying the move")
else:
    ...resolve the sender, send the alert, record it...

_move_email(uid, "INBOX.No Attachments", stats)
```

**The `continue` is gone.** The alert happens once and the move happens every
time. The already-alerted check is untouched in what it tests; only where it sits
relative to the move has moved, which is what the brief asked.

**Why the retry cannot misfire, as tests rather than as a paragraph.**
`move_email_to_folder()` copies, flags `\Deleted` and expunges, so a second move
of a uid that has gone has nothing to copy and returns False. And an email that
moved is not in INBOX, so `fetch_emails_without_attachments()` never offers it
again. **Only an email still in INBOX can be retried**, which is exactly the
failed case.

`test_the_retry_can_never_move_one_email_twice` runs three polls with two
failures and asserts **exactly one attempt succeeded**.
`test_a_move_that_worked_is_not_tried_again` runs two polls with no failures and
asserts one attempt in total.

**The cost, which Paul accepted rather than discovered**: a move that keeps
failing, say because the folder has been renamed, retries on every run and logs
every time. Noisier than silence, and silence is what produced an email nobody
knew about.

---

## 5. Evidence

### 5.1 The stub models the real function

**This is the part the brief singles out and it decides whether any of the rest
means anything.** `Mailbox` in the new test file has three properties, each read
off `worker/email/reader.py`:

- **An email is fetched only while it is still in INBOX.** A move that worked
  takes the email out of the next poll's results, which is what makes
  "not tried again" a real assertion rather than a coincidence.
- **A move copies, flags `\Deleted` and expunges.** A second move of a uid that
  has gone returns False.
- **A failed move leaves the email exactly where it was**, because the real
  function returns before flagging anything when the copy does not respond OK.

**A stub that recorded every call as a success would hide this defect and report
the fix as broken.** `CLAUDE.md`, 2026-09-08, and `Routes._move()` in
`tests/resolution_fixtures.py` carries the same lesson from the same incident.
`Mailbox` is written fresh rather than reusing `Routes`, because `Routes` has no
no-attachment route and cannot make a move fail.

### 5.2 Red before green

Against the unchanged `app.py`, **`11 failed, 2 passed`**:

```
FAILED ...::TheStrandedEmailIsRetriedTest::test_a_failed_move_is_attempted_again_on_the_next_run
FAILED ...::TheStrandedEmailIsRetriedTest::test_it_keeps_trying_until_it_works
FAILED ...::TheStrandedEmailIsRetriedTest::test_the_retry_can_never_move_one_email_twice
FAILED ...::TheRunCountsFailedMovesTest::test_a_clean_run_reports_nought_rather_than_omitting_the_key
FAILED ...::TheRunCountsFailedMovesTest::test_a_failed_move_is_counted
FAILED ...::TheRunCountsFailedMovesTest::test_the_count_is_this_run_and_not_a_running_total
FAILED ...::TheRunCountsFailedMovesTest::test_two_failures_in_one_run_count_twice
FAILED ...::TheCallSitesTest::test_every_site_goes_through_the_helper
FAILED ...::TheCallSitesTest::test_no_call_discards_the_result
FAILED ...::TheCallSitesTest::test_the_helper_takes_the_stats_dict
FAILED ...::TheCallSitesTest::test_the_raw_function_is_called_once_and_only_by_the_helper
```

with, among others:

```
AssertionError: 5 != 1 : move_email_to_folder() should be called in exactly one
place, the helper that counts its failures. Found: ['app.py:1738 in
process_once()', 'app.py:2045 in process_once()', 'app.py:2184 in
process_once()', 'app.py:1555 in process_once()', 'app.py:1712 in
process_once()']
```

**The two that pass are correct to pass.**
`test_the_alert_is_sent_once_however_many_runs_it_takes` is true under either
behaviour and is the guard that the fix does not start double-alerting.
`test_a_move_that_worked_is_not_tried_again` is likewise true either way and is
there so the retry cannot be satisfied by moving every email on every poll.

**One test was renamed after that run.**
`test_no_call_discards_the_result` became
`test_no_call_to_the_raw_function_discards_the_result` when its rule was
corrected, per section 2. It was red before and after the rename; the red above
is quoted under the old name because that is what was run.

**After the change: `13 passed`.** Whole suite: **`1565 passed, 1 skipped, 1185
subtests passed in 164.22s`**, up from 1552 by the thirteen.

### 5.3 Mutations

Run with `tests/mutation_harness.py`, which refuses an anchor that does not match
exactly once, applies to a pristine copy, runs the **whole** suite, restores and
asserts the restore is byte for byte. All five anchors were counted before the
run rather than discovered by a refusal mid-run.

| Mutation | What it does | Outcome |
|---|---|---|
| `no-retry` | puts the `continue` back above the move | **caught**, 3 |
| `bare-call-at-one-site` | one site stops using the helper | **caught**, 6 |
| `helper-counts-nothing` | the increment becomes `pass` | **caught**, 3 |
| `counter-not-initialised` | the key is dropped from the stats dict | **caught**, 2 |
| `prose-only` | rewords one docstring line | **survived**, as required |

The brief named the first two. The other three are one per thing the change
claims: that the counter is incremented, that it is initialised, and that a
comment is only a comment.

**Every failure across all five is in `tests/test_email_move_failures.py`.**
Nothing else in the 1,565-test suite notices any of them, which is the measure of
how silent this was.

**`no-retry` is the deliverable-one revert** and it is caught by exactly the
three tests that need more than one poll to see anything:

```
FAILED ...::TheStrandedEmailIsRetriedTest::test_a_failed_move_is_attempted_again_on_the_next_run
FAILED ...::TheStrandedEmailIsRetriedTest::test_it_keeps_trying_until_it_works
FAILED ...::TheStrandedEmailIsRetriedTest::test_the_retry_can_never_move_one_email_twice
```

**`test_the_alert_is_sent_once_however_many_runs_it_takes` does not fail under
it**, and that is right: putting the `continue` back stops the retry without
double-alerting anybody. A test that failed there would mean the alert guard and
the move were tangled.

**`bare-call-at-one-site` is caught six times, and the split is the point.**
Three are the source guards and **three are behavioural**:

```
FAILED ...::TheCallSitesTest::test_every_site_goes_through_the_helper
FAILED ...::TheCallSitesTest::test_no_call_to_the_raw_function_discards_the_result
FAILED ...::TheCallSitesTest::test_the_raw_function_is_called_once_and_only_by_the_helper
FAILED ...::TheRunCountsFailedMovesTest::test_a_failed_move_is_counted
FAILED ...::TheRunCountsFailedMovesTest::test_the_count_is_this_run_and_not_a_running_total
FAILED ...::TheRunCountsFailedMovesTest::test_two_failures_in_one_run_count_twice
```

**A bare call is not merely untidy, it stops counting**, so the guard and the
behaviour agree about what is wrong rather than the guard asserting a
convention. That is worth having: a source guard nothing behavioural backs is a
rule about style.

**`counter-not-initialised` is the one a reader would have shrugged at.**
Dropping `"email_moves_failed": 0` changes nothing when a move fails: the
counter is created by `stats.get(..., 0) + 1` on first use and the number is
still right. What it changes is a **clean** run, which then omits the field
entirely, so a reader of `runs.ndjson` cannot tell nought from a version of the
code that did not count. Caught by
`test_a_clean_run_reports_nought_rather_than_omitting_the_key`.

---

## 6. What did not change

- **`move_email_to_folder()` itself.** Not edited. It returns the right thing and
  logs the right thing; the brief is about the callers.
- **The already-alerted check.** One alert per email, and
  `test_the_alert_is_sent_once_however_many_runs_it_takes` holds it across three
  polls.
- **Which folder each call site targets.** The five folders are unchanged, and
  the enumeration in section 3 lists them before and after.

---

## 7. Flags. Not fixed.

### 7.1 The other four sites have the same silence, and now they count

This is not a flag so much as a consequence worth stating: **deliverable one
fixes the retry for one of the five sites only.** The other four still make one
attempt per email and, if it fails, the email stays in INBOX.

**For three of them that is already self-correcting**, because the email is still
in INBOX and the next poll fetches it again and reaches the same branch: the
unknown-sender sites and the two `outcome_folder` sites all re-derive their
answer from the email itself. **The no-attachment site was the odd one out**
precisely because `has_alert_been_sent()` short-circuited it, which is why it was
the one that stranded.

**No change recommended.** The other four already retry by construction, and the
count now makes a persistent failure visible rather than silent.

### 7.2 `_worst_outcome_folder()` returning None is indistinguishable from a failure

`if outcome_folder: _move_email(...)` at two sites. When the ranking returns None
the email is deliberately not moved, which is correct and documented. **But a run
where nothing moved because the outcome was unrankable looks identical, in
`runs.ndjson`, to a run where nothing needed moving**: neither increments
anything.

**The obvious fix is a second counter**, say `email_moves_skipped`, incremented
where `outcome_folder` is falsy. **Not made**: it is outside this brief, and
whether an unrankable outcome is worth counting is a decision rather than a
default. The function's own docstring says None has two meanings, and only one of
them is interesting.

### 7.3 Nothing reads `runs.ndjson`

`email_moves_failed` now leaves the run, which is what the brief asked for. **It
leaves it into a file nothing reads yet.** `pipeline-status.json` is what
IntelliBooks Desktop reads, and it carries five keys, none of them this. The
console's intake panel at 8.6 is not built.

**No change recommended and this is not an argument against the counter**: the
number being recorded is the precondition for anything reading it, and the
alternative was not recording it. Flagged so nobody expects a failed move to show
up on a screen today. **It shows up in `C:\Intellibills\logs\runs.ndjson`, one
JSON object per run.**

---

## 8. Mistakes I made, disclosed

1. **My first version of the call-site guard demanded that the five sites use the
   helper's return value.** That is five treatments again, which is the thing the
   helper exists to replace, and it is not what the brief asked. Corrected before
   the change was written, so no production code was shaped by it. Section 2.
2. **I renamed a test after taking the red**, so the red output quotes a name
   that no longer exists. Section 5.2 says which, rather than silently quoting
   the new name against the old run.

---

## 9. Confidence

- **That a failed move is now retried: high**, from two and three-poll tests
  through a real `app.process_once()` with only the mailbox replaced, and from a
  mutation that puts the `continue` back.
- **That the retry cannot move one email twice: high**, and it rests on the stub
  modelling the real function rather than on reading the IMAP code: three polls,
  two failures, exactly one success.
- **That there are five call sites and one mechanism: high.** Enumerated from the
  tree before and after, printed whole, and re-derived by `TheCallSitesTest` at
  every run.
- **That a persistent failure is now visible: medium, and the limit is 7.3.** It
  is visible in `runs.ndjson` and in `run.log`. It is not visible on any screen,
  because nothing reads either.
- **That `move_email_to_folder()` returning False is the real failure mode:
  medium.** I read its body and its docstring; **I have not seen an IMAP move
  fail on this system**, and there is no record of one. The stranded email this
  fixes is a path I reasoned to from the code, not one anybody has observed.

---

## 10. The commit. Made on 2026-09-17, on Paul's approval.

**`fa57195` on `feat/console-phase0`, two files, 507 insertions and 23
deletions.** Nothing pushed, no branch created.

**The suite was run again afterwards**, because this adds a file and two source
guards sweep the git-tracked set rather than the working tree:
**`1565 passed, 1 skipped, 1185 subtests passed in 104.70s`**.

**One docs commit landed from the consultant session while the mutations ran**,
`5970a8c`, touching `2026-07-25_BUILD_STATUS.md` and
`2026-07-25_CONSOLE_DESIGN.md` only. Checked before committing; it touches
nothing here.

**No difference from the message proposed below.**

The message as committed:

```
fix(email): a failed move is retried, and every run counts the failures

move_email_to_folder() returns False and logs a warning rather than raising.
All five of its callers discarded that bool as a bare expression statement,
enumerated from the syntax tree, so a failed move was silent.

An email with no attachments was worst affected. It got its alert, the row was
written, and then the move was attempted; if the move failed the email stayed
in INBOX and every later run passed over it at the already-alerted check,
before the move was reached. Never re-alerted, which is right, and never
re-moved, which is not. The check is now an if/else with the move below both
branches, so the alert happens once and the move happens every time, and the
site count stays at five.

The retry cannot misfire: move_email_to_folder() copies, flags \Deleted and
expunges, so a second move of a uid that has gone returns False, and an email
that moved is not in INBOX for the next poll to fetch. Only an email still in
INBOX can be retried, which is exactly the failed case.

_move_email() is now the one caller, and it counts a failure into the run's
stats, which _log_run() writes into runs.ndjson. email_moves_failed is stated
in the initial dict so a clean run reports nought rather than omitting the
field. One helper and not five treatments, because five are correct today and
silently wrong at the sixth site; the guard asserts on the source that no
unwrapped call remains and that the number of wrapped ones is five.

Files: app.py, tests/test_email_move_failures.py

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

**Two files.** The four reports and this brief are untracked and are not in the
commit.
