# Brief: a deleted function is checked by definition, and the harness states its expected outcome

**Written 2026-09-08 by the consultant session, on Paul's decision the same day.**
**Report to `2026-09-08_REPORT_claude_code_definition_guards_and_harness_outcome.md` in this repository root.**

**Two small things, both your own flags from
`2026-09-08_REPORT_claude_code_source_guards_and_harness.md`, both approved. On no list.**

---

## 1. A guard that a function is gone checks for its definition, not for its name in the text

**Your flag 1.** `DeadResolverIsGoneTest` in `tests/test_default_firm_id.py` asserts
`resolve_client_by_code` appears nought times in `worker/database/repository.py`'s text.

**Latent rather than live**, checked here on 2026-09-08: that name appears zero times in that file
today, so the guard passes on the truth. **What makes it fragile is this project's own convention.**
A deleted function is recorded in a tombstone comment beside where it was, and **three such comments
already exist in production code**: `worker/database/repository.py` lines 73 and 364, and `app.py`
line 319. **The next deletion from `repository.py` recorded that way breaks this guard**, and the fix
would look like rewording a comment to get past a test, which is what happened to
`test_default_firm_id.py`'s other guard yesterday.

**Its docstring is right and must survive the change.** "A text count is the only available
assertion: an uncalled function has no behaviour to observe." **That is true of behaviour and not of
the source.** The narrower assertion is available: **parse the module and assert no `FunctionDef` of
that name exists.** A definition check is immune to any comment, docstring or string, and it says
what the guard means rather than approximating it.

**What has to be true when you are done.** Every guard asserting that something is *gone* from a
production file checks for its definition rather than for its name.

**Enumerate the set first and print it whole, across every production file rather than just
`app.py`.** **That scoping is the consultant session's error and it is worth naming**: the last brief
said "every test that asserts something about `app.py`'s source", and this fault was sitting one file
over the whole time. **So the set is guards over any file under `worker\`, plus `app.py` and
`config.py`.**

**One judgement is yours.** A guard asserting a *comment* is present, if there is one, genuinely is
about the text and stays. **Say which you left and why.**

## 2. The harness states which outcome it is asserting

**Your flag 2.** It exits 1 when nothing catches a mutation. **That is right for a real mutation and
inverted for a prose mutation, whose whole point is to pass.**

**One expected-outcome argument on the call**, so the harness reports pass or fail against what was
asked rather than against one fixed assumption, and a reader does not have to know which kind of
mutation they are looking at to read the exit code.

**Both kinds are now in use**, per your own last report: three real mutations and two prose ones. **So
this is a live ambiguity rather than a tidy-up.**

**Say in the report what the argument is called and what each value means.**

## 3. Out of scope

- **Item 174** of `2026-08-20_LIST_outstanding_items_and_decisions.md`.
- **Every outstanding sub-step of step 10f.** Twenty-five are outstanding and none is here.
- **Section 18.2b's freeze stands.**
- **No pipeline behaviour changes.** If either item would need one, stop and report it.

## 4. Standard of evidence

- **Prove item 1 with the harness**, which is what it is for: a tombstone comment of exactly the kind
  this project writes, added to the file the guard reads, failing the old guard and passing the new
  one. **That is the same shape as the prose mutations in your last report**, and it is a prose
  mutation, so it is also the first real use of item 2's argument.
- **Print every enumeration whole rather than counting it.** **Watch `ast.walk`**: your last report
  records it reporting one call against every enclosing compound statement, which counted one site
  eleven times.
- **Show the real mutation is still caught**, so the guard has not been loosened into uselessness.
- **Quote passes and subtests separately.**
- **Flag, do not fix. Disclose your own mistakes. State confidence, say what it rests on and what it
  is about.**
- **A commit each.**

## 5. What the report has to carry

`2026-09-08_REPORT_claude_code_definition_guards_and_harness_outcome.md`, in this repository root.

1. The enumeration of every guard asserting something is gone, across `app.py`, `config.py` and
   `worker\`, printed whole, with which checked text and which checked a definition.
2. Any guard you left as a text check, and why.
3. The tombstone-comment mutation: the old guard failing, the new one passing.
4. The real mutation still being caught.
5. What the harness's expected-outcome argument is called and what each value means.
6. The suite, passes and subtests, measured both ends.
7. Anything you flagged, and anything this brief got wrong.
