from models.navigation import NavigationCandidate


def make_candidate(name, links):

    return NavigationCandidate(
        element_name="div",
        element_id=name,
        classes=[],
        aria_label="",
        links=links,
        link_count=len(links),
        navigation_type="unknown",
        score=0
    )


def calculate_similarity(candidate_a, candidate_b):

    links_a = set(candidate_a.links)
    links_b = set(candidate_b.links)

    if not links_a or not links_b:
        return 0.0

    intersection = links_a & links_b

    smaller_size = min(
        len(links_a),
        len(links_b)
    )

    return len(intersection) / smaller_size

def calculate_coverage(
    candidate_a,
    candidate_b
):

    links_a = set(candidate_a.links)
    links_b = set(candidate_b.links)

    if not links_a or not links_b:
        return 0.0

    intersection = links_a & links_b

    larger_size = max(
        len(links_a),
        len(links_b)
    )

    return len(intersection) / larger_size


def run_test(
    test_name,
    candidate_a,
    candidate_b,
    expected
):

    similarity = calculate_similarity(
        candidate_a,
        candidate_b
    )

    passed = abs(similarity - expected) < 0.001

    print("\n" + "=" * 70)
    print(test_name)
    print("=" * 70)

    print("Candidate A:", candidate_a.links)
    print("Candidate B:", candidate_b.links)

    print(
        "Similarity :",
        round(similarity, 3)
    )

    print(
        "Expected   :",
        expected
    )

    print(
        "RESULT     :",
        "PASS" if passed else "FAIL"
    )

    return passed


def main():

    tests = []

    # --------------------------------------------------
    # TEST 1 — Exact duplicate
    # --------------------------------------------------

    a = make_candidate(
        "menu-a",
        [
            "Home",
            "Admissions",
            "Research",
            "Departments",
            "Contact"
        ]
    )

    b = make_candidate(
        "menu-b",
        [
            "Home",
            "Admissions",
            "Research",
            "Departments",
            "Contact"
        ]
    )

    tests.append(
        run_test(
            "TEST 1 — EXACT DUPLICATE",
            a,
            b,
            1.0
        )
    )

    # --------------------------------------------------
    # TEST 2 — Partial overlap
    # --------------------------------------------------

    a = make_candidate(
        "menu-a",
        [
            "Home",
            "Admissions",
            "Research",
            "Departments",
            "Contact"
        ]
    )

    b = make_candidate(
        "menu-b",
        [
            "Admissions",
            "Research",
            "Departments"
        ]
    )

    tests.append(
        run_test(
            "TEST 2 — PARTIAL OVERLAP",
            a,
            b,
            1.0
        )
    )

    # --------------------------------------------------
    # TEST 3 — No overlap
    # --------------------------------------------------

    a = make_candidate(
        "menu-a",
        [
            "Home",
            "Admissions",
            "Research"
        ]
    )

    b = make_candidate(
        "menu-b",
        [
            "RTI",
            "Feedback",
            "Contact"
        ]
    )

    tests.append(
        run_test(
            "TEST 3 — NO OVERLAP",
            a,
            b,
            0.0
        )
    )

    # --------------------------------------------------
    # TEST 4 — Half overlap
    # --------------------------------------------------

    a = make_candidate(
        "menu-a",
        [
            "Home",
            "Admissions",
            "Research",
            "Departments"
        ]
    )

    b = make_candidate(
        "menu-b",
        [
            "Admissions",
            "Research",
            "Library",
            "Hostel"
        ]
    )

    tests.append(
        run_test(
            "TEST 4 — HALF OVERLAP",
            a,
            b,
            0.5
        )
    )

    # --------------------------------------------------
    # TEST 5 — Empty candidate
    # --------------------------------------------------

    a = make_candidate(
        "menu-a",
        []
    )

    b = make_candidate(
        "menu-b",
        [
            "Home",
            "Research"
        ]
    )

    tests.append(
        run_test(
            "TEST 5 — EMPTY CANDIDATE",
            a,
            b,
            0.0
        )
    )


    # --------------------------------------------------
    # TEST 6 — DUPLICATE VS SUBSET
    # --------------------------------------------------

    a = make_candidate(
        "menu-a",
        [
            "Home",
            "Admissions",
            "Research",
            "Departments",
            "Contact"
        ]
    )

    b = make_candidate(
        "menu-b",
        [
            "Admissions",
            "Research",
            "Departments"
        ]
    )

    containment = calculate_similarity(a, b)
    coverage = calculate_coverage(a, b)

    print("\n" + "=" * 70)
    print("TEST 6 — DUPLICATE VS SUBSET")
    print("=" * 70)

    print(
        "Containment :",
        round(containment, 3)
    )

    print(
        "Coverage    :",
        round(coverage, 3)
    )

    expected_containment = 1.0
    expected_coverage = 0.6

    passed = (
        abs(containment - expected_containment) < 0.001
        and
        abs(coverage - expected_coverage) < 0.001
    )

    print(
        "Expected containment :",
        expected_containment
    )

    print(
        "Expected coverage    :",
        expected_coverage
    )

    print(
        "RESULT     :",
        "PASS" if passed else "FAIL"
    )

    tests.append(passed)

    # --------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------

    print("\n" + "=" * 70)

    passed = sum(tests)
    total = len(tests)

    print(
        f"TOTAL: {passed}/{total} TESTS PASSED"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()