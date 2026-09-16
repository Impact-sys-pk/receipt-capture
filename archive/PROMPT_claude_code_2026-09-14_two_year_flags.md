# Claude Code brief, 2026-09-14: your flags 8.2 and 8.3, both taken

Paul's decisions, 2026-09-14, on flags 8.2 and 8.3 of
`2026-09-14_REPORT_claude_code_implausible_year_guard.md`. Amendment 468 of
`2026-07-25_CONSOLE_DESIGN.md` records both.

**Report to `2026-09-14_REPORT_claude_code_two_year_flags.md`.**

**One commit, proposed and not pushed. The two parts are independent; if one turns out to be wrong,
say so and build the other.**

---

## Part one, your flag 8.2. The year rule covers `transaction_date` as well

`parse_attached_message()` in `worker/attached.py` validates `transaction_date` with the shape the
three receipt doors had before this morning: the ISO form, then the calendar, and nothing about the
year. `0026-08-30` passes.

**Build:** call `unreadable_year()` there too, refusing with the wording that door already uses for a
date that is not a real calendar date, and **widen the set guard from `invoice_date` alone to
`invoice_date` and `transaction_date`**, so a fifth door on either field goes red rather than
passing.

**Paul's reason, and it is the scope decision your flag asked for:** the point of one rule is that
nobody has to ask which fields it covers.

**Your own tracing stands and is not to be re-argued:** `transaction_date` reaches a
`resolution_events` audit row through `record_attached_document()` and does not compose a filed path
or reach `determine_tax_year()`. So this protects a record of what happened rather than a tax year,
and that is worth four lines rather than worth skipping.

## Part two, your flag 8.3. The three-digit refusal tests the digits

`parse_ambiguous_date()` in `worker/extraction/postprocess.py` reads `elif c < 1000: return None`
under the comment "A three-digit year is a misread, not a year." `c` is the integer, so `int("026")`
is 26 and `30/08/026` takes the two-digit branch and returns `2026-08-30`. Only 100 to 999 are
refused.

**Build:** test how many digits were written rather than what they add up to, which is what the
comment already claims. **After this, `30/08/026` returns None and the receipt routes to Review with
the note that branch already produces**, which is 10d.41's own decision applied to the case it was
written for.

**This is the one exception to "10d.41's branch stays as it is".** That instruction meant its bound
is not tidied to match the four-digit rule. It did not mean a branch that does not do what its own
comment says is left alone. **Change the behaviour, keep the bound.**

**In the same edit, the stale line above it.** The comment at `postprocess.py:98` says the
`elif c < 1000` branch "is deleted" and the branch is live at `:105`. Correct the comment with the
superseded wording struck rather than removed, per this project's convention.

**Your own test `test_a_three_digit_year_is_still_refused` currently pins the behaviour as found.**
It changes with this, and its comment should record that it once pinned the opposite and why.

## Evidence expected

- Red before green for both parts, with the failing output quoted, and note which of your existing
  tests change and why.
- The 100-subtest sweep over the two-digit branch must still pass unchanged: **this touches three
  digits and must not move two.** That is the control on part two.
- Mutations anchored on a unique string, `str.count()` asserted at 1, each diff printed.
- The suite before and after, measured.
- Your own mistakes, and a confidence level saying what it rests on.
