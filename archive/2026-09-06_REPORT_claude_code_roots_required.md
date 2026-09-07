# Report: the two roots are required, and absolute

**Claude Code, 2026-09-06, 13:00 to 14:11 BST.** Written from
`PROMPT_claude_code_2026-09-06_roots_required.md`. Times are BST, read from the machine clock at
14:11; the consultant session's shell reports UTC and would call the same instant 13:11.

**Result: done, all four tasks, with one repair the brief anticipated in a different form.**
`tests/live_paths.py` does set the environment variables rather than the constants, which is what the
brief hoped, **and it still broke the whole suite**, for a reason the brief did not predict: it reads
the two roots out of `config.py`'s source and requires the two-argument
`Path(os.environ.get(<name>, <default>))` shape, which this change removes. Section 5 has the detail.

---

## 1. The suite, before and after

**Before**, on the tree as committed at `1da13be`:

```
526 passed, 330 subtests passed in 16.79s
```

**After**, the whole change in place:

```
535 passed, 340 subtests passed in 15.33s
```

Both run as `.\.venv\Scripts\python.exe -m pytest -q`. **The brief's figure of 526 passed, 330
subtests matched exactly.**

**The arithmetic on the difference, because a count that is not reconciled is a count nobody has
checked.** Nine new tests, all in `tests/test_required_roots.py`: 526 + 9 = 535. Ten new subtests:
eight in the new file, being three refusal states for each of the two variables plus two constants in
the source-shape test, and two in the rewritten
`test_the_live_roots_are_what_config_would_have_resolved`. 330 + 10 = 340.

---

## 2. Task 1, the `.env` line

**Done first, before anything in `config.py` changed.** Two keys appended:

```
PRACTICE_ROOT
INTELLIBILLS_UNSYNCED_ROOT
```

`.env` now holds ten keys. The other eight are unchanged and are not printed here.

**The values were taken by parsing `config.py` with `ast` and writing the parsed string constants
straight into the file**, so no path passed through a keyboard or through this report. The two
literals it found were the ones at `config.py:33` and `:37`.

**How the unquoted-backslash behaviour was confirmed.** Not from the brief and not from the
documentation: `dotenv_values('.env')` was run against the written file and its return value
compared, in Python, against `r"C:\Users\PDK7\OneDrive - Intellitax Accounting Limited"` and
`r"C:\Intellibills"`. Both compared equal, so python-dotenv read the value literally with the
backslashes intact and nothing was interpreted as an escape.

**One detail worth recording: `.env` did not end with a newline.** Appending without checking would
have joined `POLL_INTERVAL_SECONDS=300` to the first new line and corrupted both. The file was read
as bytes, the absence of the trailing newline was confirmed, and a newline was written before the new
block.

## 3. Task 2, `.env.example`

Both keys added at the top of the file, above the IMAP block, with a comment that states they are
required, that each must be absolute, that `config.py` refuses to import otherwise, and that neither
value is quoted or escaped. The values are placeholders and are not Paul's paths:

```
PRACTICE_ROOT=C:\Users\<you>\OneDrive - <Your Practice Name>
INTELLIBILLS_UNSYNCED_ROOT=C:\<a folder outside OneDrive>\Intellibills
```

**The angle brackets are deliberate.** A placeholder that is itself a valid absolute path would pass
the new check, so somebody copying `.env.example` to `.env` unedited would get folders built at the
example location rather than a refusal. These fail on sight instead.

## 4. Task 3, `config.py`

The two definitions at `:33-37` are replaced by one helper and two calls, now at `:38-69`:

```python
def _required_root(variable: str) -> Path:
    value = os.environ.get(variable)
    if not value or not Path(value).is_absolute():
        raise RuntimeError(...)
    return Path(value)


PRACTICE_ROOT = _required_root("PRACTICE_ROOT")
UNSYNCED_ROOT = _required_root("INTELLIBILLS_UNSYNCED_ROOT")
```

**Both literals are deleted. `grep -n "C:" config.py` now returns nothing at all**, and a test asserts
that, described in section 6.

**On "one check per root", which the brief was firm about.** This is one function called twice, not
one combined check. Each call raises its own message naming its own variable, and a test asserts that
the message for one root does not name the other. **The check runs at the definition**, which is
earlier than the brief's "immediately after the two definitions" rather than later, and 92 lines
above the `mkdir` block, now at `:161-165`.

`RuntimeError`, not `assert`. There is a test that runs the child under `python -O` for exactly that
reason.

### The refusal messages, quoted from a run

Produced by importing `config` in a subprocess with the variable removed. Six cases were run, three
per variable, and each names its own variable and quotes its own value. Two of the six in full:

```
RuntimeError: PRACTICE_ROOT is required and must be an absolute path. It read None. There is no
default: config.py carried one until 2026-09-06 and it was one person's own folder, which is how a
bare import made folders on machines it did not belong to. Set it in
C:\LastingImpact\receipt_capture\.env, unquoted and with the backslashes unescaped, and see
C:\LastingImpact\receipt_capture\.env.example for the shape.
```

```
RuntimeError: INTELLIBILLS_UNSYNCED_ROOT is required and must be an absolute path. It read
'unsynced_relative'. There is no default: config.py carried one until 2026-09-06 and it was one
person's own folder, which is how a bare import made folders on machines it did not belong to. Set it
in C:\LastingImpact\receipt_capture\.env, unquoted and with the backslashes unescaped, and see
C:\LastingImpact\receipt_capture\.env.example for the shape.
```

The other four differ only in the variable name and the quoted value: `''` for empty, `None` for
unset, `'not_absolute_here'` for a relative practice root.

**And the temp working directory the six children ran in was empty afterwards**, checked
programmatically, which is the ordering claim rather than an assertion about it.

### One comment changed that the brief did not name

The comment above the definitions, at `config.py:27-35`, ended "Neither variable is set in .env
or .env.example, so the rename changes no configuration." That sentence is now false because of task 1. It is struck through in place and the
correction sits beside it, per the project's convention. **Disclosed because the brief said only the
two definitions and the new checks**, and a comment that describes the lines being changed seemed
worse left true-looking and wrong than corrected.

## 5. Task 4, the tests

### What `tests/live_paths.py` actually does

Read, not assumed. Three questions, three answers:

- **It sets the environment variables, not the constants.** `os.environ[PRACTICE_VAR] = ...` and
  `os.environ[UNSYNCED_VAR] = ...`, and the variable names are read out of `config.py`'s source
  rather than copied.
- **The values it sets are absolute.** They come from `tempfile.mkdtemp()`, which returns an absolute
  path, with `/ "practice"` and `/ "unsynced"` joined onto it.
- **It sets them before `config` is imported.** `tests/conftest.py` imports `live_paths` as its only
  import, and `live_paths` opens with a module-level `assert "config" not in sys.modules`.

**So the arrangement this change depends on is sound, and the brief's predicted failure did not
happen.**

### The failure that did happen, and it is the brief's central risk arriving by another door

`live_paths._root_declaration()` parses `config.py`'s AST and requires each root to be declared as
`Path(os.environ.get(<name>, <default>))` with two constant arguments. Removing the default removed
that shape, so the function raised the error it was written to raise and **the entire suite died at
conftest import**:

```
ImportError while loading conftest 'C:\LastingImpact\receipt_capture\tests\conftest.py'.
tests\live_paths.py:132: in <module>
    PRACTICE_VAR, PRACTICE_DEFAULT = _root_declaration("PRACTICE_ROOT")
E   RuntimeError: config.py no longer declares PRACTICE_ROOT as Path(os.environ.get(<name>,
    <default>)). tests/live_paths.py reads it from the source to avoid holding a second copy of the
    defaults, so this needs updating alongside config.py rather than being worked around.
```

**That is the failure mode working exactly as designed**, and it is worth saying so: the file refused
to guess rather than silently capturing a wrong live root, which is what its docstring says it exists
to prevent.

**The fix, in two parts.**

1. `_root_declaration(constant) -> (var, default)` becomes `_root_variable(constant) -> str`. It
   matches an assignment whose value is a call taking exactly one string argument and no keywords,
   and returns that string. **It deliberately does not match on `_required_root` by name**: the
   helper's name is `config.py`'s business, and matching it would put a second copy of something in
   this file, which is the thing the function exists to avoid.
2. `LIVE_PRACTICE_ROOT` and `LIVE_UNSYNCED_ROOT` have no default to fall back on any more, so they
   are read from the environment, which `load_dotenv()` has already populated from `.env` at that
   point, through a `_live_root()` that refuses an unset, empty or relative value with a message
   naming the variable and both `.env` files. **Refusing matters here.** With no default, an unset
   variable would have made `LIVE_PRACTICE_ROOT` into `Path('.')`, `live()` would have mapped every
   redirected path onto the repository, and the two isolation tests would have asserted that nothing
   was written to a folder that is not the one they mean. Green, and testing nothing.

`tests/test_conftest_redirect.py::LivePathsSurviveTest::test_the_live_roots_are_what_config_would_have_resolved`
compared the captured roots against the source defaults, which no longer exist. It now asserts that
the two variable names still come out of `config.py`'s source and are the expected two, and that each
captured root is absolute and is not under the session temp directory, which is what a capture taken
after the redirect would look like. Two subtests.

### The refusal test: `tests/test_required_roots.py`, 9 tests, 8 subtests

**A subprocess, not `importlib.reload`, and the reason is not only awkwardness.** `config` is
imported by `conftest.py` before any test module and by thirty modules in this process, so a reload
recomputes eighteen constants that other modules already hold, and a reload that *succeeded* would
re-run the `mkdir` block against whatever the patched environment said. A subprocess starts with no
`config` in `sys.modules`, takes its folders with it, and tests the actual failure, which is an
import in a fresh process.

**A trap inside that, and it would have made the test worthless.** `config.py` calls `load_dotenv()`
at import, and after task 1 `.env` sets both roots. A child that merely deleted a variable from its
environment would have it put straight back by dotenv, and the "unset" case would have been an import
that succeeded and a test that passed for the wrong reason. **The child therefore installs a stub
`dotenv` module in `sys.modules` before importing `config`**, so its environment is exactly what the
test gives it. Setting a variable to an offending value does survive `.env`, because python-dotenv
does not override a variable already present, but unset does not, and unset is the case the brief
asked for.

The nine:

| Test | What it holds down |
| --- | --- |
| `test_a_good_pair_imports` | The control. Every other test asserts a failure, so without this they would all pass against a child that could not start at all |
| `test_practice_root_is_required_and_absolute` | Three subtests: unset, empty, relative. Each asserts the message names `PRACTICE_ROOT`, quotes the value read, and does **not** name the other variable |
| `test_unsynced_root_is_required_and_absolute` | The same three for `INTELLIBILLS_UNSYNCED_ROOT` |
| `test_the_message_names_both_env_files` | The message carries the full path of `.env` and of `.env.example` |
| `test_it_is_a_runtime_error_and_not_an_assert` | Runs the child under `python -O` |
| `test_a_relative_practice_root_creates_nothing` | The child's working directory is an empty temp folder and stays empty |
| `test_a_relative_unsynced_root_creates_nothing` | The same for the other root |
| `test_each_root_is_declared_with_the_variable_name_and_nothing_else` | Reads the AST: one call, one string argument, no keywords |
| `test_config_carries_no_absolute_path_literal` | No string constant anywhere in `config.py` looks like an absolute path |

The last two read the source rather than the behaviour, on purpose. **Every behavioural test above
sets or unsets an environment variable, and a reintroduced default would simply answer in its place**,
so no amount of behavioural testing can catch a fallback coming back. Mutations 3 and 4 below are
what proves that claim rather than asserting it.

## 6. Mutations

Four, each applied to a pristine copy of `config.py` and run against the whole suite, with the file
restored afterwards and the restoration verified by comparing the text. The pristine copy was taken
first and confirmed byte-exact by md5, `7b2c9341d07c29b0a529594914f621a7`, which is also the md5 of
the file now.

| Mutation | Suite | Red |
| --- | --- | --- |
| 1. `if not value or not Path(value).is_absolute():` becomes `if False:`, so both checks pass unconditionally | 10 failed, 531 passed | 4 tests and 6 subtests, all in `test_required_roots.py`: both refusal tests in all three states, `test_it_is_a_runtime_error_and_not_an_assert`, `test_the_message_names_both_env_files`, and both ordering tests |
| 2. The absoluteness half dropped, `if not value:`, both roots | 5 failed, 532 passed | Both refusal tests in the `relative` state, `test_it_is_a_runtime_error_and_not_an_assert`, and both ordering tests |
| 3. `PRACTICE_ROOT` gets its old default back, that root only | 7 failed, 531 passed | `test_practice_root_is_required_and_absolute` in all three states, `test_the_message_names_both_env_files`, `test_a_relative_practice_root_creates_nothing`, `test_it_is_a_runtime_error_and_not_an_assert`, and `test_config_carries_no_absolute_path_literal` |
| 4. `INTELLIBILLS_UNSYNCED_ROOT` gets its old default back, that root only | 5 failed, 533 passed | `test_unsynced_root_is_required_and_absolute` in all three states, `test_a_relative_unsynced_root_creates_nothing`, and `test_config_carries_no_absolute_path_literal` |

**No check is uncovered.** Every mutation is caught, and each is caught by tests that name the thing
that was mutated: mutation 3 turns nothing about the unsynced root red and mutation 4 turns nothing
about the practice root red, which is the "two separate messages" requirement holding rather than
being asserted.

**Two things this exercise showed that are worth keeping.**

- **Mutations 3 and 4 had to be written twice.** The first version restored the literal default in its
  original `Path(os.environ.get(<name>, <default>))` form, which `_root_variable` refuses, so the
  suite died at collection and reported no failures at all rather than showing which tests catch a
  fallback. The second version keeps the one-string-argument call shape and reintroduces the fallback
  inside a helper. **A mutation that breaks collection tells you nothing about coverage**, and the
  first run's "NOTHING WENT RED" for both was my parser reporting an absence of `FAILED` lines from a
  suite that never ran.
- **The first mutation run under-reported.** It printed 4 red for mutation 1 while the summary line
  said 10 failed, because `pytest-subtests` writes `SUBFAILED` and the parser only matched `FAILED`.
  The table above is from a rerun that matches both, and every figure in it was read off the run
  rather than inferred from the counts.

## 7. The pipeline still starts on Paul's machine

Three checks, strongest last.

1. **All eighteen `config` Path constants are identical before and after.** Captured to a file by
   importing `config` with `.env` in force before `config.py` was touched, captured again afterwards,
   and compared as a dictionary: `18 -> 18`, `identical: True`, `differences: {}`. That is the whole
   surface the change could have moved.
2. **`import app` succeeds in a fresh process**, pulling in the entire pipeline import chain, 30
   `worker` modules. Everything inside `app.py` runs under `main()` behind an `if __name__` guard, so
   this starts no polling, takes no lock and sends no mail. `PRACTICE_ROOT`, `UNSYNCED_ROOT`,
   `DB_PATH`, `CHARTS_DIR` and `CLIENTS_JSON` all resolve to their real locations and all exist on
   disk; the registry loads 5 client records and 1 firm.
3. **535 tests pass**, every one of them importing `config` through the redirect.

**What none of these prove.** They do not prove a poll cycle works, because that needs the mailbox and
would cost an OpenAI call. The claim here is that configuration and imports are unchanged, which is
the class of thing this change could have broken.

## 8. The Linux sandbox, and whether the check closes the fourth trap

**Yes, I agree, and I read the trap in `CLAUDE.md` before answering.**

Verified rather than assumed, though by proxy rather than on Linux: this session runs on Windows, so
`pathlib.PurePosixPath` was used, which implements POSIX semantics on any host. Against the values
actually in `.env`:

```
PRACTICE_ROOT
   as Windows path: is_absolute = True
   as POSIX path  : is_absolute = False | parts = ('C:\\Users\\PDK7\\OneDrive - Intellitax Accounting Limited',)
INTELLIBILLS_UNSYNCED_ROOT
   as Windows path: is_absolute = True
   as POSIX path  : is_absolute = False | parts = ('C:\\Intellibills',)
```

**The whole string is one relative path component under POSIX**, which is precisely the mechanism the
trap describes, and `is_absolute()` is `False`, so `_required_root` raises. The sandbox reads the same
`.env` through `load_dotenv()`, so it gets the same values and the same refusal. **The trap changes
from a rule somebody has to have read into a `RuntimeError`.**

**Two qualifications, because the trap is about more than the two roots.**

- The check fires **before** the `mkdir` block but **after** `load_dotenv()` and the module's own
  imports, which is soon enough: the five `mkdir` calls are the only import-time filesystem writes in
  `config.py`, checked by grepping the module for `mkdir`, `open`, `write` and `touch`.
- **`python3 -m py_compile config.py` remains the right check in the sandbox.** It is still cheaper
  and it still proves more, because it never executes the module at all. The refusal is a floor, not
  a replacement for the habit.

**The trap's wording will need amending and I have not touched `CLAUDE.md`**, per the brief.

## 9. Flag, do not fix

**1. The two variable names are asymmetric, and yes, it is worth raising.** `PRACTICE_ROOT` has no
prefix, `INTELLIBILLS_UNSYNCED_ROOT` does. **The change makes this worse rather than neutral**, for a
reason that did not exist yesterday: until today neither variable was in `.env`, so nobody typed
either name; from today both are required, so the first thing anybody does on a new machine is type
both, from memory, into a file where a wrong key produces a refusal naming the *right* key. Renaming
an environment variable is Paul's decision and is not in this brief.

**2. `app.py:147` now points at the wrong line, and my change put it there.** A docstring in
`_write_pipeline_status()` says a person can reconcile the field "against `.env` or against
`config.py:33`". Line 33 is now a comment, and `PRACTICE_ROOT` is at `config.py:68`. **The sharper
point is that the value is no longer in `config.py` at all**, so the sentence should probably name
`.env` alone. **Small and obviously right, and I have not done it**: it is in a file the brief put out
of scope. Say the word and it is a one-line edit.

**3. `import_vendor_csv.py:75` holds the practice root as a literal**, inside the usage example it
prints when run with no arguments. Same class as the defaults this brief removed and much smaller,
because it is help text rather than a path the code builds anything from, but it is the only
occurrence of that string left in any Python file in the repository, checked by grep excluding
`.history\`.

**4. Four documents cite `config.py` line numbers that this change moved.** Listed for the consultant
session rather than edited, since they are not mine:
`2026-07-25_CONSOLE_DESIGN.md` amendment 241 and sub-step 10e.14, `2026-08-20_LIST_settings_firm_and_client.md`
row F17, and the two reports of 2026-09-05, which are history and should probably stay as written.
The moves are `PRACTICE_ROOT` 33 to 68, `UNSYNCED_ROOT` 37 to 69, `CLIENTS_ROOT` 42 to 74,
`RESOLUTIONS_DIR` 96 to 128, and the `mkdir` block 129 to 161.

**5. Not raised as new, per the brief: `SMTP_HOST`, `SMTP_PORT` and `SMTP_USERNAME`** still carry live
`lastingimpact.co.uk` defaults, now at `config.py:150-152`.

## 10. My own mistakes in this session

- **The first attempt to write `tests/test_required_roots.py` through a shell heredoc failed with an
  unterminated quote and wrote no file.** Caught by checking `ls` and `git status` rather than by
  assuming the write had happened, which is the only reason the following pytest run was not reported
  as a mysterious pass.
- **The first mutation harness reported two mutations as catching nothing**, and both were artefacts:
  one of a mutation that broke collection, one of a parser that ignored `SUBFAILED`. Both are written
  up in section 6 rather than quietly corrected.
- **I refreshed a line reference in `tests/live_paths.py` to `:76-128` and it should have been
  `:95-128`.** Line 76 is a comment; `FILES_DIR`, the first of the derived paths, is at 95. Found by
  grepping for the constant instead of trusting the arithmetic, and fixed.

## 11. Files changed

| File | Change |
| --- | --- |
| `.env` | Two keys appended, values parsed out of `config.py`. Gitignored, not committed |
| `.env.example` | The same two keys as placeholders, marked required |
| `config.py` | `_required_root()` and two calls replace two defaulted reads; both literals deleted; one superseded comment struck through |
| `tests/live_paths.py` | `_root_variable()` replaces `_root_declaration()`; `_live_root()` captures the live roots and refuses a bad one; three `config.py:N` references refreshed |
| `tests/test_conftest_redirect.py` | One test rewritten, the one that compared the capture against the deleted defaults |
| `tests/test_required_roots.py` | New. 9 tests, 8 subtests |

## 12. Confidence

**High that `config.py` refuses correctly, and what that rests on is running it**: six subprocess
imports covering unset, empty and relative for each variable, each message read in full, plus four
mutations that all go red.

**High that Paul's pipeline is unaffected**, resting on the eighteen constants comparing identical
across the change and on `import app` succeeding with every real path present on disk. **It does not
extend to a poll cycle**, which was not run.

**High that `tests/live_paths.py` sets the environment variables before `config` is imported**,
because that is read out of the file and guarded by its own assertion, and the suite passes.

**Medium-high on the Linux sandbox claim.** The mechanism is verified and the values are the real
ones, but through `PurePosixPath` on Windows rather than by running it on Linux. If somebody wants
certainty, `python3 -c "from pathlib import Path; print(Path(...).is_absolute())"` in the sandbox
settles it in one line, and importing `config.py` there to check would be the trap all over again.
