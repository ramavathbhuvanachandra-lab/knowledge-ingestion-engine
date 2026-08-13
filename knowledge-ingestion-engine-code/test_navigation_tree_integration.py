from bs4 import BeautifulSoup

from extractor.navigation_extractor import NavigationExtractor
from analyzer.navigation_tree import NavigationTreeExtractor


def get_candidate(html, index=0):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    extractor = NavigationExtractor(soup)

    candidates = extractor.discover_candidates()

    assert candidates

    return candidates[index]


def build_tree(candidate, soup):

    element = soup.find(
        candidate.element_name,
        id=candidate.element_id
    )

    if element is None:

        # Fall back to matching by class.
        for candidate_element in soup.find_all(
            candidate.element_name
        ):

            candidate_classes = set(
                candidate.classes
            )

            element_classes = set(
                candidate_element.get(
                    "class",
                    []
                )
            )

            if candidate_classes == element_classes:
                element = candidate_element
                break

    extractor = NavigationTreeExtractor()

    return extractor.extract(
        element
    )


def test_1_flat_navigation():

    html = """
    <nav>
        <a href="/">Home</a>
        <a href="/academics">Academics</a>
        <a href="/research">Research</a>
    </nav>
    """

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    candidate = get_candidate(html)

    tree = build_tree(
        candidate,
        soup
    )

    assert candidate.links == [
        "Home",
        "Academics",
        "Research"
    ]

    assert [
        node.text
        for node in tree
    ] == [
        "Home",
        "Academics",
        "Research"
    ]


def test_2_nested_navigation():

    html = """
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
                    </li>

                    <li>
                        <a href="/research">
                            Research
                        </a>
                    </li>
                </ul>

            </li>

        </ul>
    </nav>
    """

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    candidate = get_candidate(html)

    tree = build_tree(
        candidate,
        soup
    )

    assert candidate.links == [
        "Academics",
        "Departments",
        "Research"
    ]

    assert tree[0].text == "Academics"

    assert [
        node.text
        for node in tree[0].children
    ] == [
        "Departments",
        "Research"
    ]


def test_3_deep_university_navigation():

    html = """
    <nav class="main-navigation">

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
                                <a href="/ee">
                                    Electrical Engineering
                                </a>

                                <ul>

                                    <li>
                                        <a href="/faculty">
                                            Faculty
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
    """

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    candidate = get_candidate(html)

    tree = build_tree(
        candidate,
        soup
    )

    academics = tree[0]

    departments = academics.children[0]

    electrical = departments.children[0]

    faculty = electrical.children[0]

    assert academics.text == "Academics"

    assert departments.text == "Departments"

    assert electrical.text == (
        "Electrical Engineering"
    )

    assert faculty.text == "Faculty"


def test_4_multiple_branches():

    html = """
    <nav class="main-navigation">

        <ul>

            <li>
                <a href="/academics">
                    Academics
                </a>

                <ul>
                    <li>
                        <a href="/courses">
                            Courses
                        </a>
                    </li>
                </ul>

            </li>

            <li>
                <a href="/research">
                    Research
                </a>

                <ul>
                    <li>
                        <a href="/labs">
                            Labs
                        </a>
                    </li>
                </ul>

            </li>

        </ul>

    </nav>
    """

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    candidate = get_candidate(html)

    tree = build_tree(
        candidate,
        soup
    )

    assert len(tree) == 2

    assert tree[0].text == "Academics"

    assert tree[0].children[0].text == "Courses"

    assert tree[1].text == "Research"

    assert tree[1].children[0].text == "Labs"


def test_5_href_preserved():

    html = """
    <nav>
        <a href="/admissions">
            Admissions
        </a>
        <a href="/research">
            Research
        </a>
    </nav>
    """

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    candidate = get_candidate(html)

    tree = build_tree(
        candidate,
        soup
    )

    assert tree[0].href == "/admissions"

    assert tree[1].href == "/research"


def test_6_skip_link_preserved_in_flat_links():

    html = """
    <nav>
        <a href="#main">
            Skip to content
        </a>

        <a href="/">
            Home
        </a>

        <a href="/research">
            Research
        </a>
    </nav>
    """

    candidate = get_candidate(html)

    assert candidate.links == [
        "Home",
        "Research"
    ]


def test_7_empty_navigation():

    html = """
    <nav></nav>
    """

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    extractor = NavigationExtractor(soup)

    candidates = extractor.discover_candidates()

    assert candidates == []


def test_8_dropdown():

    html = """
    <nav>

        <ul>

            <li>

                <a href="/services">
                    Services
                </a>

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

        </ul>

    </nav>
    """

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    candidate = get_candidate(html)

    tree = build_tree(
        candidate,
        soup
    )

    assert tree[0].text == "Services"

    assert [
        node.text
        for node in tree[0].children
    ] == [
        "Certificates",
        "Documents"
    ]


def test_9_tree_does_not_change_flat_links():

    html = """
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
                    </li>

                </ul>

            </li>

        </ul>

    </nav>
    """

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    candidate = get_candidate(html)

    original_links = list(
        candidate.links
    )

    tree = build_tree(
        candidate,
        soup
    )

    assert candidate.links == original_links

    assert tree[0].text == "Academics"

    assert tree[0].children[0].text == (
        "Departments"
    )


def test_10_empty_element_tree():

    extractor = NavigationTreeExtractor()

    assert extractor.extract(
        None
    ) == []


def test_11_wrapper_navigation():

    html = """
    <nav>

        <div class="wrapper">

            <a href="/">
                Home
            </a>

            <a href="/research">
                Research
            </a>

        </div>

    </nav>
    """

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    candidate = get_candidate(html)

    tree = build_tree(
        candidate,
        soup
    )

    assert [
        node.text
        for node in tree
    ] == [
        "Home",
        "Research"
    ]


def test_12_deep_four_levels():

    html = """
    <nav>

        <ul>

            <li>
                <a href="/one">
                    One
                </a>

                <ul>

                    <li>
                        <a href="/two">
                            Two
                        </a>

                        <ul>

                            <li>
                                <a href="/three">
                                    Three
                                </a>

                                <ul>

                                    <li>
                                        <a href="/four">
                                            Four
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
    """

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    candidate = get_candidate(html)

    tree = build_tree(
        candidate,
        soup
    )

    assert tree[0].text == "One"

    assert (
        tree[0]
        .children[0]
        .text
        == "Two"
    )

    assert (
        tree[0]
        .children[0]
        .children[0]
        .text
        == "Three"
    )

    assert (
        tree[0]
        .children[0]
        .children[0]
        .children[0]
        .text
        == "Four"
    )


def test_13_government_navigation():

    html = """
    <nav id="main-menu">

        <ul>

            <li>
                <a href="/ministries">
                    Ministries
                </a>
            </li>

            <li>

                <a href="/services">
                    Services
                </a>

                <ul>

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

        </ul>

    </nav>
    """

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    candidate = get_candidate(html)

    tree = build_tree(
        candidate,
        soup
    )

    assert tree[0].text == "Ministries"

    assert tree[1].text == "Services"

    assert [
        node.text
        for node in tree[1].children
    ] == [
        "Certificates",
        "Documents"
    ]


def test_14_sibling_order():

    html = """
    <nav>

        <a href="/one">One</a>
        <a href="/two">Two</a>
        <a href="/three">Three</a>
        <a href="/four">Four</a>

    </nav>
    """

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    candidate = get_candidate(html)

    tree = build_tree(
        candidate,
        soup
    )

    assert [
        node.text
        for node in tree
    ] == [
        "One",
        "Two",
        "Three",
        "Four"
    ]


def test_15_no_cross_branch_contamination():

    html = """
    <nav>

        <ul>

            <li>
                <a href="/academics">
                    Academics
                </a>

                <ul>
                    <li>
                        <a href="/courses">
                            Courses
                        </a>
                    </li>
                </ul>

            </li>

            <li>
                <a href="/research">
                    Research
                </a>

                <ul>
                    <li>
                        <a href="/labs">
                            Labs
                        </a>
                    </li>
                </ul>

            </li>

        </ul>

    </nav>
    """

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    candidate = get_candidate(html)

    tree = build_tree(
        candidate,
        soup
    )

    assert [
        child.text
        for child in tree[0].children
    ] == [
        "Courses"
    ]

    assert [
        child.text
        for child in tree[1].children
    ] == [
        "Labs"
    ]


def run():

    tests = [
        test_1_flat_navigation,
        test_2_nested_navigation,
        test_3_deep_university_navigation,
        test_4_multiple_branches,
        test_5_href_preserved,
        test_6_skip_link_preserved_in_flat_links,
        test_7_empty_navigation,
        test_8_dropdown,
        test_9_tree_does_not_change_flat_links,
        test_10_empty_element_tree,
        test_11_wrapper_navigation,
        test_12_deep_four_levels,
        test_13_government_navigation,
        test_14_sibling_order,
        test_15_no_cross_branch_contamination,
    ]

    passed = 0

    for index, test in enumerate(
        tests,
        start=1
    ):

        print("\n" + "=" * 70)

        print(
            f"TEST {index} — "
            f"{test.__name__}"
        )

        print("=" * 70)

        try:

            test()

            print(
                "RESULT : PASS"
            )

            passed += 1

        except Exception as error:

            print(
                "RESULT : FAIL"
            )

            print(
                "ERROR  :",
                type(error).__name__
            )

            print(
                "MESSAGE:",
                str(error)
            )

    print("\n" + "=" * 70)

    print(
        f"TOTAL: {passed}/{len(tests)} TESTS PASSED"
    )

    print("=" * 70)


if __name__ == "__main__":
    run()