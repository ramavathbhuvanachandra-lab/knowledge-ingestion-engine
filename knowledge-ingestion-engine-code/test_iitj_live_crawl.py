import asyncio

from crawler.crawl_engine import CrawlEngine


async def main():

    START_URL = "https://www.iitj.ac.in/"

    MAX_PAGES = 10

    print("=" * 100)
    print("IIT JODHPUR LIVE CRAWL TEST")
    print("=" * 100)
    print("Start URL :", START_URL)
    print("Max pages :", MAX_PAGES)
    print("=" * 100)

    engine = CrawlEngine()

    await engine.start(
        start_url=START_URL,
        max_pages=MAX_PAGES,
    )

    print()
    print("=" * 100)
    print("CRAWL COMPLETE")
    print("=" * 100)
    print("Pages crawled       :", engine.pages_crawled)
    print("Documents discovered:", engine.documents_discovered)
    print("Resources discovered:", engine.resources_discovered)
    print("Ignored plans       :", engine.ignored_plans)
    print("Failed pages        :", engine.failed_pages)
    print("=" * 100)


if __name__ == "__main__":
    asyncio.run(main())