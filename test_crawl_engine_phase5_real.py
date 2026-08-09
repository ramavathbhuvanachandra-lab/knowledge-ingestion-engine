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
    # DOCUMENT INVENTORY
    # --------------------------------------------------

    print("\nDOCUMENT INVENTORY")
    print("-" * 100)

    print(
        "Unique documents:",
        len(engine.document_inventory),
    )

    for index, (document_url, document) in enumerate(
        engine.document_inventory.items(),
        start=1,
    ):
        print(
            f"\nDocument #{index}"
        )

        print(
            "URL:",
            document_url,
        )

        print(
            "Type:",
            document["url_type"],
        )

        print(
            "Depth:",
            document["depth"],
        )

        print(
            "Discovered from:",
            len(
                document["discovered_from"]
            ),
            "page(s)",
        )

        for source_page in document[
            "discovered_from"
        ]:
            print(
                "  -",
                source_page,
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
        engine.depth_tracker.size()
        >= engine.pages_crawled
    ), (
        "Tracked URL count is smaller "
        "than pages crawled"
    )

    # --------------------------------------------------
    # DOCUMENT INVENTORY INVARIANTS
    # --------------------------------------------------

    assert (
        engine.documents_discovered
        == len(engine.document_inventory)
    ), (
        "documents_discovered does not match "
        "unique document inventory size"
    )

    for document_url, document in (
        engine.document_inventory.items()
    ):

        assert document_url, (
            "Document URL is empty"
        )

        assert document["url"] == document_url, (
            "Inventory URL mismatch"
        )

        assert document["url_type"] == "pdf", (
            f"Unexpected document type: "
            f"{document['url_type']}"
        )

        assert document["discovered_from"], (
            f"No source page recorded for: "
            f"{document_url}"
        )

        # Every source page should be unique.
        assert len(
            document["discovered_from"]
        ) == len(
            set(
                document["discovered_from"]
            )
        ), (
            f"Duplicate source pages found "
            f"for document: {document_url}"
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

            print(
                "\nFAILED:",
                url,
            )

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

    assert passed == len(TEST_URLS), (
        "One or more real crawl engine "
        "tests failed"
    )

    print(
        "\nREAL CRAWL ENGINE INTEGRATION: PASS"
    )


if __name__ == "__main__":
    asyncio.run(main())