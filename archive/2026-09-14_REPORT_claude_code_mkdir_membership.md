# Report, Claude Code, 2026-09-16: the mkdir block's membership is asserted

Written against `PROMPT_claude_code_2026-09-14_mkdir_membership.md`, Paul's decision of
2026-09-14 taking flag 8.4 of `2026-09-12_REPORT_claude_code_exports_dir.md`.

**Built, tested and not committed.** The commit is proposed in section 7.

**Times are BST, read from Python's `zoneinfo`.** Written 2026-09-16.

---

## 1. The set, printed whole

Read from `config.py`'s syntax tree on 2026-09-16, module scope only:

```
module-scope mkdir calls: 7
  line  917  INTELLIBILLS_ROOT            {'parents': True, 'exist_ok': True}
  line  918  FILES_DIR                    {'parents': True, 'exist_ok': True}
  line  919  BACKUPS_ROOT                 {'parents': True, 'exist_ok': True}
  line  920  DB_PATH.parent               {'parents': True, 'exist_ok': True}
  line  921  LOGS_DIR                     {'parents': True, 'exist_ok': True}
  line  931  INTELLIBOOKS_PUBLISH_DIR     {'parents': True, 'exist_ok': True}
  line  936  EXPORTS_DIR                  {'parents': True, 'exist_ok': True}
```

**Seven.** The test names all seven and counts none of them.

`DB_PATH.parent` is an attribute rather than a constant, because the constant is the
database file and the block creates the folder holding it. It is asserted in that form,
as the expression the call is made on.

---

## 2. Seven, and the brief said six

**The brief's correction was right to tell me to read the block, and wrong about why.**
It says
`PROMPT_claude_code_2026-09-15_publish_the_address_not_the_picture.md` "removes the line
that created `IntelliBooks\Incoming\`". **It removes no line.** It re-points
`INTELLIBOOKS_PUBLISH_DIR` from `INTELLIBOOKS_ROOT` to `INTELLIBILLS_ROOT`, so the same
`mkdir` line now creates `Intellibills\Incoming\` and the membership of the block is
untouched.

**So the set was not six before my commit either.** Counted from the syntax tree at four
commits rather than reasoned about:

```
     ae336b9: 7   (the publish commit)
   ae336b9~1: 7
     48090d0: 7
     52cc007: 7
```

**What actually moved it**, enumerated across the last twelve commits that touched
`config.py`:

```
7  ae336b9 2026-09-16 fix(publish): the item carries the document's address, not the docume
7  64878e1 2026-09-15 docs: strike four incorrect statements about the boundary rules, amen
7  ce520f7 2026-09-14 feat(config): exports leave the repository for Intellibills\Exports\
6  f9f81ec 2026-09-14 feat(client-copy): write a per-client delivery log on every document
6  476df39 2026-09-13 refactor(config): remove the RESOLUTIONS_DIR environment override
...
6  8762250 2026-09-09 feat(config): the publish destination is a firm setting with no defau
5  956b896 2026-09-07 fix(config): the shared refusal message is true of all eight settings
```

**Five until `8762250` on 2026-09-09, six until `ce520f7` on 2026-09-14, seven since.**
`ce520f7` is step 10r, which landed the same day the brief was written, so "the six as
they stand today" was stale on the day and for a reason nobody had connected to it.

**This is the exercise working rather than a complaint about the brief.** The instruction
was to read the block and not to take a number, and reading it is what found this.

### Four other counts were circulating at the same time

Enumerated with a grep across the repository, `.history\` excluded:

| Where | Says |
|---|---|
| `config.py`, `_required_root`'s own docstring | "builds five directories from these two roots" |
| `2026-07-25_CONSOLE_DESIGN.md`, amendment 287 | "one of the six mkdir targets" |
| `2026-07-25_BUILD_STATUS.md`, step 10f.4's row | "one of the six mkdir targets" |
| `2026-09-09_HANDOVER_consultant_session_19.md` | "one of six mkdir targets" |

**None of them was wrong when written and all of them are wrong now.** That is what a
count does and a list does not, and it is the case for this test made by the block
itself rather than argued.

**A fifth, in amendment 184, is a correction of the same fault**: "six mkdir paths where
there are five", written 2026-09-03 when the answer was five.

**None of the four is corrected in this commit.** Section 8.1 flags them.

---

## 3. What was built

**A sibling class, `MkdirMembershipTest`, in `tests/test_client_top_folder.py`**, beside
`test_every_refusal_sits_above_every_mkdir`, which is unchanged. Two tests over one
block, each with one job: one asks whether every refusal precedes every `mkdir`, the
other asks which folders it makes.

**Two methods.** `test_the_block_creates_exactly_these_folders` compares the block
against a written-out list. `test_the_block_is_read_rather_than_this_list_being_trusted`
is the control: it asserts the reader found something, that `INTELLIBILLS_ROOT` is among
it, and that nothing appears twice, so the comparison cannot pass by the parser having
broken.

### Three choices inside it

**Sorted rather than ordered.** Every call passes `parents=True`, so a parent listed
after its child still works and the order inside the block is not load-bearing. Pinning
it would make a harmless reorder fail for a non-reason. **Mutation 4 proves the test
means this** rather than merely saying it.

**Sorted lists rather than sets.** A set comparison hides a line duplicated, which the
control also tests for directly.

**Module scope only.** A `mkdir` inside a function is not this block: `acquire_lock()`
calls one on the lock file's parent and it is not an import-time folder. Read off the
tree rather than off a grep, because `config.py` carries four comments mentioning
`mkdir` and a text search reads every one of them.

---

## 4. Red before green, and what "red" means for a test like this

**This test passed on its first run, and that is a property of what it is rather than a
failure to write it first.** It records what `config.py` holds, so against the code it
was written from it can only pass. A first run that was red would have meant the list
was typed wrong.

**So the red is the control the brief asks for, in both directions**, and
`CLAUDE.md` names this case exactly: where a test cannot come first, mutate the behaviour
from a pristine copy and show which tests catch each mutation.

**The failing output, with one `mkdir` line removed by hand from a copy and restored
afterwards:**

```
E       AssertionError: Lists differ: ['BAC[26 chars]t', 'FILES_DIR', 'INTELLIBILLS_ROOT', 'INTELLI[26 chars]DIR'] != ['BAC[26 chars]t', 'EXPORTS_DIR', 'FILES_DIR', 'INTELLIBILLS_[41 chars]DIR']

E         ['BACKUPS_ROOT',
E          'DB_PATH.parent',
E       +  'EXPORTS_DIR',
E          'FILES_DIR',
E          'INTELLIBILLS_ROOT',
E          'INTELLIBOOKS_PUBLISH_DIR',
E          'LOGS_DIR'] : config.py's import-time mkdir block does not create what this
test says it creates. If a folder was added, add it to EXPECTED and say in the commit why
it is created at import. If one was removed, check nothing depends on it existing before
first use: the whole point of this test is that removing a line used to leave the suite
green.

1 failed, 1 passed in 0.10s
```

**The message names the folder and says what to do about it in both directions**, which
is what a reader hitting this in six months needs. The control passed in the same run,
which is what "1 passed" is.

`config.py` was copied first, restored afterwards and md5 compared:
`ca78ae2185ca47a3295a510d4bfcc2e9` before and after, and `git status config.py` clean.

---

## 5. Mutations

Five, through `tests/mutation_harness.py`. Every anchor `str.count()` asserted at 1
before anything was written, every diff printed, every file restored byte for byte, each
measured against the whole suite.

| # | Mutation | Expect | Result | Caught by |
|---|---|---|---|---|
| 1 | `mkdir-line-removed` | caught | **caught** | 1 |
| 2 | `mkdir-line-added` | caught | **caught** | 1 |
| 3 | `mkdir-line-swapped` | caught | **caught** | 1 |
| 4 | `mkdir-lines-reordered` | **survives** | **survived** | 0 |
| 5 | `prose-only` | **survives** | **survived** | 0 |

**Mutation 1 is the one this whole commit exists for.** It is the mutation flag 8.4
found uncaught on 2026-09-12, when removing a `mkdir` line left all 1458 tests green. It
now fails `MkdirMembershipTest::test_the_block_creates_exactly_these_folders` and
nothing else.

**Mutations 1 and 2 are the two directions the brief asks for**, a line removed and a
line added.

**Mutation 3 is the reason the brief says name them rather than count them.**
`EXPORTS_DIR` is swapped for `CHARTS_DIR`, so the count is unchanged at seven. **A
count-based test passes this.** The list does not.

**Mutation 4 had to survive and did.** Two lines reordered, suite unchanged at 1493. A
failure there would have meant the test was pinning the order after saying it would not.

**Mutation 5 confirms no guard reads prose.** A comment in `config.py` mentioning
`mkdir` was reworded and the suite stayed at 1493.

**Each of the three caught mutations is caught by exactly one test**, which is the right
number: this is the only test that asks the question, and that is the gap being closed.

Full harness output, five blocks with diffs, in
`C:\Users\PDK7\AppData\Local\Temp\claude\c--LastingImpact-receipt-capture\1d19c2e5-bffa-4afe-a492-3e0c9fabb139\scratchpad\mutations_mkdir.txt`.

---

## 6. The suite

| When | Result |
|---|---|
| Before, at `ae336b9` | `1491 passed, 1 skipped, 1137 subtests passed` |
| After | `1493 passed, 1 skipped, 1137 subtests passed in 127.13s` |

**+2 tests**, the membership test and its control. No new subtests and no new file.

**No file is added**, so the `git ls-files` source guards see nothing new and the
post-commit run has no blind spot to cover. It will be run anyway if you want it.

---

## 7. The proposed commit

```
test(config): the mkdir block's membership is asserted, not just its order

Paul's decision, 2026-09-14, on flag 8.4 of
2026-09-12_REPORT_claude_code_exports_dir.md. Nothing held which folders
config.py creates at import: the only test reading that block asserts that
every refusal precedes every mkdir, and it passes with any number of lines in
it. Removing a mkdir line left all 1458 tests green.

MkdirMembershipTest in tests/test_client_top_folder.py names the seven folders
the block creates, read from config.py's syntax tree at module scope. The
ordering test is unchanged: two tests over one block, each with one job.

Named rather than counted, because a count passes when one folder is swapped
for another and goes stale silently. It had: the brief for this test said six
and the answer was already seven, step 10r having added EXPORTS_DIR the same
day it was written. Four other stale counts are flagged in the report and not
corrected here.

Sorted rather than ordered, because every call passes parents=True so the order
inside the block is not load-bearing; sorted lists rather than sets, so a
duplicated line cannot hide. A control asserts the reader works independently of
what it finds.

Five mutations: a line removed, a line added and one folder swapped for another
are each caught by this test and nothing else; a reorder and a comment change
each survive.

Files: tests/test_client_top_folder.py
Suggested branch: feat/console-phase0 (the current branch)

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

```
 tests/test_client_top_folder.py | 116 +++++++++++++++++++++
 1 file changed, 116 insertions(+)
```

**Not done:** nothing committed, nothing pushed. No folder added to or removed from the
block, which section 8 flags instead. No change to `config.py`.

---

## 8. Flags

Each reported and left alone, with the fix named.

### 8.1 Five stale counts of this block, one of them inside `config.py`

Section 2 has the table. The one that matters most is **`config.py`'s own
`_required_root` docstring**, which says the block "builds five directories from these
two roots" and is read by anybody working out why the roots are required.

**The obvious fix, and it is the one this commit's own subject argues for: say what the
block is for rather than how many lines it has.** "The mkdir block below builds the
folders this module's constants name" carries the same meaning and cannot go stale. The
same wording works for the three document occurrences, except that the two in the
amendment record are dated history and stay as written, per this project's rule.

**Not done here** because the brief is one test and `config.py` is not in this commit.
It is four short edits across three files and I would take them in one pass.

### 8.2 The block's keyword arguments are not asserted

Every call passes `parents=True, exist_ok=True`, and nothing holds that.
`exist_ok=False` would raise on the second start of the pipeline, and `parents=False`
would raise on a fresh machine. **Neither is caught by anything**, including the new
test, which reads only what each call is made on.

**The obvious fix is four lines in the same class**: assert both keywords on every call
in `mkdir_targets()`. **Not done because the brief says one job per test and names the
job as membership**, and because it is a different question from which folders are
created. **I would add it** as a third method next time this file is open.

### 8.3 `CHARTS_DIR` is deliberately not in the block, and nothing says so where it matters

`config.py` carries a comment above `CHARTS_DIR` saying an absent folder "is a fault to
report rather than one to paper over with a mkdir", which is the decision. **The new
test records that `CHARTS_DIR` is absent only by not listing it**, which reads as an
omission rather than as a decision to a stranger.

**The obvious fix: name it in the test's `EXPECTED` comment as the one constant
deliberately excluded, with the reason.** One sentence. **Not done because the brief says
the set records what is there rather than what should be**, and a list of what is
deliberately absent is the start of the second thing. Flagged because mutation 2 used
`CHARTS_DIR` as its added line, which is exactly the folder somebody would add in good
faith.

---

## 9. My own mistakes

### 9.1 I ran the membership test before I had a way for it to fail

I wrote the test, ran it, got green, and only then built the controls. **That ordering is
the right one for this kind of test, and I did not establish that it was before relying
on it.** The reasoning in section 4 was written afterwards. It happens to hold: a test
that records existing state cannot be red first unless it is wrong, and the brief
anticipated this by asking for the control rather than for a red first run.

### 9.2 I stated a clock time I had not read, the day after disclosing the same fault

The reply sent while the mutations were running opened `2026-09-16 10:47 BST`. **I did
not read the clock for it.** The last reading I had taken was 10:31, and I put a
plausible number on the reply instead of reading again.

**Measured afterwards rather than estimated**, from file modification times: the mutation
script was written at **10:34** and its output landed at **10:43**, so that reply was
composed at about 10:35 and the stated time was roughly twelve minutes ahead.

**This is the same fault I disclosed in section 7.1 of
`2026-09-14_REPORT_claude_code_two_year_flags.md` yesterday**, where two invented times
were struck and replaced with times sourced from file stamps. Disclosing it once did not
stop it. `CLAUDE.md` states the rule in as many words: state the date from a file, not
from a session header, and re-check it if the session is long. **The habit that fixes it
is reading the clock in the same tool call that produces the reply's other facts**, which
is what the header of this report was written from.

### 9.3 Nothing else

The two claims I made in that reply about the work itself, that the set is seven and that
my publish commit did not move it, are both in section 2 with the measurements behind
them.

---

## 10. Confidence

**High that the block creates exactly those seven folders**, resting on a syntax-tree
read of `config.py` at module scope printed whole in section 1, and on mutations 1, 2 and
3 each being caught when the set is changed in a different way.

**High that the test does not pin the order**, resting on mutation 4 surviving with the
suite unchanged at 1493 rather than on the test's own docstring saying so.

**High that this closes flag 8.4.** It rests on mutation 1 being the same mutation that
report measured as uncaught, run again and now caught, rather than on the two being
described as the same.

**High that the counts in section 2 are right.** They were computed by walking each
revision's `config.py` with `ast` and printing the targets, rather than by reading the
prose that states them.

**Medium that the four stale counts in section 2 are all of them.** It rests on a grep
for four phrasings across the repository with `.history\` excluded, and **a count stated
in words I did not think to grep for would not appear**. The four found are enough to
make the argument; the claim that they are the complete set is the weaker half.

**Low, and flagged as speculation, on whether the block should hold seven folders.** That
is Paul's decision and the brief says this test records what is there. I have not
assessed whether any of the seven should be created at import, beyond noting in 8.3 that
`CHARTS_DIR`'s exclusion is already a recorded decision.

---

## 11. Flag 8.1 taken, 2026-09-16, and it was worse than I reported

**Paul's instruction after reading this report: take 8.1, leave 8.2 and 8.3.** Say what
the block is for rather than how many lines it has. This section is that work, in a
second commit; the test above is `5bcfbe4` and is already in.

### 11.1 I under-counted the stale counts, in a flag about stale counts

**Section 2 said five occurrences. There are seven.** Enumerated properly this time,
with a regex over every tracked `.py` and `.md` file rather than the four phrasings I
happened to grep for:

| Where | Says | Live or history |
|---|---|---|
| `config.py`, `_required_root`'s docstring | five directories | **live** |
| `CLAUDE.md`, the fourth trap | one of the six mkdir targets | **live** |
| `2026-07-25_BUILD_STATUS.md:419`, step 10f.4 | one of the six mkdir targets | history, a dated BUILT row naming `8762250` |
| `2026-07-25_CONSOLE_DESIGN.md:566`, amendment 184 | six mkdir paths where there are five | history, dated amendment |
| `2026-07-25_CONSOLE_DESIGN.md:1144`, amendment 287 | one of the six mkdir targets | history, dated amendment |
| `2026-09-09_HANDOVER_consultant_session_19.md:61` | one of six mkdir targets | history, spent handover |
| `2026-09-09_REPORT_claude_code_stage1_piece3_publish.md:352` | four mkdir targets | history, delivered report |

**The two I missed are the two that make the point best**: `CLAUDE.md`'s is in the
standing trap list every new session reads, and the report's "four mkdir targets" is a
sixth different number for the same block.

**This is the enumerate-the-set rule broken inside a flag whose whole subject is counts
going stale.** Section 10's own confidence line predicted it: "Medium that the four stale
counts are all of them... a count stated in words I did not think to grep for would not
appear." It did not appear, and there were two of them.

### 11.2 Two edits, not four, and why

Paul said four short edits, taking the number from section 8.1 of this report. **Section
8.1 was wrong about that as well.** Only two of the seven are live text:

- **`config.py`'s `_required_root` docstring.** Now reads "builds the folders this
  module's constants name, from these two roots, at import", with the old clause struck
  and the history of the count recorded beside it.
- **`CLAUDE.md`'s fourth trap.** Section 11.3.

**The other five stay, and that is this project's own rule rather than a shortcut.**
Amendment 82's rule, cited in amendment 184's own row: history keeps its old values. Two
dated amendment rows, a dated BUILT row naming its commit, a spent handover and a
delivered report are all records of what was true when written. Editing them would
rewrite the trail this project keeps deliberately. **A count in a dated record is not
stale; it is dated.**

**The number four came from my own report and I have not manufactured two more edits to
meet it.**

### 11.3 The `CLAUDE.md` sentence was wrong twice over, and the second half matters more

It read: "the folder is kept because `INTELLIBOOKS_PUBLISH_DIR` is one of the six mkdir
targets and the next pipeline start would make it anyway."

**The count is the small half.** The large half is that **the reason has gone**. Commit
`ae336b9` re-pointed `INTELLIBOOKS_PUBLISH_DIR` at `Intellibills\Incoming\`, per section
20.6 item 6, so the next pipeline start makes that folder and **no longer makes
`IntelliBooks\Incoming\` at all**.

**So the folder is orphaned rather than kept.** It is still on disk, checked on
2026-09-16, and section 20.1 says it is to be deleted. **Deleting it is Paul's**, as the
publish brief already said.

The sentence is struck rather than replaced, with both corrections beside it, per the
convention that file itself uses throughout.

**This was found by fixing a count.** Correcting the number meant reading the sentence
the number was in, and the sentence had stopped being true for a different reason
altogether. That is the argument for taking small corrections rather than listing them.

### 11.4 The suite, and what remains

`1493 passed, 1 skipped, 1137 subtests passed in 117.38s`, unchanged by these edits,
which touch a docstring and a markdown file.

Re-enumerated afterwards: the two live statements are corrected and the only remaining
matches in those two files are **my own struck quotations of the superseded wording**,
which is the convention rather than an oversight. The five historical occurrences are
untouched.

### 11.5 The proposed second commit

```
docs(config): say what the mkdir block is for, not how many lines it has

Paul's instruction, 2026-09-16, taking flag 8.1 of
2026-09-14_REPORT_claude_code_mkdir_membership.md. The same fault as a count
asserted about a set, in the prose about the set this repository had just
started naming.

config.py's _required_root docstring said the block "builds five directories".
It held five until 2026-09-09, six until 2026-09-14 and seven after. It now
says what the block is for and points at MkdirMembershipTest for the list.

CLAUDE.md's fourth trap said IntelliBooks\Incoming\ is kept because
INTELLIBOOKS_PUBLISH_DIR is one of the six mkdir targets and the next start
would make it anyway. Wrong twice: the count, and the reason. ae336b9
re-pointed that constant at Intellibills\Incoming\, so nothing creates
IntelliBooks\Incoming\ any more. The folder is orphaned rather than kept, it
is still on disk, and section 20.1 says it is to be deleted. Deleting it is
Paul's and is not in this commit.

Five further occurrences are left as written: two dated amendment rows, a dated
BUILT row, a spent handover and a delivered report. Amendment 82's rule, history
keeps its old values. A count in a dated record is dated rather than stale.

Files: config.py, CLAUDE.md
Suggested branch: feat/console-phase0 (the current branch)

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
```

**Not done:** `IntelliBooks\Incoming\` is not deleted. 8.2 and 8.3 left, per Paul.
