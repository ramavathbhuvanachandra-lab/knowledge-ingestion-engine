import asyncio

from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler

from extractor.navigation_extractor import NavigationExtractor
from analyzer.navigation_classifier import NavigationClassifier
from analyzer.navigation_candidate_filter import (
    NavigationCandidateFilter
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


async def test_website(
    name,
    url,
    crawler
):

    print("\n" + "=" * 80)
    print(name)
    print(url)
    print("=" * 80)

    result = await crawler.arun(
        url=url
    )

    if not result.success:

        print("CRAWL FAILED")
        return

    soup = BeautifulSoup(
        result.html,
        "html.parser"
    )

    # ----------------------------------------------
    # Extraction
    # ----------------------------------------------

    extractor = NavigationExtractor(
        soup
    )

    candidates = extractor.discover_candidates()

    raw_count = len(candidates)

    # ----------------------------------------------
    # Classification
    # ----------------------------------------------

    classifier = NavigationClassifier()

    candidates = classifier.classify(
        candidates
    )

    # ----------------------------------------------
    # Filtering
    # ----------------------------------------------

    filter_engine = (
        NavigationCandidateFilter()
    )

    filtered = filter_engine.filter(
        candidates
    )

    filtered_count = len(filtered)

    removed_count = (
        raw_count - filtered_count
    )

    # ----------------------------------------------
    # Statistics
    # ----------------------------------------------

    print(
        "\nRAW CANDIDATES      :",
        raw_count
    )

    print(
        "FILTERED CANDIDATES :",
        filtered_count
    )

    print(
        "REMOVED             :",
        removed_count
    )

    if raw_count > 0:

        percentage = (
            removed_count
            / raw_count
            * 100
        )

        print(
            "REMOVAL RATE        :",
            f"{percentage:.1f}%"
        )

    # ----------------------------------------------
    # Kept candidates
    # ----------------------------------------------

    print(
        "\nKEPT CANDIDATES:"
    )

    for index, candidate in enumerate(
        filtered,
        start=1
    ):

        print(
            f"\n{index}. "
            f"{candidate.element_name}"
        )

        print(
            "   ID      :",
            candidate.element_id
        )

        print(
            "   Classes :",
            candidate.classes
        )

        print(
            "   Type    :",
            candidate.navigation_type
        )

        print(
            "   Score   :",
            candidate.score
        )

        print(
            "   Links   :",
            candidate.link_count
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