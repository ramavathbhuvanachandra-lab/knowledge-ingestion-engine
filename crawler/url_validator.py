from urllib.parse import urlparse


def is_valid_url(url: str) -> bool:
    """
    Returns True if the URL is worth crawling.
    """

    if not url:
        return False

    url = url.strip()

    if url == "#":
        return False

    if " " in url:
        return False

    if url.startswith("javascript:"):
        return False

    if url.startswith("mailto:"):
        return False

    if url.startswith("tel:"):
        return False

    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        return False

    if not parsed.netloc:
        return False

    return True