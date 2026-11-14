# Brief: flag F1, the narrower scope wins at equal priority

Written 2026-11-14 by the consultant session. For Claude Code.

This is small. It is a separate brief rather than a note on the last one because
the last one is reported and closed.

## The decision

**Paul's decision of 2026-11-14 on your flag F1, recorded in amendment 568 of
`2026-07-25_CONSOLE_DESIGN.md`. Read it there rather than from this brief.**

In short: at equal priority the narrower scope wins, and **firm sits above
sector**. His reason for that second part, in the amendment: every client has a
firm and no client has a trade, so firm is the more specific of the two in
practice.

So the order becomes priority, then scope with client first, then oldest first,
then the rule id.

**Priority still overrides everything.** That is decision 6 of amendment 565 and
it does not move: raising a firm rule's priority above a client rule's must
still make the firm rule win.

## What to do

1. **Make the order carry the scope.** You named `get_client_rules()` in your
   report as the one read. Confirm that is still the only place rules are
   ordered before you change it, and say what you found.
2. **Check the publish.** Your report says each client's rules file lists its
   rules **in the order layer 0 tries them**. If that order comes from the same
   query, it follows for free. If it does not, it has to change with it, because
   a file that disagrees with the engine is worse than one that says nothing.
3. **Say what you chose for the ordering itself.** A rank expression in the
   `ORDER BY` and a stored rank column are both defensible and I am not naming
   one.

## Tests

- Equal priority, a client rule and a firm rule, client wins.
- Equal priority, a firm rule and a sector rule, firm wins.
- Equal priority, a client rule and a sector rule, client wins.
- **Priority still overrides scope**: a firm rule at a higher priority beats a
  client rule at a lower one. This is the test that stops the change going too
  far.
- Equal priority and equal scope still resolves oldest first, which is already
  held by `TheOrderTest`; confirm it still passes rather than rewriting it.
- The published file lists rules in the engine's order, with the scopes mixed.

Insert the rules in an order that cannot pass by accident, the way your existing
order tests already do.

## Evidence

`CLAUDE.md`'s standard, unchanged. Red before green with the failing output
quoted. At least one mutation that reverts the scope ranking and shows which
tests catch it. Run the suite again after the commit if the change adds a file.

Flag anything else you find, with a recommendation attached.

## What to report, and where

`2026-11-14_REPORT_claude_code_rule_scope_order.md` in the repository root,
uncommitted, and say so.

**You do not mark step 10bu built.** The consultant session does that, and the
step is not finished in any case: the screen is still to be written.
