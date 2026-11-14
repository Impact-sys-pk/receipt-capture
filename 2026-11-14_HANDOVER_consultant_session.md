# Handover, consultant session, 2026-11-14

Written 2026-11-14, 11:30 GMT, Cowork consultant session, at Paul's
instruction, for the session that takes over.

`2026-11-13_HANDOVER_consultant_session.md` is the previous handover and
is history, not direction. Read it only for reasoning behind something
in this one. Where the two disagree, this one is later.

## Read these first, in this order

1. `CLAUDE.md`, the "How this project is worked" section, and the traps.
   The traps live there and nowhere else.
2. `2026-07-25_BUILD_STATUS.md`, section 16's head line and the step
   bodies for 10bt and 10bu.
3. `2026-07-25_CONSOLE_DESIGN.md`, amendments 548 to 561 at the end of
   the amendment record. 559, 560 and 561 are today's.
4. This file.

Everything agreed in chat on 2026-11-13 and 2026-11-14 is now in those
files. Nothing material is held only in a chat.

## What this session is

The consultant session owns verification, the design document, the
prompts, and since 2026-09-06 it also writes
`IntelliBooks-Desktop-v3.html`. Claude Code owns the Python pipeline.
Paul is the only channel between the two. He is the operator, the tester
and the accounting authority.

## Where the build is, 2026-11-14

`2026-07-25_BUILD_STATUS.md`: 77 built, 17 outstanding, 6 cancelled, 1
moved out of this order, 101 steps.

| Step | State |
|---|---|
| 10bs, approval status and the client vendor lookup | BUILT 2026-11-14, thirteen sub-steps, amendments 549, 553 and 558 |
| 10bt, the Receipts tab line items count | BUILT 2026-11-14, amendment 560. Paul has not seen a count on screen |
| 10bu, receipt rules, layer 0 | OUTSTANDING. Four decisions taken 2026-11-14, amendment 559. Nothing built |

## What is with Claude Code right now

**Nothing.** Every item briefed today has been reported, read in full
and verified against the code.

When the next one comes back, its report will be a file in the repo
root, uncommitted. **Read it in full, then verify the claims that matter
against the code and the database rather than against the report.**

Reported and verified today:

| Commit | What |
|---|---|
| `e613d26` | `import_vendor_csv.py` reports and skips a name filed under two codes |
| `90ece98` | Layers 3 and 4 record the answering variant's `vendor_name` |
| `1b6e2f5` | Layer 5 records no matched vendor. Was the vendor key, now `None` |
| `da054c4` | `line_item_count` on every published item, review branch included |
| `70dd460` | The poll stores the line items the model read. Closes the half of step 10p that was never in effect |

Reports: `2026-11-14_REPORT_claude_code_amendment_558_two_items.md` and
`2026-11-14_REPORT_claude_code_ai_matched_vendor_and_line_item_count.md`.
Both read in full by this session, both uncommitted by their own
statement. `70dd460` was reported in the chat and has no report file;
amendment 562 records it.

## Step 10bu, receipt rules: the design, settled

Paul's four decisions of 2026-11-14 are in amendment 559 in his words.
In short:

1. **A rule must not match the receipt's line items.** Paul: "NO".
2. **Scope goes in the table and the matcher now**, client and firm
   built, sector accepted but unreachable until a client can be given a
   trade.
3. **One screen lists rules and taught mappings together**, the two
   distinguished, both editable and deletable.
4. **A rule can be authored from two places**: beside the Remember tick,
   pre-filled from the receipt on screen, and from an Add rule box on
   the card.

What exists, read from the files on 2026-11-14:

- `categorisations_client_rules` at `worker\database\schema.py` line 56,
  eleven columns, `client_id NOT NULL`, no scope column.
- `get_client_rules()` at `worker\database\repository.py` line 979, one
  caller: layer 0 at `worker\categorisation\engine.py` line 252.
- `create_client_rule()` line 990 and `delete_client_rule()` line 1005:
  **no caller at all.**
- `_rule_matches()` at `engine.py` line 183, called at line 254 as
  `self._rule_matches(rule, vendor_key, supplier_name)`, so
  `condition_field = "detail"` means the supplier name.

So layer 0 runs on every receipt and can never match.

**Still to decide inside the step, and not assumed:** what a rule may
match on beyond the supplier name, the priority order where a rule and a
taught mapping both answer, and whether a firm-scope rule can be written
from a client's screen. Put those to Paul when the step is briefed.

**Next action on 10bu:** write the brief for the pipeline half. The
brief should quote step 10bu's body in `2026-07-25_BUILD_STATUS.md`, not
restate it.

## Open, flagged, nothing scheduled

Numbering is the running list Paul uses. Do not renumber it.

| # | What |
|---|---|
| 23 | The first-word truncation rule in `extract_vendor_key()`. Demoted, because layer 0 rules answer the problem it caused. Changing it moves every stored key |
| 28 | `categorisations.needs_review` is written in many places and the hold no longer reads it. Whether anything else reads it is open |
| 29 | Every row carries `business_type = UNSPECIFIED`. It comes from `trade` in `Intellibills\clients.json`, no client carries one, and no control exists to set one. A control is its own piece of work and blocks sector rules |
| 32 | `AGENTS.md` was untracked since 2026-10-25 and `git add -A` swept it into commit `c24a397`. `git rm --cached AGENTS.md` if that was unintended |
| new | The other 8 `save_extraction()` call sites do not pass line items: 5 in `app.py`, 3 in `worker\resolution\service.py`. The poll was fixed in `70dd460`; these need checking one at a time under their own brief, because some write a correction rather than a fresh read. Receipts saved before `70dd460` cannot be backfilled |

Item 24, the hardcoded `LOCATION_WORDS` and the trade words it strips,
is recorded as settled with no change in
`2026-11-13_HANDOVER_consultant_session.md`, with the reasoning. This
session's running list carried it as still open. **Treat the handover as
the record and put it to Paul if it comes up again.**

## Waiting on Paul, screen tests

1. A Shell forecourt receipt and a Shell EV receipt through the
   pipeline, confirming each gets its own code.
2. One correction, confirming no fresh AI call and that the stored
   suggestion is the original run's.
3. A new multi-line receipt, confirming a number appears in the `Lines`
   column on the Receipts tab.

None of the three has been done.

## The Desktop half of 10bt, for reference

Built in `IntelliBooks-Desktop-v3.html` on 2026-11-14 and read back byte
for byte, 579,723 bytes:

- `LINE_ITEM_COUNT_KEY="line_item_count"` beside `VENDOR_KEY_KEY`.
- `out.lineItemCount` in `parseSidecar()`, `s.lineItemCount` in the
  inbox item parser. A number or `null`.
- `lineCountCell(r)`, returning a `.pill.lines` carrying the number only
  where the count is 2 or more.
- A `Lines` column between Category and Net, on the receipt rows and the
  review rows. Empty-table `colspan` raised to 12.

**Blank covers 0, 1 and absent.** Absent reading as blank is this
session's decision, not Paul's, and it is recorded as such in amendment
560: every receipt already on the tab was published before the field
existed.

## Method, and the two faults to avoid

- **Read the report in full, then verify the claims that matter against
  the thing itself.** Verifying does not replace reading.
- **A claim about a set is checked before it is written down**, by
  enumerating the set. Both wrong claims of this class on this project
  were given away by a count asserted about a set never enumerated.
- **`device_commit_files` has reported success while leaving old bytes.**
  Read every file back off Paul's machine after writing it. Every write
  in this session was read back and compared.
- **`IntelliBooks-Desktop-v3.html` is LF throughout. `CLAUDE.md` is
  CRLF**, 962 of them, and a text-mode edit strips them. Edit it at byte
  level. The design document and the build status are LF.

## Faults disclosed by this session, 2026-11-14

- The sub-step numbers `10bt.x` were written into
  `IntelliBooks-Desktop-v3.html`'s comments before step 10bt existed.
  The step was named in the code and recorded in the documents
  afterwards, which is the wrong order. The number is kept because the
  code carries it. Recorded in amendment 560.
- `2026-07-25_BUILD_STATUS.md` carried step 10bs as BUILT in the table
  and OUTSTANDING in its body. Corrected the same morning.
- This session proposed holding step 10bu's four decisions out of the
  design document because it held its own wording of the questions
  rather than Paul's. Paul rejected that, supplied the four questions
  and his answers, and they went in verbatim. **Do not leave a decision
  in a chat. Put it to him and write it down.**
