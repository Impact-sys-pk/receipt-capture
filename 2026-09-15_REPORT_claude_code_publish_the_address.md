# Report, Claude Code, 2026-09-15: publish the address, not the picture

Written against `PROMPT_claude_code_2026-09-15_publish_the_address_not_the_picture.md`,
Paul's decisions of 2026-09-15. Section 20 of `2026-07-25_CONSOLE_DESIGN.md` carries
the design and 20.6 the seventeen build items. **This is items 1 to 7, the Python
worker half.** Items 8 to 17 are the front end and belong to the consultant session.

**Section 18 was not opened, not quoted and not used as authority for anything**, per
the brief and per section 20's own instruction.

**Built, tested and not committed.** The commit is proposed in section 8.

**Times are BST, read from Python's `zoneinfo`** rather than from `TZ=... date`, which
on this machine reports GMT in September. Finished 22:29 BST.

---

## 1. The seven items

| # | What | Where |
|---|---|---|
| 1 | The item stops reading the document's bytes and stops setting `image_base64` | `build_item()` in `worker/publish.py` |
| 2 | It carries `archive_path` instead | same |
| 3 | The address is relative to the practice root, with backslashes | new `archive_address()` |
| 4 | The absolute path is converted where the address is written | same |
| 5 | `image_media_type` stays | unchanged, with the reason recorded beside it |
| 6 | An explicit existence check replaces the one the byte read was doing | `build_item()`, raising `PublishError` as before |
| 7 | The exchange folder moves to `Intellibills\Incoming\` | `INTELLIBOOKS_PUBLISH_DIR` in `config.py` |

`base64` is no longer imported by `worker/publish.py`, which had one use.

**The key is `archive_path`**, the brief's own name. Nothing in the thread said
otherwise.

**The constant keeps the name `INTELLIBOOKS_PUBLISH_DIR`.** Item 6 of 20.6 names it as
it stands, so renaming it was not part of this change. It is read by
`worker/publish.py` and by six test fixtures.

---

## 2. What an item looks like now

The address, driven rather than described:

```
Intellibills\Documents\CLIENT01\2026\09\11111111-2222-3333-4444-555555555555_receipt.pdf
```

No drive letter, no user profile, backslashes. It round-trips through
`resolve_practice_path()` in `worker/resolution/service.py`, which is the function the
rest of this system uses to turn a stored path back into a file, and a test reads the
document's bytes back through it rather than joining the path a second way.

**Backslashes are joined rather than taken from `str(Path)`.** `str()` gives
backslashes on Windows and forward slashes anywhere else, and the form is part of a
contract with another product rather than a property of the host.

### Item 5, stated because it is the one thing that stays

`image_media_type` is still on every item. The front end uses it to tell a picture from
a PDF before it decides how to render, so it cannot wait to read the file. Only the
bytes go.

---

## 3. The one decision the brief left open, and Paul's ruling on it

**What happens to a document that is not under the practice root.** It has no address
that would work on another machine, and the brief does not name the case.

**I refuse it with `PublishError`.** Item 3 says the stored value "must contain no drive
letter and no user profile", and falling back to the absolute path would put both in
silently, which is the one thing that requirement forbids. Refusing makes it true by
construction rather than by every caller remembering.

**In production the guard can never fire.** The single call site is handed
`receipts.file_path`, which `save_file()` in `worker/storage/store.py` wrote under
`config.FILES_DIR`, itself under the practice root.

**The cost was seven test fixtures and Paul took the decision knowing it**, on
2026-09-15, with his reason recorded here in his words: those fixtures publish a
document from outside the practice root, and production cannot; making them publish from
inside it makes them honest rather than just green.

---

## 4. Red before green, and a disclosure about how it was obtained

**I wrote the production code before running the new tests, so the first run of the
publish tests was green.** That is the brief's first evidence requirement not met in the
order it asks for, and it is disclosed rather than presented as though it had been.

**A genuine red run was reconstructed rather than claimed.** `config.py` and
`worker/publish.py` were copied to the scratchpad, restored from `HEAD` with
`git checkout HEAD -- <the two paths>`, the new and changed tests run against the
unchanged code, then restored from the copies and md5 compared:

```
ca78ae2185ca47a3295a510d4bfcc2e9 *config.py
911a300f5334cda60cb50324427c4378 *worker/publish.py
```

Identical before and after, and `git reset -- <the two paths>` left the index as it was.

**16 failed, 67 passed, 87 subtests passed in 3.04s.**

```
FAILED tests/test_publish_item.py::ItemShapeTest::test_the_address_carries_the_archive_layout
FAILED tests/test_publish_item.py::ItemShapeTest::test_the_address_is_relative_to_the_practice_root
FAILED tests/test_publish_item.py::ItemShapeTest::test_the_address_resolves_back_to_the_document
FAILED tests/test_publish_item.py::ItemShapeTest::test_the_item_carries_no_picture_at_all
FAILED tests/test_publish_item.py::ItemShapeTest::test_the_item_carries_the_sidecar_key_set_and_two_more
FAILED tests/test_publish_item.py::ItemShapeTest::test_the_sidecar_passed_in_is_not_modified
FAILED tests/test_publish_item.py::TheDocumentHasToBeThereTest::test_a_document_outside_the_practice_root_is_refused
FAILED tests/test_publish_item.py::TheDocumentHasToBeThereTest::test_the_check_runs_before_anything_is_built
FAILED tests/test_publish_destination.py::AcceptedTest::test_a_name_with_a_space_is_accepted
FAILED tests/test_publish_destination.py::AcceptedTest::test_other_destinations_in_the_object_are_ignored
FAILED tests/test_publish_destination.py::AcceptedTest::test_surrounding_whitespace_is_stripped
FAILED tests/test_publish_destination.py::AcceptedTest::test_the_destination_folder_is_created_at_import
FAILED tests/test_publish_destination.py::AcceptedTest::test_the_destination_is_the_practice_root_then_intellibooks_then_the_leaf
FAILED tests/test_publish_destination.py::AcceptedTest::test_the_word_incoming_is_not_required_anywhere
FAILED tests/test_publish_destination.py::NoDefaultSurvivesInTheSourceTest::test_the_publish_directory_is_composed_from_intellibills_root
FAILED tests/test_path_layout.py::NothingLeftInIntelliBooksTest::test_no_unexpected_path_constant_resolves_inside_intellibooks
16 failed, 67 passed, 87 subtests passed in 3.04s
```

Six of the sixteen are
`AttributeError: module 'worker.publish' has no attribute 'ARCHIVE_PATH_KEY'`, counted
with `grep -c` rather than eyeballed. Two more read for themselves:

```
AssertionError: Lists differ: ['INTELLIBOOKS_PUBLISH_DIR'] != []
  : these still point inside IntelliBooks' own folder: ['INTELLIBOOKS_PUBLISH_DIR']
```

**A reconstructed red run is weaker evidence than one taken in order**, and the reason
is worth stating rather than glossing: the tests were written against code I already had
in mind, so they cannot prove I did not shape them to what I had built. **What carries
the weight instead is section 5's mutations**, which break one property at a time from a
pristine copy and show which tests notice.

---

## 5. Mutations

Eight, through `tests/mutation_harness.py`. Every anchor `str.count()` asserted at 1
before anything was written, every diff printed, every file restored byte for byte, each
measured against the whole suite.

| # | Mutation | Expect | Result | Caught by |
|---|---|---|---|---|
| 1 | `address-is-absolute` | caught | **caught** | 3 |
| 2 | `address-uses-forward-slashes` | caught | **caught** | 2 |
| 3 | `no-existence-check` | caught | **caught** | 3 |
| 4 | `existence-check-uses-exists` | caught | **caught** | 1 |
| 5 | `outside-the-root-falls-back-to-absolute` | caught | **caught** | 1 |
| 6 | `extra-wins-over-the-address` | caught | **caught** | 1 |
| 7 | `exchange-folder-back-under-intellibooks` | caught | **caught** | 8 |
| 8 | `prose-only` | **survives** | **survived** | 0 |

**Mutation 1 is item 3 undone** and it is caught in three places, including
`test_the_item_carries_the_address_of_the_document_that_arrived`, which drives a receipt
all the way through the email route and resolves the address off the written item.

**Mutation 4 is the one worth reading.** `is_file()` becomes `exists()`, which every
test but one would accept, because a missing file answers False either way. Only
`test_a_directory_is_not_a_document` separates them. **A directory where a document
should be is exactly the state a half-finished move leaves**, and `exists()` would have
published an address pointing at it.

**Mutation 5 is the decision in section 3 undone**, replacing the refusal with
`return str(document)`. One test catches it, which is the right number: it is the only
one that puts a document outside the practice root.

**Mutation 7 is item 7 undone** and it takes eight failures across two files. The two
roots are two letters apart and both are real folders, so nothing would have failed at
run time; the suite is what notices.

**Mutation 8 confirms no guard reads prose.** A comment in `config.py` was changed and
the suite stayed at 1491.

### What mutation 7 did NOT catch, stated rather than left to be assumed

It did not fail `test_the_middle_level_is_intellibills_under_the_practice_root` or
`test_the_two_roots_are_still_two_different_folders`, the two guards described in
section 6. **That is correct and it is worth knowing why**: those two assert what the
roots themselves are, and moving the publish directory between them does not move
either root. The test that catches the substitution is
`test_the_publish_directory_is_composed_from_intellibills_root`, which reads the
assignment off `config.py`'s syntax tree, and it is in the caught list.

Full harness output, eight blocks with diffs, in
`C:\Users\PDK7\AppData\Local\Temp\claude\c--LastingImpact-receipt-capture\1d19c2e5-bffa-4afe-a492-3e0c9fabb139\scratchpad\mutations_publish.txt`.

---

## 6. The guard that was turned round

`tests/test_publish_destination.py` carried a guard written on 2026-09-09 **specifically
to stop `INTELLIBOOKS_PUBLISH_DIR` being derived from `INTELLIBILLS_ROOT` by accident**,
because the two words are two letters apart and both name real folders, so the mistake
would have shown up as a published item nobody finds. Item 7 makes that exact
substitution deliberately.

**It was turned round rather than deleted, on Paul's instruction.** It refused
`Intellibills` where `IntelliBooks` was meant; it now refuses `IntelliBooks` where
`Intellibills` is meant. **The direction changed and the protection did not.** Deleting
it because the design moved would have left the substitution unguarded in both
directions, which is the difference between a test that was updated and one that was
abandoned.

**A control was added beside it.** The child process now prints both roots and
`test_the_two_roots_are_still_two_different_folders` asserts they are different sibling
folders under the practice root. Without it, the two roots merging would have left the
guard above reading green while the distinction it protects had gone.

`tests/test_path_layout.py`'s `ALLOWED` set drops from two names to one. **That makes
the rule stronger**, in the opposite direction to the 2026-09-09 change recorded in its
own docstring: fewer constants are excused from the sweep.
`INTELLIBOOKS_ROOT` stays, because `worker/client_copy.py` composes the delivery log
folder from it at call time.

---

## 7. Which existing tests changed, and why

**Ten files, and every change is one of three kinds.**

| File | Kind | What |
|---|---|---|
| `tests/test_publish_item.py` | contract | Two picture tests replaced by four address tests and a new class for the existence check; fixture moved into the archive |
| `tests/test_publish_trigger.py` | contract | `test_the_item_carries_the_document_that_arrived` becomes `..._the_address_of_the_document_that_arrived` |
| `tests/test_stage4_client_copy.py` | contract | The reserved-key test now guards `archive_path` |
| `tests/test_publish_destination.py` | item 7 | Six path assertions, two guards, one rename, the module docstring |
| `tests/test_path_layout.py` | item 7 | `ALLOWED` and its control's name |
| `tests/test_auto_retry_cap.py` | fixture | Document written into the archive |
| `tests/test_resume_safety.py` | fixture | same |
| `tests/test_sidecar_category_keys.py` | fixture | `source_file()` writes into the archive |

**The two picture tests were replaced rather than deleted quietly.**
`test_the_document_round_trips_byte_for_byte` and
`test_the_encoded_document_is_plain_ascii` asked whether the bytes were on the item and
whether they survived JSON. Neither question exists now. Their replacement is named in
the docstring of `test_the_item_carries_no_picture_at_all`, with the superseded names
struck.

**`test_the_item_carries_the_address_of_the_document_that_arrived` is a stronger test
than the one it replaces.** The old one decoded base64 and compared it against the
bytes the route was handed, which proves a copy travelled. The new one resolves the
address and reads the file it names, which proves the address reaches the document.

**One test name was left misleading for an hour and then fixed**:
`test_the_destination_is_the_practice_root_then_intellibooks_then_the_leaf` was
asserting `Intellibills` while still saying `intellibooks` in its own name. Caught by
reading the mutation output rather than by a test.

---

## 8. The suite, and the proposed commit

| When | Result |
|---|---|
| Before | `1484 passed, 1 skipped, 1117 subtests passed` |
| After | `1491 passed, 1 skipped, 1137 subtests passed in 86.29s` |

**+7 tests and +20 subtests**, and the arithmetic is 4 + 4 + 1 - 2. Four address tests
and four existence tests in `tests/test_publish_item.py`, one root control in
`tests/test_publish_destination.py`, and two picture tests removed.

**The baseline was measured at `b21b4f2`.** `48090d0` landed between that reading and
this one and is documentation only, four markdown files and no code, checked with
`git show --stat`, so it moves neither figure. The subtests are
mostly `test_the_item_carries_no_picture_at_all`, which subtests every key on the item.

**No file is added**, so the two `git ls-files` source guards see nothing new and the
post-commit run has no blind spot to cover. It will be run anyway if you want it.

```
fix(publish): the item carries the document's address, not the document

Section 20.6 items 1 to 7, Paul's decisions of 2026-09-15. The Python worker
half only; items 8 to 17 are the front end.

build_item() stopped reading the document's bytes and setting image_base64. It
sets archive_path instead: the document's location relative to the practice
root, with backslashes, which is the form resolve_practice_path() resolves. No
drive letter and no user profile, so the same record works on another machine.
save_file() returns an absolute path and receipts.file_path stores it absolute,
so the conversion lives in archive_address(), where the address is written.

image_media_type stays: the front end needs it to tell a picture from a PDF.

The byte read was checking the document existed as a side effect, and that
behaviour does not change: an explicit is_file() check raises PublishError in
the same place, so a missing document still fails the publish and still writes
its reason to publish_events. A document outside the practice root is refused
for the same reason rather than written absolute, which is what makes "no drive
letter" true by construction. That case cannot arise in production: the one
call site is handed receipts.file_path.

INTELLIBOOKS_PUBLISH_DIR derives from INTELLIBILLS_ROOT, so the exchange folder
is Intellibills\Incoming\ and the one mkdir moved with it. Both ends are
Intellibills. Nothing creates IntelliBooks\Incoming\ any more; deleting the live
folder is Paul's.

test_publish_destination.py's guard against composing the publish directory from
the wrong root is turned round rather than deleted, with a control asserting the
two roots are still different sibling folders. Seven fixtures now publish from
inside the practice root, which is what production does.

Files: worker/publish.py, config.py, tests/test_publish_item.py,
tests/test_publish_destination.py, tests/test_path_layout.py,
tests/test_publish_trigger.py, tests/test_stage4_client_copy.py,
tests/test_sidecar_category_keys.py, tests/test_auto_retry_cap.py,
tests/test_resume_safety.py
Suggested branch: feat/console-phase0 (the current branch)

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

```
 config.py                           |  30 +++++-
 tests/test_auto_retry_cap.py        |  11 ++-
 tests/test_path_layout.py           |  17 +++-
 tests/test_publish_destination.py   | 138 +++++++++++++++++++-------
 tests/test_publish_item.py          | 181 ++++++++++++++++++++++++++++++---
 tests/test_publish_trigger.py       |  20 +++-
 tests/test_resume_safety.py         |   9 +-
 tests/test_sidecar_category_keys.py |  16 +++-
 tests/test_stage4_client_copy.py    |  25 +++--
 worker/publish.py                   | 112 ++++++++++++++++----
 10 files changed, 475 insertions(+), 84 deletions(-)
```

**Not done:** nothing committed, nothing pushed. Nothing in
`IntelliBooks-Desktop-v3.html`. `make_enriched_sidecar()` untouched.
`IntelliBooks\Incoming\` on disk not deleted, which is Paul's.

---

## 9. My own mistakes

### 9.1 The production code went in before the tests were run

Section 4. Disclosed, reconstructed, and the reconstruction's weakness stated.

### 9.2 A stale test name survived my own rewrite

`test_the_destination_is_the_practice_root_then_intellibooks_then_the_leaf` asserted
`Intellibills` and said `intellibooks`. **Found by reading the mutation output, where
the name appears in the caught list**, and not by any check. A test whose name says the
opposite of what it asserts is the shape this project keeps finding in prose beside code.

### 9.3 A bulk string replacement fired before I had read what it would hit

Repointing the six `"practice" / "IntelliBooks"` assertions was done with a blind
`str.replace()` across the file. It also changed the line inside the guard I was about
to turn round by hand, so my next edit failed to find its anchor. **No harm, because the
anchor mismatch was loud**, but it is the `str.replace()` fault `CLAUDE.md` records at
the head of `tests/mutation_harness.py`: a replacement with no count changes what it
finds rather than what you meant. The count was printed afterwards, 6 and 1, which is
the right habit applied in the wrong order.

### 9.4 Two earlier claims about the repository were incomplete

I reported the consultant session's design-document change as staged and uncommitted. It
was committed as `48090d0` during this work, so that state no longer describes anything.
And my `b21b4f2` sits on `68b46b6` rather than on `52cc007`, because the consultant
session had already landed a commit between them. Neither changes any result here; both
are corrected because I stated them.

---

## 10. Flags

### 10.1 Six fixtures still pin the publish directory under a folder called IntelliBooks

`tests/resolution_fixtures.py`, `tests/test_embedded_image_pipeline_version.py`,
`tests/test_failure_path_engine.py`, `tests/test_sidecar_category_keys.py`,
`tests/test_status_counts_from_db.py` and `tests/test_delivery_log.py` set
`config.INTELLIBOOKS_ROOT = self.path / "IntelliBooks"` and then
`config.INTELLIBOOKS_PUBLISH_DIR = config.INTELLIBOOKS_ROOT / "Published"`.

**They pin the constant explicitly, so they exercise the code correctly and the suite is
green.** What they now model is a tree that production does not have. It is cosmetic,
inside a temp directory, and it is a flag rather than a fix because the brief names none
of them and twelve lines of churn across six files is not obviously worth it.

**The obvious fix if you want it:** point those fixtures at a folder named
`Intellibills`, two lines each. **I would leave them** until something depends on the
distinction, and then move them all at once.

### 10.2 `tests/live_paths.py` counts the config Path constants and the count did not move

It says "twenty-one of the twenty-two Path constants land in temp" and asserts the count
next door in `tests/test_conftest_redirect.py`. **Item 7 changed which root
`INTELLIBOOKS_PUBLISH_DIR` hangs off and not how many constants there are**, so the
figure is still right and no change was needed. Recorded because a reader checking that
file for fallout would otherwise have to work it out.

---

## 11. Confidence

**High that items 1 to 6 do what section 1 says**, resting on tests I drove in both
directions and on six mutations that each broke one property and were each caught, plus
one prose mutation that was not. Not on the reconstructed red run, for the reason section
4 gives.

**High that item 7 moved the folder and nothing else.** It rests on mutation 7 taking
eight failures across two files when reversed, and on `test_the_destination_folder_is_
created_at_import` asserting the new folder is made by a real import in a fresh process
against a practice root the test controls.

**High that the address resolves back to the document**, resting on
`resolve_practice_path()` being the resolver under test rather than a second join
written in the test, and on the bytes being compared after the round trip.

**Medium that no other caller anywhere passes `build_item()` a document outside the
practice root.** It rests on a syntax-tree enumeration of `build_item()` call sites,
re-run after the change rather than quoted from before it: **18 in total**, 17 across
three test files and one in `worker/publish.py`. ~~12 in total, 11 in three test
files~~ **That was the count before my own test changes added six, and quoting it would
have been a figure this work had already moved.** **It is medium rather than high
because it enumerates callers of `build_item()` and not callers of
`publish_receipt()`**, which is the function a new caller would actually reach for, and
I did not enumerate those.

**Low, and flagged as speculation, on whether the front end half lands cleanly against
this.** The contract is one key name and one path form, both pinned by tests here, but
the other end is written by a session that cannot see this file and I have read none of
it.
