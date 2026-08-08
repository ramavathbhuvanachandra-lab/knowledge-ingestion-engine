from bs4 import BeautifulSoup

from analyzer.navigation_structure import (
    NavigationStructureAnalyzer
)

from analyzer.navigation_hierarchy import (
    NavigationHierarchyBuilder
)


def create_candidates(soup):

    elements = soup.find_all(
        ["nav", "ul"]
    )

    candidates = []

    for index, element in enumerate(elements):

        candidates.append({
            "id": index,
            "element": element
        })

    return candidates


def create_relationships(
    candidates
):

    analyzer = NavigationStructureAnalyzer()

    relationships = []

    for i, candidate_a in enumerate(
        candidates
    ):

        for j, candidate_b in enumerate(
            candidates
        ):

            if i == j:
                continue

            relationship = analyzer.get_relationship(
                candidate_a["element"],
                candidate_b["element"]
            )

            relationships.append({

                "a": candidate_a["id"],

                "b": candidate_b["id"],

                "relationship": relationship
            })

    return relationships


def print_tree(
    node,
    candidates,
    level=0
):

    indent = "    " * level

    candidate_id = node["id"]

    element = candidates[
        candidate_id
    ]["element"]

    print(
        f"{indent}- {element.name}"
    )

    for child in node["children"]:

        print_tree(
            child,
            candidates,
            level + 1
        )


def run_test(
    name,
    html
):

    print("\n" + "=" * 70)

    print(name)

    print("=" * 70)

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    candidates = create_candidates(
        soup
    )

    relationships = create_relationships(
        candidates
    )

    builder = NavigationHierarchyBuilder()

    hierarchy = builder.build(
        candidates,
        relationships
    )

    print("\nCANDIDATES:")

    for candidate in candidates:

        print(
            f"  {candidate['id']} "
            f"→ {candidate['element'].name}"
        )

    print("\nHIERARCHY:")

    for root in hierarchy:

        print_tree(
            root,
            candidates
        )

    return hierarchy


def main():

    # ==================================================
    # TEST 1 — DIRECT PARENT
    # ==================================================

    run_test(
        "TEST 1 — DIRECT PARENT",

        """
        <nav>
            <ul>
                <li>Home</li>
                <li>Academics</li>
            </ul>
        </nav>
        """
    )

    # ==================================================
    # TEST 2 — DEEP NESTING
    # ==================================================

    run_test(
        "TEST 2 — DEEP NESTING",

        """
        <nav>

            <ul>

                <li>
                    Academics

                    <ul>
                        <li>Undergraduate</li>
                        <li>Postgraduate</li>
                    </ul>

                </li>

            </ul>

        </nav>
        """
    )

    # ==================================================
    # TEST 3 — MULTIPLE SIBLINGS
    # ==================================================

    run_test(
        "TEST 3 — MULTIPLE SIBLINGS",

        """
        <nav>

            <ul>
                <li>Home</li>
            </ul>

            <ul>
                <li>Academics</li>
            </ul>

            <ul>
                <li>Research</li>
            </ul>

        </nav>
        """
    )

    # ==================================================
    # TEST 4 — MULTI LEVEL MENU
    # ==================================================

    run_test(
        "TEST 4 — MULTI LEVEL MENU",

        """
        <nav>

            <ul>

                <li>

                    Academics

                    <ul>

                        <li>

                            Undergraduate

                            <ul>
                                <li>B.Tech</li>
                                <li>B.Sc</li>
                            </ul>

                        </li>

                        <li>

                            Postgraduate

                            <ul>
                                <li>M.Tech</li>
                                <li>M.Sc</li>
                            </ul>

                        </li>

                    </ul>

                </li>

            </ul>

        </nav>
        """
    )

    # ==================================================
    # TEST 5 — UNRELATED NAVIGATIONS
    # ==================================================

    run_test(
        "TEST 5 — UNRELATED NAVIGATIONS",

        """
        <nav id="main">

            <ul>
                <li>Home</li>
                <li>Academics</li>
            </ul>

        </nav>


        <nav id="footer">

            <ul>
                <li>Contact</li>
                <li>Privacy</li>
            </ul>

        </nav>
        """
    )

    # ==================================================
    # TEST 6 — NO NAVIGATION
    # ==================================================

    run_test(
        "TEST 6 — NO NAVIGATION",

        """
        <main>

            <h1>
                Electrical Engineering
            </h1>

            <p>
                Power systems research.
            </p>

        </main>
        """
    )


if __name__ == "__main__":

    main()