# Report: one place pins every config path, and nothing skips to get there

**Written 2026-09-05, 16:11 BST**, by the implementation session in Claude Code. Follows
`2026-09-05_REPORT_claude_code_config_pinning.md`, which was the proposal, and Paul's instruction of
the same day to build it with one change.

**Built. Your change is in and it is the reason the count went up rather than down.**

| Run | Result |
| --- | --- |
| Before | **456 passed, 200 subtests passed** |
| Redirect only, before your change was applied | **450 passed, 6 skipped, 198 subtests** |
| Final | **467 passed, 226 subtests passed, 0 skipped** in 12.46s |

**The middle row is the finding.** It is what the proposal would have shipped if I had built it as
written: six tests skipping, the suite still green, and three classes whose subject is the published
bundle quietly testing nothing.

---

## What was built

Three new files and five edited.

**`tests/live_paths.py`** does the work. It asserts `config` is not yet in `sys.modules`, reads the
two root declarations out of `config.py`'s **source** rather than importing it, captures the live
roots, then redirects both in the environment to a session temp directory.

**`tests/conftest.py`** is nineteen lines and imports exactly one thing. Its whole job is to make
that import happen before any test module loads. pytest imports `conftest.py` first, so that is what
gives the ordering.

**`tests/test_conftest_redirect.py`** asserts the arrangement is actually in force, which is the test
the proposal said it would need.

### Reading the defaults rather than copying them

`config.py:33-37` declares both roots as `Path(os.environ.get(<name>, <default>))`.
`_root_declaration()` walks `config.py`'s syntax tree and pulls out the variable name and the default
for each. **Not copied, because a second statement of those defaults would drift**, and not imported,
because `config.py:117-129` calls `mkdir` on five paths at import and that is the fourth trap in
`CLAUDE.md`.

It raises rather than guessing if the shape moves. **A wrong default there would silently capture the
wrong live root**, and the two isolation tests would then assert against a folder that does not
exist, which passes.

It also calls `load_dotenv()` before capturing, mirroring `config.py:7`. Neither root is in `.env`
today, checked; that is so it stops being load-bearing.

### What it covers

**All 18 `Path` constants**, asserted one at a time rather than sampled, including the five no
fixture pinned at all: `FIRMS_JSON`, `INTELLIBILLS_ROOT`, `PIPELINE_LOCKFILE`, `UNSYNCED_ROOT` and
`RESOLUTIONS_DIR`. `BASE_DIR` is the repository, is derived from neither root, and is named as the
one exception rather than skipped by a rule.

`RESOLUTIONS_DIR` needed its own line: `config.py:96` reads an environment override of its own before
falling back to `INTELLIBILLS_ROOT`, so a value in `.env` would have survived the redirect and
pointed at the live folder. It is cleared for the run.

**Every test file, including the 16 that pin nothing**, with no edit to any of them. **The 15
existing fixture classes are untouched and still work**, redirecting from the session temp directory
to their own per-test one. Nothing was replaced.

And `config.py:129`'s import-time `mkdir` block now builds its folders in temp.

---

## Your change: no silent skips

**Applied, and it was needed.** Building the redirect alone produced exactly the six skips the
proposal predicted:

```
SKIPPED tests\test_chart_bundle.py:297: no chart bundle at ...\practice\Intellibills\Charts
SKIPPED tests\test_fallback_accounts.py:693: no fallback table at ...\practice\Intellibills\Charts
SKIPPED tests\test_fallback_accounts.py:696: no fallback table at ...\practice\Intellibills\Charts
SKIPPED tests\test_fallback_accounts.py:699: no fallback table at ...\practice\Intellibills\Charts
SKIPPED tests\test_vat_rates.py:299:  no VAT rate table at ...\practice\Intellibills\Charts
SKIPPED tests\test_vat_rates.py:302:  no VAT rate table at ...\practice\Intellibills\Charts
```

`live()` maps any redirected config path back onto the captured root, and `LiveBundle` points
`CHARTS_DIR` at the real published bundle for the duration of one test, clearing and restoring the
four parse caches so a cached read of the fixture's chart cannot answer for the real one.

**The three real-bundle classes now read the real bundle again** and skip only when there is
genuinely no practice root, which is the condition they always had.

**The two isolation classes gained a second assertion each rather than having one replaced.**
`LogsIsolationTest` and `SuiteWritesNoLogsTest` snapshot the redirected logs directory **and**
`live(config.LOGS_DIR)`. The first still catches a leak inside the test; the second is the class's
actual subject, the live `resolve.log` this suite once appended 5 KB per run to, and under a blanket
redirect it would have been comparing a temp folder with itself.

`live()` **raises** for a path under neither root rather than returning it unchanged, because
returning it would hand a test a temp path it believes is live, which is how a vacuous assertion gets
written in the first place.

---

## Verification

### The two sweeps, re-run

**Live reads: 10 tests across 6 files, every one deliberate and every access a read.** The five
classes above plus `test_conftest_redirect.py`'s own guard, which reads the bundle to check the three
real-bundle classes did not skip. Nothing else in the suite touches either live root.

**Writes outside a temp directory: one, and it is `\\.\nul`**, the Windows null device, opened at
import. Unchanged from before the conftest.

Both sweep plugins had to stop importing `config` at module scope to run at all, because a `-p`
plugin loads before `conftest.py`. **That is the assertion doing its job on the first thing that
broke it**, and it broke loudly:

```
tests\live_paths.py:73: in <module>
    assert "config" not in sys.modules, (
E   AssertionError: tests/live_paths.py must run before config is imported, and config is
    already in sys.modules. Something imported it first: <module 'config' from ...>.
    Without this ordering the redirect below does nothing and the whole suite runs against
    the live practice root.
```

### Mutation

Four, each on a pristine copy with the file restored and the restore hash-checked.

| Mutation | Result |
| --- | --- |
| **M13** the redirect is not applied at all | **37 failed.** Named red: both `RedirectIsInForceTest` cases, two `LivePathsSurviveTest` cases, and all six real-bundle tests plus the three isolation tests, which now fail rather than skip |
| **M14** `live()` returns an unmapped path instead of raising | 1: `LivePathsSurviveTest::test_live_refuses_a_path_under_neither_root` |
| **M15** a real-bundle class loses `LiveBundle` | 1, and it is **the mutation that matters**: `LivePathsSurviveTest::test_the_real_bundle_classes_are_not_skipping`, with "RealBundleFallbackTest skipped under the redirect, which reports success while testing nothing". The run also shows **3 skipped**, which is the failure you rejected, caught |
| **M16** the capture is wrong and the live root becomes a temp path | 1: `LivePathsSurviveTest::test_the_live_roots_are_what_config_would_have_resolved`, plus 7 skips |

**M15 is the red-before-green for your change, applied after the fact.** It reproduces the state the
proposal would have shipped in, and one named test catches it.

---

## What it does not do, stated plainly

- **Paths only.** `CLIENTS_BY_ID`, `CLIENTS`, `FIRMS`, `PREFER_DAYFIRST`, `EXTRACTION_ENGINE`,
  `DEFAULT_FIRM_ID`, `_CLIENTS_MTIME` and `get_pipeline_version` are still each test's own business.
  A conftest could reset those between tests too; that is a second decision and I have not folded it
  in.
- **pytest only.** A module run directly through its `if __name__ == "__main__": unittest.main()`
  block does not load `conftest.py` and gets the live paths, exactly as before this existed. **No
  regression, but no improvement either.** `.\.venv\Scripts\python.exe -m pytest -q` is the
  documented way to run the suite and is what CLAUDE.md names.
- **It replaced nothing.** The ten hand-rolled `TempEnvironment` classes still redo the redirect;
  they are now redundant rather than wrong, and collapsing them into `resolution_fixtures.py` is
  separate work nobody has to do at once.

---

## Mistakes I made, disclosed

Two, both caught in the session.

1. **I ran the mutation sweep with `-rs`, which suppresses the failure names**, so the first pass
   printed "NOTHING WENT RED" beside runs that plainly said "37 failed" and "1 failed". Had I read
   only the RED lines I would have reported four untested branches. **The tell was the contradiction
   between two numbers in the same line**, and the fix was `-rfs`. This is the same shape as the
   `git status` and `git diff` disagreement earlier today: two outputs answering different questions
   and only one of them mine.
2. **M15's failure still came back unnamed after the fix**, because it is a subtest and the summary
   line is `SUBFAILED(cls=...)`. I ran that one mutation by hand rather than reporting it as
   uncaught. **It is the most important of the four**, so reporting it as untested would have been
   the worst available error.

---

## Confidence

**High that all 18 constants are redirected**, because `RedirectIsInForceTest` enumerates
`vars(config)` at run time, asserts the count is 18 so a nineteenth cannot slip in unchecked, and
checks each one individually.

**High that the six real-bundle tests are reading the real bundle**, because the live-read sweep
shows them opening `Intellibills\Charts\Master_COA.csv`, `PHV_DRIVER.csv`, `fallback_accounts.csv`
and `vat_rates.csv` in OneDrive by name, and because removing `LiveBundle` from one of them turns a
named test red.

**High that no test writes outside a temp directory**, unchanged from this morning and re-measured
under the conftest.

**Medium that nothing else in the suite depended on the live paths in a way that has not surfaced.**
The suite is green and both sweeps are clean, but a branch that did not execute today would not
appear in either. That is the same limit the earlier sweep had and it has not changed.
