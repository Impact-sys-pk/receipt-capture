# Claude Code report, 2026-09-14: step 10r, exports leave the repository

Brief: `PROMPT_claude_code_2026-09-12_exports_leave_the_repository.md`, written 2026-09-12 and worked
2026-09-14. Section 16 step 10r of `2026-07-25_BUILD_STATUS.md`, amendment 359 of
`2026-07-25_CONSOLE_DESIGN.md`, Paul's decision closing outstanding item 37.

Times read from the Windows clock, Europe/London. The Git Bash time zone database on this machine is
an hour out and names the zone wrongly, which is flag 8.5 of
`2026-09-14_REPORT_claude_code_implausible_year_guard.md`.

**Built. Not committed: the commit is proposed at section 9 and waits for a yes.**

---

## 1. The brief was two days old, and its decision survived

Checked before building, because four files it does not mention have moved since it was written.

| What changed since 2026-09-12 | Does it touch this decision? |
| --- | --- |
| `worker/client_copy.py` at steps 10ax and 10az | No. It writes into `Clients\` and `IntelliBooks\Delivery\` and names no export. |
| `config.py` at step 10az | No. It gained `DELIVERY_FOLDER_NAME` and `DELIVERY_LOG_SUFFIX`, two strings, neither a Path constant. |
| `worker/validation/rules.py` and `worker/resolution/service.py` at the year guard | No. Nothing there reads or writes an export. |

**What the brief got wrong is smaller than that and is at section 2: its count of the sites.**
Everything else in it held, including both `OUTPUT_DIR` lines being exactly where it says.

---

## 2. Evidence item 2: the set of sites, and the brief undercounts it

**The brief names two sites and says that if there is a third, it is the one that matters. There is a
third, and a fourth, a fifth and a sixth.**

### First sweep, and it was the wrong question

Enumerating `BinOp` nodes matching `BASE_DIR / "exports"` over the **151 tracked `.py` files**,
production and tests, `.history\` excluded by construction because it is gitignored and therefore
untracked:

```
capture_report.py                 69  config.BASE_DIR / 'exports'
export_bookkeeping.py             25  config.BASE_DIR / 'exports'
count: 2
```

**Exactly the two the brief names. That agreement was the trap.** Widening to every non-docstring
string constant equal to `exports` adds four test sites, which is what Paul's message pointed at:

```
tests/test_capture_report.py     281  'exports'
tests/test_capture_report.py     785  'exports'
tests/test_london_surfaces.py    418  'exports/'
tests/test_london_surfaces.py    418  'exports\\'
```

**And that sweep is still the wrong question, because it missed the site that actually broke.**
`tests/test_capture_report.py:836` reads `self.assertEqual(capture_report.OUTPUT_DIR.parent,
config.BASE_DIR)`. It pins the exports location exactly and contains the word `exports` nowhere.

### Second sweep, on `BASE_DIR` rather than on the word

```
capture_report.py                   69  code: config.BASE_DIR
config.py                           12  code: BASE_DIR          (the definition)
config.py                     63,64,104,105,123  code: BASE_DIR  (error messages naming .env)
config.py                       949, 963  code: BASE_DIR        (git status helper)
export_bookkeeping.py               25  code: config.BASE_DIR
tests/test_capture_report.py       836  code: config.BASE_DIR
tests/test_conftest_redirect.py     37  string: 'BASE_DIR'
tests/test_london_surfaces.py      407  string: "config.BASE_DIR / 'exports'"
tests/test_london_surfaces.py      429  string: 'config.BASE_DIR / '
tests/test_receipt_accounts.py      52  string: 'BASE_DIR'
total sites: 15
```

### The set, and what each one is

| Site | What it is | Changed? |
| --- | --- | --- |
| `capture_report.py:69` | `OUTPUT_DIR` | **Yes.** The brief's first. |
| `export_bookkeeping.py:25` | `OUTPUT_DIR` | **Yes.** The brief's second. |
| `tests/test_capture_report.py:836` | asserts `OUTPUT_DIR.parent == config.BASE_DIR` | **Yes. The third, and the one that matters.** |
| `tests/test_london_surfaces.py:407` | asserts the source text is `config.BASE_DIR / 'exports'` | **Yes.** A fourth. |
| `tests/test_london_surfaces.py:428` | asserts the source text against `capture_report.OUTPUT_DIR.name` | **Yes.** A fifth. |
| `tests/test_conftest_redirect.py:32` | asserts there are 21 config `Path` constants | **Yes.** A sixth, and it appears in neither sweep. |
| `tests/live_paths.py` prose | "twenty of the twenty-one Path constants" | **Yes.** Prose the test above polices. |
| `tests/test_capture_report.py:281` | a fixture making a temp `exports` folder and redirecting `OUTPUT_DIR` | No. Relative to its own temp root. |
| `tests/test_capture_report.py:785` | asserts the new file's path starts with `exports` | No. Relative to that same temp root. |
| `tests/test_london_surfaces.py:418` | guards against a path relative to the working directory | No. Still passes, and still worth having. |
| `config.py` x8, `test_receipt_accounts.py:52`, `test_conftest_redirect.py:37` | `BASE_DIR` for reasons unrelated to exports | No. |

**Six sites changed where the brief named two.** The two it named were right; the count was not.

### The lesson, and it is the useful part of this report

**Two sweeps agreeing is not the same as the set being closed, when both sweep the same term.**
Paul's instruction, 2026-09-14, in his own words: the brief told me to sweep for the wrong thing, his
own sweep agreed with it, and **the agreement is what made it look safe.**

The shape is worth stating flatly, because it is not the ordinary version of the enumerate-the-set
rule. That rule says a claim about a set is not verified by verifying its members, and the usual
failure is checking four things and asserting there are four. **This failure is different and more
comfortable**: two people enumerated independently, from the syntax tree, with `.history\` excluded,
and got the same answer. Everything about the method was right except the term.

**Both sweeps asked "where does the text `BASE_DIR / "exports"` appear", and the question the task
needed was "what would break if the exports folder moved".** Those are different sets and the second
contains the first. `tests/test_capture_report.py:836` is in the second and not the first: it pins
the location exactly, in one line, and it contains neither the word `exports` nor that expression.
`tests/test_conftest_redirect.py:32` is further out still, and it names nothing about exports at all,
because it breaks on any new config constant whatever the constant is for.

**What would have caught it first time is asking what the change does rather than what the change
looks like.** The change moves a folder out of `BASE_DIR`, so the sweep is on `BASE_DIR`, not on
`exports`; and it adds a config constant, so the question "what counts the config constants" has to be
asked separately and is answered by neither sweep. **Independent agreement is evidence about the
sweeping, not about the term**, and where two sweeps share a term they share its blind spot exactly.

**The suite found the same set independently**, which is the check on the enumeration rather than a
repeat of it: after changing only the three production lines, the run failed in exactly four tests,
and those four are rows three to six above. **Nothing was found by the suite that the tree sweep had
missed, and nothing the tree sweep flagged turned out to be a false alarm.**

---

## 3. Evidence item 1: the constant, read back out of the file

```
config.py:212   EXPORTS_DIR = INTELLIBILLS_ROOT / "Exports"
config.py:910   EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
```

**Where it resolves, chained out of the files rather than imported**, per the brief's instruction and
`CLAUDE.md`'s fourth trap:

```
config.py:127   PRACTICE_ROOT     = _required_root("INTELLIBILLS_PRACTICE_ROOT")
config.py:132   INTELLIBILLS_ROOT = PRACTICE_ROOT / "Intellibills"
.env            INTELLIBILLS_PRACTICE_ROOT=C:\Users\PDK7\OneDrive - Intellitax Accounting Limited
```

so `EXPORTS_DIR` is
`C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills\Exports`.

**That folder already exists and already holds what amendment 359 says it holds**, listed read-only:
`2026-08-18_EXPORT_categorisations_client_vendors.csv` and
`2026-08-18_EXPORT_legacy_codes_summary.csv`, both dated 18 August.

**No `import config` was run at any point.** The chain above is three greps and one `.env` line, and
that `.env` line was extracted by naming the variable rather than by printing or masking the file,
which is the third trap's own lesson: a mask is not an allowlist.

### Why `EXPORTS_DIR`

The brief left the name to me and asked for the reasoning.

**I tested a rule and it is false, so it is not the reason.** I supposed `_ROOT` meant a folder the
code navigates into and `_DIR` a flat one. Checked against the call sites: `FILES_DIR` is the deepest
of all, `client_id\year\month`, and `BACKUPS_ROOT` is a flat `glob("receipts-*.db")`. **The suffixes
carry no consistent distinction and choosing on that basis would have been inventing a rule to
justify a choice.**

**The reason that survives is the nearest neighbours by what the folder holds.** A folder of
generated files this product writes for a person is `LOGS_DIR`, `CHARTS_DIR`, `RESOLUTIONS_DIR` and
`ATTACHED_DIR`, and all four are `_DIR`. `EXPORTS_DIR` sits with them. It also matches the name the
brief's own report filename assumes, `..._exports_dir.md`, which is corroboration rather than a
reason.

---

## 4. Evidence item 3: the test that holds the mkdir ordering

**`tests/test_client_top_folder.py::NoDefaultSurvivesInTheSourceTest::test_every_refusal_sits_above_every_mkdir`.**
Run on its own after the change: **1 passed in 0.12s.**

**The name in `config.py`'s own comment is one level short of the node id.** The comment says
`tests/test_client_top_folder.py::test_every_refusal_sits_above_every_mkdir` and omits the class, so
pytest answers `ERROR: not found`. Minor, and flagged at 8.3 rather than fixed.

**Passing is not the same as protecting this change, so it was mutated.** Mutation 3 at section 6
moves the new `mkdir` from the block at the foot of the module up to the line under the constant's
definition, which puts it above nine refusals, at `config.py:297` to `:860`. That is a real ordering
break rather than a cosmetic one, and the test catches it.

---

## 5. What changed

### `config.py`

`EXPORTS_DIR = INTELLIBILLS_ROOT / "Exports"` beside the other constants derived from that root, and
one line in the mkdir block at the foot of the module, below every refusal. The constant's comment
carries amendment 359's three reasons: why the practice root, why sync is not an objection, and what
the change must not lose.

### `export_bookkeeping.py` and `capture_report.py`

Both `OUTPUT_DIR = config.EXPORTS_DIR`. **Both keep the pin and both keep their comments, amended.**
`export_bookkeeping.py` keeps its own `mkdir` too: `config.py` now creates the folder at import,
which covers a machine that has never run an export, while the script's own call covers the folder
being removed between then and now.

**`capture_report.py`'s comment argued against this change and is struck rather than deleted**, per
the house convention. It read "**Deliberately not under any config root**", then ruled out `Clients\`
by 18.2b, `Intellibills\Documents\` by 18.2 and the unsynced root by 18.2a. **Those three exclusions
still hold and none of them argued for the repository**: they ruled out three roots and the
repository was what was left. 18.2's third rule decides it, which is the reasoning now in its place.

### Three tests and one prose file

Detailed at section 7, because two of them are rewrites rather than edits.

---

## 6. Evidence

### 6.1 The suite, measured rather than carried

| Point | Result |
| --- | --- |
| Baseline, measured at `94c5b00` at the start of this work | **1458 passed, 1 skipped, 1113 subtests** |
| After the change, at `1054d21` | **1458 passed, 1 skipped, 1116 subtests** |

**No new test, and +3 subtests. All three are accounted for and only two of them are mine.**

| Source | Subtests |
| --- | --- |
| `tests/test_conftest_redirect.py`, which subTests every config `Path` constant: 21 to 22 | +1 |
| `tests/test_receipt_accounts.py`, which does the same but skips `BASE_DIR` before the subTest: 20 to 21 | +1 |
| **Not mine.** `tests/test_implausible_year.py` subTests every tracked production file, and the consultant session's `1054d21` added `check_build_status.py` to the repository root: 57 files to 58, so 56 subtests to 57 | +1 |
| **Total** | **+3** |

**The third one cost a detour and is worth recording.** The count moved from 1115 to 1116 between two
of my own runs with no subTest loop changed, and I chased it rather than shrugging, which is
`CLAUDE.md`'s rule about the regression found only because a total moved by nine. **My first two
hypotheses were wrong**: I supposed my own report file in the repository root, tested it by moving
the file out and re-running, and the count did not move; I then supposed
`test_category_hold.py`'s `REPO_ROOT.glob("*.py")` sweep, read it, and it subTests per call site
rather than per file. **The answer was a guard I wrote earlier the same day**, in a file this step
does not touch, reacting correctly to a new production file committed by the other session at 13:26.
`git ls-files "*.py"` excluding `tests/` returns 58 where it returned 57 this morning.

**The enumeration of `vars(config)` loops was done rather than assumed**, from the syntax tree: three
tests reference `vars(config)`, and exactly two of them subTest. The third,
`test_path_layout.py::test_no_unexpected_path_constant_resolves_inside_intellibooks`, uses a list
comprehension and contributes nothing, which is why the total is +2 from my change and not +3.

**HEAD moved four commits under this work**, `cd3dc9e`, `81674d3`, `1054d21` and one before them, all
the consultant session's. Only one touched code: `check_build_status.py`, a new root script. The
baseline above predates it, which is why the reconciliation has to name it.

### 6.2 Mutations

Seven. Each anchored on a string whose `str.count()` was asserted to be exactly 1, each printing its
own unified diff, every file restored from original bytes in a `finally` and verified byte-exact.
Mutation 3 is one mutation expressed as two anchored edits, both counted.

| # | Mutation | Suite | Caught by |
| --- | --- | --- | --- |
| 1 | the constant goes back to the repository anchor | 2 failed | `test_conftest_redirect.py::RedirectIsInForceTest`, `test_receipt_accounts.py::ShippedNotPublishedTest` |
| 2 | the constant leaves the import-time mkdir block | **1458 passed** | **NOTHING** |
| 3 | the mkdir moves above nine refusals | 4 failed | `test_client_top_folder.py::NoDefaultSurvivesInTheSourceTest`, `test_client_top_folder.py::RefusalTest`, `test_publish_destination.py::RefusedTest`, `test_stage4_client_copy.py::TheTriggerIsAFirmSettingTest` |
| 4 | `capture_report.py` goes back to the repository anchor | 2 failed | `test_capture_report.py::ReadsOnlyTest`, `test_london_surfaces.py::ExportPathTest` |
| 5 | `export_bookkeeping.py` goes back to the repository anchor | 2 failed | `test_london_surfaces.py::ExportPathTest` |
| 6 | the two scripts part company: `export_bookkeeping.py` to `BACKUPS_ROOT` | 2 failed | `test_london_surfaces.py::ExportPathTest` |
| 7 | both named `Exports`, in different roots | 2 failed | `test_london_surfaces.py::ExportPathTest`, both of its tests |

**Mutation 3 is the one the brief asked for.** Moving the new `mkdir` from the block at the foot of
the module to the line under the constant's definition puts it above nine refusals at `config.py:297`
to `:860`, and `test_every_refusal_sits_above_every_mkdir` catches it. Three other tests catch it too,
because a refused installation now makes a folder before it refuses.

**Mutation 1 is caught by neither export test, and that is correct rather than a hole.** Changing the
constant's own definition moves both scripts together, so the tests asserting that they agree still
agree. What catches it is the pair of tests asserting every config `Path` lands under a temp root,
which is what "it left the practice root" actually means.

**Mutation 2 was caught by nothing. That is a real gap and it is flag 8.4.**

### 6.3 Mutation 7, which is why one test was rewritten rather than edited

**Mutation 6 does not justify the rewrite and I nearly claimed it did.** Pointing
`export_bookkeeping.py` at `config.BACKUPS_ROOT` is caught by the old form too, because the source
text stops matching. **The case the old form misses is both scripts sharing a folder NAME under
different roots**, so mutation 7 builds exactly that: `capture_report.py` stays at
`config.EXPORTS_DIR`, whose folder is named `Exports`, and `export_bookkeeping.py` becomes
`config.BASE_DIR / "Exports"`.

The old assertion was reconstructed and evaluated against the mutated source rather than argued about:

```
  source text        : "config.BASE_DIR / 'Exports'"
  OLD assertion's rhs: "config.BASE_DIR / 'Exports'"
  OLD TEST WOULD: PASS
  RESULT: 2 failed  ->  test_it_writes_where_capture_report_writes
                        test_the_output_folder_is_derived_from_a_config_constant
```

**Stated precisely, because the class as a whole was not blind.** Its sibling
`test_the_output_folder_is_derived_from_config_base_dir` would have failed this mutation on the
capital `E`, since it pinned the lower-case `'exports'`. **What was wrong is that the test whose
stated job is "the two write to the same place" was doing that job by a coincidence of naming rather
than by comparing the two folders.** It now compares them.

**Mutation 7 also found a weakness in my replacement, which I fixed before running it.** The first
version asserted `expression.count(".") == 1`, and `"config.BASE_DIR / 'Exports'"` has exactly one
dot, so the guard passed and `getattr(config, "BASE_DIR / 'Exports'")` raised `AttributeError`. A
mutation caught by a crash rather than by an assertion is caught, but the sentence explaining what is
wrong never prints. It is now `assertRegex(expression, r"^config\.[A-Z][A-Z0-9_]*$")`.

---

## 7. The four test changes, two of them rewrites

**`tests/test_conftest_redirect.py`, the count.** 21 to 22, because `EXPORTS_DIR` is a `Path` in
`vars(config)`. One line and a comment naming the step.

**`tests/live_paths.py`, the prose the count polices.** "twenty of the twenty-one" to "twenty-one of
the twenty-two", with the superseded figures struck beside the new one as the file already does for
its two earlier moves. **A paragraph added saying `EXPORTS_DIR` needed no entry anywhere else, and
that this is the arrangement working rather than luck**: it derives from `INTELLIBILLS_ROOT`, which
derives from a root this file redirects in the environment before `config` is imported, so it lands
in a temp folder without any fixture naming it.

**This is worth stating plainly because step 10az reached the opposite conclusion five days ago and
both are right.** `config.py`'s `DELIVERY_FOLDER_NAME` comment says a Path constant would need adding
by hand to three lists and so used strings instead. Of those three, `test_path_layout.py`'s `ALLOWED`
set is specific to constants inside `IntelliBooks\`, which `Intellibills\Exports\` is not; and
`resolution_fixtures.py`'s `TempEnvironment` pins a subset by hand for fixtures that need it, and no
fixture drives an export script. **Only the count applied here, and the count is asserted rather than
remembered.**

**`tests/test_capture_report.py::ReadsOnlyTest::test_the_output_folder_is_not_the_client_folder`.**
The second assertion moved from `OUTPUT_DIR.parent == config.BASE_DIR` to
`OUTPUT_DIR == config.EXPORTS_DIR`. **The subject did not move**: it is that a capture report is not
written into a client's folder, which is the first assertion. The second says the folder is the one
constant that owns it rather than a path composed in the script, which is the same claim about a
different constant. Recorded in the docstring, with a note that **step 10ai will move this again**
into the client's own folder, and that when it does the first assertion is the one to argue with
rather than edit.

**`tests/test_london_surfaces.py::ExportPathTest`, two tests.**

`test_the_output_folder_is_derived_from_config_base_dir` is renamed
`test_the_output_folder_is_derived_from_a_config_constant` and asserts `config.EXPORTS_DIR`. A
straight edit: it reads the assignment's source text off the syntax tree and that text changed.

`test_it_writes_where_capture_report_writes` is **rewritten, and the new one is stronger than what it
replaces.** It read:

```python
self.assertEqual(assignments["OUTPUT_DIR"],
                 f"config.BASE_DIR / {str(capture_report.OUTPUT_DIR.name)!r}")
```

**That compared one script's source text against the other's folder NAME**, so it agreed whenever both
ended in the same word. It would have gone on passing had one script moved to a different root while
keeping the name `exports`, which is the precise failure this step exists to remove. It now resolves
the name against `config` and compares the two folders themselves:

```python
expression = self._assignments()["OUTPUT_DIR"]
self.assertTrue(expression.startswith("config.") and expression.count(".") == 1, ...)
resolved = getattr(config, expression.split(".", 1)[1])
self.assertEqual(resolved, capture_report.OUTPUT_DIR)
```

It fails if the two part company for any reason, it still fails if the pin is replaced by a composed
path, and it survives the constant being renamed, which the old form did not. **Mutation 6 at section
6 is the case the old test would have missed**, and it is caught.

---

## 8. Flags, each with the obvious fix

**Disposition, added 2026-09-14 after Paul read them.** **8.4 is taken and is a separate brief**,
a test asserting which folders `config.py`'s mkdir block creates; it is not in this commit and he
is sending it. **8.1, 8.2, 8.3 and 8.5 are accepted as they stand**: `.gitignore` left alone for
the reason given, the ordering test's name in `config.py`'s comment flagged rather than fixed, and
the seven-file commit right because splitting the four tests out would leave it red.

### 8.1 `.gitignore`, which the brief asked me to flag and not change

`.gitignore:14-18` lists `exports/` with a comment saying it is generated output and that it trips
`config.check_git_status_on_startup()`'s clean-tree warning.

**Established rather than assumed**, which is amendment 359's own claim re-checked: `git ls-files
logs exports` returns nothing, so neither folder holds a tracked file. `exports\` currently holds one
file, `bookkeeping_export.csv`, dated 2026-09-04. `logs\` is empty and has been since 2026-08-02.

**The obvious fix is to delete the `exports/` entry, and the obvious fix is wrong today.** Nothing
writes there after this commit, so the entry describes a folder the repository will not have. But the
folder and its one file are still on disk until the consultant session moves them, and **removing the
ignore entry before the folder goes would make that file untracked and trip the very warning the
entry exists to prevent.**

**So: leave it, and delete it in the same change that removes the folder**, which is the consultant
session's and is already scheduled. `logs/` at line 10 is the same case one step further on, already
empty. **Neither is mine and neither is in this commit.**

The comment at lines 14 to 17 covers `exports/` and `Claude outputs/` together, so deleting one entry
means rewriting the comment rather than deleting it.

### 8.2 `capture_report.py` will move again at step 10ai, and this commit is not wasted work

Step 10ai, amendment 388, moves the per-client capture report into the client's own folder and leaves
`export_bookkeeping.py` where 10r puts it. **Flagged so nobody reads the two steps as contradicting
each other.** They do not: 10r takes both out of the repository, which is the fault item 37 named,
and 10ai then separates the one-client report from the whole-database export. `EXPORTS_DIR` survives
10ai as `export_bookkeeping.py`'s anchor.

**No fix, and nothing to do.** It is here because a reader arriving at 10ai should not think 10r was
done twice.

### 8.3 `config.py`'s comment names the ordering test without its class

The mkdir block's comment says
`tests/test_client_top_folder.py::test_every_refusal_sits_above_every_mkdir`. The node id is
`tests/test_client_top_folder.py::NoDefaultSurvivesInTheSourceTest::test_every_refusal_sits_above_every_mkdir`,
and pytest answers `ERROR: not found` to the shorter form, which is how I found it.

**Fix: add the class name to that comment.** One line. **Not done**: the brief scopes my change in
`config.py` to the constant and the mkdir line, and this is a different comment about a different
block.

### 8.4 Nothing in the suite holds the membership of `config.py`'s mkdir block

**Mutation 2 removed `EXPORTS_DIR.mkdir(...)` from the block and the whole suite passed:
1458 passed, 1 skipped, 1116 subtests, no failure of any kind.**

**The gap is not mine and not specific to `EXPORTS_DIR`.** Established from the code rather than
inferred: one test parses that block,
`test_client_top_folder.py::NoDefaultSurvivesInTheSourceTest::test_every_refusal_sits_above_every_mkdir`.
It collects every module-level `mkdir` call into a dict, then asserts two things: that the dict is
non-empty, and that `min(mkdirs) > max(refusals)`. **It asserts ordering and non-emptiness, never
membership**, so removing any one of the six lines leaves it green. `INTELLIBOOKS_PUBLISH_DIR`,
`FILES_DIR`, `BACKUPS_ROOT`, `LOGS_DIR` and `DB_PATH.parent` are in exactly the same position.

**Nor is anything else watching.** A grep of `tests\` for `mkdir` returns fixtures creating their own
folders and nothing asserting what `config.py` creates.

**The obvious fix: a sibling test in the same class asserting the block's membership as a set**, in
the shape the ordering test already uses, since it collects the names already. Roughly ten lines, and
it would fail loudly when a seventh folder is added without being considered.

**Not built, because which folders must exist at import is a design decision rather than an
implementation detail**, and this brief scopes `config.py` to the constant and the one mkdir line.
Say the word and it is a short follow-up.

### 8.5 The brief's "one commit" and the file count

The brief says one commit and names three files to change. **This commit touches seven**, the extra
four being the three tests and one prose file that pin the old value. They cannot be split out: the
suite is red between the production change and the test change, so a commit containing only one half
would not build. Stated rather than assumed to be obvious.

---

## 9. The commit, proposed and not run

The brief is not an `AUTOMATIC task`, so nothing is staged, committed or pushed.

```
feat(config): exports leave the repository for Intellibills\Exports\

Step 10r, amendment 359, Paul's decision of 2026-09-12 closing outstanding
item 37. config.EXPORTS_DIR is INTELLIBILLS_ROOT / "Exports", and
export_bookkeeping.py and capture_report.py both point at it instead of
config.BASE_DIR / "exports". The repository held an exports\ while the
practice root already held Intellibills\Exports\ with two CSVs in it: two
folders for one thing, which is the fault item 37 named.

Why the practice root: 18.2's third rule is that each store has one owner,
and an export is an Intellibills output for a person rather than source.
Why sync is not an objection: 18.2a's test is whether a file is held open,
and an export is written once and closed. What the change does not lose:
both scripts still pin OUTPUT_DIR to a constant rather than writing a
relative path, and each still says why in its own comment. That reason is
about having an anchor, not about which anchor.

The constant joins the import-time mkdir block for
INTELLIBOOKS_PUBLISH_DIR's reason, below every refusal in the module, which
tests/test_client_top_folder.py's test_every_refusal_sits_above_every_mkdir
holds and a mutation confirms.

Four sites pinned the old value where the brief named two. The third is
test_capture_report.py's assertion that OUTPUT_DIR.parent is config.BASE_DIR,
which contains the word "exports" nowhere. test_london_surfaces.py's
test_it_writes_where_capture_report_writes is rewritten rather than edited:
it compared one script's source text against the other's folder NAME, so it
would have passed with the two in different roots sharing a name.

No file is moved on disk and .gitignore is unchanged, both deliberately.

Files: config.py, capture_report.py, export_bookkeeping.py,
tests/test_capture_report.py, tests/test_london_surfaces.py,
tests/test_conftest_redirect.py, tests/live_paths.py
Suggested branch: feat/console-phase0 (current)

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

**This change adds no file**, so the extra after-commit run `CLAUDE.md` requires for an added file
does not apply. Saying so rather than skipping it silently, which the brief asks for. The two
`git ls-files` source guards sweep production files only and every file here was already tracked, so
a commit cannot change what they see.

Push is a separate yes.

---

## 10. My own mistakes in this session, disclosed

**Seven.**

1. **My first enumeration answered the wrong question and agreed with the brief, which is the worst
   way to be wrong.** I swept for `BASE_DIR / "exports"` as a `BinOp`, got exactly the two sites the
   brief names, and had I stopped there I would have reported "the brief's two are the whole set" with
   a syntax-tree sweep behind it. **The site that mattered,
   `tests/test_capture_report.py:836`, contains neither the word `exports` nor that expression.** It
   took a third sweep, on `BASE_DIR` alone including string constants, to find it. `CLAUDE.md`'s rule
   is that a claim about a set is not verified by verifying its members; the sharper version this
   taught me is that **a sweep agreeing with the claim it was meant to test is not corroboration if
   the sweep asks the claim's own question.**

2. **My second sweep also missed a site, and the suite found it.**
   `tests/test_conftest_redirect.py`'s count of 21 config `Path` constants appears in no sweep for
   `exports` or `BASE_DIR`, because it is a property of adding any constant at all. I found it by
   reading that file for a different reason before running anything, so it cost nothing, but I did
   not find it by enumeration and the report should not imply I did.

3. **I invented a naming rule, tested it, and it was false.** I supposed `_ROOT` meant a folder the
   code navigates into and `_DIR` a flat one, which would have made `EXPORTS_DIR` follow from a
   principle. `FILES_DIR` is the deepest constant in the module and `BACKUPS_ROOT` the flattest.
   Disclosed because the name is right and the reason I first had for it was not, and section 3
   carries the reason that survived.

4. **I broke an `Edit` on `tests/live_paths.py` by reconstructing a line from memory**, dropping a
   `**` and matching nothing. Harmless, and it is the same habit as mistake 1: I quoted the file from
   what I thought it said instead of from what it says. Redone with anchored byte replacements, each
   asserted to occur exactly once.

5. **I wrote into the report that mutation 6 was "the case the old test would have missed", and it is
   not.** Pointing `export_bookkeeping.py` at `BACKUPS_ROOT` changes its source text, so the form I
   replaced would have caught it too. I had written the sentence before running the mutation and it
   read as evidence for the rewrite when it was not. **Caught by checking the claim against what the
   old assertion would actually have compared**, which is section 6.3, and corrected by building
   mutation 7, which genuinely separates the two. **The rewrite was still right; my justification for
   it was not, and a justification that does not hold is worth the same as a wrong answer.**

6. **My replacement test had a hole that mutation 7 found.** It guarded with
   `expression.count(".") == 1`, and `"config.BASE_DIR / 'Exports'"` has exactly one dot, so the
   guard passed and the `getattr` beneath it raised `AttributeError` instead of the assertion
   printing its sentence. Fixed to `assertRegex(expression, r"^config\.[A-Z][A-Z0-9_]*$")` before the
   mutation was run. **A test written in the same hour as the mutation that probes it is the only
   reason this was found**, which is the argument for mutating your own new tests rather than only
   the code.

7. **Two wrong hypotheses about the moving subtest count**, both tested and both discarded: my own
   report file in the repository root, and `test_category_hold.py`'s root `*.py` sweep. Neither cost
   anything but the second was answerable by reading the test, which I should have done before
   running the suite with the file moved out.

---

## 11. Confidence

**High that the set of sites is now complete**, because it was reached three ways that agree: a
syntax-tree sweep on `BASE_DIR` across all 151 tracked `.py` files, a reading of the two test files
those sweeps pointed at, and a full suite run against the production change alone, which failed in
exactly the four tests the sweeps had already named and in nothing else.

**High on where the constant resolves**, because it was chained out of `config.py` and `.env` by
grep, with no `import config` at any point, and the destination folder was then listed read-only and
holds the two CSVs amendment 359 says it holds.

**High that the mkdir ordering is protected rather than merely passing**, because the guard was run
by its full node id and then mutated: moving the new `mkdir` above nine refusals is caught.

**High that nothing moved on disk.** `exports\bookkeeping_export.csv` is where it was, `.gitignore`
is unchanged, and no file was created outside the repository by this work.

**High on flag 8.1's mechanism and moderate on its timing recommendation**, and the two are worth
separating. **The mechanism is read rather than assumed**: `check_git_status_on_startup()` shells out
to `git status --porcelain` and warns on any non-empty output, and `--porcelain` lists an untracked
file as `?? path`, so an unignored `exports\bookkeeping_export.csv` would trip it. **What I did not
do is start the pipeline and watch it warn**, so the recommendation to delete the entry only in the
same change that removes the folder rests on reading the function, not on observing it.
