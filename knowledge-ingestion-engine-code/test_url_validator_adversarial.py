from crawler.url_validator import is_valid_url


VALID_URLS = [
    "https://example.com",
    "https://example.com/",
    "https://example.com/about",
    "https://example.com/page?id=10",
    "https://example.com/PageContents.aspx?pageid=29",
    "https://example.com/search?department=engineering&year=2026",
]


INVALID_URLS = [
    "",
    "   ",
    "#",
    "javascript:void(0)",
    "JavaScript:void(0);",
    "mailto:test@example.com",
    "tel:+911234567890",
    ":VOID0;",
    ":VOID0;?cd=MwA%3D",
    "https://example.com/:VOID0;",
    "https://example.com/:VOID0;?cd=MwA%3D",
]


def test_valid_urls():

    for url in VALID_URLS:

        assert is_valid_url(url), (
            f"Expected valid URL to pass: {url}"
        )


def test_invalid_urls():

    for url in INVALID_URLS:

        assert not is_valid_url(url), (
            f"Expected invalid URL to be rejected: {url}"
        )


if __name__ == "__main__":

    test_valid_urls()
    test_invalid_urls()

    print("URL VALIDATOR ADVERSARIAL TESTS: PASS")