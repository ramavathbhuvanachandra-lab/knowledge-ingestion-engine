import asyncio
import re
import time

from bs4 import BeautifulSoup
from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
    CacheMode,
)


URL = "https://gwpgc.ac.in/"


def analyze_result(name, result):
    html = result.html or ""
    markdown = result.markdown or ""

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    links = soup.find_all("a")

    nav_elements = soup.find_all("nav")

    body = soup.find("body")

    body_text = ""

    if body:
        body_text = body.get_text(
            " ",
            strip=True,
        )

    title = ""

    if result.metadata:
        title = result.metadata.get(
            "title",
            "",
        )

    print()
    print("=" * 70)
    print(name)
    print("=" * 70)

    print(
        "SUCCESS       :",
        result.success,
    )

    print(
        "HTML          :",
        len(html),
        "characters",
    )

    print(
        "MARKDOWN      :",
        len(markdown),
        "characters",
    )

    print(
        "BODY TEXT     :",
        len(body_text),
        "characters",
    )

    print(
        "LINKS         :",
        len(links),
    )

    print(
        "NAV ELEMENTS  :",
        len(nav_elements),
    )

    print(
        "TITLE         :",
        title,
    )

    print()
    print("FIRST 10 LINKS:")
    print("-" * 70)

    for index, link in enumerate(links[:10], 1):

        text = link.get_text(
            " ",
            strip=True,
        )

        href = link.get(
            "href",
            "",
        )

        print(
            f"{index}. {text[:60]} -> {href[:100]}"
        )

    print()
    print("CONTENT KEYWORDS:")
    print("-" * 70)

    keywords = [
        "admission",
        "academic",
        "department",
        "faculty",
        "research",
        "contact",
        "notice",
        "college",
        "student",
        "course",
    ]

    lower_text = (
        body_text.lower()
    )

    for keyword in keywords:

        count = len(
            re.findall(
                re.escape(keyword),
                lower_text,
            )
        )

        print(
            f"{keyword:<15}: {count}"
        )

    print()
    print("MARKDOWN PREVIEW:")
    print("-" * 70)

    print(
        markdown[:1000]
    )

    print("-" * 70)


async def crawl(
    crawler,
    strategy,
):
    config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        wait_until=strategy,
        page_timeout=60000,
        delay_before_return_html=1.0,
    )

    start = time.perf_counter()

    try:

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
            f"{strategy} TIME: "
            f"{elapsed:.2f}s"
        )

        return result

    except Exception as error:

        print()
        print(
            f"{strategy} FAILED:"
        )

        print(
            type(error).__name__,
            str(error),
        )

        return None


async def main():

    print()
    print("=" * 70)
    print("GWPGC CONTENT QUALITY COMPARISON")
    print("=" * 70)

    async with AsyncWebCrawler() as crawler:

        # --------------------------------------------------
        # COMMIT
        # --------------------------------------------------

        commit_result = await crawl(
            crawler,
            "commit",
        )

        if commit_result is not None:

            analyze_result(
                "COMMIT RESULT",
                commit_result,
            )

        # --------------------------------------------------
        # LOAD
        # --------------------------------------------------

        load_result = await crawl(
            crawler,
            "load",
        )

        if load_result is not None:

            analyze_result(
                "LOAD RESULT",
                load_result,
            )

    print()
    print("=" * 70)
    print("COMPARISON COMPLETE")
    print("=" * 70)


if __name__ == "__main__":

    asyncio.run(
        main()
    )