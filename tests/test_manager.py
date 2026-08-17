import asyncio

from crawler.crawl_engine import CrawlEngine


async def main():

    manager = CrawlEngine()

    await manager.start("https://iitj.ac.in")


if __name__ == "__main__":
    asyncio.run(main())