# Claude Code brief, 2026-09-14: step 10az, the delivery-log writer

Section 16 step 10az. Decided by amendment 456 in `2026-07-25_CONSOLE_DESIGN.md`, closing part of
outstanding item 131 (the other part, step 10au, is Desktop-side and not yours). Not verified
against the code by this session beyond what's stated below; confirm it yourself before changing
anything, per this project's own rule.

## Why this exists

Step 10au is a check comparing what's actually in a client's folder against what IntelliBooks
recorded delivering there. That check cannot be built because nothing writes the record it would
check against. This step is the record.

Confirmed by this session, 2026-09-14: `worker/client_copy.py` was read directly and contains
nothing referencing "Delivery", "delivery_log", or any per-document log. `IntelliBooks-Desktop-v3.html`
was searched and has one incidental mention of "delivery log" in an on-screen help table, nothing
that writes one.

## What to do

1. Find `copy_for_published_receipt()` in `worker/client_copy.py` yourself and read it directly. It
   is the function that copies a document into a client's folder, per amendment 122 (the pipeline's
   job, not Desktop's).
2. Every time it copies a document, append one line to `IntelliBooks\Delivery\{CODE}.log`, where
   `{CODE}` is the client's own code/id. Append-only: never rewrite or truncate the file. Never
   delete a log file, same as this project's other event logs.
3. Format: one JSON object per line (NDJSON), matching the style `receipt_events_FIRM001.ndjson`
   already uses for this kind of fact, per amendment 291. Before choosing field names, find that
   log's own writer and read its actual field names and conventions, and use the same spellings
   here rather than inventing new ones for the same kind of thing. Starting point, correct it
   against what you find:
   - `client_id`
   - `receipt_id`
   - `document_path` (the path written, relative to the client's own folder)
   - `posted_at` (ISO 8601, UTC)
   - `pipeline_version`
   If the copy function doesn't have ready access to one of these fields, say so rather than
   inventing a value for it.
4. A failure writing the log entry must not stop the document copy from succeeding, and must not
   silently disappear either: this project's own step 10af, built today in Desktop, exists because
   a swallowed file failure is the wrong default. Log a warning naming the receipt if the log write
   fails; the copy itself still completes.
5. Confirm whether any per-firm setting already gates whether the copy into `Clients\` happens at
   all (amendment 73 mentions one). If it does, the log write follows the same gate: no copy, no
   log line. If you find no such setting controls the log independently, don't invent one.

## What is not asked

Do not build step 10au, the reconciliation check. That's a separate step, on the Desktop side, and
depends on this one. Do not touch the reader of `receipt_events_FIRM001.ndjson`, only match its
field-naming convention.

Report the same way as your last two: what you read directly, what you built, the suite before and
after, and anything you had to judge rather than measure.
