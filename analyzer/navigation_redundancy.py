from analyzer.navigation_relationship import (
    calculate_containment,
    calculate_coverage,
)

from analyzer.navigation_structure import (
    NavigationStructureAnalyzer,
)


class NavigationRedundancyAnalyzer:

    def __init__(self):
        self.structure_analyzer = NavigationStructureAnalyzer()

    def analyze(
        self,
        candidate_a,
        candidate_b,
        element_a=None,
        element_b=None,
    ):
        """
        Compare two navigation candidates.

        Possible relationships:
        - duplicate
        - structural_duplicate
        - subset
        - overlap
        - unrelated
        """

        links_a = candidate_a.links
        links_b = candidate_b.links

        # --------------------------------------------------
        # DOM relationship
        # --------------------------------------------------

        if (
            element_a is not None
            and element_b is not None
        ):
            structure_relationship = (
                self.structure_analyzer.get_relationship(
                    element_a,
                    element_b
                )
            )
        else:
            structure_relationship = "unknown"

        # --------------------------------------------------
        # Empty candidates
        # --------------------------------------------------

        if not links_a or not links_b:

            return {
                "relationship": "unrelated",
                "containment": 0.0,
                "coverage": 0.0,
                "structure": structure_relationship,
                "redundant": False,
            }

        # --------------------------------------------------
        # Calculate link similarity
        # --------------------------------------------------

        containment = calculate_containment(
            links_a,
            links_b
        )

        coverage = calculate_coverage(
            links_a,
            links_b
        )

        # --------------------------------------------------
        # Exact duplicate
        # --------------------------------------------------

        if set(links_a) == set(links_b):

            return {
                "relationship": "duplicate",
                "containment": 1.0,
                "coverage": 1.0,
                "structure": structure_relationship,
                "redundant": True,
            }

        # --------------------------------------------------
        # Structural duplicate
        #
        # Same information is contained inside a
        # parent/child DOM relationship.
        # --------------------------------------------------

        if (
            containment == 1.0
            and structure_relationship in {
                "direct_parent",
                "direct_child",
                "ancestor",
                "descendant",
            }
        ):

            return {
                "relationship": "structural_duplicate",
                "containment": containment,
                "coverage": coverage,
                "structure": structure_relationship,
                "redundant": True,
            }

        # --------------------------------------------------
        # Subset
        #
        # One candidate's links are completely contained
        # inside the other, but they are not structurally
        # related.
        # --------------------------------------------------

        if containment == 1.0:

            return {
                "relationship": "subset",
                "containment": containment,
                "coverage": coverage,
                "structure": structure_relationship,
                "redundant": False,
            }

        # --------------------------------------------------
        # Partial overlap
        # --------------------------------------------------

        if coverage > 0.0:

            return {
                "relationship": "overlap",
                "containment": containment,
                "coverage": coverage,
                "structure": structure_relationship,
                "redundant": False,
            }

        # --------------------------------------------------
        # Completely unrelated
        # --------------------------------------------------

        return {
            "relationship": "unrelated",
            "containment": containment,
            "coverage": coverage,
            "structure": structure_relationship,
            "redundant": False,
        }
