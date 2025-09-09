# core/utils.py
import pycountry

def country_to_flag(alpha2: str) -> str:
    """Return emoji flag from ISO alpha-2 (e.g. 'US' -> 🇺🇸)."""
    if not alpha2 or len(alpha2) != 2:
        return "🏳️"
    return "".join(chr(0x1F1E6 + ord(c.upper()) - ord('A')) for c in alpha2)

def lookup_country_code(value: str) -> str:
    """
    Accepts many forms: 'US', 'usa', 'United States', 'Ng', 'Nigeria', etc.
    Returns alpha_2 or '' if unknown.
    """
    if not value:
        return ""
    try:
        return pycountry.countries.lookup(value).alpha_2
    except LookupError:
        return ""

