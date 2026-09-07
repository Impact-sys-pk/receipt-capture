# Brief: the IMAP settings and the OpenAI key become required with a message

**Written 2026-09-07 by the consultant session, chat 17. Branch `feat/console-phase0`.**
**Item 173 of `2026-08-20_LIST_outstanding_items_and_decisions.md`. Paul's decision, 2026-09-07: do it.**

**This is your own observation from section 5 of `2026-09-07_REPORT_claude_code_two_small_fixes.md`,
turned into work.** You were right to raise it rather than act on it.

---

## 1. What to change

**Four settings stop being bare `os.environ[...]` subscripts and become required with a message, by
the pattern amendment 253 established for the four SMTP settings this morning:**

| Setting | What it is, for the message |
|---|---|
| `IMAP_HOST` | The mail server the capture mailbox is read from |
| `IMAP_USERNAME` | The capture mailbox itself, the address clients email receipts to |
| `IMAP_PASSWORD` | That mailbox's password |
| `OPENAI_API_KEY` | The key every extraction is billed to |

**Use the existing helpers.** `_required()` and `_required_int()` are already there and already
tested, and reusing them is the point rather than an economy: a fifth shape of refusal would need
adding by hand to `test_every_refusal_sits_above_every_mkdir`, which you wrote this afternoon and
whose docstring says exactly that.

**Each message says what the setting is for and where to put it**, the way the SMTP four do. The
value of the change is entirely in the message: a `KeyError: 'IMAP_HOST'` on a fresh checkout tells
somebody nothing.

---

## 2. `IMAP_PORT` is deliberately NOT in this brief

**It reads `os.environ.get("IMAP_PORT", "993")`, so it carries a default and the other three do
not.** Paul's decision covers the four in the table above and not the port.

**There is an argument each way and it is not yours or mine to settle.** `SMTP_PORT` was made
required this morning even though it had a default of `465`, so consistency says the port follows.
Against that, `993` is the standard IMAPS port rather than one firm's value, which is the reasoning
amendment 253 actually rested on.

**So leave it, and flag it in your report if you think the inconsistency is worse than the default.**
Do not change it.

---

## 3. What this must not do

**Do not touch the two roots, the four SMTP settings, or `_required_root()`.** They are done and
tested.

**Do not reorder anything.** `9c6186e` put every refusal above every `mkdir` this afternoon and these
four are already above it. `test_every_refusal_sits_above_every_mkdir` should stay green throughout
rather than needing anything.

**`.env` on Paul's machine sets all four already**, so there is no behaviour change on his machine
and the suite should not need a value it did not need before. **If a test does start needing one,
that is a finding: say so rather than adding it quietly.** `tests\live_paths.py` writes a firm record
and redirects paths; it deliberately does not set these, and the two subprocess test files supply
their own environment.

---

## 4. Evidence expected

The standard is `CLAUDE.md`'s and you have applied it twice today.

- **Red before green**, output quoted.
- **Drive the refusal, one case per setting, missing and empty**, in child processes with `dotenv`
  stubbed, the way `tests\test_required_smtp.py` already does. Reuse that file's method rather than
  inventing a second one.
- **A mutation per setting**, putting the bare subscript back, each caught by tests naming the
  setting.
- **An AST guard that no `SMTP_*`, `IMAP_*` or `OPENAI_API_KEY` name is read through `environ.get` or
  a bare subscript in the module**, which is the shape of the defect rather than four instances of
  it. `tests\test_required_smtp.py` has one for the SMTP four; extend or mirror it, and say which.
- **Quote the suite before and after**, passes and subtests separately. It stood at **603 passed, 363
  subtests** at `1f9c4b8`. **Measure the before figure, do not carry it forward.** You have been
  caught by that once today and said so.
- **Flag, do not fix.** Anything else wrong gets reported, with an offer if it is small.
- **Disclose your own mistakes.**
- **Separate commits, with explicit path lists.**

---

## 5. The report

**Write it to
`C:\LastingImpact\receipt_capture\2026-09-07_REPORT_claude_code_imap_and_openai_required.md`
and commit it.**

Carry, beyond what you did:

1. **Whether any test needed an environment value it did not need before**, and if so which and why.
2. **The AST guard**: extended or mirrored, and the reason.
3. **Your view on `IMAP_PORT`**, one paragraph, as a flag rather than a change.
4. **Anything in this brief that was wrong.**

**This brief is spent on delivery of that report and goes into `archive\` with `git mv`.**
