# Brief: the reason a receipt did not reach `ok` goes into the log

**Written 2026-09-09 by the consultant session. Paul's instruction, 2026-09-09: "I need a reason in the log."**

**Small and self-contained. It is not part of the publish step and it is not stage 4.**

---

## 1. What is wrong, and the evidence

On 2026-09-09 an emailed receipt failed and **neither log said why**.

What `C:\Intellibills\logs\run.log` recorded, in full, for that receipt:

```
2026-09-09 11:33:28,357 INFO worker.email.reader — Extracted embedded image: image0.jpeg
2026-09-09 11:33:32,813 INFO httpx — HTTP Request: POST https://api.openai.com/v1/chat/completions "HTTP/1.1 200 OK"
2026-09-09 11:33:33,014 INFO worker.email.reader — Moved email uid=26 to INBOX.Failed Processing
```

What `C:\Intellibills\logs\receipt_events_FIRM001.ndjson` recorded for the same receipt:

```json
{"receipt_id": "a96ab8f7-3af1-42e7-bd98-dee8be2529b8", "action": "extracted",
 "client_id": "Client_004", "extraction_status": "failed",
 "supplier_name": "Octopus Energy", "invoice_date": "2026-08-15"}
```

**The reason existed only in the database**, in `extractions.validation_notes`, which reads `missing gross_amount`.

So an operator reading either log sees that a receipt failed and cannot see why without opening SQLite. **That is the whole of the defect.**

**Three things established by reading, so you do not have to re-establish them:**

- `validate()` in `worker/validation/rules.py` returns a `ValidationResult` carrying `status` and a `notes` list. The notes are already the human-readable reason: `missing gross_amount`, `invalid date: ...`, `gross mismatch: ... `, `net_amount is negative: ...`.
- `worker/extraction_pipeline.py` has **no logger of any kind**. It writes the ndjson event log and nothing else. The `Moved email uid=...` line comes from `worker/email/reader.py`, which knows the destination folder and not the reason.
- **`_log_receipt()` already has a `review_reason` parameter and the `"extracted"` call site does not pass it.** The parameter exists and is unused on that path.

## 2. What to build

**Deliverable 1. Every receipt whose validation status is not `ok` produces one line in `run.log` carrying the reason.**

The line must carry, at minimum: the receipt id, the client id, the status, and the validation notes. Level `WARNING`.

**All three non-`ok` statuses, not only `failed`.** `needs_review` and `possible_duplicate` are equally unexplainable from the log today.

**Deliverable 2. The same reason reaches the ndjson event log**, through the `review_reason` parameter that already exists on `_log_receipt()`.

**Deliverable 3. A receipt that reaches `ok` logs no such line.** A warning on the ordinary case is noise and stops the line being read.

**Where these belong is yours to decide.** The place that holds both the status and the notes is where the outcome is decided; the place that writes `run.log` today is elsewhere. Do not change the return shape of a function with several callers just to move the notes, unless you have enumerated those callers first and say so.

## 3. Decisions already taken, so nothing here waits on Paul

| # | Decision | Why |
|---|---|---|
| 1 | **The notes are logged verbatim, not summarised or re-worded** | `validate()`'s note strings are already written for a person and are the same strings the database holds. Two wordings for one condition is how a search for the reason stops finding it |
| 2 | **`WARNING`, not `ERROR`** | A receipt that failed validation is an outcome the pipeline is designed to produce, not a fault in the pipeline. `ERROR` is what a publish failure uses |
| 3 | **Not the run summary** | What belongs in the run summary is Claude Code's own flag 3 from `2026-09-09_REPORT_claude_code_stage1_piece3_publish.md`, and it is a separate decision about what Paul reads after a run. **Do not add a statistic here** |
| 4 | **All three non-`ok` statuses** | Paul asked for the reason, not for the reason on one status |
| 5 | **One line per receipt, not one per note** | A receipt with three notes is one outcome |

## 4. What is out of scope and must not change

- **18.2b's freeze still holds.** `get_client_directory()`, `file_receipt()` and `make_enriched_sidecar()` in `worker\filing.py` are frozen and nothing in this brief touches them. Stage 3's acceptance test has not been run.
- **Nothing about publishing.** `worker\publish.py` and the `publish_events` table are not in this brief.
- **The two copies of `_log_receipt()`.** The report of 2026-09-05 flagged that `app.py` holds a near-identical copy which already differs. **Flag anything you find there. Do not repair it.**
- **`validate()`'s own rules.** Whether a missing gross should fail rather than go to review is an accounting judgement and it is Paul's. Not here.

## 5. Standard of evidence

The project standard, unchanged:

- **Red before green**, with the failing output quoted.
- **Mutations anchored to one place, each printing its own diff**, with the anchor asserted to match exactly once.
- **A guard over the set, not over its members.** The claim that every non-`ok` status logs a reason is a set claim: enumerate the statuses from `validate()` itself rather than listing them by hand, so a fourth status added later fails the guard rather than passing silently.
- **A test that a receipt reaching `ok` logs nothing**, with a control, so the test cannot pass by the logger being broken.
- **Do not cite a line number in `config.py` or `app.py`.**
- **Disclose your own mistakes**, including ones you caught and corrected.
- **Say what each confidence rests on and what it is about.**

## 6. Where to write the report

**`C:\LastingImpact\receipt_capture\2026-09-09_REPORT_claude_code_validation_reason_logging.md`.**

Carry in it: what was built, the commits, the suite before and after, every mutation and its result, every decision this brief did not settle and what you chose, anything you flagged, and your own mistakes.
