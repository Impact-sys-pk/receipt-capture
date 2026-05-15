"""Chart of Accounts (COA) templates for business types.

Provides GL code lookups for categorisation suggestions and user review dropdowns.
"""

# Standard GL code templates per business type
_COA_TEMPLATES = {
    "PHV_DRIVER": [
        ("1000", "Fixed Assets"),
        ("1100", "Motor Vehicles"),
        ("1200", "Accumulated Depreciation"),
        ("5000", "Office Supplies"),
        ("5100", "Software & Subscriptions"),
        ("6000", "Repairs & Maintenance"),
        ("6100", "Fuel"),
        ("6200", "Vehicle Expenses"),
        ("6300", "Insurance"),
        ("6400", "MOT & Vehicle Tax"),
        ("6500", "Travel & Accommodation"),
        ("6600", "Meals & Entertainment"),
        ("7000", "Salaries & Wages"),
        ("7100", "Employer NI"),
        ("7200", "Pension Contributions"),
        ("8000", "Professional Fees"),
        ("8100", "Accountancy Fees"),
        ("8200", "Legal Fees"),
        ("9000", "Utilities"),
        ("9100", "Telephone & Internet"),
        ("9200", "Postage & Delivery"),
    ],
    "CONTRACTOR": [
        ("5000", "Office Supplies"),
        ("5100", "Software & Subscriptions"),
        ("6000", "Repairs & Maintenance"),
        ("6500", "Travel & Accommodation"),
        ("6600", "Meals & Entertainment"),
        ("7000", "Salaries & Wages"),
        ("7100", "Employer NI"),
        ("7200", "Pension Contributions"),
        ("8000", "Professional Fees"),
        ("8100", "Accountancy Fees"),
        ("8200", "Legal Fees"),
        ("8300", "Subscriptions & Memberships"),
        ("9000", "Utilities"),
        ("9100", "Telephone & Internet"),
        ("9200", "Postage & Delivery"),
    ],
    "UNSPECIFIED": [
        ("5000", "Office Supplies"),
        ("6000", "Repairs & Maintenance"),
        ("6500", "Travel & Accommodation"),
        ("7000", "Salaries & Wages"),
        ("8000", "Professional Fees"),
        ("9000", "Utilities"),
        ("9100", "Telephone & Internet"),
    ],
}


def get_coa_for_business_type(business_type: str) -> list[tuple[str, str]]:
    """Get chart of accounts template for a business type.

    Args:
        business_type: Business type code (e.g., "PHV_DRIVER", "CONTRACTOR")

    Returns:
        List of (code, name) tuples. Falls back to UNSPECIFIED if type not found.
        Example: [("5000", "Office Supplies"), ("6100", "Fuel"), ...]
    """
    return _COA_TEMPLATES.get(business_type, _COA_TEMPLATES["UNSPECIFIED"])


def get_coa_for_client(client_id: str, business_type: str) -> list[tuple[str, str]]:
    """Get chart of accounts for a specific client.

    Currently returns the template for the client's business type.
    Future: could be overridden per-client in DB (coa_client_codes table).

    Args:
        client_id: Client ID (for future per-client overrides)
        business_type: Client's business type code

    Returns:
        List of (code, name) tuples for the client's business type
    """
    # For now, use business type template. Client-specific overrides can be added later.
    return get_coa_for_business_type(business_type)
