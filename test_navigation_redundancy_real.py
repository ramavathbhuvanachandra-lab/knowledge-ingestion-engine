import asyncio
from collections import Counter

from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler

from extractor.navigation_extractor import NavigationExtractor
from analyzer.navigation_classifier import NavigationClassifier
from analyzer.navigation_candidate_filter import (
    NavigationCandidateFilter
)
from analyzer.navigation_redundancy import (
    NavigationRedundancyAnalyzer
)


WEBSITES = [
    ("IIT Bombay", "https://www.iitb.ac.in"),
    ("IIT Madras", "https://www.iitm.ac.in"),
    ("IIT Delhi", "https://www.iitd.ac.in"),
    ("IIT Hyderabad", "https://www.iith.ac.in"),
    ("ISRO", "https://www.isro.gov.in"),
    ("India.gov.in", "https://www.india.gov.in"),
    ("LangChain", "https://docs.langchain.com"),
    ("Supabase", "https://supabase.com/docs"),
    ("GWPGC", "https://gwpgc.ac.in/"),
]


def get_candidate_element(
    soup,
    candidate
):
    """
    Try to resolve the original DOM element
    represented by a navigation candidate.
    """

    for element in soup.find_all(True):

        element_id = element.get(
            "id",
            ""
        )

        classes = element.get(
            "class",
            []
        )

        aria_label = element.get(
            "aria-label",
            ""
        )

        # --------------------------------------------------
        # Basic metadata match
        # --------------------------------------------------

        if element.name != candidate.element_name:
            continue

        if element_id != candidate.element_id:
            continue

        if classes != candidate.classes:
            continue

        if aria_label != candidate.aria_label:
            continue

        # --------------------------------------------------
        # Link text match
        # --------------------------------------------------

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


async def test_website(
    name,
    url,
    crawler
):

    print("\n")
    print("=" * 80)
    print(name)
    print(url)
    print("=" * 80)

    # ------------------------------------------------------
    # Crawl
    # ------------------------------------------------------

    result = await crawler.arun(
        url=url
    )

    if not result.success:

        print("CRAWL FAILED")
        print(
            "ERROR:",
            result.error_message
        )

        return

    soup = BeautifulSoup(
        result.html,
        "html.parser"
    )

    # ------------------------------------------------------
    # Extraction
    # ------------------------------------------------------

    extractor = NavigationExtractor(
        soup
    )

    candidates = extractor.discover_candidates()

    raw_count = len(candidates)

    # ------------------------------------------------------
    # Classification
    # ------------------------------------------------------

    classifier = NavigationClassifier()

    candidates = classifier.classify(
        candidates
    )

    # ------------------------------------------------------
    # Filtering
    # ------------------------------------------------------

    filter_engine = NavigationCandidateFilter()

    candidates = filter_engine.filter(
        candidates
    )

    filtered_count = len(candidates)

    print(
        "\nRAW CANDIDATES      :",
        raw_count
    )

    print(
        "FILTERED CANDIDATES :",
        filtered_count
    )

    # ------------------------------------------------------
    # Resolve DOM elements
    # ------------------------------------------------------

    resolved_elements = []

    for candidate in candidates:

        element = get_candidate_element(
            soup,
            candidate
        )

        resolved_elements.append(
            element
        )

    resolved_count = sum(
        element is not None
        for element in resolved_elements
    )

    print(
        "RESOLVED ELEMENTS   :",
        resolved_count
    )

    # ------------------------------------------------------
    # Redundancy analysis
    # ------------------------------------------------------

    analyzer = NavigationRedundancyAnalyzer()

    relationships = Counter()

    redundant_count = 0

    pair_count = 0

    examples = []

    for i in range(
        len(candidates)
    ):

        for j in range(
            i + 1,
            len(candidates)
        ):

            candidate_a = candidates[i]
            candidate_b = candidates[j]

            element_a = resolved_elements[i]
            element_b = resolved_elements[j]

            result = analyzer.analyze(
                candidate_a,
                candidate_b,
                element_a,
                element_b
            )

            relationship = (
                result["relationship"]
            )

            relationships[
                relationship
            ] += 1

            pair_count += 1

            if result["redundant"]:

                redundant_count += 1

                # Keep only a few examples
                # for inspection.

                if len(examples) < 10:

                    examples.append(
                        (
                            i,
                            j,
                            candidate_a,
                            candidate_b,
                            result
                        )
                    )

    # ------------------------------------------------------
    # Summary
    # ------------------------------------------------------

    print(
        "\nTOTAL PAIRS        :",
        pair_count
    )

    print(
        "REDUNDANT PAIRS    :",
        redundant_count
    )

    print(
        "\nRELATIONSHIP COUNTS:"
    )

    for relationship, count in (
        relationships.most_common()
    ):

        print(
            f"  {relationship:22} : {count}"
        )

    # ------------------------------------------------------
    # Redundant examples
    # ------------------------------------------------------

    print(
        "\nREDUNDANT EXAMPLES:"
    )

    if not examples:

        print(
            "  None detected."
        )

    else:

        for (
            index_a,
            index_b,
            candidate_a,
            candidate_b,
            result
        ) in examples:

            print("\n" + "-" * 70)

            print(
                f"Candidate A : {index_a}"
            )

            print(
                "  Element    :",
                candidate_a.element_name
            )

            print(
                "  ID         :",
                candidate_a.element_id
            )

            print(
                "  Classes    :",
                candidate_a.classes
            )

            print(
                "  Links      :",
                candidate_a.link_count
            )

            print(
                f"Candidate B : {index_b}"
            )

            print(
                "  Element    :",
                candidate_b.element_name
            )

            print(
                "  ID         :",
                candidate_b.element_id
            )

            print(
                "  Classes    :",
                candidate_b.classes
            )

            print(
                "  Links      :",
                candidate_b.link_count
            )

            print(
                "\n  Relationship:",
                result["relationship"]
            )

            print(
                "  Containment :",
                result["containment"]
            )

            print(
                "  Coverage    :",
                result["coverage"]
            )

            print(
                "  Structure   :",
                result["structure"]
            )

            print(
                "  Redundant   :",
                result["redundant"]
            )


async def main():

    async with AsyncWebCrawler() as crawler:

        for name, url in WEBSITES:

            try:

                await test_website(
                    name,
                    url,
                    crawler
                )

            except Exception as error:

                print(
                    "\nERROR:",
                    type(error).__name__,
                    str(error)
                )


if __name__ == "__main__":

    asyncio.run(
        main()
    )