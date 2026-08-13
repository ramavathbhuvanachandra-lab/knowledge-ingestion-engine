import asyncio
import time

from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
    CacheMode,
)


URL = "https://home.iitd.ac.in/"


async def main():

    print("=" * 70)
    print("IIT DELHI — ANTIBOT CONFIGURATION TEST")
    print("=" * 70)

    config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        wait_until="commit",
        page_timeout=60000,
        delay_before_return_html=1.0,

        magic=True,
        simulate_user=True,
        override_navigator=True,
    )

    start = time.perf_counter()

    try:

        async with AsyncWebCrawler() as crawler:

            result = await crawler.arun(
                url=URL,
                config=config,
            )

        elapsed = (
            time.perf_counter()
            - start
        )

        print()
        print(
            "SUCCESS :",
            result.success,
        )

        print(
            "TIME    :",
            f"{elapsed:.2f}s",
        )

        print(
            "HTML    :",
            len(result.html or ""),
        )

        print(
            "MARKDOWN:",
            len(result.markdown or ""),
        )

        title = ""

        if result.metadata:

            title = result.metadata.get(
                "title",
                "",
            )

        print(
            "TITLE   :",
            title,
        )

        if result.success:

            print()
            print(
                "RESULT  : PASS"
            )

        else:

            print()
            print(
                "RESULT  : FAIL"
            )

            print()
            print(
                "ERROR:"
            )

            print(
                result.error_message
            )

    except Exception as error:

        elapsed = (
            time.perf_counter()
            - start
        )

        print()
        print(
            "EXCEPTION:",
            type(error).__name__,
        )

        print(
            "TIME     :",
            f"{elapsed:.2f}s",
        )

        print(
            "MESSAGE  :",
            str(error),
        )


if __name__ == "__main__":

    asyncio.run(
        main()
    )