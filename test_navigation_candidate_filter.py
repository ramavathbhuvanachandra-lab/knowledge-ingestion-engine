from models.navigation import NavigationCandidate
from analyzer.navigation_candidate_filter import (
    NavigationCandidateFilter
)


def make_candidate(
    element_name="div",
    element_id="",
    classes=None,
    aria_label="",
    link_count=0,
    navigation_type="unknown",
    score=0
):
    return NavigationCandidate(
        element_name=element_name,
        element_id=element_id,
        classes=classes or [],
        aria_label=aria_label,
        links=[
            f"Link {i}"
            for i in range(link_count)
        ],
        link_count=link_count,
        navigation_type=navigation_type,
        score=score
    )


def run_test(
    name,
    candidate,
    expected
):

    filter_engine = NavigationCandidateFilter()

    result = filter_engine.filter(
        [candidate]
    )

    actual = len(result) > 0

    print("\n" + "=" * 70)
    print(name)
    print("=" * 70)

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

    print(
        "Expected:",
        "KEEP" if expected else "REMOVE"
    )

    print(
        "Actual  :",
        "KEEP" if actual else "REMOVE"
    )

    if actual == expected:

        print(
            "RESULT  : PASS"
        )

        return True

    print(
        "RESULT  : FAIL"
    )

    return False


def main():

    tests = [

        # ==================================================
        # 1. SEMANTIC NAVIGATION
        # ==================================================

        (
            "TEST 1 — SEMANTIC NAV",
            make_candidate(
                element_name="nav",
                link_count=3
            ),
            True
        ),

        # ==================================================
        # 2. PRIMARY NAVIGATION
        # ==================================================

        (
            "TEST 2 — PRIMARY NAVIGATION",
            make_candidate(
                element_name="nav",
                navigation_type="primary",
                score=15,
                link_count=10
            ),
            True
        ),

        # ==================================================
        # 3. MAIN MENU CLASS
        # ==================================================

        (
            "TEST 3 — MAIN MENU CLASS",
            make_candidate(
                element_name="div",
                classes=[
                    "main-menu"
                ],
                navigation_type="secondary",
                score=10,
                link_count=5
            ),
            True
        ),

        # ==================================================
        # 4. DROPDOWN MENU
        # ==================================================

        (
            "TEST 4 — DROPDOWN MENU",
            make_candidate(
                element_name="ul",
                classes=[
                    "dropdown-menu"
                ],
                link_count=6
            ),
            True
        ),

        # ==================================================
        # 5. SIDEBAR MENU
        # ==================================================

        (
            "TEST 5 — SIDEBAR MENU",
            make_candidate(
                element_name="div",
                classes=[
                    "side-menu"
                ],
                link_count=15
            ),
            True
        ),

        # ==================================================
        # 6. FOOTER NAVIGATION
        # ==================================================

        (
            "TEST 6 — FOOTER NAVIGATION",
            make_candidate(
                element_name="nav",
                element_id="footer-nav",
                navigation_type="footer",
                score=10,
                link_count=4
            ),
            True
        ),

        # ==================================================
        # 7. ARIA NAVIGATION
        # ==================================================

        (
            "TEST 7 — ARIA NAVIGATION",
            make_candidate(
                element_name="div",
                aria_label="Main Navigation",
                link_count=4
            ),
            True
        ),

        # ==================================================
        # 8. NAVIGATION ID
        # ==================================================

        (
            "TEST 8 — NAVIGATION ID",
            make_candidate(
                element_name="div",
                element_id="site-navigation",
                link_count=4
            ),
            True
        ),

        # ==================================================
        # 9. LIST WITH MANY LINKS
        # ==================================================

        (
            "TEST 9 — LIST WITH MANY LINKS",
            make_candidate(
                element_name="ul",
                link_count=8
            ),
            True
        ),

        # ==================================================
        # 10. RANDOM DIV
        # ==================================================

        (
            "TEST 10 — RANDOM DIV",
            make_candidate(
                element_name="div",
                element_id="random-wrapper",
                classes=[
                    "random-wrapper"
                ],
                link_count=5,
                navigation_type="unknown",
                score=0
            ),
            False
        ),

        # ==================================================
        # 11. CONTENT SECTION
        # ==================================================

        (
            "TEST 11 — CONTENT SECTION",
            make_candidate(
                element_name="div",
                element_id="content",
                classes=[
                    "content"
                ],
                link_count=2,
                navigation_type="unknown",
                score=1
            ),
            False
        ),

        # ==================================================
        # 12. GENERIC SECTION
        # ==================================================

        (
            "TEST 12 — GENERIC SECTION",
            make_candidate(
                element_name="section",
                classes=[
                    "wrapper"
                ],
                link_count=4,
                navigation_type="unknown",
                score=0
            ),
            False
        ),

        # ==================================================
        # 13. LARGE GENERIC DIV WITH STRONG SCORE
        # ==================================================

        (
            "TEST 13 — LARGE GENERIC CONTAINER",
            make_candidate(
                element_name="div",
                classes=[
                    "large-container"
                ],
                link_count=15,
                score=5
            ),
            True
        ),

        # ==================================================
        # 14. SMALL UL
        # ==================================================

        (
            "TEST 14 — SMALL UL",
            make_candidate(
                element_name="ul",
                classes=[
                    "list"
                ],
                link_count=2,
                navigation_type="unknown",
                score=0
            ),
            False
        ),

        # ==================================================
        # 15. NESTED UNIVERSITY MENU
        # ==================================================

        (
            "TEST 15 — UNIVERSITY DROPDOWN",
            make_candidate(
                element_name="ul",
                classes=[
                    "dropdown-menu",
                    "submenu"
                ],
                link_count=4
            ),
            True
        ),

    ]

    passed = 0

    for (
        name,
        candidate,
        expected
    ) in tests:

        if run_test(
            name,
            candidate,
            expected
        ):

            passed += 1

    print("\n" + "=" * 70)

    print(
        f"TOTAL: {passed}/{len(tests)} TESTS PASSED"
    )

    print("=" * 70)


if __name__ == "__main__":

    main()