# Claude Code brief, 2026-09-20: the test fixture's client folder

Written by the consultant session, 2026-09-20, 10:24 BST, read off the clock in this reply. Paul's
decision of 2026-09-20, taken on your own flag in the archive-root work: he does not want it left
open. Step 10bl of `2026-07-25_BUILD_STATUS.md`, added by amendment 524.

**Report to `2026-09-20_REPORT_claude_code_clients_root.md` in the repository root.**

**Commit the archive-root and step 10am work first, as you proposed it. This is a separate commit
after it.** Build it, propose the commit, and wait for a yes.

---

## Three rules about this brief

**1. `2026-07-25_BUILD_STATUS.md` is not yours to edit.** You report; the consultant session marks
the step.

**2. `2026-07-25_CONSOLE_DESIGN.md` is not yours either.**

**3. Check every line number and every claim below against the files.** Where yours disagrees, say
so in the report and work from yours.

---

## What is wrong

`tests\resolution_fixtures.py` pins `config.CLIENTS_ROOT = config.PRACTICE_ROOT / "Clients"`.

**Production has not composed it that way since 2026-09-07.** `config.py` line 862 reads
`CLIENTS_ROOT = _client_top_folder(FIRMS)`, off the firm record's `client_top_folder`, and the
comment at line 144 records why the literal was removed: the client top folder is the firm's own
filing structure, it need not sit under the practice root, and a firm whose folder is named anything
else needed a code change while the literal was there.

So the fixture restates a rule production dropped. It is the last restated derivation in that file
after the archive-root change, and it is the same defect class: the tests work the location out one
way and the live system works it out another. Nothing is wrong today only because Paul's
`firms.json` happens to name a folder called `Clients`.

## The route you costed, and a second one you did not

Your flag costed **rebasing** the path, which renames the temp client root from `Clients` to
`Client Folders` and breaks 16 tests across three files that hardcode the name, reaching 40 files.
That route is not what this step asks for.

**The route to try first: the fixture builds a firm record and derives the path the way production
does.** `_client_top_folder(FIRMS)` takes the value off the record. The fixture can set that record's
`client_top_folder` to its own temp folder and then call the same function, so:

- the folder keeps the name the tests already expect, and the 16 tests do not move;
- the restated rule is gone;
- the tests exercise the real derivation instead of a copy of the abandoned one.

**Establish this before building it, because the consultant session has not proved it.** The
fixture does not pin `config.FIRMS` today: the name appears in that file only in a comment. Find out
what `config.FIRMS` actually holds during a test run, given `FIRMS_JSON` is redirected into temp and
there may be no file there, and whether any test depends on it being empty or on
`_client_top_folder()` raising. **If pinning it changes behaviour a test relies on, stop and report
rather than working around it.**

If that route does not hold, say why and propose the next one rather than falling back to the
rebasing route without asking.

## What it has to do

- `tests\resolution_fixtures.py` no longer states where the client folder is. It comes from the same
  function production uses.
- `PINNED_BY_HAND` shrinks by one, or says in its own words why `CLIENTS_ROOT` is still there.
- The guard in `tests\test_logs_isolation.py` that reads those tuples still holds.
- Prove it discriminates: put the composed literal back and show a test going red. **If nothing goes
  red, say so** and propose the check that would, because a fix nothing can catch is where this one
  came from.

## What not to do

- **No production code changes.** `config.py` is production.
- **No real OpenAI call.**
- Nothing outside `C:\LastingImpact\receipt_capture`.
- Check `git status` before and after any run that edits files.

## How to report

- What `config.FIRMS` holds in a test run, and how you established it.
- Every test that moved, with the reason, one by one.
- The discrimination result, red then green.
- Suite totals before and after.
- Disclose your own mistakes, including ones you caught and corrected.
