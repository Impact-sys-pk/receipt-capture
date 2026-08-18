# Instruction: which copy of the chart of accounts is authoritative

**Paste this into consultant chat 7. It answers the question you raised and supplements the handover; nothing in the handover changes.**

You were right not to assume. The answer is that there is no rival copy, and I have measured it rather than reasoned it.

---

## 1. The master exists in one place

**`C:\Users\PDK7\OneDrive - Intellitax Accounting Limited\IntelliCharts\COA_MASTER_v1.csv` is authoritative, and there is no other copy of it anywhere on the machine.**

A filesystem search for `COA_MASTER` returns three files and all three are in that folder: the CSV itself, `COA_MASTER_v1.backup_2026-08-17.csv`, and `COA_MASTER_v1.xlsx`, which is a spreadsheet rendering of the same content.

**The Claude project holds no chart of accounts file at all.** It holds four markdown documents and a metadata file. No CSV, no spreadsheet.

## 2. What is in the Claude project, and which are duplicates

Four documents. **Two are byte-identical duplicates, one is unique and worth reading, one is a variant.**

| Document | Also on disk? |
|---|---|
| `2026-08-05_NOTE_master_chart_of_accounts.md` | **Byte-identical** to the copy in `IntelliCharts\`. Same MD5, 24,591 bytes. |
| `2026-08-15_RUNLOG_coa_august_check.md` | **Nowhere else. This is the only copy.** |
| `2026-07-29_HANDOVER_consultant_chat_3.md` | Same name in the repository root, **different MD5**. One has been edited since. |
| `IntelliBooks-Desktop-Handover-2026-07-29.md` | The repository has `2026-07-29_HANDOVER_intellibooks_desktop.md`. Different name, **different MD5**. Related, not the same. |

**So on the chart of accounts specifically there is nothing to reconcile.** The note in the project is documentation *about* the master, not a copy *of* it, and it is the same file as the one in the folder.

## 3. How the master works, in five sentences

**One file is edited by hand: `COA_MASTER_v1.csv`.** Nothing else is.

**`build_coa.py` reads it, validates it, and writes everything else**: the master back out, an import file each for Xero, QuickBooks Online and Sage 50, a mapping table into Sage Final Accounts, and a list of destination exceptions. **If any check fails it writes nothing at all**, so a broken master cannot produce output.

**Two Sage Final Accounts exports sit beside it as reference and the build fails without them.** They are what the drift check compares against, so that Sage renaming an account is caught rather than absorbed.

**One thing it does not write is the IntelliBooks seed.** That is generated separately, and it is the weakest link in the chain.

## 4. Read the run log

**`2026-08-15_RUNLOG_coa_august_check.md` is the only copy of itself and the previous session never opened it**, despite the handover it was given naming it explicitly. **That is the second source that session missed after being pointed at it.**

It records the scheduled maintenance task firing in Anthropic's cloud on 15 August, finding it could not reach `build_coa.py` or `COA_MASTER_v1.csv` because both are on Paul's machine, and asking him to send the Sage exports by hand. It then records the pre-flight validation of those exports.

**Two things in it matter beyond the history.** The annual chart of accounts check cannot complete unattended, which is a live constraint on that scheduled task rather than a one-off. And the procedure itself lives in Notion, at Intellitax — Practice Management Hub > Workflows > "Annual Chart of Accounts Maintenance Check", which is outside every folder you have mounted.

## 5. What to do with this

**Nothing, beyond knowing it.** Do not copy, move or delete any of the four project documents, and do not reconcile the two handover variants. They are July records and the design document's rule is that history keeps its old values.

**Carry on with the checks.** That remains the immediate job.
