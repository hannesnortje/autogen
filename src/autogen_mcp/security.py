# Outbound Call Allowlist for Security

# Usage:
# - Add allowed domains or URL prefixes to the ALLOWED_DOMAINS set.
# - Use is_url_allowed(url) to check before making any HTTP request.

from urllib.parse import urlparse

ALLOWED_DOMAINS = {
    "api.github.com",
    "generativelanguage.googleapis.com",
    "localhost",
    "127.0.0.1",
}


def is_url_allowed(url: str) -> bool:
    parsed = urlparse(url)
    netloc = parsed.hostname or ""
    # Allow localhost and explicit allowed domains
    for allowed in ALLOWED_DOMAINS:
        if netloc == allowed or netloc.endswith("." + allowed):
            return True
    return False
