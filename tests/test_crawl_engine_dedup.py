from crawler.crawl_engine import CrawlEngine
from models.crawl_plan import CrawlAction, CrawlPriority
from models.url import URLInfo, URLType


def make_plan(url: str):
    info = URLInfo(
        raw_url=url,
        normalized_url=url,
        url_type=URLType.WEBPAGE,
        discovered_from="https://example.com/",
        depth=1,
    )

    return CrawlEngine().policy.create_plan(
        info,
        depth=1,
    )


def test_equivalent_urls_share_inventory_identity():
    engine = CrawlEngine()

    plan_a = make_plan(
        "https://example.com/"
    )

    plan_b = make_plan(
        "https://example.com"
    )

    assert engine._register_url(
        plan_a,
        source_url="https://example.com/",
    )

    assert not engine._register_url(
        plan_b,
        source_url="https://example.com/",
    )

    assert engine.unique_urls_discovered == 1
    assert engine.duplicate_urls_skipped == 1