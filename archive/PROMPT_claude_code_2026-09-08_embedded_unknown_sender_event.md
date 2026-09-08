# Brief: the embedded path logs its unknown sender, and one housekeeping commit

**Written 2026-09-08 by the consultant session, on Paul's decision the same day.**
**Report to `2026-09-08_REPORT_claude_code_embedded_unknown_sender_event.md` in this repository root.**

**Two small things, both agreed and neither needing a decision. On no list, per `CLAUDE.md`: a
two-line edit already agreed goes on neither the build order nor the outstanding items list.**

---

## 1. The embedded-image path logs its unknown sender

**This is flag 1 of `2026-09-08_REPORT_claude_code_unknown_sender_above_loop.md`, approved by Paul.**

**The attachment path now writes one `unknown_sender` event per email. The embedded path writes
none**, and never has: its branch sends the alert, moves the email and `continue`s without calling
`_log_receipt()`.

**So a stranger who sends a photo from a share button leaves no trace in
`receipt_events_UNATTRIBUTED.ndjson`, where one who attaches a file leaves a row.** The alert and the
folder already agree on both paths. **Only the audit trail differs, and that is the last of today's
asymmetries between the two.**

**What has to be true:** both paths write the same event, in the same shape, with one per email.

**The shape is settled and it is yours from 10f.35**, so this is a copy rather than a decision: one
event per email, a null filename because there is no one attachment it is about, and a synthetic
receipt id, matching `unsupported_file_type` and `duplicate_skipped`.

**One thing to satisfy yourself about rather than assume.** The attachment path passes
`config.UNATTRIBUTED_FIRM_ID` as the firm. Check that is right on the embedded branch too, and say so
either way. **The two paths writing the same event with different firm ids would be a new
divergence**, which is the thing today has been spent removing.

## 2. One housekeeping commit, and the change in it is not yours

**`.env.example` is modified in the working tree and it is the consultant session's**, made this
morning on Paul's instruction and flagged by you correctly as not yours. **Paul has asked you to
commit it**, because git writes stay off the Cowork sandbox entirely, per the third trap.

**What is in it, so you can check the diff says only this.** Two defects from
`2026-09-07_HANDOVER_consultant_session_17.md` section 7, both confirmed before the edit:

- **The IMAP block carried the live host and the capture address while the SMTP block used
  placeholders.** `IMAP_HOST` and `IMAP_USERNAME` are now placeholders in the SMTP block's style, and
  the comment above them is rewritten to say the four settings are required and that `IMAP_PORT` is
  the one that defaults.
- **The comment on `RESOLUTIONS_DIR` said the blank fallback is `IntelliBooks\Resolutions`.** It is
  `Intellibills\Resolutions`, which is what `config.RESOLUTIONS_DIR` composes from
  `INTELLIBILLS_ROOT`. Read in `config.py` before the edit.

**Its own commit, separate from section 1's.** **If the diff contains anything but those two changes,
stop and report it rather than committing**, because that would mean a third writer.

## 3. Out of scope

- **Item 174**, the missing `is_duplicate(message_id, att_id)` check on the embedded path.
- **Sub-step 10f.34**, the Review queue's all-clients view.
- Your flag 2 from the 10f.33 report, the `no_attachment` alert path.
- **Section 18.2b's freeze stands.**

## 4. Standard of evidence

- **Red before green**, quoted. The obvious test is a stranger sending an embedded photo and one
  event appearing where none did.
- **Prove one event per email on both paths**, on a two-item email from a stranger, and print the two
  events side by side so their shapes can be compared rather than described.
- **Mutations from a pristine copy, each anchored to one place with its diff printed.** **Anchor with
  care**: the two unknown-sender branches now hold near-identical lines at different indentation, and
  that is the substring collision your harness refused twice yesterday.
- **Quote passes and subtests separately.**
- **Flag, do not fix. Disclose your own mistakes. State confidence and say what it rests on.**

## 5. What the report has to carry

`2026-09-08_REPORT_claude_code_embedded_unknown_sender_event.md`, in this repository root.

1. The two events printed side by side, one per path, produced by the test.
2. Red output before the change.
3. What you concluded about the firm id on the embedded branch, and why.
4. The mutation results with diffs.
5. The `.env.example` diff you committed, and confirmation it contained only the two changes named
   above.
6. The suite, passes and subtests, measured both ends.
7. Anything you flagged, and anything this brief got wrong.
