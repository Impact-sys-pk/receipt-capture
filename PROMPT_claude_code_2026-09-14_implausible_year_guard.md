# Claude Code brief, 2026-09-14: the implausible year guard

**Sent to Claude Code as chat text at 12:06 BST and corrected at 12:33 BST. Written to a file
afterwards, because `CLAUDE.md` makes `PROMPT_*.md` the brief a session works from and a brief that
exists only in a chat is a brief the next session cannot read.** The correction is folded in below
and recorded as a correction at the end rather than tidied away.

**Report to `2026-09-14_REPORT_claude_code_implausible_year_guard.md`.**

**Amendment 460 of `2026-07-25_CONSOLE_DESIGN.md` carries the decision.**

---

## What was found

A real receipt in the live database is filed at:

```
Clients\TEST\IntelliBooks\Receipts\26-27\0026-08-30_IMO-CAR-WASH_24.00.png
```

Receipt `abe4a034-878b-43cd-965d-e4096b5a6bcd`, `Client_001`. Its first extraction had no
`invoice_date` and went to Review. The `manual_correction` row carries
`invoice_date = '0026-08-30'`: a two-digit year was typed into a date box and the browser made it
year 26. `determine_tax_year()` in `worker/filing.py` composed the folder name `26-27` from it.

**Three doors accept a four-digit year with no plausibility check**, read directly by the consultant
session before this brief was written:

- `worker/validation/rules.py`, the extraction path, which runs `strptime` alone
- `parse_corrections()` in `worker/resolution/service.py`, the command-line route
- the back-feed note validator in the same file, the route this receipt came through

**Re-enumerate that set from the syntax tree before building.** It is one session's enumeration and
a claim about a set is not verified by verifying its members.

Sub-step 10d.41 already put a year rule into ~~`parse_ambiguous_date()`~~ **`parse_ambiguous_date()`, corrected 2026-09-14 by amendment 467: the underscore-prefixed name does not exist anywhere in the repository** in
`worker/extraction/postprocess.py`. That guard covers numeric dates the extractor parses and covers
none of the three doors above. Same shape as steps 10ab and 10ac.

## The rule

**A year before 2000, or later than the current year plus one, is not readable.** Paul's decision,
2026-09-14. The current year is read when the check runs, not at import.

**The bound is IntelliBooks Desktop's own, taken as the authority for both products.** `badYear()`
in `IntelliBooks-Desktop-v3.html` has shipped since 2026-09-06 and reads
`y >= 2000 && y <= new Date().getFullYear() + 1`. Two products built by sessions that cannot see
each other have to agree on the boundary, or a receipt dated 2027 is accepted on screen and refused
by the pipeline.

## What each door does with it

- **The extraction path**: the treatment an invalid date already gets. A note naming the year, and
  the receipt routes to Review. Never silently corrected, and no century inferred: 10d.41's
  reasoning holds, a pivot tight enough to read 99 as 1999 reads 28 as 1928.
- **The two correction doors**: the field error and the note error each already raises for a date
  that is not a real calendar date, worded the same way and naming the year supplied.

## One rule, one helper

One helper holds the rule and every door calls it. The bound is not written three times. **A source
guard asserts the set**: no other place validates an `invoice_date` without going through it, so a
fourth door added later goes red rather than passing. `OneWriterTest` in
`tests/test_delivery_log.py` is the shape.

## Out of scope

- `determine_tax_year()` is not changed.
- The row on disk is not repaired. That receipt is test data and step 10i clears it.
- **10d.41's two-digit branch stays stricter and is not tidied**, rejecting anything past the current
  year. `2000 + c` is an inference the system made; a four-digit year is a figure somebody stated. A
  stricter test on the inference is not the same rule twice. Say in the report that it was left alone
  and why.

## Evidence expected

Red before green with the failing output quoted. Mutations anchored on something unique, with
`str.count()` asserted at 1 and the unified diff printed beside each result. Suite figures measured
rather than carried, and the suite run again after the commit if the change adds a file. Your own
mistakes, including ones you caught and corrected. A confidence level saying what it rests on.

**Propose the commit and wait. Do not push.**

---

## The correction, recorded rather than tidied away

**The brief as first sent gave the bound as 2000 to the current year.** That was the consultant
session's proposal and Paul agreed it before either of them had read
`IntelliBooks-Desktop-v3.html`. Reading it half an hour later showed `badYear()` already shipping
with a ceiling one year higher. **The consultant session's error**: it proposed a number for a
boundary two products share without opening the product that already had one. Corrected to Desktop's
bound and sent to Claude Code mid-build at 12:33 BST.
