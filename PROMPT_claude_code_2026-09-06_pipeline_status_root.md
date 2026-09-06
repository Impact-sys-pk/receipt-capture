# Brief: `pipeline-status.json` states the practice root

**Sub-step 10e.10 of section 16 of `2026-07-25_CONSOLE_DESIGN.md`.** Read this whole file before
starting. Read 10e in the design document too, because this sub-step is one third of a three-part
change and the other two parts are not yours.

**It is a small change with one deliberate breakage.** One field is added to a JSON payload. A test
asserts today that the payload has exactly four keys, and it will fail. That failure is the point of
task 2 and is not a fault to work around.

---

## Why this exists, in one paragraph

IntelliBooks Desktop is given the practice root folder through a browser folder picker. The browser
hands it a folder handle and a folder **name**, and no path. So IntelliBooks has never been able to
say which folder it is actually working in, and it cannot tell the right folder from a
similarly-named wrong one.

**10e.9 settles who decides**: the practice root is not a setting, it does not appear on any page,
and the pipeline's configuration is the single authority for it, because the pipeline cannot read a
file inside the practice root to learn where the practice root is. **IntelliBooks verifies; it does
not decide.**

This sub-step gives IntelliBooks something to verify against. **The two sub-steps that consume it,
10e.11 and 10e.12, are IntelliBooks Desktop work and are not in this brief.**

---

## Task 1. Add the field

`_write_pipeline_status()` at `app.py:132` builds a four-key payload:

```
last_run, processed_today, review_count, last_error
```

**Add a fifth key, named `practice_root`.** The name is fixed by amendment 241 of
`2026-07-25_CONSOLE_DESIGN.md` and the IntelliBooks half will read that exact key. Do not rename it,
do not nest it, and do not add any other field.

**Its value is `str(config.PRACTICE_ROOT)`, as configured.**

- **Do not call `.resolve()` on it**, and do not normalise the case or the separators. The value must
  be what the pipeline is configured with, so that a person comparing it against `.env` or against
  `config.py:33` sees the same string. A resolved value can differ from the configured one through
  case, a junction or a symlink, and then the two sides disagree over a difference that does not
  exist
- `PRACTICE_ROOT` is at `config.py:33` and reads from the `PRACTICE_ROOT` environment variable with a
  Windows literal default. **It was `ONEDRIVE_ROOT` until sub-step 10d.21 renamed it on 2026-09-03**,
  so do not be surprised by the old name in older documents
- Backslashes are escaped by `json.dumps()`. That is correct and is not to be worked around

**It is written on every cycle, including a failed one.** `_write_pipeline_status()` is called from
the `finally:` block at `app.py:1345`, so this is already true and nothing about the call site
changes. **Do not make the field conditional.** The case where IntelliBooks most needs to know which
folder it is looking at is the case where the pipeline is unhealthy.

The only caller is `app.py:1345`. Enumerated by searching every `.py` in the repository for
`_write_pipeline_status`, excluding `.history\`.

## Task 2. The test that asserts the shape, and it must not be deleted

`tests/test_status_counts_from_db.py`, around line 207:

```python
# The shape IntelliBooks Desktop reads must not change.
self.assertEqual(
    sorted(payload.keys()),
    ["last_error", "last_run", "processed_today", "review_count"],
)
```

**This test is doing its job.** It is a contract test between two products and it caught the change,
which is what it was written for.

- **Update it to the new five-key shape.** Do not delete it and do not loosen it into a subset check.
  A subset check would stop it catching the next unannounced field
- **Add an assertion on the value**, not only on the key: `payload["practice_root"]` equals
  `str(config.PRACTICE_ROOT)` as the test environment has redirected it. The test suite redirects
  both roots through `tests/live_paths.py`, imported from `tests/conftest.py`, so the value under
  test is the temporary root and not Paul's real one. **Say in your report what value it asserted**
- **Add one test that the field is written when the run fails**, since that is the case it exists
  for. `tests/test_failure_path_engine.py` already builds a failing `process_once()` environment;
  put it wherever it reads best and say which file you chose

**Mutation to run and report.** Remove the `practice_root` line from the payload and show which tests
go red. If only one does, say so: a single guard on a cross-product contract is worth knowing about.

## Task 3. What must not break

- **`IntelliBooks-Desktop-v3.html:1094` reads this file today**, through
  `readJSON(pd, "pipeline-status.json")`, and takes named fields off it. Adding a key is additive and
  should be invisible to it. **Confirm by reading that line, do not assume it**
- The five other test files that redirect `config.PIPELINE_STATUS_PATH` are
  `tests/resolution_fixtures.py`, `tests/test_failure_path_engine.py`,
  `tests/test_logs_isolation.py`, `tests/test_embedded_image_pipeline_version.py` and
  `tests/test_path_layout.py`. **None of them asserts the payload's keys**, checked by reading every
  `pipeline_status` line in each. Only `test_status_counts_from_db.py` does. **If you find a sixth,
  report it**

---

## Verify, and report what you ran

**Write the report to `2026-09-06_REPORT_claude_code_pipeline_status_root.md` in the repository
root.**

1. `.\.venv\Scripts\python.exe -m pytest -q` **before and after. Quote both figures.** I have not run
   the suite and I have no shell, so I am not giving you a baseline to match: the last figure on
   record is Claude Code's own, 524 passed and 330 subtests, and three commits have landed since
2. **Print the actual file.** Run a cycle, or call `_write_pipeline_status()` directly, and quote
   `pipeline-status.json` whole. **Show the real backslashes as they appear on disk**
3. Report the mutation result from task 2

## Do not

- Do not add a `config.py` constant. `PRACTICE_ROOT` already exists
- Do not resolve, normalise or reformat the path
- Do not add any field other than `practice_root`
- Do not touch `IntelliBooks-Desktop-v3.html`. The consuming half is 10e.11 and 10e.12 and belongs to
  the IntelliBooks Desktop session
- Do not build the folder gate. This brief writes a value; it checks nothing
- Do not mark 10e as BUILT. This is one of eight outstanding sub-steps

## Flag, do not fix

- **`changeRoot()` at `IntelliBooks-Desktop-v3.html:1086` is defined and called by nothing.** Recorded
  at sub-step 10e.13 on 2026-08-31 and still true, read on 2026-09-06. It is Desktop work and it is
  not yours. It is named here so you do not raise it as new
- **If `PRACTICE_ROOT` is ever not absolute, every path built from it is already wrong.** Nothing
  checks that today. Do not add a check in this brief; report it if you think it belongs somewhere

## Commit

Commit the working tree first if anything is uncommitted, then one commit for this brief's work. The
message says the field name and quotes the suite figures before and after.
