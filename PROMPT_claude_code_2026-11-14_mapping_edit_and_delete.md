# Brief: flag F2, a taught mapping gains an edit and a delete

Written 2026-11-14 by the consultant session. For Claude Code.

## What you own here

The pipeline half. The screen is the consultant session's.

**You do not mark step 10bu built.** You report, the consultant session verifies
against the code on Paul's machine, and the consultant session marks the step.

## Why this exists

**Your own flag F2**, in section 5 of
`2026-11-14_REPORT_claude_code_receipt_rules_pipeline.md`. Read it there. In
short: nothing in production deletes a row from
`categorisations_client_vendors` and nothing edits one, so a supplier taught the
wrong account stays wrong and the only way out is to teach it again, which is
how one supplier came to be taught three times.

**Paul's decision of 2026-11-14, put to him as three options and answered "1":**

- **A taught mapping's nominal code can be changed.** The account name moves
  with it, because the name is display only.
- **A taught mapping can be deleted.**
- **The supplier name is NOT editable, and neither is the vendor key.** Changing
  the taught name changes the row's identity and can change the key, which
  decides what the row is grouped with and what the fuzzy layers score against.
  Changing a name is a delete and a fresh teach.

His reason: correcting a wrong account is the case he has actually hit.

## Establish these before you build, and report what you found

Do not take any of them from this brief or from your own earlier report.

1. **Every production writer and reader of `categorisations_client_vendors`**,
   from the syntax tree, excluding `tests\`, `.history\` and `archive\`. Your F2
   text names some. Enumerate them again rather than citing yourself.
2. **What identifies a row to the screen.** The published mappings file carries
   no `mapping_id`, so the screen can only name a row by what the file holds. Say
   what you chose and why.
3. **What `times_seen` and `last_updated` should do when a code is corrected.**
   A correction is not a sighting. Recommend, with your reasoning, and say what
   layers 3 and 4 would do differently under each answer.
4. **What the firm pool does when a client mapping's code is corrected.** The
   firm pool is written automatically where the operator's code confirms the
   classifier. Whether a correction here should touch it is **not decided**.
   Establish what happens today, recommend, and do not build it either way
   without saying so.

## What has to be true when you are done

1. **The repository can change a row's nominal code and account name, and can
   delete a row**, keyed on what identifies one.
2. **Two new note words on the existing route**, the way `rule_saved` and
   `rule_deleted` already work: same folder, same writer, same mover, same
   `processed\` and `failed\`. A mapping note is not about a receipt either.
3. **The note shapes are written out in the module docstring**, as
   `worker\receipt_rules.py` does for rules. The Desktop half is written against
   that docstring and nothing else.
4. **Deleting a row that is not there is applied rather than refused**, so a note
   delivered twice does not land in `failed\` the second time. Same reasoning as
   the rule delete.
5. **Enumerate the refusals** and give each one a subtest: unknown client, a row
   that does not exist on a code change, a code that is not four digits, an empty
   account name, a missing field, and anything else you find.
6. **The publish follows.** If the file needs a field it does not carry, say so
   and add it, with every key a named constant in `config.py`.

## Evidence

`CLAUDE.md`'s standard, unchanged. Red before green with the failing output
quoted. Mutations anchored to match exactly once, each with its diff printed,
and say which tests catch each. Run the suite again after the commit if the
change adds a file.

Flag anything else you find, with a recommendation attached, and if the obvious
fix is to remove something, say that first.

## What to report, and where

`2026-11-14_REPORT_claude_code_mapping_edit_and_delete.md` in the repository
root, uncommitted, and say so.

**This brief was written by a session that has read `worker\receipt_rules.py`,
`config.py`'s rule constants and `categorise()` in
`worker\categorisation\engine.py`, and has not read
`upsert_client_vendor()` or either teaching site.** Where it states something
about the code that you find to be untrue, the code is right and the brief is
wrong. Say so in the report rather than building to the brief.
