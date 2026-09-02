# Cloud multi-firm: design inbox

**Date:** 2026-09-01
**Version:** 1.0
**Status:** Not started. Nothing in this document is scheduled and nothing here is a decision except where it says so.
**Authority:** `2026-07-25_CONSOLE_DESIGN.md` is the build authority for Intellibills and IntelliBooks. This document has no authority over either and describes a product that does not exist.

---

## 1. Why this document exists

**Local multi-firm is not built and will not be built. Multi-firm lives only in the cloud.** Paul's decision of 2026-08-20, recorded as amendment 117 of `2026-07-25_CONSOLE_DESIGN.md`, and deliberately absent from section 16 of that document because it is not in the build order.

**The firm work that stays in the local build is preparation, not multi-firm:** `firm_id` carried honestly, `firms.csv` real, and the Firm Settings page, because that page is the specification for what a tenant consists of in the cloud version.

Amendment 117 identified nine local-only constraints that no amount of local work removes. They were held as items 39 to 47 of `2026-08-20_LIST_outstanding_items_and_decisions.md`, in a section headed "Cloud only" that existed so nobody scheduled them locally. **That section was an inbox for a document that did not exist.** This is that document.

**Created 2026-09-01 on Paul's decision.** Items 39 to 46 closed on the same edit and their substance is section 3 below. Item 52 of that list, the cloud version, remains the single open pointer and now points here.

---

## 2. The one architecture question everything else waits on

**Does a firm in the cloud version get its own database, or do firms share one?**

**This has never been decided.** Amendment 146 of `2026-07-25_CONSOLE_DESIGN.md` records Paul's question that killed an earlier recommendation: adding a firm to a table's unique key "only matters if there is a cloud version and only if that version holds several firms in one database". Both conditions were unproven then and are unproven now.

**Three of the eight constraints below rest entirely on it.** Items 44, 45 and 46 are all shapes of the same thing: a table that carries no firm. Give each firm its own database and none of them is a defect, because the database is the tenant boundary. Share one database and all three are.

**So this is the first question of the cloud version's design session, and the eight constraints should not be worked before it is answered.**

---

## 3. The eight constraints

Each is a limit of the local system that no local work removes. The numbers are the outstanding-items numbers they carried until 2026-09-01, kept so the trail survives.

| Was item | Constraint |
|---|---|
| 39 | **One capture mailbox.** `capture@lastingimpact.co.uk`, redirected to `bills@intellitax.co.uk`, one IMAP account. A real product gives each firm its own capture address, which `MULTIFIRM_EMAIL_FORWARDING_ANALYSIS_AND_FINDINGS.md` named as an option and never examined |
| 40 | **One OneDrive.** `ONEDRIVE_USER` on Netlify is a single value |
| 41 | **One Netlify deployment, one Azure app registration, one `AZ_TENANT_ID`** |
| 42 | **One browser folder grant**, so one firm is open at a time |
| 43 | **One practice root and no firm level in any path**, so two firms with a client of the same name collide in `Clients\` |
| 44 | **`email_delta` holds one `delta_link` and one `last_uid` as global singletons.** Rests on section 2 |
| 45 | **`email_alerts` carries `firm_name`, a copied string, and no `firm_id`.** Rests on section 2 |
| 46 | **`statements` carries `client_id` and no `firm_id`, unlike `receipts`.** Rests on section 2 |

---

## 4. The ninth constraint, and where it went

**Amendment 117 says nine and this document carries eight. The ninth is accounted for and is not missing.**

`categorisations_firm_vendors` keys on `business_type` and has no `firm_id`, so in a multi-firm product one firm's learned vendor mapping would apply to another firm's clients. **That is a leak rather than a tier**, which is why it was the one of the nine that got scheduled locally.

It closed on 2026-08-21 as items 17 and 47 of the outstanding items list, on Paul's decision recorded as amendment 146: **a nullable `firm_id`, written and never read**, at sub-step 10d.39 of section 16. The unique key does not change, so the learned pool stays shared and no lookup changes.

**The reasoning is worth keeping here because it is the pattern for the rest.** Pooling is easy to start and impossible to unwind: mappings that accumulate with no record of who taught them can never be separated, because the provenance was never captured. Separating is easy to start and easy to pool later, since a lookup can ignore a column. **So the column is worth having whichever way section 2 is answered.** Anywhere else in this document where the same asymmetry applies, the same argument holds and the deadline is the pilot at step 10i, not the cloud build.

---

## 5. One thing about email that is settled

**Do not relitigate this.** The webhook replaces the poll, so almost none of the local email machinery survives: no MIME parsing, no regex, no routing across eight `INBOX.*` folders.

**But the client lookup does survive**, because an emailed receipt carries no credential and an address is still an address. `MULTIFIRM_EMAIL_FORWARDING_ANALYSIS_AND_FINDINGS.md` says "no `clients.csv` lookup needed", and **that is true of the phone and not of email.**

---

## 6. What this document is not

**It is not a build order and it holds no statuses.** Section 16 of `2026-07-25_CONSOLE_DESIGN.md` is the only build order and the cloud version is not in it.

**It is not the parked-work list.** Item 51 of `2026-08-20_LIST_outstanding_items_and_decisions.md` is the demo version and item 52 is the cloud version; both stay there.

**Nothing here is a defect in the local system.** Every constraint below is correct behaviour for a single-firm product, which is what has been built on purpose.

**Anything added here should be a constraint or a question, not a task.** A task belongs in section 16 once the cloud version is a decision, and it is not one yet.

---

## 7. Provenance

Section 3's eight rows are the text of items 39 to 46 of `2026-08-20_LIST_outstanding_items_and_decisions.md` as at 2026-09-01, moved rather than rewritten. Section 2 is amendment 146 of `2026-07-25_CONSOLE_DESIGN.md`. Section 4 is amendment 146 and the closed rows of items 17 and 47. Section 5 is the closing paragraph of the same list's section 6. Section 1 is amendment 117.

**Before closing items 39 to 46, `2026-07-25_CONSOLE_DESIGN.md` and `CLAUDE.md` were searched for each of the eight numbers individually.** The only hits were on "item 39" and both were change log item 39, a different list. Nothing pointed at any of the eight as an open question.

**Confidence: high**, because every sentence here was read from the file that records it rather than from a summary of it, and the searches were run per number rather than as a range.
