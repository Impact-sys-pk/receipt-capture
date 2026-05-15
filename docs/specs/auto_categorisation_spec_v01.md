# Intellitax Auto-Categorisation Engine

**Conceptual Specification v0.1**

April 2026 | DRAFT | Intellitax Accounting Limited

---

## 1. Purpose

A lightweight, local-first auto-categorisation engine for pre-posting transaction categorisation. Designed for small clients (PHV drivers initially) where commercial bookkeeping software is overkill. No client data is exposed to third-party LLMs or cloud services.

The engine serves two functions: pre-categorising transactions before they are posted to the client ledger (spreadsheet), and building a firm-level dataset of vendor-to-category mappings that compounds in value across engagements.

## 2. Context and Inspiration

The architecture draws on the Digits Agentic General Ledger concept, specifically their three-tier AI model structure (company-level, firm-level, global) and their approach to data isolation between firms. This spec adapts those principles for a small UK practice without requiring ML infrastructure.

**Key principle:** All categorisation intelligence is built from lookup tables and fuzzy string matching. No machine learning models, no LLM API calls, no third-party data processing.

## 3. Architecture

### 3.1 Four-Layer Lookup Model

| Layer          | Scope               | Data Content                                                                                                                                                                                               |
| -------------- | ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Client lookup  | Single client       | Vendor → nominal code mappings built from that client's categorised transactions                                                                                                                           |
| Firm lookup    | All clients         | Vendor → nominal code mappings aggregated across all clients, segmented by business type. No client identifiers, no amounts, no dates                                                                      |
| Fuzzy matching | Fallback            | String similarity matching when exact vendor key not found in either lookup table                                                                                                                          |
| AI suggestion  | Cold-start fallback | API call to OpenAI/Anthropic with chart of accounts as context. Triggered only when layers 1–3 return nothing. Returns suggested nominal code from constrained list. Flagged for review, never auto-posted |

Transaction flow: incoming transaction → normalise description → extract vendor key → check client lookup (exact) → check firm lookup (exact) → check client lookup (fuzzy) → check firm lookup (fuzzy) → AI suggestion against chart of accounts → unmatched.

Layer 4 gets called less over time as layers 1 and 2 grow from confirmed corrections. It is the cold-start solution for new business types where lookup data has not yet been built up.

### 3.2 Confidence Levels

| Confidence | Trigger                                                       | Action                                   |
| ---------- | ------------------------------------------------------------- | ---------------------------------------- |
| High       | Exact match in client or firm lookup                          | Auto-categorise, no review required      |
| Medium     | Fuzzy match with similarity score ≥ 0.80                      | Suggest category, flag for review        |
| Low        | Fuzzy match with similarity score 0.70–0.79, or AI suggestion | Suggest category, flag for review        |
| None       | No match found and no AI suggestion                           | Surface to accountant with no suggestion |

### 3.3 Business Type Subsets

The firm-level lookup is segmented by business type. The same vendor may map to different nominal codes depending on the client's business type. For example, Shell might map to Cost of Sales – Fuel for a PHV driver but Motor Expenses for a consultant.

Initial business types: PHV Driver, Sole Trader (General), Micro-entity Limited Company. Additional types added as the client base develops.

## 4. Input Channels

### 4.1 Receipt Capture

Existing Python script extracts vendor, date, amount, and VAT from receipt images via OpenAI Vision. The auto-categorisation engine receives this extracted data and assigns a nominal code before the transaction is posted to the client spreadsheet.

_Status: Receipt capture script exists. Categorisation integration not yet built._

### 4.2 Bank Statement Parser

Existing Python script parses bank statement PDFs and extracts transaction data (date, description, amount). The auto-categorisation engine processes the parsed output and assigns nominal codes.

_Status: Bank statement parser exists. Categorisation integration not yet built._

### 4.3 Output Format

Both channels produce the same output: a CSV file with columns for date, description, amount, VAT (where available), nominal code, account name, confidence level, and review flag. This CSV is the pre-categorised transaction list ready for posting to the client spreadsheet.

## 5. AI Suggestion Layer (Layer 4)

When layers 1–3 return no match, the engine makes a single API call to OpenAI or Anthropic. The prompt contains the chart of accounts for the client's business type (typically 30–50 lines) plus the vendor name and amount. The AI returns a suggested nominal code and account name from the constrained list provided — it does not invent categories.

The AI suggestion is always treated as low confidence and flagged for review. Once confirmed, the correction feeds into the client and firm lookup tables so the AI is never asked about that vendor again.

Cost per call is fractions of a penny (roughly 300–500 input tokens, 20–30 output tokens). The number of calls decreases over time as the lookup tables grow.

Data governance: the API call sends only a vendor name, an amount, and a generic chart of accounts. No client name, no dates, no identifying information.

## 6. Data Governance

| Principle                                | Implementation                                                                                                                   |
| ---------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| No client data in firm lookup            | Firm-level table contains only vendor names and nominal codes. No amounts, dates, client identifiers, or transaction details.    |
| Client data stays local                  | Client lookup tables and transaction history stored on the processing machine only. Never uploaded to cloud or shared storage.   |
| No third-party LLM exposure (layers 1–3) | All lookup and fuzzy matching logic runs locally. No API calls to any external service.                                          |
| Minimal data in AI calls (layer 4)       | Only vendor name, amount, and chart of accounts sent. No client-identifying information.                                         |
| Audit trail                              | Every correction logged with timestamp, original description, vendor key, nominal code, and amount in a per-client history file. |

## 7. Learning Loop

The engine improves over time through a feedback loop:

- **Seed:** Prior year categorised transactions populate the client and firm lookup tables at the start of each engagement.
- **Correct:** During transaction review, corrections update both the client lookup (always) and the firm lookup (if no conflict exists).
- **Conflict handling:** If the same vendor maps to different nominal codes across clients with the same business type, the conflict is flagged for manual review rather than overwritten.
- **Compound:** Each completed engagement adds to the firm-level dataset. New clients of the same business type benefit from day one.

## 8. Hosting and Deployment

### 8.1 Current State: Local Only

Engine runs as a Python script on the accountant's machine. All data stored locally in SQLite (consistent with the receipt capture app). No cloud infrastructure required.

### 8.2 Subcontractor Scenario

When subcontractors are introduced:

- **Firm-level lookup:** shared via secure channel or lightweight API. No client data in this layer.
- **Client-level data:** stays on the subcontractor's local machine. Never centralised.
- **Engine code:** distributed as a packaged executable (PyInstaller) to protect IP. Subcontractor runs the tool but cannot inspect source code.

### 8.3 Future: Cloud Hosting (AWS)

If the practice scales beyond one or two subcontractors:

- AWS Lambda (serverless) for the categorisation API.
- PostgreSQL (AWS RDS) for structured data. Direct migration path from SQLite.
- AWS S3 for file storage (receipt images, PDFs).
- Estimated cost at small scale: £15–30/month for PostgreSQL, pennies for S3 and Lambda. AWS free tier covers the first 12 months.

_Status: Not required yet. Move to AWS when subcontractor base exceeds 1–2 or when offering as a service to other practices._

## 9. Storage Migration Path

| Stage         | Structured Data       | File Storage     |
| ------------- | --------------------- | ---------------- |
| Local (now)   | SQLite                | Local filesystem |
| Subcontractor | SQLite (each machine) | Local filesystem |
| Cloud (AWS)   | PostgreSQL (RDS)      | S3               |

SQLite → PostgreSQL is a straightforward migration (similar SQL). This is the only migration path in this design. S3 is file storage only, not a database alternative.

## 10. IP Protection

| Option                        | Method                                                                 | Strength                                       |
| ----------------------------- | ---------------------------------------------------------------------- | ---------------------------------------------- |
| Option 1: API                 | Host engine on AWS. Subcontractor never sees code or firm lookup.      | Strongest. Recommended at scale.               |
| Option 2: Packaged executable | Distribute compiled Python (PyInstaller). Source not directly visible. | Good. Sufficient for small subcontractor base. |
| Option 3: Contract only       | Distribute source code. Rely on subcontractor agreement.               | Weakest. Simplest operationally.               |

**Recommendation:** Start with Option 2 (packaged tool + contract) while the subcontractor base is small. Move to Option 1 (AWS-hosted API) if scaling beyond one or two subcontractors.

## 11. Target Ledger

For small PHV clients, the ledger is a spreadsheet. The auto-categorisation engine produces a pre-categorised CSV that is posted (imported or manually entered) into the client spreadsheet. For MTD clients, the same spreadsheet feeds a third-party bridging solution for quarterly updates.

No commercial bookkeeping software (FreeAgent, QBO, Xero) is required for this client tier. The spreadsheet-based approach keeps costs proportionate to the client's turnover and complexity.

## 12. Working Prototype

A working Python prototype (categorisation_engine_v0.1.py) was built and tested during this design session. The prototype demonstrates three lookup layers, fuzzy matching, the learning loop, and cross-client firm-level learning. It processed sample PHV driver transactions with 70% auto-categorisation from seeded prior year data, rising to 60% for a brand-new client with no history using firm-level data alone.

_Status: Prototype complete. Not yet integrated with receipt capture or bank statement parser scripts._

## 13. Next Steps (When Ready)

- Add business type field to firm lookup data structure.
- Add Layer 4 AI suggestion call for unmatched transactions.
- Integrate categorisation engine with existing receipt capture script.
- Integrate categorisation engine with existing bank statement parser.
- Define the client spreadsheet template for PHV drivers (column structure, nominal code list).
- Seed the firm lookup with a PHV driver template based on PKPH transaction history.
- Test end-to-end flow: receipt photo → extract → categorise → post to spreadsheet.
- Package as executable for subcontractor distribution (when required).

## 14. Related Work

This spec sits alongside the main accounts workflow project (Variants 1–5). The categorisation engine is not part of those workflows but could serve as a pre-processing tool for Stage 3 (Data Verification) in future, and as the foundation of a low-cost bookkeeping service for small clients outside the standard workflow.
