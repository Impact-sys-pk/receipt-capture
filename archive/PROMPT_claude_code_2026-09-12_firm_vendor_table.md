# Brief: the firm vendor table gets a writer, and layer 2 gets its first assertions

**Written 2026-09-12 by the consultant session.** Step 10m of `2026-07-25_CONSOLE_DESIGN.md`,
amendment 238, Paul's decision of 2026-09-06 closing item 166.

**Read first, in this order:** `CLAUDE.md`, the section "How this project is worked" and the seven
traps, including the two rules added on 2026-09-11. Then step 10m's body in section 16 of
`2026-07-25_CONSOLE_DESIGN.md`, and amendment 238. Then section 11.3, which is why learning is
opt-in.

---

## 1. Two halves, and the first one is worth more than the second today

**PART A: THE ASSERTIONS AT LAYER 2. This is the step's first task and it is not the writer.**

Step 10m's body says it in terms: the assertions come before the writer. The reason is measured,
not asserted. **No test has ever checked what a matched row stores at layer 2**, because every
`categorisations` row that has ever existed reads `unmatched`. During the `vendor_key` rename a
mutation swapping two fields at layer 1 left the whole suite green for exactly that reason. Two
assertions closed it at layer 1. **The identical swap at layer 2 is still live.**

**PART B: THE WRITER.** `upsert_firm_vendor()` exists and has no caller. The table holds nought
rows. Part B gives it one, under the rule in section 3.

**DO PART A FIRST AND REPORT ITS MUTATION RESULT BEFORE PART B CHANGES ANY PRODUCTION CODE.** If the
layer 2 swap is caught by something already, say so and stop, because then part A is already done
and I have the reason wrong.

---

## 2. What you must establish before writing anything, and do not take it from this brief

**Enumerate, print whole, and say what you found:**

1. **Every write of `categorisations_firm_vendors`** across the production tree, from the syntax
   tree. I have read `upsert_firm_vendor()` and it is the only writer I know of. Prove or disprove
   that it is the only one.
2. **Every caller of it.** I believe there are none. If there is one, this step changes shape and
   you should stop and say so.
3. **Every place a resolution note's chosen category reaches the learning decision.** There are two
   resolution routes and they do not behave the same way: one learns and one has never had a
   learning branch. **Do not take my word for which is which. Find both and print them.**
4. **What a layer 2 match actually stores**, driven through the real engine rather than read off the
   source, in the same shape as the layer 1 assertions that already exist.

---

## 3. The rule for the writer

**From amendment 238, and it is Paul's. Quoted rather than paraphrased.**

- The operator's chosen code is compared with the code the chart check resolved the classifier's
  suggestion to.
- **Equal: both tables are written.** The client table with the operator's code, and the firm table
  with the account out of the shipped receipt-account list that the classifier named, keyed on
  business type and vendor key.
- **Different: the client table only.** Several master codes collapse into one under the chart
  fallback, so the operator's pick cannot be run backwards to a receipt account.
- **The tick governs both**, per section 11.3. A correction with no tick teaches neither table.
- **The confirm case arises only on a classifier answer.** A stored-mapping layer returns a code with
  no suggestion to agree with, and the firm layer already holds anything it would learn.

**Do not widen this on your own judgement.** If the rule does not cover a case you meet, report it
and stop.

---

## 4. A thing you need to know before you measure anything, and it is not a defect

**The classifier is off in the live pipeline.** The pipeline builds its engine with the AI fallback
disabled, at the one construction site in the production tree, which you should enumerate and print
rather than take from this sentence. The consequence:

- **The confirm case in section 3 cannot arise on live data today.** No row will ever be written to
  the firm table until the classifier is turned on.
- **So part B's evidence is tests, and that is expected rather than a shortfall.** Say so in the
  report rather than implying a live proof you cannot have.
- **This is not a reason to change the rule.** It is a reason to state plainly, in your report's
  first section, what would have to be true for the writer to fire.

**Do not turn the classifier on. Do not propose turning it on as part of this step.** It costs money
per receipt and it is Paul's decision, recorded as flag 3 of
`2026-09-11_REPORT_claude_code_category_hold.md`.

---

## 5. What must not change

- **No stored value moves.** No migration, no backfill, no rewrite of existing rows.
- **The client table's existing writer and its behaviour are untouched** except where section 3
  requires the firm table to be written beside it.
- **`categorisations.needs_review` and `match_source` are untouched**, and so is
  `publish.category_is_unconfirmed()`, which step 10l built on `match_source` at amendment 333.
- **Nothing published, re-processed, re-extracted, and no receipt's status moves.**
- **Nothing written into `Clients\`, `IntelliBooks\` or `Intellibills\Documents\`.**
- **Never `import config` to read a value.** Read the constant out of the file or run under pytest.

---

## 6. Evidence

- **Red before green**, with the failing output quoted. For part A that means the layer 2 assertions
  failing against a mutated engine, not against a missing function.
- **The field-swap mutation at layer 2**, the same shape as the one that was live at layer 1, shown
  caught after part A and shown surviving before it. **That pair is the whole point of part A.**
- **A mutation that writes the firm table when the codes differ**, expected caught.
- **A mutation that writes it with no tick**, expected caught.
- **A prose-only control** that survives.
- **Every mutation anchored once, printing its own diff.** Two byte-identical blocks are a real
  hazard on this project: the engine's layers are close to line-for-line copies of each other, so
  any anchor inside one must carry something the other lacks.
- **Enumerate from the syntax tree** anything you assert about a set, and print it whole.
  `.history\` excluded.
- **Run the suite again AFTER committing** if the change adds a file.
- **Flag, do not fix. Every flag carries the obvious fix, and if the fix is to remove something, say
  so first.** Disclose your own mistakes. State a confidence level and say what it is about, not only
  what it rests on.

---

## 7. Committing and reporting

**Commit on `feat/console-phase0`.** Do not push and do not create a branch. Do not commit
`2026-07-25_CONSOLE_DESIGN.md`, any `PROMPT_*` or `HANDOVER_*` file, or anything under
`Test Receipts\`.

**Commit by naming your own paths and check the index afterwards.** Files this brief forbids
committing have been sitting modified in the working tree all day, changed by the consultant session
while you work. A bare `git commit` would sweep them in. Verify afterwards that it did not and say so
in the report.

**Write the report to
`C:\LastingImpact\receipt_capture\2026-09-12_REPORT_claude_code_firm_vendor_table.md`** and carry the
commit hashes in it.

**One section at the top for Paul.** What is now asserted about layer 2 that was not before; and what
would have to be true for a row to appear in the firm vendor table.
