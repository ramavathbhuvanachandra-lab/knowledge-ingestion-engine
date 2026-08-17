import asyncio

from bs4 import BeautifulSoup

from crawler.crawler import crawl_page
from extractor.navigation_extractor import NavigationExtractor
from analyzer.navigation_classifier import NavigationClassifier


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

        extractor = NavigationExtractor(soup)

        candidates = extractor.discover_candidates()

        classifier = NavigationClassifier()

        candidates = classifier.classify(
            candidates
        )

        print(
            "\nTOTAL CANDIDATES:",
            len(candidates)
        )

        print("\nCLASSIFIED CANDIDATES")
        print("-" * 90)

        for index, candidate in enumerate(
            candidates,
            start=1
        ):

            print(
                f"\nCANDIDATE {index}"
            )

            print(
                "Element :",
                candidate.element_name
            )

            print(
                "ID      :",
                candidate.element_id
            )

            print(
                "Classes :",
                candidate.classes
            )

            print(
                "ARIA    :",
                candidate.aria_label
            )

            print(
                "Links   :",
                candidate.link_count
            )

            print(
                "Type    :",
                candidate.navigation_type
            )

            print(
                "Score   :",
                candidate.score
            )

            print(
                "Preview :",
                candidate.links[:8]
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