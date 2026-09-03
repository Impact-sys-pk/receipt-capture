> Note on origin: this session ran in Cowork (Claude's desktop assistant), advising alongside Claude Code, which wrote all the actual code. This doc follows the Handover Protocol already defined in this repo's `CLAUDE.md`, so either a Cowork chat or a Claude Code session can pick it up.

# Handover — 2026-07-25 — Test plan execution, three bugs found and fixed, retry cap built, guide rewritten

## What this session was

Continuation of the 2026-07-24 handover. Paul ran the outstanding T1–T5 test plan live against the real IMAP mailbox and OpenAI, with this chat verifying every claim directly against the database, logs, and git diffs, not just taken on report. Three genuine bugs were found along the way (not by design, by actually testing), each fixed by Claude Code and independently re-verified here. The retry-cap design question left open on 2026-07-24 was properly designed and built. The user guide was rewritten to match. No code was written directly in this chat, all of it went through Claude Code, prompted from here, same pattern as last session.

## What was completed and verified

**1. T1 — Resend a failed receipt, confirm no longer wrongly blocked.** Initially failed: a resend was silently blocked as a duplicate, but investigation traced this to a bug unrelated to the original client_name fix (see #2 below). Confirmed working after that fix: resending the identical file created a new receipt row rather than being skipped, verified via `processed_attachments`.

**2. Bug found and fixed — IMAP dedup used sequence numbers, not Message-ID headers.** `worker/email/reader.py`'s `fetch_new_messages()` set `message_id` from `imap.search()`'s sequence number, not `msg.get("Message-ID")`, despite the function's own docstring claiming header-based dedup. Sequence numbers renumber every time a message is expunged (i.e. after every processed email), so a brand-new email could collide with a stale `processed_attachments` row from a completely unrelated earlier email. Confirmed via direct query: `message_id='1'` was reused across three unrelated receipts on different dates. Also found and fixed alongside it: `move_email_to_folder()` addressed the mailbox by the same unstable sequence number, so a multi-message poll batch risked mis-addressing a later email after an earlier one in the same batch was expunged. Fixed in `aa9ae24`: real `Message-ID` header now used for dedup/alerts, `imap.uid(...)` commands used throughout for all mailbox addressing (search/fetch/copy/store). Verified live: sent two emails in one poll batch, correctly processed and routed to different folders (`Failed Processing` and `Processed Receipts`) with no cross-contamination.

**3. Bug found and fixed — `resolve_receipt.py` categorised before the extraction row existed.** `categorisations.extraction_id` has a foreign key to `extractions`, but `resolve_receipt.py` called `save_categorisation()` before `save_extraction()`, which only ran after filing. Every manual correction hit `sqlite3.IntegrityError: FOREIGN KEY constraint failed`. Fixed in `b480a7e` by moving `save_extraction()` earlier. Verified live twice: once against a fictional vendor (correctly landed `unmatched`, proving the FK fix without a real match), once after seeding a throwaway TEST2 vendor mapping (correctly landed `match_source='client'`, `confidence='high'`, real GL code, sidecar showed `"category": "999"`).

**4. Bug found and fixed — `resolve_receipt.py` called a nonexistent method.** `repo.append_validation_notes(...)` doesn't exist, only `add_validation_note()` (singular) does, confirmed by grep. This would crash any correction that still failed validation after resubmission. Fixed in `8c67da0`, one-line rename.

**5. T3 — Correct a needs_review receipt via `resolve_receipt.py`.** Fully verified end to end after the two bugs above were fixed: correction filed successfully with a real GL code, confidence, and the original `needs_review` extraction preserved alongside the new `manual_correction` one in the audit trail.

**6. T4 — Two same-day, same-amount receipts, different ref numbers.** Sent two fake Terminal 5 parking receipts, same supplier/date/amount, different ticket numbers. Both extracted correctly, both filed `ok`, neither wrongly flagged `possible_duplicate`. Confirmed `_signals_differ()` used the distinct `receipt_ref_number` values correctly.

**7. T5 — Kill `resolve_receipt.py` mid-run, confirm lock recovery.** Confirmed via DB: an abrupt process kill left `receipts.locked_at` set and never released. Verified the recovery mechanism directly against `Repository.acquire_receipt_lock()` (rather than waiting a real hour): a fresh lock attempt within the 60-minute window correctly returned `False`, and simulating the window having elapsed correctly returned `True` and reclaimed the lock. Lock released afterward to leave the receipt clean.

**8. Retry cap designed and built.** Previously, `_retry_failed_receipts()` retried every failed/needs_review receipt once per `pipeline_version` change, forever, no limit, confirmed by reading `find_failed_by_version()`. Discussed and agreed with Paul: a 7-day wall-clock cutoff (`AUTO_RETRY_MAX_AGE_DAYS`), not a retry-count cutoff, since a count-based cap would unfairly exhaust receipts caught in a burst of commits (we had 3 commits in about an hour this session alone). Past the cutoff, a receipt transitions to a new status, `retry_exhausted`, checked lazily inside `_retry_failed_receipts()` rather than a separate job. Manual `resolve_receipt.py` runs don't count toward or reset it. Built and committed in `6696bb1`, with its own red/green regression test for the exact boundary. Verified independently: diff matches description, 17/17 tests pass.

**9. User guide rewritten.** `RECEIPT_CAPTURE_GUIDE.md` replaced with the draft from 2026-07-24, updated further for everything above: `retry_exhausted` added to every status list, Step 8 describes the 7-day cap, "Where Data Really Lives" now explicitly notes that a corrected receipt's original email stays in its mailbox folder regardless of resolution status (see "Open/undecided" below), and a new "Who This Guide Is For" section frames the day-to-day operator as an office administrator rather than an accountant, with a short, explicit list of what's safe to decide independently versus what's worth a quick check with an accountant or Paul first (GL code looks wrong rather than missing, uncertainty about a possible-duplicate, uncertainty reading a figure off the original document). Committed in `e863b61`.

**10. Git hygiene.** All ten commits from this session and last are on branch `fix/imap-message-id-dedup` (based on `fix/date-disambiguation-vat-swap`), pushed to origin. **Not yet merged into `main`** — `origin/main` is still at the `fix/date-disambiguation-vat-swap` merge from before this session started.

## Open / undecided

- **Branch not merged to main.** `fix/imap-message-id-dedup` has 6 commits (message-id/UID fix, two resolve_receipt.py bugs, retry cap, guide rewrite) pushed to origin but not merged. Whoever picks this up should confirm with Paul whether to open a PR now or continue stacking work on this branch first.
- **Mailbox-folder-as-log gap, deliberately parked.** Once a receipt is corrected via `resolve_receipt.py`, the original email stays in whatever mailbox folder it was routed to ("Needs Review", "Failed Processing", etc.) — `resolve_receipt.py` has zero IMAP awareness, confirmed by grep. Paul's explicit decision: park this until the dashboard exists and gives complete confidence in DB-backed status, then reconsider whether it still matters once mailbox folders are treated purely as a log, not a queue. Documented in the guide accordingly.
- **Old draft/handover files still untracked.** `2026-07-24_HANDOVER_TO_NEXT_SESSION.md` and the now-superseded `RECEIPT_CAPTURE_GUIDE_DRAFT_2026-07-24.md` are sitting untracked in the repo root. Paul hasn't decided whether to delete the draft (now folded into the real guide) or keep it as a dated snapshot.
- **Two disposable test receipts still failing.** `de3e901e-...` and `e9f3faf3-...` (both `T1_deliberate_fail_test.jpg`, genuinely invalid image data used to test T1) are still `status='failed'` in the live DB and will keep getting retried on every future commit until they hit the new 7-day `retry_exhausted` cutoff (created 2026-07-25, so around 2026-08-01). Paul may want to mark them `discarded` sooner, same as the `56b29977` test receipt was cleaned up in the previous session, rather than waiting for the cutoff or letting them burn OpenAI calls on every future deploy in the meantime.

## Next step: Dashboard

This is the priority Paul named for the next session. Context already logged in the Notion Automation & AI Backlog from before: status overview, a Needs Review/Possible Duplicate queue with links straight into the resolve tool, OpenAI credit/balance monitoring, and the ability to switch AI provider.

**Known blocker, flagged in the 2026-07-24 handover and still true:** `resolve_receipt.py` is currently a CLI script, positional `receipt_id` argument, either correction flags or an interactive `input()`/`print()` loop. It cannot be called directly from a web dashboard as-is. It would need splitting into an importable function (no `input()`/`print()`) with the current CLI kept as a thin wrapper, before the dashboard can call it directly. This should be one of the first design questions to resolve.

Other design questions not yet touched: hosting (local vs. something reachable from a browser), auth (this touches real client financial data), whether it reads the DB directly or through a thin API layer, and whether "switch AI provider" means swapping the existing `BaseExtractor` interface at runtime or just at config/restart time.

## Where things actually live (per this session's own findings)

- The database (`data/receipts.db`) is the only source of truth for what needs attention, not the mailbox folders, not the Review folder on disk, confirmed and now explicit in the guide.
- Current live status counts (checked at end of session): 23 `ok`, 2 `failed` (the two disposable test receipts above), 1 `discarded`.
- `clients.csv` lives in OneDrive at `IntelliBooks/clients.csv`, not in this repo. TEST and TEST2 have no email registered and no vendor mappings of their own (confirmed by query), only `Client_001` (Paul Keating, real client) has any vendor history.

## Suggested first steps for whoever picks this up

1. Read this file.
2. Confirm with Paul whether to merge `fix/imap-message-id-dedup` into `main` now or keep stacking on it.
3. Decide what to do with the two disposable failed test receipts and the old draft/handover files sitting untracked.
4. Start dashboard design by resolving the `resolve_receipt.py` CLI-vs-importable-function blocker first, since the rest of the dashboard's "resolve" functionality depends on it.
