import asyncio
import time

from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
    CacheMode,
)


TEST_SITES = [
    (
        "GWPGC",
        "https://gwpgc.ac.in/",
    ),
    (
        "IIT DELHI",
        "https://home.iitd.ac.in/",
    ),
    (
        "VBSPU",
        "https://www.vbspu.ac.in/en",
    ),
]


async def test_site(
    crawler,
    name,
    url,
):

    print()
    print("=" * 70)
    print(name)
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

        result = await crawler.arun(
            url=url,
            config=config,
        )

        elapsed = (
            time.perf_counter()
            - start
        )

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

            print(
                "RESULT  : PASS"
            )

        else:

            print(
                "RESULT  : FAIL"
            )

            print()
            print(
                result.error_message
            )

    except Exception as error:

        elapsed = (
            time.perf_counter()
            - start
        )

        print(
            "SUCCESS : False"
        )

        print(
            "TIME    :",
            f"{elapsed:.2f}s",
        )

        print(
            "EXCEPTION:",
            type(error).__name__,
        )

        print(
            "MESSAGE :",
            str(error),
        )


async def main():

    print()
    print("=" * 70)
    print("RESILIENT CRAWLER TEST")
    print("=" * 70)

    async with AsyncWebCrawler() as crawler:

        for name, url in TEST_SITES:

            await test_site(
                crawler,
                name,
                url,
            )

    print()
    print("=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":

    asyncio.run(
        main()
    )