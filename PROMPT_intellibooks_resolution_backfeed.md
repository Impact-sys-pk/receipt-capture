# Build brief: IntelliBooks Desktop resolution back-feed

Paste this whole file into a new Cowork session. It is self-contained.

Origin: agreed with Paul in a Cowork design session on 2026-07-25, during the design of the Receipt Capture console. The pipeline half of this contract is being built separately in the receipt_capture repo. Both halves must match the contract in section 4 exactly.

---

## 1. What I want built

Three changes to `IntelliBooks-Desktop-v3.html`:

1. **New.** When a Review item is filed or deleted in the desktop app, write a small resolution note to a drop folder so the pipeline can update its own records. This is the desktop half of an agreed two-sided contract.
2. **Bug fix.** `exportPracticeBackup()` reads books from the pre-item-12 legacy path, so "Practice Backup (all clients)" silently produces an empty backup.
3. **Small fix.** `parseSidecar` should read the category **name** from the sidecar, not the nominal code, so receipts arrive categorised. See section 5a.

Nothing else in the app changes. Do not touch the bank transactions side, matching, reporting, imports, or the review UI itself.

## 2. Intended lifespan

A tool for the practice to use now, kept simple, consistent with the existing app. No new libraries, no build step, no framework. Everything stays in the single HTML file.

## 3. Why this is needed (read this before building)

The system specification, section 4.3, states that corrections made in IntelliBooks Desktop are the practice's decided truth, and that there is no back-feed to the pipeline in Phase 1. Change log item 19 implemented that deliberately.

Three pipeline features built after that decision now break because of it:

- **Auto-retry on `pipeline_version`.** The pipeline re-extracts anything its database still marks `needs_review` whenever the code changes. A receipt you fixed in the desktop app stays on that list, costs an OpenAI call every time, and if a retry succeeds the pipeline files a second copy in a different place.
- **Duplicate protection.** The pipeline decides whether it has seen a receipt before by checking whether it filed it. It did not file the one you completed in the desktop app, so if the same receipt arrives again by another channel nothing stops it.
- **Vendor learning.** The pipeline learns supplier-to-category mappings from resolutions. Corrections made in the desktop app never reach it, so the same supplier keeps arriving miscategorised.

The fix keeps the agreed rule intact. The desktop app still never writes to `receipts.db`. It writes a note; the pipeline reads the note and updates its own database. This is the same pattern the phone capture app already uses: drop a file in a folder, let the pipeline pick it up.

## 4. The contract (must match the pipeline side exactly)

### Location

`{practice root}\IntelliBooks\Resolutions\`

Create the folder if it does not exist. This is system territory, per change log item 12, so it belongs under `IntelliBooks\` and not under `Clients\`.

### Filename

`{receipt_id}_{unix_ms}.json`

Including the timestamp means a second resolution for the same receipt never silently overwrites the first.

### Schema

```json
{
  "schema": 1,
  "receipt_id": "de3e901e-....",
  "client_code": "TEST",
  "action": "filed",
  "resolved_by": "desktop",
  "resolved_at": "2026-07-25T14:02:11.000Z",
  "values": {
    "supplier_name": "APCOA Parking",
    "invoice_date": "2026-07-14",
    "net_amount": 8.50,
    "vat_amount": 1.70,
    "gross_amount": 10.20,
    "currency": "GBP",
    "category_name": "Parking and tolls"
  },
  "filed_path": "Clients\\Paul Keating\\Receipts\\2026-27\\2026-07-14_APCOA-Parking_10.20.jpg",
  "original_review_files": [
    "T3_needs_review_vat_mismatch.png",
    "T3_needs_review_vat_mismatch.png.review.json"
  ]
}
```

Rules:

- `action` is `"filed"` or `"discarded"`. For `"discarded"`, omit `values` and `filed_path`.
- `receipt_id` comes from the review sidecar's `extracted_values.receipt_id` or `pipeline_receipt_id`, the same value the existing code already uses as the row id. If neither is present, still write the note, set `receipt_id` to `null`, and include `original_review_files` so the pipeline can attempt a filename match.
- `filed_path` is **relative to the practice root**, using backslashes, matching the path actually written.
- `category_name` is the category **name** as shown in the desktop app. Do not attempt to convert it to a nominal code. The pipeline handles that, and cannot do so at all until the shared chart of accounts exists.
- Amounts are numbers, not strings. Omit a field entirely rather than writing `null` or `""` for an amount that was left blank.
- `schema` is `1`. Do not change it without agreeing a pipeline-side change.

### Write timing and safety

Write the note **only after** the existing filing or deletion has fully succeeded, at the same point the code currently removes the originals from Review. If filing fails, no note.

Use the app's existing `createWritable` write path, which commits atomically on close, so the pipeline can never read a half-written file.

**If writing the note fails, do not roll back the filing and do not block the user.** Show a toast saying the receipt was filed but the pipeline could not be notified, and log to the console. A missing note is a recoverable nuisance; a failed file operation is not.

### Who cleans up

The pipeline, not the desktop app. It moves processed notes to `Resolutions\processed\` and unprocessable ones to `Resolutions\failed\`. The desktop app writes and forgets. Never delete anything from `Resolutions\`.

## 5. Change 2: the backup bug

`exportPracticeBackup()` currently does this for each client:

```js
const dir=await getDir(["Clients",safeName(c.name),"IntelliBooks"],false);
const r=await readJSON(dir,c.code+"-books.json");
if(r)all.books[c.code]=r.data;
```

That path was superseded by change log item 12, which moved books to `IntelliBooks\Books\`. No client folder has an `IntelliBooks` subfolder any more, confirmed on disk, so `getDir` throws, the `try` swallows it, and every client is skipped. The download then contains `books:{}` and reports success.

Fix it to use the same directory as `loadBooks()`:

```js
const dir=await getDir([SYS_DIR,"Books"],true);
```

Keep the legacy fallback if you think it is worth it, but the primary read must be the current location. Verify by exporting a backup and confirming both TEST and TEST2 books appear in the JSON.

## 5a. Change 3: read the category name from the sidecar

Small but it fixes a live defect.

The pipeline's enriched sidecar currently writes `category` as a **nominal code**, for example `"104"`. The desktop app's categories are **names**, for example `"Parking and tolls"`, with no codes at all. So `parseSidecar` picks up `"104"`, `catOptions()` finds no matching name, and the receipt arrives effectively uncategorised.

This matters most for "Post to cashbook" (change log item 7), which creates a transaction directly from a receipt and copies the category across, so the defect reaches the books rather than staying cosmetic.

The pipeline is being changed to write **both**: `category_code` for the nominal and `category_name` for the desktop-compatible name.

Desktop side: in `parseSidecar`, prefer `category_name`, then fall back to `category` for older sidecars already on disk. Keep `category_code` if it is present, so it survives into the books for later use, but do not display it or match on it.

Order of build does not matter. Until the pipeline emits `category_name`, the fallback preserves today's behaviour exactly.

## 6. Constraints

- UK accountancy practice, GDPR and DPA apply. **Test with the TEST and TEST2 sample clients only.** Do not use real client data in Cowork.
- Single HTML file, no new dependencies, no build step.
- Match the existing code style: same helpers (`getDir`, `readJSON`, `writeJSON`, `toast`, `safeName`), same error handling, same plain-English toast wording.
- Do not alter the review UI, the filing logic, the naming convention or the sidecar the desktop app already writes. The note is additive.

## 7. Prerequisite Paul should confirm before you build

Change log items 19 to 23 are marked "built, not yet tested live". Item 19 is the review-and-file flow this change hooks into. It has been partially confirmed since (the Review row renders correctly for client Paul Keating), but a full file-and-check has not been run.

Ask Paul whether item 19 has been tested end to end. If not, that test should come first, because attaching a contract to an untested flow makes any failure twice as hard to diagnose.

## 8. What I want back from you

1. Confirm the approach, or say plainly if you think the drop-folder contract is the wrong mechanism and why. A shared status file, or the pipeline detecting a vanished Review pair, were both considered and rejected as less explicit.
2. The three changes, built.
3. New entries in `Docs\IntelliBooks-Change-Log.md` following the existing convention, as items 24, 25 and 26.

**Do not edit `IntelliBooks-System-Specification.md` or `IntelliBooks-System-Overview.md`.** Both need substantial corrections that span the pipeline as well, and they are being updated separately. Flag anything you notice rather than fixing it.

## 9. Reference

- Contract counterpart: `C:\LastingImpact\receipt_capture\` (pipeline side, built separately)
- Design context: `C:\LastingImpact\receipt_capture\2026-07-25_DASHBOARD_DESIGN.md`
- Existing conventions: `Docs\IntelliBooks-Change-Log.md`, items 12, 13 and 19 are the relevant ones
