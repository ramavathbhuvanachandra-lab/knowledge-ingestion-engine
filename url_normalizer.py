from urllib.parse import urlsplit, urlunsplit
import re


def normalize_url(url: str) -> str:
    """
    Normalize a URL without changing its meaning.
    """

    url = url.strip()

    if not url:
        return ""

    parts = urlsplit(url)

    # Remove fragment (#section)
    fragment = ""

    # Remove duplicate slashes
    path = re.sub(r"/+", "/", parts.path)

    # Remove trailing slash except root
    if path.endswith("/") and path != "/":
        path = path[:-1]

    normalized = urlunsplit((
        parts.scheme,
        parts.netloc,
        path,
        parts.query,
        fragment
    ))

    return normalized