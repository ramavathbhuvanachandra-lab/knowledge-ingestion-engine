import asyncio
from collections import Counter

from crawler.crawler import crawl_page
from pipeline.navigation_pipeline import NavigationPipeline
from url_discovery import URLDiscovery


TEST_URLS = [
    "https://gwpgc.ac.in/",
    "https://www.iitj.ac.in/",
    "https://www.vbspu.ac.in/en",
]


async def test_website(url: str):

    print("\n" + "=" * 100)
    print(f"TESTING WEBSITE: {url}")
    print("=" * 100)

    # ---------------------------------------------------------
    # 1. Crawl page
    # ---------------------------------------------------------

    page = await crawl_page(url)

    print("\nPAGE RESULT")
    print("-" * 100)
    print("Final URL :", page.url)
    print("Success   :", page.success)
    print("Title     :", page.title)
    print("HTML Size :", len(page.html or ""))

    assert page.success, f"Failed to crawl {url}"
    assert page.html, f"No HTML returned for {url}"

    # ---------------------------------------------------------
    # 2. Run Phase 3 navigation pipeline
    # ---------------------------------------------------------

    navigation_pipeline = NavigationPipeline(
        soup=_build_soup(page.html)
    )

    navigation_result = navigation_pipeline.run()

    candidates = navigation_result["candidates"]

    print("\nNAVIGATION PIPELINE")
    print("-" * 100)
    print(
        "Raw candidates      :",
        navigation_result["raw_candidates"],
    )
    print(
        "Filtered candidates :",
        navigation_result["filtered_candidates"],
    )
    print(
        "Redundant candidates:",
        navigation_result["redundant_candidates"],
    )

    # ---------------------------------------------------------
    # 3. Count navigation nodes
    # ---------------------------------------------------------

    navigation_nodes = []

    for candidate in candidates:

        navigation_nodes.extend(
            _flatten_nodes(candidate.tree)
        )

    print(
        "Navigation nodes    :",
        len(navigation_nodes),
    )

    # ---------------------------------------------------------
    # 4. Phase 4 URL discovery
    # ---------------------------------------------------------

    discovery = URLDiscovery()

    results = discovery.discover(
        candidates=candidates,
        source_url=page.url,
    )

    print("\nURL DISCOVERY")
    print("-" * 100)
    print(
        "URLs discovered     :",
        len(results),
    )

    # ---------------------------------------------------------
    # 5. Classification statistics
    # ---------------------------------------------------------

    type_counts = Counter(
        result.url_type.value
        for result in results
    )

    print("\nURL TYPES")
    print("-" * 100)

    for url_type, count in sorted(
        type_counts.items()
    ):
        print(
            f"{url_type:<15}: {count}"
        )

    # ---------------------------------------------------------
    # 6. Universal invariants
    # ---------------------------------------------------------

    normalized_urls = [
        result.normalized_url
        for result in results
    ]

    # Every discovered URL must be unique.
    assert len(normalized_urls) == len(
        set(normalized_urls)
    ), "Duplicate normalized URLs discovered"

    # Every URL must have a source.
    assert all(
        result.discovered_from
        for result in results
    ), "URL without discovered_from"

    # Every URL must have a normalized value.
    assert all(
        result.normalized_url
        for result in results
    ), "URL without normalized_url"

    # Crawl depth is not assigned during Phase 4.
    assert all(
        result.depth == 0
        for result in results
    ), "Phase 4 unexpectedly assigned crawl depth"

    # ---------------------------------------------------------
    # 7. Print sample URLs
    # ---------------------------------------------------------

    print("\nSAMPLE DISCOVERED URLS")
    print("-" * 100)

    for result in results[:30]:

        print(
            f"[{result.url_type.value:<8}] "
            f"{result.normalized_url}"
        )

    print("\n" + "-" * 100)
    print(f"PASS: {url}")
    print("-" * 100)

    return {
        "url": url,
        "final_url": page.url,
        "navigation_candidates": len(candidates),
        "navigation_nodes": len(navigation_nodes),
        "discovered_urls": len(results),
        "url_types": dict(type_counts),
    }


def _build_soup(html: str):

    from bs4 import BeautifulSoup

    return BeautifulSoup(
        html,
        "html.parser",
    )


def _flatten_nodes(nodes):

    result = []

    for node in nodes:

        result.append(node)

        if node.children:

            result.extend(
                _flatten_nodes(
                    node.children
                )
            )

    return result


async def main():

    print("\n")
    print("=" * 100)
    print("PHASE 4 — REAL WEBSITE URL DISCOVERY TEST")
    print("=" * 100)

    results = []

    for url in TEST_URLS:

        try:

            result = await test_website(url)

            results.append(result)

        except Exception as error:

            print("\n" + "!" * 100)
            print(f"FAILED: {url}")
            print("!" * 100)
            print(
                f"{type(error).__name__}: {error}"
            )

    # ---------------------------------------------------------
    # Final summary
    # ---------------------------------------------------------

    print("\n")
    print("=" * 100)
    print("REAL WEBSITE TEST SUMMARY")
    print("=" * 100)

    for result in results:

        print(
            f"\n{result['url']}"
        )

        print(
            "  Final URL            :",
            result["final_url"],
        )

        print(
            "  Navigation candidates:",
            result["navigation_candidates"],
        )

        print(
            "  Navigation nodes     :",
            result["navigation_nodes"],
        )

        print(
            "  URLs discovered      :",
            result["discovered_urls"],
        )

        print(
            "  URL types            :",
            result["url_types"],
        )

    print("\n")
    print("=" * 100)
    print(
        f"WEBSITES PASSED: {len(results)} / {len(TEST_URLS)}"
    )
    print("=" * 100)


if __name__ == "__main__":

    asyncio.run(main())