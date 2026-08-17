from urllib.parse import urlparse


# URL path fragments commonly used by JavaScript-driven
# menu systems instead of real navigation targets.
PSEUDO_TARGET_PATTERNS = (
    ":void",
    "void(0)",
)


def is_valid_url(
    url: str,
) -> bool:
    """
    Return True when a URL is a plausible HTTP/HTTPS
    crawl target.

    The validator operates on an already-resolved URL.
    Relative URLs should be resolved before reaching this
    function.

    Invalid or malformed input must return False rather
    than raising an exception.
    """

    if not url:
        return False

    url = url.strip()

    if not url:
        return False

    # Obvious non-navigation targets.
    if url == "#":
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

    # Raw whitespace inside a URL is treated as malformed.
    if any(
        character.isspace()
        for character in url
    ):
        return False

    # ------------------------------------------------------
    # URL parsing
    #
    # urllib.parse.urlparse() can raise ValueError for
    # malformed URLs, especially invalid IPv6/netloc forms.
    #
    # A crawler validator must reject such input rather
    # than allowing one malformed link to break discovery.
    # ------------------------------------------------------

    try:
        parsed = urlparse(
            url
        )

        # Access hostname explicitly so malformed ports,
        # IPv6 addresses, and other netloc issues are
        # surfaced here rather than later in the pipeline.
        hostname = parsed.hostname

        if hostname is None:
            return False

        # Accessing .port can itself raise ValueError for
        # invalid ports such as:
        #
        # https://example.com:bad-port/
        #
        _ = parsed.port

    except (
        ValueError,
    ):
        return False

    # Only HTTP/HTTPS are crawlable by this crawler.
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
    path = (
        parsed.path
        or ""
    ).lower()

    if any(
        pattern in path
        for pattern in PSEUDO_TARGET_PATTERNS
    ):
        return False

    return True