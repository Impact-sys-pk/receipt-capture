# Report: the pipeline reads the client top folder from the firm record

**Written 2026-09-07, 17:01 BST (16:01 UTC), by the implementation session in Claude Code.**
**Branch `feat/console-phase0`. Sub-step 10e.14, piece three of four.**
**Brief: `PROMPT_claude_code_2026-09-07_client_top_folder.md`, now in `archive\`.**

**Times in this report are Windows local, which is BST today.** The consultant session's shell
reports UTC, so an entry here will read an hour later than the same instant reported there. That is
the rule in `CLAUDE.md` under "The standard of evidence", applied rather than discovered.

---

## 1. What landed

**Two commits, both on `feat/console-phase0`, neither pushed.**

| Commit | What |
|---|---|
| `7b96a35` | `feat(config): the client top folder comes off the firm record` |
| `13e1c6a` | `test(config): a firm that is not FIRM001 gets its own client top folder` |

`config.py` no longer composes the client top folder. `CLIENTS_ROOT` is the `client_top_folder`
field on the single firm record in `Intellibills\firms.json`, read by a new `_client_top_folder()`,
with no default and no fallback to the old composition.

**Verified against Paul's live firm record itself rather than against the brief's quotation of it.** Read at 16:57
BST today:

```
composed today : C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Clients
firm record    : C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Clients
same folder    : True
exists on disk : True
```

**So there is no behaviour change on his machine**, which is what the brief said the deliverable was
not. What changed is that the word `Clients` is out of the pipeline.

**The suite: 579 passed, 358 subtests before; 600 passed, 358 subtests after.** Both figures are the
last line of `.\.venv\Scripts\python.exe -m pytest -q`, the first run at 16:12 BST on the tree as
handed over and the second at 16:47 BST. **The before figure is the brief's figure exactly.** The
21 new tests are 16 in `tests\test_client_top_folder.py` and 5 in `tests\test_path_layout.py`. No
subtest was added or lost.

---

## 2. The route taken on section 4, and what the test support now does

**The brief's route was taken, with one addition it did not anticipate.** The refusal is at import
and no test was loosened to allow it.

### What `tests\live_paths.py` now does

It writes one minimal firm record into the temp practice root before `config` is imported, through a
new `write_firm_record()`. Without it the suite does not run at all: the first full run after the
`config.py` change gave **50 errors during collection**, every one of them
`RuntimeError: ...\practice\Intellibills\firms.json names no firm`.

**The stored folder is deliberately not called `Clients`.** It is
`TEMP_CLIENT_TOP_FOLDER = TEMP_PRACTICE_ROOT / "Client Folders"`. Naming it `Clients` would have
made a return to composing the path invisible to behaviour, leaving only the source-level guards to
catch it. **Mutation 6 below is that exact experiment and it proves the point.** It also means the
whole suite now runs against a client top folder called something else, which is the deliverable
demonstrated rather than asserted.

**Two literals are duplicated in `live_paths.py`**, `Intellibills` and `firms.json`, because that
file may not import `config` to ask. Not extended to source-reading like `_root_variable()`, and the
reason is in the docstring: `tests\test_path_layout.py` already asserts both against the two roots,
and getting either wrong here makes `config` refuse and every test error. **The failure mode is loud rather than silent**, which is the test this project uses for whether a duplicate is tolerable.

**The folder itself is not created.** `config` does not create it and neither does the test support.
A suite that pre-made it could not catch filing failing to.

### What the docstring now says

The brief required this and it is done. Under "What it does not do", the old line is struck through
rather than deleted:

> **It redirects paths, and it writes the one firm record `config` now requires.**
> ~~It redirects paths and nothing else.~~ **Corrected 2026-09-07, and the docstring changed with the
> behaviour rather than after it.** `CLIENTS_BY_ID`, `CLIENTS`, `PREFER_DAYFIRST`,
> `EXTRACTION_ENGINE`, `DEFAULT_FIRM_ID`, `_CLIENTS_MTIME` and `get_pipeline_version` are still each
> test's own business [...]
>
> **`FIRMS` has left that list.** It was `{}` under pytest and always had been, and it is now the one
> record written below.

A new section, "It also writes one firm record, and that is new on 2026-09-07", carries the reasoning
and the 50 collection errors.

### The addition the brief did not anticipate

**Two more files needed the same treatment, and finding them is the part worth reading.**
`tests\test_required_roots.py` and `tests\test_required_smtp.py` each import `config` in a
**subprocess** against a bare temp practice root, and each has a control test that expects the import
to succeed. Those two are outside `conftest.py`'s reach entirely, so `live_paths.py`'s record does
not help them. Both went red:

```
FAILED tests/test_required_roots.py::RefusalTest::test_a_good_pair_imports
FAILED tests/test_required_smtp.py::RefusalTest::test_a_good_set_imports_and_the_port_is_an_int
2 failed, 592 passed, 358 subtests passed
```

Both now call `live_paths.write_firm_record()`, so there is one writer of that record and not three.
**They are handled differently and the difference is deliberate:**

- In `test_required_smtp.py` the call goes inside its `import_config()` helper, so every child gets a
  record. That is not only convenience: without it, `test_each_of_the_four_is_required` would assert
  `RuntimeError` and pass on the **wrong** exception, which is a check that has stopped checking its
  subject.
- In `test_required_roots.py` the call goes inside the one control test and **not** in the helper,
  because `ChecksRunBeforeTheFoldersAreMadeTest` asserts that the temp directory stays empty when a
  root is refused, and writing the record would create `practice\` on every call and break a test
  that means something. The comment in the file says so.

**No test was made to pass by loosening it.** `test_every_config_path_constant_is_under_a_temp_root`
still asserts exactly 18 constants and still requires every one but `BASE_DIR` under a temp root;
`CLIENTS_ROOT` is still one of the 18 and still satisfies it.

---

## 3. My own enumeration of `CLIENTS_ROOT` and of the literal `"Clients"`

**The set was enumerated before it was described.** All `.py` files were found by walking the
repository with `find`, excluding `.venv\`, `.history\` and `.git\`, and the list was diffed against
`git ls-files "*.py"`: **107 files on disk, 107 tracked, no untracked Python file.** `.history\` was
excluded, per the fifth trap.

**51 are not under `tests\`; 56 are.** The brief said 41 production files and did not say what it
counted. **41 reconciles exactly**: 51 minus the 9 package `__init__.py` files minus
`docs\specs\categorisation_engine.py`. Neither count changes any conclusion.

### `CLIENTS_ROOT`, before the change, all 107 files, printed whole

**74 matching lines and 84 occurrences, across 22 files.** Counted programmatically against
`HEAD~2` rather than added up by eye: see mistake 5 in section 8, where adding it up by eye is what I did
first and got wrong. **Production, 3 lines and 3 occurrences, which is the brief's figure exactly:**

```
./app.py:117:    This used to walk CLIENTS_ROOT.rglob("Review/*") and count every file, so it
./config.py:117:CLIENTS_ROOT = PRACTICE_ROOT / "Clients"
./worker/filing.py:65:    return config.CLIENTS_ROOT / client_folder_name / config.CLIENT_INTELLIBOOKS_FOLDER_NAME
```

**`tests\`, which the brief excluded and told me to search myself: 71 matching lines and 81
occurrences, across 19 files.** Every line number is printed; where a line carries the name twice it
appears once here.

```
./tests/resolution_fixtures.py:39, :67, :68
./tests/test_already_filed_guard.py:49, :103
./tests/test_auto_retry_cap.py:90, :96, :151, :164, :170, :209
./tests/test_auto_retry_no_loop.py:110, :122, :179
./tests/test_capture_inbox_cleanup.py:38, :43, :95, :109, :114, :158
./tests/test_embedded_image_pipeline_version.py:64, :83, :84, :87
./tests/test_extraction_details.py:56, :70, :71
./tests/test_failure_path_engine.py:52, :71, :72, :75
./tests/test_logs_isolation.py:102
./tests/test_resolution_backfeed.py:277
./tests/test_resolution_service.py:49, :75, :76, :176, :352, :476
./tests/test_resolve_receipt_ordering.py:32, :39, :130, :144, :151, :248
./tests/test_resolve_receipt_zero_and_types.py:43, :57, :58
./tests/test_resume_safety.py:35, :41, :116
./tests/test_retroactive_categorise_sidecar.py:37, :50, :51, :78
./tests/test_review_pair_cleanup.py:48, :62, :63
./tests/test_sidecar_category_keys.py:50, :64, :65, :136
./tests/test_status_counts_from_db.py:41, :59, :60, :63, :151
./tests/test_step10d_routing.py:102, :171, :198, :237
```

**Every one of the 71 is a fixture pinning or restoring the constant, or a test reading it back.**
None is a definition and none needed changing: `CLIENTS_ROOT` is still a module attribute with the
same meaning, so a fixture that reassigns it still works. The suite proves that; this sentence does not.

### The literal `"Clients"`, before the change, all 107 files

**47 lines and 47 occurrences, across 27 files: 17 lines in 6 production files and 30 lines in 21
test files.** In production Python, **exactly one was a composed path** and it is the one this
sub-step removed:

```
./config.py:117:CLIENTS_ROOT = PRACTICE_ROOT / "Clients"
```

The other production occurrences were prose in docstrings and comments: `app.py` 5,
`worker/database/repository.py` 3, `worker/extraction_pipeline.py` 2, `worker/filing.py` 1,
`worker/resolution/service.py` 3, `config.py` 2 more.

In `tests\`, the literal appears 30 times. **All of them name a test's own temp folder**, in the
shape `config.CLIENTS_ROOT = self.path / "Clients"` or `temp_path / "Clients"`, plus a handful in
comments and two in raw-string filed paths. **None asserts that the pipeline composes the path**, so
none contradicts the change, and the suite confirms it.

### After the change

**No path-composing `"Clients"` remains in any production Python file.** The remaining occurrences in
`config.py` are the struck-through history at the old definition site and the reasoning in
`_client_top_folder()`'s docstring and its two refusal messages. `tests\test_client_top_folder.py`'s
`test_config_composes_no_path_from_the_word_clients` walks the AST for a `"Clients"` inside a `/`
BinOp and asserts the list is empty, so this holds by test and not by my reading.

---

## 4. Did the change stay inside `config.py`? Yes

**Nothing under `worker\` and nothing in `app.py` was touched.** `git diff --stat HEAD~2 -- worker/ app.py` is empty.

**`get_client_directory()` and `file_receipt()` are untouched, so section 18.2b's freeze holds and no
ruling was needed.** `get_client_directory()` still reads `config.CLIENTS_ROOT` and simply gets a
different value. Its two callers are `file_receipt()` at `worker/filing.py:77` and `file_statement()`
at `:102`, and grepping all 107 files for `get_client_directory` returns those two plus the
definition and nothing else, which is the brief's claim confirmed rather than repeated.

**Where `CLIENTS_ROOT` now sits inside `config.py`, and why it moved down the file.** It needs
`FIRMS_JSON` and `load_firms()`, and `load_firms()` is defined near the bottom, so the assignment is
now on the line after `FIRMS = load_firms()`. A signpost comment sits where the old definition was,
carrying the struck-through original and the reason. **This is a placement decision, and see the
first flag in section 6 for what it costs.**

---

## 5. The mutations, and which tests caught each

Each mutation was applied to a pristine copy of the committed file, the **whole** suite was run, and
the file was restored and asserted byte for byte identical. Script:
`scratchpad\mutate.py`. **No mutation was left on disk**: `git status` after the runs showed
`config.py` and `tests\live_paths.py` clean against `HEAD`.

| # | Mutation | Suite | Caught by |
|---|---|---|---|
| 1 | Put `CLIENTS_ROOT = PRACTICE_ROOT / "Clients"` back | 16 failed, 583 passed | 13 in `test_client_top_folder.py` (all of `AcceptedTest` bar one, all of `RefusalTest`, 2 source guards) and 3 in `test_path_layout.py::ClientTopFolderTest` |
| 2 | Return `PRACTICE_ROOT / "Clients"` instead of refusing | 6 failed, 593 passed | `RefusalTest`: `test_a_record_with_no_field_is_refused`, `test_an_empty_value_is_refused`, `test_a_blank_value_is_refused`, `test_a_relative_value_is_refused`, `test_the_refusal_creates_no_client_folder`; plus `test_config_composes_no_path_from_the_word_clients` |
| 3 | Drop the absoluteness check, keep the presence check | 1 failed, 598 passed | `RefusalTest::test_a_relative_value_is_refused` |
| 4 | Pick the record with `DEFAULT_FIRM_ID` instead of "exactly one" | 2 failed, 598 passed | `AcceptedTest::test_a_firm_that_is_not_FIRM001_works` and `NoDefaultSurvivesInTheSourceTest::test_the_default_firm_id_is_not_used_to_pick_the_record` |
| 5 | Take the first of several firms instead of refusing | 1 failed, 598 passed | `RefusalTest::test_two_firms_are_refused_with_a_plain_message` |
| 6 | Name the suite's stored folder `Clients` in `live_paths.py` | 2 failed, 597 passed | `ClientTopFolderTest::test_it_is_not_composed_from_the_practice_root` and `::test_the_word_clients_is_not_required_of_it` |

**Every mutation was caught, each by tests that name the property it broke, and no unrelated test
fired on any of them.**

**Mutation 4 is the one that taught me something and it is disclosed as a correction rather than as a
result.** On its first run it was caught by the source-level guard **alone**, because the one firm
`live_paths.py` writes is `FIRM001`, so naming the record and taking the only one give the same
answer. A source guard with no behavioural partner is close to a check that cannot fail. I added
`test_a_firm_that_is_not_FIRM001_works`, which imports `config` against a record with
`firm_id: FIRM042`, and re-ran the mutation: it is now caught twice. That is commit `13e1c6a`.

### Red before green

`tests\test_client_top_folder.py` was written and run before `config.py` was touched. **15 failed, 0
passed**, which is every test in the file:

```
FAILED tests/test_client_top_folder.py::AcceptedTest::test_it_need_not_sit_under_the_practice_root
FAILED tests/test_client_top_folder.py::AcceptedTest::test_the_stored_path_is_the_client_top_folder
FAILED tests/test_client_top_folder.py::AcceptedTest::test_the_word_clients_is_not_required_anywhere_in_the_value
FAILED tests/test_client_top_folder.py::RefusalTest::test_a_blank_value_is_refused
FAILED tests/test_client_top_folder.py::RefusalTest::test_a_record_with_no_field_is_refused
FAILED tests/test_client_top_folder.py::RefusalTest::test_a_relative_value_is_refused
FAILED tests/test_client_top_folder.py::RefusalTest::test_an_empty_firms_list_is_refused
FAILED tests/test_client_top_folder.py::RefusalTest::test_an_empty_value_is_refused
FAILED tests/test_client_top_folder.py::RefusalTest::test_no_firms_json_at_all_is_refused
FAILED tests/test_client_top_folder.py::RefusalTest::test_the_refusal_creates_no_client_folder
FAILED tests/test_client_top_folder.py::RefusalTest::test_two_firms_are_refused_with_a_plain_message
FAILED tests/test_client_top_folder.py::NoDefaultSurvivesInTheSourceTest::test_clients_root_is_not_assigned_from_the_practice_root
FAILED tests/test_client_top_folder.py::NoDefaultSurvivesInTheSourceTest::test_config_composes_no_path_from_the_word_clients
FAILED tests/test_client_top_folder.py::NoDefaultSurvivesInTheSourceTest::test_the_default_firm_id_is_not_used_to_pick_the_record
FAILED tests/test_client_top_folder.py::NoDefaultSurvivesInTheSourceTest::test_the_field_name_is_stated_once
15 failed in 1.11s
```

`ClientTopFolderTest` in `test_path_layout.py` could not be red first, because it asserts against a
value that only exists once the change is in. **Mutations 1 and 6 are what stand in for its red run**,
and both catch it.

---

## 6. Flags: things wrong that this brief did not ask about

**Three, none fixed. Two are small and obviously right and I will do either in the same session if
told to.**

**1. The refusal happens after `config.py`'s `mkdir` block rather than before it.** `_client_top_folder()`
runs beside `load_firms()`, which is below the block that creates five directories. So an
installation with no `client_top_folder` builds `Intellibills\`, `Documents\`, `Backups\`, `db\` and
`logs\` and **then** refuses. **This is not the fourth trap**: those five sit inside a practice root
the operator configured as an absolute path, so nothing lands anywhere unexpected, and
`test_the_refusal_creates_no_client_folder` confirms the client folder itself is never made. **But it
breaks the property `_required_root()`'s own docstring states**, that the check is the definition and
cannot run after the folders are made. **Left alone deliberately.** Fixing it means either moving
`load_firms()` above the path block or moving the `mkdir` block below the loaders, and the second
would also stop an SMTP refusal creating folders, which is a behaviour change this brief did not ask
for. **Small and obviously right, one command to check: say the word and I will move the `mkdir`
block, with the SMTP consequence stated as part of the change rather than smuggled in.**

**2. `worker\filing.py`'s `get_client_directory()` docstring now says something untrue.** Its first
line reads "This client's folder under Clients", and after this change the folder is whatever the
firm's `client_top_folder` names. **Not touched, because 18.2b freezes that function and the brief
was explicit that narrowing the freeze is Paul's decision.** Five other production files carry the
same phrase in prose: `app.py` at 5 lines, `worker\database\repository.py` at 3,
`worker\extraction_pipeline.py` at 2 and `worker\resolution\service.py` at 3, enumerated in section 3.
**These are the pipeline's own equivalent of the six on-screen messages amendment 256 found in
Desktop**, and 10e.14's completion test is that no operator-facing sentence in either product
asserts the folder is called `Clients`. A docstring is not operator-facing, so this may be out of
scope by design; **I am flagging it rather than assuming either way.**

**3. A check that cannot fail, found while enumerating.**
`tests\test_resolution_backfeed.py:277`, inside
`test_a_review_pair_that_desktop_already_deleted_is_not_a_failure`, does:

```python
review_dir = config.CLIENTS_ROOT / "Test Client" / "Review"
self.assertFalse(review_dir.exists())
```

**Review left the client folder at sub-step 10d.54** and now lives at `REVIEW_ROOT / client_id`, so
that path is one nothing has written since. The assertion is true whatever the code does. **The three
assertions after it are the test's real subject and they are sound**, so the test is not worthless,
only its precondition is dead. Pre-existing and nothing to do with this change. **Small and obviously
right: point it at `config.REVIEW_ROOT / <the client id the fixture seeds>` and it starts meaning
something again. Say the word.**

---

## 7. What in the brief did not survive contact

The brief asked me to say which of its claims rest on files read today and which on a document.
**Everything I could check held.** Listed rather than summarised, because "it was all fine" is the
answer that gets given without looking.

| Claim | Rests on | Held? |
|---|---|---|
| The live `firms.json` content, quoted in full | A file read today | **Yes, byte for byte.** Read at 16:57 BST and the five fields and both values match |
| `CLIENTS_ROOT = PRACTICE_ROOT / "Clients"` is the only `"Clients"` in production Python | Code | **Yes** |
| Exactly three occurrences of `CLIENTS_ROOT`, at those three sites | Code | **Yes**, and the three are the ones named |
| `get_client_directory()` is the single choke point, callers `file_receipt()` and `file_statement()` | Code | **Yes**, and no other module calls it |
| `config.FIRMS` is `{}` under pytest and always has been | Code | **Yes.** It is why 50 collection errors appeared the moment the field became required. It is now false by design |
| `test_every_config_path_constant_is_under_a_temp_root` asserts exactly 18 | Code | **Yes**, and it is still 18 |
| `live_paths.py`'s docstring says it redirects paths and nothing else | Code | **Yes**, and that sentence is now struck through |
| The suite stood at 579 passed, 358 subtests | A run | **Yes, exactly** |
| Section 18.2b's freeze is live and was narrowed only by amendment 113, for 10d | The design document | **Not independently checkable from here.** I read 18.2b and amendment 113 and they say what the brief says; whether the freeze is still live is the document's own claim and I took it. **It cost nothing to take, because the change did not need to touch a frozen function** |
| 41 production `.py` files | A count | **Reconciles.** I found 51 non-test files; 51 minus 9 package `__init__.py` minus `docs\specs\categorisation_engine.py` is 41. The brief did not say what it excluded |
| F17 in `2026-08-20_LIST_settings_firm_and_client.md` might still describe two fields | A document | **It does not.** Row F17 was already corrected to one field by amendment 261. **But that row still says the folder name is "hardcoded [...] in `config.py`'s `CLIENTS_ROOT`" in the present tense, which this change makes stale.** The consultant session owns that file |

**One thing in the brief was incomplete rather than wrong, and it cost a round of red.** Section 4
named the pytest problem and `test_conftest_redirect.py`'s 18-constant assertion, and it did not name
`tests\test_required_roots.py` and `tests\test_required_smtp.py`, which import `config` in
subprocesses outside `conftest.py`'s reach. **That is the same shape as this project's own rule about
sets**: "the pytest problem" was described as one thing and it is three. Found by running the suite rather than by reading, and it is in section 2 above.

---

## 8. My own mistakes, including the ones I caught

**Five, all caught by my own runs before anything was committed.**

1. **`test_config_composes_no_path_from_the_word_clients` matched a substring and fired on
   `INTELLIBILLS_ROOT / "clients.json"`**, which is the client registry file and nothing to do with
   the top folder. Caught on the first red run. Changed to compare the path segment whole, and the
   reason is in the test's docstring.
2. **`test_the_field_name_is_stated_once` used a bare `assertIn` against the whole of `config.py`**,
   so its failure printed 20 KB of haystack for a one-line claim. Caught on the same run. Changed to
   an `assertTrue` with a message that names what it wanted.
3. **`test_the_default_firm_id_is_not_used_to_pick_the_record` compared the unparsed function
   including its docstring**, and the docstring explains that `DEFAULT_FIRM_ID` is deliberately not
   used, so the test failed on its own subject's explanation of itself. Caught on the first **green**
   run. The docstring is now stripped before the comparison.
4. **Mutation 4 was caught by a source guard alone**, described in section 5. Fixed with a
   behavioural test rather than left as a note.
5. **I added up an enumeration by eye and got it wrong**, in the first draft of section 3 above. It
   said `CLIENTS_ROOT` appeared "76 occurrences across 22 files" and "73" of them in `tests\`. The
   files were right and both numbers were not: it is **74 matching lines and 84 occurrences**, of
   which **71 lines and 81 occurrences** are in `tests\`. The two figures differ because `grep -c`
   counts matching lines and some lines carry the name twice. Caught by recounting programmatically
   against `HEAD~2` before committing this report, which is `CLAUDE.md`'s own rule: **count it
   programmatically and print the count, rather than adding up a printed list.** The list I printed
   was correct throughout; only my arithmetic over it was not, **which is the more dangerous of the
   two failures, because the evidence looked right underneath the wrong total.**

**Nothing was hidden and nothing was left in a mutated state.** The mutation script asserts each file
is restored byte for byte and prints that it did, and `git status` was read afterwards.

---

## 9. The one line for Paul

**Do not change `client_top_folder` on the Firm Settings page until piece four lands.** From now
until then the pipeline reads that field while IntelliBooks still uses its own hardcoded `Clients`
under the practice root, and the two agree only because the value you typed happens to match. Change
it and the two products would file into two different folders.

---

## 10. Confidence

**High that the change is correct and complete for what the brief asked**, and it rests on: the full
suite at 600 passed with 358 subtests, six mutations each caught by tests naming the property they
broke, an AST-level guard that no path in `config.py` is composed from `"Clients"`, and the live firm
record read off disk resolving to the same folder the old code composed.

**High that no frozen function was touched**, and it rests on `git diff --stat HEAD~2 -- worker/ app.py`
being empty rather than on my recollection of what I edited.

**High that the enumerations in section 3 are complete for Python**, and it rests on walking the
repository for `.py` files, diffing that walk against `git ls-files`, and printing the grep whole
rather than counting from a sample. **It says nothing about `IntelliBooks-Desktop-v3.html`**, which is
piece four and which I did not open.

**Moderate on the flag about the `mkdir` ordering being worth acting on.** The property it breaks is
real and stated in `config.py`'s own docstring; whether it matters in practice is a judgement, and it
is Paul's.
