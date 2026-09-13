# Report: two places an attached document reaches and should not

**Claude Code, 2026-09-12.** From `PROMPT_claude_code_2026-09-12_attached_documents.md`. Amendment
345, Paul's decisions of 2026-09-12.

**No md5 was supplied with this brief.** The file I read hashes to
`d26e84faea101a540206b2d0b6d45c1c`, which matches the row in
`2026-09-12_HANDOVER_consultant_session_24.md`. Recorded so it can be checked rather than assumed.

**One commit on `feat/console-phase0`, not pushed: `366ecc9`.** Four files, 541 insertions, 6
deletions.

**The suite: 1384 passed, 1 skipped, 946 subtests**, run again after the commit and green there too.
It was 1366 before this work.

---

## 1. For Paul

### What `processed_today` will read now that it did not before

**On your own database, the figure will usually be the same or lower, never higher.** Three kinds of
row stop counting:

| Stops counting | Why |
|---|---|
| **A document attached to a bank line in IntelliBooks** and handed over to be archived | It was never read. Not extracted, not validated, never published. Sub-step 10f.38. |
| **A receipt still waiting to be read**, at `pending` | `save_receipt()` writes that before anything has looked at the document. |
| **Anything that arrived just after midnight UTC on a British summer evening** | The day is now the London day. See below. |

**Still counting**, and these are decisions rather than defaults:

| Still counts | Why |
|---|---|
| **A discarded receipt** | It was READ before it was discarded. |
| **A failed extraction**, and one that exhausted its retries | The pipeline read the document and could not get data off it. That is work done. |
| **A possible duplicate** | Read, extracted, then found to look like another. |
| **A platform statement** | It is something the pipeline read. Unchanged from before. |

**Nothing you can see today changes**, because **nothing reads the field**. That is the point of
fixing it now: the console's intake panel at 8.6 is the reader it was built for and is not built, so
no reader has to be migrated and no number anybody is looking at moves.

### What a back-feed note can no longer match

**A resolution note that carries no receipt id can no longer be applied to a document attached to a
bank line.** It found one by filename before, and if that was the only match it was applied to it.

**The ambiguity refusal is unchanged**: two genuine candidates is still not a match and still logs an
error.

**One case changes and it is worth a sentence.** Where a filename matched two receipts and one of
them was an attached document, that was a refusal and is now a match on the remaining one. **That is
right rather than a loosening**: the attached document was never something the note could have been
about, because it came from the books rather than from capture and has no review sidecar for a note
to have come from. **Removing something that was never a candidate does not resolve an ambiguity; it
shows there was not one.** There is a test for exactly that case.

---

## 2. What the brief said to establish, established

### Every status a `receipts` row can hold, re-run rather than quoted

The brief points at `2026-09-11_REPORT_claude_code_capture_report.md` section 4 and says to re-run
it. Re-run from the syntax tree through `tests/test_capture_report.py`'s own
`statuses_from_source()`:

```
8 statuses enumerated from the syntax tree:
    bank_attachment
    discarded
    failed
    needs_review
    ok
    pending
    possible_duplicate
    retry_exhausted
```

**It has not moved.** Eight then, eight now, the same eight.

**Which of them mean the pipeline read the document**, as `PROCESSED_STATUSES`:

```
COUNTED (6):     ok, needs_review, possible_duplicate, failed, retry_exhausted, discarded
NOT COUNTED (2): pending, bank_attachment
```

`test_every_status_the_pipeline_can_reach_is_decided_one_way_or_the_other` asserts the union of those
two sets equals the enumerated set and that they do not overlap, **so a ninth status is a decision
rather than an accident** rather than quietly falling out of the count.

### Every reader of `processed_today`

**Zero in production.** The brief says to stop and say so if I found one. I did not.

52 textual mentions across the 382 git-tracked files, and every one is the design document, a report,
an archived brief, a handover, or this repository's own write path:

```
app.py:193    the parameter of _write_pipeline_status()
app.py:224    the key it writes
app.py:2031   the call that produces the value
tests/test_status_counts_from_db.py   asserts it
tests/test_attached_document.py:734   names it in a list of methods
```

**And IntelliBooks Desktop, which is not in this repository, read directly from OneDrive:**

```
IntelliBooks-Desktop-v3.html: 431,468 bytes
   occurrences of 'processed_today': 0
   occurrences of 'pipeline-status':  9
```

So the brief's count of nought is right, **and I checked it against the file rather than taking it**.
`renderPipeStatus()` reads `last_run`, `last_error` and `practice_root` and nothing else, which is
what 19.4 already records.

### The two call sites

```
count_processed_today()      PROD  app.py:2031  in process_once           TESTS 1
find_receipts_by_filename()  PROD  worker\resolution\service.py:1868      TESTS 0
                                   in _receipt_for_note
```

**Exactly one production caller each**, which is what makes both changes cheap.

---

## 3. The three things decided and reported rather than chosen quietly

**One. A discarded receipt counts.** The brief says there is an argument both ways and asks which I
took.

**It was read before it was discarded**, and the pipeline's work on the document is not unmade by a
person's later judgement about it. **And the alternative produces a worse figure**: a count that fell
retroactively as the day went on, because somebody discarded something the pipeline had already read
and counted, is a number an intake panel cannot be trusted with.

**Two. The day is the London day.** The brief says not to change it silently either way.

`pipeline-status.json` keeps UTC for `last_run`, which is a **timestamp**. This is not one. **It is a
count whose whole meaning is the word "today", and "today" is a word about the reader's calendar.**
The London work of 2026-09-11 settled that what a person reads is in their own clock, and
`capture_report.py`'s date range already selects on the London day, **so a count on the UTC day would
disagree with the capture report about the same day**, which is the half-change that work exists to
avoid.

**The bounds are computed as instants, not as a date**, because a London day is 23, 24 or 25 hours
long. `DATE(created_at) = DATE('now','utc')` cannot express that and neither can comparing the first
ten characters of a stored timestamp. `london_day_bounds()` builds tomorrow's midnight from
tomorrow's **date** rather than by adding 24 hours, which is the difference on the day the clocks go
back, and there is a test asserting that day is 25 hours.

**Three. `statements` are still counted and are not status-filtered.** The brief does not mention
them and the query counts them, so this is a case the brief did not cover. **A platform statement IS
something the pipeline read**, `filed` is the only status `save_statement()` gives one, and narrowing
them would be widening the change beyond what was asked. **Reported because it was not covered**, not
because it was hard.

---

## 4. Evidence

### Red before green

The new tests, run against the unchanged code:

```
13 failed, 5 passed

E   AssertionError: 'status IN' not found in "...SELECT COUNT(*) FROM receipts
    WHERE DATE(created_at) = DATE('now','utc')..." : the count has no status
    filter, so it counts every row created today again

FAILED TheFilenameFallbackTest::test_a_note_with_no_receipt_id_does_not_match_an_attached_document
FAILED WhichDayTest::test_the_bounds_are_the_london_day_and_not_the_utc_day
```

**Driven through the real writer, as the brief requires.**
`test_a_handed_over_document_is_not_counted` calls `hand_over()` and then a real `app.process_once()`,
so `record_attached_document()` writes the row. **It asserts the row's status is
`config.BANK_ATTACHMENT_STATUS` before it asserts the count**, so a test that had stopped driving the
writer it thinks it drives fails on that line rather than passing on a count of nought.

**And there are controls**, because a count that returned nought for everything would satisfy three
of these tests: `test_a_receipt_the_pipeline_read_today_is_counted`,
`test_it_still_matches_an_ordinary_receipt` and
`test_the_ambiguity_refusal_still_fires_on_two_real_candidates`.

### Mutations

Five, each anchored once, each printing its diff, each restored byte for byte, each against the whole
suite.

| Mutation | Expected | Result |
|---|---|---|
| `drop-the-status-filter-from-the-count` | caught | **caught, 3 failures** |
| `count-the-utc-day-again` | caught | **caught, 1 failure** |
| `drop-the-exclusion-from-the-caller` | caught | **caught, 2 failures** |
| `remove-the-ambiguity-guard` | caught | **caught, 2 failures** |
| `prose-only-control` | survives | **survived** |

**Two things worth reading rather than counting.**

**`count-the-utc-day-again` is caught by exactly one test**, and the margin is worth knowing. The
mutation still computes instants, so only
`test_a_receipt_in_the_last_hour_of_the_utc_day_counts_tomorrow` fails: it seeds one receipt thirty
minutes inside the London day and one thirty minutes outside it, built from the real bounds so it
holds in either season. One test, and it is the right one, but that is the whole of what stands
between this and the UTC day coming back.

**`remove-the-ambiguity-guard` was caught by a pre-existing test as well as by mine**,
`tests/test_resolution_backfeed.py::UnknownReceiptTest::test_an_ambiguous_filename_match_is_not_a_match`.
The guard was already protected and I did not weaken it.

### What must not change, checked

- **No stored value moved.** No migration, no backfill, no rewrite. Both changes are read paths.
- **`pipeline-status.json` keeps its five keys and its shape**, asserted by the two existing tests in
  `tests/test_status_counts_from_db.py` that compare the key list, which still pass.
- **Nothing published, re-processed, re-extracted, and no receipt's status moved.**
- **`find_receipts_by_filename()` is untouched**, and a test asserts it still returns an attached
  document, so the exclusion is provably the caller's rule and not the query's.
- **Nothing written into `Clients\`, `IntelliBooks\` or `Intellibills\Documents\`.**
  `IntelliBooks-Desktop-v3.html` was READ and not written.
- **`import config` was never used to read a value** outside pytest.

### Committing and the index

**Committed by naming four paths.** Files the brief forbids committing were modified in the working
tree throughout, by the consultant session, and a fifth appeared while I worked:

```
 M 2026-07-25_CONSOLE_DESIGN.md
 M 2026-08-18_BOUNDARY_two_products.md
 M 2026-08-20_LIST_outstanding_items_and_decisions.md
 M 2026-08-20_LIST_settings_firm_and_client.md
 M PROMPT_claude_code_2026-09-11_london_time_and_output_paths.md
?? 2026-09-12_HANDOVER_consultant_session_25.md
?? PROMPT_claude_code_2026-09-12_attached_documents.md
```

**All of them are still exactly that after the commit, and the index is empty.** Verified afterwards.

**The suite was run again after the commit**, since the change adds a file. Green.

---

## 5. Flags. Nothing here was fixed

**Flag 1. `london_day_bounds()` lives in `worker\database\repository.py` and is not a database
concern.** It is a time conversion, and `worker\london_time.py` is where the other five live. It is
here because it is read by exactly one query and putting it beside that query keeps the reasoning
with the SQL it shapes. **Obvious fix: move it to `worker/london_time.py` and import it**, which is
one line each way and no behaviour change. **Not taken**, because the brief names neither file for
that and a second consumer has not appeared. If one does, move it then.

**Flag 2. The suite has slowed markedly and the mutation runs are now the cost.** It was 98 seconds
on 2026-09-12 morning and is 100 to 280 seconds now, varying by run. A five-mutation set took about
20 minutes against 8 this morning. **Obvious fix: none proposed, because I have not measured WHERE
the time goes**, and proposing a fix for an unmeasured slowdown is the shape this project's own trap
list objects to. What is worth knowing is that mutation work is becoming the expensive part of a
brief, and that the variation between identical runs is large enough that the figure should not be
read as a trend from two points.

**Flag 3. `review_count` is written on every cycle and read by no production code**, exactly as
`processed_today` was. **Not flagged as a defect**, because section 19.4 already says in terms that
this is recorded rather than flagged and is neither decided nor scheduled. Named here only so it is
not mistaken for something this change addressed: **it did not, and it is unchanged.**

---

## 6. My own mistakes

- **My resolution-note fixture was missing `values.invoice_date`**, which
  `parse_resolution_note()` requires for a `filed` note, so four tests errored on the note rather
  than on the thing they were testing. Found from the red run.
- **My `save_statement()` call used `firm_id`, `period_start` and `period_end`**, none of which are
  that function's parameters. I wrote the call from what a statement sounds like rather than from the
  signature, which is this project's own rule about reading the thing itself, broken in a test I was
  writing to check a claim about the thing itself.
- **I left a dead line in `london_day_bounds()`** in the edit script, a first attempt at tomorrow's
  midnight sitting immediately above the working one. Caught by reading the script back before
  applying it, so it never reached the repository.

---

## 7. Confidence

**High, that a handed-over document is no longer counted.** It rests on a test driven through
`record_attached_document()` by a real poll, which asserts the marker on the row before it asserts
the count, and on a mutation that drops the status filter and is caught three times. Not on reading
the query.

**High, that a back-feed note cannot be applied to an attached document, and that the ambiguity
refusal is intact.** It rests on four tests covering the exclusion, the control, the two-real-
candidates refusal and the two-where-one-is-attached case, and on two mutations, one of which a
pre-existing test caught as well.

**High, that the set of statuses is completely accounted for.** It rests on an assertion comparing
`PROCESSED_STATUSES` against the statuses enumerated from the syntax tree, so the claim is about the
set rather than about its members.

**Medium, and the proposition is narrow: that the London day is the right choice for this field.** It
is a judgement rather than a measurement, and the brief asked for one. **What I can support is that
it is consistent with `capture_report.py` and with the London decision of 2026-09-11. What nobody can
support yet is what the console's intake panel will want**, because it is not built and its reader is
hypothetical. **If the panel turns out to want the UTC day, this is a one-line change and the test
that would go red is named in section 4.**

**Not verified: the figure on your machine.** Nothing was run against
`C:\Intellibills\db\receipts.db`, the pipeline was not started, and I have not seen what
`processed_today` currently reads or what it would read after this. The change is a read path, so
running the pipeline once is all it takes to see it.
