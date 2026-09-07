# Brief: the pipeline reads the client top folder from the firm record

**Written 2026-09-07 by the consultant session, chat 17. Branch `feat/console-phase0`.**
**Sub-step 10e.14 of `2026-07-25_CONSOLE_DESIGN.md`, piece three of four.**

**Read this whole file before starting. Then read sub-step 10e.14 and sub-step 10e.15 in section 16
of the design document, and the paragraph below 10e.15 that says where F17 is stored.** Amendments
261 and 262 are the dated trail and they changed the design twice today.

---

## 1. What this is for, in Paul's words

**"This piece of work is really to see how a multi-firm cloud version might look. I dont really need
it for my firm because my top folder is `Clients`. However anothers top folder might be called
anything. And if any of the code is to be ported to the Cloud version I would rather we deal with
this now."** Paul, 2026-09-07.

**So the deliverable is not a behaviour change on his machine.** His stored value resolves to the
same folder the code composes today. **The deliverable is that the word `Clients` stops being
written into the pipeline**, and a firm whose folder is called something else works without a code
change.

**The cloud version will be on AWS.** The client top folder is the firm's own filing structure, per
section 18.2 of the design document, so it is not storage this product owns and it does not move to
the cloud when our storage does. Recorded as the ninth constraint in
`2026-09-01_DESIGN_cloud_multi_firm.md`.

---

## 2. What already exists, and it is done

**`client_top_folder` is a field on the firm record and it holds a value.** Read off Paul's machine
at 16:32 BST today, after he typed it in:

```json
{
  "version": 1,
  "firms": [
    {
      "firm_id": "FIRM001",
      "name": "Intellitax",
      "email": "bills@intellitax.co.uk",
      "phone_app_url": "https://intellitax-receipts.netlify.app",
      "client_top_folder": "C:\\Users\\PDK7\\OneDrive - Intellitax Accounting Limited\\Clients"
    }
  ]
}
```

**`IntelliBooks-Desktop-v3.html` writes that field and refuses to save a value that is not an
absolute path.** Change log items 65 to 67 of `IntelliBooks\App\Docs\IntelliBooks-Change-Log.md`.
**Nothing reads it yet. That is what this brief is for.**

**F17 is ONE field, and the folder name is its last segment.** Amendment 261, Paul's decision. It
was two fields until today and the second one has gone; if you find a document still describing a
separate name field, it is stale and worth flagging.

---

## 3. What to change

**The pipeline takes the client top folder from the firm record instead of composing it from the
practice root.**

`config.py` today reads:

```python
CLIENTS_ROOT = PRACTICE_ROOT / "Clients"
```

**That is the only place the literal `"Clients"` appears in any production Python file in this
repository**, and there are exactly three occurrences of `CLIENTS_ROOT` in total. Enumerated
2026-09-07 by grepping all 41 production `.py` files, listed by walking the folders rather than
matched by a pattern, and the output printed whole:

| Where | What it is |
|---|---|
| `config.py`, the definition above | The only definition |
| `worker/filing.py`, inside `get_client_directory()` | The only reader |
| `app.py`, in a comment | Describes what a function used to do. Not a reader |

**`tests\` was not staged and is not in that count.** Search it yourself before assuming the set is
complete; that is this project's own rule about a claim over a set.

**`get_client_directory()` is the single choke point on the reading side**, and it returns
`config.CLIENTS_ROOT / client_folder_name / config.CLIENT_INTELLIBOOKS_FOLDER_NAME`. Its two callers
are `file_receipt()` and `file_statement()`.

### Keep the change inside `config.py` if you can, and here is why it matters

**`get_client_directory()` and `file_receipt()` are frozen by section 18.2b of the design document,
and that freeze is still live**: it holds until section 18.3's inbox handoff passes its acceptance
test, and 18.3 is not built. The freeze was narrowed once, for step 10d only, by amendment 113, and
that narrowing named exactly what could change and said "and may change nothing else".

**There is no such narrowing for 10e.14.** So if the change can be made where `CLIENTS_ROOT` is
defined, no frozen function is touched and no ruling is needed. **If you find that it cannot, stop
and report that rather than changing a frozen function**, because narrowing the freeze again is
Paul's decision and not yours or mine.

---

## 4. The rule when the field is absent, and this is a decision Paul may overrule

**Refuse at import, with a message that names the field and the file.** No default and no fallback
to `PRACTICE_ROOT / "Clients"`.

**Why refuse.** It is the rule this project has applied every other time: amendment 245 made the two
roots required and absolute with no defaults; sub-steps 10d.13, 10d.17 and 10d.19 removed silent
fallbacks one by one; and amendment 253 made all four SMTP settings required. **A default here would
also keep the literal `"Clients"` in `config.py`, which is the thing this sub-step exists to
remove.**

**What refusing costs, stated so it is a decision and not a surprise.** A pipeline whose
`firms.json` has no `client_top_folder` will not start. That includes a fresh checkout. Today such
an installation starts and files into a guessed folder.

**This is the consultant session's call and Paul has not ruled on it.** If he tells you to default
instead, the default is `PRACTICE_ROOT / "Clients"`, it is logged at import when it is taken, and it
is documented as a default rather than left to be discovered.

### The problem refusing creates, and it is the reason this section exists

**Under pytest there is no firm record at all, so a refusal at import would stop the whole suite.**
Established by reading, not assumed:

- `tests\conftest.py` imports `tests\live_paths.py` before anything else, which redirects both roots
  into a temp folder.
- `FIRMS_JSON` is derived from `INTELLIBILLS_ROOT`, so under pytest it points into that temp folder,
  where no `firms.json` exists.
- `tests\live_paths.py` says in terms, under "What it does not do": **"It redirects paths and nothing
  else. `CLIENTS_BY_ID`, `CLIENTS`, `FIRMS`, `PREFER_DAYFIRST`, `EXTRACTION_ENGINE`,
  `DEFAULT_FIRM_ID`, `_CLIENTS_MTIME` and `get_pipeline_version` are still each test's own
  business."**

**So `config.FIRMS` is `{}` under pytest and always has been.**

**And there is a second consequence even if you do not refuse.**
`tests\test_conftest_redirect.py`'s `test_every_config_path_constant_is_under_a_temp_root` asserts
that there are **exactly 18** config `Path` constants and that every one except `BASE_DIR` is under a
temp root. **A `CLIENTS_ROOT` sourced from the live `firms.json` would be under neither**, and that
test's own failure message would be correct: the run would be touching the live client folder.

**What to do about both.** The route the consultant session would take is to have `live_paths.py`
provide a minimal firm record inside the temp practice root before `config` is imported, so the
suite exercises the real code path against a temp folder. **That extends what `live_paths.py` does,
and its own docstring currently says it does not do that, so the docstring changes with it and the
reason goes in the docstring.** **You own the pipeline and the suite. If you can see a better route,
take it and say why.**

**Do not make either test pass by loosening it.** A test that asserts the redirect is in force is
the one thing standing between the suite and Paul's live client folder, and this project has already
recorded what a check that cannot fail costs.

---

## 5. Which firm's record

**`firms.json` holds one firm.** `config.load_firms()` returns a dict keyed on `firm_id`.

**Take the record when there is exactly one, and refuse with a plain message when there is more than
one.** Local multi-firm is not built and will not be built, which is Paul's decision of 2026-08-20
recorded as amendment 117 and as section 1 of `2026-09-01_DESIGN_cloud_multi_firm.md`.

**Do not reach for `DEFAULT_FIRM_ID` to pick the record.** Sub-step 10d.19 stopped it being a
fallback and using it here would revive it as one. If you think that is wrong, flag it rather than
deciding it.

---

## 6. What is NOT in this brief

**The eleven code sites and six on-screen messages in `IntelliBooks-Desktop-v3.html` that carry the
word `Clients`.** That is piece four and the consultant session owns that file. **Do not touch it.**

**A firm level in the path.** Two firms sharing one practice root is constraint 43 of the cloud
document and it is local multi-firm, which is not being built. Out of scope.

**Anything about the folder grant at 10e.15.** That is a browser permission and it is local only.

---

## 7. One warning about the window this opens

**Between this change landing and piece four landing, the two products agree only by coincidence.**
The pipeline will read `C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\Clients` from the
firm record while IntelliBooks still uses its own literal `Clients` under the practice root. **Those
resolve to the same folder today because Paul's stored value happens to match.**

**So say this in your report in one line, for Paul**: until piece four lands, changing
`client_top_folder` on the Firm Settings page would send the pipeline and IntelliBooks to two
different folders. He should not change it in the meantime.

---

## 8. Evidence expected

The standard is `CLAUDE.md`'s and it is not negotiable here.

- **Red before green**, with the failing output quoted. Where a test cannot come first, mutate from a
  pristine copy and show which tests catch each mutation and that no others do.
- **Do not import `config.py` from a Linux sandbox.** Amendment 245 makes it raise there, and the
  fourth trap in `CLAUDE.md` records what it built the last two times.
- **Enumerate before asserting a count.** Print the search whole. `.history\` is gitignored VS Code
  local history and must be excluded from any repository-wide search: it turned one enumeration from
  205 lines into 1,133.
- **Do not cite a line number in `config.py` or `app.py`.** Amendment 247. Name the constant or the
  function.
- **Quote the suite figures before and after**, as passes and subtests separately, from the last line
  of `pytest -q`. It stood at **579 passed, 358 subtests** after the SMTP change of this morning.
- **Flag, do not fix.** Anything wrong that this brief did not ask about gets reported. If it is small
  and obviously right, say so and offer it.
- **Disclose your own mistakes, including ones you caught and corrected.**
- **Commit after each separable change, and commit with an explicit path list.** `git mv` stages its
  own moves, which is how this morning's session swallowed two changes into one commit.

---

## 9. The report

**Write it to `C:\LastingImpact\receipt_capture\2026-09-07_REPORT_claude_code_client_top_folder.md`
and commit it.** A report with no path makes Paul the copy typist, and the consultant session cannot
see your chat.

**What it has to carry, beyond what you did:**

1. **The route you took on section 4** and why, including what you changed in the test support and
   what its docstring now says.
2. **Your own enumeration of `CLIENTS_ROOT` and of the literal `"Clients"`**, including `tests\`,
   printed whole. The consultant session's count excluded `tests\` and said so.
3. **Whether the change stayed inside `config.py`**, and if it did not, what you touched and why you
   did not stop.
4. **The mutations and which tests caught each.**
5. **Anything in this brief that was wrong.** Two things in it rest on files the consultant session
   read today and one rests on a document rather than on code: say which, if any, did not survive
   contact.
6. **The one line for Paul from section 7.**

**This brief is spent on delivery of that report and goes into `archive\` with `git mv`.**
