# Report: the client's taught supplier mappings, published

Written 2026-11-13 at 18:10 GMT by Claude Code, from
`PROMPT_claude_code_2026-11-13_published_mappings.md`. Sub-step 10bs.10,
pipeline half, amendment 554. **Report file name chosen by me, as the brief
asks:** `2026-11-13_REPORT_claude_code_published_mappings.md`, after the brief's
own name. Not committed.

**Commit `b600b8a`, 8 files.** Suite before: 1662 passed, 2 skipped. After,
run again following the commit because it adds files: **1677 passed, 2
skipped, 1265 subtests.** Not marked built anywhere; that is the consultant
session's.

---

## 1. What I established first

### 1.1 The rows, read from the live database read-only, about 17:55 GMT

16 rows, unchanged from the enumeration earlier today in
`2026-11-13_REPORT_claude_code_vendor_lookup.md` section 1.1.

| Client | Key | Name | Code | Seen |
| --- | --- | --- | --- | --- |
| Client_001 | `imo` | IMO CAR WASH | 7310 | 1 |
| Client_007 | `bearwood` | BEARWOOD TYRE CENTRE LTD | 7310 | 1 |
| Client_007 | `disclosure` | Disclosure & Barring Service | 8240 | 1 |
| Client_007 | `driversnote` | DriversNote | 7561 | 1 |
| Client_007 | `equans` | EQUANS EV Solutions Ltd | 7302 | 1 |
| Client_007 | `geniepoint` | GeniePoint | 7302 | 1 |
| Client_007 | `hertz (u.k.)` | Hertz (U.K.) | 7380 | 4 |
| Client_007 | `hertz rent-to-buy` | Hertz UK Rent-to-Buy | 7380 | 1 |
| Client_007 | `inshur` | INSHUR UK LTD | 7105 | 3 |
| Client_007 | `park group` | Park Garage Group | 7301 | 1 |
| Client_007 | `shell` | Shell Co-op Harborne | 7301 | 3 |
| Client_007 | `shell` | Shell U.K. Oil Products Limited | 7302 | 2 |
| Client_007 | `shell` | Shell U.K. Oil Products Limited on behalf of Shell UK Limited | 7302 | 3 |
| Client_007 | `taxiplus` | TaxiPlus | 8240 | 1 |
| Client_007 | `wolverhampton` | Wolverhampton Private Hire Driver Application | 8240 | 1 |
| Client_007 | `xcel autos` | Xcel Autos Limited | 7380 | 1 |

The registry, `Intellibills\clients.json`, holds Client_001, 003, 004, 005,
006 and 007. Every client id in the table is registered. **So on the first
poll after this lands, six files are written: two with mappings, four with
an empty list.**

### 1.2 Is there already a per-client publish this belongs beside?

**Two per-client files exist, and neither is the right home.** Read from
`config.py` and from `IntelliBooks-Desktop-v3.html` (read, not changed):

- `Intellibills\Receipts\{client_id}-receipts.json`. Section 20.1 of the
  design document defines it as the receipt record store. **Desktop is its
  only writer**: `loadReceipts()` creates it and the Receipts tab writes it.
  The pipeline never writes there.
- `IntelliBooks\Delivery\{client_id}.log`. The pipeline writes it, but it is
  in IntelliBooks' tree. Section 20.6 item 6 moved the publish folder into
  `Intellibills\` because both ends of it are Intellibills, and both ends of
  this file are too.

**Every exchange folder in `Intellibills\` has one writer**: `Incoming\` the
pipeline, `Resolutions\`, `Attached\` and `Receipts\` Desktop. Putting a
pipeline file in `Receipts\` would make it the first folder with two writers,
and would widen 20.1's definition of that folder without a decision. **So it
has its own folder, `Intellibills\Supplier Mappings\`, and its file name
follows the existing pattern: `{client_id}-mappings.json` beside
`{client_id}-receipts.json`.**

One fact made the other choice possible, and I record it in case the
consultant session prefers it. Desktop lists `Receipts\` in one place, the
chart usage report near its line 2634. That code takes only names matching
`-receipts.json`, so a mappings file there would be ignored. Moving the
folder is a one-constant change.

### 1.3 Is it reachable from the browser's one grant?

**Yes.** Desktop's `rootHandle` is the practice root. `verifyRoot()` accepts
it only where `Intellibills\pipeline-status.json` or `Intellibills\clients.json`
is readable under it, and `PIPE_DIR` is `"Intellibills"`. So the file opens as
`getDir(["Intellibills", "Supplier Mappings"])`, then
`getFileHandle(client.id + "-mappings.json")`. `config.SUPPLIER_MAPPINGS_DIR` is
`INTELLIBILLS_ROOT / "Supplier Mappings"`, and the tests pin that parent.

---

## 2. What was built

- **`worker\supplier_mappings.py`**, new. `publish_all(repo)` walks
  `config.CLIENTS_BY_ID` and, for each client, builds the file from
  `Repository.list_client_vendor_mappings()` (new). It writes only where the
  file is missing, unreadable or different from the database, compared as
  parsed JSON.
- **The poll**: `process_once()` in `app.py` calls it straight after
  `_consume_resolution_notes()`, which is the only place a poll teaches. A
  mapping taught from the CLI or the console between polls reaches the file
  on the next poll, by the same comparison.
- **Written atomically**: a part file in the same folder, forced to disk, then
  `os.replace()`. That is the method of `write_item()` in `worker\publish.py`.
  It is a separate function there, not a call to `write_item()`, for the
  reason in 5.1.
- **A failure never stops a poll.** It is logged at WARNING naming the client,
  and the next poll tries again.
- **Teaches nothing, merges nothing, trims nothing, folds no case.** Rows are
  published as stored, ordered by key, then name, then row id, so an unchanged
  set gives an identical file.
- **`UNKNOWN` is never published**, and nor is a client id with rows but no
  registry record.

### 2.1 Empty and missing

**A registered client with no mappings gets a file whose `mappings` is `[]`.**
A missing file means the pipeline has not published for that client: before
the first poll on this commit, for a client registered since the last poll,
or after a failed write. The reader can tell the two apart: no file means
nothing to say, and an empty list means nothing has been taught.

### 2.2 The file

```json
{
 "schema": 1,
 "client_id": "Client_007",
 "mappings": [
  {
   "vendor_key": "shell",
   "vendor_name": "Shell Co-op Harborne",
   "nominal_code": "7301",
   "account_name": "Fuel and oil",
   "times_seen": 3,
   "last_updated": "2026-11-13T12:36:28.829361+00:00"
  }
 ]
}
```

This is an illustration. **Write the reader against the constants below, not
against it.** ASCII on disk, so a non-ASCII name arrives as a `\u` escape,
which `JSON.parse` reads back exactly. `last_updated` is ISO 8601 UTC, as
stored.

---

## 3. The constants, all in `config.py`, beside `ATTACHED_DIR`

| Constant | Value | What it is |
| --- | --- | --- |
| `SUPPLIER_MAPPINGS_DIR` | `INTELLIBILLS_ROOT / "Supplier Mappings"` | the folder |
| `SUPPLIER_MAPPINGS_SUFFIX` | `"-mappings.json"` | file name is `{client_id}` plus this |
| `SUPPLIER_MAPPINGS_SCHEMA` | `1` | the value of the schema key |
| `MAPPINGS_SCHEMA_FIELD` | `"schema"` | top-level key |
| `MAPPINGS_CLIENT_ID_FIELD` | `"client_id"` | top-level key |
| `MAPPINGS_LIST_FIELD` | `"mappings"` | top-level key, a list, empty when nothing is taught |
| `MAPPING_VENDOR_KEY_FIELD` | `"vendor_key"` | per mapping |
| `MAPPING_VENDOR_NAME_FIELD` | `"vendor_name"` | per mapping, the name as taught |
| `MAPPING_NOMINAL_CODE_FIELD` | `"nominal_code"` | per mapping |
| `MAPPING_ACCOUNT_NAME_FIELD` | `"account_name"` | per mapping |
| `MAPPING_TIMES_SEEN_FIELD` | `"times_seen"` | per mapping, an integer |
| `MAPPING_LAST_UPDATED_FIELD` | `"last_updated"` | per mapping, ISO 8601 UTC |

`TheKeysAreTheConstantsTest` in `tests\test_supplier_mappings.py` pins every
value. `test_one_file_per_registered_client_with_every_field` pins that the
file carries exactly these keys.

**One thing for the reader, not in any constant:** a write leaves a
`{name}.{hex}.part` file for an instant. A reader that opens by name never
sees it. One that lists the folder should skip anything not ending in
`SUPPLIER_MAPPINGS_SUFFIX`.

---

## 4. Should the firm pool be published too? My view, not built

**Not now.** Three reasons:

1. **The operator has no lever on it.** The Remember tick writes the client
   table. The firm pool is written only by `_learn_firm_mapping_if_confirmed()`,
   automatically, when the operator's code confirms the classifier. Showing it
   at the tick would show facts the tick cannot change.
2. **10bs.9 already makes a disagreeing firm key fail safe.** Layer 2 gives no
   answer and the receipt goes on, to layer 4 and a `fuzzy_firm` hold or to
   layer 5. Nothing lands wrongly in silence.
3. **The live firm pool has no key with two names**: 9 rows, 9 keys.

**What would change my view:** a screen where the operator edits the firm
pool, or a firm pool disagreement appearing live. Either is Paul's to decide.
Building it would be the same module keyed on `business_type`, at about the
same size again.

---

## 5. Flags

**5.1 Reusing `write_item()` tripped a guard, and the guard was right.** My
first version called `write_item()` from `worker\publish.py` to avoid copying
it. `tests\test_publish_trigger.py`'s
`test_the_item_writer_is_reached_only_through_publish_receipt` went red: it
holds that nothing writes a publish item without recording it. A mappings
file is not a publish item, but calling the item writer blurs the set that
guard watches. So the module has its own ten-line writer, using the same
method, and **the guard is unchanged**. **Offered, not done**: factor the
part-file-and-replace step out of `write_item()` into a small shared function
both call, so the method has one copy. That touches `worker\publish.py`,
which this brief did not ask for.

**5.2 The 15 new tests did not all go red before the code existed.** I wrote
the module before running them, so the only red I saw was the poll test, as
expected before the poll was wired. **Mutations stand in for the missing red**
(section 6), and every behaviour the brief names has one.

**5.3 A test-fixture list and a count moved, as the precedent requires.**
`SUPPLIER_MAPPINGS_DIR` is in `REDIRECTED` in `tests\resolution_fixtures.py`, so
each test's file stays in its own temp folder. The Path-constant count in
`tests\test_conftest_redirect.py` went from 22 to 23, with the matching prose
in `tests\live_paths.py`. **The test that proves nothing writes into the
live practice root is otherwise unchanged and passes.**

**5.4 Subtests moved twice, and I have not traced the first.** They were 1252
before, 1264 before the commit and 1265 after it. The last one fits
`CLAUDE.md`'s note that two source guards sweep the git-tracked set and so
see a new file only once it is committed. **I did not trace which tests
account for the first 12.** They are counted, not explained.

**5.5 The pipeline can now write six files into OneDrive on its first poll,
and only rewrites them on change.** On a quiet poll it writes nothing,
because the comparison is against the parsed file.

---

## 6. Mutations

Six, through `tests\mutation_harness.py`, whole suite each, each restored byte
for byte. All were caught, and only by the new file.

| Mutation | Caught by |
| --- | --- |
| the poll does not publish | 2: the end-to-end poll test and the syntax-tree order test |
| always rewrite | 1: not rewritten when nothing changed |
| no file for a client with no mappings | 4 |
| names trimmed | 1: published as stored |
| a failed write stops the poll | 1 |
| `times_seen` dropped | 1: every field |

---

## 7. My own mistakes

1. **Reusing `write_item()`**, in 5.1. The suite caught it, and the fix was
   to leave the guard alone.
2. **Tests written after the module**, in 5.2.
3. **I first planned to compose the path at call time from
   `INTELLIBILLS_ROOT`**, the way the delivery log does. Reading the fixture
   showed `INTELLIBILLS_ROOT` is not redirected per test, only per session, so
   one test's file would have been the next test's starting state. That is
   why it became a redirected `Path` constant.

---

## 8. Confidence

- **That the pipeline writes the file as specified: high.** Every behaviour
  the brief names is pinned by a test, and each has a mutation that is caught.
- **That Desktop can reach it: high on reading, untested in a browser.** It
  rests on reading `verifyRoot()`, `PIPE_DIR` and `getDir()` in
  `IntelliBooks-Desktop-v3.html`. No Desktop code reads the file yet.
- **That its own folder is the right home: medium.** It follows 20.1's
  one-writer pattern, but it is my reading. 1.2 gives the alternative and
  what it would cost.
- **The live figures in 1.1: high, read-only at about 17:55 GMT.** The live
  folder does not exist until the pipeline next runs on this commit, which is
  Paul's to start.
