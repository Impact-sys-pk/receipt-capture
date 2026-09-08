# Report: the embedded path logs its unknown sender, and the `.env.example` housekeeping

**Written 2026-09-08, 12:55 BST (11:55 UTC), by the implementation session in Claude Code.**
**Branch `feat/console-phase0`.**
**Brief: `PROMPT_claude_code_2026-09-08_embedded_unknown_sender_event.md`.**

**Both done. Two commits, `45f859f` for the housekeeping and `a6cd480` for the event, neither
pushed.** The housekeeping went first so the two are separable in either direction.

**One thing in this change was not a copy and it is section 4: the firm id.** Passing the obvious
value would have put a stranger's event into a real firm's log.

---

## 1. The suite

| When | Result |
|---|---|
| Before, the committed tree at `259ce43` | **689 passed, 518 subtests** |
| After both commits, at `a6cd480` | **694 passed, 522 subtests** |

**Both measured, at 12:45 and 12:53 BST.** Five new tests and four new subtests.

---

## 2. The two events, side by side

Printed by `test_the_two_paths_write_the_same_event_shape`, which drives one stranger's email down
each path and reads the entry back out of `receipt_events_UNATTRIBUTED.ndjson`. The three values that
are unique per run by design are masked by the test rather than by me.

```
unknown_sender, one event per path, from a stranger:
  email_attachment
      action       'unknown_sender'
      filename     None
      message_id   'msg-att'
      receipt_id   '<receipt_id>'
      run_id       '<run_id>'
      timestamp    '<timestamp>'
  embedded_image
      action       'unknown_sender'
      filename     None
      message_id   'msg-emb'
      receipt_id   '<receipt_id>'
      run_id       '<run_id>'
      timestamp    '<timestamp>'
```

**Same keys, same action, same null filename.** The test asserts the key sets are equal rather than
only checking the fields it prints, so a key appearing on one path and not the other fails even if
nobody thought to look for it.

**`message_id` is deliberately not compared across the two**, and that is a correction to my own
first draft: the driver gives each path its own message, so comparing them was comparing the fixture.
It now asserts each event names the message that produced it. Section 6.

---

## 3. Red before green

Five failures before the change, all in the new class:

```
FAILED ...::BothPathsLogTheSameEventTest::test_the_embedded_path_writes_an_unknown_sender_event
    AssertionError: 0 != 1 : a stranger sending a photo left no trace in the event log
FAILED ...::BothPathsLogTheSameEventTest::test_one_event_per_email_on_the_embedded_path_too
    AssertionError: 0 != 1 : embedded_image wrote 0 unknown_sender events
FAILED ...::BothPathsLogTheSameEventTest::test_the_embedded_event_carries_no_filename
    IndexError: list index out of range
FAILED ...::BothPathsLogTheSameEventTest::test_the_two_paths_write_the_same_event_shape
SUBFAILED(path='embedded_image') ...::test_neither_path_writes_the_event_into_a_real_firms_log
```

**The subtest label is worth noticing**: the firm-id test failed for `embedded_image` and passed for
`email_attachment` in the same run, because the attachment path already wrote its event and the
embedded path wrote nothing at all.

---

## 4. The firm id, which needed establishing rather than copying

**The answer is `config.UNATTRIBUTED_FIRM_ID`, named in the branch, and it is not the same expression
that would have been obvious.**

**Passing the branch's own `firm_id` would have been wrong.** `resolve_client_info()` returns the
default firm constant when it cannot place the sender, read in
`worker/database/repository.py`, so on this branch `firm_id` is `FIRM001`. The event would have
landed in `receipt_events_FIRM001.ndjson`, **a real firm's log**, which is the exact fault amendment
128 created `receipt_events_UNATTRIBUTED.ndjson` to prevent.

**Why the attachment path never had that problem, and why copying it blindly would still have
worked.** That path derives `msg_firm_id` above its loop, which folds the unresolved case into
`UNATTRIBUTED` before anything uses it, and its `_log_receipt()` call then names `UNATTRIBUTED`
explicitly as well, so it is right twice over. **The embedded path derives no `msg_firm_id`**, which
I checked by listing every assignment to a name containing `firm_id` in `app.py`: there are two,
`receipt_firm_id` on the folder-intake path and `msg_firm_id` on the attachment path, and neither is
in scope here.

**Asserted rather than reasoned.** `test_neither_path_writes_the_event_into_a_real_firms_log` drives
both paths and asserts `UNATTRIBUTED` is the **only** event log file that exists afterwards, so a
future edit that reaches for `firm_id` fails on both paths at once. Mutation B is that edit and it is
caught.

---

## 5. The mutations

| # | Mutation | Places | Suite | Caught by |
|---|---|---|---|---|
| A | Drop the embedded event again | 1 hunk, 2 lines | 5 failed, 690 passed | All four behaviour tests plus the firm-id subtest for `embedded_image` |
| B | Pass `firm_id` instead of `UNATTRIBUTED` | 1 hunk, 2 lines | 5 failed, 690 passed | The same five, because the event exists but lands in `FIRM001`'s log |
| C | Log it per image, inside the loop | 2 hunks, 4 lines | 5 failed, 690 passed | The same five |
| D | Put a filename in it | 1 hunk, 2 lines | 2 failed, 693 passed | `test_the_embedded_event_carries_no_filename` and the `filename` subtest of the shape comparison |
| E | Drop the **attachment** path's event instead | 1 hunk, 2 lines | 5 failed, 690 passed | The shape comparison, all three `TheEventIsLoggedOncePerEmailTest`, and the firm-id subtest for `email_attachment` |

All five restored byte for byte, asserted by the harness and confirmed with `git status`.

**Mutation E is there because every other mutation attacks the new path.** A suite that only looked
at the embedded path would let the two diverge the other way, and this is the one that would catch
it.

**Mutation C's anchor was refused on its first run, and that is the third time in two days.** The
`repo.mark_processed(...)` line at the end of the embedded loop is **byte-identical** to the one at
the end of the attachment loop, both at twenty spaces, so `str.count()` saw two. The harness stopped
rather than mutating both loops. Re-anchored on that line plus the comment beneath it, which belongs
to the embedded path alone. **The trap is now well characterised: these two loops are close to
line-for-line copies of one another, so any anchor inside either one has to carry something the other
does not have.**

---

## 6. My own mistakes

**Three, all caught by my own runs.**

1. **I compared `message_id` across the two paths.** The driver gives each its own message, so the
   assertion compared `'msg-att'` with `'msg-emb'` and failed on the fixture rather than on the code.
   The test now asserts each event names its own message, and says in a comment why the
   cross-comparison was wrong.
2. **My comment block landed at the wrong indentation**, sixteen spaces inside a twenty-space branch.
   It compiled, because a comment may sit anywhere, and it read like a block boundary. Re-indented.
3. **My comment named `config.DEFAULT_FIRM_ID` in prose and tripped a source guard.** Flag 1 below.

**And one process note rather than a mistake in the work.** The heredoc I used to add the tests
collapsed `\n` inside a Python string literal into a real newline, producing an unterminated string,
for the third time today. **I have stopped using heredocs for content containing escapes** and used
the editing tools for the rest of this change.

---

## 7. Flags

### Flag 1: a source guard reads prose, and my comment tripped it

`tests/test_default_firm_id.py::NoHardcodedFirmIdTest::test_the_count_is_looking_at_the_right_file`
asserts the string `config.DEFAULT_FIRM_ID` appears nowhere in `app.py`, by plain string search.
**My comment explained why that constant is deliberately not used here, and named it**, so the guard
failed on prose describing the absence of the thing it was looking for.

**I reworked the comment rather than the guard**, to `the DEFAULT_FIRM_ID constant`, which keeps the
precision and does not use the attribute. **The guard's weakness is still there.**

**This is the third instance of one pattern in two days**, and the other two were mine:
`_client_top_folder`'s guard read its own docstring on 2026-09-07, and `_required()`'s guard read the
superseded wording its docstring records. **On this project the prose is always there**, because
superseded wording is kept beside the correction by convention, so a source guard that string-matches
will eventually read an explanation as a use.

**Small and obviously right: parse `app.py` and look for the attribute in the syntax tree**, which
ignores comments and docstrings by construction. Three or four lines, and it is the same shape as the
guards I have written this week. **Say the word.**

### Flag 2: `attachments_processed` and the embedded path

Not new today and not touched by this change, recorded because section 9 of yesterday's report
measured its attachment-path equivalent. The embedded loop increments
`stats["attachments_processed"]` per image, and on a stranger's email that loop is never entered, so
the count is zero. **That is the same behaviour the attachment path now has**, so the two agree.
Raising it only because I measured the one and not the other, and somebody comparing the two reports
would find the gap.

---

## 8. The `.env.example` commit

**Committed as `45f859f`, on its own, and the diff contained only the two changes the brief named.**
Checked before committing rather than taken on trust: two hunks, nothing else.

```
-# IMAP email settings (Krystal.io)
-IMAP_HOST=<the live host>
+# Incoming mail, being the mailbox clients email their receipts to. IMAP_HOST,
+# IMAP_USERNAME and IMAP_PASSWORD are REQUIRED and have no default; IMAP_PORT is
+# the one of the four that defaults, to 993. Placeholders below, in the same
+# style as the outgoing block: this file is a template and the live values
+# belong in .env, which is gitignored.
+IMAP_HOST=mail.<your-domain>
 IMAP_PORT=993
-IMAP_USERNAME=<the live capture address>
+IMAP_USERNAME=capture@<your-domain>
 IMAP_PASSWORD=your-email-password
@@
-# Optional. Leave blank to use IntelliBooks\Resolutions under the practice root.
+# Optional. Leave blank to use Intellibills\Resolutions under the practice root.
```

**The two old values are masked above and were not printed anywhere by me.** What I did instead was
ask the question programmatically: neither old value appears anywhere in the new file, and both new
values contain `<`, so both are placeholders. **The third trap is a live key printed by a session
that thought it had masked it, so the check is one that returns a boolean rather than the string.**

**The result reads correctly against the block three lines below it:**

```
IMAP_HOST=mail.<your-domain>          SMTP_HOST=mail.<your-domain>
IMAP_USERNAME=capture@<your-domain>   SMTP_USERNAME=alerts@<your-domain>
```

**`Intellibills\Resolutions` is right**, confirmed against `config.py`: `RESOLUTIONS_DIR` falls back
to `INTELLIBILLS_ROOT / "Resolutions"`, and `INTELLIBILLS_ROOT` is `PRACTICE_ROOT / "Intellibills"`.

---

## 9. What the brief got wrong

**Nothing.** Its description of the asymmetry matched what I found, the shape it said was settled was
settled, and its warning about the anchoring trap was right and I hit it anyway on the one mutation
where I had not applied it.

**One thing to add.** The brief calls the firm id something to "satisfy yourself about rather than
assume", which reads as a confirmation exercise. **It was the one substantive decision in the
change**: the obvious value is wrong, and passing it produces an event that exists, validates and
goes to the wrong place, which nothing but a test looking at the filename would catch.

---

## 10. Confidence

**High that the two paths now write the same event.** It rests on the side-by-side print produced by
driving each path, on the key-set equality assertion rather than a field-by-field check I chose, and
on five mutations each with its diff, including one that attacks the older path rather than the new
one.

**High that the event goes to the right log**, and it rests on asserting `UNATTRIBUTED` is the only
log file that exists after either path runs, plus mutation B failing when `firm_id` is passed
instead.

**High that the `.env.example` diff was only the two named changes**, and it rests on reading the
whole diff and on a programmatic check that neither old value survives.

**This says nothing about the event log under a real mailbox**, which no test here uses. What is
proved is what `_log_receipt()` writes and where.
