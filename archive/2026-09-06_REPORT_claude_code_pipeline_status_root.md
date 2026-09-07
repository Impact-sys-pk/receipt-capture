# Report: `pipeline-status.json` states the practice root

**Sub-step 10e.10.** Written 2026-09-06 by the Claude Code implementation
session, from `PROMPT_claude_code_2026-09-06_pipeline_status_root.md`. Times are
BST, which is what the Windows clock reports; the consultant session's shell
reports UTC and will read them an hour earlier.

**Done in full.** One field added, the contract test updated rather than
loosened, two tests added, three mutations run. Nothing outside the repository
was written, and section 6 says why and what that costs.

---

## 1. The suite, before and after

The brief gave no baseline to match and named the last figure on record as 524
passed, 330 subtests, with three commits landed since. **It is still that.**

**Before:**

```
524 passed, 330 subtests passed in 15.92s
```

**After:**

```
526 passed, 330 subtests passed in 13.24s
```

**Zero skips both times, and zero warnings both times.** The two new tests are
`test_the_practice_root_is_written_when_the_run_fails` and
`test_the_value_is_the_configured_string_and_is_not_resolved`, both in
`tests\test_status_counts_from_db.py`.

---

## 2. Task 1. The field

`_write_pipeline_status()` at `app.py:132` now writes five keys. The added line
is one:

```python
"practice_root": str(config.PRACTICE_ROOT),
```

**Not resolved, not normalised, not case-folded.** No `config.py` constant was
added; `PRACTICE_ROOT` at `config.py:33` already exists and is what is read. No
other field was added.

**The call site is unchanged.** `app.py:1345`, inside `process_once()`'s
`finally:` block, and it is the only caller. Enumerated by searching every
tracked `.py` in the repository for `_write_pipeline_status`, which returns two
lines, the definition and that call. **The field is not conditional**, so a
failed cycle carries it too.

A docstring was added to the function recording why the value is not resolved and
why the field is unconditional, so the next reader does not have to find
amendment 241 to know.

---

## 3. Task 2. The test that caught it

**It fired exactly as the brief said it would.** Adding the field before touching
any test produced this, which is the red:

```
AssertionError: Lists differ:
  ['last_error', 'last_run', 'practice_root', 'processed_today', 'review_count']
  != ['last_error', 'last_run', 'processed_today', 'review_count']
First differing element 2:
  'practice_root'
  'processed_today'
```

**Updated to the five-key shape, not deleted and not loosened.** It is still an
exact `assertEqual` on `sorted(payload.keys())`, so the next unannounced field
fails it the same way. The comment now records that it was four keys until
2026-09-06 and that it caught the change.

**The value assertion, and what it actually asserted.**

```python
self.assertEqual(payload["practice_root"], str(config.PRACTICE_ROOT))
```

**Under pytest that value is the session temp root, never Paul's real one.**
`tests\live_paths.py`, imported from `tests\conftest.py`, sets the `PRACTICE_ROOT`
environment variable to `<system temp>\intellibills-tests-<random>\practice`
**before `config` is imported**, so every path constant is computed from it. The
`TempEnvironment` fixture in `test_status_counts_from_db.py` pins thirteen
constants and **does not pin `PRACTICE_ROOT`**, checked by reading its `__enter__`
rather than assumed, so the redirected session root is what the assertion
compares against. A concrete example of the string under test:

```
C:\Users\PDK7\AppData\Local\Temp\intellibills-tests-8f3a1c\practice
```

**The failed-run test, and which file it went in.**
`tests\test_status_counts_from_db.py`, not `tests\test_failure_path_engine.py`
which the brief offered. **The reason is that the two failures are not the same
failure.** `test_failure_path_engine.py` drives an extraction that raises, which
`process_once()` catches per receipt; the run itself still succeeds and
`last_error` is `None`. What this test needs is a **run-level** exception, so
`errors` is set and the `finally:` block writes the status of a failed cycle. It
forces that by patching `fetch_new_messages` to raise, asserts `process_once()`
re-raises, then reads the payload and checks `last_error`, `practice_root` and
the full five-key shape. **And the status payload's other assertions all live in
this file**, so the shape stays in one place.

**A third test was added that the brief did not ask for**, and section 5 says why
it had to be.

---

## 4. Task 3. What must not break

**`IntelliBooks-Desktop-v3.html:1094`, read rather than assumed.**

```javascript
try{pd=await rootHandle.getDirectoryHandle(PIPE_DIR);r=await readJSON(pd,"pipeline-status.json");}catch(e){}
```

Two lines below it, `const d=r.data||{};`, and the fields taken off `d` are
**`d.last_run` and `d.last_error`**, by name. **So a new key is additive and
invisible to it.** Confirmed.

**Two things found by enumerating rather than by checking the one line named.**

- **`pipeline-status.json` appears twice in the whole Desktop file**, at `:1094`
  and in a comment at `:820`. One reader, and this is now a counted claim rather
  than a stated one.
- **Desktop reads only two of the five keys.** It never reads `processed_today`
  or `review_count`. Not a fault and not this brief's business, but it means the
  contract test guards more than the consumer currently uses, which is the right
  way round.

**The five test files that redirect `config.PIPELINE_STATUS_PATH`, and whether
there is a sixth.** Enumerated with `git grep` across every tracked `.py` for
`PIPELINE_STATUS_PATH`, `pipeline_status` and `pipeline-status`, printed whole
rather than sampled. **Eight files match: `app.py`, `config.py`, and the six test
files.** The five the brief named are all there. **The sixth is
`test_status_counts_from_db.py` itself**, which the brief already identifies as
the one that asserts the payload. **So there is no unnamed sixth**, and only one
line in the whole suite reads the payload back:
`test_status_counts_from_db.py:202`.

---

## 5. The mutations

**Three, each applied alone to a clean tree and reverted afterwards.**

| | Mutation | Red |
|---|---|---|
| **A** | Remove the `practice_root` line from the payload, which is the one the brief asked for | **3 tests** |
| **B** | Resolve the value: `str(config.PRACTICE_ROOT.resolve())` | **1 test** |
| **C** | Make the field conditional on a healthy run | **1 test** |

**Mutation A, the removal:**

```
3 failed, 523 passed, 330 subtests passed
  ProcessedTodayTest::test_status_file_reports_receipts_created_today_not_this_run
  ProcessedTodayTest::test_the_practice_root_is_written_when_the_run_fails
  ProcessedTodayTest::test_the_value_is_the_configured_string_and_is_not_resolved
```

**Three, not one.** The brief asked to be told if only one guard existed on a
cross-product contract. Three do: the original shape test, plus both new ones.

**Mutation B is the one worth reading, and it is why a third test exists.**

```
1 failed, 525 passed, 330 subtests passed
  ProcessedTodayTest::test_the_value_is_the_configured_string_and_is_not_resolved
```

**Only the test written for it catches a `.resolve()`, and the other two cannot.**
Both compare the written value against `str(config.PRACTICE_ROOT)`, and the
session temp root that `live_paths.py` installs is already fully resolved, so
resolving it again changes nothing and both stay green. **"Do not resolve" is the
central instruction of this sub-step and it would have been untested.**

The third test makes it testable, and the mechanism was checked on Windows rather
than assumed:

```
Path(r'C:\Some\Folder\..\Other')            -> 'C:\Some\Folder\..\Other'
Path(r'C:\Some\Folder\..\Other').resolve()  -> 'C:\Some\Other'
Path(r'c:\USERS\pdk7').resolve()            -> 'C:\Users\PDK7'
```

**`Path` does not collapse `..` and `.resolve()` does**, and `.resolve()` also
case-folds an existing path. So the test sets `config.PRACTICE_ROOT` to a
configured root carrying a `..`, calls `_write_pipeline_status()` directly, and
asserts the `..` is still there in the written value. It needs no folder to
exist.

**Mutation C, the conditional field:**

```
1 failed, 525 passed, 330 subtests passed
  ProcessedTodayTest::test_the_practice_root_is_written_when_the_run_fails
```

**One, and it is the test written for it.**

---

## 6. The file itself

**What IntelliBooks reads today**, read from
`C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills\pipeline-status.json`,
last written 12:00 on 2026-09-06:

```json
{
  "last_run": "2026-09-06T12:00:45.838268+00:00",
  "processed_today": 4,
  "review_count": 0,
  "last_error": null
}
```

**What it will read after the next cycle.** Produced by calling
`_write_pipeline_status()` with the real `config.PRACTICE_ROOT`, quoted whole and
exactly as it sits on disk:

```json
{
  "last_run": "2026-09-06T12:00:45.838268+00:00",
  "processed_today": 4,
  "review_count": 0,
  "last_error": null,
  "practice_root": "C:\\Users\\PDK7\\OneDrive - Intellitax Accounting Limited"
}
```

**And the failed-cycle form, which is the case the field exists for:**

```json
{
  "last_run": "2026-09-06T12:05:00.000000+00:00",
  "processed_today": 4,
  "review_count": 0,
  "last_error": "simulated IMAP outage",
  "practice_root": "C:\\Users\\PDK7\\OneDrive - Intellitax Accounting Limited"
}
```

**The doubled backslashes are correct JSON and are not worked around.** What
IntelliBooks gets after `JSON.parse` is the single-backslash string, confirmed by
parsing the file back:

```
raw in the file : "practice_root": "C:\\Users\\PDK7\\OneDrive - Intellitax Accounting Limited"
after parsing   : 'C:\Users\PDK7\OneDrive - Intellitax Accounting Limited'
equals str(config.PRACTICE_ROOT) : True
is absolute                      : True
```

**Where this was written, and why not to the live file.** The temp path
`C:\Users\PDK7\AppData\Local\Temp\10e10-hka1gl50\pipeline-status.json`. Only the
**destination** was redirected; `PRACTICE_ROOT` is the real configured value, so
the bytes above are the bytes the next real cycle will write. **`CLAUDE.md`
forbids this session writing anything under
`C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\` without asking**, and
this brief does not authorise it.

**What that costs, stated rather than glossed: the live file still has four keys
until Paul next runs the pipeline.** Nothing else is needed. `_write_pipeline_status()`
overwrites it on every cycle including a failed one, so the fifth key appears at
the end of the next run with no migration and no manual step.

---

## 7. Flag, do not fix

- **`changeRoot()` at `IntelliBooks-Desktop-v3.html:1086` is defined and called by
  nothing.** Named in the brief so it is not raised as new. **Confirmed still
  true on 2026-09-06 rather than taken on trust:** `changeRoot` appears exactly
  once in the file, at its own definition. Desktop work, 10e.13, not mine.

- **Nothing checks that `PRACTICE_ROOT` is absolute, and every path in the system
  is built from it.** The brief asked whether that check belongs somewhere.
  **My view: it belongs in `config.py`, at the point of definition, and not in
  this sub-step.** Two reasons. It is a property of the configuration rather than
  of the status file, so a check here would catch it only on a cycle that has
  already written files under a relative root. And `config.py:117-133` already
  calls `mkdir(parents=True)` on five derived paths **at import**, so a relative
  `PRACTICE_ROOT` creates its folder tree relative to the working directory
  before any code gets a chance to object. **That is the same shape as the fourth
  trap in `CLAUDE.md`**, which is about `config.py` building folders from a
  string that is a path on one platform and a filename on another. A one-line
  assertion beside the definition would close both. **Not done here, and it needs
  a decision about what a fresh checkout with no `.env` should do.**

- **The suite has no test that `PRACTICE_ROOT` is absolute either**, which is
  consistent with there being no check.

---

## 8. Everything the brief said not to do

| Instruction | State |
|---|---|
| Do not add a `config.py` constant | None added. `PRACTICE_ROOT` at `config.py:33` is what is read |
| Do not resolve, normalise or reformat the path | Not done, and mutation B is the test that proves it stays that way |
| Do not add any field other than `practice_root` | One field added. The payload has five keys |
| Do not touch `IntelliBooks-Desktop-v3.html` | Opened read-only, to confirm `:1094` and `changeRoot`. Not written |
| Do not build the folder gate | Not built. This writes a value and checks nothing |
| Do not mark 10e as BUILT | Not marked. The design document was not edited at all |

---

## 9. Two disclosures

- **I introduced a `SyntaxWarning` and caught it on the next run.** The third
  test's docstring quotes `Path(r"C:\A\..\B")` to explain the discriminator, and
  `\A` is not a valid escape in a non-raw string. The baseline had zero warnings
  and the run after my change had one. The docstring is now raw and the warning
  is gone, confirmed by re-running.
- **I checked the written test file for mangled escapes before running it**,
  because the previous brief's report had a `\f` eaten into a formfeed and a `\t`
  into a tab. The scan covers every control character except newline and carriage
  return, and returned empty. **The `\t` slipped through last time because that
  check excluded tabs**, which is why this one does not.

---

## 10. Not done, and it is not this brief's

**10e.11 and 10e.12 are the consuming half and are IntelliBooks Desktop work.**
This sub-step gives them something to verify against and verifies nothing itself.
**Step 10e stays OUTSTANDING**, with 10e.10 now built and seven other sub-steps
outstanding.
