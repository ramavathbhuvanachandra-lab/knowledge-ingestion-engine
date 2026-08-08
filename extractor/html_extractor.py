from bs4 import BeautifulSoup


class HTMLExtractor:

    # Heading class names used by different websites/CMS
    HEADING_CLASSES = [
        "page-title",
        "article-title",
        "entry-title",
        "main-title",
        "hero-title",
        "content-title",
        "post-title",
        "title",
    ]

    # Common text that should never be treated as the page heading
    INVALID_HEADINGS = {
        "footer",
        "header",
        "navigation",
        "menu",
        "navbar",
        "sidebar",
    }

    def __init__(self, html: str):

        self.soup = BeautifulSoup(
            html,
            "html.parser"
        )

    def extract_heading(self) -> str:

        # Strategy 1: <h1>
        h1 = self.soup.find("h1")

        if h1:

            heading = h1.get_text(
                " ",
                strip=True
            )

            if self._is_valid_heading(heading):
                return heading

        # Strategy 2: <h2>
        h2 = self.soup.find("h2")

        if h2:

            heading = h2.get_text(
                " ",
                strip=True
            )

            if self._is_valid_heading(heading):
                return heading

        # Strategy 3: Common heading classes
        for class_name in self.HEADING_CLASSES:

            element = self.soup.find(
                class_=class_name
            )

            if element:

                heading = element.get_text(
                    " ",
                    strip=True
                )

                if self._is_valid_heading(heading):
                    return heading

        # Strategy 4: HTML title
        title = self.soup.find("title")

        if title:

            title_text = title.get_text(
                " ",
                strip=True
            )

            return self._clean_title(title_text)

        # Strategy 5: Nothing found
        return ""

    def _is_valid_heading(self, heading: str) -> bool:

        if not heading:
            return False

        return heading.lower() not in self.INVALID_HEADINGS

    def _clean_title(self, title: str) -> str:

        if not title:
            return ""

        # Remove common website-name suffixes
        separators = [
            " | ",
            " - ",
            " — ",
            " – ",
        ]

        for separator in separators:

            if separator in title:

                return title.split(
                    separator,
                    1
                )[0].strip()

        return title.strip()

    def extract_breadcrumbs(self) -> list[str]:

        # Strategy 1: <nav aria-label="breadcrumb">
        breadcrumb = self.soup.find(
            "nav",
            attrs={
                "aria-label": lambda value:
                value and "breadcrumb" in value.lower()
            }
        )

        if breadcrumb:

            items = self._extract_breadcrumb_items(
                breadcrumb
            )

            if items:
                return items

        # Strategy 2: Common breadcrumb classes
        for class_name in [
            "breadcrumb",
            "breadcrumbs",
        ]:

            element = self.soup.find(
                class_=class_name
            )

            if element:

                items = self._extract_breadcrumb_items(
                    element
                )

                if items:
                    return items

        # Strategy 3: Any class containing "breadcrumb"
        element = self.soup.find(
            class_=lambda value:
            value and any(
                "breadcrumb" in class_name.lower()
                for class_name in value
            ) if isinstance(value, list) else
            value and "breadcrumb" in value.lower()
        )

        if element:

            items = self._extract_breadcrumb_items(
                element
            )

            if items:
                return items

        # Strategy 4: aria-label containing breadcrumb
        element = self.soup.find(
            attrs={
                "aria-label": lambda value:
                value and "breadcrumb" in value.lower()
            }
        )

        if element:

            items = self._extract_breadcrumb_items(
                element
            )

            if items:
                return items

        # Strategy 5: No breadcrumbs found
        return []

    def _extract_breadcrumb_items(self, element) -> list[str]:

        # Strategy 1: List-based breadcrumbs
        list_items = element.find_all("li")

        if list_items:

            items = []

            for item in list_items:

                text = item.get_text(
                    " ",
                    strip=True
                )

                if text:
                    items.append(text)

            return self._clean_breadcrumb_items(items)

        # Strategy 2: Direct breadcrumb elements
        items = []

        for child in element.find_all(
            ["a", "span"],
            recursive=False
        ):

            text = child.get_text(
                " ",
                strip=True
            )

            if text:
                items.append(text)

        if items:
            return self._clean_breadcrumb_items(items)

        # Strategy 3: Fallback to links
        links = element.find_all("a")

        if links:

            items = []

            for link in links:

                text = link.get_text(
                    " ",
                    strip=True
                )

                if text:
                    items.append(text)

            return self._clean_breadcrumb_items(items)

        # Final fallback: complete element text
        text = element.get_text(
            " ",
            strip=True
        )

        if text:
            return self._clean_breadcrumb_items([text])

        return []

    def _clean_breadcrumb_items(
        self,
        items: list[str]
    ) -> list[str]:

        cleaned = []

        # Common breadcrumb separators
        separators = {
            "/",
            ">",
            "›",
            "»",
            "|",
            "→",
        }

        for item in items:

            item = item.strip()

            if not item:
                continue

            # Remove separator-only items
            if item in separators:
                continue

            # Avoid duplicate breadcrumb items
            if item not in cleaned:
                cleaned.append(item)

        return cleaned