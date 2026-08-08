from dataclasses import dataclass

@dataclass
class PageContext:
    url: str
    domain: str
    title: str
    h1: str
    main_content: str
    url_segments: list[str]
    breadcrumbs: list[str]
    navigation: list[str]
    language: str
    depth: int