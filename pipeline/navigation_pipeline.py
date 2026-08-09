from extractor.navigation_extractor import NavigationExtractor

from analyzer.navigation_redundancy import (
    NavigationRedundancyAnalyzer,
)

from analyzer.navigation_redundancy_decision import (
    NavigationRedundancyDecision,
)

from analyzer.navigation_tree import (
    NavigationTreeExtractor,
)


class NavigationPipeline:

    def __init__(self, soup):

        self.soup = soup

        self.extractor = NavigationExtractor(
            soup
        )

        self.redundancy_analyzer = (
            NavigationRedundancyAnalyzer()
        )

        self.redundancy_decision = (
            NavigationRedundancyDecision()
        )

        self.tree_extractor = (
            NavigationTreeExtractor()
        )

    def run(self):

        # ==================================================
        # 1. Discover navigation candidates
        # ==================================================

        candidates = (
            self.extractor.discover_candidates()
        )

        raw_count = len(candidates)

        # ==================================================
        # 2. Compare every candidate pair
        # ==================================================

        redundant_ids = set()

        relationship_results = []

        for i in range(
            len(candidates)
        ):

            for j in range(
                i + 1,
                len(candidates)
            ):

                candidate_a = candidates[i]
                candidate_b = candidates[j]

                # ------------------------------------------
                # Raw redundancy analysis
                # ------------------------------------------

                analysis = (
                    self.redundancy_analyzer.analyze(
                        candidate_a,
                        candidate_b,
                        candidate_a.element,
                        candidate_b.element,
                    )
                )

                # ------------------------------------------
                # Higher-level redundancy decision
                # ------------------------------------------

                decision = (
                    self.redundancy_decision.decide(
                        analysis,
                        candidate_a,
                        candidate_b,
                    )
                )

                relationship_results.append(
                    {
                        "a": candidate_a,
                        "b": candidate_b,
                        "analysis": analysis,
                        "decision": decision,
                    }
                )

                # ------------------------------------------
                # Mark redundant candidate
                # ------------------------------------------

                if (
                    decision["decision"]
                    == "redundant"
                ):

                    redundant_id = (
                        self._choose_redundant_candidate(
                            candidate_a,
                            candidate_b,
                        )
                    )

                    redundant_ids.add(
                        redundant_id
                    )

        # ==================================================
        # 3. Remove redundant candidates
        # ==================================================

        filtered_candidates = [
            candidate
            for candidate in candidates
            if id(candidate)
            not in redundant_ids
        ]

        # ==================================================
        # 4. Build trees for final candidates
        # ==================================================

        for candidate in filtered_candidates:

            candidate.tree = (
                self.tree_extractor.extract(
                    candidate.element
                )
            )

        # ==================================================
        # 5. Return pipeline result
        # ==================================================

        return {
            "candidates": filtered_candidates,

            "raw_candidates": raw_count,

            "filtered_candidates": len(
                filtered_candidates
            ),

            "redundant_candidates": len(
                redundant_ids
            ),

            "relationships": relationship_results,
        }

    def _choose_redundant_candidate(
        self,
        candidate_a,
        candidate_b,
    ):
        """
        Decide which candidate to remove when
        two candidates are exact duplicates.

        Prefer the candidate with stronger
        navigation evidence.
        """

        # --------------------------------------------------
        # 1. Higher navigation score wins
        # --------------------------------------------------

        if (
            candidate_a.score
            > candidate_b.score
        ):

            return id(candidate_b)

        if (
            candidate_b.score
            > candidate_a.score
        ):

            return id(candidate_a)

        # --------------------------------------------------
        # 2. If scores are equal, prefer more links
        # --------------------------------------------------

        if (
            candidate_a.link_count
            > candidate_b.link_count
        ):

            return id(candidate_b)

        if (
            candidate_b.link_count
            > candidate_a.link_count
        ):

            return id(candidate_a)

        # --------------------------------------------------
        # 3. If completely equal, keep first
        # --------------------------------------------------

        return id(candidate_b)