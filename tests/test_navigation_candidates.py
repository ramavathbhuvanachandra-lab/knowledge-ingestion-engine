import asyncio

from bs4 import BeautifulSoup

from crawler.crawler import crawl_page
from extractor.navigation_extractor import NavigationExtractor


URLS = [
    "https://www.iitb.ac.in",
    "https://docs.langchain.com",
    "https://supabase.com/docs",
]


async def main():

    for url in URLS:

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

                print("\n" + "-" * 80)

                print(
                    f"CANDIDATE #{index}"
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
                    candidate.links[:15]
                )

        except Exception as e:

            print(
                "FAILED:",
                e
            )


if __name__ == "__main__":
    asyncio.run(main())