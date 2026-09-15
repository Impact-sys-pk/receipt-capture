# Where receipt documents live: the stores and the lifecycle

Written 2026-09-15, consultant session. Verified against the code, not against any document describing the code: `worker/storage/store.py`, `worker/publish.py`, `worker/filing.py`, `config.py`, and `IntelliBooks-Desktop-v3.html` were all read directly.

## The stores

**The archive** (Intellibills). One file per document. Never changed once written. Path: `Intellibills\Documents\{client_id}\{year}\{month}\{receipt_id}_{filename}`, built by `save_file()` and `save_inbox_file()` in `worker/storage/store.py`, rooted at `config.FILES_DIR`. The year and month are the arrival date in London time, not the invoice date: filing runs before extraction, and an arrival date never needs correcting. Already built. Matches this design as it stands.

**The database** (Intellibills), three tables by role:
- The record table: one row per document, holding the archive path and its status.
- The log table: one row per reading of a document, tagged by machine or by operator, never updated once written. An operator's correction writes a row here, the same as an automatic read does. An "unchanged correction" is not a coherent case: if nothing changed there is nothing to log.
- The working table: one row per document awaiting a decision, reflecting the last item published to IntelliBooks, not live edits made inside IntelliBooks. Intellibills and IntelliBooks share no live database, so a correction made inside IntelliBooks cannot appear here in real time. Only the final decision, when it comes back on the pipeline's next poll, moves this table. The poll is every five minutes, `POLL_INTERVAL_SECONDS = 300` in `config.py`; every other mention of "next poll" below means this same cycle.

**IntelliBooks' own copy.** The receipt held and edited in `books.receipts` while the operator works on it carries the archive path, not the image. Every view of the document, thumbnail or full, reads the file live from the archive at that path when it is opened. Zero-copy: the image is never embedded into IntelliBooks' own data, so nothing is later dropped, because nothing was copied in.

**The transaction file** (IntelliBooks). `{client_id}-books.json`'s `transactions` array. Each transaction carries its own status, new or posted, and a `receiptId`. A receipt's id may appear on more than one transaction. Confirmed wanted, not merely tolerated: a split transaction (one bank transaction, several ledger entries), or one document (an insurance schedule) attached to several instalments, are both real cases.

**The Clients folder.** `Clients\{client_folder_name}\IntelliBooks\Receipts\{tax year}\`, owned by neither module: Intellitax's own filing structure, presented through the client portal. Written only by Intellibills, on a firm setting: on Post, on successful publish, or never. Corresponds to `receipts.filed_path`. Deleting a receipt that already has a Clients folder copy delivered does not touch the archive; it optionally removes the Clients folder copy, by the operator's choice made at the point of deletion, actioned on the pipeline's next poll.

## The lifecycle, receipt to posted transaction

1. A document arrives, by email or folder intake, and is written once to the archive by `save_file()` or `save_inbox_file()`.
2. Its record is created in the record table, and its first reading is written to the log table.
3. Extraction runs and is logged. Any operator correction, wherever it happens, is also logged.
4. The item is published into `IntelliBooks\Incoming\`.
5. IntelliBooks picks the item up and holds its own copy in `books.receipts`, keyed to the archive path.
6. The operator works the receipt by one of two routes. Route A, `confirmPostToCashbook()` / `postReceiptToCashbook()`: post it directly to the cashbook, creating a new transaction and copying the category and VAT onto it. Route B, `attachReceipt()`: attach it as evidence to an existing transaction, arising from bank statement import or matching, copying no figures. Both routes converge at the same posting step.
7. Posting, `postTxn()`, is one meaning only: signing off a transaction, whether that transaction already existed or was created in the same act from a receipt. A receipt is never itself "posted"; only a transaction is.
8. Posting calls `reportAttachedAfterPost()`, which sends a note back to Intellibills on the pipeline's next poll, regardless of which route was taken.
9. The operator may instead delete the receipt. Delete is the operator-facing verb; the note sent to Intellibills records the outcome as `discarded`, and carries the operator's choice of whether to also remove a Clients folder copy already delivered. The archive copy is never touched by a deletion, either way.

Unposting or deleting a transaction (`unpostTxn()`, `deleteTxn()`) affects only the transaction: it remains in the Transactions tab, marked unposted or removed. The Receipts tab and the record table are unaffected either way.

## What changes from today

- The receipt thumbnail on the Receipts tab is replaced by a type pill, computed synchronously with no file read, styled like the existing status pills. Clicking it triggers an on-demand, asynchronous read of the file from the archive, using the same three-call pattern (`getFileHandle` / `.getFile()` / `URL.createObjectURL`) already used for PDFs today.
- The published item stops carrying `image_base64` and `image_media_type`. It carries the archive path instead, now that IntelliBooks may read the archive directly. This follows automatically from dropping the base64 image; it is not a separate decision.
- PDF viewing, which today falls back to reading from the Clients folder copy, should target the archive directly instead, for the same reason.
- No new grant is needed for IntelliBooks to read the archive directly. Its single folder handle, `rootHandle`, is already requested at the practice root (`showDirectoryPicker({mode:"readwrite"})`), and `Intellibills\Documents\` sits under that root. IntelliBooks already has read and write reach into the archive today, technically; this design is the first thing to use it.

## Open

- `make_enriched_sidecar()` does not currently carry an archive or file path field. One is needed on the published item, or IntelliBooks must derive it from fields the sidecar already carries (`receipt_id`, `client_id`, `capture_date`, `original_filename`) — the archive path is built deterministically from exactly those fields, so deriving it is possible. Which of the two is chosen has not been decided.
- Multiple transactions may now carry the same `receiptId`. Whether the existing single Attach control in `IntelliBooks-Desktop-v3.html` currently guards against a second attachment, and if so whether that guard needs removing, has not been checked against the code.

## What was checked and found not to need any change for this redesign

VAT treatment, bulk actions (`bulkPost`, `bulkCashbook`), the Receipts-view "Attached" marker (a live computed value, never stored), the cashbook check, and unposting or deleting a transaction.

Out of scope, noted so it is not mistaken for an oversight: of the two validation checks this area used to cover, only the cashbook check survives; the other, the Difference check, was cancelled on 2026-09-11. Neither stores or sends anything, so neither bears on document storage.

## What has not yet been done

- This text has not been written into `2026-07-25_CONSOLE_DESIGN.md`. It is ready-to-insert content, held here.
- An implementation gap list was drawn up against `worker/publish.py` and `worker/filing.py`: build items on both the Intellibills and IntelliBooks sides, assessed as small to moderate, not yet itemised in this note and not started.

## Confidence

High on every claim above that names a function or file: each was read directly in the code this session. Medium on the three-table shape of Intellibills' database (record, log, working): the design is agreed, but it has not been checked line for line against the live `receipts` / `extractions` / `resolution_events` tables in `receipts.db` for an exact fit.

The numbered lifecycle above is a fresh write-up from this session's verified findings, not a retyping of an earlier draft: the earlier draft's exact wording was not available to check against when this file was written. The substance was checked as set out in this note; the phrasing was not compared word for word to whatever was agreed in chat before.
