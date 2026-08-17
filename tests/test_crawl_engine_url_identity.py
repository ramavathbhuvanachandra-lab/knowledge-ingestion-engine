from crawler.crawl_engine import CrawlEngine


def test_root_and_trailing_slash_share_identity():
    engine = CrawlEngine()

    first_key = engine._normalize_tracking_key(
        "https://example.com/"
    )

    second_key = engine._normalize_tracking_key(
        "https://example.com"
    )

    assert first_key == second_key


def test_tracking_key_matches_canonical_normalization():
    engine = CrawlEngine()

    urls = [
        "https://example.com/",
        "https://example.com/about/",
        "HTTPS://EXAMPLE.COM/About/",
        "https://example.com/search?q=test#results",
    ]

    from crawler.url_normalizer import normalize_url

    for url in urls:
        assert (
            engine._normalize_tracking_key(url)
            == normalize_url(url)
        )


def test_equivalent_root_urls_have_one_identity():
    engine = CrawlEngine()

    urls = [
        "https://example.com",
        "https://example.com/",
        "HTTPS://EXAMPLE.COM/",
        " https://example.com/ ",
    ]

    keys = {
        engine._normalize_tracking_key(url)
        for url in urls
    }

    assert len(keys) == 1