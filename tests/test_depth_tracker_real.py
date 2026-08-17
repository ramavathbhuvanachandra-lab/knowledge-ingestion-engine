import asyncio

from bs4 import BeautifulSoup

from crawler.crawler import crawl_page
from pipeline.navigation_pipeline import NavigationPipeline
from crawler.depth_tracker import DepthTracker


TEST_URLS = [
    "https://gwpgc.ac.in/",
    "https://www.iitj.ac.in/",
    "https://www.vbspu.ac.in/en",
    "https://home.iitd.ac.in/",
]


def flatten_nodes(nodes):
    result = []

    for node in nodes:

        result.append(node)

        if node.children:
            result.extend(
                flatten_nodes(node.children)
            )

    return result


async def test_website(url: str):

    print("\n" + "=" * 100)
    print("TESTING:", url)
    print("=" * 100)

    page = await crawl_page(url)

    assert page.success, (
        f"Failed to crawl: {url}"
    )

    assert page.html, (
        f"No HTML returned: {url}"
    )

    soup = BeautifulSoup(
        page.html,
        "html.parser",
    )

    pipeline = NavigationPipeline(
        soup=soup,
    )

    result = pipeline.run()

    candidates = result["candidates"]

    tracker = DepthTracker()

    root_url = page.url

    root_depth = tracker.register_root(
        root_url
    )

    assert root_depth == 0

    total_nodes = 0
    max_depth = 0

    # Every navigation candidate is treated
    # as being discovered from the page being
    # analyzed.
    for candidate in candidates:

        nodes = flatten_nodes(
            candidate.tree
        )

        total_nodes += len(nodes)

        for node in nodes:

            href = node.href.strip()

            if not href:
                continue

            # We intentionally do not perform URL
            # resolution here. Phase 4 already owns
            # URL discovery/resolution.
            #
            # This test verifies that the depth
            # tracker can correctly represent a
            # navigation tree once URLs are known.

            parent_url = root_url

            depth = tracker.register_child(
                href,
                parent_url,
            )

            assert depth >= 1

            max_depth = max(
                max_depth,
                depth,
            )

    print("\nRESULTS")
    print("-" * 100)
    print("Navigation candidates :", len(candidates))
    print("Navigation nodes      :", total_nodes)
    print("Tracked URLs          :", tracker.size())
    print("Maximum crawl depth   :", max_depth)

    assert tracker.get_depth(
        root_url
    ) == 0

    assert tracker.size() >= 1

    print("\nPASS:", url)


async def main():

    print("\n")
    print("=" * 100)
    print("DEPTH TRACKER — REAL WEBSITE TEST")
    print("=" * 100)

    passed = 0

    for url in TEST_URLS:

        try:

            await test_website(url)

            passed += 1

        except Exception as error:

            print("\nFAILED:", url)
            print(
                f"{type(error).__name__}: {error}"
            )

    print("\n")
    print("=" * 100)
    print(
        f"WEBSITES PASSED: "
        f"{passed} / {len(TEST_URLS)}"
    )
    print("=" * 100)

    assert passed == len(TEST_URLS), (
        "One or more real websites failed"
    )


if __name__ == "__main__":

    asyncio.run(main())