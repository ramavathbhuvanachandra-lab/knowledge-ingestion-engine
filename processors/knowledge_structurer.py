from pathlib import Path
import json
import re
from urllib.parse import urlparse


class KnowledgeStructurer:
    """
    Phase 7.4:
    Convert cleaned knowledge Markdown into
    deterministic semantic structure.

    Responsibilities:

    - Read cleaned Markdown + metadata.
    - Detect page boundaries.
    - Detect Markdown headings.
    - Group content under headings.
    - Preserve paragraphs, lists, tables and links.
    - Preserve source metadata.
    - Determine domain safely.
    - Classify sections conservatively.
    - Do not chunk.
    - Do not embed.
    - Do not use an LLM.
    """

    def __init__(
        self,
        output_path: str | Path = "storage/structured_knowledge",
    ):
        self.output_path = Path(output_path)

    # --------------------------------------------------------
    # PUBLIC API
    # --------------------------------------------------------

    def structure(
        self,
        markdown_path: str | Path,
        metadata_path: str | Path,
    ) -> tuple[Path, Path]:

        markdown_path = Path(markdown_path)
        metadata_path = Path(metadata_path)

        self._validate_input(
            markdown_path,
            metadata_path,
        )

        markdown = markdown_path.read_text(
            encoding="utf-8"
        )

        metadata = json.loads(
            metadata_path.read_text(
                encoding="utf-8"
            )
        )

        if not markdown.strip():
            raise ValueError(
                f"Markdown is empty: {markdown_path}"
            )

        # ----------------------------------------------------
        # PARSE CONTENT
        # ----------------------------------------------------

        pages = self._parse_pages(
            markdown
        )

        # ----------------------------------------------------
        # DOCUMENT METADATA
        # ----------------------------------------------------

        source_url = (
            metadata.get("url")
            or metadata.get("source_url")
        )

        domain = (
            metadata.get("storage_domain")
            or metadata.get("domain")
        )

        category = (
            metadata.get("storage_category")
            or metadata.get("category")
            or "others"
        )

        # ----------------------------------------------------
        # DERIVE DOMAIN FROM SOURCE URL
        # ----------------------------------------------------

        if not domain and source_url:

            parsed = urlparse(
                source_url
            )

            domain = parsed.netloc

        if not domain:

            raise ValueError(
                "Unable to determine domain for: "
                f"{markdown_path}"
            )

        # ----------------------------------------------------
        # CLEAN STORAGE COMPONENTS
        # ----------------------------------------------------

        domain = self._clean_component(
            domain
        )

        category = self._clean_component(
            category
        )

        # ----------------------------------------------------
        # BUILD STRUCTURE
        # ----------------------------------------------------

        structure = {
            "document": {
                "title": metadata.get(
                    "title"
                ),
                "url": source_url,
                "domain": domain,
                "category": category,
                "document_type": metadata.get(
                    "document_type",
                    "webpage",
                ),
                "source_file": metadata.get(
                    "source_file"
                ),
            },
            "pages": pages,
        }

        # ----------------------------------------------------
        # OUTPUT DIRECTORY
        # ----------------------------------------------------

        output_dir = (
            self.output_path
            / domain
            / category
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        # ----------------------------------------------------
        # OUTPUT FILE
        # ----------------------------------------------------

        output_file = (
            output_dir
            / f"{markdown_path.stem}.json"
        )

        output_file.write_text(
            json.dumps(
                structure,
                indent=4,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        # ----------------------------------------------------
        # LOGGING
        # ----------------------------------------------------

        print(
            f"Structured JSON : {output_file}"
        )

        print(
            f"Pages           : {len(pages)}"
        )

        print(
            f"Sections        : "
            f"{self._count_sections(pages)}"
        )

        return (
            output_file,
            metadata_path,
        )

    # --------------------------------------------------------
    # INPUT VALIDATION
    # --------------------------------------------------------

    def _validate_input(
        self,
        markdown_path: Path,
        metadata_path: Path,
    ) -> None:

        if not markdown_path.exists():
            raise FileNotFoundError(
                f"Markdown file does not exist: "
                f"{markdown_path}"
            )

        if not markdown_path.is_file():
            raise ValueError(
                f"Markdown path is not a file: "
                f"{markdown_path}"
            )

        if not metadata_path.exists():
            raise FileNotFoundError(
                f"Metadata file does not exist: "
                f"{metadata_path}"
            )

        if not metadata_path.is_file():
            raise ValueError(
                f"Metadata path is not a file: "
                f"{metadata_path}"
            )

    # --------------------------------------------------------
    # PAGE PARSING
    # --------------------------------------------------------

    def _parse_pages(
        self,
        markdown: str,
    ) -> list[dict]:

        lines = markdown.splitlines()

        pages = []
        current_page = None

        for line in lines:

            page_match = re.match(
                r"^##\s+Page\s+(\d+)\s*$",
                line.strip(),
                flags=re.IGNORECASE,
            )

            if page_match:

                if current_page is not None:

                    self._finalize_page(
                        current_page
                    )

                    pages.append(
                        current_page
                    )

                current_page = {
                    "page_number": int(
                        page_match.group(1)
                    ),
                    "sections": [],
                }

                continue

            # ------------------------------------------------
            # WEBPAGE WITHOUT PAGE MARKERS
            # ------------------------------------------------

            if current_page is None:

                current_page = {
                    "page_number": None,
                    "sections": [],
                }

            self._consume_line(
                current_page,
                line,
            )

        # ----------------------------------------------------
        # FINAL PAGE
        # ----------------------------------------------------

        if current_page is not None:

            self._finalize_page(
                current_page
            )

            pages.append(
                current_page
            )

        return pages

    # --------------------------------------------------------
    # LINE PARSING
    # --------------------------------------------------------

    def _consume_line(
        self,
        page: dict,
        line: str,
    ) -> None:

        stripped = line.strip()

        if not stripped:
            return

        # ----------------------------------------------------
        # MARKDOWN HEADING
        # ----------------------------------------------------

        heading_match = re.match(
            r"^(#{1,6})\s+(.+?)\s*$",
            stripped,
        )

        if heading_match:

            level = len(
                heading_match.group(1)
            )

            heading = (
                heading_match
                .group(2)
                .strip()
            )

            page["sections"].append(
                {
                    "heading": heading,
                    "level": level,
                    "content": [],
                }
            )

            return

        # ----------------------------------------------------
        # CONTENT BEFORE FIRST HEADING
        # ----------------------------------------------------

        if not page["sections"]:

            page["sections"].append(
                {
                    "heading": None,
                    "level": 0,
                    "content": [],
                }
            )

        page["sections"][-1][
            "content"
        ].append(
            stripped
        )

    # --------------------------------------------------------
    # PAGE FINALIZATION
    # --------------------------------------------------------

    def _finalize_page(
        self,
        page: dict,
    ) -> None:

        cleaned_sections = []

        for section in page["sections"]:

            content = self._normalize_content(
                section["content"]
            )

            # Skip completely empty sections.

            if (
                not section["heading"]
                and not content
            ):
                continue

            content_text = "\n".join(
                content
            )

            cleaned_sections.append(
                {
                    "heading": section[
                        "heading"
                    ],
                    "level": section[
                        "level"
                    ],
                    "content": content,
                    "content_type": (
                        self._classify_section(
                            section["heading"],
                            content_text,
                        )
                    ),
                    "content_length": len(
                        content_text
                    ),
                    "content_items": len(
                        content
                    ),
                }
            )

        page["sections"] = (
            cleaned_sections
        )

    # --------------------------------------------------------
    # SECTION CLASSIFICATION
    # --------------------------------------------------------

    def _classify_section(
        self,
        heading: str | None,
        content: str,
    ) -> str:
        """
        Conservatively classify a section.

        This does NOT delete content.

        The classification is metadata for downstream
        processing stages such as chunking and retrieval.

        Possible values:

        - knowledge
        - navigation
        - accessibility
        """

        heading_text = (
            heading or ""
        ).strip().lower()

        content_text = (
            content or ""
        ).strip().lower()

        # ----------------------------------------------------
        # ACCESSIBILITY / UI CONTENT
        # ----------------------------------------------------

        accessibility_terms = (
            "accessibility",
            "accessibility options",
            "ux4g",
            "bigger text",
            "smaller text",
            "dyslexia",
            "adhd mode",
            "saturation",
            "invert colors",
            "text to speech",
        )

        if any(
            term in heading_text
            for term in accessibility_terms
        ):
            return "accessibility"

        # ----------------------------------------------------
        # NAVIGATION HEADING
        # ----------------------------------------------------

        navigation_terms = (
            "navigation",
            "menu",
            "main menu",
            "footer",
            "important links",
            "quick links",
            "students login",
            "admin login",
            "login close",
            "designed, developed and maintained",
        )

        if any(
            term in heading_text
            or term in content_text
            for term in navigation_terms
        ):
            return "navigation"

        # ----------------------------------------------------
        # LINK-HEAVY CONTENT
        # ----------------------------------------------------

        lines = [
            line.strip()
            for line in content.splitlines()
            if line.strip()
        ]

        if lines:

            link_lines = sum(
                1
                for line in lines
                if (
                    "http://" in line
                    or "https://" in line
                    or "](" in line
                )
            )

            link_ratio = (
                link_lines / len(lines)
            )

            if link_ratio >= 0.80:
                return "navigation"

        # ----------------------------------------------------
        # DEFAULT
        # ----------------------------------------------------

        return "knowledge"

    # --------------------------------------------------------
    # CONTENT NORMALIZATION
    # --------------------------------------------------------

    def _normalize_content(
        self,
        content: list[str],
    ) -> list[str]:

        result = []

        for line in content:

            line = line.strip()

            if not line:
                continue

            line = re.sub(
                r"\s+",
                " ",
                line,
            )

            result.append(
                line
            )

        return result

    # --------------------------------------------------------
    # SECTION COUNT
    # --------------------------------------------------------

    def _count_sections(
        self,
        pages: list[dict],
    ) -> int:

        return sum(
            len(
                page["sections"]
            )
            for page in pages
        )

    # --------------------------------------------------------
    # SAFE PATH COMPONENT
    # --------------------------------------------------------

    def _clean_component(
        self,
        value: str,
    ) -> str:

        value = (
            value or ""
        ).strip().lower()

        cleaned = []

        for character in value:

            if (
                character.isalnum()
                or character in "._-"
            ):
                cleaned.append(
                    character
                )

            else:
                cleaned.append(
                    "_"
                )

        result = "".join(
            cleaned
        )

        while "__" in result:

            result = result.replace(
                "__",
                "_",
            )

        return (
            result.strip("._-")
            or "unknown"
        )