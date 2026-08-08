from bs4 import BeautifulSoup

from analyzer.navigation_structure import (
    NavigationStructureAnalyzer
)


TESTS = [

    (
        "TEST 1 — PARENT",
        """
        <nav>
            <ul>
                <li>Academics</li>
            </ul>
        </nav>
        """,
        "nav",
        "ul",
        "direct_parent"
    ),

    (
        "TEST 2 — CHILD",
        """
        <nav>
            <ul>
                <li>Academics</li>
            </ul>
        </nav>
        """,
        "ul",
        "nav",
        "direct_child"
    ),

    (
        "TEST 3 — SIBLING",
        """
        <nav id="main">
            <a>Home</a>
        </nav>

        <nav id="footer">
            <a>Contact</a>
        </nav>
        """,
        "#main",
        "#footer",
        "sibling"
    ),

    (
        "TEST 4 — DEEP NESTING",
        """
        <nav>
            <ul>
                <li>
                    Academics
                    <ul>
                        <li>Undergraduate</li>
                    </ul>
                </li>
            </ul>
        </nav>
        """,
        "nav",
        "ul ul",
        "ancestor"
    ),

    (
        "TEST 5 — SAME ELEMENT",
        """
        <nav>
            <a>Home</a>
        </nav>
        """,
        "nav",
        "nav",
        "same"
    ),

    (
        "TEST 6 — UNRELATED",
        """
        <nav>
            <a>Home</a>
        </nav>

        <main>
            <p>Content</p>
        </main>
        """,
        "nav",
        "main",
        "sibling"
    ),
]


def run_test(
    name,
    html,
    selector_a,
    selector_b,
    expected
):

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

    analyzer = NavigationStructureAnalyzer()

    actual = analyzer.get_relationship(
        element_a,
        element_b
    )

    print("\n" + "=" * 70)
    print(name)
    print("=" * 70)

    print("A        :", selector_a)
    print("B        :", selector_b)
    print("Expected :", expected)
    print("Actual   :", actual)

    if actual == expected:

        print("RESULT   : PASS")
        return True

    print("RESULT   : FAIL")
    return False


def main():

    passed = 0

    for test in TESTS:

        if run_test(*test):

            passed += 1

    print("\n" + "=" * 70)

    print(
        f"TOTAL: {passed}/{len(TESTS)} TESTS PASSED"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()