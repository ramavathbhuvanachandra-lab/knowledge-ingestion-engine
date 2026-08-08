from dataclasses import dataclass


@dataclass
class URLStructure:

    scheme: str
    domain: str
    segments: list[str]
    query: dict
    fragment: str
    depth: int