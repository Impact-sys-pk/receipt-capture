# FreeAgent reports, walked through by Paul on 2026-09-22

Written by the consultant session on 2026-09-22, between 11:41 and 12:10 BST, clock read in each reply.

**WHY THIS EXISTS.** Step 10t of `2026-07-25_BUILD_STATUS.md` names four reports: Profit and Loss, Balance Sheet, Trial Balance, Bank Reconciliation. Paul's instruction of 2026-09-20 is that they are modelled on FreeAgent in function only. He drove FreeAgent on his own screen and the session read each page through the Claude extension in Chrome. The tour cannot be repeated cheaply, so what was on the screen is written down here rather than left in the chat.

**WHAT THIS IS NOT.** It is not FreeAgent's wording, styling or artwork, and none of that is to be copied. It records what a report holds and what the operator can do with it. The copyright position is in amendment 530 of `2026-07-25_CONSOLE_DESIGN.md`.

**WHAT WAS READ.** Live data in Paul's practice account, `intellitaxaccountinglimited.freeagent.com`, viewing the client Paul Keating Private Hire at `pkph.freeagent.com`. Every line below was read off a screenshot of the page named, except where it says Paul said so.

## Patterns that run across every report

- **Blue means it drills down.** Every blue figure or label opens the detail behind it. Totals and subtotals are black and do not.
- **A drill down lands on Show Transactions**, `accounting/show_transactions/{from}_{to}/{account code}`, with its own filters for date range, account type and whether there is an attachment, an Apply button, columns Date, Description, Debit, Credit, a Total line, and an Attachments marker at the foot. Descriptions there are blue and drill again.
- **Export Report, top right, offers CSV and PDF. Two options and nothing else**, read off the open menu on the comparative balance sheet. The Bank Reconciliation's button reads Export rather than Export Report.
- **The period is in the URL**, for example `profit_and_loss/2026-04-01_2026-09-22`, so a report as run is addressable.
- **Every named date option carries its actual dates beside it**, so the label never has to be decoded.
- **The accounting years offered are the client's own**, 2025/26 and 2026/27 here, not tax years fixed in code.
- **A warning banner sits above the report when the data is incomplete**, here because of unexplained bank transactions, with a link to the Banking area.
- **Two small layout toggle buttons** sit above each table.

## Profit and Loss

Four views: **Monthly, Quarterly, Yearly, Comparative.**

Date range, five options: Current year to date (01 Apr 26 to Today), Accounting year 2026/27 (01 Apr 26 to 31 Mar 27), Accounting year 2025/26 (01 Apr 25 to 31 Mar 26), Opening balances (01 Apr 25), Custom date range. **Opening balances is offered as a date range rather than as its own report.**

- **Yearly.** Debit and Credit columns. Expandable groups: Cost of Sales, Gross Profit, Administration Expenses, Operating Profit, Drawings, Profit and Loss journal entries, Retained Profit this period, Retained Profit brought forward, Distributable Reserves / Retained Profit carried forward. **It is the only view that runs past Operating Profit.**
- **Monthly.** One column per month, Apr to Sep, under a 2026 year header, plus Total. Ends at Operating Profit, with a footnote that monthly operating profit excludes depreciation, dividends and income or corporation taxes.
- **Quarterly.** Columns Q1 2026/27 (Apr 01 to Jun 30), Last 3 Months, Total. Ends at Operating Profit with the same footnote.
- **Comparative.** Three controls: Comparison type (Yearly), Period 1, Period 2. Columns Period 1, Period 2, Difference, Percentage change, and an up or down arrow on each row. It shows accounts that are nil in one period, so the row list is longer than either single period, including a Tax-Disallowable Cost of Sales group.

## Balance Sheet

Four views: **Custom date, Monthly, Quarterly, Comparative. There is no Yearly view.**

Date, five options: Today (22 Sep 26), As at 31 Mar 27, As at 31 Mar 26, Opening balances (01 Apr 25), Custom date.

- **Custom date.** Two money columns. Groups: Capital Assets, Net Book Value, Current Assets, Current Liabilities, Net Current Assets, Total Assets, Owner's Equity, Retained Profit, Total Owner's Equity. Bank accounts appear by name as individual rows.
- **Monthly.** Twelve month-end columns, 30 Apr 25 to 31 Mar 26, grouped under 2025 and 2026 headers.
- **Quarterly.** Four "As at" columns three months apart, 22 Dec 25, 22 Mar 26, 22 Jun 26, 22 Sep 26. **A Suspense Account row is shown in red**, including where it is nil.
- **Comparative.** Same three controls as the P&L, with Period 2 offering "Now". Columns Period 1, Period 2, Difference, Percentage change, arrows per row.

## Trial Balance

**No view tabs.** One screen.

Date, five options: Today (22 Sep 26), As at 31 Mar 27, As at 31 Mar 26, Opening balances (01 Apr 25), Custom date range.

- Columns: Account, Debit, Credit.
- **Every account row is blue, so every line drills down.**
- **The account code is on the row with its name**, for example `283 Motor Expenses`, `750-2 Bank Account: PKPH - Starling`. **Codes carry a sub-number where one account has several instances**, 750-1 to 750-4 for the bank accounts.
- The last line is **Trial Balance Check (nearest £)**, showing the debit and credit totals side by side.

## Bank Reconciliation

Two views: **Summary and Full Report.**

Controls on Summary, three: **Bank account picker**, currently PKPH - Starling; **Date range**; **Closing balance**, a box the operator types a figure into, with Apply.

Date range is grouped rather than flat, and scrolls: Custom Range, then By Accounting Year (Accounting Year 2025/26, Accounting Year 2026/27, Current Year to date), then every individual month under year headings 2025 and 2026.

- **Summary rows, in order**: Opening balance with its date, Explained Transactions (Money In), Explained Transactions (Money Out), Manually Added (Money In), Manually Added (Money Out), Closing balance per your Balance Sheet with its date, Unexplained (Money In), Unexplained (Money Out), Closing balance per Banking area, Closing balance per Bank statement, Difference.
- **Six rows drill down**, the explained, manually added and unexplained pairs. The balance lines and the Difference line do not.
- **The typed closing balance lands on "Closing balance per Bank statement" and Difference is the check.** Difference is shown in red.
- **Full Report.** Heading gives the period and the account, `01 Dec 25 - 31 Dec 25 - PKPH - Starling`. Four filters: All transactions, Explained, Unexplained, Manually added. Columns Date, Description, Type, Money in, Money out, Balance. It opens with a Balance brought forward line and carries a running balance down the right. The closing balance is carried in the URL as a query parameter.

## Journal Entries, shown alongside the four

Two tabs: **Posted Journals** and **Recurring Journal Profiles**. An **Add new** button serves both.

- **Posted Journals.** Controls: accounting year picker and a sort order, oldest to newest. Each journal is a block: date, narrative, then its lines showing account code and name, Additional information, Debit, Credit. An **Actions** menu sits on each journal.
- **Recurring Journal Profiles.** One filter with four values: All Profiles, Active Profiles, Inactive Profiles, Invalid Profiles. None exist for this client, and the screen says so rather than showing an empty table.

## What was not looked at

- The Export menus on the individual reports other than the comparative balance sheet. Paul stated that every report exports to CSV or PDF and the one menu opened agreed with him.
- What a CSV or a PDF actually contains. Neither was downloaded.
- The Find and Fix screen, which was on screen at the end of the tour and was not part of it.
- Any report other than the five named here.
