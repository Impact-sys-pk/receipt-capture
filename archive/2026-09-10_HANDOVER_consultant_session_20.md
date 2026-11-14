# Handover: consultant session 20, chat 20

**Written 2026-09-10 08:45 BST by the consultant session, at Paul's instruction. It covers the
session that ran from 2026-09-09 morning to 2026-09-10 morning.**

**You are the consultant session in Cowork. You own verification, this project's design document and
the prompts, and since 2026-09-06 you also write `IntelliBooks-Desktop-v3.html` on Paul's standing
instruction. You do not write the pipeline; Claude Code does.**

---

## 1. Read these, in this order, before doing anything

1. **This file, in full.**
2. **`CLAUDE.md`**, section "How this project is worked", and the traps. **The traps live there and
   nowhere else.** Section 7 of this file adds only the ones this session actually hit.
3. **`2026-07-25_CONSOLE_DESIGN.md`**, the amendment record from **307 to 311**, which is this
   session's work. Then section 18, receipt and transaction integrity, before the body.
4. **`IntelliBooks\App\Docs\IntelliBooks-Change-Log.md`**, items **20, 22, 23, 39, 71, 72 and 73**,
   which are this session's Desktop work and live checks.
5. **`2026-09-08_PLAN_publish_step.md`**, which is now complete in all four stages.

**Do not read the handovers in `archive\`. They are superseded.**

**Do not state what any of these contains unless you have opened it.**

---

## 2. The one thing in flight, and it is not yours

**Claude Code is executing `PROMPT_claude_code_2026-09-10_reference_number_case.md`, in the
repository root, 5,230 bytes, md5 `080d7fc393e856932c218e25ce0f5b1f`.** Paul briefed it at 08:29 on
2026-09-10.

**Nothing else is in flight. Nothing is half-built.**

**When Claude Code's report arrives**, at
`2026-09-10_REPORT_claude_code_reference_number_case.md`:

- **Read it in full first**, then verify the claims that matter against the code. That is this
  project's rule and about half its defects were found that way.
- **Then check 5 of sub-step 10f.30 is re-run**, and it is Paul's to run, not yours.
- **Check 5 passing closes step 10f.** Nothing else in step 10f is workable.

**How to re-run check 5, because the report that describes it is wrong.** Part D of section 4 of
`IntelliBooks\App\Docs\2026-08-20_REPORT_desktop_menu_groups.md` has Paul build a fake review item in
`Intellibills\Review\TEST\`. **Amendment 304 records that this cannot work**: `scanReview()` no
longer reads that folder and the check names it by client code rather than `client_id`. **What was
done instead, and it worked:** one RingGo receipt was put through twice, once as the PDF and once as
a screen capture of it, so the bytes differ and the file-hash check cannot see it. That is amendment
107's own case.

**Before the re-run, Paul has two clean-up steps he has been given and may not have done:** delete
the duplicate books row for the receipt with a picture thumbnail, receipt `86ea018a`, keeping the one
with the PDF button, `6a3b0214`; and delete
`Clients\Test Sole Trader\IntelliBooks\Receipts\2021-22\2021-09-04_ringgo_5.17.png`, leaving the
`.pdf`. **Ask him rather than checking, or check the folder and the books; do not assume either
way.**

---

## 3. What this session did, and the state to verify

**Verify at least three rows of this table against the code, the file or the disk before you act on
any of it. Say which three and what you found.**

| # | Claim | Where to check it |
|---|---|---|
| 1 | The back-feed fix is built AND live. A `filed` note with no `filed_path` goes to `_settle_note()`, which delegates to `resolve_receipt()`. | `worker\resolution\service.py`, the branch at the end of `apply_resolution_note()`. Amendment 307. |
| 2 | `resolve_receipt()` takes `decided_by_operator`, default False, passed True only by `_settle_note()`. | Same file, line ~650 for the signature and ~817 for the override. Amendment 309. |
| 3 | Two production call sites of `resolve_receipt()`, exactly one passing the keyword. | Enumerate from the syntax tree across all 44 non-test Python files. `resolve_receipt.py` does not, `worker\resolution\service.py` does. |
| 4 | Sub-step 10f.2 is BUILT, and its marker said OUTSTANDING until 2026-09-10. | `config.py`, `PUBLISH_DESTINATIONS_FIELD`. Amendment 311. |
| 5 | `IntelliBooks-Desktop-v3.html` is 345,601 bytes, md5 `fbf67517ea8d2406db5fd8e3e467d482`. | Read it back from Paul's machine and compare. |
| 6 | `2026-07-25_CONSOLE_DESIGN.md` holds 311 amendments, contiguous, and 36 sub-steps in step 10f, 1 to 36, four outstanding: 1, 3, 27, 30. | Parse them out of the document. Do not count by hand and do not trust this row. |
| 7 | Duplicate detection is broken by a one-character case difference in a reference number. | `_signals_differ()` in `worker\extraction_pipeline.py`. Amendment 310. |

**Amendments 307 to 311, in one line each.**

- **307.** The back-feed fix built and verified live. A settle note now settles.
- **308.** The Bank Transactions Category column showed a bare account code on posted rows. Fixed.
- **309.** `decided_by_operator`: a settled receipt reaches `ok` and the failed checks are recorded.
- **310.** Check 5 failed and found a live defect in duplicate detection. Briefed.
- **311.** Sub-step 10f.2's marker was stale; all three pieces were built.

**Change log items 20, 22, 23, 39, 71, 72, 73.** Four live checks passed, one failed, three Desktop
changes built.

---

## 4. Step 10f, and it is nearly closed

**36 sub-steps, 1 to 36, no gaps, no duplicates, parsed out of the document on 2026-09-10.**

| Outstanding | Why it cannot be worked |
|---|---|
| 10f.1 | Deferred by Paul's decision of 2026-09-08, amendment 279. One destination exists, so the per-client column can only hold one value. |
| 10f.3 | Deferred the same day, amendment 280. Nothing says what the CSV contains, where it goes or when. |
| 10f.27 | Blocked on the console, which is not built. |
| 10f.30 | **In progress. Check 5 is the only part left.** |

**All four stages of `2026-09-08_PLAN_publish_step.md` are complete.** Stage 3's five checks passed,
stage 4 landed, and check 1, stage 4's completion test, passed at 15:15 on 2026-09-09, closing
18.2b's freeze and amendment 75's interim.

---

## 5. The console, and the discussion Paul wants carried forward

**Paul and I went through the console at a high level on 2026-09-09. He asked four things and I
answered them in chat. THE ANSWERS WERE NOT WRITTEN TO A FILE, so they are lost, and that is this
session's failure against this project's own rule that anything agreed in a chat and not written down
is gone.** What survives is where the material is, and that is enough to rebuild it.

**Where the console is specified.** `2026-07-25_CONSOLE_DESIGN.md`:

- **Section 8, "Console pages"**, which names the module layout and the six pages: **8.1 Status
  (`/`), 8.2 Queue (`/queue`), 8.3 Browse (`/receipts`), 8.4 Receipt detail
  (`/receipt/<receipt_id>`), 8.5 Settings (`/settings`, admin only), 8.6 Intake panel (`/intake`)**,
  plus 8.7 Presentation.
- **Section 5.2, `console_users`**, the table it authenticates against.
- **Section 13**, which records that the chart of accounts module is **built and not part of the
  console**.

**What Paul asked, and what the shape of the answer was.** He wanted, in plain English and with no
history: what the console is for and what it will comprise; whether everything it will do is
something IntelliBooks Desktop could not do; and a side-by-side of the six pages against what Desktop
already does, marking each as cheap, dear or impossible in Desktop. **He read the section and found
it long, which is why he asked.** If he asks again, the honest thing is to say the earlier answer was
not recorded, and to rebuild it from section 8 rather than from memory.

**The console blocks sub-step 10f.27**, which is deleting a possible duplicate and removing its copy
from the client folder, performed by Intellibills' own front end with every write and delete logged.

---

## 6. What Paul was offered next, and has not chosen

**Three candidates, none started.** They were put to him at 08:35 on 2026-09-10 and section 9 carries
that message word for word.

1. **The console**, the Flask app. It unblocks 10f.27 and it is the largest thing left.
2. **Item 168, clearing the test estate**, which the plan puts immediately before step 10i.
3. **`IntelliBooks-System-Specification.md` and `IntelliBooks-System-Overview.md`**, both materially
   stale: the specification has 30 mentions of sidecars and 14 of the client folder route, both of
   which 2026-09-09's work removed. **Offered days ago and never started.**

---

## 7. Traps this session hit, on top of `CLAUDE.md`'s

- **No `device_bash` in this session.** Everything on Paul's machine is done by staging a file,
  editing it here, sending it, committing it back with `device_commit_files`, and staging it again to
  compare the md5. **Always read the file back and compare.**
- **`device_commit_files` with `force: true` bypasses the modification-time guard for every file in
  the call, not just the one that needs it.** Send the forced write and the guarded write as two
  calls. This session got that wrong once and disclosed it.
- **A `.bak` is written by sending the previous version through `SendUserFile` and committing it to
  the `.bak` path**, then staging it back to prove it byte-exact. There is no copy on the device.
- **Read the clock in every reply.** This session twice carried a time forward in its head and was
  wrong by half an hour both times. `TZ=Europe/London date` is one command.
- **Ask Paul rather than deriving.** He is the operator. He knows what he clicked, what the toast
  said and when he restarted the pipeline.
- **Do not give him an expected value you have not checked.** Twice this session an expected count or
  row list was wrong and the screen was right.
- **A question with two halves gets an ambiguous answer.** Ask one thing at a time, and if the answer
  could mean either, ask again rather than choosing.
- **A database read through the Cowork bridge is not evidence.** Paul ran the read-only query that
  cracked check 5 and pasted the output.

**This session's own mistakes, all disclosed to Paul at the time.** An expected value of one row when
five was right, from misreading a directory listing taken earlier in the same session. A truncated
md5 typed into a draft amendment and corrected before it was committed. Amendment 307 justified with
18.4, which amendment 107 records this session getting wrong once before; corrected by amendment 309
after Claude Code flagged it. The `force` mistake above.

---

## 8. Files this session changed, with their md5 as read back from Paul's machine

| File | Bytes | md5 |
|---|---|---|
| `C:\LastingImpact\receipt_capture\2026-07-25_CONSOLE_DESIGN.md` | 1,231,896 | `5a08c5397cafec870ba21867cfd1bf16` |
| `...\IntelliBooks\App\IntelliBooks-Desktop-v3.html` | 345,601 | `fbf67517ea8d2406db5fd8e3e467d482` |
| `...\IntelliBooks\App\Docs\IntelliBooks-Change-Log.md` | 231,945 | `b9d74223dc0af018d4e0d1ba3a58ba07` |
| `C:\LastingImpact\receipt_capture\PROMPT_claude_code_2026-09-10_reference_number_case.md` | 5,230 | `080d7fc393e856932c218e25ce0f5b1f` |

**Also written by this session and already executed by Claude Code:**
`PROMPT_claude_code_2026-09-09_desktop_note_settles_rather_than_files.md` and
`PROMPT_claude_code_2026-09-09_decided_by_operator.md`.

**`feat/console-phase0` is pushed.** Local and remote both at
`d4b50948cc5fade71e3a61e34d32dc5e972802b5`, read from the repository's own refs on 2026-09-10.

---

## 9. Where the next chat starts

**Paul's instruction: the new chat begins precisely on the message below, which is the last
substantive message of this session, reproduced word for word.** Read it as the state of play and
wait for his answer to it. **Do not restate it back to him.**

---

**2026-09-10 08:35 BST (V=2)**

**I read the sub-steps rather than the summary, and found one wrong.**

**Sub-step 10f.2 read OUTSTANDING and all three of its pieces are built.** Piece 1 is the
`IntelliBooks publish folder` box on Firm Settings, which you and I both looked at yesterday. Piece 2
is its value, `Incoming`. Piece 3 is `config.py`, which holds
`PUBLISH_DESTINATIONS_FIELD = "publish_destinations"`, reads it with no default and no fallback, and
refuses to start without it. And `run.log` shows every receipt publishing into
`IntelliBooks\Incoming\`.

Corrected, with the old marker struck, and recorded as **amendment 311**. Read back from your
machine, md5 `5a08c5397cafec870ba21867cfd1bf16`, 1,231,896 bytes.

**Where step 10f actually stands, enumerated from the document rather than counted by hand.** 36
sub-steps, 1 to 36, no gaps, no duplicates. **Four outstanding, and three of them cannot be worked:**

| Sub-step | Why it is not workable |
|---|---|
| 10f.1 | Deferred by your decision of 2026-09-08. One publishing destination exists, so the per-client column can only hold one value. |
| 10f.3 | Deferred the same day. Nothing says what the CSV contains, where it goes or when. |
| 10f.27 | Blocked on the console, which is not built. |
| **10f.30** | **In progress. Check 5 is the only thing left.** |

**So step 10f closes when check 5 passes, and check 5 is waiting on Claude Code's brief.** There is
nothing else in step 10f to pick up.

**Which means the next real question is what comes after it, and that is yours.** The candidates, and
none is started:

1. **The console**, the Flask app. It unblocks 10f.27 and it is the largest thing left.
2. **Item 168, clearing the test estate**, which the plan says goes immediately before step 10i and
   which the pilot needs.
3. **The two stale documents I offered days ago and never started**:
   `IntelliBooks-System-Specification.md` and `IntelliBooks-System-Overview.md`. The specification has
   30 mentions of sidecars and 14 of the client folder route, both of which the last two days
   removed.

Say which and I will start on it.

---

## 10. What this handover does not claim

**It does not claim the state table is right.** Section 3 exists to be verified and one of its rows
is flagged as untrustworthy on purpose.

**It does not claim check 5 will pass once the reference number fix lands.** The fix addresses case
and nothing else, and an extractor that misreads any other character of a reference number can still
defeat the check. That is stated in amendment 310 and in the brief.

**Confidence.** High on sections 2, 4 and 8, because each was read back from Paul's machine or parsed
out of the document on 2026-09-10. High on section 3's rows 1 to 4 and 7, read in the named source
files the same morning. **Section 5 is the weakest**: the console discussion itself is gone and only
its subject matter survives.
