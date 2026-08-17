from crawler.crawl_queue import CrawlQueue
from models.crawl_plan import (
    CrawlAction,
    CrawlPlan,
    CrawlPriority,
)
from models.url import URLInfo, URLType


def make_plan(
    url: str,
    priority: CrawlPriority,
    depth: int = 0,
) -> CrawlPlan:

    info = URLInfo(
        raw_url=url,
        normalized_url=url,
        url_type=URLType.WEBPAGE,
        discovered_from="https://gwpgc.ac.in/",
        depth=depth,
    )

    return CrawlPlan(
        url_info=info,
        action=CrawlAction.CRAWL,
        priority=priority,
        depth=depth,
    )


def test_high_priority_before_normal():

    queue = CrawlQueue()

    normal = make_plan(
        "https://example.com/normal",
        CrawlPriority.NORMAL,
    )

    high = make_plan(
        "https://example.com/high",
        CrawlPriority.HIGH,
    )

    queue.enqueue(normal)
    queue.enqueue(high)

    assert queue.dequeue() == high
    assert queue.dequeue() == normal
    assert queue.dequeue() is None


def test_high_priority_before_low():

    queue = CrawlQueue()

    low = make_plan(
        "https://example.com/low",
        CrawlPriority.LOW,
    )

    high = make_plan(
        "https://example.com/high",
        CrawlPriority.HIGH,
    )

    queue.enqueue(low)
    queue.enqueue(high)

    assert queue.dequeue() == high
    assert queue.dequeue() == low


def test_normal_priority_before_low():

    queue = CrawlQueue()

    low = make_plan(
        "https://example.com/low",
        CrawlPriority.LOW,
    )

    normal = make_plan(
        "https://example.com/normal",
        CrawlPriority.NORMAL,
    )

    queue.enqueue(low)
    queue.enqueue(normal)

    assert queue.dequeue() == normal
    assert queue.dequeue() == low


def test_priority_order():

    queue = CrawlQueue()

    plans = [
        make_plan(
            "https://example.com/low",
            CrawlPriority.LOW,
        ),
        make_plan(
            "https://example.com/high",
            CrawlPriority.HIGH,
        ),
        make_plan(
            "https://example.com/normal",
            CrawlPriority.NORMAL,
        ),
        make_plan(
            "https://example.com/high-2",
            CrawlPriority.HIGH,
        ),
    ]

    for plan in plans:
        queue.enqueue(plan)

    assert queue.dequeue().url == (
        "https://example.com/high"
    )

    assert queue.dequeue().url == (
        "https://example.com/high-2"
    )

    assert queue.dequeue().url == (
        "https://example.com/normal"
    )

    assert queue.dequeue().url == (
        "https://example.com/low"
    )


def test_same_priority_preserves_fifo():

    queue = CrawlQueue()

    first = make_plan(
        "https://example.com/first",
        CrawlPriority.HIGH,
    )

    second = make_plan(
        "https://example.com/second",
        CrawlPriority.HIGH,
    )

    third = make_plan(
        "https://example.com/third",
        CrawlPriority.HIGH,
    )

    queue.enqueue(first)
    queue.enqueue(second)
    queue.enqueue(third)

    assert queue.dequeue() == first
    assert queue.dequeue() == second
    assert queue.dequeue() == third


def test_duplicate_urls_are_rejected():

    queue = CrawlQueue()

    first = make_plan(
        "https://example.com/about",
        CrawlPriority.HIGH,
    )

    duplicate = make_plan(
        "https://example.com/about",
        CrawlPriority.NORMAL,
    )

    assert queue.enqueue(first) is True
    assert queue.enqueue(duplicate) is False

    assert queue.size() == 1


def test_contains():

    queue = CrawlQueue()

    plan = make_plan(
        "https://example.com/about",
        CrawlPriority.HIGH,
    )

    assert queue.contains(
        "https://example.com/about"
    ) is False

    queue.enqueue(plan)

    assert queue.contains(
        "https://example.com/about"
    ) is True


def test_size():

    queue = CrawlQueue()

    assert queue.size() == 0
    assert queue.is_empty() is True

    queue.enqueue(
        make_plan(
            "https://example.com/a",
            CrawlPriority.HIGH,
        )
    )

    queue.enqueue(
        make_plan(
            "https://example.com/b",
            CrawlPriority.NORMAL,
        )
    )

    queue.enqueue(
        make_plan(
            "https://example.com/c",
            CrawlPriority.LOW,
        )
    )

    assert queue.size() == 3
    assert queue.is_empty() is False

    queue.dequeue()

    assert queue.size() == 2


def test_empty_queue():

    queue = CrawlQueue()

    assert queue.dequeue() is None
    assert queue.size() == 0
    assert queue.is_empty() is True


if __name__ == "__main__":

    test_high_priority_before_normal()
    test_high_priority_before_low()
    test_normal_priority_before_low()
    test_priority_order()
    test_same_priority_preserves_fifo()
    test_duplicate_urls_are_rejected()
    test_contains()
    test_size()
    test_empty_queue()

    print("CRAWL QUEUE TESTS: PASS")