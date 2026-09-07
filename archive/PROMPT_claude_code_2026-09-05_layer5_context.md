# Brief: give layer 5 the amount, and extract line items

**Paul's instruction, 2026-09-05.** Read this whole file before starting.

**Layer 5 ran for the first time on this project today.** It had never run before: it was
constructed with `enable_ai_fallback=False` everywhere. Two defects were found and fixed by the
consultant session this afternoon, both already on disk and both covered by a green suite, **389
passed, 190 subtests**, run by Paul at 13:33 BST.

- `_ai_suggest()` passed `response_format` as a dict. `client.beta.chat.completions.parse()` only
  parses the reply when it is given a model class, so `message.parsed` was always `None` and every
  call logged `AI response invalid` while the answer sat unread in `message.content`. Fixed with a
  Pydantic model, `AiAccountSuggestion`.
- Layer 5 was given only the normalised `vendor_key`. "Canary Hand Car Wash" reaches it as
  `canary`, so the model answered "Software and subscriptions". Fixed by passing `supplier_name`
  as well.

**This brief is the next two steps. It does not change what layer 5 chooses from.**

---

## What the run showed, and it is the reason for task 1

Six receipts, probe output read by Paul and by the consultant session:

| Supplier | Answer | Wrong because |
|---|---|---|
| Halfords | `0081 Motor vehicles - cars - additions` | **No amount.** Nothing stopped a small receipt becoming a capitalised car |
| Asda Wallington | `7520 Stationery and office supplies` | No line items. A supermarket receipt cannot be read from the supplier name |
| Canary Hand Car Wash | `7391 Car wash`, correct, on the 95-account master pool | This one worked |

---

## Task 1. The amount reaches layer 5

**`gross_amount` is already extracted and is in hand at both call sites. It is not passed.**

- `CategorisationEngine.categorise()` in `worker/categorisation/engine.py` takes `receipt_id`,
  `extraction_id`, `supplier_name`, `client_id`, `business_type`. Add `gross_amount`, defaulting to
  `None`
- `_ai_suggest()` at line 353 takes `vendor_key`, `client_id`, `supplier_name`. Add `gross_amount`
  the same way, and put it in the prompt beside the supplier
- **Three call sites, enumerated by grep rather than by memory**: `app.py:478`,
  `worker/extraction_pipeline.py:218`, `retroactive_categorise.py:133`. The first two have
  `extraction.gross_amount` in scope. Check the third yourself and say what you found
- **`probe_layer5.py` in the repository root calls `categorise()` too.** It is the consultant
  session's read-only probe. Update it with the rest
- **Say in the prompt what the amount is**, so the model is not left to guess whether it is net or
  gross. It is the gross where the extraction established one, and it can be `None`

**Do not add a capitalisation threshold.** Paul's ruling of 2026-09-05 is that the five asset
accounts are gated on amount, and **the figure is outstanding item 33 and is not yet decided.**
Passing the amount is this task. Acting on it is not.

## Task 2. Line items come out of the extraction call

- `_SYSTEM_PROMPT` in `worker/extraction/openai_vision.py` asks for nine fields and no line items
- Add a `line_items` field: the item lines as they appear on the receipt, or null
- **The image is already being sent.** This costs a longer reply on a call that is already made,
  not a second call

## Task 3. Layer 5 uses them

- Carry `line_items` on `ExtractionResult` in `worker/extraction/base.py`
- Pass them through `categorise()` to `_ai_suggest()` and into the prompt
- **Nothing is stored.** No column on `extractions`, nothing in the sidecar, nothing to IntelliBooks.
  Storing line items is a separate decision with a schema change behind it and it is not in this
  brief. **Flag it, do not build it**

---

## Verify, and report what you ran

**Write the report to `2026-09-05_REPORT_claude_code_layer5_context.md` in the repository root.**

1. `.\.venv\Scripts\python.exe -m pytest -q` before you start. Expect **389 passed, 190 subtests**
2. The same after. The pass count should move only by tests you added
3. `.\.venv\Scripts\python.exe probe_layer5.py`. **Quote the whole output.** Six OpenAI calls
4. Say whether `0081 Motor vehicles - cars - additions` still comes back for Halfords, and whether
   Asda moves off `7520`
5. **If an answer gets worse, say so.** This is a measurement, not a demonstration

## Tests

- A test that `categorise()` passes the amount and the line items to `_ai_suggest()`. Mutation:
  drop each from the call site in turn and show which test goes red
- A test that `_ai_suggest()` puts both in the prompt when they are present, and omits them cleanly
  when they are `None`
- **Grep for the exact string before rewriting any message a test asserts on.** Amendment 200 is on
  the record because that was not done

## Do not

- Do not change what layer 5 chooses from. That is the client's published chart today and a
  decision about it is open as item 152
- Do not add a second OpenAI call anywhere
- Do not put the chart into the extraction prompt. `BaseExtractor` and the factory exist so a
  second provider inherits behaviour; a chart-aware extractor would have to be rewritten per provider
- Do not store line items
- Do not touch `enable_ai_fallback`'s default. It stays `False`

## Commit

**Commit the working tree first, before you start.** `worker/categorisation/engine.py` and
`probe_layer5.py` are uncommitted: they are the consultant session's two fixes from this afternoon
and the green suite covers them. One commit for those, naming the defect and the suite figure.
Then a second commit for this brief's work.
