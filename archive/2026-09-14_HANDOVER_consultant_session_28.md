# Handover: consultant session 28

**Written 2026-09-14 by the consultant session. It covers everything since
`2026-09-13_HANDOVER_consultant_session_27.md`, which is now spent.**

**You are the consultant session in Cowork.** You own verification, `2026-07-25_CONSOLE_DESIGN.md`,
`2026-07-25_BUILD_STATUS.md` (new this session, see section 5), the `PROMPT_*.md` briefs, and
`IntelliBooks-Desktop-v3.html` on Paul's standing instruction of 2026-09-06. You do not write the
Python pipeline; Claude Code does. Paul is the only channel between you.

**This handover itself was written after three context compactions in one running session.** Section
1 explains what that means for how much to trust it.

---

## 0. THE ONE NEW STANDING INSTRUCTION THIS SESSION, READ FIRST

**Paul, this session: "All instructions to cc are drafted by you."** Every message Paul sends to
Claude Code, however short, is drafted by the consultant session first, not typed by Paul directly.
This was said once, in passing, and is recorded here because a rule stated once in chat and not
written down is lost, per this project's own working method. Treat it as standing until Paul says
otherwise.

---

## 1. THE CONTEXT THIS HANDOVER WAS WRITTEN FROM, AND ITS LIMITS

**This session ran long enough to compact its own context three times.** What follows is written
from: (a) a structured summary the harness produced of everything before the third compaction, and
(b) direct re-reading and re-verification of the files on disk this session, done specifically to
write this handover rather than trusted from the summary alone. **Where a claim below rests only on
the summary and was not independently re-checked while writing this handover, it says so.** Where a
claim was re-verified just now (amendment count, step-table counts, commit hashes, file sizes, md5s),
it says that instead, because that is a different and stronger kind of confidence.

**Amendments 450 to 456 in `2026-07-25_CONSOLE_DESIGN.md` (a Desktop batch build, steps 10u, 10y,
10z-10ae, 10af, and the 10au/10az split) are dated 2026-09-14 and are this session's**, per the
document's own dates, but they were made **before** the portion of this session captured in the
summary this handover was written from. **This handover does not narrate how that work was done**
(no tool calls for it are in the visible history available to this handover). Take the design
document's own amendment record as authoritative for that work, not this handover's account of it.

**Tools available this session, confirmed by use, not assumed:** `mcp__remote-devices__device_stage_files`,
`device_commit_files`, `device_list_dir`, `device_request_folder_access`, `get_device_info`. **Whether
a `device_bash` tool (a shell on Paul's machine) was available this session is not established either
way** — nothing in the visible history used one, but that is not proof it was absent, only that it
was not tried. Test for it before assuming either way next session.

**Folders used this session, both already working with no fresh grant needed except the third:**

```
C:\LastingImpact\receipt_capture
C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliBooks\App        (per amendments 451/452/455's own Desktop edits, not directly narrated here — see above)
```

**Newly granted this session:** `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills\PhoneApp\`,
reason given to Paul: "Locate the phone capture app for step 10ak, the Statements screen." Granted.

---

## 2. Read these, in this order, before doing anything

1. **This file, in full.**
2. **`CLAUDE.md`**, "How this project is worked" and the traps. The traps live there and nowhere
   else; do not trust a restated list, including session 27's own section 8 or anything below.
3. **`2026-07-25_BUILD_STATUS.md`, in full.** New this session (section 5). This is now where
   sections 16 and 17 live — the step table and the documents/open-questions section. It is **not**
   in `2026-07-25_CONSOLE_DESIGN.md` any more.
4. **`2026-07-25_CONSOLE_DESIGN.md`**: amendments 450 to 457, all this session's. Note amendment
   457 corrects amendment 405's row in place (a second instance of the in-place-correction convention
   session 27's handover flagged at amendment 443 — now used twice, still not a written rule anywhere,
   still a judgement call).
5. **This project's Cowork custom-instructions text was corrected this session** (not a repo file —
   a project-setting text Paul maintains). Two sentences added, both about the new
   `2026-07-25_BUILD_STATUS.md` split. Paul pasted the corrected text back himself and confirmed
   "OK that is done." Nothing further owed here.

---

## 3. What is in flight with Claude Code

**Sent and confirmed running:**

- **`PROMPT_claude_code_2026-09-14_delivery_log_writer.md`, step 10az** (the delivery-log writer in
  `copy_for_published_receipt()`, format specified in amendment 456). Paul confirmed **"Done cc
  working"** on this. **No report has landed yet.** The design document's own row for 10az, read
  directly from the locally staged copy this session, still says OUTSTANDING — expected, since no
  report exists yet to update it against.
- Step **10au** is blocked on 10az by design (amendment 456) and cannot be briefed until 10az's
  report confirms the log format landed as specified.

**Sitting on disk, not confirmed sent:**

- **`PROMPT_claude_code_2026-09-12_exports_leave_the_repository.md`**, for step 10r. This file exists
  in the repository root, dated 2026-09-12. Step 10r's own row in `2026-07-25_BUILD_STATUS.md` reads
  "OUTSTANDING. Added 2026-09-12 by amendment 359..." and **does not name an owner** in the text this
  handover read. **Do not assume this brief was sent or is queued correctly** — check with Paul
  before treating it as "next," despite an earlier point in this session's own conversation
  apparently planning to send it after 10az. Confirm ownership and send-state first.

**Unbriefed OUTSTANDING steps carried over from session 27's list, minus 10aq (now BUILT, amendment
457) and plus nothing new added to this sub-list this session:**

| Step | What it needs |
|---|---|
| 10aw | Null-id filename fallback. Not fully decided; Claude Code reads the code and proposes the fix. |
| 10ai | Per-client capture report moves into the client's own folder. |
| 10aj | End-to-end test proving a statement can arrive and be filed. |
| 10at | `export_bookkeeping.py`'s latest-attempt-row fix. Already fully specified. |

---

## 4. What this session found and decided, in order

**Verified two Claude Code reports on the 10aq recovery-sweep work, both read in full and checked
directly against the repository before anything in them was accepted:**

1. **`2026-09-14_REPORT_claude_code_recovery_sweep_review_fallback.md`** (the 10aq fix itself, plus
   three flags). Paul's decisions, all yes: accept "publish-as-review" rather than the literal
   "route to Review" wording amendment 405 had recorded (Review has had zero readers since sub-step
   10f.15, confirmed independently by reading `scanReview()`/`itemIsHeld()` in
   `IntelliBooks-Desktop-v3.html`); fix Flag 1 (dead `tax_year` local); fix Flag 2 (wrong docstring in
   `worker/filing.py`); fix Flag 3 (stale test cross-reference). Recorded as **amendment 457**,
   correcting amendment 405's row in place. Step 10aq now **BUILT**.
2. **`2026-09-14_REPORT_claude_code_three_flags.md`** (the three flags built). Verified directly:
   `tax_year` grep in `app.py`, both named reader functions in `worker/filing.py` read in full, the
   struck test cross-reference confirmed absent from `tests/`. **Found the report's own "7 ahead of
   origin" claim wrong: independently counted 9** by reading both `.git/logs/HEAD` and
   `.git/logs/refs/remotes/origin/feat/console-phase0` directly, because Claude Code's count had
   missed a consultant-session commit (amendment 457's own) landing on the shared branch mid-session.
   Paul decided: push, yes; build Claude Code's own proposed new unresolved-client-guard test, yes.
3. **`2026-09-14_REPORT_claude_code_unresolved_client_test_and_push.md`** (the follow-up). Verified
   directly: the new `AnUnresolvedClientIsNotPublishedTest` class read in full in
   `tests/test_recovery_sweep_fallback.py`, both reflogs re-read to confirm the push actually reached
   origin (commits `92556cd`, `8f3e71e3`). Claude Code's own account of the earlier 7-vs-9 miscount
   (it had counted only its own commits rather than using `git status -sb`) checked and accepted; it
   recorded the lesson in its own project memory. No decision needed from Paul on this report.

**Restructured `2026-07-25_CONSOLE_DESIGN.md`, on Paul's own initiative ("I think it has become too
unwieldy"), in two separately-agreed, separately-verified steps:**

4. **Step 1: shrunk the section-16 headline paragraph** from 22,489 characters (89 accreted
   `~~struck~~`/`**bold**` correction tokens, never removed, only appended to) to 686 characters, by
   moving every non-current token, in original order, into a new appendix, 16A. Verified lossless by
   a no-whitespace character-count comparison before and after. Delivered, committed `efcfae7`.
5. **Step 2, decided only after asking Paul how he actually reads the document** (his own answer:
   "the only sections I really look at are Section 16 and possibly s17... I cant make head or tail of
   the rest of it") **split sections 16 and 17 out into a new file, `2026-07-25_BUILD_STATUS.md`**,
   verbatim, section numbers unchanged (Paul's own mid-task instruction: "I think we should retain
   the original section numbers though" — checked and confirmed preserved). `2026-07-25_CONSOLE_DESIGN.md`
   keeps a short pointer in their place. `CLAUDE.md` got one sentence updated to point at the new
   file. A subfolder for the split was considered and explicitly declined by Paul ("lets forget that
   for now"). Delivered, committed `a437dbd`. **This commit is not yet pushed to origin** — see
   section 7.
6. **The Cowork project custom-instructions text was corrected** to describe the new file and the
   superseded sentence about section 16/17. Paul asked for, and was given, the complete corrected
   text to paste back himself, since this tool cannot edit that text directly. Confirmed done.

**Located and partially verified the phone capture app's Statements feature for step 10ak, on Paul's
agreement not to correct the design document until this was checked:**

7. Located the app at `Intellibills\PhoneApp\` (README: copied there 2026-09-01, "a copy, not a
   move," no repository, no build step — "Drag and drop... Only Paul can deploy it"). Read
   `README.md` in full, `index.html` in three passes, `netlify\functions\upload.js` in full (166
   lines).
8. **Confirmed with Paul directly, rather than derived, that the Statements feature has never been
   deployed** ("never deployed"), and that his separate, real complaint — the phone shortcut
   reverting to "Set up your app" — is a different, so-far-undiagnosed problem. Located the relevant
   client-side mechanism (`getClient()`/`setClient()`, `localStorage["ib_client"]`) but **did not
   diagnose the cause**.
9. **Checked the apparent gap between `upload.js` (writes both receipts and statements to the same
   inbox folder, no branch on `type`) and the design document's own separate `Receipts\`/`Statements\`
   folder paths.** Read `app.py` around line 1740 (`intake.is_statement` branch: hash-based dedup
   scoped to the client, client-folder resolution, `platform`/`week_ending` metadata validation, calls
   `file_statement()` and `repo.save_statement()`) and `worker/filing.py:84-134` (`file_statement()`
   itself, building the destination as `client_dir / config.CLIENT_STATEMENTS_FOLDER_NAME / tax_year /
   platform`, genuinely distinct from the receipts path). **This resolves the apparent gap**: the
   upload function only has to write into the shared inbox; the Python pipeline is what does the
   type-based routing into the separate `Statements\` tree afterward, and it does. **Confidence: high
   for what was read directly** (`app.py`, `worker/filing.py`, `worker/database/repository.py`, all
   read in full or in the relevant sections). **Not yet verified: exactly how `intake.is_statement`
   is set** — its definition lives in `worker/intake/folder_reader.py`, which was never staged into
   this session and so was not read. Plausible it derives from the sidecar's `type` field the same
   way `upload.js` writes it, but this is not confirmed. **This is the one loose end in an otherwise
   load-bearing finding: stage and read that file before telling Paul the pipeline side is fully
   verified.**
10. **Noticed, not yet reported to Paul or investigated:** `index.html` declares
    `APP_VERSION="IntelliBooks Receipts v6"`; the README's own provenance section (last verified
    2026-09-01) documents the deployed app as "v5". Could simply mean the copied source moved on since
    the README's own check; could mean the README is stale. Not resolved.

---

## 5. New file this session: `2026-07-25_BUILD_STATUS.md`

**Created this session by the split in section 4, item 5.** Carries section 16 (Implementation
order, the step table and appendix 16A) and section 17 (Documents and remaining questions) verbatim
out of `2026-07-25_CONSOLE_DESIGN.md`. Amendment references inside it still resolve in
`2026-07-25_CONSOLE_DESIGN.md`'s own amendment record — nothing about amendment numbering changed.

**Confirmed by Paul to trigger the Claude desktop app's own "Showing this large file as plain text to
keep the page responsive" fallback when opened in that app.** Confirmed to preview correctly in
Windows Explorer. Confirmed by Paul that VS Code "was never an issue" — the file is readable there,
just found voluminous. **Paul's decision: leave it as is** ("agree"). The size is real content (the
step table alone is 234,735 of the file's 284,504 bytes), not clutter, so there is nothing to trim
without losing substance.

---

## 6. Paul's decisions this session, in full

| What | Decision |
|---|---|
| Instructions to Claude Code | Standing instruction: always drafted by the consultant session, never sent by Paul directly |
| 10aq's fallback wording | Accept "publish-as-review" over the literal, now-unbuildable "route to Review" wording |
| Flag 1 (dead `tax_year` local) | Fix it |
| Flag 2 (wrong docstring) | Fix it |
| Flag 3 (stale test cross-reference) | Fix it |
| Push the three-flags commits | Yes |
| Build the new unresolved-client-guard test | Yes |
| Restructure the design document | Agreed, Paul's own initiative |
| How to restructure | Two separate steps: shrink the headline first, decide the split only after |
| The split's actual seam | Sections 16 and 17 only, based on Paul's own account of how he reads the document |
| A subfolder for the split files | No, declined, "lets forget that for now" |
| Retain original section numbers in the split | Yes, Paul's own mid-task correction |
| The corrected Cowork project-instructions text | Approved, pasted back himself, "OK that is done" |
| `2026-07-25_BUILD_STATUS.md`'s size/readability | Leave as is, "agree" |
| Next Claude Code brief | 10az (delivery-log writer), sent |
| Phone app Statements screen | Verify fully (client, server, pipeline) before any design-document correction, "agree" |
| Phone app: ever deployed? | No — "never deployed" |
| A handover is due | Yes, this document |

---

## 7. The state, as this session leaves it

**Amendment record, `2026-07-25_CONSOLE_DESIGN.md`: 457 rows, 1 to 457, strictly sequential, no gaps,
no duplicates.** Verified just now by a script scoping strictly between `## Amendment record` and
`## How to use this document` and checking every numbered row — not carried from an earlier claim.

**Step table, `2026-07-25_BUILD_STATUS.md`: 80 rows — 49 BUILT, 27 OUTSTANDING, 3 CANCELLED, 1
MOVED.** Verified just now the same way, and cross-checked against the document's own headline
sentence ("49 built, 27 outstanding, 3 cancelled, 1 moved out of this order, 80 steps"), which
matches exactly.

**Git, `feat/console-phase0`: HEAD is one commit ahead of origin.** Verified just now by reading both
`.git/logs/HEAD` and `.git/logs/refs/remotes/origin/feat/console-phase0` directly. Last pushed:
`8f3e71e3`. Local HEAD: `a437dbd` (the sections 16/17 split), not yet pushed. **The PowerShell push
command for this is owed to Paul and was not yet given** — the handover was written first. Give it
next: `git push` from a clean working tree, or confirm nothing else is staged first with `git status`.

**Files delivered and committed this session** (local staged-copy sizes/md5s as last read this
session — see section 9 caveat on currency): `2026-07-25_CONSOLE_DESIGN.md`, `2026-07-25_BUILD_STATUS.md`
(new), `CLAUDE.md` (one sentence). All three landed in commit `a437dbd`; the design document also
carries the earlier `dd5e2bf` (amendment 457) and `efcfae7` (headline-to-appendix move) from this
session.

**Cowork project custom-instructions text**: corrected and confirmed live by Paul. Nothing owed.

---

## 8. Files this session changed, with verification detail

**`2026-07-25_CONSOLE_DESIGN.md`** — final state this session: 1,276,429 bytes, md5
`155b7409ea194dc84e3c7add4959e456` (local staged copy, read just now for this handover). Changes:
amendment 457 added correcting amendment 405's row in place; headline paragraph shrunk from 22,489 to
686 characters with history moved to new appendix 16A; sections 16 and 17 (including 16A) then
extracted wholesale into `2026-07-25_BUILD_STATUS.md`, replaced with a short pointer. Committed
`dd5e2bf`, `efcfae7`, `a437dbd`.

**`2026-07-25_BUILD_STATUS.md`** — new, 284,504 bytes, md5 `f85a7a4612b34c71d1254ece01ace122` (same
caveat). Contains sections 16 and 17 verbatim, section numbers unchanged, plus an explanatory header.
Committed as part of `a437dbd`.

**`CLAUDE.md`** — one sentence changed, pointing "the current state of the build" at
`2026-07-25_BUILD_STATUS.md` instead of just "the design document... and the handover." md5
`862a26fa763e43f5985d6740a20cee0a`. Committed as part of `a437dbd`.

**No `.bak-before-<change>` files were created or referenced in git-add instructions this session**,
per session 27's own corrected practice. Not independently re-confirmed against Paul's actual
`git status` output this session, since this handover was written without a fresh terminal paste.

---

## 9. What this handover does not claim

- **The pipeline-side verification of the phone app's Statements feature is incomplete.**
  `worker/intake/folder_reader.py`, which defines `is_statement` and presumably `scan_inbox()`, was
  never staged this session and was not read. Do not tell Paul the Statements feature is fully
  verified end to end until that file is read and the sidecar-to-`is_statement` mapping is confirmed
  to match what `upload.js` actually writes.
- **The `v5`/`v6` version-number discrepancy in the phone app has not been reported to Paul or
  investigated.** Flagged here only.
- **The PWA "reverts to Set up your app" problem Paul reported is not diagnosed.** Only the relevant
  storage mechanism was located.
- **Step 10ak's row in `2026-07-25_BUILD_STATUS.md` has not yet been corrected.** It still reads as
  though the Statements screen needs building from scratch. It does not — it exists and has never
  been deployed — but the row is not rewritten pending the item above.
- **Amendments 450 to 456 (the earlier Desktop-batch work) are not independently narrated by this
  handover.** They are this session's by date, per the design document itself, but occurred before
  the portion of this session visible to the summary this handover was drafted from. Trust the
  document, not this handover, for how that work was verified.
- **File sizes and md5s in sections 7 to 8 are read from the local staged copy at the time this
  handover was written, not re-staged from Paul's machine afterward.** They should match what is on
  his machine, since every prior edit this session went stage → edit → deliver → commit → re-stage →
  md5-compare, but this handover itself did not repeat that round-trip before being written.
- **No test suite was run this session** by the consultant session itself (no shell on Paul's
  machine, or none confirmed). Every pass/fail count in the design document is Claude Code's own
  claim, relayed and spot-checked by reading the specific files it names, not independently executed.
- **The push of `a437dbd` has not happened yet.** See section 7.

---

## 10. Where the next chat starts

**Ask Paul first**, the order is his, but the obvious candidates:

1. **Give Paul the PowerShell command to push `a437dbd`.** Not yet done.
2. **Finish the phone-app pipeline check**: stage and read `worker/intake/folder_reader.py`, confirm
   how `is_statement` is set, then correct step 10ak's row in `2026-07-25_BUILD_STATUS.md` (a new
   amendment in `2026-07-25_CONSOLE_DESIGN.md`, per this project's own convention) to reflect "exists,
   never deployed" rather than "needs building."
3. **Report, and ask Paul about, the two open phone-app items**: the `v5`/`v6` version mismatch, and
   the PWA reversion-to-setup problem (not yet even started).
4. **Check whether `PROMPT_claude_code_2026-09-12_exports_leave_the_repository.md` (step 10r) was
   actually sent**, before assuming it is queued.
5. **Wait for, then verify, the 10az report** when it lands, the same way every other Claude Code
   report this session was verified: read in full, then check its claims against the files directly.
6. **The four remaining unbriefed steps**, section 3's table, each on its own when Paul wants it.
