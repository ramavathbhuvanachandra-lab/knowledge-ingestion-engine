import asyncio

from bs4 import BeautifulSoup

from crawler.crawler import crawl_page
from extractor.navigation_extractor import NavigationExtractor


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
        "IIT Jodhpur",
        "https://iitj.ac.in"
    ),
    (
        "India Government",
        "https://www.india.gov.in"
    ),
    (
        "ISRO",
        "https://www.isro.gov.in"
    ),
    (
        "LangChain",
        "https://docs.langchain.com"
    ),
    (
        "Supabase",
        "https://supabase.com/docs"
    ),
]


async def test_site(name, url):

    print("\n" + "=" * 90)
    print(name)
    print(url)
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

        candidates = (
            extractor.discover_candidates()
        )

        print(
            "\nCANDIDATE COUNT:",
            len(candidates)
        )

        for index, candidate in enumerate(
            candidates,
            start=1
        ):

            print(
                f"\n#{index}"
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
                "Preview :",
                candidate.links[:10]
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