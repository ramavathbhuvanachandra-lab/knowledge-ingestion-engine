import asyncio

from bs4 import BeautifulSoup

from crawler.crawler import crawl_page
from extractor.navigation_extractor import NavigationExtractor
from analyzer.navigation_relationship import (
    determine_relationship,
)


TEST_SITES = [
    (
        "IIT Bombay",
        "https://www.iitb.ac.in"
    ),
    (
        "IIT Delhi",
        "https://home.iitd.ac.in"
    ),
    (
        "IIT Madras",
        "https://www.iitm.ac.in"
    ),
    (
        "IIT Hyderabad",
        "https://www.iith.ac.in"
    ),
    (
        "ISRO",
        "https://www.isro.gov.in"
    ),
    (
        "India Government",
        "https://www.india.gov.in"
    ),
    (
        "LangChain",
        "https://docs.langchain.com"
    ),
    (
        "Supabase",
        "https://supabase.com/docs"
    ),
    (
        "GWPGC",
        "https://gwpgc.ac.in/"
    ),
]


async def test_site(name, url):

    print("\n" + "=" * 90)
    print(name)
    print(url)
    print("=" * 90)

    try:

        page = await crawl_page(url)

        if page is None:
            print("FAILED: crawler returned None")
            return

        soup = BeautifulSoup(
            page.html,
            "html.parser"
        )

        extractor = NavigationExtractor(
            soup
        )

        candidates = (
            extractor.discover_candidates()
        )

        print(
            "\nCANDIDATE COUNT:",
            len(candidates)
        )

        if len(candidates) < 2:

            print(
                "Not enough candidates for relationship testing."
            )

            return

        for i in range(
            len(candidates)
        ):

            for j in range(
                i + 1,
                len(candidates)
            ):

                candidate_a = candidates[i]
                candidate_b = candidates[j]

                relationship = (
                    determine_relationship(
                        candidate_a.links,
                        candidate_b.links
                    )
                )

                if relationship == "unrelated":
                    continue

                print("\n" + "-" * 80)

                print(
                    f"CANDIDATE {i + 1} ↔ "
                    f"CANDIDATE {j + 1}"
                )

                print(
                    "A:",
                    candidate_a.element_name,
                    candidate_a.element_id,
                    f"({candidate_a.link_count} links)"
                )

                print(
                    "B:",
                    candidate_b.element_name,
                    candidate_b.element_id,
                    f"({candidate_b.link_count} links)"
                )

                print(
                    "RELATIONSHIP:",
                    relationship
                )

    except Exception as e:

        print(
            "FAILED:",
            repr(e)
        )


async def main():

    for name, url in TEST_SITES:

        await test_site(
            name,
            url
        )


if __name__ == "__main__":

    asyncio.run(main())