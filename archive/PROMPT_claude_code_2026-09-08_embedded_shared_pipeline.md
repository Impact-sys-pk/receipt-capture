# Brief: sub-step 10f.32, the embedded-image path uses the shared pipeline

**Written 2026-09-08 by the consultant session, on Paul's instruction the same day.**
**Report to `2026-09-08_REPORT_claude_code_embedded_shared_pipeline.md` in this repository root.**

**This is sub-step 10f.32 of `2026-07-25_CONSOLE_DESIGN.md`, added 2026-09-08 by amendment 269,
and it is worked first of everything left in step 10f.** Read that sub-step before this brief.

---

## 1. The fault, and it is your own flag 1

**The `embedded_images` loop in `app.py` does not call `process_extraction_result()`.** The other
three intake paths do. Established by parsing `app.py` and listing every call inside the loop:
`process_extraction_result()`, `file_receipt()` and `categorise()` are all absent.

**So a receipt arriving as a photo in the body of an email is extracted, validated and written to
the database, and then nothing else happens to it.** It is `status = ok` with `filed_path` NULL. It
is never categorised, never copied into the client folder, and never reaches IntelliBooks. **Nothing
reports it.**

**Unexercised, and this is why it is a step rather than an emergency.** Read live from
`C:\Intellibills\db\receipts.db` on 2026-09-07 with sqlite3 in read-only mode: **no receipt is `ok`
with a NULL `filed_path`.** 16 receipts, 12 `desktop`, 1 `email`, 1 `phone`, 2 `other` both
discarded, and the one emailed receipt arrived as an attachment and was filed. **It goes live the
first time a client uses a share button rather than a paperclip.**

## 2. What has to be true when you are done

**The embedded-image path calls `process_extraction_result()` and takes its returned status.**

**It is a deletion plus a call rather than new machinery.** The loop already holds every argument
that function takes, checked name by name against its signature: `receipt_id`, `extraction`,
`file_path`, `filename`, `firm_id`, `client_id`, `source`, `message_id`, `att_id`, `file_hash`, the
repository, the engine, `stats`, `run_id` and `pipeline_version`. **What goes is the loop's own
`validate()`, `save_extraction()` and `_log_receipt()` block. What arrives is the call.**

**Its returned status feeds the routing you built at amendment 268**, so `embedded_outcomes` takes
the status the shared function returns rather than a status this path worked out for itself.

**The duplicate branch stays where it is and is not folded in.** It is a per-image hash decision
taken before extraction, and it belongs to sub-step 10f.33, which is not this brief.

## 3. No new behaviour is being designed, and this is the consultant session's judgement

**Your report called this "a behaviour change with a design decision inside it". The consultant
session disagrees and the disagreement is recorded in amendment 269 so it can be held against the
outcome.** Everything the shared function adds is behaviour the other three paths already have:

- a receipt needing review is filed into `Intellibills\Review\`
- the semantic duplicate check runs, so `possible_duplicate` becomes reachable on this path
- an unresolved client files nothing and the item goes to Review, per 10d.18

**If a genuine decision surfaces while you build it, stop and report it rather than taking it.**
That is the one thing this brief asks you to treat as a hard boundary.

## 4. The exception branch needs deciding and it is the one real question inside the change

The loop's `except` block today writes its own extraction row with `validation_status="failed"`.
**`process_extraction_result()` is called with an extraction, so it cannot be the thing that handles
a raise.** Read the attachment path and see what it does with its own `except`, then do the same
thing here. **Say in the report which shape you chose and why**, and make sure a raise still lands
in `INBOX.Failed Processing`, which amendment 268 established and which a test already pins.

## 5. Out of scope

- **Sub-step 10f.33**, the one ranking across both email paths, and flag 2 of your last report
  which it subsumes. **Do not touch the attachment path's routing block.**
- **Item 174**, the missing `is_duplicate(message_id, att_id)` check on this path. It stays absent.
- Everything else in step 10f. **Section 18.2b's freeze stands**: `get_client_directory()`,
  `file_receipt()` and `make_enriched_sidecar()` are not edited. **Note that
  `process_extraction_result()` calls `file_receipt()`, and calling a frozen function is not
  editing it.**

## 6. Standard of evidence

- **Red before green**, quoted. The test that matters most is the one that already exists in shape:
  drive one good receipt down the embedded path and assert `filed_path` is set and a
  categorisation row exists. **Your own flag 1 printed exactly that comparison; make it a test.**
- **Drive both email paths and print the same columns for each**, `status`, `filed_path` and the
  categorisation count, so the two can be read side by side. **Produced by the test rather than
  transcribed.**
- **Mutate from a pristine copy, each mutation anchored to one place with its diff printed**, which
  is the standard you set yourself in the last report and it worked.
- **Every outcome still routes as amendment 268 built it.** `ok`, `needs_review`, `failed` and a
  raise, plus the mixed cases and the all-duplicates case. **A regression here is the main risk of
  this change**, because the status now comes from somewhere else.
- **Quote passes and subtests separately.** Your last report's only finding came from a subtest
  count moving while passes rose.
- **Flag, do not fix. Disclose your own mistakes. State confidence and say what it rests on.**

## 7. What the report has to carry

`2026-09-08_REPORT_claude_code_embedded_shared_pipeline.md`, in this repository root.

1. The enumeration of every call inside the `embedded_images` loop, before and after.
2. The red output, and the both-paths table of `status`, `filed_path` and categorisation count.
3. The mutation results, each with its diff.
4. Which shape you chose for the exception branch and why.
5. Proof that amendment 268's routing still holds on every outcome including the mixed cases.
6. The suite, passes and subtests, measured both ends.
7. Anything you flagged, and anything this brief got wrong.
