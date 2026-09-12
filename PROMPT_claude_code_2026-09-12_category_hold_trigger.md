# Brief: narrow the category hold to a machine's answer

**Written 2026-09-12 by the consultant session, from Paul's decision the same day. Amendment 333 of
`2026-07-25_CONSOLE_DESIGN.md`, which amends amendment 330. Step 10l, the pipeline half.**

**This is section 2 of your own report,
`2026-09-11_REPORT_claude_code_category_hold.md`, answered. Option 3.**

**Read first:** that report's sections 1.3, 2 and 5, then amendment 333.

---

## 1. The decision

**`category_unconfirmed` is true where a MACHINE PRODUCED A CATEGORY and nobody has confirmed it.
Nothing else.**

**Amendment 330's first point is superseded.** The hold no longer reads
`categorisations.needs_review`.

**What holds:** `fuzzy_client`, `fuzzy_firm`, `ai`.

**What does not:** `rule`, `client`, `firm`, `unmatched`.

**Enumerate the `match_source` values from `worker\categorisation\engine.py` rather than from this
list, and print the enumeration whole.** This brief has read that file but the set is yours to hold,
and a value added later must fail a test rather than fall silently into one side.

---

## 2. Why, so that nobody narrows or widens it again by accident

**An unmatched receipt is not a guess.** It carries no category at all, the empty field says so on
screen, and it is already in the uncategorised count. A pill reading `Category unconfirmed` on it
states what the operator can already see.

**Amendment 237's purpose is that a MACHINE'S GUESS must not reach a client's books unseen**, and
that is layers 3, 4 and 5.

**Holding every unmatched receipt would do more than add a pill.** It stops such a receipt draining
into the books at all, so it waits in the inbox instead. On Paul's live database that is 25 of 26
rows. **Whether uncategorised receipts should be held at the door is a separate decision and it has
not been taken.**

---

## 3. Two consequences, both intended. Do not treat either as a defect

**One. The chart forcing no longer holds anything.** `resolve_against_chart()` in
`worker\categorisation\fallback.py` forces `needs_review` True on an unreadable bundle and on a code
the chart does not hold, and it leaves `match_source` alone. **A trigger reading `match_source`
therefore does not fire on a hand-taught layer 1 mapping when the chart is missing or mid-sync.**
That is flag 2 of your report and it is disposed of, not overlooked.

**So `TheUnreadableChartTest` must invert.** It currently asserts that an unreadable chart holds an
exact match. Under this decision it must assert the opposite, with the same control in place.
**Called out here so you do not meet a red test and stop to ask.**

**Two. A receipt whose code was stripped because the chart does not hold it publishes
`category_unconfirmed` false and carries no category.** It drains and shows as uncategorised, the same
way an unmatched one does. **Nothing now signals that a code was never checked against the chart.**
Your offer of a second key for the chart outcome is noted and **not taken**: it is a separate decision
and a separate brief.

---

## 4. What must not change

- **The database column.** `categorisations.needs_review` keeps its current meaning and every current
  writer. Nothing about it moves; the hold simply stops reading it.
- **`validation.status`** keeps its arithmetic meaning.
- **The key's name, its boolean type, the absent case and the every-item rule**, all of which are
  settled by section 1 of your report and are what the Desktop half will be built from.
- **No new table and no new column.**
- **Nothing re-published, re-extracted or re-categorised.**
- **F16's value**, and `write_client_copy()` as the only writer into `Clients\`.

---

## 5. Evidence

- **Red before green**, with the failing output quoted.
- **A test per layer**: 3, 4 and 5 hold; 0, 1, 2 and `unmatched` do not. Driven through the real
  engine, as your per-layer tests already are.
- **The inverted chart test, with its control.**
- **A guard over the set of `match_source` values**, so a value added to the engine later fails rather
  than defaulting to one side.
- **Mutations** through the harness, each anchored once and printing its diff: the trigger reads
  `needs_review` again; `unmatched` is added to the holding set; one of the three is dropped from it;
  and a prose-only control that survives.
- **Enumerate from the syntax tree** anything you assert about a set, and print it whole. `.history\`
  excluded.
- **Run the suite again AFTER committing**, per the `CLAUDE.md` rule of 2026-09-11.
- **Nothing run against the live practice root. Never `import config` to read a value.**
- **Flag, do not fix. Every flag carries the obvious fix. Disclose your own mistakes. State a
  confidence level and say what it is about.**

---

## 6. Committing and reporting

**Commit on `feat/console-phase0`.** Do not push, do not create a branch, and do not commit
`2026-07-25_CONSOLE_DESIGN.md`, any `PROMPT_*` or `HANDOVER_*` file, or anything under
`Test Receipts\`.

**Write the report to
`C:\LastingImpact\receipt_capture\2026-09-12_REPORT_claude_code_category_hold_trigger.md`** and carry
the commit hashes in it.

**Short is right here.** One line of production code changed. **What the report needs to say is the
final contract for the Desktop half**: whether anything in section 1 of your previous report has moved,
and if nothing has, say so in those words, because that section is what the other product is built
from.

---

## 7. One thing from your last report that is answered rather than asked

**Your flag 1, the stale brief hash, was the consultant session's error and is corrected.** The
hash was recorded in the design document and the brief was then edited, so the document asserted a
hash nothing matched. **It is struck rather than refreshed**, and briefs' hashes are no longer
recorded in the document: a hash of a file that can still be edited is a citation that goes stale.
Nothing for you to do.
