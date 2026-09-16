# Claude Code report, 2026-09-14: the three flags from the 10aq report

Flags 1, 2 and 3 of `2026-09-14_REPORT_claude_code_recovery_sweep_review_fallback.md`, all approved
by Paul on 2026-09-14 and recorded at amendment 457.

Session ran 09:14 to 09:26 BST, times read from the machine clock each time rather than carried
forward.

**All three built, one commit each, on `feat/console-phase0`. Nothing pushed.**

| Flag | Commit | What it is |
| --- | --- | --- |
| 1 | `4b10bec` | the unused `tax_year` local deleted from the sweep |
| 2 | `32d7797` | `file_review()`'s docstring corrected about who reads the Review folder |
| 3 | `b652998` | the stale cross-reference struck in `tests/test_resume_safety.py` |

---

## 1. The suite

| Point | Result |
| --- | --- |
| Baseline at HEAD, before any change | **1392 passed, 1 skipped, 967 subtests** |
| After flag 1 | 1392 passed, 1 skipped, 967 subtests |
| After flag 2 | 1392 passed, 1 skipped, 967 subtests |
| After flag 3 | 1392 passed, 1 skipped, 967 subtests |

Unchanged throughout, which is the expected result: one dead local removed and two comments
corrected. No file was added, so no post-commit re-run was needed on the new-file rule.

**The baseline was measured at the start of this session rather than carried from yesterday's
report**, which is the habit that caught the 957-against-947 confusion in the last one. It came out
the same, 1392 / 967.

---

## 2. Flag 1. The unused `tax_year` local

**Built.** `tax_year = determine_tax_year(invoice_date)` is gone from
`_publish_unpublished_receipts()` in `app.py`.

### Enumerated from the syntax tree rather than grepped

Before:

```
references to the name tax_year in app.py: 3
  line   709  Store         in _publish_unpublished_receipts
  line  1773  Store         in process_once
  line  1790  Load          in process_once

determine_tax_year() call sites: [709, 1773]
```

A `Store` with no matching `Load` inside the sweep, and a genuine `Store`/`Load` pair in
`process_once()`. After:

```
references to the name tax_year in app.py: 2
  line  1777  Store         in process_once
  line  1794  Load          in process_once

determine_tax_year() call sites: [1777]
```

**The import stays live**, `determine_tax_year` keeping one real call site, so nothing else had to
move.

### What replaced the line

A comment, rather than nothing. The tax year that decides the client folder's subfolder is worked out
inside `copy_for_published_receipt()` from the `invoice_date` handed to it a few lines below, so
somebody reading that call could reasonably conclude the sweep owes it a tax year and put the line
back. The comment says it does not.

### MY OWN ERROR IN THE FLAG THAT ASKED FOR THIS

**The flag cited `app.py:753` and the line was at 709.** I checked before deleting: 709 held
`tax_year = determine_tax_year(invoice_date)` and 753 held a comment about `gross_amount` being
passed to the classifier.

This is precisely the fault `CLAUDE.md`'s "do not cite a line number in `config.py`" rule generalises,
and I committed it in a delivered report yesterday. **The rule's own remedy applies: name the function,
because a name does not move.** `2026-09-14_REPORT_claude_code_recovery_sweep_review_fallback.md` is
left as written, being a dated report rather than live text, and this paragraph is the correction.

Confidence: **high**, resting on the two enumerations above and on reading both lines.

---

## 3. Flag 2. The Review folder's docstring

**Built**, and **the flag itself was wrong in a way the work exposed, so this section leads with
that.**

### What the flag claimed, and what is actually true

The flag said the Review folder "now has no reader at all". **That is false.** Enumerating every
`REVIEW_ROOT` reference in the live tree found readers inside this very module:

- **`remove_review_pair()`** in `worker/filing.py` finds a receipt's image and sidecar and deletes
  them when its life in Review ends, on a successful resolve or a discard.
- **`_scan_other_clients_for_receipt()`** iterates every subfolder of `REVIEW_ROOT` to find that pair
  when it is not where it was expected.

So the folder is **the pipeline's own record of what is awaiting a human**, written by
`file_review()` and cleaned up by the resolution service.

**What is true is the narrower claim**, and it is what the docstring now says: **IntelliBooks Desktop
no longer reads it.** Sub-step 10f.15 moved that queue onto the published inbox and step 10f completed
on 2026-09-11. Measured again today rather than taken from yesterday: `scanReview()` appears 10 times
in `IntelliBooks-Desktop-v3.html` and the Review folder path appears **zero** times.

**How I got the flag wrong.** I grepped for `RESOLUTIONS_DIR|REVIEW_DIR|Review` with a filter that
happened to exclude the two call sites, read nothing further, and wrote the consequence. The
enumeration that found them took one command and I ran it only when I came to do the work. **A nought
is a claim about a set**, which is amendment 97's rule, and I asserted one without enumerating the
set.

### What the docstring says now

The superseded sentence is struck rather than deleted, per this project's convention, with three
things beside it: that Desktop stopped reading the folder at 10f.15 and the two halves therefore no
longer have to move together; that the pipeline does still read it, naming both functions, which is
why the write stays; and that **whether the folder should exist at all is a question for Paul rather
than a correction**, left open rather than answered.

### A second mistake of mine, caught by a check I had not been running

**I introduced an invalid escape sequence into that docstring.** Writing `Intellibills\Review` inside
a non-raw docstring makes `\R`, which Python reports as a `SyntaxWarning`.

**Plain `python -m py_compile` exits 0 on it and prints only a warning, and the suite stays green**,
so neither of my usual checks would have caught it. I found it by compiling with
`-W error::SyntaxWarning`, and fixed it by doubling the backslash, which is what the surrounding code
already does.

**Then I checked whether the repository had others**, since a fault my normal checks cannot see is
worth measuring rather than assuming away:

```
files compiled with SyntaxWarning as error: 149
files that failed: 0
```

**All 149 live Python files are clean**, `.history`, `archive`, `Backups`, `.venv` and `__pycache__`
excluded. So mine was the only one and it is gone. No flag arises; recorded because the measurement is
the only thing that makes "it was only mine" a fact rather than a hope.

Confidence: **high** on what reads the folder, resting on the `REVIEW_ROOT` enumeration and on reading
both functions. **High** on Desktop not reading it, resting on two counts taken off the live file
today.

---

## 4. Flag 3. The stale cross-reference

**Built.** The sentence in `tests/test_resume_safety.py` naming
`test_an_unresolved_client_is_not_filed` as "the other half" is struck.

**Swept before striking**, `.history`, `Backups` and `archive` excluded. The name occurs in exactly
three places and **none of them is a test**:

```
2026-07-25_CONSOLE_DESIGN.md:1337      amendment 457, recording this flag
2026-09-14_REPORT_..._review_fallback.md:354   the flag itself
tests/test_resume_safety.py:51         the stale comment now struck
```

**The nearest real test is `test_an_unresolved_client_names_nothing`** in
`tests/test_step10d_pipeline.py:463`. I read it rather than matching on its name: it asserts
`app._client_folder_name("Client_999")` is `None`, which covers **the helper** rather than the
sweep's own branch that reads the helper and skips the receipt. So it is not the missing other half, and
repointing the reference to it would have been wrong. The struck comment says so, so the next reader
does not go looking again.

The three sentences above it are accurate and are kept: they explain why the fixture needs a real
registry entry, which is still true.

### A FLAG ARISING, reported and not built

**Nothing tests the recovery sweep's unresolved-client branch.** The sweep has:

```python
client_folder_name = _client_folder_name(receipt["client_id"])
if not client_folder_name:
    logger.warning(...)
    continue
```

Searched `tests/` for its warning text and for any sweep test setting up an unresolvable client:
nothing. **That is what the missing test was evidently meant to be**, and striking the reference
records the gap rather than closing it.

**The obvious fix, and it adds rather than removes, so it needs your yes:** one test in
`tests/test_recovery_sweep_fallback.py`, which already has the fixture, seeding a receipt whose
`client_id` is absent from `CLIENTS_BY_ID` and asserting the sweep publishes nothing, copies nothing
and logs the warning. Roughly fifteen lines. **I have not written it**, because the branch is
pre-existing behaviour nobody asked me to change and adding coverage is a decision rather than a
correction.

Confidence: **high** that no such test exists, resting on the sweep printed whole above, the
three-hit name sweep, and reading the near-neighbour rather than trusting its name.

---

## 5. What I judged rather than measured

One thing, and it is small.

**Keeping the three accurate sentences in flag 3's comment and striking only the fourth.** You said
delete the stale cross-reference; the sentence before it explains why the fixture needs a real
registry entry and is still true, so deleting the whole comment would have removed a working
explanation along with the broken pointer. If you wanted the lot gone, say so.

Everything else here is measured: the `tax_year` enumeration before and after, the `REVIEW_ROOT`
readers, the two Desktop counts, the three-hit name sweep, the 149-file escape check, and the suite
at four points.

---

## 6. Nothing pushed

Three commits, `4b10bec`, `32d7797` and `b652998`, on `feat/console-phase0`. The branch is now 7
ahead of `origin`, the other four being step 10aq's pair and yesterday's two, all already reported.

**Recommended: push.** All three are comment-and-dead-code changes with the suite unchanged at every
point, and each reverts on its own.

**One thing wants a yes:** the flag arising in section 4, a test for the sweep's unresolved-client
branch. Nothing else here needs anything from you.
