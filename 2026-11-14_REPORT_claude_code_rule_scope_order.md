# Report: flags F1 and F3, rule scope order and the supplier name's stored word

Written 2026-11-14 at 13:14 GMT by Claude Code, from
`PROMPT_claude_code_2026-11-14_rule_scope_order.md` and Paul's addition on flag
F3, sent mid-task. This report is uncommitted. Step 10bu is not marked built.

**One commit: `416b9176f26cf7acc6011bc038697a33805f1a17`**, "fix(categorisation):
the narrower rule scope wins at equal priority", parent `25a363b`, six files,
not pushed. Suite before the commit: **1794 passed, 2 skipped, 1390 subtests**.
The commit added no file, so the rerun-after-commit rule did not apply.

## 1. Is `get_client_rules()` still the only place rules are ordered?

**Yes.** Enumerated from the syntax tree over the 64 production `.py` files,
excluding `tests\`, `.history\`, `archive\` and `.venv\`:

```
get_client_rules: 2 call(s)
   worker\categorisation\engine.py:199 in _first_matching_rule()
   worker\receipt_rules.py:189 in payload_for()
```

String constants naming `categorisation_rules`: the `SELECT` in
`get_client_rules()`, plus an `INSERT`, a `DELETE`, the single-row `SELECT` in
`get_rule()`, `schema.py` and `schema_info.py`. **Only one of them has an
`ORDER BY`.**

Neither caller re-sorts. The only `sorted()` calls near them are
`worker\receipt_rules.py:231`, which sorts client ids in `publish_all()`, and
`worker\categorisation\engine.py:123`, the fuzzy matcher.

## 2. Does the publish follow?

**Yes, for free.** `payload_for()` lists rules in the order the query returns
them, and layer 0 tries them in the same order. The test
`test_the_published_file_is_in_the_engines_order` checks both the file order and
the engine's answer on one set of rules with mixed scopes.

## 3. What I chose for the ordering

**A rank expression in the `ORDER BY`**:

```sql
ORDER BY priority DESC,
         CASE scope WHEN ? THEN 0 WHEN ? THEN 1 WHEN ? THEN 2 END,
         created_at ASC, rule_id ASC
```

The three scope names are bound from `config.RULE_SCOPES`. Why I did not use a
stored rank column:

- The rank depends only on `scope`, so a stored rank would be a second copy
  that could disagree with it.
- Adding a column to the existing table would stop the pipeline starting until
  the live database was altered by hand.

**What this makes load-bearing**: the order of `config.RULE_SCOPES`, client then
firm then sector. That is now said beside the constant, and
`TheKeysAreTheConstantsTest` already pins the tuple.

## 4. Flag F3: `detail` becomes `supplier_name`

Paul's addition, in the same commit. **`config.RULE_FIELD_SUPPLIER_NAME` now
holds `supplier_name`.**

I listed every occurrence rather than taking the count from the message. The
stored value was spelled out in two places, as Paul said:

- `worker\receipt_rules.py:24`, the example note in the module docstring.
- `worker\categorisation\engine.py:212`, the default in `_rule_matches()`. It
  now reads the constant rather than a second literal.

Also changed:

- `tests\test_receipt_rules.py`, the pinned vocabulary.
- `tests\test_category_hold.py`, two `save_rule()` calls.

**Left alone, deliberately:**

- **The parameter named `detail` in `_rule_matches()`**, `engine.py:204`,
  `205` and `220`. It is a variable name, not a stored value. Renaming it is a
  free one-line follow-up if wanted.
- **Two `'detail'` literals in `import_vendor_csv.py:46` and
  `regenerate_vendor_codes.py:46`**, plus one in their test. All three are the
  CSV column `detail` on taught mappings, which is a different thing.

**Paul's reason for doing it now is still true.** Read-only at 13:14:
`categorisation_rules` holds 0 rows. No file containing `rule_saved` or
`rule_deleted` is in `Resolutions\`, `processed\` or `failed\`.

**Red first.** With the tests changed and the code not yet changed, three
failed: `test_the_four_condition_types_are_unchanged`;
`test_the_trigger_holds_exactly_the_three_machine_answers`; and the `0 rule`
subtest of `test_layers_nought_to_two_do_not_need_review`. The last two failed
because a rule stored with the new word did not match under the old constant.

## 5. Tests

| Test | Holds |
| --- | --- |
| `TheScopeOrderTest.test_client_beats_firm_at_equal_priority` | client wins |
| `test_firm_beats_sector_at_equal_priority` | firm wins |
| `test_client_beats_sector_at_equal_priority` | client wins |
| `test_priority_still_overrides_scope` | a newer, broader firm rule at 60 beats a client rule at 50 |
| `test_the_published_file_is_in_the_engines_order` | file order is `d-sector-high`, `c-client`, `b-firm`, `a-sector`, and the engine's answer agrees |
| `TheOrderTest.test_oldest_first_whichever_way_the_ids_sort` | new, see 6.2 |

**In every equal-priority case, the broader rule is saved first and its id sorts
first.** So neither `created_at` nor `rule_id` can make the narrower rule win
by accident.

**Red first**: four of the five new scope tests failed before the change. The
failing output showed the old order, for example
`['d-sector-high', 'a-sector', 'b-firm', 'c-client'] != ['d-sector-high', 'c-client', 'b-firm', 'a-sector']`.
`test_priority_still_overrides_scope` passed before and after. That is by
design: it exists to stop the change going too far, and mutation S3 shows it
catching that.

**`test_two_rules_on_one_priority_resolve_oldest_first` still passes and was
not rewritten**, as the brief asked.

**Two tests from the last step changed**, and both pinned the order Paul has
now overruled:

- `test_the_order_is_one_ordering_across_scopes` is retired, struck through in
  a comment and replaced by `TheScopeOrderTest`.
- `test_every_rule_that_answers_for_the_client_in_match_order` expected the
  older firm rule first. It now expects the client rule first.

## 6. Mutations

Each anchor matched once, applied from a pristine copy, with the diff printed.
Run against `test_receipt_rules`, `test_category_hold`,
`test_supplier_mappings` and `test_vendor_key_naming`, not the full suite.
Output:
`C:\Users\PDK7\AppData\Local\Temp\claude\43687783b5645321\9ee8db8d-892f-421d-bd3f-6f3dcedba8af\scratchpad\mutations_scope.txt`.

| Mutation | Caught by |
| --- | --- |
| **S1 revert the scope ranking** (every scope rank 0) | the 3 equal-priority scope tests, the published-file test, `test_every_rule_that_answers_for_the_client_in_match_order` |
| S2 sector above firm | `test_firm_beats_sector_at_equal_priority`, the published-file test |
| **S3 scope above priority** (too far) | `test_priority_still_overrides_scope`, the published-file test |
| S4 broadest first | the same 5 as S1 |
| S5 `created_at` dropped, ids descending | `test_oldest_first_whichever_way_the_ids_sort` only |
| S6 `created_at` dropped, ids ascending | the 3 oldest-first tests in `TheOrderTest` |

**All six caught.** The F3 rename was not mutated separately. Its red run in
section 4 does that job: reverting the constant is exactly the state that ran
red.

### 6.1 My mistake in the first version of S1

My first version of S1 deleted the `CASE` line. That left three extra bound
parameters, so the query raised an error and **35 tests failed for that
reason**, not because of the order. A mutation that breaks the query proves
nothing about ordering. The corrected S1 keeps the bindings and ranks every
scope equal, which is the real order before amendment 568.

### 6.2 A weakness in my own test from the last step, found by S5

**`test_two_rules_on_one_priority_resolve_oldest_first` could not fail under
`ORDER BY ... rule_id DESC`.** Its ids are `rule-old` and `rule-new`, and
sorting them descending puts the old one first by accident. My last report's
M1 used `rule_id ASC`, which happened to be the direction that test does catch,
so the gap went unseen.

The brief said to confirm that test rather than rewrite it, so I added
`test_oldest_first_whichever_way_the_ids_sort`. It runs two pairs whose ids
sort in opposite directions, so only `created_at` can decide both. S5 is now
caught by it alone.

## 7. Flags

**G1. The running pipeline holds the old code.** It was started at 12:01:39 on
the working tree that became `07f4e5b`. Python loaded those modules at start-up
and does not reload them, so the running process still orders without scope and
still expects `detail`. No rule exists and Desktop does not write rule notes
yet, so nothing is affected today. **Recommendation: restart the pipeline before
the Desktop half writes its first rule note.** The restart also corrects the
`pipeline_version` it records, which the last report raised.

**G2. Sector against firm is fixed in code, and that is Paul's choice.** It
rests on the fact that no client has a trade today. If trades arrive and that
reasoning changes, reversing it is a one-line change to the order of
`config.RULE_SCOPES` plus `test_firm_beats_sector_at_equal_priority`. No action
recommended; recorded so a later session does not mistake it for an accident.

**Carried from the last report and still open**: F2 (no edit or delete route
for a taught mapping), F4 (seven `"UNSPECIFIED"` literals), F5 (the empty old
table in the live database), F6 to F12. F1 and F3 are closed by this commit.

## 8. My own mistakes

- The first version of S1 broke the query rather than reverting the order.
  See 6.1.
- Before changing the order I looked only for the test that pinned the old
  cross-scope order by name. **I missed a second one**,
  `test_every_rule_that_answers_for_the_client_in_match_order`, which the
  change turned red. That test was right to go red, and the miss cost one run.
- Section 6.2 is a weakness in a test I wrote in the last step.

## 9. Confidence

**High that the order is now priority, then client, firm, sector, then oldest,
then id, in the engine and the published file alike.** It rests on red-first
tests, six mutations each caught, the full suite green, and one query read by
both consumers, enumerated from the syntax tree. That confidence is about the
committed code. **The running pipeline does not have it yet**; see G1.
