class NavigationStructureAnalyzer:

    def get_relationship(
        self,
        element_a,
        element_b
    ) -> str:

        if element_a is None or element_b is None:
            return "unknown"

        # Same HTML element
        if element_a is element_b:
            return "same"

        # ------------------------------------------
        # Direct parent / child
        # ------------------------------------------

        if element_b.parent is element_a:
            return "direct_parent"

        if element_a.parent is element_b:
            return "direct_child"

        # ------------------------------------------
        # Deeper ancestor / descendant
        # ------------------------------------------

        if element_b in element_a.descendants:
            return "ancestor"

        if element_a in element_b.descendants:
            return "descendant"

        # ------------------------------------------
        # Neither contains the other
        # ------------------------------------------

        return "sibling"