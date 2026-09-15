# Terminology review, 2026-09-14

## 0. The four things, Paul's words, 2026-09-14. Everything below uses these

1. **The receipt document.** The photograph or the PDF. It is never editable.
2. **The record of that document.** Supplier, date, net, VAT, gross, category. Editable.
3. **The document may become evidence for a transaction.**
4. **The record of that transaction.**

**"Receipt" alone is ambiguous between 1 and 2 and is not used on its own.** That ambiguity is what
made this afternoon's discussion go round twice: the document cannot be altered and the record of it
can, and the same word was doing both jobs.

**One consequence falls straight out of it.** A record of a document should not contain the document.
Today the record carries the document inside it, which is why one client file is three megabytes of
which 98.3% is pictures and PDFs, measured on 2026-09-14.

**Written for Paul to rule on.** He said the terminology has to be got right. Nothing here is built
and nothing is renamed: this names each term, says what it actually points at, says what is wrong
with it, and proposes one name. **Every recommendation is a proposal and his to accept, change or
refuse.**

**How each row was settled.** By reading the code or the file it names, not from memory. Where a row
rests on something not read, it says so.

---

## 1. The two that are wrong today, and they are why this document exists

### "File Receipt", the button, and `fileReviewReceipt()`

**What it does now**, read from `IntelliBooks-Desktop-v3.html`: checks the supplier, the date and the
gross; writes a row into the client's receipts list; saves; removes the item from
`IntelliBooks\Incoming\`; writes a note telling the pipeline what was decided.

**What it does not do: file anything.** Sub-step 10f.14 took that away deliberately, so the client
folder has one writer and it is the pipeline.

**Why the name bites.** `receipts.filed_path` in the database means the copy in the client's folder,
and `filed_at` with it. So a receipt can be **filed** by the button and not **filed** in the
database, at the same moment, which is where a receipt sat this afternoon.

**Proposed: `Accept Receipt`.** The act is the operator agreeing the document and its figures.
`fileReviewReceipt()` becomes `acceptReviewReceipt()`.

**Cost:** one button label, one function name, the toast wording, and the places that name the
function in comments. No data changes and no contract changes: the note's `action` is `filed` on the
wire and that is a separate question, at row 3 below.

### "the books", and `{client_id}-books.json`

**What it holds**, read off `Client_001-books.json`: `accounts`, `transactions`, `receipts`, `rules`,
`categories`, `mappings`, `balances`, plus the chart provenance and the save housekeeping. Fifteen
top-level keys.

**Why the name bites.** To an accountant the books are the accounts. This file is the client's whole
working set, and a receipt row in it is not in the accounts at all. So "in the books" is true of the
file and false of the accounts, for the same receipt, on the same day.

**Proposed: the client file**, `{client_id}-client.json`, in `IntelliBooks\Clients\`. "The books"
then means what you mean by it and nothing else.

**Cost: the highest on this page, and it may not be worth paying.** The word is in both products,
in the folder name, in the filename convention, in `handoverPack()`, in the backup and restore, and
in five live files on disk plus five superseded ones. **A cheaper half-measure: leave the file and
stop using the word in anything written for the operator**, saying "the client file" on screen and
in messages while the filename stays.

---

## 2. The pair already recorded, and still right

**`Post`.** Two acts, one word, and `CLAUDE.md` already carries this: `postTxn()` and **Post
Selected** sign off a transaction that exists; `postReceiptToCashbook()` and **Post Selected to
Cashbook** create a transaction from a receipt.

**Proposed: leave it.** Both are genuinely posting in the accounting sense, the screen distinguishes
them, and renaming would move the confusion rather than remove it.

**`Attach` and `Link`.** Attach is receipt to transaction; Link is transaction to transaction.
**Leave both.** They name different things and the words do not overlap in ordinary use.

---

## 3. The words on the wire, which are a different question

**`filed_path` and `file_path` on `receipts`.** `file_path` is the document store copy and
`filed_path` is the client folder copy. **Two words one letter apart for two different places.**

**Proposed: `archive_path` and `client_copy_path`.** Each says where it points.

**Cost: a schema change on a live database**, which today has no migration path, which is what the
`line_items` fault of this morning was. **So this one waits for the start-up schema check at least,
and is a candidate for the clear-down at step 10i rather than before it.**

**The resolution note's `action: "filed"`.** It is the contract between two products written by two
sessions that cannot see each other. **Proposed: leave it alone until the button is renamed and
settled**, then decide separately. Changing a wire word costs a coordinated release of both halves,
which is the thing amendment 241 exists to avoid doing casually.

---

## 4. Words that are right and are worth stating so nobody reopens them

- **Intellibills** for the Python system, **IntelliBooks Desktop** for the browser app,
  **IntelliCharts** for the chart folder, **the master** for `COA_MASTER_v2.xlsx`, **the console**
  for the Flask app not yet built, **the database** for `receipts.db`. All defined and all used.
- **Publish** means the pipeline handing an item to IntelliBooks through `IntelliBooks\Incoming\`.
  One meaning, one direction.
- **Delivery**, the log at `IntelliBooks\Delivery\{client_id}.log`, is a record of documents copied
  into a client folder. One meaning.
- **Review** is the queue of receipts waiting for a person.
- **Capture** means the mailbox and nothing else, since sub-step 10d.43.

---

## 5. What is being asked

Four rulings, in the order they cost least:

1. **Rename the button to `Accept Receipt`.** Cheap, and it removes the collision that bit today.
2. **Stop using "the books" for the file in anything written for the operator**, keeping the filename
   as it is.
3. **Rename the file and its folder as well**, or leave it. This is the expensive one.
4. **`file_path` and `filed_path`**, renamed at the step 10i clear-down or left.
