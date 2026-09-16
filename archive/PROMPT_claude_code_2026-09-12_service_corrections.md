# Brief: four small corrections in the resolution service

**Written 2026-09-12 by the consultant session, from Paul's decisions the same day.** Amendments 343
and 344 of `2026-07-25_CONSOLE_DESIGN.md`. **Three of the four come from your own report,
`2026-09-12_REPORT_claude_code_firm_vendor_table.md`.**

**Read first, in this order:** `CLAUDE.md`, the section "How this project is worked" and the seven
traps. Then amendments 343 and 344, and step 10m's body, which is now marked built.

**Four items, one commit each or one commit for all four, your call. None of them is a step and none
of them needs a design decision: all four are decided and recorded.**

---

## 1. Delete `increment_firm_vendor_count()`

**Amendment 344, point one. Paul's decision, and the fix is to remove something.**

Nought callers, and it cannot create a row. Delete it and its two assertions in
`tests/test_layer_two_row.py::TheFirmTableHasNoProductionWriterTest`.

**Amendment 234's reasoning applies word for word**: a dead function that touches the firm pool is one
rename away from becoming a silent firm write, and the firm pool is the table that reaches every
client of a trade.

**Re-enumerate the callers before deleting rather than trusting your own earlier count or this
brief**, and print it whole. **If anything calls it, stop and say so.**

---

## 2. `resolve_receipt()`'s learning guard requires the code to be chart-confirmed

**Amendment 344, point three. Paul's decision, and this one changes behaviour.**

**The difference, from your own section 2.3.** Two routes teach the client table and their guards
differ: one requires the operator's code to have been confirmed against the client's chart and the
other does not. **Make the command-line route match.**

**Why, in Paul's terms.** On the command line the code is typed, so a typo, an old code or another
client's code all teach happily. A mapping taught from a code the client's chart does not hold can
never work as taught: layer 1 returns it with confidence `high` and the chart check substitutes or
strips it on every future receipt, silently. `_resolve_category()`'s own docstring already says this
about the unreadable case; this extends it to the code simply not being there.

**What is given up, and it is intended.** A correction on that route carrying a code the chart does
not hold no longer teaches the mapping. **The receipt is still corrected and still filed.**

**The firm write is unaffected either way**, because the helper checks the chart outcome itself. Say
so in the report rather than leaving it to be inferred.

---

## 3. Delete the dead `sidecar_payload` in `resolve_receipt()`

**Amendment 344, point four.**

It is assigned and read nowhere in that function. `make_enriched_sidecar()` makes no calls and returns
a dict, so the site builds a dictionary and drops it: no file is written and nothing depends on it.

**The comment above it is the part that costs something**, because it tells the next reader a sidecar
is produced there. **Delete the assignment and the comment together**, and renumber or adjust the
surrounding step comments so the sequence still reads.

**Establish it yourself before deleting**: that the name is read nowhere in the enclosing function,
and that the builder has no side effect. **The local computed on the line above it is NOT dead** and
is passed to the client folder copy, so read that before you touch either.

---

## 4. A correction that clears `possible_duplicate` says so in `run.log`

**Amendment 343. Paul's decision, and it is a control against a double-claimed expense.**

**The fault.** `resolve_receipt()` ends with an unconditional status write of `ok`, so correcting a
receipt flagged `possible_duplicate` clears the flag and the receipt drains into the books. **The
guard against exactly that is already written and sits in a branch a corrected receipt with sound
figures never reaches**, and which the operator-decided path skips outright.

**What is NOT wanted: do not move that guard.** Hoisting it leaves a corrected receipt at
`possible_duplicate` for ever, because nothing else clears that status. It would strand receipts.

**What is wanted: a WARNING in `run.log`** when a correction takes a receipt out of
`possible_duplicate`, naming both receipts, so it is not silent.

**The precedent is a few lines away in the same function**: the warning that fires when a receipt
reaches `ok` by decision despite failed checks, and its reason is the same one. Paul reads `run.log`,
and a receipt that silently turns green is worse than the fault being fixed. **Follow that one's
shape.**

**It fires only where the status actually was `possible_duplicate`**, with a negative control proving
it does not fire otherwise.

**The IntelliBooks Desktop half is built already** and is change log item 93: the window the
correction is made in now names the receipt it looks like a duplicate of.

---

## 5. What must not change

- **No stored value moves.** No migration, no backfill, no rewrite.
- **The firm table's rule and its single caller are untouched**, except that item 2 changes a guard
  on the client write beside it.
- **Nothing published, re-processed, re-extracted, and no receipt's status moves** beyond what item 4
  reports on.
- **Nothing written into `Clients\`, `IntelliBooks\` or `Intellibills\Documents\`.**
- **Never `import config` to read a value.**

---

## 6. Evidence

- **Red before green**, with the failing output quoted, for items 2 and 4.
- **Item 1 is a deletion**, so the evidence is the enumeration showing nought callers printed whole,
  and the suite green after.
- **Mutations**, each anchored once and printing its own diff: the chart-confirmed condition removed
  from the guard; the warning dropped; the warning fired on a receipt that was not a possible
  duplicate; and a prose-only control that survives.
- **A negative control on the warning**, so a check that cannot fail is not mistaken for one that
  passed.
- **Enumerate from the syntax tree** anything you assert about a set, and print it whole.
  `.history\` excluded.
- **Run the suite again AFTER committing** if the change adds a file.
- **Flag, do not fix. Every flag carries the obvious fix, and if the fix is to remove something, say
  so first.** Disclose your own mistakes. State a confidence level and say what it is about.

---

## 7. Committing and reporting

**Commit on `feat/console-phase0`.** Do not push and do not create a branch. Do not commit
`2026-07-25_CONSOLE_DESIGN.md`, any `PROMPT_*` or `HANDOVER_*` file, or anything under
`Test Receipts\`.

**Commit by naming your own paths and check the index afterwards**, and say so in the report.

**Write the report to
`C:\LastingImpact\receipt_capture\2026-09-12_REPORT_claude_code_service_corrections.md`** and carry
the commit hashes in it.

**One section at the top for Paul.** What behaviour changed that he would notice, and what he will
see in `run.log` that he did not see before.
