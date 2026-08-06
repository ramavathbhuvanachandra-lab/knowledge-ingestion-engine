from pathlib import Path
from urllib.parse import urlparse


class KnowledgeOrganizer:

    def __init__(self, base_path="storage/output"):
        self.base_path = Path(base_path)

    def get_save_location(self, page):

        url = page.url.lower()

        category = "others"
        filename = "page"

        if "electrical" in url:
            category = "departments/electrical"

        elif "computer" in url or "cse" in url:
            category = "departments/cse"

        elif "hostel" in url:
            category = "hostel"

        elif "admission" in url:
            category = "admissions"

        elif "academics" in url:
            category = "academics"

        elif "faculty" in url:
            category = "faculty"

        elif "research" in url:
            category = "research"

        parsed = urlparse(url)

        parts = [
            p for p in parsed.path.split("/")
            if p
        ]

        if len(parts):
            filename = "_".join(parts)

        return category, filename