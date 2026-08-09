from dataclasses import dataclass


@dataclass
class DepthTracker:
    """
    Tracks crawl depth for discovered URLs.

    The root page is depth 0.
    A child discovered from a page at depth N
    receives depth N + 1.

    The first accepted depth for a URL is retained.
    """

    _depths: dict[str, int]

    def __init__(self) -> None:
        self._depths = {}

    def register_root(self, url: str) -> int:
        """
        Register the root URL at depth 0.

        Returns the existing depth if the URL was already registered.
        """

        if url in self._depths:
            return self._depths[url]

        self._depths[url] = 0

        return 0

    def register_child(
        self,
        url: str,
        parent_url: str,
    ) -> int:
        """
        Register a URL discovered from a parent URL.

        The child's depth is parent depth + 1.

        If either URL is unknown, the parent is assumed
        to represent the current crawl root.
        """

        parent_depth = self._depths.get(
            parent_url,
            0,
        )

        child_depth = parent_depth + 1

        if url in self._depths:
            return self._depths[url]

        self._depths[url] = child_depth

        return child_depth

    def get_depth(self, url: str) -> int | None:
        """
        Return the registered depth for a URL.
        """

        return self._depths.get(url)

    def contains(self, url: str) -> bool:
        """
        Return True if the URL has a registered depth.
        """

        return url in self._depths

    def size(self) -> int:
        """
        Return the number of tracked URLs.
        """

        return len(self._depths)
        