# Report: `_required()`'s shared sentence is now true of all eight settings

**Written 2026-09-07, 18:05 BST (17:05 UTC), by the implementation session in Claude Code.**
**Branch `feat/console-phase0`. On Paul's instruction of 2026-09-07.**
**Closes flag 1 of `2026-09-07_REPORT_claude_code_imap_and_openai_required.md`. Flag 2, `IMAP_PORT`, is agreed and left as it is.**

---

## 1. What landed

**One commit, `956b896`, and it is not pushed.** `fix(config): the shared refusal message is true of all eight settings`.

| When | Result |
|---|---|
| Before, the committed tree at `fca710b` | **612 passed, 379 subtests** |
| After, at `956b896` | **615 passed, 379 subtests** |

**The before figure was measured at 17:58 BST on the tip before any edit**, rather than carried
forward. The three extra passes are the three tests below; no subtest was added or lost.

**Eight settings reach this helper, enumerated from `config.py`'s AST rather than counted by eye**,
which is the check I got wrong two reports ago:

```
  line  212  IMAP_HOST        via _required
  line  215  IMAP_USERNAME    via _required
  line  219  IMAP_PASSWORD    via _required
  line  225  OPENAI_API_KEY   via _required
  line  251  SMTP_HOST        via _required
  line  253  SMTP_PORT        via _required_int
  line  255  SMTP_USERNAME    via _required
  line  260  SMTP_PASSWORD    via _required
total settings reached by _required's message: 8
```

`SMTP_PORT` is in the eight because `_required_int()` calls `_required()` for the presence check, so
a missing port gets this message and only a non-numeric one gets `_required_int()`'s own.

---

## 2. The assembled messages, driven in child processes

**Both produced by removing the variable from a child's environment with `dotenv` stubbed, and
reading `stderr`.** Neither is quoted from the source.

**One SMTP setting:**

```
RuntimeError: SMTP_HOST is required. It read None. It is the outgoing mail server alerts are
sent through. There is no default, because this is one installation's own value and config.py
must not answer for it. Set it in C:\LastingImpact\receipt_capture\.env, unquoted, and see
C:\LastingImpact\receipt_capture\.env.example for the shape.
```

**One IMAP setting:**

```
RuntimeError: IMAP_HOST is required. It read None. It is the mail server the capture mailbox is
read from. There is no default, because this is one installation's own value and config.py must
not answer for it. Set it in C:\LastingImpact\receipt_capture\.env, unquoted, and see
C:\LastingImpact\receipt_capture\.env.example for the shape.
```

Both exited 1.

---

## 3. One departure from the wording you named, and why

**You said to replace the shared sentence with the wording I proposed. I did, and I also dropped
three words from the sentence before it.** The first sentence read "`{variable}` is required and has
no default." It now reads "`{variable}` is required."

**Because keeping it gave this:**

> SMTP_HOST is required **and has no default**. It read None. It is the outgoing mail server alerts
> are sent through. **There is no default**, because this is one installation's own value and
> config.py must not answer for it.

**Twice in four sentences, and the second time is the one that explains itself.** This was only
visible once the message was assembled, which is exactly why you asked for it to be driven rather
than quoted, so I have treated finding it as the job rather than as a reason to stop and ask.

**Nothing else in the message moved**, and the sentence you named is verbatim. **If you would rather
have the words back, it is a three-word edit and the tests do not care**: they assert the claim
("one installation's own value", "must not answer for it") rather than the full sentence, precisely
so a copy-edit does not break them while a reversion to the false history does.

---

## 4. What was deliberately not touched

**`_required_root()`'s message keeps its own account and it is untouched.** It says almost the same
thing:

> There is no default: config.py carried one until 2026-09-06 and it was one person's own folder,
> which is how a bare import made folders on machines it did not belong to.

**That is true of the roots.** They really did carry one person's folders, and the consequence it
names really happened, twice, and is the fourth trap in `CLAUDE.md`. **Deleting it to be consistent
would be fixing a false explanation by throwing away a true one**, so the new source guard asserts
it is still there. Mutation C below is that assertion being exercised.

**`_required_int()`'s own message is untouched**, because it fires only for a value that is present
and not a number, where no question of defaults arises.

---

## 5. Evidence

### Red before green

Three tests written and run before `config.py` was touched:

```
FAILED tests/test_required_smtp.py::RefusalTest::test_the_message_says_why_there_is_no_default_without_claiming_history
FAILED tests/test_required_smtp.py::NoDefaultSurvivesInTheSourceTest::test_the_shared_message_makes_no_claim_about_what_config_used_to_hold
FAILED tests/test_required_imap_and_openai.py::RefusalTest::test_the_message_says_why_there_is_no_default_without_claiming_history
3 failed, 19 passed, 30 subtests passed
```

**Two behavioural and one on the source, and the split is the point.** One drives an SMTP setting and
one an IMAP setting, so both families are shown getting one true message. The third reads
`_required()`'s statements, because **a behavioural test cannot tell the two helpers apart**: both
raise a `RuntimeError` naming a variable, and the four settings whose history claim was true would
have gone on passing whatever `_required_root()` said.

### The mutations

| # | Mutation | Suite | Caught by |
|---|---|---|---|
| A | Put the false sentence back | 3 failed, 612 passed | All three of the tests above |
| B | Delete the explanation instead of correcting it | 3 failed, 612 passed | All three |
| C | Sweep `_required_root()`'s true account up with the false one | 1 failed, 614 passed | The source guard |

**Mutation B is there because "do not say something false" is satisfied by saying nothing**, and a
message that named the variable, quoted the value and named both `.env` files would have passed every
other test in both files. **Mutation C is there because the fix and the over-fix look identical from
outside.**

All three restored byte for byte, asserted by the harness and confirmed with `git status`.

---

## 6. My own mistake, and it is the same one twice in one day

**The source guard failed on its first green run, on `_required()`'s docstring.** That docstring
quotes the old sentence, because this project records superseded wording rather than deleting it, so
a check reading the unparsed function found the very string it was asserting absent.

**I made the identical mistake this morning**, in
`tests/test_client_top_folder.py`'s `test_the_default_firm_id_is_not_used_to_pick_the_record`, and
wrote it up in that report. **Knowing about it did not stop me repeating it four hours later**, which
is worth more than the fix.

**The rule that falls out, and it is sharper than "strip the docstring":** on this project a check on
what code does must never read prose about that code, because **the prose is always there.** The
convention of keeping superseded wording, struck through and beside the correction, guarantees that
every corrected thing has its old version written down within a few lines of the new one. **Every
source-level guard here is walking past a copy of exactly what it is looking for.**

Both tests now strip docstrings before comparing, and both say why in their own docstrings.

---

## 7. Flags

**None new.** Nothing else came up. `IMAP_PORT` stands as agreed, with its default, its comment in
`config.py`, its test, and its place in the credential guard's exception list.

---

## 8. Confidence

**High that the sentence is now true of all eight settings.** It rests on the AST enumeration of the
eight callers rather than on reading the file, on both assembled messages driven in child processes
rather than quoted, and on three mutations each caught by tests naming what they broke.

**High that `_required_root()` is untouched**, and it rests on `git diff` showing the only lines
mentioning it are new docstring lines in `_required()`, plus mutation C going red when its message is
changed.

**The departure in section 3 is the one thing you may want reversed**, and it is three words.
