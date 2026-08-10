from dataclasses import dataclass

from models.crawl_plan import (
    CrawlAction,
    CrawlPlan,
    CrawlPriority,
)
from models.url import URLInfo, URLType


@dataclass(frozen=True)
class CrawlPolicy:
    """
    Deterministic policy for converting URLInfo
    into a CrawlPlan.
    """

    crawl_webpages: bool = True
    process_documents: bool = True
    process_resources: bool = True
    allow_external: bool = False

    webpage_priority: CrawlPriority = CrawlPriority.HIGH
    document_priority: CrawlPriority = CrawlPriority.NORMAL
    resource_priority: CrawlPriority = CrawlPriority.LOW

    def create_plan(
        self,
        url_info: URLInfo,
        depth: int | None = None,
    ) -> CrawlPlan:

        effective_depth = (
            url_info.depth
            if depth is None
            else depth
        )

        action, priority = self._decide(
            url_info
        )

        return CrawlPlan(
            url_info=url_info,
            action=action,
            priority=priority,
            depth=effective_depth,
        )

    def _decide(
        self,
        url_info: URLInfo,
    ) -> tuple[CrawlAction, CrawlPriority]:

        if url_info.url_type == URLType.WEBPAGE:

            if self.crawl_webpages:

                return (
                    CrawlAction.CRAWL,
                    self.webpage_priority,
                )

            return (
                CrawlAction.IGNORE,
                CrawlPriority.LOW,
            )

        # ------------------------------------------------------
        # DOCUMENTS
        # ------------------------------------------------------

        if url_info.url_type in (
            URLType.PDF,
            URLType.XLSX,
        ):

            if self.process_documents:

                return (
                    CrawlAction.DOCUMENT,
                    self.document_priority,
                )

            return (
                CrawlAction.IGNORE,
                CrawlPriority.LOW,
            )

        if url_info.url_type == URLType.IMAGE:

            if self.process_resources:

                return (
                    CrawlAction.RESOURCE,
                    self.resource_priority,
                )

            return (
                CrawlAction.IGNORE,
                CrawlPriority.LOW,
            )

        if url_info.url_type == URLType.EXTERNAL:

            if self.allow_external:

                return (
                    CrawlAction.CRAWL,
                    CrawlPriority.LOW,
                )

            return (
                CrawlAction.IGNORE,
                CrawlPriority.LOW,
            )

        return (
            CrawlAction.IGNORE,
            CrawlPriority.LOW,
        )