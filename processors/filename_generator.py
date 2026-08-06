import re


class FilenameGenerator:

    def generate(self, page):

        title = page.title

        # Remove anything after |
        title = title.split("|")[0]

        # Remove anything after -
        title = title.split("-")[0]

        # Lowercase
        title = title.lower()

        # Replace spaces with underscores
        title = title.replace(" ", "_")

        # Keep only letters, numbers and underscores
        title = re.sub(r"[^a-z0-9_]", "", title)

        # Remove duplicate underscores
        title = re.sub(r"_+", "_", title)

        # Remove leading/trailing underscores
        title = title.strip("_")

        if not title:
            title = "page"

        return title