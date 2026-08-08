class NavigationRedundancyDecision:

    def decide(
        self,
        redundancy_result,
        candidate_a,
        candidate_b,
    ):
        """
        Decide whether a navigation candidate should
        be treated as redundant or preserved.

        This layer sits ABOVE the raw redundancy analyzer.

        Raw similarity does NOT automatically mean
        redundant data.
        """

        relationship = (
            redundancy_result["relationship"]
        )

        structure = (
            redundancy_result["structure"]
        )

        containment = (
            redundancy_result["containment"]
        )

        coverage = (
            redundancy_result["coverage"]
        )

        type_a = (
            candidate_a.navigation_type
        )

        type_b = (
            candidate_b.navigation_type
        )

        links_a = candidate_a.link_count
        links_b = candidate_b.link_count

        # --------------------------------------------------
        # EXACT DUPLICATE
        # --------------------------------------------------
        #
        # Same links and same information.
        #
        # This is the strongest redundancy signal.
        # --------------------------------------------------

        if relationship == "duplicate":

            return {
                "decision": "redundant",
                "reason": "exact_duplicate",
                "confidence": 1.0,
            }

        # --------------------------------------------------
        # STRUCTURAL RELATIONSHIP
        # --------------------------------------------------
        #
        # A parent containing a smaller child menu is
        # usually legitimate hierarchy, NOT redundancy.
        # --------------------------------------------------

        if relationship == "structural_duplicate":

            if structure in {
                "direct_parent",
                "ancestor",
            }:

                return {
                    "decision": "keep_both",
                    "reason": "legitimate_child_navigation",
                    "confidence": 0.90,
                }

            if structure in {
                "direct_child",
                "descendant",
            }:

                return {
                    "decision": "keep_both",
                    "reason": "legitimate_parent_child_navigation",
                    "confidence": 0.90,
                }

        # --------------------------------------------------
        # SUBSET
        # --------------------------------------------------
        #
        # A subset is not automatically redundant.
        # It may represent a useful section of navigation.
        # --------------------------------------------------

        if relationship == "subset":

            if structure in {
                "direct_parent",
                "direct_child",
                "ancestor",
                "descendant",
            }:

                return {
                    "decision": "keep_both",
                    "reason": "hierarchical_subset",
                    "confidence": 0.90,
                }

            return {
                "decision": "keep_both",
                "reason": "independent_subset",
                "confidence": 0.75,
            }

        # --------------------------------------------------
        # OVERLAP
        # --------------------------------------------------
        #
        # Partial overlap is normally useful information.
        # Don't delete it.
        # --------------------------------------------------

        if relationship == "overlap":

            return {
                "decision": "keep_both",
                "reason": "partial_overlap",
                "confidence": 0.85,
            }

        # --------------------------------------------------
        # UNRELATED
        # --------------------------------------------------

        if relationship == "unrelated":

            return {
                "decision": "keep_both",
                "reason": "unrelated_navigation",
                "confidence": 1.0,
            }

        # --------------------------------------------------
        # FALLBACK
        # --------------------------------------------------

        return {
            "decision": "keep_both",
            "reason": "uncertain",
            "confidence": 0.50,
        }