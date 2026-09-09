# Brief: stage 1 piece 3, the pipeline publishes

**Written 2026-09-09 by the consultant session. For Claude Code, the implementation session.**

**Scope: sub-steps 10f.2, 10f.4, 10f.5, 10f.6, 10f.7 and 10f.36 of `2026-07-25_CONSOLE_DESIGN.md`.**
Nothing else in step 10f is in scope. **Nothing here is open.** Every decision this work needs is
recorded, and where you find one that is not, stop and say so rather than taking it.

---

## 1. Read before starting

1. **Section 18.2a** of `2026-07-25_CONSOLE_DESIGN.md`, the practice root tree, and **18.3**, the
   handoff. 18.3's interim note matters: the pull that exists today continues.
2. **Section 16, sub-steps 10f.2 and 10f.4 to 10f.7, and 10f.36.**
3. **Amendments 279, 280, 281, 282 and 283** in that document's amendment record. 280 fixes three
   names, 282 settles the `version` key, 283 settles the four points this brief rests on.
4. **`CLAUDE.md`**, the standard-of-evidence section including the six rules added on 2026-09-08,
   and the seven traps.
5. **Section 0.5 and 0.5.1** of `2026-07-31_PLAN_reset_and_restructure.md`. The freeze and the
   acceptance test. **The test is stage 3 and is not yours.**

## 2. What is already true, established rather than assumed

- **`Intellibills\firms.json` holds one firm record carrying `publish_destinations`**, set by Paul on
  2026-09-08 through the Firm Settings page and read back off the file: `{"intellibooks": "Incoming"}`.
  The file is a wrapper, `{"version": 1, "firms": [ ... ]}`.
- **`config.load_firms()` copies every key off the record with `dict(record)` and validates none of
  them**, so the new key is already reaching `config.FIRMS` and nothing refuses it.
- **`config.py` has no constant for the `IntelliBooks\` tree.** Every root constant there hangs off
  `INTELLIBILLS_ROOT`, which is the practice root plus `Intellibills`.
- **`CLIENT_TOP_FOLDER_FIELD` is the precedent for holding a firm-record field name as a constant**,
  and **`_client_top_folder()` is the precedent for reading one with no default**, refusing when the
  file names no firm, names more than one, or holds the field blank.
- **`resolution_events` in `worker/database/schema.py` is the precedent for one row per event.**
- **There is no publish code in the pipeline.** Every occurrence of "publish" in the Python concerns
  the IntelliCharts chart bundle.
- **`receipts` carries `filed_path` and `filed_at` and nothing for publishing.**

## 3. What is decided, so nothing is chosen while building

| # | Decided | Where |
|---|---|---|
| 1 | The destination folder is the practice root, then `IntelliBooks`, then the value of `publish_destinations["intellibooks"]`. **The setting is the leaf only** and the `IntelliBooks` level stays in code, because 18.2 gives that tree to IntelliBooks | Amendments 280 and 283 |
| 2 | The key inside the object is exactly `intellibooks` | Amendment 280 |
| 3 | The value is a folder name and never a path. Blank, absent, or carrying a separator is refused | Amendments 280 and 283 |
| 4 | **One folder for every client.** The client identity travels inside the item | 10f.4 and 10f.5 |
| 5 | **One JSON file per receipt with the image embedded as base64** | 10f.6 |
| 6 | The item carries **the 19 keys `make_enriched_sidecar()` in `worker/filing.py` returns**, plus the image and its media type | Amendment 283 |
| 7 | The item is `{receipt_id}.json`, written under a temporary name and renamed | 10f.7 and amendment 283 |
| 8 | The publish record is **a new table on the `resolution_events` pattern**, one row per receipt per destination per attempt | 10f.36 and amendment 283 |
| 9 | **The first run publishes only receipts arriving from then on.** The 16 already in `receipts.db` are not published | Amendment 283, Paul's decision |
| 10 | `version` in `firms.json` does not move | Amendment 282 |

## 4. What to build

**Five deliverables. Commit after each.**

1. **The setting reader.** `publish_destinations` off the single firm record, **no default and no
   fallback**, on the model `_client_top_folder()` already uses. Hold the field name as a constant
   the way `CLIENT_TOP_FOLDER_FIELD` is held. **Refuse, at import, with a message naming the field,
   the file and the Firm Settings page:** no firm, more than one firm, the key absent, the
   `intellibooks` entry absent or blank, or a value that is not a single folder name. **A value with
   `\` or `/` in it is refused**, because the setting is a leaf and a path there would compose into
   somewhere nobody looks.
2. **The destination path.** The practice root, then `IntelliBooks`, then that value. There is no
   constant for the middle level today and it needs one, derived from `PRACTICE_ROOT` and not from
   `INTELLIBILLS_ROOT`. **Create the folder if it is absent**, the same way the pipeline's own roots
   are made.
3. **The item writer.** One JSON file per receipt, named `{receipt_id}.json`, **written under a
   temporary name in the same folder and renamed into place**, so a half-written file can never be
   read. Payload: the sidecar's 19 keys, plus the image bytes base64-encoded and the media type.
   **Read `make_enriched_sidecar()` and reuse its key set exactly. Do not modify that function**: it
   is frozen by 18.2b and the freeze holds through stage 1.
4. **The publish record.** A new table, one row per receipt per destination per attempt, that
   distinguishes **no row at all** from **an attempt that failed** and from **one that succeeded**,
   carrying at least the receipt, the destination, the outcome, the time, and the reason on a
   failure. Add it to `worker/database/schema.py` so one definition is the only definition.
5. **The trigger.** A receipt that reaches `ok` is published, once. **A receipt that is not `ok` is
   not published**, and neither is a `possible_duplicate`: 10f.24 makes that explicit and is not in
   this scope, so simply do not publish anything whose status is not `ok`. **Publishing failing must
   not fail the receipt**: record the failure and carry on, because the filing route is still live
   and is what IntelliBooks reads today.

## 5. What must not change

- **The on-arrival write into `Clients\` continues.** Stage 1 is additive. Nothing changes route and
  nothing Paul does differs.
- **18.2b's freeze holds** on `get_client_directory()`, `file_receipt()` and
  `make_enriched_sidecar()`. Read them; do not edit them.
- **The recovery sweep is not touched.** Repointing it is stage 4, sub-step 10f.13.
- **Nothing in `IntelliBooks-Desktop-v3.html` changes.** Desktop does not drain the folder until
  stage 2, so the folder fills and nothing reads it. **That is the point: the worst outcome of a
  defect here is a file nobody opens.**
- **No existing receipt is published.** Deliverable 5 applies to arrivals only.

## 6. Evidence

The standard in `CLAUDE.md`, and four of its rules bite here in particular.

- **Red before green**, with the failing output quoted. Where a test cannot come first, mutate the
  behaviour from a pristine copy and show which tests catch each mutation and that no others do.
- **A mutation is anchored to one place and prints its own diff.** The two email loops in `app.py`
  are close to line-for-line copies, so an anchor inside one must carry something the other lacks.
- **Enumerate calls from the syntax tree, not by grepping**, and compute the enclosing loop rather
  than eyeballing indentation.
- **A guard over the set, not over its members.** If publishing has more than one call site, assert
  on the source that no unwrapped write remains and that the count of wrapped ones is what you
  expect. A per-path test proves a path works; only a guard over the set proves the set is complete.

**Also state:** what the suite reported before and after, with the subtest count; whether
`INTELLIBILLS_PRACTICE_ROOT` and `INTELLIBILLS_UNSYNCED_ROOT` were set for the run; and the commit
hashes, one per deliverable.

**Commit before any run whose `pipeline_version` matters.** A run started on a dirty tree records a
version that does not describe the code that ran.

## 7. What to report, and where

**Write the report to `C:\LastingImpact\receipt_capture\2026-09-09_REPORT_claude_code_stage1_piece3_publish.md`.**
Paul is the only channel between the sessions, so a report with no path makes him the copy-typist.

Cover, in this order:

1. What was built, per deliverable, with its commit.
2. **What the brief got wrong.** Anything named here that is not where this brief says it is, or that
   does not do what it says. That section has found real defects on this project every time.
3. **Every decision you had to take that this brief did not settle**, and what you chose. If one
   arrives that is Paul's, stop and say so rather than taking it.
4. The tests added, the mutations tried and which tests caught each.
5. **Flags: anything wrong that this brief did not ask about.** Report it, do not repair it. If it is
   small and obviously right, say so and offer it.
6. Your own mistakes, including ones you caught and corrected.
7. A confidence level per claim, saying what it rests on and what it is about.

## 8. Traps

**`CLAUDE.md` holds seven and is the authority.** Three bite this work:

- **Exclude `.history\` from any repository-wide search.** It holds a dated copy of every file edited.
- **`grep -c` counts matching lines, not occurrences.** If the figure matters, count characters.
- **A check that cannot fail is not a check**, and the tell is that it has never returned anything
  but a pass.
