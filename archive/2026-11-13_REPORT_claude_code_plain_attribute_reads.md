# Report: a categorisation's fields are read as plain attributes

Written 2026-11-13 by Claude Code, for the consultant session. It implements
section 4 of `2026-11-13_REPORT_claude_code_vendor_key_on_review_items.md`, on
Paul's decision of 2026-11-13.

`2026-07-25_BUILD_STATUS.md` is not touched.

---

## 1. What was done

One commit, `bd38035`, on `feat/console-phase0`. Two files:

| File | Change |
|---|---|
| `worker\publish.py` | `category_is_unconfirmed()` reads `categorisation.match_source`; `extra_for()` reads `categorisation.vendor_key`. The `None` checks above both are unchanged |
| `tests\test_vendor_key_naming.py` | The guard is rewritten on the syntax tree and covers `publish.py` as well as `service.py`; a second test asserts the two plain reads |

**Behaviour is unchanged for every caller that exists.** A future caller that
passes an object without these fields now gets an `AttributeError` where it
used to get `null` or `False`, and that is the point of the change.

---

## 2. The enumeration, done before either read changed

**Method.** I parsed every `*.py` at the repository root, under `worker\` and
under `tests\`: 167 files, with `.history\` and `archive\` excluded. I found
every `ast.Call` whose function's last name segment is `extra_for` or
`category_is_unconfirmed`. I also looked for any `import ... as` alias of
either name, and for any reference to either that is not a call, such as one
passed as a value. **There are no aliases and no non-call references**, so the
list of calls below is the whole set. The script is at
`C:\Users\PDK7\AppData\Local\Temp\claude\43687783b5645321\c06fa307-c485-4b69-9e2e-96335aeb0cf3\scratchpad\enumerate_callers.py`.

**17 calls: 13 to `extra_for()`, 4 to `category_is_unconfirmed()`.**

| Where | Enclosing function | Function | Categorisation passed |
|---|---|---|---|
| `app.py:888` | `_publish_unpublished_receipts()` | `extra_for` | `categorisation` |
| `worker\extraction_pipeline.py:544` | `process_extraction_result()` | `extra_for` | `categorisation` |
| `worker\publish.py:485` | `extra_for()` | `category_is_unconfirmed` | its own parameter |
| `tests\test_category_hold.py:312` | `test_the_trigger_holds_exactly_the_three_machine_answers()` | `category_is_unconfirmed` | `result` |
| `tests\test_category_hold.py:330` | `test_the_trigger_no_longer_tracks_the_needs_review_column()` | `category_is_unconfirmed` | `result` |
| `tests\test_category_hold.py:738` | `test_item_only_keys_is_exactly_what_the_item_adds()` | `extra_for` | not passed, default `None` |
| `tests\test_category_hold.py:746` | `test_extra_for_defaults_to_not_unconfirmed()` | `extra_for` | not passed, default `None` |
| `tests\test_category_hold.py:750` | `test_category_is_unconfirmed_of_nothing_is_false()` | `category_is_unconfirmed` | `None` |
| `tests\test_item_vendor_key.py:216` | `test_no_categorisation_gives_null()` | `extra_for` | not passed |
| `tests\test_item_vendor_key.py:223` | `test_a_categorisation_with_no_key_gives_null()` | `extra_for` | `result()` |
| `tests\test_item_vendor_key.py:227` | `test_an_empty_string_is_published_as_null()` | `extra_for` | `result(vendor_key='')` |
| `tests\test_item_vendor_key.py:233` | `test_the_key_is_passed_through_exactly()` | `extra_for` | `result(vendor_key='shell')` |
| `tests\test_item_vendor_key.py:238` | `test_nothing_else_moves()` | `extra_for` | `result(vendor_key='shell', match_source='ai')` |
| `tests\test_item_vendor_key.py:251` | `test_with_no_categorisation_the_key_passed_is_published()` | `extra_for` | not passed |
| `tests\test_item_vendor_key.py:255` | `test_an_empty_key_passed_is_published_as_null()` | `extra_for` | not passed |
| `tests\test_item_vendor_key.py:262` | `test_a_categorisation_and_a_key_together_are_refused()` | `extra_for` | `result(vendor_key='shell')` |
| `tests\test_item_vendor_key.py:266` | `test_it_survives_json()` | `extra_for` | `result(vendor_key='apcoa')` |

**Where each value comes from:**

- **`result()` in `tests\test_item_vendor_key.py`** builds a
  `CategorisationResult` directly.
- **`result` in `tests\test_category_hold.py`** comes from that module's
  `categorise()` helper (line 177). The helper calls the real
  `CategorisationEngine.categorise()`; one case replaces `_ai_suggest` with a
  lambda returning a dict, which is used inside `categorise()` and never
  returned.
- **The two production callers pass a variable**, so I enumerated every
  binding of the name `categorisation` in both functions from the syntax tree
  (script `trace_origins.py`, same folder):
  - `app.py:809`: `categorisation = categorisation_engine.categorise(...)`
  - `app.py:830`: `categorisation = resolve_against_chart(categorisation, repo=repo)`
  - `worker\extraction_pipeline.py:352`: `categorisation = None`
  - `worker\extraction_pipeline.py:382`: `categorisation = categorisation_engine.categorise(...)`
  - `worker\extraction_pipeline.py:400`: `categorisation = resolve_against_chart(categorisation, repo=repo)`

  Neither function takes `categorisation` as a parameter.
- **Every `return` in `CategorisationEngine.categorise()`, 9 of them, returns
  `CategorisationResult(...)`.** Every `return` in `resolve_against_chart()`,
  5 of them, returns `result`, the object it was handed.
- **What tests hand in place of those, enumerated from the syntax tree over
  `tests\`:**
  - every class defining `categorise()`
  - every `def` of `categorise`, `resolve_against_chart` or
    `CategorisationEngine`
  - every assignment to an attribute of those names
  - every `patch`, `patch.object` or `setattr` naming them

  Four were found:
  - `test_category_hold.py:177`, `categorise()`: a helper over the real
    engine.
  - `test_correction_keeps_original_suggestion.py:79`, `CountingEngine`: a
    subclass that counts calls and returns `super().categorise()`.
  - `test_vendor_lookup_by_name.py:107`, `_Base.categorise()`: a helper over
    the real engine.
  - `test_firm_vendor_writer.py:316`: patches `categorise` with `fake`, which
    returns `ai_result()`, which builds a `CategorisationResult` (line 82).
  - **No test replaces `resolve_against_chart`.**
- **Every engine handed to the pipeline in tests** is a real
  `CategorisationEngine`: either built directly, or through `env.engine()`
  in `resolution_fixtures.py`, `env_engine()` in four test modules, or
  `CategorisationEngineFor()` in `test_stage4_client_copy.py`. All were read.

**Conclusion: every value reaching either function is `None` or a
`CategorisationResult`.** `vendor_key` and `match_source` are declared fields
of that dataclass with defaults, so every instance has both. No caller passes
an object without them, so the change went ahead.

**And the production `getattr`s were exactly two.** A syntax-tree search over
the root and `worker\` for `getattr` whose first argument mentions a
categorisation found `worker\publish.py:438` (`match_source`) and `:478`
(`vendor_key`), and nothing else.

---

## 3. The guard

**`test_nothing_reaches_a_categorisation_field_through_getattr`**, replacing
`test_neither_branch_reaches_the_field_through_getattr`. It parses
`worker\resolution\service.py` and `worker\publish.py` and finds any call to
`getattr` whose first argument is the name `categorisation`, one subtest per
file. The old version matched the line text `getattr(categorisation` in
`service.py` only. It would have missed a call split over two lines, and it
would have flagged struck wording in a docstring.

**`test_publish_reads_both_fields_as_plain_attributes`** is the positive half.
It asserts `extra_for()` reads `categorisation.vendor_key` exactly once and
`category_is_unconfirmed()` reads `categorisation.match_source` exactly once.
Without it, the guard could pass because a read was deleted rather than
corrected.

**Red first.** With the guard written and the reads unchanged, the
`publish.py` subtest failed, listing
`438: getattr(categorisation, 'match_source', None)` and
`478: getattr(categorisation, 'vendor_key', None)`. Both positive subtests
failed too, and the `service.py` subtest passed. That pre-change state is the
mutation that matters, putting a `getattr` back, so I ran no separate
mutation.

**Scope.** The guard watches the two files named, as asked. A search over the
whole production tree costs nothing more and today finds nothing. I can widen
it if you want new files covered as well as these two.

---

## 4. Evidence

**Suite after the commit**: 1703 passed, 2 skipped, 1296 subtests. That is
one test more than after `b61f055` (one renamed, one added) and 4 subtests
more (two files and two functions).

---

## 5. Confidence

- **High that no caller passes an object without these fields.** It rests on
  the syntax-tree enumeration in section 2: every call, every binding in the
  two production callers, every return of the two producing functions, every
  test replacement. This replaces the medium of the earlier report, which
  rested on a search by name.
- **What it does not cover: a caller added later.** That is what the plain
  read is for: such a caller now raises instead of publishing a wrong answer
  quietly.
