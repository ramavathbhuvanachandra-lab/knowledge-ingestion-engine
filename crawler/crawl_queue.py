from collections import deque

from models.crawl_plan import CrawlPlan, CrawlPriority


class CrawlQueue:
    """
    Priority-aware crawl queue.

    Guarantees:
    - HIGH priority before NORMAL.
    - NORMAL priority before LOW.
    - FIFO ordering within the same priority.
    - A URL can enter the crawl lifecycle only once.
    - A URL remains marked as seen after dequeue().
    """

    def __init__(self) -> None:
        self._queues = {
            CrawlPriority.HIGH: deque(),
            CrawlPriority.NORMAL: deque(),
            CrawlPriority.LOW: deque(),
        }

        self._seen: set[str] = set()

    def mark_seen(self, url: str) -> bool:
        """
        Mark a URL as already seen.

        This is primarily used for the root URL because the root
        is crawled directly rather than being placed in the queue.

        Returns:
            True  -> newly marked
            False -> already seen
        """

        if not url:
            return False

        if url in self._seen:
            return False

        self._seen.add(url)

        return True

    def enqueue(self, plan: CrawlPlan) -> bool:
        """
        Add a plan to the queue.

        Returns:
            True  -> plan added
            False -> URL already seen
        """

        url = plan.url

        if not url:
            return False

        if url in self._seen:
            return False

        self._queues[plan.priority].append(plan)
        self._seen.add(url)

        return True

    def dequeue(self) -> CrawlPlan | None:
        """
        Remove and return the highest-priority pending plan.

        Priority:
            HIGH -> NORMAL -> LOW

        FIFO is preserved within each priority.
        """

        for priority in (
            CrawlPriority.HIGH,
            CrawlPriority.NORMAL,
            CrawlPriority.LOW,
        ):
            queue = self._queues[priority]

            if queue:
                return queue.popleft()

        return None

    def size(self) -> int:
        """Return the number of plans currently waiting."""

        return sum(
            len(queue)
            for queue in self._queues.values()
        )

    def is_empty(self) -> bool:
        """Return True when no plans are waiting."""

        return self.size() == 0

    def contains(self, url: str) -> bool:
        """
        Return True if the URL has entered the crawl lifecycle.

        This remains True after the URL is dequeued.
        """

        if not url:
            return False

        return url in self._seen

    def seen_count(self) -> int:
        """Return the number of unique URLs seen."""

        return len(self._seen)