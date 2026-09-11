# Handover: consultant session 22, chat 22

**Written 2026-09-11 by the consultant session, at Paul's instruction. It covers the session that ran
from 2026-09-10 late afternoon to 2026-09-11 late afternoon.**

**You are the consultant session in Cowork. You own verification, this project's design document and
the prompts, and since 2026-09-06 you also write `IntelliBooks-Desktop-v3.html` on Paul's standing
instruction. You do not write the pipeline; Claude Code does.**

---

## 1. Read these, in this order, before doing anything

1. **This file, in full.**
2. **`CLAUDE.md`**, section "How this project is worked", and the traps. **The traps live there and
   nowhere else.** Section 7 of this file adds only the ones this session actually hit.
3. **`2026-07-25_CONSOLE_DESIGN.md`**, the amendment record from **317 to 330**, all of which is this
   session's work. Then section 18, receipt and transaction integrity, before the body.
4. **`IntelliBooks\App\Docs\IntelliBooks-Change-Log.md`**, items **79 to 87**, which are this
   session's Desktop work.
5. **The three Claude Code reports of this session**, all in the repository root:
   `2026-09-10_REPORT_claude_code_post_time_client_copy.md`,
   `2026-09-11_REPORT_claude_code_attached_document.md` and
   `2026-09-11_REPORT_claude_code_corrected_note.md`.

**Do not read the handovers in `archive\`. They are superseded.**

**Do not state what any of these contains unless you have opened it.**

---

## 2. What is in flight

**Nothing is executing.** Claude Code reported its last brief, the work was verified, and the tree is
committed on `feat/console-phase0`. Nothing is pushed.

**One brief is written and held, and it is the next piece of work.**
`PROMPT_claude_code_2026-09-11_capture_report.md`, in the repository root, md5
`41afd85e97e84a767ac4ce215fba2c3f`. **It has not been sent to Claude Code.** It is step 10n, the
capture report. Send it as your first act unless Paul says otherwise.

**One brief per session at a time.** That rule held all day and it is the reason the reports are
readable.

---

## 3. What this session did, and the state to verify

**Step 10f closed.** Sub-step 10f.37, the Post-time message, and 10f.38, the attached document, both
built, both proved on Paul's machine with real receipts.

**Step 10g closed.** 10g.3 search by category name, 10g.4 the split transaction, 10g.7 the Post to
Cashbook check. 10g.8 cancelled.

**Step 10k built, both halves.** The pipeline half is Claude Code's, commits `41774a5` and `b6b6f44`.
The Desktop half is this session's. **Paul tested it and it passes.**

**Step 10n rescoped**, amendment 327, and it moved from this session to Claude Code.

**Step 10l's open design question decided**, amendment 330. The step itself is not built.

**Verify rather than take this on trust.** The three claims worth checking against the thing itself:

1. `CORRECTED_ACTION` is a fourth value in `NOTE_ACTIONS` **and** in `NOTE_APPLIED_OUTCOMES` in
   `worker\resolution\service.py`. Both, not one. A third action word was once added to only one of
   two places and every successful message went to `failed\`.
2. `_apply_corrected_note()` passes `filing_already_settled=True`, and that keyword is what skips
   `copy_for_published_receipt()` at step 11 of `resolve_receipt()`. Read the guard, not the comment.
3. `saveReceiptEdit()` in `IntelliBooks-Desktop-v3.html` writes **no** field until both gates have
   passed. The supplier assignment used to sit above them.

---

## 4. Step 10k, and what Paul ruled

**The `corrected` note is sent only where something changed.** Paul's ruling, 2026-09-11. Six things
are compared: supplier, date, net, VAT, gross and category. The pipeline's `CORRECTABLE_FIELDS` holds
seven; `receipt_ref_number` and `receipt_time` are not on the Edit Receipt window, are never sent,
and cannot differ.

**A save that alters nothing writes nothing.** Each note costs a poll, a `resolution_events` row and
an append-only `extractions` row.

**Tested on Paul's machine.** Net unchanged wrote no file. Net changed wrote one note, which is
`e10419a8-574b-4d23-8521-47630ee7bd79_1789134427684.json`. Net above gross was refused.

---

## 5. The decision that shapes the next piece of work

**Step 10l, amendment 330, decided 2026-09-11 and not yet built.**

1. The hold for a layer 5 guessed category lives in **`categorisations.needs_review`**.
   `validation.status` keeps its arithmetic meaning only.
2. **The published item must carry a second key.** `drainInbox()` routes on one key, `s.validation`,
   and a receipt with perfect figures and a guessed category is `ok` today, so it drains straight
   through. Written as a requirement, not as a field name, **because this session did not read the
   pipeline's publish code**.
3. **A second amber pill on screen, `Category unconfirmed`**, alongside the existing ones rather than
   a new value of them. A receipt with bad figures and a guessed category shows both.
4. **The confirmation is recorded, not inferred.** A receipt having moved out of the inbox is not a
   record that anyone confirmed the category.

**Step 10m's first task is the layer 2 assertion.** Claude Code measured that exchanging
`suggested_code` and `suggested_name` in the firm-lookup branch of `worker\categorisation\engine.py`
leaves all 1186 tests green. **The identical swap at layer 1 was closed; layer 2 is still live.**

---

## 6. What else is open

**Four flags raised and not fixed. None is a defect Paul has been asked to decide on yet.**

1. **The two products' VAT tolerances disagree and have since 2026-09-04.**
   `worker\validation\rules.py:12` is `0.01`. `_VAT_TOLERANCE` in `IntelliBooks-Desktop-v3.html` is
   `0.02` and its own comment says to keep the two in step. **The new Edit Receipt check uses the
   pipeline's number. The Post to Cashbook check still uses `0.02`.** Recommendation on the table and
   not yet answered: change it to `0.01`.
2. **A fifth `source` value, `folder`.** Live on five of `Client_004`'s receipts. Sub-step 10d.40
   allows four values and `folder` is not one of them. **This session did not read what writes it.**
   The Source column prints it unchanged rather than hiding it as Other.
3. **A correction clears a `possible_duplicate` finding**, Claude Code's flag.
4. **`sidecar_payload` is built and never read**, Claude Code's flag.

**Two of Claude Code's flags were checked and do not arise from Desktop.** A correction on a
`discarded` receipt cannot be sent, because deleting a receipt removes it from `books.receipts` and
`editReceipt()` cannot open one. A correction on a `bank_attachment` row cannot be sent either,
because a 10f.38 document is not in `books.receipts` by design.

---

## 7. Traps this session hit, on top of `CLAUDE.md`'s

**A filter is not a reader, again, and it nearly produced a wrong accusation.** This session
enumerated the callers of `copy_for_published_receipt()` over the five files it had staged rather
than over the repository, got four, and nearly reported Claude Code's five as wrong. **Staging all 53
non-test Python files gave five.** The rule is in `CLAUDE.md` and this session broke it anyway.

**A test written for a reason must be driven by a case only that reason explains.** Twice. A pence
comparison was "proved" by `8` against `8.00`, which in JavaScript is one number, so the mutation
swapping it for a string comparison survived. A tolerance was "proved" by a case 3p out, which fires
at 1p and at 2p alike, so widening it survived. **Both tests passed and neither tested anything.**

**Do not borrow a fact from the neighbouring rule.** The Edit Receipt mismatch was graded amber on
the reasoning that a part-rated receipt does not always add up. Part-rated means the VAT is below the
rate applied to the gross, which is a different test. Net plus VAT equalling gross is one arithmetic
statement on one receipt. **Paul broke it inside the hour by typing 0.67 on a gross of 8.00.**

**Write nothing to the record until every gate has passed.** The supplier was written before the
arithmetic check ran, so a refused save still renamed the receipt.

**Do not raise a flag as a permanent outstanding item without being asked.** This session added item
179 to `2026-08-20_LIST_outstanding_items_and_decisions.md` for a transitional artefact. Paul: it
would be raised time and time again in future, wasting tokens. It was removed byte-exact and item
178's reference to it cleared.

**Quote the paragraph, do not point at the file.** Paul had to open a long document to find a
paragraph that could have been repeated in four lines. **And never bring something to his attention
without a recommendation. If it is pure housekeeping, just do it.**

**Look at the disk before asking him again.** He reported an edit had produced no message. Reading
`Intellibills\Resolutions\` showed the note had been written correctly and the wording of the
instruction was what misled him.

---

## 8. Files this session changed, with their md5 as read back from Paul's machine

| File | Bytes | md5 |
|---|---|---|
| `IntelliBooks\App\IntelliBooks-Desktop-v3.html` | 419,012 | `b1e9054806be0b2adda0b7eb092c110e` |
| `2026-07-25_CONSOLE_DESIGN.md` | 1,307,087 | `336bbfde1bea6d96b71dbfa8c365ea71` |
| `IntelliBooks\App\Docs\IntelliBooks-Change-Log.md` | 269,812 | `ed18cbf1ccba647462b01117e3b4f95e` |
| `2026-08-20_LIST_outstanding_items_and_decisions.md` | 141,790 | `7b1de9ee3d4bb1a371797037ea4db1de` |
| `PROMPT_claude_code_2026-09-11_corrected_note.md` | 6,504 | `a99f64e5e322d93f4aff9de6e0c7a336` |
| `PROMPT_claude_code_2026-09-11_capture_report.md` | 5,148 | `41afd85e97e84a767ac4ce215fba2c3f` |

**Backups written before each Desktop pass**, in `IntelliBooks\App\`:
`IntelliBooks-Desktop-v3.html.bak-before-10f37` and `.bak-before-10k`. The second was proved
byte-exact against the file it copied before anything was written.

**Amendments 317 to 330** in the design document. **Change log items 79 to 87.**

**The design document, the outstanding list and the two briefs are committed on
`feat/console-phase0`.** Nothing is pushed.

---

## 9. Where the next chat starts

**Send `PROMPT_claude_code_2026-09-11_capture_report.md` to Claude Code.** It is step 10n and it is
written, held and unchanged since it was drafted.

**While Claude Code runs, the work that does not touch it** is 10l's Desktop half: the second amber
pill and the reason line, which amendment 330 settles the wording of. **Do not build the routing
half.** That needs the pipeline's publish code read first, and that is Claude Code's territory.

**Paul is the operator, the tester and the accounting authority.** Ask him rather than deriving. He
usually holds the answer in one sentence.

**Move fast.** He said so twice on 2026-09-11 and he was right both times.

---

## 10. What this handover does not claim

**It does not claim the pipeline's publish code was read.** It was not. Amendment 330's second key is
written as a requirement for that reason.

**It does not claim `worker\categorisation\fallback.py` was read.** Step 10l's statements about
`categorisations.needs_review` being read by nothing come from the design document's own account at
10l and 10m, which cites `fallback.py:220-227`.

**It does not claim what writes the `folder` source value.** That was flagged, not chased.

**It does not claim the whole of `2026-09-11_REPORT_claude_code_attached_document.md` was verified.**
Its structural claims about the handoff contract were, by building against them and by Paul testing
the result. Its test counts were not re-run.

**It does not claim any test of Desktop code ran in a browser.** Every Desktop assertion in this
session comes from `node --check` with a negative control, from functions lifted out verbatim and
driven under node, and from Paul using the app. There is no browser harness on this project.
