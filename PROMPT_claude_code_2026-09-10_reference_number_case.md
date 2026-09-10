# Brief: a reference number that differs only in case must not defeat duplicate detection

**Written 2026-09-10 by the consultant session. Paul's decision of 2026-09-10, option 1 of three.
Sub-step 10f.30's check 5, amendment 107, and `worker\extraction_pipeline.py`.**

**This is a live fault, found on Paul's machine, and it is the first thing check 5 has produced. A
real semantic duplicate went through as `ok`, reached the books, and was copied into the client
folder.**

---

## 1. What happened, in the data

A RingGo parking receipt was put through the pipeline twice, deliberately: once as the PDF, once as a
screen capture of that same PDF, so the bytes differ and the file-hash check cannot see it. That is
amendment 107's own case, a phone photo and an emailed PDF of one document.

The two extraction rows, read from `C:\Intellibills\db\receipts.db` in read-only mode on 2026-09-10:

```
6a3b0214... Client_004 ok RingGo 2021-09-04 5.17 'LBCAMRL-2021-09-04-01303' '12:30'
86ea018a... Client_004 ok RingGo 2021-09-04 5.17 'LBcAMRL-2021-09-04-01303' '12:30'
```

Both carry a `published` row.

**Same client, same supplier, same date, same amount, same time. The reference numbers differ by one
character of case: `C` against `c`.**

**The consequence, read in the code rather than inferred.** `find_by_transaction_loose()` matched.
`is_published()` passed. `_signals_differ()` then compared the reference numbers with a plain `!=`,
which is case-sensitive, returned True, and the possible-duplicate flag was never set. The receipt
validated `ok`, published, was drained into the books by IntelliBooks Desktop, and
`copy_for_published_receipt()` wrote it into
`Clients\Test Sole Trader\IntelliBooks\Receipts\2021-22\2021-09-04_ringgo_5.17.png`, beside the
`.pdf` of the same receipt.

**The supplier is already compared case-insensitively and the reference number is not.** That
inconsistency is the whole of the fault.

---

## 2. What to build

**Deliverable 1. `_signals_differ()` compares reference numbers case-insensitively and with
surrounding whitespace stripped.**

Paul chose this over the wider option of also ignoring punctuation and spacing, on the grounds that
the wider one starts guessing. **Do not normalise anything else**: no removing hyphens, no stripping
internal spaces, no collapsing runs of characters.

**Deliverable 2. Say whether the same treatment belongs on the receipt time.**

The time comparison parses `HH:MM` and allows five minutes, so case does not arise, but check whether
a stray space or a different separator can throw it into the `except` and silently skip the
comparison. Report what you find; change it only if it is the same fault in the same function.

**Deliverable 3. Say what else compares text from two extractions with a bare `!=` or `==`.**

Enumerate them from the syntax tree, print the set, and say for each whether case can differ between
two readings of one document. **Do not change them in this brief.** This fault is the general one and
the point is to know how many other places carry it.

---

## 3. What must not change

- **`find_by_transaction_loose()`.** It matched correctly and its query is not the problem.
- **`is_published()` and the `published` marker**, per 10f.24.
- **The five-minute window on the time comparison.**
- **The veto itself.** A reference number that genuinely differs still separates two transactions.
  That is what the veto is for and it stays.
- **No schema change. Nothing in the run summary.**

---

## 4. Standard of evidence

- **Red before green**, with the failing output quoted. **The red case is this one, and use these
  exact values**: two extractions of one document differing only in the case of one character of the
  reference number.
- **Drive it through a real `process_extraction_result()`** and assert the receipt ends
  `possible_duplicate` with `duplicate_of` set, rather than asserting on `_signals_differ()` alone.
- **Assert the veto still works.** Two receipts with genuinely different reference numbers, same
  supplier, date and amount, must still both be `ok`. Without this the fix trades one fault for
  another.
- **Drive the empty and missing cases.** One reference number present and the other absent must
  behave exactly as it does today.
- **Mutations anchored to one place**, each asserted to match exactly once, each printing its own
  diff. **Include one that puts the case-sensitive comparison back**, and it must be caught.
- **Do not cite a line number in `config.py` or `app.py`.**
- **Flag, do not fix. Disclose your own mistakes. Say what each confidence rests on and what it is
  about.**

---

## 5. Two things Paul is holding, and neither is yours

The duplicate receipt is in the books and in the client folder, and check 5 will be re-run once this
lands. **Do not delete anything on his machine and do not write into `Clients\`.**

---

## 6. Where to write the report

**`C:\LastingImpact\receipt_capture\2026-09-10_REPORT_claude_code_reference_number_case.md`.**

Carry in it: what was built, the commit, the suite before and after, every mutation and its result,
the set from deliverable 3 printed whole, what you found on the time comparison, any flag, and your
own mistakes.
