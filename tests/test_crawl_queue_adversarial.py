from models.crawl_plan import (
    CrawlAction,
    CrawlPlan,
    CrawlPriority,
)

from models.url import (
    URLInfo,
    URLType,
)

from crawler.crawl_queue import CrawlQueue


def make_plan(
    url: str,
    priority: CrawlPriority,
) -> CrawlPlan:

    url_info = URLInfo(
        raw_url=url,
        normalized_url=url,
        url_type=URLType.WEBPAGE,
        discovered_from="test",
        depth=1,
    )

    return CrawlPlan(
        url_info=url_info,
        action=CrawlAction.CRAWL,
        priority=priority,
        depth=1,
    )


def test_duplicate_url():

    queue = CrawlQueue()

    plan = make_plan(
        "https://example.com/page",
        CrawlPriority.HIGH,
    )

    assert queue.enqueue(plan) is True
    assert queue.enqueue(plan) is False

    assert queue.size() == 1


def test_duplicate_after_dequeue():

    queue = CrawlQueue()

    plan = make_plan(
        "https://example.com/page",
        CrawlPriority.HIGH,
    )

    assert queue.enqueue(plan) is True

    dequeued = queue.dequeue()

    assert dequeued is not None
    assert dequeued.url == (
        "https://example.com/page"
    )

    # URL must remain known even after dequeue.
    assert queue.contains(
        "https://example.com/page"
    )

    # Must never be queued again.
    assert queue.enqueue(plan) is False

    assert queue.size() == 0


def test_root_marked_seen():

    queue = CrawlQueue()

    root = "https://example.com"

    assert queue.mark_seen(root) is True

    assert queue.contains(root)

    plan = make_plan(
        root,
        CrawlPriority.HIGH,
    )

    assert queue.enqueue(plan) is False

    assert queue.size() == 0


def test_mark_seen_is_idempotent():

    queue = CrawlQueue()

    url = "https://example.com/page"

    assert queue.mark_seen(url) is True
    assert queue.mark_seen(url) is False

    assert queue.seen_count() == 1


def test_priority_order():

    queue = CrawlQueue()

    queue.enqueue(
        make_plan(
            "https://example.com/low",
            CrawlPriority.LOW,
        )
    )

    queue.enqueue(
        make_plan(
            "https://example.com/normal",
            CrawlPriority.NORMAL,
        )
    )

    queue.enqueue(
        make_plan(
            "https://example.com/high",
            CrawlPriority.HIGH,
        )
    )

    first = queue.dequeue()
    second = queue.dequeue()
    third = queue.dequeue()

    assert first is not None
    assert second is not None
    assert third is not None

    assert first.priority == CrawlPriority.HIGH
    assert second.priority == CrawlPriority.NORMAL
    assert third.priority == CrawlPriority.LOW


def test_fifo_with_same_priority():

    queue = CrawlQueue()

    urls = [
        "https://example.com/one",
        "https://example.com/two",
        "https://example.com/three",
    ]

    for url in urls:
        queue.enqueue(
            make_plan(
                url,
                CrawlPriority.HIGH,
            )
        )

    result = []

    while not queue.is_empty():

        plan = queue.dequeue()

        assert plan is not None

        result.append(plan.url)

    assert result == urls


def test_large_duplicate_burst():

    queue = CrawlQueue()

    url = "https://example.com/repeated"

    plan = make_plan(
        url,
        CrawlPriority.HIGH,
    )

    accepted = 0

    for _ in range(1000):

        if queue.enqueue(plan):
            accepted += 1

    assert accepted == 1
    assert queue.size() == 1
    assert queue.seen_count() == 1


def test_empty_urls_are_rejected():

    queue = CrawlQueue()

    plan = make_plan(
        "",
        CrawlPriority.HIGH,
    )

    assert queue.enqueue(plan) is False
    assert queue.size() == 0


def run_all_tests():

    test_duplicate_url()
    test_duplicate_after_dequeue()
    test_root_marked_seen()
    test_mark_seen_is_idempotent()
    test_priority_order()
    test_fifo_with_same_priority()
    test_large_duplicate_burst()
    test_empty_urls_are_rejected()

    print(
        "CRAWL QUEUE ADVERSARIAL TESTS: PASS"
    )


if __name__ == "__main__":
    run_all_tests()