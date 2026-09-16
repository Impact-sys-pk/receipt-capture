# Report: a client folder copy that failed after a successful publish is retried

**Claude Code, 2026-09-09. Executed from `PROMPT_claude_code_2026-09-09_client_copy_retry.md`, which
is my own flag 6 of `2026-09-09_REPORT_claude_code_stage4_pipeline.md`.**

**Confidence that the clause works and is correctly gated: high, and what it rests on is 17 tests
driving a real failure through a real `app.process_once()` and then a real second poll, the whole
suite at 914 passed and 667 subtests, and six mutations of which five had to be caught and were and
one had to survive and did.** What that confidence is **about** is the behaviour of the clause under
pytest, on all three trigger values, with and without the cutover.

**One thing needs Paul before the next pipeline start, and it is in section 3.** The first poll after
this lands will copy **exactly one** document into a live client folder, and it is not a failed copy:
it is check 1 clause A's receipt, published while the trigger was `never`. Named there so he can
decide before starting.

---

## 1. What was built

**One deliverable, one clause, one new repository query, one new function.**

| Where | What |
|---|---|
| `worker\database\repository.py` | `get_published_receipts_without_client_copy()`. Four conditions in SQL: `status = 'ok'`, `filed_path IS NULL`, the cutover, and a `published` row exists |
| `app.py` | `_copy_missing_client_copies(repo)`. Returns before the query unless the trigger is `publish`; otherwise reads the extraction for the filename and calls the one gated copy function |
| `app.py`, `process_once()` | One call, immediately after `_publish_unpublished_receipts()` |

**142 insertions, 1 deletion, across three files, plus one new test file.** No schema change. Nothing
new writes into `Clients\`: the clause reaches `copy_for_published_receipt()`, which every other
route reaches.

### Where the trigger condition sits, and it is above the query

**Above it, in `_copy_missing_client_copies()`, so the query is never executed on `never` or `post`.**
The brief asked which and this is the answer. Putting it in SQL would have meant binding a config
value into a `WHERE` clause; putting it after the query would have meant reading the whole table
every five minutes and discarding it.

**Held as behaviour, not as structure**: `TheTriggerGatesTheWholeSweepTest` patches the repository
method with a spy and asserts it was **not called** on `never` and on `post`, and called exactly once
on `publish`. The third is the control, without which the first two would pass against a clause that
never ran on any trigger.

### The retry publishes nothing and categorises nothing

Both already happened for every receipt it can see. **Republishing would overwrite an item Desktop may
already have drained**, and a second `categorisations` row for one receipt would be a duplicate nobody
asked for. Held two ways: the row counts before and after a retry, and a syntax-tree guard that the
function calls none of `publish_receipt`, `categorise`, `save_categorisation`, `make_enriched_sidecar`
or `write_client_copy`.

### Nothing in the run summary, held structurally

`stats` is what `_log_run()` spreads into `runs.ndjson`, which is the run summary per rule 1 of
`CLAUDE.md`. **`_copy_missing_client_copies()` takes no `stats` parameter at all**, so it cannot add a
key, and `test_the_sweep_takes_no_stats_and_so_writes_nothing_to_the_run_summary` asserts that on the
signature. What a reader sees instead is one INFO line naming the count and
`copy_for_published_receipt()`'s own INFO line per receipt.

---

## 2. The suite, before and after

| When | Result |
|---|---|
| Before, on `1fcc7a0` | **897 passed, 667 subtests passed in 83.60s** |
| After | **914 passed, 667 subtests passed in 77.50s** |

**17 tests added, all mine, and the subtest count did not move.** That is expected rather than
suspicious: the 667 already included the ten `ProcessOnceRedirectionTest` subtests for the new module,
because that guard globs `tests\test_*.py` on disk rather than collecting them, so the file counted
towards it from the moment it existed. **Checked rather than assumed**, by taking the baseline with
`--ignore=tests/test_client_copy_retry.py` while the file was on disk.

**One existing test changed.** `tests\test_stage4_client_copy.py`'s caller-set guard asserted
`copy_for_published_receipt()` has exactly three call sites. **It has four now**, and the fourth is
this clause. The set is enumerated rather than counted, so it named itself.

### The red run, before the implementation

```
FAILED tests/test_client_copy_retry.py::ACopyThatFailedIsRetriedOnTheNextPollTest::test_a_retry_that_fails_again_leaves_the_receipt_alone
FAILED tests/test_client_copy_retry.py::ACopyThatFailedIsRetriedOnTheNextPollTest::test_the_document_reaches_the_client_folder_on_the_next_poll
FAILED tests/test_client_copy_retry.py::TheTriggerGatesTheWholeSweepTest::test_never_never_runs_the_query_and_writes_nothing
FAILED tests/test_client_copy_retry.py::TheTriggerGatesTheWholeSweepTest::test_post_never_runs_the_query_and_writes_nothing
FAILED tests/test_client_copy_retry.py::TheTriggerGatesTheWholeSweepTest::test_publish_does_run_the_query
FAILED tests/test_client_copy_retry.py::TheCutoverHoldsHereTooTest::test_a_receipt_created_after_the_cutover_is_offered
FAILED tests/test_client_copy_retry.py::TheCutoverHoldsHereTooTest::test_a_receipt_created_before_the_cutover_is_left_alone
FAILED tests/test_client_copy_retry.py::TheCutoverHoldsHereTooTest::test_an_empty_publish_log_offers_nothing
FAILED tests/test_client_copy_retry.py::StillOneWriterTest::test_the_gated_entry_point_has_four_callers_and_this_is_the_fourth
FAILED tests/test_client_copy_retry.py::StillOneWriterTest::test_the_retry_sweep_publishes_nothing_and_categorises_nothing
FAILED tests/test_client_copy_retry.py::StillOneWriterTest::test_the_sweep_is_called_once_from_process_once
11 failed, 4 passed in 1.45s
```

The four that passed were the two source guards about what does **not** call the writer, plus two the
cutover answered. **Three of those four were passing for the wrong reason**, which is section 5.

---

## 3. WHAT THE FIRST POLL WILL DO ON PAUL'S MACHINE, and it needs a decision

**I read `C:\Intellibills\db\receipts.db` directly, read-only, with sqlite3 in `mode=ro` on Windows.
Not through any bridge, and `config` was not imported to do it.** Caveat stated: the database is in
write-ahead mode and the pipeline may have been running, so a row written in the seconds around the
read might be missing. Nothing below depends on that.

**Exactly one receipt satisfies the new clause today:**

```
ok + published + filed_path NULL, before the cutover is applied: 1
   e10419a8-574b-4d23-8521-47630ee7bd79  created 2026-09-09T13:58:39
the same WITH the cutover: 1
```

**It is check 1 clause A's receipt, and it is not a failed copy.** The four receipts of today, read
from the two tables:

| Created | Receipt | Status | Published at | Copied? |
|---|---|---|---|---|
| 10:33:28 | `a96ab8f7` | ok | 11:22:50 | yes, 11:22:50 |
| 10:43:34 | `aff2d279` | ok | 10:43:37 | yes, 10:43:37 |
| **13:58:39** | **`e10419a8`** | **ok** | **13:58:45** | **NO** |
| 14:15:40 | `daddc1c6` | ok | 14:15:48 | yes, 14:15:48 |

**Amendment 292's clause A is run with the trigger set to `never`**, and clause B with it set to
`publish`. `e10419a8` published at 13:58 and was never copied; `daddc1c6` published at 14:15 and was.
**So `e10419a8` is clause A's receipt, deliberately uncopied because the trigger said `never` at the
time**, and `daddc1c6` is clause B's.

**On the next pipeline start with the trigger back on `publish`, this clause will copy
`rcpt_mtu5x5ik_cexz1v.jpg` into `Client_004`'s client folder, and 18.2b says a copy is never
withdrawn.**

**Whether that is wrong is Paul's call and I have not pre-empted it.** The case for letting it happen:
it is a real `ok` receipt for a real client, the trigger now says `ok` receipts get copied, and 18.2b's
purpose is that the client sees the result of the work. The case against: it was excluded on purpose,
and a feature sold as "retry failed copies" copying something that never failed is not what it says.

**If he does not want it, it needs no code change**: setting that one receipt's `filed_path` to any
value stops the clause offering it. **That is an `UPDATE` against the live database, which I must not
run**, so it is his or it is a briefed change.

---

## 4. Every mutation and its result

Through `tests\mutation_harness.py`: pristine copy, anchor asserted to match exactly once before
anything is written, unified diff printed beside the result, whole suite run, restore asserted byte
for byte.

| Mutation | Change | Expected | Result |
|---|---|---|---|
| `drop-the-cutover` | Remove the `created_at >=` clause | caught | **caught, 1 failure**, and by exactly the test the brief named |
| `drop-the-filed-path-condition` | Remove `filed_path IS NULL` | caught | **caught, 1 failure** |
| `drop-the-published-condition` | Remove the `EXISTS ... published` block | caught | **NOTHING CAUGHT IT on the first run.** See below. **Caught, 1 failure**, after a test was added |
| `drop-the-trigger-gate` | Remove the trigger check above the query | caught | **caught, 2 failures** |
| `never-call-the-sweep` | Remove the call from `process_once()` | caught | **caught, 5 failures** |
| `prose-only-reword-the-sweep-docstring` | Replace the docstring's trigger paragraph with waffle | **survives** | **survived, 0 failures** |

**`drop-the-cutover` is caught by exactly one test and that is the point.** The brief asked for a
mutation dropping the cutover caught by exactly the cutover test, and
`test_a_receipt_created_before_the_cutover_is_left_alone` is the only thing that fails. Its pair,
`test_a_receipt_created_after_the_cutover_is_offered`, still passes, which is what shows the two
receipts differ in one value and nothing else can decide between them.

### The third is the one worth reading

**`drop-the-published-condition` was caught by nothing, because no test drove the state it protects.**
That state is a receipt that is `ok`, has no client copy, and whose **publish failed**. Without the
condition, this clause would copy a document into a client folder for a receipt IntelliBooks never
received. **F16's trigger is "on a successful publish"**, so that is the condition's whole meaning and
I had not tested it.

Fixed by adding `OnlyASUCCESSFULPublishIsCopiedTest`, which patches `publish.write_item` to raise,
drives a real arrival, and asserts that the receipt is **not** offered for copying and **is** offered
by `get_unpublished_ok_receipts()`, because it is the publish sweep's to recover. The mutation is now
caught by exactly that test.

**Second time in two briefs that a mutation has found a missing test rather than confirmed a present
one.** In both cases the query had two conditions that could exclude a row and my test named one.

### One unexplained collateral failure, disclosed rather than smoothed over

`never-call-the-sweep` was caught by five tests, and the fifth is
`tests\test_logging_setup.py::SuiteWritesNoLogsTest::test_running_a_cli_writes_to_the_redirected_logs_dir_not_the_real_one`,
which has nothing to do with this clause. **I have not explained it.** It passes on the clean tree
every run, including five full-suite runs today, so it is not a defect I introduced; the likely cause
is order or state dependence surfacing under a changed run. **Recorded because a reader of the
mutation output would otherwise wonder, and because I did not chase it.**

---

## 5. Decisions the brief did not settle

| # | Decision | What I chose | Why |
|---|---|---|---|
| 1 | **Where the trigger condition sits** | **Above the query**, in the sweep function | The brief asked which. A config value has no business in a `WHERE` clause, and after the query means reading the whole table to discard it. Asserted as "the query was never called", not as "its answer was ignored" |
| 2 | **A separate function, or a second query feeding the existing sweep loop** | **A separate function** | The publish sweep's loop categorises and publishes, and this must do neither. Sharing the loop would have meant two flags through eighty lines |
| 3 | **Whether it takes `stats`** | **No parameter at all** | The brief says nothing in the run summary, and `stats` is the run summary. A function that cannot add a key is better than one that remembers not to |
| 4 | **Where it sits in `process_once()`** | **Immediately after the publish sweep** | So the two recovery clauses read together in the code and in `run.log`. A receipt this poll publishes gets its copy in the clause above; this one is for copies that failed on an earlier poll |
| 5 | **Whether to pass `filed_path` as `None` or from the row** | **From the row** | The query guarantees NULL, so both work today. Passing the row means the one-copy gate in `copy_for_published_receipt()` still holds if the query ever changes |
| 6 | **What happens when the extraction row is missing, or the source document has gone** | **A WARNING and skip, per receipt**, matching the publish sweep's two guards word for word | An `ok` receipt with no extraction row should not exist, and a document missing from the store is a bigger problem than a missing copy. Neither should take a poll down |

---

## 6. Flags. Nothing here was repaired

### Flag 1. The clause cannot tell a failed copy from a deliberate one, and nothing can

**Nothing in the database records WHY a receipt was not copied.** The four reasons are: the copy
raised, the trigger was `never`, the trigger was `post`, or the client had no `client_folder_name`.
Only the first is what this clause is for, and all four leave the same row.

**The consequence is general, not a one-off.** A firm moving `client_copy_trigger` from `never` to
`publish` offers its entire backlog of published-but-uncopied receipts on the next poll, and 18.2b
says a copy is never withdrawn. Section 3 is that consequence with today's numbers.

**The fix would be a record of the attempt**, which is a schema change and is forbidden here, or a
marker on the receipt, which is a design decision. **Flagged and left.**

### Flag 2. The cutover is not load-bearing on this clause, and it costs one receipt

**The brief says the cutover is "the one that can do real damage" and that without it the first poll
would copy every historical `ok` receipt. I checked, and on this database that is not so.** Every one
of the 17 historical `ok` receipts has a `filed_path`, because they were filed on arrival under the
old route, so `filed_path IS NULL` already excludes all of them. Without the cutover the clause
selects **1** receipt; with it, **1**.

**What the cutover does exclude here is the earliest-published receipt**, whose own publish row is the
`MIN`, written moments after the receipt row, so `created_at >= MIN` is false for it and only for it.
**So on a fresh installation, a copy that fails on the very first receipt ever published is never
retried.** On this installation the hole is empty: `aff2d279` is the earliest-published receipt and it
was copied.

**I built it with the cutover anyway, and that is deliberate.** The brief is emphatic, the cost of
being wrong is a file in a live client folder that the product cannot withdraw, and one line of
defence in depth against a case I have not thought of is worth one receipt on a fresh install.
**Reported rather than quietly dropped**, because the reasoning in the brief rests on a premise the
data does not support, and Paul should know that the protection he was told about is not the one doing
the work here. **What does the work is `filed_path IS NULL` combined with the `published` row.**

### Flag 3. My own breach of stage 4's brief, found while reading this one

**Stage 4's brief also said "Nothing in the run summary", and I added a key to it.** Before stage 4,
`app.py` had `stats["recovery_filed"]` and no `recovery_failed`; confirmed by
`git show 250b36b:app.py`. Stage 4 renamed the first to `recovery_published` and **added
`recovery_failed`**, which lands in `runs.ndjson`. **That is a new key in the run summary under a brief
that forbade one, and I did not notice or disclose it at the time.**

**Not repaired, because removing it now is a behaviour change this brief did not ask for either.** The
fix is one line and one word if he wants it: delete the `stats["recovery_failed"]` increment in
`_publish_unpublished_receipts()`, and the `publish_events` row already records the same failure.
**Offered, not done.**

### Flag 4. An unpublishable receipt is still retried on every poll, for ever

Unchanged from flag 7 of the stage 4 report, and this clause adds a second instance of the same shape:
a receipt whose copy can never succeed, for example a client folder that will never exist, is offered
every poll and writes one ERROR each time. **Today's publish sweep has the same unbounded shape**, so
it is inherited rather than introduced. A cap is a behaviour decision and I did not invent one.

---

## 7. My own mistakes

**1. The one that mattered: three of my tests failed and three passed for the same wrong reason.**
The cutover excludes a fresh database's only receipt, because a receipt's `created_at` precedes its own
publish row's. So the end-to-end tests failed, and
`test_the_retry_neither_republishes_nor_recategorises` and
`test_an_already_copied_receipt_is_not_copied_a_second_time` **passed because nothing happened at
all.** The brief warned about exactly this, in terms, and I still wrote it.

**Fixed properly rather than patched.** `seed_the_cutover()` puts an earlier `published` row in place,
and `arrive_with_a_broken_copy()` now **asserts that the query actually offers the receipt** before any
test relies on it. That precondition assertion is the part worth keeping: it makes it impossible for a
future test built on the helper to be answered by the cutover.

**2. I had no test for the condition that gives the clause its meaning.** Section 4's third mutation.
"On a successful publish" is F16's wording and I tested the copy, the trigger and the cutover without
testing the publish.

**3. I wrote a helper I never used.** `_poll_and_count_query_calls()` was written, then bypassed by
three tests that each did the same thing inline, and it sat there dead until I removed it while fixing
mistake 1.

**4. I nearly reported the cutover as protective without checking.** The brief asserts it prevents a
historical backfill; I ran the query against the live database both ways and it makes no difference to
the answer. **The habit that caught it was reading the database rather than the brief**, and I only did
that because the brief said the damage would be real, which made it worth measuring.

**5. Both mutation anchors touching the cutover line matched twice on my first attempt**, because that
line is now byte-identical at the same indentation in two queries. `replace_once()` refused before
writing anything, which is the third time that refusal has earned its place. Each anchor now carries a
neighbouring line unique to the new query.

---

## 8. Out of scope, and confirmed untouched

- **`copy_for_published_receipt()` still swallows.** Not touched at all. The guarantee that a failed
  copy cannot fail a receipt is the reason this clause exists.
- **One writer into `Clients\` still.** `write_client_copy()` has no callers outside
  `worker\client_copy.py`, asserted on the tree. The gated entry point gained a fourth caller.
- **The publish half of the sweep is untouched**, including its own cutover clause.
- **No schema change.** One query and one function added.
- **Nothing in the run summary**, held on the signature.
- **No write to the live database.** The only live access was one read-only sqlite connection, and
  section 3 names what it read.
- **Nothing written outside `C:\LastingImpact\receipt_capture`** except scratch files in the session
  scratchpad.

---

## 9. The commit

On `feat/console-phase0`, as `0a4946c`. **Nothing was pushed.** One commit: the clause and its
tests land together,
because a commit with the tests alone is red and a commit with the clause alone is untested.

```
feat(publish): retry the client folder copy for anything that published without one

_copy_missing_client_copies() offers any ok receipt that has a published row and
no filed_path, gated above the query on the firm's client_copy_trigger being
publish, and carrying the same cutover the publish sweep has. It reaches the one
gated copy function, publishes nothing, categorises nothing, and takes no stats.

Claude Code's flag 6 of 2026-09-09_REPORT_claude_code_stage4_pipeline.md.
```

---

## 10. What Paul will see change

- **A copy that fails because OneDrive had the folder locked now appears on the next poll**, with
  `retrying the client folder copy for N published receipt(s) that have none` in `run.log` followed by
  `receipt X copied into the client folder at ...`.
- **On `never` and on `post`, nothing at all**: no line, no query, no file.
- **On the very first poll after this lands, one document he did not ask for.** Section 3 names it.
  That is the one thing to decide before starting the pipeline.
