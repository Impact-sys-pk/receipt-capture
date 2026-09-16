# Brief: an edit to an already-filed receipt writes a `corrected` note

**Written 2026-09-11 by the consultant session. Step 10k of `2026-07-25_CONSOLE_DESIGN.md`, added
2026-09-06 by amendment 235 on Paul's decision closing outstanding items 36 and 167.**

**Read first, in this order:** `CLAUDE.md`, the section "How this project is worked" and the seven
traps. Then section 12, the resolution back-feed contract, and 11.3. Then 18.1, 18.6 and step 10k
itself in section 16. Then amendments 306, 307, 309 and 322, which are the four that shaped the note
mechanism you are adding to.

---

## 1. What this is

A receipt has been through the pipeline, validated, categorised and filed, and its figures are in the
books. **Paul then finds one of them is wrong.** Today there is no route for that correction to reach
the pipeline's own record, so the database goes on holding what the extraction read.

**Step 10k gives it one.** IntelliBooks Desktop writes a resolution note with a new action,
`corrected`, and the pipeline applies the corrected values to its own record.

**This brief is the pipeline half only.** The Desktop half is the consultant session's and is written
from your report. **The two halves land together or not at all.**

---

## 2. The rule that decides the shape

**A `corrected` note does not re-file anything.** The receipt is already filed, `filed_path` is
already set, and the client folder copy is already written. 18.2b: a copy is never withdrawn.

So this is the first note action that changes the pipeline's record **without moving a file**, which
is what separates it from `filed`, from `settle` and from `attached`.

**Scope is the receipt record.** A recoding made against a transaction in the books is outstanding
item 35 and is not in this step. Do not build it and do not widen into it.

---

## 3. Deliverable 1: the pipeline applies a correction

**What the note carries**, and it is the same shape a `filed` note carries so Desktop has one
vocabulary: the receipt, the client, `action`, `resolved_by`, `resolved_at`, the corrected `values`,
and `remember_gl_for_supplier`.

**Name the action and state it in the report**, because the Desktop half is written to match. Step
10k says `corrected`. **Say plainly whether you are adding a fourth value to `NOTE_ACTIONS` or
carrying a field on an existing action, and why**, the way amendment 322 settled that question for
`attached`. Amendment 307's rule is that the field chooses the path and not the action word; say
whether it applies here or not.

**What the pipeline does with it.**

- **Applies the corrected values** to its own record, through the path the console and the CLI
  already take rather than a second implementation of resolution.
- **Applies the learning**, per 11.3: the `remember_gl_for_supplier` tick teaches, an unticked
  correction teaches nothing.
- **Writes one `resolution_events` row**, so a replay of the same note is refused on the idempotency
  key of 12.3 step 3.
- **Does not re-file, does not re-publish, does not touch `Clients\` and does not touch
  `Intellibills\Documents\`.** Assert each of those, not only the first.

**Two things to establish rather than assume, and report both.**

1. **What happens to a correction on a receipt that is not `ok`.** A `failed` or `possible_duplicate`
   receipt can be edited in Desktop like any other. Say what the pipeline does with a correction for
   one, and whether `decided_by_operator` from amendment 309 is the right instrument or the wrong
   one.
2. **Whether a correction can reach a receipt the pipeline never issued.** Desktop tests the
   identifier's shape before it sends anything, so it should not arise. Say what happens if it does.

---

## 4. The assertions come before the writer

**Step 10k says so in terms and it is not a formality.** Nothing has ever tested what a matched
categorisation row stores, and **every `categorisations` row in existence reads `unmatched`**. During
the `vendor_key` rename a mutation swapping two fields at layer 1 left the whole suite green for
exactly that reason. Two assertions closed it at layer 1 and **the identical swap at layer 2 is still
live**.

**So write the assertions for what a corrected row stores first, watch them fail, and then build.**

---

## 5. What must not change

- **`write_client_copy()` stays the only writer into `Clients\`**, and nothing in this step reaches
  it at all.
- **`Intellibills\Documents\` is never written to or deleted from here.**
- **The `filed`, `discarded` and `attached` paths**, all three of which are live and two of which
  were proved on Paul's machine on 2026-09-11.
- **F16's value**, which is `post` on Paul's firm record.

---

## 6. Evidence

- **Red before green**, with the failing output quoted, driven through a real `process_once()`.
- **A test that no file moves**, listing the client folder and the document store whole before and
  after, rather than asserting on the call.
- **A test that the same note twice changes nothing the second time.**
- **A test for the tick and for no tick.**
- **Mutations** through the harness, each anchored once and printing its diff: re-file on a
  correction; drop the learning; drop the audit row; and a prose-only control that survives.
- **Enumerate from the syntax tree** anything you assert about a set, and print it whole.
  `.history\` excluded.
- **Nothing run against the live practice root. Never `import config` to read a value.**
- **Flag, do not fix. Disclose your own mistakes. State a confidence level and say what it is about.**

---

## 7. Committing and reporting

**Commit on `feat/console-phase0`.** Do not push, do not create a branch, and do not commit
`2026-07-25_CONSOLE_DESIGN.md`, any `PROMPT_*` or `HANDOVER_*` file, or anything under
`Test Receipts\`.

**Write the report to
`C:\LastingImpact\receipt_capture\2026-09-11_REPORT_claude_code_corrected_note.md`** and carry the
commit hashes in it.

**Four things the Desktop half is written from, so put them in one section at the top.**

1. The action word, the exact shape of the note, and every field it must carry.
2. What the pipeline does with a correction on a receipt that is not `ok`.
3. What Desktop can honestly tell Paul at the moment he saves the edit, given the pipeline reads the
   note on its next poll.
4. Whether the note should be sent on every edit of a filed receipt, or only where a figure actually
   changed. **Paul has not ruled on this. Set out what each would mean and it goes to him.**
