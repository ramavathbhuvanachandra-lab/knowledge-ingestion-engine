from models.navigation import NavigationCandidate, NavigationNode
from models.url import URLType
from url_discovery import URLDiscovery


SOURCE_URL = "https://gwpgc.ac.in/"


def build_candidate(nodes):
    return NavigationCandidate(
        element_name="nav",
        element_id="main-menu",
        classes=[],
        aria_label="",
        tree=nodes,
    )


def test_relative_url():
    candidate = build_candidate([
        NavigationNode(
            text="Admission",
            href="/admission",
        )
    ])

    results = URLDiscovery().discover(
        [candidate],
        SOURCE_URL,
    )

    assert len(results) == 1
    assert results[0].normalized_url == (
        "https://gwpgc.ac.in/admission"
    )
    assert results[0].url_type == URLType.WEBPAGE


def test_nested_navigation():
    candidate = build_candidate([
        NavigationNode(
            text="Academics",
            href="/academics",
            children=[
                NavigationNode(
                    text="Courses",
                    href="/academics/courses",
                    children=[
                        NavigationNode(
                            text="B.Tech",
                            href="/academics/courses/btech",
                        )
                    ],
                )
            ],
        )
    ])

    results = URLDiscovery().discover(
        [candidate],
        SOURCE_URL,
    )

    urls = {
        result.normalized_url
        for result in results
    }

    assert urls == {
        "https://gwpgc.ac.in/academics",
        "https://gwpgc.ac.in/academics/courses",
        "https://gwpgc.ac.in/academics/courses/btech",
    }


def test_duplicate_urls():
    candidate = build_candidate([
        NavigationNode(
            text="Admission",
            href="/admission",
        ),
        NavigationNode(
            text="Admissions",
            href="/admission",
        ),
    ])

    results = URLDiscovery().discover(
        [candidate],
        SOURCE_URL,
    )

    assert len(results) == 1


def test_pdf():
    candidate = build_candidate([
        NavigationNode(
            text="Brochure",
            href="/documents/brochure.pdf",
        )
    ])

    results = URLDiscovery().discover(
        [candidate],
        SOURCE_URL,
    )

    assert len(results) == 1
    assert results[0].url_type == URLType.PDF


def test_image():
    candidate = build_candidate([
        NavigationNode(
            text="Campus",
            href="/images/campus.jpg",
        )
    ])

    results = URLDiscovery().discover(
        [candidate],
        SOURCE_URL,
    )

    assert len(results) == 1
    assert results[0].url_type == URLType.IMAGE


def test_external_url():
    candidate = build_candidate([
        NavigationNode(
            text="UGC",
            href="https://ugc.gov.in/",
        )
    ])

    results = URLDiscovery().discover(
        [candidate],
        SOURCE_URL,
    )

    assert len(results) == 1
    assert results[0].url_type == URLType.EXTERNAL


def test_special_links_are_ignored():
    candidate = build_candidate([
        NavigationNode(
            text="Email",
            href="mailto:test@example.com",
        ),
        NavigationNode(
            text="Phone",
            href="tel:+911234567890",
        ),
        NavigationNode(
            text="JavaScript",
            href="javascript:void(0)",
        ),
        NavigationNode(
            text="Empty",
            href="",
        ),
        NavigationNode(
            text="Fragment",
            href="#",
        ),
    ])

    results = URLDiscovery().discover(
        [candidate],
        SOURCE_URL,
    )

    assert results == []


def test_query_and_fragment():
    candidate = build_candidate([
        NavigationNode(
            text="Search",
            href="/search?department=engineering#results",
        )
    ])

    results = URLDiscovery().discover(
        [candidate],
        SOURCE_URL,
    )

    assert len(results) == 1
    assert results[0].normalized_url == (
        "https://gwpgc.ac.in/search?department=engineering"
    )


def test_content_link_discovery():
    html = """
    <html>
        <body>
            <main>
                <h2>Associated Faculty Members</h2>

                <p>
                    <a href="/people/profile/test-profile">
                        Test Faculty
                    </a>
                </p>
            </main>
        </body>
    </html>
    """

    discovery = URLDiscovery()

    results = discovery.discover_html_links(
        html=html,
        source_url=(
            "https://www.iitj.ac.in/ece/en/research"
        ),
    )

    urls = {
        result.normalized_url
        for result in results
    }

    assert (
        "https://www.iitj.ac.in/people/profile/test-profile"
        in urls
    )

def test_discovered_from_source():
    candidate = build_candidate([
        NavigationNode(
            text="Contact",
            href="/contact",
        )
    ])

    results = URLDiscovery().discover(
        [candidate],
        SOURCE_URL,
    )

    assert results[0].discovered_from == SOURCE_URL
    assert results[0].depth == 0


if __name__ == "__main__":
    test_relative_url()
    test_nested_navigation()
    test_duplicate_urls()
    test_pdf()
    test_image()
    test_external_url()
    test_special_links_are_ignored()
    test_query_and_fragment()
    test_discovered_from_source()

    print("URL DISCOVERY TESTS: PASS")