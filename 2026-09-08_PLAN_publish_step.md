# The publish step: a staged plan

**Written 2026-09-08 by the consultant session. Sub-steps 10f.1 to 10f.17 and 10f.36 of
`2026-07-25_CONSOLE_DESIGN.md`.**

**This is a plan and not a brief.** It exists because the publish step cannot be one brief, for the
reason below, and because a change this size has had a plan every other time on this project: step
10d ran as five stages, section 17.5a as six, and the reset has `2026-07-31_PLAN_reset_and_restructure.md`
which is still live.

**Nothing here is decided. Every stage boundary is Paul's to accept or move.**

---

## 1. Why it cannot be one brief

**Eighteen sub-steps across three codebases**, being the pipeline, `IntelliBooks-Desktop-v3.html`
and the settings pages, plus an acceptance test that needs a real receipt from a phone.

**And it cannot be done piecemeal either**, which is the harder constraint. Amendment 106 requires
the publish step and the client folder copy to land together. Section 18.2b's freeze holds
`get_client_directory()`, `file_receipt()` and `make_enriched_sidecar()` until the handoff passes its
acceptance test. **Sub-step 10f.13 stops the on-arrival write into `Clients\`, and that write is
today the only route a receipt has from capture into the books.** Land it before the drain works and
receipts stop reaching IntelliBooks with nothing reporting it.

**So the requirement is stages that each leave the system working**, rather than one change or
seventeen.

## 2. The staging

**Four stages. The test of each is that Paul could stop after it and the practice still runs.**

### Stage 1: the pipeline publishes as well as filing

**Sub-steps ~~10f.1~~ ~~10f.2 to 10f.7~~ 10f.2 and 10f.4 to 10f.7, and 10f.36. Corrected 2026-09-08 by amendment 279: 10f.1 is deferred out of this stage and is not cancelled. Corrected again the same day by amendment 280: 10f.3 is deferred with it, so F15 leaves this stage too and piece 1 is F14 alone**, because there is one destination today and a column whose every row holds the same value is not a setting yet. The pipeline gains a
firm setting per destination address, ~~the CSV switch,~~ and an inbox writer at
~~`IntelliBooks\Inbox\`~~ `IntelliBooks\Incoming\`: one JSON file per receipt, the image embedded, the client inside the item,
written temp-name-and-rename. **Plus the record that it published**, which 10f.36 adds and which
everything after this depends on.

**What does not change.** The on-arrival write into `Clients\` continues. Desktop does not read the
inbox. **Nothing Paul does differs, and no receipt changes route.**

**Why it is safe.** The new path writes to a folder nothing reads. **The whole stage is additive**,
and the worst outcome of a defect is a file nobody opens.

~~**Pipeline only. One brief.**~~ **CORRECTED 2026-09-08, within the hour, and the correction was found by starting to write the brief. Stage 1 is NOT pipeline only and it is three pieces, which is the shape sub-step 10e.14 already used for `client_top_folder`.**

**Piece 1, the consultant session's. ONE field. Amendment 280.** ~~TWO fields, not three. Amendment 279.~~ **F14**, each destination's address, becomes a field on **Firm Settings** in the **Intellibills Settings** card. ~~and **F15**, the always-on CSV switch,~~ **F15 is deferred with 10f.1 and 10f.3 by amendment 280**, because nothing says what the CSV contains, where it is written or when. **F14 sits in the "Decided and not built yet" card today**, read there on 2026-09-08, and it moves out of it. ~~**C20**, this client's publishing destination, on the **Client Settings** tab~~ **is deferred with 10f.1.** **F15 and F16 stay in that card**, F15 by amendment 280 and F16 being 10f.12 and stage 4's.

**The three names, fixed by amendment 280 and carried in full at sub-step 10f.2.** The field is `publish_destinations` on the firm record in `Intellibills\firms.json`. It is an object keyed by destination. The internal destination's key is `intellibooks`, and its value is a folder name relative to the practice root. **Paul's value is `{"intellibooks": "Incoming"}`**, and the folder is `IntelliBooks\Incoming\`, renamed from `IntelliBooks\Inbox\` by the same amendment.

**Piece 2, Paul's.** He sets the values once, the way he typed `client_top_folder` at 16:32 BST on 2026-09-07.

**Piece 3, Claude Code's.** The pipeline reads ~~the three~~ **the one, `publish_destinations`,** with no default and no fallback, writes the inbox item into `IntelliBooks\Incoming\`, and records the publish. **Corrected 2026-09-08 by amendment 280: amendment 279 made it two and deferring F15 makes it one.** **That is the brief.**

**Why the order is fixed rather than a preference.** Sub-step 10d.19 stopped `DEFAULT_FIRM_ID` being a fallback and amendment 245 made the roots required, so **this project's own rule is that a setting the pipeline needs has no default**. A pipeline that refuses to start without a value nobody can set yet is a pipeline that cannot start. **The field comes first, then the value, then the reader.**

### Stage 2: IntelliBooks drains the inbox

**Sub-steps 10f.8, 10f.9 and 10f.10.** Desktop drains automatically when a client is opened, matching
what `scanFiledReceipts()` already does, with a visible manual control and a waiting count. Section
0.5.1's check 5 is reworded for one folder.

**What does not change.** The pipeline still files into `Clients\` and Desktop still reads that too.
**A receipt now arrives by two routes, and Desktop has to take one and ignore the other.** ~~How it
tells them apart is the one design question in this stage and it is not yet answered.~~ **Answered
2026-09-09 by amendment 285: it tells them apart on `receipt_id`, which both payloads carry, and
`ingestReceiptFiles()` already skips a receipt the books hold. No new mechanism.**

**Why it is safe.** The old route is untouched, so a drain that fails leaves the system exactly as it
is today.

**Desktop only. One brief. The consultant session writes it, per amendment 242. Unblocked 2026-09-09 by amendment 285, and it is written after stage 1 lands rather than now, so that Claude Code's report on piece 3 can correct it first.**

### Stage 3: the acceptance test

**Sub-step 10f.29.** Section 0.5.1's ~~six~~ **five** checks in
`2026-07-31_PLAN_reset_and_restructure.md`, **being checks 2, 3, 4, 5 and 6**, run against both
routes live. **Corrected 2026-09-09 by amendment 290: CHECK 1 IS STAGE 4'S COMPLETION TEST AND NOT
STAGE 3'S.** It requires a listing of `Clients\` before and after to be identical, and stages 1 and
2 deliberately keep the on-arrival write that sub-step 10f.13 stops in stage 4, so check 1 needed
stage 4 done while stage 4 needed check 1 passed.

**Paul's, not a session's.** It needs a real receipt from the phone, a Review item, and a post.

**Passing the five is what releases 18.2b's freeze FOR STAGE 4'S WORK and for nothing else.** Nothing in stage 4 may start before those five pass. **The freeze's other protections stand, and the interim in section 0.5 closes when check 1 passes at the end of stage 4.** Amendment 290, which narrows this freeze on amendment 113's precedent.

### Stage 4: the old route is switched off

**Sub-steps 10f.11 to 10f.17.** The client folder copy becomes Intellibills' own function with the
three triggers per firm, the on-arrival write stops at all three call sites, the recovery sweep is
repointed to publish, `fileReviewReceipt()` stops writing into `Clients\`, and the Review queue stops
touching the pipeline's folders.

**This is the stage that can lose a receipt** and it is the reason for the three before it. It is
also the largest: three codebases in one window, which is what sub-step 10a.2 and step 10d both
needed and both survived.

**Two briefs at least, and they land together or not at all.**

**Its completion test is check 1**, being a full listing of `Clients\` before and after a pipeline
run, identical. Amendment 290. **And the portal gap the reset plan asks about does not arise**:
sub-step 10f.12 builds F16 in this same window and its first trigger is on a successful publish, so
the client folder keeps filling.

## 3. What is not in any stage, and why

- **10f.24 to 10f.27**, the remaining duplicate work. 10f.24 needs the publish step to exist before a
  possible duplicate can be "never published", so it follows stage 1 and is not part of it.
- **10f.28**, the Desktop status pill, and **10f.30**, the live checks. Both wait for the Receipts tab
  to settle, which stage 4 does.
- **10f.34**, the Review queue's all-clients view. It comes after 10f.15, so after stage 4.
- **10f.3 and F15**, the always-on CSV export. **Deferred 2026-09-08 by amendment 280**, because nothing says what the CSV contains, where it is written or when, and its customer is a standalone Intellibills firm which does not exist yet. **Deferred and not cancelled**, and F15 stays in the Decided and not built yet card.
- **Item 174** and **item 176**. Recorded, not scheduled.

## 4. The open questions, and each is Paul's

1. ~~**How Desktop tells an inbox receipt from the same receipt arriving the old way**, during stage 2
   when both routes run. **This is the one that blocks stage 2 from being briefed.**~~ **ANSWERED
   2026-09-09 by amendment 285, from the code rather than by a decision: both payloads carry the same
   `receipt_id`, `books.receipts` is keyed on it, and `ingestReceiptFiles()` skips a receipt it
   already holds. Whichever route arrives first wins. Stage 2 is no longer blocked.** Its brief
   carries three things that follow: the drain shares one insert rather than adding a sixth id check,
   it filters by `client_id` rather than warning about a foreign one, and the embedded image is
   ignored where the existing row already holds a non-image file.
2. ~~**Which of the three client-folder-copy triggers Intellitax itself uses**, per 10f.12: on
   successful publish, at Post, or never. It is a firm setting and Paul is a firm.~~ **RECLASSIFIED
   2026-09-09, and it was never an open design question. It is a VALUE, not a decision this plan
   needs: F16 is the setting, sub-step 10f.12 builds the box in stage 4, and Paul types a value into
   it then, exactly as he typed `Incoming` into F14's box at piece 2 of stage 1.** **It blocks
   nothing and it cannot be answered before the box exists.** **The consultant session's error, and
   it is the same one this plan already records at question 3:** it was put to Paul as a decision to
   take now, and this plan's own sentence, that it is a firm setting and Paul is a firm, already said
   what it was. **So the four questions are one open design question at most, and question 1 closed
   on 2026-09-09.**
3. ~~**Whether stage 1's destination work is worth building now**, given one destination exists.
   10f.1 to 10f.3 are the settings model for something with one member.~~ **ANSWERED 2026-09-08. Paul: build F14, defer 10f.1.** ~~build F14 and F15~~ **Corrected the same day by amendment 280, which defers 10f.3 and F15 as well, because a switch with no defined output is not a setting yet.** Amendment 279 carries the reasoning for 10f.1 and amendment 280 for 10f.3. **The address becomes a setting rather than a literal, the per-client column waits for a second destination, and the CSV switch waits for a defined output.**
4. ~~**Whether the test estate is cleared before stage 3 or before 10i**, which is item 168. It says
   immediately before 10i and stage 3 is a live test.~~ **ANSWERED, and it moved. Item 168 closed 2026-09-13, amendment 429 of `2026-07-25_CONSOLE_DESIGN.md`: immediately before step 10i and not before, written onto step 10i's own row in section 16. This plan's question 4 is that same answer; nothing new was decided here.**

## 5. What this plan does not claim

**No stage has been briefed and none has been sized.** The staging rests on reading the sub-steps and
the code they name, not on having built any of it.

**Confidence.** High that the four stage boundaries each leave a working system, because each rests
on the old route being untouched until stage 4 and on the freeze's own close condition. **High that
one brief cannot carry it**, from the sub-step count, the three codebases and the acceptance test.
**Low on the order inside each stage**, which is the brief's job rather than the plan's.
