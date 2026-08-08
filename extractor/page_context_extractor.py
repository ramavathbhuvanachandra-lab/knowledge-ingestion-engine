from parser.url_parser import URLParser
from models.page_context import PageContext
from extractor.html_extractor import HTMLExtractor
from extractor.main_content_extractor import MainContentExtractor


class PageContextExtractor:

    def __init__(self):
        self.url_parser = URLParser()

    def extract(self, page):

        # Parse URL
        url_structure = self.url_parser.parse(page.url)

        # Parse HTML once
        html_extractor = HTMLExtractor(page.html)

        # Extract page heading
        heading = html_extractor.extract_heading()

        # Extract breadcrumbs
        breadcrumbs = html_extractor.extract_breadcrumbs()

        # Extract main page content
        main_content_extractor = MainContentExtractor(
            html_extractor.soup
        )

        main_content = main_content_extractor.extract()

        # Build Page Context
        return PageContext(
            url=page.url,
            domain=url_structure.domain,
            title=page.title,
            h1=heading,
            main_content=main_content,
            url_segments=url_structure.segments,
            breadcrumbs=breadcrumbs,
            navigation=[],
            language="",
            depth=url_structure.depth
        )