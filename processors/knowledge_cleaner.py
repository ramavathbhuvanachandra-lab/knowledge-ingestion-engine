from pathlib import Path
import json
import re


class KnowledgeCleaner:
    """
    Phase 7.3:
    Clean and normalize extracted knowledge documents.

    Responsibilities:

    - Read Markdown + metadata pairs.
    - Normalize whitespace.
    - Remove obvious extraction noise.
    - Preserve meaningful headings, paragraphs,
      lists, tables, and links.
    - Preserve source metadata.
    - Do not chunk.
    - Do not embed.
    - Do not modify crawler output.
    """

    def __init__(
        self,
        output_path: str | Path = "storage/knowledge",
    ):
        self.output_path = Path(output_path)

    # --------------------------------------------------------
    # PUBLIC API
    # --------------------------------------------------------

    def clean(
        self,
        markdown_path: str | Path,
        metadata_path: str | Path,
    ) -> tuple[Path, Path]:

        markdown_path = Path(markdown_path)
        metadata_path = Path(metadata_path)

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if not markdown_path.exists():
            raise FileNotFoundError(
                f"Markdown file does not exist: "
                f"{markdown_path}"
            )

        if not metadata_path.exists():
            raise FileNotFoundError(
                f"Metadata file does not exist: "
                f"{metadata_path}"
            )

        if not markdown_path.is_file():
            raise ValueError(
                f"Markdown path is not a file: "
                f"{markdown_path}"
            )

        if not metadata_path.is_file():
            raise ValueError(
                f"Metadata path is not a file: "
                f"{metadata_path}"
            )

        # ----------------------------------------------------
        # READ
        # ----------------------------------------------------

        markdown = markdown_path.read_text(
            encoding="utf-8"
        )

        metadata = json.loads(
            metadata_path.read_text(
                encoding="utf-8"
            )
        )

        # ----------------------------------------------------
        # CLEAN CONTENT
        # ----------------------------------------------------

        cleaned = self._clean_markdown(
            markdown
        )

        if not cleaned.strip():
            raise ValueError(
                f"Cleaning produced empty content: "
                f"{markdown_path}"
            )

        # ----------------------------------------------------
        # OUTPUT LOCATION
        # ----------------------------------------------------

        domain = metadata.get(
            "storage_domain"
        )

        category = metadata.get(
            "storage_category"
        )

        if not domain:
            domain = self._domain_from_metadata(
                metadata
            )

        if not category:
            category = "others"

        domain = self._clean_component(
            domain
        )

        category = self._clean_component(
            category
        )

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
        # OUTPUT FILES
        # ----------------------------------------------------

        output_markdown = (
            output_dir
            / markdown_path.name
        )

        output_metadata = (
            output_dir
            / metadata_path.name
        )

        # ----------------------------------------------------
        # WRITE MARKDOWN
        # ----------------------------------------------------

        output_markdown.write_text(
            cleaned,
            encoding="utf-8",
        )

        # ----------------------------------------------------
        # ENRICH METADATA
        # ----------------------------------------------------

        metadata = dict(metadata)

        metadata[
            "knowledge_cleaned"
        ] = True

        metadata[
            "cleaning_version"
        ] = "7.3"

        metadata[
            "cleaned_content_length"
        ] = len(cleaned)

        metadata[
            "original_content_length"
        ] = len(markdown)

        metadata[
            "cleaned_storage_path"
        ] = str(
            output_markdown
        )

        output_metadata.write_text(
            json.dumps(
                metadata,
                indent=4,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        return (
            output_markdown,
            output_metadata,
        )

    # --------------------------------------------------------
    # MARKDOWN CLEANING
    # --------------------------------------------------------

    def _clean_markdown(
        self,
        markdown: str,
    ) -> str:

        text = markdown

        # Normalize line endings.
        text = text.replace(
            "\r\n",
            "\n",
        )

        text = text.replace(
            "\r",
            "\n",
        )

        # Remove null characters.
        text = text.replace(
            "\x00",
            "",
        )

        # Remove obvious accessibility-tool boilerplate.
        text = re.sub(
            r"Ctrl\+F2.*",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"UX4G Accessibility Tool",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"Accessibility options Ctrl\+F2",
            "",
            text,
            flags=re.IGNORECASE,
        )

        # Remove repeated accessibility option labels.
        accessibility_patterns = [
            r"Open the accessibility option",
            r"Bigger Text",
            r"Smaller Text",
            r"Text Spacing",
            r"Line Height",
            r"Dyslexia Friendly",
            r"ADHD Mode",
            r"Saturation Low Saturation High Saturation",
            r"Desaturate",
            r"Light-Dark",
            r"Invert Colors",
            r"Highlight Links",
            r"Text To Speech",
            r"Cursor",
            r"Pause Animation",
            r"Hide Images",
            r"Reset All Settings",
        ]

        for pattern in accessibility_patterns:
            text = re.sub(
                pattern,
                "",
                text,
                flags=re.IGNORECASE,
            )

        # Remove empty image-only Markdown links.
        text = re.sub(
            r"!\[\s*\]\([^)]*\)",
            "",
            text,
        )

        # Normalize horizontal whitespace.
        text = re.sub(
            r"[ \t]+",
            " ",
            text,
        )

        # Remove whitespace around blank lines.
        lines = [
            line.strip()
            for line in text.split("\n")
        ]

        # Remove excessive blank lines.
        cleaned_lines = []

        blank_count = 0

        for line in lines:

            if not line:

                blank_count += 1

                if blank_count <= 2:
                    cleaned_lines.append("")

                continue

            blank_count = 0

            cleaned_lines.append(
                line
            )

        text = "\n".join(
            cleaned_lines
        )

        # Remove leading/trailing blank space.
        text = text.strip()

        return text

    # --------------------------------------------------------
    # DOMAIN FALLBACK
    # --------------------------------------------------------

    def _domain_from_metadata(
        self,
        metadata: dict,
    ) -> str:

        source_url = (
            metadata.get("url")
            or metadata.get("source_url")
            or ""
        )

        match = re.search(
            r"https?://([^/]+)",
            source_url,
        )

        if match:
            return match.group(1)

        return "unknown"

    # --------------------------------------------------------
    # SAFE COMPONENT
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
                cleaned.append("_")

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