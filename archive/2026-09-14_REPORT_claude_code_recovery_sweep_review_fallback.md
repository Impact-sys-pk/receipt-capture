# Claude Code report, 2026-09-14: step 10aq, the recovery sweep's silent fallback

Against `PROMPT_claude_code_2026-09-14_recovery_sweep_review_fallback.md`. Session ran 08:31 to
09:00 BST on 2026-09-14, times read from the machine clock rather than carried forward.

**Built. One commit, `9869a63`, on `feat/console-phase0`. Not pushed.**

**Read this section before the rest. Amendment 405's wording and the system's actual behaviour
disagree, and I have built against the behaviour.** Section 3 has the measurement and the reasoning,
and it is the one thing in this step you may want to overturn.

---

## 1. What I read directly

Everything below was opened and read rather than taken from the brief or from amendment 405.

| File | What I read it for |
| --- | --- |
| `app.py`, `_publish_unpublished_receipts()` | the sweep itself, whole |
| `worker/validation/rules.py` | how the normal path decides Review |
| `worker/extraction_pipeline.py`, `process_extraction_result()` | what the normal path DOES about it |
| `worker/client_copy.py`, `copy_for_published_receipt()` | the client folder gate |
| `worker/filing.py`, `file_review()` | what the Review folder write is |
| `worker/database/repository.py`, `get_unpublished_ok_receipts()` | what the sweep selects |
| `worker/publish.py`, `extra_for()` and the key constants | the item's own key names |
| `IntelliBooks-Desktop-v3.html`, `scanReview()` and `itemIsHeld()` | where the Review queue reads from |

The Desktop file is the live one at
`C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliBooks\App\IntelliBooks-Desktop-v3.html`.
Read only.

---

## 2. Step 1 of the brief: is amendment 405's description still accurate?

**Yes, on every point, and I confirmed each from the code.**

The four fallbacks were five consecutive lines in `_publish_unpublished_receipts()`:

```python
invoice_date = extraction.get("invoice_date") or datetime.now(timezone.utc).date().isoformat()
tax_year = determine_tax_year(invoice_date)
supplier = extraction.get("supplier_name") or "unknown"
gross = extraction.get("gross_amount") if extraction.get("gross_amount") is not None else 0.0
currency = extraction.get("currency") or config.DEFAULT_CURRENCY
```

- **Four fields**, exactly the four named: `invoice_date`, `supplier`, `gross`, `currency`.
- **Where the values come from**: today's date in UTC, the literal `"unknown"`, the float `0.0`, and
  `config.DEFAULT_CURRENCY`.
- **"Invents silently" was accurate.** No log line of any kind between the client-folder-name check
  above and the categorisation below. The sidecar was then built with a hardcoded
  `validation_status="ok"` and `copy_for_published_receipt()` was called with a hardcoded
  `validation_status="ok"`, so the receipt published and was copied as though it had been read
  cleanly.
- **The invented date decides the tax year.** Confirmed by making it happen rather than by reading:
  see the red output in section 5, where a receipt with no invoice date landed at
  `Test Client/IntelliBooks/Receipts/2026-27/2026-09-14_apcoa-parking_12.00.pdf`. Today's date, and
  the tax year derived from it.

---

## 3. THE ONE THING I JUDGED: "instead of publishing" cannot be done as written

Amendment 405, the section 16 step text and the brief all say the receipt "routes to Review **instead
of publishing**". **I have built it so that the receipt routes to Review BY publishing, carrying
`validation_status: "needs_review"`.** That is the opposite of the literal instruction and it is
deliberate.

### The measurement that decides it

**Desktop's Review queue no longer reads the Review folder.** Sub-step 10f.15 moved it, and step 10f
completed on 2026-09-11.

- `scanReview()` at line 5699 of `IntelliBooks-Desktop-v3.html` calls `inboxItems()`. It reads the
  **published inbox**.
- The string `Intellibills\Review` appears in that file **zero** times, counted with `grep -c`.
  `parseSidecar` appears 10 times and `scanReview` 10 times, so the file was searched correctly.
- What keeps an item in the queue rather than letting the drain take it into the books is
  `itemIsHeld()` at line 5382:
  ```js
  function itemIsHeld(s){
    return !!((s.validation&&s.validation!=="ok")||s.categoryUnconfirmed);
  }
  ```
  and `scanReview()` skips anything that is not held, with the comment "an item nothing holds is the
  drain's, not this queue's".

**So an unpublished receipt reaches the operator nowhere at all.** Marking it `needs_review` also
removes it from the sweep permanently, because `get_unpublished_ok_receipts()` selects
`WHERE status = 'ok'`. It would sit in the database, invisible in Desktop, until some future
`pipeline_version` bump made `_retry_failed_receipts()` pick it up and spend an OpenAI call
re-reading it.

### Why I built it this way rather than asking first

Four reasons, and the last is the one that settled it.

1. **The Why column supports it.** Amendment 405's reasoning is "the engine's whole design marks what
   it cannot place for review rather than guessing at it; a silent invented value reaching a client's
   books is the one outcome that design exists to prevent". Publishing as `needs_review` marks it for
   review and keeps it out of the books: the drain will not take a held item, and the client folder
   copy is refused. The invented value reaches nobody's books.
2. **The brief's own step 2 points here.** It says to find where the normal validation path routes to
   Review and "use the same mechanism here rather than building a second one". The normal path's
   mechanism publishes: `publish_receipt()` in `process_extraction_result()` sits outside the ok and
   review branches and runs for every status, since amendment 293 widened it on 2026-09-09. The
   comment there says in terms that `failed`, `needs_review` and `possible_duplicate` "have to reach
   Desktop through the inbox or they reach it nowhere". **So the brief's headline and its step 2 point
   in opposite directions**, and step 2 is the one that matches the code.
3. **"Instead of publishing" reads as pre-10f.15 wording.** When Review meant a folder Desktop read,
   Review and publishing were alternatives. Since 10f.15 they are not.
4. **The failure modes are not symmetrical.** If I build publish-as-review and you wanted
   no-publish, the receipt appears in the Review queue with a pill and notes naming the invented
   field, and you tell me to change it. If I build no-publish and you wanted publish-as-review, the
   receipt silently disappears from every surface the operator has. **One of those is visible and
   recoverable and the other is invisible data loss**, so I took the visible one.

**This is a judgement rather than a measurement, and it is yours to overturn.** If you want the literal
reading, it is a two-line change and I will also need to tell you where such a receipt should then
surface, because today the answer is nowhere.

---

## 4. What I built

One function, `_publish_unpublished_receipts()` in `app.py`. 90 lines added, 7 removed, most of it
comment.

**Detection.** The four `or`-style fallbacks become explicit tests that record which field fired, in
a `fallbacks` list.

**The warning, step 3 of the brief.** One `logger.warning` per field that fell back, naming it, on
every fallback. Per field and not per receipt, because a receipt can fall back on more than one and
the operator needs to know which value is invented. These fire whether or not the routing changes,
which is what the brief asked for; the mutation in section 6 shows they are independent of the
routing.

**The routing, and no new mechanism anywhere.** Three existing mechanisms carry it:

| What | Mechanism reused |
| --- | --- |
| the item Desktop sees | `validation_status` in the sidecar, which Desktop routes on |
| the client folder | `copy_for_published_receipt()`'s own gate, which already refuses every status but `ok` and `bank_attachment` |
| the receipt row | `repo.update_receipt_status()`, the same call the normal path makes |
| the run summary | `stats['review_flags_issued']`, the same counter the normal path increments |

The sweep previously passed a hardcoded `"ok"` to the sidecar and to
`copy_for_published_receipt()`. Both now receive the status it actually has. **Nothing new gates the
client folder: that function's existing rule does it**, which is what step 2 asked for.

The published item's `validation_notes` now name the fields, so the operator sees which value was
invented on the row itself rather than only in `run.log`.

**What I did not do.** I did not call `file_review()`, which is what the normal path uses to write
into `Intellibills\Review\`. Nothing reads that folder any more: `REVIEW_ROOT` has no reader in the
pipeline and Desktop has none either, per the count in section 3. Adding a filesystem write with no
reader is a change to a part of the sweep the brief said not to change. Flag 2 covers the stale
docstring that still claims a reader.

---

## 5. Red before green

The new tests were written first and run against the unchanged sweep. **The control passed and every
fallback assertion failed**, which is the shape that says the tests are about the change rather than
about the fixture:

```
11 failed, 4 passed
```

The client folder assertion printed the defect in the raw:

```
AssertionError: Lists differ:
  ['Test Client/IntelliBooks/Receipts/2026-27/2026-09-14_apcoa-parking_12.00.pdf'] != []
  : a receipt with an invented invoice date was copied into a client folder,
    under a tax year nobody chose
```

That is a receipt whose extraction row had no invoice date, filed into a live client folder under
tax year **2026-27**, named with **today's date**. 18.2b says a copy there is never withdrawn. It is
the whole of item 112 in one line of output.

After the change: **5 passed, 10 subtests passed.**

---

## 6. Two mutations, because one would have proved half of it

Both anchored on a string asserted to match exactly once, backed up first, diff printed rather than
described, per `CLAUDE.md`'s rule of 2026-09-08.

**M1, the routing never fires:**

```
-            validation_status = "needs_review" if fallbacks else "ok"
+            validation_status = "ok"  # MUTANT M1: never routes to Review
MUTATION never APPLIED (1 site)
```

```
SUBFAILED(field='invoice_date')  test_each_missing_field_sends_the_receipt_to_review
SUBFAILED(field='supplier')      test_each_missing_field_sends_the_receipt_to_review
SUBFAILED(field='gross')         test_each_missing_field_sends_the_receipt_to_review
SUBFAILED(field='currency')      test_each_missing_field_sends_the_receipt_to_review
FAILED  test_nothing_reaches_the_client_folder_when_a_field_fell_back
5 failed, 4 passed, 6 subtests passed
```

**The warning tests correctly stayed green**, because the warnings do not depend on the routing.
That is the brief's step 3 holding as a separable property rather than as a side effect.

**M2, the routing always fires**, which is the failure M1's tests could not see:

```
-            validation_status = "needs_review" if fallbacks else "ok"
+            validation_status = "needs_review"  # MUTANT M2: always routes
MUTATION always APPLIED (1 site)
```

```
FAILED  TheControlTest::test_a_complete_extraction_row_still_publishes_as_ok_and_is_copied
1 failed, 4 passed, 10 subtests passed
```

Neither mutation turns both sets red, which is what makes them a pair rather than two versions of
one check.

**And I checked whether my control was redundant, because step 10as yesterday was about deleting a
test that duplicated another.** Running the whole existing suite against M2 turns two existing tests
red as well:
`test_resume_safety.py::test_recover_validated_receipt_without_filed_path` and
`test_stage4_client_copy.py::TheSweepPublishesRatherThanFilesTest::test_the_sweep_writes_nothing_into_the_client_folder`.
**The control is kept**, because what it adds over those two is the pair of properties 10aq is
actually about: that a complete row's item still says `ok`, and that it logs no fallback warning.
**Its docstring now names those two tests** so nobody reads it as the only guard.

**The existing suite provably does not catch M1**, which is the real defect direction: M1 is exactly
what the code was before this commit, and the suite was green.

---

## 7. Step 4 of the brief: the tests this touches

Enumerated by grep over `tests/`, `.history` excluded, for the sweep and its stats keys.

**Three drive the sweep directly:**

```
tests/test_resume_safety.py:109        app._publish_unpublished_receipts(repo, engine, stats)
tests/test_sidecar_category_keys.py:319 app._publish_unpublished_receipts(repo, engine, {})
tests/test_stage4_client_copy.py:1267  app._publish_unpublished_receipts(repo, engine, {})
```

**Four name it in a source-guard list:**

```
tests/test_client_copy_retry.py:572    "app.py::_publish_unpublished_receipts"
tests/test_post_time_client_copy.py:773
tests/test_publish_trigger.py:438
tests/test_stage4_client_copy.py:349 and :1368
```

**None needed changing**, and none did. All seven pass unaltered. The change adds a status to
existing calls rather than adding or removing one, so the guards that enumerate call sites see the
same set.

New file: `tests/test_recovery_sweep_fallback.py`, 5 tests and 10 subtests.

---

## 8. The suite, and a baseline I had to go and measure

| Point | Result |
| --- | --- |
| Baseline at HEAD, my change stashed | **1387 passed, 1 skipped, 957 subtests** |
| After the change | **1392 passed, 1 skipped, 967 subtests** |
| After the commit, nothing changed | **1392 passed, 1 skipped, 967 subtests** |

Exactly +5 tests and +10 subtests, which is what the new file contains.

**I nearly reported a wrong baseline and caught it by measuring.** My last run yesterday was
1387 passed / **947** subtests, so the first run after this change looked like +20 subtests where my
file only has 10. Rather than explain the extra ten, I stashed `app.py` and re-ran: **957 without my
change**. The ten arrived with other people's commits landing on this branch between sessions,
`92f7d20` and `f167b2b`, which reclassified thirteen steps in `2026-07-25_CONSOLE_DESIGN.md`. Some
test subtests over that document's rows.

**The lesson is the one `CLAUDE.md` already states and I had to relearn:** a baseline is a
measurement of the tree you are on now, and this branch has two other sessions committing to it.
Carrying yesterday's number forward is the same fault as carrying yesterday's date forward.

**The post-commit run was done because this commit adds a file**, per the rule from step 10n. Green.

---

## 9. MY OWN MISTAKE: I committed two files that were not mine

**Disclosed because it was a real error against another session's live work, and because it is the
second time this week a commit has picked up more than intended.**

`git add app.py tests/test_recovery_sweep_fallback.py` staged two files. The commit that followed
contained **four**: `2026-07-25_CONSOLE_DESIGN.md`, modified by another session while I worked, and
`PROMPT_claude_code_2026-09-14_delivery_log_writer.md`, a brief that appeared in the root during this
session. Neither is mine and I have read neither.

I noticed it in the commit's own output, `4 files changed`, having expected two.

**Fixed before anything was pushed**, with the commit still local:

1. `git reset --soft HEAD~1`, which undoes the commit and touches nothing on disk.
2. `git restore --staged` on the two files, which unstages without altering their contents.
3. `git status --short` read back: the design document is ` M` unstaged again and the brief is `??`
   untracked again, exactly as they were.
4. Recommitted. `2 files changed`.

**Nothing of the other session's work was altered, committed or lost**, and the working tree copies
are byte-identical to what they were, having never been written to.

**What I still cannot account for is why they were staged**, and I am not going to guess. The most
likely candidate is the `git stash push app.py` and `git stash pop` I ran while isolating the subtest
baseline, but I did not verify that and will not assert it. **The habit that catches it regardless is
to read `git status --short` immediately before committing rather than immediately after**, and I
read it after.

---

## 10. Flags

Three, none fixed, each with the obvious fix.

**FLAG 1. `tax_year` in the sweep is assigned and never used.** `determine_tax_year(invoice_date)` at
what is now `app.py:753`, with no reader anywhere in the function; the tax year that matters is
computed inside `copy_for_published_receipt()` from the `invoice_date` passed to it. So amendment
405's "the invented `invoice_date` decides the tax year" is true of the system and NOT because of
this line. **Obvious fix: delete the line.** One line, no behaviour. I left it because the brief said
to change no other part of the sweep, and because deleting it is the sort of thing that looks
unrelated in this commit's diff.

**FLAG 2. `file_review()`'s docstring names a reader that no longer reads it.**
`_review_dir_for_client_id()` in `worker/filing.py` ends "`scanReview()` in
IntelliBooks-Desktop-v3.html is the reader, sub-step 10d.59, and the two halves have to move together
or the Review list is empty." Since 10f.15 `scanReview()` reads the published inbox and the string
`Intellibills\Review` is absent from that file, so the Review folder now has no reader at all.
**Obvious fix, and it removes rather than adds:** correct the docstring to say the folder is a local
record with no reader since 10f.15, striking the old sentence. If the folder genuinely has no reader
and no purpose, the larger question is whether the write should exist, and that is a decision rather
than an edit, so I have not proposed it as one.

**FLAG 3, small. A stale cross-reference in `tests/test_resume_safety.py`.** Its comment at line 50
says "test_an_unresolved_client_is_not_filed below is the other half of that". That file has exactly
one test and no such function; a grep finds the name nowhere in `tests/`. **Obvious fix: delete the
sentence**, or repoint it if you know where that test went.

---

## 11. What I judged rather than measured

Asked for by the brief's closing line.

1. **Section 3, publishing a review item rather than withholding it.** The measurement is certain;
   what it means for Paul's wording is a judgement. This is the one to look at.
2. **Not calling `file_review()`.** Measured that nothing reads the folder; judged that adding a
   write with no reader is outside "no change to any other part of the sweep".
3. **Using `review_flags_issued` rather than a new stat key.** Judged from the brief's "use the same
   mechanism": the normal path counts a Review routing under that key, so the run summary counts all
   of them together. A new key would have hidden the sweep's in a name of its own.
4. **Keeping the control test after finding two existing tests also catch M2.** Judged that its two
   unique assertions earn it, and recorded the overlap in its docstring rather than leaving the
   claim broad.

Everything else in this report is measured: the four fields and their fallback values, the tax-year
consequence, where Desktop's Review queue reads from, what holds an item there, what
`copy_for_published_receipt()` refuses, the test enumeration, and the suite counts.

---

## 12. Confidence

**High on the behaviour**, resting on the red output in section 5, the two mutations in section 6,
and rows and folders read back rather than return values trusted.

**High on where Desktop's Review queue reads from**, resting on `scanReview()` and `itemIsHeld()`
read in the live file, plus a zero count for `Intellibills\Review` in it.

**Medium on the decision in section 3**, which is a judgement about Paul's intent against explicit
wording that says the opposite. The evidence is one-sided but the call is his.

**High that nothing of the other session's work was harmed by section 9's mistake**, resting on
`git status --short` read back after the correction and on the fact that no step in the recovery
wrote to either file.

---

## 13. Nothing pushed

One commit, `9869a63`, on `feat/console-phase0`, which is 3 ahead of `origin`. The other two ahead
are yesterday's, already reported.

**Recommended: read section 3 first.** If you are content with publish-as-review, push. If you want
the literal "instead of publishing", say so and tell me where such a receipt should surface, because
on today's code the answer is nowhere.

Flags 1, 2 and 3 need a yes before I touch them.
