from urllib.parse import urlparse


# URL path fragments commonly used by JavaScript-driven
# menu systems instead of real navigation targets.
PSEUDO_TARGET_PATTERNS = (
    ":void",
    "void(0)",
)


def is_valid_url(url: str) -> bool:
    """
    Return True when a URL is a plausible HTTP/HTTPS crawl target.

    This validator intentionally operates on an already-resolved URL.
    Relative URLs should be resolved before reaching this function.
    """

    if not url:
        return False

    url = url.strip()

    if not url:
        return False

    # Obvious non-navigation targets.
    if url in {"#"}:
        return False

    lowered_url = url.lower()

    if lowered_url.startswith(
        (
            "javascript:",
            "mailto:",
            "tel:",
        )
    ):
        return False

    # Whitespace inside a URL is generally a strong signal
    # of malformed navigation data.
    if any(character.isspace() for character in url):
        return False

    parsed = urlparse(url)

    # Only web URLs are crawlable by the HTTP crawler.
    if parsed.scheme.lower() not in {
        "http",
        "https",
    }:
        return False

    if not parsed.netloc:
        return False

    # Detect pseudo-navigation targets embedded in the path.
    #
    # Examples:
    #   https://example.com/:VOID0;
    #   https://example.com/:VOID0;?cd=MwA%3D
    path = parsed.path.lower()

    if any(
        pattern in path
        for pattern in PSEUDO_TARGET_PATTERNS
    ):
        return False

    return True