import asyncio

from crawler.crawl_engine import CrawlEngine


TEST_URLS = [
    "https://gwpgc.ac.in/",
    "https://www.iitj.ac.in/",
    "https://www.vbspu.ac.in/en",
    "https://home.iitd.ac.in/",
]


async def test_engine(url):
    print("\n" + "=" * 100)
    print("REAL CRAWL ENGINE TEST")
    print("URL:", url)
    print("=" * 100)

    engine = CrawlEngine()

    await engine.start(url)

    print("\nENGINE RESULTS")
    print("-" * 100)

    print(
        "Pages crawled       :",
        engine.pages_crawled,
    )

    print(
        "Documents discovered:",
        engine.documents_discovered,
    )

    print(
        "Resources discovered:",
        engine.resources_discovered,
    )

    print(
        "Ignored plans       :",
        engine.ignored_plans,
    )

    print(
        "Failed pages        :",
        engine.failed_pages,
    )

    print(
        "Tracked URLs        :",
        engine.depth_tracker.size(),
    )

    print(
        "Remaining queue     :",
        engine.queue.size(),
    )

    # --------------------------------------------------
    # SAFETY / INTEGRATION INVARIANTS
    # --------------------------------------------------

    assert engine.pages_crawled >= 1, (
        f"Engine crawled zero pages: {url}"
    )

    assert engine.failed_pages == 0, (
        f"Engine had failed pages: "
        f"{engine.failed_pages}"
    )

    assert (
        engine.depth_tracker.size() >=
        engine.pages_crawled
    ), (
        "Tracked URL count is smaller "
        "than pages crawled"
    )

    print(
        "\nPASS:",
        url,
    )


async def main():

    passed = 0

    for url in TEST_URLS:

        try:

            await test_engine(url)

            passed += 1

        except Exception as error:

            print("\nFAILED:", url)

            print(
                f"{type(error).__name__}: "
                f"{error}"
            )

            raise

    print("\n" + "=" * 100)

    print(
        f"REAL CRAWL ENGINE TEST: "
        f"{passed}/{len(TEST_URLS)} PASSED"
    )

    print("=" * 100)

    assert passed == len(TEST_URLS)

    print(
        "\nREAL CRAWL ENGINE INTEGRATION: PASS"
    )


if __name__ == "__main__":
    asyncio.run(main())