# Report: the test environment's archive root, 2026-09-20

Written by the implementation session, Claude Code, 2026-09-20, 11:17 BST, read off the clock in the
reply that states it. Zone established rather than assumed: `date` reports `GMTDT`, which is Windows'
"GMT Daylight Time" with the spaces stripped, and is BST, so this shell's local time is Europe/London
and needs no conversion.

Worked from `PROMPT_claude_code_2026-09-20_temp_environment_archive_root.md`.

**Nothing in `2026-07-25_BUILD_STATUS.md` or `2026-07-25_CONSOLE_DESIGN.md` was touched.** Both were
modified by the consultant session while this work was running, and neither was staged or committed
by me.

**No production code was changed.**

---

## 1. The one measured suite total, and what the earlier figures were

**1603 passed, 2 skipped, 1201 subtests**, measured on 2026-09-20 at 11:17 BST on commit `809f158`,
which is the committed state of both this work and step 10am.

**This supersedes every other figure in my reports and messages for this work.** Four totals were
quoted across two days and they are not in conflict; each was a snapshot of a different tree, and I
did not say so at the time, which is the fault being corrected here.

| Figure | Tree it measured | Where I quoted it |
|---|---|---|
| 1592 passed, 1 skipped, 1201 subtests | HEAD with none of my work, measured with `--ignore=tests/test_review_seam.py` | 2026-09-19 report, section 3.2, as the "before" |
| 1601 passed, 2 skipped, 1201 subtests | HEAD plus step 10am only | 2026-09-19 report, section 3.2, as the "after" |
| 1602 passed, 2 skipped, 1201 subtests | plus this brief's fix, before the hole in section 4 was closed | a message on 2026-09-20 |
| **1603 passed, 2 skipped, 1201 subtests** | **commit `809f158`, the state now** | here |

**The message that needs correcting is mine of 2026-09-20 after the commit.** It reported 1603 and
said "Same as before it". **That was true and it read as a contradiction**, because the comparison
was between the run immediately before the commit and the run immediately after it, both 1603, while
the 2026-09-19 report's "after" figure says 1601. Nothing moved across the commit; what moved was the
tree, twice, between the two reports. **Saying "the same as before" without naming which before is
how a true sentence becomes a misleading one**, and the table above is what I should have written.

**The two tests between 1601 and 1603**, so the arithmetic is checkable rather than asserted:

- `test_the_shared_fixture_covers_everything_process_once_writes`, added to
  `tests\test_logs_isolation.py` as the control on the guard change in section 3
- `test_a_fresh_polls_volatile_fields_are_sound`, added to `tests\test_review_seam.py` to close the
  hole in section 4

**`test_the_volatile_fields_are_checked_rather_than_waved_through` was renamed**, to
`test_the_committed_fixtures_volatile_fields_are_sound`, so the count moved by two and not by three.

---

## 2. What was wrong, confirmed against the files

**The brief is right and I have checked every claim in it.**

`config.py` derives the archive folder in two steps: `INTELLIBILLS_ROOT = PRACTICE_ROOT /
"Intellibills"` and then `FILES_DIR = INTELLIBILLS_ROOT / "Documents"`. Read off `config.py`'s syntax
tree, along with the other nineteen path constants.

`tests\resolution_fixtures.py`'s `TempEnvironment` wrote its own version, `config.PRACTICE_ROOT =
self.path` and `config.FILES_DIR = self.path / "Documents"`, **with the middle segment dropped**.
The same drop was in nine of its assignments, not one: `FILES_DIR`, `RECEIPT_INBOX_ROOT`,
`REVIEW_ROOT`, `RESOLUTIONS_DIR`, `ATTACHED_DIR`, `PIPELINE_STATUS_PATH`, `BACKUPS_ROOT`,
`CHARTS_DIR` and `INTELLIBOOKS_PUBLISH_DIR`, which was also rooted at `INTELLIBOOKS_ROOT` where
`config.py` roots it at `INTELLIBILLS_ROOT`.

**Why nothing saw it.** `archive_address()` returns the document's path relative to `PRACTICE_ROOT`,
and the fixture moved both ends, so the short address was internally consistent. **The suite already
disagreed with itself**: `tests\test_publish_item.py` asserts the address starts with
`Intellibills\Documents\` and passes, because it builds its own environment and never reaches
`TempEnvironment`. `ARCHIVE_PATH_RE` in my `tests\test_review_seam.py` expected the short form, which
is why the fixture guard could not catch it.

**It surfaced only because step 10am committed one of those addresses as a fixture handed to another
product**, and the consultant session compared it with what the live pipeline writes.

---

## 3. What was built

**No production code changed.** Two test files modified, plus the regenerated fixture.

### 3.1 `TempEnvironment` stops restating the derivation

**`_rebased()` takes each config path's position below whichever session temp root it sits under and
moves it onto the test's own directory.** The layout is not written down here at all, so a change in
`config.py` reaches this fixture with no edit.

**This is `live_paths.live()` in the other direction, and for its stated reason.** That function's
docstring already says it maps a redirected path back "by taking the part below whichever temp root
it sits under, so this module holds no second copy of the layout and a path that moves in config.py
moves here with it". **The argument was already written and this fixture was the counter-example.**

**What is still written out is the LIST of names, and deliberately.** `REDIRECTED` is the guard: a
config path not in it keeps the session temp root shared by the whole run, so a test writing through
it would be seen by the next test's poll. Every entry is there because that happened once, and the
existing comments recording which sub-step added each are kept.

**`config.PRACTICE_ROOT` still equals `self.path`.** Several tests build a path outside the client
folder as `env.path / "elsewhere.pdf"` and mean "inside the practice root, outside the store", so
splitting this into a `practice\` subfolder would quietly change what those tests assert.

### 3.2 `CREATED_PARENTS`, and it was not optional

Rebasing put the database at `db\receipts.db`, where `config.py` puts it, and nothing created that
folder. **819 tests failed with `sqlite3.OperationalError: unable to open database file`.** sqlite
creates a missing database file and will not create the folder above it, which is why `config.py`'s
own mkdir block carries `DB_PATH.parent.mkdir(...)`. The fixture now does the same.

### 3.3 `tests\test_logs_isolation.py`, and this one is a judgement call

**Its redirect guard read each module's source text for `config.X =`.** The refactor replaced those
literals with a `setattr()` loop, so the text vanished and **192 subtests went red with nothing
actually unredirected**.

It now reads the fixture's own `REDIRECTED` and `PINNED_BY_HAND` tuples for modules that use the
fixture, and keeps the text search for every other module, because the hand-rolled environments this
guard mostly exists to catch do assign one at a time. **That is stronger than the text search rather
than weaker**: it reads the list the fixture actually loops over, where before a name could have sat
in a commented-out assignment and still matched.

**`test_the_shared_fixture_covers_everything_process_once_writes` is the control**, asserting every
name `process_once()` writes is one `TempEnvironment` pins. Without it `_fixture_redirects()` could
return anything and the guard would pass on every module using the fixture.

**Flagged as yours to reverse.** The brief says to stop and report where a test fails for a reason
that is not the path, and this one does not fail for a path reason. **I changed it because it is
caused directly by the required refactor**: you cannot stop restating the derivation without
defeating a guard that greps for the restatements, and handing back a 192-red suite would have been
handing back half the work. If you would rather have had it stopped, this is the change to undo.

---

## 4. The mutation that was not caught, and what it exposed

**This is the most important section and it is a defect in my own step 10am work.**

The brief asked me to put the segment back and show the fixture guard failing. I mutated `_rebased()`
to strip `Intellibills` again, reproducing the old behaviour exactly, and ran the whole suite.

```
=== the-fixture-drops-the-archive-root-again ===  expects: caught
last line: 1602 passed, 2 skipped, 1201 subtests passed in 209.72s
caught by 0 reported failure(s):
verdict: NOTHING CAUGHT IT, and this mutation had to be caught
restored, byte for byte
```

**Nothing caught it. The entire suite passed.** So the fix was in and there was no guard on it.

**Why.** `ARCHIVE_PATH_RE` ran against the **committed fixture only**. `normalised()` replaces
`archive_path` on both sides of the equality check, so the freshly produced address was examined by
nothing. A regression in the derivation left the committed file still matching the pattern and hid
the produced value entirely.

**The general form, and this project has named it before.** A guard over a stored artefact is not a
guard over the thing that produced it. **Mine asserted the file it was meant to be checking
against**, which is amendment 97's shape: it could not have failed for the reason it existed.

**The fix.** The volatile-field assertions now run against a freshly produced item as well as the
committed one, through one shared helper. Re-run on the same mutation:

```
last line: 1 failed, 1602 passed, 2 skipped, 1201 subtests passed in 153.47s
caught by 1 reported failure(s):
  FAILED tests/test_review_seam.py::TheCommittedFixtureIsWhatThePipelineProducesTest::test_a_fresh_polls_volatile_fields_are_sound
verdict: OK: caught, as expected
restored, byte for byte
```

**Red before green on the pattern as well**, before the fixture was regenerated:

```
E  AssertionError: Regex didn't match:
   '^Intellibills\\Documents\\CLIENT001\\\d{4}\\\d{2}\\[0-9a-f-]{36}_shared\.pdf$'
   not found in 'Documents\CLIENT001\2026\09\a3626a56-..._shared.pdf'
```

The regenerated fixture reads
`Intellibills\Documents\CLIENT001\2026\09\d4410e6c-5458-454c-9471-c22c4d81b3ac_shared.pdf`.

---

## 5. Counts, and one disagreement with the brief

**42 files carry a module-level import from `tests\resolution_fixtures.py`, not 43.** Enumerated with
`grep -l` over `tests\*.py`. **45 mention the module name**, the other three being
`tests\mutation_harness.py` and `tests\test_logs_isolation.py`, which name it in prose or read it as
a file, and no third importer. Two of the 42, `test_firm_vendor_writer.py` and `test_layer_two_row.py`,
import only `rows` and never touch `TempEnvironment`. **My best guess at the difference is that the
brief counted `resolution_fixtures.py` itself**, which would give 43, but that is a guess and I have
not checked it against whatever the brief counted.

**52 files mention `TempEnvironment`, which agrees.**

**Tests that moved: 208 failed at the worst point and 0 remain.** 819 before `CREATED_PARENTS`, then
208, of which 192 were the one source guard in section 3.3 and 16 were the `CLIENTS_ROOT` name in
section 6.

---

## 6. Every test I changed, one by one

**One file, and no test was changed to suit the new path.**

| File | Change | Reason |
|---|---|---|
| `tests\test_logs_isolation.py` | `_fixture_redirects()` added; the guard reads it for modules using the fixture; `test_the_shared_fixture_covers_everything_process_once_writes` added as its control | Section 3.3. Not a path reason, and flagged there as yours to reverse |
| `tests\test_review_seam.py` | `ARCHIVE_PATH_RE` requires the `Intellibills\` segment | **This one WAS asserting the short form**, which is the case the brief permits |
| `tests\test_review_seam.py` | volatile-field assertions run against a freshly produced item as well as the committed one | Section 4. My own defect, not a path patch |
| `tests\fixtures\published_item_needs_review.json` | regenerated through the `REGENERATE_REVIEW_FIXTURE=1` route | The brief's item two |

**Sixteen tests across three files were NOT changed**, and that is the decision in section 7.

---

## 7. Flagged, not fixed: the client root's name

**Rebasing `CLIENTS_ROOT` renames the temp client folder from `Clients` to `Client Folders`, and I
stopped rather than carry that.**

`tests\live_paths.py` calls the session one `Client Folders` **deliberately**, and says so: "if
`config.py` ever went back to composing `PRACTICE_ROOT / "Clients"` the value would change and a test
comparing against it goes red". **`TempEnvironment`'s `Clients` undoes that for every test that uses
it**, which is a real weakness and is not the defect this brief is about.

**What it costs to fix**: 16 tests failed across `test_discard_client_copy.py`,
`test_discard_sidecar_and_cli.py` and `test_corrected_note.py`, all on a hardcoded `Clients` segment
in `FILED_RELATIVE`-style constants, and the literal appears in 40 test files. **`CLIENTS_ROOT` is
also a firm setting rather than a layout**, read by `config.py` through `_client_top_folder(FIRMS)`
and not composed from the practice root, so it is not `_rebased()`'s business either way.

**So it is pinned by hand at `PRACTICE_ROOT / "Clients"`, exactly as before**, in `PINNED_BY_HAND`
with the reasoning beside it. **The obvious fix is to take it from the firm record the way
`config.py` does**, which makes the fixture exercise the real path and removes the last hand-written
location; that is a change across 40 files and was not mine to start here.

**Noted rather than claimed:** a brief named
`PROMPT_claude_code_2026-09-20_clients_root_from_the_firm_record.md` appeared in the repository root
while this work was running. I have not read it and do not know whether it covers this.

**And the flag in the brief is answered.** `category_unconfirmed` reading `false` needs no change:
the consultant session enumerated the readers in `IntelliBooks-Desktop-v3.html` and nothing acts on
`false`. Closed, not carried.

---

## 8. Mistakes I made, disclosed

**Five.**

**1. The archive root itself.** My step 10am fixture carried the short address and my report asserted
it was `archive_address()`'s documented form. It was not. Corrected in place in
`2026-09-19_REPORT_claude_code_review_seam.md` section 2.2, with the superseded wording struck rather
than deleted.

**2. The guard that could not catch its own subject**, section 4. Worse than the first, because the
first was a defect and this was a check that gave the appearance of covering it.

**3. I stated the time in four replies without reading the clock**, deriving it from a reading taken
at the start of the session and running up to about 27 minutes ahead. `CLAUDE.md` sets this out in
full, including that a derived timestamp is unbounded error rather than drift. **Paul caught it, not
me.** Every reply since has run `date` in the reply that states the time.

**4. "Same as before it"**, section 1. True of the comparison I had made and misleading against the
figure in the other report.

**5. An ordering bug I caught myself.** The first version pinned `CLIENTS_ROOT` by hand **after** the
folder-creation loop, so the loop would have created the session client folder and left the test
without its own. Found by reading the block back before running it, and the hand pins now come first
with a comment saying why.

---

## 9. Confidence

- **That the archive path is now the live form: high.** The regenerated fixture was read back and the
  pattern requires the segment.
- **That the fixture no longer restates the layout: high**, from reading the file: the only path
  literals left in `TempEnvironment` are the two in `PINNED_BY_HAND`, both non-layout and both
  documented.
- **That a regression would now be caught: high, and measured rather than argued.** The same mutation
  that passed 1602 tests fails one after the change, and the harness restored the file byte for byte
  both times.
- **That no test was weakened: medium-high.** The guard change in section 3.3 I believe is stronger,
  and I have given the reasoning rather than only the conclusion so it can be checked. **What I
  cannot claim is that it is equivalent**: it reads a different thing from what it read before.
- **That 1603 is the total on `809f158`: high**, measured at 11:17 BST today.
- **That 42 is the importer count: high** for my enumeration, and **I cannot say what the brief's 43
  counted.**

---

## 10. The commit

**Made, on Paul's instruction of 2026-09-20.** `809f158` on `feat/console-phase0`, four files, 820
insertions, 94 deletions. One commit carrying this work and step 10am, as the brief required.

**The suite was run again after it: 1603 passed, 2 skipped, 1201 subtests**, unchanged across the
commit, so the two source guards that sweep the git-tracked set found nothing new in the added files.

**Committed by explicit path.** The consultant session modified `2026-07-25_BUILD_STATUS.md` and
`2026-07-25_CONSOLE_DESIGN.md` while this was running and `PROMPT_claude_code_2026-09-19_review_seam.md`
was staged by somebody else. None was swept in, and the staged prompt was left staged rather than
committed or unstaged.

**No push and no PR.** `feat/console-phase0` is the current branch and two other sessions commit to it.
