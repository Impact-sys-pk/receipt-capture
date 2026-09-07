# Report: step 10f, the six duplicate sub-steps, plus amendment 1

**Written 2026-09-07, 19:53 BST (18:53 UTC), by the implementation session in Claude Code.**
**Branch `feat/console-phase0`.**
**Brief: `PROMPT_claude_code_2026-09-07_step10f_duplicates.md`, amended mid-run at 19:35 BST.**

**All six sub-steps are built, and amendment 1 with them.** 10f.18, 10f.19, 10f.20, 10f.21, 10f.22
and 10f.23, plus `find_statement_by_hash()`.

---

## 1. What landed

**Seven commits, one per sub-step, none pushed.**

| Commit | Sub-step | What |
|---|---|---|
| `6994d3c` | 10f.23 | Two dead duplicate lookups go |
| `0157561` | 10f.18 | The hash lookup is scoped to the client |
| `55d0595` | 10f.19 | The semantic lookup is scoped to the client |
| `8e77e01` | amendment 1 | The statement hash lookup takes the client |
| `af01ca8` | 10f.20 | The embedded-image path checks the match was filed |
| `0095891` | 10f.21 | An inbox duplicate is moved rather than deleted |
| `274dda1` | 10f.22 | All four arrival routes reach the same verdict |

**The suite.**

| When | Result |
|---|---|
| Before, the committed tree at `bd8e137` | **615 passed, 379 subtests** |
| After all seven, at `274dda1` | **639 passed, 408 subtests** |

**The before figure was measured at 19:02 BST on the tip before any edit**, rather than carried
forward. 24 new tests and 29 new subtests, all in `tests/test_step10f_duplicates.py` and the
rewritten `tests/test_capture_inbox_cleanup.py`.

**Nothing out of scope was touched.** No `IntelliBooks\Inbox\`, nothing about where or when a
receipt is filed, nothing in 10f.24, and none of `get_client_directory()`, `file_receipt()` or
`make_enriched_sidecar()`, so section 18.2b's freeze stands.

---

## 2. Every call site, enumerated rather than counted

**All searches ran over the 109 `.py` files found by walking the repository excluding `.venv`,
`.history` and `.git`, or with `git grep`, which does not see `.history` at all.**

### `find_by_hash()`, before the change

```
./app.py:312:    left behind is found by `find_by_hash()` on the next poll, is not
./app.py:1104:                    existing = repo.find_by_hash(file_hash)
./app.py:1304:            existing = repo.find_by_hash(intake.file_hash)
./app.py:1473:                existing = repo.find_by_hash(file_hash)
./tests/test_capture_inbox_cleanup.py:84:  existing_receipt_id = repo.find_by_hash(intake.file_hash)
./tests/test_inbox_processed_move.py:5:the original in `Receipt Inbox\{CODE}\`. On the next poll `find_by_hash()` finds
./worker/database/repository.py:30:    def find_by_hash(self, file_hash: str) -> Optional[str]:
```

**Three production call sites, all in `app.py`, which is the brief's figure exactly.** `:312` and
the `test_inbox_processed_move.py` line are prose. **The brief did not mention the fourth caller, in
`tests/test_capture_inbox_cleanup.py`**, which is fair since it named that file as needing rewriting
for a different reason.

**All three hold the client at the point of the call, established by reading each:**

| Call site | Where the client comes from |
|---|---|
| Embedded-image path | `client_id`, from `resolve_client_info(email_from)` resolved once per message above the loop |
| Folder-intake path | `intake.client_id`, from the item's own sidecar |
| Attachment path | `client_id`, from `resolve_client_info(email_from)` resolved once per message above the loop |

**So `client_id` is a required positional rather than a defaulted keyword**, and a test asserts the
signature so a future call site cannot quietly keep asking the unscoped question.

**One hoist was needed.** The folder-intake path computed `receipt_client_id` and `receipt_firm_id`
*after* the hash check. They are now computed before it, so the lookup asks about the same client the
receipt row will name. Nothing else moved.

### `find_by_transaction_loose()`

```
./worker/database/repository.py:616:    def find_by_transaction_loose(...)
./worker/extraction_pipeline.py:163:        dup = repo.find_by_transaction_loose(
```

**One caller, as the brief said**, and `client_id` was already a parameter of the function that
contains it, `process_extraction_result()`. Nothing new is looked up.

### `find_statement_by_hash()`, amendment 1

```
2026-07-25_CONSOLE_DESIGN.md:1280: (prose)
app.py:1241:                if repo.find_statement_by_hash(intake.file_hash):
worker/database/repository.py:138:    def find_statement_by_hash(self, file_hash: str) -> Optional[str]:
```

**One caller, as the amendment said**, and it holds `intake.client_id`.

### `_remove_inbox_pair()` and `_move_inbox_pair_to_processed()`, before 10f.21

```
./app.py:271:def _remove_inbox_pair(intake) -> None:
./app.py:308:def _move_inbox_pair_to_processed(intake) -> None:
./app.py:1241:                    _remove_inbox_pair(intake)
./app.py:1308:                    _remove_inbox_pair(intake)
./app.py:1421:                _move_inbox_pair_to_processed(intake)
./tests/test_capture_inbox_cleanup.py:88:                    app._remove_inbox_pair(intake)
./tests/test_capture_inbox_cleanup.py:151:                    app._remove_inbox_pair(intake)
./tests/test_inbox_processed_move.py:4: (prose)
```

**Two production callers, as the brief said**, the duplicate-statement path and the
duplicate-receipt path, plus the two direct calls in the test file the brief said to rewrite.

### The two dead functions, 10f.23

`git grep` over every tracked file, plus a check for dynamic access:

```
--- find_by_transaction_no_date ---
2026-07-25_CONSOLE_DESIGN.md:392   (amendment 137, prose)
2026-07-25_CONSOLE_DESIGN.md:2708  (sub-step 10f.23, prose)
worker/database/repository.py:50   (the definition)
--- find_by_transaction, excluding _loose and _no_date ---
2026-07-25_CONSOLE_DESIGN.md:392   (prose)
2026-07-25_CONSOLE_DESIGN.md:2708  (prose)
worker/database/repository.py:43   (the definition)
--- getattr(...) on either name, or on repo ---
(no matches)
```

**Definitions only. No caller in production, none in `tests\`, and no dynamic access.** The brief's
claim held.

---

## 3. Red before green, per sub-step

**Every sub-step had failing output before its change.** Quoted rather than described.

**10f.23**

```
SUBFAILED(method='find_by_transaction') ...::test_neither_dead_transaction_lookup_is_on_the_repository
SUBFAILED(method='find_by_transaction_no_date') ...::test_neither_dead_transaction_lookup_is_on_the_repository
2 failed, 2 passed
```

**10f.18**

```
FAILED ...::HashLookupIsScopedToTheClientTest::test_an_attachment_row_whose_receipt_is_gone_matches_nobody
FAILED ...::HashLookupIsScopedToTheClientTest::test_another_clients_identical_file_is_not_a_duplicate
FAILED ...::HashLookupIsScopedToTheClientTest::test_the_client_is_required_rather_than_defaulted
FAILED ...::HashLookupIsScopedToTheClientTest::test_the_processed_attachments_query_is_scoped_too
FAILED ...::HashLookupIsScopedToTheClientTest::test_the_same_client_resending_is_still_a_duplicate
5 failed, 2 passed
```

**10f.19**

```
E   TypeError: Repository.find_by_transaction_loose() got an unexpected keyword argument 'client_id'
FAILED ...::SemanticLookupIsScopedToTheClientTest::test_another_clients_identical_transaction_is_not_a_duplicate
FAILED ...::SemanticLookupIsScopedToTheClientTest::test_it_is_scoped_on_the_no_date_branch_too
FAILED ...::SemanticLookupIsScopedToTheClientTest::test_the_client_is_required_rather_than_defaulted
FAILED ...::SemanticLookupIsScopedToTheClientTest::test_the_same_client_buying_it_twice_is_still_caught
4 failed, 7 passed
```

**Amendment 1**

```
E   TypeError: Repository.find_statement_by_hash() takes 2 positional arguments but 3 were given
FAILED ...::StatementHashLookupIsScopedToTheClientTest::test_another_clients_identical_statement_is_not_a_duplicate
FAILED ...::StatementHashLookupIsScopedToTheClientTest::test_the_client_is_required_rather_than_defaulted
FAILED ...::StatementHashLookupIsScopedToTheClientTest::test_the_same_client_resending_is_still_a_duplicate
3 failed, 11 passed
```

**10f.20**

```
E   AssertionError: 'is_recorded_and_filed' not found in
    '                    existing = repo.find_by_hash(file_hash, client_id)\n
                         if existing:\n
                         logger.info(f"hash duplicate of {existing}, skipping embedded image {filename}")'
    : the find_by_hash call at app.py:1106 treats a match as a duplicate without checking it was ever filed
E   AssertionError: 0 != 1 : the embedded path skipped on a hash match against a receipt that was
    never filed, so the operator's resend produced nothing at all
2 failed, 2 passed
```

**10f.21**

```
E   AssertionError: False is not true : duplicate.pdf was deleted rather than moved into Processed\
E   AssertionError: False is not true : stmt_dup.pdf was deleted rather than moved into Processed\
E   AssertionError: True is not false : _remove_inbox_pair() is back. Nothing in the inbox is
    deleted; _move_inbox_pair_to_processed() is the one disposal and it moves.
4 failed, 1 passed
```

**10f.22 could not be red as a whole**, because it is the acceptance criterion for the four before it
and those had already landed. **Its three-route disagreement was red in a different sense**: on its
first run, two of its four tests failed and both failures were the test's own, described in section 7.
The mutations below are what stand in for its red run.

---

## 4. The mutations

Each applied to a pristine copy of the committed file, the **whole** suite run, then restored and
asserted byte for byte. Script: `scratchpad/mutate5.py`.

| # | Mutation | Suite | Caught by |
|---|---|---|---|
| A | `find_by_hash()` ignores the client again | 6 failed, 637 passed | `test_another_clients_identical_file_is_not_a_duplicate`, `test_the_processed_attachments_query_is_scoped_too`, and `test_another_clients_copy_is_a_duplicate_on_no_route` on **all four routes** |
| B | `find_by_transaction_loose()` ignores the client again | 2 failed, 637 passed | `test_another_clients_identical_transaction_is_not_a_duplicate`, `test_it_is_scoped_on_the_no_date_branch_too` |
| C | `find_statement_by_hash()` ignores the client again | 1 failed, 638 passed | `test_another_clients_identical_statement_is_not_a_duplicate` |
| D | The embedded path drops the `is_recorded_and_filed()` guard | 2 failed, 638 passed | `test_an_unfiled_hash_match_is_reprocessed_rather_than_skipped` and the source guard, naming `app.py:1108` |
| E | The duplicate-**receipt** path deletes again | 4 failed, 637 passed | Both `test_a_duplicate_receipt_is_kept_in_processed` and the unlink guard, plus `test_the_disposal_differs_and_nothing_is_lost` on the phone and Add Receipts routes |
| F | The duplicate-**statement** path deletes again | 2 failed, 637 passed | `test_a_duplicate_statement_is_kept_in_processed` and the unlink guard |

**All six caught, each by tests naming the property it broke.** All six restored byte for byte,
asserted by the harness and confirmed with `git status`.

---

## 5. What `tests/test_capture_inbox_cleanup.py` now asserts

**It was rewritten against the new behaviour rather than made to pass**, and it asserts strictly more
than it did.

**What it used to do.** Both tests called `app._remove_inbox_pair(intake)` directly and asserted the
image and its sidecar were gone from disk. That function was the subject and it no longer exists.

**What it does now.** Both tests drive a real `app.process_once()`, so they cover the **two callers**
as well as the move itself. The old direct call could not have caught a caller that deleted instead of
moving, because it never ran a caller.

Five assertions per case, in `assert_moved_to_processed()` and around it:

1. The original is **gone from the inbox folder**, so it is not reprocessed on the next poll.
2. Its sidecar is gone from the inbox folder too.
3. Both are **present in `Processed\`**, under the same stem, so the pair is intact.
4. The **bytes that arrived are the bytes that were kept**, read back and compared.
5. The duplicate is still recognised: **no second receipt or statement row**, and for the receipt
   case **the extractor was not called at all**, which is a real OpenAI call.

Plus a third class, `TheDeletingFunctionIsGoneTest`, with three guards:

- `_remove_inbox_pair()` is gone.
- `_move_inbox_pair_to_processed()` is still there, so the first guard cannot be satisfied by
  deleting both.
- **Every `.unlink()` in `app.py` is enumerated** and matched against a named list of the three that
  are legitimate, so a delete coming back under another name has to be looked at.

**One correction to that file belongs to 10f.18 rather than 10f.21, and is disclosed as such.** Its
first test seeded a receipt for `CLIENT001` but wrote a sidecar of `{"type":"capture"}`, which names
no client. The intake therefore resolved to no client, and the scenario was a duplicate **only
because `find_by_hash()` ignored the client**. The sidecar now names `CLIENT001`. The setup was
corrected; the subject was not.

---

## 6. 10f.22: the routes, and the verdict each returned

**Four routes are driven, where the brief named three.** Email attachment, embedded image, phone and
**Add Receipts**. The embedded-image path is a fourth **code path** rather than a fourth route: an
iOS share button puts the image in the message body. **It is also the one 10f.20 had to bring into
line**, so driving only three would have left the one that was actually different untested.

**Printed by the tests rather than transcribed by me:**

```
10f.22 verdicts, one filed receipt already on record:
  email attachment   verdict=duplicate  disposal=INBOX.Duplicates
  embedded image     verdict=duplicate  disposal=INBOX.Duplicates
  phone              verdict=duplicate  disposal=Processed\
  Add Receipts       verdict=duplicate  disposal=Processed\

10f.22 verdicts, nothing on record:
  email attachment   verdict=processed  disposal=INBOX.Processed Receipts
  embedded image     verdict=processed  disposal=INBOX.Processed Receipts
  phone              verdict=processed  disposal=Processed\
  Add Receipts       verdict=processed  disposal=Processed\
```

**The verdict is identical on all four and only the disposal differs**, which is 10f.22 exactly. The
second block is the control: every other assertion in that class is that a route said "duplicate",
and without it they would all pass against a pipeline that called everything a duplicate.

**A fourth test drives the cross-client case through the routes** rather than through the queries: a
receipt filed for client A, and client B's byte-identical document arriving by each route in turn.
All four now produce a receipt for B. Before this brief all four credited it to A and produced
nothing for B.

---

## 7. My own mistakes

**Five, all caught by my own runs, three of them in one test class.**

1. **My move stub was not faithful to the mailbox.** It recorded every
   `move_email_to_folder()` call, so `moved_to[-1]` reported the embedded path leaving a duplicate in
   `INBOX.Processed Receipts`. **Reading `worker/email/reader.py` settled it**: the real function
   copies, flags deleted and expunges, so a second move of the same uid has nothing to copy and
   returns False. The stub now models that, and the email does land in `INBOX.Duplicates`. **The
   finding was half right, and the real half is flag 1 below.**
2. **Two tests ran four routes in sequence against one database over one document.** In the
   "nothing on record" case the first route filed the very receipt the second was asked about, so
   three routes were reported as disagreeing when they were right and the test was wrong. Each route
   now gets its own document there; in the "already on record" case they still share one, which is
   the case 10f.22 is about.
3. **The same fault again in the cross-client test**, for the same reason. Each route now gets its
   own `TempEnvironment`, because to ask whether A's receipt blocks B, B's document must be
   byte-identical to A's, and then two routes in sequence make the second one look at B's own
   duplicate.
4. **My first unlink guard forbade `.unlink()` anywhere in `app.py`** and went red on three
   legitimate ones: two pipeline-lock removals and backup rotation, all three deleting something the
   pipeline made itself. Narrowed to a named exception list, so a fourth has to be recorded rather
   than covered by a rule.
5. **My mutation script reverted both `_remove_inbox_pair()` callers at once.** The two blocks are
   byte-identical, and `str.replace()` has no count, so mutation E changed both and mutation F then
   found nothing left to change and reported "MUTATION DID NOT APPLY". **It was visible only because
   E's run failed the statement test as well as the receipt one**, which is a result that did not fit
   the mutation I thought I had made. Re-anchored on the log line above each call, and both re-run.
   **A mutation that changes more than it says it does overstates what the suite caught.**

I also produced two invalid escape sequences (`\:`) in log strings through heredoc quoting, caught by
`python -W error::SyntaxWarning` and fixed before the commit.

---

## 8. Flags

**Two, neither fixed, both in the embedded-image path and both out of this brief's scope.**

### Flag 1: the trailing move after the embedded-image loop is unconditional

`app.py:1208-1209`:

```python
# After processing all embedded images, move to Processed Receipts if all ok
move_email_to_folder(uid, "INBOX.Processed Receipts")
```

**The comment says "if all ok" and there is no condition.** It runs after every embedded email,
including one whose only image was a duplicate and was already moved to `INBOX.Duplicates`, and one
whose extraction failed.

**What it actually costs is small, and I am not overstating it.** The duplicate branch moves first,
and `move_email_to_folder()` copies, flags deleted and expunges, so by the time this line runs the
uid is no longer in INBOX and the copy has nothing to copy. **The email lands in `INBOX.Duplicates`
and this produces a failed move and a warning line.** So it is noise rather than misfiling, and
10f.22 passes.

**But it rests on the server refusing a COPY of an expunged uid**, which is server behaviour I have
not verified against Krystal, and the comment describes a guard that is not there. **Small and
obviously right: wrap it in the condition the comment already claims.** Say the word.

### Flag 2: the embedded-image path has no `message_id` duplicate check

The attachment path opens with `if repo.is_duplicate(message_id, att_id): ... continue`. **The
embedded-image path has no equivalent**, so it relies entirely on the email being moved out of INBOX
to avoid being offered again. Enumerated: `is_duplicate()` is called in exactly one place in the
whole repository, `app.py:1481`.

**Not a live fault today**, because the path calls `mark_processed()` for every image and moves the
email at the end, and the hash check would catch a genuine second copy in any case. **It is an
inconsistency between two routes**, which is the family 10f.22 is about, and it is the kind of thing
that becomes a fault when something upstream changes. **Reported rather than fixed**, because adding
a duplicate check to a route is a behaviour change the brief did not ask for.

---

## 9. What the brief got wrong

**Nothing was wrong. Three things are worth recording.**

| Claim | Held? |
|---|---|
| Three `find_by_hash()` call sites, all in `app.py` | **Yes**, and all three hold the client |
| One `find_by_transaction_loose()` caller | **Yes** |
| Two `_remove_inbox_pair()` callers | **Yes** |
| The embedded-image path is the one without the guard | **Yes** |
| `find_by_transaction()` and `find_by_transaction_no_date()` have no caller | **Yes**, re-enumerated including dynamic access |
| One `find_statement_by_hash()` caller, which holds the client | **Yes** |
| `statements` holds 0 rows | **Not checked by me.** Reading the live database from this session is possible but the brief did not ask and nothing in the change depends on it. The migration question is moot either way: adding a filter to a `SELECT` needs no migration whatever the row count |

**One: 10f.22 says three routes and there are four code paths.** The embedded-image path is the
fourth, and it is the one 10f.20 changed, so it is the one that most needed driving. Not an error in
the brief so much as the sub-step's own wording, which is about arrival routes as an operator sees
them.

**Two: `processed_attachments` has no `client_id`.** The brief says `find_by_hash()` "runs two
queries ... and both filter on the hash alone", which is true, and says to make them match within one
client, which is right. **It does not say how, and one of the two cannot be done by adding a filter**:
that table carries only a `receipt_id`, so the scope has to come from a join onto `receipts`. Read
out of `worker/database/schema.py`. The one visible consequence is pinned by a test: an attachment row
naming a receipt a rebuild has dropped now matches nobody, where the unjoined query returned the
dangling id. **No caller can tell**, because each pairs the lookup with `is_recorded_and_filed()` and
a receipt with no row is not filed.

**Three: the brief was amended mid-run**, at 19:35 BST, after 10f.23 and 10f.18 had landed. The
consultant session disclosed that itself in the amended file. **It cost nothing here**, because
amendment 1 is the same change as 10f.18 applied to a second function and it landed as its own
commit, and because its caller was already going to be edited for 10f.21.

---

## 10. Confidence

**High that all six sub-steps and amendment 1 are built as specified.** It rests on: the suite at 639
passed and 408 subtests; failing output quoted for every sub-step before its change; six mutations
each caught by tests naming what they broke; every call-site claim re-enumerated and printed whole
rather than taken from the brief; and the four routes driven through a real `process_once()` with
their verdicts printed by the test rather than transcribed by me.

**High that nothing out of scope moved.** `git diff` across the seven commits touches `app.py`,
`worker/database/repository.py`, `worker/extraction_pipeline.py` and two test files, and none of the
three frozen functions appears in it.

**Moderate on flag 1's real-world consequence.** That the email lands in `INBOX.Duplicates` rather
than `INBOX.Processed Receipts` follows from `move_email_to_folder()` expunging, which I read in the
source; **what an actual IMAP server returns for a COPY of an expunged uid I have not tested**, and
Paul's mailbox is the only place that could answer it.

**The `statements` row count in section 9 is the one claim I have taken from the brief without
checking.** Nothing in the change depends on it.
