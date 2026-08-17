from models.navigation import NavigationCandidate, NavigationNode
from models.url import URLType
from url_discovery import URLDiscovery


SOURCE_URL = "https://gwpgc.ac.in/academics/"


def build_candidate(nodes):
    return NavigationCandidate(
        element_name="nav",
        element_id="main-menu",
        classes=[],
        aria_label="",
        tree=nodes,
    )


def discover(nodes):
    candidate = build_candidate(nodes)

    return URLDiscovery().discover(
        [candidate],
        SOURCE_URL,
    )


def get_urls(results):
    return {
        result.normalized_url
        for result in results
    }


def test_parent_relative_url():
    results = discover([
        NavigationNode(
            text="Faculty",
            href="../faculty",
        )
    ])

    assert get_urls(results) == {
        "https://gwpgc.ac.in/faculty",
    }


def test_protocol_relative_url():
    results = discover([
        NavigationNode(
            text="Home",
            href="//gwpgc.ac.in/",
        )
    ])

    assert get_urls(results) == {
        "https://gwpgc.ac.in",
    }


def test_trailing_slash_normalization():
    results = discover([
        NavigationNode(
            text="Admissions",
            href="/admissions/",
        ),
        NavigationNode(
            text="Admissions Duplicate",
            href="/admissions",
        ),
    ])

    assert len(results) == 1
    assert results[0].normalized_url == (
        "https://gwpgc.ac.in/admissions"
    )


def test_uppercase_url_normalization():
    results = discover([
        NavigationNode(
            text="Admissions",
            href="/ADMISSIONS/",
        )
    ])

    assert get_urls(results) == {
        "https://gwpgc.ac.in/ADMISSIONS",
    }


def test_query_parameters_are_preserved():
    results = discover([
        NavigationNode(
            text="Search",
            href="/search?department=engineering",
        )
    ])

    assert get_urls(results) == {
        "https://gwpgc.ac.in/search?department=engineering",
    }


def test_fragment_is_removed_but_query_is_preserved():
    results = discover([
        NavigationNode(
            text="Search",
            href="/search?department=engineering#results",
        )
    ])

    assert get_urls(results) == {
        "https://gwpgc.ac.in/search?department=engineering",
    }


def test_multiple_query_parameters():
    results = discover([
        NavigationNode(
            text="Search",
            href="/search?department=ee&year=2026",
        )
    ])

    assert get_urls(results) == {
        "https://gwpgc.ac.in/search?department=ee&year=2026",
    }


def test_nested_navigation_deep_tree():
    results = discover([
        NavigationNode(
            text="Academics",
            href="/academics",
            children=[
                NavigationNode(
                    text="Departments",
                    href="/academics/departments",
                    children=[
                        NavigationNode(
                            text="Electrical Engineering",
                            href="/academics/departments/ee",
                            children=[
                                NavigationNode(
                                    text="Research",
                                    href="/academics/departments/ee/research",
                                )
                            ],
                        )
                    ],
                )
            ],
        )
    ])

    assert get_urls(results) == {
        "https://gwpgc.ac.in/academics",
        "https://gwpgc.ac.in/academics/departments",
        "https://gwpgc.ac.in/academics/departments/ee",
        "https://gwpgc.ac.in/academics/departments/ee/research",
    }


def test_duplicate_urls_across_candidates():
    candidates = [
        build_candidate([
            NavigationNode(
                text="Admission",
                href="/admission",
            )
        ]),
        build_candidate([
            NavigationNode(
                text="Admissions",
                href="/admission/",
            )
        ]),
    ]

    results = URLDiscovery().discover(
        candidates,
        SOURCE_URL,
    )

    assert len(results) == 1


def test_external_subdomain_is_classified():
    results = discover([
        NavigationNode(
            text="Portal",
            href="https://portal.gwpgc.ac.in/",
        )
    ])

    assert len(results) == 1
    assert results[0].url_type == URLType.EXTERNAL


def test_external_domain_is_classified():
    results = discover([
        NavigationNode(
            text="UGC",
            href="https://ugc.gov.in/",
        )
    ])

    assert len(results) == 1
    assert results[0].url_type == URLType.EXTERNAL


def test_pdf_is_not_discarded():
    results = discover([
        NavigationNode(
            text="Admission Brochure",
            href="/documents/brochure.pdf",
        )
    ])

    assert len(results) == 1
    assert results[0].url_type == URLType.PDF


def test_image_is_not_discarded():
    results = discover([
        NavigationNode(
            text="Campus Image",
            href="/images/campus.jpg",
        )
    ])

    assert len(results) == 1
    assert results[0].url_type == URLType.IMAGE


def test_whitespace_is_removed_from_href():
    results = discover([
        NavigationNode(
            text="About",
            href="   /about   ",
        )
    ])

    assert get_urls(results) == {
        "https://gwpgc.ac.in/about",
    }


def test_empty_and_whitespace_href_are_ignored():
    results = discover([
        NavigationNode(
            text="Empty",
            href="",
        ),
        NavigationNode(
            text="Whitespace",
            href="   ",
        ),
    ])

    assert results == []


def test_special_links_are_ignored():
    results = discover([
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
            text="Fragment",
            href="#",
        ),
    ])

    assert results == []


def test_special_parent_node_does_not_block_children():
    results = discover([
        NavigationNode(
            text="Open Menu",
            href="#",
            children=[
                NavigationNode(
                    text="Admission",
                    href="/admission",
                )
            ],
        )
    ])

    assert get_urls(results) == {
        "https://gwpgc.ac.in/admission",
    }


def test_discovered_from_is_preserved():
    results = discover([
        NavigationNode(
            text="Contact",
            href="/contact",
        )
    ])

    assert results[0].discovered_from == SOURCE_URL


def test_depth_remains_zero_until_crawl_planning():
    results = discover([
        NavigationNode(
            text="Contact",
            href="/contact",
        )
    ])

    assert results[0].depth == 0


if __name__ == "__main__":

    test_parent_relative_url()
    test_protocol_relative_url()
    test_trailing_slash_normalization()
    test_uppercase_url_normalization()
    test_query_parameters_are_preserved()
    test_fragment_is_removed_but_query_is_preserved()
    test_multiple_query_parameters()
    test_nested_navigation_deep_tree()
    test_duplicate_urls_across_candidates()
    test_external_subdomain_is_classified()
    test_external_domain_is_classified()
    test_pdf_is_not_discarded()
    test_image_is_not_discarded()
    test_whitespace_is_removed_from_href()
    test_empty_and_whitespace_href_are_ignored()
    test_special_links_are_ignored()
    test_special_parent_node_does_not_block_children()
    test_discovered_from_is_preserved()
    test_depth_remains_zero_until_crawl_planning()

    print("URL DISCOVERY ADVERSARIAL TESTS: PASS")