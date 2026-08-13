from dataclasses import dataclass


@dataclass
class Hierarchy:

    root: str

    entity: str

    section: str

    language: str

    leaf: str

    depth: int