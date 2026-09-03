> Note on origin: this session ran in Cowork (Claude's desktop assistant), advising alongside Claude Code, which wrote all the actual code. This doc follows the Handover Protocol already defined in this repo's `CLAUDE.md`, so either a Cowork chat or a Claude Code session can pick it up.

# Handover — 2026-07-24 — Receipt Capture bug-fix and resolution session

## What this session was

Paul brought a completed Claude Code fix for the `client_name` bug to review, then used this chat as a systems adviser: reviewing Claude Code's designs before code was written, drafting precise prompts for Paul to relay to Claude Code, and independently verifying every claim against the actual repo files and the live SQLite database. No code was written directly in this chat — all of it went through Claude Code, prompted from here.

## What was completed and verified

**1. Original `client_name` bug backlog — closed out.** All 19 real receipts affected are now `ok` with real categorisation (1 matched, 18 flagged `unmatched` for manual review). Verified via a LEFT JOIN query: 0 orphaned `extraction_id` references.

**2. Part 1 — Automatic retry on code fix.** `app.py::_retry_failed_receipts()` finds any `failed`/`needs_review` receipt whose `pipeline_version` differs from the currently running git short-hash, and retries it once through the shared pipeline. Locking (`receipts.locked_at`, atomic acquire/release, 60-minute staleness allowance) stops it clashing with manual resolution running at the same time.

- Bug caught and fixed: the original version-comparison used `<`, which is a lexicographic string comparison on git hashes and doesn't mean "older" — fixed to `!=`. Verified by running the actual query against the live DB and by watching a live app restart correctly retry the one expected candidate.

**3. Part 2 — Duplicate detection, corrected.** `is_recorded_and_filed()` now only hard-blocks a resend if the earlier attempt was genuinely filed (`filed_path IS NOT NULL`), not merely attempted. `find_by_transaction_loose()` (case-insensitive, ±£0.01) plus `_signals_differ()` (compares `receipt_ref_number`/`receipt_time`) route ambiguous same-supplier/date/amount matches to a new `possible_duplicate` status rather than auto-filing or auto-blocking — this specifically covers Paul's Terminal 5 same-day-parking-charge case.

**4. Part 3 — Manual resolution tool.** `resolve_receipt.py` is built and working: `python resolve_receipt.py <receipt_id>` (interactive prompts for all 7 fields) or with correction flags (`--supplier`, `--gross`, etc., or `--duplicate-decision file/discard`). Locks the receipt, re-validates, categorises, files, and appends a new `engine="manual_correction"` extraction row — never overwrites history.

**5. Shared pipeline consolidation.** `worker/extraction_pipeline.py::process_extraction_result()` is now the one function used by all three live call sites (email intake, folder intake, Part 1 retry) for validate → semantic-dup-check → save → categorise/file → log. This was built specifically because the original `client_name` bug happened due to path divergence — one intake path had a fix the other lacked.

**6. Real bugs caught during implementation and fixed (all verified by direct code read and/or live DB query, not just taken on Claude Code's word):**
- `save_categorisation()` keyword mismatch (`vendor_code` passed where `vendor_key` expected) — crashed 10 live receipts.
- `_file_unfiled_ok_receipts()` was filing receipts with `category=None`, silently skipping categorisation — fixed to call the categorisation engine properly.
- Same function was generating a fresh `extraction_id` instead of reusing the real one — caused orphaned categorisation rows.
- Stale-lock recovery query used strict `locked_at IS NULL`, excluding exactly the rows it was meant to recover — fixed to `(locked_at IS NULL OR locked_at < cutoff)`.
- `process_extraction_result()` was missing the `file_review()` call for non-ok statuses during the refactor — a regression against original behaviour, fixed.
- `mark_processed()` (moves the email out of INBOX) wasn't being called for all outcomes, especially `possible_duplicate` — fixed with optional params, email-only.
- `add_validation_note()` used invalid SQL (`UPDATE ... ORDER BY ... LIMIT 1`) — fixed to target the specific `extraction_id`. **Not yet independently reconfirmed as committed — check `git log` for this before assuming it's in.**

**7. Test-data cleanup.** Receipt `56b29977-8c9d-4912-9c90-cf1a064b5d00` (client_code TEST, genuinely inconsistent OpenAI extraction across 4 attempts) closed out: DB status set to `discarded` with a logged reason, three duplicate files deleted from `Clients/Test/Review/` on disk. Confirmed via direct query that it no longer appears in the failed/needs_review backlog.

**8. Git hygiene.** `.gitattributes` added (`* text=auto eol=lf`) plus `git add --renormalize .` to stop CRLF drift inflating diffs. `logs/*.ndjson` added to `.gitignore` (runtime output, not source, and may contain client-identifying data).

## What's drafted but not yet applied

**`RECEIPT_CAPTURE_GUIDE_DRAFT_2026-07-24.md`** (saved alongside this handover doc, in this same folder) — a full rewrite of `RECEIPT_CAPTURE_GUIDE.md` reflecting everything built this session: Automatic Retry & Manual Resolution as a numbered step, a new "Where Data Really Lives" section (database is sole source of truth, folders are one-way output), `possible_duplicate` woven throughout, `resolve_receipt.py` documented under a new "Resolution Scripts" heading, the `client_code` fallback-to-raw-code behaviour, the shared-pipeline principle, updated schema/status list, a second worked timeline example, and a "Future Enhancements" section listing the dashboard and the retry-cap idea as explicitly not yet built.

**Paul's instruction: do not apply this to the real `RECEIPT_CAPTURE_GUIDE.md` yet.** He asked for a first draft to review "at the end of this current session" — that review hadn't happened before the handover became the priority. Whoever picks this up should surface the draft to Paul for a decision before overwriting the real file.

## Open / undecided

- **Retry cap.** Discussed analytically only — benefits (cost, Review-folder noise, signal clarity) and risks (Paul's bursty commit pattern makes a fixed retry-count threshold awkward to choose; what state should a receipt land in once the cap is hit — a new status, or just a count with no status change; whether manual-correction attempts via `resolve_receipt.py` should count toward the cap). No threshold value has been agreed, no prompt drafted.
- **Staff-facing "N items need review" alert.** Raised as a possible cheap stopgap before the full dashboard exists (currently there is no staff-facing notification at all — confirmed via grep of `worker/email/alerts.py`, which only has client-facing `send_no_attachment_alert()` and `send_unknown_sender_alert()`). Not decided or scoped.
- **`add_validation_note()` fix commit status.** Paul was told to commit this as its own commit; not independently reconfirmed via `git log`.
- **Dashboard scoping.** Already logged in the Notion Automation & AI Backlog with what's been listed so far (status overview, Needs Review/Possible Duplicate queue with links into `resolve_receipt.py`, OpenAI credit/balance check, ability to switch AI provider). Paul said this moves to top priority once testing wraps up, but scoping hasn't started. Note from later in the session: `resolve_receipt.py` as it stands is a CLI script (positional `receipt_id` arg, either correction flags or an interactive `input()` loop) — it can't be called from a web dashboard as-is. It would need splitting into an importable function (no `input()`/`print()`) with the current CLI as a thin wrapper, before the dashboard can call it directly.

## Where things actually live (per this session's own findings)

- The database (`data/receipts.db`) is the only source of truth for what needs attention — not the mailbox folders, not the Review folder on disk. Always check with `query_receipts.py` / `view_receipts.py`, never by looking at a folder.
- `clients.csv` lives in OneDrive at `IntelliBooks/clients.csv`, not in this repo.
- Client TEST *is* a registered client_code (`Client_004,Test,,FIRM001,UNSPECIFIED,TEST,`) — an earlier claim in this session that it wasn't registered was wrong, caused by a sandbox path-resolution failure, not a real gap in `clients.csv`. Corrected on the record.

## Suggested first steps for whoever picks this up

1. Read this file and the guide draft sitting next to it.
2. Confirm with Paul whether the guide draft should now be applied to the real `RECEIPT_CAPTURE_GUIDE.md`.
3. Check `git log` to confirm the `add_validation_note()` fix landed as its own commit.
4. Pick back up on the retry-cap design conversation if Paul wants to continue it — the questions above are exactly where it left off.
