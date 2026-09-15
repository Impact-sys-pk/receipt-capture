# Could the receipts staging list leave the books file, and what would break

**Written 2026-09-14 for Paul to decide on. Nothing is built and nothing is proposed as agreed.**
Everything below was read out of `IntelliBooks-Desktop-v3.html` and out of a live books file, not
recalled.

---

## 1. Why the question exists

Section 7 of `2026-08-18_BOUNDARY_two_products.md` sets three conditions that make the Receipts tab
Intellibills' front end rather than a label. **Condition 2 reads: "It reads and writes only
Intellibills' stores, plus the shared client registry."**

`fileReviewReceipt()` writes a row into `IntelliBooks\Books\{client_id}-books.json` and saves it.
That is IntelliBooks' store and it is not the client registry. **Condition 2 is not met today.**

Section 18.6 of the design document calls the same arrangement **"the anomaly in what exists
today"**, and says the receipts list is a staging area holding items awaiting a decision, nothing in
which is part of the books.

**No document says where the staging list should live.** The arrangement is inherited from
IntelliBooks Desktop, which had a receipts list before Intellibills existed.

---

## 2. The coupling, enumerated rather than estimated

**`books.receipts` appears 53 times in 32 functions** in `IntelliBooks-Desktop-v3.html`, counted from
the file with each occurrence's enclosing function taken from the source.

Most are the Receipts tab's own code and would move with the list. **Nine are books-side**, and they
are the whole problem:

| Function | What it does with the list |
|---|---|
| `editTxn` | `t.receiptId` looked up in the list, to show the attached document in the transaction window |
| `renderBank` | The same, twice: `t.match` for a proposed match and `t.receiptId` for an attached one |
| `refreshMatches` | Walks every receipt to propose matches against transactions |
| `handoverPack` | Walks every receipt to write the client's handover pack |
| `exportClientBackup` and its restore | Carries receipts in and out of a client backup |
| `categoryReferences` | Counts receipts pointing at a category, which is the guard that refuses a category deletion |
| `ensureAcct` | Checks a receipt id is not already present, and sorts the list |
| `migrateBooks` | Walks the list on a version migration |
| `taxYearRange` | A comment only, no code |

---

## 3. The fact that decides the answer

**A transaction carries only `receiptId`. It does not carry the document or the figures.** Read from
`Client_004-books.json`: a transaction with an attached receipt has the keys `accountId, amount,
category, currency, date, desc, id, ignored, key, manual, match, receiptId, ref, status, transferId,
vat, vatRate, vatRateSet`. **No image and no receipt figures.** The image sits on the receipt row, as
base64, up to 457,718 bytes for one of the seventeen in that file.

**So section 18.6 is not built.** It says that at Post the transaction takes the confirmed figures,
the image and the document's id, and that the receipt stops being a separate record. Today the
transaction takes an id and points back into the staging list for everything else.

**That is why the list cannot simply move.** Four of the 31 transactions in that one file resolve a
receipt by looking into it, and every future posted transaction would do the same.

---

## 4. The two routes

### Route A: move the list now, into a second file loaded alongside

**What it costs:** repointing the nine books-side sites at the second file, a one-off migration of
existing rows, and a second file with its own save, its own clash detection and its own place in the
backup.

**What it does not buy.** The books code still reads Intellibills' store, so condition 1, "no books
code calls into it", is still not met and condition 2 is met only on a technicality. **And it makes
a posted transaction depend on a file belonging to a product that a standalone IntelliBooks would
not have.** That is worse than today, not better.

### Route B: build 18.6 first, then move the list

**Step one.** At Post, the transaction takes the image, the confirmed figures and the document id,
and the staging row is removed. After that, nothing books-side needs the staging list except the
staging-time functions, which are Intellibills' own.

**Step two.** The list moves to a file of Intellibills' own and the nine sites reduce to the few that
genuinely belong to staging.

**What it costs.** Step one is the larger piece and it is a change to how a posted transaction is
stored, so it touches the books file's shape. **Step two is then nearly free.**

**What it buys.** 18.6's own two consequences, stated there: locking a receipt becomes unnecessary,
because nothing depends on it before Post and it is not a separate record after; and the two copies
can no longer disagree, because after Post there is only one. **The divergence 18.6 cites as evidence
is real**: receipt `be7d656c`'s sidecar reads gross £10.99 and its books row reads VAT £52.00.

---

## 5. What would still need deciding under either route

- **The client backup.** Does it carry the staging list, or become books-only? Today it carries both.
- **The handover pack.** Does a departing client's pack include receipts that were never posted?
- **The category deletion guard.** It must still see staged receipts, so it reads the second file.
- **Where the second file lives.** `Intellibills\` alongside `clients.json`, or under the client
  folder. The first matches every other Intellibills store; the second does not, because `Clients\`
  is the firm's filing and not a product's store.
- **File size.** The staging file carries the images, so it holds most of the three megabytes. Under
  route B it shrinks every time something is posted.

---

## 6. What I am not claiming

- **I have not read all 53 sites**, only the nine books-side ones and the two that decide the shape.
  The Receipts tab's own uses were counted, not read.
- **I have not costed 18.6.** It is described in the design document and has no step in section 16.
- **Nothing here says the move is worth doing.** It says it is possible, that route A makes the
  boundary worse rather than better, and that route B depends on work nobody has scheduled.

---

## 7. Does the current arrangement break the rules? Tested against each one

**`2026-08-18_BOUNDARY_two_products.md` is the authority for which product a thing belongs to, and
says so: "Where the two disagree, this one decides, and the design document is corrected."** Each of
its rules is quoted and then tested.

### Section 3, the rule itself. BROKEN, and this is the one that matters

> **No function may live only in the other product.** If Intellibills needs something in order to
> work, that thing must be inside Intellibills. It may not sit in IntelliBooks and be borrowed.
> **The test is one question: take IntelliBooks away. Does Intellibills still work?**

**Take IntelliBooks away.** The receipts staging list is written into
`IntelliBooks\Books\{client_id}-books.json`, a file IntelliBooks creates and saves. **Standalone
Intellibills has nowhere to record a captured receipt while it awaits a decision.** Its own front
end, the Receipts tab, writes into a file that would not exist.

> **IntelliBooks may depend on Intellibills for anything; Intellibills may depend on IntelliBooks
> for nothing.**

**Intellibills depends on IntelliBooks for its staging store.** That is the asymmetry stated in
absolute terms, and it is the wrong way round.

### Section 2, where the line falls. BROKEN

> **Intellibills owns the document and everything read from it. IntelliBooks owns the books.**

A staging row is the document and everything read from it: supplier, date, net, VAT, gross, the
image. **It is stored in the books.**

### Section 7, condition 2. BROKEN

> It reads and writes only Intellibills' stores, plus the shared client registry.

`fileReviewReceipt()` writes a row into the books file and saves it. That is IntelliBooks' store and
it is not the client registry.

### Section 7, condition 1. BROKEN IN BOTH DIRECTIONS

> Its code calls no books functions, and no books code calls into it. Physically in the same file,
> logically separate.

The Receipts tab's code saves the books file. **And nine books-side functions read `books.receipts`**,
enumerated at section 2 of this note.

### Section 4, the naming rule. ARGUABLE, and it is not claimed

> **Nothing in Intellibills may be named after IntelliBooks.** No constant, no adapter, no field.
> An adapter is named for what it does; the address it writes to is configuration.

The address an Intellibills function writes to is `IntelliBooks\Books\`, hardcoded rather than
configured. **Whether that rule reaches a path as well as a constant is not stated**, so this is
raised and not asserted.

### Section 5's table of breaches. THIS IS A FIFTH, AND IT IS A DIFFERENT KIND

The four recorded breaches are all the same shape: **a function of Intellibills that can only be
performed on IntelliBooks' screen**, because IntelliBooks had a screen and Intellibills did not.

**This one is the store rather than the screen**, and the four inspections missed it for the reason
section 5 gives about the fourth: they went through a screen. **Section 5's own sentence applies
exactly: "None of these was a decision to put an Intellibills function inside IntelliBooks."** The
staging list is inherited from IntelliBooks Desktop, which had one before Intellibills existed.

**If Paul agrees it is a breach, section 5's table gains a fifth row.** That is a change to the
document that is above both products and it is his.

---

## 8. A second thing found while testing, and it is NOT a boundary breach

**Section 18.2 declares three stores. The second one does not exist.**

> `IntelliBooks\Attachments\{CODE}\{year}\{month}\{receipt id}_{original filename}` | IntelliBooks |
> The evidence attached to a transaction. **Today this is base64 inside `{CODE}-books.json`, which is
> the right principle in the wrong shape.**

So the design already says the images should be a store of their own and that their present home is
wrong. **That is IntelliBooks' own store on both sides of the question, so it breaks no boundary
rule.** It is unbuilt design rather than a breach, and it is why one client file is three megabytes
for seventeen receipts.

**It bears on the decision in front of Paul**, because moving the staging list and building
`Attachments\` both take the images out of the books file, and doing them separately means moving the
same data twice.

---

## 9. The mechanics, worked through, and a correction to section 4 above

**Section 4's claim that route A "makes the boundary worse rather than better" is wrong, and the
rule that shows it is in the boundary document's own section 3.**

> **IntelliBooks may depend on Intellibills for anything; Intellibills may depend on IntelliBooks
> for nothing.**

**Today the dependency runs the forbidden way**: Intellibills' front end writes into IntelliBooks'
store. **After the move it runs the permitted way**: books code reads Intellibills' staging store.
**So the nine books-side sites stop being a problem the moment the file moves.** They become the
allowed direction, and no interface has to be invented for them.

**That removes the precondition I put on it.** Building 18.6 first is not required. It remains worth
doing for its own reasons, which 18.6 states, but the file split does not wait on it.

### What a second file actually needs, read from the save and load path

`saveBooks()` and `loadBooks()` hold five things per file, and a second file needs its own of each:

| Held today | What the second file needs |
|---|---|
| `booksHandle`, the file handle | Its own handle |
| `booksMod`, the last modification time | Its own, because the clash check compares against it |
| `savingBlocked` | Its own, or the pair share one and a clash in either stops both |
| The 400ms debounce in `scheduleSave()` | Its own timer, or one timer that writes both |
| `idbSet("cache:"+client_id)` | Its own cache key |

**The clash detection is the part to get right.** `saveBooks()` refuses to save when the file's
modification time has moved since it loaded, and stops the session with an alert. **Two files means
two of those, and a session could be blocked on one and not the other.**

### The one real risk, stated plainly

**Today one save writes the transactions and the staging receipts together. Two files are two
writes.** A failure between them leaves a transaction referencing a staging row that was not saved,
or the reverse. **That is the thing that can break and it has no equivalent today.**

**Two ways to hold it**, and both are ordinary: write the staging file first and the books file
second, so the surviving state is a staging row nothing points at, which is harmless and visible;
or accept that after 18.6 the coupling exists only between Post and the next save, which is
seconds.

### What else has to move with it, enumerated

- **`loadBooks()`'s legacy migration.** The same shape is needed once, to lift `receipts` out of
  every existing books file into the new one. Five live files.
- **`exportClientBackup()` and its restore.** They carry `receipts` today. Either the backup carries
  both files or it becomes books-only, which is a decision rather than a mechanic.
- **`handoverPack()`** walks the staging list to write a departing client's pack.
- **`wipeClientData()` and `deleteClient()`** must clear or delete the second file too, or a deleted
  client leaves a staging file behind.
- **`migrateBooks()`** walks `books.receipts` on load.
- **`emptyBooks()`** creates the `receipts` array for a new client.

### The one genuine cross-product function, and it is not solved by the move

**`refreshMatches()` walks every transaction against every staging receipt to propose a match.** It
is reconciliation, so it is a books function, and it needs the whole staging list. **It runs before
Post, so 18.6 does not remove the need.**

**It is permitted**, by the asymmetry quoted above: IntelliBooks may depend on Intellibills. But it
means the books side loads the staging file on every client open, so the second file is not optional
for a combined-product session and cannot be lazily loaded only when the Receipts tab is opened.

**The boundary document does not discuss matching at all.** Recorded as a gap rather than a fault.
