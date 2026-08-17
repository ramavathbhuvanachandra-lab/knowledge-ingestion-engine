from processors.filename_generator import FilenameGenerator
from storage.saver import save_page
from utils import get_domain


class PageProcessor:
    """
    Converts crawled PageData into raw knowledge files.

    This processor is responsible only for saving freshly
    crawled webpage content.

    Semantic organization is handled later by the knowledge
    organization pipeline. The crawler therefore does not
    make site-specific assumptions about categories.
    """

    RAW_PAGE_CATEGORY = "pages"

    def __init__(
        self,
        base_path="storage/output",
    ):
        self.filename_generator = (
            FilenameGenerator()
        )
        self.base_path = base_path

    def process(self, page):
        """
        Process and persist a crawled page.
        """

        domain = get_domain(
            page.url
        )

        filename = (
            self.filename_generator.generate(
                page
            )
        )

        return save_page(
            page=page,
            domain=domain,
            category=self.RAW_PAGE_CATEGORY,
            filename=filename,
            base_path=self.base_path,
        )