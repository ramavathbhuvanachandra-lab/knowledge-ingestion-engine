from dataclasses import dataclass
from enum import Enum


@dataclass
class PageData:
    url: str
    title: str
    markdown: str
    html: str
    success: bool