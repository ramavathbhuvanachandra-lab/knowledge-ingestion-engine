from bs4 import BeautifulSoup

from extractor.html_extractor import HTMLExtractor


def run_test(name, html, expected):

    print("\n" + "=" * 70)
    print(name)
    print("=" * 70)

    extractor = HTMLExtractor(html)

    breadcrumbs = extractor.extract_breadcrumbs()

    print("Extracted :", breadcrumbs)
    print("Expected  :", expected)

    if breadcrumbs == expected:
        print("RESULT    : PASS")
    else:
        print("RESULT    : FAIL")


# TEST 1 — Standard semantic breadcrumb
run_test(
    "TEST 1 — NAV ARIA-LABEL",
    """
    <html>
        <body>

            <nav aria-label="breadcrumb">
                <ol>
                    <li><a href="/">Home</a></li>
                    <li><a href="/departments">Departments</a></li>
                    <li>Electrical Engineering</li>
                </ol>
            </nav>

        </body>
    </html>
    """,
    [
        "Home",
        "Departments",
        "Electrical Engineering"
    ]
)


# TEST 2 — Common breadcrumb class
run_test(
    "TEST 2 — BREADCRUMB CLASS",
    """
    <html>
        <body>

            <ol class="breadcrumb">
                <li><a href="/">Home</a></li>
                <li><a href="/academics">Academics</a></li>
                <li>Programs</li>
            </ol>

        </body>
    </html>
    """,
    [
        "Home",
        "Academics",
        "Programs"
    ]
)


# TEST 3 — Plural breadcrumbs class
run_test(
    "TEST 3 — BREADCRUMBS CLASS",
    """
    <html>
        <body>

            <div class="breadcrumbs">
                <a href="/">Home</a>
                <a href="/research">Research</a>
                <span>Research Areas</span>
            </div>

        </body>
    </html>
    """,
    [
        "Home",
        "Research",
        "Research Areas"
    ]
)


# TEST 4 — Custom breadcrumb class
run_test(
    "TEST 4 — CUSTOM BREADCRUMB CLASS",
    """
    <html>
        <body>

            <div class="site-breadcrumbs">
                <ul>
                    <li>Home</li>
                    <li>Departments</li>
                    <li>Faculty</li>
                </ul>
            </div>

        </body>
    </html>
    """,
    [
        "Home",
        "Departments",
        "Faculty"
    ]
)


# TEST 5 — Breadcrumb with separators
run_test(
    "TEST 5 — BREADCRUMB WITH SEPARATORS",
    """
    <html>
        <body>

            <nav aria-label="Breadcrumb">
                <ol>
                    <li><a href="/">Home</a></li>
                    <li> / </li>
                    <li><a href="/departments">Departments</a></li>
                    <li> / </li>
                    <li>Electrical Engineering</li>
                </ol>
            </nav>

        </body>
    </html>
    """,
    [
        "Home",

        "Departments",

        "Electrical Engineering"
    ]
)


# TEST 6 — No breadcrumbs
run_test(
    "TEST 6 — NO BREADCRUMBS",
    """
    <html>
        <body>

            <header>University Header</header>

            <main>
                <h1>Admissions</h1>
                <p>Admission information.</p>
            </main>

            <footer>University Footer</footer>

        </body>
    </html>
    """,
    []
)


# TEST 7 — Empty HTML
run_test(
    "TEST 7 — EMPTY HTML",
    "",
    []
)


# TEST 8 — Breadcrumb aria-label without nav
run_test(
    "TEST 8 — ARIA LABEL",
    """
    <html>
        <body>

            <div aria-label="breadcrumb">
                <a href="/">Home</a>
                <a href="/courses">Courses</a>
                <span>Computer Science</span>
            </div>

        </body>
    </html>
    """,
    [
        "Home",
        "Courses",
        "Computer Science"
    ]
)