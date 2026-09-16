# Report: the Post-time message, so the client folder copy happens at Post

**Claude Code, 2026-09-10, 17:31 BST.** Read off the clock at the end of the
work. Times in this session drifted earlier today because I carried them
forward instead of reading them, which Paul caught; this one is read.

Brief: `PROMPT_claude_code_2026-09-10_post_time_client_copy.md`, md5
`a3a94eee258c10c24b6d313dcb9b8f9d`, verified before reading it. **Sub-step
10f.37**, amendment 315, from Paul's decision of 2026-09-10.

| | |
| --- | --- |
| Branch | `feat/console-phase0` |
| The pipeline half | `2bd2418` |
| This report | the commit whose subject is `docs: the report for sub-step 10f.37`. A file cannot carry the hash of the commit that adds it |

Not pushed, no branch created. Not committed, per section 5:
`2026-07-25_CONSOLE_DESIGN.md`, any `PROMPT_*` or `HANDOVER_*` file, or anything
under `Test Receipts\`.

**One thing about the brief itself, since I checked.** It is dirty in the working
tree, and I did not touch it: the committed copy is an older version, and the
consultant session edited it after committing to remove the `HOLD UNTIL THE
CURRENT BRIEF IS REPORTED` line and to add the paragraph about the comment and
the warning. **The version I read and worked from is the current one and its md5
is the one I was given**, so nothing changed under me. Left uncommitted.

---

## 1. The four things the Desktop half is written from

### 1. The action word, the shape, and every field

**The action is `attached`.** `NOTE_ACTIONS` is now
`("filed", "discarded", "attached")`. The whole message:

```json
{
  "schema": 1,
  "receipt_id": "de3e901e-....",
  "client_id": "Client_004",
  "action": "attached",
  "resolved_by": "desktop",
  "resolved_at": "2026-09-10T17:00:00.000Z"
}
```

Written into `Intellibills\Resolutions\` as `{receipt_id}_{unix_ms}.json`, the
same convention 12.2 already gives every note, with `unix_ms` derived from
`resolved_at` rather than a second clock read.

| Field | Required | Notes |
| --- | --- | --- |
| `schema` | yes | Must be `1`. Unchanged: the field is additive, so neither half has to ship first for the *existing* actions. |
| `action` | yes | Exactly `"attached"`. Anything else is refused. |
| `receipt_id` | **yes in practice** | The parser allows null and falls back to matching `original_review_files` against `receipts.filename`, but that fallback is already broken for a Desktop note, flagged in `2026-09-09_REPORT_claude_code_desktop_note.md`. **Send the `receipt_id`.** |
| `resolved_at` | yes | It is the idempotency key of 12.3 step 3. A note without it is refused. |
| `client_id` | send it | Not read by this path, which takes the client off the receipt row, and it is in every other note. |
| `resolved_by` | send it | `"desktop"`, as the other notes do. |
| **`filed_path`** | **never** | Present-and-ignored with a WARNING. The pipeline composes the name; a name composed by Desktop cannot tell a collision's `-2` from its original. |
| **`values`** | **never** | Same treatment. Nothing about the receipt changes. |

**Why a third action rather than a field on `filed`**, since amendment 307's
rule is that the field chooses the path and not the action word. Two reasons,
and the first is decisive:

- **A new action word fails loudly, a new field fails silently.**
  `parse_resolution_note()` refuses an action outside `NOTE_ACTIONS`, so a
  Desktop that ships before the pipeline leaves its notes in
  `Resolutions\failed\` with an `.error.txt` beside each, which is what "the two
  halves land together" looks like when they do not. **A field would be swallowed
  by the parser's documented leniency** that extra keys are ignored, and the
  note applied as a filing: `_settle_note()` would re-settle an already-`ok`
  receipt, write a new `manual_correction` extraction row and recategorise it.
- **Both existing actions change the receipt's status.** This one changes
  nothing about the receipt: no status, no extraction, no categorisation. It is
  a different kind of message, not a variant of an existing one.

**And `attached` names the receipt's state rather than the moment Desktop sent
it**, so it is true from Attach onwards and still true after Post. That is
deliberate: it does not presuppose the answer to question 4.

### 2. What the pipeline does on `publish` and on `never`, and what I would rather Desktop did

| Trigger | What happens | Log |
| --- | --- | --- |
| `post` | **The client folder copy is written** | `receipt X is attached to a transaction, so its client folder copy is due: {path}` |
| `publish` | Nothing is written. The copy was made when the receipt published | `... client_copy_trigger is 'publish', so its client folder copy was already made when it published and there is nothing to write now` |
| `never` | Nothing is written | `... client_copy_trigger is 'never', so nothing is written into {Clients root}` |

**In all three the note is applied and moves to `processed\`.** None of them is
an error, and a test drives all three.

**What I would rather Desktop did: always send it, and let the pipeline
decide.** Three reasons.

- **Desktop does not reliably know the trigger.** It is a firm setting the
  pipeline reads with no default, and a second reader is a second thing that can
  disagree with the first.
- **The trigger can change between the message being sent and being read.** The
  pipeline reads notes on its next poll, so a decision taken in Desktop at
  17:00 would be applied against a setting as it was at 17:00 and not as it is
  when the copy is due. The pipeline's own read is the only one that cannot be
  stale.
- **It is the arrangement that already exists.** `copy_for_published_receipt()`
  holds the trigger for the four publish-path callers, and a Desktop that
  decided for itself would be a fifth reader of a setting that has one owner.

**The cost of always sending is one small JSON file per attach, applied and
moved to `processed\`.** That is the same cost the `filed` and `discarded` notes
already carry.

### 3. What Desktop can honestly tell the operator at that moment

**Nothing about the copy in the past tense.** The pipeline reads
`Resolutions\` at the start of its next poll, five minutes by default, so at the
moment the operator clicks, no copy exists and no pipeline has seen the message.

Honest wordings, in order of how much they claim:

- **Safest, and true on every trigger:** "Attached. Intellibills has been
  told." That is exactly what happened: a file was written into a folder the
  pipeline drains.
- **Where Desktop knows the firm is on `post`:** "Attached. The receipt will be
  copied into the client folder when Intellibills next runs."
- **What Desktop must not say:** anything of the form "filed to
  `Clients\...`", because it does not know the path, the pipeline composes it,
  and on two of the three triggers no copy is coming at all.

**And if the pipeline is not running, the message waits.** A note sits in
`Resolutions\` until a poll picks it up, which is a queue rather than a loss.
Nothing in `Resolutions\` is ever deleted on any path.

### 4. Attach, Post, or both. Paul's to rule on, and this is what each would mean

**Not mine to decide, and I have not built a preference into the pipeline:** the
handler acts on the message whenever it arrives, so all three options work
against the same pipeline half with no code change.

**At Attach.** The document is copied when a person links it to a transaction.

- The folder fills earlier, and it fills with documents a person has
  deliberately connected to a transaction, which is most of Paul's requirement.
- **A transaction can be attached and never posted**, so the folder would hold
  documents for transactions that are not yet in the accounts. 18.6 says the
  receipts list is a staging area and nothing in it is part of the books until
  Post, so at Attach the document is one step short of what Paul asked for.
- Detaching is possible, and **18.2b says a copy is never withdrawn**, so an
  attach-then-detach leaves a document in the folder that belongs to no
  transaction. That is the same class of stray the move away from `publish` was
  meant to remove.

**At Post.** The document is copied when the transaction is signed off.

- **It is what Paul's words describe**: the folder holds the receipts relating
  to that client's transactions, and after Post the transaction is in the
  accounts. 18.6: "At Post the transaction takes the confirmed figures, the
  image and the document's identity are attached, and the staging entry
  retires."
- The setting is called `post` and 18.2b's own reasoning is Post-time.
- **A document attached but not yet posted has no copy**, so between Attach and
  Post the folder is behind the operator's screen. That is a smaller gap than a
  stray.

**Both.** Send at Attach and again at Post.

- **The pipeline already tolerates it**, and that is measured rather than
  assumed: a second message for one receipt writes nothing twice, and section 4
  below sets out the three separate things that hold that.
- The audit trail would then carry two rows per receipt, which is arguably more
  useful: it records when it was attached and when it was posted.
- **It doubles the notes for no benefit if Attach is the answer**, because the
  copy is already there by the time the Post message arrives, and the second
  message's only effect is a log line and an audit row.

**My reading, offered and not acted on: Post.** It is the one that matches
Paul's own words and 18.6's statement that nothing in the staging area is part
of the books, and the stray a detach would leave is exactly the kind of thing
this whole change exists to stop. **But the gap between Attach and Post is real
and it is his call whether it matters.**

---

## 2. What was built

**`worker\client_copy.py`.** `copy_for_published_receipt()` gains
`at: str = None`, defaulting to `config.CLIENT_COPY_ON_PUBLISH`. The trigger gate
becomes "the firm's trigger names a moment, `at` names the moment this caller is
at, and they have to match":

```python
    at = at or config.CLIENT_COPY_ON_PUBLISH

    if config.CLIENT_COPY_TRIGGER == config.CLIENT_COPY_NEVER:
        return None

    if config.CLIENT_COPY_TRIGGER != at:
        ...
        return None
```

**The function's name is still true** and was not changed: a receipt reaches the
books through the drain, which needs a publish, so a receipt named by a Post-time
message has published.

**`worker\resolution\service.py`.** `ATTACHED_ACTION`, a third value in
`NOTE_ACTIONS`, `NOTE_APPLIED_OUTCOMES`, `EVENT_CLIENT_COPY_WRITTEN_KEY`, the
parser's present-and-ignored branch extended to the new action, and
`_apply_attached_note()`, which:

- warns where the receipt has no `published` row;
- passes **the receipt row's own `status`** as the validation status, so the
  existing `ok`-only gate refuses anything else rather than a new gate here;
- calls `copy_for_published_receipt(..., at=config.CLIENT_COPY_AT_POST)`;
- logs which of the three triggers applied;
- writes one `resolution_events` row, `action` `attach`, `outcome` `attached`,
  carrying `note_resolved_at` and, where a copy was written, its path.

**`app.py`.** `_consume_resolution_notes()` decides `processed\` against the
imported `NOTE_APPLIED_OUTCOMES` instead of its own `("filed", "discarded")`
literal.

### The branch survived, reworded, and it names 10f.37

The brief asked which of two things happened. **The `post` branch survives.**
It was:

> `client_copy_trigger` is 'post', and the Post-time trigger has no mechanism
> yet: it needs the message from IntelliBooks Desktop at sub-step **10f.16**,
> which is not built. No copy is written into `Clients\` by this pipeline until
> it is.

a WARNING. It is now:

> `client_copy_trigger` is 'post', so no copy is written into `Clients\` when a
> receipt publishes. The copy is written when IntelliBooks Desktop says the
> receipt is attached to a transaction, which is sub-step **10f.37**. Set
> `client_copy_trigger` to 'publish' to copy on a successful publish instead.

an INFO. **The level changed for a reason rather than by preference**: the old
line was the pipeline unable to act, the new one is the pipeline waiting for a
message that now exists. Still once per process, so a real firm's every receipt
does not carry it.

**10f.16 still appears once in that file, in the sentence recording that it was
the number pointed at and that it is BUILT.** A guard asserts every surviving
mention says `BUILT` on its own line, so a reader is not sent to finished work
while the trail is kept. See mistake 3.

### What did not change

`Intellibills\Documents\` is neither written to nor deleted from, asserted. The
`publish` trigger's behaviour is unchanged and F16's value is untouched: **Paul
switches it himself, after this lands.** `write_client_copy()` is still reached
from exactly one place. This morning's discard work is untouched.

---

## 3. The two things the brief asked me to establish

### 1. Can a receipt reach Post without having published?

**No, by the built route, and it is not refused if it happens.**

A receipt reaches the books by Desktop draining `IntelliBooks\Incoming\`, which
the pipeline writes at publish. So to appear in the receipts list at all it must
have published. **The one way a document reaches a transaction without
publishing is sub-step 10f.38**, attaching from the Bank Transactions tab a
document Intellibills has never seen, which amendment 315 records as "not
extracted, not validated, never published back and never in the receipts list".
Such a document has no `receipt_id`, so it cannot be the subject of this
message.

**What happens if a message arrives for a receipt with no `published` row: the
copy is written and a WARNING is logged.** Not refused, and the reasoning is:

- **Desktop owns the books and is the authority on what is in them.**
  `publish_events` records what the pipeline offered, not what the accounts
  contain.
- **Refusing would produce the worse of two states**: a receipt in the accounts
  with no copy **and** a note in `Resolutions\failed\`, which section 12 says
  means the database and the books disagree.
- The document is a client receipt that reached `ok`, and 18.2b says a copy is
  never withdrawn, so writing it is not a decision that has to be undone.

Driven, not reasoned: `test_a_receipt_with_no_published_row_is_copied_and_reported`.

### 2. Does the sweep interfere?

**No, and on `post` it does not even run its query.** The first statement of
`_copy_missing_client_copies()`, read off the code:

```python
    if config.CLIENT_COPY_TRIGGER != config.CLIENT_COPY_ON_PUBLISH:
        return
```

So on `post` and on `never` the sweep returns before the query. **The two
cannot write the same file because only one of them runs on any given
trigger.** Held two ways: a tree guard asserting that comparison is the
function's first statement and a `return` its body, so a later edit moving it
below the query goes red; and a behavioural test that a poll with no note writes
nothing on `post`.

**And `_publish_unpublished_receipts()`, the other publish-time caller, does not
reach a published receipt either**, because it selects on
`NOT EXISTS (published)`. That is why the once-per-process INFO line needed a
real arrival to test: see mistake 2.

---

## 4. A second message writes nothing twice, and three separate things hold it

The brief asked which. **All three, and each is asserted separately rather than
inferred from one pass.**

| Layer | What it stops | Test |
| --- | --- | --- |
| **The idempotency key**, 12.3 step 3 | A replay of the *same* note. `_note_already_applied()` matches on `resolved_at` inside `corrections_json` and returns before the action branch | `test_the_same_note_twice_is_skipped_on_the_key` |
| **The one-copy gate** in `copy_for_published_receipt()` | A *genuinely later* note, different `resolved_at`. `filed_path` is set, so no copy is written and the receipt keeps the one it has | `test_a_genuinely_later_note_writes_nothing_twice_either` |
| **The identical-bytes skip** in `write_client_copy()`, 10f.25 | The same document under the same composed name, even if the two above were bypassed | `test_the_identical_bytes_skip_is_the_third_layer` |

**The idempotency layer rests on the audit row**, which is why
`_apply_attached_note()` writes one: a handler that wrote no row would apply the
same message on every poll for ever. Mutation M5 removes the row and is caught
by four tests, two of them the idempotency ones.

**A genuinely later note still leaves its own audit row**, asserted, because two
attaches of one receipt are two events even though only the first can produce a
file.

---

## 5. The suite and the enumerations

| Run | Result |
| --- | --- |
| The new tests, before any production change | **23 failed, 9 passed** |
| The pre-existing tests, with the change in | **1087 passed, 1 skipped, 742 subtests** |
| Everything, after | **1118 passed, 1 skipped, 745 subtests** in 70s |

**What "before" means.** The middle row is the suite with
`--ignore=tests/test_post_time_client_copy.py`. It is exactly the previous
commit's test count, 1087, so nothing pre-existing broke; the subtest count is
742 against 732 because `tests/test_logs_isolation.py` globs `test_*.py` and
checks each module that drives `process_once()` against ten config names, and
`--ignore` stops collection but not that glob. Same arithmetic as this morning,
and checked rather than assumed.

**Five pre-existing set guards went red on the way, all correctly**, and each is
updated with the reasoning in place:

| Guard | What changed |
| --- | --- |
| `test_the_gated_entry_point_has_four_callers_and_this_is_the_fourth` | Five callers now. Renamed. |
| `ClientFolderWritersTest::test_every_caller_goes_through_the_gated_entry_point` | The fifth caller listed. |
| `ClientFolderWritersTest::test_the_set_of_routes_into_the_client_folder_is_the_allowed_set` | `_apply_attached_note` names `config.CLIENTS_ROOT` in a log line, so it joins the set. It writes nothing itself. |
| `TheTriggerDecidesTest::test_post_writes_nothing_and_says_so_once` | The line is INFO and names 10f.37. Renamed to `..._at_publish_time_...`. |
| `test_the_guard_is_asked_at_the_one_call_site_and_it_is_the_new_one` | `is_published()` has a second caller, asking a different question and gating nothing. |

### The red

```
FAILED …OnThePostTriggerTest::test_the_copy_is_written_when_the_message_arrives
E   AssertionError: Lists differ: [] != ['Test Client/IntelliBooks/Receipts/2025-26/2026-04-01_apcoa-parking_96.00.pdf']
E    : the Post-time message did not produce the client folder copy

23 failed, 9 passed in 2.30s
```

The nine that passed red are the shape guards and the sweep's own behaviour,
which this change does not alter.

### Every caller of the gated copier, and the moment each passes

From the syntax tree, `.history\` excluded. Line numbers omitted for `app.py`
per `CLAUDE.md`.

```
app.py                              [_publish_unpublished_receipts]   at = (default: CLIENT_COPY_ON_PUBLISH)
app.py                              [_copy_missing_client_copies]     at = (default: CLIENT_COPY_ON_PUBLISH)
worker/extraction_pipeline.py:534   [process_extraction_result]       at = (default: CLIENT_COPY_ON_PUBLISH)
worker/resolution/service.py:1143   [resolve_receipt]                 at = (default: CLIENT_COPY_ON_PUBLISH)
worker/resolution/service.py:2079   [_apply_attached_note]            at = config.CLIENT_COPY_AT_POST

5 callers
```

And the one writer, unchanged:

```
worker/client_copy.py:526           [copy_for_published_receipt]      write_client_copy()
1 caller
```

### Where the action and outcome sets are read

So the third word is shown to reach every place that decides on one:

```
NOTE_ACTIONS:           3 reads in 2 places   service.py::<module scope>, service.py::parse_resolution_note
NOTE_APPLIED_OUTCOMES:  3 reads in 3 places   app.py::_consume_resolution_notes,
                                              service.py::<module scope>,
                                              service.py::apply_resolution_note
ATTACHED_ACTION:        8 reads in 4 places   service.py::<module scope>, ::_apply_attached_note,
                                              ::apply_resolution_note, ::parse_resolution_note
CLIENT_COPY_TRIGGER:    8 reads in 5 places   app.py::_copy_missing_client_copies,
                                              client_copy.py::copy_for_published_receipt,
                                              config.py::<module scope>,
                                              service.py::_apply_attached_note,
                                              service.py::resolve_receipt
```

**`NOTE_APPLIED_OUTCOMES` in three places is the point of it.** Two of them were
`("filed", "discarded")` literals in two files that had to agree, and on the
first run they did not: every successfully applied Post-time message went to
`Resolutions\failed\` with an ERROR.

---

## 6. The mutations

Eight, through `tests\mutation_harness.py`, each anchored on one place, each
printing its diff, each running the whole suite, each restored byte for byte.
**The four the brief names are M1, M2, M3 and M6.**

| # | Mutation | Expected | Result |
| --- | --- | --- | --- |
| M1 | write the copy on `never` | caught | **caught**: 1 failure, after the fix below |
| M2 | write twice for two messages | caught | **caught**: 1 failure |
| M3 | ignore the trigger altogether | caught | **caught**: 6 failures |
| M4 | the post caller passes the publish moment | caught | **caught**: 6 failures |
| M5 | the handler writes no audit row | caught | **caught**: 4 failures |
| M6 | prose only, in the handler's docstring | **survives** | **survived**: 1118 passed |
| M7 | the receipt's own status is not passed | caught | **caught**: 1 failure |
| M8 | the applied outcomes lose the third word | caught | **caught**: 10 failures |

**M1 survived on its first run, and the fix was a test rather than a deletion.**
Removing

```python
    if config.CLIENT_COPY_TRIGGER == config.CLIENT_COPY_NEVER:
        return None
```

left the whole suite green, because the next check is
`if config.CLIENT_COPY_TRIGGER != at` and on a `never` firm that is true for
either moment a real caller can be at. **So the branch was subsumed and
untestable.** I kept it and made it load-bearing instead:
`test_never_means_never_whatever_moment_the_caller_claims` calls the function
with `at=config.CLIENT_COPY_NEVER`, which without the branch satisfies
`never != never` as False and falls through to write a copy on the one trigger
whose entire purpose is that nothing is written. Nothing passes that today; the
branch is what means a future caller cannot. M1 is caught now.

**M8 is the one that would have shipped broken** and is worth reading: removing
`ATTACHED_ACTION` from `NOTE_APPLIED_OUTCOMES` fails ten tests, because every
successfully applied message then goes to `failed\`. That is the exact fault the
one definition removes.

---

## 7. Flags

**Flag 1. Four copies of the same argument-gathering block.** Each of the five
callers of `copy_for_published_receipt()` composes `invoice_date`, `supplier`,
`gross` and the `or`-defaults from whatever it has in hand: the arrival path from
an `ExtractionResult`, the other four from an `extractions` row. **My handler is
the fifth copy.** The `or "unknown"` and `or 0.0` defaults are repeated in four
of them. A helper taking `(repo, receipt, extraction, at)` would remove it, and
that is a refactor of `app.py`'s sweep and two other paths, which this brief did
not ask for. Reported, not done.

**Flag 2. `_POST_WARNED` is process state and the tests reset it by hand.**
`client_copy._reset_post_warning()` exists for the test and is called in three
test files now. It works. It is the kind of module-level flag that a second
process or a long-running pipeline makes awkward: the line is said once per
process, so a pipeline running for a week says it once on the first receipt
after start. That is the intended behaviour and it is worth knowing it is the
behaviour.

**Flag 3. Nothing tells the operator the copy has been made.** The Post-time
message is one-way: Desktop asserts, the pipeline acts, and the only record is
`run.log` and the `resolution_events` row. **Section 12.4 says the reverse
direction needs nothing**, and for a filing that was true because Desktop's own
scan saw the file. Since 10f.15 Desktop no longer reads that folder, so **there
is now no route by which Desktop can know the copy happened.** Not a fault of
this sub-step and not something the brief asked for; recorded because "did it
work" is a question Paul will eventually ask from the Desktop side.

**Flag 4. `receipt_id` is optional in the parser and must not be for this
action.** `parse_resolution_note()` allows a null `receipt_id` and falls back to
matching `original_review_files` against `receipts.filename`, and that fallback
has been broken for Desktop notes since Desktop began sending the published
inbox item name, flagged in `2026-09-09_REPORT_claude_code_desktop_note.md`. An
`attached` note with no `receipt_id` would therefore go to `failed\` as
"no receipt matched". **Harmless today because Desktop always sends one**, and I
have not added a stricter check: it would be a second refusal for a condition
the existing one already reports clearly.

---

## 8. My own mistakes

1. **A test that could not tell two writers apart.**
   `test_on_publish_a_receipt_with_no_copy_yet_still_gets_none_from_this`
   asserted `filed_path` was still NULL on the `publish` trigger, and it went
   red because a copy really did appear: `_copy_missing_client_copies()` sweeps
   exactly that shape on `publish`, so **the sweep wrote it, not my handler**.
   The column records that a copy exists, not who made it. Rewritten to assert
   on `client_copy_written` in the audit row, which only the handler writes.
2. **A test for a log line that nothing in that poll could produce.**
   `test_the_publish_time_caller_says_why_it_wrote_nothing_on_post` seeded an
   already-published receipt and asserted the once-per-process INFO line, and
   the log came back empty. **Nothing in such a poll calls the publish-time gate
   at all**: `_publish_unpublished_receipts()` skips a published receipt and
   `_copy_missing_client_copies()` returns before its query on `post`. It now
   drives a real arrival, and a second test asserts the line is said once
   across two arrivals.
3. **A guard that would have deleted history.** My first version of
   `test_the_code_no_longer_sends_its_reader_to_a_built_sub_step` asserted the
   string `10f.16` was **absent** from `worker\client_copy.py`. That is against
   this project's convention: superseded wording is kept beside the correction,
   and the sentence recording which number *was* pointed at is worth keeping.
   Narrowed to assert every surviving mention says `BUILT` on its own line.
4. **A mutation that survived, and it found redundant code rather than a gap.**
   M1, in section 6. I kept the clause and wrote the test that makes it mean
   something, rather than deleting it, because "never means never whatever the
   caller claims" is a property worth having.

---

## 9. Confidence

- **That a file appears in the client folder when the message arrives: high, and
  it is about the file rather than the call.** Ten tests drive a real
  `process_once()` and list the client folder tree whole; the red quoted in
  section 5 is that listing being empty.
- **That the other two triggers write nothing and still apply the note: high.**
  Each is driven separately and a subtest drives all three, and M3 removes the
  comparison and is caught six ways including a pre-existing test in another
  file.
- **That a second message writes nothing twice: high, and it is three
  independent properties rather than one.** Each layer has its own test and M2
  and M5 each remove a different one.
- **That the sweep cannot interfere: high.** The guard is the first statement of
  that function, asserted from the tree, and a poll with no note is driven.
- **That a receipt cannot reach Post without publishing: medium, and the
  uncertainty is not about the pipeline.** The route through the drain needs a
  publish, which I read; what I cannot rule out from this side is a Desktop that
  puts a receipt in the books some other way. **The behaviour if it happens is
  tested either way**, which is why it is not a gate.
- **That the action word is the right shape: high on the mechanics, and it is
  the mechanics I am confident about.** A new action fails loudly and a new
  field would be applied silently and wrongly, both read out of
  `parse_resolution_note()`. Whether `attached` is the word Paul wants is his
  call and one line to change in each half.
- **On Attach versus Post: no confidence offered, because it is not a technical
  question.** Section 1.4 sets out what each would mean and the pipeline half
  works unchanged under any of the three.
