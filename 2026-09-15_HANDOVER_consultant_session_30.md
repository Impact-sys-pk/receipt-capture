# Handover: consultant session 30

**Written 2026-09-15, 13:30 BST, by the consultant session in Cowork on the Receipts capture App project.**

You are the consultant session. You own verification, the design document, the prompts, and `IntelliBooks-Desktop-v3.html`. You cannot see the Claude Code session or the IntelliBooks Desktop session. Paul is the only channel.

---

## 0. START HERE. Paul's instruction: reproduce this table verbatim in your first reply

**Open your first reply by reproducing this table exactly as written. Do not reword it, reorder it, or renumber it.**

| # | Item | State |
|---|---|---|
| 1 | **Where records of receipt documents live.** The question you raised yesterday. | Open. Every rule I gave you as the reason against moving them is now struck. Nothing in any document forbids either shape. |
| 2 | Re-check yesterday's amendments 458 to 472 against the code. | Promised, not started. You said to do it after the fundamental issue. |
| 3 | `2026-09-14_REPORT_claude_code_filed_path_on_delete.md` sits untracked in the repo. | I cannot tell you I have read it. If I have not, that is a report asked for and not read. |
| 4 | Three Claude Code briefs queued: schema drift check, two year flags, mkdir membership. | Written, not sent. |
| 5 | Step 10au's two-direction comparison. | Built, never run. Needs a receipt attached or posted, then the button. |
| 6 | Receipt `bbe45473`, attached from the Bank Transactions tab, no client folder copy and no `filed_path`. | Unexplained since yesterday. |

**Then say this, and nothing more, about what has changed since the table was written:**

- **Row 3 is closed.** The report was read in full and its claims verified against the code. Amendment 482. Claude Code built nothing and was right to: the change shipped on 2026-09-10 in commit `a96627a`, four days before the brief was written. One row stays open out of it, and it is now item 7 below.
- **Row 1 is still the pick.**

**One item is new since the table was written:**

| 7 | Receipt `a96ab8f7-3af1-42e7-bd98-dee8be2529b8`, `Client_004`, status `discarded`, still carries a `filed_path`. Its own `resolution_events` row records `filed_path_cleared`. | Unexplained. Six causes ruled out by Claude Code, no seventh offered. Settling it needs Paul to discard a receipt today with the copy deleted and read the column back. |

---

## 1. Standing instructions from Paul, and they are not negotiable

1. **Send him command prompts automatically. Do not ask first.** "Please do not bother me with your own admin. Just do it."
2. **Do not append an extra item at the end of every reply.**
3. **He reads section 16 of `2026-07-25_BUILD_STATUS.md` and nothing else.** The amendment record is a file he never opens. Anything he needs to know goes in the reply or in section 16.
4. **You keep the Claude Code queue.** Hand him the next brief when the previous one reports. He will not track it.
5. **All instructions to Claude Code are drafted by you**, standing from session 28.
6. **No prose.** Bullets, tables and numbered steps. Short. Answer the question asked and stop.
7. **Start every reply with the date, time, time zone and verbosity level**, read from the clock in that reply. Never carry a time forward. This was got wrong for hours on 2026-09-14.
8. **Say what a confidence level rests on**, and name the file or record it was read in, or say plainly it has not been read.
9. **One thing at a time**, in an order agreed with him first.
10. **Never say "the app".** He will ask "which app".

---

## 2. The state at handover

- **Amendments 473 to 482 written today.** All committed, eight commits, `64878e1` through `11f3cdf`.
- **`2026-08-18_BOUNDARY_two_products.md` has a new section 0**, Paul's governing statement in his own words, and it governs everything below it.
- **18.2c's three rules are all struck.** What remains from that block is one one-way rule.
- **Uncommitted at handover**: `2026-07-25_BUILD_STATUS.md` is modified from yesterday's section 16 work and three files are untracked. A commit command is at section 7.

---

## 3. Read these, in this order, before acting

1. `CLAUDE.md`, the "How this project is worked" section and the traps. The traps live there and nowhere else.
2. `2026-07-25_BUILD_STATUS.md` section 16, in full.
3. `2026-08-18_BOUNDARY_two_products.md` **section 0 first**, then the rest. Sections 1, 3, 5, 7 and 12 all carry strikes against section 0 and several sentences in them are struck.
4. `2026-07-25_CONSOLE_DESIGN.md` section 18.2c, which is where today's work landed.
5. Amendments 473 to 482 of `2026-07-25_CONSOLE_DESIGN.md`. They carry the reasoning for every strike, including the wording that was struck.

---

## 4. What happened today, in order

**It began with Paul saying the rules were totally mixed up and asking for every rule and verbatim quote I had given him.** He was right. The list, checked word for word against the files, produced seven incorrect statements across three files.

**Items 1, 2, 6 and 7, needing no decision from him, amendments 473 to 475:**

- Boundary section 3's headline, "No function may live only in the other product", struck. It is symmetric and the rule is not. The rule is: no Intellibills function may live only in IntelliBooks.
- Boundary section 7's first condition lost its second half, "and no books code calls into it". It contradicts section 3, and nine books-side functions in `IntelliBooks-Desktop-v3.html` read `books.receipts`.
- Five places in the design document called the three rules "18.2's second rule". They live in 18.2c. All five corrected in place.
- Amendment 77 cited "rule 2 in 18.2c, never derive a location from a path", which was neither that rule nor its wording. Struck.
- `config.py`'s `EXPORTS_DIR` comment said "18.2's third rule is that each store has one owner". It is not what that rule says. Corrected in place.

**Then the three rules themselves, one decision at a time, amendments 476 to 478. Paul chose to strike all three.**

- **Rule 1**, copy at handoff never reference afterwards, struck entire. It ran both ways and only one way needs a rule. Its OneDrive reasoning was wrong on its own terms: the books file is on the same OneDrive and is the more exposed of the two. **What replaces it: Intellibills may hold no reference into IntelliBooks' store.**
- **Rule 2**, each copy must stand alone, struck entire, nothing replacing it. Its only stated reason was the coupling that rule 1's strike had just permitted. 18.8's dependent clause struck with it.
- **Rule 3**, never expect the two module stores to hold the same set, struck entire, nothing replacing it. Its premise is false: `worker/extraction_pipeline.py:522` calls `publish_receipt()` outside the `ok` branch, so every validation status reaches IntelliBooks.
- The block heading above the three is struck, and the three stay numbered where they are because five places cite them by number.

**Amendment 479.** Paul objected that 18.2c's section heading still said "the rules that keep the two stores independent". Renamed to "Data relationships, and referencing between the two stores", replaced outright rather than struck, because a heading is a label and leaving the old words struck leaves them there. The cross-reading paragraph corrected in the same pass.

**Amendment 480. Paul then gave the governing statement in his own words**, and it is section 0 of the boundary document. Six points. One product line. IntelliBooks is Mark 2 of Intellibills. Intellibills alone is not a product today. A spin-off is an option, not a plan, and would be the cloud version. IntelliBooks may depend on Intellibills; Intellibills may not depend on IntelliBooks. **They are not two independent systems.**

Struck against it: section 1's heading and its completeness claim, section 3's old test, section 5's breach framing, section 12's "the bill arrives" paragraph and its closing question.

**Paul's own test replaces section 3's**, and it is better because it returns a list: **what would come out to leave Intellibills alone?** Run on `IntelliBooks-Desktop-v3.html` the same day, from the tab markup: Bank Transactions and Reports come out whole; Receipts, Clients and Firm Settings stay whole; **Client Data and Client Settings split, and those two are the watch list.**

**Amendment 481.** Standalone Intellibills' own shell stops being work anyone owes and becomes a record. The Still open item for it is closed, not deferred. What it would carry stays listed.

**Amendment 482.** The Claude Code report on `filed_path` on delete, read in full and verified.

---

## 5. Paul's decisions today

1. Strike all four incorrect statements by striking and replacing in place, not by adding another statement about them.
2. 18.2c rule 1: strike entire, option 3.
3. 18.2c rule 2: strike entire, option 1.
4. 18.2c rule 3: strike entire, option 1. **With the rider that, depending on the review now under way, a cross-store report may not be required, so no step was created for it.**
5. Rename 18.2c's heading, because that kind of wording is what caused the problem.
6. Write his six points into the boundary document as the governing statement.
7. Reframe section 7's shell and close the Still open item.
8. Handover now, before item 1 starts.

---

## 6. My own mistakes today, disclosed

1. **I gave Paul B2 and B5 as rules without noticing that both contradict the asymmetry I quoted in the same list.** He found both.
2. **I told him that not enforcing standalone completeness now makes a future spin-off dearer.** It does not. Nothing local survives a cloud rebuild, which 18.11 already says. I wrote that sentence in the paragraph after the one recording his point that a spin-off would be a cloud rebuild. Withdrawn, and recorded in amendment 480.
3. **I wrote and sent a brief against work already built**, because `a96627a` landed on 2026-09-10 with no step and no amendment. Recorded in amendment 482.
4. Carried forward from 2026-09-14 and still true: I told him on that day that documents sit inside the books record because of 18.2c rules 1 and 2. That was wrong, and every rule I cited for it is now struck.

---

## 7. Commit state, and one command to run

Eight commits today, `64878e1` to `11f3cdf`, all of today's amendments. Left uncommitted at handover:

```powershell
cd C:\LastingImpact\receipt_capture
git add 2026-07-25_BUILD_STATUS.md 2026-09-14_NOTE_receipts_staging_store.md 2026-09-14_NOTE_terminology_review.md 2026-09-14_REPORT_claude_code_filed_path_on_delete.md 2026-09-15_HANDOVER_consultant_session_30.md
git commit -m "docs: session 29 and 30 notes, the filed_path report, and the session 30 handover"
```

---

## 8. What this handover does not claim

- **I have not re-checked amendments 458 to 472 against the code.** That is item 2 of the table and it is promised, not started. At least one of them, 465, was found wrong yesterday.
- **The four legitimate causes of a difference between the two stores are my enumeration, not a proved set.** They are a deletion in IntelliBooks, a failed publish, an undrained item, and a bank-line attachment. **None has been verified to leave a stored trace**, and that is what decides whether a cross-store report is worth building.
- **The allocation of Client Data's and Client Settings' contents between the two products is my judgement**, not any document's.
- **Step 10au's two-direction comparison has still never run.**
- **I have not opened `2026-08-15_RUNLOG_coa_august_check.md`**, which the project instructions say two sessions have failed to open.

---

## 9. Where the next chat starts

**The table at section 0, reproduced verbatim, then the two lines about what has changed.**

**Then item 1, which is Paul's open question: where records of receipt documents live.** Everything today cleared the ground for it. Nothing in any document now forbids either shape, and the vocabulary he set on 2026-09-14 is at section 0 of `2026-09-14_NOTE_terminology_review.md`: the receipt document, the record of that document, the document may become evidence for a transaction, and the record of that transaction. His stated principle with it: a record of a document contains a link to that document and one or more fields which describe the document's status.

**Do not start it by writing anything.** He has said twice that nothing is decided and that he wants it approached with total thought and analysis, and he has rejected several answers for being descriptions rather than reasons.
