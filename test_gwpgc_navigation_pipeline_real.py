import asyncio

from bs4 import BeautifulSoup

from crawler.crawler import crawl_page
from pipeline.navigation_pipeline import NavigationPipeline


URL = "https://gwpgc.ac.in/"


async def main():

    print()
    print("=" * 70)
    print("GWPGC — REAL NAVIGATION PIPELINE TEST")
    print("=" * 70)

    # --------------------------------------------------
    # 1. CRAWL
    # --------------------------------------------------

    page = await crawl_page(URL)

    print()
    print("CRAWL")
    print("-" * 70)

    print("SUCCESS :", page.success)
    print("TITLE   :", page.title)
    print("HTML    :", len(page.html or ""))
    print("MARKDOWN:", len(page.markdown or ""))

    if not page.success:
        print()
        print("RESULT : CRAWL FAILED")
        return

    # --------------------------------------------------
    # 2. PARSE HTML
    # --------------------------------------------------

    soup = BeautifulSoup(
        page.html,
        "html.parser",
    )

    # --------------------------------------------------
    # 3. RUN ACTUAL NAVIGATION PIPELINE
    # --------------------------------------------------

    pipeline = NavigationPipeline(
        soup
    )

    result = pipeline.run()

    # --------------------------------------------------
    # 4. PIPELINE SUMMARY
    # --------------------------------------------------

    print()
    print("=" * 70)
    print("PIPELINE RESULT")
    print("=" * 70)

    print(
        "Raw candidates      :",
        result["raw_candidates"],
    )

    print(
        "Final candidates    :",
        result["filtered_candidates"],
    )

    print(
        "Redundant candidates:",
        result["redundant_candidates"],
    )

    # --------------------------------------------------
    # 5. FINAL CANDIDATES
    # --------------------------------------------------

    candidates = result[
        "candidates"
    ]

    print()
    print("=" * 70)
    print("FINAL NAVIGATION CANDIDATES")
    print("=" * 70)

    for index, candidate in enumerate(
        candidates,
        start=1,
    ):

        print()
        print(
            f"Candidate {index}"
        )

        print(
            "Element :",
            candidate.element_name,
        )

        print(
            "ID      :",
            candidate.element_id,
        )

        print(
            "Classes :",
            candidate.classes,
        )

        print(
            "Type    :",
            candidate.navigation_type,
        )

        print(
            "Score   :",
            candidate.score,
        )

        print(
            "Links   :",
            candidate.link_count,
        )

        print(
            "Tree    :",
            "BUILT"
            if getattr(
                candidate,
                "tree",
                None,
            )
            is not None
            else "MISSING",
        )

        print(
            "Sample  :",
            candidate.links[:10],
        )

    # --------------------------------------------------
    # 6. RELATIONSHIP SUMMARY
    # --------------------------------------------------

    relationships = result[
        "relationships"
    ]

    print()
    print("=" * 70)
    print("RELATIONSHIP SUMMARY")
    print("=" * 70)

    relationship_counts = {}

    decision_counts = {}

    for relationship in relationships:

        analysis = relationship[
            "analysis"
        ]

        decision = relationship[
            "decision"
        ]

        relationship_name = analysis[
            "relationship"
        ]

        decision_name = decision[
            "decision"
        ]

        relationship_counts[
            relationship_name
        ] = (
            relationship_counts.get(
                relationship_name,
                0,
            )
            + 1
        )

        decision_counts[
            decision_name
        ] = (
            decision_counts.get(
                decision_name,
                0,
            )
            + 1
        )

    print(
        "Relationships:"
    )

    for name, count in sorted(
        relationship_counts.items()
    ):

        print(
            f"  {name:22} : {count}"
        )

    print()
    print(
        "Decisions:"
    )

    for name, count in sorted(
        decision_counts.items()
    ):

        print(
            f"  {name:22} : {count}"
        )

    # --------------------------------------------------
    # 7. TREE VALIDATION
    # --------------------------------------------------

    trees_built = 0
    trees_missing = 0

    for candidate in candidates:

        tree = getattr(
            candidate,
            "tree",
            None,
        )

        if tree is None:
            trees_missing += 1
        else:
            trees_built += 1

    print()
    print("=" * 70)
    print("TREE VALIDATION")
    print("=" * 70)

    print(
        "Trees built   :",
        trees_built,
    )

    print(
        "Trees missing :",
        trees_missing,
    )

    # --------------------------------------------------
    # 8. FINAL RESULT
    # --------------------------------------------------

    print()
    print("=" * 70)
    print("FINAL RESULT")
    print("=" * 70)

    if (
        page.success
        and len(candidates) > 0
        and trees_missing == 0
    ):

        print(
            "RESULT : PASS"
        )

    else:

        print(
            "RESULT : FAIL"
        )


if __name__ == "__main__":

    asyncio.run(
        main()
    )
