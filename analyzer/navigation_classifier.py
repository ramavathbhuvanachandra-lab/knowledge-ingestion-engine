from models.navigation import NavigationCandidate


class NavigationClassifier:

    def classify(
        self,
        candidates: list[NavigationCandidate]
    ) -> list[NavigationCandidate]:

        for candidate in candidates:

            candidate.navigation_type = self._classify_type(
                candidate
            )

            candidate.score = self._calculate_score(
                candidate
            )

        return candidates

    def _classify_type(
        self,
        candidate: NavigationCandidate
    ) -> str:

        element = candidate.element_name.lower()

        classes = [
            value.lower()
            for value in candidate.classes
        ]

        aria = candidate.aria_label.lower()

        element_id = candidate.element_id.lower()

        # ------------------------------------------
        # Semantic navigation
        # ------------------------------------------

        if element == "nav":

            if "footer" in aria or "footer" in element_id:
                return "footer"

            return "primary"

        # ------------------------------------------
        # Footer navigation
        # ------------------------------------------

        if (
            "footer" in element_id
            or any("footer" in value for value in classes)
            or "footer" in aria
        ):
            return "footer"

        # ------------------------------------------
        # Explicit menu/navigation indicators
        # ------------------------------------------

        navigation_keywords = {
            "menu",
            "navigation",
            "navbar",
            "main-menu",
            "main-navigation",
            "primary-menu",
            "primary-navigation",
            "site-navigation",
        }

        for value in classes:

            if value in navigation_keywords:
                return "secondary"

        for keyword in navigation_keywords:

            if keyword in element_id:
                return "secondary"

        # ------------------------------------------
        # Otherwise unknown
        # ------------------------------------------

        return "unknown"

    def _calculate_score(
        self,
        candidate: NavigationCandidate
    ) -> int:

        score = 0

        element = candidate.element_name.lower()

        classes = [
            value.lower()
            for value in candidate.classes
        ]

        aria = candidate.aria_label.lower()

        element_id = candidate.element_id.lower()

        # ------------------------------------------
        # Semantic <nav>
        # ------------------------------------------

        if element == "nav":
            score += 10

        # ------------------------------------------
        # ARIA information
        # ------------------------------------------

        if aria:

            score += 5

            if "main" in aria:
                score += 5

            if "global" in aria:
                score += 5

            if "footer" in aria:
                score -= 5

        # ------------------------------------------
        # ID indicators
        # ------------------------------------------

        if element_id:

            if "nav" in element_id:
                score += 5

            if "menu" in element_id:
                score += 5

        # ------------------------------------------
        # Class indicators
        # ------------------------------------------

        navigation_keywords = {
            "navbar",
            "navigation",
            "main-menu",
            "main-navigation",
            "primary-menu",
            "primary-navigation",
            "site-navigation",
            "menu",
        }

        for value in classes:

            if value in navigation_keywords:
                score += 5

        # ------------------------------------------
        # Link count
        # ------------------------------------------

        if candidate.link_count >= 10:
            score += 5

        elif candidate.link_count >= 5:
            score += 3

        elif candidate.link_count >= 2:
            score += 1

        # ------------------------------------------
        # Footer penalty
        # ------------------------------------------

        if candidate.navigation_type == "footer":
            score -= 5

        return max(score, 0)