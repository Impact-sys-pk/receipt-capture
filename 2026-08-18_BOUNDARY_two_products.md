# The boundary between Intellibills and IntelliBooks

**Written 2026-08-18 by the consultant session, from decisions taken by Paul the same day.**

**This document is above both products.** `2026-07-25_CONSOLE_DESIGN.md` is the build authority for how things are built; this is the authority for **which product a thing belongs to**. Where the two disagree, this one decides, and the design document is corrected.

~~**Its home is provisional.** It sits in `C:\LastingImpact\receipt_capture\` because that is where the authoritative documents live and both build sessions are pointed there. But that is Intellibills' repository and this document governs both products, which is the same category error it exists to prevent. Moving it is a filing decision Paul has not yet taken.~~

**Settled 2026-09-12. Paul's decision: it stays in `C:\LastingImpact\receipt_capture\`.** No file move. **The category error above stands, tolerated rather than fixed**: Paul gave the decision without reasoning beyond it, and none is invented here. Recorded at amendment 350 of `2026-07-25_CONSOLE_DESIGN.md`, closing outstanding item 31.

---

## 0. What this document is for, settled 2026-09-15

**Paul's statement, in his own words, 2026-09-15. It governs everything below it. Where anything later in this document disagrees with it, this section decides.**

1. **One product line. IntelliBooks is the Mark 2 version of Intellibills, with the bookkeeping added.** The names may change later.
2. **Intellibills on its own does not amount to a product today.** It would need connectors to QBO, Xero and the rest before anyone could sell it.
3. **Spinning it off is an option being kept open, not a plan.**
4. **If it ever happens it is the cloud version**, so today's local constraints do not travel with it.
5. **IntelliBooks includes Intellibills. IntelliBooks may depend on Intellibills. Intellibills may not depend on IntelliBooks.**
6. **They are not two independent systems.**

**What follows from it, written here so it is not worked out twice.**

- **Standalone completeness is not an obligation on today's build.** Sections 1, 5 and 12 were written as though it were, and each is struck or reframed where it says so.
- **Point 5 is the only rule in this document that constrains anything today, and it runs one way.** It is what stops Intellibills reading the books file.
- **The standalone question survives as a test, not as a rule.** Paul's own form of it: what would come out to leave Intellibills alone? Run on `IntelliBooks-Desktop-v3.html` on 2026-09-15, the answer was two tabs out whole, being Bank Transactions and Reports; three in whole, being Receipts, Clients and Firm Settings; and two that split, being Client Data and Client Settings. **The list is worth more than a verdict, because the tabs that split are where a function gets tangled without anyone noticing.**
- **What has to be kept is the record of which function belongs to which product, not separated code.** The code does not survive a cloud rebuild. The record does, and it is sections 5, 7 and 10 of this document.

**Recorded by amendment 480 of `2026-07-25_CONSOLE_DESIGN.md`.**

---

## 1. ~~Two products, sold two ways~~ **One product line, and a capture-only variant that does not exist yet**

**Intellibills, the receipts capture app.** ~~Sellable on its own to a firm that keeps its books elsewhere: Xero, QuickBooks, a CSV, or IntelliBooks. It must therefore be **complete without IntelliBooks**, including having its own front end, because a standalone customer has no other screen to borrow.~~ **STRUCK 2026-09-15 BY AMENDMENT 480, on section 0 points 2, 3 and 4. It is not sellable on its own today and would need connectors to QBO, Xero and the rest first. A spin-off is an option being kept open and would be the cloud version, so completeness of this local build is not an obligation on it. A standalone shell would still need a front end, and that is recorded at section 7.**

**IntelliBooks, the bookkeeping app.** **Never sold on its own.** It is Intellibills plus the books. One login, one client list, one bill.

~~Both possibilities are live, and "both" is the stricter constraint. Standalone means each product must be complete. Sold together means the join must be a declared interface rather than a convenience.~~ **STRUCK 2026-09-15 BY AMENDMENT 480, on section 0 point 6. They are not two independent systems, so "both" is not a live constraint. What survives is that the join is worth declaring.**

## 2. Where the line falls

> **Intellibills owns the document and everything read from it. IntelliBooks owns the books.**

That is the whole test. For anything new, ask: **is this a document function or a books function?**

**An earlier version of this sentence said the boundary was the publish step, and it was wrong.** It quietly equated "after publish" with "bookkeeping", and those are not the same thing. Section 6 below is the case that proved it. The phrasing is recorded here as rejected so nobody reinstates it.

## 3. The rule

~~**No function may live only in the other product.**~~ **STRUCK 2026-09-15 BY AMENDMENT 473, on Paul's finding. The struck sentence is symmetric and this rule is not. It is replaced by: NO INTELLIBILLS FUNCTION MAY LIVE ONLY IN INTELLIBOOKS.** If Intellibills needs something in order to work, that thing must be inside Intellibills. It may not sit in IntelliBooks and be borrowed. **Those two sentences were always one way round, and so is the asymmetry two paragraphs below. The struck headline contradicted both, and it was the one that got quoted because it was the bold one.**

~~**The test is one question: take IntelliBooks away. Does Intellibills still work?**~~ **REPLACED 2026-09-15 BY AMENDMENT 480 with Paul's own form of it, which returns a list instead of a verdict: WHAT WOULD COME OUT TO LEAVE INTELLIBILLS ALONE? It is a test and not a rule, per section 0. Run on `IntelliBooks-Desktop-v3.html` on 2026-09-15: Bank Transactions and Reports come out whole, Receipts, Clients and Firm Settings stay whole, and Client Data and Client Settings split. The two that split are the watch list.**

**And the dependency runs one way only.** IntelliBooks is never sold alone, so **IntelliBooks may depend on Intellibills for anything; Intellibills may depend on IntelliBooks for nothing.**

That asymmetry is why one client registry owned by Intellibills is permitted rather than a breach: client identity is not something IntelliBooks lacks, it is something the combined product takes from the part that is always present.

## 4. What this forbids, and what it does not

**Forbidden:** a function belonging to Intellibills that can only be performed inside IntelliBooks.

**Not forbidden:** IntelliBooks displaying Intellibills' work. That is what the combined product should do, so the operator works in one window rather than two. Intellibills owns the function; IntelliBooks may surface it.

**Also forbidden: naming.** Nothing in Intellibills may be named after IntelliBooks. No constant, no adapter, no field. An adapter is named for what it does; the address it writes to is configuration. **Intellibills publishes to the destination configured for that client and does not know what is at the other end.**

## 5. ~~Four breaches, and how they arose~~ **Four Intellibills functions that live only on IntelliBooks' screens**

~~Three breaches found on 2026-08-18.~~ **Three were found on 2026-08-18 and a fourth on 2026-08-20.** The heading was corrected rather than left to contradict its own table.

None of these was a decision to put an Intellibills function inside IntelliBooks. **Each was a reasonable decision about something else, whose side effect was a breach.** That is the pattern to watch for, and it is why the rule has to be applied deliberately rather than relied on to be obvious. **REFRAMED 2026-09-15 BY AMENDMENT 480. Under section 0 these are not breaches of anything binding today. The table below is the list of what a capture-only product would have to be given, and that is what it is worth. The word breach is left standing in the table so the history reads straight.**

| Breach | Why it happened |
|---|---|
| **Add Receipts.** Getting a document into the capture stream is Intellibills' work, and the only way to do it by hand is a button inside `IntelliBooks-Desktop-v3.html`. | IntelliBooks had a screen and Intellibills did not. |
| **The Review queue.** Clearing an exception is Intellibills' work, and the only screen that can do it belongs to IntelliBooks. | The same reason. |
| **The copy into `Clients\`.** Filing a document into the firm's client folder is a document function, and it could only happen at Post, which is a bookkeeping event. | A good decision about **when**, whose moment happened to exist only in one product. See section 6. |
| **Creating and editing a client.** Added 2026-08-20. Registering a client is Intellibills' work, and the only way to do it is **+ New Client** and the **Edit** row on IntelliBooks' **Clients** tab. | The same reason as the first two: IntelliBooks had a screen and Intellibills did not. **It was missed on 2026-08-18 because that day's inspection went through the Receipts tab and this control is on the Clients tab.** |

**A fourth breach, found 2026-08-20 while settling the field list for the one registry, and it is the same class as the first two rather than a new kind.** Take IntelliBooks away and standalone Intellibills has no way to register a client except editing a file by hand, which is not a function of a product being sold.

**Paul's resolution, 2026-08-20, and it costs nothing new: standalone Intellibills' own shell carries an Add Client item on its menu.** Section 7 already says that shell has to exist and is not designed, so this becomes one more item on it rather than separate work. **Recorded rather than solved for now**, which is deliberate: the shell is not being designed yet and a client can be registered today.

**Amendment 105 sharpens it and does not close it.** After the one-registry change, IntelliBooks' New Client dialog writes into Intellibills' own store. Section 7 condition 2 permits that, since the shared client registry is named there explicitly, so it is not a new breach. What stays broken is that **the function still lives only on IntelliBooks' screen.**

## 6. The worked example: filing into the firm's client folder

**The function.** Put a copy of a receipt image into `{top folder}\{client_folder_name}\Receipts\{tax year}\`.

**Whose is it?** No transaction, no ledger, no category, no VAT. A firm capturing receipts and publishing to Xero wants it as much as a firm keeping its own books. **It is a document function, so it is Intellibills'.**

**How it broke.** The trigger chosen was Post. Paul's reasoning was sound: a folder fed straight from capture shows the client everything that arrived, duplicates and misfires included, so a client on a portal sees a dump of files. Posting is the point at which a document has been accepted.

**But "accepted" had two meanings and only one was noticed.** Accepted into the accounts needs books. Accepted by the capture system — validated and published successfully — needs neither, and serves the same purpose, because nothing that failed validation, needed review, or was flagged as a possible duplicate ever publishes.

**How it was found.** Not by inspection. By Paul asking what happens in the standalone version. The rule turns "is this sensible" into "would this work if IntelliBooks were not there", and the second question catches what the first cannot.

**The resolution.** The function belongs to Intellibills, with **two triggers, set per firm**: on successful publish, or at Post, or never. Standalone Intellibills can only offer the first. The combined product offers either. Recorded in the design document.

## 7. The Receipts tab

**The Receipts tab is Intellibills' front end, hosted inside IntelliBooks' shell**, because locally that shell is the only one there is. **The conflation is in the hosting, not in the functions.** Hosting is not ownership.

**It keeps the name Receipts.** Renaming it to Intellibills was considered on 2026-08-18 and withdrawn.

**Three conditions make that real rather than a label:**

1. Its code calls no books functions~~, and no books code calls into it~~. Physically in the same file, logically separate. **The second half struck 2026-09-15 by amendment 473, on Paul's finding. Section 3 lets IntelliBooks depend on Intellibills for anything, so books code calling into this tab is not a breach. It is also not true of the built product: nine books-side functions in `IntelliBooks-Desktop-v3.html` read `books.receipts`, being `editTxn`, `renderBank`, `refreshMatches`, `handoverPack`, `exportClientBackup`, `categoryReferences`, `ensureAcct`, `migrateBooks` and `taxYearRange`. The half that survives is the half that carries the separation: this tab's code calls no books functions.**
2. It reads and writes only Intellibills' stores, plus the shared client registry.
3. Its access to `Clients\` is legitimate, because client-folder filing is Intellibills' function.

**And it may act on Intellibills' own files directly.** Intellibills locally is two parts, a Python worker and a front end, and both are Intellibills. The front end deleting a file the worker wrote is Intellibills managing its own store, not a boundary crossing. No message is needed and there is no delay.

**Two honest caveats.** The browser's folder permission is a single grant covering everything, so the separation is held by discipline and not enforced by the platform. And ~~**standalone Intellibills will need its own shell** to host this front end: locally, either a second HTML file or the same file with the books parts switched off. That is work the boundary implies rather than a new cost.~~ **REFRAMED 2026-09-15 BY AMENDMENT 481, on section 0. NOBODY OWES THIS WORK. A capture-only product is an option being kept open, not a plan, and if it is ever built it is the cloud version, which gets a web front end from scratch. What is recorded below is what such a shell would have to carry. It is a record, and it is the part that survives a cloud rebuild.**

**What that shell would have to carry, added 2026-08-20 and kept here so it accumulates in one place rather than being rediscovered. "Has to" became "would have to" on 2026-09-15 by amendment 481: it is a list of what would be needed, not a list of what is owed.** The Receipts tab itself, per this section. **Add Client and Edit Client**, per the fourth breach in section 5, which is Paul's resolution of it. **Firm Settings and Client Settings**, because `2026-08-20_LIST_settings_firm_and_client.md` establishes that all 18 firm settings belong to Intellibills and none to IntelliBooks, so a standalone product with no settings screen would have nothing a customer could configure. **The list is not the design**, and the shell is still not designed.

### The five things on that tab that depend on the books

**Omitted in the standalone product:**

1. Attach to a bank transaction.
2. Post to cashbook.
3. Post Selected, the bulk version.
4. The attached / not attached marker, and the filter that defaults to it.

**Re-sourced rather than omitted:**

5. The category dropdown. A standalone Receipts App still needs a category, because it publishes a code. What changes is where the list comes from: the books file today, `IntelliCharts` standalone.

Everything else on that tab — Add Receipts, the Review queue, the receipt list, the filters, the tax-year picker, Delete — is identical in both products.

## 8. Add Receipts is already correctly shaped

Worth recording because it is the only part of that tab that was already right.

It writes into `Intellibills\Receipt Inbox\{...}\`, which is **the receiver's own folder**. That is a push into somebody's inbox, the same shape the receipt handoff is moving to. In the cloud it becomes a POST to an intake address with no design change.

Its function belongs to Intellibills. Its control sits on IntelliBooks' screen. Both are correct.

## 9. One client registry

**One client registry, owned by Intellibills.** IntelliBooks does not hold its own client list. Book-only attributes, being entity type, partners, year end and the MTD flags, are added to the Intellibills client record rather than held separately. ~~and VAT scheme~~ **VAT scheme struck 2026-08-21 by amendment 142: the field is deleted at step 10e because nothing read it, and Paul will ask for it when he wants it.**

**Why Intellibills owns it:** it is the product that exists in every configuration. In the combined product the books are added to an Intellibills client, never the reverse.

**Why not two registries with a shared key:** that is the worst of the three options, because it keeps the duplication and adds an obligation to keep the two in step. It is also what existed before this decision, and on 2026-08-18 the two lists had **no client in common at all**, with nothing checking and nothing reporting.

The field names are in the design document.

## 10. Settings

**Two levels: Firm Settings and Client Settings.** Within each, two sub-headings: **Intellibills Settings** and **IntelliBooks Settings**.

There is no third, system level on any page. Everything above firm level is either an engineering constant nobody should change — the extraction engine, the AI model, the validation tolerance, the poll interval, internal naming — or a secret that belongs in environment configuration. Neither is a setting in the sense of something a user changes.

**Bank Accounts, Categories and Learned Statement Rules are not settings.** They are the client's working data. They move to a tab named **Client Data**.

## 11. What changes hands when the product is sold

Recorded because nothing else records it, and because these four move in the opposite direction from everything else: they are Paul's today and become the vendor's in a sold product.

1. **The Azure app registration** the capture app uses to write into OneDrive: tenant id, client id, client secret.
2. **The alert email account** and its SMTP credentials.
3. **The capture app's address.** Today a Netlify deployment Paul owns. In a sold product there is one capture app and it is the vendor's.
4. **Date interpretation.** A UK-only product decides day-first once; a product sold abroad cannot.

## 12. The standing danger

**The overlap that exists today was designed in for expediency, one convenience at a time.** Something needed a home, one product had a convenient place, and it went there.

Every one of those decisions was reasonable on the day. **None of them was a decision about the boundary**, which is precisely why they were invisible. ~~The bill arrives the first time Intellibills is offered to a firm that does not want the books, and by then it is in a dozen places.~~ **STRUCK 2026-09-15 BY AMENDMENT 480, on section 0 points 3 and 4. That bill does not arrive in this form, because a spin-off would be a cloud rebuild and none of this code goes with it. What is still worth having is the record of which function belongs where, because that is what does survive the rebuild.**

A breach you argue for is one you can weigh. A breach that arrives as a side effect of a good decision about something else is one you only find by going looking.

~~**So the question gets asked deliberately, every time: would this still work if IntelliBooks were not there?**~~ **REPLACED 2026-09-15 BY AMENDMENT 480 with section 3's replacement test: what would come out to leave Intellibills alone? Asked deliberately, and asked for the list it produces rather than for a yes or a no.**

---

## Still open

- ~~**Where Client Settings live in the menu.** Deferred until the settings list exists.~~ **Proposed 2026-08-20: a Client Settings item in the centre menu group, beside Client Data.** Not yet decided, and it comes after the one registry rather than before it, per amendment 110.
- ~~**The settings list itself**: every firm and client setting, which product owns it, whether it exists or is proposed, where it is stored, where it is entered, and where it should appear.~~ **Done 2026-08-20: `2026-08-20_LIST_settings_firm_and_client.md`, 38 rows, 30 existing and 8 proposed.** Its finding for this document is that **all 18 firm settings belong to Intellibills and none to IntelliBooks**, so the Firm Settings page's IntelliBooks Settings heading is correctly empty rather than incomplete.
- ~~**Standalone Intellibills' own shell.** Named in section 7 and not designed. What it has to carry is now listed there.~~ **CLOSED 2026-09-15 BY AMENDMENT 481, on section 0. It is not an open item, because it is not work anyone owes. It is not designed and it does not need to be. What it would have to carry stays listed in section 7 as a record.**

**Confidence.** High on every decision recorded here: those in sections 1 to 12 were taken by Paul on 2026-08-18 in one working session, and the 2026-08-20 additions in sections 5, 7 and Still open were taken by him on 2026-08-20. Nothing in this document is inferred. High on all **four** breaches in section 5, each established by reading the code rather than the design document; the fourth was found on 2026-08-20 by reading the Clients tab markup, which the 2026-08-18 pass did not cover because it went through the Receipts tab. Section 11's allocation is the consultant session's judgement and is flagged as such.

**Dates in this document.** It was written on 2026-08-20 and its filename says 2026-08-18. **That is deliberate and it is not renamed**, per amendment 109 of `2026-07-25_CONSOLE_DESIGN.md`: renaming it would break every reference to it while leaving the same mistake in the commit that introduced it. The decisions it records were taken between 2026-08-18 and 2026-08-20 and cannot now be dated individually.
