# Report: the test fixture's client folder, 2026-09-20

Written by the implementation session, Claude Code, 2026-09-20, 11:36 BST, read off the clock in the
reply that states it.

Worked from `PROMPT_claude_code_2026-09-20_clients_root_from_the_firm_record.md`. Step 10bl.

**Nothing in `2026-07-25_BUILD_STATUS.md` or `2026-07-25_CONSOLE_DESIGN.md` was touched.** Both were
modified by the consultant session while this ran, and neither was staged or committed by me.

**No production code was changed.**

---

## 1. The brief's claims, checked

**Both hold.** `config.py` line 862 reads `CLIENTS_ROOT = _client_top_folder(FIRMS)`. The comment
above `INTELLIBILLS_ROOT` records the removal: "CLIENTS_ROOT was `PRACTICE_ROOT / "Clients"` on this
line until 2026-09-07 ... It is not composed here any more because the client top folder is the
firm's own filing structure." **Nothing in the brief disagreed with the files.**

**One number of my own for the record.** The fixture composed it for **thirteen days**, 2026-09-07
to 2026-09-20.

---

## 2. What `config.FIRMS` holds in a test run, and how I established it

**Probed, not reasoned about.** A throwaway test printed the values under a real pytest run and was
deleted afterwards.

```
FIRMS_JSON: ...\intellibills-tests-v3740eh1\practice\Intellibills\firms.json
FIRMS_JSON exists: True
FIRMS: {"FIRM001": {"firm_id": "FIRM001", "name": "Test Firm",
        "client_top_folder": "...\practice\Client Folders",
        "publish_destinations": {"intellibooks": "Published"},
        "client_copy_trigger": "publish"}}
CLIENTS_ROOT: ...\practice\Client Folders
_client_top_folder(FIRMS): ...\practice\Client Folders
--- inside TempEnvironment ---
FIRMS still: {"FIRM001": ...}          <- not pinned, still the session record
CLIENTS_ROOT: ...\tmpcvgvve6z\Clients  <- composed by the fixture
```

**So it holds exactly one record**, written by `live_paths.write_firm_record()` before `config` is
imported, and the file it came from exists. **`_client_top_folder()` does not raise under pytest**
and never had the chance to: it raises on an empty registry and on more than one firm, and the
session gives it precisely one.

**Nothing depends on it being empty.** `tests\test_step10d_pipeline.py` is the only place that
assigns `config.FIRMS`, at three lines including `config.FIRMS = {}`, and it does so **inside** the
environment, after `__enter__` has run. So pinning it at entry changes nothing those tests rely on,
which the green suite then confirmed.

**And the fixture was not pinning `FIRMS` at all**, which the brief suspected and which the probe
settled: inside `TempEnvironment` the record still named the session folder while `CLIENTS_ROOT`
named the test's own. **The environment already disagreed with itself**, quietly, before this change.

---

## 3. What was built

**The brief's first route held and no fallback was needed.**

`TempEnvironment.__enter__()` now copies the session firm record, moves its `client_top_folder` onto
this test's own directory, pins `config.FIRMS` to the copy, and reads the path back out with
`config._client_top_folder()`. **The location is no longer stated in the fixture.**

**`FIRMS` is pinned as well as `CLIENTS_ROOT`, and that is not tidiness.** `app.py` reads
`config.FIRMS` at runtime in two places, for the firm name on an alert, so deriving the client root
from a record the environment does not hold would have left the disagreement in section 2 in place
while looking like a fix.

**`PINNED_BY_HAND` shrank by one, to `("CLIENTS_JSON",)`.** `CLIENTS_ROOT` moved to a new
`FROM_THE_FIRM_RECORD = ("FIRMS", "CLIENTS_ROOT")`, whose comment carries the reasoning and strikes
the old entry rather than deleting it.

**`TempEnvironment` gained one optional argument**, `client_top_folder`, defaulting to
`self.path / "Clients"`. Section 4 is why it exists.

**The guard in `tests\test_logs_isolation.py` still holds.** It reads `REDIRECTED + PINNED_BY_HAND`,
and `CLIENTS_ROOT` is in neither now. **That is correct rather than a gap**: `PROCESS_ONCE_WRITES`
does not list `CLIENTS_ROOT`, so the guard never asked about it. Checked by reading the tuple, not
assumed from the suite passing.

---

## 4. The discrimination result: nothing caught it, then something did

**The brief asked me to put the composed literal back and show a test going red. Nothing went red.**

```
=== the-fixture-composes-the-client-root-again ===  expects: caught
    -        firm_id, firm = next(iter(self._saved["FIRMS"].items()))
    -        config.FIRMS = {firm_id: dict(
    -            firm, **{config.CLIENT_TOP_FOLDER_FIELD: str(self.path / "Clients")})}
    -        config.CLIENTS_ROOT = config._client_top_folder(config.FIRMS)
    +        config.CLIENTS_ROOT = config.PRACTICE_ROOT / "Clients"
last line: 1603 passed, 2 skipped, 1201 subtests passed
caught by 0 reported failure(s):
verdict: NOTHING CAUGHT IT, and this mutation had to be caught
```

**The reason is not subtle and it is the whole problem with this fix.** While the record names a
folder called `Clients` under the practice root, the composition and the derivation produce the same
path character for character. **A fix nothing can catch is where both of this week's defects came
from**, which the brief says in terms, so the check is part of the change rather than a follow-up.

**What discriminates is pointing the record where a composition cannot reach.**
`_client_top_folder()`'s own docstring says the value "is an absolute path in its own right and need
not sit under the practice root", so a folder **outside** the practice root is a real case rather
than a contrived one, and no composition from `PRACTICE_ROOT` can produce it.

`TheTestFixtureUsesTheSameDerivationTest` in `tests\test_client_top_folder.py`, three tests:

| Test | What it holds |
|---|---|
| `test_the_default_keeps_the_name_every_other_test_expects` | The control. `CLIENTS_ROOT` is still `env.path / "Clients"` by default, so the guard is not bought at the expense of the 16 tests that spell the name out |
| `test_the_client_root_follows_the_record_and_not_the_practice_root` | The discriminator. The record points outside the practice root and `CLIENTS_ROOT` follows it |
| `test_the_firm_record_and_the_client_root_agree` | `config.FIRMS` and `CLIENTS_ROOT` name the same folder, which is the disagreement section 2 found |

**Re-run against the same mutation, and it is now caught:**

```
last line: 2 failed, 1604 passed, 2 skipped, 1201 subtests passed
caught by 2 reported failure(s):
  FAILED tests/test_client_top_folder.py::TheTestFixtureUsesTheSameDerivationTest::test_the_client_root_follows_the_record_and_not_the_practice_root
  FAILED tests/test_client_top_folder.py::TheTestFixtureUsesTheSameDerivationTest::test_the_firm_record_and_the_client_root_agree
verdict: OK: caught, as expected
restored, byte for byte
```

**The control passed under the mutation and that is the point of it**: the mutation produces the
right path in the default case, so a guard that failed there too would be failing for the wrong
reason.

---

## 5. Every test that moved, one by one

**None moved. Three were added and one file gained an argument.**

| File | Change | Reason |
|---|---|---|
| `tests\resolution_fixtures.py` | `CLIENTS_ROOT` derived from the firm record; `FIRMS` pinned; `PINNED_BY_HAND` shrank; optional `client_top_folder` argument | The step itself, and section 4 for the argument |
| `tests\test_client_top_folder.py` | `TheTestFixtureUsesTheSameDerivationTest` added, 3 tests | Section 4. Put in the file that owns this subject rather than in a new one |

**The 16 tests across `test_discard_client_copy.py`, `test_discard_sidecar_and_cli.py` and
`test_corrected_note.py` did not move**, which was the point of taking the brief's route rather than
the rebasing route I had costed. They hardcode `Clients` in `filed_path` constants and the folder
still carries that name, **but the name is now a property of the firm record rather than a rule the
fixture states**, which is the whole change: a firm whose folder is called anything else needs no
edit here.

**No test was changed to suit anything.**

---

## 6. Suite totals

| Figure | Tree |
|---|---|
| 1603 passed, 2 skipped, 1201 subtests | commit `809f158`, before this step |
| 1603 passed, 2 skipped, 1201 subtests | after the derivation change, before the guard: **unchanged, which is the finding in section 4** |
| **1606 passed, 2 skipped, 1201 subtests** | **now**, measured at 11:36 BST today |

**+3, which is the three tests in section 4 and nothing else.**

---

## 7. Mistakes I made, disclosed

**Two, both caught by the tooling rather than by me.**

**1. I nearly repeated the ordering bug from the archive-root change.** The derivation has to run
before the folder-creation loop, because `CLIENTS_ROOT` is one of the folders created and reading it
a line too early would make the session folder and leave the test without its own. I had made
exactly this mistake hours earlier, and the comment I wrote then is what stopped me making it again.

**2. My script to update the mutation's anchor failed its own assertion and I did not notice until
the harness refused.** The heredoc escaping did not match the file, so the mutation still carried the
stale anchor and the harness reported "the anchor appears 0 times and must appear once", **before
writing anything**. Nothing was left on disk. **That is the second time this session the harness has
caught a fault of mine rather than a fault in the code**, and the third time heredoc escaping has
cost me a round trip; I rewrote the mutation with the file's exact text instead.

---

## 8. Confidence

- **That `config.FIRMS` holds one record under pytest: high**, from a probe run under pytest and
  printed whole, not from reading `live_paths.py` and inferring.
- **That the fixture no longer states the client folder's location: high**, from reading the file:
  the only remaining path literal in `__enter__` is `CLIENTS_JSON`'s deliberately absent name, and
  the `"Clients"` that remains is the default value of an argument feeding the firm record rather
  than a path composed onto `PRACTICE_ROOT`.
- **That a regression would now be caught: high, and measured.** The same mutation went from caught
  by nothing to caught by two, with the control still passing.
- **That no existing test moved: high.** 1603 before, 1606 after, and the three added are named.
- **That pinning `config.FIRMS` breaks nothing: medium-high.** The suite is green and I checked the
  only three places that assign it, all in one file and all inside the environment. **What I have not
  done is enumerate every runtime read of `config.FIRMS` beyond the two in `app.py`** that a grep
  found.

---

## 9. The commit

Proposed, not made. Awaiting a yes, per the brief.

```
test(fixture): the test client folder comes off the firm record

config.py stopped composing PRACTICE_ROOT / "Clients" on 2026-09-07, when the
client top folder became the firm's own filing structure read from
client_top_folder on the firm record. tests/resolution_fixtures.py went on
composing it for thirteen days, so the tests worked the location out one way
and the live system worked it out another. Nothing was wrong in practice only
because the firm record happens to name a folder called Clients.

TempEnvironment now copies the session firm record, moves its client_top_folder
onto the test's own directory and reads the path back with config's own picker.
config.FIRMS is pinned alongside it, because app.py reads it at runtime and the
environment was already disagreeing with itself about which folder it meant.

Putting the composed literal back was caught by nothing across 1603 tests: both
forms produce the same path while the record names Clients under the practice
root. TheTestFixtureUsesTheSameDerivationTest points the record outside the
practice root, where no composition can follow, and the same mutation is now
caught by two tests with the default-name control still passing.

No production code changed. 1606 passed, 2 skipped, 1201 subtests.

Files: tests/resolution_fixtures.py, tests/test_client_top_folder.py
Suggested branch: feat/console-phase0 (current)
```

**No push and no PR proposed.** `feat/console-phase0` is the current branch and two other sessions
commit to it.

**The suite will be run again after the commit**, because two source guards sweep the git-tracked
set; this change adds no file, so the risk is lower than last time, and it will be run regardless.
