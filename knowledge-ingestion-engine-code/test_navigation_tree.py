from bs4 import BeautifulSoup

from analyzer.navigation_tree import (
    NavigationTreeExtractor,
)


def print_tree(
    nodes,
    level=0
):

    for node in nodes:

        print(
            "  " * level
            + f"- {node.text}"
            + (
                f" [{node.href}]"
                if node.href
                else ""
            )
        )

        print_tree(
            node.children,
            level + 1
        )


def extract(
    html
):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    element = soup.find("nav")

    extractor = NavigationTreeExtractor()

    return extractor.extract(
        element
    )


def test_1_flat_menu():

    nodes = extract(
        """
        <nav>
            <a href="/">Home</a>
            <a href="/academics">Academics</a>
            <a href="/research">Research</a>
        </nav>
        """
    )

    assert [
        node.text
        for node in nodes
    ] == [
        "Home",
        "Academics",
        "Research"
    ]


def test_2_one_level():

    nodes = extract(
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
    )

    assert len(nodes) == 1

    assert nodes[0].text == "Academics"

    assert [
        child.text
        for child in nodes[0].children
    ] == [
        "Departments",
        "Research"
    ]


def test_3_two_level():

    nodes = extract(
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
        """
    )

    assert nodes[0].text == "Academics"

    departments = nodes[0].children[0]

    assert departments.text == "Departments"

    assert [
        child.text
        for child in departments.children
    ] == [
        "Electrical Engineering",
        "Computer Science"
    ]


def test_4_multiple_branches():

    nodes = extract(
        """
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
    )

    assert [
        node.text
        for node in nodes
    ] == [
        "Academics",
        "Research"
    ]

    assert nodes[0].children[0].text == "Courses"

    assert nodes[1].children[0].text == "Labs"


def test_5_href():

    nodes = extract(
        """
        <nav>
            <a href="/home">
                Home
            </a>
        </nav>
        """
    )

    assert nodes[0].href == "/home"


def test_6_skip_link():

    nodes = extract(
        """
        <nav>
            <a href="#main">
                Skip to content
            </a>

            <a href="/">
                Home
            </a>
        </nav>
        """
    )

    assert [
        node.text
        for node in nodes
    ] == [
        "Home"
    ]


def test_7_empty_nav():

    nodes = extract(
        """
        <nav></nav>
        """
    )

    assert nodes == []


def test_8_empty_text():

    nodes = extract(
        """
        <nav>
            <a href="/one"></a>
            <a href="/two">
                Two
            </a>
        </nav>
        """
    )

    assert [
        node.text
        for node in nodes
    ] == [
        "Two"
    ]


def test_9_separators():

    nodes = extract(
        """
        <nav>

            <a href="/">Home</a>

            <span>/</span>

            <a href="/academics">
                Academics
            </a>

            <span>/</span>

            <a href="/research">
                Research
            </a>

        </nav>
        """
    )

    assert [
        node.text
        for node in nodes
    ] == [
        "Home",
        "Academics",
        "Research"
    ]


def test_10_university_navigation():

    nodes = extract(
        """
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
                                </li>

                                <li>
                                    <a href="/cse">
                                        Computer Science
                                    </a>
                                </li>

                            </ul>

                        </li>

                        <li>
                            <a href="/courses">
                                Courses
                            </a>
                        </li>

                    </ul>

                </li>

                <li>
                    <a href="/admissions">
                        Admissions
                    </a>
                </li>

            </ul>

        </nav>
        """
    )

    assert [
        node.text
        for node in nodes
    ] == [
        "Academics",
        "Admissions"
    ]

    assert nodes[0].children[0].text == (
        "Departments"
    )

    assert (
        nodes[0]
        .children[0]
        .children[0]
        .text
        == "Electrical Engineering"
    )


def test_11_dropdown():

    nodes = extract(
        """
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
    )

    assert nodes[0].text == "Services"

    assert [
        child.text
        for child in nodes[0].children
    ] == [
        "Certificates",
        "Documents"
    ]


def test_12_deep_nesting():

    nodes = extract(
        """
        <nav>

            <ul>

                <li>
                    <a href="/one">One</a>

                    <ul>

                        <li>
                            <a href="/two">Two</a>

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
    )

    assert (
        nodes[0]
        .children[0]
        .children[0]
        .children[0]
        .text
        == "Four"
    )


def test_13_non_nav_element():

    soup = BeautifulSoup(
        """
        <div>
            <a href="/one">One</a>
            <a href="/two">Two</a>
        </div>
        """,
        "html.parser"
    )

    extractor = NavigationTreeExtractor()

    nodes = extractor.extract(
        soup.div
    )

    assert [
        node.text
        for node in nodes
    ] == [
        "One",
        "Two"
    ]


def test_14_wrapper_elements():

    nodes = extract(
        """
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
    )

    assert [
        node.text
        for node in nodes
    ] == [
        "Home",
        "Research"
    ]


def test_15_deep_university_structure():

    nodes = extract(
        """
        <nav>

            <ul>

                <li>
                    <a href="/academics">
                        Academics
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
    )

    academics = nodes[0]

    engineering = academics.children[0]

    electrical = engineering.children[0]

    faculty = electrical.children[0]

    assert academics.text == "Academics"

    assert engineering.text == "Engineering"

    assert electrical.text == (
        "Electrical Engineering"
    )

    assert faculty.text == "Faculty"


def run():

    tests = [
        test_1_flat_menu,
        test_2_one_level,
        test_3_two_level,
        test_4_multiple_branches,
        test_5_href,
        test_6_skip_link,
        test_7_empty_nav,
        test_8_empty_text,
        test_9_separators,
        test_10_university_navigation,
        test_11_dropdown,
        test_12_deep_nesting,
        test_13_non_nav_element,
        test_14_wrapper_elements,
        test_15_deep_university_structure,
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
                type(error).__name__,
                str(error)
            )

    print("\n" + "=" * 70)

    print(
        f"TOTAL: {passed}/{len(tests)} TESTS PASSED"
    )

    print("=" * 70)


if __name__ == "__main__":
    run()