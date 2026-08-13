from bs4 import BeautifulSoup

from extractor.navigation_extractor import NavigationExtractor


TESTS = [

    (
        "TEST 1 — BASIC NAV",
        """
        <nav>
            <a href="/">Home</a>
            <a href="/academics">Academics</a>
            <a href="/research">Research</a>
        </nav>
        """,
        [
            "Home",
            "Academics",
            "Research"
        ]
    ),

    (
        "TEST 2 — ARIA NAVIGATION",
        """
        <nav aria-label="Main Navigation">
            <a href="/">Home</a>
            <a href="/departments">Departments</a>
            <a href="/contact">Contact</a>
        </nav>
        """,
        [
            "Home",
            "Departments",
            "Contact"
        ]
    ),

    (
        "TEST 3 — MAIN MENU CLASS",
        """
        <div class="main-menu">
            <a href="/">Home</a>
            <a href="/admissions">Admissions</a>
            <a href="/research">Research</a>
        </div>
        """,
        [
            "Home",
            "Admissions",
            "Research"
        ]
    ),

    (
        "TEST 4 — NESTED NAVIGATION",
        """
        <nav>
            <ul>
                <li>
                    <a href="/academics">Academics</a>
                    <ul>
                        <li>
                            <a href="/ug">Undergraduate</a>
                        </li>
                        <li>
                            <a href="/pg">Postgraduate</a>
                        </li>
                    </ul>
                </li>
            </ul>
        </nav>
        """,
        [
            "Academics",
            "Undergraduate",
            "Postgraduate"
        ]
    ),

    (
        "TEST 5 — SEPARATORS",
        """
        <nav>
            <a href="/">Home</a>
            <span>/</span>
            <a href="/academics">Academics</a>
            <span>/</span>
            <a href="/research">Research</a>
        </nav>
        """,
        [
            "Home",
            "Academics",
            "Research"
        ]
    ),

    (
        "TEST 6 — SKIP LINK",
        """
        <nav>
            <a href="#main">Skip to content</a>
            <a href="/">Home</a>
            <a href="/about">About</a>
        </nav>
        """,
        [
            "Home",
            "About"
        ]
    ),

    (
        "TEST 7 — NO NAVIGATION",
        """
        <main>
            <h1>Electrical Engineering</h1>
            <p>Power systems research.</p>
        </main>
        """,
        []
    ),

    (
        "TEST 8 — EMPTY HTML",
        "",
        []
    ),

]


def run_test(name, html, expected):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    extractor = NavigationExtractor(soup)

    actual = extractor.extract()

    print("\n" + "=" * 70)
    print(name)
    print("=" * 70)

    print("Extracted :", actual)
    print("Expected  :", expected)

    if actual == expected:
        print("RESULT    : PASS")
        return True

    print("RESULT    : FAIL")
    return False


def main():

    passed = 0

    for name, html, expected in TESTS:

        if run_test(
            name,
            html,
            expected
        ):
            passed += 1

    print("\n" + "=" * 70)
    print(
        f"TOTAL: {passed}/{len(TESTS)} TESTS PASSED"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()