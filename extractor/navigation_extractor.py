from bs4 import BeautifulSoup

from models.navigation import NavigationCandidate
from analyzer.navigation_tree import NavigationTreeExtractor


class NavigationExtractor:

    NAVIGATION_CLASSES = [
        # Main navigation
        "navbar",
        "navigation",
        "main-menu",
        "main-navigation",
        "primary-menu",
        "primary-navigation",
        "site-navigation",
        "site-nav",

        # Generic menus
        "menu",
        "dropdown-menu",
        "dropdown",
        "sub-menu",
        "submenu",

        # Sidebar
        "side-menu",
        "sidebar-menu",
        "sidebar-navigation",
        "side-navigation",

        # Footer
        "footer-navigation",
        "footer-menu",

        # Useful institutional navigation
        "quick-links",
        "quicklinks",
        "important-links",
        "important-links-menu",
        "useful-links",
        "related-links",
    ]

    NAVIGATION_ID_KEYWORDS = [
        # Main navigation
        "navbar",
        "navigation",
        "main-menu",
        "mainmenu",
        "main-navigation",
        "primary-menu",
        "primarymenu",
        "primary-navigation",
        "site-menu",
        "sitemenu",
        "site-nav",
        "sitenav",

        # Menus
        "menu",
        "dropdown-menu",
        "dropdown",
        "sub-menu",
        "submenu",

        # Sidebar
        "side-menu",
        "sidebar-menu",
        "sidebar-navigation",
        "side-navigation",

        # Footer
        "footer-navigation",
        "footer-menu",

        # Institutional links
        "quick-links",
        "quicklinks",
        "important-links",
        "useful-links",
        "related-links",
    ]

    def __init__(
        self,
        soup: BeautifulSoup
    ):
        self.soup = soup
        self.tree_extractor = NavigationTreeExtractor()

    # ==================================================
    # PUBLIC API
    # ==================================================

    def discover_candidates(
        self
    ) -> list[NavigationCandidate]:

        candidates = []

        # --------------------------------------------------
        # Strategy 1 — Semantic <nav>
        # --------------------------------------------------

        for element in self.soup.find_all("nav"):

            candidate = self._build_candidate(
                element
            )

            if candidate:
                candidates.append(candidate)

        # --------------------------------------------------
        # Strategy 2 — Navigation/menu classes
        # --------------------------------------------------

        for class_name in self.NAVIGATION_CLASSES:

            elements = self.soup.find_all(
                class_=lambda classes:
                    classes
                    and class_name in classes
            )

            for element in elements:

                # Ignore leaf menu items
                if element.name in {
                    "a",
                    "li"
                }:
                    continue

                candidate = self._build_candidate(
                    element
                )

                if candidate:
                    candidates.append(candidate)

        # --------------------------------------------------
        # Strategy 3 — Navigation-like IDs
        # --------------------------------------------------

        for element in self.soup.find_all(
            id=True
        ):

            element_id = (
                element.get(
                    "id",
                    ""
                )
                .lower()
            )

            if not any(
                keyword in element_id
                for keyword in
                self.NAVIGATION_ID_KEYWORDS
            ):
                continue

            if element.name in {
                "a",
                "li"
            }:
                continue

            candidate = self._build_candidate(
                element
            )

            if candidate:
                candidates.append(candidate)

        # --------------------------------------------------
        # Remove exact duplicate representations
        # --------------------------------------------------

        return self._deduplicate_candidates(
            candidates
        )

    # ==================================================
    # BACKWARD COMPATIBILITY
    # ==================================================

    def extract(
        self
    ) -> list[str]:

        candidates = self.discover_candidates()

        if not candidates:
            return []

        best_candidate = max(
            candidates,
            key=lambda candidate: (
                candidate.score,
                candidate.link_count
            )
        )

        return best_candidate.links

    # ==================================================
    # BUILD CANDIDATE
    # ==================================================

    def _build_candidate(
        self,
        element
    ):

        links = self._extract_links(
            element
        )

        # A useful navigation container
        # should contain at least two links.
        if len(links) < 2:
            return None

        element_id = element.get(
            "id",
            ""
        )

        classes = element.get(
            "class",
            []
        )

        aria_label = element.get(
            "aria-label",
            ""
        )

        navigation_type = (
            self._classify_navigation(
                element
            )
        )

        score = self._calculate_score(
            element
        )
        tree = self.tree_extractor.extract(
            element
            )


        return NavigationCandidate(

            element_name=element.name,

            element_id=element_id,

            classes=classes,

            aria_label=aria_label,

            links=links,

            link_count=len(links),

            navigation_type=navigation_type,

            score=score,

            tree=tree,

            element=element

        )

    # ==================================================
    # LINK EXTRACTION
    # ==================================================

    def _extract_links(
        self,
        element
    ):

        links = []

        for link in element.find_all("a"):

            text = link.get_text(
                " ",
                strip=True
            )

            if not text:
                continue

            normalized_text = (
                text.lower()
            )

            # Accessibility skip links
            if (
                "skip to content"
                in normalized_text
                or
                "skip to main content"
                in normalized_text
                or
                "skip navigation"
                in normalized_text
            ):
                continue

            if text in links:
                continue

            links.append(text)

        return links

    # ==================================================
    # EXACT DUPLICATE CANDIDATE REMOVAL
    # ==================================================

    def _deduplicate_candidates(
        self,
        candidates
    ):

        unique = []

        seen = set()

        for candidate in candidates:

            key = (
                candidate.element_name,
                candidate.element_id,
                tuple(candidate.classes),
                candidate.aria_label,
                tuple(candidate.links)
            )

            if key in seen:
                continue

            seen.add(key)

            unique.append(candidate)

        return unique

    # ==================================================
    # NAVIGATION CLASSIFICATION
    # ==================================================

    def _classify_navigation(
        self,
        element
    ):

        aria_label = (
            element.get(
                "aria-label",
                ""
            )
            or ""
        ).lower()

        element_id = (
            element.get(
                "id",
                ""
            )
            or ""
        ).lower()

        classes = {
            class_name.lower()
            for class_name in element.get(
                "class",
                []
            )
        }

        # --------------------------------------------------
        # Footer
        # --------------------------------------------------

        if (
            "footer" in aria_label
            or "footer" in element_id
            or any(
                "footer" in value
                for value in classes
            )
        ):
            return "footer"

        # --------------------------------------------------
        # Sidebar
        # --------------------------------------------------

        if (
            "sidebar" in aria_label
            or "side" in aria_label
            or "sidebar" in element_id
            or "side-menu" in classes
            or "sidebar-menu" in classes
        ):
            return "sidebar"

        # --------------------------------------------------
        # Primary
        # --------------------------------------------------

        if (
            "main" in aria_label
            or "primary" in aria_label
            or "main" in element_id
            or "primary" in element_id
            or "main-menu" in classes
            or "main-navigation" in classes
            or "primary-menu" in classes
            or "primary-navigation" in classes
        ):
            return "primary"

        # --------------------------------------------------
        # Semantic <nav>
        # --------------------------------------------------

        if element.name == "nav":
            return "semantic"

        # --------------------------------------------------
        # Secondary menu
        # --------------------------------------------------

        if (
            "menu" in classes
            or "dropdown-menu" in classes
            or "sub-menu" in classes
            or "submenu" in classes
            or "quick-links" in classes
            or "important-links" in classes
        ):
            return "secondary"

        return "unknown"

    # ==================================================
    # SCORE
    # ==================================================

    def _calculate_score(
        self,
        element
    ):

        score = 0

        # --------------------------------------------------
        # Semantic HTML
        # --------------------------------------------------

        if element.name == "nav":
            score += 10

        # --------------------------------------------------
        # ARIA
        # --------------------------------------------------

        aria_label = (
            element.get(
                "aria-label",
                ""
            )
            or ""
        ).lower()

        if "navigation" in aria_label:
            score += 5

        if "main" in aria_label:
            score += 5

        if "menu" in aria_label:
            score += 5

        # --------------------------------------------------
        # ID
        # --------------------------------------------------

        element_id = (
            element.get(
                "id",
                ""
            )
            or ""
        ).lower()

        if any(
            keyword in element_id
            for keyword in
            self.NAVIGATION_ID_KEYWORDS
        ):
            score += 5

        # --------------------------------------------------
        # Classes
        # --------------------------------------------------

        classes = {
            class_name.lower()
            for class_name in element.get(
                "class",
                []
            )
        }

        if any(
            class_name in classes
            for class_name in
            self.NAVIGATION_CLASSES
        ):
            score += 5

        # --------------------------------------------------
        # Footer penalty
        # --------------------------------------------------

        if any(
            "footer" in value
            for value in classes
        ):
            score -= 2

        return max(
            score,
            0
        )