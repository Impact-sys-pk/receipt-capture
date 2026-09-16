# Brief: a Desktop resolution note means "settle this receipt", not "Desktop filed it"

**Written 2026-09-09 by the consultant session. Section 12 of `2026-07-25_CONSOLE_DESIGN.md`,
sub-step 10f.14, and Paul's decision of 2026-09-09.**

**This is a live fault. One receipt on Paul's machine is in the books and not in the database, which
is the disagreement the back-feed contract exists to prevent.**

---

## 1. What happened, and it is the consultant session's error

Sub-step 10f.14 stopped `fileReviewReceipt()` in `IntelliBooks-Desktop-v3.html` writing into
`Clients\`. Amendment 299 built it and **removed `filed_path` from the resolution note**, on the
reasoning that the pipeline is now the only writer into `Clients\` and its `client_copy_trigger`
decides whether a copy happens at all, so a path from Desktop would be one product naming the other's
file.

**That reasoning stands and the change was made without reading the other half of the contract.**
`worker\resolution\service.py` refuses a `filed` note that carries no `filed_path`, resolves the path,
checks the file exists, and refuses again if the database holds a different one.

**The live result, read from Paul's machine on 2026-09-09:**

```
17:16:48 resolution notes to apply: 1
17:16:48 ERROR unusable resolution note for a587b166-35a1-473c-aa5a-409749f7b642:
         'filed_path' is required for a filed note
```

Receipt `a587b166-35a1-473c-aa5a-409749f7b642` reads `status: failed`, `filed_path: NULL`, and has no
`resolution_events` row. It is in the books in Desktop as LA BELLA RESTAURANT, £27.50. **The note is
in `Intellibills\Resolutions\failed\` with its `.error.txt`, so nothing is lost.**

---

## 2. What to build

**Paul's decision, 2026-09-09, taken over the smaller alternative of relaxing the validator: a note
from Desktop stops meaning "Desktop filed this" and starts meaning "these are the corrected values,
settle this receipt".** The smaller fix was rejected because it leaves the word `filed` naming
something that no longer happens, and a name that lies is what this project has spent the day paying
for.

**Deliverable 1. A `filed` note with no `filed_path` is applied through the ordinary resolution
path.**

That path already exists and already does the whole job: it applies the corrections, re-validates,
categorises, calls the client folder copy on the firm's trigger, sets the receipt to `ok`, and records
a resolution event. **It is what the CLI and the console use.** A Desktop note should now reach it.

**Deliverable 2. A `filed` note that DOES carry `filed_path` keeps today's behaviour exactly.**

Older notes exist on disk, and the console and any other writer may still send one. **Do not delete
the Desktop-filed path; choose between the two on whether the field is present.**

**Deliverable 3. The note in `Resolutions\failed\` can be applied.**

Say how Paul re-applies it: whether moving it back is enough, or whether something else is needed.
**Do not move it yourself**; it is outside the repository.

---

## 3. Decisions this brief does not settle, and each is yours

- **What `action` should be called.** `filed` is now wrong for the Desktop case and the field is part
  of a contract with a file format on disk. Renaming it is a breaking change to notes already
  written. **Say what you chose and why.**
- **What `original_review_files` should mean.** Desktop now names the inbox item it removed. Nothing
  reads it today as far as this brief knows. Check that, and say so either way.
- **Whether the actor and source recorded should stay `desktop`.** The correction is Desktop's; the
  filing is now the pipeline's.
- **Whether a Desktop-settled receipt should be re-categorised or keep the category the note
  carries.** The note sends `category_code` and `category_name`, and a person chose them.

---

## 4. What must not change

- **Desktop still never writes `receipts.db`.** It writes a note; the pipeline writes the database.
  Section 12.1, and it is the whole point of the contract.
- **One writer into `Clients\`.** The copy still happens through the one gated function.
- **The double-filing guard.** The Desktop-filed path refuses when the database already holds a
  different `filed_path`, and that check must survive for notes that carry one.
- **No schema change.**
- **Nothing in the run summary.**

---

## 5. Standard of evidence

- **Red before green**, with the failing output quoted.
- **Drive a real note through a real `process_once()`**, both shapes: with `filed_path` and without.
- **Drive all three trigger values.** On `never` a settled receipt gets no client folder copy and must
  still reach `ok`.
- **Assert the receipt ends `ok` with a `resolution_events` row**, because the live fault is that
  neither happened.
- **Mutations anchored to one place**, each asserted to match exactly once, each printing its own
  diff. **Include one that makes a note without `filed_path` take the Desktop-filed path again**, and
  it must be caught.
- **Do not cite a line number in `config.py` or `app.py`.**
- **Flag, do not fix. Disclose your own mistakes. Say what each confidence rests on and what it is
  about.**

---

## 6. Where to write the report

**`C:\LastingImpact\receipt_capture\2026-09-09_REPORT_claude_code_desktop_note.md`.**

Carry in it: what was built, the commit, the suite before and after, every mutation and its result,
every decision this brief did not settle and what you chose, any flag, your own mistakes, and **what
Paul has to do to get receipt `a587b166-35a1-473c-aa5a-409749f7b642` settled.**
