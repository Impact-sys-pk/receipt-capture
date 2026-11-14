# Brief: step 10bu, receipt rules, the pipeline half

Written 2026-11-14 by the consultant session. For Claude Code.

## What you own here, and what you do not

You own the Python pipeline. This brief covers the pipeline half of step 10bu
only. **The screen is the consultant session's and is not in this brief.**

**You do not mark this step built.** `2026-07-25_BUILD_STATUS.md` is written by
the consultant session and by nobody else, Paul's instruction of 2026-09-16. You
report, the consultant session verifies against the code on Paul's machine, and
the consultant session then marks the step.

## The step

Read step 10bu's body in `2026-07-25_BUILD_STATUS.md` in full before you start.
It is quoted nowhere in this brief on purpose. It names four pieces, the ruling
that a rule must not match line items, and the decisions taken on 2026-11-14.

Read amendments 559 and 565 in `2026-07-25_CONSOLE_DESIGN.md`. They carry Paul's
seven decisions on this step with his wording and the reasoning.

## Establish these before you build, and report what you found

Do not take any of them from this brief. Each is a statement the consultant
session made from a partial read, and each needs your own enumeration.

1. **Every caller of `get_client_rules()`, `create_client_rule()` and
   `delete_client_rule()`**, from the syntax tree across the production tree,
   excluding `tests\`, `.history\` and `archive\`. The consultant session found
   one caller for the first and none for the other two. Confirm or correct it.
2. **How many rows `categorisations_client_rules` holds in the live database**,
   and what they are. The consultant session has not queried it this session.
   If it holds rows, a schema change has to carry them.
3. **Whether anything other than layer 0 reads a rule**, and whether
   `match_source` of `rule` is read anywhere outside the engine.
4. **Where a resolution note reaches the pipeline**, and what shape an existing
   note takes, so a rule written on a screen has a route in that matches the
   routes already there rather than a new one.
5. **Whether a per-client publish already exists that a rules file belongs
   beside.** Sub-step 10bs.10 publishes supplier mappings. A rules file has the
   same shape of problem.

## What has to be true when you are done

The order below is the order the consultant session would build it in. Say so if
you find a better one.

### 1. A rule carries a scope

- A rule is scoped **client**, **firm** or **sector**.
- A **client** rule answers for that client alone. This is what every rule is
  today.
- A **firm** rule answers for every client of that firm.
- A **sector** rule is accepted, stored and matched by the same code path, and
  **can never match today**, because every row carries `business_type`
  `UNSPECIFIED` and no control exists to set a client's trade. That is
  outstanding item 29 and it is not in this step. Build sector so that it starts
  working on the day a client can be given a trade, and do not build the
  control.
- `categorisations_client_rules` has `client_id TEXT NOT NULL` and no scope
  column, read in `worker\database\schema.py` on 2026-11-14. **The schema change
  is yours to design.** Say what you chose and why, and what happens to the
  table's name, which now describes only one of three scopes.

### 2. A rule can be written and deleted

- The two repository functions that have no caller get one.
- A rule written on a screen reaches the pipeline the way corrections already
  do. Find that route rather than inventing a second one.
- A rule can be deleted by the same route.
- **A taught mapping must be editable and deletable too**, which is Paul's
  decision 3 of amendment 559. Establish whether a route already exists for that
  and say what is missing.

### 3. The matcher

- **A rule matches on the supplier name and the vendor key and on nothing
  else.** Paul's decision 5 of 2026-11-14. Amount, date, VAT and the filename
  were put to him and refused.
- **A rule must never read the receipt's line items.** Paul's decision 1 of
  amendment 559, in his word, "NO". Write a guard that fails if a rule's match
  path can reach them, and make it parse the syntax tree rather than the source
  text.
- The four condition types stay as they are.

### 4. The order

- **A rule always beats a taught mapping.** Paul's decision 6. Layer 0 already
  returns before layer 1 is reached, so confirm this rather than change it.
- **Two rules on one priority resolve oldest first.** `get_client_rules()`
  orders `priority DESC` alone today, read in `worker\database\repository.py` on
  2026-11-14, so the order between equal priorities is whatever SQLite returns.
  It becomes `priority DESC, created_at ASC`.
- **Where a client rule and a firm rule both match, say what you chose and
  why.** This was not put to Paul and is not decided. Report it as a question
  rather than building it silently; if your reading of the code makes one answer
  obvious, recommend it.

### 5. The screen has to be able to see a rule

The screen is the consultant session's, and it reads published files. It cannot
open `receipts.db`. So the pipeline publishes what the screen needs: a client's
rules, with everything needed to show them, distinguish them from taught
mappings, and identify one for editing or deletion.

**Every key you publish is declared as a named constant in `config.py`**, on
`CLIENT_TOP_FOLDER_FIELD`'s precedent and as sub-step 10bs.10 did, so the reader
is written against the names rather than against an example of the output.

**Say where you put the file and why.** Every exchange folder under
`Intellibills\` has one writer, which is the reasoning recorded in amendment 555
for the supplier mappings file.

## Evidence

The standard is `CLAUDE.md`'s and it is not relaxed for this step.

- Red before green, with the failing output quoted. Where a test cannot come
  first, mutate from a pristine copy, anchor each mutation so it matches exactly
  once, assert that, and print the unified diff beside the result.
- Enumerate calls from the syntax tree, not by grepping.
- A claim about a set is checked by enumerating the set and printing it whole.
- Exclude `.history\` from every repository-wide search.
- Run the suite again after any commit that adds a file, and treat the second
  run as the one that counts.
- Flag, do not fix. Anything wrong that this brief did not ask about gets
  reported with a recommendation attached, and if the obvious fix is to remove
  something, say that first.
- Disclose your own mistakes, including ones you caught and corrected.
- State a confidence level and say what it rests on, and what it is about.

## What to report, and where

Write it to `2026-11-14_REPORT_claude_code_receipt_rules_pipeline.md` in the
repository root. Leave it uncommitted and say so.

Carry in it: what you established under each of the five questions above, with
the output; every commit hash with what it does; the tests you wrote and what
each one would catch; the mutations and which tests caught each; every flag with
its recommendation; and everything in this brief you found to be wrong.

**This brief was written by a session that has read parts of
`worker\categorisation\engine.py`, `worker\database\repository.py` and
`worker\database\schema.py` and has read neither file whole.** Where it states
something about the code that you find to be untrue, the code is right and the
brief is wrong. Say so in the report rather than building to the brief.
