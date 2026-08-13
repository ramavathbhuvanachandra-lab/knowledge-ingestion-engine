from models.navigation import NavigationCandidate

from analyzer.navigation_redundancy_decision import (
    NavigationRedundancyDecision,
)


def make_candidate(
    links,
    navigation_type="unknown",
    element_name="nav",
    element_id="",
    classes=None,
    aria_label="",
):
    return NavigationCandidate(
        element_name=element_name,
        element_id=element_id,
        classes=classes or [],
        aria_label=aria_label,
        links=links,
        link_count=len(links),
        navigation_type=navigation_type,
        score=0,
    )


def run_test(
    name,
    candidate_a,
    candidate_b,
    redundancy_result,
    expected_decision,
    expected_reason,
):
    print("\n" + "=" * 75)
    print(name)
    print("=" * 75)

    analyzer = NavigationRedundancyDecision()

    result = analyzer.decide(
        redundancy_result,
        candidate_a,
        candidate_b,
    )

    print(
        "A type       :",
        candidate_a.navigation_type
    )

    print(
        "B type       :",
        candidate_b.navigation_type
    )

    print(
        "Relationship  :",
        redundancy_result["relationship"]
    )

    print(
        "Structure     :",
        redundancy_result["structure"]
    )

    print(
        "Containment   :",
        redundancy_result["containment"]
    )

    print(
        "Coverage      :",
        redundancy_result["coverage"]
    )

    print(
        "Decision      :",
        result["decision"]
    )

    print(
        "Reason        :",
        result["reason"]
    )

    print(
        "Confidence    :",
        result["confidence"]
    )

    if (
        result["decision"] == expected_decision
        and result["reason"] == expected_reason
    ):
        print("RESULT        : PASS")
        return True

    print("RESULT        : FAIL")
    print(
        "Expected      :",
        expected_decision,
        "/",
        expected_reason
    )

    return False


def main():

    tests = [

        # ==================================================
        # 1. EXACT DUPLICATE
        # ==================================================

        (
            "TEST 1 — EXACT DUPLICATE",

            make_candidate(
                [
                    "Home",
                    "Admissions",
                    "Academics",
                    "Research",
                ],
                navigation_type="primary",
            ),

            make_candidate(
                [
                    "Home",
                    "Admissions",
                    "Academics",
                    "Research",
                ],
                navigation_type="primary",
            ),

            {
                "relationship": "duplicate",
                "containment": 1.0,
                "coverage": 1.0,
                "structure": "sibling",
                "redundant": True,
            },

            "redundant",
            "exact_duplicate",
        ),

        # ==================================================
        # 2. DESKTOP / MOBILE DUPLICATE
        # ==================================================

        (
            "TEST 2 — DESKTOP MOBILE DUPLICATE",

            make_candidate(
                [
                    "Home",
                    "Admissions",
                    "Academics",
                    "Research",
                ],
                navigation_type="primary",
                classes=["desktop-menu"],
            ),

            make_candidate(
                [
                    "Home",
                    "Admissions",
                    "Academics",
                    "Research",
                ],
                navigation_type="primary",
                classes=["mobile-menu"],
            ),

            {
                "relationship": "duplicate",
                "containment": 1.0,
                "coverage": 1.0,
                "structure": "sibling",
                "redundant": True,
            },

            "redundant",
            "exact_duplicate",
        ),

        # ==================================================
        # 3. LEGITIMATE SMALL SUBMENU
        # ==================================================

        (
            "TEST 3 — HUGE PARENT + SMALL CHILD",

            make_candidate(
                [
                    "Home",
                    "Admissions",
                    "Academics",
                    "Research",
                    "Departments",
                    "Hostel",
                    "Library",
                    "Contact",
                    "Placements",
                    "Alumni",
                ],
                navigation_type="primary",
            ),

            make_candidate(
                [
                    "Departments",
                    "Hostel",
                ],
                navigation_type="secondary",
            ),

            {
                "relationship": "structural_duplicate",
                "containment": 1.0,
                "coverage": 0.2,
                "structure": "direct_parent",
                "redundant": True,
            },

            "keep_both",
            "legitimate_child_navigation",
        ),

        # ==================================================
        # 4. DEEP MEGA MENU CHILD
        # ==================================================

        (
            "TEST 4 — DEEP MEGA MENU CHILD",

            make_candidate(
                [
                    "Home",
                    "Admissions",
                    "Academics",
                    "Research",
                    "Departments",
                    "Faculty",
                    "Students",
                ],
                navigation_type="primary",
            ),

            make_candidate(
                [
                    "Faculty",
                    "Students",
                ],
                navigation_type="secondary",
            ),

            {
                "relationship": "structural_duplicate",
                "containment": 1.0,
                "coverage": 0.285,
                "structure": "ancestor",
                "redundant": True,
            },

            "keep_both",
            "legitimate_child_navigation",
        ),

        # ==================================================
        # 5. WRAPPER WITH EXACT SAME LINKS
        # ==================================================

        (
            "TEST 5 — STRUCTURAL WRAPPER",

            make_candidate(
                [
                    "Home",
                    "Admissions",
                    "Academics",
                    "Research",
                    "Contact",
                ],
                navigation_type="primary",
            ),

            make_candidate(
                [
                    "Home",
                    "Admissions",
                    "Academics",
                    "Research",
                    "Contact",
                ],
                navigation_type="unknown",
            ),

            {
                "relationship": "duplicate",
                "containment": 1.0,
                "coverage": 1.0,
                "structure": "direct_parent",
                "redundant": True,
            },

            "redundant",
            "exact_duplicate",
        ),

        # ==================================================
        # 6. FOOTER DUPLICATES PRIMARY
        # ==================================================

        (
            "TEST 6 — FOOTER DUPLICATES PRIMARY",

            make_candidate(
                [
                    "Home",
                    "Admissions",
                    "Academics",
                    "Research",
                    "Contact",
                ],
                navigation_type="primary",
            ),

            make_candidate(
                [
                    "Home",
                    "Admissions",
                    "Academics",
                    "Research",
                    "Contact",
                ],
                navigation_type="footer",
            ),

            {
                "relationship": "duplicate",
                "containment": 1.0,
                "coverage": 1.0,
                "structure": "sibling",
                "redundant": True,
            },

            "redundant",
            "exact_duplicate",
        ),

        # ==================================================
        # 7. FOOTER PARTIAL OVERLAP
        # ==================================================

        (
            "TEST 7 — FOOTER PARTIAL OVERLAP",

            make_candidate(
                [
                    "Home",
                    "Admissions",
                    "Academics",
                    "Research",
                    "Contact",
                ],
                navigation_type="primary",
            ),

            make_candidate(
                [
                    "Home",
                    "Contact",
                    "Privacy",
                    "RTI",
                ],
                navigation_type="footer",
            ),

            {
                "relationship": "overlap",
                "containment": 0.5,
                "coverage": 0.285,
                "structure": "sibling",
                "redundant": False,
            },

            "keep_both",
            "partial_overlap",
        ),

        # ==================================================
        # 8. SIBLING IDENTICAL MENUS
        # ==================================================

        (
            "TEST 8 — SIBLING IDENTICAL MENUS",

            make_candidate(
                [
                    "Home",
                    "Research",
                    "Contact",
                ],
                navigation_type="secondary",
            ),

            make_candidate(
                [
                    "Home",
                    "Research",
                    "Contact",
                ],
                navigation_type="secondary",
            ),

            {
                "relationship": "duplicate",
                "containment": 1.0,
                "coverage": 1.0,
                "structure": "sibling",
                "redundant": True,
            },

            "redundant",
            "exact_duplicate",
        ),

        # ==================================================
        # 9. NEAR DUPLICATE — ONE EXTRA LINK
        # ==================================================

        (
            "TEST 9 — NEAR DUPLICATE",

            make_candidate(
                [
                    "Home",
                    "Admissions",
                    "Academics",
                    "Research",
                    "Contact",
                ],
                navigation_type="primary",
            ),

            make_candidate(
                [
                    "Home",
                    "Admissions",
                    "Academics",
                    "Research",
                    "Contact",
                    "Alumni",
                ],
                navigation_type="primary",
            ),

            {
                "relationship": "subset",
                "containment": 1.0,
                "coverage": 0.833,
                "structure": "sibling",
                "redundant": False,
            },

            "keep_both",
            "independent_subset",
        ),

        # ==================================================
        # 10. SIDEBAR CONTAINS PRIMARY LINKS
        # ==================================================

        (
            "TEST 10 — SIDEBAR PARTIAL DUPLICATE",

            make_candidate(
                [
                    "Home",
                    "Admissions",
                    "Academics",
                    "Research",
                    "Departments",
                    "Contact",
                ],
                navigation_type="primary",
            ),

            make_candidate(
                [
                    "Academics",
                    "Research",
                    "Departments",
                    "Faculty",
                    "Students",
                ],
                navigation_type="secondary",
            ),

            {
                "relationship": "overlap",
                "containment": 0.75,
                "coverage": 0.5,
                "structure": "sibling",
                "redundant": False,
            },

            "keep_both",
            "partial_overlap",
        ),

        # ==================================================
        # 11. COMPLETELY UNRELATED
        # ==================================================

        (
            "TEST 11 — COMPLETELY UNRELATED",

            make_candidate(
                [
                    "Home",
                    "Academics",
                    "Research",
                ],
                navigation_type="primary",
            ),

            make_candidate(
                [
                    "RTI",
                    "Feedback",
                    "Privacy",
                ],
                navigation_type="footer",
            ),

            {
                "relationship": "unrelated",
                "containment": 0.0,
                "coverage": 0.0,
                "structure": "sibling",
                "redundant": False,
            },

            "keep_both",
            "unrelated_navigation",
        ),

        # ==================================================
        # 12. EMPTY A
        # ==================================================

        (
            "TEST 12 — EMPTY A",

            make_candidate(
                [],
                navigation_type="unknown",
            ),

            make_candidate(
                [
                    "Home",
                    "Research",
                ],
                navigation_type="primary",
            ),

            {
                "relationship": "unrelated",
                "containment": 0.0,
                "coverage": 0.0,
                "structure": "sibling",
                "redundant": False,
            },

            "keep_both",
            "unrelated_navigation",
        ),

        # ==================================================
        # 13. EMPTY B
        # ==================================================

        (
            "TEST 13 — EMPTY B",

            make_candidate(
                [
                    "Home",
                    "Research",
                ],
                navigation_type="primary",
            ),

            make_candidate(
                [],
                navigation_type="unknown",
            ),

            {
                "relationship": "unrelated",
                "containment": 0.0,
                "coverage": 0.0,
                "structure": "sibling",
                "redundant": False,
            },

            "keep_both",
            "unrelated_navigation",
        ),

        # ==================================================
        # 14. THREE-LEVEL NAVIGATION
        # ==================================================

        (
            "TEST 14 — THREE LEVEL NAVIGATION",

            make_candidate(
                [
                    "Home",
                    "Academics",
                    "Research",
                    "Admissions",
                    "Departments",
                    "Faculty",
                    "Students",
                ],
                navigation_type="primary",
            ),

            make_candidate(
                [
                    "Faculty",
                    "Students",
                ],
                navigation_type="secondary",
            ),

            {
                "relationship": "structural_duplicate",
                "containment": 1.0,
                "coverage": 0.285,
                "structure": "descendant",
                "redundant": True,
            },

            "keep_both",
            "legitimate_parent_child_navigation",
        ),

        # ==================================================
        # 15. SAME LINKS DIFFERENT TYPES
        # ==================================================

        (
            "TEST 15 — SAME LINKS DIFFERENT TYPES",

            make_candidate(
                [
                    "Home",
                    "Admissions",
                    "Research",
                ],
                navigation_type="primary",
            ),

            make_candidate(
                [
                    "Home",
                    "Admissions",
                    "Research",
                ],
                navigation_type="footer",
            ),

            {
                "relationship": "duplicate",
                "containment": 1.0,
                "coverage": 1.0,
                "structure": "sibling",
                "redundant": True,
            },

            "redundant",
            "exact_duplicate",
        ),

        # ==================================================
        # 16. LARGE OVERLAP BUT UNIQUE INFORMATION
        # ==================================================

        (
            "TEST 16 — LARGE OVERLAP WITH UNIQUE LINKS",

            make_candidate(
                [
                    "Home",
                    "Admissions",
                    "Academics",
                    "Research",
                    "Departments",
                    "Faculty",
                    "Students",
                    "Hostel",
                    "Library",
                    "Contact",
                ],
                navigation_type="primary",
            ),

            make_candidate(
                [
                    "Academics",
                    "Research",
                    "Departments",
                    "Faculty",
                    "Students",
                    "Placements",
                    "Alumni",
                ],
                navigation_type="secondary",
            ),

            {
                "relationship": "overlap",
                "containment": 0.714,
                "coverage": 0.588,
                "structure": "sibling",
                "redundant": False,
            },

            "keep_both",
            "partial_overlap",
        ),

        # ==================================================
        # 17. LEGITIMATE CHILD WITH 100% CONTAINMENT
        # ==================================================

        (
            "TEST 17 — LEGITIMATE CHILD 100 PERCENT CONTAINMENT",

            make_candidate(
                [
                    "Home",
                    "Academics",
                    "Research",
                    "Admissions",
                    "Departments",
                    "Contact",
                ],
                navigation_type="primary",
            ),

            make_candidate(
                [
                    "Departments",
                ],
                navigation_type="secondary",
            ),

            {
                "relationship": "structural_duplicate",
                "containment": 1.0,
                "coverage": 0.166,
                "structure": "ancestor",
                "redundant": True,
            },

            "keep_both",
            "legitimate_child_navigation",
        ),

        # ==================================================
        # 18. UNKNOWN STRUCTURE
        # ==================================================

        (
            "TEST 18 — UNKNOWN DOM STRUCTURE",

            make_candidate(
                [
                    "Home",
                    "Research",
                    "Contact",
                ],
                navigation_type="primary",
            ),

            make_candidate(
                [
                    "Home",
                    "Research",
                    "Contact",
                ],
                navigation_type="unknown",
            ),

            {
                "relationship": "duplicate",
                "containment": 1.0,
                "coverage": 1.0,
                "structure": "unknown",
                "redundant": True,
            },

            "redundant",
            "exact_duplicate",
        ),
    ]

    passed = 0

    for test in tests:

        if run_test(*test):
            passed += 1

    print("\n" + "=" * 75)

    print(
        f"TOTAL: {passed}/{len(tests)} TESTS PASSED"
    )

    print("=" * 75)


if __name__ == "__main__":
    main()