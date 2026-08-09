import re
from urllib.parse import parse_qsl, urlparse


class FilenameGenerator:
    """
    Generates deterministic, human-readable base filenames.

    Collision handling is intentionally NOT performed here.

    Example:

        https://iitj.ac.in/admissions/programs

        -> admissions_programs

    The storage layer adds a deterministic hash only when
    another URL already occupies the same filename.
    """

    MAX_LENGTH = 120

    def generate(self, page) -> str:
        """
        Generate a readable filename from page title and URL.
        """

        title = self._clean_title(
            getattr(page, "title", "")
        )

        url = (getattr(page, "url", "") or "").strip()

        if title:
            return self._limit(title)

        identity = self._build_url_identity(url)

        return self._limit(identity)

    # ------------------------------------------------------------
    # TITLE
    # ------------------------------------------------------------

    def _clean_title(self, title: str) -> str:
        """
        Convert a page title into a readable filename.
        """

        if not title:
            return ""

        title = title.strip()

        # Remove common website branding.
        separators = (
            " | ",
            " - ",
            " — ",
            " :: ",
        )

        for separator in separators:
            if separator in title:
                title = title.split(separator, 1)[0]

        title = title.lower()

        title = re.sub(
            r"[^a-z0-9]+",
            "_",
            title,
        )

        title = re.sub(
            r"_+",
            "_",
            title,
        )

        return title.strip("_")

    # ------------------------------------------------------------
    # URL IDENTITY
    # ------------------------------------------------------------

    def _build_url_identity(self, url: str) -> str:
        """
        Build a readable identity from URL path and query.
        """

        if not url:
            return "page"

        parsed = urlparse(url)

        segments = [
            self._clean_segment(segment)
            for segment in parsed.path.split("/")
            if segment
        ]

        segments = [
            segment
            for segment in segments
            if segment
        ]

        if not segments:
            identity = "home"
        else:
            identity = "_".join(segments)

        query_parts = []

        for key, value in parse_qsl(
            parsed.query,
            keep_blank_values=True,
        ):
            key = self._clean_segment(key)
            value = self._clean_segment(value)

            if key:
                if value:
                    query_parts.append(
                        f"{key}_{value}"
                    )
                else:
                    query_parts.append(key)

        if query_parts:
            identity = "_".join(
                [identity, *query_parts]
            )

        return identity or "page"

    def _clean_segment(self, value: str) -> str:
        value = value.lower()

        value = re.sub(
            r"[^a-z0-9]+",
            "_",
            value,
        )

        value = re.sub(
            r"_+",
            "_",
            value,
        )

        return value.strip("_")

    def _limit(self, value: str) -> str:
        value = value.strip("_")

        if not value:
            return "page"

        return value[:self.MAX_LENGTH].rstrip("_") or "page"