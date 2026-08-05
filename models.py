from dataclasses import dataclass
from enum import Enum


class URLType(Enum):
    WEBPAGE = "webpage"
    PDF = "pdf"
    IMAGE = "image"
    EXTERNAL = "external"
    INVALID = "invalid"


@dataclass
class URLInfo:
    raw_url: str
    normalized_url: str
    url_type: URLType
    discovered_from: str


@dataclass
class PageData:
    url: str
    title: str
    markdown: str
    html: str
    success: bool