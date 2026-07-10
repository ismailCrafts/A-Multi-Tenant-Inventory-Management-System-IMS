import babel.dates
import datetime


# Bengali digit → ASCII digit mapping
_BN_DIGITS = str.maketrans('০১২৩৪৫৬৭৮৯', '0123456789')


def _bn_to_ascii(s):
    """Convert Bengali/Indic numeral digits in a string to ASCII digits."""
    return s.translate(_BN_DIGITS)


def parse_localized_date(value, locale=None):
    if not value:
        return None

    # Normalize: convert Bengali numerals to ASCII first so every path below
    # can work with plain digit strings (e.g. "২০২৪-০১-১৫" → "2024-01-15")
    normalized = _bn_to_ascii(value.strip())

    # ISO fallback — handles YYYY-MM-DD whether digits were Bengali or ASCII
    try:
        return datetime.datetime.strptime(normalized, "%Y-%m-%d").date()
    except Exception:
        pass

    # Only try Bangla babel parse when org is actually Bangla and ISO failed
    if locale == 'bn':
        try:
            return babel.dates.parse_date(normalized, locale='bn')
        except Exception:
            pass
        # Also try with original value in case babel needs Bangla script
        try:
            return babel.dates.parse_date(value.strip(), locale='bn')
        except Exception:
            pass

    return None