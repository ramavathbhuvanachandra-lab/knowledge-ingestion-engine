from dataclasses import dataclass
from enum import Enum

from models.url import URLInfo, URLType


class CrawlAction(Enum):
    CRAWL = "crawl"
    DOCUMENT = "document"
    RESOURCE = "resource"
    IGNORE = "ignore"


class CrawlPriority(Enum):
    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass(frozen=True)
class CrawlPlan:
    url_info: URLInfo
    action: CrawlAction
    priority: CrawlPriority
    depth: int

    @property
    def url(self) -> str:
        return self.url_info.normalized_url

    @property
    def url_type(self) -> URLType:
        return self.url_info.url_type

    @property
    def discovered_from(self) -> str:
        return self.url_info.discovered_from