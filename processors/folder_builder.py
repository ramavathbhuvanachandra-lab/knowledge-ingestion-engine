from urllib.parse import urlparse


class FolderBuilder:

    def get_folder(self, page):

        path = urlparse(page.url).path.lower()

        # Admissions
        if "admission-postgraduate" in path:
            return "admissions/postgraduate"

        if "bachelor-of-technology" in path:
            return "admissions/undergraduate"

        if "phd" in path:
            return "admissions/phd"

        # Departments
        if "electrical-engineering" in path:
            return "departments/electrical"

        if "ece" in path:
            return "departments/ece"

        if "computer-science" in path:
            return "departments/cse"

        if "mechanical" in path:
            return "departments/mechanical"

        # Offices
        if "office-of-" in path:
            return "administration"

        return "others"