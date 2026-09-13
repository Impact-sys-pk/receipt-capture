# Report: three pieces of dead code and one wrong module docstring

**Claude Code, 2026-09-12.** From `PROMPT_claude_code_2026-09-12_dead_code_and_a_wrong_docstring.md`,
md5 `dad0b95fe0adcf6e5b18386b53056f72`. No hash was supplied with the instruction; this is the one I
read. Items 114, 115, 116 and 118 of `2026-08-20_LIST_outstanding_items_and_decisions.md`, section 10.

**Four commits on `feat/console-phase0`, one per item, none pushed.**

| Item | Commit | What |
|---|---|---|
| 114 | **`8a30daa`** | `write_review_file()` deleted, with its one caller |
| 115 | **`45156f2`** | `regenerate_codes()` deleted |
| 116 | **`441dcab`** | Three dead names in `folder_reader.py` deleted. **See section 6: this commit also contains two files the brief forbids.** |
| 118 | **`c80fa43`** | The module docstring of `worker\extraction\postprocess.py` corrected |

**The suite, at every step.** 1384 before anything. 1383 after item 114, which is the one deleted
test and nothing else. 1383 after 115, 116 and 118, each unchanged. 1 skipped and 946 subtests
throughout.

**No file is added by any of the four commits**, so the after-commit suite run `CLAUDE.md` requires
for an added file does not apply. Confirmed rather than assumed: `git show --name-status` on all four
returns `M` for every path and no `A`. Said here rather than silently skipped.

---

## 1. Section 6 first, because it is a breach and not a detail

**Commit `441dcab`, item 116, contains two files the brief forbids committing.** The full account is
in section 6. It was not repaired, and the reason is there too.

---

## 2. Item 114: `write_review_file()`

### The enumeration, printed whole, from the syntax tree

```
swept 148 Python files, excluding ['.git', '.history', '.venv', '__pycache__', 'archive']

CALLS to write_review_file(): 1
   tests\test_london_surfaces.py:317   in StorageStillWritesUtcTest::test_the_review_sidecar_keeps_utc
   defined at: ['worker\filing.py:362']
```

**The brief is right and the item is stale.** The item says nothing calls it; exactly one thing does,
and it is the test the brief names. The `def` was at line 362, as the brief says.

**`.history\` excluded**, which is `CLAUDE.md`'s sixth trap: it is VS Code's local history and holds
a dated copy of every file ever edited, so an enumeration including it reports names that no longer
exist anywhere live.

### Why it was dead rather than merely uncalled, checked

`file_review()` names its sidecar `dest_file.suffix + REVIEW_SIDECAR_SUFFIX`, giving
`image0.jpeg.review.json`. `write_review_file()` named its own `{stem}.review` plus `.json`, giving
`image0.review.json`. **Nothing read the second shape**, so anything it wrote could never be found,
paired or removed by `_find_review_sidecar()`, `_delete_review_pair()` or `remove_review_pair()`.

### The part of this that is mine

**I wrote that caller myself**, on 2026-09-11, during the London time work.
`test_the_review_sidecar_keeps_utc` asserted the timestamp `write_review_file()` writes is stored in
UTC. **I did not notice the function was dead**, so I wrote a test of dead code and reported it in
that day's report as coverage of "the review sidecar". It was not.

**Deleting it loses no coverage of the live path**, and that is checked rather than assumed.
`reviewed_at`, which `file_review()` writes, appears in exactly two places in the repository outside
`.history\`, `.venv\` and `archive\`: `worker\filing.py:166` where it is written, and a name in a
list in `tests\test_london_surfaces.py`. **It is still held to UTC by
`tests\test_london_time.py::StorageIsStillUtcTest`**, which asserts every `datetime.now()` in the
production tree passes `timezone.utc`, and that guard covers `filing.py:166`. See flag 2.

**Left exactly as they are**, per the brief: `file_review()`, `REVIEW_SIDECAR_SUFFIX`,
`_find_review_sidecar()`, `_delete_review_pair()` and `remove_review_pair()`.

**After: 0 callers and 0 definitions**, re-run.

---

## 3. Item 115: `regenerate_codes()`

```
CALLS to regenerate_codes(): 0
   defined at: ['regenerate_vendor_codes.py:70']
```

**Line 70, not the item's 68**, as the brief says.

### The brief's correction, confirmed and worth the sentence it asked for

The item says the `if __name__ == "__main__":` block "re-implements the same logic inline". **It
re-implements most of it and differs in one respect**, read off both:

- **The function wrote back over `csv_path` IN PLACE**: `open(csv_path, 'w', ...)`.
- **The `__main__` block reads `input_path` and writes a separate `output_path`**,
  `categorisations_client_vendors_cleaned.csv` to
  `categorisations_client_vendors_regenerated.csv`.

**So deleting the function removes the only in-place variant.** On a file of learned vendor mappings
that is the variant worth losing: it had no caller, no runner and no backup step, so anything that
ever reached it would have overwritten the input with no way back.

The `__main__` block is unchanged. `extract_vendor_key()` and `normalise_description()` stay, and
every import in the file is still used, checked from the tree after the deletion.

---

## 4. Item 116: three dead names in `worker\intake\folder_reader.py`

### Before

```
INTAKE_PATTERN:
   imported at:            nowhere
   bound / parameter at:   ['worker\intake\folder_reader.py:13']
   READ at:                nowhere
   PASSED as a keyword at: nowhere

STATEMENT_PREFIX:
   imported at:            nowhere
   bound / parameter at:   ['worker\intake\folder_reader.py:14']
   READ at:                nowhere
   PASSED as a keyword at: nowhere

internal_path:
   imported at:            nowhere
   bound / parameter at:   ['worker\intake\folder_reader.py:42 (parameter)']
   READ at:                ['worker\intake\folder_reader.py:55']
   PASSED as a keyword at: nowhere
```

**The brief asked me to check no construction site passes `internal_path` before removing it. None
does**, and a second sweep for attribute references found exactly one in the repository:

```
1 attribute reference(s):
    worker\intake\folder_reader.py:55  ctx=Store  self.internal_path
```

**A Store and nothing else. Nothing ever read `record.internal_path`.** Removing a keyword parameter
with a default is source-compatible with every construction site, and none passed it.

### One line number the brief gets wrong

**The brief says the constructor parameter is at line 41. It was at line 42.** Line 41 is
`statement_metadata: dict[str, Any] | None,`. The assignment was at 55, as the brief says. The item's
own figures, 32 and 46, were further out, which the brief already corrects.

**After: all three report `nowhere` on every axis.** And all six names the brief said to leave alone
were checked present afterwards: `SIDE_CAR_EXT`, `EMAIL_SOURCE`, `PHONE_SOURCE`, `DESKTOP_SOURCE`,
`OTHER_SOURCE`, `INTAKE_SOURCES`.

---

## 5. Item 118: the module docstring

### Every claim in the brief's table, confirmed from the tree

```
6 except handler(s):
  line   56  in parse_ambiguous_date        except Exception  body=['Return']  -> return None
  line   62  in parse_ambiguous_date        except Exception  body=['Return']  -> return None
  line  105  in parse_ambiguous_date        except Exception  body=['Return']  -> return None
  line  184  in establish_gross_from_vat    except Exception  body=['Expr']    -> logger.warning(...)
  line  254  in resolve_invoice_date        except Exception  body=['Expr']    -> logger.warning(...)
  line  261  in resolve_invoice_date        except Exception  body=['Expr']    -> logger.warning(...)

handlers whose body is exactly `pass`: 0
handlers catching `Exception`: 6
```

**All three logging handlers pass `exc_info=True`**, checked individually. **There is no
`except Exception: pass` anywhere in the file**, exactly as the brief says.

**The brief's two corrections to the item, both confirmed.** `apply_vat_inclusive_swap()` is not
defined in the file; the functions are `establish_gross_from_vat`, `parse_ambiguous_date` and
`resolve_invoice_date`. The only surviving mention of the old name is at line 113, inside a docstring
explaining the rename. And the item describes two handlers where there are six.

### What the docstring says now

The superseded wording is struck rather than overwritten, per this project's convention. What
replaces it keeps the half that was right, that the broad handlers are deliberate because a coercion
or parse failure must leave the values untouched rather than fail the extraction, and adds the half
that was missing: **none of them is silent.** The three in `parse_ambiguous_date()` return so the
caller decides; the other three log at warning with `exc_info=True`.

**No code changed, and that is proved rather than asserted.** The syntax trees before and after are
identical once the module docstring is removed from both, and the docstring itself differs:

```
trees identical once the MODULE DOCSTRING is removed from both: True
the module docstring itself changed: True
bytes: 12416 -> 13523
```

That is a stronger check than reading the diff, because `ast.dump()` KEEPS docstrings: comparing the
trees whole would have said "changed" and told me nothing. Removing the one node that was meant to
change and comparing the rest is what makes it a check.

The inline comment reading "Logged rather than swallowed" is untouched, as the brief said.

---

## 6. The breach, and why it was not repaired

**Commit `441dcab`, item 116, contains two files the brief forbids committing:**

```
M  2026-07-25_CONSOLE_DESIGN.md                       (amendments 357 and 358)
M  2026-08-20_LIST_outstanding_items_and_decisions.md
M  worker/intake/folder_reader.py                     (mine, and correct)
```

### How it happened, and it is a flaw in my technique

**I was using `git add <my paths>` and then a bare `git commit`. That commits the whole index, not
what I added.** It held for four commits today only because I verified the index was empty before
each one. Between my check after item 115 and this commit, those two files were staged, and my
`git commit` took them.

**The correct technique is `git commit -- <paths>`**, which commits only the named paths whatever
else is in the index. That is the property wanted, and it is what item 118 was committed with. **I
was naming my paths to the wrong command**, which is not the same thing as naming them.

### One correction to my own account, and the attribution matters

**I first reported that the consultant session staged those files. That is wrong.** It has no git
write access and runs git read-only. **Paul staged them**, by running a `git add` line the consultant
session gave him without the `git commit` under it.

**So the hazard is not another session writing to the index.** It is **a staged-and-uncommitted
window between two pastes by a person**, and it will recur. The consultant session is now issuing
`git add` and `git commit` as one line. Recorded because what I guard against depends on which of the
two it is, and I had it wrong.

### Why nothing was repaired

**I proposed `git reset --soft HEAD~1` and asked before running it. I did not run it, and it is as
well.** By the time the answer came, the tip had moved: `d5a9865`, the consultant session's
amendments 362 to 364, was committed at 20:26. **`441dcab` was no longer `HEAD~1`**, so that reset
would have rewound somebody else's commit and left mine untouched.

**Nothing is lost.** `441dcab` holds correct file content in the wrong commit, nothing is pushed, and
the later state of both documents is in `d5a9865`. Paul's instruction: leave the history alone.

**The one thing I got right about it was the risk**, which I flagged when proposing the fix: that the
window would close if anything else committed. It closed.

---

## 7. Flags. Nothing here was fixed

**Flag 1. `IntakeRecord` now has eleven positional parameters and no `internal_path`**, and the
construction sites pass them positionally. That is not a defect and nothing about it changed today;
removing a trailing keyword parameter cannot break a positional call. **Obvious fix: none proposed.**
Named only so nobody reads this deletion as having touched the calling convention. It did not.

**Flag 2. `file_review()`'s `reviewed_at` has no behavioural test**, only the source guard over every
`datetime.now()`. That was true before today and item 114 did not change it: the test I deleted
covered the dead writer, not this one. **Obvious fix, and it needs no decision: add the equivalent of
the deleted test against `file_review()`**, which writes a real review pair and asserts `reviewed_at`
ends `+00:00`. It is about eight lines in `tests/test_london_surfaces.py`. **Not taken**, because the
brief says in terms not to touch anything else while in these files, and the guard means nothing is
currently unprotected. Say the word and I will do it.

**Flag 3. The brief's line number for `internal_path`'s parameter is 41 and it was 42.** One line.
**Obvious fix: none in the code.** It is recorded because the brief invited me to assume it has its
own staleness, and that is the only instance I found: every other line number, count and claim in it
was exact.

---

## 8. My own mistakes

- **The breach in section 6 is the large one**, and the technique behind it had been wrong all day
  and all of yesterday. It only failed once because the index happened to be empty the other times.
- **I misattributed the staging to the consultant session** when reporting it, and had to be
  corrected. It cannot write to git. The guess was plausible and I stated it as fact rather than as a
  guess, which is the thing to avoid: I had not checked who could stage a file.
- **I wrote `test_the_review_sidecar_keeps_utc` on 2026-09-11 against a function that was already
  dead**, and reported it as coverage of the review sidecar in that day's report. Item 114 is partly
  cleaning up after myself.

---

## 9. Confidence, per item

**Item 114: high.** It rests on a syntax-tree enumeration over 148 files run before the deletion and
again after, on reading both filename conventions and the three readers of the live one, and on the
suite moving by exactly one test, which is the one deleted. Not on the item, which was stale.

**Item 115: high.** Nought call sites from the tree, and I read both the function and the `__main__`
block to establish the in-place difference rather than taking the brief's word for it.

**Item 116: high.** Three names, each checked on four axes, before and after, plus a separate sweep
for attribute references that found one Store and no reads. The six names to be left alone were
checked present afterwards.

**Item 118: high, and it is the strongest of the four**, because the claim is that no code changed
and that is proved by tree comparison rather than by inspection. The enumeration of six handlers
matches the brief's table line for line.

**Lower, and the proposition is narrow: that these four deletions leave nothing that wanted them.**
What I verified is that nothing in the 148 Python files references any of them. **What I cannot
verify is whether anything outside this repository does**, and one thing plausibly might: a script
Paul runs by hand. `regenerate_vendor_codes.py` is that kind of file, and its `__main__` block
survives, so the route Paul would actually use is intact. **Nothing outside the repository was
searched.**

**Not verified: anything on the live system.** Nothing was run against the practice root or the live
database, and the pipeline was not started. All four changes are deletions of unreachable code and a
comment.
