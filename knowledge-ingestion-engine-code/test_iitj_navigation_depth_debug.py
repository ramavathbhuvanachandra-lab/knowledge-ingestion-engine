import asyncio

from bs4 import BeautifulSoup

from crawler.crawler import crawl_page
from pipeline.navigation_pipeline import NavigationPipeline


URL = "https://www.iitj.ac.in/"


def walk(nodes, level=0):

    for node in nodes:

        print(
            "  " * level
            + f"- {node.text!r} -> {node.href!r}"
        )

        if node.children:

            walk(
                node.children,
                level + 1,
            )


async def main():

    page = await crawl_page(URL)

    assert page.success

    soup = BeautifulSoup(
        page.html,
        "html.parser",
    )

    pipeline = NavigationPipeline(
        soup=soup,
    )

    result = pipeline.run()

    candidates = result["candidates"]

    print("=" * 100)
    print("IITJ NAVIGATION DEBUG")
    print("=" * 100)

    print(
        "Candidates:",
        len(candidates),
    )

    for index, candidate in enumerate(
        candidates,
        start=1,
    ):

        print("\n" + "-" * 80)

        print(
            "Candidate:",
            index,
        )

        print(
            "Element:",
            candidate.element_name,
        )

        print(
            "Class:",
            candidate.classes,
        )

        print(
            "Links:",
            candidate.link_count,
        )

        print(
            "Tree nodes:",
            len(candidate.tree),
        )

        print("\nTREE:")

        walk(candidate.tree)


if __name__ == "__main__":

    asyncio.run(main())