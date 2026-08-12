import asyncio

from crawler.crawl_engine import CrawlEngine


START_URL = "https://www.iitj.ac.in"

# Tonight: crawl only 10 webpage pages.
# Tomorrow: change this number for the larger/full crawl.
MAX_PAGES = 10


async def main():
    engine = CrawlEngine()

    await engine.start(
        start_url=START_URL,
        max_pages=MAX_PAGES,
    )


if __name__ == "__main__":
    asyncio.run(main())
