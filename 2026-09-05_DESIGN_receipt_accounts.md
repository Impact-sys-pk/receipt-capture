# The receipt accounts list

**Written 2026-09-05 by the consultant session, on Paul's decisions of the same day.** Amendments
224, 225 and 226 of `2026-07-25_CONSOLE_DESIGN.md` are the dated trail. **This document is what to
read to understand the thing.** The build order is step 10j of that document, 11 sub-steps.

**Confidence.** High on every count and every file property below: each was read from the file on
2026-09-05, and the reads are named where it matters. High on the decisions, which are Paul's and
were taken in this session. **Nothing here is inferred from a summary.**

---

## 1. What this is

**A list of the accounts a receipt can be, owned by Intellibills.**

Intellibills' classifier has to answer in some vocabulary. Until 2026-09-05 it answered in the
client's own published chart of accounts. From step 10j.10 it answers in this list, and the answer
is then resolved to an account in the client's chart.

**The list is 66 rows and every code in it is a four-digit master code.** No new identifier scheme
was invented, because the master code already is a permanent identifier.

## 2. Why the vocabulary had to change

**A learned vendor mapping is only worth anything in a vocabulary its owner controls.**

- "Halfords is vehicle repairs and servicing" is true for every customer there will ever be
- Learned against one client's account code it is worth nothing to the next client, whose chart is
  numbered and named differently
- Learned against a shared list, every customer benefits from every correction anyone ever made

Three smaller reasons, all of them consequences of the same property:

- It works for a client with no chart at all
- A client renaming accounts, or moving from one bookkeeping product to another, touches the
  resolution and not the classifier
- An account that cannot be resolved becomes a review item rather than a posting to the wrong
  account

**Item 152 of `2026-08-20_LIST_outstanding_items_and_decisions.md` is where this was argued and
settled.** It offered two candidates. **What was decided is neither of them as written**: it takes
the shared-vocabulary benefit and keeps the master's codes as the identifiers.

## 3. Why the master's codes work as identifiers

**Read on 2026-09-05 across the eight library charts in `Intellibills\Charts\`:**

- 927 rows in total
- **0 codes that are not master codes**
- **0 rows where the name, the SA103F box or the VAT treatment differs from the master**

**A library chart is a strict subset of the master.** So inside this practice the resolution from a
receipt account to a client's account is code equality, and a mapping table would map each code to
itself.

**Section 1 of `IntelliCharts\2026-08-05_NOTE_master_chart_of_accounts.md` is why there was nothing
to adopt instead.** No cross-vendor UK chart of accounts standard exists. XBRL GL is chart-neutral,
SAF-T is a submission format, Sweden's BAS has no UK equivalent, and the FRC taxonomies tag reported
figures rather than accounts. Portability is per-app mapping in every case.

**Section 2 of that note is why the codes travel.** They match Sage 50's published default ranges,
and Sage Accounting's ranges nest inside them. Sage 50 is the only product where the code decides
which report an account appears on.

## 4. How the 66 were cut

Start from the master's `classifier_eligible = Yes` accounts. **95 of its 240**, being 90 expense
accounts and 5 asset accounts.

| Removed | Count | Why |
|---|---|---|
| No supplier receipt evidences it | 24 | Payroll, journals, bank and finance statements, employee claims, HMRC notices |
| Capital additions `0051`, `0061`, `0071`, `0081`, `0091` | 5 | **Paul's ruling, 2026-09-05** |
| **Remaining** | **66** | Every one an expense account |

**On the capital additions, because the reasoning matters more than the list.** Layer 5 answered
`0081 Motor vehicles - cars - additions` for a Halfords receipt. A gate on the amount was designed
and then dropped: **a materiality threshold applies on the accruals basis only, under the cash basis
capital spend is an expense, and Paul's judgement is that the number of items this applies to is
relatively small.** So the classifier does not propose them, a capital purchase reaches a person,
and there is no threshold logic to build or maintain. **Item 33, the materiality threshold, stays
open and no longer blocks anything here.**

**On the four catch-alls, which were argued against and kept.** `7300 Motor expenses`,
`7390 Other Vehicle expenses`, `7500 Printing, postage and stationery` and `8250 Sundry expenses`
are all in the 66. **Paul's ruling: a chart needs them.** The risk is real and was demonstrated:
before line items existed, an Asda fuel receipt was answered `8250 Sundry expenses`. **The
mitigation is that every layer 5 answer carries `confidence = low` and `needs_review`, so none of
them posts unseen.**

## 5. The three files, and who owns each

| File | Holds | Owner | Published |
|---|---|---|---|
| `worker\categorisation\receipt_accounts.csv` | The 66, with VAT treatment, recoverability, SA103F box, MTD category, synonyms | **Intellibills** | No. Shipped with the code |
| `Intellibills\Charts\<chart>.csv` | The accounts one client actually has | IntelliCharts | Yes, into both bundles |
| `Intellibills\Charts\fallback_accounts.csv` | Where an absent account collapses to | IntelliCharts | Yes, into both bundles |

**`receipt_accounts.csv` is seeded from `COA_MASTER_v2.xlsx` and then frozen.** It is versioned in
git with the code. **It must never be read from IntelliCharts at run time**: an Intellibills sold on
its own has no IntelliCharts to read.

Its columns: `code`, `name`, `fallback_code`, `synonyms`, `vat_default`, `vat_variable`,
`vat_recoverability`, `sa103f_box`, `mtd_itsa_category`, `vat_explanation`. **`synonyms` is empty
today.**

## 6. The fallback

**A library chart is a subset, so the account the classifier picks is often not in the client's
chart.** Counted 2026-09-05 against the 66:

| Chart | Holds | Absent |
|---|---|---|
| `SALE_OF_SERVICES` | 41 | 25 |
| `SALE_OF_SERVICES_LTD` | 41 | 25 |
| `SALE_OF_SERVICES_PARTNERSHIP` | 41 | 25 |
| `SALE_OF_GOODS` | 45 | 21 |
| `SALE_OF_GOODS_LTD` | 45 | 21 |
| `SALE_OF_GOODS_PARTNERSHIP` | 45 | 21 |
| `FIN_ADVISER` | 38 | 28 |
| `PHV_DRIVER` | 29 | 37 |

**These were first written as 44, 49, 40 and 30**, counted against a 71-account cut before the five
capital additions came out and made it 66. **Corrected 2026-09-05**, and the wrong figures reached
`publish_master.py`, step 10j.8 and a Claude Code brief before they were caught.

**An absent account is the ordinary case, not the edge one.**

**Paul's ruling, 2026-09-05: a car wash goes to `7310 Vehicle repairs and servicing` where the
client's chart does not hold `7391 Car wash`.** Which account an absent one collapses into is an
accounting fact about the account, so it is recorded per account and never inferred at run time.

**Where it lives.** `Master!N`, a column named `fallback_code`, **deliberately outside
`MASTER_COLS`** in `publish_master.py`. `read_master()` compares only the first `len(MASTER_COLS)`
header cells, so a fourteenth column is invisible to it and **no published chart file gains a
column**. The banner moved from `N1` to `O1` to make room.

**What is published.** `write_fallbacks_csv()` generates `fallback_accounts.csv` from that column,
two columns and only the accounts that have a fallback. **An account absent from the file has no
fallback, and that means Review.**

**What `validate_fallbacks()` refuses**, so none of it is re-checked downstream:

- A target that is not an account in the master
- A target that is the account itself
- A target whose status is not `active`
- **A target that itself carries a fallback. One hop only**, so there is no chain to walk and no
  cycle to detect at run time

## 7. What happens to a receipt

Layers 0 to 5 are `CategorisationEngine.categorise()` in `worker\categorisation\engine.py`,
documented in `CATEGORISATION.md`. **They stop at the first that answers.**

1. `normalise_description()` then `extract_vendor_key()` turn the supplier into `vendor_code`
2. **Layer 0**, client rules
3. **Layer 1**, client vendor, exact on `(client_id, vendor_code)`
4. **Layer 2**, firm vendor, exact on `(business_type, vendor_code)`
5. **Layer 3**, fuzzy against the client's vendors, threshold 0.70
6. **Layer 4**, fuzzy against the firm's, same threshold
7. **Layer 5**, the AI. It is given the supplier name, the gross amount and the line items, and it
   chooses one entry. **Off by default: `enable_ai_fallback` is `False` and the live pipeline
   constructs the engine with it off**
8. Nothing answered: `unmatched`, `needs_review`, and **no code is invented**

Then the resolution, step 10j.8, **BUILT 2026-09-05**, at all five `categorise()` call sites:

1. The code is in the client's chart: use it
2. Not in the chart, and the fallback table gives one that is: use the fallback, **and record the
   substitution as a `resolution_events` row with `actor` pipeline.** No column that means a person
   changed it is written by a machine
3. Neither: no code, the row is flagged, and the note says which account was suggested
4. The chart could not be read at all: **the suggestion is left standing**, because an empty read
   means the file was unreadable rather than the code being wrong, **and the row is flagged**

**`needs_review` flags the row and does not move the file. It is written by four call sites and read
by nothing**, enumerated from the syntax trees by Claude Code on 2026-09-05 and now held by two
tests. **What routes a receipt to the Review folder is `validation.status`**, which is a different
thing. Anything in this project that says a categorisation "goes to Review" is using the word
loosely, this document included until it was corrected.

## 8. Where learning goes, and it is the point

**Nothing in this system has ever learned a vendor mapping. All four learned tables hold 0 rows,
read from `receipts.db` on 2026-09-05.**

- Learned rows must key on **receipt account codes**, not on the client's chart account
- Section 11.3 forbids learning automatically. One correction against a misread supplier name would
  poison the table and layers 1 and 2 would then apply it confidently to every future receipt from
  that vendor
- **Learning is an opt-in tick**, "Remember this code for future receipts from this supplier",
  default off. **Two of the three parts are missing, not three**: `worker\resolution\service.py:100`
  carries `remember_gl_for_supplier` on the corrections record and `:756` acts on it. **What does not
  exist is the control in IntelliBooks Desktop and a field in the 12.2 back-feed payload to carry it**,
  so the flag is always false in practice and that is why the tables are empty

**Step 10j.11.** Every other sub-step improves one answer at a time. **Only this one compounds, and
it is the whole argument for owning the vocabulary.**

## 9. What is standalone, and what is not

`2026-08-18_BOUNDARY_two_products.md` rules on Intellibills against IntelliBooks and says nothing
about Intellibills against IntelliCharts. **Its test still applies: take the other product away,
does this one work.**

- Intellibills needs a vocabulary to classify into. **That is a document function, so it ships
  inside Intellibills.** The 66 ship
- Intellibills does not need a chart of accounts. **Posting to an account is a books function.**
  The eight library charts do not ship
- **Paul, 2026-09-05: "There is no way I would include industry charts without IntelliCharts."** A
  standalone customer already has a chart and maps the 66 to it. A customer with no chart at all
  buys IntelliCharts as well
- **A firm not using this master needs a real mapping table**, receipt account to their account.
  Nothing built anticipates it, and nothing needs to, **provided learning keys on the 66**

## 10. What is built, as at 2026-09-05

| Built | Not built |
|---|---|
| Layer 5 works at all, 10j.1 | The two `service.py` call sites, 10j.6 |
| Supplier name reaches it, 10j.2 | The pipeline reads the fallback, 10j.8 |
| Gross amount reaches it, 10j.3 | Layer 5 chooses from the 66, 10j.10 |
| Line items extracted, 10j.4 | Learning, 10j.11 |
| Layer 5 uses all three, 10j.5 | |
| The fallback column and its publish, 10j.7 | |
| `receipt_accounts.csv` placed, 10j.9 | |

**Layer 5 had never returned an answer before 2026-09-05.** `_ai_suggest()` passed
`response_format` as a dict, and `client.beta.chat.completions.parse()` only parses the reply when
it is given a model class, so `message.parsed` was always `None` and every call logged
`AI response invalid` while the answer sat unread in `message.content`. Read from `openai` 2.34.0
in the repository's own `.venv`.

**The one measurement that exists.** Six real receipts, extracted and categorised on 2026-09-05
with the AI layer on:

| Supplier | Answer | Verdict |
|---|---|---|
| ASDA, diesel | `7301 Fuel and oil` | Correct |
| Morrisons, diesel | `7301 Fuel and oil` | Correct |
| Tesco PFS, diesel | `7301 Fuel and oil` | Correct |
| Tesco, diesel | `7301 Fuel and oil` | Correct |
| Windsor Yards Car Park | `7340 Parking and tolls` | Correct, on the supplier name alone |
| IMO Car Wash Merton | `7300 Motor expenses` | The catch-all. `7391` is absent from that chart and the fallback is not read yet |

**Five of six. Earlier the same day, before the supplier name and the line items reached layer 5, it
was nought of six.** Three of the six are supermarket names and are fuel: **the line items are what
decides them, and `ASDA` with no line items had been answered `7520 Stationery and office
supplies`.**

## 11. Open

- **Synonyms.** Empty on all 66. Needed for matching a firm's own account names at 10j.10 and
  beyond
- **How a substitution is recorded** when the fallback fires. Named in the brief, not decided
- **`categorisations.vendor_key` is `None` on every row** and always will be: it is set only on
  layers 1 to 4, which cannot fire while the tables are empty, and there is no `vendor_code` column.
  **So the table does not record which vendor an unmatched receipt was for**, which is the join a
  later measurement and the learning control both need
- **`trade` is `UNSPECIFIED` on all five clients**, read from `Intellibills\clients.json`, so layer
  2's pool is one undifferentiated pool
- **The remaining 65 fallbacks.** One is filled in. The rest are Paul's judgement, one pass down the
  list, and blank means Review in the meantime

## 12. What must not happen

- **Intellibills must not read `IntelliCharts\` at run time.** It reads its own shipped list and the
  published bundle it owns
- **Nothing writes into `Intellibills\Charts\`.** The flow is one way
- **Nothing reads `IntelliBooks\Charts\`.** Same content, other product's copy
- **No second hop on a fallback.** `publish_master.py` refuses one on purpose
- **No silent substitution.** A receipt whose account was swapped must be distinguishable from one
  posted where the classifier said
- **`enable_ai_fallback` stays `False` by default.** Layer 5 costs an OpenAI call per unknown vendor
