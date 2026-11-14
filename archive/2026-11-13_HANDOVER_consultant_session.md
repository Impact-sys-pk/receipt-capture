# Handover, consultant session, 2026-11-13

Written at 13:31 GMT, updated 15:02 GMT, 2026-11-13. Cowork consultant
session.

**Nothing in this session has been written to any file in
`C:\LastingImpact\receipt_capture` or to
`IntelliBooks-Desktop-v3.html`.** The link to Paul's computer dropped
part way through and had not returned when this was written. Readings
below came either from copies staged into the session before the link
dropped, or from query output Paul ran on his own machine and pasted.
Each claim says which.

## Part one, the approval status work

Paul was processing real receipts and could not tell from the Receipts
tab in IntelliBooks Desktop which receipts he had already approved.

### The existing vocabulary, read rather than recalled

`receipts.status` in `receipts.db`, eight values. Column declared in
`worker\database\schema.py` line 123. The six in `PROCESSED_STATUSES`
are at `worker\database\repository.py` lines 38 to 45.

| Value | Meaning |
|---|---|
| `pending` | Written by `save_receipt()`. Stored, nothing has read it. |
| `ok` | Extracted and validated with no problems. |
| `needs_review` | Extracted, validation flagged something. |
| `possible_duplicate` | Looks like a document already held. |
| `failed` | Read, and no usable data came off it. |
| `retry_exhausted` | Failed and past `AUTO_RETRY_MAX_AGE_DAYS`. |
| `discarded` | A person discarded it after the pipeline read it. |
| `bank_attachment` | Attached to a bank line in IntelliBooks Desktop and handed over to be archived. Never extracted, validated or published. |

The Status column on screen is a different axis and is stored nowhere.
`renderReceipts()` draws two row types. A filed row gets `Attached` or
`Not attached`, line 4746, from a membership test over the
transactions. A review row gets `reviewPills()`, line 5887, drawing on
`validationPill()`, line 3663, plus a separate `Category unconfirmed`
pill.

### Why attached receipts stay on the Receipts tab

From `2026-07-25_CONSOLE_DESIGN.md` section 20, lines 2862 to 2871.
Paul's decision of 2026-09-16, headed "A receipt record is not retired
when it becomes a transaction". Four reasons: size is not a reason, at
about 452 bytes a record; its figures cannot reach the accounts after
that point; retiring it would put the same thing in two places, because
a Bank Transactions row looks the receipt up by id; and the consequence
was accepted rather than discovered later.

### Defect found and flagged

Line 2871 of `2026-07-25_CONSOLE_DESIGN.md` says the Receipts tab
"defaults to Not attached and filters by tax year". It does not. The
select at `IntelliBooks-Desktop-v3.html` line 226 has `All receipts`
first with an empty value and nothing sets `rf-status` at startup. Paul
confirmed it from the screen. His ruling: the code is wrong and the
default should be Not attached.

### Paul's decisions, all 2026-11-13

- The Status column on a filed receipt row holds exactly one of **To
  Approve**, **Approved**, **Attached**. Pink review rows keep their own
  pills.
- **Absence of an approval stamp means To Approve.** Nothing is written
  on arrival. Matches how `categoryUnconfirmed` already behaves.
- **To Cashbook, and attaching from the Bank Transactions tab, both
  imply approval** and write the stamp. Near precedent is amendment 324.
- **Editing after approval does not clear the approval.**
- Row shading on all three statuses, pastel, pill still drawn on every
  row. Paul will test it.

| Status | Pill | Row shade |
|---|---|---|
| To Approve | amber `#fff3e0` / `#e65100` | `#fffaf3` |
| Approved | green `#e8f5e9` / `#2e7d32` | `#f6fbf7` |
| Attached | grey `#eceff1` / `#455a64` | `#fafbfc` |

Precedence when drawing: Attached, then Approved, then To Approve.

Blue was Paul's first suggestion for Attached and was changed on advice,
because blue is `.pill.new` on Bank Transactions, where it means a
transaction that still needs posting. The three row shades are the
consultant session's values. Paul has not seen them on screen.

### Where the approval stamp has to live

`Intellibills\Receipts\{client_id}-receipts.json`, read by
`loadReceipts()` at line 1482, described at line 1087. **The pipeline
cannot assign To Approve**, because it does not write that file. It
publishes one `{receipt_id}.json` and `drainInbox()` in the front end
writes the record. This is why absence was chosen to mean To Approve.

This is the first stored state on a receipt record. Section 20 lines
2857 to 2860 record the hazard: every path that changes the receipt has
to clear a stored flag and one always forgets. Paul's ruling that
editing does not clear the approval removes the hazard rather than
managing it.

## Part two, the categorisation findings

Paul asked how the pipeline decided the category on his last few
receipts. Four queries were run by Paul and pasted back. Everything in
this part rests on that output and on
`worker\database\repository.py`, which was staged before the link
dropped.

### What was found, in order

**The classifier is on for this firm.** `match_source = ai` on the PGG
rows. The consultant session had earlier stated the designed default
from `config.py` as though it were the live state, without reading
`firms.json`. That was wrong and is recorded here as its own error.
`firms.json` has still not been read.

**Duplicate `categorisations` rows are an audit trail rather than a
fault.** Every manual correction writes a new `extractions` row with
`engine = manual_correction` and a fresh `categorisations` row. The
consultant session flagged this as a defect and withdrew the flag.

**The AI categorised a fuel receipt on one word of the trading name.**
`52e76e99`, Park Garage Group, fuel £40.45. The first run suggested
7301 Fuel and oil at low confidence. The correction run suggested 7340
Parking and tolls, also low, also `ai`. Paul corrected to 7301. The
suggestion now stored in the audit trail is Parking and tolls, a value
never shown on screen.

**A correction re-runs the categorisation engine, deliberately, and on
a receipt with no client mapping that means a fresh AI call.** First
suspected from timestamps: the `manual_correction` extraction on
`52e76e99` is followed by a categorisation 1.28 seconds later with
`match_source = ai`, while the two Shell corrections took 3
milliseconds each with `match_source = client`. Then established by a
`Select-String` over `worker\resolution\service.py`, run by Paul. Line
1006 is the docstring "Apply corrections, re-validate, categorise,
file. Append-only throughout." Line 1280 reads "8. Categorise, then
save the engine's suggestion. Never overwrite", with the call to
`categorisation_engine.categorise()` at 1283. Line 2305 reads
"Categorise for the audit trail, exactly as 4.3 step 8 does." Line 2695
says the function "categorises, applies the category as a GL override
and learns on the tick."

**The audit trail this produces records the wrong moment.** The
suggestion stored against a correction is the one the engine made at
correction time rather than the one the operator was shown. On
`52e76e99` those differ: Fuel and oil on the original run, Parking and
tolls on the correction run, same document, both low confidence. Paul
ruled for option B, which is item 11.

Only the four cited lines and their neighbours were read. The function
bodies in `worker\resolution\service.py` have not been read.

**`needs_review` on a `categorisations` row may still be written and
never read.** Amendment 228, 2026-09-05, says four call sites write it
and nothing reads it, and that validation status is what routes a
receipt to review. Both PGG rows carry `needs_review` 1 and low
confidence, and nothing on screen said so. Whether the
`category_unconfirmed` key from amendment 330 now covers this is unread.

### The lookup defect, which is the main finding

Read in `worker\database\repository.py`:

- `categorisations_client_vendors` is unique on `client_id`,
  `vendor_key`, `vendor_name`. `upsert_client_vendor()` at line 649
  checks all three, so each name variant gets its own row.
- `get_client_vendor()` at line 638 takes `client_id` and `vendor_key`
  only. It ignores `vendor_name`, orders by `times_seen DESC,
  last_updated DESC`, and takes `LIMIT 1`.

So the engine keeps the distinction when it writes and discards it when
it reads. `get_firm_vendor()` at line 685 has the same shape.

Proved against the live table. `Client_007` holds three rows on key
`shell`:

| vendor_name | Code | times_seen | last_updated |
|---|---|---|---|
| Shell U.K. Oil Products Limited on behalf of Shell UK Limited | 7302 EV charging | 3 | 12:46:33 |
| Shell Co-op Harborne | 7301 Fuel and oil | 3 | 12:36:28 |
| Shell U.K. Oil Products Limited | 7302 EV charging | 2 | 12:01:50 |

**Standing prediction, untested.** The next Shell receipt for
`Client_007` will come back 7302 EV charging at high confidence with no
review row, whatever it is for, until a Shell variant is taught a fourth
time.

### A second problem, kept separate

"Shell U.K. Oil Products Limited" and "Shell U.K. Oil Products Limited
on behalf of Shell UK Limited" are one supplier read off the receipt two
ways. Exact name matching treats them as two, which fragments
`times_seen` and means teaching one does nothing for the other. Not
designed. On the list as item 10.

## The change list

Nothing on it has been started. Paul said twice not to edit yet.

1. Remove the View button from the Options column on the Receipts list.
   It does the same as the image button on the left of the row.
2. Receipts tab filter to default to Not attached.
3. Status column holds one of To Approve, Approved, Attached, with the
   colours and row shades above.
4. Absence of an approval stamp means To Approve. Nothing written on
   arrival.
5. To Cashbook and attaching from Bank Transactions both write the
   stamp.
6. Editing after approval leaves the stamp alone.
7. Approve button on every To Approve row, in the Options column, one
   click per receipt. Approve also on the selection bar, for a batch.
   Approve and Save button on the Edit Receipt card. Paul's decision,
   both placements rather than one. **Approve refuses a receipt with no
   category**, with a tooltip saying why, the same way To Cashbook is
   already disabled when the gross is zero.
8. Bulk category change on the Receipts tab. Select by status To Approve
   and exact supplier name. Set one category. Apply to all selected. The
   code is written as given, with no categorisation run per receipt. The
   `Remember this supplier for this client` tick appears in the bulk
   dialogue, unticked on every open, matching the single receipt
   behaviour. Paul's decision, option 3 of three put to him.
9. `get_client_vendor()` to match on `vendor_name` first. No exact match
   falls back to the key **only where every variant for that key carries
   the same nominal code**; variants disagreeing means unmatched, and
   the receipt goes on to the later layers. Paul's decision, option C of
   three put to him. The consultant session said the same rule would be
   applied to `get_firm_vendor()`, which has the identical shape, and
   invited Paul to say otherwise.
10. Supplier name variants that are one real supplier. **The operator
    says when two names are one supplier. Nothing merges names on its
    own.** Paul's decision, option B of three put to him. When a
    mapping is taught and the key already holds a variant under a
    different name, the window asks whether it is the same supplier; on
    yes, the new name is written as its own row on
    `categorisations_client_vendors` carrying the same nominal code.
    The schema already allows this, because the unique key includes
    `vendor_name`, so no new table is needed. Copying the code also
    keeps the variants agreeing, which keeps item 9's key level
    fallback available for that supplier. Trimming leading and trailing
    spaces, collapsing repeated internal spaces and comparing case
    insensitively are included, being transcription noise. Anything
    that removes words is a decision and stays with the operator.

    Automatic normalisation was recommended against and refused. It has
    the shape amendment 233 rules out: a fallback that produces a
    plausible value, silently, at high confidence, with no review row.
11. A correction stops re-running the categorisation engine. The new
    `categorisations` row carries the suggestion the engine made on the
    original run, so the audit trail shows what was on screen when the
    operator decided. Paul's decision, option B of three put to him.
12. The approval stamp is a single key `approvedAt` on the receipt
    record, holding an ISO 8601 UTC timestamp, absent until the receipt
    is approved. Paul's decision.

    A timestamp rather than a boolean, because absence already means To
    Approve and a boolean would give two ways of saying one thing. The
    comment on `categoryUnconfirmed` in
    `IntelliBooks-Desktop-v3.html` records what that costs: the test
    there is `=== true` rather than a truthiness test because a value
    of 1 and a missing key both had to be handled.

    camelCase, because the receipt record's own keys are the front
    end's and `addedAt` is the precedent. The snake_case keys
    `archive_path` and `category_unconfirmed` are on the pipeline's
    published item rather than on the receipt record.

    UTC, because everything stores UTC and displays London through
    `worker\london_time.py`.

    **No `approvedBy`.** Nothing reads it and Paul is the only person
    approving. Cost of leaving it out, stated and accepted: receipts
    approved before any later change carry no name and cannot be given
    one.

    **Watch, rather than build now.** `approvedAt` is written and read
    by the front end alone, so it is not a `config.py` constant yet.
    The moment anything in the pipeline needs it, for example the
    capture report counting approved receipts, it becomes shared
    vocabulary and the constant has to be added before the second
    reader is written.

Item 9 needs the caller to pass the supplier name into the lookup. Where
that call is made is in `worker\categorisation\engine.py`, which has not
been read, so no function in it is named here.

## Settled on 2026-11-13, after the twelve items

Paul was given recommendations on all seven remaining points and said
he agreed with all of them.

- **`get_firm_vendor()` gets item 9's rule**, same as
  `get_client_vendor()`. The firm table appears to be empty, so the
  change is free to make now.
- **`2026-07-25_CONSOLE_DESIGN.md` line 2871 is left alone.** Item 2
  changes the code to open on Not attached, which makes the sentence
  true. The amendment records that the two disagreed and that item 2
  resolves it.
- **Today's work goes into the design document as one amendment**,
  covering the twelve items, the lookup defect proved against the live
  table, and the consultant session's own two errors.

### Build order, agreed

1. Item 9. The only item producing wrong figures in the books right
   now. One function, defect proved, fix small.
2. Item 11. Same correction path, small.
3. Items 1, 2, 3, 4, 5, 6, 7, 12 as one piece. All of them touch the
   Receipts tab render and the approval stamp. **Item 1 sits inside
   this group rather than ahead of it**, which supersedes Paul's
   earlier instruction that the View button removal goes first. He
   agreed to the change in order.
4. Item 8. Bulk change filters on the To Approve status, so that has to
   exist first.
5. Item 10. Needs `engine.py` read, and item 9 reduces the harm it
   causes meanwhile.

### The three reads, now done

Done on 2026-11-13 by Paul running `Select-String` and `Get-Content`
over his own machine and pasting the output. The link was down
throughout. Nothing was staged.

**How a supplier name becomes a key.** `normalise_description()` at
`worker\categorisation\engine.py` line 128 lowercases, strips bank
prefixes, removes reference numbers of six or more digits and digit
fragments of one or two, then drops anything in `NOISE_WORDS` and any
single character word. `extract_vendor_key()` at line 151 then returns
an alias if the whole string or the first word is one, strips trailing
numbers and anything in `LOCATION_WORDS`, and **keeps only the first
word where more than two remain**.

Traced against Paul's three live keys:

- Shell U.K. Oil Products Limited on behalf of Shell UK Limited: noise
  removal drops `limited`, `uk`, `on`, `of`, leaving six words, so the
  first is kept. Key `shell`.
- Shell Co-op Harborne: three words survive, so the first is kept. Key
  `shell`.
- Park Garage Group: `garage` is in `LOCATION_WORDS` and is stripped,
  leaving two words, which is not more than two, so both are kept. Key
  `park group`.

No alias was involved. `DEFAULT_ALIASES` holds nine entries, for
Amazon, PayPal, TfL, SumUp and Google.

**The layer order**, from the module docstring, which records that the
file once numbered its layers three different ways: 0 client rules, 1
client lookup, 2 firm lookup, 3 fuzzy against the client's keys, 4
fuzzy against the firm's keys, 5 AI. Unmatched is not a layer.

**Item 9 is smaller than it looked.** `categorise()` at line 268
already takes `supplier_name`, so the exact name is in hand at the
lookup. Nothing upstream changes.

**Item 10's design stands.** The alias dictionary is hardcoded and firm
wide with nothing writing to it, so it is not the place to record that
two names are one supplier.

**The hold reads `match_source`, not `needs_review`.**
`category_is_unconfirmed()` at `worker\publish.py` line 357 returns
true when `match_source` is in `MACHINE_MATCH_SOURCES`, which is
`frozenset({"fuzzy_client", "fuzzy_firm", "ai"})` at line 354.
Amendment 330 put the hold on `categorisations.needs_review` and
**amendment 333 superseded that**, because `needs_review` is true for
layers 3, 4 and 5, for all three unmatched sites, and at two points in
`resolve_against_chart()` whatever the layer, so reading it held 25 of
26 rows on the live database including hand-taught mappings.

So layers 0, 1 and 2 drain to the filed list with nothing on them, and
layers 3, 4 and 5 are held in the review queue with a `Category
unconfirmed` pill. Paul's three Shell receipts matched at layer 1 and
drained, which is why a wrong category arrived looking settled. The
cause was the lookup defect alone.

`categorisations.needs_review` is still written in many places and the
hold no longer reads it. **Whether anything else reads it is open
again**, and amendment 228's claim from 2026-09-05 is at least
out of date in its reasoning.

### Flagged on 2026-11-13, and settled the same day

Paul accepted the recommendation on all four. Three produce no change.
The fourth adds a refusal to item 7.

**No change, and the reasoning, so it is not re-opened by a later
session.**

- The hardcoded location and trade word lists stay as they are. Item 9
  makes the key a coarse bucket that matters much less, because the
  lookup matches the full name first. Editing a hardcoded list to chase
  one client's town is tuning with no owner. If it still matters once
  item 9 has been live a while, the answer is a per firm editable list,
  which is a piece of work rather than an edit. **The two word list
  flags are one decision and are to be taken together**, because they
  are the same question from two sides.
- **The south east list missing Birmingham contributed to the collision
  rather than causing a separate problem.** Stripping a location word
  shortens the name, and the key builder keeps every word when two or
  fewer remain. Had Harborne been on the list, "Shell Co-op Harborne"
  would have produced the key `shell co-op` rather than `shell`.
- The 0.70 fuzzy threshold stays. No defect has been observed, only a
  shape that could produce one, and it already fails safe: a fuzzy
  match is held in the review queue as unconfirmed. If a wrong fuzzy
  match is ever seen there, that is the moment to lower the threshold
  or log the score.
- The hold is not extended to `unmatched`. Item 3 makes a blank
  category correct by construction: the filed list filtered to Not
  attached is the approval queue, and an uncategorised row sitting
  there as To Approve is where it belongs. The blank is visible, which
  satisfies the rule that an unrecognised value must appear rather than
  disappear.

**Added to item 7.** Approve refuses a receipt with no category, with a
tooltip saying why, the way To Cashbook is already disabled when the
gross is zero. Without it, bulk approve lets an uncategorised receipt
out of the queue in one click and nothing asks about it again.

### What the location word list is for

Read off the behaviour. The constant carries no comment; the only
written hint is beside the truncation rule, which says it exists to
avoid verbosity and gives `apcoa hal ss` becoming `apcoa`.

Its purpose is to make every branch of one supplier produce the same
key, so a mapping is taught once rather than once per branch. Shell
Dartford, Shell Bromley and Shell Sidcup all become `shell`. The
branch format words do the same job for Tesco Express, Extra, Metro and
Superstore.

**The whole design assumes one supplier means one code.** That holds
for a supermarket and for parking. It breaks for a fuel brand that also
sells electricity, which is the live case. Item 9 is what stops the
assumption being enforced where it does not hold.

### Superseded flag list, kept for the reasoning above

- **The word lists are hardcoded and tuned to south east London and
  Kent.** `LOCATION_WORDS` holds Dartford, Bromley, Swanley, Croydon,
  Greenwich, Lewisham, Bexley, Sevenoaks, Maidstone, Orpington, Sidcup,
  Eltham, Woolwich and Erith. The live client is in Birmingham.
  Harborne, Bearwood and Wolverhampton are absent, and `NOISE_WORDS`
  carries Birmingham. Nothing on screen lets Paul edit any of it.
- **The same list strips `garage`, `petrol`, `station`, `express`,
  `local`, `extra`, `superstore` and `metro` as locations.** For a
  private hire client those are trade words. It is why Park Garage
  Group lost the word saying what it is.
- **Fuzzy matching runs at a 0.70 `SequenceMatcher` ratio on the keys**,
  `engine.py` line 183, used at lines 351 and 370. Keys are short, and
  0.70 on short strings is loose. A fuzzy match is held as unconfirmed,
  so it surfaces rather than landing silently.
- **An `unmatched` receipt is not held.** `unmatched` is absent from
  `MACHINE_MATCH_SOURCES`, so an otherwise `ok` receipt with no
  category drains to the filed list. The Category column is blank,
  which is visible, so this may be correct rather than a fault.

### To check when item 9 is built

With item 9 in place, a new Shell variant with no exact row returns
nothing at layers 1 and 2 and falls to layer 3, which fuzzy matches on
the key. `fuzzy_match("shell", ...)` scores the key `shell` at 1.0, so
layer 3 may re-introduce the collapse item 9 exists to stop. **If it
does, the result carries `match_source` `fuzzy_client`, which is held
as unconfirmed**, so the receipt surfaces for review rather than
landing silently. That is probably the right outcome, and it has not
been read: lines 351 to 385 of `engine.py` were seen in a search
result rather than opened.

Then write the amendment, then build.

## What was read

Staged copies, from before the link dropped:

- `worker\database\repository.py`, `worker\database\schema.py`,
  `worker\validation\rules.py`, `config.py`, `app.py`,
  `view_receipts.py`, `2026-07-25_CONSOLE_DESIGN.md`
- `IntelliBooks-Desktop-v3.html`

Read in part rather than in full: `app.py`, `config.py`,
`2026-07-25_CONSOLE_DESIGN.md` and `IntelliBooks-Desktop-v3.html`. The
line numbers cited above were read. Nothing else in those files was.

`2026-07-25_BUILD_STATUS.md` was staged and searched. No section of it
was read.

Not read at all: `worker\categorisation\engine.py`, `firms.json`,
`CLAUDE.md`, `AGENTS.md`, `CATEGORISATION.md`.
`worker\resolution\service.py` was searched by Paul and not opened.

Four queries were run by Paul on his own machine and pasted: the last
five `categorisations` rows by receipt creation, the same filtered to
Park Garage Group, the run history for two receipt ids, and the whole of
`categorisations_client_vendors`.

### One error in the queries, the consultant session's

The first query put `LIMIT 5` on the joined rows rather than on
receipts, so it returned five rows covering three receipts when five
receipts were asked for.

---

## Where it got to, 2026-11-13 evening

Ten of step 10bs's twelve sub-steps are built. **10bs.8 and 10bs.10 are
what remain.** Amendment 549 in `2026-07-25_CONSOLE_DESIGN.md` records
all of it, and step 10bs's body in `2026-07-25_BUILD_STATUS.md` is
marked accordingly.

**The front end, 10bs.1 to 10bs.7 and 10bs.12.** Built by the
consultant session in `IntelliBooks-Desktop-v3.html` and tested on
screen by Paul the same afternoon. `node --check` over the whole script
block with a negative test, the three new pure helpers driven directly
over thirteen cases, the written bytes read back off OneDrive and
checked again, and `IntelliBooks-Desktop-v3.html.bak-before-10bs`
written first.

**The pipeline, 10bs.9 and 10bs.11.** Built by Claude Code in `f69aba8`
and `dd7d290` on `feat/console-phase0`. Suite 1657 passed, 2 skipped,
the same two skips as before. Report at
`2026-11-13_REPORT_claude_code_vendor_lookup.md`, uncommitted by its
own statement. Verified by the consultant session against the code and
against `.git\refs\heads\feat\console-phase0` rather than against the
report.

**Paul's decision on the case nobody had ruled on.** A correction with
no original run to copy writes an `unmatched` row, no code, confidence
`none`, with his code in the correction columns beside it. The
knock-on, also accepted: the firm pool is taught less, and two of the
nine live firm rows would not be taught today. Both recorded as
intended in amendment 549 so neither is later read as a regression.

**Layer 3 does hand back the mapping layers 1 and 2 now refuse**, and
the result is held for review because it carries `fuzzy_client`. Pinned
by a test, so changing it later is a deliberate edit.

**Amendment 548 is corrected by 549.** Its prediction said the wrong
Shell answer held until a variant was taught a fourth time. The two
leading rows were tied at three sightings, broken by which was updated
last, so teaching Shell Co-op Harborne once more would have flipped it.
The error is the consultant session's: a statement about a set written
from the shape of the data rather than from running the query.

### Still to do, in order

1. **Paul**: send a Shell forecourt receipt and a Shell EV receipt
   through and confirm each gets its own code. Not yet done.
2. **Paul**: correct one receipt and confirm no fresh AI call, and that
   the stored suggestion is the original run's. Not yet done.
3. Claude Code: the three small fixes it offered, report sections 5.3,
   5.4 and 5.5, accepted by the consultant session as routine.
4. 10bs.8, bulk category change. First establish whether it needs
   anything in the pipeline.
5. 10bs.10, name variants.
6. **Paul**: the Tesco fact. What the Supplier column says on a Tesco
   fuel receipt and on a Tesco shop receipt.

### A fault in the tooling, recorded because it nearly went unnoticed

**Two writes to Paul's machine reported success and did not land.**
`device_commit_files` returned `written` with no rejections, and the
files still held their old bytes. Both were caught by reading the file
size back off the machine afterwards; a forced second commit landed
each time. **Every file written to that machine in this session should
be read back rather than trusted to the result**, and the two caught
this way were `2026-07-25_CONSOLE_DESIGN.md` with
`2026-07-25_BUILD_STATUS.md`, and this handover.
