class NavigationHierarchyBuilder:

    def build(
        self,
        candidates,
        relationships
    ):
        """
        Build a navigation hierarchy by assigning each
        candidate to its closest candidate ancestor.
        """

        # --------------------------------------------------
        # Create nodes
        # --------------------------------------------------

        nodes = {}

        for candidate in candidates:

            nodes[candidate["id"]] = {
                "id": candidate["id"],
                "children": []
            }

        # --------------------------------------------------
        # Find possible parents for each candidate
        # --------------------------------------------------

        possible_parents = {}

        for relationship in relationships:

            parent_id = relationship["a"]
            child_id = relationship["b"]

            relationship_type = (
                relationship["relationship"]
            )

            if parent_id == child_id:
                continue

            if relationship_type not in {
                "direct_parent",
                "ancestor"
            }:
                continue

            if child_id not in possible_parents:

                possible_parents[child_id] = []

            possible_parents[child_id].append(
                parent_id
            )

        # --------------------------------------------------
        # Build lookup for candidates
        # --------------------------------------------------

        candidate_lookup = {}

        for candidate in candidates:

            candidate_lookup[
                candidate["id"]
            ] = candidate

        # --------------------------------------------------
        # Calculate DOM depth
        # --------------------------------------------------

        def get_depth(element):

            depth = 0

            current = element

            while current.parent is not None:

                depth += 1

                current = current.parent

            return depth

        # --------------------------------------------------
        # Assign closest candidate parent
        # --------------------------------------------------

        has_parent = set()

        for child_id, parent_ids in (
            possible_parents.items()
        ):

            if not parent_ids:
                continue

            # Choose the candidate that is deepest
            # in the DOM tree.
            parent_id = max(
                parent_ids,
                key=lambda candidate_id:
                    get_depth(
                        candidate_lookup[
                            candidate_id
                        ]["element"]
                    )
            )

            # Prevent self-parenting
            if parent_id == child_id:
                continue

            nodes[parent_id]["children"].append(
                nodes[child_id]
            )

            has_parent.add(
                child_id
            )

        # --------------------------------------------------
        # Find root candidates
        # --------------------------------------------------

        roots = []

        for candidate in candidates:

            candidate_id = candidate["id"]

            if candidate_id not in has_parent:

                roots.append(
                    nodes[candidate_id]
                )

        return roots