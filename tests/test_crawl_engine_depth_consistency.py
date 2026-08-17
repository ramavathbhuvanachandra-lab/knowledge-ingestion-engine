import asyncio

from crawler.crawl_engine import CrawlEngine


def test_root_is_registered_in_depth_tracker():
    async def run_crawl():
        engine = CrawlEngine()

        report = await engine.start(
            start_url="https://gwpgc.ac.in/",
            max_pages=1,
        )

        return engine, report

    engine, report = asyncio.run(
        run_crawl()
    )

    root_url = "https://gwpgc.ac.in"

    assert root_url in engine.url_inventory
    assert root_url in engine.depth_tracker._depths
    assert engine.depth_tracker.get_depth(
        root_url
    ) == 0

    assert (
        report["statistics"]["unique_urls_discovered"]
        == report["statistics"]["tracked_urls"]
    )