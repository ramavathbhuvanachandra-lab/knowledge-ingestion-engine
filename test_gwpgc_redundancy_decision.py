import asyncio

from bs4 import BeautifulSoup

from crawler.crawler import crawl_page
from extractor.navigation_extractor import NavigationExtractor
from analyzer.navigation_candidate_filter import NavigationCandidateFilter
from analyzer.navigation_redundancy import NavigationRedundancyAnalyzer
from analyzer.navigation_redundancy_decision import NavigationRedundancyDecision


URL = "https://gwpgc.ac.in/"


def find_element_for_candidate(
    soup,
    candidate,
):
    elements = soup.find_all(
        candidate.element_name
    )

    for element in elements:

        element_id = (
            element.get("id", "")
        )

        classes = element.get(
            "class",
            [],
        )

        if element_id != candidate.element_id:
            continue

        if set(classes) != set(
            candidate.classes
        ):
            continue

        return element

    return None


async def main():

    print()
    print("=" * 70)
    print("GWPGC — DOM-AWARE REDUNDANCY DECISION")
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
    # 2. PARSE
    # --------------------------------------------------

    soup = BeautifulSoup(
        page.html,
        "html.parser",
    )

    # --------------------------------------------------
    # 3. EXTRACT
    # --------------------------------------------------

    extractor = NavigationExtractor(
        soup
    )

    raw_candidates = (
        extractor.discover_candidates()
    )

    # --------------------------------------------------
    # 4. FILTER
    # --------------------------------------------------

    candidate_filter = (
        NavigationCandidateFilter()
    )

    candidates = (
        candidate_filter.filter(
            raw_candidates
        )
    )

    print()
    print("CANDIDATES")
    print("-" * 70)

    print(
        "Raw candidates     :",
        len(raw_candidates),
    )

    print(
        "Filtered candidates:",
        len(candidates),
    )

    # --------------------------------------------------
    # 5. RESOLVE DOM ELEMENTS
    # --------------------------------------------------

    resolved = []

    print()
    print("DOM RESOLUTION")
    print("-" * 70)

    for candidate in candidates:

        element = find_element_for_candidate(
            soup,
            candidate,
        )

        if element is None:

            print(
                "FAILED :",
                candidate.element_name,
                candidate.element_id,
                candidate.classes,
            )

            continue

        resolved.append(
            (
                candidate,
                element,
            )
        )

        print(
            "OK     :",
            candidate.element_name,
            candidate.element_id,
            candidate.classes,
        )

    print()
    print(
        "Resolved elements:",
        len(resolved),
    )

    # --------------------------------------------------
    # 6. ANALYZERS
    # --------------------------------------------------

    redundancy_analyzer = (
        NavigationRedundancyAnalyzer()
    )

    decision_engine = (
        NavigationRedundancyDecision()
    )

    # --------------------------------------------------
    # 7. COMPARE PAIRS
    # --------------------------------------------------

    total_pairs = 0
    redundant_pairs = 0
    keep_pairs = 0

    structure_counts = {}

    print()
    print("=" * 70)
    print("DOM-AWARE REDUNDANCY DECISIONS")
    print("=" * 70)

    for i in range(
        len(resolved)
    ):

        for j in range(
            i + 1,
            len(resolved),
        ):

            candidate_a, element_a = (
                resolved[i]
            )

            candidate_b, element_b = (
                resolved[j]
            )

            total_pairs += 1

            result = (
                redundancy_analyzer.analyze(
                    candidate_a,
                    candidate_b,
                    element_a,
                    element_b,
                )
            )

            decision = (
                decision_engine.decide(
                    result,
                    candidate_a,
                    candidate_b,
                )
            )

            structure = result[
                "structure"
            ]

            structure_counts[
                structure
            ] = (
                structure_counts.get(
                    structure,
                    0,
                )
                + 1
            )

            if (
                decision["decision"]
                == "redundant"
            ):

                redundant_pairs += 1

            else:

                keep_pairs += 1

            print()
            print(
                f"PAIR {total_pairs}"
            )

            print(
                "A:",
                candidate_a.element_name,
                candidate_a.element_id,
                candidate_a.classes,
                f"({candidate_a.link_count} links)",
            )

            print(
                "B:",
                candidate_b.element_name,
                candidate_b.element_id,
                candidate_b.classes,
                f"({candidate_b.link_count} links)",
            )

            print(
                "Relationship :",
                result["relationship"],
            )

            print(
                "Structure    :",
                result["structure"],
            )

            print(
                "Containment  :",
                result["containment"],
            )

            print(
                "Coverage     :",
                result["coverage"],
            )

            print(
                "Decision     :",
                decision["decision"],
            )

            print(
                "Reason       :",
                decision["reason"],
            )

            print(
                "Confidence   :",
                decision["confidence"],
            )

    # --------------------------------------------------
    # 8. SUMMARY
    # --------------------------------------------------

    print()
    print("=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)

    print(
        "Raw candidates      :",
        len(raw_candidates),
    )

    print(
        "Filtered candidates :",
        len(candidates),
    )

    print(
        "Resolved elements   :",
        len(resolved),
    )

    print(
        "Total pairs         :",
        total_pairs,
    )

    print(
        "Redundant decisions :",
        redundant_pairs,
    )

    print(
        "Keep decisions      :",
        keep_pairs,
    )

    print()
    print(
        "STRUCTURE COUNTS"
    )

    for structure, count in sorted(
        structure_counts.items()
    ):

        print(
            f"{structure:16} : {count}"
        )

    print()
    print(
        "RESULT : DOM-AWARE DECISION TEST COMPLETE"
    )


if __name__ == "__main__":

    asyncio.run(
        main()
    )
