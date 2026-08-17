from url_discovery import URLDiscovery


def test_malformed_links_do_not_break_discovery():
    html = """
    <html>
        <body>
            <a href="https://example.com/good">
                Good
            </a>

            <a href="https://[">
                Broken IPv6
            </a>

            <a href="https://example.com:bad-port/">
                Broken Port
            </a>

            <a href="javascript:void(0)">
                JavaScript
            </a>

            <a href="mailto:test@example.com">
                Email
            </a>

            <a href="/valid/page">
                Valid Relative
            </a>
        </body>
    </html>
    """

    discovery = URLDiscovery()

    results = discovery.discover_html_links(
        html=html,
        source_url="https://example.com/",
    )

    urls = {
        result.normalized_url
        for result in results
    }

    assert urls == {
        "https://example.com/good",
        "https://example.com/valid/page",
    }