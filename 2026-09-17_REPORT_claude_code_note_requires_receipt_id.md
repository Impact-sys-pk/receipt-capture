# Report: a resolution note must carry a receipt_id

Claude Code, 2026-09-17. Worked from
`PROMPT_claude_code_2026-09-17_note_requires_receipt_id.md`, which is Paul's
decision of 2026-09-17. It replaces what step 10aw was scheduled to do.

**`2026-07-25_BUILD_STATUS.md` and `2026-07-25_CONSOLE_DESIGN.md` were not
touched.**

**Files changed:** `worker/resolution/service.py`,
`tests/test_attached_document_reach.py`, `tests/test_resolution_backfeed.py`,
and `tests/test_note_requires_receipt_id.py` added.

**Commit:** `e8ea1e7`, made on Paul's approval. Section 9.

---

## The headline, and it is not in the brief

**Six existing tests asserted the behaviour this change removes.** Five went red
and a sixth started passing for a reason its name does not describe. The brief
named none of them.

They are not a reason to stop: the brief's decision is explicit and the tests
assert exactly the thing decided against. **But four of them could not be kept
even in a weakened form**, because their fixture is a note the contract no longer
admits. Section 4 has the whole account.

---

## 1. The callers of `find_receipts_by_filename()`

**Report question 1, enumerated by me from the syntax tree, not grepped.** A grep
returns the name from comments and docstrings, and this project keeps superseded
wording beside every correction: the `ResolutionNote` field comment named the
fallback in prose and `_receipt_for_note()`'s docstring described it, so a text
search would have read the tombstone as a use.

**Before the change:**

| Where | |
|---|---|
| `worker/resolution/service.py:1891` in `_receipt_for_note()` | the only production caller |
| `tests/test_attached_document_reach.py:353` | a test of the method's own contract |

**Defined once**, at `worker/database/repository.py:242`.

**After the change: no production caller at all.** The one test caller remains,
`test_the_lookup_itself_is_left_alone_and_still_returns_everything`, which drives
the method directly and still passes.

**Whether the method goes too is a finding and not mine to decide**, which is
what the brief says. It is reported in section 6.1 with the argument both ways.

---

## 2. What a note with no `receipt_id` now produces

**Report question 2, quoted as it appears in the file**, taken from a real run of
`app._consume_resolution_notes()` rather than composed here. The note lands in
`Intellibills\Resolutions\failed\` with this beside it:

```
outcome: error
receipt_id: 
reason: 'receipt_id' is required: it is the only thing that says which receipt this note is about
```

**The `receipt_id:` line is blank and that is right.** `apply_resolution_note()`
fills it from `note.get("receipt_id")` before parsing, so a note that has none
shows none. A person reading this sees an empty field and a reason naming that
field, which is the same thing said twice.

**Before**, such a note reached `outcome: not_found` with
`no receipt matched by id or by review filename`, which named two ways of
matching when only one existed, and did so only after the note had been through
the whole of 12.3 step 2.

---

## 3. Anything else that reads `original_review_files`

**Report question 3.** Enumerated the same way, over production and tests.

**In production, six sites before the change and four after:**

| Where | What it does | After |
|---|---|---|
| `service.py:350` | the field declaration | stays |
| `service.py:444` | the contract check, `raw.get("original_review_files")` | stays |
| `service.py:461` | carried onto the note | stays |
| `service.py:2824` | named in the `not_found` message | stays |
| `service.py:1887` | the fallback's loop | **gone** |
| `service.py:1925` | the ambiguity log line | **gone** |

**So the consultant session's "none beyond the contract check and the two message
strings" is right about the ones that survive, and it counted five where the
field is touched six times.** The sixth is the declaration itself, which is
easily read past. Nothing else reads it anywhere, in production or in tests.

**One of the "two message strings" was inside the code being removed.**
`service.py:1925` is the ambiguity log, which the brief lists for deletion in the
same paragraph. The pair that survives is at `service.py:2823-2826`, both in
`apply_resolution_note()`'s `not_found` branch, and both are untouched as
instructed.

**Flagged, and then decided in the same exchange.**
`error_detail="no receipt matched by id or by review filename"` named a way of
matching that no longer exists. **Paul chose `"no receipt matched this id"`,
2026-09-17**, and it is in this commit. Section 6.2.

---

## 4. The six existing tests

**None of these is in the brief.** They are the cost of the decision, and they
are reported first because a reader checking this change should not have to
discover them from a diff.

### Four in `tests/test_attached_document_reach.py`, all of one class

`TheFilenameFallbackTest` was written for amendment 345, Paul's decision of
**2026-09-12**: an attached document is not something a back-feed note can be
about, so it is excluded from the filename fallback's candidates. **The exclusion
lived inside the loop this change deletes.**

| Test | What happened |
|---|---|
| `test_a_note_with_no_receipt_id_does_not_match_an_attached_document` | removed |
| `test_it_still_matches_an_ordinary_receipt` | removed |
| `test_the_ambiguity_refusal_still_fires_on_two_real_candidates` | removed |
| `test_two_candidates_where_one_is_attached_is_a_match_and_not_a_refusal` | removed |
| `test_the_lookup_itself_is_left_alone_and_still_returns_everything` | **kept**, its subject still exists |
| `test_a_note_carrying_a_receipt_id_is_unaffected` | **kept**, still passes unchanged |

**Each of the four built its note with `"receipt_id": None`**, which
`parse_resolution_note()` now refuses, so none could be kept even weakened: the
fixture is a note the contract no longer admits.

**They are not deleted silently.** The class keeps a docstring naming all four
and saying why they went, which is this project's convention for a removed
thing, and it records that amendment 345 was five days old and was never wrong:
what removed it was the discovery that the path it guarded could not run.

### Two in `tests/test_resolution_backfeed.py`

- **`test_a_null_receipt_id_is_matched_on_the_review_filenames` went red**, which
  is correct: it asserted the fallback resolving a note. Rewritten as
  `test_a_null_receipt_id_is_refused_by_the_contract`, **keeping its fixture**,
  which matches `R-1.PDF` against a receipt named `r-1.pdf`. That fixture is the
  whole point: it is a note the fallback really would have matched, so the test
  still cannot pass by accident.
- **`test_an_ambiguous_filename_match_is_not_a_match` stayed green and stopped
  meaning anything.** It asserts the note lands in `failed\`, and a note refused
  by the contract also lands in `failed\`. Rewritten as
  `test_two_receipts_sharing_a_filename_no_longer_matter`, asserting on the
  `.error.txt` instead: the reason must name `receipt_id` and must **not** say
  "ambiguous".

**The second is the one worth noticing.** A test that keeps passing while its
subject is deleted is worse than one that fails, because nothing tells you.

---

## 5. Evidence

### 5.1 Red before green, and two goes at making it discriminate

`tests/test_note_requires_receipt_id.py`, 20 tests, of which 19 were written
before the mutation run and the twentieth holds Paul's wording decision below.
Against the unchanged code,
**`11 failed, 10 passed`**:

```
FAILED ...::TheContractRequiresTheIdTest::test_a_note_with_no_receipt_id_is_refused
FAILED ...::TheContractRequiresTheIdTest::test_a_note_with_the_key_absent_altogether_is_refused
SUBFAILED(receipt_id='')    ...::test_an_empty_string_is_refused_too
SUBFAILED(receipt_id='   ') ...::test_an_empty_string_is_refused_too
FAILED ...::TheContractRequiresTheIdTest::test_the_reason_names_the_field_and_says_why
FAILED ...::TheFallbackIsGoneTest::test_a_note_that_the_fallback_would_have_matched_is_now_refused
FAILED ...::TheFallbackIsGoneTest::test_the_receipt_is_untouched_by_the_refused_note
FAILED ...::TheErrorFileAPersonOpensTest::test_the_error_file_says_which_field_and_why
FAILED ...::NothingMatchesOnAFilenameTest::test_it_does_not_read_original_review_files
FAILED ...::NothingMatchesOnAFilenameTest::test_it_has_no_loop_left
FAILED ...::NothingMatchesOnAFilenameTest::test_it_makes_no_call_that_matches_on_a_filename
```

**That red took three attempts, and the first two were tests that could not
fail.** The brief warned about exactly this and I still had to run it to find
out:

1. **First fixture: a note carrying `filed_path`.** Such a note is refused anyway
   when that path is not on disk, so against the old code it produced
   `outcome: error` whatever the fallback did.
   `test_the_receipt_is_untouched_by_the_refused_note` passed for a reason with
   nothing to do with this change. **Fixed by using the settle shape**, a note
   with no `filed_path`, which today really does resolve the receipt.
2. **Second fixture: a receipt with no extraction.** A settle note against one
   returns `not_found` with "This receipt has no extraction to correct", so the
   receipt was still untouched and the test still could not fail. **Fixed by
   using `TempEnvironment.seed()`**, which writes a receipt **and** a seed
   extraction, and whose `filename` is `r-1.pdf`, exactly what
   `original_review_files` names.

**Both were found by running a probe and printing the outcome**, not by reading.
The first probe printed `filed_path does not exist on disk`; the second printed
`not_found | This receipt has no extraction to correct`. Neither would have been
visible from the pass/fail line.

**After the change: `19 passed, 6 subtests passed`**, and `20 passed` once
the wording test was added.

### 5.2 The whole suite, and what it caught

**With the change and before the existing tests were rewritten:**
`5 failed, 1579 passed`. Those five are section 4's. **After rewriting them:
`1580 passed, 1 skipped, 1191 subtests passed`**, and `1581 passed` with the
wording change and its test.**

**The suite is what found five of the six**, and reading found the sixth: it
passed, so I checked why, because its name promised something the code could no
longer do.

### 5.3 Mutations

Run with `tests/mutation_harness.py`, which refuses an anchor that does not match
exactly once, applies to a pristine copy, runs the **whole** suite, restores and
asserts the restore is byte for byte. All five anchors were counted before the
run rather than discovered by a refusal mid-run.

| Mutation | What it does | Outcome |
|---|---|---|
| `contract-accepts-a-missing-id` | the check is deleted | **caught**, 7 |
| `the-fallback-is-back` | the check is deleted **and** the lookup falls back | **caught**, 12 |
| `the-reason-does-not-name-the-field` | the reason becomes generic | **caught**, 3 |
| `review-files-stop-being-carried` | the field parses but is not carried | **caught**, 1 |
| `prose-only` | rewords one docstring line | **survived**, as required |

The brief named the first two. The other three are one per thing the change
claims: that the reason is readable, that `original_review_files` survives in the
contract, and that a comment is only a comment.

**`the-fallback-is-back` had to be both halves, and that is the point of writing
it as a callable.** Deleting only the check leaves a note that parses and then
finds nothing; restoring only the fallback leaves it unreachable, which is the
state this change found. Either alone measures nothing. It is caught 12 times,
and the three that matter most are the source guards:

```
FAILED ...::NothingMatchesOnAFilenameTest::test_it_makes_no_call_that_matches_on_a_filename
FAILED ...::NothingMatchesOnAFilenameTest::test_it_does_not_read_original_review_files
FAILED ...::NothingMatchesOnAFilenameTest::test_it_has_no_loop_left
```

**And one of the twelve is a rewritten existing test**, which is the evidence
that section 4's rewrite discriminates rather than merely passing:

```
FAILED tests/test_resolution_backfeed.py::UnknownReceiptTest::test_a_null_receipt_id_is_refused_by_the_contract
```

**The restored fallback is a simplified one**, without the bank-attachment
exclusion or the ambiguity logging, because what the mutation measures is whether
the shape can come back at all. A fuller restoration would be caught by strictly
more, so this is the weaker and therefore the honest version.

**`review-files-stop-being-carried` is caught by exactly one test in 1,580**, and
that is the "what must not change" list working: `original_review_files` stays in
the contract, and only
`TheContractStillCarriesReviewFilesTest::test_it_is_still_carried_onto_the_note`
would notice if it quietly stopped.

**The mutation run predates the wording change**, which added one test and
touched one string; nothing in the set measures that string, so the results stand
as run and are not re-quoted.

**Every failure across all five is in `tests/test_note_requires_receipt_id.py`
and `tests/test_resolution_backfeed.py`**, the new file and the one whose tests
were rewritten. The four tests removed from
`tests/test_attached_document_reach.py` appear in no catch list, which is right:
they are gone.

---

## 6. Flags. Not fixed.

### 6.1 `find_receipts_by_filename()` now has no production caller

Section 1 enumerates it: one production caller before, none after, one test
caller that drives the method directly.

**The brief says explicitly that whether it goes too is a finding to report
rather than a decision to take.** Both arguments, briefly:

- **For removing it:** this project deletes rather than leaves dead, and
  `worker/filing.py`'s `file_receipt()` tombstone gives the reason in as many
  words: a function that does a thing is one import away from doing it again.
  The same argument was used to delete `find_by_transaction()` at 10f.23 and
  `add_validation_note()` at step 9.
- **For keeping it:** it is a general-purpose lookup with an honest contract, and
  the console at section 8 is not built. A search by filename is an ordinary
  thing for an operator's screen to want.

**The obvious fix if it goes is to delete the method and the one test that drives
it**, in one change, leaving a tombstone naming both.

### 6.2 ~~Flag~~ An error message named a way of matching that does not exist. FIXED, Paul's wording

**Raised as a flag and decided in the same exchange, 2026-09-17.** It is kept as
a numbered section rather than moved, because the flag is the reason the decision
was asked for.

`apply_resolution_note()`'s `not_found` branch read:

```python
error_detail="no receipt matched by id or by review filename",
```

**There is no matching by review filename any more.** The brief listed "the two
message strings that name it" under what must not change, and also criticised
this exact string in its own description of the old behaviour. **I flagged the
tension rather than resolving it, because a message a person reads is Paul's to
word.**

**Paul chose `"no receipt matched this id"`, 2026-09-17**, and it is in this
commit. The person reading the `.error.txt` in `Resolutionsailed\` is deciding
whether the pipeline or Desktop is at fault, and a reason naming a path that does
not exist sends them looking for it.

**Held by a test rather than by a comment.**
`test_the_not_found_reason_names_one_way_of_matching_and_not_two` asserts the
string exactly and asserts the word "filename" is absent, because nothing else in
1,581 tests would notice it drifting back.

**The companion string at `service.py:2823-2824` is unchanged** and should not
change with it: it prints the note's `receipt_id` and its `original_review_files`
verbatim, which is evidence rather than an explanation, and it is exactly what
somebody needs when a note fails.

### 6.3 A five-day-old decision became unreachable

Amendment 345 of 2026-09-12 decided that an attached document is not a candidate
for a back-feed note, and put the exclusion in the caller rather than the query,
deliberately. **That code is gone**, because the loop it lived in is gone.

**Nothing is wrong and no change is recommended.** It is recorded because the
decision was correct when taken and a reader finding it in the design document
should be able to find out what happened to it. **The consultant session owns the
amendment recording that**, per rule 2 of the brief.

---

## 7. Mistakes I made, disclosed

1. **My first two fixtures produced tests that could not fail**, in the exact way
   the brief warned about. Section 5.1 has both, how each was found, and what
   each was replaced with. **The brief's sentence "without a genuinely matching
   filename in the fixture the test cannot tell the fallback was removed" was
   necessary but not sufficient**: the filename matched in all three versions;
   what defeated the first two was the note failing for an unrelated reason
   further down.
2. **My first version of the source guard over `_receipt_for_note()` asserted
   more than the brief asked**, adding "it has no loop left" and "it does not
   read `original_review_files`" to "it makes no call that matches on a
   filename". I kept those two: they are cheap and they describe the function
   this change leaves behind. Recorded as an addition rather than presented as
   the brief's requirement.

---

## 8. Confidence

- **That a note with no `receipt_id` is refused with a readable reason: high.**
  The `.error.txt` in section 2 is quoted from a real consume run, not composed.
- **That the fallback is gone rather than merely unused: high**, and it rests on
  a fixture where it demonstrably would have worked: the third version of that
  fixture resolves the receipt against the old code, which is what makes the test
  able to fail.
- **That no production caller of `find_receipts_by_filename()` remains: high**,
  enumerated from the syntax tree over 57 production files and 100 test files,
  printed whole.
- **That nothing else reads `original_review_files`: high**, same enumeration,
  and it counts the field declaration, the keyword argument, the string literal
  and the attribute loads separately so a site cannot hide behind a spelling.
- **That the fallback could never have run in production: medium, and it is not
  my reading.** The brief asserts it from IntelliBooks Desktop, which is not in
  this repository and which I have not opened. What I verified is the pipeline
  half: nothing here writes a note into `Resolutions\`. **The Desktop half I have
  taken on the brief's word.**
- **That removing it breaks nothing outside the tests in section 4: medium.** The
  suite is green and the enumeration is complete for this repository. **A note
  written by some other producer, or a note already sitting in
  `Resolutions\` right now with no id, would now be refused where before it might
  have applied.** The brief says every note in `processed\` and `failed\` on
  Paul's machine carries an id; I did not check that myself.

---

## 9. The commit. Made on 2026-09-17, on Paul's approval.

**`e8ea1e7` on `feat/console-phase0`, four files, 551 insertions and 131
deletions.** Nothing pushed, no branch created.

**The suite was run again afterwards**, because this adds a file and two source
guards sweep the git-tracked set rather than the working tree:
**`1581 passed, 1 skipped, 1191 subtests passed in 114.71s`**.

**Two docs commits landed from the consultant session while this was being
built**, `6f55fdb` and `8f7aac4`, which committed the four reports and two briefs
from the 2026-09-16 work and added steps 10bd and 10be. Checked before
committing; neither touches anything here.

**One difference from the message proposed before the wording decision**: a
paragraph naming `"no receipt matched this id"` and saying Paul chose it. Section
6.2.

The message as committed:

```
fix(resolution): a note must carry a receipt_id, and the filename fallback goes

parse_resolution_note() refuses a note with no receipt_id, the way it already
refuses a missing resolved_at, naming the field in a reason a person reads in
the .error.txt beside the note in Resolutions\failed\. Before, such a note
failed further in as outcome: not_found with "no receipt matched by id or by
review filename", which named two ways of matching when only one existed.

_receipt_for_note() keeps its receipt_id lookup and loses the rest: the loop
over original_review_files, both find_receipts_by_filename() calls, the
bank-attachment exclusion inside that loop and the ambiguity guard after it.

Removing it is not a judgement call. It was reached only when receipt_id was
falsy and no producer sends a note without one, and if it had been reached it
could not have matched: original_review_files carries the tray item's name,
{receipt_id}.json, and receipts.filename holds the document's original
filename. Flagged on 2026-09-09 and written into the ResolutionNote field
comment the same day, where it stood for eight days while step 10aw was
scheduled to fix a suffix problem in a path that could not run.

original_review_files stays in the contract, still parsed, still refused when
it is not a list of strings, and still named in the not_found message.

Six existing tests asserted the removed behaviour. Four in
test_attached_document_reach.py built their note with receipt_id: null and
could not be kept in any form; the class records all four by name and why they
went, and keeps the two whose subject still exists. Two in
test_resolution_backfeed.py are rewritten, keeping the fixtures that reached
the fallback, and the one that had started passing for the wrong reason now
asserts on the .error.txt instead of on the folder.

Paul's decision of 2026-09-17. It replaces what step 10aw was scheduled to do.

Files: worker/resolution/service.py, tests/test_note_requires_receipt_id.py,
tests/test_attached_document_reach.py, tests/test_resolution_backfeed.py

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

**Four files.** This report and this brief are untracked and are not in the
commit.
