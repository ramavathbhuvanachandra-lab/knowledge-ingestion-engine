from pathlib import PurePosixPath
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
    ".ico",
)


DOCUMENT_EXTENSIONS = {
    ".pdf": URLType.PDF,
    ".xlsx": URLType.XLSX,
}


def classify_url(
    raw_url: str,
    normalized_url: str,
    base_domain: str,
    discovered_from: str,
) -> URLInfo:
    """
    Classify a resolved URL into a crawler URL type.

    Classification is based on:
    - URL validity
    - hostname/domain
    - path file extension

    Query parameters do not affect file-type detection.
    """

    parsed = urlparse(
        normalized_url
    )

    # ------------------------------------------------------
    # Invalid URL
    # ------------------------------------------------------

    if not parsed.scheme or not parsed.netloc:
        url_type = URLType.INVALID

    else:
        parsed_domain = (
            parsed.netloc
            .lower()
        )

        expected_domain = (
            (base_domain or "")
            .strip()
            .lower()
        )

        # --------------------------------------------------
        # External Website
        # --------------------------------------------------

        if parsed_domain != expected_domain:
            url_type = URLType.EXTERNAL

        else:
            # ----------------------------------------------
            # File extension must come from PATH only.
            #
            # Example:
            # /file.pdf?version=2
            #
            # parsed.path = /file.pdf
            # parsed.query = version=2
            # ----------------------------------------------

            path = (
                parsed.path
                or ""
            )

            suffix = (
                PurePosixPath(
                    path
                )
                .suffix
                .lower()
            )

            # ----------------------------------------------
            # Documents
            # ----------------------------------------------

            if suffix in DOCUMENT_EXTENSIONS:

                url_type = (
                    DOCUMENT_EXTENSIONS[
                        suffix
                    ]
                )

            # ----------------------------------------------
            # Images
            # ----------------------------------------------

            elif suffix in IMAGE_EXTENSIONS:

                url_type = URLType.IMAGE

            # ----------------------------------------------
            # Default webpage
            # ----------------------------------------------

            else:

                url_type = URLType.WEBPAGE

    return URLInfo(
        raw_url=raw_url,
        normalized_url=normalized_url,
        url_type=url_type,
        discovered_from=discovered_from,
    )