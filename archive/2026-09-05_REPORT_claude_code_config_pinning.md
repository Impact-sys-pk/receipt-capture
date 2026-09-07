# Report: four files to LF, and a proposal for one place that pins every config path

**Written 2026-09-05, 16:04 BST**, by the implementation session in Claude Code. Follows
`2026-09-05_REPORT_claude_code_review_root.md` and Paul's three instructions of the same day.

**Item 2 is done. Item 3 is a proposal and nothing was built.**

Suite unchanged either side: **456 passed, 200 subtests passed**.

---

## Item 2. The four text files

Converted. Only CRLF pairs were replaced, and the script refuses a file holding a lone CR. The two
CSVs were re-parsed before and after and their row and column counts compared, because a CSV is the
one shape here where a line ending is structural.

```
file                                               before    after  pairs
2026-09-05_REPORT_claude_code_layer5_context.md     24052    23621    431
Test Receipts/transactions_sample.csv               76476    75215   1261
                                                 csv rows/widths unchanged: (1261, [4])
archive/2026-09-02_REPORT_claude_code_step10a.md    28886    28311    575
worker/categorisation/receipt_accounts.csv          10491    10424     67
                                                 csv rows/widths unchanged: (67, [10])
```

**Zero git-visible change again**, the same as the sixteen: staging everything and asking git what
differs names only `2026-07-25_CONSOLE_DESIGN.md` and this report. Neither CSV is read by any code:
`transactions_sample.csv` appears once, in a help string at `seed_client_vendors.py:173`, and
`receipt_accounts.csv` is read by nothing until 10j.10.

**Five tracked files still hold CRLF and all five are binary**: two PNGs, two PDFs and an XLSX. Those
bytes are data, their blobs hold the same bytes, and converting one would corrupt it. **No text file
in the repository holds CRLF any more.**

---

## Item 3. The proposal

**Not built. What follows is what it would cover, what it would cost, and what it would replace.**

### The census it rests on

Enumerated from the syntax trees of all 47 files in `tests\`, not sampled.

- **`config.py` has 18 `Path` constants.** Tests also pin **8 other config attributes**: `CLIENTS`,
  `CLIENTS_BY_ID`, `DEFAULT_FIRM_ID`, `EXTRACTION_ENGINE`, `FIRMS`, `PREFER_DAYFIRST`,
  `_CLIENTS_MTIME` and `get_pipeline_version`.
- **31 test files pin something on config. 16 pin nothing at all.**
- **There are 15 separate fixture classes** doing this work, in 15 files.
- **The most complete is `tests\resolution_fixtures.py` at 13 of the 18 paths.** Everything else is
  below it: four files at 10, five at 6, and a long tail at 1 to 5.

**Five constants are pinned by nobody:** `BASE_DIR`, `FIRMS_JSON`, `INTELLIBILLS_ROOT`,
`PIPELINE_LOCKFILE`, `UNSYNCED_ROOT`.

**Coverage per constant, printed whole:**

| Constant | Files pinning it |
| --- | --- |
| `DB_PATH` | 20 |
| `CLIENTS_BY_ID` | 19 |
| `LOGS_DIR` | 16 |
| `RUNS_LOG` | 15 |
| `CLIENTS_ROOT` | 14 |
| `CLIENTS_JSON` | 13 |
| `_CLIENTS_MTIME` | 12 |
| `REVIEW_ROOT` | **10** |
| `CHARTS_DIR` | 5 |
| `FILES_DIR` | 5 |
| `BACKUPS_ROOT`, `PIPELINE_STATUS_PATH`, `RESOLUTIONS_DIR` | 4 each |
| `RECEIPT_INBOX_ROOT` | 3 |
| `PRACTICE_ROOT` | **1** |
| `BASE_DIR`, `FIRMS_JSON`, `INTELLIBILLS_ROOT`, `PIPELINE_LOCKFILE`, `UNSYNCED_ROOT` | **0** |

**`PIPELINE_LOCKFILE` is the one that should worry us and it is pinned by nobody.** `acquire_lock()`
at `app.py:585` writes it and `app.py:619` unlinks it. **Nothing has ever touched the live lock from
a test only because `acquire_lock()` is called from `main()` at `app.py:1364` and not from
`process_once()`**, which is what `resolution_fixtures.run_pipeline_once()` drives. That is safety by
accident, and it is one refactor away from not being true.

### Why one assignment cannot do it today

`config.py:41` and `:63-96` compute every derived path **at import**:

```python
PRACTICE_ROOT  = Path(os.environ.get("PRACTICE_ROOT", r"C:\Users\PDK7\OneDrive - ..."))
UNSYNCED_ROOT  = Path(os.environ.get("INTELLIBILLS_UNSYNCED_ROOT", r"C:\Intellibills"))
INTELLIBILLS_ROOT = PRACTICE_ROOT / "Intellibills"
REVIEW_ROOT       = INTELLIBILLS_ROOT / "Review"
...
```

**So `resolution_fixtures.py` setting `config.PRACTICE_ROOT = temp` does nothing to `REVIEW_ROOT`.**
It has to set all thirteen by hand, and that is exactly why the thirteen have to be remembered, and
why a fourteenth added tomorrow will be forgotten. **The per-file comment is not the failure; the
shape is.**

### The proposal: a session-level redirect in `tests\conftest.py`

**There is no `conftest.py` in this repository and no `pytest.ini`, `pyproject.toml`, `setup.cfg` or
`tox.ini`.** So this is a new file and it collides with nothing.

`PRACTICE_ROOT` and `UNSYNCED_ROOT` are read from the environment at `config.py:33-37`. **A
`conftest.py` that sets those two variables to a session temp directory before anything imports
`config` redirects all 18 constants at once**, because every one of them is derived from those two.

Roughly twenty lines: make a session temp directory, set the two variables, and record the true
values on the module so the handful of tests that legitimately need the real paths can ask for them.

### What it would cover

- **All 18 `Path` constants**, including the five nobody pins today and `PIPELINE_LOCKFILE` in
  particular.
- **Every test file, including the 16 that pin nothing**, without any of them being edited.
- **A test file written next month**, whose author never reads this document. That is the property
  the two existing warning comments do not have, and it is the whole point.
- **`config.py`'s import-time `mkdir` block at `:129`**, which currently creates `Intellibills\`,
  `Documents\`, `Backups\`, `db\` and `logs\` in the live practice root on any import. Under the
  redirect it creates them in temp. That also removes the fourth trap in `CLAUDE.md` for anything run
  through pytest.

### What it would cost

**Four things, and the second is the one that would bite.**

1. **A new dependency on import order.** `conftest.py` has to set the variables before `config` is
   imported anywhere. pytest imports `conftest.py` before the test modules under it, so this holds
   for a plain run, **but it is a rule that is invisible when broken**: a plugin importing `config`
   first would silently give every test the live paths again, and everything would still pass. It
   needs an assertion in `conftest.py` that `config` is not yet in `sys.modules`, so the failure is
   loud.

2. **Six tests that read the real bundle on purpose would silently stop testing it.**
   `RealBundleTest`, `RealBundleFallbackTest` and `RealBundleRatesTest` all skip when the bundle is
   absent, so under a redirected `CHARTS_DIR` **they would skip rather than fail, and a skipped test
   reports success.** That is a check that cannot fail, arriving by the back door. They would each
   need one line to read the captured true path instead. Same for the two isolation tests,
   `test_logging_setup.py` and `test_logs_isolation.py`, which assert nothing was written to the
   **real** logs directory: under a global redirect those assertions become vacuous.
   **Five files, one line each, and the change makes their intent explicit rather than implicit,
   which is a gain rather than a cost.**

3. **The database and the log files move for every test**, including the 16 that pin nothing. Those
   16 pass today because they never touch a path. If any of them turns out to touch one, its
   behaviour changes. **The write sweep says none of them writes anywhere outside temp**, so the risk
   is bounded and measured, but it is not zero.

4. **It covers paths and not the other 8 attributes.** `CLIENTS_BY_ID`, `FIRMS`, `PREFER_DAYFIRST`
   and the rest still leak per-test, and `test_prefer_dayfirst_isolation.py` exists precisely because
   one of them did. **A conftest could reset those between tests as well**, but that is a second
   decision and I would not fold it into the first.

`test_path_layout.py` is **not** affected: it asserts relationships between constants, such as
`INTELLIBILLS_ROOT == PRACTICE_ROOT / "Intellibills"`, and those hold wherever the root points.

### Which existing fixtures it would replace

**None, immediately, and that is the argument for it.** It is additive. The 15 fixture classes keep
working: they would redirect from the session temp directory to their own per-test temp directory,
which is what they already do relative to the live root. **No migration, no rewrite of 31 files, and
it can be reverted by deleting one file.**

**What it makes optional afterwards**, as separate work nobody has to do at once:

- The **ten hand-rolled `TempEnvironment` classes** in `test_embedded_image_pipeline_version.py`,
  `test_extraction_details.py`, `test_failure_path_engine.py`, `test_resolution_service.py`,
  `test_resolution_view.py`, `test_resolve_receipt_zero_and_types.py`,
  `test_retroactive_categorise_sidecar.py`, `test_review_pair_cleanup.py`,
  `test_sidecar_category_keys.py` and `test_status_counts_from_db.py` exist mostly to redo the
  redirect. Their **seeding** helpers differ and are worth keeping; the redirect half becomes
  redundant.
- **`tests\resolution_fixtures.py` is the one to keep and grow.** It already has the shape, the
  reasoning in its docstring, and the seeding helpers. It would shed its thirteen assignments and
  keep `seed()`, `engine()`, `inbox_dir()`, `RecordingExtractor` and `run_pipeline_once()`.
- `tests\chart_fixtures.py` stays as it is: it writes bundle **content**, which is a different job
  from redirecting a path, and the content is what its callers need.

### The alternative I considered and would not recommend

**Making the derived paths lazy in `config.py`**, so `PRACTICE_ROOT` is genuinely the single point
and pinning it pins everything. It is the structurally correct fix and it is the expensive one:
every `config.REVIEW_ROOT` in the codebase becomes a call, or the module grows a `__getattr__` and
the existing assignments have to be deleted so it is reached, at which point every fixture's restore
loop needs `delattr` rather than `setattr` and would be wrong in a way that still passes. **It
changes production code to fix a test problem, which is the wrong direction when a twenty-line
conftest covers the same 18 constants.**

**A single shared `TempEnvironment` replacing all 15 classes** is the other option. It is a migration
of 31 files whose fixtures have genuinely different seeding helpers, and the tests that currently
rely on **not** pinning something would each need finding first. Higher cost, same coverage, and it
does not cover a file written next year unless its author uses it.

### What I would want before building it

Two things, both cheap.

- **The five real-path tests identified and given the captured true root in the same commit**, not
  afterwards. If they land skipped, the suite reports 456 passes and six of them are asserting
  nothing.
- **A test that the redirect is in force**, asserting `config.PRACTICE_ROOT` is under the session
  temp directory. Without it the whole thing can stop working silently, which is the failure mode
  the proposal exists to remove.

---

## Confidence

**High on the census**, because it is read from the syntax trees of all 47 files in `tests\` and
printed whole, not sampled: 18 Path constants, 8 other attributes, 31 files pinning something, 16
pinning nothing, 15 fixture classes, and 5 constants pinned by nobody.

**High that the env-var route redirects all 18**, because `config.py:33-37` reads both roots from the
environment and `:41` and `:63-96` derive every other path from them, which I read rather than
inferred.

**Medium on the cost estimate**, and the uncertainty is item 2 of the four: I have identified five
files that would need the captured true path, from the live-read sweep. **That sweep only sees what
today's tests actually read**, so a test that reads a real path conditionally, on a branch that did
not run, would not appear in it.

**None on whether Paul wants this at all.** It is a proposal.
