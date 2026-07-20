from urllib.parse import urlsplit


def normalize_domain(value):
    """Return a hostname suitable for DomainToBusinessMapping."""
    raw_value = str(value or "").strip()
    if not raw_value:
        return ""

    parsed = urlsplit(raw_value if "://" in raw_value else f"//{raw_value}")
    if not parsed.hostname or parsed.username or parsed.password:
        return ""
    return parsed.hostname.rstrip(".").lower()
