# Report: SMTP settings required, plus repository housekeeping

**Claude Code, 2026-09-07, 11:45 to 12:20 BST.** Written from
`PROMPT_claude_code_2026-09-07_smtp_required_and_housekeeping.md`. Branch `feat/console-phase0`.

**All five changes are done.** Six commits, one per change plus one for the two documents the
consultant session left uncommitted while I worked.

**Suite: 569 passed and 344 subtests before, 579 passed and 358 subtests after.** Both figures are
passes and subtests separately, quoted from the last line of `pytest -q`, which prints them as two
counts. Nothing in the suite failed at any point.

**Two things worth reading before the detail.**

**One, `.env` really was the only thing keeping the sending address right.** Confirmed rather than
assumed: `.env` set `SMTP_PASSWORD` and none of the other three, so `mail.lastingimpact.co.uk`, port
`465` and `alerts@lastingimpact.co.uk` came from the literals in `config.py` every time the pipeline
sent an alert. All four are now required and the three values are in `.env`, so this machine behaves
exactly as it did. Verified by importing `config` and reading all four back.

**Two, I bundled changes 2, 4 and 5 into one commit by mistake and then separated them.** `git mv`
stages its own moves, so `git add app.py && git commit` swept in the image moves and the twenty-two
archive moves that were already staged. Both commits were local and unpushed, so I did a mixed reset
back to change 1 and re-committed in four, then proved the result is byte-identical: the tree hash
after separating is `b6e6aae67a18b0f4a7bb062970ce25ae2e01edf1`, the same hash the bundled pair
produced. Section 8 has the detail. **Change 1 was never bundled with anything**, which is the part
the brief said not to do.

---

## Change 1. The four SMTP settings are required

### What the code does now

Two new helpers in `config.py`, placed with `_required_root` rather than with their callers so the
three read together:

```python
def _required(variable: str, what: str) -> str:
```

Presence is the whole test. `what` describes the setting and is printed in the message, so a person
who has never opened `config.py` learns what to put there. One call and one message per variable, for
the reason `_required_root`'s docstring already gives: a combined message sends somebody to check the
variable that was already right.

```python
def _required_int(variable: str, what: str) -> int:
```

The same, then `int()`, and a `ValueError` is re-raised as a `RuntimeError` naming the variable.
`int()` on its own reports `invalid literal for int() with base 10: 'four six five'`, which names the
string and not the setting it came from.

**`_required_root` is untouched.** The brief said not to reuse it as-is and I did not extend it
either, for a reason worth recording: `tests/live_paths.py`'s `_root_variable()` parses `config.py`'s
source with `ast` and requires each root to be declared as **a call taking exactly one string
argument and no keywords**. Giving `_required_root` a second parameter would have broken that reader
and, through it, the capture of the live roots that five tests depend on. The two new helpers take two
arguments, and nothing parses their call sites.

The four settings:

```python
SMTP_HOST = _required(
    "SMTP_HOST", "It is the outgoing mail server alerts are sent through.")
SMTP_PORT = _required_int(
    "SMTP_PORT", "It is the SMTP port, and the code connects with SMTP_SSL.")
SMTP_USERNAME = _required(
    "SMTP_USERNAME",
    "It is the mailbox alerts are sent from. It is the From address the "
    "recipient sees and it is printed in the body of the unknown-sender reply, "
    "so a wrong one publishes somebody else's mailbox to a client.")
SMTP_PASSWORD = _required(
    "SMTP_PASSWORD", "It is that mailbox's password.")
```

With a comment block above them recording what the defaults were and why they mattered.

**A correction I made to my own first version, before any measurement was taken.** The shared part of
the message originally ended "...which for the sending address meant printing that firm's mailbox in
email to somebody else's correspondent". That sentence is about `SMTP_USERNAME` and it was being
printed for all four, so a missing port would have been explained by a consequence that has nothing
to do with ports. The shared text now says only that one firm's own values were carried here and
another installation inherited them, and the sending-address consequence sits in `SMTP_USERNAME`'s own
`what` where it belongs. **I found that by reading the probe output in section 1's table rather than
by reasoning about it**, which is the only reason I found it at all.

### `.env` and `.env.example`

**`.env` gains the three it did not carry**, taken from the literals being deleted so nothing about
this machine changes:

```
# SMTP. All four are required; config.py has no defaults for them from
# 2026-09-07. These three were the literals it used to carry.
SMTP_HOST=mail.lastingimpact.co.uk
SMTP_PORT=465
SMTP_USERNAME=alerts@lastingimpact.co.uk
SMTP_PASSWORD=<unchanged>
```

`.env` is gitignored, confirmed with `git check-ignore -v .env`, which reports `.gitignore:1:.env`,
and it is not tracked. **It was edited by a script rather than by a shell command, and the readback
prints keys with the three new values and `<not printed>` for everything else.** That file holds two
passwords and an API key, and CLAUDE.md's rule about not reasoning from output you filtered yourself
exists because a `sed` mask over `.env` printed a live API key in full on 2026-08-01. Nothing in this
session's output contains a secret.

**`.env.example` gains all four with placeholders** and a comment block in the roots block's style,
saying they are required, that `config.py` refuses to import without them, and what each one is,
including that `SMTP_USERNAME` is published to the recipient and receives replies. It had no SMTP
section at all, so a fresh checkout was never told these settings exist.

### The refusal, driven rather than assumed

Eight cases, each a fresh child process with `dotenv` stubbed out so `.env` could not put back the
variable being removed, and with valid roots and IMAP and OpenAI settings supplied so that any failure
is the SMTP check and not a missing prerequisite.

| Case | Exit | What it said |
| --- | --- | --- |
| all four set | 0 | `imported, SMTP_HOST='mail.example.com' SMTP_PORT=465 SMTP_USERNAME='alerts@example.com'` |
| `SMTP_HOST` missing | 3 | `RuntimeError: SMTP_HOST is required and has no default. It read None. ...` |
| `SMTP_HOST` empty | 3 | the same, `It read ''` |
| `SMTP_PORT` missing | 3 | `RuntimeError: SMTP_PORT is required and has no default. It read None. ...` |
| `SMTP_PORT` not a number | 3 | `RuntimeError: SMTP_PORT must be a whole number and it read 'four six five'.` |
| `SMTP_USERNAME` missing | 3 | names `SMTP_USERNAME` and nothing else |
| `SMTP_PASSWORD` missing | 3 | names `SMTP_PASSWORD` |
| `SMTP_PASSWORD` empty | 3 | the same, `It read ''` |

**`SMTP_PORT` still arrives as an `int`**, printed as `465` with `type(...)` reported as `int` in the
control case.

**And the values on this machine are unchanged**, read back through a normal import with `.env` in
place:

```
SMTP_HOST      'mail.lastingimpact.co.uk'
SMTP_PORT      465 int
SMTP_USERNAME  'alerts@lastingimpact.co.uk'
SMTP_PASSWORD  set, length 16
```

### `SMTP_PASSWORD`, which was the consultant session's suggestion rather than Paul's instruction

**Nothing broke and I found no reason to stop.** Its default was `""`, which fails at send time inside
`smtplib.login` rather than at import, and `.env` already set it. Making it required removes the last
of the four and moves that failure to the earliest point it can be reported. The empty-string case is
tested and refused, which is the case its own default used to produce.

### The consequence the brief asked me to confirm

**Confirmed by running, not assumed.** `config.py` calls `load_dotenv()` at import; `.env` now sets
all four; the suite is green at **579 passed, 358 subtests**. No test failed at import and no test
needed changing.

**`tests/live_paths.py` needed no change and I made none.** It sets the two root variables because it
**redirects** them, which is a different job: the roots have to point somewhere private before
`config` computes eighteen paths from them. The SMTP settings are read from `.env` like the IMAP and
OpenAI settings already are, and those have been required with `os.environ[...]` for months.
**Setting them in `live_paths.py` would have been actively wrong**: it would mask a genuinely
misconfigured `.env` from the entire suite, which is the shape of a check that cannot fail.

### The test file, which the brief did not ask for

**`tests/test_required_smtp.py` is new and nothing in the brief asked for it. I judged it part of the
change rather than an extra, and this is me saying so rather than hoping it passes unnoticed.** Change
1 alters behaviour, and this repository's standard is that a defect which has been fixed must go red
if it comes back. Without it, somebody restoring one `os.environ.get` default would break the thing
the change exists to prevent and the suite would stay green.

10 tests and 14 subtests, modelled on `tests/test_required_roots.py` and using its subprocess method
and its stubbed `dotenv` for the reasons that file gives:

- **A control that imports successfully**, without which every other test would pass against a child
  that could not start at all, and which also asserts the port arrives as an `int`.
- **Each of the four refused when unset and when empty**, eight subtests, each checking the message
  quotes the value it read and does not say another variable is required.
- **A non-numeric port** naming the variable, and asserting `invalid literal` is **not** in the
  output, so a bare `ValueError` fails the test.
- **The message names `.env` and `.env.example`**, so a person who has just cloned can act on it.
- **`RuntimeError` and not an `assert`**, driven under `python -O`, where asserts are stripped and the
  check would silently vanish.
- **An AST guard on the source**, which is the check the behavioural tests cannot make: all four
  assigned at module level, each a call to `_required` or `_required_int` naming its own variable with
  exactly two arguments and no keywords, the port through the int helper, neither deleted literal
  present as a value, and **no `SMTP_*` name read through `environ.get` anywhere in the module**,
  which is the shape of the defect rather than one instance of it.

**The mutation.** All four defaults put back exactly as they were, from a copy of the changed file:

```
19 failed, 574 passed, 344 subtests passed in 32.80s
```

**Every one of the 19 is in `tests/test_required_smtp.py`** and nothing outside that file moved, which
I checked by listing the distinct files in the `FAILED` and `SUBFAILED` lines rather than by reading
the tail. **Counted with both prefixes**, because `pytest-subtests` writes `SUBFAILED` and matching
only `FAILED` would have reported 8 rather than 19: eight subtests from the four-variables test, four
plus two more from the two AST subtests, and five whole tests. Restored, and green again at 579 and
358.

## Change 2. The stale line-number comment in `app.py`

Was:

```python
            # Release lock (acquired at line 282)
            repo.release_receipt_lock(receipt_id)
```

Now:

```python
            # Release the lock repo.acquire_receipt_lock() took at the top of
            # this iteration. Named rather than numbered: this comment said
            # "acquired at line 282" and the file had grown past it, so the
            # number pointed at unrelated code. Amendment 247.
```

**A correction to the brief, and to my own commit message.** The brief says the acquire is "several
hundred lines above it". It is not: `repo.acquire_receipt_lock(receipt_id, allow_stale_after_minutes=60)`
is 94 lines above the release, and both are inside `_retry_failed_receipts()`, which spans lines 881
to 1004. The acquire is at the top of the same `for receipt in failed:` iteration whose `finally`
does the release. Measured by parsing `app.py` with `ast` and asking which function contains each
line, rather than by counting. **I repeated the brief's "several hundred lines above it" in commit
`aa35041`'s message before checking it**, so that message carries the wrong figure and this paragraph
is the correction. I have not rewritten that commit; the code comment says "at the top of this
iteration", which is right.

No other line-number comment was added or renumbered.

## Change 3. `live_paths.py`'s docstring

**The brief is right on both counts and the test next door was right all along.** Two statements
corrected, superseded wording struck through rather than deleted:

- **"all eighteen Path constants land in temp"** becomes **seventeen of the eighteen**. `BASE_DIR` is
  `Path(config.__file__).parent`, the repository itself, derived from neither root, so this redirect
  cannot move it.
- **The five no fixture pins** drops `BASE_DIR` and gains `RESOLUTIONS_DIR`, which is what
  `tests/test_conftest_redirect.py:50` already listed. `BASE_DIR` is pinned by nothing because there
  is nothing to pin, and `test_every_config_path_constant_is_under_a_temp_root` names it as the one
  exception for exactly that reason.

The correction says which file was right and why, so the next reader does not have to work out which
of the two lists to trust.

**Three `config.py` line citations replaced by names**, per amendment 247: `:73` and `:95-128` become
the `PRACTICE_ROOT` and `UNSYNCED_ROOT` assignments and the block of path constants below them, and
`:161` becomes "`config.py`'s import-time `mkdir` block". **Two of the three were already stale**, as
the roots change of 2026-09-06 moved everything below the definitions.

**A fourth citation I also corrected, disclosed because the brief said three.** A comment further down
the same file read "RESOLUTIONS_DIR has an environment override of its own at `config.py:128`". That
is a fourth `config.py:NN` in the same file and the same amendment covers it, so it is now "an
environment override of its own, read before the fall back to `INTELLIBILLS_ROOT`". Searching the file
afterwards, the only `config.py:NN` left is inside a struck-through record of the old wording, which is
this project's convention for superseded text.

## Change 4. The two loose test images

**Searched first, as the brief required.** Both filenames across the whole repository, excluding
`.history\` and `Backups\`: **five mentions, every one prose in a `.md` file**, plus a check that no
`.py` file anywhere opens a name containing `REPORT`, `PROMPT` or `HANDOVER`. **Nothing opens either
image by name**, so both were moved with `git mv`:

```
R100  TEST_review_A_pennine_cafe.png       -> Test Receipts/TEST_review_A_pennine_cafe.png
R100  TEST_review_B_kirkgate_hardware.png  -> Test Receipts/TEST_review_B_kirkgate_hardware.png
```

`R100` is git's own rename detection at 100% similarity, so the content is untouched and the history
follows. Sizes on disk after the move are 48,166 and 52,300 bytes, the same as before. Suite unchanged
at 579 and 358.

**Where the five mentions are**, in case any is worth amending: `2026-07-31_PLAN_reset_and_restructure.md:435`,
`archive\2026-09-05_REPORT_claude_code_review_root.md:215-216`,
`2026-09-06_HANDOVER_consultant_session_15.md:109`,
`archive\2026-07-29_HANDOVER_consultant_chat_3.md:127`, and the brief itself. The handover's line 109
is the one that says they are loose in the root, so it is now out of date in the way that fixes
itself.

**One thing I noticed and did not act on.** `2026-07-31_PLAN_reset_and_restructure.md:435` records
that `Receipt Inbox\TEST\Processed\` in the practice root holds files of these two names. If those are
the same images, the repository copies are a second copy of a fixture that also lives in OneDrive. I
have not looked in the practice root and I am not claiming they are the same files.

## Change 5. Twenty-two spent files moved to `archive\`

**The brief's list is exactly right: 22 names, all 22 present in the root, none already in
`archive\`.** Checked before moving anything, and the mover refuses as a batch rather than discovering
a clash half way through.

**The link check, printed whole rather than counted.** 258 files searched under the repository,
excluding `.git`, `.history`, `Backups`, `__pycache__` and `.venv`, over `.md`, `.py`, `.html`,
`.bat`, `.json`, `.txt` and `.csv`. Two questions kept separate, because they have different
consequences:

- **Path-like references, which a move would break**: a markdown link of the form `](name)`, or the
  name with a directory separator in front of it. **None. Not one, for any of the 22.**
- **Bare filename mentions in prose, which a move does not break**: many, and they are listed per file
  in the check's output. Six are in Python docstrings, at `app.py:665`, `:670` and `:760`,
  `tests/test_pipeline_lock.py:10`, `:17` and `:207`, `tests/test_layer5_context.py:3` and
  `tests/test_receipt_accounts.py:3`. **I read all eight of those lines rather than trusting the
  classifier**: every one is a citation inside a docstring or comment, naming a report or brief as
  provenance. None is an `open()`.

All 22 moved with `git mv`, all recorded as `R100`.

**`2026-09-06_HANDOVER_consultant_session_15.md` stays in the root**, as instructed, and is present.

**`PROMPT_intellibooks_desktop_changes.md` stays in the root, and the brief was right to leave it.**
CLAUDE.md's rule on spent files names this file explicitly: "A standing brief is not spent however old
it is. `PROMPT_intellibooks_desktop_changes.md` is the brief the IntelliBooks Desktop session works
from and it stays in the root." So it is not a guess either way; it is written down.

**The root holds 20 markdown files with this report in it**, against 41 before the moves, and they are:
`2026-07-25_CONSOLE_DESIGN.md`, `2026-07-31_PLAN_reset_and_restructure.md`,
`2026-08-03_NOTE_chart_of_accounts_for_paul.md`, `2026-08-18_BOUNDARY_two_products.md`,
`2026-08-18_INSTRUCTION_coa_authority.md`, `2026-08-20_LIST_outstanding_items_and_decisions.md`,
`2026-08-20_LIST_settings_firm_and_client.md`, `2026-08-20_NOTE_demo_version.md`,
`2026-09-01_DESIGN_cloud_multi_firm.md`, `2026-09-05_DESIGN_receipt_accounts.md`,
`2026-09-06_HANDOVER_consultant_session_15.md`, `CATEGORISATION.md`, `CLAUDE.md`,
`EMAIL_PROCESSING_MICROSTEPS.md`, `MULTIFIRM_EMAIL_FORWARDING_ANALYSIS_AND_FINDINGS.md`,
`PAUL_CHECKS_2026-07-30.md`, `PROMPT_intellibooks_desktop_changes.md`,
`RECEIPT_CAPTURE_GUIDE.md`, this report, and
`PROMPT_claude_code_2026-09-07_smtp_required_and_housekeeping.md`, which becomes spent on
delivery of this report. **Counted with `ls *.md | wc -l` rather than by adding up the list.**

**Four of those are candidates for the same treatment and I am flagging rather than moving them**, in
section 9.

## 6. The suite

```
$ .\.venv\Scripts\python.exe -m pytest -q      (before, at 568b378)
569 passed, 344 subtests passed in 20.47s

$ .\.venv\Scripts\python.exe -m pytest -q      (after all five changes)
579 passed, 358 subtests passed in 28.96s
```

**Ten tests and fourteen subtests more, all from `tests/test_required_smtp.py`**, and every existing
test still passes with none adjusted. The arithmetic: 569 + 10 = 579 and 344 + 14 = 358.

**Run four times in between**, after change 1, after changes 2 and 3, after change 4 and after change
5, all green.

## 7. Where the brief was right, and the one place it was not

**Right, and checked rather than taken:** the four `os.environ.get` lines and their exact defaults;
`.env` setting only `SMTP_PASSWORD`; `.env.example` having no SMTP section; `SMTP_USERNAME` appearing
in the body of the unknown-sender reply, which is `worker/email/alerts.py:92`; the two docstring lists
disagreeing on the fifth constant and the test being the one that is right; both images being tracked
and not gitignored; all 22 archive candidates existing in the root; and the two files to leave alone.

**Not right, in one place:** the acquire in change 2 is 94 lines above the release, not several
hundred. Section 2.

## 8. Commits, and the one I got wrong

Six, in order:

| Commit | Change |
| --- | --- |
| `19f2a5a` | Change 1, the SMTP settings, plus `.env.example` and the new test file |
| `aa35041` | Change 2, the `app.py` comment |
| `24a5591` | Change 3, the `live_paths.py` docstring |
| `03c7a67` | Change 4, the two images |
| `a562e9f` | Change 5, the twenty-two files |
| `1a3895f` | The consultant session's two documents, committed untouched |

**What went wrong and how it was put right.** `git mv` stages its own moves, so by the time I came to
commit change 2 the index already held the image moves and all 22 archive moves. `git add app.py &&
git commit` commits everything staged, not only what was just added, so change 2's commit swallowed
changes 4 and 5. I noticed when the follow-up `git commit -- <old image paths>` failed with
`pathspec ... did not match any file(s) known to git`, because those paths no longer existed.

Both commits were local and unpushed. I recorded the resulting tree hash, did a **mixed** reset back
to `19f2a5a`, which unstages without touching the working tree, and re-committed in four with explicit
path lists. **Then compared the tree hash**: `b6e6aae67a18b0f4a7bb062970ce25ae2e01edf1` before and
after, identical, so the five commits contain exactly what the two contained and nothing was lost or
added. Both rename commits still show `R100`.

**The habit that would have avoided it is `git commit -- <paths>` or staging nothing until the moment
of committing**, and the reason it matters here is that the brief's whole instruction about commits was
about separating them.

**The sixth commit is not mine.** `2026-07-25_CONSOLE_DESIGN.md` and
`2026-08-20_LIST_outstanding_items_and_decisions.md` were clean when I started, at `568b378`, and
appeared modified partway through: v2.12 with amendments 251 to 255, and items 171 and 172 raised.
Committed untouched, in their own commit, so nothing of the consultant session's is mixed into this
brief's diff. **Not read beyond the diff summary needed to write the commit message.**

**Nothing is pushed.**

## 9. Flags

**Nothing here was fixed.**

1. **`.env.example`'s IMAP block carries the real values, not placeholders.**
   `IMAP_HOST=mail.lastingimpact.co.uk` and `IMAP_USERNAME=capture@lastingimpact.co.uk`. It is a
   different thing from a default in the source, because nobody's code reads `.env.example`, but it is
   the same information in the same repository and the SMTP block I added deliberately uses
   `mail.<your-domain>` and `alerts@<your-domain>` instead. **The two blocks now disagree in style**,
   which is a reason to decide rather than to leave.
2. **`.env.example`'s `RESOLUTIONS_DIR` comment names the wrong folder.** It says "Leave blank to use
   `IntelliBooks\Resolutions` under the practice root". `config.py` falls back to
   `INTELLIBILLS_ROOT / "Resolutions"`, which is `Intellibills\Resolutions`. `IntelliBooks\` is the
   other product's folder, which amendment 72 emptied of ours, so the comment points a new
   installation at the folder this project spent a step moving out of.
3. **Four more files in the root look spent by the same convention**, and I have not touched them
   because the brief listed 22 and these are not among them.
   `2026-07-31_PLAN_reset_and_restructure.md` describes a reset that happened;
   `PAUL_CHECKS_2026-07-30.md` is a checklist for one day in July;
   `EMAIL_PROCESSING_MICROSTEPS.md` and `MULTIFIRM_EMAIL_FORWARDING_ANALYSIS_AND_FINDINGS.md` both
   predate the module split. **Each is a judgement about whether its content is carried elsewhere,
   which is yours and not mine.**
4. **A fixture may exist twice.** Section 4's last paragraph:
   `2026-07-31_PLAN_reset_and_restructure.md:435` says `Receipt Inbox\TEST\Processed\` in the practice
   root holds files with the same two names as the images just moved. Unverified; I did not look
   outside the repository.
5. **`app.py:775`'s citation is now moot but the class of thing is not.** The comment change in this
   brief is the third amendment-247 correction in three days, in `config.py`, `live_paths.py` and now
   `app.py`. **A grep for `\.py:[0-9]` across the live `.py` files would find the rest in one pass**,
   and nobody has run it.
6. **The design document and the outstanding items list moved under me while I worked.** Not a
   defect, and worth knowing for the two-session arrangement: I read `config.py`, `.env`,
   `.env.example`, `app.py`, `tests/live_paths.py` and `tests/test_required_roots.py` at the start of
   the session, and the two documents changed after that. **Nothing I did depended on their content**,
   but a brief that told me to read one of them would have had me reading a version that no longer
   existed by the time I finished.

## 10. Confidence

**High that the four settings are required and that the messages name the right variable**, resting on
eight child-process cases driven with `dotenv` stubbed out, printed in section 1, and on the mutation
reddening 19 assertions in the new test file and nothing else. Not on reading the code back alone.

**High that this machine's behaviour is unchanged**, resting on importing `config` with `.env` in
place and reading all four values back, and on the three added values being copied from the literals
in the same edit that deleted them.

**High that nothing in the repository opens any of the 24 moved files by name**, resting on a search
over 258 files that separates path-like references from prose, on reading all eight Python-file
mentions individually, and on a grep for `open(` against the three filename patterns. **The limit is
that it covers this repository only.** `IntelliBooks-Desktop-v3.html` is in OneDrive and I have not
read it; if anything there names a report by path, this search could not see it.

**High that the two commits were separated without loss**, and this one does not rest on judgement at
all: the tree hash is identical before and after, `b6e6aae67a18b0f4a7bb062970ce25ae2e01edf1`.

**High that `tests/live_paths.py` needed no SMTP change**, resting on the suite passing and on the
distinction in section 1: it sets the root variables because it redirects them, and the SMTP settings
have nowhere to be redirected to.

**Medium that including `SMTP_PASSWORD` breaks nothing beyond import.** The empty-string case is
tested and `.env` sets it, so the suite and this machine are covered. **What I have not done is send an
alert**, which would cost nothing but needs a real receipt from an unknown sender, so the send path
itself is unexercised in this session. `worker/email/alerts.py` reads the constant and I did not change
how it reads it.

**Low on whether the four files in flag 3 are genuinely spent**, and that is why they are flagged
rather than moved. I read their names and their opening lines, not their content.
