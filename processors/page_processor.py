from processors.knowledge_organizer import KnowledgeOrganizer
from processors.filename_generator import FilenameGenerator

from storage.saver import save_page
from utils import get_domain


class PageProcessor:

    def __init__(self):
        self.organizer = KnowledgeOrganizer()
        self.filename_generator = FilenameGenerator()

    def process(self, page):

        domain = get_domain(page.url)

        # Organizer decides WHERE to save
        category, _ = self.organizer.get_save_location(page)

        # FilenameGenerator decides WHAT to call the file
        filename = self.filename_generator.generate(page)

        save_page(
            page=page,
            domain=domain,
            category=category,
            filename=filename
        )