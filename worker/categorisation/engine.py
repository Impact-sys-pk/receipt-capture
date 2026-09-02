"""
Intellitax Auto-Categorisation Engine
A lightweight, local-only categorisation system with no third-party LLM calls.

Architecture:
  Layer 1 - Client-level lookup (vendor → nominal code for specific client)
  Layer 2 - Firm-level lookup (vendor → nominal code by business type)
  Layer 3 - Fuzzy matching (string similarity)
  Layer 4 - AI suggestion (fallback, LLM call if enabled)
"""

import re
import logging
from datetime import datetime
from difflib import SequenceMatcher
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

import config
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None
from .coa import get_coa_for_business_type

logger = logging.getLogger(__name__)


NOISE_WORDS = {
    "ltd", "limited", "plc", "inc", "co", "uk",
    "payment", "to", "from", "direct", "debit", "credit",
    "card", "visa", "mastercard", "contactless",
    "purchase", "pos", "online", "mobile",
    "london", "manchester", "birmingham",
    "the", "and", "of", "for", "in", "at", "on",
    "ref", "reference", "txn",
}

DEFAULT_ALIASES = {
    "amzn": "amazon", "amz": "amazon", "amazon.co.uk": "amazon",
    "pp": "paypal", "tfl": "tfl", "transport for london": "tfl",
    "sumup": "sumup", "sum up": "sumup",
    "google": "google", "goog": "google",
}

LOCATION_WORDS = {
    "dartford", "bromley", "swanley", "london", "croydon",
    "greenwich", "lewisham", "bexley", "sevenoaks", "maidstone",
    "orpington", "sidcup", "eltham", "woolwich", "erith",
    "stn", "serv", "station", "connect", "garage", "petrol",
    "express", "local", "extra", "superstore", "metro",
}


@dataclass
class CategorisationResult:
    """Result of attempting to categorise a transaction."""
    receipt_id: str
    extraction_id: str
    client_id: str
    business_type: str
    vendor_code: Optional[str] = None
    vendor_key: Optional[str] = None
    suggested_code: Optional[str] = None
    suggested_name: Optional[str] = None
    confidence: str = "none"
    match_source: str = "unmatched"
    matched_vendor: Optional[str] = None
    needs_review: bool = True


def normalise_description(raw: str) -> str:
    """Strip noise from a bank/receipt description to extract usable vendor name."""
    text = raw.lower().strip()

    # Remove common prefixes
    text = re.sub(r"^(dd|so|bgo|bgc|chq|tfr|bp|fp|ddr)\s*[-–]\s*", "", text)

    # Remove asterisks and everything before them
    text = text.replace("*", " ")

    # Remove reference numbers (6+ digits)
    text = re.sub(r"\b\d{6,}\b", "", text)

    # Remove single/double digit fragments
    text = re.sub(r"\b\d{1,2}\b", "", text)

    # Split and filter noise
    words = text.split()
    filtered = [w for w in words if w not in NOISE_WORDS and len(w) > 1]

    return " ".join(filtered)


def extract_vendor_key(normalised: str, aliases: dict = None) -> str:
    """Extract canonical vendor key from normalised description."""
    if aliases is None:
        aliases = DEFAULT_ALIASES

    # Check full string against aliases
    if normalised in aliases:
        return aliases[normalised]

    # Check first word against aliases
    words = normalised.split()
    if words and words[0] in aliases:
        return aliases[words[0]]

    # Strip trailing numbers (store codes)
    words = [w for w in words if not w.isdigit()]

    # Strip known location words
    core_words = [w for w in words if w not in LOCATION_WORDS]

    # Fallback to first word if stripping removed everything
    if not core_words and words:
        core_words = [words[0]]

    # Take only first 1-2 words to avoid verbosity (e.g., "apcoa hal ss" → "apcoa")
    if len(core_words) > 2:
        core_words = core_words[:1]

    result = " ".join(core_words)
    return result if result else normalised


def fuzzy_match(query: str, candidates: list[str], threshold: float = 0.70) -> list[tuple[str, float]]:
    """Find candidates that fuzzy-match the query above threshold."""
    matches = []
    for candidate in candidates:
        score = SequenceMatcher(None, query, candidate).ratio()
        if score >= threshold:
            matches.append((candidate, score))
    return sorted(matches, key=lambda x: x[1], reverse=True)


class CategorisationEngine:
    """
    Three-layer categorisation engine with optional AI fallback.
    Lookup priority:
      1. Exact match in client lookup → high confidence
      2. Exact match in firm lookup → high confidence
      3. Fuzzy match in client lookup → medium/low confidence
      4. Fuzzy match in firm lookup → medium/low confidence
      5. AI suggestion (if enabled) → low confidence
      6. Unmatched → no confidence
    """

    def __init__(self, repo=None, enable_ai_fallback: bool = False):
        """
        Initialize engine.
        repo: Repository instance for lookups
        enable_ai_fallback: If True, call LLM for unmatched transactions
        """
        self.repo = repo
        self.enable_ai_fallback = enable_ai_fallback
        self.aliases = dict(DEFAULT_ALIASES)

    def _rule_matches(self, rule: dict, vendor_code: str, detail: str) -> bool:
        """Check if a rule matches the given vendor and detail."""
        # Vendor code must match if specified in rule
        if rule.get("vendor_code") and rule["vendor_code"] != vendor_code:
            return False

        # Check condition
        condition_type = rule.get("condition_type", "contains")
        condition_field = rule.get("condition_field", "detail")
        condition_value = rule.get("condition_value", "").lower()

        # Get the field to check
        field_value = detail.lower() if condition_field == "detail" else vendor_code.lower()

        # Evaluate condition
        if condition_type == "contains":
            return condition_value in field_value
        elif condition_type == "exact_match":
            return condition_value == field_value
        elif condition_type == "startswith":
            return field_value.startswith(condition_value)
        elif condition_type == "regex":
            import re
            try:
                return bool(re.search(condition_value, field_value))
            except Exception:
                return False
        return False

    def categorise(self, receipt_id: str, extraction_id: str, supplier_name: str,
                   client_id: str, business_type: str) -> CategorisationResult:
        """
        Categorise a single receipt through the rules-first engine.
        Returns CategorisationResult with suggested code and confidence.

        Layer 0: Rules (highest priority)
        Layer 1: Client vendor lookup
        Layer 2: Firm vendor lookup
        Layer 3: Fuzzy matching (client)
        Layer 4: Fuzzy matching (firm)
        Layer 5: AI suggestion (if enabled)
        """
        if not supplier_name:
            return CategorisationResult(
                receipt_id=receipt_id, extraction_id=extraction_id,
                client_id=client_id, business_type=business_type,
                confidence="none", match_source="unmatched", needs_review=True
            )

        # Normalise and extract vendor code
        normalised = normalise_description(supplier_name)
        vendor_code = extract_vendor_key(normalised, self.aliases)

        if not vendor_code:
            return CategorisationResult(
                receipt_id=receipt_id, extraction_id=extraction_id,
                client_id=client_id, business_type=business_type,
                confidence="none", match_source="unmatched", needs_review=True
            )

        # Layer 0: Check rules first (highest priority)
        if self.repo:
            rules = self.repo.get_client_rules(client_id)
            for rule in rules:
                if self._rule_matches(rule, vendor_code, supplier_name):
                    return CategorisationResult(
                        receipt_id=receipt_id, extraction_id=extraction_id,
                        client_id=client_id, business_type=business_type,
                        vendor_code=vendor_code, suggested_code=rule["nominal_code"],
                        suggested_name=rule["account_name"],
                        confidence="high", match_source="rule",
                        matched_vendor=rule.get("rule_name"), needs_review=False
                    )

        # Layer 1: Exact match in client lookup
        if self.repo:
            client_vendor = self.repo.get_client_vendor(client_id, vendor_code)
            if client_vendor:
                return CategorisationResult(
                    receipt_id=receipt_id, extraction_id=extraction_id,
                    client_id=client_id, business_type=business_type,
                    vendor_code=vendor_code, vendor_key=client_vendor["vendor_key"],
                    suggested_code=client_vendor["nominal_code"],
                    suggested_name=client_vendor["account_name"],
                    confidence="high", match_source="client",
                    matched_vendor=vendor_code, needs_review=False
                )

            # Layer 2: Exact match in firm lookup (by business type)
            firm_vendor = self.repo.get_firm_vendor(business_type, vendor_code)
            if firm_vendor:
                return CategorisationResult(
                    receipt_id=receipt_id, extraction_id=extraction_id,
                    client_id=client_id, business_type=business_type,
                    vendor_code=vendor_code, vendor_key=firm_vendor["vendor_key"],
                    suggested_code=firm_vendor["nominal_code"],
                    suggested_name=firm_vendor["account_name"],
                    confidence="high", match_source="firm",
                    matched_vendor=vendor_code, needs_review=False
                )

            # Layer 3a: Fuzzy match in client lookup
            client_vendors = self.repo.list_client_vendors(client_id)
            if client_vendors:
                fuzzy_results = fuzzy_match(vendor_code, client_vendors, threshold=0.70)
                if fuzzy_results:
                    best_match, score = fuzzy_results[0]
                    matched_vendor = self.repo.get_client_vendor(client_id, best_match)
                    if matched_vendor:
                        conf = "medium" if score >= 0.80 else "low"
                        return CategorisationResult(
                            receipt_id=receipt_id, extraction_id=extraction_id,
                            client_id=client_id, business_type=business_type,
                            vendor_code=vendor_code, vendor_key=matched_vendor["vendor_key"],
                            suggested_code=matched_vendor["nominal_code"],
                            suggested_name=matched_vendor["account_name"],
                            confidence=conf, match_source="fuzzy_client",
                            matched_vendor=best_match, needs_review=True
                        )

            # Layer 3b: Fuzzy match in firm lookup
            firm_vendors = self.repo.list_firm_vendors(business_type)
            if firm_vendors:
                fuzzy_results = fuzzy_match(vendor_code, firm_vendors, threshold=0.70)
                if fuzzy_results:
                    best_match, score = fuzzy_results[0]
                    matched_vendor = self.repo.get_firm_vendor(business_type, best_match)
                    if matched_vendor:
                        conf = "medium" if score >= 0.80 else "low"
                        return CategorisationResult(
                            receipt_id=receipt_id, extraction_id=extraction_id,
                            client_id=client_id, business_type=business_type,
                            vendor_code=vendor_code, vendor_key=matched_vendor["vendor_key"],
                            suggested_code=matched_vendor["nominal_code"],
                            suggested_name=matched_vendor["account_name"],
                            confidence=conf, match_source="fuzzy_firm",
                            matched_vendor=best_match, needs_review=True
                        )

        # Layer 4: AI suggestion (if enabled)
        if self.enable_ai_fallback:
            ai_result = self._ai_suggest(vendor_code, business_type)
            if ai_result:
                return CategorisationResult(
                    receipt_id=receipt_id, extraction_id=extraction_id,
                    client_id=client_id, business_type=business_type,
                    vendor_code=vendor_code, suggested_code=ai_result.get("code"),
                    suggested_name=ai_result.get("name"),
                    confidence="low", match_source="ai",
                    matched_vendor=vendor_code, needs_review=True
                )

        # No match
        return CategorisationResult(
            receipt_id=receipt_id, extraction_id=extraction_id,
            client_id=client_id, business_type=business_type,
            vendor_code=vendor_code, confidence="none", match_source="unmatched", needs_review=True
        )

    def _ai_suggest(self, vendor_key: str, business_type: str) -> Optional[dict]:
        """
        Call OpenAI with constrained output to categorise unmatched vendor.

        Args:
            vendor_key: Normalised vendor name
            business_type: Client's business type for GL code selection

        Returns:
            {code: str, name: str} or None if API fails
        """
        if not OpenAI:
            logger.warning("OpenAI module not available")
            return None

        try:
            # Get valid GL codes for this business type
            coa = get_coa_for_business_type(business_type)
            if not coa:
                logger.warning(f"No COA available for business_type={business_type}")
                return None

            # Format COA as JSON schema for constrained output
            coa_options = [{"code": code, "name": name} for code, name in coa]

            # Call OpenAI with constrained output
            client = OpenAI(api_key=config.OPENAI_API_KEY)
            response = client.beta.chat.completions.parse(
                model=config.OPENAI_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Categorise the vendor "{vendor_key}" into the most appropriate GL code.

Valid GL codes:
{chr(10).join(f"- {code}: {name}" for code, name in coa)}

Return the best matching GL code and name."""
                    }
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "categorisation",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "code": {
                                    "type": "string",
                                    "description": "GL code (e.g., 103, 281)"
                                },
                                "name": {
                                    "type": "string",
                                    "description": "GL account name"
                                }
                            },
                            "required": ["code", "name"]
                        }
                    }
                }
            )

            # Parse and validate response
            if response.choices and response.choices[0].message.parsed:
                parsed = response.choices[0].message.parsed
                code = parsed.code
                name = parsed.name

                # Verify code exists in COA
                if any(c[0] == code for c in coa):
                    logger.info(f"AI categorised {vendor_key} -> {code} {name}")
                    return {"code": code, "name": name}

            logger.warning(f"AI response invalid for {vendor_key}")
            return None

        except Exception as e:
            logger.warning(f"AI categorisation failed for {vendor_key}: {e}")
            return None

    def learn_from_correction(self, client_id: str, business_type: str,
                             vendor_key: str, nominal_code: str, account_name: str):
        """
        Record a user correction. Update both client and firm lookups.
        """
        if not self.repo or not vendor_key:
            return

        now = datetime.now().isoformat()

        # Update client lookup
        self.repo.upsert_client_vendor(
            client_id=client_id, vendor_key=vendor_key,
            nominal_code=nominal_code, account_name=account_name,
            last_updated=now
        )

        # Update firm lookup (only if no conflict)
        existing_firm = self.repo.get_firm_vendor(business_type, vendor_key)
        if existing_firm is None:
            # First time for this vendor in this business type.
            #
            # 10d.39. The firm is resolved from the client_id this method already
            # receives, rather than added as a parameter, which is what keeps
            # categorise()'s five production call sites untouched. It is written
            # and never read: the unique key does not change and the learned pool
            # stays shared.
            #
            # It reads config.CLIENTS_BY_ID rather than being told, because after
            # 10d.19 the client loader refuses a record with no firm, so a client
            # that resolves at all has a firm. None where it does not resolve,
            # and a null provenance is honest where an invented one is not.
            firm_id = (config.CLIENTS_BY_ID.get(client_id) or {}).get("firm_id")
            self.repo.upsert_firm_vendor(
                business_type=business_type, vendor_code=vendor_key,
                nominal_code=nominal_code, account_name=account_name,
                last_updated=now, firm_id=firm_id
            )
        elif existing_firm["nominal_code"] == nominal_code:
            # Consistent correction, increment counter
            self.repo.increment_firm_vendor_count(business_type, vendor_key)
        else:
            # CONFLICT: different code for same vendor in same business type
            # Log but don't update firm lookup
            pass
