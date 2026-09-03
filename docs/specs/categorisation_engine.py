"""
Intellitax Auto-Categorisation Engine v0.1
==========================================
A lightweight, local-only transaction categorisation system.
No data leaves the machine. No third-party LLM calls.

Architecture:
  Layer 1 - Client-level lookup (vendor → nominal code per client)
  Layer 2 - Firm-level lookup (vendor → nominal code across all clients)
  Layer 3 - Fuzzy matching + confidence scoring

Data files:
  data/firm_lookup.json        - Firm-wide vendor → nominal code mappings
  data/clients/{id}/lookup.json - Per-client vendor → nominal code mappings
  data/clients/{id}/history.json - Categorisation history for audit trail

Usage:
  engine = CategorisationEngine(data_dir="data")
  engine.load_client("PKPH")
  results = engine.categorise_transactions(transactions)
  engine.learn_from_corrections(corrections)
"""

import json
import os
import re
from datetime import datetime
from difflib import SequenceMatcher
from dataclasses import dataclass, field, asdict
from typing import Optional
from pathlib import Path


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Transaction:
    """Raw bank feed transaction."""
    date: str                  # ISO format YYYY-MM-DD
    description: str           # Raw bank feed description
    amount: float              # Negative = payment out, positive = receipt
    reference: Optional[str] = None  # Bank reference if available

@dataclass
class CategorisationResult:
    """Result of attempting to categorise a transaction."""
    transaction: Transaction
    suggested_code: Optional[str] = None     # Nominal code
    suggested_name: Optional[str] = None     # Account name
    confidence: str = "none"                  # "high", "medium", "low", "none"
    match_source: str = "unmatched"           # "client", "firm", "fuzzy_client", "fuzzy_firm"
    matched_vendor: Optional[str] = None      # The vendor name that was matched against
    needs_review: bool = True

@dataclass
class VendorMapping:
    """A single vendor → nominal code mapping."""
    vendor: str           # Normalised vendor name
    nominal_code: str     # e.g. "6200" or "Motor Expenses"
    account_name: str     # Human-readable account name
    times_seen: int = 1   # How many times this mapping has been confirmed
    last_updated: str = ""

    def __post_init__(self):
        if not self.last_updated:
            self.last_updated = datetime.now().isoformat()


# ---------------------------------------------------------------------------
# Noise words stripped from bank descriptions
# ---------------------------------------------------------------------------

NOISE_WORDS = {
    # Common bank feed noise
    "ltd", "limited", "plc", "inc", "co", "uk",
    "payment", "to", "from", "direct", "debit", "credit",
    "card", "visa", "mastercard", "contactless",
    "purchase", "pos", "online", "mobile",
    # Location noise
    "london", "manchester", "birmingham",
    # Generic
    "the", "and", "of", "for", "in", "at", "on",
    "ref", "reference", "txn",
}

# Vendor aliases - common variations that should resolve to the same vendor
DEFAULT_ALIASES = {
    "amzn": "amazon",
    "amz": "amazon",
    "amazon.co.uk": "amazon",
    "amazon marketplace": "amazon",
    "pp": "paypal",
    "paypal": "paypal",
    "tfl": "tfl",
    "transport for london": "tfl",
    "sumup": "sumup",
    "sum up": "sumup",
    "google": "google",
    "google cloud": "google",
    "goog": "google",
}


# ---------------------------------------------------------------------------
# String normalisation
# ---------------------------------------------------------------------------

def normalise_description(raw: str) -> str:
    """
    Strip noise from a bank feed description to extract a usable vendor name.

    Examples:
        "SHELL SERV STN DARTFORD"  → "shell dartford"
        "PAYMENT TO AMAZON.CO.UK"  → "amazon"
        "DD - EE LIMITED"          → "ee"
        "CARD PAYMENT TO SUMUP *JOES CAFE" → "sumup joes cafe"
    """
    text = raw.lower().strip()

    # Remove common prefixes
    text = re.sub(r"^(dd|so|bgo|bgc|chq|tfr|bp|fp|ddr)\s*[-–]\s*", "", text)

    # Remove asterisks and everything before them in SumUp/Square style
    # e.g. "SUMUP *JOES CAFE" - keep both parts
    text = text.replace("*", " ")

    # Remove digits that look like reference numbers (6+ digits)
    text = re.sub(r"\b\d{6,}\b", "", text)

    # Remove single/double digit fragments
    text = re.sub(r"\b\d{1,2}\b", "", text)

    # Split into words and filter noise
    words = text.split()
    filtered = [w for w in words if w not in NOISE_WORDS and len(w) > 1]

    return " ".join(filtered)


def extract_vendor_key(normalised: str, aliases: dict = None) -> str:
    """
    Extract a canonical vendor key from a normalised description.
    Checks aliases first, then strips location/number noise to get
    a clean vendor identifier.

    Examples:
        "shell serv stn dartford"  → "shell"
        "greggs 5678 bromley"      → "greggs"
        "bp garage swanley"        → "bp"
        "pod point"                → "pod point"
        "dvla vehicle tax"         → "dvla vehicle tax"
        "halfords autocentre"      → "halfords autocentre"
    """
    if aliases is None:
        aliases = DEFAULT_ALIASES

    # Check full string against aliases
    if normalised in aliases:
        return aliases[normalised]

    # Check first word against aliases
    words = normalised.split()
    if words and words[0] in aliases:
        return aliases[words[0]]

    # Strip trailing numbers (store/branch codes like "1234", "5678")
    words = [w for w in words if not w.isdigit()]

    # Strip known location words (common UK towns that appear in bank feeds)
    location_words = {
        "dartford", "bromley", "swanley", "london", "croydon",
        "greenwich", "lewisham", "bexley", "sevenoaks", "maidstone",
        "orpington", "sidcup", "eltham", "woolwich", "erith",
        "stn", "serv", "station", "connect", "garage", "petrol",
        "express", "local", "extra", "superstore", "metro",
    }
    core_words = [w for w in words if w not in location_words]

    # If stripping removed everything, fall back to first word
    if not core_words and words:
        core_words = [words[0]]

    # For single-word vendors (Shell, BP, Greggs) return just that
    # For multi-word vendors (Pod Point, Halfords Autocentre) return both
    result = " ".join(core_words)
    return result if result else normalised


# ---------------------------------------------------------------------------
# Fuzzy matching
# ---------------------------------------------------------------------------

def fuzzy_match(query: str, candidates: list[str], threshold: float = 0.70) -> list[tuple[str, float]]:
    """
    Find candidates that fuzzy-match the query above the threshold.
    Returns list of (candidate, score) sorted by score descending.
    """
    matches = []
    for candidate in candidates:
        score = SequenceMatcher(None, query, candidate).ratio()
        if score >= threshold:
            matches.append((candidate, score))
    return sorted(matches, key=lambda x: x[1], reverse=True)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class CategorisationEngine:
    """
    The main categorisation engine.

    Lookup priority:
      1. Exact match in client lookup     → confidence: high
      2. Exact match in firm lookup        → confidence: high
      3. Fuzzy match in client lookup      → confidence: medium
      4. Fuzzy match in firm lookup        → confidence: medium/low
      5. No match                          → confidence: none
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.firm_lookup: dict[str, VendorMapping] = {}
        self.client_lookup: dict[str, VendorMapping] = {}
        self.client_id: Optional[str] = None
        self.aliases: dict[str, str] = dict(DEFAULT_ALIASES)

        # Ensure directory structure exists
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "clients").mkdir(exist_ok=True)

        # Load firm-level lookup
        self._load_firm_lookup()

    # --- File I/O ---

    def _firm_lookup_path(self) -> Path:
        return self.data_dir / "firm_lookup.json"

    def _client_dir(self, client_id: str) -> Path:
        return self.data_dir / "clients" / client_id

    def _client_lookup_path(self, client_id: str) -> Path:
        return self._client_dir(client_id) / "lookup.json"

    def _client_history_path(self, client_id: str) -> Path:
        return self._client_dir(client_id) / "history.json"

    def _load_lookup(self, path: Path) -> dict[str, VendorMapping]:
        if not path.exists():
            return {}
        with open(path, "r") as f:
            raw = json.load(f)
        return {k: VendorMapping(**v) for k, v in raw.items()}

    def _save_lookup(self, lookup: dict[str, VendorMapping], path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = {k: asdict(v) for k, v in lookup.items()}
        with open(path, "w") as f:
            json.dump(raw, f, indent=2)

    def _load_firm_lookup(self):
        self.firm_lookup = self._load_lookup(self._firm_lookup_path())

    def _save_firm_lookup(self):
        self._save_lookup(self.firm_lookup, self._firm_lookup_path())

    # --- Client management ---

    def load_client(self, client_id: str):
        """Load a client's lookup table. Creates empty one if new client."""
        self.client_id = client_id
        self._client_dir(client_id).mkdir(parents=True, exist_ok=True)
        self.client_lookup = self._load_lookup(
            self._client_lookup_path(client_id)
        )

    def save_client(self):
        """Save the current client's lookup table."""
        if self.client_id:
            self._save_lookup(
                self.client_lookup,
                self._client_lookup_path(self.client_id)
            )

    # --- Seed from prior year ---

    def seed_from_transactions(self, categorised_transactions: list[dict]):
        """
        Seed lookup tables from previously categorised transactions.

        Each dict should have:
          - description: str (raw bank description)
          - nominal_code: str
          - account_name: str

        Populates both client-level and firm-level lookups.
        """
        for txn in categorised_transactions:
            normalised = normalise_description(txn["description"])
            vendor_key = extract_vendor_key(normalised, self.aliases)

            if not vendor_key:
                continue

            mapping = VendorMapping(
                vendor=vendor_key,
                nominal_code=txn["nominal_code"],
                account_name=txn["account_name"],
            )

            # Client level
            if vendor_key in self.client_lookup:
                self.client_lookup[vendor_key].times_seen += 1
                self.client_lookup[vendor_key].last_updated = datetime.now().isoformat()
            else:
                self.client_lookup[vendor_key] = mapping

            # Firm level - only add if not already present
            # (don't overwrite firm-level with client-specific mapping)
            if vendor_key not in self.firm_lookup:
                self.firm_lookup[vendor_key] = VendorMapping(
                    vendor=vendor_key,
                    nominal_code=txn["nominal_code"],
                    account_name=txn["account_name"],
                )
            else:
                self.firm_lookup[vendor_key].times_seen += 1

        self.save_client()
        self._save_firm_lookup()

    # --- Core categorisation ---

    def categorise(self, txn: Transaction) -> CategorisationResult:
        """Categorise a single transaction through the three-layer engine."""

        normalised = normalise_description(txn.description)
        vendor_key = extract_vendor_key(normalised, self.aliases)

        if not vendor_key:
            return CategorisationResult(
                transaction=txn,
                confidence="none",
                match_source="unmatched",
                needs_review=True,
            )

        # Layer 1: Exact match - client lookup
        if vendor_key in self.client_lookup:
            m = self.client_lookup[vendor_key]
            return CategorisationResult(
                transaction=txn,
                suggested_code=m.nominal_code,
                suggested_name=m.account_name,
                confidence="high",
                match_source="client",
                matched_vendor=m.vendor,
                needs_review=False,
            )

        # Layer 2: Exact match - firm lookup
        if vendor_key in self.firm_lookup:
            m = self.firm_lookup[vendor_key]
            return CategorisationResult(
                transaction=txn,
                suggested_code=m.nominal_code,
                suggested_name=m.account_name,
                confidence="high",
                match_source="firm",
                matched_vendor=m.vendor,
                needs_review=False,
            )

        # Layer 3: Fuzzy match - client lookup first, then firm
        client_matches = fuzzy_match(
            vendor_key, list(self.client_lookup.keys()), threshold=0.70
        )
        if client_matches:
            best_key, score = client_matches[0]
            m = self.client_lookup[best_key]
            conf = "medium" if score >= 0.80 else "low"
            return CategorisationResult(
                transaction=txn,
                suggested_code=m.nominal_code,
                suggested_name=m.account_name,
                confidence=conf,
                match_source="fuzzy_client",
                matched_vendor=m.vendor,
                needs_review=True,
            )

        firm_matches = fuzzy_match(
            vendor_key, list(self.firm_lookup.keys()), threshold=0.70
        )
        if firm_matches:
            best_key, score = firm_matches[0]
            m = self.firm_lookup[best_key]
            conf = "medium" if score >= 0.80 else "low"
            return CategorisationResult(
                transaction=txn,
                suggested_code=m.nominal_code,
                suggested_name=m.account_name,
                confidence=conf,
                match_source="fuzzy_firm",
                matched_vendor=m.vendor,
                needs_review=True,
            )

        # No match at all
        return CategorisationResult(
            transaction=txn,
            confidence="none",
            match_source="unmatched",
            needs_review=True,
        )

    def categorise_transactions(self, transactions: list[Transaction]) -> list[CategorisationResult]:
        """Categorise a batch of transactions. Returns sorted by confidence."""
        results = [self.categorise(txn) for txn in transactions]

        # Sort: high confidence first, then medium, low, none
        confidence_order = {"high": 0, "medium": 1, "low": 2, "none": 3}
        results.sort(key=lambda r: confidence_order.get(r.confidence, 4))

        return results

    # --- Learning loop ---

    def learn_from_correction(
        self,
        txn: Transaction,
        nominal_code: str,
        account_name: str,
        update_firm: bool = True,
    ):
        """
        Record a confirmed categorisation. Updates client lookup
        and optionally the firm lookup.
        """
        normalised = normalise_description(txn.description)
        vendor_key = extract_vendor_key(normalised, self.aliases)

        if not vendor_key:
            return

        now = datetime.now().isoformat()

        # Update client lookup
        if vendor_key in self.client_lookup:
            self.client_lookup[vendor_key].nominal_code = nominal_code
            self.client_lookup[vendor_key].account_name = account_name
            self.client_lookup[vendor_key].times_seen += 1
            self.client_lookup[vendor_key].last_updated = now
        else:
            self.client_lookup[vendor_key] = VendorMapping(
                vendor=vendor_key,
                nominal_code=nominal_code,
                account_name=account_name,
                last_updated=now,
            )

        # Update firm lookup (only vendor + nominal code, no client data)
        if update_firm:
            if vendor_key not in self.firm_lookup:
                self.firm_lookup[vendor_key] = VendorMapping(
                    vendor=vendor_key,
                    nominal_code=nominal_code,
                    account_name=account_name,
                    last_updated=now,
                )
            else:
                # Only update if same code (don't overwrite with conflicts)
                if self.firm_lookup[vendor_key].nominal_code == nominal_code:
                    self.firm_lookup[vendor_key].times_seen += 1
                    self.firm_lookup[vendor_key].last_updated = now
                # If different code, leave firm lookup unchanged
                # (flag as conflict for manual review)

        # Append to history
        self._append_history(txn, vendor_key, nominal_code, account_name)

        self.save_client()
        self._save_firm_lookup()

    def _append_history(self, txn: Transaction, vendor_key: str,
                        nominal_code: str, account_name: str):
        """Append a correction to the client's history log."""
        if not self.client_id:
            return

        history_path = self._client_history_path(self.client_id)
        history = []
        if history_path.exists():
            with open(history_path, "r") as f:
                history = json.load(f)

        history.append({
            "timestamp": datetime.now().isoformat(),
            "description": txn.description,
            "vendor_key": vendor_key,
            "nominal_code": nominal_code,
            "account_name": account_name,
            "amount": txn.amount,
        })

        with open(history_path, "w") as f:
            json.dump(history, f, indent=2)

    # --- Reporting ---

    def summary(self, results: list[CategorisationResult]) -> dict:
        """Summary statistics for a batch of categorisation results."""
        total = len(results)
        by_confidence = {"high": 0, "medium": 0, "low": 0, "none": 0}
        by_source = {}

        for r in results:
            by_confidence[r.confidence] = by_confidence.get(r.confidence, 0) + 1
            by_source[r.match_source] = by_source.get(r.match_source, 0) + 1

        auto_rate = (by_confidence["high"] / total * 100) if total > 0 else 0
        review_rate = (
            (by_confidence["medium"] + by_confidence["low"] + by_confidence["none"])
            / total * 100
        ) if total > 0 else 0

        return {
            "total_transactions": total,
            "by_confidence": by_confidence,
            "by_source": by_source,
            "auto_categorised_pct": round(auto_rate, 1),
            "needs_review_pct": round(review_rate, 1),
        }

    def show_conflicts(self) -> list[dict]:
        """
        Show vendor names that map to different nominal codes
        across different clients. Useful for firm-level review.
        """
        conflicts = []
        for vendor_key, firm_mapping in self.firm_lookup.items():
            if vendor_key in self.client_lookup:
                client_mapping = self.client_lookup[vendor_key]
                if client_mapping.nominal_code != firm_mapping.nominal_code:
                    # Sub-step 10d.67: `client_code` goes completely and appears nowhere.
                    # These four keys never held a client code: they hold the nominal code
                    # and the account name of the client-level mapping and of the firm-level
                    # one. `client_name` was the worse of the two, because it read as the
                    # client's business name and is an account name. Renamed to say so.
                    conflicts.append({
                        "vendor": vendor_key,
                        "client_nominal_code": client_mapping.nominal_code,
                        "client_account_name": client_mapping.account_name,
                        "firm_nominal_code": firm_mapping.nominal_code,
                        "firm_account_name": firm_mapping.account_name,
                    })
        return conflicts


# ---------------------------------------------------------------------------
# Demo / test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    # Create engine
    engine = CategorisationEngine(data_dir="demo_data")

    # Load a client
    engine.load_client("PKPH")

    # Seed with some prior year categorised transactions
    prior_year = [
        {"description": "SHELL SERV STN DARTFORD", "nominal_code": "5100", "account_name": "Cost of Sales - Fuel"},
        {"description": "SHELL SERV STN DARTFORD", "nominal_code": "5100", "account_name": "Cost of Sales - Fuel"},
        {"description": "SHELL SERV STN BROMLEY", "nominal_code": "5100", "account_name": "Cost of Sales - Fuel"},
        {"description": "EE LIMITED DD", "nominal_code": "5400", "account_name": "Cost of Sales - Telephone"},
        {"description": "AMAZON.CO.UK MARKETPLACE", "nominal_code": "7500", "account_name": "Office Supplies"},
        {"description": "DVLA VEHICLE TAX", "nominal_code": "7100", "account_name": "Motor Expenses"},
        {"description": "POD POINT LTD", "nominal_code": "5100", "account_name": "Cost of Sales - EV Charging"},
        {"description": "BP GARAGE SWANLEY", "nominal_code": "5100", "account_name": "Cost of Sales - Fuel"},
        {"description": "GREGGS 1234 DARTFORD", "nominal_code": "8200", "account_name": "Subsistence"},
        {"description": "MCDONALD'S DARTFORD", "nominal_code": "8200", "account_name": "Subsistence"},
        {"description": "NCP CAR PARK LONDON", "nominal_code": "5200", "account_name": "Cost of Sales - Parking"},
        {"description": "HALFORDS AUTOCENTRE", "nominal_code": "7100", "account_name": "Motor Expenses"},
    ]
    engine.seed_from_transactions(prior_year)

    # Now categorise some new transactions
    new_transactions = [
        Transaction("2026-04-01", "SHELL SERV STN DARTFORD", -65.00),
        Transaction("2026-04-02", "EE LIMITED DD", -25.99),
        Transaction("2026-04-03", "AMAZON.CO.UK AMZN MKTP", -19.99),
        Transaction("2026-04-04", "GREGGS 5678 BROMLEY", -4.50),
        Transaction("2026-04-05", "DVLA VEHICLE TAX", -180.00),
        Transaction("2026-04-06", "POD POINT LIMITED", -12.40),
        Transaction("2026-04-07", "TESCO PETROL DARTFORD", -55.00),   # New vendor
        Transaction("2026-04-08", "HMRC SELF ASSESSMENT", -500.00),   # New vendor
        Transaction("2026-04-09", "BP CONNECT SWANLEY", -60.00),      # Fuzzy match to BP GARAGE SWANLEY
        Transaction("2026-04-10", "UBER TRIP LONDON", -15.00),        # Unknown
    ]

    results = engine.categorise_transactions(new_transactions)

    # Print results
    print("=" * 80)
    print("INTELLITAX AUTO-CATEGORISATION ENGINE v0.1")
    print("Client: PKPH | Run date:", datetime.now().strftime("%Y-%m-%d %H:%M"))
    print("=" * 80)

    print(f"\n{'Description':<35} {'Suggested':<25} {'Conf':<8} {'Source':<15}")
    print("-" * 80)

    for r in results:
        desc = r.transaction.description[:33]
        suggested = (r.suggested_name or "---")[:23]
        flag = "" if not r.needs_review else " *"
        print(f"{desc:<35} {suggested:<25} {r.confidence:<8} {r.match_source:<15}{flag}")

    print()
    stats = engine.summary(results)
    print(f"Total: {stats['total_transactions']} | "
          f"Auto: {stats['auto_categorised_pct']}% | "
          f"Review: {stats['needs_review_pct']}%")
    print()
    print("* = needs review")
    print()

    # --- Now demonstrate firm-level learning with a second client ---

    print("\n" + "=" * 80)
    print("SECOND CLIENT DEMO: Firm-level learning")
    print("=" * 80)

    # First, teach the engine about HMRC and Tesco from PKPH corrections
    engine.learn_from_correction(
        Transaction("2026-04-07", "TESCO PETROL DARTFORD", -55.00),
        nominal_code="5100", account_name="Cost of Sales - Fuel"
    )
    engine.learn_from_correction(
        Transaction("2026-04-08", "HMRC SELF ASSESSMENT", -500.00),
        nominal_code="3200", account_name="Drawings - Tax Payments"
    )

    # Now load a different client
    engine.load_client("CLIENT_002")

    # This client has NO prior history at all - brand new
    new_client_txns = [
        Transaction("2026-04-01", "SHELL GARAGE MAIDSTONE", -45.00),
        Transaction("2026-04-02", "AMAZON MKTP UK", -32.99),
        Transaction("2026-04-03", "TESCO PETROL SEVENOAKS", -50.00),
        Transaction("2026-04-04", "HMRC SELF ASSESSMENT", -1200.00),
        Transaction("2026-04-05", "SCREWFIX DIRECT", -89.50),  # Genuinely unknown
    ]

    results2 = engine.categorise_transactions(new_client_txns)

    print(f"\n{'Description':<35} {'Suggested':<25} {'Conf':<8} {'Source':<15}")
    print("-" * 80)
    for r in results2:
        desc = r.transaction.description[:33]
        suggested = (r.suggested_name or "---")[:23]
        flag = "" if not r.needs_review else " *"
        print(f"{desc:<35} {suggested:<25} {r.confidence:<8} {r.match_source:<15}{flag}")

    print()
    stats2 = engine.summary(results2)
    print(f"Total: {stats2['total_transactions']} | "
          f"Auto: {stats2['auto_categorised_pct']}% | "
          f"Review: {stats2['needs_review_pct']}%")
    print()
    print("Note: CLIENT_002 has NO prior history. All matches come from")
    print("the firm-level lookup, built from PKPH's categorised transactions.")
