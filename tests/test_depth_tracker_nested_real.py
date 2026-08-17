import asyncio
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from crawler.crawler import crawl_page
from crawler.depth_tracker import DepthTracker
from crawler.url_normalizer import normalize_url
from crawler.url_validator import is_valid_url
from pipeline.navigation_pipeline import NavigationPipeline


TEST_URLS = [
    "https://gwpgc.ac.in/",
    "https://www.iitj.ac.in/",
    "https://www.vbspu.ac.in/en",
    "https://home.iitd.ac.in/",
]


def walk_tree(
    nodes,
    parent_url,
    parent_depth,
    tracker,
):
    """
    Recursively walk the real navigation tree.

    Important rule:

    A non-crawlable navigation trigger such as
    javascript:void(0) does NOT create a crawl depth.

    Its children remain children of the last valid
    crawlable URL.
    """

    for node in nodes:

        raw_href = (
            node.href.strip()
            if node.href
            else ""
        )

        # --------------------------------------------------
        # NON-CRAWLABLE / EMPTY NAVIGATION NODE
        # --------------------------------------------------

        if not raw_href:

            yield from walk_tree(
                node.children,
                parent_url,
                parent_depth,
                tracker,
            )

            continue

        resolved_url = urljoin(
            parent_url,
            raw_href,
        )

        normalized_url = normalize_url(
            resolved_url
        )

        # --------------------------------------------------
        # INVALID / PSEUDO URL
        # --------------------------------------------------

        if not is_valid_url(
            normalized_url
        ):

            # IMPORTANT:
            #
            # The node itself is not crawlable,
            # but its children may contain real URLs.
            #
            # Therefore we DO NOT stop traversal.
            # We simply keep the same crawl parent.

            yield from walk_tree(
                node.children,
                parent_url,
                parent_depth,
                tracker,
            )

            continue

        # --------------------------------------------------
        # VALID URL
        # --------------------------------------------------

        already_known = tracker.contains(
            normalized_url
        )

        expected_depth = (
            parent_depth + 1
        )

        actual_depth = tracker.register_child(
            normalized_url,
            parent_url,
        )

        # First discovery establishes the depth.
        if not already_known:

            assert actual_depth == expected_depth, (
                f"Invalid first-discovery depth for "
                f"{normalized_url}: "
                f"expected {expected_depth}, "
                f"got {actual_depth}"
            )

        else:

            # Existing URL keeps its original depth.
            assert actual_depth >= 0

        yield (
            normalized_url,
            actual_depth,
            already_known,
        )

        # --------------------------------------------------
        # CHILDREN
        # --------------------------------------------------

        yield from walk_tree(
            node.children,
            normalized_url,
            actual_depth,
            tracker,
        )


async def test_website(url):

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

    root_url = normalize_url(
        page.url
    )

    assert tracker.register_root(
        root_url
    ) == 0

    observed_nodes = 0
    unique_urls = 0
    duplicate_urls = 0
    maximum_depth = 0

    depth_counts = {}

    for candidate in candidates:

        for (
            normalized_url,
            depth,
            was_duplicate,
        ) in walk_tree(
            candidate.tree,
            root_url,
            0,
            tracker,
        ):

            observed_nodes += 1

            maximum_depth = max(
                maximum_depth,
                depth,
            )

            depth_counts[depth] = (
                depth_counts.get(depth, 0) + 1
            )

            if was_duplicate:

                duplicate_urls += 1

            else:

                unique_urls += 1

    print("\nRESULTS")
    print("-" * 100)

    print(
        "Navigation candidates :",
        len(candidates),
    )

    print(
        "Navigation occurrences:",
        observed_nodes,
    )

    print(
        "Unique URLs           :",
        unique_urls,
    )

    print(
        "Duplicate discoveries :",
        duplicate_urls,
    )

    print(
        "Tracked URLs          :",
        tracker.size(),
    )

    print(
        "Maximum crawl depth   :",
        maximum_depth,
    )

    print(
        "Depth distribution    :",
        dict(sorted(depth_counts.items())),
    )

    assert tracker.get_depth(
        root_url
    ) == 0

    assert observed_nodes > 0

    assert tracker.size() >= 1

    print(
        "\nPASS:",
        url,
    )

    return {
        "maximum_depth": maximum_depth,
        "observed_nodes": observed_nodes,
        "unique_urls": unique_urls,
        "duplicate_urls": duplicate_urls,
        "depth_counts": depth_counts,
    }


async def main():

    print("\n")
    print("=" * 100)
    print(
        "DEPTH TRACKER — NESTED REAL WEBSITE TEST"
    )
    print("=" * 100)

    passed = 0
    results = {}

    for url in TEST_URLS:

        try:

            results[url] = await test_website(
                url
            )

            passed += 1

        except Exception as error:

            print("\nFAILED:", url)

            print(
                f"{type(error).__name__}: "
                f"{error}"
            )

    print("\n")
    print("=" * 100)

    print(
        f"WEBSITES PASSED: "
        f"{passed} / {len(TEST_URLS)}"
    )

    print("=" * 100)

    for url, result in results.items():

        print(
            f"\n{url}"
        )

        print(
            "  max depth:",
            result["maximum_depth"],
        )

        print(
            "  unique:",
            result["unique_urls"],
        )

        print(
            "  duplicates:",
            result["duplicate_urls"],
        )

        print(
            "  depth distribution:",
            dict(
                sorted(
                    result["depth_counts"].items()
                )
            ),
        )

    assert passed == len(TEST_URLS), (
        "One or more real websites failed"
    )


if __name__ == "__main__":

    asyncio.run(main())