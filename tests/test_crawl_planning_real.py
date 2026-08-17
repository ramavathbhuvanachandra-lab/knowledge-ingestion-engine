import asyncio
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from crawler.crawler import crawl_page
from crawler.crawl_policy import CrawlPolicy
from crawler.crawl_queue import CrawlQueue
from crawler.depth_tracker import DepthTracker
from crawler.url_normalizer import normalize_url
from crawler.url_validator import is_valid_url

from models.crawl_plan import (
    CrawlAction,
    CrawlPriority,
)

from models.url import URLInfo, URLType

from pipeline.navigation_pipeline import NavigationPipeline


TEST_URLS = [
    "https://gwpgc.ac.in/",
    "https://www.iitj.ac.in/",
    "https://www.vbspu.ac.in/en",
    "https://home.iitd.ac.in/",
]


def classify_url_type(
    normalized_url: str,
    root_domain: str,
) -> URLType:

    lower_url = normalized_url.lower()

    if lower_url.endswith(".pdf"):
        return URLType.PDF

    image_extensions = (
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".svg",
        ".webp",
        ".bmp",
        ".ico",
    )

    if lower_url.endswith(
        image_extensions
    ):
        return URLType.IMAGE

    parsed = urlparse(
        normalized_url
    )

    if parsed.netloc != root_domain:
        return URLType.EXTERNAL

    return URLType.WEBPAGE


def walk_navigation_tree(
    nodes,
    parent_url,
    parent_depth,
    root_domain,
    tracker,
    policy,
    queue,
    stats,
):
    """
    Convert real navigation nodes into crawl plans.

    Invalid navigation triggers such as
    javascript:void(0) are not crawl targets,
    but their children are still traversed.
    """

    for node in nodes:

        raw_href = (
            node.href.strip()
            if node.href
            else ""
        )

        # --------------------------------------------------
        # EMPTY HREF
        # --------------------------------------------------

        if not raw_href:

            stats["empty"] += 1

            yield from walk_navigation_tree(
                node.children,
                parent_url,
                parent_depth,
                root_domain,
                tracker,
                policy,
                queue,
                stats,
            )

            continue

        # --------------------------------------------------
        # RESOLVE
        # --------------------------------------------------

        resolved_url = urljoin(
            parent_url,
            raw_href,
        )

        normalized_url = normalize_url(
            resolved_url
        )

        # --------------------------------------------------
        # VALIDATE
        # --------------------------------------------------

        if not is_valid_url(
            normalized_url
        ):

            stats["invalid"] += 1

            # Invalid menu triggers can still
            # contain valid child links.

            yield from walk_navigation_tree(
                node.children,
                parent_url,
                parent_depth,
                root_domain,
                tracker,
                policy,
                queue,
                stats,
            )

            continue

        # --------------------------------------------------
        # CLASSIFY
        # --------------------------------------------------

        url_type = classify_url_type(
            normalized_url,
            root_domain,
        )

        # --------------------------------------------------
        # DEPTH
        # --------------------------------------------------

        already_known = tracker.contains(
            normalized_url
        )

        depth = tracker.register_child(
            normalized_url,
            parent_url,
        )

        if not already_known:

            expected_depth = (
                parent_depth + 1
            )

            assert depth == expected_depth, (
                f"Depth error for "
                f"{normalized_url}: "
                f"expected {expected_depth}, "
                f"got {depth}"
            )

            stats["unique"] += 1

        else:

            stats["duplicates"] += 1

        # --------------------------------------------------
        # URL INFO
        # --------------------------------------------------

        info = URLInfo(
            raw_url=raw_href,
            normalized_url=normalized_url,
            url_type=url_type,
            discovered_from=parent_url,
            depth=depth,
        )

        # --------------------------------------------------
        # POLICY
        # --------------------------------------------------

        plan = policy.create_plan(
            info
        )

        stats["plans"] += 1

        stats[
            f"action:{plan.action.value}"
        ] += 1

        # IMPORTANT:
        # Use enum members as dictionary keys.
        # Do not assume enum.value is "high"/"normal"/"low".

        stats["priority"][plan.priority] += 1

        # --------------------------------------------------
        # EXECUTION QUEUE
        # --------------------------------------------------

        if plan.action == CrawlAction.IGNORE:

            stats["ignored"] += 1

        else:

            added = queue.enqueue(
                plan
            )

            if added:

                stats["queued"] += 1

            else:

                stats["queue_duplicates"] += 1

        # --------------------------------------------------
        # YIELD
        # --------------------------------------------------

        yield (
            normalized_url,
            depth,
            url_type,
            plan,
        )

        # --------------------------------------------------
        # CHILDREN
        # --------------------------------------------------

        yield from walk_navigation_tree(
            node.children,
            normalized_url,
            depth,
            root_domain,
            tracker,
            policy,
            queue,
            stats,
        )


async def test_website(url):

    print("\n" + "=" * 100)
    print("TESTING:", url)
    print("=" * 100)

    page = await crawl_page(url)

    assert page.success, (
        f"Crawl failed: {url}"
    )

    assert page.html, (
        f"Empty HTML: {url}"
    )

    soup = BeautifulSoup(
        page.html,
        "html.parser",
    )

    pipeline = NavigationPipeline(
        soup=soup,
    )

    result = pipeline.run()

    candidates = result["candidates"]

    root_url = normalize_url(
        page.url
    )

    root_domain = urlparse(
        root_url
    ).netloc

    tracker = DepthTracker()
    policy = CrawlPolicy()
    queue = CrawlQueue()

    assert tracker.register_root(
        root_url
    ) == 0

    stats = {
        "empty": 0,
        "invalid": 0,
        "unique": 0,
        "duplicates": 0,
        "plans": 0,
        "queued": 0,
        "ignored": 0,
        "queue_duplicates": 0,
        "action:crawl": 0,
        "action:document": 0,
        "action:resource": 0,
        "action:ignore": 0,
        "priority": {
            CrawlPriority.HIGH: 0,
            CrawlPriority.NORMAL: 0,
            CrawlPriority.LOW: 0,
        },
    }

    maximum_depth = 0

    # --------------------------------------------------
    # BUILD REAL PLANS
    # --------------------------------------------------

    for candidate in candidates:

        for (
            normalized_url,
            depth,
            url_type,
            plan,
        ) in walk_navigation_tree(
            candidate.tree,
            root_url,
            0,
            root_domain,
            tracker,
            policy,
            queue,
            stats,
        ):

            maximum_depth = max(
                maximum_depth,
                depth,
            )

            assert plan.action in (
                CrawlAction.CRAWL,
                CrawlAction.DOCUMENT,
                CrawlAction.RESOURCE,
                CrawlAction.IGNORE,
            )

            assert depth >= 0

            if normalized_url == root_url:
                assert depth == 0
            else:
                assert depth >= 1

            assert plan.depth == depth

            assert (
                plan.url
                == normalized_url
            )

    # --------------------------------------------------
    # ROOT
    # --------------------------------------------------

    assert tracker.get_depth(
        root_url
    ) == 0

    # --------------------------------------------------
    # QUEUE
    # --------------------------------------------------

    assert queue.size() == (
        stats["queued"]
    )

    # --------------------------------------------------
    # DRAIN QUEUE
    # --------------------------------------------------

    previous_priority = None

    dequeued = 0

    priority_rank = {
        CrawlPriority.HIGH: 0,
        CrawlPriority.NORMAL: 1,
        CrawlPriority.LOW: 2,
    }

    while not queue.is_empty():

        plan = queue.dequeue()

        assert plan is not None

        dequeued += 1

        # IGNORE must never enter the
        # execution queue.

        assert plan.action != (
            CrawlAction.IGNORE
        )

        # Priority must never go backwards.

        if previous_priority is not None:

            assert (
                priority_rank[
                    plan.priority
                ]
                >=
                priority_rank[
                    previous_priority
                ]
            )

        previous_priority = (
            plan.priority
        )

    assert dequeued == stats["queued"]

    # --------------------------------------------------
    # OUTPUT
    # --------------------------------------------------

    print("\nRESULTS")
    print("-" * 100)

    print(
        "Navigation candidates :",
        len(candidates),
    )

    print(
        "Unique URLs           :",
        stats["unique"],
    )

    print(
        "Duplicate discoveries :",
        stats["duplicates"],
    )

    print(
        "Invalid / ignored hrefs:",
        stats["invalid"],
    )

    print(
        "Plans created         :",
        stats["plans"],
    )

    print(
        "Executable queued     :",
        stats["queued"],
    )

    print(
        "Ignored plans         :",
        stats["ignored"],
    )

    print(
        "Queue duplicates      :",
        stats["queue_duplicates"],
    )

    print(
        "CRAWL plans           :",
        stats["action:crawl"],
    )

    print(
        "DOCUMENT plans        :",
        stats["action:document"],
    )

    print(
        "RESOURCE plans        :",
        stats["action:resource"],
    )

    print(
        "IGNORE plans          :",
        stats["action:ignore"],
    )

    print(
        "HIGH priority         :",
        stats["priority"][
            CrawlPriority.HIGH
        ],
    )

    print(
        "NORMAL priority       :",
        stats["priority"][
            CrawlPriority.NORMAL
        ],
    )

    print(
        "LOW priority          :",
        stats["priority"][
            CrawlPriority.LOW
        ],
    )

    print(
        "Tracked URLs          :",
        tracker.size(),
    )

    print(
        "Maximum crawl depth   :",
        maximum_depth,
    )

    print(
        "\nPASS:",
        url,
    )


async def main():

    print("\n")
    print("=" * 100)
    print(
        "REAL CRAWL PLANNING INTEGRATION"
    )
    print("=" * 100)

    passed = 0

    for url in TEST_URLS:

        await test_website(url)

        passed += 1

    print("\n")
    print("=" * 100)

    print(
        f"WEBSITES PASSED: "
        f"{passed} / {len(TEST_URLS)}"
    )

    print("=" * 100)

    assert passed == len(TEST_URLS)

    print(
        "\nREAL CRAWL PLANNING "
        "INTEGRATION: PASS"
    )


if __name__ == "__main__":

    asyncio.run(main())