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

    # Remove duplicate slashes
    path = re.sub(r"/+", "/", parts.path)

    # ⭐ Root path should become empty
    if path == "/":
        path = ""

    # Remove trailing slash from non-root paths
    elif path.endswith("/"):
        path = path[:-1]

    return urlunsplit((
        parts.scheme.lower(),
        parts.netloc.lower(),
        path,
        parts.query,
        ""
    ))