# Report: a reference number that differs only in case no longer defeats duplicate detection

**Claude Code, 2026-09-10, 09:03 BST.** Times in this report are local, which is
BST today. `CLAUDE.md` records that the two sessions' clocks differ by an hour
and neither is wrong, so the zone is stated.

Brief: `PROMPT_claude_code_2026-09-10_reference_number_case.md`. Paul's decision
of 2026-09-10, option 1 of three. Sub-step 10f.30's check 5, amendment 107.

---

## 1. What was built

**One function, one comparison, and eleven tests.**

`worker\extraction_pipeline.py` gains `_comparable_ref()`, and `_signals_differ()`
passes both reference numbers through it before comparing them:

```python
def _comparable_ref(value):
    return str(value or "").strip().lower()
```

```python
    ref_new = _comparable_ref(getattr(extraction, 'receipt_ref_number', None))
    ref_dup = _comparable_ref(dup_extraction.get('receipt_ref_number'))

    if ref_new and ref_dup and ref_new != ref_dup:
        return True
```

**Three things about that one line, each of which is answerable.**

- **`.strip().lower()` and nothing else**, per Paul's decision. No removing
  hyphens, no stripping internal spacing, no collapsing runs. Two tests pin
  that: a space in the middle and a hyphen turned into a space both still
  separate two transactions.
- **`.strip().lower()` rather than `.casefold()`**, because `.strip().lower()`
  is exactly what the supplier already gets in
  `find_by_transaction_loose()`, which is called with `case_insensitive=True`
  and compares against SQL `LOWER()`. That inconsistency between the two
  fields was the whole of the fault, so the fix is the supplier's own
  treatment rather than a second one. `.casefold()` changes a handful of
  characters beyond their case, which is the guessing that was ruled out.
- **`str()` because the value need not be a string.** See section 6, flag 1.
  This is the one thing in the change the brief did not ask for, and it is
  there because without it the fix introduces a crash the fault did not have.

**One normaliser, applied to both sides**, rather than the same expression
written twice. A mutation that normalises only the stored side is caught by
three tests and five subtests; see section 4.

**Tests: `ReferenceNumberCaseTest` in `tests\test_step10f_duplicates.py`.**
Eleven tests and nineteen subtests. Ten drive a real `process_once()` through
`Routes(...).email_attachment()` twice with different bytes, so the file-hash
check cannot answer and the semantic check is the one being measured; the
eleventh is a table over `_signals_differ()` itself, which is where both
directions of every asymmetric pair are enumerated.

**No schema change. Nothing in the run summary.
`find_by_transaction_loose()`, `is_published()`, the `published` marker and the
five-minute time window are all untouched.**

---

## 2. The commit

| | |
| --- | --- |
| Branch | `feat/console-phase0` |
| Fix and tests | `a444877` |
| This report | the commit whose subject is `docs: the report for the reference number case fix`. A file cannot carry the hash of the commit that adds it |

**A note on the commit, because this brief was not an `AUTOMATIC task`.** The
default in `CLAUDE.md` is that I do not commit without explicit approval.
Paul's instruction was "read the brief and execute it", and section 6 of the
brief requires this report to carry the commit, so committing is part of what
was asked for. Nothing was pushed and no branch was created. `git push` is
still Paul's.

**Not in either commit, and deliberately:** `2026-07-25_CONSOLE_DESIGN.md` is
modified in the working tree by the consultant session and is not mine to
commit, and the two `PROMPT_*` files and
`2026-09-10_HANDOVER_consultant_session_20.md` are untracked, which is the
shape of the previous pair of commits (`9682a97` then `d4b5094`).

---

## 3. The suite, before and after

| Run | Result |
| --- | --- |
| The eleven new tests, before the fix | **10 failed, 7 passed, 8 subtests passed** |
| The pre-existing tests, with the fix in | **980 passed, 676 subtests passed, 10 deselected** |
| Everything, after | **991 passed, 695 subtests passed** in 63s |

**What "before" means here, stated rather than implied.** The middle row is the
suite run with `--deselect ReferenceNumberCaseTest`, so it is the pre-existing
tests measured against the changed code: it says the fix breaks nothing. I did
not run the suite at `HEAD` with the code reverted, so I am not claiming a
figure for that. The top row is the red run.

### Red before green

The red case is the brief's, with the values off Paul's machine:

```
FAILED tests/test_step10f_duplicates.py::ReferenceNumberCaseTest::test_one_character_of_case_no_longer_defeats_the_check
E           AssertionError: 'ok' != 'possible_duplicate'
E           - ok
E           + possible_duplicate
E            : 'LBcAMRL-2021-09-04-01303' against 'LBCAMRL-2021-09-04-01303' was treated as a
             second transaction, so the reference numbers are still being compared case-sensitively
```

The whole red run, before any change to `worker\extraction_pipeline.py`:

```
FAILED ...ReferenceNumberCaseTest::test_a_reference_number_of_only_whitespace_vetoes_nothing
FAILED ...ReferenceNumberCaseTest::test_one_character_of_case_no_longer_defeats_the_check
FAILED ...ReferenceNumberCaseTest::test_surrounding_whitespace_is_stripped
SUBFAILED(case='one character of case')            ...test_the_signals_helper_answers_the_same_way_on_its_own
SUBFAILED(case='the same pair, reversed')          ...test_the_signals_helper_answers_the_same_way_on_its_own
SUBFAILED(case='every character of case')          ...test_the_signals_helper_answers_the_same_way_on_its_own
SUBFAILED(case='surrounding whitespace')           ...test_the_signals_helper_answers_the_same_way_on_its_own
SUBFAILED(case='surrounding whitespace, reversed') ...test_the_signals_helper_answers_the_same_way_on_its_own
SUBFAILED(case='the new reading has only whitespace')     ...test_the_signals_helper_answers_the_same_way_on_its_own
SUBFAILED(case='the earlier reading has only whitespace') ...test_the_signals_helper_answers_the_same_way_on_its_own
10 failed, 7 passed, 30 deselected, 8 subtests passed in 1.19s
```

**The seven that passed red are the ones that had to.** The veto, the internal
spacing, the hyphen, the same reference number twice, and the missing and empty
cases all describe behaviour this change does not alter, so a red there would
have meant the fix was wider than the brief. They are the reason the change can
be called narrow rather than asserted to be.

**The number-rather-than-string tests were written after the fix, not before**,
because the risk they cover was found by reading `openai_vision.py` while
checking my own change. A mutation stands in for the red run: see
`drop-the-str-coercion` below, which fails exactly those cases.

---

## 4. The mutations

Eight, through `tests\mutation_harness.py`. Every one is anchored on one place,
the harness refuses an anchor matching anything other than once before it writes
anything, each ran the **whole** suite, each printed its own unified diff, and
each restored the file byte for byte.

| # | Mutation | Diff | Expected | Result |
| --- | --- | --- | --- | --- |
| 1 | `case-sensitive-again` | `-return str(value or "").strip().lower()` / `+return str(value or "").strip()` | caught | **caught**: 4 failures, 990 passed |
| 2 | `drop-the-strip` | `+return str(value or "").lower()` | caught | **caught**: 6 failures, 989 passed |
| 3 | `drop-the-str-coercion` | `+return (value or "").strip().lower()` | caught | **caught**: 4 failures, 990 passed |
| 4 | `drop-the-falsy-guard` | `+return str(value).strip().lower()` | caught | **caught**: 4 failures, 990 passed |
| 5 | `widen-to-option-2-internal-spacing` | `+return str(value or "").strip().lower().replace(" ", "")` | caught | **caught**: 2 failures, 990 passed |
| 6 | `normalise-one-side-only` | `-ref_dup = _comparable_ref(dup_extraction.get('receipt_ref_number'))` / `+ref_dup = dup_extraction.get('receipt_ref_number')` | caught | **caught**: 9 failures, 988 passed |
| 7 | `veto-removed-altogether` | `-if ref_new and ref_dup and ref_new != ref_dup:` / `+if False:` | caught | **caught**: 6 failures, 988 passed |
| 8 | `prose-only-the-docstring` | `option 1 of three` → `option 9 of three` in the docstring | **survives** | **survived**: 991 passed |

Each reported one hunk and two lines, which is the harness's own count.

**1, the one the brief names.** Putting the case-sensitive comparison back:

```
FAILED ...ReferenceNumberCaseTest::test_one_character_of_case_no_longer_defeats_the_check
SUBFAILED(case='every character of case')
SUBFAILED(case='one character of case')
SUBFAILED(case='the same pair, reversed')
```

**3, which stands in for a red run I could not write first.** Dropping the
`str()` fails precisely the cases that exist for it, and nothing else:

```
FAILED ...ReferenceNumberCaseTest::test_a_reference_number_the_model_returned_as_a_number
SUBFAILED(case='a number against nothing')
SUBFAILED(case='the new reading gave a number')
SUBFAILED(case='two numbers that really differ')
```

**5, which is the one that pins Paul's decision rather than the code.** Widening
to option 2 is caught by `test_internal_spacing_is_left_alone` and by one
subtest, and by nothing else in the suite. So the narrow scope is a tested
property, not a comment.

**7 is the veto's negative control.** Removing it leaves
`test_a_genuinely_different_reference_number_still_separates_them`, the hyphen
test and the internal-spacing test failing. Without those three, every other
test in this class would pass against a comparison that called everything a
duplicate.

**8 is the discrimination control**, per `CLAUDE.md`'s three incidents in two
days of guards that read prose as though it were code. A word changed inside
`_comparable_ref()`'s docstring is caught by nothing.

### A mutation that survived, and it changed the code

The first run of the mutation set had a ninth, `drop-the-or-None`, against an
earlier draft that read:

```python
    if not value:
        return None
    return value.strip().lower() or None
```

```
=== whitespace-counts-as-a-reference-number ===  expects: caught
    -    return value.strip().lower() or None
    +    return value.strip().lower()
last line: 990 passed, 691 subtests passed in 67.46s
caught by 0 reported failure(s):
verdict: NOTHING CAUGHT IT, and this mutation had to be caught
```

**It survived because it could not fail.** `"   ".strip()` is already the empty
string and already falsy, and `_signals_differ()` reads the value for truth, so
`or None` and the early return were both doing nothing. The normaliser was
simplified to the single line above and every mutation in the table was re-run
against it. **A clause no test can distinguish is one this project does not
keep**, and it was visible only because the mutation was expected to be caught
and was not.

---

## 5. Deliverable 2: the receipt time

**Answer: it is not the same fault, so nothing was changed.**

- **A stray space cannot throw it into the `except`.** `int()` strips
  surrounding whitespace, so `' 12:30'`, `'12:30 '` and even `'12 : 30'` all
  parse and compare correctly.
- **A different separator, a missing separator, seconds, or a meridiem all do
  throw it, and the comparison is then silently skipped.**
- **Case cannot arise.** The only letters that can appear are a meridiem, and a
  meridiem already fails the parse, so lower-casing would change no answer.

**Why it is a different fault, and this is the part that decides it.** A skipped
time comparison returns no veto, so `_signals_differ()` returns False and the
receipt IS flagged `possible_duplicate` and routed to Review for a person to
look at. The reference-number fault ran the other way: it produced a veto that
should not have existed, so a real duplicate reached `ok`, published, and was
copied into the client folder. **One fails towards a person, the other fails
past them.** The brief says to change it only if it is the same fault, and it is
not.

Driven rather than reasoned about. The statements below were lifted out of
`_signals_differ()`'s syntax tree and executed, so this is the code's answer
rather than my reading of it:

```
--- the statements being driven, unparsed from the tree ---
new_h, new_m = map(int, time_new.split(':'))
dup_h, dup_m = map(int, time_dup.split(':'))
new_mins = new_h * 60 + new_m
dup_mins = dup_h * 60 + dup_m
diff = abs(new_mins - dup_mins)
if diff > 5:
    return True
--- the handler ---
(ValueError, AttributeError) -> pass

identical                                 '12:30' vs '12:30'    no difference -> falls through to `return False`
four minutes apart, inside the window     '12:30' vs '12:34'    no difference -> falls through to `return False`
six minutes apart, outside the window     '12:30' vs '12:36'    differ -> True, a separate transaction
two hours apart                           '12:30' vs '14:45'    differ -> True, a separate transaction
leading space                            ' 12:30' vs '12:30'    no difference -> falls through to `return False`
trailing space                           '12:30 ' vs '12:30'    no difference -> falls through to `return False`
spaces around the separator             '12 : 30' vs '12:30'    no difference -> falls through to `return False`
a full stop as the separator              '12.30' vs '12:30'    SKIPPED, the except swallows ValueError: invalid literal for int() with base 10: '12.30'
a full stop on both, two hours apart      '12.30' vs '14.45'    SKIPPED, the except swallows ValueError: invalid literal for int() with base 10: '12.30'
no separator                               '1230' vs '12:30'    SKIPPED, the except swallows ValueError: not enough values to unpack (expected 2, got 1)
seconds as well                        '12:30:45' vs '12:30'    SKIPPED, the except swallows ValueError: too many values to unpack (expected 2)
a meridiem                              '12:30pm' vs '12:30'    SKIPPED, the except swallows ValueError: invalid literal for int() with base 10: '30pm'
a meridiem on both, two hours apart     '12:30pm' vs '2:45pm'   SKIPPED, the except swallows ValueError: invalid literal for int() with base 10: '30pm'
empty                                          '' vs '12:30'    the `if new and dup` guard is False, so the parse never runs
absent                                       None vs '12:30'    the `if new and dup` guard is False, so the parse never runs
```

**One consequence worth Paul knowing, since it is a real outcome rather than a
theoretical one.** Where a model returns `14.45` for one reading and `12:30`
for the other, with no reference numbers to separate them, two genuinely
different parking sessions two hours apart are flagged as possible duplicates
and both wait in Review. That is a false positive costing a person a look, and
it is silent: nothing in `run.log` says the time comparison did not run.
Flagged below, not changed.

---

## 6. Deliverable 3: every other bare `!=` or `==` over extraction text

**Enumerated from the syntax tree**, not by grepping, because on this project
superseded wording is kept beside every correction and prose about a comparison
sits next to it. **`.history\` excluded**, per `CLAUDE.md`'s trap: it holds a
dated copy of every edited file. Also excluded: `tests\`, `archive\`,
`__pycache__`, `Backups\`, `docs\`, `exports\`, `logs\`.

**The field names were read rather than typed**: twelve off `ExtractionResult`'s
own annotations in `worker\extraction\base.py`, seventeen off
`schema.py`'s `CREATE TABLE IF NOT EXISTS extractions`, eighteen in the union.
**The first version of this script asserted both lists were non-empty and the
assertion fired**, because my regex for the CREATE TABLE block never matched.
Had I not asserted, the answer would have come back from twelve names and
looked complete.

**110 Eq/NotEq comparisons across 52 production modules.** Two passes.

### Pass A: an operand that names an extraction field. Five.

| Where | Comparison | Can case differ between two readings of one document? |
| --- | --- | --- |
| `worker\client_copy.py:273` `copy_for_published_receipt()` | `validation_status != 'ok'` | **No.** One extraction, and the value is written by `validate()` from a fixed set of four words. Nothing off the document. |
| `worker\extraction\postprocess.py:213` `resolve_invoice_date()` | `parsed_from_raw != invoice_date` | **No.** Both sides are `YYYY-MM-DD`, digits only, and both come from one extraction: the deterministic parse of the model's raw date string against the model's own ISO reading. Not two readings at all. |
| `worker\filing.py:216` `_find_review_sidecar()` | `found_id == receipt_id` | **No.** Two copies of one `uuid4()` the pipeline generated, one of them read back out of a sidecar the pipeline wrote. Nothing reads it off a document. |
| `worker\resolution\service.py:189` `parse_corrections()` | `name == 'invoice_date'` | **No.** A field name against a literal, iterating a list this module defines. |
| `worker\resolution\service.py:749` `resolve_receipt()` | `extraction['extraction_id'] != expected_extraction_id` | **No, and it fails safe if it ever did.** Both are `uuid4()` strings the pipeline generated; the right-hand one is echoed back by whoever rendered the view. A differently-cased echo would report `stale`, which writes nothing and asks for a reload. |

**So the answer to the brief's question is: none of the five.** The
reference-number comparison was the only place where text read off a document
by two separate model calls was compared with a bare `!=`.

### Pass A would have missed the fault it was written for

**Stated plainly because it is the honest limit of this enumeration.** The
comparison that was fixed is `ref_new != ref_dup`. Neither operand names an
extraction field: they are locals. **A field-name pass does not find it**, which
is why pass B exists and why I am not offering pass A alone as the set.

### Pass B: the bound. A non-constant on both sides, and not already in pass A. Thirty-nine.

Printed whole. This is the shape of "a value from one reading against a value
from another" whatever the locals are called, so anything pass A missed is here.

```
app.py:235   [_client_folder_name()]                 client_id == config.UNKNOWN_CLIENT_ID
app.py:687   [_copy_missing_client_copies()]         config.CLIENT_COPY_TRIGGER != config.CLIENT_COPY_ON_PUBLISH
app.py:855   [_is_process_running()]                 err == _ERROR_INVALID_PARAMETER
app.py:857   [_is_process_running()]                 err != _ERROR_ACCESS_DENIED
app.py:868   [_is_process_running()]                 exit_code.value == _STILL_ACTIVE
app.py:1026  [release_lock()]                        existing_pid != os.getpid()
app.py:1242  [process_once() > for email_msg]        client_id == config.UNKNOWN_CLIENT_ID
app.py:1684  [process_once() > for msg]              client_id != config.UNKNOWN_CLIENT_ID
app.py:1697  [process_once() > for msg]              client_id == config.UNKNOWN_CLIENT_ID
config.py    [_is_single_folder_name()]              pathlib.PureWindowsPath(value).name == value
config.py    [reload_clients_if_changed()]           current == _CLIENTS_MTIME
probe_extract.py:145  [main() > for ...]             cat.suggested_code == chosen_code
regenerate_vendor_codes.py:96  [regenerate_codes()]  new_code != old_code
regenerate_vendor_codes.py:152 [for row in ...]      new_code != old_code
retroactive_categorise.py:203  [main()]              categorised == len(AFFECTED_RECEIPTS)
worker/categorisation/chart.py:67   [chart_filename()]  chart_code.strip().upper() == MASTER_CHART_CODE
worker/categorisation/chart.py:119  [load_chart()]       cached[0] == mtime
worker/categorisation/chart.py:232  [load_accounts()]    cached[0] == mtime
worker/categorisation/engine.py:217 [_rule_matches()]    rule['vendor_key'] != vendor_key
worker/categorisation/engine.py:232 [_rule_matches()]    condition_value == field_value
worker/categorisation/engine.py:523 [_ai_suggest()]      c[0] == code
worker/categorisation/fallback.py:127 [load_fallbacks()] cached[0] == mtime
worker/client_copy.py:140 [_same_bytes()]                one.stat().st_size != other.stat().st_size
worker/client_copy.py:142 [_same_bytes()]                _digest(one) == _digest(other)
worker/client_copy.py:250 [copy_for_published_receipt()] config.CLIENT_COPY_TRIGGER == config.CLIENT_COPY_NEVER
worker/client_copy.py:253 [copy_for_published_receipt()] config.CLIENT_COPY_TRIGGER == config.CLIENT_COPY_AT_POST
worker/extraction_pipeline.py:150 [_signals_differ()]         ref_new != ref_dup
worker/extraction_pipeline.py:343 [process_extraction_result()] client_id == config.UNKNOWN_CLIENT_ID
worker/extraction_pipeline.py:346 [process_extraction_result()] client_id == config.UNKNOWN_CLIENT_ID
worker/filing.py:222 [_find_review_sidecar() > for sidecar]      nested_filename == original_filename
worker/filing.py:316 [_scan_other_clients_for_receipt() > for]   review_dir == searched_dir
worker/intake/folder_reader.py:106 [scan_inbox() > for > for]    item.suffix.lower() == SIDE_CAR_EXT
worker/logging_setup.py:66 [attach_log_handler() > for existing] Path(getattr(existing, 'baseFilename', '')) == path
worker/publish.py:276 [_warn_if_already_published()]             row.get('outcome') == PUBLISHED
worker/resolution/service.py:287  [parse_resolution_note()]      schema != NOTE_SCHEMA
worker/resolution/service.py:1185 [_note_already_applied() > for] event.get('source') != DESKTOP_SOURCE
worker/resolution/service.py:1191 [_note_already_applied() > for] payload.get(NOTE_RESOLVED_AT_KEY) == resolved_at
worker/resolution/service.py:1509 [_apply_filed_note()]           str(existing) != str(target)
worker/vat_rates.py:126 [load_rates()]                            cached[0] == mtime
```

**Line numbers in `app.py` and `config.py` are deliberately not given for those
two files**, per `CLAUDE.md`. The function name is in brackets. The other paths
carry numbers because that rule names those two files.

**Nothing in pass B compares text from two extractions either**, so the answer
to the brief's question stands at one place: the one this change repaired.
**Two of the 39 do compare text where case can differ**, and neither is two
readings of a document: one is a filename the pipeline wrote, the other is an
operator-authored rule against a normalised vendor key, which is flag 2. Here
is the reading, grouped so each group carries a reason rather than a verdict:

**The groups below account for all 39, each comparison in exactly one, and the
arithmetic was checked by a script rather than eyeballed.** The first draft of
this section said twenty-one constants and five modification times, from reading
down the list, and left two comparisons in no group at all. `CLAUDE.md`'s rule
about the word "the" in front of a plural, broken and then caught.

| Count | Group | Can case differ between two readings of one document? |
| --- | --- | --- |
| 1 | `ref_new != ref_dup` | This is the comparison the brief fixed. |
| 17 | **Against a constant this codebase defines**, a module constant or a `config` value: `UNKNOWN_CLIENT_ID` five times, the three copy triggers, the two Windows error codes, `_STILL_ACTIVE`, `SIDE_CAR_EXT`, `MASTER_CHART_CODE`, `PUBLISHED`, `NOTE_SCHEMA`, `DESKTOP_SOURCE` | **No.** Both sides are the codebase's own words. `chart_filename()` and `scan_inbox()` already case-fold theirs. |
| 6 | **A cached modification time or a pid** | **No.** Numbers. |
| 2 | **File size and SHA digest**, in `_same_bytes()` | **No.** A digest is lower-case hex from one function. |
| 4 | **Ids, paths or filenames the pipeline itself wrote**: `nested_filename == original_filename`, `review_dir == searched_dir`, `Path(baseFilename) == path`, `str(existing) != str(target)` | **In principle yes for the filename one**, because Windows filenames are case-insensitive while Python string equality is not, so a sidecar written with a differently-cased filename would fail the fallback match. It is the fallback for sidecars written before the receipt id was recorded, and it is not extraction text. Reported, not changed. |
| 1 | **A timestamp the pipeline wrote, echoed back by a Desktop note**: `payload.get(NOTE_RESOLVED_AT_KEY) == resolved_at` | **No.** Both are machine-written ISO strings and the only letters in one are `T` and the offset. |
| 2 | **The categorisation rule matcher**, `_rule_matches()` | **Yes for `rule['vendor_key'] != vendor_key`, and it is a real one.** See flag 2. The condition comparison beside it already lower-cases both sides. |
| 1 | **The layer 5 code check**, `any(c[0] == code for c in coa)` | **No.** Codes are four digits. Whitespace on the model's code would drop the suggestion, which fails safe. |
| 1 | **A path against its own last segment**, `_is_single_folder_name()` | **No.** One string against a derived part of itself. |
| 4 | **Counters and a supplied choice, in scripts rather than the pipeline**: `probe_extract.py`, `regenerate_vendor_codes.py` twice, `retroactive_categorise.py` | **No.** Numbers, and a code the operator passed in. |

**Nothing in this section was changed**, per the brief.

---

## 7. Flags

**Flag 1. The one thing in the change the brief did not ask for, and why I did
it rather than flagging it.**

`worker\extraction\openai_vision.py` sets
`receipt_ref_number=parsed.get("receipt_ref_number")` straight out of the
model's parsed JSON. The schema it asks for says `"string or null (a visible
transaction, ticket, or reference number on the receipt)"` and **nothing
enforces that**, so a receipt numbered `01303` can arrive as the JSON number
`1303`. The bare `!=` compared an int without complaint. `.strip()` on an int
raises `AttributeError`, and the only `try` in `_signals_differ()` is around the
time parse, so it would come out through `process_extraction_result()` and take
the receipt's intake with it.

**So the `str()` is not a widening of the fix; it is the fix not being a
regression.** I read this while checking my own change rather than being told
it, which is why the tests for it came after the fix and lean on mutation 3.

**Two things about it that are checked, not assumed.** `str(value or "")`
preserves the old truthiness exactly, including for `0`. And the stored side can
never be a non-string: `receipt_ref_number` is a TEXT column, so SQLite's TEXT
affinity converts `1303` to `'1303'` on the way in, `typeof()` `'text'`. I
verified that by running the real `CREATE TABLE` statement, lifted as text out
of `schema.py`, against an in-memory database. **Only the in-memory side of the
comparison can be a number**, and the matrix row that writes one is a pin on
that conversion rather than a test of the coercion. Said so in the test.

**Flag 2. `_rule_matches()` compares a rule's `vendor_key` case-sensitively,
and layer 0 is the only layer a person authors by hand.**
`worker\categorisation\engine.py:217`:

```python
if rule.get("vendor_key") and rule["vendor_key"] != vendor_key:
    return False
```

The `vendor_key` passed in comes from `normalise_description()`, which
lower-cases. The rule's own `vendor_key` comes out of
`categorisations_client_rules` and **`create_client_rule()` does not lower it**.
So a rule authored with `APCOA` would never match anything, silently. The
condition comparison four lines below is fine: both sides are already
`.lower()`ed.

**It is not reachable today**, and that is from an enumeration rather than from
a guess: `create_client_rule()` appears once in the whole repository with
`.history\` excluded, its own `def`, with no caller in production code and none
in `tests\` either. So nothing writes a rule row and layer 0 has no rows to
match. **Small and obviously
right if Paul wants it**: lower both sides of that one comparison, one test
over an upper-case rule. It needs his decision on whether the normalising
belongs at write time or read time, and on whether the not-yet-existing rule
editor should do it instead, so it is flagged and left.

**Flag 3. The time comparison's silent skip.** Section 5. A separator the parse
cannot read turns the comparison off, and two genuinely different transactions
with no reference numbers then wait in Review as each other's possible
duplicate. Nothing logs that the comparison did not run. Fails towards a
person, so it is not urgent, and it is not this brief's fault.

**Flag 4, and it is about check 5 rather than the code.** The two RingGo rows on
Paul's machine are still `ok` and both still carry a `published` row. **This
change fixes the next arrival, not the two that are already through**, and
nothing in it reaches back. The duplicate in the books and the copy in
`Clients\Test Sole Trader\IntelliBooks\Receipts\2021-22\` are the two things
section 5 of the brief says are Paul's, and I have touched neither.

---

## 8. My own mistakes

1. **The heredoc that broke a regex.** Patching the enumeration script through
   a shell heredoc turned `\n` inside a raw string into a real newline, split
   the regex across two lines and left a file that would not parse. Rewritten
   with a proper edit. No effect on the repository, which the heredoc never
   touched.
2. **The field list that came back empty, and the assertion that caught it.**
   My first regex for `CREATE TABLE IF NOT EXISTS extractions` required a
   closing quote after the bracket and matched nothing, so `schema_columns` was
   empty and the enumeration would have run on twelve names instead of
   eighteen. It fired the assertion I had written for exactly that, and the
   only reason there was an assertion is `CLAUDE.md`'s rule about a check that
   has never returned anything but a pass. **The enumeration would still have
   printed a plausible answer.**
3. **`or None` written and then deleted.** My first `_comparable_ref()` carried
   an early `return None` and an `or None`, both of which did nothing, and I
   found that out only because a mutation I expected to be caught survived. It
   is in section 4 with the harness output.
4. **The matrix row that could not fail.** I wrote
   `("1303", 1303, ...)` believing it exercised the coercion on the stored
   side. Mutation 3 did not fail it, which sent me to check the column's
   affinity, which is where the answer in flag 1 came from. The row is kept and
   relabelled `"a number stored, which comes back as text"`, with a comment
   saying what it can and cannot prove.
5. **I nearly imported `config` to read a constant.** The first version of the
   affinity check did `import config` through `resolution_fixtures`, outside
   pytest. It failed on the import path before it got that far, and
   `CLAUDE.md`'s fourth trap says why that was lucky: on Windows an
   `import config` outside pytest runs the `mkdir` block against the live roots,
   which created a folder in OneDrive on 2026-09-09. Rewritten to lift the DDL
   out of `schema.py` as text and run it against an in-memory database, with no
   import of `config` at all.

---

## 9. Confidence

- **That the fault is fixed for the next arrival: high, and it is about the
  receipt's status rather than about the comparison.** Ten of the eleven tests
  drive a real `process_once()` and assert `possible_duplicate` with
  `duplicate_of` set on a row read back out of the database, and mutation 1
  puts the case-sensitive comparison back and is caught.
- **That the veto still works: high.** Mutation 7 removes it and three tests
  fail, so the tests asserting it are load-bearing rather than decorative.
- **That the change is as narrow as Paul asked: high.** Mutation 5 shows option
  2 is caught by the suite, so the scope is tested rather than described.
- **That nothing else in the repository has this fault: medium, and what the
  confidence is about matters here.** I am confident about the enumeration I
  ran: 110 comparisons, five naming an extraction field, thirty-nine more with
  a non-constant on both sides, all printed above and all read. I am less
  confident that "compares text from two extractions" has no third shape my two
  passes do not describe. **Pass A alone would have missed the very fault under
  repair**, which is the measured reason for saying medium rather than high.
- **That the time comparison is a different fault: high, because I drove the
  statements out of the tree rather than reading them.** Section 5 carries the
  output.
- **That `create_client_rule()` has no production caller: high, from an
  enumeration of the name across the repository with `.history\` excluded.**
  One hit, its own `def` in `worker\database\repository.py`, and no call
  anywhere including tests. `get_client_rules()` beside it has one caller,
  `worker\categorisation\engine.py:284`, so the rules are read and never
  written.
