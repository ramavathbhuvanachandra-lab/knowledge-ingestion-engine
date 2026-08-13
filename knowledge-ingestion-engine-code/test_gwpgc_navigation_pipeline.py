import asyncio

from bs4 import BeautifulSoup

from crawler.crawler import crawl_page
from extractor.navigation_extractor import NavigationExtractor
from analyzer.navigation_candidate_filter import NavigationCandidateFilter


URL = "https://gwpgc.ac.in/"


def print_candidate(
    index,
    candidate,
):
    print()
    print(
        f"Candidate {index}"
    )

    print(
        "  Element :",
        candidate.element_name,
    )

    print(
        "  ID      :",
        candidate.element_id,
    )

    print(
        "  Classes :",
        candidate.classes,
    )

    print(
        "  Type    :",
        candidate.navigation_type,
    )

    print(
        "  Score   :",
        candidate.score,
    )

    print(
        "  Links   :",
        candidate.link_count,
    )

    print(
        "  Sample  :",
        candidate.links[:10],
    )


async def main():

    print()
    print("=" * 70)
    print("GWPGC — REAL NAVIGATION PIPELINE")
    print("=" * 70)

    print()
    print("URL :", URL)

    # --------------------------------------------------------
    # CRAWL
    # --------------------------------------------------------

    page = await crawl_page(
        URL
    )

    print()
    print("=" * 70)
    print("CRAWL RESULT")
    print("=" * 70)

    print(
        "SUCCESS :",
        page.success,
    )

    print(
        "TITLE   :",
        page.title,
    )

    print(
        "HTML    :",
        len(page.html or ""),
    )

    print(
        "MARKDOWN:",
        len(page.markdown or ""),
    )

    if not page.success:

        print()
        print(
            "RESULT : CRAWL FAILED"
        )

        return

    # --------------------------------------------------------
    # PARSE HTML
    # --------------------------------------------------------

    soup = BeautifulSoup(
        page.html,
        "html.parser",
    )

    # --------------------------------------------------------
    # DISCOVER NAVIGATION
    # --------------------------------------------------------

    extractor = NavigationExtractor(
        soup
    )

    raw_candidates = (
        extractor.discover_candidates()
    )

    print()
    print("=" * 70)
    print("RAW NAVIGATION CANDIDATES")
    print("=" * 70)

    print(
        "COUNT :",
        len(raw_candidates),
    )

    for index, candidate in enumerate(
        raw_candidates,
        1,
    ):

        print_candidate(
            index,
            candidate,
        )

    # --------------------------------------------------------
    # FILTER
    # --------------------------------------------------------

    candidate_filter = (
        NavigationCandidateFilter()
    )

    final_candidates = (
        candidate_filter.filter(
            raw_candidates
        )
    )

    print()
    print("=" * 70)
    print("FILTERED NAVIGATION CANDIDATES")
    print("=" * 70)

    print(
        "COUNT :",
        len(final_candidates),
    )

    for index, candidate in enumerate(
        final_candidates,
        1,
    ):

        print_candidate(
            index,
            candidate,
        )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    print(
        "Raw candidates    :",
        len(raw_candidates),
    )

    print(
        "After filtering   :",
        len(final_candidates),
    )

    print(
        "Removed by filter :",
        len(raw_candidates)
        - len(final_candidates),
    )

    if final_candidates:

        print()
        print(
            "RESULT : NAVIGATION DISCOVERED"
        )

    else:

        print()
        print(
            "RESULT : NO NAVIGATION FOUND"
        )


if __name__ == "__main__":

    asyncio.run(
        main()
    )