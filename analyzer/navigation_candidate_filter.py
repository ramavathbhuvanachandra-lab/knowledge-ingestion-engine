class NavigationCandidateFilter:

    def filter(
        self,
        candidates
    ):
        """
        Remove obvious navigation noise while preserving
        candidates that contain meaningful navigation evidence.
        """

        filtered = []

        for candidate in candidates:

            if self._should_keep(candidate):

                filtered.append(candidate)

        return filtered

    def _should_keep(
        self,
        candidate
    ):
        """
        Decide whether a candidate has enough evidence
        to remain in the navigation pipeline.
        """

        element = (
            candidate.element_name
            .lower()
        )

        classes = {
            value.lower()
            for value in candidate.classes
        }

        element_id = (
            candidate.element_id
            .lower()
        )

        aria = (
            candidate.aria_label
            .lower()
        )

        navigation_type = (
            candidate.navigation_type
            .lower()
        )

        link_count = (
            candidate.link_count
        )

        score = candidate.score

        # ==================================================
        # 1. Semantic <nav>
        # ==================================================

        if element == "nav":

            return True

        # ==================================================
        # 2. Explicitly classified navigation
        # ==================================================

        if navigation_type in {
            "primary",
            "secondary",
            "footer",
            "sidebar"
        }:

            return True

        # ==================================================
        # 3. Strong navigation score
        # ==================================================

        if score >= 10:

            return True

        # ==================================================
        # 4. Explicit navigation naming
        # ==================================================

        navigation_keywords = {
            "nav",
            "navbar",
            "navigation",
            "menu",
            "main-menu",
            "main-navigation",
            "primary-menu",
            "primary-navigation",
            "site-navigation",
            "site-nav",
            "side-menu",
            "sidebar-menu",
            "footer-navigation",
            "footer-menu",
        }

        # --------------------------------------------------
        # ID
        # --------------------------------------------------

        if any(
            keyword in element_id
            for keyword in navigation_keywords
        ):

            return True

        # --------------------------------------------------
        # Classes
        # --------------------------------------------------

        if any(
            keyword in classes
            for keyword in navigation_keywords
        ):

            return True

        # --------------------------------------------------
        # ARIA
        # --------------------------------------------------

        if (
            "navigation" in aria
            or "menu" in aria
        ):

            return True

        # ==================================================
        # 5. Lists
        # ==================================================

        if element in {
            "ul",
            "ol"
        }:

            # A list with several links can represent
            # a dropdown or menu even when its class is
            # not obviously named.
            if link_count >= 3:

                return True

        # ==================================================
        # 6. Generic containers
        # ==================================================

        if element in {
            "div",
            "section",
            "article"
        }:

            # Generic containers require stronger evidence.
            if link_count >= 10 and score >= 5:

                return True

            return False

        # ==================================================
        # 7. Everything else
        # ==================================================

        return False