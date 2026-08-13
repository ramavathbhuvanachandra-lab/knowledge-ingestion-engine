import asyncio

from bs4 import BeautifulSoup

from crawler.crawler import crawl_page
from extractor.navigation_extractor import NavigationExtractor


TEST_URLS = [
    "https://www.iitb.ac.in",
    "https://www.iitb.ac.in/institute-functionaries",
    "https://www.iitm.ac.in",
    "https://www.iitd.ac.in",
    "https://www.iith.ac.in",
    "https://www.isro.gov.in",
    "https://www.india.gov.in",
    "https://docs.langchain.com",
    "https://supabase.com/docs",
    "https://gwpgc.ac.in/",
]


def get_dom_depth(element):

    depth = 0
    parent = element.parent

    while parent is not None:

        depth += 1
        parent = parent.parent

    return depth


def get_parent_info(element):

    parent = element.parent

    if parent is None:
        return None

    return {
        "tag": parent.name,
        "id": parent.get("id", ""),
        "classes": parent.get("class", []),
    }


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

        print(
            "\nTOTAL CANDIDATES:",
            len(candidates)
        )

        print("\nCANDIDATE STRUCTURE")
        print("-" * 90)

        # --------------------------------------------------
        # Build a map from candidate object -> HTML element
        # --------------------------------------------------

        candidate_elements = []

        for candidate in candidates:

            matching_element = None

            for element in soup.find_all(
                candidate.element_name
            ):

                element_id = element.get(
                    "id",
                    ""
                )

                classes = element.get(
                    "class",
                    []
                )

                if (
                    element_id == candidate.element_id
                    and
                    classes == candidate.classes
                ):

                    element_links = []

                    for link in element.find_all("a"):

                        text = link.get_text(
                            " ",
                            strip=True
                        )

                        if not text:
                            continue

                        if text in element_links:
                            continue

                        element_links.append(text)

                    if (
                        element_links
                        == candidate.links
                    ):

                        matching_element = element
                        break

            candidate_elements.append(
                (
                    candidate,
                    matching_element
                )
            )

        # --------------------------------------------------
        # Print candidates
        # --------------------------------------------------

        for index, (
            candidate,
            element
        ) in enumerate(
            candidate_elements,
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
                "Type    :",
                candidate.navigation_type
            )

            print(
                "Score   :",
                candidate.score
            )

            print(
                "Links   :",
                candidate.link_count
            )

            if element is None:

                print(
                    "DOM     : element not resolved"
                )

                continue

            print(
                "DOM Depth :",
                get_dom_depth(element)
            )

            parent_info = get_parent_info(
                element
            )

            print(
                "Parent    :",
                parent_info
            )

            # --------------------------------------------------
            # Immediate child structure
            # --------------------------------------------------

            children = []

            for child in element.find_all(
                recursive=False
            ):

                children.append(
                    child.name
                )

            print(
                "Children  :",
                children
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