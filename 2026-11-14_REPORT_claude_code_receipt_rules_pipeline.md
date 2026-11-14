# Report: step 10bu, receipt rules, the pipeline half

Written 2026-11-14 at 12:17 GMT by Claude Code, from
`PROMPT_claude_code_2026-11-14_receipt_rules_pipeline.md`. This report is
uncommitted. Step 10bu is not marked built anywhere by this session.

## 0. Read this first: the live pipeline is already running this code

**Paul started the pipeline at 12:01:39 GMT while this step was uncommitted in
the working tree.** `run.log` line 46143 records it: "uncommitted changes
detected at startup; pipeline_version=a38f9ce may not reflect working tree.
Changed files: 9 file(s)". The commit came later, at 12:13:18, as `07f4e5b`.

What that start did, read from the log and the disk, both read-only:

- **`init_db()` created `categorisation_rules` and its index in the live
  `C:\Intellibills\db\receipts.db`.** Empty, 0 rows. The old
  `categorisations_client_rules` is still there, also empty.
- **It created `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Intellibills\Receipt Rules\`**
  and wrote six files, `Client_001-rules.json` and five others, each holding
  `"rules": []`.
- **Polls at 12:01, 12:06 and 12:11 ran normally**: one receipt published,
  two Desktop corrections applied, no errors.
- **Every receipt this run touches records `pipeline_version` `a38f9ce`**,
  which does not describe the code running. So far that is receipt
  `1573408b-de18-41ed-b770-ca6881e4f0a8`.

**Was the running code half-edited?** No, and this is how I established it.
The log shows the rules files published at 12:01:39, which needs both the call
in `app.py` and the full `worker/receipt_rules.py`. The `app.py` edit was my
last edit to any file the pipeline loads, so every loaded file was in its
committed form. I edited `schema_info.py` afterwards, and the pipeline does not
load it.

**The mutation harness ran while the pipeline was up**, writing mutated
copies of five production files between about 12:08 and 12:12 and restoring
each. A running Python process does not re-read a module it has already
imported, and all five were imported at start-up, so the live process was not
affected. File hashes after the run match those before it, printed in section 4.

**Nothing needs undoing if the consultant session accepts the design.** If it
does not, the live table and the `Receipt Rules\` folder need removing, which
is Paul's.

**Recommendation: restart the pipeline**, so its recorded version names commit
`07f4e5b` rather than `a38f9ce`.

## 1. What I established before building

### 1.1 Callers of the three rule functions

Enumerated from the syntax tree over the 61 production `.py` files, excluding
`tests\`, `.history\`, `archive\` and `.venv\`. Script:
`C:\Users\PDK7\AppData\Local\Temp\claude\43687783b5645321\9ee8db8d-892f-421d-bd3f-6f3dcedba8af\scratchpad\enum_calls.py`.

```
production .py files scanned: 61
create_client_rule: 0 call(s)
delete_client_rule: 0 call(s)
get_client_rules: 1 call(s)
   worker\categorisation\engine.py:252 in categorise()
```

**The brief is right.** Inside `tests\`, `create_client_rule()` had two callers,
both in `tests\test_category_hold.py`. The brief excluded tests, so this is
extra information rather than a correction.

### 1.2 Rows in `categorisations_client_rules`

Read with `sqlite3` in `mode=ro` against `C:\Intellibills\db\receipts.db`:

```
rules rows: (0,)
match_source counts: [('ai', 41), ('client', 25), ('unmatched', 25)]
client vendor rows: (16,)
```

**0 rows, so no data had to be carried.** Its stored definition matched
`schema.py` exactly. No categorisation has ever had `match_source` `rule`.

### 1.3 Who reads a rule, or `match_source` `rule`

String constants enumerated from the syntax tree, docstrings excluded:

```
eq:rule:
   worker\categorisation\engine.py:260  'rule'
contains:categorisations_client_rules:
   migrate_2026_09_06_vendor_key_naming.py:28
   schema_info.py:33
   worker\database\repository.py:981, 996, 1008
   worker\database\schema.py:18
```

- **Nothing other than layer 0 reads a rule row.**
- **`match_source` `rule` is read in one place outside the engine:**
  `MACHINE_MATCH_SOURCES` in `worker\publish.py` names the sources that hold a
  receipt for confirmation, and `rule` is deliberately outside it, so a rule's
  answer is not held. `tests\test_category_hold.py` enumerates the engine's
  vocabulary from the tree and still passes.
- `worker\categorisation\fallback.py` and `worker\resolution\service.py` copy
  `match_source` through without testing its value.
  `_learn_firm_mapping_if_confirmed()` acts on `ai` only.
- **IntelliBooks Desktop does not read `match_source` at all.** A grep of
  `IntelliBooks-Desktop-v3.html` for `match_source`, `matchSource` and a
  quoted `rule` returned nothing.

### 1.4 Where a resolution note reaches the pipeline

There are **two** Desktop-to-pipeline routes, both drained once a poll by
`process_once()` in `app.py`:

1. **`Intellibills\Resolutions\`**, written by Desktop's
   `writeResolutionNote(note, fileKey)` as `{fileKey}_{ms}.json`, consumed by
   `_consume_resolution_notes()`, applied by `apply_resolution_note()`, then
   moved to `processed\` or to `failed\` with an `.error.txt`. Shape:
   `schema` 1, `action` one of `filed`, `discarded`, `attached`, `corrected`,
   `resolved_at`, and **a required `receipt_id`**.
2. **`Intellibills\Attached\`**, sub-step 10f.38, its own contract in
   `worker\attached.py`, reusing the same mover.

**The receipt-note contract cannot carry a rule as it stands**, because
`parse_resolution_note()` refuses a note without a `receipt_id` and a rule is
not about a receipt. What I did is in section 2.2.

### 1.5 A per-client publish a rules file belongs beside

Yes: `worker\supplier_mappings.py`, sub-step 10bs.10, writes
`Intellibills\Supplier Mappings\{client_id}-mappings.json` once a poll, straight
after the notes, comparing as parsed JSON so an unchanged set never touches
OneDrive. Desktop already reads it (`MAPPINGS_DIR` in the HTML).
`tests\test_supplier_mappings.py` pins that file's exact key set.

## 2. What I built, and why each choice

One commit: **`07f4e5b80a73fe8f4a48c0a3af09c1db6e0d1450`**,
"feat(categorisation): receipt rules carry a scope, a writer and a publish",
parent `a38f9ce`, 17 files. Not pushed.

### 2.1 The schema: a new table

**`categorisation_rules`**, declared in `worker\database\schema.py`, with
`scope` (`client`, `firm` or `sector`) and `scope_id` (the client id, firm id or
trade). **`categorisations_client_rules` is no longer declared.**

Why a new table rather than a column on the old one:

- **The old table held 0 rows**, so nothing needed carrying.
- **A new column on an existing table stops the pipeline starting.**
  `schema_drift_message()` refuses a start when a declared column is missing,
  so that route needed an `ALTER TABLE` on the live database, which is Paul's.
  A new table is created by `init_db()` at the next start with no migration, and
  an undeclared old table is not drift. `test_a_database_holding_the_old_table_still_starts`
  holds this, and I also ran the start-up path against a copy of the live
  database: `missing_columns {}`, `undeclared_columns {}`, drift message `None`.
- **The name.** The old name described one scope of three, and `client_id NOT
  NULL` was wrong for two of them.

Other choices:

- **One `scope_id` column, not three nullable ones**, so one rule cannot claim
  two scopes.
- **No `CHECK` on `scope`.** It would be a second definition of
  `config.RULE_SCOPES`. `save_rule()` refuses an unknown scope instead.
- **No column defaults**, per 10d.23 to 10d.28. The old `priority DEFAULT 50`
  is gone and the note must state a priority.
- **`updated_at` added.** `created_at` is set once and never moves on an edit,
  because decision 6 resolves equal priorities oldest first. An edit that moved
  it would quietly send the rule to the back.

### 2.2 Writing and deleting: the `Resolutions\` route

**Two new action words on the existing route**, `rule_saved` and
`rule_deleted`: same folder, same Desktop writer, same mover, same
`processed\` and `failed\`. `apply_resolution_note()` hands a rule note to
`worker\receipt_rules.py` **before** it parses for a receipt.

- **`NOTE_ACTIONS` is unchanged.** It stays the receipt notes' vocabulary.
- **`NOTE_APPLIED_OUTCOMES` gains both words**, because `app.py` moves a note
  to `processed\` on that set alone.
- **Saving an existing `rule_id` edits the rule.** So one action covers create
  and edit.
- **Deleting a `rule_id` that is not there is applied, not refused**, so a note
  delivered twice does not land in `failed\` the second time.
- **`created_at` is the note's `resolved_at`**, so "oldest" means when the
  operator wrote the rule rather than which poll happened to apply it.

The note shapes are in `worker\receipt_rules.py`'s docstring. **For the Desktop
half: pass the `rule_id` as `writeResolutionNote()`'s `fileKey`.** The poll
applies notes in filename order, so that keeps a save and a later delete of one
rule in the order they were made.

What a `rule_saved` note is refused for, each one a subtest: unknown scope;
client not in the registry; firm not in `config.FIRMS`; sector keyed on
`UNSPECIFIED`; condition type outside the four; condition field other than the
supplier name or the vendor key; a regex that does not compile; empty value;
code that is not four digits; empty account name; boolean or text priority;
missing `rule_id`, `resolved_at` or `rule` object. The regex check matters
because `_rule_matches()` swallows a bad pattern and returns False, so a bad
pattern stored would be a rule that silently never matches.

### 2.3 The matcher

- **Layer 0 moved into `_first_matching_rule(client_id, business_type,
  vendor_key, supplier_name)`.** Its parameters are everything a rule can
  see, so the line items cannot be passed in.
- **`_rule_matches()` is now strict on the field.** It used to read the vendor
  key for **any** `condition_field` other than `detail`, so a rule on `amount`
  matched on the key. Amendment 565 describes the old behaviour as testing
  `detail` "or the vendor key", which understates it. Now `detail` reads the
  supplier name, `vendor_key` reads the key, and anything else never matches.
  This is a behaviour change, made because decision 5 says "nothing else". It
  affects no live data, because the table held no rules.
- **The four condition types are unchanged.**
- **The firm comes from `config.CLIENTS_BY_ID`**, the way both production
  callers of `categorise()` already take the trade, so `categorise()`'s
  signature and its five callers are unchanged.

### 2.4 The order

- **A rule beats a taught mapping**: confirmed rather than changed. Layer 0
  returns before layer 1 runs.
- **`ORDER BY priority DESC, created_at ASC, rule_id ASC`.** The brief named
  the first two. I added `rule_id` so two rules written in the same instant
  still come back in one order. That is a third key the brief did not name.
- **Client rule against firm rule: scope plays no part.** The same ordering
  decides across scopes. See flag F1, which carries a recommendation.

### 2.5 The publish

**`Intellibills\Receipt Rules\{client_id}-rules.json`**, written by
`worker\receipt_rules.py` and nothing else, once a poll, straight after
`supplier_mappings.publish_all()`, on that module's method. Every key is a named
constant in `config.py`. Each client's file lists every rule that answers for
that client, whatever its scope, **in the order layer 0 tries them**, so a firm
rule appears in the file of every client of that firm. Each rule carries its
`rule_id`, so the screen can name one to edit or delete.

**Why its own folder, and a correction of what I said mid-session.** I said I
would put rules inside the mappings file. I changed that on reading
`tests\test_supplier_mappings.py`, which pins that file's exact key set and
says it is the contract Desktop is written against. A sibling file leaves that
contract alone and keeps one writer per exchange folder, amendment 555's
reasoning. The screen reads two files rather than one.

### 2.6 Existing tests I changed, and why

| File | Change | Why |
| --- | --- | --- |
| `tests\test_category_hold.py` | two `create_client_rule()` calls become `save_rule()` | the function is replaced |
| `tests\test_vendor_key_naming.py` | reads `categorisation_rules` | the table is replaced |
| `tests\test_corrected_note.py`, `tests\test_post_time_client_copy.py` | `NOTE_APPLIED_OUTCOMES` gains two words | both pin the whole tuple so that a new word is considered. Both rule words were considered: they write no client folder copy and are not receipt actions |
| `tests\test_conftest_redirect.py`, `tests\live_paths.py` | Path constant count 23 to 24 | `RECEIPT_RULES_DIR` is new, and lands under the temp root |
| `tests\test_supplier_mappings.py` | the ordering guard matches `supplier_mappings.publish_all` by module as well as by name | it counted any `publish_all`, and the new rules call is a second one |
| `tests\resolution_fixtures.py` | `RECEIPT_RULES_DIR` redirected per test | so one test's rules file is not the next test's starting state |

I also corrected `schema_info.py`, which listed the old table as layer 0 and
would have described the empty table and omitted the new one. **I have not run
`schema_info.py`**, because it opens the live database.

## 3. Tests: `tests\test_receipt_rules.py`, 31 tests

| Class | What it holds |
| --- | --- |
| `TheTableTest` | the new table has a scope and no `client_id`; the old one is not declared; a database still holding the old table starts with no drift |
| `TheOrderTest` | equal priority resolves oldest first, inserted newest first so insertion order cannot pass it; higher priority beats older; an edit keeps `created_at`; one ordering across scopes |
| `TheScopesTest` | client answers for one client; firm for every client of that firm and no other; sector for its trade; **sector never for `UNSPECIFIED`**; the writer refuses an unknown scope |
| `TheMatcherTest` | a rule beats a taught mapping; a rule on the vendor key; a field that is neither never matches; the four types and two fields pinned |
| `NoLineItemsTest` | **decision 1, on the syntax tree**: `_first_matching_rule` and `_rule_matches` reference no `line_items`, `for_prompt`, `LineItem` or `gross_amount`; the one call site passes none; the table has no such column |
| `TheNoteRouteTest` | both words are applied outcomes; a save writes with no receipt; a delete removes; a missing delete is applied; a firm rule from a client screen; 16 refusal subtests; a real poll moves a rule note to `processed\` |
| `TheKeysAreTheConstantsTest` | every key and value pinned |
| `ThePublishTest` | file content in match order including a firm rule; empty list for no rules; unchanged set not rewritten; `process_once()` publishes after the notes, read from the tree |

**Red first.** The first run failed at import, which proves little, so I added
the `config.py` names and a placeholder module and ran again:
`30 failed, 2 passed`. The two that passed are explained:
`test_the_four_condition_types_are_unchanged` pins constants I had just added,
and the guard's `_rule_matches` subtest is green because that function already
could not reach the line items. Its `_first_matching_rule` subtest was red.

**Suite.** Baseline before any change: `1758 passed, 2 skipped, 1357
subtests`. After, before the commit: `1789 passed, 2 skipped, 1389 subtests`.
**After the commit, which is the run that counts because the commit added
files: `1789 passed, 2 skipped, 1390 subtests passed in 129.02s`.** The extra
subtest in the last run is consistent with a guard that sweeps git-tracked
files seeing the two new files; I did not find which guard it is.

## 4. Mutations

17 mutations, each anchored to match exactly once (the harness refuses
otherwise), applied from a pristine copy, diff printed, run against seven test
files (`test_receipt_rules`, `test_category_hold`, `test_supplier_mappings`,
`test_corrected_note`, `test_post_time_client_copy`, `test_vendor_key_naming`,
`test_conftest_redirect`), then restored. **Not run against the full suite**,
for time, so "caught only by these" means within those seven files. Full output:
`C:\Users\PDK7\AppData\Local\Temp\claude\43687783b5645321\9ee8db8d-892f-421d-bd3f-6f3dcedba8af\scratchpad\mutations.txt`.

| Mutation | Caught by |
| --- | --- |
| M1 drop `created_at` from the order | 4 tests: oldest first, edit keeps place, one ordering across scopes, publish order |
| M2 newest first | the same 4 |
| M3 an edit moves `created_at` | `test_editing_a_rule_keeps_its_place` only |
| M4 sector answers for `UNSPECIFIED` | `test_a_sector_rule_never_answers_for_unspecified` only |
| M5 engine ignores the firm | firm scope test, one ordering across scopes |
| M6 any other field reads the key (the old behaviour) | `test_a_field_that_is_neither_never_matches` only |
| M7 `_first_matching_rule` gains a `line_items` parameter | `test_the_rule_path_cannot_reach_the_line_items` only |
| M8 rule notes not dispatched | 5 note route tests |
| M9 `rule_saved` not an applied outcome | 4, including both pre-existing tuple pins |
| M10 deleting a missing rule refused | `test_deleting_a_rule_that_is_not_there_is_applied` only |
| M11 bad regex accepted | `test_unusable_notes_are_refused`, its regex subtest |
| M12 poll does not publish rules | `test_the_poll_publishes_after_the_notes` only |
| M13 publish leaves firm rules out | `test_every_rule_that_answers_for_the_client_in_match_order` only |
| M14 sector on `UNSPECIFIED` accepted by the note | refusal test, its subtest |
| M15 boolean priority accepted | refusal test, its subtest |
| M16 unknown client accepted | refusal test, its subtest |
| M17 writer accepts any scope | `test_an_unknown_scope_is_refused_by_the_writer` only |

**All 17 caught.** Hashes of the five mutated files before and after the run,
first 16 hex characters, identical:

```
0e9f2befe71a2c80 app.py
7d099f4e2605d849 worker/database/repository.py
ea6827a391eda1eb worker/categorisation/engine.py
be2a859791954708 worker/resolution/service.py
9b07677fa8f282c2 worker/receipt_rules.py
```

## 5. Flags, each with a recommendation

**F1. Client rule against firm rule: a question for Paul.** Built as one
ordering across scopes, `priority DESC, created_at ASC`. The weakness: a client
exception written at the default priority after an older firm rule at the same
priority loses, and nothing says so except the order of the list.
**Recommendation: at equal priority, the narrower scope wins, then oldest
first**, as `ORDER BY priority DESC, <client, firm, sector>, created_at ASC`.
Priority stays the explicit override, which keeps decision 6's reasoning, and
the case most likely to surprise resolves the way an operator would expect. It
is a one-line change plus one test. Where sector sits against firm is a second
question inside this one, because neither contains the other.

**F2. A taught mapping has no edit or delete route. Missing, and not built
here** because the brief asked me to establish it. The only production writers
of `categorisations_client_vendors` are `upsert_client_vendor()` from the two
teaching sites in `worker\resolution\service.py`, plus `import_vendor_csv.py` and
`seed_client_vendors.py`. Nothing deletes a row. **What is missing**: a
repository delete and edit keyed on `(client_id, vendor_key, vendor_name)`, which
the table already holds unique, and two more note words on the same dispatch,
for example `mapping_saved` and `mapping_deleted`. The published mappings file
carries no `mapping_id`, so the natural key is what Desktop can name.
**Recommendation: build it as the next pipeline piece, on exactly the pattern in
`worker\receipt_rules.py`.** It is about the size of this step's note half.

**F3. `detail` is the stored word for the supplier name.** It is what
`_rule_matches()` has always tested, so I kept it. `detail` is also a column on
`categorisations_client_vendors` meaning something else. **Recommendation:
rename it to `supplier_name` now**, while the table is empty and before Desktop
writes it. One constant in `config.py` and the tests that name it.

**F4. Seven literal `"UNSPECIFIED"` strings** in production code: `app.py`,
`config.py`, `probe_extract.py`, `probe_layer5.py`, `retroactive_categorise.py`,
`worker\extraction_pipeline.py`, `worker\resolution\service.py`. I added
`config.UNSPECIFIED_TRADE` and used it in the new code only. **Recommendation:
replace all seven with the constant.** It is mechanical, and checkable with the
same enumeration.

**F5. The old table is still in the live database, empty.** Harmless, because
nothing reads it and drift ignores it. **Recommendation: drop it**, after a
backup, which is Paul's to run.

**F6. The test fixture's firm registry does not contain its own client's firm.**
`TempEnvironment` gives `CLIENT001` the firm `INTELLITAX`, but `config.FIRMS`
is keyed on the firm record from `tests\live_paths.py`. My firm-scope note test
registers the firm itself. **Recommendation: key the fixture's firm record
`INTELLITAX`**, so the next firm-level test does not meet this.

**F7. A re-delivered old rule note can undo a newer one.** Receipt notes guard
idempotency on `resolved_at` through `resolution_events`. Rule notes have no
equivalent: an old `rule_saved` copied back into `Resolutions\` after a newer
one reverts the rule, and after a delete it brings the rule back.
**Recommendation: refuse a `rule_saved` whose `resolved_at` is older than the
stored `updated_at`.** One comparison. The case after a delete needs a record of
the delete, so I would leave it until it is seen.

**F8. No audit row for a rule write.** `resolution_events.receipt_id` is
`NOT NULL`, so a rule write cannot use it. The record is the note in
`processed\` and the INFO line in `run.log`. An edit overwrites the row, so the
old values survive only in the earlier note. A decision for Paul.

**F9. `schema_info.py` keeps its own hand list of tables**, which had drifted
here and no test noticed. **Recommendation: build the list from
`schema.declared_columns()` and keep only the descriptions by hand**, which
removes the duplicate rather than guarding it.

**F10. `worker\receipt_rules.py` imports `_on_disk`, a private helper, from
`worker\supplier_mappings.py`.** **Recommendation: make it public in the same
module.** A one-word rename.

**F11. A rule note in `failed\` prints an empty `receipt_id:` line** in its
`.error.txt`, because `app.py` writes that line for every note. The `reason:`
line names the `rule_id`. Cosmetic. **Recommendation: leave it**, unless the
Desktop half wants the rule id on its own line.

**F12. Prose that names the old table**: `CLAUDE.md` ("Layer 0 is
`categorisations_client_rules`"), `CATEGORISATION.md`,
`RECEIPT_CAPTURE_GUIDE.md`, and amendment rows in the design document. **Not
touched.** `CLAUDE.md` is the consultant session's to word. Recommendation:
correct the live sentence in `CLAUDE.md` and `CATEGORISATION.md` when 10bu is
marked; the amendment rows are history and stay.

## 6. What in the brief I found to be wrong or incomplete

1. **"A sector rule ... can never match today, because every row carries
   `business_type` `UNSPECIFIED`."** Only true while nobody writes a sector
   rule keyed on `UNSPECIFIED`. Keyed that way, it would have answered for
   every client of every firm. I made it impossible: the read skips sector
   when the trade is `UNSPECIFIED`, and the note parser refuses that key.
2. **Amendment 565 describes `_rule_matches()` as testing `detail` "or the
   vendor key".** It read the vendor key for any field that was not `detail`.
   See 2.3.
3. **"A rule written on a screen reaches the pipeline the way corrections
   already do."** The route is right, but the correction contract requires a
   `receipt_id`, so the route needed a dispatch ahead of the receipt parser.
   See 2.2.
4. **Line numbers cited in the brief and amendments** (`engine.py:183`,
   `:252`, `repository.py:979`) have moved with this change, as `CLAUDE.md`'s
   rule about line numbers predicts.

Everything else the brief stated about the code I found to be true.

## 7. My own mistakes, including those I corrected

- **I said mid-session that rules would go inside the mappings file**, then
  changed it. See 2.5.
- **My first constants test ran inside `TempEnvironment`**, which rebases the
  folder, and failed for that reason. I moved it out.
- **My firm-scope note test assumed the fixture's firm was registered.** It was
  not. See F6.
- **The mutation harness first anchored multi-line mutations on `\n`** while
  several of those files are CRLF in the working copy. I caught it before the
  first run and made the harness match the file's line endings.
- **The harness's failure parser prints fragments of subtest labels**, the
  lines reading `that`, `on`, `priority')` and `client')` in `mutations.txt`.
  That is a regex artefact from labels containing spaces. The catching test is
  the one named on the next line.
- **I did not foresee the pipeline being started mid-step.** Section 0 is the
  consequence. A step that changes `schema.py` should say in its first status
  line that the pipeline must not be started until the commit, and I did not
  say it.

## 8. Confidence

- **High that the pipeline half behaves as the tests describe**: 31 new tests,
  red first, 17 mutations each caught, the full suite green twice including
  after the commit, and the start-up path run against a copy of the live
  database. That confidence is about the Python, read and run here.
- **High that the running pipeline holds the committed code**, resting on the
  log line showing the rules publish at 12:01:39 and on `app.py` being my last
  pipeline-loaded edit. This is an inference from the log and my edit order. I
  have not read the running process's memory.
- **Medium that the note shape will suit the Desktop half**, because that half
  is not written yet and the shape is my design.
