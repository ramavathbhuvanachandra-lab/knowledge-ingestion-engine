import asyncio

from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler

from extractor.navigation_extractor import NavigationExtractor
from analyzer.navigation_tree import NavigationTreeExtractor


URLS = [
    "https://www.iitb.ac.in",
    "https://www.iitm.ac.in",
    "https://www.iitd.ac.in",
    "https://www.iith.ac.in",
    "https://www.isro.gov.in",
    "https://www.india.gov.in",
    "https://gwpgc.ac.in/",
]


def print_tree(nodes, level=0):

    for node in nodes:

        indent = "  " * level

        line = f"{indent}- {node.text}"

        if node.href:
            line += f" -> {node.href}"

        print(line)

        if node.children:
            print_tree(
                node.children,
                level + 1
            )


def resolve_element(soup, candidate):

    # First try ID.
    if candidate.element_id:

        element = soup.find(
            candidate.element_name,
            id=candidate.element_id
        )

        if element is not None:
            return element

    # Then try exact class match.
    candidate_classes = set(
        candidate.classes
    )

    for element in soup.find_all(
        candidate.element_name
    ):

        element_classes = set(
            element.get("class", [])
        )

        if element_classes == candidate_classes:
            return element

    return None


async def crawl_page(crawler, url):

    print("\n" + "=" * 80)
    print("URL:", url)
    print("=" * 80)

    try:

        result = await crawler.arun(
            url=url
        )

    except Exception as error:

        print("CRAWL ERROR:")
        print(
            type(error).__name__,
            str(error)
        )

        return

    if not result.success:

        print("CRAWL FAILED")

        print(
            "Reason:",
            result.error_message
        )

        return

    print("CRAWL SUCCESS")

    soup = BeautifulSoup(
        result.html,
        "html.parser"
    )

    # ==================================================
    # Navigation candidate discovery
    # ==================================================

    navigation_extractor = (
        NavigationExtractor(soup)
    )

    candidates = (
        navigation_extractor.discover_candidates()
    )

    print(
        "\nRAW CANDIDATES:",
        len(candidates)
    )

    if not candidates:

        print(
            "No navigation candidates found."
        )

        return

    # ==================================================
    # Tree extraction
    # ==================================================

    tree_extractor = (
        NavigationTreeExtractor()
    )

    for index, candidate in enumerate(
        candidates,
        start=1
    ):

        print("\n" + "-" * 80)

        print(
            f"CANDIDATE {index}"
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

        # ----------------------------------------------
        # Resolve candidate DOM element
        # ----------------------------------------------

        element = candidate.element

        if element is None:

            print(
                "\nTREE    : DOM element not found"
            )

            continue

        # ----------------------------------------------
        # Extract navigation tree
        # ----------------------------------------------

        try:

            tree = tree_extractor.extract(
                element
            )

        except Exception as error:

            print(
                "\nTREE ERROR:"
            )

            print(
                type(error).__name__,
                str(error)
            )

            continue

        print("\nTREE:")

        if not tree:

            print(
                "  <empty>"
            )

            continue

        print_tree(
            tree,
            level=1
        )


async def main():

    async with AsyncWebCrawler() as crawler:

        for url in URLS:

            await crawl_page(
                crawler,
                url
            )


if __name__ == "__main__":

    asyncio.run(
        main()
    )
