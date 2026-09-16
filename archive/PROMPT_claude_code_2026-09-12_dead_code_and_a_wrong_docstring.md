# Claude Code brief, 2026-09-12: three pieces of dead code and one wrong module docstring

Items 114, 115, 116 and 118 of `2026-08-20_LIST_outstanding_items_and_decisions.md`, section 10.
All four are deletions or a comment correction. No behaviour changes.

**Read this whole brief before starting.** Three of the four items are stale in a detail that
matters, and each is called out below. **The items were verified on 2026-08-21 and re-verified by
the consultant session on 2026-09-12 against the files themselves.** Where this brief and the
items list disagree, this brief is the later reading, and the items list is corrected when these
land rather than before.

**Report to `2026-09-12_REPORT_claude_code_dead_code_and_docstring.md` in the repository root.**
A report with no path leaves Paul copy-typing, and he is the only channel between the sessions.

**Four commits, one per item**, so any one can be reverted without the others.

---

## Item 114. Delete `write_review_file()`

**Where.** `worker\filing.py`, the `def` at line 362 as at 2026-09-12.

**The item says nothing in the repository calls it. That is no longer true, and it is the one
thing in this brief that changes the work.** There is exactly one caller, and it is a test:
`tests\test_london_surfaces.py`, in `test_the_review_sidecar_keeps_utc`, which calls
`filing.write_review_file(...)` and asserts the `timestamp` it writes is stored as UTC.

**So the deletion is two things, not one.** The function goes, and that test method goes with it.
The test exists only to test this function; it asserts nothing about any live path.

**Why the function is dead rather than merely uncalled.** `file_review()` at `worker\filing.py:145`
is the live writer. It names its sidecar `dest_file.suffix + REVIEW_SIDECAR_SUFFIX`, giving
`image0.jpeg.review.json`, and `REVIEW_SIDECAR_SUFFIX` is read back by
`_find_review_sidecar()`, `_delete_review_pair()` and the scan at `worker\filing.py:247`.
`write_review_file()` names its own output `{stem}.review` plus `.json`, giving
`image0.review.json`. **Nothing reads that second shape.** That is what the 2026-07-29 handover
meant by "a second writer whose output cannot be worked".

**What to do.**

1. Delete `write_review_file()` from `worker\filing.py`.
2. Delete `test_the_review_sidecar_keeps_utc` from `tests\test_london_surfaces.py`.
3. Leave `file_review()`, `REVIEW_SIDECAR_SUFFIX`, `_find_review_sidecar()`,
   `_delete_review_pair()` and `remove_review_pair()` exactly as they are.

**Prove it before you delete, not after.** Enumerate callers from the syntax tree rather than by
grepping, per `CLAUDE.md`: a grep returns the name from docstrings and from superseded prose, and
this repository keeps superseded prose beside every correction. **Exclude `.history\`**, which is
VS Code's local history and holds a dated copy of every file ever edited. Print the enumeration
whole. If it returns any caller other than the one test, **stop and report rather than deleting.**

---

## Item 115. Delete `regenerate_codes()`

**Where.** `regenerate_vendor_codes.py`, the `def` at line 70 as at 2026-09-12. The item says
line 68; it has drifted by two.

**Confirmed dead.** No call site anywhere in the 148 Python files outside `.history\`, `.git\`,
`__pycache__\`, `archive\` and `.venv\`, enumerated from the syntax tree on 2026-09-12.

**One correction to the item, and it is worth a sentence in your report.** The item says the
`if __name__ == "__main__":` block "re-implements the same logic inline". It re-implements most of
it and differs in one respect: **the function writes back over `csv_path` in place, and the
`__main__` block writes to a separate `output_path`.** So deleting the function removes the only
in-place variant. It has no caller and no runner, so it still goes, but say so rather than
reporting the two as identical.

**What to do.** Delete the function. Change nothing in the `__main__` block. Change no other file.

---

## Item 116. Delete three dead names in `worker\intake\folder_reader.py`

All three are left over from a filename-prefix design that amendment 112 of
`2026-07-25_CONSOLE_DESIGN.md` replaced. `scan_inbox()` tells a statement from a receipt by the
sidecar's `type` key, which is the decision that amendment recorded.

| Name | Where, as at 2026-09-12 | Item said |
|---|---|---|
| `INTAKE_PATTERN = "rcpt_"` | line 13 | line 13 |
| `STATEMENT_PREFIX = "stmt_"` | line 14 | line 14 |
| `IntakeRecord.internal_path` | the constructor parameter at line 41, and the assignment `self.internal_path = internal_path` at line 55 | lines 32 and 46 |

`internal_path`'s two sites have moved. It is a keyword parameter with a default of `None` on
`IntakeRecord.__init__`, so removing it is source-compatible with every construction site that
does not pass it. **Check that no construction site passes it before removing it**, from the
syntax tree, and print what you find.

**What to do.** Delete the two constants and the parameter with its assignment. Leave
`SIDE_CAR_EXT`, `EMAIL_SOURCE`, `PHONE_SOURCE`, `DESKTOP_SOURCE`, `OTHER_SOURCE` and
`INTAKE_SOURCES` alone: all six are live.

---

## Item 118. Correct the module docstring of `worker\extraction\postprocess.py`

**The defect is real and it is larger than the item says.**

The module docstring, at lines 21 to 23 as at 2026-09-12, reads:

> The broad `try/except Exception: pass` blocks are kept exactly as they were and
> are load-bearing: a numeric coercion failure must leave the values untouched
> rather than fail the extraction.

**There is no `except Exception: pass` anywhere in the file.** Enumerated from the syntax tree on
2026-09-12, the file has **six** `except Exception` handlers and not one of them is a `pass`:

| Handler at line | In | What its body does |
|---|---|---|
| 56 | `parse_ambiguous_date()` | returns |
| 62 | `parse_ambiguous_date()` | returns |
| 105 | `parse_ambiguous_date()` | returns |
| 184 | `establish_gross_from_vat()` | `logger.warning(..., exc_info=True)` |
| 254 | `resolve_invoice_date()` | `logger.warning(..., exc_info=True)` |
| 261 | `resolve_invoice_date()` | `logger.warning(..., exc_info=True)` |

**Two corrections to the item, both of which would have sent you to the wrong place.** It names
`apply_vat_inclusive_swap()` at lines 129 to 134. **That function no longer exists.** It was
renamed `establish_gross_from_vat()`, and the only surviving mention of the old name is inside a
docstring at line 113 that explains the rename. And it describes two handlers where there are six.

**What to do.** Rewrite those three docstring lines to say what the file does: broad
`except Exception` handlers are kept deliberately, because a coercion or parse failure must leave
the values untouched rather than fail the extraction, and **none of them is silent** - the three
in `parse_ambiguous_date()` return and the other three log at warning with `exc_info=True`. Keep
the superseded wording struck through beside it, per this project's convention, rather than
overwriting it.

**Change no code in this item.** Docstring only. The file's own inline comment two lines below
already reads "Logged rather than swallowed" and is correct; leave it.

---

## Evidence expected in the report

Per `CLAUDE.md`'s standard of evidence, and none of it is optional:

1. **The caller enumeration for each of items 114, 115 and 116, printed whole**, from the syntax
   tree rather than from a grep, with `.history\` excluded. A claim about a set is not verified by
   verifying its members.
2. **The suite before and after each commit.** Pass counts, not "green".
3. **Anything you find that this brief gets wrong.** Three of the four items were stale and this
   brief corrects them; assume it has its own. Flag, do not fix.
4. **Your own mistakes, including ones you caught and corrected.**
5. **A confidence level per item, saying what it rests on.** "High, because I read it back" and
   "high, because it seemed right" are different claims.

**One thing you do not need here.** No file is added by any of these four commits, so the
after-commit suite run that `CLAUDE.md` requires for an added file does not apply. Say so rather
than silently skipping it.

**Do not touch anything else while you are in these files.** Three of the four sit beside live
code that is in the middle of other work.
