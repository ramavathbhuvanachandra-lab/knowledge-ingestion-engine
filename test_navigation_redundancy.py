from bs4 import BeautifulSoup

from models.navigation import NavigationCandidate

from analyzer.navigation_redundancy import (
    NavigationRedundancyAnalyzer,
)


def make_candidate(
    links,
    element_name="nav",
    element_id="",
    classes=None,
):
    return NavigationCandidate(
        element_name=element_name,
        element_id=element_id,
        classes=classes or [],
        aria_label="",
        links=links,
        link_count=len(links),
        navigation_type="unknown",
        score=0,
    )


def run_test(
    name,
    candidate_a,
    candidate_b,
    html,
    selector_a,
    selector_b,
    expected_relationship,
    expected_redundant,
):
    print("\n" + "=" * 70)
    print(name)
    print("=" * 70)

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    element_a = soup.select_one(
        selector_a
    )

    element_b = soup.select_one(
        selector_b
    )

    analyzer = NavigationRedundancyAnalyzer()

    result = analyzer.analyze(
        candidate_a,
        candidate_b,
        element_a,
        element_b,
    )

    print(
        "Relationship :",
        result["relationship"]
    )

    print(
        "Containment  :",
        result["containment"]
    )

    print(
        "Coverage     :",
        result["coverage"]
    )

    print(
        "Structure    :",
        result["structure"]
    )

    print(
        "Redundant    :",
        result["redundant"]
    )

    relationship_pass = (
        result["relationship"]
        == expected_relationship
    )

    redundancy_pass = (
        result["redundant"]
        == expected_redundant
    )

    if (
        relationship_pass
        and redundancy_pass
    ):

        print(
            "RESULT       : PASS"
        )

        return True

    print(
        "RESULT       : FAIL"
    )

    return False


def main():

    tests = [

        # ==================================================
        # TEST 1 — EXACT DUPLICATE
        # ==================================================

        (
            "TEST 1 — EXACT DUPLICATE",

            make_candidate([
                "Home",
                "Admissions",
                "Research",
                "Contact",
            ]),

            make_candidate([
                "Home",
                "Admissions",
                "Research",
                "Contact",
            ]),

            """
            <nav id="a">
                <a>Home</a>
                <a>Admissions</a>
                <a>Research</a>
                <a>Contact</a>
            </nav>

            <nav id="b">
                <a>Home</a>
                <a>Admissions</a>
                <a>Research</a>
                <a>Contact</a>
            </nav>
            """,

            "#a",
            "#b",

            "duplicate",
            True,
        ),

        # ==================================================
        # TEST 2 — PARENT CONTAINS CHILD
        # ==================================================

        (
            "TEST 2 — PARENT CONTAINS CHILD",

            make_candidate([
                "Home",
                "Academics",
                "Research",
                "Admissions",
                "Contact",
            ]),

            make_candidate([
                "Academics",
                "Research",
                "Admissions",
            ]),

            """
            <nav id="parent">
                <a>Home</a>
                <a>Academics</a>
                <a>Research</a>

                <ul id="child">
                    <a>Academics</a>
                    <a>Research</a>
                    <a>Admissions</a>
                </ul>

                <a>Contact</a>
            </nav>
            """,

            "#parent",
            "#child",

            "structural_duplicate",
            True,
        ),

        # ==================================================
        # TEST 3 — SUBSET BUT UNRELATED DOM
        # ==================================================

        (
            "TEST 3 — SUBSET BUT UNRELATED DOM",

            make_candidate([
                "Home",
                "Academics",
                "Research",
                "Admissions",
            ]),

            make_candidate([
                "Academics",
                "Research",
            ]),

            """
            <nav id="a">
                <a>Home</a>
                <a>Academics</a>
                <a>Research</a>
                <a>Admissions</a>
            </nav>

            <nav id="b">
                <a>Academics</a>
                <a>Research</a>
            </nav>
            """,

            "#a",
            "#b",

            "subset",
            False,
        ),

        # ==================================================
        # TEST 4 — PARTIAL OVERLAP
        # ==================================================

        (
            "TEST 4 — PARTIAL OVERLAP",

            make_candidate([
                "Home",
                "Academics",
                "Research",
                "Admissions",
            ]),

            make_candidate([
                "Research",
                "Admissions",
                "Hostel",
                "Library",
            ]),

            """
            <nav id="a">
                <a>Home</a>
                <a>Academics</a>
                <a>Research</a>
                <a>Admissions</a>
            </nav>

            <nav id="b">
                <a>Research</a>
                <a>Admissions</a>
                <a>Hostel</a>
                <a>Library</a>
            </nav>
            """,

            "#a",
            "#b",

            "overlap",
            False,
        ),

        # ==================================================
        # TEST 5 — UNRELATED
        # ==================================================

        (
            "TEST 5 — UNRELATED",

            make_candidate([
                "Home",
                "Academics",
                "Research",
            ]),

            make_candidate([
                "RTI",
                "Feedback",
                "Contact",
            ]),

            """
            <nav id="a">
                <a>Home</a>
            </nav>

            <nav id="b">
                <a>RTI</a>
            </nav>
            """,

            "#a",
            "#b",

            "unrelated",
            False,
        ),

        # ==================================================
        # TEST 6 — DEEP STRUCTURAL DUPLICATE
        # ==================================================

        (
            "TEST 6 — DEEP STRUCTURAL DUPLICATE",

            make_candidate([
                "Academics",
                "Research",
                "Admissions",
            ]),

            make_candidate([
                "Academics",
                "Research",
                "Admissions",
            ]),

            """
            <nav id="a">
                <div>
                    <ul>
                        <li id="b">
                            <a>Academics</a>
                            <a>Research</a>
                            <a>Admissions</a>
                        </li>
                    </ul>
                </div>
            </nav>
            """,

            "#a",
            "#b",

            "duplicate",
            True,
        ),

        # ==================================================
        # TEST 7 — SIBLING MENUS WITH SAME LINKS
        # ==================================================

        (
            "TEST 7 — SIBLING DUPLICATE",

            make_candidate([
                "Home",
                "Research",
                "Contact",
            ]),

            make_candidate([
                "Home",
                "Research",
                "Contact",
            ]),

            """
            <div>
                <nav id="a">
                    <a>Home</a>
                    <a>Research</a>
                    <a>Contact</a>
                </nav>

                <nav id="b">
                    <a>Home</a>
                    <a>Research</a>
                    <a>Contact</a>
                </nav>
            </div>
            """,

            "#a",
            "#b",

            "duplicate",
            True,
        ),

        # ==================================================
        # TEST 8 — EMPTY CANDIDATE
        # ==================================================

        (
            "TEST 8 — EMPTY CANDIDATE",

            make_candidate([]),

            make_candidate([
                "Home",
                "Research",
            ]),

            """
            <nav id="a"></nav>

            <nav id="b">
                <a>Home</a>
                <a>Research</a>
            </nav>
            """,

            "#a",
            "#b",

            "unrelated",
            False,
        ),
    ]

    passed = 0

    for test in tests:

        if run_test(*test):

            passed += 1

    print("\n" + "=" * 70)

    print(
        f"TOTAL: {passed}/{len(tests)} TESTS PASSED"
    )

    print("=" * 70)


if __name__ == "__main__":

    main()