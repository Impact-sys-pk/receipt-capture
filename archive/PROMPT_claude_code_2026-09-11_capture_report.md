# Brief: the capture report, one client, by tax year or by dates

**Written 2026-09-11 by the consultant session, from Paul's decisions the same day. Step 10n of
`2026-07-25_CONSOLE_DESIGN.md`, added by amendment 319 and corrected by amendment 327.**

**Read first, in this order:** `CLAUDE.md`, the section "How this project is worked" and the seven
traps. Then 18.2, 18.2a and 18.2c of `2026-07-25_CONSOLE_DESIGN.md`, then step 10n in section 16,
then `2026-08-18_BOUNDARY_two_products.md` section 1.

---

## 1. What this is, and the sentence it exists to answer

**Paul's client says: "I sent this receipt. Why is it not in the file?"**

Nothing in either product answers that today. IntelliBooks Desktop holds what was published to it, so
a receipt that failed extraction, was flagged a possible duplicate or was discarded is invisible
there. **Only the pipeline's own database knows.**

**So this is a command Paul runs that prints or writes everything captured for one client and what
became of each one**, and hands him the answer while the client is still on the telephone.

**It is not a client-facing file.** Nothing new is written into `Clients\` and 18.2b's single writer
is untouched. Paul reads it or sends it himself.

---

## 2. The two scopes, and they select on different dates

**Paul's instruction, 2026-09-11.**

- **One client and one tax year.** Selects on the **document date**, because that is the accounting
  question: what belongs in that year's records.
- **One client and a range of dates.** Selects on **arrival**, because "I sent it last week" is a
  question about when it was sent, not about what the document says.

**Say in the report which column each one reads**, and make the difference visible in the output
rather than leaving the reader to infer it.

---

## 3. What a row has to say

Enough for Paul to answer the client without opening anything else. At least: when it arrived, how it
arrived, the document's own date, the supplier, the amount, and **what became of it**.

**The outcome is the point of the report.** Filed, in review, flagged a possible duplicate, failed
extraction, discarded, or an attached document from a bank line. **Read the actual statuses out of
the code rather than taking that list from this brief**, and say in the report what the full set is
and how you mapped each one into words a client would understand.

**Where a receipt went nowhere, say why in the row.** A failure with no reason given is the thing
this report exists to stop.

---

## 4. What must not change

- **Nothing is written into `Clients\`**, into `IntelliBooks\`, or into `Intellibills\Documents\`.
- **Nothing is published**, nothing is re-processed, and no receipt's status moves. This reads.
- **The database is opened read-only.**
- **F16's value** is `post` on Paul's firm record and nothing here touches it.

---

## 5. How Paul runs it

**A root script with a name that says what it does**, taking the client and one of the two scopes.
Every command he is given carries its own `cd` line, so state the exact invocation in the report.

**Say where the output goes** and why you chose it. It must not be `Clients\`. Printing to the screen
as well as writing a file is worth considering, because the common case is him reading one line back
to a client.

---

## 6. Evidence

- **Red before green**, with the failing output quoted.
- **A test for each scope**, including a receipt that falls in the tax year but outside the date
  range and the other way round, which is the whole point of them selecting on different columns.
- **A test that every status the database can hold appears in the report**, driven from the set you
  enumerated rather than from a list written by hand.
- **A test that nothing is written outside the output path** and that no row's status moved.
- **Mutations** through the harness, each anchored once and printing its diff: the two scopes read
  the same column; a status is dropped from the mapping; the report writes into `Clients\`; and a
  prose-only control that survives.
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
`C:\LastingImpact\receipt_capture\2026-09-11_REPORT_claude_code_capture_report.md`** and carry the
commit hashes in it.

**Three things for Paul, in one section at the top.**

1. The exact command for each scope, with its `cd` line.
2. The full set of outcomes a row can carry and the words you chose for each.
3. Anything the report cannot say that he might expect it to. **A receipt that never arrived at all
   leaves no row anywhere**, so say plainly how the report reads when the answer is that nothing was
   ever received.
