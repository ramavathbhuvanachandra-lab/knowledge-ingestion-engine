from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


def extract_internal_links(html: str, base_url: str):

    soup = BeautifulSoup(html, "html.parser")

    links = set()

    base_domain = urlparse(base_url).netloc

    for tag in soup.find_all("a", href=True):

        href = tag["href"]

        absolute_url = urljoin(base_url, href)

        parsed = urlparse(absolute_url)

        if parsed.netloc == base_domain:

            links.add(
                parsed.scheme + "://" + parsed.netloc + parsed.path
            )

    return sorted(links)