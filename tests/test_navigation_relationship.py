from analyzer.navigation_relationship import (
    determine_relationship,
)


def run_test(
    name,
    links_a,
    links_b,
    expected
):

    result = determine_relationship(
        links_a,
        links_b
    )

    passed = result == expected

    print("\n" + "=" * 70)
    print(name)
    print("=" * 70)

    print("A:", links_a)
    print("B:", links_b)

    print("Expected :", expected)
    print("Actual   :", result)

    print(
        "RESULT   :",
        "PASS" if passed else "FAIL"
    )

    return passed


def main():

    results = []

    # ---------------------------------------------
    # TEST 1 — Exact duplicate
    # ---------------------------------------------

    results.append(
        run_test(
            "TEST 1 — EXACT DUPLICATE",

            [
                "Home",
                "Admissions",
                "Research",
                "Contact"
            ],

            [
                "Home",
                "Admissions",
                "Research",
                "Contact"
            ],

            "duplicate"
        )
    )

    # ---------------------------------------------
    # TEST 2 — Subset
    # ---------------------------------------------

    results.append(
        run_test(
            "TEST 2 — SUBSET",

            [
                "Home",
                "Admissions",
                "Research",
                "Departments",
                "Contact"
            ],

            [
                "Admissions",
                "Research",
                "Departments"
            ],

            "subset"
        )
    )

    # ---------------------------------------------
    # TEST 3 — Partial overlap
    # ---------------------------------------------

    results.append(
        run_test(
            "TEST 3 — OVERLAP",

            [
                "Home",
                "Admissions",
                "Research",
                "Departments"
            ],

            [
                "Admissions",
                "Research",
                "Library",
                "Hostel"
            ],

            "overlap"
        )
    )

    # ---------------------------------------------
    # TEST 4 — Completely unrelated
    # ---------------------------------------------

    results.append(
        run_test(
            "TEST 4 — UNRELATED",

            [
                "Home",
                "Admissions",
                "Research"
            ],

            [
                "RTI",
                "Feedback",
                "Contact"
            ],

            "unrelated"
        )
    )

    # ---------------------------------------------
    # TEST 5 — Empty
    # ---------------------------------------------

    results.append(
        run_test(
            "TEST 5 — EMPTY",

            [],

            [
                "Home",
                "Research"
            ],

            "unrelated"
        )
    )

    # ---------------------------------------------
    # FINAL
    # ---------------------------------------------

    passed = sum(results)
    total = len(results)

    print("\n" + "=" * 70)
    print(
        f"TOTAL: {passed}/{total} TESTS PASSED"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()