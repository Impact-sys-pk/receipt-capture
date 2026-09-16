# Report: the classifier's inputs and its switch

**Claude Code, 2026-09-12.** From
`PROMPT_claude_code_2026-09-12_classifier_inputs_and_switch.md`, md5
`d4112a5eeaec1060e3f519e25d8a39de`, checked before reading and matching. Step 10p, amendment 340.

**Two commits on `feat/console-phase0`, neither pushed.**

| Commit | What |
|---|---|
| **`a45a8ce`** | The one-line fix Paul asked for first: `resolve_receipt.py` states `enable_ai_fallback=False`. |
| **`4c90130`** | Step 10p, all three parts. 14 files, 1,212 insertions, 71 deletions. |

**The suite: 1366 passed, 1 skipped, 936 subtests**, run again after the commit and green there too.
It was 1330 before this work.

**Nothing is turned on.** The setting ships off for every firm.

---

## 1. For Paul: the setting, and the command you have to run

### The setting, exactly as the consultant session needs it for the screen

| | |
|---|---|
| **File** | `Intellibills\firms.json`, on the firm record, beside `client_copy_trigger` |
| **Key** | `classifier_enabled` |
| **Values** | JSON `true` or JSON `false`. **Not the strings `"true"` and `"false"`.** |
| **Absent** | **Off.** A firm record written before today is not switched on by this change. |
| **Anything else** | **Refused, loudly, at pipeline startup.** |

```json
{
  "firm_id": "FIRM001",
  "name": "Intellitax",
  "client_top_folder": "...",
  "publish_destinations": { "intellibooks": "Incoming" },
  "client_copy_trigger": "post",
  "classifier_enabled": false
}
```

**Why a value that is present and is not a boolean refuses rather than being read loosely.** A string
`"false"` is **truthy** in Python. Read loosely, a record that says the classifier is off would turn
it on, and it costs money per receipt. Absent is a decision nobody has taken; `"false"` is a decision
somebody took and wrote down wrongly, and those want different answers.

**This differs from F16 in one respect and deliberately.** `client_copy_trigger` refuses a record
that lacks it, because a trigger the pipeline misreads writes a document into a client folder and
18.2b says a copy is never withdrawn. **Here the risk runs the other way**: the thing to prevent is
the classifier coming on for a firm that never asked, so absent means off.

### The migration, and it cannot be run against the live database by accident

```
cd C:\LastingImpact\receipt_capture
.\.venv\Scripts\python.exe migrate_2026_09_12_line_items.py --dry-run
```

That prints the statement, the row count and the columns, and **changes nothing**. Read it, then:

```
cd C:\LastingImpact\receipt_capture
.\.venv\Scripts\python.exe migrate_2026_09_12_line_items.py --write
```

**`--write` is required and a dry run is what happens without it**, so the command that changes
something cannot be reached by pressing return on the one that does not.

**Close the pipeline first.** SQLite will let two processes write and a migration racing a poll is
not a risk worth taking for the sake of not closing a window.

**It takes its own backup before it writes** and prints the path, beside `receipts.db` and named
`receipts-backup-<stamp>-pre-line_items.db`. That is separate from the daily copies in
`Intellibills\Backups\`.

**It adds one column and nothing else. Nothing is backfilled and nothing can be.** The receipts
already in the database had their item lines read once, handed to the classifier in memory and
dropped. There is no record of them anywhere. A backfill would mean re-extracting, which costs money
per receipt and would overwrite readings you may since have corrected.

**Run it twice and the second run says there is nothing to do.**

---

## 2. Part 1: the item lines are stored

### What was wrong, re-measured rather than taken from the brief

Enumerated from the syntax tree across the 55 production files:

```
categorise() production call sites: 7
  PASS line_items: 1
     worker\extraction_pipeline.py:377  in process_extraction_result
  DO NOT pass: 6
     app.py:682                         in _publish_unpublished_receipts
     probe_extract.py:120               (passes its own, off a fresh extraction)
     probe_layer5.py:94                 in main
     retroactive_categorise.py:141      in main
     worker\resolution\service.py:1225  in resolve_receipt
     worker\resolution\service.py:2240  in _apply_filed_note
```

**Seven, not six.** The brief and amendment 340 both say six. The difference is whether the two probe
scripts count: **excluding them it is five, of which one passed and four did not**, which is exactly
what amendment 340 describes. Including them it is seven. Neither reading gives six. The conclusion
is unaffected and the number is corrected here rather than carried.

**After the change, all seven pass them and none do not.**

### What changed

- **`ExtractionResult.line_items` is a list of `LineItem`**, description and amount separate, where
  it was a list of strings with the amount run into the description.
- **`worker/line_items.py` is new** and is the only thing that knows the stored format. It sits
  outside `worker/extraction/` because the repository needs it too and must not import the
  extraction layer to store a column.
- **`extractions.line_items`**, TEXT holding JSON, added by `schema.py` for a new database and by
  the migration for an existing one.
- **The vision prompt asks for objects**, and the normaliser still reads the two shapes the old
  prompt produced, because a model answers the prompt it was given and this one has changed.
- **The five paths that read an extraction back out of the database now read the lines back too.**
  Each of them carried a comment saying the lines are not stored. **Those comments were the defect
  written down**, and each is struck rather than deleted.

### The three things the brief asked me to decide and report

**One. An amount that cannot be read is `null`, not nought.** A line with no amount is ordinary on a
receipt, and **a receipt can also print a line at 0.00**: a free item or a fully discounted one.
Those are different facts. Storing a missing amount as 0.0 would make a future split that sums its
lines silently disagree with the document, which is the one thing 18.4's split must not do, since its
lines must sum to the original.

**Two. The 40-line cap stays, and it is now enforced in code as well as asked for in the prompt.** It
was advisory: the prompt said "List at most 40 lines" and nothing truncated a model that answered
with more. **That was harmless while the lines were held in memory and dropped. It is not harmless
now they are written to a column.** The ceiling is also a real cost control: `max_tokens` was raised
from 500 to 1500 on 2026-09-05 specifically to fit 40 lines. A receipt with more than 40 stores the
first 40, which is what the prompt already asked for.

**Three. What the classifier is sent.** **The same thing it always saw**: the description, then the
amount where one was read, one line each. `line_items.for_prompt()` is where the stored shape and the
prompt's wording meet.

**That is deliberate and it is the only reason part 1 is measurable at all.** Part 2 changes the same
API call in the same commit, and changing what the model is looking at at the same time would leave
neither change attributable. A line with no amount is shown without one, not as "LOOSE ITEM None" and
not as "LOOSE ITEM 0.00".

---

## 3. Part 2: the call is deterministic, and one run against the real API

`temperature=CLASSIFIER_TEMPERATURE` and `seed=CLASSIFIER_SEED`, both named constants, on the call
that passed `model`, `messages` and `response_format` and nothing else.

**The live check the brief asked for. One supplier, three calls, three identical answers.**

```
model        gpt-4o
temperature  0
seed         20260912
supplier     'London Borough of Camden'   gross 3.8   2 item line(s)

call 1   {'code': '7340', 'name': 'Parking and tolls'}
call 2   {'code': '7340', 'name': 'Parking and tolls'}
call 3   {'code': '7340', 'name': 'Parking and tolls'}

three identical answers: True
tokens       prompt 3075, completion 39, total 3114, over 3 call(s)
```

**What it cost.** 3,075 prompt tokens and 39 completion tokens across three calls, so about 1,025 and
13 per call. At gpt-4o's published rates, 2.50 US dollars per million input tokens and 10.00 per
million output, that is **about 0.8 of a US cent for all three**, so **roughly a quarter of a cent
per classifier call**. **I have not opened OpenAI's pricing page in this session**, so the token
counts are measured and the rates are from memory: treat the money figure as an order of magnitude
and check https://openai.com/api/pricing/ before quoting it.

**Two things about that result I will not overclaim.**

**The answer is now right, and determinism is not why.** The probe returned `7113 Business rates` and
`7110 Rates` for this supplier, both wrong on a parking payment. It returned `7340 Parking and tolls`
here. **That is almost certainly part 1, not part 2**: this call was told the item lines said
"PARKING SESSION" and the probe's calls were told nothing about what was on the receipt, because
nothing stored it. Determinism makes the answer the same; the item lines are what made it a better
one. **One observation of one supplier is not evidence of a general improvement.**

**Three identical answers is not proof of determinism.** It is one input, run three times, in one
session. OpenAI documents `seed` as best-effort and pairs it with a `system_fingerprint` that can
change underneath the caller, so `temperature=0` is the load-bearing half. Said here rather than
discovered later from two answers that should have matched.

---

## 4. Part 3: the switch

- **`config.CLASSIFIER_ENABLED_FIELD` and `config.CLASSIFIER_ENABLED`**, read at import so a value
  the pipeline cannot understand stops it at startup rather than being met one receipt at a time.
  That is `CLIENT_COPY_TRIGGER`'s reason too.
- **Read at exactly one construction site**, `app.py`'s, which is the live poll. Enumerated:

```
app.py:1343                    enable_ai_fallback=config.CLASSIFIER_ENABLED   <- the live poll
probe_extract.py:86            enable_ai_fallback=True                        <- a probe
probe_layer5.py:75             enable_ai_fallback=False                       <- a probe, both ways
probe_layer5.py:76             enable_ai_fallback=True
resolve_receipt.py:275         enable_ai_fallback=False                       <- hard off
retroactive_categorise.py:99   enable_ai_fallback=False                       <- hard off, per the brief
```

**Six, not one, which the brief said to check rather than assume.** Its conclusion holds: only one of
them is the live poll and only that one reads the setting. `retroactive_categorise.py` stays hard off
because turning it on re-runs history and spends money on receipts already dealt with, and a test
asserts that rather than trusting the comment.

**No environment variable.** Amendment 340 records the refusal and a test asks the reader function
itself whether it consults the environment.

---

## 5. Evidence

### Red before green

The new tests were written against the unchanged code. Eleven tests in
`tests/test_layer5_context.py` went red the moment the contract changed, and **two of them were
asserting the defect**:

```
FAILED tests/test_layer5_context.py::ExtractionCarriesLineItemsTest::test_nothing_stores_them
FAILED tests/test_layer5_context.py::EveryCallSitePassesTheAmountTest::test_only_the_live_path_can_pass_line_items
```

Both are **reversed rather than deleted**, with the old wording struck in the docstring.
`test_only_the_live_path_can_pass_line_items` becomes
`test_every_one_of_them_passes_the_line_items`, which is the guard over the set the brief asks for:
an eighth path added later fails there rather than silently sending the classifier nothing.

**And a stub caught something on the first run after it changed**, which is worth recording because
it is `CLAUDE.md`'s rule of 2026-09-08 working:

```
AI categorisation failed for halfords: _PromptRecorder.parse() got an unexpected
keyword argument 'temperature'
```

`_PromptRecorder.parse()` names every parameter the real call passes rather than taking `**kwargs`.
**A stub taking `**kwargs` would have swallowed `temperature` and `seed` silently and every test
there would have stayed green while the two went unasserted.**

### The migration, rehearsed on a copy

Run against a copy built from `schema.py` **as it stood before this change**, seeded with 33
extraction rows so "nothing is backfilled" is measured rather than asserted against an empty table.

```
statement  ALTER TABLE extractions ADD COLUMN line_items TEXT

DRY RUN. Nothing was changed.

backup     ...\rehearsal-backup-20260912-132052-pre-line_items.db
columns    ..., receipt_time, line_items
rows       33 before and after: 33 -> 33
line_items filled on 0 row(s), which must be 0: nothing is backfilled
```

**The first rehearsal ran against 0 rows** because my seed rows failed a NOT NULL constraint I had
not read. A migration proved against an empty table proves very little, so it was rebuilt with rows.
Disclosed rather than quietly redone.

Re-run with `--write` a second time: `Nothing to do: extractions.line_items already exists.`

### Mutations

Five, each anchored once, each printing its diff, each restored byte for byte, each against the whole
suite.

| Mutation | Expected | Result |
|---|---|---|
| `stored-but-not-read-back` | caught | **caught, 5 failures** |
| `store-the-amount-as-a-string` | caught | **caught, 2 failures** |
| `drop-the-temperature` | caught | **caught, 10 failures** |
| `default-the-setting-on` | caught | **caught, 1 failure** |
| `prose-only-control` | survives | **survived** |

**`default-the-setting-on` is the one that would cost money if it shipped**, and it is caught by
exactly one test: `test_a_firm_record_with_no_setting_leaves_the_classifier_off`. One is enough
because it is the right one, but it is worth knowing the margin is one test.

**`drop-the-temperature`'s ten failures are mostly the stub**, not ten independent checks: eight are
`test_layer5_context.py` tests failing because `_PromptRecorder.parse()` no longer matches the call.
The two that assert the thing directly are `DeterminismTest`'s.

**The read-back mutation anchors on `worker/line_items.py`, not on either service call site**,
because the two sites in `worker/resolution/service.py` are byte-identical in the line that matters.
That is the substring trap the harness documents, avoided by choosing a different anchor rather than
by hoping.

### The headline test, and a near-miss in it

`TheSameInputEveryTimeTest` drives a receipt read once and then re-read out of the database, and
asserts the classifier is handed the same lines both times.

**It passed on its first run for the wrong reason.** `categorise()` calls `_ai_suggest()`
**positionally**, so my helper read `call_args.kwargs`, got `None` both times, and compared `None`
with `None`. Found by reading the failure of the other assertion in the same test rather than by
suspicion. The helper reads both forms now, the reason is in a comment beside it, and **the test was
then proved to discriminate**: breaking `from_json()` makes it fail, and the file was restored
byte-identical afterwards.

### What must not change, checked

- **No stored value moved** beyond the new column. No backfill, no rewrite, no re-extraction.
- **The extracted supplier, date, net, VAT and gross are untouched**, and so is every test that
  asserts them.
- **Nothing published, re-processed, and no receipt's status moved.**
- **`categorisations.needs_review`, `match_source` and `publish.category_is_unconfirmed()` are
  untouched.**
- **Nothing written into `Clients\`, `IntelliBooks\` or `Intellibills\Documents\`**, and the live
  practice root and the live database were never touched. The migration was rehearsed on a copy in
  the scratchpad.
- **`import config` was never used to read a value** outside pytest's redirect.
- **The classifier is on for no firm.**
- **The tree-wide invalid-escape sweep is back to zero** across 144 files. I introduced one, in a
  SQL comment inside `schema.py`'s non-raw string, and fixed it before committing.

### Committing and the index

**Committed by naming fourteen paths.** Files the brief forbids committing were modified in the
working tree throughout, by the consultant session:

```
 M 2026-07-25_CONSOLE_DESIGN.md
 M 2026-08-20_LIST_outstanding_items_and_decisions.md
 M PROMPT_claude_code_2026-09-11_london_time_and_output_paths.md
?? PROMPT_claude_code_2026-09-12_attached_documents.md
```

**All four are still exactly that after the commit, and the index is empty.** Verified afterwards.

**The suite was run again after the commit**, since the change adds three files. Green.

---

## 6. The fix Paul asked for first, and the one that was already done

**`resolve_receipt.py` now states `enable_ai_fallback=False`**, commit `a45a8ce`. It was the one
construction site of six passing no keyword. The default is `False`, so nothing changes today; it
matters because that is the CLI run by hand, and the one place where a change to the default would
turn the classifier on without anybody choosing it. Re-enumerated afterwards: **six sites, zero
relying on the default.**

**The other one was already done.** `tests\test_step10d_routing.py:181` was fixed earlier today in
commit `44f743e`, on Paul's instruction at the time. The line is already `r"..."`, and compiling all
143 files with `SyntaxWarning` raised as an error reported zero. **Not repeated**, and said here so
the instruction is not left looking unanswered. It is an assertion message rather than a docstring,
which I corrected in that commit's message.

---

## 7. Flags. Nothing here was fixed

**Flag 1. `probe_extract.py` prints each item line with an f-string, so it now prints a dataclass
repr**, `LineItem(description='MILK 2L', amount=1.45)`, where it used to print the line. It is a
probe, the repr is informative, and nothing depends on the format. **Obvious fix: print
`for_prompt(items)` instead**, one line, so the probe shows what the model is shown. Not taken,
because the brief does not name that file and it changes what a measurement tool displays.

**Flag 2. `probe_extract.py:86` builds an engine with `enable_ai_fallback=True` and does not read the
new setting.** That is correct for a probe, whose purpose is measuring layer 5, and it is why it is
excluded from part 3. **But it means the setting being off does not stop somebody spending money by
running that script**, which is worth knowing rather than discovering. **Obvious fix: none in the
code.** Turning it off would remove the script's reason to exist. It is a flag about what the setting
does and does not protect.

**Flag 3. Amendment 340 and the brief both say six `categorise()` call sites and there are seven**,
or five excluding the probes. The conclusion drawn from the count was right either way. **Obvious
fix: none needed in the code**; the number is corrected in section 2 so the next session counts
rather than quotes.

**Flag 4. `CLASSIFIER_SEED` is `20260912`, the date this was decided, and the number carries no
meaning.** Any fixed integer would do. It is flagged because a date-shaped constant invites a reader
to think it should be updated, and it must not be: changing it changes the answers. **Obvious fix:
none.** The docstring says so in terms.

---

## 8. My own mistakes

- **The first migration rehearsal ran against 0 rows**, because my seed inserts failed a NOT NULL
  constraint on `receipts.message_id` that I had not read. I noticed from the row count in the
  output, not from the traceback scrolling past. Rebuilt with 33 rows.
- **`TheSameInputEveryTimeTest` passed on its first run by comparing `None` with `None`**, because
  `categorise()` passes `line_items` positionally and I read `call_args.kwargs`. Section 5.
- **My first version of `test_no_environment_variable_decides_this` matched the FIELD NAME**,
  `classifier_enabled`, and failed on it. A field name on a firm record and an environment variable
  are different things that share a word. The test now asks the reader function whether it consults
  the environment.
- **I introduced an invalid escape sequence** into `schema.py`'s SQL string, `worker\line_items.py`
  inside a non-raw Python string, hours after confirming the tree was clean of them. Caught by
  `py_compile` on the next command and fixed before committing.
- **I put two module-level constants inside a class body** in `engine.py` and got an
  `IndentationError`. Fixed by moving them, not by indenting them into class attributes, which would
  have compiled and been wrong.

---

## 9. Confidence

**High, that every path now sends the classifier the same lines the first read stored.** It rests on
a guard over the set of call sites read from the syntax tree, on a behavioural test that drives a
first read and a re-read and compares both the objects and their prompt rendering, and on a mutation
that breaks the read-back and is caught five times. Not on my reading of the five call sites.

**High, that nothing is backfilled and no stored value moved.** It rests on the migration rehearsed
against 33 rows with the row count and the filled count read back, and on a source guard asserting
the migration contains no `UPDATE`, `INSERT` or `DELETE`.

**High, that the classifier is off for every firm and cannot be switched on by an upgrade.** It rests
on the absent-means-off test, on the refusal of any non-boolean value, and on a mutation that
defaults it on and is caught.

**Medium, and the proposition is narrow: that the classifier's answers are now stable in
production.** What I verified is one supplier, three calls, one session, three identical answers, and
that the two parameters reach the call. **What I cannot verify is stability across sessions, across
model updates, or across other suppliers.** OpenAI documents `seed` as best-effort. If step 10m ever
teaches a firm-wide mapping from an answer that turns out not to have been stable, this is the
paragraph to come back to.

**Low, and I want this one stated plainly: that the classifier's answers are now GOOD.** One receipt
came back right where the probe had it wrong twice. **That is one observation, and the likely cause
is the item lines rather than anything about determinism.** Nothing here measures accuracy, and
turning the classifier on for a real client is your decision with step 10l's hold in front of it.

**Not verified: anything on your machine.** The migration has not been run against
`C:\Intellibills\db\receipts.db`, the pipeline has not been started, and no firm record has been
changed.
