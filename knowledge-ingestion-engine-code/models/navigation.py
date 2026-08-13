from dataclasses import dataclass, field


@dataclass
class NavigationNode:

    text: str

    href: str = ""

    children: list["NavigationNode"] = field(
        default_factory=list
    )


@dataclass
class NavigationCandidate:

    element_name: str

    element_id: str

    classes: list[str]

    aria_label: str

    links: list[str] = field(
        default_factory=list
    )

    link_count: int = 0

    navigation_type: str = "unknown"

    score: int = 0

    tree: list[NavigationNode] = field(
        default_factory=list
    )

    element: object = None
