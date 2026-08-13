from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler

from extractor.navigation_extractor import NavigationExtractor
from analyzer.navigation_structure import NavigationStructureAnalyzer
from analyzer.navigation_hierarchy import NavigationHierarchyBuilder


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


def convert_candidates(
    navigation_candidates
):
    """
    Convert NavigationCandidate objects into the
    dictionary structure expected by the hierarchy builder.

    Important:
    NavigationCandidate currently stores metadata, but
    not the original BeautifulSoup element.

    Therefore we resolve the element again from the
    extracted page using its identifying information.
    """

    candidates = []

    for index, candidate in enumerate(
        navigation_candidates
    ):

        candidates.append({
            "id": index,
            "candidate": candidate,
            "element": None
        })

    return candidates


def resolve_elements(
    soup,
    candidates
):
    """
    Resolve each NavigationCandidate back to its
    corresponding BeautifulSoup element.
    """

    used = set()

    for candidate_data in candidates:

        candidate = candidate_data["candidate"]

        matches = []

        # ----------------------------------------------
        # First: exact element name + ID
        # ----------------------------------------------

        if candidate.element_id:

            matches = soup.find_all(
                candidate.element_name,
                id=candidate.element_id
            )

        # ----------------------------------------------
        # Second: element name + exact class set
        # ----------------------------------------------

        if not matches:

            for element in soup.find_all(
                candidate.element_name
            ):

                classes = element.get(
                    "class",
                    []
                )

                if (
                    list(classes)
                    == list(candidate.classes)
                ):

                    matches.append(element)

        # ----------------------------------------------
        # Third: element name + aria-label
        # ----------------------------------------------

        if not matches and candidate.aria_label:

            matches = soup.find_all(
                candidate.element_name,
                attrs={
                    "aria-label":
                    candidate.aria_label
                }
            )

        # ----------------------------------------------
        # Choose first unused match
        # ----------------------------------------------

        for element in matches:

            element_identity = id(element)

            if element_identity in used:
                continue

            candidate_data["element"] = element

            used.add(
                element_identity
            )

            break


def create_relationships(
    candidates
):
    """
    Calculate structural relationships between
    all resolved candidates.
    """

    analyzer = NavigationStructureAnalyzer()

    relationships = []

    for candidate_a in candidates:

        element_a = candidate_a["element"]

        if element_a is None:
            continue

        for candidate_b in candidates:

            element_b = candidate_b["element"]

            if element_b is None:
                continue

            if (
                candidate_a["id"]
                == candidate_b["id"]
            ):
                continue

            relationship = (
                analyzer.get_relationship(
                    element_a,
                    element_b
                )
            )

            if relationship in {
                "direct_parent",
                "direct_child",
                "ancestor",
                "descendant"
            }:

                relationships.append({

                    "a": candidate_a["id"],

                    "b": candidate_b["id"],

                    "relationship":
                        relationship
                })

    return relationships


def calculate_depth(
    node
):
    """
    Calculate hierarchy depth.
    """

    if not node["children"]:

        return 1

    return 1 + max(
        calculate_depth(child)
        for child in node["children"]
    )


def count_nodes(
    node
):
    """
    Count nodes in a hierarchy tree.
    """

    total = 1

    for child in node["children"]:

        total += count_nodes(child)

    return total


def print_tree(
    node,
    candidates,
    level=0
):

    indent = "    " * level

    candidate_id = node["id"]

    candidate_data = candidates[
        candidate_id
    ]

    candidate = candidate_data[
        "candidate"
    ]

    print(
        f"{indent}- "
        f"{candidate.element_name} "
        f"| "
        f"type={candidate.navigation_type} "
        f"| "
        f"score={candidate.score} "
        f"| "
        f"links={candidate.link_count}"
    )

    for child in node["children"]:

        print_tree(
            child,
            candidates,
            level + 1
        )


async def test_website(
    name,
    url
):

    print("\n")
    print("=" * 80)
    print(name)
    print(url)
    print("=" * 80)

    async with AsyncWebCrawler() as crawler:

        result = await crawler.arun(
            url=url
        )

    if not result.success:

        print(
            "CRAWL FAILED"
        )

        return

    # --------------------------------------------------
    # Parse HTML
    # --------------------------------------------------

    soup = BeautifulSoup(
        result.html,
        "html.parser"
    )

    # --------------------------------------------------
    # Extract navigation candidates
    # --------------------------------------------------

    extractor = NavigationExtractor(
        soup
    )

    navigation_candidates = (
        extractor.discover_candidates()
    )

    print(
        "\nRAW CANDIDATES:",
        len(navigation_candidates)
    )

    if not navigation_candidates:

        print(
            "No navigation candidates found."
        )

        return

    # --------------------------------------------------
    # Convert candidates
    # --------------------------------------------------

    candidates = convert_candidates(
        navigation_candidates
    )

    # --------------------------------------------------
    # Resolve original DOM elements
    # --------------------------------------------------

    resolve_elements(
        soup,
        candidates
    )

    resolved_count = sum(
        1
        for candidate in candidates
        if candidate["element"] is not None
    )

    print(
        "RESOLVED:",
        resolved_count,
        "/",
        len(candidates)
    )

    if resolved_count == 0:

        print(
            "No candidates could be resolved."
        )

        return

    # --------------------------------------------------
    # Relationships
    # --------------------------------------------------

    relationships = create_relationships(
        candidates
    )

    print(
        "STRUCTURAL RELATIONSHIPS:",
        len(relationships)
    )

    # --------------------------------------------------
    # Build hierarchy
    # --------------------------------------------------

    builder = NavigationHierarchyBuilder()

    hierarchy = builder.build(
        candidates,
        relationships
    )

    # --------------------------------------------------
    # Statistics
    # --------------------------------------------------

    total_nodes = sum(
        count_nodes(root)
        for root in hierarchy
    )

    maximum_depth = 0

    for root in hierarchy:

        maximum_depth = max(
            maximum_depth,
            calculate_depth(root)
        )

    print(
        "ROOTS:",
        len(hierarchy)
    )

    print(
        "HIERARCHY NODES:",
        total_nodes
    )

    print(
        "MAX DEPTH:",
        maximum_depth
    )

    # --------------------------------------------------
    # Print hierarchy
    # --------------------------------------------------

    print(
        "\nHIERARCHY:"
    )

    for root in hierarchy:

        print_tree(
            root,
            candidates
        )


async def main():

    for name, url in WEBSITES:

        try:

            await test_website(
                name,
                url
            )

        except Exception as error:

            print(
                "\nERROR:",
                type(error).__name__,
                str(error)
            )


if __name__ == "__main__":

    import asyncio

    asyncio.run(
        main()
    )