from crawler.link_extractor import (
    extract_internal_links,
)


BASE_URL = "https://example.com/"


def test_realistic_internal_links_are_discovered():
    html = """
    <html>
        <body>
            <a href="/about">About</a>
            <a href="/admission">Admission</a>
            <a href="/search?q=engineering&page=2">
                Search
            </a>
            <a href="/file.pdf?version=2">
                PDF
            </a>
            <a href="/image.jpg?width=800">
                Image
            </a>
        </body>
    </html>
    """

    links = extract_internal_links(
        html=html,
        base_url=BASE_URL,
    )

    assert links == [
        "https://example.com/about",
        "https://example.com/admission",
        "https://example.com/file.pdf?version=2",
        "https://example.com/image.jpg?width=800",
        "https://example.com/search?q=engineering&page=2",
    ]


def test_relative_and_absolute_internal_links_are_both_supported():
    html = """
    <a href="/about">Relative</a>
    <a href="https://example.com/admission">
        Absolute
    </a>
    """

    links = extract_internal_links(
        html=html,
        base_url=BASE_URL,
    )

    assert links == [
        "https://example.com/about",
        "https://example.com/admission",
    ]


def test_external_links_are_excluded():
    html = """
    <a href="https://google.com/">Google</a>
    <a href="https://other.example.com/page">
        External
    </a>
    <a href="/internal">Internal</a>
    """

    links = extract_internal_links(
        html=html,
        base_url=BASE_URL,
    )

    assert links == [
        "https://example.com/internal",
    ]


def test_special_links_are_excluded():
    html = """
    <a href="#">Fragment</a>
    <a href="javascript:void(0)">JavaScript</a>
    <a href="mailto:test@example.com">Email</a>
    <a href="tel:+911234567890">Phone</a>
    <a href="/valid">Valid</a>
    """

    links = extract_internal_links(
        html=html,
        base_url=BASE_URL,
    )

    assert links == [
        "https://example.com/valid",
    ]


def test_malformed_links_do_not_stop_other_links():
    html = """
    <a href="https://[">Broken IPv6</a>
    <a href="https://example.com:bad-port/">
        Broken Port
    </a>
    <a href="/good">Good</a>
    <a href="/another-good">Another Good</a>
    """

    links = extract_internal_links(
        html=html,
        base_url=BASE_URL,
    )

    assert links == [
        "https://example.com/another-good",
        "https://example.com/good",
    ]


def test_duplicate_links_are_deduplicated():
    html = """
    <a href="/about">About</a>
    <a href="/about/">About Slash</a>
    <a href="https://example.com/about">
        About Absolute
    </a>
    """

    links = extract_internal_links(
        html=html,
        base_url=BASE_URL,
    )

    assert links == [
        "https://example.com/about",
    ]


def test_fragment_is_removed_by_normalization():
    html = """
    <a href="/about#overview">
        About
    </a>
    <a href="/about#contact">
        About Contact
    </a>
    """

    links = extract_internal_links(
        html=html,
        base_url=BASE_URL,
    )

    assert links == [
        "https://example.com/about",
    ]


def test_hostname_case_is_normalized():
    html = """
    <a href="HTTPS://EXAMPLE.COM/About">
        About
    </a>
    """

    links = extract_internal_links(
        html=html,
        base_url=BASE_URL,
    )

    assert links == [
        "https://example.com/About",
    ]


def test_empty_html_returns_empty():
    assert (
        extract_internal_links(
            html="",
            base_url=BASE_URL,
        )
        == []
    )


def test_empty_base_url_returns_empty():
    assert (
        extract_internal_links(
            html="<a href='/about'>About</a>",
            base_url="",
        )
        == []
    )


def test_no_links_returns_empty():
    html = """
    <html>
        <body>
            <h1>No navigation here</h1>
        </body>
    </html>
    """

    assert (
        extract_internal_links(
            html=html,
            base_url=BASE_URL,
        )
        == []
    )