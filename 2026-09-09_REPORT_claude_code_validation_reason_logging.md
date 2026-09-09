# Report: the reason a receipt did not reach `ok` goes into the log

**Claude Code, 2026-09-09. Executed from `PROMPT_claude_code_2026-09-09_validation_reason_in_the_log.md`.**

**Confidence that the three deliverables are built and working: high, and what that rests on is
eighteen tests driving a real `app.process_once()` across four arrival routes and four statuses, six
mutations each caught by the tests that should have caught them, one mutation that had to survive and
did, and the full suite read whole rather than in a tail.** What it is confidence **about** is the
behaviour of `worker\extraction_pipeline.py` under pytest. **It is not confidence that a live
pipeline run has produced the line**, because I have not started the pipeline and cannot. The
rendered line in section 3 below is the format applied to real strings, and it is labelled as such.

---

## 1. What was built

**One function and one call, both in `worker\extraction_pipeline.py`. 61 lines added, none removed,
and no other production file touched.**

`report_validation_outcome(receipt_id, client_id, status, notes)`:

- Returns `None` and logs nothing when the status is `ok`.
- Otherwise joins the notes with `", "`, which is exactly what `save_extraction()` does, logs one
  `WARNING`, and **returns that same string**.

The call sits immediately before the existing `_log_receipt()` call at the end of
`process_extraction_result()`, and its return value is passed as `review_reason=`.

**The module had no logger of any kind before this**, so `logging` and
`logger = logging.getLogger(__name__)` are new. A `WARNING` on the name `worker.extraction_pipeline`
is now this line and nothing else, which is what made the tests cheap to write.

### Why the return value feeds the event log rather than a second build of the string

Decision 1 of the brief says the notes are logged verbatim, and gives the reason: two wordings for
one condition is how a search for the reason stops finding it. **Two builders of one string is the
same failure a step later.** So the function returns what it logged, and the event log takes that.
`tests\test_validation_reason_logged.py::OneCallSiteTest` holds it on the syntax tree: one call to
`report_validation_outcome()` in the whole module, and the `_log_receipt()` call carries a
`review_reason` keyword.

### Why the call is at the end and not in either filing branch

**The status is overridden twice after `validate()` returns.** The semantic duplicate check makes it
`possible_duplicate`, and the unresolved-client gate of 10d.16 and 10d.18 makes it `needs_review`
with a reason of its own. The end of the function is the first point at which the status is final.
Two tests pin this behaviourally, and a mutation moving the call up to just after
`validation = validate(extraction)` is caught by both.

---

## 2. Deliverables, against the brief

| # | Deliverable | Where it is held |
|---|---|---|
| 1 | Every non-`ok` receipt produces one `run.log` line carrying receipt id, client id, status and notes, at `WARNING` | `TheReasonIsInTheLogTest`, seven tests: `failed`, `needs_review`, `possible_duplicate`, the client gate, a two-note receipt, and the folder and embedded-image routes |
| 2 | The same reason reaches the ndjson event log through `review_reason` | `TheSameReasonReachesTheEventLogTest`, three tests, plus the two-note test asserting the event log entry equals the database string |
| 3 | An `ok` receipt logs no such line | `AnOkReceiptSaysNothingTest`, one test carrying its own control |
| Set claim | Every status but `ok` logs a reason, over the set rather than its members | `EveryStatusIsAccountedForTest`, statuses enumerated from the syntax tree |

**All three non-`ok` statuses, per decision 4**, and `possible_duplicate` is driven the hard way: two
arrivals of the same purchase as different bytes, because the same bytes twice never reaches the
semantic check at all.

**One line per receipt, per decision 5.** A receipt with two things wrong produces one line holding
both notes.

**Nothing was added to the run summary, per decision 3.**

---

## 3. What the line looks like

Rendered through `worker\logging_setup.py`'s `LOG_FORMAT` with the real message template and real
note strings. **This is a rendering of the format, not a live run**, produced by a scratch script
that imports only `logging`: an `import config` on Windows outside pytest reads `.env` and runs the
mkdir block against the live practice root, which is the fourth trap in `CLAUDE.md` as narrowed on
2026-09-09.

```
2026-09-09 12:03:50,475 WARNING worker.extraction_pipeline — receipt a96ab8f7-3af1-42e7-bd98-dee8be2529b8 for client Client_004 is failed: missing gross_amount
2026-09-09 12:03:50,475 WARNING worker.extraction_pipeline — receipt a96ab8f7-3af1-42e7-bd98-dee8be2529b8 for client Client_004 is needs_review: missing supplier_name, gross mismatch: 10.0 + 2.0 = 12.0, got 99.0
2026-09-09 12:03:50,475 WARNING worker.extraction_pipeline — receipt b1c2d3e4-0000-0000-0000-000000000001 for client Client_004 is possible_duplicate: matches a96ab8f7... (supplier, date, amount)
2026-09-09 12:03:50,475 WARNING worker.extraction_pipeline — receipt c9d8e7f6-0000-0000-0000-000000000002 for client CLIENT002 is needs_review: client CLIENT002 has no client_folder_name in the registry
```

The first of those is the receipt from Paul's sitting, amendment 291, which failed with the reason in
the database and nowhere else.

**One caveat about my own output, disclosed rather than smoothed over.** The em dash in
`LOG_FORMAT` printed as `?` in my console, because the console code page is not UTF-8. The file
handler is opened `encoding="utf-8"`, so `run.log` holds the em dash. I have retyped it above.
I have not read a live `run.log` line, so what I am asserting there is the encoding of the handler
as `worker\logging_setup.py` sets it.

---

## 4. The suite, before and after

| When | Result |
|---|---|
| Before, on `40a6adb`'s tree with no change | **830 passed, 613 subtests passed in 45.08s** |
| After | **848 passed, 626 subtests passed in 43.07s** |

**18 tests and 4 subtests are mine. The other 9 subtests are explained and were checked rather than
assumed.** `tests\test_logs_isolation.py::ProcessOnceRedirectionTest` subtests every test module that
drives `process_once()` against the 9 names in `PROCESS_ONCE_WRITES`, and my new module joins its
glob because it drives `Routes`. 9 names times 1 module is 9. Measured by running the suite with my
own file excluded, which gave **830 passed, 626 minus 4 equals 622 subtests**, so the 9 arrive
without any of my tests being collected.

**That guard's own comment is why I checked rather than shrugged.** It records a leak found in 2026
only because "the suite's subtest count dropped by nine", the same arithmetic in the other direction.
A moved total on this project is worth a question.

**The pipeline is not running and I did not start it.** `CLAUDE.md` says that is Paul's to run.

---

## 5. Every mutation, and its result

Run through `tests\mutation_harness.py`, so each is applied to a pristine copy, each anchor is
asserted to match exactly once before anything is written, each prints its own unified diff, each
runs the whole suite, and each restores the file byte for byte. Definitions in the scratchpad, not in
the repository.

| Mutation | Change | Expected | Result |
|---|---|---|---|
| `no-warning-at-all` | Drop the `logger.warning()` call, keep the return | caught | **caught, 13 failures**, 1 hunk |
| `warn-on-ok-as-well` | Remove the `if status == "ok": return None` guard | caught | **caught, 4 failures**, 1 hunk |
| `error-not-warning` | `logger.warning` to `logger.error` | caught | **caught, 8 failures**, 1 hunk |
| `drop-the-reason-from-the-event-log` | Remove `review_reason=review_reason,` from the `_log_receipt` call | caught | **caught, 3 failures**, 1 hunk |
| `reword-the-join` | `", "` to `" and also "` | caught | **caught, 2 failures**, 1 hunk. **Caught by 1 before I strengthened the tests, see below** |
| `report-before-the-status-is-final` | Move the call to just after `validate()` returns | caught | **caught, 2 failures**, 2 hunks by design |
| `prose-only-reword-the-docstring` | Replace Paul's quoted instruction in the new docstring with waffle | **survives** | **survived, 0 failures**, 1 hunk |

Three of those deserve a note rather than a tick.

**`reword-the-join` was caught by one test on its first run, and that was a real weakness.** Every
outcome the test module drove produced a **single** note, so the join was invisible to all of them
and only the test calling the function directly with three notes noticed. A join that no
pipeline-driven test can see is a join that could drift from `save_extraction()`'s without anything
going red, which is precisely the condition decision 1 exists to prevent. **So I added a two-note
outcome, `supplier_name=None` with `gross_amount=99.0`, driven end to end**, and the mutation is now
caught by two, one of them through `app.process_once()`. **The mutation found a gap in my tests, which
is what a mutation is for, and I have said so rather than reporting the first number.**

**`report-before-the-status-is-final` changed two hunks, and that is declared rather than excused.**
It is a move, so it is two co-ordinated anchors, each passed through `replace_once()` and each
asserted unique. The harness's one-hunk property is about a mutation that claims to change one place;
this one claims to change two.

**And it exposed a structural guard of mine as weaker than it reads.**
`test_the_line_is_written_after_the_status_is_final` asserts the call is inside no `if` statement.
After the mutation the call sits at the top of the function body, still inside no `if`, **so that
guard passed and the two behavioural tests are what caught it.** The guard is worth keeping, because
what it forbids is a line written inside a filing branch, but it does not prove the call is after the
overrides and I should not have named it as though it did. The name is accurate about the intent and
optimistic about the mechanism. **Flagged as my own, not repaired, because renaming it is a decision
about what the guard is for.**

**`error-not-warning` was not caught by `test_a_possible_duplicate_says_why`**, which asserts the
message and not the level. The level is asserted on five other paths and in the subtest that drives
every status, so the set is covered; the one test is not.

---

## 6. Decisions the brief left to me

| Decision | What I chose | Why |
|---|---|---|
| Where the line is written | One new function in `worker\extraction_pipeline.py`, called once at the end of `process_extraction_result()` | The brief's own reading: this is where both the status and the notes are held. It is also the one function all four callers and all three arrival routes pass through, so one line serves every route |
| Whether to change any function's return shape | **No.** Nothing else was touched | The brief warned against it without enumerating callers first. Nothing needed it: `validation` is already in scope at the point the line is written |
| How the notes become one string | `", ".join(notes)`, the same join `save_extraction()` uses | Decision 1 says verbatim and says the strings are the ones the database holds. Using the same join makes that literally true, so one search finds the log and the row. Asserted directly: the test compares the log message against the string read back out of `extractions.validation_notes` |
| The message wording | `receipt {id} for client {client} is {status}: {reason}` | Carries the brief's four required items in one line, with the status as a bare word so `grep needs_review run.log` works |
| Whether the function returns the reason or the caller rebuilds it | Returns it | One builder. Held by a source guard so a second cannot appear quietly |
| Empty notes | Log `no reason recorded` rather than an empty tail | Nothing reaches it today and I have said so in the docstring and in the test. A line reading `failed:` with nothing after the colon would be read as the reason, which is worse than no line |
| Test file name | `tests\test_validation_reason_logged.py` | New file rather than an addition to an existing one: nothing existing covers process-log content, and this one file holds all four deliverables |

---

## 7. Flags. Nothing here was repaired

**1. The unresolved-client gate's reason is in no database row, and now the log is the only
machine-readable record of it.** `save_extraction()` runs **before** the gate of 10d.16 and 10d.18, so
for a receipt whose client has no `client_folder_name` the extraction row reads
`validation_status: ok` with `validation_notes: NULL`, while the receipt row reads `needs_review`.
The reason reached the Review folder note and nothing else. **This is pre-existing and it is not
small: it is a receipt whose two tables disagree about its outcome.** Pinned by two assertions in
`test_the_reason_the_client_gate_added_reaches_the_log`, with a message saying that if they go red
because the gate's reason now reaches the row, that is the flag being fixed and the test should be
updated. **Found by my own test failing on an assumption I had not checked, see section 8.**

**2. `validation_notes` cannot be split back into notes, because a note can contain the separator.**
The gross-mismatch note is `gross mismatch: 10.0 + 2.0 = 12.0, got 99.0`, which holds `", "` itself,
so a two-note string holds it twice. Pre-existing in `save_extraction()`. It costs nothing today,
because nothing splits the string, and my change carries the same string rather than a second
convention. **Worth knowing before anyone writes a reader that splits on the comma.**

**3. The two copies of `_log_receipt()`, as the brief asked.** They differ in the way the docstring in
`worker\extraction_pipeline.py` already records, and I read both to check that record rather than
quoting it: **`app.py`'s copy writes `client_id` only when the action is `"created"`**, the shared
pipeline's writes it whenever it has one, and **`app.py`'s has no `chart_outcome` parameter at all**.
Two further things about that copy, neither of them repaired:

- **`app.py`'s three `extraction_failed` call sites pass no `client_id`**, and would gain nothing if
  they did, because that copy drops it for any action but `"created"`. So an ndjson entry for a
  raised extraction names no client, while the `"extracted"` entry the shared pipeline writes now
  does.
- Those three sites already carry the reason into both logs, by `logger.error()` and by
  `review_reason=str(exc)`. **They use `ERROR` where this change uses `WARNING`, and I read that as
  correct rather than inconsistent**: a raised extraction is the API or the reader failing, which is
  decision 2's `ERROR` case, while a receipt that validated as `failed` is an outcome the pipeline is
  designed to produce. **It does mean `run.log` now carries two levels for two kinds of unexplained
  receipt, and that is deliberate.**

**4. A dead branch in the semantic duplicate override, which would drop the notes if it ever ran.**
The override reads
`validation._replace(status="possible_duplicate") if hasattr(validation, '_replace') else type(validation)(status=..., notes=[...])`.
`ValidationResult` is a `@dataclass`, so `hasattr(validation, '_replace')` is `False` and the second
branch is the live one. **If the class ever became a `NamedTuple` the first branch would run, and it
carries no notes**: a `possible_duplicate` reaching that path would have `notes == []`, because
`validate()` returned `ok` with an empty list. The log line would then read
`possible_duplicate: no reason recorded`, which is my fallback doing its job on a receipt whose
reason had been silently dropped upstream. Pre-existing, out of scope, not repaired.

**5. The brief's premise about the freeze has been overtaken by the repository.** Section 4 says
"18.2b's freeze still holds" and "Stage 3's acceptance test has not been run". `HEAD` is now
`40a6adb`, whose message is "amendment 291, stage 3 run and all five checks passed, freeze released
for stage 4", and amendment 291 records the sitting and Paul's instruction that produced this brief.
**Nothing about my change depends on which is current: I touched no file in `worker\filing.py` and
nothing in `worker\publish.py`.** Reported because the brief and the design document disagree about a
fact, and that is Paul's to note rather than mine to choose.

---

## 8. My own mistakes

**1. I assumed the extraction row carried the client gate's reason, and it does not.** My first
version of `test_the_reason_the_client_gate_added_reaches_the_log` asserted the log message contained
the string read out of `extractions.validation_notes`, and the test failed with
`TypeError: 'in <string>' requires string as left operand, not NoneType`. **The assumption was that
one row records the outcome, and `save_extraction()` runs before the gate.** The test was corrected
to assert the gate's own reason and to pin what the row actually holds; the finding is flag 1 above.
**It is the most useful thing this task turned up and I found it by being wrong, not by reading
carefully.**

**2. I counted separators to prove a join, and a note contains the separator.** The two-note test
first asserted `notes.count(", ") == 1` and got 2, because the gross-mismatch note holds `", "`
inside itself. Replaced with an assertion on the whole string, which is stronger anyway. That is
flag 2, and I would not have found it if I had written the stronger assertion first.

**3. I reported a mutation result before strengthening the tests it exposed.** `reword-the-join` was
caught by one test, I noticed that every driven outcome had a single note, and only then added the
two-note case. **The first number was true and the finish would have been an overstatement**, because
"the join is pinned" would have rested on a test that never touches the pipeline. Both numbers are in
section 5.

**4. I named a source guard as though it proved something it does not.**
`test_the_line_is_written_after_the_status_is_final` proves the call is inside no branch, not that it
is after the overrides. Disclosed in section 5 and left as it is.

**5. My first attempt to write the test file used a shell heredoc and bash rejected it**, so I used
the file-writing tool instead. No file was created by the failed attempt, and I did not diagnose why
bash broke, so **if a later session sees the same thing, this report offers no cause.**

---

## 9. Out of scope, and confirmed untouched

- **`worker\filing.py`**: not opened for edit. `git diff --stat` is one file.
- **`worker\publish.py` and `publish_events`**: not touched.
- **`validate()`'s own rules**: not touched. Whether a missing gross should go to review rather than
  fail is Paul's, and this change reports whatever `validate()` decides.
- **The run summary**: nothing added, per decision 3.
- **No database write.** Everything ran under pytest against temp databases.
- **Nothing written outside `C:\LastingImpact\receipt_capture`**, except scratch files in the session
  scratchpad, which are mine and are not in the repository.

---

## 10. Commits

Both on `feat/console-phase0`, the current branch. **Nothing was pushed.**

| Commit | What |
|---|---|
| `9c424e9` | `worker\extraction_pipeline.py` and `tests\test_validation_reason_logged.py` |
| `b090ed9` | This report. **Amended after the first write, to carry these two hashes rather than a pointer to the section below.** Unpushed at the time, so nothing published was rewritten |

The code and its test are one commit deliberately: a commit holding only the test would leave the
tree red, and a commit holding only the code would leave 18 tests unwritten in a repository whose
rule is red before green.

### 10.1

```
feat(logging): the reason a receipt did not reach ok goes into run.log

report_validation_outcome() writes one WARNING per non-ok receipt carrying the
receipt id, the client, the status and the validation notes verbatim, and
returns that same string for the ndjson event log's review_reason, which
_log_receipt() has always had and this call site never passed. ok logs nothing.

Files: worker/extraction_pipeline.py, tests/test_validation_reason_logged.py
```

### 10.2

```
docs: the report for the validation-reason logging change

Files: 2026-09-09_REPORT_claude_code_validation_reason_logging.md
```

---

## 11. What Paul will see change

**On the next pipeline run, a receipt that does not reach `ok` writes one extra `WARNING` line into
`C:\Intellibills\logs\run.log`, immediately before the `Moved email uid=... to INBOX....` line, and
that line says why.** A receipt that reaches `ok` writes nothing new.

**And `C:\Intellibills\logs\receipt_events_FIRM001.ndjson` gains a `review_reason` key** on the
`"extracted"` entry for the same receipts. An `ok` receipt's entry is unchanged.

**Nothing else changes.** No receipt changes status, nothing files or publishes differently, and no
database column moves.

**Per `CLAUDE.md`, commit before a run whose `pipeline_version` matters**: the tree is clean after the
two commits above, so a run started now records a version that describes the code that ran.
