# Report: the Review seam, the Python half, 2026-09-19

Written by the implementation session, Claude Code, 2026-09-19, 17:17 BST, read off the clock in the
reply that states it. Zone established rather than assumed: `date` gave `Sat Sep 19 17:17:11 GMTDT`
and `date -u` gave `16:17 UTC`, so this shell's local time is Europe/London and needs no conversion.

Worked from `PROMPT_claude_code_2026-09-19_review_seam.md`. Step 10am, the Python half.

**Nothing in `2026-07-25_BUILD_STATUS.md` or `2026-07-25_CONSOLE_DESIGN.md` was touched.** Both are
the consultant session's.

**No production code was changed.** Every test below was written without needing one.

---

## 1. My own enumeration, and where it agrees

**The four test names in the brief are all present**, in `tests\test_publish_trigger.py`:
`test_needs_review_publishes_one_item` at `EveryStatusPublishesTest`,
`test_a_failed_extraction_publishes_one_item`, `test_an_extraction_that_raised_publishes_nothing` and
`test_a_possible_duplicate_publishes_too`. **`tests\test_publish_item.py` holds 30 tests**, counted
with `grep -c "def test_"`. Both figures agree with the brief.

**I looked at the other end too, which the brief did not name, and it is the half that matters for
what is new.** `tests\test_resolution_backfeed.py` covers the consumer in over forty tests and
`DiscardedNoteTest` already asserts that a discard note sets the status and deletes no files. **What
none of them do is start from a receipt the pipeline made.** Every one seeds the database through
`BackfeedTestCase.seed_desktop_filed()` or `seed_awaiting_settlement()`, and every one drives the
consumer through `consume_notes()`, which calls `app._consume_resolution_notes()` directly rather
than through a poll.

**So the brief's claim that the join is untested holds, and I could state the reason rather than
repeat it**: one end starts from a real poll and stops at the published item, the other starts from a
hand-seeded row. Nothing spans the two.

---

## 2. What was built

One new test file and one new fixture. **No production file changed.**

| File | What it is |
|---|---|
| `tests\test_review_seam.py` | 530 lines. Nine tests and one skipped regeneration route |
| `tests\fixtures\published_item_needs_review.json` | The published item, written by a real poll |

### 2.1 The fixture, and the path I chose

**`tests\fixtures\published_item_needs_review.json`.**

**Why there.** `tests\` already holds `chart_fixtures.py` and `resolution_fixtures.py`, so a reader
looking for fixtures looks in `tests\`. This is the first fixture in the repository that is a data
file rather than a module, so `tests\fixtures\` is a new directory. **`Test Receipts\` at the root
was the alternative and is wrong for this**: everything in it is a document a receipt is made of, a
PDF or a PNG or a bank CSV, and this is the pipeline's own output rather than an input to it.

**Why that name.** It says what the item is and what state the receipt behind it is in, so the
Desktop harness reading it does not have to open it to find out whether it belongs in the Review
queue.

**What is in it.** The item exactly as `write_item()` wrote it on a real poll: 23 keys, `receipt_id`
through `archive_path`, `validation_status` of `needs_review` and one `validation_notes` entry
reading `gross mismatch: 10.0 + 2.0 = 12.0, got 99.0`. **The receipt behind it is not `ok`**, which
the guard asserts rather than assumes.

### 2.2 The guard on the fixture

~~`TheCommittedFixtureIsWhatThePipelineProducesTest`, four tests.~~ **Five from 2026-09-20**,
counted with `pytest --collect-only` rather than carried: the fifth runs the checks below against a
freshly produced item and not only against the committed file.

**A fresh poll regenerates the item and it is compared with what is committed**, keys first and then
values. **Four fields cannot be the same twice and are named rather than skipped**: `receipt_id`,
`pipeline_receipt_id`, `capture_date` and `archive_path`. ~~Each is then asserted on its own, so
"normalised" does not quietly become "unchecked":~~ **WRONG, corrected 2026-09-20: each was asserted
on its own ONLY on the committed fixture, and the item a fresh poll produced was checked by nothing.
"Unchecked" is exactly what "normalised" became.** The assertions run against both from 2026-09-20;
see the note below the bullets and section 4 of the 2026-09-20 report. The bullets are what was
asserted, of the committed fixture alone:

- the two id keys carry one value, and it parses as a uuid
- `capture_date` parses as an ISO timestamp and carries an offset
- ~~`archive_path` matches `Documents\CLIENT001\{year}\{month}\{uuid}_shared.pdf`, which is
  `archive_address()`'s documented form, and contains the receipt's own id~~
  **WRONG, corrected 2026-09-20. It was not `archive_address()`'s documented form, and that was
  the defect.** The live form carries the archive root:
  `Intellibills\Documents\{client_id}\{year}\{month}\{receipt_id}_{filename}`. The fixture and the
  pattern both had the `Intellibills\` segment missing, because
  `tests\resolution_fixtures.py` restated `config.py`'s folder layout and dropped it.
  `archive_address()` returns a path relative to `PRACTICE_ROOT` and the fixture moved both ends,
  so the short address was internally consistent and wrong. **`tests\test_publish_item.py` already
  asserted the live form, so the suite disagreed with itself and this report asserted the wrong
  half of it.** Fixed and regenerated on 2026-09-20, commit `809f158`, reported in
  `2026-09-20_REPORT_claude_code_temp_environment_archive_root.md`.

**The sentence introducing those bullets was the more misleading one and is struck above.** It was
true of the committed fixture and false of the item a fresh poll produces, which nothing checked at
all. **A mutation dropping the archive root from the derivation passed all 1602 tests on
2026-09-20.** The assertions now run against both. See section 4 of the 2026-09-20 report.

**How this correction came to be claimed twice before it was made.** I wrote a note quoting the
sentence and describing it as corrected, and took quoting it for striking it, then reported it done
without reading the line back. **The same fault as the defect being corrected**: I checked the
artefact I had just written instead of the thing it was about. Paul caught it, on line 75, after two
such reports.

**Regeneration is executable rather than described.**
`REGENERATE_REVIEW_FIXTURE=1 .\.venv\Scripts\python.exe -m pytest tests/test_review_seam.py -q`
rewrites the file. **It is a skipped test rather than a script, and that is deliberate**: it must run
under pytest, because `tests\conftest.py` imports `tests\live_paths.py` before anything imports
`config`, and that is what redirects the two roots into a temp directory. A standalone
`python tests\test_review_seam.py` would import `config` against the live roots and run the `mkdir`
block against OneDrive, which is `CLAUDE.md`'s fourth trap. **It is skipped rather than absent so the
failure message can name a command that exists.**

**It does not regenerate the file when the comparison fails.** A guard that healed itself would be a
check that cannot fail, which amendment 97 already names on this project.

### 2.3 The note shape, checked against the contract rather than taken from the brief

**The brief's shape matches `parse_resolution_note()`, and the check is in code.**
`keys_the_note_parser_reads()` walks the parser's syntax tree and collects every top-level key it
reads, by its three access forms: `raw.get("x")`, `_note_text(raw, "x")` and `_note_flag(raw, "x")`,
resolving a module constant where one is passed instead of a literal. The test asserts every key in
the note is in that set, and asserts the set is non-empty first so an enumeration that found nothing
cannot pass.

**All seven keys in the brief's note are keys the parser reads**: `schema`, `receipt_id`,
`client_id`, `action`, `resolved_by`, `resolved_at`, `original_review_files`. The note also parses,
and `schema: 1` equals `service.NOTE_SCHEMA`.

**One property of the contract the test records rather than tidies away.** The note Desktop wrote on
Paul's machine carries `client_id: "Client_004"` and the fixture receipt is `CLIENT001`. **They are
left disagreeing on purpose**: `_receipt_for_note()` finds the receipt by `receipt_id` and nothing
reconciles the note's `client_id` against the row. A test that quietly corrected it would hide that,
and the docstring on `desktop_note_for()` says so.

### 2.4 The round trip, in one test

`TheRoundTripTest.test_a_published_item_is_resolved_and_applied_back_in_one_run`.

A real poll produces, publishes and archives the receipt. The note is written into
`config.RESOLUTIONS_DIR`. **The second poll is a real `app.process_once()` with an empty mailbox**,
so the consumer runs in the live order. Then:

- **the receipt**: status `discarded`, `filed_path` cleared, one `resolution_events` row with action
  `discard`, whose `actor` and `source` are asserted against `service.DESKTOP_ACTOR` and
  `service.DESKTOP_SOURCE` rather than against literals, so the row proves the back-feed path was
  taken and not the CLI. The note's own `resolved_at` is in `corrections_json` under
  `service.NOTE_RESOLVED_AT_KEY`, which is the idempotency key
- **the note file**: gone from `Resolutions\`, present in `Resolutions\processed\`, and
  `Resolutions\failed\` never created
- **the document**: still in the archive and byte for byte what it was
- **and one extraction row**, because a discard writes none

### 2.5 The archive survives a discard

`TheArchiveSurvivesADiscardTest`, two tests, against a receipt this file's own poll archived.
`discard_receipt()`'s first docstring line says the original file in the document store is never
deleted on any path. **The second test is the one that makes it worth having**: it passes
`delete_client_copy=True`, which is the only flag on that function that deletes a file at all, and
asserts the archived document is still there and unchanged.

---

## 3. Evidence

### 3.1 Red before green

The file was written before the fixture existed and run against the tree. **Seven of the nine failed
and two passed**, which is the right shape: four fixture tests with no fixture to read, the two
contract tests with a bug of mine in them, and the round trip.

**The round trip's first red is worth quoting, because it failed further in than I expected and that
is what corrected me:**

```
E  AssertionError: 'desktop' != 'resolution_note'
```

It had already driven the whole seam. The status was `discarded` and the note applied; what was wrong
was my assertion about the audit row.

After the fixture was generated and the three errors in section 5 corrected: **9 passed, 1 skipped**.

### 3.2 The suite, before and after

`.\.venv\Scripts\python.exe -m pytest -q`, both measured on today's HEAD.

| | Passed | Skipped | Subtests |
|---|---|---|---|
| Before, with `--ignore=tests/test_review_seam.py` | 1592 | 1 | 1201 |
| After | **1601** | **2** | 1201 |

**Nine tests and one skip, which is exactly the new file.** The skip is the regeneration route.

**The before-figure was measured rather than carried.** Yesterday's report recorded 1592 passed and
**1191** subtests; today's HEAD gives 1592 passed and **1201**. The pass count is unchanged and the
subtest count moved by ten, from commits landed since, so quoting yesterday's line would have put a
stale number in this table.

### 3.3 Mutations

Five, through `tests\mutation_harness.py`, each anchored, asserted unique before anything was
written, run against the whole suite, and restored byte for byte. **All five were expected to be
caught and all five were.**

| Mutation | Target | Caught by |
|---|---|---|
| The item carries a fixed media type | `worker/publish.py` | 4 tests, one of them new |
| `"confidence"` renamed to `"confidence_level"` in the sidecar | `worker/filing.py` | **1 test, and it is the new fixture guard** |
| `process_once()` stops consuming notes | `app.py` | 45 tests, the new round trip among them |
| A discard unlinks the archived document | `worker/resolution/service.py` | 10 tests, 3 of them new |
| `build_item()` mints a fresh `receipt_id` for the item | `worker/publish.py` | 4 tests, one of them new |

**The second is the one that earns the fixture.** A key rename in the published item is invisible to
every other test in the suite. That item is a contract with a product written by a session that
cannot see this one, so a silent rename is precisely the failure the fixture exists to catch.

**And a claim of mine that the mutations refuted, stated because I made it before measuring.** I
expected the third mutation to be caught mainly by the new file, reasoning that nothing else drives
the note consumer through `process_once()`. **It is caught by 45 tests.** The printed list truncated
at 15, so I re-ran that mutation against `tests\test_review_seam.py` alone to establish that the new
test is among them, and it is: `1 failed, 8 passed, 1 skipped`, the failure being the round trip.
**That was a subset run, which normally proves only that the subset noticed; here the subset was the
question being asked.**

**So the honest reading of the table: the only mutation the new file catches alone is the sidecar
rename.** Every individual link of the seam already had a test on it. **What was missing was the
links in sequence, and no mutation will ever show that**, because a mutation breaks one link at a
time and some existing test covers each link. The round-trip test is coverage of a path nothing
walked whole, not a discriminator that beats the tests already there. **Stated plainly rather than
dressed up**, because a report claiming the new test is uniquely sensitive would be claiming
something these five runs do not support.

---

## 4. Flagged, not fixed

**One, and it is small.** `category_unconfirmed` reads `false` on this fixture, a `needs_review`
receipt that was never categorised at all. `category_is_unconfirmed(None)` returns False by design,
and `extra_for()`'s docstring says why in terms: "a key that said nothing must not hold a receipt
that is fine". **So this is the documented behaviour and not a defect**, and it is flagged only
because the Desktop harness will read that key off the fixture and a reader could take `false` to
mean the category was confirmed. **Nothing to fix here. It is worth the consultant session knowing
before the Desktop half is written.**

---

## 5. Mistakes I made, disclosed

**Four. Three were caught by red-before-green, and the fourth by the mutation harness refusing an
anchor.**

**1. I asserted the discard event's `source` was `"resolution_note"`.** It is `DESKTOP_SOURCE`. I had
written what I expected the back-feed to record rather than reading the call site. **Corrected by
reading `apply_resolution_note()`'s call to `discard_receipt()`, which passes `actor=DESKTOP_ACTOR,
source=DESKTOP_SOURCE`, and the assertion now names the constants rather than the strings**, so it
would survive a rename and would fail on a path change.

**2. I asserted a `note_resolved_at` column on `resolution_events`.** There is no such column. The
value goes into `corrections_json` under `NOTE_RESOLVED_AT_KEY`, which `_record_event()`'s docstring
says in terms. I had guessed a column name instead of reading `schema.py`.

**3. My AST walk tried to resolve a loop variable as a module constant**, raising
`AttributeError: module 'worker.resolution.service' has no attribute 'unexpected'` on
`raw.get(unexpected)`. Now only an upper-case name is resolved, and the two keys that loop covers are
collected from the `for` statement's own tuple.

**4. The one that mattered, and I should have caught it earlier.** The first mutation run was
interrupted mid-flight. The harness restores in a `finally`, and a killed process does not run one,
so it left `worker\filing.py` carrying the `confidence_level` mutation and its own
`worker\filing.py.pristine` beside it. **I then ran a full suite and a mutation against that tree
without checking `git status` first**, and reported a result from it. That result is discarded and
nothing from it is in section 3.3; every figure there is from the re-run on the clean tree.

**The repair was established rather than assumed.** `git --no-optional-locks show HEAD:worker/filing.py`
piped through `sed 's/$/\r/'` md5s as `ff5f6a77ce51fd911243a964cae4e06b`, identical to
`worker\filing.py.pristine`, so I restored from the backup rather than using a git discard, deleted
the backup, and confirmed the restored file carries that same md5. **The line-ending step was needed
because git stores LF and the working file is CRLF**, and comparing them raw had already given two
different md5s, which is the reading that would have looked like a mismatch if I had stopped there.

**What I take from it.** A tool that edits production files and is interrupted leaves the tree
changed, so `git status` belongs before the next run and not after something looks odd. **It was
found only because the harness refused the next anchor**, reporting it appeared 0 times, which sent
me to read the file. The refusal was built for a different fault and caught this one.

---

## 6. Confidence

- **That the join was untested before this: high.** Established by reading
  `tests\test_resolution_backfeed.py`'s two seed helpers and its `consume_notes()` driver, not by
  searching for a test name. **What this confidence is about is the discard path specifically**; I
  did not enumerate every note action against every intake route.
- **That the new tests pass and the suite is green at 1601: high**, measured in this session.
- **That the fixture is what the pipeline produces today: high**, because the guard regenerates it on
  every run and the run is green. **It is only as good as the day it last ran**, which is the whole
  design.
- **That the note shape matches the contract: high**, from an enumeration off the parser's syntax
  tree rather than from the brief.
- **That the archive survives a discard: high**, asserted on bytes read before and after, on both the
  back-feed path and the `delete_client_copy` path.
- **That the mutation figures in section 3.3 are from a clean tree: high.** The tree was restored and
  verified by md5 before the re-run, and `git status` after every run since shows only the two new
  files and the staged brief.
- **That the new file is uniquely sensitive: LOW, and I am not claiming it.** Section 3.3 says what
  the measurements support and what they do not.

---

## 7. The commit

Proposed, not made. Awaiting a yes, per the brief.

```
test(review-seam): a published item, resolved by Desktop, applied by the next poll

Step 10am, the Python half. Nothing proved that an item the pipeline itself
produced is taken up on the other side, resolved and applied back: one end of
the suite starts from a real poll and stops at the published item, the other
starts from a hand-seeded row.

The round trip runs in one test. A real poll publishes and archives a
needs_review receipt; the note Desktop writes on a delete is written for that
receipt; a second real process_once() applies it. The receipt, the note file and
the archived document are all asserted afterwards.

tests/fixtures/published_item_needs_review.json is one real published item for
the Desktop half's node harness, which cannot run Python. It is written by
production code and guarded: a fresh poll regenerates it every run and the test
fails when it differs, with the four volatile fields named and separately
checked rather than skipped.

No production code changed.

Files: tests/test_review_seam.py,
tests/fixtures/published_item_needs_review.json
Suggested branch: feat/console-phase0 (current)
```

**No push and no PR proposed.** `feat/console-phase0` is the current branch and two other sessions
commit to it.

**The suite will be run again immediately after the commit and this section updated**, because the
change adds files and two source guards in the suite sweep the git-tracked set.
