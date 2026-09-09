# Brief: the duplicate check stops depending on `filed_path`, and the client folder handles its own collisions

**Written 2026-09-09 by the consultant session. Sub-steps 10f.24 and 10f.25 of
`2026-07-25_CONSOLE_DESIGN.md`, and amendment 303.**

**Two deliverables, both small, and one of them is your own flag 1 of
`2026-09-09_REPORT_claude_code_stage4_pipeline.md`.**

**Read amendment 303 first.** It settles what the four duplicate sub-steps actually are: 10f.24 and
10f.25 are work, 10f.26 was satisfied by 10f.28 the same afternoon, and 10f.27 is blocked on the
console, which is not built.

---

## 1. Deliverable 1. The semantic duplicate check asks whether the earlier receipt PUBLISHED

**This is your flag 1 and the diagnosis in it is accepted in full.**

The check in `worker\extraction_pipeline.py` asks `is_recorded_and_filed(dup)` before flagging a
possible duplicate. That reads `filed_path`. **After stage 4 a `filed_path` exists only when the
firm's `client_copy_trigger` is `publish`, so on `never` and on `post` no receipt has one and the
check stops flagging anything at all.**

**What it must ask instead: does the earlier receipt have a `published` row.** Amendment 293's fifth
point already names that as the marker, and amendment 303 records the decision.

**Where the change goes, and this is a constraint rather than a preference.**

- **At the one call site, not inside `is_recorded_and_filed()`.** Established here from the syntax
  tree: that helper has four call sites, and the other three are the file-hash dedup in `app.py`.
- **Do not widen the shared helper.** `_move_inbox_pair_to_processed()`'s docstring depends in terms
  on a `needs_review` receipt NOT counting as filed, so that a file an operator puts back by hand is
  deliberately reprocessed. Amendment 293 gives every status a `published` row, so a widened helper
  would make a resent review item look like a duplicate.
- **Enumerate the callers yourself before you change anything** and print the set. If it is not four,
  say so and stop.

**What "settled" should mean is yours to decide and to state.** A `published` row of outcome
`published` is the obvious reading. Say what you chose about a `failed` publish row, and why.

## 2. Deliverable 2. The client folder copy handles a name collision on the bytes

Sub-step 10f.25.

`write_client_copy()` composes `{invoice_date}_{supplier}_{gross}` and hands it to `_unique_path()`,
so a second document that matches on all three lands as `-2` with nothing compared.

**What the sub-step asks for:**

- **Identical bytes: skip.** No second file, and say so in the log.
- **Different bytes: keep the suffix and flag it.** The `-2` still happens, and the log says a
  document with the same date, supplier and amount already sits there with different content.

**Why it is nearly free, in the sub-step's own words:** the filename already carries the three values
a semantic duplicate matches on, so the collision is already the signal. Only the response was wrong.

**Do not change the naming convention.** A listing of `Clients\` taken before and after this change
must differ only where this brief says it differs, and check 1's two clauses stay true.

---

## 3. What must not change

- **One writer into `Clients\`.** `write_client_copy()` stays the only one, and the guard over that
  set stays.
- **The copy still swallows its own failures**, per stage 4.
- **No schema change.** The `published` row already exists.
- **Nothing in the run summary.** That decision is still open.
- **`validate()`'s rules, and what a possible duplicate does next.** A possible duplicate reaches
  Review and does not become a books row on its own, and that already holds on the Desktop side per
  amendment 299. Nothing here changes routing.

---

## 4. Standard of evidence

- **Red before green**, with the failing output quoted.
- **Drive the trigger dimension.** The whole point of deliverable 1 is that the check behaved
  differently on `never`. Your own `DuplicateDetectionDependsOnTheTriggerTest` asserts today's broken
  behaviour, with a message saying that if it goes red the flag has been fixed and it should be
  deleted. **It should now go red. Delete it and put its opposite in place.**
- **Drive both branches of deliverable 2 with real bytes**, identical and different, and assert the
  file count in the folder afterwards.
- **Enumerate `is_recorded_and_filed()`'s callers before and after and print both sets.**
- **Mutations anchored to one place**, each asserted to match exactly once, each printing its own
  diff. **Include one that swaps the `published` test back to `filed_path`**, and it must be caught
  by a test that drives the `never` trigger.
- **Do not cite a line number in `config.py` or `app.py`.**
- **Flag, do not fix. Disclose your own mistakes. Say what each confidence rests on and what it is
  about.**

---

## 5. Where to write the report

**`C:\LastingImpact\receipt_capture\2026-09-09_REPORT_claude_code_duplicates.md`.**

Carry in it: what was built, the commit, the suite before and after, both caller sets printed whole,
every mutation and its result, every decision this brief did not settle and what you chose, any flag,
and your own mistakes.
