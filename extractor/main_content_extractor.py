class MainContentExtractor:

    # Common content container classes used by different websites/CMS
    CONTENT_CLASSES = [
        "main-content",
        "page-content",
        "article-content",
        "entry-content",
        "post-content",
        "content",
    ]

    # Elements that are normally not knowledge content
    BOILERPLATE_TAGS = [
        "header",
        "nav",
        "footer",
        "aside",
        "script",
        "style",
        "noscript",
    ]

    def __init__(self, soup):

        self.soup = soup

    def extract(self) -> str:

        # Strategy 1: <main>
        main = self.soup.find("main")

        if main:
            content = self._extract_text(main)

            if content:
                return content

        # Strategy 2: <article>
        article = self.soup.find("article")

        if article:
            content = self._extract_text(article)

            if content:
                return content

        # Strategy 3: Common content classes
        for class_name in self.CONTENT_CLASSES:

            element = self.soup.find(
                class_=class_name
            )

            if element:
                content = self._extract_text(element)

                if content:
                    return content

        # Strategy 4: Largest meaningful container
        container = self._find_largest_container()

        if container:
            content = self._extract_text(container)

            if content:
                return content

        # Strategy 5: Body fallback
        body = self.soup.find("body")

        if body:

            content = self._extract_text(body)

            if content:
                return content

        # Strategy 6: Nothing useful found
        return ""

    def _extract_text(self, element) -> str:

        self._remove_boilerplate(element)

        text = element.get_text(
            "\n",
            strip=True
        )

        return text

    def _remove_boilerplate(self, element):

        # Remove obvious boilerplate HTML elements
        for tag_name in self.BOILERPLATE_TAGS:

            for element_to_remove in element.find_all(tag_name):

                element_to_remove.decompose()

        # Remove elements explicitly marked as navigation
        for element_to_remove in element.select(
            '[role="navigation"]'
        ):

            element_to_remove.decompose()

        # Remove elements explicitly marked as navigation
        for element_to_remove in element.select(
            '[aria-label*="navigation" i]'
        ):

            element_to_remove.decompose()

        # Remove common "skip navigation" links
        for element_to_remove in element.select(
            ".skip-link, .skip-to-content"
        ):

            element_to_remove.decompose()

    def _find_largest_container(self):

        candidates = self.soup.find_all(
            ["div", "section"]
        )

        if not candidates:
            return None

        best_element = None
        best_length = 0

        for element in candidates:

            text = element.get_text(
                " ",
                strip=True
            )


            text_length = len(text)

            if text_length > best_length:

                best_length = text_length
                best_element = element

        return best_element