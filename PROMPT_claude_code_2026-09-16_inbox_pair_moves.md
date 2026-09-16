# Claude Code brief, 2026-09-16: the statement branch leaves the inbox pair behind

Written by the consultant session, 2026-09-16, 15:35 BST. From your own finding in
`2026-09-16_REPORT_claude_code_statement_end_to_end.md`, verified by the consultant session against
`app.py` on Paul's machine. **Paul's decision, 2026-09-16: move the pair.**

**Report to `2026-09-16_REPORT_claude_code_inbox_pair_moves.md` in the repository root.**

**One commit. Build it, propose the commit, and wait for a yes.**

---

## Two rules about this brief

**1. `2026-07-25_BUILD_STATUS.md` is not yours to edit.** Do not mark anything built and do not touch
that file. You report; the consultant session verifies and marks it.

**2. This is your finding and it was right.** The consultant session checked it rather than took it:
four `continue` statements leave the statement branch of `app.py`, and you correctly excluded the
duplicate-by-hash one, which calls `_move_inbox_pair_to_processed()` before it goes. The other three
do not.

---

## What is decided

**Every exit from the statement branch leaves the document and its sidecar moved out of the Receipt
Inbox, exactly once.** That is the property. **The mechanism is yours**, because you have just read
this code and the consultant session has not read it whole.

The receipt branch already guarantees the same thing with a `finally`, and its own comment says why
that shape was chosen: the failure branch copies the original into Review first, so the move has to
happen after it, and a `finally` is the only place that covers both branches without repeating the
call.

**Exactly once matters.** The duplicate-by-hash branch already moves the pair explicitly. A `finally`
wrapped round the whole branch without touching that call would move it twice.

## Why it is being fixed

Two of the three never correct themselves. `file_review()` writes a fresh copy on every poll, so an
unresolved client or a sidecar missing its platform or week ending accumulates `-2`, `-3` and
onwards, at 288 polls a day on the five-minute default. You measured that over three polls with a
probe rather than reasoning about it, which is why it is being acted on today.

The third, the success path, self-corrects on the next poll by matching its own hash and taking the
branch that does move the pair. **It is in scope anyway**, because a rule with an exception in it is
the thing that gets forgotten, and because a document sitting in the inbox for five minutes after it
has been filed is a document somebody can pick up and wonder about.

## What Paul considered and decided against

**Leaving the two review branches alone, so the document stays where a person can see it and fix the
sidecar by hand.** Decided against: Review already holds a copy, so nothing is lost, and the pair
moves to `Processed\` inside the same client's inbox folder rather than anywhere obscure. **A folder
filling with 288 copies a day of one bad file is not somewhere anybody can see anything.**

## What must not change

- **The duplicate-by-hash branch's behaviour.** It already moves the pair and counts two stats.
- **What `file_review()` writes.** This brief is about the pair in the inbox, not about Review.
- **The receipt branch.** It is the pattern being matched, not a thing to alter.

## Evidence

The standard in `CLAUDE.md` applies in full. Three parts this change makes specific:

- **Red before green.** A test per branch that fails on today's code by finding the pair still in the
  inbox, and passes after.
- **Exactly once, proved.** A test that the duplicate branch does not move the pair twice. Whatever
  mechanism you choose, this is the assertion that says you chose it correctly.
- **Mutations.** Anchor on something unique, assert the anchor matches exactly once, print the
  unified diff. At minimum: remove the move from each of the three branches in turn, and make the
  duplicate branch move twice.

Run the suite again after the commit if this adds a file.

## What to report

Everything the standard asks, plus:

1. The mechanism you chose and why, and how you held "exactly once".
2. Whether anything outside the statement branch shares the same gap. **Flag it, do not fix it.**
