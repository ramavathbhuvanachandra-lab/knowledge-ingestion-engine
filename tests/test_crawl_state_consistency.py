import asyncio

from crawler.crawl_engine import CrawlEngine


def test_crawl_state_consistency():
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

    inventory_urls = {
        record["normalized_url"]
        for record in engine.url_inventory.values()
    }

    tracked_urls = set(
        engine.depth_tracker._depths.keys()
    )

    queue_seen_urls = set(
        engine.queue._seen
    )

    print(
        "\n=== CRAWL STATE CONSISTENCY ==="
    )

    print(
        "Inventory:",
        len(inventory_urls),
    )

    print(
        "Depth tracker:",
        len(tracked_urls),
    )

    print(
        "Queue seen:",
        len(queue_seen_urls),
    )

    print(
        "Report unique:",
        report["statistics"]["unique_urls_discovered"],
    )

    print(
        "Report tracked:",
        report["statistics"]["tracked_urls"],
    )

    print(
        "\n--- INVENTORY vs DEPTH ---"
    )

    print(
        "Missing from depth:",
        sorted(
            inventory_urls - tracked_urls
        ),
    )

    print(
        "Extra in depth:",
        sorted(
            tracked_urls - inventory_urls
        ),
    )

    print(
        "\n--- INVENTORY vs QUEUE ---"
    )

    print(
        "Missing from queue lifecycle:",
        sorted(
            inventory_urls - queue_seen_urls
        ),
    )

    print(
        "Extra in queue lifecycle:",
        sorted(
            queue_seen_urls - inventory_urls
        ),
    )

    assert report["statistics"]["failed_pages"] == 0