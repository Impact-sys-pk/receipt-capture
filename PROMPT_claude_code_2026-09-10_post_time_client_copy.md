# Brief: the Post-time message, so the client folder copy happens at Post

**Written 2026-09-10 by the consultant session, from Paul's decision the same
afternoon. Sub-step 10f.37 of `2026-07-25_CONSOLE_DESIGN.md`, given its own
number today by amendment 315.**

**HOLD UNTIL THE CURRENT BRIEF IS REPORTED.** This is the next one, not a second
one open at the same time.

**Read first, in this order:** `CLAUDE.md`, the section "How this project is
worked" and the seven traps. Then 18.2a and 18.2b of
`2026-07-25_CONSOLE_DESIGN.md`, then section 12, the resolution back-feed
contract, then sub-steps 10f.11, 10f.12 and 10f.16 in section 16.

---

## 1. What this is, and why it has no code today

`client_copy_trigger` has three values: on successful publish, at Post, or never.
**The `post` value has never worked.** `copy_for_published_receipt()` says so in
its own warning: the Post-time trigger needs a message from IntelliBooks Desktop,
that message is not built, and no copy is written until it is.

**That message had no sub-step.** 10f.12 said it was 10f.16's and 10f.16 said it
was 10f.12's, both are BUILT, and the code comment points at 10f.16. Three places
pointing elsewhere and none holding the work. **It is 10f.37 now.**

**Why Paul wants it, and this is the decision rather than the mechanism.** On the
`publish` trigger the client folder holds whatever the pipeline succeeded on,
including duplicates that got through, strays and documents that turned out to be
personal, and nothing removes them. **His requirement, in his words:
`Clients\{client}\IntelliBooks\Receipts\{tax year}\` should hold the receipts
relating to that client's transactions and make sense to him and to the client
years later.** On the `post` trigger a document reaches that folder because it was
attached to a transaction, so the folder is curated by construction.

**This brief is the pipeline half only.** The IntelliBooks Desktop half, being the
message at Attach and at Post, is the consultant session's and is written from
your report. **The two halves land together or not at all.**

---

## 2. Deliverable 1: the pipeline accepts a Post-time message

**A note that says a receipt has become part of the accounts**, and, on the `post`
trigger, writes the client folder copy for it.

**Name the action and state it in the report**, because the Desktop half is
written to match whatever you choose. `NOTE_ACTIONS` holds `filed` and
`discarded` today. **Amendment 307's rule applies: the field chooses the path,
not the action word**, so say plainly whether you are adding a third action or
carrying a field on an existing one, and why.

**What the message has to be able to say**, and no more than this: which receipt,
which client, that it is now attached to a transaction, and when. **No path.**
The pipeline composes the client folder name itself, as it does today, and a name
composed by Desktop cannot tell a collision's `-2` from its original.

**What the pipeline does with it.**

- **On `post`: write the client folder copy** through the one writer that already
  exists, so the collision rule, the one-copy rule and the missing-folder-name
  refusal are not reimplemented.
- **On `publish`: the copy already exists**, so there is nothing to write. Say so
  in the log and apply the note. This must not be an error: a firm can be on
  either trigger and the same Desktop sends the same message.
- **On `never`: nothing is written**, and that is the setting doing its job.
- **A second message for the same receipt writes nothing twice.** Say whether that
  rests on the idempotency key in 12.3 step 3, on the identical-bytes skip in the
  copy, or on both, and assert it rather than reasoning about it.

**Two things to establish rather than assume, and report both.**

1. **Whether a receipt can reach Post without having published.** It reaches the
   books through the drain, which needs a publish, so it looks impossible. Say
   whether it is, and what happens if a message arrives for a receipt with no
   `published` row.
2. **Whether the sweep interferes.** `_copy_missing_client_copies()` runs every
   poll and I read a trigger test in it. Confirm from the code that it does
   nothing on `post`, and that the two cannot write the same file twice.

---

## 3. What must not change

- **`Intellibills\Documents\` is never written to or deleted from.**
- **The `publish` trigger's behaviour**, which is what Paul is running on today
  and will keep running on until he switches the setting himself.
- **`write_client_copy()` stays the only writer into `Clients\`**, and this
  message reaches it through the existing gated caller rather than beside it.
- **Nothing in this brief changes F16's value.** Paul switches it, deliberately,
  after this lands. **Do not switch it and do not suggest a default**: 10f.16
  records what happens if the trigger moves before the message exists, which is
  that the client folders go quiet with nothing reporting it.
- **The discard work of this morning**, the note flag, the clearing and the
  resend behaviour.

---

## 4. Evidence

- **Red before green**, with the failing output quoted, and driven through a real
  `process_once()` rather than asserted on a function, because the value of this
  change is that a file appears in a folder.
- **A test for each trigger**, `publish`, `post` and `never`, and for a second
  message for one receipt.
- **Mutations** through the harness, each anchored once and printing its diff:
  write the copy on `never`; write it twice for two messages; ignore the trigger
  altogether; and a prose-only control that survives.
- **Enumerate from the syntax tree** anything you assert about a set of call
  sites, and print it whole. `.history\` excluded.
- **Nothing run against the live practice root.**
- **Never `import config` to read a value.** `CLAUDE.md`'s fourth trap.
- **Flag, do not fix.** **Disclose your own mistakes.** **State a confidence level
  and say what it is about.**

---

## 5. Committing and reporting

**Commit on `feat/console-phase0`.** Do not push, do not create a branch, and do
not commit `2026-07-25_CONSOLE_DESIGN.md`, any `PROMPT_*` or `HANDOVER_*` file, or
anything under `Test Receipts\`.

**Write the report to
`C:\LastingImpact\receipt_capture\2026-09-10_REPORT_claude_code_post_time_client_copy.md`**
and carry the commit hashes in it.

**Four things the Desktop half is written from, so put them in one section at the
top.**

1. The action word, the exact shape of the message, and every field it must carry.
2. What the pipeline does when the trigger is `publish` or `never`, so Desktop
   knows whether to send the message at all or always send it and let the pipeline
   decide. **Say which you would rather it did.**
3. What Desktop can honestly tell the operator at the moment of Attach or Post,
   given the pipeline reads the message on its next poll.
4. Whether the message should be sent at Attach, at Post, or at both, in your
   reading of 18.2b and section 12. **Paul has not ruled on this and it is not
   yours to decide either. Set out what each would mean and it goes to him.**
