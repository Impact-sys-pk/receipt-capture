# Report: four small corrections in the resolution service

**Claude Code, 2026-09-12.** From `PROMPT_claude_code_2026-09-12_service_corrections.md`, md5
`34a1665688fe4fca61b3c59a1144984b`, checked before reading and matching. Amendments 343 and 344.

**One commit on `feat/console-phase0`, not pushed: `da65b23`.** Five files, 547 insertions, 39
deletions.

**Three of the four items are built. Item 3 is reverted, reported, and now SETTLED.**
~~Section 3 says why, and it is the one thing in this report that needs a decision from you.~~
**Paul's decision, 2026-09-12, recorded as amendment 346: keep the code, fix only the comment.**
Done in commit `1dd8f3e`, comment only. Section 3 is kept as written because it is the reasoning
the decision was taken on.

**The suite: 1330 passed, 1 skipped, 922 subtests**, run again after the commit and green there too.
It was 1318 passed, 1 skipped, 920 subtests before this work.

---

## 1. For Paul: what changed that you would notice

### In `run.log`, two lines that were never written before

**One. A correction that clears a possible duplicate now says so.** Amendment 343.

```
WARNING  receipt r-1 was possible_duplicate and a correction in console has cleared
it to ok, so it will now drain into the books. It looked like a duplicate of receipt
r-original. Nothing asked the operator about the duplicate and they may never have
known there was one, so check the two are genuinely different documents before the
expense is claimed twice
```

It names **both** receipts, so it can be acted on rather than only noticed. It fires only where the
receipt's status actually was `possible_duplicate`, and there is a negative control proving it does
not fire otherwise.

**Two. A correction that asks to remember a supplier, against a code your chart does not hold, now
says why it did not.** Amendment 344 point three.

```
WARNING  remember_gl_for_supplier was requested for receipt r-1 but 9999 is not in
client CLIENT001's chart of accounts, so no vendor mapping was learned. The receipt
is still corrected and still filed. A mapping taught from a code the chart does not
hold cannot work: the chart check would strip it on every future receipt
```

**That second line is not in the brief and I added it deliberately.** Refusing to learn in silence
would have been a new silent behaviour introduced by this change, which is the fault amendment 343
is about. The Desktop route already says it, through the validation note `_resolve_category()`
returns, so this makes the two routes match in what they say as well as in what they do. Disclosed
here rather than buried.

### Behaviour that changed

**On the command line only**, a correction that ticks "remember this supplier" and carries a code
that is not in the client's chart **no longer teaches the vendor mapping**. The receipt is still
corrected, still filed, and still carries your code. Only the mapping is not written.

**Nothing changed in IntelliBooks Desktop's route**, which already behaved this way.

**The firm vendor table is unaffected either way**, because `_learn_firm_mapping_if_confirmed()`
checks the chart outcome itself. That is asserted rather than left to be inferred, in
`TheFirmWriteIsUnaffectedTest`.

### What is gone

`increment_firm_vendor_count()` in `worker\database\repository.py`. Nothing called it and it could
not create a row.

---

## 2. The three items built

### Item 1: `increment_firm_vendor_count()` deleted

**Re-enumerated before deleting, as the brief required, rather than trusting my own earlier count.**
Two sweeps, because they answer different questions:

```
CALLS to increment_firm_vendor_count() in PRODUCTION (55 files): 0
CALLS to increment_firm_vendor_count() in TESTS (87 files): 0

EVERY textual mention across the 375 git-tracked files: 9
   2026-07-25_CONSOLE_DESIGN.md:1220          amendment 344 itself
   archive/2026-09-06_REPORT_...:581,618,916  the historical record
   tests/test_layer_two_row.py:262,274,299,302   my own assertions
   worker/database/repository.py:625          the definition
```

**The second sweep is the one that matters** and it is `git ls-files` rather than a glob, so
`.history\` and `.venv\` are excluded because neither is tracked rather than by a filter. A name can
be called without appearing as a `Call` node, through `getattr()` or a string, and only a textual
sweep would find that. Nothing did.

The archive report is worth quoting because it closes the history: it records
`self.repo.increment_firm_vendor_count(business_type, vendor_key)` inside `learn_from_correction()`,
which amendment 234 deleted. So its last caller went in September and it has been unreachable since.

**Its two assertions went with it**, and this is the one place I did not do the literal thing:

- `test_increment_firm_vendor_count_has_no_caller` is **replaced**, not simply deleted, by
  `test_the_deleted_function_has_not_come_back`, which asserts the repository class does not define
  it. Asserted as absent rather than as uncalled, because **uncalled is what it was for months**
  before somebody would have renamed it into life.
- `test_the_writers_are_the_only_two` is **kept and narrowed** to one writer rather than deleted. It
  is a set guard over every function that writes `categorisations_firm_vendors`, and deleting it
  would have removed the thing that catches a replacement appearing under another name. **If you
  meant both assertions gone, say so and I will remove it.**

**And a class name I got wrong yesterday is corrected.** `TheFirmTableHasNoProductionWriterTest` said
the firm table has no production writer, and part B of step 10m gave it one the same day. The class
even said it expected to change when part B landed, and it did not. It is now
`TheFirmTableWritersTest`. That is my error from yesterday, disclosed rather than quietly tidied.

### Item 2: the command-line learning guard

`resolve_receipt()` required only that a code existed. It now requires the code to be in the client's
chart, which is what `_apply_filed_note()` has always required through
`_CategoryDecision.chart_confirmed`.

**An unreadable chart teaches nothing either, and that falls out rather than being special-cased.**
`get_chart_accounts_for_client()` returns an empty mapping both when the chart is empty and when the
bundle is missing, so no code is in it. That matches `_resolve_category()`, which refuses to learn
there for the same reason and in nearly the same words.

### Item 4: the possible-duplicate warning

**The guard is not moved, and that is the point.** `preserve_status` sits inside
`if validation.status != "ok":`, which a corrected receipt with sound figures never reaches, and
`decided_by_operator` forces validation to `ok` before that branch so it skips it outright. Hoisting
it would leave a corrected receipt at `possible_duplicate` for ever, because nothing else clears that
status.

**One constant, not two literals.** `POSSIBLE_DUPLICATE_STATUS` is read by both the new warning and
`preserve_status`. Two copies of one string in one function that have to agree is the drift this
project's own trap list objects to, and the mutation `watch-for-a-status-nothing-writes` proves it
matters: changing the constant broke the pre-existing preservation tests as well as the new ones,
which is exactly what a shared constant is for.

A test reads the value back off `worker\extraction_pipeline.py`'s own source, so a rename there goes
red rather than leaving this module watching for a status nothing writes.

---

## 3. Item 3 is NOT built. Establishing it turned up a reason to stop

**The brief said: "Establish it yourself before deleting: that the name is read nowhere in the
enclosing function, and that the builder has no side effect."** Both are true, verified from the
syntax tree:

```
inside resolve_receipt():
  sidecar_payload: STORE at [1268]  LOAD at []
  invoice_date:    STORE at [1267]  LOAD at [1337]     <- NOT dead, as the brief warned

make_enriched_sidecar(): calls made: NONE, returns: Dict
```

**I deleted it, ran the suite, and three tests failed.** Not one, and not tests about something else:

```
FAILED tests/test_sidecar_category_keys.py::AllFourCallSitesTest::test_all_four_call_sites_write_the_same_keys
FAILED tests/test_sidecar_category_keys.py::AllFourCallSitesTest::test_resolve_receipt_writes_the_three_keys_after_a_manual_correction
FAILED tests/test_resolution_service.py::GlOverrideTest::test_the_payload_this_path_builds_carries_the_corrected_code_and_name
```

**`AllFourCallSitesTest` spies on that exact call** to capture what this route would write, and
compares its key set against the other three writers. Its own docstring says why it exists: *"Four
writers of one file format is how it diverged. Lock the key set."* Delete the call and a four-way
comparison silently becomes three-way.

**And the deadness is already known, already recorded, and already assigned.** The comment sitting
above that spy, written on 2026-09-09:

> **The payload is captured at the point it is built, not read off disk, and that is a finding rather
> than a convenience.** Stage 4, 2026-09-09: `resolve_receipt()` no longer writes it anywhere. ... So
> a CLI-resolved receipt's corrected values reach the database and no file at all, which is flagged in
> `2026-09-09_REPORT_claude_code_stage4_pipeline.md` and **is 10f.15's to answer. This call site still
> builds the payload, so the four-way comparison below is still a real comparison.**

So deleting it does three things amendment 344 did not have in front of it:

1. **Reduces a format guard from four writers to three.**
2. **Destroys the only executable record of what the command-line route would write**, which is
   sub-step 10f.15's own input.
3. **Pre-empts 10f.15.** If that sub-step decides a CLI-resolved receipt should produce a file, the
   builder has to go back.

**So I reverted it to exactly what it was**, with no new code and no new comment, because a comment
saying "kept, contrary to amendment 344" would be me recording a decision I do not have. Section 3 of
the brief says to report a case the rule does not cover and stop, and `CLAUDE.md` rule 6 says report,
do not choose.

**Three ways forward, and the first is what I would do.**

- **Leave it until 10f.15.** The cost is one dead local and a comment that overstates what happens
  there. **The obvious fix for the comment alone, which needs no decision: strike "Sidecar from the
  effective code and name, all three keys" and say that this route builds the payload and writes
  nothing, pending 10f.15.** That removes the thing amendment 344 identified as the real cost,
  without touching the code or the guard. One edit, and I will do it on a word from you.
- **Delete it and let the comparison become three-way**, updating `AllFourCallSitesTest` and renaming
  it. That is the literal instruction, and it trades a guard for tidiness.
- **Delete it and answer 10f.15 first**, which is a step rather than a correction.

### SETTLED 2026-09-12, amendment 346. Paul took the first option

**Keep the code, fix only the comment.** Commit `1dd8f3e`.

The struck sentence is gone from the code and kept beside its replacement, per this project's
convention. What stands there now says the route builds the payload and writes nothing, records why
the call is kept, and names both `AllFourCallSitesTest` and sub-step 10f.15 so a reader who wonders
why a dead local survives finds the answer without leaving the file. **Amendment 344 point four is
superseded by 346, and both numbers are in the comment**, so a reader of either finds the other.

**The change is comment only, and that is proved rather than asserted.** `ast.dump()` of the file
before and after is identical. That is a stronger check than reading the diff: the dump drops
comments entirely while keeping docstrings, so anything executable that had moved would show. The
suite is green either way, 1330 passed.

---

## 4. Evidence

### Red before green

The new tests, run against the unchanged service before anything was edited:

```
7 failed, 5 passed, 2 subtests passed
FAILED TheChartConfirmedGuardTest::test_a_code_the_chart_does_not_hold_teaches_nothing
E   AssertionError: Lists differ: [{'mapping_id': '862f8de4-...', 'nominal_code': '7304', ...}] != []
FAILED ThePossibleDuplicateWarningTest::test_it_warns_and_names_both_receipts
E   AssertionError: no logs of level WARNING or higher triggered on worker.resolution.service
FAILED TheStatusLiteralTest::test_the_constant_holds_the_status_the_pipeline_writes
E   AttributeError: module 'worker.resolution.service' has no attribute 'POSSIBLE_DUPLICATE_STATUS'
```

**The five that passed before the change are the controls**, including
`test_a_code_the_chart_holds_still_teaches_the_mapping`. Without it, a guard that refused everything
would have satisfied the failing test above.

### Mutations

Five, each anchored once against a pristine copy, each printing its own diff, each restored byte for
byte, each measured against the whole suite.

| Mutation | Expected | Result |
|---|---|---|
| `drop-the-chart-confirmed-condition` | caught | **caught, 2 failures** |
| `drop-the-possible-duplicate-warning` | caught | **caught, 1 failure** |
| `fire-the-warning-on-every-correction` | caught | **caught, 6 failures** |
| `watch-for-a-status-nothing-writes` | caught | **caught, 4 failures** |
| `prose-only-control` | survives | **survived** |

**Two of those are worth reading rather than counting.**

`fire-the-warning-on-every-correction` is the negative control's own proof, and **four of its six
failures are pre-existing tests** in `test_resolution_backfeed.py` and `test_resolution_service.py`
that assert no such warning fires on an ordinary correction. The suite already guarded against a
noisy warning; my two tests are the third and fourth voices, not the only ones.

`watch-for-a-status-nothing-writes` was caught by `test_possible_duplicate_preserved.py` as well as
by the new tests, **because `preserve_status` now reads the same constant.** That is the argument for
one constant made by measurement rather than by assertion.

### The guard I changed, and proof it still discriminates

`tests/test_vendor_key_naming.py`'s `learn_from_correction` guard read the TEXT of every `.py` file,
and item 1's tombstone comment names that function as the deleted one's last caller. It went red on
prose about the code.

**`CLAUDE.md`, 2026-09-08, is explicit that the guard is what changes**: a source guard parses the
syntax tree, because this project keeps superseded wording beside every correction, and three earlier
guards were each patched by rewording the prose, *"which is the wrong way round."* So it walks the
tree now.

**A rewritten guard that passes proves nothing**, so it was driven over three cases with a probe file
in the repository root, then removed:

```
def learn_from_correction(): ...   -> FAILED: ['_guard_probe.py:1 defines it']
x.learn_from_correction()          -> FAILED: ['_guard_probe.py:2 calls it']
# learn_from_correction was deleted -> 1 passed
```

It catches a definition, catches a call, and ignores a comment.

### What must not change, checked

- **No stored value moved.** No migration, no backfill, no rewrite.
- **The firm table's rule and its single caller are untouched.** Item 2 changes only the client write
  beside it; `TheFirmWriteIsUnaffectedTest` drives both sides of the guard and asserts the firm table
  stays empty either way.
- **No receipt's status moves beyond what item 4 reports on.** Item 4 adds a log line and changes no
  status: the write below it is the one that was already there.
- **Nothing published, re-processed or re-extracted.**
- **Nothing written into `Clients\`, `IntelliBooks\` or `Intellibills\Documents\`**, and nothing run
  against the live practice root or the live database.
- **`import config` was never used to read a value**, and no OpenAI call was made.

### Committing and the index

**Committed by naming five paths.** Files the brief forbids committing were in the working tree
throughout, changed by the consultant session while I worked:

```
 M PROMPT_claude_code_2026-09-11_london_time_and_output_paths.md
?? PROMPT_claude_code_2026-09-12_attached_documents.md
```

**Both are still exactly that after the commit, and the index is empty.** Verified after committing.

**The suite was run again after the commit**, per the rule added on 2026-09-11, since the change adds
`tests/test_service_corrections.py`. Green.

---

## 5. Flags. Nothing here was fixed

~~**Flag 1. The comment above `sidecar_payload` still says a sidecar is produced there and none
is.**~~ **CLOSED the same day by amendment 346, commit `1dd8f3e`.** Paul's decision: keep the code,
fix only the comment. See the end of section 3. The original flag is struck rather than deleted
because the report is the record of what was found, and what was found was correct.

**Flag 2. `tests/test_layer_two_row.py`'s class asserted something false about itself for a day**,
because part B landed the same day and the class said in terms that it expected to change and then
did not. Fixed here as part of item 1, and flagged because **it is my error and the mechanism that
allowed it is general**: a test that says "this is expected to change when X lands" has no way to go
red when X lands. **Obvious fix, and it is a habit rather than an edit:** where a test's premise is
about to be falsified by scheduled work, assert the premise rather than describing it in the
docstring. No change proposed to anything else.

**Flag 3. Three of the four `CategorisationEngine` construction sites pass `enable_ai_fallback`
explicitly and `resolve_receipt.py:268` relies on the default.** Carried from yesterday's report and
unchanged. It is safe today because the default is `False`, and it is the CLI you run by hand, so it
is the one place where a change to that default would cost money without anybody choosing it.
**Obvious fix: pass the keyword explicitly there, matching the other three.** One word, no behaviour
change today. Not taken, because it touches a file this brief does not name.

---

## 6. My own mistakes

- **I deleted item 3 before running the suite**, found three failures, and had to read the tests to
  discover the call site was deliberately kept. The brief told me to establish two facts and I
  established exactly those two and no more. **Establishing what depends on a thing is part of
  establishing whether it is dead**, and I learned that from the failure rather than from the
  instruction.
- **Yesterday's `TheFirmTableHasNoProductionWriterTest` was wrong the moment I committed part B**, as
  set out in flag 2. I wrote the docstring that predicted it and did not act on the prediction.
- **My first instinct on the reverted item was to add a `del sidecar_payload` and a long comment
  explaining why it was kept.** That would have been me writing a decision I do not have into the
  source. Reverted to exactly what was there instead.

---

## 7. Confidence

**High, that `increment_firm_vendor_count()` was unreachable and its deletion changes no behaviour.**
It rests on two independent sweeps, one over the syntax tree of 142 files and one over the text of
all 375 git-tracked files, plus the archive record naming its last caller and the amendment that
deleted it.

**High, that item 2 changes what it is meant to change and nothing else.** It rests on a mutation
that is caught, on a control test proving a chart-held code still teaches, and on an explicit
assertion that the firm table is untouched whichever way the guard falls.

**High, that the possible-duplicate warning fires exactly where it should.** It rests on a mutation
firing it everywhere, which four pre-existing tests and two new ones caught, and on a mutation
silencing it, which one caught. Not on my reading of the condition.

**Lower, and the proposition is narrow: that item 2 is the right behaviour for every operator on the
command line.** What I verified is that it matches `_apply_filed_note()` and that amendment 344 says
to. **What I cannot verify is how often you correct a receipt on the CLI with a code your chart does
not hold**, because that is a question about your working habits and there is no observation of it.
If that happens often, this will feel like the mapping quietly not being learned, and the new WARNING
is the only thing that will tell you.

**Not verified: anything on your machine.** No script was run against the live practice root or the
live database, and no real receipt went through any of this.
