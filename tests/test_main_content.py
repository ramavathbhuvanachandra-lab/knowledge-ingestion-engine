from bs4 import BeautifulSoup

from extractor.main_content_extractor import MainContentExtractor


def run_test(name, html):

    print("\n" + "=" * 60)
    print(name)
    print("=" * 60)

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    extractor = MainContentExtractor(soup)

    content = extractor.extract()

    print(content)

    print("\nContent length:", len(content))


# TEST 1 — <main>
run_test(
    "TEST 1 — MAIN TAG",
    """
    <html>
        <body>
            <header>Website Header</header>

            <nav>Home About Contact</nav>

            <main>
                <h1>Electrical Engineering</h1>
                <p>Our department focuses on power systems and embedded systems.</p>
                <p>Students can participate in research projects.</p>
            </main>

            <footer>Copyright 2026</footer>
        </body>
    </html>
    """
)


# TEST 2 — <article>
run_test(
    "TEST 2 — ARTICLE TAG",
    """
    <html>
        <body>
            <header>Header</header>
            <nav>Navigation Navigation Navigation</nav>

            <article>
                <h1>Research Areas</h1>
                <p>Power Systems</p>
                <p>VLSI</p>
                <p>Signal Processing</p>
            </article>

            <footer>Footer</footer>
        </body>
    </html>
    """
)


# TEST 3 — Common content class
run_test(
    "TEST 3 — CONTENT CLASS",
    """
    <html>
        <body>
            <header>Header</header>

            <div class="page-content">
                <h1>Admissions</h1>
                <p>Applications are accepted through the official portal.</p>
                <p>Applicants must satisfy the eligibility requirements.</p>
            </div>

            <footer>Footer</footer>
        </body>
    </html>
    """
)


# TEST 4 — No obvious container
run_test(
    "TEST 4 — NO OBVIOUS CONTAINER",
    """
    <html>
        <body>
            <div>
                <p>This is useful university information.</p>
                <p>The university offers undergraduate programs.</p>
                <p>Students can access academic resources.</p>
            </div>
        </body>
    </html>
    """
)


# TEST 5 — Boilerplate-heavy page
run_test(
    "TEST 5 — BOILERPLATE",
    """
    <html>
        <body>

            <header>
                University Header
                University Navigation
            </header>

            <nav>
                Home
                Admissions
                Departments
                Contact
            </nav>

            <div class="page-content">
                <h1>Computer Science Department</h1>
                <p>The department offers undergraduate and postgraduate programs.</p>
                <p>Research includes artificial intelligence and distributed systems.</p>
            </div>

            <aside>
                Related Links
                Popular Pages
            </aside>

            <footer>
                Copyright
                Privacy Policy
            </footer>

        </body>
    </html>
    """
)

# TEST 6 — Empty HTML
run_test(
    "TEST 6 — EMPTY HTML",
    """
    <html>
        <head></head>
        <body></body>
    </html>
    """
)


# TEST 7 — Only boilerplate
run_test(
    "TEST 7 — ONLY BOILERPLATE",
    """
    <html>
        <body>

            <header>Header</header>

            <nav>
                Home
                About
                Contact
            </nav>

            <footer>Copyright 2026</footer>

        </body>
    </html>
    """
)