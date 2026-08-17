import asyncio
import time

from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
    CacheMode,
)


# ============================================================
# TEST WEBSITES
# ============================================================

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


# ============================================================
# LOADING STRATEGIES
# ============================================================

STRATEGIES = [
    "domcontentloaded",
    "load",
    "commit",
]


# ============================================================
# TEST ONE STRATEGY
# ============================================================

async def test_strategy(
    crawler,
    site_name,
    url,
    strategy,
):

    print()
    print("-" * 70)
    print(
        f"{site_name} | {strategy}"
    )
    print("-" * 70)

    start_time = time.perf_counter()

    config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        wait_until=strategy,
        page_timeout=60000,
        delay_before_return_html=1.0,
    )

    try:

        result = await crawler.arun(
            url=url,
            config=config,
        )

        elapsed = (
            time.perf_counter()
            - start_time
        )

        html_length = len(
            result.html or ""
        )

        print(
            "SUCCESS     :",
            result.success
        )

        print(
            "TIME        :",
            f"{elapsed:.2f}s"
        )

        print(
            "HTML LENGTH :",
            html_length
        )

        if result.success:

            title = ""

            if result.metadata:

                title = result.metadata.get(
                    "title",
                    ""
                )

            print(
                "TITLE       :",
                title
            )

            print(
                "RESULT      : PASS"
            )

            return {
                "success": True,
                "time": elapsed,
                "html_length": html_length,
                "error": "",
            }

        print(
            "RESULT      : FAIL"
        )

        print()

        print(
            "ERROR:"
        )

        print(
            result.error_message
        )

        return {
            "success": False,
            "time": elapsed,
            "html_length": html_length,
            "error": result.error_message,
        }

    except Exception as error:

        elapsed = (
            time.perf_counter()
            - start_time
        )

        print(
            "SUCCESS     : False"
        )

        print(
            "TIME        :",
            f"{elapsed:.2f}s"
        )

        print(
            "HTML LENGTH : 0"
        )

        print(
            "RESULT      : EXCEPTION"
        )

        print(
            "ERROR       :",
            type(error).__name__,
        )

        print(
            "MESSAGE     :",
            str(error),
        )

        return {
            "success": False,
            "time": elapsed,
            "html_length": 0,
            "error": str(error),
        }


# ============================================================
# TEST ONE WEBSITE
# ============================================================

async def test_site(
    crawler,
    site_name,
    url,
):

    print()
    print("=" * 70)
    print(
        f"TESTING: {site_name}"
    )
    print(
        url
    )
    print("=" * 70)

    site_results = {}

    for strategy in STRATEGIES:

        result = await test_strategy(
            crawler,
            site_name,
            url,
            strategy,
        )

        site_results[strategy] = result

    return site_results


# ============================================================
# FINAL SUMMARY
# ============================================================

def print_summary(
    all_results,
):

    print()
    print()
    print("=" * 90)
    print("FINAL CRAWLER STRATEGY COMPARISON")
    print("=" * 90)

    print()

    print(
        f"{'WEBSITE':<15}"
        f"{'DOMCONTENT':<18}"
        f"{'LOAD':<18}"
        f"{'COMMIT':<18}"
    )

    print("-" * 90)

    for site_name, results in all_results.items():

        values = []

        for strategy in STRATEGIES:

            result = results[strategy]

            if result["success"]:

                values.append(
                    f"PASS {result['time']:.1f}s"
                )

            else:

                values.append(
                    "FAIL"
                )

        print(
            f"{site_name:<15}"
            f"{values[0]:<18}"
            f"{values[1]:<18}"
            f"{values[2]:<18}"
        )

    print("-" * 90)

    print()

    print(
        "HTML SIZE FOR SUCCESSFUL CRAWLS:"
    )

    print()

    for site_name, results in all_results.items():

        print(
            site_name
        )

        for strategy in STRATEGIES:

            result = results[strategy]

            if result["success"]:

                print(
                    f"  {strategy:<20}"
                    f"{result['html_length']} characters"
                )

        print()


# ============================================================
# MAIN
# ============================================================

async def main():

    all_results = {}

    print()
    print("=" * 70)
    print("MULTI-SITE CRAWLER ROBUSTNESS TEST")
    print("=" * 70)

    print()

    print(
        "Sites:",
        len(TEST_SITES)
    )

    print(
        "Strategies:",
        ", ".join(STRATEGIES)
    )

    async with AsyncWebCrawler() as crawler:

        for site_name, url in TEST_SITES:

            results = await test_site(
                crawler,
                site_name,
                url,
            )

            all_results[site_name] = results

    print_summary(
        all_results
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    asyncio.run(
        main()
    )