from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from crawler.url_normalizer import normalize_url
from crawler.url_validator import is_valid_url


NON_NAVIGATION_SCHEMES = (
    "javascript:",
    "mailto:",
    "tel:",
    "data:",
)


def extract_internal_links(
    html: str,
    base_url: str,
) -> list[str]:
    """
    Extract valid internal HTTP/HTTPS links from HTML.

    The extractor is deliberately defensive:

    - Empty hrefs are ignored.
    - Fragment-only links are ignored.
    - Non-navigation schemes are ignored.
    - Malformed hrefs that make urljoin() fail are ignored.
    - Final URLs are normalized and validated.
    - External URLs are excluded.
    - Duplicate normalized URLs are removed.
    """

    if not html or not base_url:
        return []

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    links: set[str] = set()

    # Resolve the host from the crawl source once.
    try:
        base_domain = (
            urlparse(
                base_url
            ).netloc.lower()
        )
    except ValueError:
        return []

    if not base_domain:
        return []

    for tag in soup.find_all(
        "a",
        href=True,
    ):

        href = tag.get(
            "href",
            "",
        )

        if not isinstance(
            href,
            str,
        ):
            continue

        href = href.strip()

        if not href:
            continue

        # --------------------------------------------------
        # Reject non-navigation targets BEFORE urljoin().
        # --------------------------------------------------

        if href == "#":
            continue

        lowered_href = href.lower()

        if lowered_href.startswith(
            NON_NAVIGATION_SCHEMES
        ):
            continue

        # Other fragment links such as:
        #
        #   #section
        #
        # are also document-internal navigation and should
        # not become the page URL itself.
        if href.startswith("#"):
            continue

        # --------------------------------------------------
        # Resolve safely.
        # --------------------------------------------------

        try:
            absolute_url = urljoin(
                base_url,
                href,
            )
        except ValueError:
            continue

        # --------------------------------------------------
        # Normalize.
        # --------------------------------------------------

        normalized_url = normalize_url(
            absolute_url
        )

        if not normalized_url:
            continue

        # --------------------------------------------------
        # Validate.
        # --------------------------------------------------

        if not is_valid_url(
            normalized_url
        ):
            continue

        # --------------------------------------------------
        # Same-host filtering.
        # --------------------------------------------------

        try:
            parsed = urlparse(
                normalized_url
            )
        except ValueError:
            continue

        if (
            parsed.netloc.lower()
            != base_domain
        ):
            continue

        links.add(
            normalized_url
        )

    return sorted(
        links
    )