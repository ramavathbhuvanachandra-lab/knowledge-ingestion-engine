from urllib.parse import urlparse

from models.url import URLInfo, URLType


IMAGE_EXTENSIONS = (
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".svg",
    ".webp",
    ".bmp",
    ".ico"
)


def classify_url(
    raw_url: str,
    normalized_url: str,
    base_domain: str,
    discovered_from: str
) -> URLInfo:

    parsed = urlparse(normalized_url)

    # Invalid URL
    if not parsed.scheme or not parsed.netloc:
        url_type = URLType.INVALID

    # External Website
    elif parsed.netloc != base_domain:
        url_type = URLType.EXTERNAL

    # PDF
    elif normalized_url.lower().endswith(".pdf"):
        url_type = URLType.PDF

    elif normalized_url.lower().endswith(".xlsx"):
        url_type = URLType.XLSX

    # Image
    elif normalized_url.lower().endswith(IMAGE_EXTENSIONS):
        url_type = URLType.IMAGE

    # Default
    else:
        url_type = URLType.WEBPAGE

    return URLInfo(
        raw_url=raw_url,
        normalized_url=normalized_url,
        url_type=url_type,
        discovered_from=discovered_from
    )