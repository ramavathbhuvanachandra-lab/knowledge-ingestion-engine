from models.navigation import NavigationCandidate

from analyzer.navigation_redundancy_decision import (
    NavigationRedundancyDecision,
)


def make_candidate(
    links,
    navigation_type="unknown",
):
    return NavigationCandidate(
        element_name="nav",
        element_id="",
        classes=[],
        aria_label="",
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
    print("\n" + "=" * 70)
    print(name)
    print("=" * 70)

    analyzer = NavigationRedundancyDecision()

    result = analyzer.decide(
        redundancy_result,
        candidate_a,
        candidate_b,
    )

    print(
        "Relationship :",
        redundancy_result["relationship"]
    )

    print(
        "Structure    :",
        redundancy_result["structure"]
    )

    print(
        "Decision     :",
        result["decision"]
    )

    print(
        "Reason       :",
        result["reason"]
    )

    print(
        "Confidence   :",
        result["confidence"]
    )

    if (
        result["decision"] == expected_decision
        and result["reason"] == expected_reason
    ):
        print("RESULT       : PASS")
        return True

    print("RESULT       : FAIL")
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
        # TEST 2 — LEGITIMATE CHILD
        # ==================================================

        (
            "TEST 2 — LEGITIMATE CHILD",

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

            {
                "relationship": "structural_duplicate",
                "containment": 1.0,
                "coverage": 0.6,
                "structure": "direct_parent",
                "redundant": True,
            },

            "keep_both",
            "legitimate_child_navigation",
        ),

        # ==================================================
        # TEST 3 — DEEP CHILD
        # ==================================================

        (
            "TEST 3 — DEEP CHILD",

            make_candidate([
                "Home",
                "Academics",
                "Research",
                "Departments",
            ]),

            make_candidate([
                "Research",
                "Departments",
            ]),

            {
                "relationship": "structural_duplicate",
                "containment": 1.0,
                "coverage": 0.5,
                "structure": "ancestor",
                "redundant": True,
            },

            "keep_both",
            "legitimate_child_navigation",
        ),

        # ==================================================
        # TEST 4 — INDEPENDENT SUBSET
        # ==================================================

        (
            "TEST 4 — INDEPENDENT SUBSET",

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

            {
                "relationship": "subset",
                "containment": 1.0,
                "coverage": 0.5,
                "structure": "sibling",
                "redundant": False,
            },

            "keep_both",
            "independent_subset",
        ),

        # ==================================================
        # TEST 5 — PARTIAL OVERLAP
        # ==================================================

        (
            "TEST 5 — PARTIAL OVERLAP",

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

            {
                "relationship": "overlap",
                "containment": 0.5,
                "coverage": 0.5,
                "structure": "sibling",
                "redundant": False,
            },

            "keep_both",
            "partial_overlap",
        ),

        # ==================================================
        # TEST 6 — UNRELATED
        # ==================================================

        (
            "TEST 6 — UNRELATED"
            ,
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