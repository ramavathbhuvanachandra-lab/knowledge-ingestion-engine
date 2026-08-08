from bs4 import BeautifulSoup, Tag

from models.navigation import NavigationNode


class NavigationTreeExtractor:

    def extract(
        self,
        element: Tag
    ) -> list[NavigationNode]:

        if element is None:
            return []

        return self._extract_children(
            element
        )

    # ==================================================
    # Extract direct navigation children
    # ==================================================

    def _extract_children(
        self,
        container: Tag
    ) -> list[NavigationNode]:

        nodes = []

        # Look through the container's direct
        # structural children.
        for child in container.children:

            if not isinstance(child, Tag):
                continue

            # --------------------------------------------------
            # Direct link
            # --------------------------------------------------

            if child.name == "a":

                node = self._build_node(
                    child
                )

                if node:
                    nodes.append(node)

                continue

            # --------------------------------------------------
            # List container
            # --------------------------------------------------

            if child.name in {
                "ul",
                "ol"
            }:

                nodes.extend(
                    self._extract_list(
                        child
                    )
                )

                continue

            # --------------------------------------------------
            # Non-link wrapper
            # --------------------------------------------------

            nodes.extend(
                self._extract_children(
                    child
                )
            )

        return nodes

    # ==================================================
    # Extract <ul>/<ol>
    # ==================================================

    def _extract_list(
        self,
        list_element: Tag
    ) -> list[NavigationNode]:

        nodes = []

        for item in list_element.find_all(
            "li",
            recursive=False
        ):

            node = self._extract_list_item(
                item
            )

            if node:
                nodes.append(node)

        return nodes

    # ==================================================
    # Extract <li>
    # ==================================================

    def _extract_list_item(
        self,
        item: Tag
    ):

        link = item.find(
            "a",
            recursive=False
        )

        # --------------------------------------------------
        # No direct <a>
        #
        # The li may contain a wrapper.
        # --------------------------------------------------

        if link is None:

            for child in item.children:

                if not isinstance(
                    child,
                    Tag
                ):
                    continue

                link = child.find(
                    "a",
                    recursive=False
                )

                if link is not None:
                    break

        # --------------------------------------------------
        # No link = not a navigation node
        # --------------------------------------------------

        if link is None:
            return None

        node = self._build_node(
            link
        )

        if node is None:
            return None

        # --------------------------------------------------
        # Find nested submenu
        # --------------------------------------------------

        nested_lists = item.find_all(
            ["ul", "ol"],
            recursive=False
        )

        for nested_list in nested_lists:

            children = self._extract_list(
                nested_list
            )

            node.children.extend(
                children
            )

        return node

    # ==================================================
    # Build node
    # ==================================================

    def _build_node(
        self,
        link: Tag
    ):

        text = link.get_text(
            " ",
            strip=True
        )

        if not text:
            return None

        # --------------------------------------------------
        # Ignore accessibility skip links
        # --------------------------------------------------

        normalized = text.lower()

        if (
            "skip to content"
            in normalized
            or
            "skip to main content"
            in normalized
            or
            "skip navigation"
            in normalized
        ):
            return None

        href = link.get(
            "href",
            ""
        )

        return NavigationNode(
            text=text,
            href=href,
            children=[]
        )