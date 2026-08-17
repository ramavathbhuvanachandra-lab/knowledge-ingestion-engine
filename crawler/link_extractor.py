from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from crawler.url_normalizer import normalize_url
from crawler.url_validator import is_valid_url


def extract_internal_links(
    html: str,
    base_url: str,
) -> list[str]:

    if not html or not base_url:
        return []

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    links: set[str] = set()

    base_domain = urlparse(
        base_url
    ).netloc.lower()

    for tag in soup.find_all(
        "a",
        href=True,
    ):

        href = tag.get("href", "")

        if not isinstance(href, str):
            continue

        href = href.strip()

        if not href:
            continue

        absolute_url = urljoin(
            base_url,
            href,
        )

        normalized_url = normalize_url(
            absolute_url
        )

        if not is_valid_url(
            normalized_url
        ):
            continue

        parsed = urlparse(
            normalized_url
        )

        if parsed.netloc.lower() != base_domain:
            continue

        links.add(
            normalized_url
        )

    return sorted(links)