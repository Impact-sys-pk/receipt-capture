# Brief: a guessed category holds the receipt, and the published item says so

**Written 2026-09-11 by the consultant session, from Paul's decisions of 2026-09-11. Step 10l of
`2026-07-25_CONSOLE_DESIGN.md`, added by amendment 237 and decided by amendment 330.**

~~**HELD. Do not start this while another brief is open.**~~ **RELEASED 2026-09-11: step 10n has
reported and no other brief is open. One brief per session at a time, so the next one,
`PROMPT_claude_code_2026-09-11_london_time_and_output_paths.md`, waits on this one.**

**Read first, in this order:** `CLAUDE.md`, the section "How this project is worked" and the seven
traps. Then section 18.1 of `2026-07-25_CONSOLE_DESIGN.md`, then step 10l and step 10m in section 16,
then amendments 237, 228, 236 and 330 in the amendment record.

---

## 1. What this is, and the receipt it exists to stop

**A receipt whose figures are perfect and whose category is a layer 5 guess reaches the client's books
today with nobody having looked at the category.** Paul's decision of 2026-09-06, amendment 237: an AI
guess must not reach a real client's books unseen. This is before 10i for that reason.

**The figures and the category are two different questions and one field is answering both.**
`validation.status` carries an arithmetic meaning: supplier, date, and net plus VAT against gross.
A layer 5 guess makes none of those wrong, so such a receipt is `ok` and drains straight through.

---

## 2. What is already decided, and is not yours or mine to reopen

**Amendment 330, Paul, 2026-09-11.**

1. **The hold lives in `categorisations.needs_review`.** Not in `validation.status`, which keeps its
   arithmetic meaning only. Not in `confidence`, which is the constant `low` for every layer 5 answer.
2. **The published item must carry a second key**, so the consumer can hold on either that or the
   validation status. **Written as a requirement and not as a field name, and section 3 is why.**
3. **The screen carries a second amber pill, `Category unconfirmed`**, alongside the existing pills
   rather than as a new value of them. A receipt with bad figures and a guessed category shows both.
4. **The confirmation is recorded, not inferred.** A receipt having moved out of the inbox is not a
   record that anyone confirmed the category.

**Points 3 and 4 are the other product's half and are not in this brief.**

---

## 3. The one thing this brief exists to get, and it is the reason it is written as a requirement

**Name the second key, and state it in the report as a contract.**

The consultant session has **not read the pipeline's publish code** and is not going to name a field
it has not read. Amendment 330 records that in terms. **IntelliBooks Desktop's half is written from
your report**, which is how sub-step 10f.37's action word was settled and how 10f.38's handoff folder
and message shape were settled.

So the report must say, plainly enough to build against without a second exchange:

- **What the key is called** on the published item, and why that name.
- **What values it takes**, and what an item written before this key existed reads as. A missing key
  must not hold a receipt that is fine; that is the rule `drainInbox()` already follows for a blank
  validation status.
- **When it is set and from what.** Name the condition, not the layer number alone.
- **Whether it travels on every published item or only on the held ones**, and which you chose.
- **What the consumer has to do to say the category is confirmed**, if anything comes back this way
  at all. 18.3's handoff is one way, so say so if the answer is nothing.

---

## 4. What to establish rather than assume, and one claim to test

**`categorisations.needs_review` is asserted to be read by nothing.** Step 10l and step 10m both say
it and both cite `worker\categorisation\fallback.py:220-227`. **No session has recorded opening that
file**, and the handover of session 22 says in terms that it did not. **So establish it rather than
quoting it**, enumerate the readers from the syntax tree, and print the enumeration whole.

**If it is read by something, say so before building on it.** The whole of amendment 330 rests on that
column being free to become load-bearing.

**The column defaults to 1**, per the schema section of `CLAUDE.md`. Say what that means for every row
already in the live database, because a hold that fires on every historic receipt is not a hold.

---

## 5. What must not change

- **`validation.status` keeps its arithmetic meaning.** Nothing here widens it, and no receipt's
  validation status moves because of a category.
- **Nothing is re-published, re-extracted or re-categorised** to backfill the new key.
- **F16's value** is `post` on Paul's firm record and nothing here touches it.
- **`write_client_copy()` stays the only writer into `Clients\`**, reached through the one gated
  caller.
- **No new table and no new column on an existing table without saying so first.** `schema.py` only
  creates and there is no `ALTER TABLE` in this repository, so a new column would exist only in a
  database made after the change and Paul's live one would not have it. If you believe a column is
  needed, **report it and stop rather than adding it.**

---

## 6. Evidence

- **Red before green**, with the failing output quoted.
- **A test that a receipt with perfect figures and a guessed category is held**, and a test that one
  with perfect figures and a category from layers 0 to 4 is not.
- **A test that an item carrying no such key at all is not held**, which is the item written before
  this change.
- **A test that `validation.status` did not move** on any of the above.
- **Mutations** through the harness, each anchored once and printing its diff: the key is never
  written; the key is written on every receipt rather than on the held ones; the hold reads the
  validation status instead of the category column; and a prose-only control that survives.
- **Enumerate from the syntax tree** anything you assert about a set, and print it whole. `.history\`
  excluded.
- **Nothing run against the live practice root. Never `import config` to read a value.**
- **Flag, do not fix. Disclose your own mistakes. State a confidence level and say what it is about.**

---

## 7. Committing and reporting

**Commit on `feat/console-phase0`.** Do not push, do not create a branch, and do not commit
`2026-07-25_CONSOLE_DESIGN.md`, any `PROMPT_*` or `HANDOVER_*` file, or anything under
`Test Receipts\`.

**Write the report to
`C:\LastingImpact\receipt_capture\2026-09-11_REPORT_claude_code_category_hold.md`** and carry the
commit hashes in it.

**One section at the top, for the half that is built from this report.** The key's name, its values,
the blank case, when it is set, whether it travels on every item, and anything that comes back the
other way. **That section is the contract. Everything else in the report is the evidence for it.**
