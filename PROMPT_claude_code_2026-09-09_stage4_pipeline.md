# Brief: stage 4, the pipeline half. The old route stops and Intellibills owns the client folder copy

**Written 2026-09-09 by the consultant session. Sub-steps 10f.11, 10f.12, 10f.13 and 10f.16 of
`2026-07-25_CONSOLE_DESIGN.md`, plus amendment 293's widened publish.**

**Stage 4 of `2026-09-08_PLAN_publish_step.md`. Stage 3 passed on 2026-09-09 and 18.2b's freeze is
released FOR THIS WORK AND FOR NOTHING ELSE**, per amendment 290. `get_client_directory()`,
`file_receipt()` and `make_enriched_sidecar()` in `worker\filing.py` may finally change, and only for
what is in this brief.

**This is the stage that can lose a receipt.** Three stages exist before it for that reason.

**There is a Desktop half and it lands in the same window.** It is the consultant session's and is
not briefed here, per amendment 242. **Nothing in this brief may be committed on the assumption that
the Desktop half is already in place, and nothing in it depends on the Desktop half either.** The
ordering across the two is Paul's to run and is in section 7.

---

## 1. Read first

1. **Amendments 290, 292, 293 and 296** of `2026-07-25_CONSOLE_DESIGN.md`. 293 and 296 are the two
   that change what stage 4 is, and neither is in the plan document.
2. **Section 18.2b**, all of it, including the rules table. **The image-only rule is a deliverable
   here and it is easy to read past.**
3. **Section 16, sub-steps 10f.11 to 10f.17**, including 10f.13's three-caller table.
4. `CLAUDE.md`, the standard of evidence and the seven traps. **The fourth trap bit this project on
   2026-09-09: never `import config` to read a value, on Windows as well as Linux.**

---

## 2. What is wrong today, established rather than asserted

- **Three call sites write into `Clients\` and the sub-step names one.** The table at 10f.13 lists
  them, corrected by amendment 278 from the syntax tree: the arrival write, the completed review item,
  and a recovery sweep in `app.py` that no design document had recorded.
- **The recovery sweep files rather than publishes.** It runs at the top of every poll and files
  anything that is `ok` with a NULL `filed_path`. **Paul's decision of 2026-09-08 is option B: the
  sweep survives, repointed to publish.** It becomes "publish anything that was read and never
  published", which is why 10f.36 exists.
- **The copy into `Clients\` carries a sidecar today and 18.2b says image only.**
- **Publishing fires only on `ok`.** Verified from the syntax tree on 2026-09-09: one call site,
  inside `if validation.status == "ok"`. **Amendment 293 widens it.**

---

## 3. Deliverables

**Deliverable 1. The client folder copy is Intellibills' own function and the only writer.**
Sub-step 10f.11.

- One function. **No other code writes into `Clients\` after this.**
- **Image only.** No sidecar, no data file of any kind beside it. 18.2b's rules table.
- The document date names the folder and the file, which is what the existing convention already
  produces. Not the transaction date.
- A copy is **never withdrawn**, and a second write for one receipt must not produce a second file.

**Deliverable 2. The trigger is a firm setting with no default and no fallback.** Sub-step 10f.12.

- The field is **`client_copy_trigger`** on the firm record in `Intellibills\firms.json`. **It is
  already built and Paul's value is already set**, so this deliverable is the reader alone.
- Its three values are **`publish`, `post` and `never`**, and they are the exact words on the record.
- **Refuse at import on anything else**, on `_publish_destination()`'s model, with a message naming
  the field, the file and the Firm Settings page.
- **`publish` copies on a successful publish. `never` copies nothing.**
- **`post` is the one with no mechanism yet.** Decide what a `post` firm does between now and the
  message existing, say what you chose, and **do not build a Desktop-to-pipeline message in this
  brief**: that crosses into the Desktop half and into 10f.16.

**Deliverable 3. The on-arrival write stops at all three call sites.** Sub-step 10f.13.

- **Enumerate the writers from the syntax tree before and after**, and assert the set is empty
  afterwards apart from deliverable 1's own function.
- **The recovery sweep is repointed, not deleted.** It becomes "publish anything that was read and
  never published", answered from `publish_events` rather than from `filed_path`.

**Deliverable 4. Publishing covers every validation status.** Amendment 293.

- The item carries **`validation_status`**, which is already one of the sidecar's 20 keys, plus **the
  validation notes**, plus **the id it duplicates** where the status is `possible_duplicate`.
- **A `failed` receipt publishes.** Desktop decides what to do with it and must never make a books row
  from it, which is the Desktop half's problem and not yours.
- **A republish must not silently overwrite.** With one status publishing, flag 5 of
  `2026-09-09_REPORT_claude_code_stage1_piece3_publish.md` had nil consequence. With four it does not.
  Check `list_publish_events()` before writing, and say what you do when a row is already there.

---

## 4. What must not change

- **`Intellibills\Documents\` is untouched.** It is the archive of record and every document stays in
  it, rejects and duplicates included, whatever the trigger says.
- **The Review folder keeps being written for now.** Desktop stops reading it in the same window, and
  until both land the folder is what the queue has. **Removing the write is not in this brief.**
- **No schema change.** `publish_events` has the columns it needs.
- **Nothing in the run summary.** Flag 3 is still a separate decision.
- **`IntelliBooks\Incoming\` is not read by the pipeline.** It belongs to Desktop.

---

## 5. Standard of evidence

- **Red before green**, with the failing output quoted.
- **Enumerate every set claim from the syntax tree and print it whole.** The writers into `Clients\`,
  the publish call sites, and the statuses that publish are three set claims and each has been wrong
  on this project at least once.
- **A guard over the set, not over its members.** A per-path test proves a path; only a guard proves
  the set is complete. **This is the brief where that matters most**, because a fourth writer nobody
  listed is exactly what amendment 278 found.
- **Mutations anchored to one place**, each asserted to match exactly once, each printing its own
  diff. **The two email loops in `app.py` are near line-for-line copies, so an anchor inside one must
  carry something the other lacks.**
- **A stub models what the real function does.** A stub that records a call rather than doing the
  work would report a copy that never happened.
- **Do not cite a line number in `config.py` or `app.py`.**
- **Flag, do not fix.** Disclose your own mistakes. Say what each confidence rests on and what it is
  about.

---

## 6. The completion test, and it is not yours to run

**Check 1 of section 0.5.1 of `2026-07-31_PLAN_reset_and_restructure.md`, in its two clauses**,
reworded 2026-09-09 by amendment 292. Paul runs it.

- **Clause A**, with `client_copy_trigger` set to `never`: a receipt travels from capture to the books
  and two full listings of `Clients\` are identical.
- **Clause B**, with it set to `publish`: the same journey adds exactly one file to `Clients\`, the
  document for that receipt, and nothing else.

**Write nothing that could pass clause A by publishing nothing.** Both clauses require the receipt to
reach the books.

---

## 7. Landing order, because the two halves cannot land at one instant

Paul is the only channel, so state in your report **which of your deliverables are safe to run against
today's Desktop**, and which are not. The known constraint from the other side: **Desktop stops
reading `Clients\` before the copy becomes image only**, per amendment 296. Nothing you build should
assume that has already happened.

---

## 8. Where to write the report

**`C:\LastingImpact\receipt_capture\2026-09-09_REPORT_claude_code_stage4_pipeline.md`.**

Carry in it: what was built, the commits, the suite before and after, every set enumeration printed
whole, every mutation and its result, every decision this brief did not settle and what you chose,
every flag, and your own mistakes.
