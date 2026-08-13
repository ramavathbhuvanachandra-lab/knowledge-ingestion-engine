import asyncio

from crawler.crawl_engine import CrawlEngine


START_URL = "https://www.iitj.ac.in/"


async def main():

    print()
    print("=" * 100)
    print("IIT JODHPUR — FULL PRODUCTION CRAWL")
    print("=" * 100)

    engine = CrawlEngine(
        report_root="storage/crawl_reports"
    )

    report = await engine.start(
        start_url=START_URL,
        max_pages=None,
    )

    stats = report["statistics"]

    print()
    print("=" * 100)
    print("FINAL PRODUCTION CRAWL SUMMARY")
    print("=" * 100)

    print(
        "Mode                 :",
        report["crawl"]["mode"],
    )

    print(
        "Start URL            :",
        report["crawl"]["start_url"],
    )

    print(
        "Unique URLs          :",
        stats["unique_urls_discovered"],
    )

    print(
        "Duplicate URLs       :",
        stats["duplicate_urls_skipped"],
    )

    print(
        "Pages Attempted      :",
        stats["pages_attempted"],
    )

    print(
        "Pages Crawled        :",
        stats["pages_crawled"],
    )

    print(
        "Failed Pages         :",
        stats["failed_pages"],
    )

    print(
        "Documents Discovered :",
        stats["documents_discovered"],
    )

    print(
        "Documents Processed  :",
        stats["documents_processed"],
    )

    print(
        "Failed Documents     :",
        stats["failed_documents"],
    )

    print(
        "Resources            :",
        stats["resources_discovered"],
    )

    print(
        "Ignored Plans        :",
        stats["ignored_plans"],
    )

    print(
        "Tracked URLs         :",
        stats["tracked_urls"],
    )

    print(
        "Remaining Queue      :",
        stats["remaining_queue"],
    )

    print(
        "Queue Exhausted      :",
        report["queue_exhausted"],
    )

    print()
    print(
        "Crawl Report:"
    )

    print(
        "storage/crawl_reports/"
        "www.iitj.ac.in/"
        "crawl_report.json"
    )

    print()
    print("=" * 100)


if __name__ == "__main__":
    asyncio.run(main())