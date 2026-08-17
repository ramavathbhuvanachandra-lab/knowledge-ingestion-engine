import asyncio

from bs4 import BeautifulSoup

from crawler.crawler import crawl_page
from extractor.navigation_extractor import NavigationExtractor
from analyzer.navigation_structure import (
    NavigationStructureAnalyzer
)


TEST_URLS = [
    "https://www.iitb.ac.in",
    "https://www.iitm.ac.in",
    "https://www.iitd.ac.in",
    "https://www.iith.ac.in",
    "https://www.isro.gov.in",
    "https://www.india.gov.in",
    "https://docs.langchain.com",
    "https://supabase.com/docs",
    "https://gwpgc.ac.in/",
]


def find_candidate_element(
    soup,
    candidate
):

    for element in soup.find_all(
        candidate.element_name
    ):

        if (
            element.get("id", "")
            != candidate.element_id
        ):
            continue

        if (
            element.get("class", [])
            != candidate.classes
        ):
            continue

        links = []

        for link in element.find_all("a"):

            text = link.get_text(
                " ",
                strip=True
            )

            if not text:
                continue

            if text in links:
                continue

            links.append(text)

        if links == candidate.links:
            return element

    return None


async def inspect_url(url):

    print("\n" + "=" * 90)
    print("URL:", url)
    print("=" * 90)

    try:

        page = await crawl_page(url)

        soup = BeautifulSoup(
            page.html,
            "html.parser"
        )

        extractor = NavigationExtractor(
            soup
        )

        candidates = extractor.discover_candidates()

        analyzer = NavigationStructureAnalyzer()

        print(
            "\nTOTAL CANDIDATES:",
            len(candidates)
        )

        # Resolve HTML elements
        resolved = []

        for candidate in candidates:

            element = find_candidate_element(
                soup,
                candidate
            )

            if element is not None:
                resolved.append(
                    (candidate, element)
                )

        print(
            "RESOLVED CANDIDATES:",
            len(resolved)
        )

        if len(resolved) < 2:
            print(
                "\nNot enough candidates "
                "for relationship analysis."
            )
            return

        print("\nRELATIONSHIPS")
        print("-" * 90)

        # Compare every candidate pair
        for i in range(
            len(resolved)
        ):

            candidate_a, element_a = (
                resolved[i]
            )

            for j in range(
                i + 1,
                len(resolved)
            ):

                candidate_b, element_b = (
                    resolved[j]
                )

                relationship = (
                    analyzer.get_relationship(
                        element_a,
                        element_b
                    )
                )

                # Only show structural relationships
                # that are useful for hierarchy.
                if relationship in {
                    "direct_parent",
                    "direct_child",
                    "ancestor",
                    "descendant"
                }:

                    print(
                        f"\nCandidate {i + 1}"
                    )

                    print(
                        "  Element:",
                        candidate_a.element_name
                    )

                    print(
                        "  ID:",
                        candidate_a.element_id
                    )

                    print(
                        "  Links:",
                        candidate_a.link_count
                    )

                    print(
                        f"  {relationship.upper()}"
                    )

                    print(
                        f"Candidate {j + 1}"
                    )

                    print(
                        "  Element:",
                        candidate_b.element_name
                    )

                    print(
                        "  ID:",
                        candidate_b.element_id
                    )

                    print(
                        "  Links:",
                        candidate_b.link_count
                    )

    except Exception as e:

        print(
            "\nFAILED:",
            type(e).__name__,
            e
        )


async def main():

    for url in TEST_URLS:

        await inspect_url(url)


if __name__ == "__main__":

    asyncio.run(main())
