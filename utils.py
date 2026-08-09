from urllib.parse import urlparse
import re


def get_domain(url: str) -> str:
    """
    Return the normalized hostname from a valid URL.

    Example:

        https://www.iitj.ac.in/page

        -> www.iitj.ac.in
    """

    parsed = urlparse((url or "").strip())

    domain = parsed.hostname

    if not domain:
        return "unknown-domain"

    return domain.lower().strip()


def sanitize_filename(name: str) -> str:
    """
    Convert arbitrary text into a filesystem-safe filename.
    """

    name = (name or "").strip()

    if not name:
        return "page"

    name = name.lower()

    name = re.sub(
        r"[^a-z0-9]+",
        "_",
        name,
    )

    name = re.sub(
        r"_+",
        "_",
        name,
    )

    name = name.strip("_")

    return name or "page"