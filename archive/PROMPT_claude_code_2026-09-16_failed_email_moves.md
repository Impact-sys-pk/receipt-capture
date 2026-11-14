# Claude Code brief, 2026-09-16: a failed email move stops being silent

Written by the consultant session, 2026-09-16, 18:15 BST. From your own flag in
`2026-09-16_REPORT_claude_code_inbox_pair_moves.md`, and from what the consultant session found
checking it. **Both decided by Paul, 2026-09-16.**

**Report to `2026-09-16_REPORT_claude_code_failed_email_moves.md` in the repository root.**

**One commit. Build it, propose the commit, and wait for a yes.**

---

## Two rules about this brief

**1. `2026-07-25_BUILD_STATUS.md` is not yours to edit.** You report; the consultant session verifies
and marks it.

**2. Your flag was right and checking it turned up a second thing.** That second thing is deliverable
two, and it is the reason the first one was invisible.

---

## Deliverable one: the stranded email is retried

**Your flag, verified in `app.py` on Paul's machine.** An email with no attachments gets its alert,
`record_alert_sent()` writes the row, and then the move to `INBOX.No Attachments` is attempted. **If
that move fails the email stays in INBOX**, and on every run afterwards the already-alerted check
passes over it before the move is reached. Never re-alerted, which is right. Never re-moved, which is
not.

**Paul's decision: retry it.** The email is passed over only after the move has been attempted again.

**Why the retry cannot misfire**, and this is the part worth holding with a test: `move_email_to_folder()`
copies, flags `\Deleted` and expunges, so a second move of a uid that already moved cannot succeed.
Only an email still in INBOX can be retried, which is exactly the failed case.

**The cost Paul accepted rather than discovered:** a move that keeps failing, say because the folder
has been renamed, retries on every run and logs every time. Noisier than silence, and silence is what
produced a stranded email nobody knew about.

## Deliverable two: the five call sites read the result

**`move_email_to_folder()` already returns a bool**, documented as "True if move succeeded, False if
failed (logs warning, does not raise)". It is honest. **Its callers are not listening.**

**Five call sites, enumerated from the syntax tree across every production `.py` file in the
repository, and every one discards the result as a bare expression statement:** `app.py` lines 1555,
1712, 1738, 2045 and 2184. The consultant session said six before enumerating and was wrong; five is
the count from the tree.

**What has to be true: a run knows how many of its moves failed, and that number leaves the run.**
The function already logs each failure, so what is missing is the run's own account of itself.

**The mechanism is yours.** `stats` already carries counters of this kind in the same loop.
**Whatever you choose, it must be one mechanism at all five sites and not five**, for the reason your
own report gave about the statement branch: five explicit treatments are correct today and silently
wrong at the sixth call site.

## What must not change

- **`move_email_to_folder()` itself.** It returns the right thing and logs the right thing. This
  brief is about the callers.
- **The already-alerted check.** An email gets one alert. Deliverable one moves where it is tested,
  not whether it is tested.
- **Which folder each call site targets.**

## Evidence

The standard in `CLAUDE.md` applies in full. Four parts this change makes specific:

- **Red before green.** For deliverable one, a test where the first move fails and the second run
  reaches the move again. **The stub must model the real function**, per `CLAUDE.md`'s rule of
  2026-09-08: a recording stub that reports success on every call hides exactly this defect and
  reports the fix as broken. It has to refuse a second move of a uid that already moved.
- **A guard over the set**, for deliverable two. Assert on the source that no call to
  `move_email_to_folder()` remains a bare expression statement, and that the count of handled calls
  is what you expect. **A per-site test proves a site works; only a guard over the set proves the set
  is complete**, and it is what catches the sixth call site added without it.
- **The guard parses the syntax tree**, not the text. This file keeps superseded wording beside every
  correction and there are tombstone comments naming this function.
- **Mutations**, each anchored, asserted unique, diff printed. At minimum: remove the retry, and
  restore a bare call at one site.

Run the suite again after the commit if this adds a file.

## What to report

Everything the standard asks, plus:

1. The mechanism you chose for deliverable two and how you held it to one.
2. Whether the count is five, from your own enumeration rather than from this brief.
3. What a failed move now causes, in one sentence a person could act on.
