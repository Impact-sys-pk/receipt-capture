# Build brief: IntelliBooks Desktop resolution back-feed

Paste this whole file into a new Cowork session. It is self-contained.

**Version 2, rewritten 2026-07-28.** Version 1 was written on 26 July before the pipeline half existed. Four things in it were wrong and one of its three changes turned out to be unnecessary. Everything below reflects the pipeline as actually built and tested.

Origin: agreed with Paul in a Cowork design session on 2026-07-25, during the design of the Receipt Capture console. **The pipeline half of this contract is built, pushed and tested with 263 passing tests.** It is waiting for notes and has never seen a real one. Both halves must match section 4 exactly.

---

## 1. What I want built

Five changes to `IntelliBooks-Desktop-v3.html`. Two are the substance, three are small and were found while building the pipeline half.

1. **New, the substance.** When a Review item is filed or deleted, write a small resolution note to a drop folder so the pipeline can update its own records. Section 4.
2. **Bug fix.** `exportPracticeBackup()` reads books from the pre-item-12 legacy path, so "Practice Backup (all clients)" silently produces an empty backup. Section 5.
3. **Rename.** The button reading `Run Matching Analyser` does no matching. Section 6.
4. **Guard.** `delCategory()` lets you delete a category that a statement rule or a receipt still uses. Section 7.
5. **A question, not a change.** Whether a transaction may be posted with a blank category. Section 8. Do not build anything for this; give Paul the options.

**No longer wanted, and this is a change from version 1.** Version 1 asked for a `parseSidecar` change to prefer `category_name` over `category`. **It is not needed.** The pipeline now writes three keys, `category_code`, `category_name` and the legacy `category` holding the **name**, and `parseSidecar` at line 1141 already tolerates a plain string, an object with a `.name`, or `asserted.category`. So Desktop reads the new sidecars correctly with no change at all. Do it only if you want the code to be clearer; it fixes nothing.

Nothing else changes. Do not touch the bank transactions side, matching, reporting, imports, or the review UI itself.

## 2. How to work, because this app has no tests

`IntelliBooks-Desktop-v3.html` is a single 2,229-line file with no test suite and no build step, and it is the application the practice actually uses. So the discipline that has worked on the pipeline side, a failing test before a fix, is not available. The substitute:

- **Copy the file before you start.** `IntelliBooks-Desktop-v3.html.bak-2026-07-28` beside it. Say in your report that you did.
- **One change at a time**, and stop after each so Paul can try it. Do not batch all five and hand back a single edited file.
- **Read the changed region back after each edit** and quote it, rather than reporting what you intended to write.
- **Give Paul a manual check per change**, phrased as steps he can follow in the UI, because he is the test suite here.
- Keep every change additive where you can. The note writing is purely additive. The backup fix replaces one path. The rename is text. The guard adds two conditions.

## 3. Why the back-feed is needed

The system specification, section 4.3, says corrections made in Desktop are the practice's decided truth, with no back-feed in Phase 1, and change log item 19 implemented that deliberately. Three pipeline features built afterwards break under that rule:

- **Auto-retry.** The pipeline re-extracts anything its database still marks `needs_review` whenever the code changes. A receipt you fixed in Desktop stays on that list and costs an OpenAI call every time.
- **Duplicate protection.** The pipeline decides whether it has seen a receipt by checking whether *it* filed it. It did not file the one you completed in Desktop.
- **Vendor learning.** Corrections made in Desktop never reach the pipeline's mappings.

The fix keeps the rule intact. Desktop still never writes `receipts.db`. It writes a note; the pipeline reads the note and updates its own database. Same pattern as the phone capture app: drop a file, let the pipeline pick it up.

**Item 19 has now been tested end to end**, on 28 July, which version 1 listed as an unmet prerequisite. It works: the form validations behave, the image and sidecar are written to `Clients\{Name}\Receipts\{tax year}\`, the books entry is correct, and Desktop removes the Review pair itself. So you are attaching this contract to a flow that has been proven once, not to an untested one.

## 4. The contract

### What the pipeline does with a note, so you know what you are feeding

Read this before the schema. It answers the questions that otherwise get guessed.

The pipeline consumes `Resolutions\*.json` at the start of every poll, before its retry pass, so a receipt you resolved is never re-extracted in the same cycle.

For a `filed` note it **does not re-file the image**. The file is already where Desktop put it. The pipeline records that path, writes a `manual_correction` extraction row, categorises, and sets its status to `ok`. There is no second copy. This was the single most important thing to get right on the pipeline side and it is tested by counting the files in the target folder before and after.

It **does not rewrite your sidecar.** Desktop's own sidecar stays as the record for a receipt Desktop filed. Two sidecar shapes will coexist in a client's Receipts folder, and that is accepted for now.

It **does not expect the Review pair to still exist.** Desktop deletes it, correctly, and the pipeline's cleanup finding nothing is a normal outcome rather than an error. `original_review_files` is matched against the pipeline's own database record of the filename, not against the disk, so naming files that no longer exist is fine.

It **never deletes a note.** Processed notes move to `Resolutions\processed\`, unusable ones to `Resolutions\failed\` with a `.error.txt` alongside. Desktop writes and forgets.

Applying the same note twice is a no-op, keyed on `resolved_at`.

### Location

`{practice root}\IntelliBooks\Resolutions\`

Create it if it does not exist. It already exists on Paul's machine and is empty. This is system territory per change log item 12, so it belongs under `IntelliBooks\`, not under `Clients\`.

Do not create `processed\` or `failed\`. The pipeline owns those.

### Filename

`{receipt_id}_{unix_ms}.json`

The timestamp means a second resolution for the same receipt never overwrites the first. Note that the pipeline sorts these by name, which orders correctly per receipt but not globally across receipts. That is intended and needs nothing from you.

### Schema

```json
{
  "schema": 1,
  "receipt_id": "c5a3fccd-6684-4bb9-b3fb-5023e86b6461",
  "client_code": "TEST",
  "action": "filed",
  "resolved_by": "desktop",
  "resolved_at": "2026-07-28T11:30:40.602Z",
  "values": {
    "supplier_name": "MARLOW TRADE SUPPLIES LTD",
    "invoice_date": "2026-07-21",
    "net_amount": 80,
    "vat_amount": 16,
    "gross_amount": 96,
    "currency": "GBP",
    "category_name": "Motor expenses"
  },
  "filed_path": "Clients\\Test\\Receipts\\2026-27\\2026-07-21_MARLOW-TRADE-SUPPLIES-LTD_96.00.png",
  "original_review_files": [
    "TEST_vat_mismatch.png",
    "TEST_vat_mismatch.png.review.json"
  ]
}
```

Field by field, and this is what the pipeline's parser actually enforces:

| Field | Rule |
|---|---|
| `schema` | Must be `1`. A `2` is rejected outright, so a future version cannot be silently misread. |
| `receipt_id` | Text, or `null`. Take it from the review sidecar's `extracted_values.receipt_id` or `pipeline_receipt_id`, which is the value the existing code already uses as the row id. If neither is present, still write the note with `null` and rely on `original_review_files`. |
| `client_code` | Required. The pipeline parses it but never uses it to resolve a path, because Desktop writes the client **code** into its sidecar's `client.name` field and the two applications do not agree on a client's name. |
| `action` | `"filed"` or `"discarded"`. Anything else is rejected. |
| `resolved_by` | `"desktop"`. Validated, then unused: the pipeline forces the actor to `desktop`. It exists so that if Desktop ever gains named users, this becomes the actor with no contract change. |
| `resolved_at` | **Required, and it is the idempotency key.** A note without one is refused. ISO 8601 with a `Z`, which is what `new Date().toISOString()` gives you. |
| `values` | Required for `filed`, absent for `discarded`. |
| `filed_path` | Required for `filed`, absent for `discarded`. Relative to the practice root, backslashes, matching the path actually written. **The pipeline checks the file exists on disk** and sends the note to `failed\` if it does not. |
| `original_review_files` | A list of strings. The pipeline skips the `.review.json` entry and matches the image name case-insensitively. |

Rules on the values:

- **Amounts are JSON numbers.** Strings are rejected, and so are booleans. Whole numbers arriving as `80` rather than `80.0` are fine and expected, because that is what `JSON.stringify` does.
- **`null` is accepted for an amount and means "no value".** This corrects version 1, which told you to omit the field rather than write `null`. Your own code at line 1787 already writes `net: isNaN(net) ? null : Math.abs(net)`, so version 1 was asking you to change working code for no reason. Leave it as it is.
- The pipeline **rounds amounts to two decimal places** on ingest. Send what you have.
- `supplier_name`, `invoice_date` and `gross_amount` are required for a `filed` note.
- `invoice_date` must be `YYYY-MM-DD` and a real calendar date. `14/07/2026` and `2026-02-30` are both rejected.
- `currency` is optional and defaults to `GBP`.
- `category_name` is the category **name** as shown in Desktop. Do not convert it to a nominal code; the pipeline does that, and cannot until the shared chart of accounts exists. **An empty string is fine and means no category**, which is the common case because Desktop does not require one before filing. The pipeline treats `""` as no category rather than looking it up.
- Unknown extra keys are ignored, so adding a field later will not break the consumer.

### Write timing and safety

Write the note **only after the filing or deletion has fully succeeded**, at the point the existing code removes the originals from Review. That is the moment the filing becomes irreversible. If filing fails, no note.

The books entry is a separate matter. `scheduleSave()` is debounced, so the note may be written before `books.json` hits disk. That is acceptable: the books are Desktop's own record and the item 21 auto-scan rebuilds them from the filed files. Do not try to synchronise the two.

Use the existing `createWritable` path, which commits on close, so the pipeline can never read a half-written file.

**If writing the note fails, do not roll back the filing and do not block the user.** Toast that the receipt was filed but the pipeline could not be notified, and log to the console. A missing note is a recoverable nuisance; a failed file operation is not.

### Manual check for Paul

File a Review item for TEST. Then confirm: a single `.json` appears in `IntelliBooks\Resolutions\`, its `receipt_id` matches the one in the review sidecar, `filed_path` matches where the image actually went, and the amounts are numbers rather than quoted strings. Then he starts the pipeline, waits one poll, and confirms the note has moved to `processed\` and the receipt reads `ok` in the database. That is test 41 and it is the moment this contract is either real or not.

## 5. Change 2: the backup bug

`exportPracticeBackup()` does this per client:

```js
const dir=await getDir(["Clients",safeName(c.name),"IntelliBooks"],false);
const r=await readJSON(dir,c.code+"-books.json");
if(r)all.books[c.code]=r.data;
```

That path was superseded by change log item 12, which moved books to `IntelliBooks\Books\`. No client folder has an `IntelliBooks` subfolder any more, so `getDir` throws, the `try` swallows it, every client is skipped, and the download contains `books:{}` while reporting success.

Use the same directory as `loadBooks()`:

```js
const dir=await getDir([SYS_DIR,"Books"],true);
```

Keep the legacy fallback if you think it earns its place, but the primary read must be the current location.

**Manual check.** Export a practice backup and confirm both TEST and TEST2 books appear in the JSON, with receipts and transactions in them, not empty objects.

## 6. Change 3: rename the button

The button at line 115, on the Bank Transactions tab, reads `Run Matching Analyser` and its `onclick` is `runAnalyser()`, which calls `applyRules(true)`. That categorises transactions from statement rules. It does no matching whatsoever. Receipt-to-transaction matching is `refreshMatches()`, which runs by itself and has no button.

The label actively misleads, and it matters more than cosmetics: pressing it before attaching a receipt is what decides whose category wins, because `applyRules()` fills `t.category` and `attachReceipt()` then only copies the receipt's category when the field is empty.

Rename it to **`Categorise from Rules`**. Fix the same wording in the tooltip at line 1324, which says rules are "applied by the Matching Analyser". Change no behaviour.

## 7. Change 4: guard category deletion properly

`delCategory()` at line 1997 refuses to delete a category when a transaction uses it:

```js
if(books.transactions.some(t=>t.category===c.name)){toast("In use by transactions. Recategorise them first.");return;}
```

It does not check **receipts**, and it does not check **statement rules**. So a category can be deleted while a rule still assigns it, and `applyRules()` will then keep writing a category that no longer exists onto new transactions.

Add both checks, with a message that says which kind of thing is using it, so the operator knows where to look. Note also that `addCategory()` compares names case-insensitively while this check is case-sensitive, so a reference differing only in case does not block deletion either; make the comparison consistent with `addCategory()`.

Paul's requirement, stated 2026-07-28: **a category must not be deletable while anything is linked to it.**

**Manual check.** Create a category, use it in a statement rule only, and confirm deletion is refused. Repeat with a receipt only. Confirm a genuinely unused category still deletes.

## 8. Section 8 is a question, not a change

Do not build anything for this. Give Paul the options and let him decide.

A category has no identifier: `addCategory()` pushes `{name, type, hmrc}`, and every reference to it anywhere is a copy of that string. There is no rename feature, which is the only reason nothing is broken today.

The live question is what happens at `postReceiptToCashbook()`, line 1659, which creates a transaction from a receipt and does `t.category = r.category || ""`. Because Desktop does not require a category before filing a receipt, the common case is a receipt with a blank category, which produces a **transaction** with a blank category. The transaction is the record the HMRC and P&L reports read. Its own toast already says "Review the category, then Post", so the design expects the operator to fix it, which is a prompt rather than a control.

Paul's framing, and I agree with it: receipts are documents and may reasonably have no category. **The gate belongs on the transaction, at the point it is posted.** So the question is whether a transaction should be allowed to reach a posted state with a blank category, and if not, whether the block is hard or a warning.

The same applies to `bulkCashbook()` at line 1534, which does the same thing for a selection.

While you are in there: `bulkCashbook()` at line 1534 and `postReceiptToCashbook()` at line 1666 both write `t.category = r.category || ""` with no guard. Both currently act on a transaction created a line earlier, so nothing is overwritten and it is harmless. But it is an unguarded write that would wipe an existing category to an empty string if either were ever pointed at an existing transaction. Worth a guard now while it costs nothing. Flag it, do not fix it, unless Paul says otherwise.

## 9. Constraints

- UK accountancy practice, GDPR and DPA apply. **Test with the TEST and TEST2 sample clients only.** Do not put real client data into Cowork.
- Single HTML file, no new dependencies, no build step.
- Match the existing style: same helpers, `getDir`, `readJSON`, `writeJSON`, `toast`, `safeName`, same error handling, same plain-English toast wording.
- Do not alter the review UI, the filing logic, the naming convention, or the sidecar Desktop already writes.

### Terminology, and hold to it even when it feels laboured

The two systems share almost every noun. Say **Receipt Capture** or **the pipeline** for the Python system, **IntelliBooks Desktop** or **Desktop** for this app, **the console** for the new Flask app, **the books** for `IntelliBooks\Books\{CODE}-books.json`, and **the database** for the pipeline's `receipts.db`. Never say "the app". Qualify shared nouns: "Desktop categories" versus "pipeline categorisation", "the Review folder" versus "the console queue".

## 10. What I want back

1. Confirm the approach or say plainly if you think the drop-folder contract is wrong and why. A shared status file and the pipeline detecting a vanished Review pair were both considered and rejected as less explicit. The pipeline half is built, so a change of mechanism now has a real cost, but a genuine objection is still worth hearing.
2. The four changes, one at a time, each with the changed code quoted back and a manual check for Paul.
3. Your answer on section 8, as options rather than a decision.
4. New entries in `Docs\IntelliBooks-Change-Log.md` following the existing convention, continuing from item 23.
5. **Anything where this brief and the code disagree.** Say it rather than working around it. The pipeline half was built from the same contract by a session that could not see yours, and a silent divergence here is the one failure mode nobody catches until it is in the books.

**Do not edit `IntelliBooks-System-Specification.md` or `IntelliBooks-System-Overview.md`.** Both need corrections spanning the pipeline too and are being updated separately. Flag, do not fix.

## 11. Reference

- Pipeline side, built and tested: `C:\LastingImpact\receipt_capture\`, branch `feat/console-phase0`, tip `f453a9c`.
- The contract in full: `C:\LastingImpact\receipt_capture\2026-07-25_CONSOLE_DESIGN.md`, section 12, including the 2026-07-27 and 2026-07-28 amendments. Section 4.3 is the resolution flow, 3.7 the sidecar category, 14 the category conflict rule, 13 the chart of accounts.
- Existing conventions: `Docs\IntelliBooks-Change-Log.md`, items 12, 13, 19 and 21 are the relevant ones.
