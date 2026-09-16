# Claude Code brief, 2026-09-16: step 10aj, a statement arrives and is filed

Written by the consultant session, 2026-09-16, 15:05 BST. Step 10aj of
`2026-07-25_BUILD_STATUS.md`, amendment 389 of `2026-07-25_CONSOLE_DESIGN.md`, Paul's decision of
2026-09-13 closing outstanding item 74.

**Report to `2026-09-16_REPORT_claude_code_statement_end_to_end.md` in the repository root.**

**One commit. Build it, propose the commit, and wait for a yes.**

---

## Two rules about this brief

**1. `2026-07-25_BUILD_STATUS.md` is not yours to edit. Paul's instruction, 2026-09-16.** Do not mark
this step built and do not touch that file. You report; the consultant session verifies against the
code on Paul's machine and marks the step.

**2. Everything this brief names has been read this session**, from the syntax tree rather than by
grepping, per `CLAUDE.md`'s rule of 2026-09-08. The call graph below is enumerated, not sampled. If a
name here does not match what you find, that is a finding about this brief.

---

## What is decided

From amendment 389, quoted:

> `file_statement()` is live code, already the subject of real design decisions since 10d.55 including
> amendments 297 and 316, contrary to the item's claim that this area is untouched. **What is
> genuinely unconfirmed is the intake side.** `scan_inbox()` treats an item as a statement purely on a
> `"type": "statement"` key in its sidecar, independent of which of the four sources produced it.
> **Decided: build and run an end-to-end test**, a crafted statement sidecar dropped into the inbox,
> confirming `scan_inbox()` and `file_statement()` carry it through to a filed document and a
> `statements` row.

Its Why column, which is the part that says what this is really for:

> The output side, filing, has had real attention and was wrongly called frozen and untouched by
> nobody. The input side, whether anything ever triggers it, had genuinely had none.

**So the test is about the seam, not about `file_statement()`.** `file_statement()` already has
attention. What has never been shown is that a sidecar on disk reaches it.

## The producer exists and is undeployed

Step 10aj's paragraph used to say the only plausible producer was the Uber parser and that the link
was unconfirmed. **That was corrected on 2026-09-16.** Step 10ak records, from amendment 470, that
`netlify\functions\upload.js:52` writes `type` as `"statement"` or `"receipt"` into the sidecar. That
file is the phone app rather than this repository. **What has never happened is a deployment.**

This changes nothing about what you build. It means the shape you craft should match what that file
writes, so read it before you invent a sidecar. **It is not in this repository**: it is under
`Intellibills\PhoneApp\` in the practice root. If you cannot reach it, say so and craft the sidecar
from `scan_inbox()`'s own reader instead, and say in the report which you did.

## The path, enumerated from the syntax tree

Read in the files on Paul's machine this session:

| Step | Where |
|---|---|
| `scan_inbox()` is imported | `app.py:32` |
| `file_statement()` is imported | `app.py:41` |
| `scan_inbox()` is called, once | `app.py:1505` |
| The statement branch runs | `app.py` around 1781 to 1812 |
| `file_statement()` is called, once | `app.py:1796` |

Inside `scan_inbox()`, `worker\intake\folder_reader.py:128`, `is_statement` is set from
`sidecar.get("type") == "statement"`, and lines 132 to 134 take `platform` and `week_ending` from
beside it.

Inside the branch, in order: a `statement_id`, the tax year from `week_ending`, a copy into the
document store, `file_statement()` for the client folder copy, then `repo.save_statement()` for the
row. The `statements` table is declared at `worker\database\schema.py:134`.

## What to build

**One test that starts with a file pair on disk and ends with a row in the database.**

It writes a document and a sidecar into the inbox, runs the intake, and then asserts, on the far
side:

1. **`scan_inbox()` classified it as a statement** and carried `platform` and `week_ending` through.
2. **A copy exists in the document store.**
3. **A copy exists in the client folder**, under the folder, tax year and platform that
   `file_statement()` composes, with the name it composes.
4. **A row exists in `statements`**, carrying the ids, the platform, the week ending, the source, the
   hash, and both paths.

**The tax year is the assertion most worth getting right.** `file_statement()`'s own docstring records
that a statement files by its end date and only by its end date. **So craft a week ending that
straddles 5 April and assert it lands in the year the end date says**, not the year the period
started in. A test that only uses a mid-year date proves nothing about the rule that was actually
decided.

**Two negative cases, because this is a seam and a seam fails by not firing:**

- **A sidecar with no `type` key** goes down the receipt path, not the statement path.
- **A sidecar with `type` set to something else** does the same.

Without these the test cannot tell a working classifier from one that says statement to everything.

## What must not change

**This is a test. No production behaviour moves.** If the test cannot be made to pass without changing
`scan_inbox()`, `file_statement()`, `app.py` or the schema, **stop and report that**. A change needed
to make this test pass is a defect this step has just found, and it is Paul's to decide, not yours to
fix inside a test brief.

## Evidence

The standard in `CLAUDE.md` applies in full. Three parts this change makes specific:

- **Red before green**, with the failing output quoted. For a test of existing behaviour, the red is a
  mutation: break the classifier and show the test catches it.
- **Mutations.** Anchor on something unique, assert the anchor matches exactly once, print the unified
  diff beside the result. At minimum: make `is_statement` always false, make it always true, and
  change the tax year to come from the period start. Show which tests catch each and that no others
  do.
- **Run the suite again after the commit**, because this adds a file and the two `git ls-files` source
  guards cannot see it until it is tracked. Treat the second run as the one that counts.

## What to report

Everything the standard asks, plus these by name:

1. Whether you could read `netlify\functions\upload.js`, and if so whether the sidecar shape you
   crafted matches what it writes, field for field.
2. The straddling-5-April case: the week ending you used, the tax year it landed in, and the year it
   would have landed in under the other rule.
3. Anything you had to change in production code to make the test pass, or a plain statement that you
   changed none.

**Flag, do not fix.** `file_review()` is called at `app.py:1769`, `:1777` and `:1919` and at
`worker\extraction_pipeline.py:483`, four sites against `file_statement()`'s one. If anything about
that asymmetry looks wrong while you are in there, say so and stop.

## One disclosure about this brief

Writing it, I first searched for callers across the Python files I had staged and concluded there was
no production caller for either function. **`app.py` was not in that set.** The call graph above comes
from a syntax-tree walk over the 11 files I then staged, and the file list was printed rather than
assumed. The wrong conclusion never reached the brief, and it is recorded here because it is the
enumerate-the-set rule broken and caught inside one turn.
