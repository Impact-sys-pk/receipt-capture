# Report: a deleted function is checked by definition, and the harness states its expected outcome

**Written 2026-09-08, 14:01 BST (13:01 UTC), by the implementation session in Claude Code.**
**Branch `feat/console-phase0`.**
**Brief: `PROMPT_claude_code_2026-09-08_definition_guards_and_harness_outcome.md`.**

**Both done, and a third thing came out of doing them. Three commits, none pushed.** `ea04cd0` the
harness argument, `ef3cb7b` a harness defect the work exposed, `3b13708` the guards. **No pipeline
behaviour changed**: `app.py`, `config.py` and `worker\` are untouched.

**The scope widened once I looked.** The brief expected one guard, one file over. **There were six
assertions in five files.**

---

## 1. The suite

| When | Result |
|---|---|
| Before, the committed tree at `b85eb8d` | **713 passed, 522 subtests** |
| After all three, at `3b13708` | **725 passed, 527 subtests** |

**Both measured, at 13:16 and 13:58 BST.** Twelve tests and five subtests added, all of them guards
over the guards: seven for the harness's `expect`, four for the CRLF defect, and one asserting that a
tombstone comment is not a definition.

---

## 2. Every guard asserting something about a production file's source

**Scope is the brief's, widened by Paul: `app.py`, `config.py` and everything under `worker\`.**
Found by parsing each test module, and the enclosing function taken as the **smallest** one
containing the line, because `ast.walk` reports a node against every enclosing scope, which counted
one call site eleven times yesterday.

**Six assertions in five files read a production file as text. All six are converted.**

| Test | What it read as text | Now |
|---|---|---|
| `test_default_firm_id.py::test_repository_py_does_not_define_resolve_client_by_code` | `source.count("resolve_client_by_code")` | `defines(tree, name)` |
| `test_default_firm_id.py::test_the_count_is_looking_at_the_right_file` | `'def resolve_client_info(' in source`, ×2 | the module's defined function names |
| `test_resolution_view.py::test_the_service_neither_prints_nor_reads_input` | `print(`, `input(`, `sys.exit` in the text | the module's called names |
| `test_required_smtp.py::test_no_smtp_default_literal_is_left_in_the_module` | `f'"{gone}"' in source`, quotation marks and all | string constants equal to the value |
| `test_step10d_pipeline.py::test_no_migration_survives` | `"ALTER TABLE" in source` | string constants containing it |
| `test_logging_setup.py::test_importing_the_module_attaches_nothing` | a newline-prefixed call name, and a line-prefix scan of three entry points | module-scope calls |

**After, no assertion about a production file's source rests on its text**, from the same enumeration
re-run. Twenty-one assertions across sixteen functions, every one on a tree.

### What each was actually vulnerable to, which is not the same as being wrong today

**None of the six was failing.** Each is latent, and each has a specific comment that would break it:

- **The resolver.** A deleted function leaves a tombstone comment naming it, and **three already sit
  in production code**: two in `worker/database/repository.py` and one in `app.py`. The next deletion
  from `repository.py` recorded that way breaks the guard.
- **The domain layer.** `service.py`'s docstrings discuss what it must not do. One sentence containing
  `print(` fails it.
- **The SMTP literals, and this is the one that was already half-defeated.** The guard searched for
  `"mail.lastingimpact.co.uk"` **with the double quotes attached**, which is exactly why
  `config.py`'s own comment can name all three values today without failing it. It was approximating
  "is this hardcoded" with "does this appear in quotes", and the approximation **also missed a
  single-quoted form and a concatenated one**. The parsed version catches those and ignores the
  comment, so the guard got stronger and quieter at once.
- **`ALTER TABLE`.** A comment recording the removal, which is the comment this project writes.
- **The log handlers.** A comment or docstring line at column nought.

### One trap solved once, in the shared helper

**A docstring is a string constant.** A guard asking "does this forbidden text appear in a string"
reads a docstring recording the text's removal, which is the same fault in a new place.
`string_constants()` excludes docstrings by default and says why.

**`tests/source_guards.py` exists because six conversions across five files would have been five
copies of the same walk**, and this project has form on two copies of one thing drifting. It imports
nothing from the pipeline and is not named `test_*`.

### Guards left as text checks, and why

**None over these files.** Two things adjacent to the set are deliberately untouched:

- **`tests/test_step10d_pipeline.py`'s other assertions in the same function**,
  `assertIn(column, self._columns("receipts"))`. They read the **database** rather than the source, and my
  enumerator swept them in only because they share a function with the one that did. Not source
  guards at all.
- **`tests/live_paths.py::_root_variable()`** reads `config.py` and already parses it. It is not a
  guard; it extracts a value.

**No guard here asserts a comment is present**, which is the case the brief said would legitimately
stay as text. If one appears later it should stay, and the distinction is whether the subject is the
prose or the code.

---

## 3. The tombstone mutation, and the real one as control

**Run with the harness, and the four tombstones are the first real use of `expect=SURVIVES`.** Each
is a comment of exactly the shape this project writes, added to the production file its guard reads.

```
=== tombstone-names-the-deleted-resolver ===  expects: survives
    +    # resolve_client_by_code() was here until 2026-09-01. Nothing called
    +    # it and it restated the fallback firm_id twice. Amendment 93.
last line: 721 passed, 527 subtests passed
caught by 0 reported failure(s):
verdict: OK: survived, as expected

=== docstring-mentions-print ===  expects: survives
    +# An earlier draft used print( and sys.exit here; the domain layer does
    +# neither, per design document 4.1.
verdict: OK: survived, as expected

=== comment-records-the-removed-migrations ===  expects: survives
    +# Eleven ALTER TABLE ADD COLUMN guards were removed at 10d.34 and their
    +# columns are in the CREATE statements below.
verdict: OK: survived, as expected

=== comment-quotes-the-old-smtp-default ===  expects: survives
    +# The default here used to be "mail.lastingimpact.co.uk", which every
    +# installation inherited.
verdict: OK: survived, as expected
```

**All four would have failed the old guards.** Each contains the exact text its guard searched for,
including the SMTP one's quotation marks, which is the only way to fail that particular check.

**Three real mutations, all caught:**

| Mutation | Caught by |
|---|---|
| `resolve_client_by_code()` defined again in `repository.py` | `test_repository_py_does_not_define_resolve_client_by_code` |
| `print("parsing")` added to `parse_corrections()` | `test_the_service_neither_prints_nor_reads_input`, subtest `call='print'` |
| `SMTP_HOST` back to `os.environ.get(..., "mail.lastingimpact.co.uk")` | seven, including `test_no_smtp_default_literal_is_left_in_the_module`, subtest `literal='mail.lastingimpact.co.uk'` |

**So the converted guards are not loosened.** Each of the three is caught by the guard that was
converted, by name.

---

## 4. The harness's expected-outcome argument

**It is called `expect`, on `Mutation`, and it takes one of two module constants.**

- **`CAUGHT`** means the mutation changes behaviour and **the suite must notice**. Nothing catching it
  is a gap in the suite.
- **`SURVIVES`** means the mutation changes only prose, a comment or a docstring or a string nothing
  reads, and **the suite must not notice**. Something catching it is the finding: a guard is reading
  prose as though it were code.

**`CAUGHT` is the default, and it is the safer of the two.** A prose mutation left at the default
reports its pass as an alarm, which is merely the old behaviour; a real mutation wrongly marked
`SURVIVES` would report a genuine gap in the suite as success. An unrecognised value is refused when
the `Mutation` is constructed rather than after the suite has run.

**What a reader sees.** The header says `expects: survives`, and a `verdict:` line names which of the
four cases happened in words. The prose-caught case reads **"CAUGHT, and this mutation had to
survive: a guard is reading prose as though it were code"**, so the output states the finding rather
than leaving it to be inferred from a failure.

**The exit code now answers "did every mutation do what it said it would"**, which is the same
question for both kinds. It used to answer "was everything caught".

Seven tests cover it: all four combinations of expectation and outcome, the default, the refusal of a
bad value, and that the verdict reaches the printed report.

---

## 5. A harness defect the work exposed, and its own commit

**`ef3cb7b`. Found by using the harness on `config.py` for the first time**, three briefs after
writing it.

**This repository holds a mix of line endings: `app.py` is LF and `config.py` is CRLF.** `run_one()`
read the target with `read_bytes().decode()`, so a multi-line anchor written with `\n` matched
nothing on a CRLF file. `replace_once()` then reported **"the code moved. Read the file rather than
loosening the anchor"**, which sent me to read a file that was exactly as I thought it was. Two of the
three real mutations were blocked by it before I looked at the bytes.

**The message being wrong is the worse half.** A refusal that names the wrong cause costs more than
one that says nothing, because it is actionable and the action is useless.

The edit now sees LF whatever the file holds and the file is written back in its own convention.
**The restore is from the byte copy either way, so byte-exactness was never at risk**, and a test
asserts that.

**Four tests, and the fourth is the one worth having.** It drives the harness with a command that
reads the mutated file and reports whether it still holds CRLF. **A harness that silently rewrote
every CRLF file it touched would be worse than the bug**: the diff would be the whole file and any
guard comparing text would fail for the wrong reason.

---

## 6. My own mistakes

**Four, all caught by my own runs.**

1. **My enumerator under-reported after the conversion.** It detected a guard by looking for
   `.read_text()` on a production path, and a converted guard calls `source_guards.tree_of()`
   instead, so four modules dropped off the list entirely. **The tool that proves the set is complete
   stopped seeing the members I had just fixed.** Widened to detect both shapes before I quoted it.
2. **And then it mislabelled them.** Its "parses or matches text" flag looked for `ast.parse` in the
   function, which a converted guard no longer calls directly, so all six conversions were reported
   as text matches. Same fault one step along: **the tool encoded what the old code looked like
   rather than what the question was.**
3. **Two mutation anchors I wrote from memory did not exist.** The harness refused both rather than
   proceeding, and one of the two refusals was the CRLF defect wearing a disguise. The other was a
   line I had simply invented; I read the file and used a line that appears once.
4. **A heredoc mangled an escape sequence again**, on a string that itself contained `\n`. I had said
   the day before that I would stop using heredocs for content with escapes and did it anyway. The
   edit failed loudly rather than silently, and I used the editing tools for the rest.

**Numbers 1 and 2 are the same mistake as the one in yesterday's report**, where classifying by "is
`ast.parse` present" nearly reported a hybrid as a parser. **Three instances now of a measuring tool
answering a question about the code's shape rather than about its meaning**, and each time the tool
was mine and written minutes earlier.

---

## 7. Flags

### Flag 1: `CLAUDE.md` is modified in the working tree and is not mine

The six rules added to its standard-of-evidence section on 2026-09-08, which the brief's section 0
told me to read. **They are the consultant session's and are uncommitted.** I have read them and left
the file alone.

**Same shape as `.env.example` yesterday**, which Paul then asked me to commit because git writes
stay off the Cowork sandbox. **Say the word and I will commit it**, after reading the whole diff as I
did with that one.

### Flag 2: two entry-point scripts define `main()` and are not covered by the log-handler guard

Noticed while converting that guard, which checks `app.py`, `resolve_receipt.py` and
`discard_receipt.py`. **The list of three is hardcoded in the test.** `worker/logging_setup.py`'s own
`ENTRY_POINT_LOGS` names four log files, `run`, `resolve`, `discard` and `console`, and the console
is not built yet.

**So the guard is right today and its list is not derived from anything.** When the console arrives,
nothing makes the fourth entry point appear in it. **Small and obviously right: derive the modules
from `ENTRY_POINT_LOGS` rather than listing them**, which is the same set-completeness rule that
caught the retry wrapper. It needs a decision about how a log name maps to a module file, so I have
not taken it.

---

## 8. What the brief got wrong

**Nothing.** Its diagnosis of the resolver guard was right, its reading of that guard's docstring was
right, and its scoping instruction was the important part: **"that scoping is the consultant
session's error and it is worth naming"** is what turned one conversion into six.

**One thing to add.** The brief says the fault "was sitting one file over the whole time". **It was
sitting in five files**, four of them not `repository.py`. The enumeration is in section 2 and the
brief could not have known, because the previous brief's scope stopped at `app.py` and so did mine.

---

## 9. Confidence

**High that no guard over `app.py`, `config.py` or `worker\` now rests on text.** It rests on the
enumeration being taken from each test module's syntax tree, re-run after the change and reporting
nothing, and on four tombstone mutations surviving where each would have failed the old guard.

**High that nothing was loosened**, and it rests on three real mutations each being caught by the
specific guard that was converted, named in the failure.

**High that `expect` does what section 4 says**, and it rests on seven tests covering all four
combinations plus the default and the refusal.

**High on the CRLF defect being fixed and not having caused damage**, and it rests on the restore
being from a byte copy, asserted, plus a test that reads the file while it is mutated.

**This says nothing about guards over the test files themselves**, or over
`IntelliBooks-Desktop-v3.html`, neither of which I looked at. The scope was the three production
locations the brief named.
