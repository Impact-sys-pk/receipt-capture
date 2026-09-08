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

**Sub-steps ~~10f.1~~ 10f.2 to 10f.7 and 10f.36. Corrected 2026-09-08 by amendment 279: 10f.1 is deferred out of this stage and is not cancelled**, because there is one destination today and a column whose every row holds the same value is not a setting yet. The pipeline gains a
firm setting per destination address, the CSV switch, and an inbox writer at
`IntelliBooks\Inbox\`: one JSON file per receipt, the image embedded, the client inside the item,
written temp-name-and-rename. **Plus the record that it published**, which 10f.36 adds and which
everything after this depends on.

**What does not change.** The on-arrival write into `Clients\` continues. Desktop does not read the
inbox. **Nothing Paul does differs, and no receipt changes route.**

**Why it is safe.** The new path writes to a folder nothing reads. **The whole stage is additive**,
and the worst outcome of a defect is a file nobody opens.

~~**Pipeline only. One brief.**~~ **CORRECTED 2026-09-08, within the hour, and the correction was found by starting to write the brief. Stage 1 is NOT pipeline only and it is three pieces, which is the shape sub-step 10e.14 already used for `client_top_folder`.**

**Piece 1, the consultant session's. TWO fields, not three. Amendment 279.** **F14**, each destination's address, and **F15**, the always-on CSV switch, become fields on **Firm Settings** in the **Intellibills Settings** card. **Both sit in the "Decided and not built yet" card today**, read there on 2026-09-08, and they move out of it. ~~**C20**, this client's publishing destination, on the **Client Settings** tab~~ **is deferred with 10f.1.** **F16 stays in that card**, being 10f.12 and stage 4's.

**Piece 2, Paul's.** He sets the values once, the way he typed `client_top_folder` at 16:32 BST on 2026-09-07.

**Piece 3, Claude Code's.** The pipeline reads the three with no default and no fallback, writes the inbox item, and records the publish. **That is the brief.**

**Why the order is fixed rather than a preference.** Sub-step 10d.19 stopped `DEFAULT_FIRM_ID` being a fallback and amendment 245 made the roots required, so **this project's own rule is that a setting the pipeline needs has no default**. A pipeline that refuses to start without a value nobody can set yet is a pipeline that cannot start. **The field comes first, then the value, then the reader.**

### Stage 2: IntelliBooks drains the inbox

**Sub-steps 10f.8, 10f.9 and 10f.10.** Desktop drains automatically when a client is opened, matching
what `scanFiledReceipts()` already does, with a visible manual control and a waiting count. Section
0.5.1's check 5 is reworded for one folder.

**What does not change.** The pipeline still files into `Clients\` and Desktop still reads that too.
**A receipt now arrives by two routes, and Desktop has to take one and ignore the other.** How it
tells them apart is the one design question in this stage and it is not yet answered.

**Why it is safe.** The old route is untouched, so a drain that fails leaves the system exactly as it
is today.

**Desktop only. One brief. The consultant session writes it, per amendment 242.**

### Stage 3: the acceptance test

**Sub-step 10f.29.** Section 0.5.1's six checks in
`2026-07-31_PLAN_reset_and_restructure.md`, run against both routes live.

**Paul's, not a session's.** It needs a real receipt from the phone, a Review item, and a post.

**Passing it is what releases 18.2b's freeze.** Nothing in stage 4 may start before it passes.

### Stage 4: the old route is switched off

**Sub-steps 10f.11 to 10f.17.** The client folder copy becomes Intellibills' own function with the
three triggers per firm, the on-arrival write stops at all three call sites, the recovery sweep is
repointed to publish, `fileReviewReceipt()` stops writing into `Clients\`, and the Review queue stops
touching the pipeline's folders.

**This is the stage that can lose a receipt** and it is the reason for the three before it. It is
also the largest: three codebases in one window, which is what sub-step 10a.2 and step 10d both
needed and both survived.

**Two briefs at least, and they land together or not at all.**

## 3. What is not in any stage, and why

- **10f.24 to 10f.27**, the remaining duplicate work. 10f.24 needs the publish step to exist before a
  possible duplicate can be "never published", so it follows stage 1 and is not part of it.
- **10f.28**, the Desktop status pill, and **10f.30**, the live checks. Both wait for the Receipts tab
  to settle, which stage 4 does.
- **10f.34**, the Review queue's all-clients view. It comes after 10f.15, so after stage 4.
- **Item 174** and **item 176**. Recorded, not scheduled.

## 4. The open questions, and each is Paul's

1. **How Desktop tells an inbox receipt from the same receipt arriving the old way**, during stage 2
   when both routes run. **This is the one that blocks stage 2 from being briefed.**
2. **Which of the three client-folder-copy triggers Intellitax itself uses**, per 10f.12: on
   successful publish, at Post, or never. It is a firm setting and Paul is a firm.
3. ~~**Whether stage 1's destination work is worth building now**, given one destination exists.
   10f.1 to 10f.3 are the settings model for something with one member.~~ **ANSWERED 2026-09-08. Paul: build F14 and F15, defer 10f.1.** Amendment 279 carries the reasoning. **The address becomes a setting rather than a literal; the per-client column waits for a second destination.**
4. **Whether the test estate is cleared before stage 3 or before 10i**, which is item 168. It says
   immediately before 10i and stage 3 is a live test.

## 5. What this plan does not claim

**No stage has been briefed and none has been sized.** The staging rests on reading the sub-steps and
the code they name, not on having built any of it.

**Confidence.** High that the four stage boundaries each leave a working system, because each rests
on the old route being untouched until stage 4 and on the freeze's own close condition. **High that
one brief cannot carry it**, from the sub-step count, the three codebases and the acceptance test.
**Low on the order inside each stage**, which is the brief's job rather than the plan's.
