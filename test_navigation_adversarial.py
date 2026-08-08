import asyncio

from bs4 import BeautifulSoup

from extractor.navigation_extractor import NavigationExtractor
from analyzer.navigation_classifier import NavigationClassifier
from analyzer.navigation_candidate_filter import (
    NavigationCandidateFilter,
)
from analyzer.navigation_redundancy import (
    NavigationRedundancyAnalyzer,
)
from analyzer.navigation_redundancy_decision import (
    NavigationRedundancyDecision,
)


TESTS = [

    # ==========================================================
    # 1 — BOOTSTRAP MEGA MENU
    # ==========================================================

    (
        "TEST 1 — BOOTSTRAP MEGA MENU",
        """
        <nav class="navbar">
            <ul class="navbar-nav">
                <li>
                    <a href="/academics">Academics</a>

                    <ul class="dropdown-menu">
                        <li>
                            <a href="/departments">Departments</a>
                        </li>
                        <li>
                            <a href="/faculty">Faculty</a>
                        </li>
                        <li>
                            <a href="/courses">Courses</a>
                        </li>
                    </ul>
                </li>

                <li>
                    <a href="/research">Research</a>
                </li>

                <li>
                    <a href="/contact">Contact</a>
                </li>
            </ul>
        </nav>
        """,
    ),

    # ==========================================================
    # 2 — DRUPAL STYLE
    # ==========================================================

    (
        "TEST 2 — DRUPAL STYLE MENU",
        """
        <nav aria-label="Main navigation">
            <ul class="menu">
                <li class="expanded">
                    <a href="/admissions">Admissions</a>

                    <ul class="menu">
                        <li>
                            <a href="/ug">Undergraduate</a>
                        </li>
                        <li>
                            <a href="/pg">Postgraduate</a>
                        </li>
                    </ul>
                </li>

                <li>
                    <a href="/research">Research</a>
                </li>
            </ul>
        </nav>
        """,
    ),

    # ==========================================================
    # 3 — WORDPRESS STYLE
    # ==========================================================

    (
        "TEST 3 — WORDPRESS STYLE MENU",
        """
        <nav id="site-navigation">
            <ul id="primary-menu" class="menu">
                <li class="menu-item">
                    <a href="/">Home</a>
                </li>

                <li class="menu-item">
                    <a href="/academics">Academics</a>

                    <ul class="sub-menu">
                        <li class="menu-item">
                            <a href="/departments">Departments</a>
                        </li>

                        <li class="menu-item">
                            <a href="/programs">Programs</a>
                        </li>
                    </ul>
                </li>

                <li class="menu-item">
                    <a href="/research">Research</a>
                </li>
            </ul>
        </nav>
        """,
    ),

    # ==========================================================
    # 4 — DESKTOP + MOBILE DUPLICATE
    # ==========================================================

    (
        "TEST 4 — DESKTOP MOBILE DUPLICATE",
        """
        <nav class="desktop-menu">
            <a href="/">Home</a>
            <a href="/admissions">Admissions</a>
            <a href="/research">Research</a>
        </nav>

        <nav class="mobile-menu">
            <a href="/">Home</a>
            <a href="/admissions">Admissions</a>
            <a href="/research">Research</a>
        </nav>
        """,
    ),

    # ==========================================================
    # 5 — PRIMARY + SIDEBAR
    # ==========================================================

    (
        "TEST 5 — PRIMARY + SIDEBAR",
        """
        <nav class="primary-navigation">
            <a href="/">Home</a>
            <a href="/academics">Academics</a>
            <a href="/research">Research</a>
            <a href="/contact">Contact</a>
        </nav>

        <aside class="side-menu">
            <a href="/academics">Academics</a>
            <a href="/research">Research</a>
            <a href="/departments">Departments</a>
        </aside>
        """,
    ),

    # ==========================================================
    # 6 — FOOTER DUPLICATION
    # ==========================================================

    (
        "TEST 6 — FOOTER DUPLICATION",
        """
        <nav class="primary-navigation">
            <a href="/">Home</a>
            <a href="/academics">Academics</a>
            <a href="/research">Research</a>
            <a href="/contact">Contact</a>
        </nav>

        <footer>
            <nav class="footer-navigation">
                <a href="/">Home</a>
                <a href="/academics">Academics</a>
                <a href="/research">Research</a>
                <a href="/contact">Contact</a>
            </nav>
        </footer>
        """,
    ),

    # ==========================================================
    # 7 — THREE LEVEL UNIVERSITY NAVIGATION
    # ==========================================================

    (
        "TEST 7 — THREE LEVEL UNIVERSITY NAVIGATION",
        """
        <nav class="main-navigation">

            <ul>
                <li>
                    <a href="/academics">Academics</a>

                    <ul>
                        <li>
                            <a href="/departments">
                                Departments
                            </a>

                            <ul>
                                <li>
                                    <a href="/ee">
                                        Electrical Engineering
                                    </a>
                                </li>

                                <li>
                                    <a href="/cse">
                                        Computer Science
                                    </a>
                                </li>
                            </ul>

                        </li>
                    </ul>

                </li>
            </ul>

        </nav>
        """,
    ),

    # ==========================================================
    # 8 — GOVERNMENT PORTAL
    # ==========================================================

    (
        "TEST 8 — GOVERNMENT PORTAL",
        """
        <nav id="main-menu">

            <ul>
                <li>
                    <a href="/ministries">Ministries</a>
                </li>

                <li>
                    <a href="/services">Services</a>

                    <ul class="dropdown-menu">
                        <li>
                            <a href="/certificates">
                                Certificates
                            </a>
                        </li>

                        <li>
                            <a href="/documents">
                                Documents
                            </a>
                        </li>
                    </ul>

                </li>

                <li>
                    <a href="/citizens">
                        Citizen Services
                    </a>
                </li>
            </ul>

        </nav>
        """,
    ),

    # ==========================================================
    # 9 — SAME LINKS DIFFERENT PURPOSE
    # ==========================================================

    (
        "TEST 9 — SAME LINKS DIFFERENT PURPOSE",
        """
        <nav class="primary-navigation">
            <a href="/">Home</a>
            <a href="/admissions">Admissions</a>
            <a href="/academics">Academics</a>
        </nav>

        <section class="quick-links">
            <h2>Quick Links</h2>

            <a href="/">Home</a>
            <a href="/admissions">Admissions</a>
            <a href="/academics">Academics</a>
        </section>
        """,
    ),

    # ==========================================================
    # 10 — ACCESSIBILITY DUPLICATION
    # ==========================================================

    (
        "TEST 10 — ACCESSIBILITY DUPLICATION",
        """
        <nav aria-label="Main navigation">
            <a href="/">Home</a>
            <a href="/academics">Academics</a>
            <a href="/research">Research</a>
        </nav>

        <div class="screen-reader-navigation">
            <nav aria-label="Accessible navigation">
                <a href="/">Home</a>
                <a href="/academics">Academics</a>
                <a href="/research">Research</a>
            </nav>
        </div>
        """,
    ),

    # ==========================================================
    # 11 — HIDDEN MOBILE MENU
    # ==========================================================

    (
        "TEST 11 — HIDDEN MOBILE MENU",
        """
        <nav class="main-navigation">
            <a href="/">Home</a>
            <a href="/admissions">Admissions</a>
            <a href="/research">Research</a>
        </nav>

        <nav class="mobile-navigation" style="display:none">
            <a href="/">Home</a>
            <a href="/admissions">Admissions</a>
            <a href="/research">Research</a>
        </nav>
        """,
    ),

    # ==========================================================
    # 12 — RANDOM LINK CONTAINER
    # ==========================================================

    (
        "TEST 12 — RANDOM LINK CONTAINER",
        """
        <main>

            <div class="article">
                <h1>Research</h1>

                <p>
                    Read more information:
                </p>

                <div class="random-wrapper">
                    <a href="/research/a">Research A</a>
                    <a href="/research/b">Research B</a>
                    <a href="/research/c">Research C</a>
                </div>

            </div>

        </main>
        """,
    ),

    # ==========================================================
    # 13 — LARGE SIDEBAR
    # ==========================================================

    (
        "TEST 13 — LARGE SIDEBAR",
        """
        <aside class="side-menu">

            <ul>
                <li><a href="/about">About</a></li>
                <li><a href="/academics">Academics</a></li>
                <li><a href="/research">Research</a></li>
                <li><a href="/departments">Departments</a></li>
                <li><a href="/faculty">Faculty</a></li>
                <li><a href="/students">Students</a></li>
                <li><a href="/hostel">Hostel</a></li>
                <li><a href="/library">Library</a></li>
            </ul>

        </aside>
        """,
    ),

    # ==========================================================
    # 14 — EMPTY NAV
    # ==========================================================

    (
        "TEST 14 — EMPTY NAV",
        """
        <nav></nav>
        """,
    ),

    # ==========================================================
    # 15 — LINKS WITHOUT NAV
    # ==========================================================

    (
        "TEST 15 — LINKS WITHOUT NAV",
        """
        <main>

            <article>
                <h1>Important Links</h1>

                <a href="/one">One</a>
                <a href="/two">Two</a>
                <a href="/three">Three</a>
            </article>

        </main>
        """,
    ),

    # ==========================================================
    # 16 — DEEP NESTING
    # ==========================================================

    (
        "TEST 16 — DEEP NESTING",
        """
        <nav>

            <ul>
                <li>
                    <a href="/academics">
                        Academics
                    </a>

                    <ul>
                        <li>
                            <a href="/departments">
                                Departments
                            </a>

                            <ul>
                                <li>
                                    <a href="/engineering">
                                        Engineering
                                    </a>

                                    <ul>
                                        <li>
                                            <a href="/ee">
                                                Electrical Engineering
                                            </a>
                                        </li>
                                    </ul>

                                </li>
                            </ul>

                        </li>
                    </ul>

                </li>
            </ul>

        </nav>
        """,
    ),
]


def analyse_html(
    html,
):
    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    extractor = NavigationExtractor(
        soup,
    )

    candidates = extractor.discover_candidates()

    classifier = NavigationClassifier()

    candidates = classifier.classify(
        candidates,
    )

    filter_engine = NavigationCandidateFilter()

    candidates = filter_engine.filter(
        candidates,
    )

    return soup, candidates


def run_test(
    name,
    html,
):
    print("\n" + "=" * 75)
    print(name)
    print("=" * 75)

    try:

        soup, candidates = analyse_html(
            html,
        )

        print(
            "CANDIDATES :",
            len(candidates),
        )

        for index, candidate in enumerate(
            candidates,
            start=1,
        ):

            print(
                f"\nCandidate {index}"
            )

            print(
                "  Element :",
                candidate.element_name,
            )

            print(
                "  ID      :",
                candidate.element_id,
            )

            print(
                "  Classes :",
                candidate.classes,
            )

            print(
                "  Type    :",
                candidate.navigation_type,
            )

            print(
                "  Score   :",
                candidate.score,
            )

            print(
                "  Links   :",
                candidate.link_count,
            )

        # --------------------------------------------------
        # Pairwise redundancy
        # --------------------------------------------------

        redundancy = (
            NavigationRedundancyAnalyzer()
        )

        decision = (
            NavigationRedundancyDecision()
        )

        redundant = 0
        keep_both = 0

        for i in range(
            len(candidates)
        ):

            for j in range(
                i + 1,
                len(candidates)
            ):

                result = redundancy.analyze(
                    candidates[i],
                    candidates[j],
                )

                final_decision = decision.decide(
                    result,
                    candidates[i],
                    candidates[j],
                )

                if (
                    final_decision["decision"]
                    == "redundant"
                ):
                    redundant += 1

                elif (
                    final_decision["decision"]
                    == "keep_both"
                ):
                    keep_both += 1

        print(
            "\nRedundant pairs :",
            redundant,
        )

        print(
            "Kept pairs      :",
            keep_both,
        )

        print(
            "RESULT          : PASS"
        )

        return True

    except Exception as error:

        print(
            "\nRESULT          : FAIL"
        )

        print(
            "ERROR           :",
            type(error).__name__,
        )

        print(
            "MESSAGE         :",
            str(error),
        )

        return False


def main():

    passed = 0

    for name, html in TESTS:

        if run_test(
            name,
            html,
        ):
            passed += 1

    print("\n" + "=" * 75)

    print(
        f"TOTAL: {passed}/{len(TESTS)} TESTS COMPLETED"
    )

    print("=" * 75)


if __name__ == "__main__":
    asyncio.run(
        asyncio.sleep(0)
    )

    main()
import asyncio

from bs4 import BeautifulSoup

from extractor.navigation_extractor import NavigationExtractor
from analyzer.navigation_classifier import NavigationClassifier
from analyzer.navigation_candidate_filter import (
    NavigationCandidateFilter,
)
from analyzer.navigation_redundancy import (
    NavigationRedundancyAnalyzer,
)
from analyzer.navigation_redundancy_decision import (
    NavigationRedundancyDecision,
)


TESTS = [

    # ==========================================================
    # 1 — BOOTSTRAP MEGA MENU
    # ==========================================================

    (
        "TEST 1 — BOOTSTRAP MEGA MENU",
        """
        <nav class="navbar">
            <ul class="navbar-nav">
                <li>
                    <a href="/academics">Academics</a>

                    <ul class="dropdown-menu">
                        <li>
                            <a href="/departments">Departments</a>
                        </li>
                        <li>
                            <a href="/faculty">Faculty</a>
                        </li>
                        <li>
                            <a href="/courses">Courses</a>
                        </li>
                    </ul>
                </li>

                <li>
                    <a href="/research">Research</a>
                </li>

                <li>
                    <a href="/contact">Contact</a>
                </li>
            </ul>
        </nav>
        """,
    ),

    # ==========================================================
    # 2 — DRUPAL STYLE
    # ==========================================================

    (
        "TEST 2 — DRUPAL STYLE MENU",
        """
        <nav aria-label="Main navigation">
            <ul class="menu">
                <li class="expanded">
                    <a href="/admissions">Admissions</a>

                    <ul class="menu">
                        <li>
                            <a href="/ug">Undergraduate</a>
                        </li>
                        <li>
                            <a href="/pg">Postgraduate</a>
                        </li>
                    </ul>
                </li>

                <li>
                    <a href="/research">Research</a>
                </li>
            </ul>
        </nav>
        """,
    ),

    # ==========================================================
    # 3 — WORDPRESS STYLE
    # ==========================================================

    (
        "TEST 3 — WORDPRESS STYLE MENU",
        """
        <nav id="site-navigation">
            <ul id="primary-menu" class="menu">
                <li class="menu-item">
                    <a href="/">Home</a>
                </li>

                <li class="menu-item">
                    <a href="/academics">Academics</a>

                    <ul class="sub-menu">
                        <li class="menu-item">
                            <a href="/departments">Departments</a>
                        </li>

                        <li class="menu-item">
                            <a href="/programs">Programs</a>
                        </li>
                    </ul>
                </li>

                <li class="menu-item">
                    <a href="/research">Research</a>
                </li>
            </ul>
        </nav>
        """,
    ),

    # ==========================================================
    # 4 — DESKTOP + MOBILE DUPLICATE
    # ==========================================================

    (
        "TEST 4 — DESKTOP MOBILE DUPLICATE",
        """
        <nav class="desktop-menu">
            <a href="/">Home</a>
            <a href="/admissions">Admissions</a>
            <a href="/research">Research</a>
        </nav>

        <nav class="mobile-menu">
            <a href="/">Home</a>
            <a href="/admissions">Admissions</a>
            <a href="/research">Research</a>
        </nav>
        """,
    ),

    # ==========================================================
    # 5 — PRIMARY + SIDEBAR
    # ==========================================================

    (
        "TEST 5 — PRIMARY + SIDEBAR",
        """
        <nav class="primary-navigation">
            <a href="/">Home</a>
            <a href="/academics">Academics</a>
            <a href="/research">Research</a>
            <a href="/contact">Contact</a>
        </nav>

        <aside class="side-menu">
            <a href="/academics">Academics</a>
            <a href="/research">Research</a>
            <a href="/departments">Departments</a>
        </aside>
        """,
    ),

    # ==========================================================
    # 6 — FOOTER DUPLICATION
    # ==========================================================

    (
        "TEST 6 — FOOTER DUPLICATION",
        """
        <nav class="primary-navigation">
            <a href="/">Home</a>
            <a href="/academics">Academics</a>
            <a href="/research">Research</a>
            <a href="/contact">Contact</a>
        </nav>

        <footer>
            <nav class="footer-navigation">
                <a href="/">Home</a>
                <a href="/academics">Academics</a>
                <a href="/research">Research</a>
                <a href="/contact">Contact</a>
            </nav>
        </footer>
        """,
    ),

    # ==========================================================
    # 7 — THREE LEVEL UNIVERSITY NAVIGATION
    # ==========================================================

    (
        "TEST 7 — THREE LEVEL UNIVERSITY NAVIGATION",
        """
        <nav class="main-navigation">

            <ul>
                <li>
                    <a href="/academics">Academics</a>

                    <ul>
                        <li>
                            <a href="/departments">
                                Departments
                            </a>

                            <ul>
                                <li>
                                    <a href="/ee">
                                        Electrical Engineering
                                    </a>
                                </li>

                                <li>
                                    <a href="/cse">
                                        Computer Science
                                    </a>
                                </li>
                            </ul>

                        </li>
                    </ul>

                </li>
            </ul>

        </nav>
        """,
    ),

    # ==========================================================
    # 8 — GOVERNMENT PORTAL
    # ==========================================================

    (
        "TEST 8 — GOVERNMENT PORTAL",
        """
        <nav id="main-menu">

            <ul>
                <li>
                    <a href="/ministries">Ministries</a>
                </li>

                <li>
                    <a href="/services">Services</a>

                    <ul class="dropdown-menu">
                        <li>
                            <a href="/certificates">
                                Certificates
                            </a>
                        </li>

                        <li>
                            <a href="/documents">
                                Documents
                            </a>
                        </li>
                    </ul>

                </li>

                <li>
                    <a href="/citizens">
                        Citizen Services
                    </a>
                </li>
            </ul>

        </nav>
        """,
    ),

    # ==========================================================
    # 9 — SAME LINKS DIFFERENT PURPOSE
    # ==========================================================

    (
        "TEST 9 — SAME LINKS DIFFERENT PURPOSE",
        """
        <nav class="primary-navigation">
            <a href="/">Home</a>
            <a href="/admissions">Admissions</a>
            <a href="/academics">Academics</a>
        </nav>

        <section class="quick-links">
            <h2>Quick Links</h2>

            <a href="/">Home</a>
            <a href="/admissions">Admissions</a>
            <a href="/academics">Academics</a>
        </section>
        """,
    ),

    # ==========================================================
    # 10 — ACCESSIBILITY DUPLICATION
    # ==========================================================

    (
        "TEST 10 — ACCESSIBILITY DUPLICATION",
        """
        <nav aria-label="Main navigation">
            <a href="/">Home</a>
            <a href="/academics">Academics</a>
            <a href="/research">Research</a>
        </nav>

        <div class="screen-reader-navigation">
            <nav aria-label="Accessible navigation">
                <a href="/">Home</a>
                <a href="/academics">Academics</a>
                <a href="/research">Research</a>
            </nav>
        </div>
        """,
    ),

    # ==========================================================
    # 11 — HIDDEN MOBILE MENU
    # ==========================================================

    (
        "TEST 11 — HIDDEN MOBILE MENU",
        """
        <nav class="main-navigation">
            <a href="/">Home</a>
            <a href="/admissions">Admissions</a>
            <a href="/research">Research</a>
        </nav>

        <nav class="mobile-navigation" style="display:none">
            <a href="/">Home</a>
            <a href="/admissions">Admissions</a>
            <a href="/research">Research</a>
        </nav>
        """,
    ),

    # ==========================================================
    # 12 — RANDOM LINK CONTAINER
    # ==========================================================

    (
        "TEST 12 — RANDOM LINK CONTAINER",
        """
        <main>

            <div class="article">
                <h1>Research</h1>

                <p>
                    Read more information:
                </p>

                <div class="random-wrapper">
                    <a href="/research/a">Research A</a>
                    <a href="/research/b">Research B</a>
                    <a href="/research/c">Research C</a>
                </div>

            </div>

        </main>
        """,
    ),

    # ==========================================================
    # 13 — LARGE SIDEBAR
    # ==========================================================

    (
        "TEST 13 — LARGE SIDEBAR",
        """
        <aside class="side-menu">

            <ul>
                <li><a href="/about">About</a></li>
                <li><a href="/academics">Academics</a></li>
                <li><a href="/research">Research</a></li>
                <li><a href="/departments">Departments</a></li>
                <li><a href="/faculty">Faculty</a></li>
                <li><a href="/students">Students</a></li>
                <li><a href="/hostel">Hostel</a></li>
                <li><a href="/library">Library</a></li>
            </ul>

        </aside>
        """,
    ),

    # ==========================================================
    # 14 — EMPTY NAV
    # ==========================================================

    (
        "TEST 14 — EMPTY NAV",
        """
        <nav></nav>
        """,
    ),

    # ==========================================================
    # 15 — LINKS WITHOUT NAV
    # ==========================================================

    (
        "TEST 15 — LINKS WITHOUT NAV",
        """
        <main>

            <article>
                <h1>Important Links</h1>

                <a href="/one">One</a>
                <a href="/two">Two</a>
                <a href="/three">Three</a>
            </article>

        </main>
        """,
    ),

    # ==========================================================
    # 16 — DEEP NESTING
    # ==========================================================

    (
        "TEST 16 — DEEP NESTING",
        """
        <nav>

            <ul>
                <li>
                    <a href="/academics">
                        Academics
                    </a>

                    <ul>
                        <li>
                            <a href="/departments">
                                Departments
                            </a>

                            <ul>
                                <li>
                                    <a href="/engineering">
                                        Engineering
                                    </a>

                                    <ul>
                                        <li>
                                            <a href="/ee">
                                                Electrical Engineering
                                            </a>
                                        </li>
                                    </ul>

                                </li>
                            </ul>

                        </li>
                    </ul>

                </li>
            </ul>

        </nav>
        """,
    ),
]


def analyse_html(
    html,
):
    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    extractor = NavigationExtractor(
        soup,
    )

    candidates = extractor.discover_candidates()

    classifier = NavigationClassifier()

    candidates = classifier.classify(
        candidates,
    )

    filter_engine = NavigationCandidateFilter()

    candidates = filter_engine.filter(
        candidates,
    )

    return soup, candidates


def run_test(
    name,
    html,
):
    print("\n" + "=" * 75)
    print(name)
    print("=" * 75)

    try:

        soup, candidates = analyse_html(
            html,
        )

        print(
            "CANDIDATES :",
            len(candidates),
        )

        for index, candidate in enumerate(
            candidates,
            start=1,
        ):

            print(
                f"\nCandidate {index}"
            )

            print(
                "  Element :",
                candidate.element_name,
            )

            print(
                "  ID      :",
                candidate.element_id,
            )

            print(
                "  Classes :",
                candidate.classes,
            )

            print(
                "  Type    :",
                candidate.navigation_type,
            )

            print(
                "  Score   :",
                candidate.score,
            )

            print(
                "  Links   :",
                candidate.link_count,
            )

        # --------------------------------------------------
        # Pairwise redundancy
        # --------------------------------------------------

        redundancy = (
            NavigationRedundancyAnalyzer()
        )

        decision = (
            NavigationRedundancyDecision()
        )

        redundant = 0
        keep_both = 0

        for i in range(
            len(candidates)
        ):

            for j in range(
                i + 1,
                len(candidates)
            ):

                result = redundancy.analyze(
                    candidates[i],
                    candidates[j],
                )

                final_decision = decision.decide(
                    result,
                    candidates[i],
                    candidates[j],
                )

                if (
                    final_decision["decision"]
                    == "redundant"
                ):
                    redundant += 1

                elif (
                    final_decision["decision"]
                    == "keep_both"
                ):
                    keep_both += 1

        print(
            "\nRedundant pairs :",
            redundant,
        )

        print(
            "Kept pairs      :",
            keep_both,
        )

        print(
            "RESULT          : PASS"
        )

        return True

    except Exception as error:

        print(
            "\nRESULT          : FAIL"
        )

        print(
            "ERROR           :",
            type(error).__name__,
        )

        print(
            "MESSAGE         :",
            str(error),
        )

        return False


def main():

    passed = 0

    for name, html in TESTS:

        if run_test(
            name,
            html,
        ):
            passed += 1

    print("\n" + "=" * 75)

    print(
        f"TOTAL: {passed}/{len(TESTS)} TESTS COMPLETED"
    )

    print("=" * 75)


if __name__ == "__main__":
    asyncio.run(
        asyncio.sleep(0)
    )

    main()
