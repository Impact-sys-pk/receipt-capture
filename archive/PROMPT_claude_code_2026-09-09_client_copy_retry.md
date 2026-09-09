# Brief: a client folder copy that failed after a successful publish is retried

**Written 2026-09-09 by the consultant session. Claude Code's own flag 6 of
`2026-09-09_REPORT_claude_code_stage4_pipeline.md`, offered there as small and obviously right.**

**Now unblocked.** It was declined earlier that day only because folding it into stage 4 would have
made stage 4 two things. **Check 1 passed in both clauses at 15:15, stage 4 is complete and 18.2b's
freeze is closed, per amendment 298.** That reason is spent.

**Small. One sweep clause and its tests.**

---

## 1. What is wrong

`copy_for_published_receipt()` swallows its own failures, and that is right: by the time it runs the
item is already in the folder IntelliBooks drains, and the archive of record holds the document, so a
folder in the firm's own tree being unavailable must not fail a complete receipt.

**But nothing retries it.** The repointed sweep asks "was this published", and a receipt whose publish
succeeded and whose copy failed **has** a `published` row, so it is never swept. The failure is an
ERROR in `run.log`, `filed_path` stays NULL, and the document never reaches the client folder.

**On OneDrive this is not hypothetical.** A locked or syncing folder is the ordinary case.

---

## 2. What to build

**One deliverable. The sweep also offers a receipt that published and was never copied.**

The selection, stated so it is not interpreted:

- validation status `ok`, **and**
- it has a `published` row in `publish_events`, **and**
- its `filed_path` is NULL, **and**
- **the firm's `client_copy_trigger` is `publish`.**

**The trigger condition is a deliverable and not a detail.** On `never` and on `post` no receipt ever
has a `filed_path`, so without it this clause selects every `ok` receipt in the database on every
poll, for ever. `copy_for_published_receipt()` no-ops per receipt on those triggers, so nothing would
be written; the cost is a query answering with the whole table every five minutes and a sweep line
that means nothing. **Decide where the condition sits, in the query or above it, and say which.**

**THE CUTOVER APPLIES HERE TOO, and this is the one that can do real damage.** Your own decision 3
gives the publish sweep a cutover: anything created before the earliest `publish_events` row is
history rather than a gap. **The same must hold for this clause.** Without it, the first poll after
this lands would copy **every historical `ok` receipt** into live client folders, and 18.2b says a
copy is never withdrawn, so it could not be undone by the product. **Amendment 283 is Paul's decision
that the first run publishes only what arrives from then on, and this is that decision applied to the
copy.**

---

## 3. What must not change

- **`copy_for_published_receipt()` keeps swallowing.** The guarantee that a failed copy cannot fail a
  receipt is the reason this clause exists rather than a reason to remove it.
- **One writer into `Clients\` still.** Nothing new writes there. This clause reaches the same
  function.
- **The publish half of the sweep is untouched**, and so is its own cutover clause. Its test caught a
  mutation only after you fixed it to seed an early row, per section 4 of your report; **do not let
  this clause's tests be answered by the cutover in the same way.**
- **No schema change.**
- **Nothing in the run summary.**

---

## 4. Standard of evidence

- **Red before green**, with the failing output quoted.
- **Drive a real failure**, rather than asserting the query. A copy that raises, then a poll, then the
  document present and `filed_path` set.
- **A test per trigger**: on `publish` it retries; on `never` and on `post` it selects nothing and
  writes nothing.
- **A test that the cutover holds**, seeded so that the cutover is not what answers the clause under
  test, and a mutation dropping the cutover that is caught by exactly that test.
- **Mutations anchored to one place**, each asserted to match exactly once, each printing its own
  diff.
- **Do not cite a line number in `config.py` or `app.py`.**
- **Flag, do not fix. Disclose your own mistakes. Say what each confidence rests on and what it is
  about.**

---

## 5. Where to write the report

**`C:\LastingImpact\receipt_capture\2026-09-09_REPORT_claude_code_client_copy_retry.md`.**

Carry in it: what was built, the commit, the suite before and after, every mutation and its result,
every decision this brief did not settle and what you chose, any flag, and your own mistakes.
