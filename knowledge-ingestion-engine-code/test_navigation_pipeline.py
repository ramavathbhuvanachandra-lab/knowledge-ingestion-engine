import asyncio

from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler

from pipeline.navigation_pipeline import NavigationPipeline


# ============================================================
# DEVELOPMENT TEST WEBSITES
# ============================================================

TEST_SITES = [
    (
        "IIT DELHI",
        "https://home.iitd.ac.in/"
    ),
    (
        "VBSPU",
        "https://www.vbspu.ac.in/en"
    ),
]


# ============================================================
# TREE NODE COUNT
# ============================================================

def count_tree_nodes(nodes):

    total = 0

    for node in nodes:

        total += 1

        if node.children:

            total += count_tree_nodes(
                node.children
            )

    return total


# ============================================================
# PRINT REMOVED CANDIDATES
# ============================================================

def print_removed_candidates(
    result
):

    removed = []

    for relationship in result["relationships"]:

        decision = relationship["decision"]

        if decision["decision"] != "redundant":
            continue

        candidate_a = relationship["a"]
        candidate_b = relationship["b"]

        analysis = relationship["analysis"]

        # Same logic used by the pipeline:
        # higher score is kept.
        # If equal, more links are kept.
        # If completely equal, first candidate is kept.

        if candidate_a.score > candidate_b.score:

            removed_candidate = candidate_b
            kept_candidate = candidate_a

        elif candidate_b.score > candidate_a.score:

            removed_candidate = candidate_a
            kept_candidate = candidate_b

        elif candidate_a.link_count > candidate_b.link_count:

            removed_candidate = candidate_b
            kept_candidate = candidate_a

        else:

            removed_candidate = candidate_b
            kept_candidate = candidate_a

        removed.append(
            (
                removed_candidate,
                kept_candidate,
                analysis,
                decision,
            )
        )

    if not removed:

        print()
        print("REMOVED CANDIDATES : NONE")
        return

    print()
    print("-" * 70)
    print("REMOVED CANDIDATES")
    print("-" * 70)

    for (
        removed_candidate,
        kept_candidate,
        analysis,
        decision,
    ) in removed:

        print(
            removed_candidate.element_name,
            "-> REMOVED"
        )

        print(
            "  Classes   :",
            removed_candidate.classes
        )

        print(
            "  Type      :",
            removed_candidate.navigation_type
        )

        print(
            "  Score     :",
            removed_candidate.score
        )

        print(
            "  Links     :",
            removed_candidate.link_count
        )

        print(
            "  Kept      :",
            kept_candidate.element_name,
            kept_candidate.classes
        )

        print(
            "  Relation  :",
            analysis["relationship"]
        )

        print(
            "  Structure :",
            analysis["structure"]
        )

        print(
            "  Reason    :",
            decision["reason"]
        )

        print()


# ============================================================
# PRINT FINAL CANDIDATES
# ============================================================

def print_final_candidates(
    result
):

    print()
    print("-" * 70)
    print("FINAL KEPT CANDIDATES")
    print("-" * 70)

    candidates = result["candidates"]

    if not candidates:

        print("NONE")
        return

    for index, candidate in enumerate(
        candidates,
        start=1
    ):

        tree_nodes = count_tree_nodes(
            candidate.tree
        )

        print(
            f"{index}. "
            f"{candidate.element_name}"
        )

        print(
            "   Classes   :",
            candidate.classes
        )

        print(
            "   Type      :",
            candidate.navigation_type
        )

        print(
            "   Score     :",
            candidate.score
        )

        print(
            "   Links     :",
            candidate.link_count
        )

        print(
            "   Tree      :",
            tree_nodes,
            "nodes"
        )


# ============================================================
# PRINT SITE RESULT
# ============================================================

def print_site_result(
    name,
    result
):

    print()
    print("=" * 70)
    print(name)
    print("=" * 70)

    print(
        "RAW CANDIDATES      :",
        result["raw_candidates"]
    )

    print(
        "FINAL CANDIDATES    :",
        result["filtered_candidates"]
    )

    print(
        "REDUNDANT REMOVED   :",
        result["redundant_candidates"]
    )

    print_removed_candidates(
        result
    )

    print_final_candidates(
        result
    )


# ============================================================
# TEST ONE WEBSITE
# ============================================================

async def test_site(
    crawler,
    name,
    url
):

    print()
    print("#" * 70)
    print("TESTING:", name)
    print(url)
    print("#" * 70)

    # --------------------------------------------------------
    # Crawl website
    # --------------------------------------------------------

    try:

        crawl_result = await crawler.arun(
            url=url
        )

    except Exception as error:

        print()
        print(
            "CRAWL ERROR:",
            type(error).__name__
        )

        print(
            "MESSAGE:",
            str(error)
        )

        return "crawl_failed"

    # --------------------------------------------------------
    # Crawl failed
    # --------------------------------------------------------

    if not crawl_result.success:

        print()
        print(
            "CRAWL FAILED"
        )

        print(
            "MESSAGE:",
            crawl_result.error_message
        )

        return "crawl_failed"

    # --------------------------------------------------------
    # Parse HTML
    # --------------------------------------------------------

    try:

        soup = BeautifulSoup(
            crawl_result.html,
            "html.parser"
        )

    except Exception as error:

        print()
        print(
            "HTML PARSE ERROR:",
            type(error).__name__
        )

        print(
            "MESSAGE:",
            str(error)
        )

        return "pipeline_failed"

    # --------------------------------------------------------
    # Run navigation pipeline
    # --------------------------------------------------------

    try:

        pipeline = NavigationPipeline(
            soup
        )

        result = pipeline.run()

    except Exception as error:

        print()
        print(
            "PIPELINE ERROR:",
            type(error).__name__
        )

        print(
            "MESSAGE:",
            str(error)
        )

        return "pipeline_failed"

    # --------------------------------------------------------
    # Print result
    # --------------------------------------------------------

    print_site_result(
        name,
        result
    )

    return "passed"


# ============================================================
# MAIN
# ============================================================

async def main():

    pipeline_passed = 0

    crawl_failed = 0

    pipeline_failed = 0

    total_sites = len(
        TEST_SITES
    )

    # --------------------------------------------------------
    # Start crawler
    # --------------------------------------------------------

    async with AsyncWebCrawler() as crawler:

        for name, url in TEST_SITES:

            status = await test_site(
                crawler,
                name,
                url
            )

            if status == "passed":

                pipeline_passed += 1

            elif status == "crawl_failed":

                crawl_failed += 1

            elif status == "pipeline_failed":

                pipeline_failed += 1

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("PIPELINE TEST SUMMARY")
    print("=" * 70)

    print(
        "TOTAL SITES     :",
        total_sites
    )

    print(
        "PIPELINE PASSED :",
        pipeline_passed
    )

    print(
        "CRAWL FAILED    :",
        crawl_failed
    )

    print(
        "PIPELINE FAILED :",
        pipeline_failed
    )

    if pipeline_failed == 0:

        print(
            "RESULT          : PASS"
        )

    else:

        print(
            "RESULT          : FAIL"
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    asyncio.run(
        main()
    )