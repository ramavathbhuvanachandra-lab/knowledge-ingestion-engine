from crawler.url_validator import is_valid_url


# ============================================================
# VALID REAL-WORLD URL SHAPES
# ============================================================

VALID_URLS = [
    "https://example.com",
    "https://example.com/",
    "http://example.com/",
    "https://example.com/about",
    "https://example.com/about/",
    "https://example.com/PageContents.aspx?pageid=29",
    "https://example.com/Search?query=admission&page=2",
    "https://example.com/file.pdf?version=2",
    "https://example.com/image.jpg?width=800",
    "https://sub.example.com/page",
    "https://example.com:443/page",
    "http://example.com:80/page",
    "https://user:pass@example.com/page",
    "https://example.com/my%20page",
    "https://example.com/%7Euser",
    "https://example.com/a%2Fb",
    "https://example.com/a;b",
    "https://example.com/path?x=1#section",
    "HTTPS://EXAMPLE.COM/About",
]


# ============================================================
# INVALID / NON-CRAWLABLE URL SHAPES
# ============================================================

INVALID_URLS = [
    "",
    "   ",
    "#",
    "javascript:void(0)",
    "JavaScript:void(0);",
    "javascript:alert('hello')",
    "mailto:test@example.com",
    "TEL:+911234567890",
    "tel:+911234567890",
    "data:text/html,hello",
    "ftp://example.com/file.pdf",
    "file:///tmp/test.pdf",
    ":VOID0;",
    ":VOID0;?cd=MwA%3D",
    "https://example.com/:VOID0;",
    "https://example.com/:VOID0;?cd=MwA%3D",
]


# ============================================================
# WHITESPACE
# ============================================================

def test_valid_urls_with_no_raw_spaces():
    for url in VALID_URLS:
        assert is_valid_url(url), (
            f"Expected valid URL to pass: {url!r}"
        )


def test_empty_and_whitespace_urls_are_rejected():
    cases = [
        "",
        " ",
        "    ",
        "\t",
        "\n",
    ]

    for url in cases:
        assert not is_valid_url(url), (
            f"Expected whitespace/empty URL to fail: {url!r}"
        )


def test_internal_raw_whitespace_is_rejected():
    cases = [
        "https://example.com/my page",
        "https://example.com/page?id=hello world",
        "https://example.com/ page",
    ]

    for url in cases:
        assert not is_valid_url(url), (
            f"Expected raw-space URL to fail: {url!r}"
        )


# ============================================================
# SCHEME
# ============================================================

def test_http_and_https_are_valid():
    assert is_valid_url(
        "http://example.com/"
    )

    assert is_valid_url(
        "https://example.com/"
    )


def test_scheme_comparison_is_case_insensitive():
    assert is_valid_url(
        "HTTP://example.com/page"
    )

    assert is_valid_url(
        "HTTPS://example.com/page"
    )


def test_non_http_schemes_are_rejected():
    for url in [
        "ftp://example.com/file",
        "file:///tmp/file",
        "data:text/plain,hello",
        "ws://example.com/socket",
        "wss://example.com/socket",
    ]:
        assert not is_valid_url(url), (
            f"Expected non-HTTP scheme to fail: {url!r}"
        )


# ============================================================
# DOMAIN / NETLOC
# ============================================================

def test_missing_domain_is_rejected():
    cases = [
        "https://",
        "https:///page",
        "http:///page",
    ]

    for url in cases:
        assert not is_valid_url(url), (
            f"Expected missing-domain URL to fail: {url!r}"
        )


def test_subdomains_are_valid_urls():
    assert is_valid_url(
        "https://library.example.com/"
    )


def test_ports_are_valid():
    assert is_valid_url(
        "https://example.com:443/page"
    )

    assert is_valid_url(
        "http://example.com:8080/page"
    )


def test_userinfo_is_not_rejected_by_validator():
    assert is_valid_url(
        "https://user:pass@example.com/page"
    )


# ============================================================
# QUERY / FRAGMENT
# ============================================================

def test_query_string_is_valid():
    assert is_valid_url(
        "https://example.com/search?q=test"
    )


def test_complex_query_string_is_valid():
    assert is_valid_url(
        "https://example.com/search?"
        "department=engineering&year=2026&page=2"
    )


def test_fragment_does_not_make_url_invalid():
    assert is_valid_url(
        "https://example.com/page#results"
    )


# ============================================================
# ENCODED URLS
# ============================================================

def test_percent_encoded_space_is_valid():
    assert is_valid_url(
        "https://example.com/my%20page"
    )


def test_percent_encoded_tilde_is_valid():
    assert is_valid_url(
        "https://example.com/%7Euser"
    )


def test_percent_encoded_slash_is_valid():
    assert is_valid_url(
        "https://example.com/a%2Fb"
    )


# ============================================================
# JAVASCRIPT / SPECIAL TARGETS
# ============================================================

def test_javascript_targets_are_rejected():
    cases = [
        "javascript:void(0)",
        "javascript:void(0);",
        "JavaScript:void(0)",
        "JAVASCRIPT:VOID(0)",
        "javascript:window.open('/page')",
    ]

    for url in cases:
        assert not is_valid_url(url), (
            f"Expected JavaScript URL to fail: {url!r}"
        )


def test_mailto_targets_are_rejected():
    assert not is_valid_url(
        "mailto:admin@example.com"
    )


def test_tel_targets_are_rejected():
    assert not is_valid_url(
        "tel:+911234567890"
    )


def test_fragment_only_target_is_rejected():
    assert not is_valid_url("#")


# ============================================================
# PSEUDO NAVIGATION
# ============================================================

def test_pseudo_navigation_paths_are_rejected():
    cases = [
        "https://example.com/:VOID0;",
        "https://example.com/:VOID0;?cd=MwA%3D",
        "https://example.com/menu/void(0)",
    ]

    for url in cases:
        assert not is_valid_url(url), (
            f"Expected pseudo-navigation URL to fail: {url!r}"
        )


# ============================================================
# REAL DOCUMENT / RESOURCE URLS
# ============================================================

def test_real_document_url_shapes_are_valid():
    cases = [
        "https://example.com/files/brochure.pdf",
        "https://example.com/files/brochure.pdf?version=2",
        "https://example.com/files/fees.xlsx",
        "https://example.com/files/fees.xlsx?download=true",
    ]

    for url in cases:
        assert is_valid_url(url), (
            f"Expected document URL to pass: {url!r}"
        )


def test_real_image_url_shapes_are_valid():
    cases = [
        "https://example.com/images/logo.png",
        "https://example.com/images/campus.jpg?width=800",
        "https://example.com/assets/icon.svg",
    ]

    for url in cases:
        assert is_valid_url(url), (
            f"Expected image URL to pass: {url!r}"
        )


# ============================================================
# MALFORMED URL CASES
#
# These are important because URL parsing itself can sometimes
# raise exceptions. The validator should reject bad input rather
# than taking down the crawl.
# ============================================================

def test_malformed_urls_are_rejected():
    cases = [
        "https://[",
        "https://[::1",
        "https://example.com:bad-port/",
        "://example.com",
        "https://",
    ]

    for url in cases:
        assert not is_valid_url(url), (
            f"Expected malformed URL to fail: {url!r}"
        )


# ============================================================
# BOOLEAN CONTRACT
# ============================================================

def test_validator_returns_boolean():
    cases = [
        "https://example.com",
        "javascript:void(0)",
        "",
        "https://example.com/file.pdf?x=1",
    ]

    for url in cases:
        result = is_valid_url(url)

        assert isinstance(result, bool), (
            f"Validator must return bool for {url!r}, "
            f"got {type(result).__name__}"
        )