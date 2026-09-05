"""
Intellitax Auto-Categorisation Engine
A lightweight, local-only categorisation system with no third-party LLM calls.

Architecture. One numbering, and it is the one in categorise()'s own docstring.
Corrected 2026-09-03 under step 10h: this file numbered its layers three
different ways, here, in categorise() and in the inline comments, so a log line
or a report saying "layer 4" named a different step depending on which set the
reader had in front of them. Rules were missing here altogether.

  Layer 0 - Rules (client-specific overrides, highest priority)
  Layer 1 - Client-level lookup (vendor -> nominal code for one client)
  Layer 2 - Firm-level lookup (vendor -> nominal code by business type)
  Layer 3 - Fuzzy matching against the client's vendor codes
  Layer 4 - Fuzzy matching against the firm's vendor codes
  Layer 5 - AI suggestion (only when enable_ai_fallback is True)

Unmatched is not a layer. It is what is recorded when no layer answered:
match_source "unmatched", confidence "none", needs_review 1, and no code.
"""

import re
import logging
from datetime import datetime
from difflib import SequenceMatcher
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path

import config
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None
from pydantic import BaseModel, Field
from .chart import get_eligible_accounts_for_client

logger = logging.getLogger(__name__)


class AiAccountSuggestion(BaseModel):
    """The shape of layer 5's answer, as a class rather than as a schema dict.

    Fixed 2026-09-05, and layer 5 had never once returned an answer before it.
    `client.beta.chat.completions.parse()` parses the reply for the caller ONLY
    when `response_format` is a model class. `openai/lib/_parsing/_completions.py`
    decides that in `has_rich_response_format()`, which returns False for a dict,
    so `maybe_parse_content()` returned None and `message.parsed` was always None.
    The old code passed a dict holding a JSON schema, tested `message.parsed`,
    found nothing every time, and logged "AI response invalid" while the model's
    answer sat unread in `message.content`. Every call was paid for.

    The two descriptions are carried across unchanged from that schema, including
    the deliberate absence of an example code: amendment 198 removed "e.g., 103,
    281" because it contradicted the four-digit list in the same prompt, and an
    example taken from one chart is absent from another client's. The list of
    valid codes in the prompt is the only thing that names a code.
    """

    code: str = Field(description="The account code, taken exactly from the list of valid codes above")
    name: str = Field(description="The account name shown beside that code in the list above")


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
                   client_id: str, business_type: str,
                   gross_amount: Optional[float] = None,
                   line_items: Optional[List[str]] = None) -> CategorisationResult:
        """
        Categorise a single receipt through the rules-first engine.
        Returns CategorisationResult with suggested code and confidence.

        Layer 0: Rules (highest priority)
        Layer 1: Client vendor lookup
        Layer 2: Firm vendor lookup
        Layer 3: Fuzzy matching (client)
        Layer 4: Fuzzy matching (firm)
        Layer 5: AI suggestion (if enabled)

        gross_amount and line_items reach layer 5 and no other layer. Layers 0
        to 4 match on the vendor and are unchanged by either. Both default to
        None and both are allowed to be None: a caller that reads an extraction
        back out of the database has the amount but cannot have the item lines,
        because line items are not stored.
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

            # Layer 3: Fuzzy match in client lookup
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

            # Layer 4: Fuzzy match in firm lookup
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

        # Layer 5: AI suggestion (if enabled)
        if self.enable_ai_fallback:
            ai_result = self._ai_suggest(vendor_code, client_id, supplier_name,
                                         gross_amount, line_items)
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

    def _ai_suggest(self, vendor_key: str, client_id: str,
                    supplier_name: str = "",
                    gross_amount: Optional[float] = None,
                    line_items: Optional[List[str]] = None) -> Optional[dict]:
        """
        Call OpenAI with constrained output to categorise unmatched vendor.

        Args:
            vendor_key: Normalised vendor name. It is a lookup key, built to be
                stable for the exact and fuzzy layers, and it is lossy: rule 8 of
                extract_vendor_key() keeps only the first word once more than two
                remain, so "Canary Hand Car Wash" arrives here as "canary".
            client_id: The client, whose published chart bounds what may be
                suggested. Was business_type until 2026-09-04, which selected one
                of three hardcoded lists in the deleted coa.py. The chart a
                client is on is a property of the client, not of its trade.
            supplier_name: The supplier as it appeared on the receipt. Added
                2026-09-05, on the first run of layer 5 this project has ever
                made. Given "canary" alone the model returned "Software and
                subscriptions", and given "berkeley" it returned "Consultancy
                fees"; both are reasonable readings of the input they were sent.
                The key is kept in the prompt as well, because it is what the
                learned tables are keyed on and what a later correction attaches
                to. Empty is allowed: a receipt can yield a key and no name.
            gross_amount: The total on the receipt, VAT included, where the
                extraction established one. Added 2026-09-05 because the first
                run of layer 5 answered "0081 Motor vehicles - cars - additions"
                for a Halfords receipt: nothing in the prompt said how much had
                been spent, so nothing stopped a small receipt becoming a
                capitalised car. It is named as the gross in the prompt so the
                model is not left to work out whether it is net or gross.
                **This passes the amount and does nothing with it.** There is no
                capitalisation threshold here and there must not be one: Paul's
                ruling of 2026-09-05 is that the five asset accounts are gated on
                amount, and the figure is outstanding item 33 and is not decided.
                None is allowed and the line is then left out of the prompt.
            line_items: The item lines as they appeared on the receipt. Added
                2026-09-05 for the same run, which answered "7520 Stationery and
                office supplies" for an Asda Wallington receipt: a supermarket
                receipt cannot be read from the supplier name, and what was
                bought is the only thing that distinguishes one from another.
                They come off the extraction call that was already made and are
                not stored anywhere, so a caller reading an extraction back out
                of the database passes None and the line is left out.

        Returns:
            {code: str, name: str} or None if API fails
        """
        if not OpenAI:
            logger.warning("OpenAI module not available")
            return None

        try:
            # The accounts this client's published chart marks
            # classifier_eligible. Layer 5 is the only layer that reads a chart.
            coa = get_eligible_accounts_for_client(client_id)
            if not coa:
                logger.warning(f"no classifier-eligible accounts for client_id={client_id}")
                return None

            # What is known about the receipt, one line each, and a line is
            # absent rather than empty where the value is None. An absent line
            # says nothing; "Gross amount on the receipt: None" would be a
            # sentence the model has to interpret.
            facts = [
                f'Supplier as it appeared on the receipt: "{supplier_name or vendor_key}"',
                f'Normalised lookup key: "{vendor_key}"',
            ]
            if gross_amount is not None:
                # Named as the gross so the model does not have to guess. No
                # currency is stated because _ai_suggest() is not given one, and
                # naming the wrong one is worse than naming none.
                facts.append(
                    f"Gross amount on the receipt, VAT included: {gross_amount}"
                )
            if line_items:
                lines = chr(10).join(f"  {item}" for item in line_items)
                facts.append(f"Item lines on the receipt:{chr(10)}{lines}")

            # Call OpenAI with constrained output
            client = OpenAI(api_key=config.OPENAI_API_KEY)
            response = client.beta.chat.completions.parse(
                model=config.OPENAI_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Categorise this supplier into the most appropriate GL code.

{chr(10).join(facts)}

Valid GL codes:
{chr(10).join(f"- {code}: {name}" for code, name in coa)}

Return the best matching GL code and name."""
                    }
                ],
                # A model class, not a schema dict. The library only parses the
                # reply when this is a class; a dict means "the caller will parse
                # it", and message.parsed is then always None. See
                # AiAccountSuggestion's docstring for the defect this fixed.
                response_format=AiAccountSuggestion,
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
