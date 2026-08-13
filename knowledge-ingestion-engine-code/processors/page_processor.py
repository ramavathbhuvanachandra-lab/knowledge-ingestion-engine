from processors.knowledge_organizer import KnowledgeOrganizer
from processors.filename_generator import FilenameGenerator
from storage.saver import save_page
from utils import get_domain


class PageProcessor:
    """
    Converts crawled PageData into organized knowledge files.
    """

    def __init__(
        self,
        base_path="storage/output",
    ):
        self.organizer = KnowledgeOrganizer()
        self.filename_generator = FilenameGenerator()
        self.base_path = base_path

    def process(self, page):
        """
        Process and persist a crawled page.
        """

        domain = get_domain(
            page.url
        )

        category, _ = (
            self.organizer.get_save_location(
                page
            )
        )

        filename = (
            self.filename_generator.generate(
                page
            )
        )

        return save_page(
            page=page,
            domain=domain,
            category=category,
            filename=filename,
            base_path=self.base_path,
        )