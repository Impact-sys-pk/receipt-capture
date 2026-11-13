"""The vendor key rule: how a supplier name becomes the key every layer looks up.

**Moved here from `engine.py` on 2026-11-13, Paul's decision, verbatim.** It
had been copied into `seed_client_vendors.py` and the regenerate script beside
it at the repository root, "to avoid openai import", and both copies had fallen
behind the engine. (The regenerate script's filename is not written here
because it contains the retired field name, which
`tests/test_vendor_key_naming.py` holds absent from `worker\\` outside
comments.) The
seed copy never had the rule that keeps only the first word of a name of three
or more, and the regenerate copy lacked the four articles added in `b61f055`.
The reasons, and the alternatives rejected, are in
`2026-11-13_REPORT_claude_code_vendor_key_rule_one_home.md`.

**This module imports nothing but `re`, and that is its whole reason to exist.**
`engine.py` imports `config`, which creates folders under the practice root at
import, and the `openai` client. A script that needs only the key rule imports
it from here and gets neither. `tests/test_vendor_key_rule_has_one_home.py`
holds that, in a fresh interpreter.

`engine.py` imports all five names from here, so `engine.NOISE_WORDS` and the
rest are the same objects, and every existing import from the engine still
works. **Add a word here, not there.**
"""

import re

NOISE_WORDS = {
    "ltd", "limited", "plc", "inc", "co", "uk",
    "payment", "to", "from", "direct", "debit", "credit",
    "card", "visa", "mastercard", "contactless",
    "purchase", "pos", "online", "mobile",
    "london", "manchester", "birmingham",
    "the", "and", "of", "for", "in", "at", "on",
    # The singular definite article in French, Italian and Spanish, the other
    # languages most common on UK restaurant and cafe names. Added 2026-11-13,
    # Paul's decision: `LA BELLA RESTAURANT` keyed on `la`, because the
    # three-word rule in extract_vendor_key() keeps only the first word. `la` is
    # the one the live database held; the other three fail the same way.
    # Plurals, prepositions such as `de` and `di`, and indefinite articles were
    # deliberately left out: see
    # 2026-11-13_REPORT_claude_code_vendor_key_articles.md.
    "la", "le", "il", "el",
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
