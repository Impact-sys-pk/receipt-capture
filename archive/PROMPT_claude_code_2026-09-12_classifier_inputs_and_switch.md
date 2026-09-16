# Brief: the classifier's inputs and its switch

**Written 2026-09-12 by the consultant session, from Paul's decisions the same day after he ran
`probe_layer5.py` against his live database.** Step 10p of `2026-07-25_CONSOLE_DESIGN.md`, amendment
340.

**Read first, in this order:** `CLAUDE.md`, the section "How this project is worked" and the seven
traps, including the two rules added on 2026-09-11. Then step 10p's body in section 16 and amendment
340. Then 18.4, for what a split is and why item lines bear on it.

**This is the pipeline half only. The Firm Settings screen is the consultant session's and is being
written separately. Build the setting so it is read; do not build a screen for it.**

---

## 1. Three parts, and they ship together

Turning the classifier on without parts 1 and 2 is what the probe showed going wrong. Do not split
this into a smaller change.

1. **Item lines are stored on the extraction, description and amount separate.**
2. **The classifier call becomes deterministic.**
3. **The classifier's on and off becomes a per-firm setting, default off.**

---

## 2. Part 1: store the item lines

**The problem, measured rather than asserted, and re-run it rather than trusting this paragraph.**
Item lines come off the extraction call and are stored nowhere. Of the six production calls to
`categorise()`, one passes them and four do not, each of the four because it reads the extraction
back out of the database. **So the same receipt is categorised from less on every run after the
first, and nothing on screen or in the log says so.**

**What changes.**

- **The extraction result carries description and amount separately** instead of one string per line
  with the amount run into it. Today it is a list of strings capped at 40, and the vision prompt asks
  for the description and the amount on one string. **Both change.**
- **The extraction is stored with them**, on the `extractions` table, and an existing database gets
  the column by migration. **Nothing is backfilled. Paul's instruction: he does not care about the
  receipts already in the database**, whose lines were never captured and cannot be recovered.
- **Every path that re-runs the engine reads them back and passes them.** Enumerate those paths
  yourself from the syntax tree and print the enumeration whole; do not take the count from this
  brief.

**Three things to decide and report rather than choose quietly.**

- **What an amount that cannot be read becomes.** A line with no amount is ordinary on a receipt.
  Nought and absent are different answers and the difference reaches a future split.
- **Whether the 40-line cap stays**, and what a receipt with more than 40 lines stores.
- **What the classifier is sent now.** It was given the lines as printed. Report what you send it
  after the change and why, because the prompt's wording and the stored shape are now two things.

**What must not change.** The extracted supplier, date, net, VAT and gross, and every test that
asserts them. **The item lines are evidence and not an accounting record**, per 18.1: nothing here
categorises a line, posts a line, or makes a split.

---

## 3. Part 2: the classifier call becomes deterministic

**The call passes `model`, `messages` and `response_format` and nothing else**, so it samples at the
API default. On Paul's live data the probe returned two different codes for the same supplier, the
same amount and the same client: `7113 Business rates` on one receipt and `7110 Rates` on the other.

**Set a temperature of nought and a fixed seed.** Name the seed as a constant rather than writing a
literal at the call site.

**Do not claim this makes the answer right.** It makes it the same answer every time, which is what
step 10m needs before a confirmation teaches a permanent mapping.

**Test it against the real API once and report what you saw**, since a unit test with a stubbed
client proves the parameters are passed and not that the answer is stable. **One supplier, three
calls, three identical answers** is the evidence. Say what it cost.

---

## 4. Part 3: the on and off becomes a per-firm setting

- **On the firm record, default off.** The firm record is the pipeline's own file and you should read
  how the existing per-firm settings are shaped and follow them rather than inventing a shape. F16,
  the client copy trigger, is the precedent.
- **Read at the one place the pipeline constructs the engine.** Enumerate the construction sites and
  print them; there is more than one in the production tree and only one of them is the live poll.
- **`retroactive_categorise.py` stays hard off.** Turning that on re-runs history and spends money on
  receipts already dealt with. It is not part of this step.
- **Absent means off**, so a firm record written before this key existed does not switch the
  classifier on.
- **Do not add an environment variable for this.** An environment variable cannot be per firm and the
  cloud version is one service serving several firms. Amendment 340 records that and it was refused.

**Report the exact key name and its values in your report's first section**, because the consultant
session writes the screen from it and cannot see your code.

---

## 5. What must not change

- **No stored value moves**, beyond the new column. No backfill, no rewrite, no re-extraction.
- **Nothing published, re-processed, and no receipt's status moves.**
- **`categorisations.needs_review` and `match_source` are untouched**, and so is
  `publish.category_is_unconfirmed()`, which step 10l built on `match_source`.
- **Nothing written into `Clients\`, `IntelliBooks\` or `Intellibills\Documents\`.**
- **Never `import config` to read a value.** Read the constant out of the file or run under pytest.
- **Do not turn the classifier on for any firm.** The setting ships off and Paul turns it on.

---

## 6. Evidence

- **Red before green**, with the failing output quoted.
- **A test that a receipt read for the first time and the same receipt re-run through each other path
  now send the classifier the same input.** That is the whole point of part 1 and a per-path test
  does not prove it: **write a guard over the set of paths**, so a fifth path added later fails
  rather than silently passing nothing.
- **A test that an amount is stored as a number and not as text.**
- **A test that a firm record with no setting leaves the classifier off.**
- **Mutations**, each anchored once and printing its own diff: the item lines are stored but not read
  back; the amount is stored as a string; the temperature is dropped; the setting is read with the
  wrong default; and a prose-only control that survives.
- **The migration run against a copy first**, with the row count and the schema read back after it,
  and the statement itself printed.
- **Enumerate from the syntax tree** anything you assert about a set, and print it whole.
  `.history\` excluded.
- **Run the suite again AFTER committing** if the change adds a file.
- **Flag, do not fix. Every flag carries the obvious fix, and if the fix is to remove something, say
  so first.** Disclose your own mistakes. State a confidence level and say what it is about, not only
  what it rests on.

---

## 7. Committing and reporting

**Commit on `feat/console-phase0`.** Do not push and do not create a branch. Do not commit
`2026-07-25_CONSOLE_DESIGN.md`, any `PROMPT_*` or `HANDOVER_*` file, or anything under
`Test Receipts\`.

**Commit by naming your own paths and check the index afterwards.** Files this brief forbids
committing are modified in the working tree by the consultant session while you work. Verify
afterwards and say so in the report.

**Write the report to
`C:\LastingImpact\receipt_capture\2026-09-12_REPORT_claude_code_classifier_inputs_and_switch.md`**
and carry the commit hashes in it.

**Two things at the top for Paul.** The exact setting key and its values, and the migration command
he has to run, with its own `cd` line, written so it cannot be run against the live database by
accident.
