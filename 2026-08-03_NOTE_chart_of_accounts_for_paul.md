# Chart of accounts, draft 2, for Paul to mark up

**Written 2026-08-03 by the consultant session.** ~~Companion to `C:\LastingImpact\receipt_capture\chart_of_accounts_DRAFT2_2026-08-03.csv`.~~ **That CSV was deleted from disk by Paul on 2026-09-01. Struck 2026-09-02 by amendment 167 of `2026-07-25_CONSOLE_DESIGN.md`. It survives in git as blob `0dd8a06d012416f3d7273313d81fd40c27f0a586`, 8,583 bytes.**

~~`C:\LastingImpact\receipt_capture\chart_of_accounts_DRAFT.csv` is untouched and stays as the record of what the vendor mappings produced.~~ **Deleted from disk by Paul on 2026-09-01. Struck 2026-09-02 by amendment 167 of `2026-07-25_CONSOLE_DESIGN.md`. It survives in git as blob `46c04a03d11c3dd718243c83592614e5f749e38d`, 1,504 bytes.** **This file stays in the repository root under step 10h and neither CSV does, so the two sentences above are struck rather than deleted.**

**Mark up the CSV, not this file.** This file exists for the four things that do not fit in a CSV cell.

---

## What the draft does

42 data rows, up from 23. Every one of the original 23 codes and names is unchanged, verified programmatically after writing. `vat_treatment`, `qbo_detail_type` and `xero_tax_type` are now populated on all 42, where before all three were empty on all 23.

| | Before | After |
|---|---|---|
| income | 0 | 2 |
| expenses | 20 | 30 |
| assets | 2 | 4 |
| liabilities | 1 | 4 |
| equity | 0 | 2 |

VAT treatment across the 42, using only 18.4's six permitted values: `20%` on 20, `Not set` on 11, `Outside scope` on 6, `Exempt` on 5. **`5%` and `0% zero-rated` are used as a default on nothing**, which is deliberate: both occur as overrides on individual transactions rather than as the ordinary case for any whole category.

Every `hmrc_box` value is one of the fifteen keys in `HMRC_BOXES` at `IntelliBooks-Desktop-v3.html:359-374`, checked programmatically. One expense row has no box, code 386, which is carried forward from the original draft and is question 3 below.

---

## 1. The chart cannot say "standard rated but the input tax is blocked", and that is a real gap in 18.4

18.4's six values are `20%`, `5%`, `0% zero-rated`, `Exempt`, `Outside scope`, `Not set`. **None of them describes a supply that carries VAT which cannot be recovered.** Three ordinary cases fall in that hole:

- **A car.** The supply is standard rated. Input tax on a car is blocked unless it is used exclusively for business, which a PHV car normally is not. Code 603.
- **Business entertainment.** Standard rated, input tax blocked. It shares HMRC box `advertising` with marketing, so it lands on code 260, which carries `20%`.
- **Home EV charging.** A 5% domestic supply with recovery restricted to the business proportion. Code 105.

Set the rate and the system will imply recovery. Set `Outside scope` and the accounts misdescribe the supply. **I have set the rate in all three and put the warning in the `notes` column, which is the weaker of the two wrong answers rather than a right one.**

This is a decision for you and it belongs in section 18.4, not in a CSV note. Three ways out that I can see: a seventh value; a separate boolean column for recoverability; or accept that the rate is only a default and rely on the override, which is what 18.4 already says a category's rate is.

## 2. Two charts exist and they disagree, and on the Desktop side the name is the primary key

This is the substance of 18.10's "it is the shared vocabulary", sharper than the wording suggests. `DEFAULT_CATEGORIES` at `IntelliBooks-Desktop-v3.html:381` gives every new books file 21 categories, confirmed against `IntelliBooks\Books\PKPH-books.json` which was created from nothing on 2 August. Section 13 of the design document records that **a category has no identifier and its name is the key**, and that there is no rename feature.

So the same account exists twice under two spellings, and neither side can be corrected by editing the other.

| Desktop's name, which is its key | This chart | Note |
|---|---|---|
| Sales income | 001 Sales income | ADDED, adopted Desktop's spelling |
| Other income | 002 Other income | ADDED, adopted Desktop's spelling |
| Cost of sales | 101 Cost of sales | ADDED, adopted Desktop's spelling |
| Motor expenses | 283 Motor Expenses | **Differs by case only.** NTFS-style collision, and section 18.2c rule 2 already records what that costs |
| Fuel | 106 Fuel | ADDED |
| Parking and tolls | 104 Parking & Toll Charges | **Different words** |
| Travel and subsistence | 284 Subsistence, 285 Lodging/Hotels | Desktop has one, this chart has two |
| Software and subscriptions | 269 Computer Software | **Different words** |
| Office costs | 270 Office costs | ADDED |
| Phone and internet | 274 Telephone | **Different words** |
| Insurance | 320 Insurance, 282 Motor Expenses - Insurance | ADDED 320. Desktop files insurance under `premises`, this chart files motor insurance under `travel`, so **one word reaches two HMRC boxes** |
| Professional fees | 292 Accountancy Fees, 293 Legal and professional fees | ADDED 293. Desktop has one, this chart now has two |
| Advertising and marketing | 260 Advertising and marketing | ADDED |
| Bank charges and interest | 362 Interest Payable, 363 Bank/Finance Charges | **Desktop merges what this chart splits** |
| Repairs and maintenance | 300 Repairs and maintenance | ADDED. Premises work. Vehicle maintenance stays at 281 |
| Staff costs | 210 Staff costs | ADDED |
| Sundry expenses | 390 Sundry expenses | ADDED |
| Drawings | 921 Drawings | ADDED |
| Capital introduced | 922 Capital introduced | ADDED |
| Equipment | 601 Equipment, 271 Office Equipment | ADDED 601. See question 2 below |
| Loans | 740 Loans, 731 Bounce Back Loan | ADDED 740 |

**Where I added a row I took Desktop's spelling exactly, so that half needs no decision.** Where a code already existed I changed nothing, because renaming an account that 100 vendor mappings point at is your call and not a drafting choice. Six rows in the middle column need a decision, marked in bold.

## 3. The numbering is FreeAgent's, verified, and two codes sit outside their range

The 23 codes and names in the original draft are exactly the distinct `nominal_code` and `account_name` values in `Intellibills\categorisations_client_vendors_cleaned.csv`, so the chart was never designed; it is whatever the mappings happened to contain.

The scheme is FreeAgent's. Its published ranges, from its own API documentation at https://dev.freeagent.com/docs/categories:

| Group | Range |
|---|---|
| Income | 001 to 049 |
| Cost of sales | 096 to 199 |
| Admin expenses | 200 to 399 |
| Current assets | 671 to 720 |
| Liabilities | 731 to 780 |
| Equity | 921 to 960 |

**Every code I added is inside the correct range, and none of them is FreeAgent's own code except 001.** Each is marked ADDED in its `notes` cell.

**Two of the original codes are outside any of those ranges.**

- **620 Prepayments.** Current assets are 671 to 720. 620 is in the 600s.
- **271 Office Equipment** is in the admin expense range, which is right for an expense and wrong for an asset. That is the capitalisation question the original draft already flagged.

I have inferred the 600s to be FreeAgent's capital asset range from a sub-account example in its API docs rather than from a published range table, so **moderate confidence on that inference and high confidence on the six ranges above.** You will know at a glance whether 620 is a mis-code.

## 4. One code carries two different name strings today

`chart_of_accounts_DRAFT.csv`, now in git only, spells code 386 `Motor Expenses - Car Tax - Private Use` with hyphens. `categorisations_client_vendors_cleaned.csv` spells the same code `Motor Expenses — Car Tax — Private Use` with em dashes. One code, two strings, and Desktop keys on the string.

---

## The five questions I could not answer for you

1. **Postage, code 358.** I defaulted it to `Exempt` on the basis that ordinary stamps are Royal Mail's universal service. Couriers and business account mail are 20%. This is the default of mine I am least sure of.
2. **Office equipment: 271 expense or 601 asset?** I drafted both so you can delete one. Keeping both is a third answer and it needs a rule about which one a receipt goes to.
3. **Code 386, the private-use adjustment.** No HMRC box, disallowable, and arguably not an account at all but a journal. It is the only expense row in the file with no box.
4. **Code 283 Motor Expenses is a parent with five children.** I set it to `Not set` so nothing inherits a rate from it, but nothing in the system stops a receipt being posted to it. Should a parent be postable?
5. **VAT liability, code 760.** I added it because it is needed the moment a client registers. All five clients are `vat:false` today. Delete it if you would rather add it when it is needed.

---

**Confidence.** High on everything read from a file: the row counts, the column counts, the two charts' contents, the FreeAgent ranges, the 386 spelling difference, the fifteen HMRC box keys. High on the VAT treatments that are settled law: insurance and interest exempt, VED outside scope, statutory licence fees outside scope, passenger transport standard rated below ten seats. **The judgement calls are the five questions above plus the blocked-input-tax gap, and those are yours.** Every `notes` cell that starts ADDED, CHECK or FLAG marks a place where I made a choice rather than read a fact.
