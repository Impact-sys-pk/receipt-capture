# Report: the IMAP settings and the OpenAI key are required with a message

**Written 2026-09-07, 17:48 BST (16:48 UTC), by the implementation session in Claude Code.**
**Branch `feat/console-phase0`. Item 173 of `2026-08-20_LIST_outstanding_items_and_decisions.md`.**
**Brief: `PROMPT_claude_code_2026-09-07_imap_and_openai_required.md`, now in `archive\`.**

---

## 1. What landed

**Three commits, none pushed.**

| Commit | What |
|---|---|
| `72e2cbe` | `fix(config): the IMAP settings and the OpenAI key refuse with a message` |
| `ec5746f` | `test(config): the credential guard covers every family and both shapes` |
| `6a85cf9` | `style(tests): drop a false-contrast phrasing from an assertion message` |

The third is wording in one assertion message and is mistake 2 in section 7. It was committed
separately rather than amended into `ec5746f`, which was a whole commit back by then.

`IMAP_HOST`, `IMAP_USERNAME`, `IMAP_PASSWORD` and `OPENAI_API_KEY` go through the existing
`_required()` helper. `IMAP_PORT` is untouched. Nothing was reordered and
`test_every_refusal_sits_above_every_mkdir` stayed green throughout, as the brief expected.

**The suite.**

| When | Result |
|---|---|
| Before, the committed tree at `1b43192` | **603 passed, 363 subtests** |
| After all three, at `6a85cf9` | **612 passed, 379 subtests** |

**The before figure was measured, at 17:34 BST on the tip before any edit**, rather than carried
forward from yesterday's report. It agrees with the brief's 603. The nine extra passes and sixteen
extra subtests are all in `tests\test_required_imap_and_openai.py` and in the widened guard.

**Here is the message a person now gets**, driven in a child process with `IMAP_HOST` removed rather
than quoted from the source:

```
RuntimeError: IMAP_HOST is required and has no default. It read None. It is the mail server the
capture mailbox is read from. config.py carried one firm's own values here until 2026-09-07, so
another installation inherited them instead of being asked for its own. Set it in
C:\LastingImpact\receipt_capture\.env, unquoted, and see
C:\LastingImpact\receipt_capture\.env.example for the shape.
```

**One sentence in that message is untrue for these four settings.** It is flag 1 in section 5, and
it is the reason I am putting the real output here rather than describing it.

**`.env.example` already lists all five names**, checked rather than assumed, so the message points
somewhere that answers it.

---

## 2. Did any test need an environment value it did not need before? No

**No test needed anything new, and nothing was added quietly.** The full suite went from 603 passing
to 612 passing with no failure at any point after the change, so no existing test was relying on
`config` importing with one of these four absent.

**Why that was the likely outcome, established by reading rather than by the run passing.** Every
route by which the suite imports `config` already had all four:

- **Through `conftest.py`.** `tests\live_paths.py` calls `load_dotenv()` before it captures the live
  roots, so the pytest process's own environment carries everything `.env` sets. It sets none of
  these four itself, and it did not need to.
- **Through the three subprocess files.** `tests\test_required_roots.py`,
  `tests\test_required_smtp.py` and the new one all build their child's environment from
  `dict(os.environ)`, so they inherit the same values. `test_required_smtp.py` was already relying on
  this for IMAP before today.
- **Through `tests\test_resolution_view.py`**, which spawns a child importing
  `worker.resolution.service` with the environment inherited and no `env=` argument, so it gets the
  parent's.

**So the answer rests on the mechanism as well as on the green run**, which matters because "no test
broke" is also what a test that stopped checking anything would report.

---

## 3. The AST guard: widened in place rather than mirrored

**Widened**, in `tests\test_required_smtp.py`'s `NoDefaultSurvivesInTheSourceTest`, and renamed from
`test_no_smtp_variable_is_read_with_environ_get` to
`test_no_credential_is_read_with_environ_get_or_a_bare_subscript`.

**Why not a second copy in the new file.** It guards a **shape** in `config.py`'s source rather than
anything about SMTP, and two guards over one shape drift apart. `CLAUDE.md`'s traps section records
exactly that happening on this project, where one copy of a list had four entries and the other six.
**The cost is that a file named for SMTP now carries a test that is not about SMTP**, and both that
file's docstring and the new file's say so, so a reader arriving at either finds the other.

**It had to be widened in shape as well as in scope, and that is the part worth reading.** The old
version looked only for `os.environ.get(name, default)`, a default by definition. **Every one of the
four settings item 173 changed was a bare subscript, `os.environ["IMAP_HOST"]`, which the old guard
passed in silence.** A bare subscript is not the same defect, because it carries no value for an
installation to inherit; it is the same absent message. So the guard now catches both shapes.

**`OPENAI_MODEL` is matched out by using the exact name `OPENAI_API_KEY` rather than an `OPENAI_`
prefix.** It is a model name with a sensible default and has no business in a credential guard.

**`IMAP_PORT` is the one exception and the test asserts its own exception list**:

```python
allowed_defaults = {"IMAP_PORT"}
self.assertEqual(allowed_defaults, {"IMAP_PORT"},
                 "the exception list changed; that needs a decision behind it rather than a refactor")
```

That looks circular and is not. It means a future edit that quietly adds a name to the exception list
fails, so an exception has to be argued rather than slipped in behind a prefix rule.

---

## 4. Evidence

### Red before green

`tests\test_required_imap_and_openai.py` and the widened guard were written and run before
`config.py` was touched. **18 failed, 16 passed, 15 subtests passed**, the passes being the
`IMAP_PORT` test, the key-safety test and the SMTP file's own unchanged tests. The widened guard's
failure names all four:

```
E  AssertionError: Lists differ: ['IMAP_HOST (bare subscript)', 'IMAP_PASSWORD (bare subscript)',
   'IMAP_USERNAME (bare subscript)', 'OPENAI_API_KEY (bare subscript)'] != [] : these are read
   straight from the environment, so they either carry a default or refuse with a bare KeyError
```

### The mutations, one per setting plus one

| # | Mutation | Suite | Caught by |
|---|---|---|---|
| 1 | `IMAP_HOST` back to a bare subscript | 6 failed, 610 passed | The widened guard; `test_each_is_a_call_naming_its_own_variable_and_carrying_no_default` (subtest IMAP_HOST); `test_each_message_says_what_the_setting_is_for` (IMAP_HOST); `test_each_of_the_four_is_required` (IMAP_HOST unset and empty); `test_the_message_names_the_env_file` |
| 2 | `IMAP_USERNAME` back to a bare subscript | 5 failed, 611 passed | The same four, all naming IMAP_USERNAME |
| 3 | `IMAP_PASSWORD` back to a bare subscript | 5 failed, 611 passed | The same four, all naming IMAP_PASSWORD |
| 4 | `OPENAI_API_KEY` back to a bare subscript | 6 failed, 610 passed | The same four, plus `test_it_is_a_runtime_error_and_not_an_assert`, which drives that key under `python -O` |
| 5 | `IMAP_HOST` given a default of `mail.lastingimpact.co.uk` | 7 failed, 610 passed | All of mutation 1's, plus `test_no_smtp_default_literal_is_left_in_the_module`, which already guarded that literal |

**Mutation 5 is there because the other four only prove the guard catches the shape it was widened
for.** The old shape, a default carrying one firm's value, is the one this project has actually been
bitten by, and it is still caught.

All five restored byte for byte, asserted by the harness and confirmed with `git status` afterwards.

### One departure from `test_required_smtp.py`'s method, and it is deliberate

**The child never prints `OPENAI_API_KEY`.** It compares it against a fake and prints
`key_matches=True`. `CLAUDE.md`'s third trap is a live key printed in full by a session that believed
it had masked it, which had to be revoked. `import_config()` always overwrites the variable, so the
real key cannot reach the child today; printing `repr()` anyway would mean one edit removing that
override is all it takes to put a live key into pytest output and into anything that captures it.
**`test_the_key_is_never_printed_by_this_file` holds it**, and it also asserts the real key from
`.env` appears in neither stream.

---

## 5. Flags

**Two, neither fixed. The first is small, obviously right, and I will do it on your word.**

### Flag 1: `_required()`'s shared sentence is untrue for these four

Quoted in full in section 1. The middle sentence reads:

> config.py carried one firm's own values here until 2026-09-07, so another installation inherited
> them instead of being asked for its own.

**That is true of the four SMTP settings and false of these four.** `IMAP_HOST` was
`os.environ["IMAP_HOST"]`, so `config.py` never carried a value for it and no installation ever
inherited one. **The whole value of this change is the message, so a message containing a false
statement about its own history is worth more than a quibble.**

**Not fixed, because the sentence lives in `_required()` and the brief's section 3 says not to touch
the four SMTP settings**, whose messages would change with it. That is Paul's call rather than mine.

**The one-line fix, if he wants it.** Replace that sentence in `_required()` with wording true of
both cases:

> There is no default, because this is one installation's own value and `config.py` must not answer
> for it.

It is a one-line edit in one helper, and `tests\test_required_smtp.py` asserts only that the message
names the variable, quotes the value and names both `.env` files, so nothing goes red. **Say the word
and it is done in the same session.**

### Flag 2: `IMAP_PORT`, as section 5.3 of the brief asked

**My view: leave it, and the inconsistency is the lesser of the two problems.**

The argument for making it required is consistency with `SMTP_PORT`, which was made required this
morning despite having a default of `465`. The argument against is that `993` is the standard IMAPS
port defined by the protocol, where `465` was a value somebody typed. **The distinction that decides
it is whose value it is**, which is the reasoning amendment 253 actually rested on and the same test
that separates `OPENAI_MODEL` from `OPENAI_API_KEY`: `gpt-4o` and `993` are facts about the world,
and `mail.lastingimpact.co.uk` and `alerts@lastingimpact.co.uk` were facts about Intellitax.

**So `SMTP_PORT` and `IMAP_PORT` are not the same case, and treating them alike would be consistency
about the wrong property.** If anything, `SMTP_PORT` is the odd one now: `465` is also a standard
port, so amendment 253 arguably swept it up with three settings that genuinely were one firm's.
**I am not proposing to reverse it**, because a required setting that somebody has already put in
`.env` costs nothing and reversing it would be churn.

**What makes the remaining inconsistency safe is that it is written down in three places rather than
left to be noticed**: a comment in `config.py`, a test in
`tests\test_required_imap_and_openai.py` that asserts the default is still there, and the exception
list inside the widened guard. **An undocumented inconsistency is the problem; a recorded one is a
decision.**

---

## 6. Anything in the brief that was wrong

**Nothing was wrong. Two things were incomplete, and one of them changed what I built.**

| Claim | Held? |
|---|---|
| The four are bare `os.environ[...]` subscripts | **Yes** |
| `IMAP_PORT` reads `os.environ.get("IMAP_PORT", "993")` | **Yes** |
| `_required()` and `_required_int()` exist and are tested | **Yes**, and only `_required()` was needed: none of the four is a number |
| `test_required_smtp.py` has an AST guard for the SMTP four | **Yes, but it guards only one of the two shapes.** It looked for `environ.get` alone, so it would not have caught any of the four settings this brief is about even after they were named in it. **Widening its scope without widening its shape would have produced a guard that passed on the exact defect being fixed**, which is the thing this project calls a check that cannot fail. Section 3 |
| `.env` on Paul's machine sets all four, so no behaviour change and no test needs a new value | **Yes**, and section 2 gives the mechanism rather than only the green run |
| The suite stood at 603 passed, 363 subtests at `1f9c4b8` | **Yes**, measured at `1b43192`, which is `1f9c4b8` plus a report |
| `tests\live_paths.py` deliberately does not set these | **Yes** |
| A fifth shape of refusal would need adding by hand to `test_every_refusal_sits_above_every_mkdir` | **Yes**, and using `_required()` avoided it. That test needed no change and stayed green |

**The second incomplete thing cost nothing.** The brief's table gives `IMAP_USERNAME` as "the capture
mailbox itself, the address clients email receipts to", which I used almost verbatim. It does not say
what to do when the four messages and `_required()`'s shared sentence disagree, which is flag 1, and
that is fair enough: nobody had read the assembled message until I drove it.

---

## 7. My own mistakes

**Two.**

**A subtest of mine passed in the red state for the wrong reason.**
`test_each_message_says_what_the_setting_is_for` originally looked for the word `password` in
`IMAP_PASSWORD`'s message. Against the old bare subscript the error is
`KeyError: 'IMAP_PASSWORD'`, which lowercases to contain `password`, so **three of the four subtests
went red and the fourth went green while nothing had been fixed.** A check that cannot fail hiding
inside a check that can, and it would have been invisible once the change made everything green.

Corrected two ways rather than one: the phrase became `that mailbox`, and the subtest now asserts
that no phrase is a substring of its own variable name, so the same mistake cannot be made again in
the other three rows. The docstring records it.

**Second, and smaller: I wrote a banned construction into an assertion message.** The exception-list
assertion in the widened guard read "that is a decision, not a refactor", which is the
false-contrast shape the house style rules out anywhere in output, generated files included. Caught
by running the style check over the report and finding the same phrase quoted back from the source.
Fixed in both, commit `6a85cf9`. **Worth recording because I ran that check on the report and not on
the code**, and the rule does not distinguish between them.

---

## 8. Confidence

**High that the change is correct and complete.** It rests on: the suite at 612 passed and 379
subtests with no failure; eighteen failures quoted from the red run before `config.py` was touched;
five mutations each caught by tests naming the setting they broke, including one for the older
default-shaped defect; the real refusal message driven in a child process rather than read off the
source; and `.env.example` checked to contain every name the message points at.

**High that nothing else moved.** `config.py`'s only other change is the comment block above the four
settings, no ordering changed, and `test_every_refusal_sits_above_every_mkdir` was green before,
during and after.

**Moderate on flag 2 being the right call**, because it is a judgement about consistency rather than
a fact, and Paul or the consultant session may weigh it differently. The facts under it are firm:
`993` is the standard IMAPS port, and the exception is recorded in three places.

**Flag 1 is a fact rather than a judgement**, and I would rather it were fixed than left, but it is
inside a helper the brief told me not to disturb.
