# Intellitax Practice Console — Design

**Date:** 2026-07-25
**Version:** 1.4, amended 2026-07-28
**Status:** Design agreed with Paul. Phase 0 in progress on `feat/console-phase0`.
**Supersedes:** `2026-07-25_DASHBOARD_DESIGN.md` (earlier draft in this repo, deleted).

## Amendment record

Superseded wording is kept visible with its reason, so the decision trail survives. Same convention as `IntelliBooks-System-Specification.md`.

### v1.1, 2026-07-26

| # | Section | Change | Why |
|---|---|---|---|
| 1 | 16, step 0 | The merge into `main` is cancelled. Build continues on `feat/console-phase0`, cut from `fix/imap-message-id-dedup`. | `main` turned out to be 42 commits behind that branch and diverged by one, not six behind as believed. A branch cut from `main` had left the working tree missing 13 files of the built system. See the note in section 16. |
| 2 | 16, steps 1, 2, 7 | Recorded as built, with commit hashes. | Phase 0 step 1 landed on 2026-07-26. Step 7's `BaseExtractor.name` came early because the step 1 fix needs it. |
| 3 | 3.1 | Records the missing-file status decision and the branch B implementation deviation. | Both were live questions during implementation and the answers belong in the spec, not only in a chat. |
| 4 | 4.3 | The claim that a swallowed traceback reaches `data/run.log` is corrected. | Nothing wrote that file at all. It now has a handler, but only on the pipeline entry point. |
| 5 | 6.5, new | Records the logging requirement, the Windows rotation constraint, the dead `config.RECEIPTS_LOG` and the import-time `config.RUNS_LOG`. | Three of the four callers of the resolution service would not write the log the design relies on, and two processes cannot share a rotating handler on Windows. |
| 6 | 15 | Test count 17 to 27. Adds the log-redirection rule for tests. | The suite grew with phase 0 step 1. Tests were writing synthetic rows into the live operational logs, which the console reads. |
| 7 | 17.4 | Two new open questions: how the CLI expresses "clear this field", and whether `add_validation_note()` should stop mutating extraction rows in place. | Both surfaced during implementation. Neither blocks phase 0. |

### v1.2, 2026-07-27

| # | Section | Change | Why |
|---|---|---|---|
| 8 | 4.3 step 6, 15 test 16 | **Decided.** `add_validation_note()` is retired. A `still_invalid` outcome appends a new extraction row carrying the notes. | Paul's decision, 2026-07-27. The method runs `UPDATE extractions SET validation_notes` on an existing row, which `CLAUDE.md` forbids. A resolution attempt that failed validation is an event worth a row, not a footnote appended to the row it disagrees with. Phase 0 step 1 already took this route for the missing-file branch. |
| 9 | 16, step 3 | Recorded as built, with commit hashes. | Landed 2026-07-27. |
| 10 | 4.2 | Three unstated points settled: the GL fields on `Corrections` are not read from `raw`, `receipt_time` has no format rule, and an empty string on the CLI flags path now clears a field. | All three were undefined, and the console form at step 16 builds against this contract. |
| 11 | 3.5, 3.6, 3.10 | Implementation detail for step 4: where the cleanup helper lives, how to locate the pair safely, which statuses `review_count` counts, and 3.10 folded into the same step. | Reconstructing the review filename is unsafe because `_unique_path()` may have appended a suffix. Worth stating before someone deletes the wrong file. |
| 12 | 17.4 | The `export_bookkeeping.py` question is answered, and two defects in it recorded. | It reads no category at all, so 11.2 cannot reach it. The question changes shape rather than closing. |

### v1.3, 2026-07-27

| # | Section | Change | Why |
|---|---|---|---|
| 13 | 3.5 | The two matching rules in amendment 11 contradicted each other on the same input. Corrected, with the ordering that resolves them. | One rule said fall back to `original_filename` for sidecars with no `receipt_id`; the other said ignore sidecars with no `receipt_id`. A different implementer would reasonably have skipped them outright and silently lost the fallback. Flagged by the implementation session, and it was a drafting error here. |
| 14 | 3.6 | Clarifies that `review_count` feeds `pipeline-status.json`, which IntelliBooks Desktop reads, and is not the console queue. | Amendment 11 left it open to read as though it defined what an operator sees. The queue is 8.2, which already includes `retry_exhausted`. |
| 15 | 3.7 | Records what the `category` key actually holds across the 32 filed sidecars on disk, and the four call sites the fix has to cover. | The section describes one failure mode. There are four kinds of value in that field in live data, and a fix to the writer changes nothing already filed. |
| 16 | 16, step 4 | Recorded as built, with commit hashes. | Landed 2026-07-27. |
| 17 | 15 | Test count 27 to 64. | Steps 3 and 4 added 37 tests. |
| 18 | 17.4, 3.7 | Asked and closed the same day: no backfill. Every filed receipt and sidecar on disk is test data. | Paul confirmed on 2026-07-27. Nothing to preserve, so 3.7's table is evidence of how the format drifted rather than a data problem. |
| 19 | Dates | v1.2's stamps corrected from 26 to 27 July. | Steps 3 and 4 were committed on 27 July. v1.1's 26 July stamps are correct and unchanged. |
| 20 | 12.4, 17.4 | Records that IntelliBooks Desktop writes its own sidecar when it files, in a different shape, deletes the Review pair itself, and that its reader already tolerates the new format. New question on which shape wins. | Read from `IntelliBooks-Desktop-v3.html` lines 1141 to 1158 and 1760 to 1803. Recorded nowhere, and 12.4 asserts the reverse direction needs nothing. |
| 21 | 3.7 | Two gaps the implementation exposed: what the review path writes, and what happens when a code has no name. | Both are consequences of carrying two keys where there was one, and neither was described. |
| 22 | 16, step 5 | Recorded as built, with commit hashes. | Landed 2026-07-27. |
| 23 | 10.2, 16 step 6 | Line boundaries corrected from "98-214" to the three actual ranges. Step 6 recorded as built. Seven defects found during the move recorded, none fixed. | The stated range began eleven lines early, inside the JSON parse. The seven findings came from reading code that had not been read closely since it was written, and they would otherwise live only in a chat log. |
| 24 | 17.4 | New decision: whether to fix the two date-handling defects, add logging to the moved handlers, and stop the two test files leaking `PREFER_DAYFIRST`. Decided the same day: yes, as step 6b. | Findings 1, 2, 6 and 7 in 10.2. All small, all in one area, and two of them mean an agreed fix silently does not apply. |
| 25 | 3.11 new, 8.4, 16 step 6c | `extractions.details` is never written, so every automatic amendment the pipeline makes goes unrecorded. New phase 0 item. | Found while verifying step 6b. The column exists with a migration, and `save_extraction()` has no parameter for it. `apply_vat_inclusive_swap()` rewrites two financial figures with no record that it did. Two rows from 19 July prove the write once worked, so it is a regression. |
| 26 | 16, step 6b | Recorded as built, with commit hashes. | Landed 2026-07-27. |
| 27 | 3.12 new, 16 step 7b | Two extraction writes on the embedded-image path omit `pipeline_version`, so their receipts are retried once for nothing. New phase 0 item. | Flagged by the implementation session for one call site; verification found two. Same family as 3.1, one wasted retry rather than an endless loop. |
| 28 | 5, 16 | `resolution_events` moves from step 11 to step 8. | 4.3 step 14 has the resolution service write to a table the build order created three steps later. The service could not have been built as specified. |
| 29 | 3.11, 10.3, 16 steps 6c and 7 | Recorded as built. `config.EXTRACTION_ENGINE` recorded as the engine's source of truth, and that the phase 2 `settings` table must replace that read rather than join it. The sidecar asymmetry `details` creates is stated deliberately. | Two sources of truth for the running engine is the bug 10.1 exists to prevent, and an undocumented asymmetry gets reported as a defect by whoever meets it first. |
| 30 | 4.3 new step 1a, 4.2 outcomes | `resolve_receipt()` must refuse a receipt that is already filed, returning a new `already_filed` outcome. | Nothing in the fifteen steps inspected `filed_path`, so the service would re-file an `ok` receipt and leave a second copy on disk. That is the double-filing the whole design exists to prevent. Found by the implementation session. |
| 31 | 4.3 step 6 | On `still_invalid`, preserve a `possible_duplicate` status and let the others follow `validate()`. 8.4's duplicate comparison keys on `duplicate_of`, not `status`. | Overwriting it would hide the duplicate comparison and make the receipt auto-retry eligible after a human had already looked at it. |
| 32 | 4.3 steps 9 and 13 | The GL override trigger and the source of `vendor_code` specified. | Both were left to the implementer, and step 13 could not be built without choosing. |
| 33 | 5.1 | `reason TEXT` added. | `discard_receipt()` takes a reason the table had nowhere to store. |
| 34 | 4.2 | `ResolutionView.extraction` widened to `dict | None`. | A receipt can exist with no extraction, and the read side should not decide policy. |
| 35 | 16, steps 7b and 8 | Recorded as built, with commit hashes. | Landed 2026-07-27. |
| 36 | 4.3 step 1a, 5 | `receipts.filed_at` added. | 4.3's `already_filed` message promises a date the schema cannot supply, and 8.3 already lists a "filed" column. `mark_receipt_filed()` is the single writer, so it costs one line. |
| 37 | 4.4 | `confirm_duplicated_action()` must actually be called. `actor` on a CLI resolution comes from `getpass.getuser()` with a `--actor` override. The "~100 lines" target is corrected to what 4.4's own requirements allow. | The function has never been called, by the old CLI or the new one, so a `possible_duplicate` receipt goes straight to the correction prompts and is filed without anyone being asked. That is the one place the CLI can still file a duplicate silently. |
| 38 | 4.4, 6.5 | The CLI reconfigures stdout to UTF-8. | `✓` and `✗` raised `UnicodeEncodeError` on a cp1252 console **after** filing, so the work succeeded and the operator got a traceback. Pre-existing, present at `60df040`. |
| 39 | 16, steps 8b and 9 | Recorded as built, with commit hashes. | Landed 2026-07-27. |
| 40 | 3.13 new, 16 step 9c | A folder-intake receipt that is not `ok` leaves its original in the inbox and is re-extracted every poll. New phase 0 item, fix decided the same day. | Found live on 2026-07-28 while creating a Review item, caught before the second pass. The folder-intake twin of 3.1. |
| 41 | 22 | The Claude Code permissions setup is recorded in `CLAUDE.md` rather than the operator guide. | Allow rules in `.claude/settings.json` are ignored unless the workspace is trusted; the local file's are not. Three attempts to find, worth writing down. |
| 42 | 12.4, 17.4 | Change log item 19 confirmed working live, with five details from the real sidecar that reading the code did not show. The two-decimal-places rule. The blank-category question re-framed after Paul corrected the accounting. | First live test since 19 July. Receipts do not map to HMRC boxes or the P&L; transactions do. The risk of a blank category sits at `postReceiptToCashbook()`, not at filing. |
| 43 | 13, 14, 17.5 new | Category identity: no rename feature exists and a category has no identifier, so codes are a prerequisite for renaming rather than an improvement to it. The delete guard misses receipts and rules. No migration of existing references is needed. New 17.5 records what the clean-slate reset must and must not touch. | Paul's three requirements, 2026-07-28. All books data is test data and will be cleared, which removes the migration but makes the reset itself worth planning: the vendor mappings are real practice knowledge, and clearing `processed_attachments` while anything sits in `INBOX` would re-extract it at one OpenAI call each. |

### v1.4, 2026-07-28

Rows 40 to 43 above are also 28 July work, recorded under the v1.3 table before this section existed. Left where they are rather than moved, so no row number changes meaning.

| # | Section | Change | Why |
|---|---|---|---|
| 44 | 12.4 detail 3 | **The stated mechanism is corrected.** Superseded wording: "Desktop wrote the code into the name". It does not. Desktop writes `client:{code:c.code,name:c.name}`, the real name. The two registries hold **different names for the same client**: `IntelliBooks-Practice.json` has `{"name":"TEST","code":"TEST"}`, `clients.csv` has `Test`. Adds the consequence for the cloud version. | I inferred the mechanism from a filed sidecar reading `{"code":"TEST","name":"TEST"}` and was wrong about the cause. Flagged by the IntelliBooks session, confirmed against both registry files. The conclusion survives and gets stronger: never resolve a path from the note's `client.name`, because the two tools disagree on it. And a new consequence, which is why this is more than a footnote: Desktop writes `filed_path` as `Clients\TEST\...` from `safeName(c.name)` while the pipeline files the same client to `Clients\Test\`. `resolve_practice_path()` then calls `target.exists()`, which passes on Windows because NTFS is case-insensitive. **Test 41 therefore passes for the wrong reason**, and on S3 or Linux those are two folders. |
| 45 | 12.2 | Filename convention amended to what Desktop writes. Superseded wording: "Filename `{receipt_id}_{unix_ms}.json`". | Desktop writes the receipt id when the sidecar carried one, and otherwise the review image name with its extension stripped and any character outside `[A-Za-z0-9._-]` replaced by `-`. That is a fair reading of a section that permits a null `receipt_id`, and the pipeline only sorts on the name, so nothing breaks. Recorded because spec and shipped code disagreed, which is the drift this document exists to catch. |
| 46 | 12.2 | Records that `Resolutions\` sits inside OneDrive, and that this is a same-machine assumption rather than a property of the design. | Raised by the IntelliBooks session and worth keeping. Fine while Desktop and the pipeline run on one machine. On two, sync latency and conflict copies (`file-DESKTOP-ABC.json`) become the pipeline's problem, and `glob("*.json")` would pick them up. |
| 47 | 12.4, 17.4 | **Decided.** Leave both sidecar shapes on disk and make every reader tolerant, keyed on the discriminator: `corrected_by` means Desktop wrote it, `capture_date` means the pipeline did. | Paul's decision, 2026-07-28. Closes the question row 20 opened and 12.4 parked at step 10. Rewriting would be a write into a folder Desktop has just written to, with a new failure mode, for the benefit of no reader that exists yet. The discriminator makes tolerance a small testable rule rather than an open-ended one. |
| 48 | 12.3 step 2, 17.4 | The null-id filename fallback can miss. Flagged, not fixed. | Desktop sends the on-disk Review image name in `original_review_files`, and `file_review()` names that image through `_unique_path()`, which may have appended `-2`. `receipts.filename` holds the unsuffixed original, so the match fails and the note lands in `failed\`. Only bites when the id is absent **and** there was a name collision, and failing audibly into `failed\` is the designed behaviour for an unmatchable note. |
| 49 | 17.4 | Two flags from verifying the Desktop half, and one fix. | `write_review_file()` has no caller in `app.py` or `worker/`, and the `{stem}.review.json` name it writes is invisible to Desktop's `scanReview()`, which derives the image name by stripping `.review.json` and skips the item when no such file exists. Separately, `clients.csv` gave `Client_004` to both `Test` and `She Run's It! Ldn Ltd`, so anything keyed on `client_id` conflated two clients. **Fixed 2026-07-28** ahead of test 41 on Paul's instruction: `SHERUNSIT` becomes `Client_005`, which touched no existing row because all `Client_004` receipts belong to `TEST`. |
| 50 | 15 test 41, 16 | Test 41 covers **both** note actions, filed and discarded, and the `clients.csv` fix comes before it. | Paul's decisions, 2026-07-28. The discard branch has never run at all, and it is the cheaper half to get wrong. Two Review items means two OpenAI calls, accepted deliberately. Fixing the registry before generating new rows against it rather than after. |

| 51 | 12.2, 15 test 41 | **Terminology.** The note's `action` value is `discarded`, but **nothing in IntelliBooks Desktop says "discard".** The button is red and says **Delete**, on the Review row and in the Edit window, and it raises a browser confirm reading "Delete this receipt permanently from `Clients\{name}\Review\`? This cannot be undone." | Written after test-41 instructions phrased in the code's vocabulary confused Paul, which was my error and the exact failure the terminology rule in the handover exists to prevent. Anyone writing instructions for an operator names the button on screen; `discarded` is the value in the note and belongs in code and in this document, not in a walkthrough. Same class of problem as "the app": one thing, two names, and only one of them is visible to the person doing the work. |

| 52 | 17.4, and a change for the IntelliBooks session | **Decided.** A receipt whose own net, VAT and gross do not reconcile must produce a **warning at the point the transaction is posted**, in Desktop. Not a block, and nothing is carried into the books entry. | Paul's decision, 2026-07-29, taken after reviewing the branch test 41 did not exercise. What prompted it: a transaction has `amount` and `vat` and **no net field at all**, so net is always derived as the difference. Post a receipt reading net 21.50, VAT 4.30, gross 27.00 and the transaction is 27.00 with VAT 4.30, implied net 22.70. The receipt's stated net is dropped and the discrepancy resolves itself silently in favour of gross and VAT. That treatment is defensible, since gross is what left the bank and net is derived, but it was reached by omission rather than by decision. And the pipeline's own record of the disagreement, the `filed by decision in Desktop despite` line, lives in `extractions.validation_notes`, which Desktop never reads, so the caveat never reaches the person posting. The warning must use the pipeline's test exactly, `abs(round(net + vat, 2) - round(gross, 2)) > 0.02` and **only when all three are present**, so the two tools cannot disagree about the same receipt. `parseSidecar()` already carries `net` and `vat` through, so this works for auto-loaded receipts too. **Mechanism, decided the same day:** a confirm box on the single-receipt path, which the operator must acknowledge and may proceed through, and a **count** on the bulk path, because `bulkCashbook()` cannot ask per receipt and a toast that vanishes in 4.5 seconds is too weak for a figure that will not be questioned again. |
| 53 | 17.4, 13 | The blank-category-at-posting question was put alongside amendment 52 and **deliberately left open.** | Paul's decision, 2026-07-29. Recorded so nobody later reads it as an oversight, and so nobody bundles it into the VAT change on the assumption it was forgotten. The two questions sit at the same two functions, `postReceiptToCashbook()` and `bulkCashbook()`, and doing them together would have cost one visit rather than two, which is why it was asked now. Left open anyway: the existing toast already says "Review the category, then Post", so a prompt of a kind exists, and the VAT change is worth keeping small. When it is taken, it is one guard in the same place. |
| 54 | 16 step 10c, 17.5, 15 test 43 | **10c moves again: after the four IntelliBooks Desktop changes A to D, not immediately after test 41.** The ordering constraint it was placed under is unchanged, still before any console work. Test 43 moves to after the reset. | Paul's decision, 2026-07-29. Two reasons, and the second is the one that decides it. The Desktop app is about to be modified by the session briefed in `PROMPT_intellibooks_desktop_changes.md`, and resetting either side of a code change is two variables at once, which is the same reasoning that kept 10c out of the way of step 10. More concretely, **change D cannot be tested after the reset**: test 44 posts a receipt whose figures do not reconcile from the books to the cashbook, and the reset clears the books. Build D, test it against the test data that exists now, then clear down. Test 43 goes the other way and moves to **after** the reset, because 17.5 already requires a fresh fixture and one clean cycle to be confirmed post-reset, so a single Review item and a single OpenAI call serves both purposes instead of two. |
| 55 | 13A new, 16 steps 10a and 10b, 17.5 | **Decided: the client folder hierarchy is namespaced.** Everything this system owns moves under `Clients\{name}\_IntelliBooks\`, with `_Receipts\{tax year}\`, `_Review\`, `_Handover Pack\` and `_HMRC Summaries\` beneath it. The tax year folder keeps its bare `2026-27` form with **no** leading underscore. | Paul's decisions, 2026-07-29. A client folder is a mixture: `Clients\Paul Keating\` already holds `Document Requests`, `Misc` and eight loose PDFs from another tool alongside the two this system writes, and as engagement letters, correspondence and returns accumulate there is nothing to tell an operator which folders a program writes into. The leading underscore marks them as managed and sorts them to the top. `HMRC Summaries` replaces the proposed `HMRC_Mapping` because the folder holds period summary CSVs, one per period, and the mapping itself lives on `books.categories[].hmrc` and never goes there; naming it for the mapping would be the same fault as `Run Matching Analyser`. **The tax year exception is not a style preference.** Desktop's `listReceiptYears()` tests folder names against `/^\d{4}-\d{2}$/`, so `_2026-27` matches nothing, the year dropdown comes back empty and no filed receipt loads for any year. `determine_tax_year()` produces `2026-27` and both tools already agree on it. |
| 56 | 13A new, 8.1 | **Locking the managed folders was asked and answered: it is not achievable on Windows with OneDrive, and detection replaces it.** | Paul asked on 2026-07-29 whether the folders could be writable only by the app. Three reasons no. NTFS permissions restrict by **user account**, not application, and both tools run as Paul, so any permission that admits them admits Explorer. Controlled Folder Access is genuinely per-application but its granularity collapses here: the pipeline is `python.exe`, so allowing it allows every Python script; Desktop is a browser using the File System Access API, so allowing it allows any site granted folder access; and `explorer.exe` needs allowing or ordinary file management breaks. And restrictive ACLs inside a OneDrive sync root are unwise: synced files do not reliably inherit the parent's permissions and OneDrive needs full access as the user to reconcile. **Prevention arrives free on AWS**, where an IAM policy can give write access to the app's role and nothing else, so no Windows workaround should be built. Detection is also strictly better than a lock would have been, because a lock stops only one of the ways these folders acquire files nobody intended: it would not stop a OneDrive conflict copy, and it would not have caught the 23 ghost receipts found on 2026-07-29. |
| 57 | 13A.4, and a change for the IntelliBooks session | **A live defect in Desktop: every auto-scanned filed receipt is added to the books twice.** `ingestReceiptFiles()` keys images with the extension stripped and then looks them up with it present, so a sidecar never finds its image. | Found 2026-07-29 while answering what happens to a manually added receipt, and confirmed across all four books files rather than inferred. **23 ghosts in total**, ids like `img_2026-07-24_PENNINE-CAFE-&-BAKERY_27.00`, gross 0, note "Image only. Edit details.": 11 of 23 receipts in `TEST`, 8 of 13 in `TEST2`, 4 of 13 in `PAUL`. **And the fingerprint that proves the mechanism rather than merely fitting it: in `TEST2` and `PAUL` the number of receipts carrying a thumbnail is exactly the number of ghosts**, 8 and 8, 4 and 4. The ghosts are the only receipts with images, because a sidecar-loaded receipt never finds its image. `TEST` has 9 further images because a receipt filed through `fileReviewReceipt()` is pushed to the books with the image it just read, without going through the scan at all, so the two code paths are visibly different in the data. Three consequences. The real receipt gets no thumbnail because the lookup returns null; `delete images[base]` removes nothing so the image falls through to the orphan loop and is pushed a second time; and the books file carries every image twice as base64, which is why `TEST-books.json` is 6.1 MB. Contained rather than harmless: `postReceiptToCashbook()` refuses a gross of 0, so a ghost cannot reach the cashbook until a human types an amount into it. Ordered ahead of the button rename and the delete guard because it is affecting books data while those are not. All affected data is test data that 10c clears, so no cleanup is needed if the fix lands first. **Built and verified 2026-07-29, with two corrections to the fix I specified, both found by the implementation session and both material.** First, the image must be claimed **before** the `isStatement` and already-in-books `continue` statements, not after them where the original code put it. A receipt already in the books leaves its image unclaimed and the image drops into the loose-image loop, so the twin still appears. That is every receipt filed through Review, because `fileReviewReceipt()` pushes to the books itself and the scan then hits the dedup `continue`. My specified fix would have passed a code review and failed its own manual check. It also explains the thumbnail arithmetic: a review-filed receipt gets a real entry with an image from the filing path **and** a ghost from the scan, which is why `TEST` has 20 thumbnails against 11 ghosts. Second, the loose-image loop must take its stem from `f.name` rather than the new lowercased lookup key, or `img_` ids gain a file extension, the dedup check misses, and every existing duplicate is added a third time. **And one thing I asserted that was not true:** I reported `if(imf&&/image/.test(imf.type||"x")!==false)` as always true when `imf` is truthy. It is not. `.test()` returns a boolean and `!== false` on a boolean is the identity, so the expression is exactly `imf && /image/.test(...)`, and a PDF was already skipped. Redundant, not a defect, and the session checked rather than accepting it. |
| 58 | A change for the IntelliBooks session | **A receipt with no amount must be visible at a glance in the Desktop receipts list**, as a red pill reading "No amount" beside the supplier, keyed on `rGross(r)<=0`. | Paul asked on 2026-07-29 for the "Image only. Edit details." note to be a different colour. The note is the wrong thing to style: it renders as `<div class="muted small">`, deliberately dimmed, so the request means fighting the stylesheet, and it is a string written in one branch of one loop. The row already has a pill mechanism at lines 42 to 47, with a red `pill review` shown when `r.validation` is set and not `ok`; a loose image has empty validation and so gets nothing. A pill keyed on the amount is better on three counts: it survives the note wording changing, it sits in a column so a long list stays scannable, and it catches **every** receipt with no amount rather than only loose images, including one whose extraction found no gross and one an operator half-edited. Those cannot be posted either, since `postReceiptToCashbook()` refuses a gross of 0, and today they look fine. Related and flagged not fixed: the amber "To Cashbook" button is offered on rows the same function will refuse. |
| 59 | 57 | **Decided: the change E fix is forward-only and stays that way.** A receipt already in the books is skipped by the dedup `continue`, so it never acquires the thumbnail it should have had. 17 receipts are in that state, 12 in `PAUL` and 5 in `TEST2`. **Note the difference between a file count and a screen count**, which caught me out on 2026-07-29: the receipts list is filtered by the selected tax year, so `TEST2` shows **four** on 2026-27 and the fifth, a Canva receipt dated 2023-07-07, only appears on 2023-24. Any expectation quoted to an operator has to be the year-filtered number. No retrospective update will be built. | Flagged by the implementation session on 2026-07-29 as needing a decision, and the decision is to leave it. Three reasons. **The condition cannot recur after the reset**: a receipt filed through Desktop is pushed into the books with its image already in hand, and a receipt filed by the pipeline is loaded by the scan, which now pairs correctly on first sight. The 17 are historical artefacts of the defect rather than an ongoing gap. **The reset clears them anyway**, and delete-and-rescan repairs any one of them in the meantime, which is how the fix was verified. And **an "update the entry if it has no image" rule would fire on every scan for every PDF-backed receipt**, which correctly has no thumbnail and never will, so the rule would have to distinguish "missing" from "not applicable" for no benefit. Worth knowing before anyone concludes the fix has not worked on a client they have not touched: `TEST2` will show five thumbnail-less receipts indefinitely and that is expected. |
| 60 | A note for the IntelliBooks session | `runAnalyser()` keeps its name behind a button now labelled "Categorise from Rules". Left deliberately. | Flagged rather than fixed on 2026-07-29, correctly. Renaming the function means editing the `onclick` string too, which is behaviour-adjacent for no user-visible gain, and the name is not on screen. The mild irony is noted: a misleading name is what change B existed to fix. The difference is that a label lies to an operator and a function name only misleads a reader. Fold the rename in whenever someone is next editing that region for another reason; do not open the file for it. |
| 61 | 17.4, a question for Paul | **Changing one transaction's category from its row dropdown silently creates or overwrites a statement rule. The bulk path asks first; the single-row path does not.** | Found by Paul on 2026-07-29 while testing change B, and confirmed in the source. The row dropdown calls `setCategory(id, cat, true)`, and with `learn` true it derives a key from the description and runs `if(ex) ex.category=cat; else books.rules.push({pattern:key,category:cat})`. No modal, no toast, no confirmation. `bulkCategorise()` does the same job and behaves quite differently: it builds `pendingRules`, opens "Learn rules from this?", lets the operator edit each pattern or untick it, and shows a `pill review` reading "updates rule (was X)" precisely when an existing rule would change. So the two paths to the same outcome have opposite safety characteristics, and the unguarded one is the one used constantly. **Learning itself is intended**, per change log item 2, so this is not a defect report. The sharp edge is the silent **overwrite**: correcting a single transaction can reverse a rule set deliberately earlier and change how every future transaction from that supplier is categorised, with nothing on screen to say so. Note the contrast with 11.3 on the pipeline side, which forbids automatic learning outright because one correction against a misread supplier name poisons the mapping table and the engine then applies the wrong code confidently. Desktop is a different system with a human at the keyboard, so the same rule need not apply, but the asymmetry between its own two paths is hard to defend. ~~**Paul's decision:** leave it, warn on overwrite only, or route the row dropdown through the same preview.~~ **Decided 2026-07-29: warn on overwrite only**, built as change G. Creating a rule from a first-time categorisation is the intended behaviour and asking would be noise; silently reversing a rule set deliberately is the only part that can cost anything. The warning names the old category and the new one, because "a rule changed" without saying which way is not actionable. |
| 62 | 17.4, a question for Paul | **Two statement rules can exist for one supplier with no visible relationship, and the amount-conditioned one silently wins.** | Flagged by me at amendment 61 and returned in concrete form by the implementation session on 2026-07-29, confirmed against `bestRuleFor()`: `const pool=conditioned.length?conditioned:cands` means an amount-conditioned rule beats the pattern-only rule for any amount satisfying its condition, and among the pool the longest pattern wins. Two consequences, both of which will be reported as "the app ignored me" rather than as a rule problem. **First**, where an amount rule already exists for a supplier, a category set from the row dropdown updates the pattern-only rule, the change G toast confirms a rule changed, and future transactions at that amount are still categorised the old way. The operator has been told the opposite of what happens. **Second**, where *only* an amount rule exists, the dropdown creates a pattern-only rule that can never fire for those amounts. Silent creation is by design, per amendment 61, but this particular rule is born shadowed. Neither is a defect in change G and neither is in its scope. The underlying question is whether two rules for one supplier should be visible as related in the rules table, and whether the narrower one winning should be stated somewhere. Recorded in change log item 28. **Decided 2026-07-29: change H, the toast names the other rules. The rules table is deferred with a self-measuring trigger.** Change H extends `setCategory()` so that on **both** the create and the update path it reports any other rule sharing the pattern, which collapses both consequences into one condition and one sentence. **Corrected in the same conversation:** I argued the table work could wait partly because no pattern currently has both kinds of rule. Paul rejected that reasoning and was right, since six rules across a handful of test transactions says nothing about the rate in a real practice with thousands. The deferral survives on grounds that do not depend on frequency: the reset clears every rule, so nothing built now would run against real data; the toast catches the operator who is **not** looking, which a table only helps someone who is; and the console work from step 12 introduces GL codes and may change how rules are presented, so a table redesign now risks being done twice. **The trigger is change H itself.** The first time that toast mentions an amount rule, the situation is live and the table work is due. I considered adding it as a reconciliation finding instead and rejected that: finding 8 reads only the filenames in `IntelliBooks\Books\`, whereas counting rules means the pipeline parsing the internal shape of Desktop's books, which is a coupling worth avoiding for a statistic. |
| 63 | A correction to change C | **Adding or deleting a category never refreshes the statement rules table, so its "Categorise as" dropdown is stale in both directions.** | Found by Paul on 2026-07-29 running change C's own manual check, which could not be completed because a newly added category was not offered in the rules dropdown. Confirmed in the source. `addCategory()` ends `scheduleSave();renderCats();renderBank();` and never calls `renderRules()`; `delCategory()`, including the version just written for change C, ends identically. So a new category cannot be pointed at by a rule until something else redraws that table, and **a deleted category carries on being offered there**, which is the more serious direction because selecting it writes a rule referencing a category that no longer exists, which is precisely what change C exists to prevent. The receipts dropdown appears to work only because the Edit modal is rebuilt from `books.categories` each time it opens; the bank dropdowns work because `renderBank()` is called. `renderAll()` already exists at line 2324 and calls all seven renderers. **This is a pre-existing defect in `addCategory()` that change C inherited by copying its ending**, and it means change C is not complete: its guard is right and its reporting is right, but the table it guards can still offer a deleted name. Notable as a process point too: it was found by an operator following a manual check, not by reading the code, and neither the implementation session nor I spotted it while looking straight at both functions. |
| 64 | 16, and the IntelliBooks brief | **Desktop change D is deferred past the handover to another account. H and F are not.** The boundary is: A, B, C, E, G, H, F built and tested; D, 10a, 10b, 10c specified and not started. | Paul's decision, 2026-07-29, on my recommendation. The asymmetry that decides it: **H fixes something introduced the same day.** Change G's toast can report that a rule changed when an amount rule means it has not, so handing it over unfixed means handing over a message that states something false. **D addresses a risk that is not new** and has existed since the app was written, so deferring it makes nothing worse. D is also the only change that adds a new branch and needs wording agreed before Paul sees it, which makes it the one most likely to acquire a defect if rushed to a deadline. F goes with H because it is one line and fully specified, so finishing it removes an item from the handover rather than adding one. "Specified and not started" is a cleaner thing to inherit than "built today, half tested". D's ordering constraint is untouched: it must be built and tested before 10c, per amendment 54. |

Grounded in a direct read of `app.py`, `resolve_receipt.py`, `worker/database/repository.py`, `worker/database/schema.py`, `worker/extraction_pipeline.py`, `worker/validation/rules.py`, `worker/extraction/base.py`, `worker/extraction/openai_vision.py`, `config.py`, plus `IntelliBooks-Desktop-v3.html` and its `Docs\` folder, at commit on branch `fix/imap-message-id-dedup`.

## How to use this document

A build spec, not a discussion. "Must" means the decision was deliberate; check with Paul before reversing it.

Read `CLAUDE.md` first. Everything here is subject to its rules: no data loss, append-only extractions, no hardcoded firm or client IDs, commit after each logical unit.

**Do not start at section 8.** Sections 3 and 4 are prerequisites and matter more than the console does.

---

## 1. What this is

A local, authenticated web console for practice operations, run alongside the existing pipeline on Paul's machine.

**Module 1, Receipts.** Built now. System status, a queue of receipts needing attention, resolve-and-file, a browse and search view, intake problems, OpenAI spend.

**Module 2, Chart of accounts.** Deferred. Specified in section 13 with its schema reserved so it drops in without reworking module 1.

It is a **sixth component** in the system described by `IntelliBooks-System-Specification.md`, alongside the Capture App, Upload Function, Receipt Pipeline, IntelliBooks Desktop and OneDrive. That specification needs updating accordingly; see section 17.

### 1.1 What it does not do

It does not replace IntelliBooks Desktop, and it does not remove anything from it. Desktop keeps bank transactions, receipt-to-transaction matching, cashbook posting, statement rules, VAT, P&L and HMRC reporting. It also keeps its review-and-file flow (change log item 19), which stays fully working.

Both tools can resolve a receipt. Safety comes from the resolution back-feed contract in section 12, not from removing a capability.

---

## 2. Decisions taken

| Question | Decision | Rationale |
|---|---|---|
| Shape | One app, two modules. Receipts now, chart of accounts later. | Both need the same auth, DB access, client list and conventions. Two separate local web apps would drift. |
| Hosting | Localhost, `127.0.0.1`, built so remote is a config change. | Paul operates it alone initially; a remote admin may be needed at short notice. Documented remote path is Tailscale or Cloudflare Tunnel, never port forwarding. |
| Auth | Required from day one. Session cookie, argon2, roles `admin` and `operator`. | Real client financial data, and every write needs an actor. Retrofitting attribution into an append-only trail is impossible. |
| Data access | One process, server-rendered HTML, importing `Repository` and the resolution service in-process. No JSON API. | One consumer, one machine. Domain layer stays free of web imports so a cloud API can wrap it later unchanged. |
| Framework | Flask plus Jinja2, no JS framework. | Codebase is entirely synchronous. FastAPI's async model adds risk for no gain. |
| Database | One database. CoA tables live in `receipts.db` with a `coa_` prefix. | The receipts module reads the CoA on every categorisation and picker render. Separate files mean `ATTACH` for no benefit. |
| Who resolves receipts | Both the console and IntelliBooks Desktop. Made safe by the back-feed contract. | Respects the agreed Corrections rule while fixing the three defects it now causes. Preserves built work. |
| Review folder | Written by the pipeline, treated as a log. Cleared on resolution by whichever tool resolves. | Matches the decision already taken for mailbox folders. |
| GL correction | In scope, against the Default CoA CSV. | `resolve_receipt.py` cannot override a category today and `repo.update_categorisation()` is never called. The GL code is the field most likely to be wrong. |
| Default CoA | Keep the detailed numbered ledger. Mapping columns for QBO and Xero reserved but empty. | Vendor history already encodes the distinctions and they cannot be recovered once collapsed. Export adapters are phase 2 or 3. |
| Provider switching | Phase 1 only: factory, `extractor.name`, shared post-processing, display current engine. | Phase 2 touches `find_failed_by_version` and the retry cap tested on 2026-07-25, and deserves its own session. |
| Locking for the web UI | No lock on view. Lock only for the submit. Optimistic concurrency via `expected_extraction_id`. | The 60-minute stale window suits a CLI that finishes or crashes, not an operator closing a tab. |
| Browsing | Queue defaults to receipts needing attention. A separate browse page filters all receipts by client, tax year or recent days, with search. | Empty queue means nothing needs attention. Browsing filed receipts needs different filters, notably invoice date rather than capture date. |

---

## 3. Phase 0: bugs to fix before anything else

Each gets its own commit and its own red/green test, following the pattern used for the retry cap on 2026-07-25.

### 3.1 Auto-retry loops every poll when extraction throws (highest priority, costs money)

`_retry_failed_receipts()` is meant to retry each receipt once per `pipeline_version` change. When `extract_with_transient_retry()` raises, control jumps to the bare `except Exception` at line 374, which logs and moves on. `process_extraction_result()` never runs, so `save_extraction()` never runs, so the receipt's latest extraction keeps its **old** `pipeline_version`.

`find_failed_by_version()` compares the latest extraction's version against the current one, so the receipt stays eligible permanently and is retried on **every five-minute poll**, burning three real OpenAI calls each time via the transient-retry helper.

Reproduced live: the same `pipeline_version` retried five times, five minutes apart, for two known-broken test receipts.

**Fix.** In the exception path, save a `failed` extraction row tagged with the current `pipeline_version`, mirroring what a normal failed outcome records:

```python
repo.save_extraction(
    extraction_id=str(uuid.uuid4()),
    receipt_id=receipt_id,
    engine=extractor.name,              # not hardcoded, see 3.8
    supplier_name=None, invoice_date=None,
    net_amount=None, vat_amount=None, gross_amount=None,
    currency="GBP",
    raw_response=str(exc),
    validation_status="failed",
    validation_notes=[f"auto-retry extraction error: {exc}"],
    pipeline_version=pipeline_version,
    update_status=False,                 # see below
)
```

**`update_status=False` is deliberate and needs adding to `save_extraction()`.** That method currently also runs `UPDATE receipts SET status = validation_status`, which would flip a `needs_review` receipt to `failed`. A crashed retry is information about the API, not about the document, and the operator-facing distinction is worth keeping. Default the parameter to `True` so no existing caller changes behaviour.

**Same defect, second branch.** The missing-file branch at line 335 calls `add_validation_note()` and `continue`s without saving an extraction row, so a receipt whose original has gone is reconsidered every poll too. No OpenAI cost, since it never reaches extraction, but it logs a warning every five minutes forever. Same fix: save a `failed` row tagged with the current version.

**This compounds with 3.9.** A declined card makes the extractor raise, so an OpenAI billing problem becomes a five-minute loop making three failing calls each time.

**Test.** Mock the extractor to raise. Run `_retry_failed_receipts()` twice under the same `pipeline_version`. Assert the extractor was called on the first pass and **not** on the second. Add a second test for the missing-file branch.

**Built 2026-07-26 in `787493f`, with `tests/test_auto_retry_no_loop.py`.** Two points settled during implementation.

*Branch B keeps its note in the new row, not on the old one.* The design above said "same fix" and left `add_validation_note()` in place. It should not have. That method at `repository.py:571` runs `UPDATE extractions SET validation_notes = ?` against an existing row, so the original behaviour mutated an append-only row on every poll, and keeping both calls would have mutated the old row **and** written a new one. The missing-file note now goes into the new `failed` extraction row and names the path. The earlier extraction is left untouched. See 17.4 for the wider question about `add_validation_note()`.

*A receipt whose original file has gone keeps its existing status.* It was tempting to send it straight to `failed` or `retry_exhausted`. Both are wrong. `retry_exhausted` means "we stopped retrying because of age" and would misreport why. `failed` would erase a `needs_review` receipt's real finding about the document. Because the status is untouched, the receipt still appears in the queue at 8.2, where the validation note explains that the original is missing, which is where an operator should see it. The cost is one extraction row per `pipeline_version` change and no API calls. No further change.

*Known gap, accepted.* If `save_extraction()` itself raises inside the exception handler, it propagates out and abandons the remaining receipts in that pass. The `finally` still releases the lock, and `process_once()` catches it, so the worst case is one logged error per run. Not worth a nested `try` until it happens.

### 3.2 A corrected value of zero is silently ignored

`resolve_receipt.py` lines 209-216 use `corrections.get(k) or extraction.get(k)`. `0.0` is falsy, so `--vat 0` keeps the wrong extracted VAT. Line 192's `if any([...])` compounds it: `--vat 0` alone fails the truthiness test and drops into interactive mode.

Correcting VAT to 0.00 is routine for zero-rated and exempt supplies, and currently cannot be done.

**Fix.** Key presence, not truthiness, everywhere including the mode-selection guard. Build the corrections dict from arguments that are `is not None`.

**Test.** Correct a non-zero extracted VAT to `0`; assert the stored row has `vat_amount = 0.0`.

### 3.3 Amount corrections are typed inconsistently, and the interactive path crashes

`get_corrections_interactive()` returns `input().strip()`, so strings. The `--flags` path uses `type=float`. `validate()` then does `round(result.net_amount + result.vat_amount, 2)` and `val < 0`, both of which raise `TypeError` on a string. Swallowed by the broad `except` at line 353 and surfaced as a bare "ERROR:".

The T3 test passed on 2026-07-25 because it used the typed flags path.

**Fix.** One coercion function, `parse_corrections`, in the service layer, used by the CLI, the interactive prompts, the web form and the back-feed. Returns field-level errors rather than raising. See 4.2.

**Test.** Pass all amounts as strings; assert coerced floats or field errors, never a `TypeError`.

### 3.4 No actor recorded on a manual correction

A correction records `engine='manual_correction'` and nothing about who made it. With two authenticated console users plus `"desktop"` resolutions arriving via the back-feed, attribution is not optional.

**Fix.** New `resolution_events` table, section 5.1. Every resolution writes one row, whatever the entry point.

### 3.5 Review pair left on disk after resolution

`resolve_receipt.py` has no awareness of `Clients\{Name}\Review\`. Every receipt ever resolved has left its image and `.review.json` behind, so IntelliBooks still shows it as needing review and completing it there files a duplicate.

**Fix.** The resolution service removes the pair on a successful resolve or discard. Local file I/O, no IMAP involved. Log and continue if the files are already gone.

> **Amended 2026-07-27, implementation detail for step 4.** The service does not exist until step 8, so the helper goes in `worker/filing.py`, next to `file_review()` which writes the pair, and `resolve_receipt.py` calls it now. Step 8's service calls the same function. One implementation, four callers, per 4.1.
>
> **Do not locate the pair by reconstructing the filename.** `file_review()` at `worker/filing.py:114` names the image through `_unique_path()`, so a second review item for the same original filename becomes `{stem}-2{ext}`, and its sidecar `{stem}-2{ext}.review.json`. Rebuilding `{stem}{ext}` would miss that file, or worse, delete a different receipt's pair. Locate it by reading each `*.review.json` in that client's `Review` folder and matching the receipt: `extracted_values.receipt_id`, which `make_enriched_sidecar()` populates, falling back to `extracted_values.original_filename` for older sidecars. Delete the sidecar and the image it belongs to, together, and never delete an image whose sidecar you have not matched.
>
> `file_review()` should also start writing `receipt_id` at the top level of the payload, so a future reader does not have to reach into `extracted_values`. Forward-only: sidecars already on disk will not have it, hence the fallback.
>
> Note two things while in this area. `write_review_file()` at `worker/filing.py:142` is never called from anywhere in tracked source, so it is dead code that a reader could easily mistake for the live writer. And `app.py:666` files a **statement** to Review with `intake.sidecar or {}`, so that payload has no `receipt_id` and no receipt row exists. The cleanup must ignore it rather than fail on it.

> **Corrected 2026-07-27, and built in `dce1fdc`.** The two rules above contradict each other on the same input: fall back to `original_filename` for sidecars with no `receipt_id`, and also ignore any sidecar with no `receipt_id`. A sidecar with no id is the same file in both sentences. Flagged by the implementation session; it was a drafting error here, not an implementation question.
>
> The ordering that makes both survive, and what is built. Match on `receipt_id` across the whole folder first. Only then consider id-less sidecars for a filename match, and only when there is **exactly one** candidate: two review items can share an original filename, which is precisely the `-2` case, and an ambiguous match is not a match, so it logs a warning and touches nothing. Match on `extracted_values.original_filename` only, never the top-level copy, because the top-level key is on every review sidecar ever written including the statement one, so using it would widen the blast radius for no gain.
>
> Two further implementation policies, both accepted. A failed image deletion leaves **both** files in place and returns 0, rather than removing the sidecar anyway: an image with no sidecar cannot be found by this code again, so a retryable state beats an orphan. And `file_review()` writes `receipt_id` only when there is one, pulled from `extracted_values`, rather than always writing the key with `null` for statements, which avoids adding a null key to a payload IntelliBooks reads.
>
> **Untested against a live pair.** There has been no receipt in a Review folder since 26 July, so all of the above is temp-directory evidence. The first live exercise is whenever a receipt next lands in review and is resolved, and it is worth watching rather than assuming. All 32 filed sidecars carry `receipt_id`, so the filename fallback is theoretical on current evidence and guards only against sidecars from a version nobody can now inspect.

### 3.6 `review_count` over-reports, permanently and cumulatively

`_count_review_items()` (line 89) counts files under `Clients\*\Review\`. Because of 3.5, nothing is ever removed, so the count in `pipeline-status.json` only grows. It happens not to show in IntelliBooks today only because change log item 20 removed that clause from the banner.

**Fix.** Count from `receipts.db` by status, which is the stated source of truth. Fixing 3.5 makes the folder count correct too, but the DB is the right source regardless.

> **Amended 2026-07-27.** `review_count` means **`needs_review` plus `possible_duplicate`**: the receipts where a human has to decide something. `failed` and `retry_exhausted` are not review items, they are receipts the system could not read, and conflating them would tell an operator to go and look at something there is nothing to look at yet. Report them as their own counts on the status page at 8.1, which already lists all seven statuses separately.
>
> `_count_review_items()` at `app.py:121` walks `CLIENTS_ROOT.rglob("Review/*")` and counts every file, so it counts each pair twice and never decreases. Replace the body and keep the name; it gains a `repo` parameter, which is available at the only call site, `app.py:978` inside `process_once()`. Do it through a new `repo.count_receipts_by_status(statuses)`, which section 6.3 already lists as a required query method, rather than SQL in `app.py`. Leave `_write_pipeline_status()` and the shape of `pipeline-status.json` alone: IntelliBooks Desktop reads that file.

> **Clarified 2026-07-27, and built in `25c6665`.** `review_count` exists to feed `pipeline-status.json`, which IntelliBooks Desktop reads. **It does not define what the console shows an operator.** That is the queue page at 8.2, whose default filter is `needs_review`, `possible_duplicate`, `failed` **and `retry_exhausted`**, so a receipt that automatic retry has given up on does have a home there. The two counts answer different questions and are allowed to differ.
>
> `_count_review_items()` keeps its name per the amendment above, but it no longer counts items and no longer touches the Review folder, so the name will read as a lie to the next person in that file. Deliberate for now: renaming it would touch the same lines that steps 9 and 15 revisit. Rename it at step 15, when the console's read queries land and `_write_pipeline_status()` is in scope anyway.

### 3.7 The sidecar writes a nominal code where the books expect a name

`make_enriched_sidecar()` writes `category` as a nominal code, for example `"104"`. IntelliBooks' categories are names with no codes, and `catOptions()` matches on name, so the value matches nothing and the receipt arrives uncategorised.

This reaches the books rather than staying cosmetic, because "Post to cashbook" (IntelliBooks change log item 7) creates a transaction directly from a receipt and copies the category across.

**Fix.** The sidecar carries **both**: `category_code` for the nominal and `category_name` for the desktop-compatible name. Keep the existing `category` key populated with the name for backward compatibility with sidecars already on disk. The IntelliBooks half, preferring `category_name` in `parseSidecar`, is covered by the separate brief in `PROMPT_intellibooks_resolution_backfeed.md`.

Until the Default CoA CSV exists there is no code-to-name mapping, so `category_name` falls back to `account_name` from the vendor mapping, which is what the engine already returns.

> **Amended 2026-07-27, before step 5 is built. What is actually in that field on disk is worse than this section says.**
>
> Across the 32 sidecars already filed under `Clients\*\Receipts\`, `category` holds four different kinds of value:
>
> | Value | Count | What it is |
> |---|---|---|
> | `"unmatched"` | 18 | The literal `match_source`, not a code and not a name. The `categorisations` table has `suggested_code = NULL` for all 22 unmatched rows, so the live writer at `worker/extraction_pipeline.py:232` cannot have produced this. Something else wrote it, most likely `retroactive_categorise.py`. |
> | `null` | 10 | Six of these carry `"confidence": "high"`, which is a contradiction on its face: high confidence in nothing. |
> | `"271"`, `"999"` | 2 | Nominal codes. The case this section describes. |
> | `"Parking and tolls"` | 2 | A category **name**, with no `confidence` key at all. Not from the vendor tables: every `nominal_code` in both mapping tables is numeric, checked. These two are also the pair with the swapped dates, `2026-05-09` and `2026-09-05`, so they predate the day-first fix and probably predate this pipeline. |
>
> **All 32 are test data, confirmed by Paul on 2026-07-27: test clients and his own record, not a third party's books.** So the table above is forensic evidence of how one field drifted across five writers, not a data problem to repair. Nothing needs backfilling, see 17.4. Read it for what it says about the format, which is the part that matters, because the same writers will produce the same drift on real data if they are not fixed.
>
> Two consequences that do carry. First, whoever builds this must find out what wrote `"unmatched"` and whether it can still run, because a fix to `make_enriched_sidecar()` does not stop a script that writes the field directly. It was `retroactive_categorise.py:150`, `code = categorisation_data.get('suggested_code') or "unmatched"`, and it can still be run by hand. Second, the two sidecars carrying a category **name** with no `confidence` key were written by something other than any writer in this repository, and if that something is IntelliBooks Desktop's own filing flow then two sidecar shapes will coexist for the same receipt population once step 10 lands. That is a format question, not a data question, and it survives the data being disposable.
>
> **Two gaps this section left open, both settled 2026-07-27 after `9f5cdad`.**
>
> **The review path writes all three keys as `null`, and that is intended.** "The sidecar carries both" is not true on the review path, because nothing is categorised until a receipt is filed. A review sidecar therefore advertises three category keys it can never populate. That is deliberate: it is what makes all four call sites produce an identical key set, which is the property that stops the format diverging again. A reader comparing a review sidecar with a filed one should read three nulls as "categorisation has not run", not "categorisation failed".
>
> **A code with no name is now possible, and it is worse than either alone.** `category_name` comes from `categorisation.suggested_name`, which is only as populated as the engine layer that set it. Layers 0 to 4 take `account_name` from a rule or a vendor row, so they always have one. Layer 5, the AI suggestion at `engine.py:307`, sets `suggested_name=ai_result.get("name")`, which is `None` if the model's response omits the key. That would write `category_code` with a real nominal and `category`, `category_name` as `null`, so the books would carry a nominal while Desktop showed the receipt as uncategorised. **It cannot happen today**, because `enable_ai_fallback=False` at every call site, `app.py:489` and `retroactive_categorise.py:91`. Whoever enables the AI layer must require a name alongside a code, or refuse the suggestion. Do not treat `suggested_code` and `suggested_name` as independently optional.
>
> **Four call sites, not one.** `make_enriched_sidecar()` is called from `app.py:229`, `resolve_receipt.py:328`, `worker/extraction_pipeline.py:184` and `worker/extraction_pipeline.py:257`, and `extraction_pipeline.py:232` then overwrites `sidecar_payload['category']` and `['confidence']` after the fact. All of them have to carry `category_code` and `category_name`, or the format is inconsistent depending on which path filed the receipt, which is the same class of problem as the four value kinds above.

### 3.8 `engine="openai_vision"` hardcoded on failure paths

`app.py` around lines 530, 709 and 880 hardcode the engine string when saving a failure row. These would misreport after any provider change. Replace with `extractor.name` from the factory in section 10.

### 3.9 Billing errors indistinguishable from unreadable documents

A quota, authentication or rate-limit failure surfaces as a generic extraction exception, marks the receipt `failed`, routes the email to "Failed Processing", and starts the 7-day `retry_exhausted` clock. So a billing outage silently becomes a pile of receipts that look like bad documents, and they can burn their whole retry window while a card is declined.

**Fix.** `worker/extraction/retry_helper.py` already distinguishes transient errors. Extend it to classify quota, auth and rate-limit errors separately, record the classification in the validation notes, exclude billing-blocked receipts from the `AUTO_RETRY_MAX_AGE_DAYS` clock, and surface them distinctly on the status page: "3 receipts failed because of API billing, not because the document was unreadable."

### 3.10 `processed_today` is mislabelled

`app.py` line 908 writes "receipts created in this run" into a field called `processed_today`. `repo.count_processed_today()` does the real thing and is not wired to it. Fix the status file, and do not let the console inherit the confusion; the console reads the DB.

> **Amended 2026-07-27.** Built with step 4 rather than as its own step. It is `processed_today = stats.get("receipts_created", 0)` at `app.py:977`, three lines above the `review_count` call this step is already replacing, in the same function. Splitting them would mean two commits touching the same three lines. The bundling is deliberate and the tests stay separate.

---

### 3.11 `extractions.details` is never written, so every automatic amendment goes unrecorded

Added 2026-07-27, found while verifying step 6b.

`ExtractionResult.details` is where the post-processing records what it changed and why: `auto_treated_amount_as_gross(...)` when it decides an extracted net was really a gross, `auto_parsed_invoice_date_from_raw(...)` when it overrides the model's date, and the two ambiguity notes. **None of it reaches the database.**

`extractions` has a `details` column, `schema.py:120`, with a `PRAGMA table_info` migration for older databases at `schema.py:165-168`. So the column was added deliberately. But `save_extraction()` takes no `details` parameter and its `INSERT` lists sixteen columns, not including that one, so nothing has ever written it through that method. Nothing passes `details` to it anywhere. The sidecar has no `details` key either.

**This is a regression, not an omission.** Two of the 49 rows in the live database do hold a value: both from 19 July, both with `pipeline_version` NULL, one reading `auto_parsed_invoice_date_from_raw(raw=09/05/26 -> 2026-05-09)`. So the write worked once and was lost. `git log -S` on `repository.py` points at `799cead` and `10d5742` as the commits that touched `details` handling there.

**Why it matters more than a missing field.** `apply_vat_inclusive_swap()` rewrites `net` and `gross` on the strength of an implied VAT rate. That is a change to two financial figures, made automatically, and `CLAUDE.md` says this is a capture and audit system whose job is to read, extract, validate and store, not to clean or normalise, with a full audit trail. The swap is a transformation, it is the right one to make, and there is currently no record anywhere that it happened. A query for `auto_treated` or `auto_parsed` across `validation_notes` and `raw_response` in all 49 rows returns zero.

It also means step 6b improved a string nobody can read. The functional half of that step landed properly, because an ISO raw date now produces the right `invoice_date` and that column is written. The notes half did not.

**Fix.** Add `details=None` to `save_extraction()` and to the `INSERT`, pass it from every caller that has an `ExtractionResult`, and display it on the receipt detail page per 8.4. Do not fold it into `validation_notes`: those are validation outcomes and these are amendment records, and merging them would make both harder to read. `details` stays out of the sidecar for now, because that is a format change to a file IntelliBooks reads.

**Built 2026-07-27 in `4aeadcd`**, and `799cead` on 21 July is where the write was dropped, confirmed from its diff. Two call sites hold an `ExtractionResult` and pass it, `worker/extraction_pipeline.py:160` and `app.py:576`; the five failure paths have none, because the call raised before producing one, and take the default; `resolve_receipt.py:278` passes `None` explicitly for a manual correction.

> **One consequence of keeping it out of the sidecar, stated so nobody reports it as a bug.** From `4aeadcd` onwards the database records that an amount was amended and the sidecar does not, so the same receipt opened in the console and in IntelliBooks Desktop will disagree about whether anything was changed. That is deliberate and it is the right trade while the sidecar is a format another application reads, but it is a real asymmetry rather than an oversight. Revisit it alongside the two-sidecar-shapes question in 17.4, since both are really the same question about what that file is for.

---

### 3.12 Two extraction writes omit `pipeline_version`, so their receipts are retried once for nothing

Added 2026-07-27, found while verifying step 7. Flagged by the implementation session for one call site; there are two.

`find_failed_by_version()` at `repository.py:481` treats a NULL `pipeline_version` on the latest extraction as eligible for retry. Both writes on the embedded-image path omit the argument, so the column is NULL:

| Call site | Path | Effect |
|---|---|---|
| `app.py:576` | embedded-image success | A receipt that lands `needs_review` is re-extracted on the next poll whatever the version. |
| `app.py:610` | embedded-image failure | A `failed` receipt is re-extracted on the next poll whatever the version. |

Every other write passes it: `app.py:386`, `446`, `792`, `963`, `resolve_receipt.py:278` and `worker/extraction_pipeline.py:160`.

**This is the same class of defect as 3.1 but not the same severity.** It costs one unnecessary retry, three OpenAI calls, per affected receipt, and then self-corrects, because the retry itself writes a versioned row through a path that does pass the argument. It is not the endless loop 3.1 fixed. It is still a real cost on a live path and the fix is one keyword argument in each place.

**Fix.** Pass `pipeline_version=pipeline_version` at both sites. Test that a receipt created through the embedded-image path is not selected by `find_failed_by_version()` on a second pass under the same version, which is the assertion that catches this whole family.

Note for whoever writes it: 28 of the 49 rows in the live database have a NULL `pipeline_version`, almost all of them from before the column existed. So a query for NULLs is not a measure of this defect, and fixing it does not clean them up.

---

### 3.13 A folder-intake receipt that is not `ok` is re-extracted on every poll

Added 2026-07-28, found live while creating a Review item for the change log item 19 test.

`_remove_inbox_pair(intake)` at `app.py:777` runs only `if status == "ok"`. So a receipt that lands `needs_review`, `failed` or `possible_duplicate` leaves its original in `Receipt Inbox\{CODE}\`. On the next poll `find_by_hash()` finds the existing receipt, `is_recorded_and_filed()` returns false because `filed_path` is NULL, and `app.py:717` then deliberately continues: "If hash matches a failed/needs_review receipt, allow reprocessing".

**So it is re-extracted every five minutes, indefinitely**, creating a new receipt row, a new extraction row and a new Review pair each time. This is the folder-intake twin of 3.1, which was fixed first because it was the only defect costing money continuously. It has been live throughout and went unnoticed because nobody had left a non-`ok` receipt in an inbox folder.

Observed: `TEST_vat_mismatch.png` dropped into `Receipt Inbox\TEST\` at 12:09 on 2026-07-28, processed at 12:12 to `needs_review`, original still in the inbox, next poll due at 12:17. Caught before the second pass.

**Fix, decided by Paul 2026-07-28.** Move the original out of the inbox on **every** outcome, not only `ok`. A `Processed\` subfolder under the client's inbox folder, so the file is retained rather than deleted, per the no-data-loss rule. The reprocessing rule at `app.py:717` then becomes unreachable for this case and should be left alone rather than removed, because it still guards the genuine resend of a file the operator puts back deliberately.

The alternative considered and rejected was to keep the reprocessing rule and gate it on `pipeline_version`, mirroring `find_failed_by_version()`. Rejected because the auto-retry loop already re-extracts from the database properly, so the inbox does not need a second mechanism for the same thing. One implementation, not two.

**Test.** A receipt that lands `needs_review` through folder intake has its original moved out of the inbox, and a second `process_once()` under the same version creates no second receipt row and makes no extraction call. Same for `failed`. And the `ok` path keeps working, since it currently deletes rather than moves and that changes.

### 3.14 The statement path in folder intake never clears the inbox

Added 2026-07-28, found by the implementation session while fixing 3.13. Not fixed.

Two branches in the folder-intake loop, neither covered by 3.13's fix, because 3.13 named the receipt outcome paths.

`app.py:756-783` files a statement and continues without clearing the inbox. The next poll's `find_statement_by_hash()` recognises it and cleans up, so it self-corrects one poll late. Untidy rather than harmful.

The missing-metadata branch above it is worse: it writes a Review pair and continues, so it **writes another Review pair on every poll, indefinitely**. No OpenAI cost, because statements are never extracted, so this is not the money bug. It is the same family as 3.13 and it fills a client's Review folder.

Fix when picked up: the same treatment as 3.13, move the original to `Processed\` on every outcome, including both statement branches. Left for now because it was outside the brief and statements are not in use.

The two hash-duplicate paths at `app.py:665` and `app.py:713` still delete rather than move, and that is correct: in both cases the original is already filed elsewhere, so there is nothing to lose.

---

## 4. The resolution service

### 4.1 Layering

```
resolve_receipt.py                 CLI wrapper. All print() and input(). ~100 lines.
console/web.py                     Flask routes. All HTTP.
app.py                             Pipeline. Consumes back-feed notes.
worker/resolution/service.py       Domain logic. No print, no input, no Flask, no IMAP.
```

`worker/resolution/service.py` must not import Flask, `argparse`, or anything under `worker/email/`. That is what makes it reusable by a cloud API later and testable now.

**There are four callers and they must all go through the same functions.** The CLI, the console, the back-feed consumer, and any future API. Three independent implementations of resolution is what caused the divergence this design exists to fix.

### 4.2 Service API

```python
CORRECTABLE_FIELDS = (
    "supplier_name", "invoice_date", "net_amount",
    "vat_amount", "gross_amount", "receipt_ref_number", "receipt_time",
)

@dataclass
class ResolutionView:
    receipt: dict
    extraction: dict | None             # latest, the one being corrected; None if there is none
    extraction_history: list[dict]      # all, newest first
    categorisation: dict | None         # may be None; the non-ok path saves none
    resolution_events: list[dict]
    duplicate_of_receipt: dict | None   # when status == 'possible_duplicate'
    duplicate_of_extraction: dict | None
    client_name: str
    business_type: str
    gl_code_options: list[dict]         # from the Default CoA, section 11
    effective_gl_code: str | None       # correction_code if set, else suggested_code
    file_path: str
    is_locked: bool                     # informational only

@dataclass
class Corrections:
    values: dict[str, object]           # only fields explicitly supplied
    gl_nominal_code: str | None = None
    gl_account_name: str | None = None
    gl_correction_reason: str | None = None
    remember_gl_for_supplier: bool = False

@dataclass
class ResolutionOutcome:
    outcome: Literal["filed","discarded","still_invalid","stale",
                     "locked","not_found","already_filed","error"]
    receipt_id: str
    extraction_id: str | None
    filed_path: str | None
    category_code: str | None
    category_name: str | None
    category_confidence: str | None
    validation_notes: list[str]
    message: str                        # safe to show an operator
    error_detail: str | None            # logs only, never rendered


def get_resolution_view(repo, receipt_id) -> ResolutionView | None:
    """Read-only. Takes no lock. None if the receipt does not exist."""

def parse_corrections(raw: dict) -> tuple[Corrections, dict[str, str]]:
    """Normalise operator input. Returns (corrections, field_errors). Never raises."""

def resolve_receipt(repo, categorisation_engine, receipt_id, corrections,
                    actor, source, expected_extraction_id=None) -> ResolutionOutcome:
    """Apply corrections, re-validate, categorise, file. Append-only throughout."""

def discard_receipt(repo, receipt_id, reason, actor, source, note_resolved_at=None) -> ResolutionOutcome:
    """Status to 'discarded'. Never deletes the original file or any extraction row."""

def apply_resolution_note(repo, categorisation_engine, note: dict) -> ResolutionOutcome:
    """Back-feed entry point. Validates the note, then calls resolve_receipt or
    discard_receipt with actor='desktop'. Must not reimplement resolution."""
```

> **Amended 2026-07-27, before step 8 is built.** `source` added as a required parameter to `resolve_receipt()` and `discard_receipt()`. `resolution_events` in 5.1 has both an `actor` and a `source` column, `'console' | 'cli' | 'desktop'`, and the signatures as first written supplied only `actor`, so the service could not have populated its own audit row. Required rather than defaulted: a default would be wrong for three of the four callers, and the point of the column is that nobody has to guess.
>
> **Which outcomes write a `resolution_events` row:** `filed`, `discarded` and `still_invalid`. Not `not_found`, `stale` or `locked`, because nothing happened and 4.3 steps 1 to 4 say write nothing. Not `error` either: the state is unknown at that point and a second write risks compounding it, so the traceback in the log is the record. Note that until step 9 builds `worker/logging_setup.py`, per 6.5, that traceback only reaches `data/run.log` when the service is called from inside `app.py`.

`parse_corrections` rules:

- A key absent from `raw`, or `None`, is omitted from `values`.
- An empty string means "clear this field", stored as `None`. Distinct from omission, so an operator can remove a wrongly extracted reference number.
- Amounts coerce to float. Reject thousands separators, currency symbols and more than two decimal places as field errors rather than guessing.
- `invoice_date` must be `YYYY-MM-DD` and a real date. Do not reparse other formats; that is the extractor's job and guessing here would undo the day-first work in `openai_vision.py`.
- Never raises. Bad input becomes a field error.

> **Amended 2026-07-27.** Built in `c0ac145`. Three points this section left unstated, now settled.
>
> **The four GL fields on `Corrections` are not read from `raw`.** `parse_corrections` populates `values` only, and leaves `gl_nominal_code`, `gl_account_name`, `gl_correction_reason` and `remember_gl_for_supplier` at their defaults. GL semantics belong to section 11 and the console form at step 16, which sets them on the dataclass directly. When step 16 arrives, decide there whether `remember_gl_for_supplier` reads a checkbox key's presence or its value, because an unchecked HTML checkbox sends nothing at all.
>
> **`receipt_time` has no format rule and is stored as stripped text.** It is the one correctable field with no validation, so `25:99` is accepted. Defensible, because the extractor writes it and no validation rule reads it, but it was unstated rather than decided. If the console offers a time input, validate it there.
>
> **Implementation decisions worth knowing.** A whitespace-only string is treated as a clear, same as empty. `.50` is accepted as `0.50`, since it is unambiguous and not one of the three forms this section rejects. `nan` and `inf` are rejected, which a bare `float()` would have accepted. A leading minus is accepted, so a negative amount reaches `validate()` and becomes a validation note rather than a field error, which keeps the "is this a bad figure or a bad document" judgement in one place.
>
> **On the CLI, an empty-string flag now clears a field.** `--ref-number ""` reaches `parse_corrections` as present-and-empty. That is this section's own semantics arriving unaltered, not a sentinel, and it is the shape the console form will use. Interactive mode still treats a blank answer as "keep existing" and omits the key, which `RECEIPT_CAPTURE_GUIDE.md` documents. The asymmetry is accepted for now, see 17.4.
>
> One consequence to note: `type=float` was removed from `--net`, `--vat` and `--gross` in `0cae398`, because leaving it would keep a second and more permissive coercion in the CLI, which is the thing 3.3 exists to remove. `--gross 1,234.56` used to exit 2 from argparse and now exits 1 with a field error naming the field. Both non-zero. Step 21 should mention empty-string flags in the guide.

### 4.3 `resolve_receipt` control flow

Order matters. Commit `b480a7e` fixed a foreign key violation caused by categorising before the extraction row existed. Do not reorder steps 7 and 8.

1. Load receipt. Missing, return `not_found`.
2. Load latest extraction. Missing, return `not_found` with a message saying so.
3. If `expected_extraction_id` is supplied and does not match the latest, return `stale` and write nothing.
4. Acquire the receipt lock. Failure, return `locked`. Everything below in `try/finally` releasing it.
5. Merge corrections over the existing extraction by key presence, not truthiness.
6. Build `ExtractionResult` with `engine="manual_correction"`, run `validate()`. Not ok: **append a new extraction row** carrying the corrected values, `validation_status` from `validate()` and the validation notes, then write a `resolution_events` row with outcome `still_invalid`, and return. Do not file.

> **Amended 2026-07-27, decided by Paul.** Superseded wording: "Not ok: `add_validation_note()`, write a `resolution_events` row with outcome `still_invalid`, return."
>
> `add_validation_note()` at `repository.py:571` reads the latest extraction, concatenates, and runs `UPDATE extractions SET validation_notes = ? WHERE extraction_id = ?`. That is an in-place edit of a table `CLAUDE.md` says is never modified after creation. A resolution attempt that failed validation is an event worth its own row, not a footnote appended to the row it disagrees with. Phase 0 step 1 already took this route for the missing-file branch, see 3.1, so the codebase would otherwise be doing it two ways.
>
> **Consequences to handle at step 8, not before.** `add_validation_note()` is retired: its callers are `resolve_receipt.py:239` and `app.py`'s missing-file branch, which no longer needs it. Remove the method once both are gone, rather than leaving a tempting mutation in the repository. `tests/test_resolve_receipt_ordering.py:209` asserts the mutation happens and must be rewritten to assert the new row instead. Test 16 in section 15 is reworded accordingly. Note that this row is written on a path that does **not** file, so `resolution_events.extraction_id` is now populated for a `still_invalid` outcome, which is why 5.1 makes that column nullable but puts no foreign key on it.
7. Generate `extraction_id`, then `save_extraction()`. The FK from `categorisations` requires the row to exist first.
8. `categorisation_engine.categorise()`, then `save_categorisation()` with the engine's suggestion. Never overwrite `suggested_code` with the operator's value; that is the audit trail.
9. If a GL override was supplied, `update_categorisation()` now, before filing. Section 11.2 explains why.
10. Build the enriched sidecar using the **effective** code and name: the override if present, otherwise the suggestion. Populate `category_code`, `category_name` and legacy `category`.
11. `file_receipt()`, `mark_receipt_filed()`, `update_receipt_status(receipt_id, 'ok')`.
12. Remove the Review pair for this receipt, per 3.5. Log and continue if already gone.
13. If `remember_gl_for_supplier`, `upsert_client_vendor()`. Opt-in only, section 11.3.
14. Write a `resolution_events` row with outcome `filed`.
15. Return `filed`.

> **Amended 2026-07-27, after step 8 was built. Five points this control flow left to the implementer, four now decided here and one still Paul's.**
>
> **New step 1a, and it is the important one: refuse a receipt that is already filed.** Nothing in the fifteen steps inspects `filed_path` or `status`, so `resolve_receipt()` on an `ok` receipt will re-file it, write a second `manual_correction` row and leave a second copy on disk under a `-2` name. That is the double-filing this entire design exists to prevent, arriving through the front door. `expected_extraction_id` makes it unlikely from the console, because the caller must know the current extraction, but the CLI and the back-feed can both omit it. **So: if `filed_path` is not NULL, return the new `already_filed` outcome and write nothing.** It is a distinct expected condition, not an error, and the console must be able to say "this was already filed on <date>, here it is" rather than showing a failure. The back-feed's `filed` note is the one legitimate exception and it does not come through this path: 12.3 step 5 has `apply_resolution_note()` call `mark_receipt_filed()` directly.
>
> **Step 6, `update_status`.** `save_extraction()` stamps `receipts.status` with the new `validation_status` unless told not to. On the `still_invalid` branch that is right for a `needs_review` or `failed` receipt and wrong for a `possible_duplicate` one, which would silently become `needs_review`: the duplicate framing would vanish from `status`, 8.4's side-by-side comparison would stop rendering, and the receipt would become eligible for auto-retry, which `possible_duplicate` is not. A human has already looked at it. **So preserve `possible_duplicate` and let the other statuses follow `validate()`.** `possible_duplicate` is a statement about the relationship between two receipts, not about the validity of one, so validation must not overwrite it. Separately, 8.4's duplicate comparison should key on `duplicate_of` being non-NULL rather than on `status`, which makes it robust whatever the status says.
>
> **Step 9's trigger.** "If a GL override was supplied" is ambiguous, because `Corrections` carries the code and the name separately. An override is present when **either** is non-empty after stripping; fill the missing half from the engine's suggestion; default the reason to something naming the actor. Whitespace-only counts as absent, consistent with `parse_corrections`.
>
> **Step 13's `vendor_code`.** `upsert_client_vendor()` is keyed on `(client_id, vendor_code, vendor_name)` and this section never says where the code comes from. Use `CategorisationResult.vendor_code`. When it is `None`, which is what an unmatched supplier gives, log a warning and learn nothing. **Do not import the engine's `normalise_description()` into the service**: the service must not acquire a second implementation of vendor normalisation.
>
> **Resolving a `possible_duplicate` is the "file it anyway" path.** There is no separate action and none is needed. `discard_receipt()` is "this is a duplicate", and `resolve_receipt()` files it because nothing in the flow inspects `status`. That is now intended rather than incidental, and 8.4 should label the two buttons accordingly.

Keep a broad `except Exception` logging with `exc_info=True` and returning `error` with `error_detail`. Trade-off accepted: the caller cannot see the traceback, but the web layer never 500s on a Save.

> **One observation, no action.** `resolve_receipt()` calls `config.get_pipeline_version()`, which shells out to `git rev-parse`. `resolve_receipt.py` already did, so it is not new, and 4.1 does not forbid it. Note that it returns the string `"unknown"` on any failure, so on a machine where git is unavailable a still-invalid correction would stamp `"unknown"` and `find_failed_by_version()` would then treat that receipt as eligible on every poll. Harmless today because the console runs beside the repository. It becomes real the day this is deployed anywhere else, and the fix then is to resolve the version once per process rather than per call.

> **Amended 2026-07-26.** Superseded wording: "and the traceback still reaches `data/run.log`". That was not true when it was written. `logging.basicConfig` in `app.py` set `handlers=[StreamHandler(sys.stdout)]` and nothing else, no `FileHandler` existed anywhere in the tracked source, and `data/run.log` had not been written since 5 May. Commit `285ed63` attached a `RotatingFileHandler`, but from `app.main()` only, so the claim now holds for the back-feed consumer and nothing else. `resolve_receipt.py:34` calls `basicConfig` with no handlers argument and logs to stderr. **This trade-off is only sound once every entry point attaches the handler.** See 6.5 and step 9 in section 16.

### 4.4 What the CLI keeps

`argparse`, `show_receipt_state()` rewritten to render a `ResolutionView`, `confirm_duplicated_action()`, `get_corrections_interactive()`, every `print()`. Maps outcomes to exit codes: `filed` and `discarded` are 0, everything else 1.

> **Amended 2026-07-27, after step 9 was built. Four things.**
>
> **`confirm_duplicated_action()` has never been called**, by the old CLI or the new one. Verified: it is defined at `resolve_receipt.py:105` and appears nowhere else in tracked source. So a `possible_duplicate` receipt with no `--duplicate-decision` flag goes straight to the correction prompts and is filed without anyone being asked whether it is a genuine second transaction. Given the amendment to 4.3 confirming that resolving a `possible_duplicate` **is** the "file it anyway" path, that is the one route left by which the CLI files a duplicate silently. **Wire it up.** Keeping a dead function because a document lists it is the worse of the two options.
>
> **`actor` on a CLI resolution** has no source, and `resolution_events.actor` is `NOT NULL`. It is `getpass.getuser()` by default, with an optional `--actor` flag to override. This section did not say, and the implementation had to choose.
>
> **The "about 100 lines" target in 4.1 is not achievable** while keeping what this section says to keep, and the target was wrong rather than the implementation. `resolve_receipt.py` is 268 lines: 76 are the three retained rendering and prompting functions, about 60 are the module docstring and `build_parser()`, and `main()` is 44. Nothing that belongs in the service is left in it. If the number matters later, `show_receipt_state()` is the candidate to move to a rendering module shared with the web layer.
>
> **The CLI reconfigures stdout to UTF-8 with `errors="replace"`.** The `✓` and `✗` characters raise `UnicodeEncodeError` on a cp1252 console, and they are printed **after** the receipt is filed, so the work succeeded and the operator got a traceback. Pre-existing, present at `60df040`, found during the manual test 40 run. Output is unchanged wherever the console can already encode it.

Existing behaviour must not change. Every command in `RECEIPT_CAPTURE_GUIDE.md` keeps working verbatim, except that zero now works and string amounts no longer crash.

Add `discard_receipt.py` as a thin CLI over `discard_receipt()`. Discarding a `failed` receipt has been done by hand three times now; it deserves a command.

---

## 5. Schema additions

Add to `worker/database/schema.py` inside the existing `executescript`, following the `CREATE TABLE IF NOT EXISTS` pattern, and the `PRAGMA table_info` guard pattern at lines 157-189 for new columns. Do not write a migration framework.

> **Sequencing corrected 2026-07-27.** Section 16 puts all of these at step 11, but **`resolution_events` (5.1) must be created at step 8**, because 4.3 step 14 has the resolution service write a row to it and step 8 is where that service is built. Everything else here stays at step 11: `console_users`, `extraction_usage`, `openai_credit_topups`, `openai_cost_daily`, `coa_accounts` and the indexes in 5.6. Splitting the schema work across two steps is less bad than a service that cannot record who did what, and `CREATE TABLE IF NOT EXISTS` means step 11 re-running the whole script is harmless.

### 5.1 `resolution_events`

```sql
CREATE TABLE IF NOT EXISTS resolution_events (
    event_id            TEXT PRIMARY KEY,
    receipt_id          TEXT NOT NULL,
    extraction_id       TEXT,
    actor               TEXT NOT NULL,      -- console username, or 'desktop'
    source              TEXT NOT NULL,      -- 'console' | 'cli' | 'desktop'
    action              TEXT NOT NULL,      -- 'resolve' | 'discard'
    corrections_json    TEXT,
    gl_override_code    TEXT,
    outcome             TEXT NOT NULL,
    created_at          TEXT NOT NULL,
    FOREIGN KEY (receipt_id) REFERENCES receipts(receipt_id)
);

CREATE INDEX IF NOT EXISTS idx_resolution_events_receipt
    ON resolution_events(receipt_id, created_at);
```

`extraction_id` is nullable, because a `still_invalid` outcome produces no extraction row. **Do not add a foreign key on it**; writing the event row for that outcome would then fail, which is the same class of bug as `b480a7e`.

> **Amended 2026-07-27.** Two corrections, both from building it.
>
> **Add a `reason TEXT` column.** `discard_receipt(repo, receipt_id, reason, actor, source)` takes a reason, and the table has nowhere to put it, so it currently reaches a log line and the operator's return message and then vanishes. For a discard the reason is the single most useful thing to keep: it is the difference between "duplicate of r-x" and "the client sent a bank statement by mistake". Use the `PRAGMA table_info` guard pattern; the table has no rows yet, so this costs nothing. Do not overload `corrections_json` for it.
>
> **The nullability rationale above is now out of date, though the rule still holds.** Under the amended 4.3 step 6 a `still_invalid` outcome does write an extraction row, so `extraction_id` will usually be populated. Keep the column nullable and keep the foreign key off it anyway: `not_found`, `stale`, `locked` and `already_filed` write no event row today, but the next outcome added might, and a nullable column with no FK cannot be the thing that breaks it.

### 5.1a `receipts.filed_at`

Added 2026-07-27. One new column via the `PRAGMA table_info` guard pattern:

```sql
ALTER TABLE receipts ADD COLUMN filed_at TEXT
```

`mark_receipt_filed()` is the only writer of `filed_path`, so it is the only place this needs setting, and the two stay consistent by construction. Existing rows keep NULL and must not be back-filled from a file mtime, which records when a copy was written rather than when the practice filed it.

Needed by 4.3 step 1a, whose `already_filed` message promises the operator a date, and by 8.3, which already lists a "filed" column that would otherwise only ever be a yes or no.

### 5.2 `console_users`

```sql
CREATE TABLE IF NOT EXISTS console_users (
    user_id         TEXT PRIMARY KEY,
    username        TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    role            TEXT NOT NULL CHECK (role IN ('admin', 'operator')),
    is_active       INTEGER NOT NULL DEFAULT 1,
    created_at      TEXT NOT NULL,
    last_login_at   TEXT
);
```

### 5.3 `extraction_usage`

Separate table so the append-only extraction row is untouched and capture stays optional.

```sql
CREATE TABLE IF NOT EXISTS extraction_usage (
    extraction_id       TEXT PRIMARY KEY,
    engine              TEXT NOT NULL,
    model               TEXT,
    prompt_tokens       INTEGER,
    completion_tokens   INTEGER,
    total_tokens        INTEGER,
    estimated_cost_usd  REAL,
    recorded_at         TEXT NOT NULL,
    FOREIGN KEY (extraction_id) REFERENCES extractions(extraction_id)
);
```

### 5.4 `openai_credit_topups` and `openai_cost_daily`

```sql
CREATE TABLE IF NOT EXISTS openai_credit_topups (
    topup_id        TEXT PRIMARY KEY,
    amount_usd      REAL NOT NULL,
    occurred_on     TEXT NOT NULL,
    note            TEXT,
    recorded_by     TEXT NOT NULL,
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS openai_cost_daily (
    day             TEXT PRIMARY KEY,
    amount_usd      REAL NOT NULL,
    currency        TEXT NOT NULL DEFAULT 'USD',
    fetched_at      TEXT NOT NULL,
    raw_json        TEXT
);
```

### 5.5 `coa_accounts` — reserved for module 2, created now

Created and populated from the Default CoA CSV in phase 1, so the receipts module reads it through the query layer from day one and module 2 enriches the same table with no change to the receipts side.

```sql
CREATE TABLE IF NOT EXISTS coa_accounts (
    account_key     TEXT PRIMARY KEY,   -- UUID
    scope           TEXT NOT NULL,      -- 'default' | 'group' | 'client'
    scope_ref       TEXT,               -- NULL for default, business_type, or client_id
    code            TEXT NOT NULL,
    name            TEXT NOT NULL,
    type            TEXT NOT NULL,      -- assets|liabilities|equity|income|expenses
    hmrc_box        TEXT,
    vat_treatment   TEXT,
    parent_code     TEXT,
    status          TEXT NOT NULL DEFAULT 'active',  -- active|not_adopted|archived
    provenance      TEXT NOT NULL DEFAULT 'default', -- default|group|client|imported
    maps_to_code    TEXT,               -- for archived/merged accounts
    source_ref      TEXT,               -- original name/code when imported
    qbo_detail_type TEXT,               -- reserved, phase 2/3
    xero_tax_type   TEXT,               -- reserved, phase 2/3
    notes           TEXT,
    updated_at      TEXT NOT NULL,
    UNIQUE(scope, scope_ref, code)
);

CREATE INDEX IF NOT EXISTS idx_coa_lookup ON coa_accounts(scope, scope_ref, status);
```

Phase 1 uses only `scope='default'`. The group and client tiers, the four import dispositions and the three statuses are specified in section 13 but not built.

### 5.6 Indexes for the queue and browse pages

None currently exist on `receipts.status`, `receipts.client_id` or `extractions.receipt_id`.

```sql
CREATE INDEX IF NOT EXISTS idx_receipts_status ON receipts(status);
CREATE INDEX IF NOT EXISTS idx_receipts_client_created ON receipts(client_id, created_at);
CREATE INDEX IF NOT EXISTS idx_extractions_receipt ON extractions(receipt_id, extracted_at);
CREATE INDEX IF NOT EXISTS idx_extractions_invoice_date ON extractions(invoice_date);
CREATE INDEX IF NOT EXISTS idx_extractions_supplier ON extractions(supplier_name);
```

Unmeasurable at 26 receipts. Free now, matters at a few thousand.

### 5.7 `clients.csv` gains `entity_type`

New column: `sole_trader | partnership | ltd | llp`, blank permitted. `load_clients()` reads it into the client dict with a default of empty string. Unused by module 1; module 2 needs it, because tax mapping targets depend on legal form, not on client group. A PHV driver can be either.

**`business_type` and `entity_type` are orthogonal and must not be merged.** Group drives the CoA template and the vendor mappings; entity type drives the tax mapping.

---

## 6. Data access and concurrency

WAL is **already enabled** (`schema.py` line 7) and persists in the DB file, so concurrent readers do not block on the worker's writes. Three things still need care.

**6.1 Never share a `Repository` across request threads.** It holds a single `self._conn`, and `sqlite3` connections are not thread-safe by default. Create per request. Do not set `check_same_thread=False` to work around it.

**6.2 Never call `init_db()` per request.** `Repository.__init__` runs the whole schema script plus several `PRAGMA table_info` queries every time. For reads, open a read-only connection:

```python
sqlite3.connect(f"file:{config.DB_PATH}?mode=ro", uri=True, timeout=30.0)
```

Set `row_factory = sqlite3.Row`. For writes, construct a normal `Repository`; that path is correct and infrequent.

**6.3 No SQL in route functions.** Add read methods to `Repository` or to `console/queries.py`:

```
get_status_counts() -> dict[str, int]
list_receipts_by_status(statuses, limit, offset) -> list[dict]
count_receipts_by_status(statuses) -> int
list_recent_runs(limit) -> list[dict]                     # from logs/runs.ndjson
get_extractions_for_receipt(receipt_id) -> list[dict]     # all, newest first (new)
list_resolution_events(receipt_id) -> list[dict]
search_receipts(filters, limit, offset) -> list[dict]
count_receipts(filters) -> int
list_clients_with_receipts() -> list[dict]
list_tax_years_with_receipts() -> list[str]
list_gl_code_options(client_id, business_type) -> list[dict]
get_spend_summary(period) -> dict
list_intake_issues() -> dict                              # section 8.6
```

**6.4 The console must run on the same machine as `receipts.db`.** SQLite over a network share risks corruption. The DB is correctly on local disk, not in OneDrive. Do not move it.

**6.5 Logging, added 2026-07-26.** Four things, all found during phase 0 step 1.

**Every entry point must attach the file handler.** `app.py` has `attach_run_log_handler()`, idempotent, called from `main()`. The resolution service has four callers, per 4.1, and only the back-feed consumer runs inside `app.py`. So move that function into a shared `worker/logging_setup.py` and call it from `app.main()`, `resolve_receipt.py`, `discard_receipt.py` and `run_console.py`. Build it at step 9, before the console exists, because 4.3 depends on it.

**Attach it at the entry point, never at import.** Attaching at import was tried and reverted the same day. It added 29 lines of synthetic test output to `data/run.log` on every suite run, some of it reading like real receipts being filed, which would mislead anyone running test 39.

**Two processes cannot share one `RotatingFileHandler` on Windows.** The loser of a rollover cannot rename a file the winner holds open, and it raises. The pipeline and the console are designed to run at the same time, and the CLI can run alongside both. So it is one file per entry point, `run.log`, `resolve.log`, `console.log`, or a single writer behind a `QueueHandler`. Not the same rotating handler in three processes. Decide at step 9. Current settings: 5 MB, three backups, UTF-8, append.

**Two config traps.** `config.RECEIPTS_LOG` at `config.py:15` points at `receipt_events.ndjson` and is referenced nowhere in tracked source; the real writers build `receipt_events_{firm_id}.ndjson` from `LOGS_DIR` directly, at `app.py:84` and `worker/extraction_pipeline.py:96`. Delete it or wire it up before the intake panel at 8.6 reads these files, because a dead constant with a plausible name is a trap. And `config.RUNS_LOG` is resolved from `LOGS_DIR` at import, so redirecting `LOGS_DIR` alone does not move it. Anything that redirects one must redirect both.

---

## 7. Auth

New dependencies: `argon2-cffi`, and `flask-wtf` for CSRF only. Hand-rolled CSRF is a common source of security bugs and these forms perform destructive writes.

- Session cookie login. No self-signup. Users created by `create_console_user.py`, which prompts for a password and never accepts one as an argument.
- argon2 via `argon2-cffi`, defaults fine. Never store, log or display a password.
- `CONSOLE_SECRET_KEY` from `.env`. **No default, no fallback.** Refuse to start if missing. A hardcoded fallback is a session forgery vector the moment this goes remote.
- `SESSION_COOKIE_HTTPONLY=True`, `SESSION_COOKIE_SAMESITE='Lax'`, `SESSION_COOKIE_SECURE` from config so it can be turned on behind a tunnel without a code change.
- `PERMANENT_SESSION_LIFETIME` 8 hours.
- 5 failed logins per username per 15 minutes, in-memory. Log failures at WARNING, never the attempted password.
- **Deny by default in `before_request`**, not a per-route decorator. A decorator you forget to add is an unauthenticated page.
- `?next=` handling on login, so a deep link to a receipt survives the login redirect.

### 7.1 Roles

| Capability | operator | admin |
|---|---|---|
| View status, queue, browse, receipt detail | yes | yes |
| Correct extracted fields and file | yes | yes |
| Correct GL code | yes | yes |
| Discard a receipt | no | yes |
| Register a client from the intake panel | no | yes |
| Record a credit top-up | no | yes |
| View settings and engine config | no | yes |

Enforce server side in the route. Hiding a button is presentation, not access control.

### 7.2 Config additions

```
CONSOLE_SECRET_KEY=            # required, no default
CONSOLE_BIND_HOST=127.0.0.1    # 0.0.0.0 only behind a tunnel
CONSOLE_PORT=8080
CONSOLE_COOKIE_SECURE=0
OPENAI_ADMIN_KEY=              # optional, Costs API
OPENAI_COST_API_KEY_ID=        # optional, filter costs to this app
RESOLUTIONS_DIR=               # optional override, default IntelliBooks\Resolutions
```

Follow the existing `config.py` pattern. Add every key to `.env.example`. Never commit real values.

### 7.3 Remote access, when needed

Tailscale or Cloudflare Tunnel with Access. Never port forwarding to this workstation. The only code-side change should be `CONSOLE_BIND_HOST` and `CONSOLE_COOKIE_SECURE`. If anything else needs changing, the design has drifted.

---

## 8. Console pages

```
console/__init__.py
console/web.py            Flask app and routes
console/auth.py
console/queries.py
console/costs.py
console/templates/
console/static/
run_console.py
create_console_user.py
```

Name the Flask module `web.py`, not `app.py`, to avoid confusion with the pipeline's `app.py`.

### 8.1 Status page (`/`)

- **Worker health.** Read `config.PIPELINE_LOCKFILE` for `pid` and `started_at`, test liveness with `app.py`'s `_is_process_running()`. **Extract that function to a shared module rather than duplicating it.** Green if the pid is alive and the last run finished within about two poll intervals; amber if alive but stalled; red if no live pid.
- **Last run.** Latest entry in `logs/runs.ndjson`: finished time, duration, per-run stats.
- **Status counts** from the DB: `pending`, `ok`, `needs_review`, `failed`, `possible_duplicate`, `retry_exhausted`, `discarded`.
- **Throughput today** via `repo.count_processed_today()`.
- **Last error** from the most recent run.
- **Billing-blocked banner** when 3.9's classification finds any.
- **Spend**: month to date, cost per receipt, estimated credit remaining.
- **Engine in use**: current engine and model from config.
- **Intake issues** summary, linking to 8.6.
- **Back-feed status**: count of unprocessed notes in `Resolutions\`, and any in `Resolutions\failed\`. A note sitting in `failed` means the DB and the books disagree, which is the one thing this design exists to prevent, so it belongs on the front page.

Do not build this page on `pipeline-status.json`. Read the DB. Leave that file alone; IntelliBooks reads it.

### 8.2 Queue page (`/queue`)

Default filter: `needs_review`, `possible_duplicate`, `failed`, `retry_exhausted`.

Columns: created, client, supplier, gross, status, reason (first validation note), age, and days remaining before the 7-day `AUTO_RETRY_MAX_AGE_DAYS` cutoff. That last column tells the operator what is about to stop being retried.

Rows link to the receipt detail page. Server-side pagination.

### 8.3 Browse page (`/receipts`)

One page, filter bar. Covers both "everything in the last N days" and "everything for a client in a tax year".

| Filter | Behaviour |
|---|---|
| Client | From `list_clients_with_receipts()`, plus "All" and an explicit "Unknown", since `client_id='UNKNOWN'` is a real state. |
| Date basis | Which date the period filter and default sort use: **capture date** (`receipts.created_at`) or **invoice date** (`extractions.invoice_date`). Present it as part of the period control, reading "Period applies to: invoice date". Both dates are always columns. |
| Period | Tax year picker, or last N days with presets 7, 30, 90. Mutually exclusive. |
| Status | Multi-select, default all. |
| Search | `LIKE` against `supplier_name`, `filename`, `receipt_ref_number`. Case-insensitive. |

**Capture date and invoice date are different and confusing them gives wrong answers.** A receipt captured in July 2026 can carry an invoice date in the 2025/26 tax year. Label the chosen basis in the results header, for example "Invoice date between 6 Apr 2026 and 5 Apr 2027". Never default silently to `created_at` while a tax year is selected.

**Tax year filtering must reuse `determine_tax_year()`.** Tax year is not stored anywhere; it is computed at filing time in `worker/filing.py` for the folder path. Do not reimplement the 6 April boundary in SQL and do not add a `tax_year` column. Add a companion `tax_year_bounds(tax_year) -> tuple[str, str]` next to it, have `determine_tax_year()` use it so the two cannot drift, and filter `invoice_date BETWEEN start AND end`.

Receipts with a NULL `invoice_date` cannot be placed in a tax year. Exclude them from tax-year results and show a separate count: "3 receipts excluded: no invoice date". Do not guess.

Columns: received, invoice date, client, supplier, net, VAT, gross, GL code, status, filed. Totals row with count and summed gross for the current filter.

Filters live in the query string so a view is bookmarkable. Server-side pagination. An empty result states what was filtered on and offers to clear.

**This is also the main cross-tool lookup.** From a bank line in IntelliBooks with no receipt attached, the operator searches here by date and amount to find out whether a receipt exists but is stuck.

### 8.4 Receipt detail page (`/receipt/<receipt_id>`)

Rendered from one `ResolutionView`.

1. **Document preview.** Serve from `receipt['file_path']` through a route that validates the path resolves inside `config.FILES_DIR` before opening, and never accepts a caller-supplied path. Look up by `receipt_id` only.
2. **Header.** Client, status, filename, created, source. For `possible_duplicate`, a prominent link to the counterpart.
3. **Side-by-side duplicate comparison** when applicable, highlighting supplier, invoice date, gross, `receipt_ref_number` and `receipt_time`. The last two are exactly what `_signals_differ()` uses, so it shows the operator why the system was unsure.
4. **Correction form.** The seven `CORRECTABLE_FIELDS` prefilled, plus the GL control from section 11, plus a hidden `expected_extraction_id`. Field errors from `parse_corrections`.
5. **Extraction history.** All rows, newest first: engine, extracted at, values, validation status, notes, **`details`**, `pipeline_version`. Read-only.

> **Amended 2026-07-27.** `details` added to that list, and it is not optional. It is the only place the pipeline records an automatic amendment it made to a receipt, per 3.11: which figures it rewrote, which date it overrode, and where it knew the date was ambiguous. Validation notes say what was wrong; `details` says what the system changed. An operator deciding whether to trust an extraction needs both. Display it verbatim rather than parsing it: it mixes the model's own prose with machine-readable notes joined by `; `, and if the console ever needs to act on those notes they should get their own field first.
6. **Resolution events.** Who did what, including `desktop` resolutions arriving via the back-feed.
7. **Actions.** Save and file. Discard, admin only, with a typed reason.

### 8.5 Settings page (`/settings`), admin only

Current engine and model, read-only in phase 1. Credit top-up ledger with an add form. User list. Back-feed folder status with a retry action for anything in `Resolutions\failed\`. **Never render an API key**, not even masked.

### 8.6 Intake panel (`/intake`)

Problems that never become receipt rows, so a DB-only queue is blind to them. `app.py` logs and moves the email on.

| Item | Source | Action |
|---|---|---|
| Pipeline not running or stalled | lockfile, `runs.ndjson` | none, informational |
| Files waiting in Receipt Inbox | filesystem count under `RECEIPT_INBOX_ROOT` | none |
| Unknown senders | `email_alerts` where `alert_type='unknown_sender'` | **Register this client** |
| No-attachment alerts | `email_alerts` where `alert_type='no_attachment'` | none |
| Unsupported file types | `logs/receipt_events_*.ndjson`, action `unsupported_file_type` | none |

**Register this client** is the one that earns its place, and it needs care. `config.CLIENTS` is loaded once at import (`config.py` line 100), so appending a row to `clients.csv` does not reach the running pipeline. Two parts:

- Append the row to `clients.csv` in OneDrive, admin only, with validation that the email and client code are not already present.
- Provide a **reload** mechanism so `app.py` picks it up without a restart. Simplest correct approach: the console writes a small marker, and `app.py` calls `config.load_clients()` again at the top of each `process_once()` if the marker is newer than the last load. Do not add a signal handler or an IPC channel.

Note the unknown-sender email itself has already been moved to `INBOX.Unknown Sender` and no receipt row exists, so registering the client does not retroactively process it. The client must resend. Say so in the UI.

### 8.7 Presentation

Server-rendered Jinja2, plain CSS, no framework, no build step. Vanilla JS only where it earns its place. Must be implementable in one pass and readable cold.

---

## 9. Cost and credit monitoring

### 9.1 What is available

The Usage API and Costs API (`GET /v1/organization/costs`) are official and documented, return spend bucketed by day, and support `group_by` on `project_id`, `line_item` and `api_key_id`. They require an **Admin key**, which is a different credential from `OPENAI_API_KEY`.

There is **no documented endpoint for remaining prepaid credit balance.** Do not build anything depending on `/v1/dashboard/billing/credit_grants`; it is undocumented, has historically needed a session token, and has broken repeatedly.

### 9.2 Local token ledger, build first

`openai_vision.py` keeps only `response.choices[0].message.content` (line 82) and discards `response.usage`.

1. Add optional `prompt_tokens`, `completion_tokens`, `model` to `ExtractionResult` in `worker/extraction/base.py`, defaulting to `None`.
2. Populate them in `OpenAIVisionExtractor.extract()` from `response.usage`, guarded with `getattr`, since a failed or mocked call may not carry usage.
3. Add `MODEL_PRICING` to `config.py` as model to input and output price per token, with a comment pointing at `platform.openai.com/pricing`. **Confirm current prices at implementation time. There are deliberately none in this document.** Unknown model: store tokens, leave `estimated_cost_usd` NULL.
4. Add `repo.save_extraction_usage()` and call it immediately after each `save_extraction()` where usage exists. Call sites: `worker/extraction_pipeline.py` line 160, and the failure paths in `app.py` around 494, 527, 706 and 877. Manual corrections have no usage.

This gives cost per receipt, per day and per client. The Costs API cannot give cost per client, because only the DB knows which client a call belonged to. That is the number to price the service on.

### 9.3 Costs API

`console/costs.py` polls `/v1/organization/costs` once a day, or on demand from Settings, and caches into `openai_cost_daily`. Filter by `api_key_id`, which means issuing a dedicated OpenAI key or project for this app and putting its id in `OPENAI_COST_API_KEY_ID`.

Never call OpenAI on a page load. Read the cache, show `fetched_at`, offer a manual refresh. If the Admin key is absent, degrade to local-ledger figures and say so. Do not fail the page.

### 9.4 Remaining credit

Show as an **estimate**, labelled as one: `openai_credit_topups` minus spend since the earliest top-up, preferring Costs API figures and falling back to the ledger. Do not present it as authoritative.

The real protection against running out is OpenAI's own auto-recharge and billing threshold alerts, configured in their dashboard. Note that in `RECEIPT_CAPTURE_GUIDE.md` as an operational setup step.

---

## 10. Provider factory, phase 1 subset

**10.1 `worker/extraction/factory.py`**

```python
_REGISTRY = {"openai_vision": OpenAIVisionExtractor}

def get_extractor(name: str | None = None) -> BaseExtractor: ...
def available_engines() -> list[str]: ...
```

Add a `name` property to `BaseExtractor`. Replace `extractor = OpenAIVisionExtractor()` in `app.py` line 406 with `get_extractor()`. Replace the hardcoded engine strings per 3.8.

> **Amended 2026-07-26.** The `name` property is already built, in `117fb1b`. It landed with step 1 rather than here, because the auto-retry exception fix needs the engine identity and had no `ExtractionResult` to read `.engine` from. It is an **abstract** property on `BaseExtractor`, concrete on `OpenAIVisionExtractor`, so any future extractor must declare it. What remains for step 7 is the factory itself and the three hardcoded `engine="openai_vision"` strings at `app.py` lines 530, 709 and 880.

**10.2 Move post-processing out of `openai_vision.py`**

`_parse_ambiguous_date`, the `PREFER_DAYFIRST` logic and the VAT-inclusive-total swap live inside `openai_vision.py` lines 98-214. A second provider would silently not inherit any of it, so the day-first and VAT fixes would stop applying the moment the engine changed.

> **Corrected 2026-07-27.** "Lines 98-214" was eleven lines too early: line 98 is the `except json.JSONDecodeError` of the JSON parse, which is not post-processing and stayed put. The actual boundaries at `96a5c5a` were **109-149** for `_parse_ambiguous_date`, **151-184** for the VAT swap and **186-218** for the date resolution. Recorded because the next person may use the range to check the move was complete and wrongly conclude something was left behind.
>
> **Built 2026-07-27 in `bf1976d`**, with `tests/test_postprocess.py`. Acceptance criterion met: `tests/test_date_disambiguation.py` and `tests/test_vat_swap.py` are untouched, confirmed by an empty `git status` on both and by the commit touching only three files, and they pass on their own. The move was verified mechanically rather than by reading: 82 code lines out, 87 in, 11 differing once whitespace and comments are ignored, and all 11 are structural. Three `def` lines, two `return` statements because the old blocks mutated `extract()`'s locals, `config.PREFER_DAYFIRST` becoming the `prefer_dayfirst` parameter and its internal call site, and a module-level `from datetime import date`.
>
> **Seven defects were found by reading the code closely during the move. None was fixed, because a move that fixes things is not a move.** Recorded here so they are not lost. Two are worth acting on and are the subject of the decision in 17.4.
>
> 1. **The `ambiguous_invoice_date_no_raw` note lies when a raw string was present but unparseable.** The guard is `if not parsed_from_raw and invoice_date`, which is true both when there was no raw string and when there was one that failed to parse. Confirmed by calling `resolve_invoice_date("2026-05-09", "2026-05-09", None, True)`, which returns the note `ambiguous_invoice_date_no_raw(model_iso=2026-05-09)` with a raw string plainly present. This is the field an operator reads to decide whether to trust the date, so a wrong label is worse than no label.
> 2. **An ISO-shaped `invoice_date_raw` silently defeats the whole deterministic path.** `parse_ambiguous_date("2026-05-09", ...)` splits to `2026, 5, 9`, normalises the year to 2009 because the third part is under 100, then fails both branches and returns `None`. Confirmed empirically, both values of `prefer_dayfirst`. So for a receipt that prints its date in ISO form, and whose raw string the model therefore returns in ISO form, the day-first fix does not apply and the receipt falls through to the ambiguity annotation. It fails safe and it fails silently, which is the worst combination for a fix nobody will think to re-test.
> 3. **Two-digit years always resolve to the 2000s.** `01/01/99` becomes 2099, not 1999. Fine for current receipts, wrong for a historical document, and there is no note.
> 4. **The `elif c < 1000` branch is dead and its comment is false.** Identical body to the branch above it, and the comment says "treat as 2000s" where `2000 + 999` is 2999.
> 5. **The 0.03 VAT tolerance is absolute, so it is proportionally far looser on the reduced rate.** It accepts 17 to 23 per cent for standard rate, sensible, and 2 to 8 per cent for reduced rate, which is 60 per cent wide either side. Not a bug today. It matters before anyone adds a third rate.
> 6. **The broad handlers now swallow silently in a module a second provider inherits.** There are three `try/except Exception: pass` blocks, one nested, and `postprocess.py` has no logger at all, confirmed by grep. In `openai_vision.py` a failure there was at least adjacent to code that logs. Here, a genuine `TypeError` from a shape the next provider returns produces no line in `data/run.log`, no note in `details`, and an extraction that looks as though it simply had nothing to correct. A `logger.warning(..., exc_info=True)` in each changes nothing on the happy path.
> 7. **Both existing test files set `config.PREFER_DAYFIRST = True` in `setUp` and never restore it**, leaking module state to every test that runs afterwards. Harmless today only because `True` is also the default at `config.py:41`. It is the same class of problem `tests/test_logs_isolation.py` exists to prevent, and it could not be fixed during this step because those two files had to stay unmodified.

Move to `worker/extraction/postprocess.py`. **A pure move: behaviour must not change and the existing tests must pass unmodified.** If a test needs editing, something was changed that should not have been.

**10.3** Status page displays the current engine and model. No switching control in phase 1.

> **Amended 2026-07-27, built in `71fe757`.** This section never said where `get_extractor(None)` takes its default from. It is now `config.EXTRACTION_ENGINE`, an environment variable in the existing `config.py` style, defaulting to `openai_vision` and documented in `.env.example`. Not the phase 2 `settings` table. `get_extractor()` refuses an unregistered name and its message says whether the bad value came from the argument or from config, which matters when the answer is a typo in a `.env`.
>
> **So the status page reads `config.EXTRACTION_ENGINE`, and when the phase 2 `settings` table arrives the table wins.** Recording that now, because two sources of truth for "which engine is running" that can disagree is exactly the shape of bug this section exists to prevent. The switch-over must move the read, not add a second one.

Phase 2, not now: the `settings` table, switching from the UI, and making `pipeline_version` a composite of git hash, engine and model. Without that composite key, switching provider will **not** cause `find_failed_by_version()` to re-attempt existing failures under the new engine, which is the main reason to switch. It needs its own regression test against the retry-cap boundary.

---

## 11. GL correction

### 11.1 Where the code options come from

The **Default CoA CSV**, loaded into `coa_accounts` with `scope='default'`. A draft generated from the live vendor mappings is at `chart_of_accounts_DRAFT.csv` in this repo; Paul extends it with income, equity and remaining balance sheet accounts.

`list_gl_code_options(client_id, business_type)` returns active accounts for `scope='default'` in phase 1, ordered by frequency of use in that client's vendor mappings, then by code. Allow free-text entry for a code not yet in the CoA, and record it in the notes so it can be promoted later.

**If the CSV is absent**, fall back to distinct `(nominal_code, account_name)` pairs from the vendor tables so the console still functions. Show a banner saying the CoA has not been loaded.

### 11.2 How the override is applied

`repo.update_categorisation(categorisation_id, correction_code, correction_name, correction_reason)` exists, sets `corrected_at`, and is currently called by nothing.

Ordering matters. `resolve_receipt.py` line 323 builds the sidecar with `categorisation.suggested_code`. Apply the override after filing and the sidecar on disk disagrees with the DB permanently. So:

1. `save_categorisation()` with the engine's suggestion. Never overwrite `suggested_code`; that is the audit trail.
2. `update_categorisation()` with the override.
3. Build the sidecar with the **effective** code and name.
4. `file_receipt()`.

The effective-code rule applies anywhere a category is read for output. **Check `export_bookkeeping.py` during implementation and report whether it needs the same treatment. Do not change it silently.**

### 11.3 Feeding corrections back into the mappings

`repo.upsert_client_vendor()` exists. Offer it as an **explicit opt-in checkbox**, "Remember this code for future receipts from this supplier", default off.

Do not learn automatically. One correction against a possibly misread supplier name would poison the client mapping table, and the engine's layer 2 exact match would then confidently apply the wrong code to every future receipt from that vendor.

Record the choice in `resolution_events.corrections_json`.

---

## 12. The resolution back-feed contract

**This is a two-sided contract.** The IntelliBooks half is specified in `PROMPT_intellibooks_resolution_backfeed.md` and built in a separate session. Both halves must match this section exactly.

### 12.1 Why it exists

`IntelliBooks-System-Specification.md` section 4.3 states that corrections made in Desktop are the practice's decided truth, with no back-feed in Phase 1, and change log item 19 implemented that deliberately. Three pipeline features built afterwards break under that rule:

- **Auto-retry on `pipeline_version`** re-extracts anything the DB still marks `needs_review`.
- **Duplicate protection keyed on `filed_path IS NOT NULL`** is blind to Desktop-filed receipts.
- **Vendor learning** never sees a category corrected in Desktop.

The rule was coherent while the pipeline was fire-and-forget. It no longer is. The back-feed keeps the rule's letter intact: Desktop still never writes `receipts.db`. It writes a note; the pipeline writes the DB.

### 12.2 Location and format

`{practice root}\IntelliBooks\Resolutions\`, override via `RESOLUTIONS_DIR`. Filename `{receipt_id}_{unix_ms}.json`.

> **Amended 2026-07-28 to what Desktop actually writes.** Superseded wording is the line above. The key is the `receipt_id` **when the review sidecar carried one**, and otherwise the review image name with its extension stripped and any character outside `[A-Za-z0-9._-]` replaced by `-`. A note may legitimately carry a null `receipt_id`, so the original wording described a filename that could not always be built. `unix_ms` is derived from `resolved_at` rather than a second clock read, so the name and the idempotency key can never disagree. **Nothing may parse meaning out of this filename.** The pipeline uses it for sort order only, and that is the whole contract it carries.
>
> **`Resolutions\` sits inside OneDrive, and that is an assumption rather than a property of the design.** Fine while Desktop and the pipeline run on one machine, which they do. On two, sync latency and conflict copies named `file-DESKTOP-ABC.json` become the pipeline's problem: `glob("*.json")` would pick them up and apply them. Raised by the IntelliBooks session on 2026-07-28. Revisit before anything here runs on more than one machine, and carry it into the AWS design.

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
  "original_review_files": ["...png", "...png.review.json"]
}
```

- `action` is `filed` or `discarded`. For `discarded`, `values` and `filed_path` are absent.
- `receipt_id` may be `null` if the review sidecar lacked one; then `original_review_files` is used for a filename match.
- `filed_path` is relative to the practice root, backslashes.
- `category_name` is a **name**, not a code. Desktop has no codes.
- Amounts are numbers. Absent rather than null or empty string.

> **Corrected 2026-07-28, and this is the most important line in this section for the IntelliBooks session.** "Absent rather than null" is not what Desktop does. `IntelliBooks-Desktop-v3.html:1787` writes `net: isNaN(net) ? null : Math.abs(net)`, so a receipt with no net emits `"net": null`. A consumer built to the letter of this section would reject real notes for real receipts. **An explicit `null` must be accepted and read as "no value", exactly as an absent key is.** The pipeline half already does. Either Desktop stops emitting null or this line stops forbidding it, and since Desktop's behaviour is the one already shipped, this line changes.

### 12.3 Pipeline consumer

Runs at the start of `process_once()`, before `_retry_failed_receipts()`, so a resolved receipt is never retried in the same cycle it was resolved.

For each `*.json` in `Resolutions\`, oldest first by filename:

> **Clarified 2026-07-28.** The filename is `{receipt_id}_{unix_ms}.json`, so sorting by name sorts by receipt id first and by time second. That is **not** global time order across receipts, and it does not need to be: what sequencing requires is that two notes for the same receipt are applied in the order they were written, which this gives. Stated because "oldest first" reads as a global guarantee and is not one.

1. Parse. On failure, move to `Resolutions\failed\` with a `.error.txt` alongside, log at ERROR, continue. **Never delete.**
2. Resolve the receipt: by `receipt_id`, else by matching `original_review_files` against `receipts.filename`. Not found: move to `failed\`, log, continue.
3. **Idempotency.** If a `resolution_events` row already exists for this receipt with the same `resolved_at`, treat as already applied, move to `processed\`, continue.
4. Call `apply_resolution_note()` with `actor='desktop'`, `source='desktop'`.

> **Corrected 2026-07-28.** Superseded wording: "which calls `resolve_receipt()` or `discard_receipt()`". That contradicted step 5, which requires the filed path to set `filed_path` directly and explicitly not to route through `resolve_receipt()`. Both could not be true. **Step 5 wins**, and what is built is: a `discarded` note goes through `discard_receipt()`; a `filed` note does **not** go through `resolve_receipt()` and has its own path. The IntelliBooks session needs to know that, because it is the difference between one copy of a receipt and two.
5. Special handling for a `filed` note: the file already exists at `filed_path`, so **do not re-file it**. `apply_resolution_note()` must set `filed_path` directly via `mark_receipt_filed()` rather than calling `file_receipt()`, write the `manual_correction` extraction row, categorise, and set status `ok`. This is the one place where the resolution flow diverges from the console path, and it must be explicit rather than a flag threaded through `resolve_receipt()`.
6. `category_name` to code: look up the name in `coa_accounts`. Found, store the code. Not found, store the name only, add a validation note. Until the Default CoA is loaded this is always the second case, which is expected and not an error.

> **Corrected 2026-07-28.** Superseded wording: "Found, store the code **and learn the vendor mapping**", and "skip learning" on the not-found branch. That contradicted 11.3, which says never learn automatically, because one correction against a possibly misread supplier name poisons the client mapping table and the engine's exact-match layer then applies the wrong code confidently to every future receipt from that vendor.
>
> **11.3 wins: a back-feed note never learns a mapping.** 11.3 is a reasoned decision with a stated failure mode, and the learning clause here was an oversight. A note is also the least qualified source to learn from: it carries a category name chosen from a dropdown in another application, with no confidence attached and no record of how sure anyone was. Learning stays opt-in from an operator who ticked a box, per 11.3, and nothing else.
7. On success, move the note to `Resolutions\processed\`. Never delete.

### 12.4 Reverse direction needs nothing

When the console resolves, it files to `Clients\{Name}\Receipts\{tax year}\` and IntelliBooks' item 21 auto-scan imports it. The only requirement is that the console removes the Review pair, per 3.5, or the item lingers in Desktop's list.

> **Amended 2026-07-27, read before building step 10. Desktop writes its own sidecar when it files, and it deletes the Review pair itself.** Read from `IntelliBooks-Desktop-v3.html` lines 1770 to 1797. This was not recorded anywhere.
>
> Its filing flow copies the image to `Clients\{name}\Receipts\{taxYear}\{date}_{supplier}_{gross}{ext}`, using the same `-2`, `-3` uniqueness convention as the pipeline's `_unique_path()`, writes a sidecar at `{filed}.json`, and only then removes the review image and the review json. On any error it toasts "Filing failed, nothing was deleted". That is careful code and nothing needs changing in it.
>
> **The sidecar it writes is a different shape from `make_enriched_sidecar()`:**
>
> ```
> receipt_id, client:{code,name}, source, invoice_date, supplier,
> net, vat, gross, currency, category, validation_status,
> corrected_by:"desktop", corrected_at, original_filename, pipeline_receipt_id
> ```
>
> Differences that matter. `client` is a **nested object** where the pipeline writes flat `client_code` and `client_name`. There is no `confidence`, no `capture_date`, no `asserted`, no `claimed_client_code`, and after step 5 no `category_code` or `category_name` either. `category` is a name, because Desktop has no codes. Amounts are passed through `Math.abs()`, and `net` and `vat` become `null` when not a number. It adds `corrected_by` and `corrected_at`, which the pipeline's shape has no equivalent of.
>
> This explains the two sidecars on disk carrying `"category": "Parking and tolls"` with no `confidence` key, see 3.7. They were filed through Desktop.
>
> **Two consequences for step 10.** First, `remove_review_pair()` will find nothing when a Desktop note is consumed, because Desktop already deleted the pair. That is handled: already-gone logs at INFO and returns 0, per 3.5. No action, but do not treat a zero return as a failure. Second, and this needs a decision: 12.3 step 5 forbids re-filing, so **Desktop's sidecar stays on disk as the sidecar of record for that receipt**, and two shapes will coexist across a client's Receipts folder. Desktop itself copes, because `parseSidecar()` at line 1141 reads both its own and the enriched pipeline shape. Anything on the pipeline or console side that reads a filed sidecar will not, unless it is written to tolerate both. The options are to leave both shapes and make every reader tolerant, or to have `apply_resolution_note()` rewrite the sidecar into the pipeline shape after recording the filing. Rewriting is a write into a folder Desktop has just written to, so it is not free. ~~**Paul decides at step 10, and 17.4 carries the question.**~~
>
> > **Decided 2026-07-28: leave both shapes and make every reader tolerant.** Paul's call. `apply_resolution_note()` does not rewrite the sidecar, which is what it already does, so nothing changes in the built code. The rule this creates, and it is now binding on step 16 and on anything later that reads a filed sidecar: **read the writer from the discriminator, never guess from the fields.** `corrected_by` present means Desktop wrote it; `capture_date` present means the pipeline did. Neither present is a pre-step-5 file and gets no special handling beyond not crashing.
> >
> > Why this over rewriting. Rewriting buys one shape on disk, and pays for it with a write into a folder Desktop has just finished writing to, a new failure mode on a path whose whole purpose is that it does not touch files it did not create, and a rewrite that would have to run on every Desktop resolution for ever. The only thing it saves is tolerance in readers, and there are no such readers yet. Tolerance is also testable in isolation; a rewrite is only testable end to end.
>
> Two facts that make that decision cheaper than it looks, both confirmed in the source. **Desktop's reader already copes with the new format.** `parseSidecar()` at line 1141 reads `category` and tolerates three forms: a plain string, an object with a `.name`, or `asserted.category`. Because step 5 keeps the legacy `category` key populated with the **name**, sidecars written by the pipeline from now on are read correctly by Desktop with no change to Desktop at all. The `parseSidecar` change in `PROMPT_intellibooks_resolution_backfeed.md`, preferring `category_name`, is therefore an improvement and not a prerequisite. Worth knowing before that session is scheduled.
>
> **And the two shapes are cleanly distinguishable without guessing.** `corrected_by` appears only in Desktop's sidecar; `capture_date` appears only in the pipeline's. Either key identifies the writer, so "make every reader tolerant" is a small, testable rule rather than an open-ended one.
>
> One more thing that follows from `catOptions()` at line 1429, and it is the direct evidence for 3.7 rather than an inference: the category select is built as `<option>` elements from `books.categories` **names only**, and the selected-match test at line 1431 is on `c.name`. A nominal code in that field cannot match anything, by construction.

> **Confirmed live 2026-07-28.** Change log item 19 was tested end to end for the first time, on receipt `c5a3fccd`. It works: the four form validations behave, the image and sidecar are written to `Clients\Test\Receipts\2026-27\`, the books entry carries the corrected figures, and Desktop removed the Review pair itself. The sidecar Desktop wrote is exactly the shape predicted from the source, which means the discriminator holds: `corrected_by` present, `capture_date` absent.
>
> **Five details from the real file that step 10 must handle, none of which were visible from reading the code.**
>
> 1. **`"category": ""`, an empty string, not null.** Desktop does not require a category before filing, so the common case is an empty string. 12.3 step 6 looks `category_name` up in `coa_accounts`; an empty string must be treated as "no category" and skipped, not looked up and not stored as a name. A blank category in a books entry is also an accounting gap in its own right, see 17.4.
> 2. **Amounts arrive as JSON integers where they are whole.** The real file has `"net": 80, "vat": 16, "gross": 96`, because JavaScript drops the trailing `.0`. 12.2's "amounts are numbers" is satisfied, but the consumer must coerce rather than assume a decimal point, and must not reject an int as malformed.
>
>    **Two decimal places, ruled by Paul 2026-07-28.** An amount is a money value and must read as one: 80.00, never 80 or 80.0. Three parts to that, and only the middle one is a real change.
>
>    *On the wire, amounts stay JSON numbers.* `JSON.stringify` cannot emit `80.00` for a number, so the only way to get two decimals into the file is a string, and 12.2 forbids strings for exactly the reason bug 3.3 exists: string amounts reached `validate()` and raised `TypeError` on `round()`. Do not change the note format.
>
>    *On ingest and on storage, round to two decimal places.* `round(value, 2)` as the note is parsed, before anything is written. This is the change: nothing currently guarantees it, and `parse_corrections` rejects more than two decimals from an operator while the pipeline accepts whatever the extractor returns.
>
>    *On every output, format to two decimal places.* `f"{value:.2f}"` for the console, the CLI and any export. Both filename builders already do this, `worker/filing.py:83` and `IntelliBooks-Desktop-v3.html:1769`, which is why this receipt filed as `_96.00`. The older files in that folder showing `_4.5` and `_8` predate it and are evidence of what happens without the rule.
> 3. **`"client": {"code": "TEST", "name": "TEST"}`.** Desktop wrote the code into the name. `clients.csv` has the name as `Test` and the folder is `Clients\Test\`. Harmless here because the folder path came from Desktop's own client record, but the two tools do not agree on a client's name, so the consumer must never use the note's `client.name` to resolve a path. Match on `receipt_id`.
>
>    > **Corrected 2026-07-28. The mechanism above is wrong; the instruction is right.** Superseded wording: "Desktop wrote the code into the name". It does not. `IntelliBooks-Desktop-v3.html:1786` writes `client:{code:c.code,name:c.name}`, the real name. What is actually true is worse: **the two registries hold different names for the same client.** `IntelliBooks-Practice.json` has that client as `{"name":"TEST","code":"TEST"}` and `clients.csv` has `Test`, so `c.name` genuinely is `TEST`. I inferred a writer bug from a filed sidecar and there is no writer bug. Flagged by the IntelliBooks session, confirmed against both registry files. So "never resolve a path from the note's `client.name`" stands, for a better reason, and this is the Registry sync open item arriving early.
>    >
>    > **The consequence nobody had, and it matters more than the correction. Confirmed live by test 41 on 2026-07-29**, where the filed receipt's `filed_path` in the database reads `Clients\TEST\Receipts\2026-27\2026-07-24_PENNINE-CAFE-&-BAKERY_27.00.png`: `Clients\TEST\` rather than `Clients\Test\`, and the supplier not lowercased, both as predicted. Desktop builds `filed_path` from `safeName(c.name)`, so it writes `Clients\TEST\Receipts\...`, while the pipeline files the same client to `Clients\Test\` from the `clients.csv` name. `resolve_practice_path()` then calls `target.exists()`, which returns true on Windows because NTFS is case-insensitive. **So test 41 passes for the wrong reason.** On S3, or on Linux, `Clients\TEST\` and `Clients\Test\` are two folders and every Desktop note would land in `failed\`. This is a latent cloud-migration defect, recorded now while it is cheap. It is not fixed here: the fix is registry sync, which is a Phase 2 item, and a receipt-side patch would hide it.
> 4. **`"source": "folder"`**, carried through from the pipeline's own value, not overwritten with `"desktop"`. So `source` describes how the receipt arrived, and `corrected_by` describes who resolved it. Do not read `source` as the actor.
> 5. **The filed filename is `2026-07-21_MARLOW-TRADE-SUPPLIES-LTD_96.00.png`.** Desktop does not lowercase the supplier; the pipeline does. So the two tools produce differently cased filenames for the same receipt. Cosmetic, no accounting consequence, and not worth changing either side, but anything that ever matches a filed receipt by filename must be case-insensitive.

---

## 13. Chart of accounts module, specified not built

Reserved so module 1 does not need reworking. `coa_accounts` (5.5) is created in phase 1 with `scope='default'` populated.

**Three tiers.** Default, then Client group, then Client. Resolution runs client, then group, then default: the same fallback the categorisation engine already implements for vendor mappings, where the group tier is `business_type`.

**Group and entity type are orthogonal.** Group drives the CoA template and vendor mappings. Entity type drives the tax mapping, because "Motor expenses" maps to a self assessment box for a sole trader and a corporation tax line for a company. The mapping is `(account, entity_type) → target`.

**Provenance, not restriction.** No account is precluded. Every account records where it came from: inherited from default, inherited from group, added for this client, or imported with the client.

**Three statuses.** `active`, `not_adopted` (inherited but unwanted, keeps pickers clean), `archived` (was in use, retired, `maps_to_code` retained so history can be restated).

**Import as proposal, not permissive.** Nothing enters a client CoA until dispositioned. Four dispositions per imported account: match to an existing account, add as client-specific, archive, or **promote to group or default**. That fourth is how the default improves from real client data.

**Output includes the old-to-new mapping,** not just the new CoA. Without it a client's history cannot be restated and comparatives stop tying.

**Two AI jobs, not one.** Normalising an imported CoA is a matching problem, verifiable line by line, and is the same fuzzy-plus-LLM technique the vendor matcher already uses at a 70 percent threshold. Interviewing the client's circumstances to propose accounts is a judgement problem. Build the first one first.

**The interview is a versioned structured question set,** not a free-form chat: a core set everyone answers plus a branch per client group. Every proposed account carries a reason. The answers are saved, so next year's run starts from last year's answers.

**Transaction evidence beats the interview** where it exists. An account with three years of activity is needed; one with nothing in two years is a candidate to archive; a cluster in "Sundry" is a missing account. That needs counting, not AI.

**Export adapters are phase 2 or 3.** For now the output is a CSV and importing it into QBO, Xero or FreeAgent is manual. Known constraints when that work starts: QBO requires Account Name, Type and Detail Type with Detail Type constrained by Type; Xero needs a template from the specific organisation and its TaxType values must already exist there or the account silently defaults to Tax Exempt at 0%; FreeAgent is not a CoA import target at all, since its structure is rigid and its import is of opening balances matched by category name.

**Already built in IntelliBooks, do not duplicate:** SA103F cash-basis HMRC box mappings on every income and expense category, per-client year end, MTD flag, quarter basis, and the HMRC Summary Export (change log item 8). The five-type taxonomy and optional hierarchical names exist too (spec 5.4 item 4). What the category model lacks is only a **code**.

> **Amended 2026-07-28, and this is now the strongest concrete argument for building this module.** Read from `IntelliBooks-Desktop-v3.html`, with three requirements from Paul.
>
> **A category has no identifier of any kind.** `addCategory()` at line 1990 pushes `{name, type, hmrc}`. The name is the primary key, and every reference to a category anywhere in the books is a copy of that string: `t.category` on a transaction, `r.category` on a receipt, and `category` on a statement rule.
>
> **Requirement 1: a rename must carry through to everything linked to it.** Today it cannot, because the link is the name itself. The saving grace is that **there is no rename feature**: no code anywhere writes `c.name`, so a category can only be added or deleted. So nothing is broken today, and the risk arrives the moment somebody adds a rename before codes exist. **Adding codes is therefore a prerequisite for renaming, not an improvement to it.**
>
> **No migration of existing references is needed**, per Paul 2026-07-28: every books entry on disk is test data and will be cleared before real use, so codes can be designed cleanly rather than retrofitted. See 17.5 for what the reset must and must not touch.
>
> **Requirement 2: a category must not be deletable while anything is linked to it.** Partly true today, and the gap matters. `delCategory()` at line 1997 checks `books.transactions.some(t => t.category === c.name)` and refuses if any transaction uses it. It does **not** check receipts, and it does **not** check statement rules. So a category can be deleted while a rule still assigns it, and `applyRules()` will then keep writing a category that no longer exists onto future transactions. The guard needs to cover all three reference types. Note also that `addCategory()` compares names case-insensitively while `delCategory()` compares them case-sensitively, so a reference differing only in case does not block deletion either.
>
> **Requirement 3: manual categories are never overwritten by the rules.** Already true, `applyRules()` at line 964 skips any transaction that already has a category. Confirmed as intended behaviour, so do not change it.
>
> Together these mean the CoA module is not only about a richer chart. It is what makes a category a thing with an identity rather than a string that happens to match, and until then rename is impossible and delete is only partly guarded.

---

## 13A. File reconciliation

Inserted 2026-07-29, using the same lettered convention section 16 already uses for inserted steps. It replaces the folder locking asked about in amendment 56, which is not achievable here.

### 13A.1 What it is for

The managed client folders acquire files nobody in this system put there. Four ways, and only the first is a mistake anyone would notice:

- a receipt dropped straight into `_Receipts\{tax year}\` by hand, which the pipeline never sees at all and Desktop degrades to `img_{filename}` with a gross of 0
- a OneDrive conflict copy, `file-DESKTOP-ABC.ext` or `file (1).ext`, which OneDrive creates itself and no permission scheme prevents
- a half-written or half-synced pair, where the image landed and the sidecar did not
- a receipt filed by a tool before the back-feed existed, so the file is on disk and the database still calls it `needs_review`

Each of these is a **quiet** disagreement between the disk and the database. Nothing currently notices any of them. The 23 ghost receipts found across the books files on 2026-07-29 sat there for weeks.

### 13A.2 What it must not do

**Read-only. It never moves, renames, deletes or repairs anything, on any path.** A check that fixes what it finds is not an audit, and the first thing it would "fix" is a file a human deliberately put somewhere. It reports, and a person decides.

It also does not run on every poll. Walking every client's receipt folders across OneDrive is not free, and nothing here is urgent to the minute: a file that should not be there this morning will still not belong this evening. On demand from a CLI, once a day from the pipeline, and read from a cached result by the console.

### 13A.3 The checks

Against the managed tree only, meaning `Clients\*\_IntelliBooks\` and its four subfolders per amendment 55. Anything elsewhere in a client folder is the client's or another tool's and is none of this system's business.

| # | Finding | Rule |
|---|---|---|
| 1 | `unpaired_media` | An image or PDF in `_Receipts\{tax year}\` with no `{full filename}.json` beside it. The manual-addition case. |
| 2 | `unpaired_sidecar` | A `*.json` in `_Receipts\{tax year}\` whose media file is missing. A half-synced or partly deleted pair. |
| 3 | `sidecar_unknown_to_db` | A filed sidecar carrying a `receipt_id` with no row in `receipts`. Something filed outside the pipeline. |
| 4 | `filed_path_missing` | A receipt row with `filed_path` set and nothing at that path. The reverse of 3, and the more serious direction: the database asserts a document exists and it does not. |
| 5 | `conflict_copy` | Any name in the managed tree matching OneDrive's conflict shapes, `*-DESKTOP-*`, `*-LAPTOP-*`, `* (1)` through `* (9)`, or `*-Copy`. |
| 6 | `review_pair_orphaned` | A `_Review\` pair whose `receipt_id` has no row, or has a row whose status is not one of the review statuses. |
| 7 | `review_pair_missing` | A receipt in `needs_review` or `possible_duplicate` with no pair on disk. The operator is told to look at something that is not there. |
| 8 | `books_file_unregistered` | A `*-books.json` in `IntelliBooks\Books\` with no matching client in `clients.csv`. Desktop's territory rather than the pipeline's, but the pipeline can see it and it is the same class of fault. `PKPH-books.json` was found this way. |

Findings 3, 4, 6 and 7 are the ones that mean the two records disagree. 1, 2, 5 and 8 are files in the wrong state. Report them as two groups, because they need different responses: the first group is investigated, the second is tidied.

### 13A.4 Matching, and the trap in it

Pair a sidecar to its media by the **full filename plus `.json`**, which is what both tools write: `2026-07-24_X_27.00.png` pairs with `2026-07-24_X_27.00.png.json`.

Do not derive the pair by stripping the extension. That is exactly the bug in Desktop's `ingestReceiptFiles()`, which keys images with the extension removed and then looks them up with it present, so nothing ever matches and every filed receipt is ingested twice. Tolerate the older `{stem}.json` shape on read, since files in that form may exist, but never generate it and never treat it as the primary rule.

All filename matching is **case-insensitive**. Desktop leaves a supplier as typed and the pipeline lowercases it, so the two tools produce differently cased names for the same receipt.

### 13A.5 Output

A JSON file at `data/reconciliation.json`: the timestamp, the counts per finding, and the findings themselves with a path and a one-line reason each. Written whole, never appended to, so the console reads the last complete run rather than a partial one.

The CLI prints the counts and, with a flag, the detail. The console status page at 8.1 reads the file and shows a single line, the total and how old the run is, linking to the detail. **A stale result must say so rather than reporting zero**, because "nothing found" and "not checked since Tuesday" are different facts and only one of them is reassuring.

### 13A.6 Why it is built before the reset

17.5 requires the clean-slate reset to be verified before and after each stage rather than once at the end. This check is the instrument for that: run it before the first deletion to record what is there, and after each stage to confirm only what was intended went. Building it afterwards would mean supervising the reset by hand and then writing the tool that would have supervised it.

It should also be run once against the current state before anything is cleared, because that state is the best test data it will ever have: a books file with no client, filed receipts of three different vintages including names predating the two-decimal rule, and whatever else is in there. A check that finds nothing wrong today is a check that does not work. Note what it cannot see: the 23 ghosts are books entries, not files, so a clean receipts result says nothing about the books.

---

## 14. Explicitly out of scope

Each a deliberate deferral.

- Provider switching from the UI, the `settings` table, and the composite `pipeline_version`. See 10.3 for the trap.
- Mailbox folder sync after resolution. Parked. When picked up: a `pending_mailbox_moves` table written by the service and drained by `app.py`, which already holds an IMAP connection. Do not give the console IMAP credentials.
- The CoA module, section 13.
- CoA export adapters for QBO, Xero and FreeAgent.
- Category conflict resolution when a receipt is matched to a bank transaction. Agreed shape: the receipt wins when its categorisation confidence is high, the statement rule wins when it is low, and the disagreement is flagged either way. It must not auto-update the rule (change log item 2). Needs the shared vocabulary first, and it lives in IntelliBooks.

> **Read 2026-07-28, so this is now what the code does rather than what we assumed it does.**
>
> **The pipeline does not categorise transactions, only receipts.** `categorise()` is called from four places and all four are receipt paths: `app.py:187`, `worker/extraction_pipeline.py:191`, `worker/resolution/service.py:433` and `retroactive_categorise.py:133`. The one call against transactions is `docs/specs/categorisation_engine.py:423`, a prototype in `docs/` that is not live code. The engine was clearly designed to handle both, its own helper is documented as normalising a "bank/receipt description", but the shipped pipeline never sees a bank transaction. The `statements` table is platform statements, Uber-style weekly files, not bank lines.
>
> So there are two categorisation systems that never meet. **The pipeline categorises receipts** into `categorisations`, as a nominal code plus an account name, from the vendor mapping tables keyed on a normalised supplier name. **Desktop categorises transactions** into `t.category`, as a category name with no code, from statement rules matched on description and amount by `bestRuleFor()` at `IntelliBooks-Desktop-v3.html:965`.
>
> **What happens today when the two disagree: the transaction wins silently.** `attachReceipt()` at line 1073 does `if(!t.category && r.category) t.category = r.category;`. So the receipt's category is copied **only when the transaction has none**. If the transaction already has one, and it usually will because `applyRules()` fills it from statement rules, the receipt's category is discarded with no comparison, no flag and no record. VAT is handled the same way on the next line.
>
> **The intended precedence, confirmed with Paul 2026-07-28: manual, then rule, then receipt.** A category the operator typed wins over everything. A category a statement rule assigns wins over the receipt's. The receipt's category applies only where neither of those has filled the field. That is a sound order, and rules are not a lesser source: they are learned from the practice's own decisions at `IntelliBooks-Desktop-v3.html:938`, so a rule is a previous human judgement, not a guess.
>
> **But it is not implemented as a precedence. It is implemented as "first non-empty value wins", and the operator's button order decides which that is.** `applyRules()` at line 964 skips any transaction that already has a category, and `attachReceipt()` only writes when the field is empty. So run the analyser first and the rule wins, which is the intended order. Attach first and the receipt wins, which inverts it. Same two facts, two different answers, and nothing in the code expresses a preference. The intended precedence happens to hold only for one of the two sequences an operator might reasonably use.
>
> **Two further gaps, both of which the intended precedence assumes away.**
>
> *There is no confidence on the rule side.* `bestRuleFor()` at line 953 takes any rule whose pattern is a substring of the normalised description, prefers an amount-conditioned rule, then prefers the longest pattern. A two-character pattern match is treated as certain. So a weak rule beats a high-confidence receipt match, which is the opposite of the agreed shape, and the pipeline does carry a confidence on its side already.
>
> *The bank description is often the worse evidence.* A line reading of a marketplace, a payment processor, or a forecourt that sells both fuel and groceries tells you who took the money, not what was bought. The receipt tells you what was bought. That is the class of case where the receipt should win, and it is why the agreed shape in this section says the receipt wins on high confidence rather than never.
>
> **So the recommendation, which reconciles the two.** Keep manual, then rule, then receipt as the default. Make it deterministic rather than order-dependent, so the answer does not depend on which button was pressed first. Put a confidence on the rule side so a weak pattern match does not beat a strong receipt match. And record the disagreement whichever way it resolves, because today it is discarded with no trace, so a bad rule can be wrong for years without anyone being able to see it. The first of those is worth doing now; the other two still need the shared vocabulary.
>
> **Rename, agreed 2026-07-28.** The button at line 115 reads `Run Matching Analyser` and does no matching: it categorises from statement rules. Receipt-to-transaction matching is `refreshMatches()`, which runs by itself and has no button. Rename it **Categorise from Rules**, and fix the same wording in the tooltip at line 1324. For the IntelliBooks session.
>
> **This also proves why the conflict rule cannot be built yet, rather than merely asserting it.** To say "the receipt says X and the transaction says Y" you need X and Y in one vocabulary, and today one is a nominal code from the vendor tables and the other is a name from `books.categories`. The shared vocabulary is the chart of accounts in section 13. So the ordering above is the part that can be fixed now; the rule itself waits.
>
> **Where the gate belongs, per Paul 2026-07-28.** Not on the receipt. A receipt is a document and may reasonably have no category. Both routes into the books run through a transaction: `postReceiptToCashbook()` at line 1659 creates one from a receipt, and attach binds one to an existing transaction. So the rule to enforce is that **a transaction must not be posted with a blank category**, which covers both routes with one control instead of policing receipts at three points.
- Bulk actions on the queue.
- Editing or deleting extraction rows. Forbidden by `CLAUDE.md`.
- Any JSON API, OAuth, SSO, JWT or permission matrix.
- Retry-from-console. The auto-retry loop handles it; a manual trigger invites races with the running worker.

---

## 15. Test plan

Syntax check with `python -m py_compile`, verify imports, then functional tests. Keep the suite green.

> **Amended 2026-07-26, count updated 2026-07-27.** The suite was 17 of 17 when this was written. It is **64 of 64** after phase 0 steps 1, 3 and 4, under both `python -m unittest discover -s tests` and `python -m pytest -q`, which agree. `pytest` is not a runtime dependency and was missing from `.venv`; it is now pinned in `requirements-dev.txt`.
>
> **Every test that reaches a writer must redirect `config.LOGS_DIR` and `config.RUNS_LOG`, and restore them afterwards.** The suite was appending synthetic rows into the live `logs\receipt_events_{firm_id}.ndjson` and `logs\runs.ndjson`, which is not tidiness: the intake panel at 8.6 reads those files, so a row like `"receipt_id": "recent-receipt"` would surface in the console as a real intake problem. Fixed in `2d19521`, with `tests/test_logs_isolation.py` asserting that a run creates nothing under the real `LOGS_DIR`. Redirect both constants, not just `LOGS_DIR`, for the reason in 6.5. Three synthetic rows written before the fix are still in the live event logs and are Paul's to decide about.

**Phase 0 regressions, each red before its fix:**

1. Mock the extractor to raise; run `_retry_failed_receipts()` twice under the same `pipeline_version`; assert extraction attempted once, not twice.
2. Same for the missing-file branch.
3. `save_extraction(update_status=False)` leaves `receipts.status` unchanged; default `True` preserves existing behaviour.
4. Correct VAT from non-zero to `0`; assert stored `0.0`.
5. `--vat 0` alone does not fall through to interactive mode.
6. All amounts as strings: coerced or field errors, never `TypeError`.
7. Resolution removes the Review pair; missing pair does not raise.
8. `review_count` from the DB matches status counts.
9. Sidecar carries `category_code` and `category_name`, and legacy `category` holds the name.

**`parse_corrections`:**

10. Omitted field absent from `values`; `"0"` present as `0.0`; `""` records an explicit clear.
11. Rejects `"1,234.56"`, `"£10"`, `"10.999"`, `"25/12/2026"` with field errors.

**Post-processing move:**

12. `postprocess` produces byte-identical results to the previous in-`openai_vision` behaviour for the existing date and VAT cases, with those tests unmodified.

**Service, temp DB:**

13. Mismatched `expected_extraction_id` returns `stale` and writes nothing.
14. Locked receipt returns `locked`.
15. Nonexistent receipt returns `not_found`, does not raise, does not `sys.exit`.
16. Still-invalid correction returns `still_invalid`, **appends a new extraction row carrying the validation notes and leaves the previous row byte-identical**, writes a `resolution_events` row, does not file. Amended 2026-07-27, see 4.3 step 6. Superseded wording: "appends a note".
17. Successful resolve writes exactly one new extraction row and leaves the original untouched.
18. GL override leaves `suggested_code` unchanged, sets `correction_code`, and the written sidecar carries the corrected code and name.
19. Opt-in mapping checkbox off leaves `categorisations_client_vendors` unchanged.
20. `discard_receipt` sets `discarded`, deletes no file, removes no extraction row.
21. Lock released on every path including the exception path.

**Back-feed:**

22. A valid `filed` note sets status `ok`, sets `filed_path` to the note's path, writes a `manual_correction` extraction, writes a `resolution_events` row with `actor='desktop'`, and **does not re-file the image**.
23. Applying the same note twice is idempotent: one extraction row, one event row.
24. A malformed note moves to `Resolutions\failed\` and is not deleted.
25. A note for an unknown receipt moves to `failed\`.
26. A `category_name` absent from `coa_accounts` stores the name, skips vendor learning, adds a note.
27. A `discarded` note sets status `discarded` and deletes no files.
28. The consumer runs before `_retry_failed_receipts()`, so a receipt resolved by note is not retried in the same cycle.

**Browse and tax year:**

29. Receipts dated 5 April and 6 April fall in different tax years and each is returned by the correct year's filter. Use `tax_year_bounds()` in the test, not hardcoded dates.
30. Capture-date and invoice-date filters return different sets when a receipt straddles the boundary.
31. NULL `invoice_date` excluded from tax-year results and counted separately.
32. Search matches supplier, filename and reference number, case-insensitively.

**Web:**

33. Every route except `/login` redirects when unauthenticated. Enumerate routes in the test so a new unprotected route fails the suite.
34. An operator gets 403 on discard, register-client, top-up and settings.
35. POST without a valid CSRF token is rejected.
36. The preview route refuses a path outside `config.FILES_DIR`.
37. `?next=` survives the login redirect.

**Manual, before trusting it:**

38. Resolve a real `needs_review` receipt through the web form; verify the DB, the filed path and the sidecar all agree.
39. Run the console and the pipeline together through a full poll cycle; confirm no `database is locked` in `data/run.log`.
40. `resolve_receipt.py` still works from the CLI in both flag and interactive mode, per `RECEIPT_CAPTURE_GUIDE.md`.
41. Resolve in IntelliBooks Desktop, wait one poll, confirm the DB updated and the note moved to `processed\`. **Scoped 2026-07-28: both actions, filed and discarded, so two Review items and two OpenAI calls.** The discard branch had never run at all. **Passed 2026-07-29.** Pennine Cafe was filed and came back `ok`, engine `manual_correction`, carrying the figures corrected in Desktop and the note "filed in IntelliBooks Desktop", with one copy on disk and no `-2`. Kirkgate Hardware was deleted and came back `discarded` rather than `ok`, which is correct: `discard_receipt()` sets `discarded` at `worker/resolution/service.py:805`. Both notes reached `processed\`, and `Resolutions\failed\` was never created.
42. Filter the browse page to Client_001 for the current tax year and reconcile the count and gross total against the OneDrive folder.

**Deferred live tests, added 2026-07-29. Paul has asked for these at an appropriate time rather than now, so they are recorded here rather than left in a chat.**

43. **File a receipt with its figures left unreconciled**, rather than corrected before filing. Confirms the branch test 41 did not exercise: the extraction row is written `validation_status="ok"` because a human decided, carrying an extra note reading `filed by decision in Desktop despite: gross mismatch: ...`. Costs one Review item and one OpenAI call. Determinate from the code, so this test confirms rather than discovers. **Moved 2026-07-29 to after the reset at 10c**: 17.5 already requires a fresh fixture and one confirmed clean cycle once the database is empty, so the same Review item and the same single call can serve both, and this test then runs against a clean slate rather than adding a receipt that is about to be deleted.
44. **Change D's confirm box**, once the IntelliBooks session has built it. Post a receipt whose figures do not reconcile and confirm the box appears; decline and confirm no transaction was created; accept and confirm the transaction carries the gross and the VAT. Then post a receipt with **no net at all** and confirm it goes through silently, because that is the common case and the one a careless implementation breaks. No OpenAI cost: this is done against receipts already in the books.
45. **The blank category at posting**, only once the question at 17.4 is decided. Recorded now so the test is not invented from scratch later.
46. **The reconciliation check against the current state**, before anything is cleared at 10c. It must find `PKPH-books.json` as unregistered and any conflict copies. It will **not** see the 23 ghost receipts, which are books entries rather than files, and that limit is worth stating in the report so nobody reads a clean receipts result as meaning the books are clean. **A run that reports nothing is a failed test, not a clean bill of health.** Then run it after each stage of the reset, which is how 17.5's before-and-after requirement is satisfied.

---

## 16. Implementation order

Commit after each step.

**Before any code, Paul:**

0. Discard the two disposable failed test receipts. Delete the two untracked draft files. Merge `fix/imap-message-id-dedup` into `main`. Start a fresh branch. Ordering matters: every commit bumps `pipeline_version` and triggers an auto-retry pass, so clear the discards first.

> **Amended 2026-07-26. Step 0 was done differently and the merge is cancelled.** What actually happened, and why it matters to anyone reading this later.
>
> The discards were done. The merge was not, and should not be attempted on the basis written above. `main` is **42 commits behind** `fix/imap-message-id-dedup` and diverged by one, not six behind as the 2026-07-25 handover recorded. The single commit `main` holds is `965cb24`, a merge commit whose two parents are both ancestors of the working branch and whose tree is byte-identical to a recomputed clean merge of them, so it contributes no content. Nothing on `main` is needed. The only tracked files there and not on the working branch are the three `logs\*.ndjson`, deliberately untracked by `0859817`.
>
> Before this was noticed, a branch `docs/console-design` had been cut from `main` and this document committed on it, leaving the working tree missing 13 files of the built system, including `resolve_receipt.py`, `worker/extraction_pipeline.py` and three regression tests. Recovered on 2026-07-26: the two doc commits were cherry-picked onto `fix/imap-message-id-dedup`, and `feat/console-phase0` was cut from that. `docs/console-design` is kept as a safety net. One casualty: `logs\runs.ndjson` lost its records between 24 July 13:20 and 25 July, restored as far as `0859817^` allows. Log history only, no database or client file affected.
>
> **Phase 0 and everything after it happens on `feat/console-phase0`.** Bringing `main` up to date is its own session, with its own care, and is not a prerequisite for anything here.

**Phase 0:**

1. ~~The auto-retry loop fix, 3.1, with tests 1 to 3.~~ **Built 2026-07-26 in `787493f`**, with `tests/test_auto_retry_no_loop.py`. See the note in 3.1. Ordering deviation, deliberate: step 2 was built first, in `22130d7`, because the fix cannot be written without it.
2. ~~`save_extraction(update_status=False)`.~~ **Built 2026-07-26 in `22130d7`**, as `update_status=True` by default with `False` at the two new call sites. Plus `BaseExtractor.name` in `117fb1b`, pulled forward from step 7, see 10.1. Plus two unplanned commits the work exposed: `2d19521`, test log isolation, see section 15; and `285ed63`, actually writing `data/run.log`, see 4.3 and 6.5.
3. ~~`parse_corrections` plus the zero-value and coercion fixes, tests 4 to 6, 10, 11.~~ **Built 2026-07-27** in `c0ac145`, `worker/resolution/service.py` with `tests/test_parse_corrections.py`, and `0cae398`, the CLI rewired with `tests/test_resolve_receipt_zero_and_types.py`. See the note in 4.2. Suite 48 of 48.
4. ~~Review-pair cleanup and `review_count` from the DB, tests 7, 8. Also `processed_today`, per 3.10.~~ **Built 2026-07-27** in `dce1fdc`, `remove_review_pair()` in `worker/filing.py` with `tests/test_review_pair_cleanup.py`, and `25c6665`, `review_count` and `processed_today` from the database with `tests/test_status_counts_from_db.py`. See the notes in 3.5, 3.6 and 3.10. Suite 64 of 64.
5. ~~Sidecar `category_code` and `category_name`, test 9.~~ **Built 2026-07-27** in `9f5cdad`, all four call sites plus the removal of the post-hoc mutation, with `tests/test_sidecar_category_keys.py`, and `96a5c5a`, `retroactive_categorise.py` with `tests/test_retroactive_categorise_sidecar.py`. See the notes in 3.7. Suite 73 of 73.
6. ~~Move post-processing to `worker/extraction/postprocess.py`, test 12. Pure move.~~ **Built 2026-07-27** in `bf1976d`, with `tests/test_postprocess.py`. Suite 94 of 94. See the note in 10.2, which records the seven defects the move exposed and did not fix.
6b. ~~Fix findings 1, 2, 6 and 7 from the 10.2 note.~~ Inserted 2026-07-27 by decision, see 17.4. **Built 2026-07-27** in `725545b`, `843a6b1`, `f0e0613` and `dc2e2ae`, with `tests/test_prefer_dayfirst_isolation.py` added. Suite 116 of 116.
6c. ~~Write `extractions.details`, per 3.11.~~ **Built 2026-07-27** in `4aeadcd`. The write was dropped by `799cead` on 21 July, confirmed from the diff: it removed the parameter, the column and the value in a commit that rewrote 457 lines of `app.py`.
7. ~~Extraction factory and `extractor.name`, replacing the hardcoded strings.~~ **Built 2026-07-27** in `71fe757`, the factory plus `config.EXTRACTION_ENGINE`, and `d931045`, the three failure paths. Suite 134 of 134. `app.py` no longer imports `OpenAIVisionExtractor` at all, so the concrete class is reachable only through the registry.
7b. ~~Pass `pipeline_version` at the two embedded-image writes, per 3.12.~~ **Built 2026-07-27** in `684216f`. All six writes in `app.py` now pass it, checked programmatically.

**Resolution service:**

8. ~~`worker/resolution/service.py`, tests 13 to 21.~~ **Built 2026-07-27** in `4c7c733` the `resolution_events` table, `f700706` the read side, and `60df040` `resolve_receipt()` and `discard_receipt()` with 23 tests. Suite 181 of 181. See the 2026-07-27 amendments to 4.2, 4.3 and 5.1 for the five points the control flow left open.
8b. ~~The three service corrections: the `already_filed` guard, preserving `possible_duplicate` on `still_invalid`, and the `reason` column.~~ **Built 2026-07-27** in `d3bf4e1`, `4fddcb0` and `39d28b5`.
9. ~~`resolve_receipt.py` as a thin CLI, plus `discard_receipt.py`. Verify test 40 by hand.~~ **Built 2026-07-27** in `e44be94` and `d4a5a97`. Suite 221 of 221. Test 40 run by hand against a temp database in all three modes, with the audit trail in `resolution_events` quoted in the report. `add_validation_note()` removed from `Repository`. One file per entry point for logging, `run.log`, `resolve.log`, `discard.log`, `console.log` reserved: the `QueueHandler` alternative was rejected because its listener has to be a process that owns the file, which means either the pipeline must be running before the CLI can log or there is a log daemon, and logging then stops silently if the listener is down.
9b. ~~Two small corrections from the 4.4 amendment: call `confirm_duplicated_action()`, and add `receipts.filed_at` per 5.1a.~~ **Built 2026-07-28** in `4b50910`, the duplicate confirmation, and `d7c3d63`, `filed_at` plus the date in the `already_filed` message.
9c. ~~Move the folder-intake original out of the inbox on every outcome, per 3.13.~~ **Built 2026-07-28** in `5ceb38b`. One commit as planned, done in the same session as 9b because it was live and costing an OpenAI call per poll for any receipt sitting in review.
   Original step 9 text, for the record: **Also `worker/logging_setup.py`**, per 6.5: move `attach_run_log_handler()` out of `app.py`, call it from every entry point, and settle whether it is one log file per process or a single writer. 4.3's accepted trade-off is unsound until this is done.
10. ~~Back-feed consumer and `apply_resolution_note()`, tests 22 to 28.~~ **Built 2026-07-28** in `6d86894`, `apply_resolution_note()` as the entry point, `af5ab0a`, the consumer at the start of every poll, and `f453a9c`, tests 22 to 28. Suite 263 of 263. **Verified end to end on 2026-07-29 by test 41**, against the IntelliBooks half built by a session that could not see this one: a receipt filed in Desktop came back `ok` with its corrected figures and one copy on disk, a receipt deleted came back `discarded`, both notes reached `processed\`, and `failed\` was never created. See the 12.2, 12.3 and 12.4 amendments for the five points the two halves disagreed on and how each was resolved. Recorded as built on 2026-07-29: the commits landed on the 28th and section 16 was not updated at the time, which understated progress by three steps.

10a. Move the client folder layout to amendment 55's namespaced form. On the pipeline side this is small: `get_client_directory()` at `worker/filing.py:64` is the single choke point, and the only other site is the `*/Review` glob at `filing.py:297`. **Introduce config constants for the four folder names rather than editing string literals**, so 13A and everything after it derive the layout from one place. Land the constants at their **current** values, so this commit changes no behaviour, and flip them in 10c when there is nothing on disk to migrate. Desktop's six `getDir(["Clients", ...])` sites change in the same window, and the tax year folder keeps its bare `2026-27` form for the reason in amendment 55.
10b. The file reconciliation check, section 13A. Run it once against the current state before anything is cleared, and confirm it finds `PKPH-books.json` and whatever else is there. A check that reports nothing today is broken.

**The clean-slate reset:**

10c. The staged clear-down in 17.5. ~~**After the live round trip, test 41, and before any console work.**~~ **Rescheduled 2026-07-29: after the four IntelliBooks Desktop changes A to D and their manual checks, and still before any console work.** Test 41 has passed, so the original precondition is met; the new one is that change D's test needs the books populated and the reset empties them. See amendment 54. Placed here on 2026-07-28 by decision. Not before step 10, because resetting and then changing the pipeline is two variables at once; not after step 11, because the console should be built on a clean slate rather than on 27 test receipts. The consultant session supervises it stage by stage, verifying state before and after each stage rather than at the end.

**Console:**

11. Schema additions, including `coa_accounts`. Verify `init_db()` is still idempotent against the live DB.
12. Load `chart_of_accounts_DRAFT.csv` into `coa_accounts` with `scope='default'`.
13. Token usage capture and `extraction_usage`.
14. Auth: `console_users`, `create_console_user.py`, login, deny-by-default, CSRF, `?next=`. Tests 33 to 35, 37.
15. Read queries, status page, queue page.
16. Receipt detail page, correction form, GL control. Tests 18, 19, 36.
17. `tax_year_bounds()`, then the browse page. Tests 29 to 32.
18. Intake panel and the clients.csv reload mechanism.
19. Costs API client and the spend panel.
20. Billing-error classification, 3.9.
21. `RECEIPT_CAPTURE_GUIDE.md`: starting the console, login, resolving through the UI, the GL override, finding a client's receipts for a tax year, that both tools can resolve safely, and OpenAI auto-recharge as a setup step.
22. `CLAUDE.md`: new tables, the resolution service boundary, the back-feed contract, and the rule that the domain layer stays free of web imports. **Also the Claude Code permissions setup**, added 2026-07-28: the pre-approved command list lives in `.claude/settings.local.json`, because **allow rules in `.claude/settings.json` are ignored unless the workspace is trusted, while the local file's are not**. That cost three attempts to find. `.claude/settings.json` holds the same content and is committed, so a fresh checkout can recreate the local file from it with a single copy; until someone does, every command prompts. `.claude/settings.local.json` is gitignored and machine-local by design. This belongs here rather than in `RECEIPT_CAPTURE_GUIDE.md`, which is written for the day-to-day operator and has no business carrying developer environment setup. Leave the existing AUTOMATIC Task Mode section alone while doing this step.

Steps 1 to 10 are worth doing even if the console slips. They fix live bugs and close the divergence.

---

## 17. Documents and remaining questions

### 17.1 Ownership

| Document | Owner |
|---|---|
| This file | Cowork design session |
| `IntelliBooks-System-Specification.md` | Cowork design session, bump to v1.1 |
| `IntelliBooks-System-Overview.md` | Cowork design session |
| `CLAUDE.md`, `RECEIPT_CAPTURE_GUIDE.md` | Implementation session, steps 21 and 22 |
| `IntelliBooks-Change-Log.md` | The IntelliBooks build session, items 24 to 26 only |

Two sessions editing whole-system documents independently is how the drift began.

### 17.2 Corrections needed to the specification

It is v1.0 of 15 July and describes itself as the single source of truth. Bump to v1.1, keep superseded wording visible with its reason, so the decision trail survives.

- Review holding is `Clients\{Name}\Review\`, not `Receipt Inbox\{CODE}\Review\`. Sections 3 and 5.3 item 6. Change log item 18 removed the latter.
- Books live at `IntelliBooks\Books\{CODE}-books.json`. Section 3 table and 5.4 item 1. Item 12 moved them.
- Section 3 predates item 12's `IntelliBooks\` versus `Clients\` split, so Receipt Inbox is `IntelliBooks\Receipt Inbox\{CODE}\`.
- Section 5.4 item 6's "Import Client's Receipt Folder" was removed in item 22.
- Section 4.3's Corrections rule: record the original, then the back-feed and the three defects that forced it.
- Section 4.3's lifecycle diagram says "human fixes, reprocess", which matches neither implementation.
- Section 2: add the console as a sixth component.
- Section 5.3 item 4's internal store path may have diverged from `CLAUDE.md`. Verify rather than assume.
- Nothing records `possible_duplicate`, `retry_exhausted`, receipt locking, the 7-day retry cap or the IMAP Message-ID fix.

### 17.3 Corrections needed to the overview

More current, 19 July, but: line 28 describes Desktop's review-and-file flow as *the* way to complete reviews; line 36's "the desktop app never writes to receipts.db" needs the note-based nuance; neither `resolve_receipt.py` nor the console appears.

### 17.4 Open questions for Paul

- Confirm the revised answer to the category-conflict question, section 14, bullet 5: receipt wins on high confidence, rule wins on low, flag either way.
- Extend `chart_of_accounts_DRAFT.csv` with income, equity and remaining balance sheet accounts. Not blocking; the 23 expense accounts cover the receipts module.
- Issue a dedicated OpenAI API key or project for this app, needed for clean cost attribution (9.3).
- Whether an org-level OpenAI Admin key on this workstation is acceptable. If not, 9.3 is skipped and the local ledger stands alone.
- ~~Whether `export_bookkeeping.py` needs the effective-GL-code treatment (11.2).~~ **Answered 2026-07-27: it cannot need it, because it exports no category at all.** The script is 45 lines and selects `receipt_id`, `firm_id`, `client_id`, `supplier_name`, `invoice_date`, `net_amount`, `vat_amount`, `gross_amount`, `currency`, `status`, `MIN(extracted_at)`, `MAX(validation_status)` and `MAX(validation_notes)`. No `categorisations` join, no nominal code. So 11.2's effective-code rule has no route into it, and whether a bookkeeping export **should** carry the GL code is a new and separate question. It probably should, given that is the point of categorising, but it is a change of purpose rather than a bug fix.
  Two real defects found in it while answering, both out of scope and neither touched. First, `e.supplier_name` and the other bare `e.*` columns sit outside the `GROUP BY`, so SQLite takes them from an arbitrary row in the group: a receipt with three extraction attempts can export the supplier from one attempt and the amounts from another. Second, `MAX(e.validation_status)` and `MAX(e.validation_notes)` are aliased `latest_*`, but `MAX` on text is alphabetical, not latest, and `MAX('ok','failed')` is `'ok'`, so a receipt whose most recent attempt failed can export as `ok`. Both matter more than the missing GL code, because both silently produce a wrong figure or a wrong status in something called a bookkeeping export.
- Whether the browse page should export CSV. `export_bookkeeping.py` already exists and two divergent export formats is worse than one; if yes, reuse its logic.
- Confirm IntelliBooks change log item 19 has been tested end to end before the back-feed is built on it. Note that testing it creates the divergence deliberately, so reset the receipt's DB status afterwards.

Added 2026-07-26, neither blocking phase 0:

- **How should the CLI express "clear this field"?** `parse_corrections` in 4.2 distinguishes omission from an explicit clear, where `""` means clear. `resolve_receipt.py`'s interactive prompt already treats a blank answer as "keep existing", which is documented in `RECEIPT_CAPTURE_GUIDE.md` and must not change. So the CLI currently has no way to clear a wrongly extracted reference number, while the console will have one. Options: a typed sentinel, a `--clear field` flag, or accept the asymmetry and leave clearing to the console. Do not invent a sentinel without deciding.
- **Should `add_validation_note()` stop mutating extraction rows?** It runs `UPDATE extractions SET validation_notes = ?` on the latest row, at `repository.py:571`. `CLAUDE.md` says extractions are append-only, and 4.3 step 6 tells the resolution service to call it on a `still_invalid` outcome, so the service as specified mutates an append-only row. Either notes are agreed to be mutable metadata while values are not, and `CLAUDE.md` says so explicitly, or the `still_invalid` path appends a new `manual_correction` row carrying the notes instead. Decide before step 8. Phase 0 step 1 already took the second route for the missing-file branch, see 3.1.
- ~~Should the `category` key be backfilled in the 32 sidecars already filed?~~ **Asked and answered 2026-07-27: no. Paul confirms every filed receipt and sidecar on disk is test data, on test clients and his own record, not a third party's books.** So there is nothing to preserve and nothing to correct. Step 5 fixes the writer, the existing files stay as they are, and if they are ever in the way they can be deleted rather than rewritten. Anyone reading 3.7's table later should read it as forensic evidence of how the field drifted, not as a client data problem.
- ~~Fix the four small defects the step 6 move exposed, or carry on?~~ **Decided 2026-07-27: fix them now, as step 6b, before step 7.** Findings 1, 2, 6 and 7 in 10.2. Findings 3, 4 and 5 stay deferred. Original reasoning kept below. Finding 2 is the one that argues for doing it: for a receipt that prints an ISO date, the day-first fix does not apply at all, and it fails silently, so nobody would find it without reading the code. Finding 1 puts a false label on the note an operator reads to decide whether to trust a date. Finding 6 is three `logger.warning` calls that change nothing on the happy path. Finding 7 is two lines of test hygiene, now unblocked because step 6 is committed. Together they are one small commit each in a single area, with tests, and they are cheaper to do now while the code is fresh than after the console is built on top of it. Against: it is not in the agreed phase 0 list and it delays step 7. Findings 3, 4 and 5 should wait either way.
- **A receipt filed with no category: where the risk actually is.** Added 2026-07-28, found during the item 19 test, and **corrected by Paul the same day.**
  Superseded framing, recorded because it was wrong in a way worth not repeating: I first wrote that an uncategorised receipt is invisible in the HMRC and P&L reports it should appear in. That is not how this system works. **Receipts do not map to HMRC boxes or to the P&L. Transactions do.** A receipt is a document; a receipt can be attached to a transaction, and a transaction can be created from a receipt. The accounting record is the transaction.
  So filing a receipt with a blank category is not itself an accounting gap. The risk is one step removed, at `postReceiptToCashbook()`, `IntelliBooks-Desktop-v3.html:1659`, which creates a transaction from a receipt and does `t.category = r.category || ""`. A blank category on the receipt therefore produces a transaction with a blank category, and **that** is the record the reports read. The toast it shows says "Review the category, then Post", so the flow expects the operator to fix it, which is a prompt rather than a control.
  The other route is attaching a receipt to an existing transaction, where the transaction already has its own category from a statement rule. That is the disagreement handled by the category-conflict rule in section 14: receipt wins on high confidence, statement rule wins on low, flag either way, never auto-update the rule.
  So the question narrows usefully: not "should Desktop require a category before filing", but **"should a transaction be allowed to reach the books with a blank category"**. Paul's call, it lives in Desktop rather than here, and it belongs in the brief for the IntelliBooks session.
Added 2026-07-28, from verifying the IntelliBooks half of the back-feed:

- ~~**Which sidecar shape wins after a Desktop-filed receipt?**~~ **Decided 2026-07-28: both stay, readers key on the discriminator.** See the 12.4 amendment for the reasoning and the binding rule.
- ~~**`clients.csv` gives `Client_004` to two different clients**, `Test` and `She Run's It! Ldn Ltd`, so anything keyed on `client_id` conflates them.~~ **Fixed 2026-07-28**, ahead of test 41 on Paul's instruction rather than after it, on the principle of not generating new rows against a broken registry. `SHERUNSIT` is now `Client_005`. No existing row moved: all 6 `Client_004` receipts belong to `TEST`, and `She Run's It! Ldn Ltd` had none, nor any vendor mappings. `clients.csv.bak-2026-07-28` sits beside it. The loader parses the result with no duplicate id, code or email.
- **`write_review_file()` has no caller** in `app.py` or `worker/`, and the name it writes, `{stem}.review.json`, is invisible to Desktop. `scanReview()` derives the image name by stripping `.review.json` and skips the item when no file of that name exists, so `receipt.review.json` yields `receipt`, which is not a file. `file_review()`, the writer that is used, produces `{stem}{ext}.review.json` and works. Probably dead code. Confirm and delete rather than leave a second writer whose output cannot be worked.
- **The null-id filename fallback can miss.** Recorded at 12.3 step 2 by amendment 48. Flagged, not fixed.
- **A note-write failure in Desktop leaves the Review pair deleted and the pipeline uninformed**, so the receipt keeps `needs_review` and the retry pass re-extracts it at one OpenAI call until the 7-day cap. This is a fallback to pre-back-feed behaviour rather than new harm, and the IntelliBooks session chose it deliberately over rolling back a filing. There is no retry and no queue. Accept, or ask for a retry on the next Desktop load.
- **A partial filing window in Desktop.** Inside one `try`, the image copy commits before the sidecar write. If the sidecar write throws, the copied image is already in `Receipts\` while the toast says "Filing failed, nothing was deleted" and the Review pair remains, so re-filing produces a `-2` duplicate. Pre-existing, unrelated to the back-feed, and the toast is accurate about the Review pair and misleading about the image.
- ~~**`PKPH-books.json` exists in `IntelliBooks\Books\` with no client in either registry.**~~ **Answered 2026-07-29: delete it.** It is a 1,174-byte stub, zero transactions, zero receipts, one bank account and Desktop's default chart of 21 categories, so there is nothing in it to preserve and OneDrive version history covers the reversal. Worth noting before it goes: those 21 categories are Desktop's built-in chart and are relevant when `chart_of_accounts_DRAFT.csv` is extended at step 12. Nothing in the pipeline's database refers to PKPH, so the reset never touched it and this is purely a file on disk.
- **The three synthetic rows in the live event logs.** Written by the test suite before `2d19521` fixed the isolation. Identifiable by `receipt_id` values `recent-receipt` and `56b29977`. They will show in the intake panel at 8.6 unless removed or filtered. Removing lines from an operational log is Paul's call.


### 17.5 The clean-slate reset, added 2026-07-28

Paul intends to clear the database and the test clients and start testing afresh, soon. Every filed receipt, sidecar and books entry on disk today is test data, which is why several decisions above are "no backfill" and "no migration". This section records what the reset must and must not touch, because two parts of it are not disposable and one of them costs money to get wrong.

**Do not clear: the vendor mappings.** `categorisations_client_vendors` holds 100 rows for `Client_001` and one for `Client_003`. That is real practice knowledge, imported from `categorisations_client_vendors_cleaned.csv`, and it is what makes the categorisation engine's layers 1 and 3 work at all. It is recoverable from that CSV if lost, and `import_vendor_csv.py` and `seed_client_vendors.py` exist for the purpose, but it should be preserved deliberately rather than rebuilt by accident. `categorisations_firm_vendors` and `categorisations_client_rules` are both empty, so nothing to protect there.

**Do not clear `processed_attachments` without checking the mailbox first, and this is the one that costs money.** It holds 20 rows, and it is the only record that a given email attachment has already been extracted. `fetch_new_messages()` selects `INBOX` and searches `ALL`, at `worker/email/reader.py:47` and `:171`, so it re-reads everything sitting in `INBOX` on every poll and relies on `processed_attachments` to know what to skip. Emails that were processed have been moved out to `INBOX.Processed Receipts` and the other routing folders, so in principle `INBOX` is empty and a reset is free. **Verify that before clearing, not after**: anything still in `INBOX` will be re-extracted at one OpenAI call per attachment, and with a fresh database there is nothing to stop it.

**Safe to clear:** `receipts`, `extractions`, `categorisations`, `resolution_events`, `statements` (empty), `email_alerts` (3 rows, all test alerts), and `email_delta`. On disk: `Clients\Test\`, `Clients\Test 2\`, the two `Books\TEST*-books.json` files, `data/files/`, and the filed receipts under `Clients\Paul Keating\Receipts\`, which are Paul's own and also test material.

**The order matters.** Stop the pipeline first, so nothing is mid-write. Back up `data/receipts.db` before touching it, `repo.backup_db()` exists for this. Then clear, then run `init_db()` once to rebuild an empty schema, then re-import the vendor mappings if they were lost, then start the pipeline and confirm one clean cycle before creating any new test fixture.

**Scheduled at step 10c**, after the live round trip and before any console work, agreed 2026-07-28, and **moved again on 2026-07-29 to sit after the four Desktop changes A to D**, per amendment 54: change D's manual check posts an unreconciled receipt from the books, and this reset empties the books, so testing has to come first. Not earlier, because step 10 changes the pipeline and resetting either side of a code change means two variables at once. Not later, because the console should be built against a clean slate rather than against 27 test receipts and a books file full of import artefacts.

**Supervised, not handed over.** Paul has asked the consultant session to run this stage by stage. That means: a plan enumerating every stage before anything is deleted; a database backup and a file-tree listing captured first; the state verified before and after each stage rather than once at the end; nothing deleted in the same stage as anything else; and the mailbox checked before `processed_attachments` is touched. If a stage does not verify, stop there rather than continue and reconcile later.

**Worth treating as a test in its own right.** A clean start exercises the paths nobody has run since May: an empty database, `init_db()` from nothing, `clients.csv` resolution with no history, and Desktop opening a books file it has to create. If any of those are broken, better to find out deliberately than on the first real client.
