# Claude Code report, 2026-09-14: the unresolved-client test, and the push

Paul's two decisions of 2026-09-14, both yes: add the test for the recovery sweep's
unresolved-client branch, and push `feat/console-phase0`.

Session ran 09:43 to 09:53 BST, times read from the machine clock each time.

**Both done. One commit, `92556cd`. The branch is pushed and in sync with `origin`.**

---

## 1. The suite

| Point | Result |
| --- | --- |
| Baseline at HEAD, before the change | **1392 passed, 1 skipped, 967 subtests** |
| After the change | **1395 passed, 1 skipped, 967 subtests** |

Three tests, no subtests. The baseline was measured at the start of this session rather than carried
from the last report.

---

## 2. The test

**Built.** Three tests in `AnUnresolvedClientIsNotPublishedTest`, added to
`tests/test_recovery_sweep_fallback.py`, which already had the fixture.

### What it covers

The guard above the four fallbacks in `_publish_unpublished_receipts()`:

```python
client_folder_name = _client_folder_name(receipt["client_id"])
if not client_folder_name:
    logger.warning(...)
    continue
```

**Three ways in, read off `_client_folder_name()` rather than guessed:** the client is absent from the
registry, its record carries a blank `client_folder_name`, or the id is the reserved `UNKNOWN`. Each
gets its own test rather than a subtest, so a regression that closes one is not masked by the other
two passing.

**Each asserts the whole outcome rather than half of it:** the warning names the receipt and the
missing folder name; nothing is written to the inbox; no `publish_events` row exists for the receipt;
nothing reaches `Clients\` with the firm's trigger set to `publish`; `filed_path` stays NULL; the
receipt keeps its `ok` status; and it is still returned by `get_unpublished_ok_receipts()`.

**That last one is the assertion that makes the branch's behaviour honest rather than lossy.** The
code's own comment says leaving the receipt unfiled "is the honest outcome and it is reported", and
that is only true if the receipt comes back. It does: nothing about it is decided, so nothing about it
is recorded, and a later registry fix picks it up on the next poll.

### This behaviour is different from the fallback routing beside it, and the tests say so

A fallback **publishes** the receipt marked for review, because the document was read and only a value
is missing. An unresolved client **publishes nothing at all**, because 10d.18 says a receipt whose
client cannot be named files nowhere. Putting both in one file risks a later reader flattening them
into one rule, so the new class's docstring states the difference and why.

### Red before green does not apply, so two mutations do

**These assert behaviour that already exists, so they cannot be red first**, and saying "they pass"
would prove nothing. Both mutations were anchored on a string asserted to match exactly once, backed
up first, and diffed rather than described.

**M1, the guard no longer skips:**

```
                 )
-                continue
+                pass  # MUTANT M1: no longer skips
MUTATION drop-continue APPLIED (1 site)
```

```
FAILED  test_a_client_the_registry_does_not_hold_publishes_nothing
FAILED  test_a_record_with_a_blank_folder_name_publishes_nothing
FAILED  test_the_reserved_unknown_id_publishes_nothing
3 failed, 5 passed, 10 subtests passed
```

All three red on the publish assertions, and the file's five existing tests untouched.

**M2, the skip is silent:**

```
                 # leaving it unfiled is the honest outcome and it is reported.
-                logger.warning(
-                    f"receipt {receipt_id} is ok but its client {receipt['client_id']} has no "
-                    "client_folder_name in the registry, so it is not filed into Clients"
-                )
+                pass  # MUTANT M2: skips silently
                 continue
MUTATION drop-warning APPLIED (1 site)
```

```
AssertionError: [] is not true : no warning naming the receipt and the missing folder name; got []
3 failed, 5 passed, 10 subtests passed
```

All three red on the warning assertion. **So both halves of the assertion set are load-bearing**, and
neither mutation is caught by the half meant for the other.

### The gap was real, and this is the measurement that shows it

Running the **whole existing suite** against M1, my own file excluded:

```
1387 passed, 1 skipped, 957 subtests passed
```

**Entirely green.** The guard can be deleted outright and nothing in 1387 tests notices. That is what
the flag claimed and it is now measured rather than asserted.

A detail worth keeping, from M1's captured log: with the guard gone the receipt published, and
`copy_for_published_receipt()` then refused the copy on its own account, logging "receipt r-sweep
published, but client UNKNOWN has no client_folder_name in the registry". **So the client folder has
a second line of defence and the inbox does not.** The publish is the part the guard was solely
protecting, which is why the "nothing written to the inbox" assertion is the one that matters most.

**The revert was verified rather than assumed**: the script asserts the guard is present exactly once
and no mutant string remains, and `git diff --stat` afterwards showed `app.py` absent from the diff.

---

## 3. My own mistakes

**Two, both caught here, and the first is a repeat.**

**I introduced another invalid escape sequence**, `Clients\ ` inside a non-raw assertion message,
while writing the new tests. **This is the second in two sessions.** It surfaced in pytest's warnings
summary this time rather than silently, then was confirmed gone with
`-W error::SyntaxWarning` on the file.

**The cause is the same both times and worth naming:** I write file content through a Python string in
a scratch script, so a backslash passes through two layers of escaping and the count is easy to get
wrong. **The habit that catches it regardless of the cause is to compile the changed file with
`-W error::SyntaxWarning` before running anything else**, since plain `py_compile` exits 0 and the
suite stays green. I did that for the last one only after the fact; this time it is the check that
closed it.

**I left an unused parameter on the new helper.** `_assert_nothing_happened(self, warnings,
sidecar_client)` took a client id it never read, and all three call sites passed one. Removed before
committing. Noting it because I had just deleted a dead local for flag 1 and adding one in the same
hour is exactly the thing that rule exists to stop.

**A third thing, which was correct and worth recording anyway:** the class docstring said the three
cases were "subtested" when I had written them as three separate test methods. Corrected, with the
reason for separate methods stated.

---

## 4. On your correction about the branch count

**You were right and the report said 7 when the branch was 9.** The cause is worth recording because
it is the same one as the subtest baseline in the report before it.

**I arrived at 7 by arithmetic over my own commits** rather than by reading the tool. My closing
message that turn said 9, because that one came from `git status -sb`. So I had the right number in
one place and a derived one in the other, and the derived one is the one that went into the file.

**Arithmetic over my own work cannot see the other two sessions committing to this branch**, and on
this occasion amendment 457's commit landed mid-session. **The rule that fixes it is the project's own,
applied to git state: read it from the thing itself.** For this push I read
`git log --oneline origin/..HEAD` and let it enumerate the eleven commits rather than counting them.

Per your instruction the previous report is left as written.

---

## 5. The push

**Done.** `c302e96..92556cd`, fast-forward, no force, dry run first.

**Eleven commits went up**, enumerated from `git log` rather than counted:

```
92556cd test(recovery): cover the sweep's unresolved-client guard
efcfae7 docs: move the section 16 headline's superseded history to appendix 16A
8c178b0 docs(report): the three flags from the 10aq report, all built
b652998 test(resume): strike the cross-reference to a test that does not exist
32d7797 docs(filing): correct the Review folder's docstring about who reads it
4b10bec refactor(recovery): delete the unused tax_year local from the sweep
dd5e2bf docs: amendment 457, step 10aq BUILT, three flags recorded, amendment 405 corrected
132fa33 docs(report): step 10aq, the recovery sweep's silent fallback
9869a63 fix(recovery): a fallback value sends the receipt to Review, not to the books
f167b2b docs: 13 steps to BUILT, amendments 452-454, headline corrected
1fb1e18 docs: brief for step 10aq, the recovery sweep's silent fallback
```

**Four of those belong to the consultant session rather than to me**: `efcfae7`, `dd5e2bf`, `f167b2b` and
`1fb1e18`. I have read none of them and they went up because they were on the branch, which is what
pushing a branch does. Saying so because a push is an outward-facing act and the list should not read
as though it were all my work.

`git status -sb` after the push reads `## feat/console-phase0...origin/feat/console-phase0` with no
ahead or behind count, so the branch is in sync.

---

## 6. Confidence

**High that the three tests discriminate**, resting on the two mutation runs above rather than on
their passing.

**High that the branch was untested before this**, resting on the whole existing suite running green
against M1.

**High that the push landed**, resting on the ref update line and on `git status -sb` read back.

Nothing here needs a decision from you. The working tree is clean apart from
`PROMPT_claude_code_2026-09-14_delivery_log_writer.md`, which is untracked and is not mine.
