"""
Command 2 — Knowledge Cleaning Engine.

Purpose:
    Convert one Markdown + metadata pair into clean, human-readable
    knowledge while preserving substantive content and provenance.

Important invariants:
    - Never modify the original input files.
    - Remove obvious website/UI/extraction noise only.
    - Preserve headings, paragraphs, lists, tables, and meaningful links.
    - Preserve unknown substantive content.
    - Preserve source URL/source provenance.
    - Never classify final semantic organization here.
    - Never chunk or embed content.

Output:
    The caller controls the output domain/category so this cleaner can
    be reused by the new Command 2 orchestration layer.
"""

from pathlib import Path
import json
import re
from urllib.parse import urlparse


class KnowledgeCleaner:
    """
    Clean one Markdown knowledge document.

    The cleaner owns content cleaning.

    The caller owns:
        - input discovery
        - source-type selection
        - batch orchestration
        - failure aggregation
        - final command manifests
    """

    CLEANING_VERSION = "8.0"

    def __init__(
        self,
        output_path: str | Path = "storage/02_cleaned",
    ):
        self.output_path = Path(
            output_path
        )

    # ========================================================
    # PUBLIC API
    # ========================================================

    def clean(
        self,
        markdown_path: str | Path,
        metadata_path: str | Path,
        output_domain: str | None = None,
        output_category: str | None = None,
    ) -> tuple[Path, Path]:
        """
        Clean one Markdown + metadata pair.

        Optional output_domain/output_category allow Command 2 to
        explicitly control the new storage structure.

        If they are not provided, the legacy metadata-based fallback
        remains available for backward compatibility.
        """

        markdown_path = Path(
            markdown_path
        )

        metadata_path = Path(
            metadata_path
        )

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
        # READ INPUT
        # ----------------------------------------------------

        markdown = markdown_path.read_text(
            encoding="utf-8"
        )

        metadata = json.loads(
            metadata_path.read_text(
                encoding="utf-8"
            )
        )

        if not isinstance(
            metadata,
            dict,
        ):
            raise ValueError(
                f"Metadata must be a JSON object: "
                f"{metadata_path}"
            )

        # ----------------------------------------------------
        # CLEAN MARKDOWN
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

        domain = (
            output_domain
            or metadata.get("storage_domain")
            or self._domain_from_metadata(
                metadata
            )
        )

        category = (
            output_category
            or metadata.get("storage_category")
            or "others"
        )

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
        # WRITE CLEANED MARKDOWN
        # ----------------------------------------------------

        output_markdown.write_text(
            cleaned,
            encoding="utf-8",
        )

        # ----------------------------------------------------
        # ENRICH METADATA
        # ----------------------------------------------------

        metadata = dict(
            metadata
        )

        source_url = (
            metadata.get("url")
            or metadata.get("source_url")
        )

        if source_url:
            metadata["source_url"] = source_url

        metadata["knowledge_cleaned"] = True
        metadata["cleaning_version"] = (
            self.CLEANING_VERSION
        )
        metadata["cleaned_content_length"] = (
            len(cleaned)
        )
        metadata["original_content_length"] = (
            len(markdown)
        )
        metadata["cleaned_storage_path"] = str(
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

    # ========================================================
    # MARKDOWN CLEANING
    # ========================================================

    def _clean_markdown(
        self,
        markdown: str,
    ) -> str:
        """
        Perform conservative Markdown cleaning.

        This method removes obvious web machinery while preserving
        substantive page-specific knowledge.
        """

        text = markdown

        # ----------------------------------------------------
        # 1. NORMALIZE BASIC TEXT
        # ----------------------------------------------------

        text = text.replace(
            "\r\n",
            "\n",
        )

        text = text.replace(
            "\r",
            "\n",
        )

        text = text.replace(
            "\x00",
            "",
        )

        # ----------------------------------------------------
        # 2. REMOVE TECHNICAL / ACCESSIBILITY GARBAGE
        # ----------------------------------------------------

        text = re.sub(
            r"Ctrl\+F2.*",
            "",
            text,
            flags=re.IGNORECASE,
        )

        technical_patterns = [
            r"UX4G Accessibility Tool",
            r"Accessibility options Ctrl\+F2",
            r"Open the accessibility option",
            r"Reset All Settings",
            r"Text To Speech",
            r"Pause Animation",
            r"Hide Images",
            r"Cursor",
            r"Dyslexia Friendly",
            r"ADHD Mode",
            r"Highlight Links",
            r"Desaturate",
            r"Invert Colors",
            r"Light-Dark",
            r"Line Height",
            r"Text Spacing",
            r"Bigger Text",
            r"Smaller Text",
            r"Saturation Low Saturation High Saturation",
        ]

        for pattern in technical_patterns:
            text = re.sub(
                pattern,
                "",
                text,
                flags=re.IGNORECASE,
            )

        # ----------------------------------------------------
        # 3. REMOVE JAVASCRIPT / UI ARTIFACTS
        # ----------------------------------------------------

        text = re.sub(
            r"\[[^\]]*\]\(\s*javascript:[^)]+\)",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"javascript:[^\s)]+",
            "",
            text,
            flags=re.IGNORECASE,
        )

        # ----------------------------------------------------
        # 4. REMOVE EMPTY IMAGE/LINK ELEMENTS
        # ----------------------------------------------------

        text = re.sub(
            r"!\[\s*\]\([^)]*\)",
            "",
            text,
        )

        text = re.sub(
            r"\[\s*\]\([^)]*\)",
            "",
            text,
        )

        # ----------------------------------------------------
        # 5. REMOVE COMMON UI-ONLY LINES
        # ----------------------------------------------------

        ui_only_patterns = [
            r"^Previous Next pause$",
            r"^Previous Next$",
            r"^Next Previous$",
            r"^pause$",
            r"^Play$",
            r"^Submit$",
            r"^Rate this translation$",
            r"^Do you like to give feedback$",
            r"^Search$",
            r"^(Main )?Menu$",
            r"^Close$",
        ]

        lines = text.split("\n")

        filtered_lines = []

        for line in lines:

            stripped = line.strip()

            if not stripped:
                filtered_lines.append("")
                continue

            remove = False

            for pattern in ui_only_patterns:
                if re.match(
                    pattern,
                    stripped,
                    flags=re.IGNORECASE,
                ):
                    remove = True
                    break

            if remove:
                continue

            filtered_lines.append(
                line
            )

        text = "\n".join(
            filtered_lines
        )

        # ----------------------------------------------------
        # 6. REMOVE GLOBAL WEBSITE CHROME
        # ----------------------------------------------------

        lines = text.split("\n")

        lines = self._remove_global_header(
            lines
        )

        lines = self._remove_global_footer(
            lines
        )

        text = "\n".join(lines)

        # ----------------------------------------------------
        # 7. REMOVE REPEATED LANGUAGE SELECTOR BLOCKS
        # ----------------------------------------------------

        text = self._remove_language_block(
            text
        )

        # ----------------------------------------------------
        # 8. REMOVE EXACT DUPLICATED URL TOKENS
        # ----------------------------------------------------

        text = re.sub(
            r"(https?://[^\s]+)\s+\1",
            r"\1",
            text,
        )

        # ----------------------------------------------------
        # 9. NORMALIZE HORIZONTAL WHITESPACE
        # ----------------------------------------------------

        text = re.sub(
            r"[ \t]+",
            " ",
            text,
        )

        # ----------------------------------------------------
        # 10. NORMALIZE BLANK LINES
        # ----------------------------------------------------

        normalized_lines = []

        blank_count = 0

        for line in text.split("\n"):

            line = line.strip()

            if not line:
                blank_count += 1

                if blank_count <= 2:
                    normalized_lines.append("")

                continue

            blank_count = 0

            normalized_lines.append(
                line
            )

        text = "\n".join(
            normalized_lines
        )

        # ----------------------------------------------------
        # 11. REMOVE EMPTY MARKDOWN ARTIFACTS
        # ----------------------------------------------------

        text = re.sub(
            r"^#+\s*$",
            "",
            text,
            flags=re.MULTILINE,
        )

        text = re.sub(
            r"^\[\s*\]\([^)]*\)\s*$",
            "",
            text,
            flags=re.MULTILINE,
        )

        # ----------------------------------------------------
        # 12. FINAL WHITESPACE CLEANUP
        # ----------------------------------------------------

        text = text.strip()

        return text

    # ========================================================
    # GLOBAL HEADER
    # ========================================================

    def _remove_global_header(
        self,
        lines: list[str],
    ) -> list[str]:
        """
        Remove obvious global website header content.

        We stop when actual page content starts.

        Uncertain content is preserved.
        """

        if not lines:
            return lines

        result = []

        started = False

        for line in lines:

            stripped = line.strip()

            if started:
                result.append(line)
                continue

            # ------------------------------------------------
            # Strong page-content signals
            # ------------------------------------------------

            if self._looks_like_content_start(
                stripped
            ):
                started = True
                result.append(line)
                continue

            # ------------------------------------------------
            # Obvious global header
            # ------------------------------------------------

            if self._looks_like_global_header(
                stripped
            ):
                continue

            # Preserve uncertain content.
            result.append(line)

        return result

    # ========================================================
    # GLOBAL HEADER DETECTION
    # ========================================================

    def _looks_like_global_header(
        self,
        line: str,
    ) -> bool:

        if not line:
            return False

        lower = line.lower()

        # ----------------------------------------------------
        # Generic language-selector signal
        # ----------------------------------------------------

        languages = [
            "english",
            "assamese",
            "bengali",
            "bodo",
            "dogri",
            "gujarati",
            "hindi",
            "kannada",
            "kashmiri",
            "maithili",
            "malayalam",
            "manipuri",
            "marathi",
            "nepali",
            "odia",
            "punjabi",
            "sanskrit",
            "santali",
            "sindhi",
            "tamil",
            "telugu",
            "urdu",
        ]

        language_hits = sum(
            1
            for language in languages
            if language in lower
        )

        if language_hits >= 3:
            return True

        # ----------------------------------------------------
        # Common global navigation
        # ----------------------------------------------------

        navigation_words = [
            "[ home ]",
            "[ sitemap ]",
            "sitemap",
        ]

        if lower in navigation_words:
            return True

        # ----------------------------------------------------
        # Accessibility remnants
        # ----------------------------------------------------

        if "accessibility" in lower:
            return True

        if "ctrl+f2" in lower:
            return True

        return False

    # ========================================================
    # CONTENT START DETECTION
    # ========================================================

    def _looks_like_content_start(
        self,
        line: str,
    ) -> bool:

        if not line:
            return False

        # Markdown heading
        if re.match(
            r"^#{1,6}\s+\S+",
            line,
        ):
            return True

        # Strong page-specific sentence.
        if len(line) > 150:
            return True

        return False

    # ========================================================
    # LANGUAGE BLOCK
    # ========================================================

    def _remove_language_block(
        self,
        text: str,
    ) -> str:

        languages = [
            "English",
            "Assamese",
            "Bengali",
            "Bodo",
            "Dogri",
            "Gujarati",
            "Hindi",
            "Kannada",
            "Kashmiri",
            "Maithili",
            "Malayalam",
            "Manipuri",
            "Marathi",
            "Nepali",
            "Odia",
            "Punjabi",
            "Sanskrit",
            "Santali",
            "Sindhi",
            "Tamil",
            "Telugu",
            "Urdu",
        ]

        lines = text.split("\n")

        result = []

        for line in lines:

            stripped = line.strip()

            lower = stripped.lower()

            hits = sum(
                1
                for language in languages
                if language.lower() in lower
            )

            # A line containing many languages is almost
            # certainly a global language selector.
            if hits >= 4:
                continue

            result.append(line)

        return "\n".join(result)

    # ========================================================
    # GLOBAL FOOTER
    # ========================================================

    def _remove_global_footer(
        self,
        lines: list[str],
    ) -> list[str]:
        """
        Remove the common global footer.

        This remains conservative: only a footer marker that is
        very clearly acting as a global footer should terminate
        the page content.
        """

        footer_markers = [
            "copyright ©",
            "for any comments/enquiries/feedback",
            "web information manager",
        ]

        cutoff = None

        for index, line in enumerate(lines):

            lower = line.strip().lower()

            if not lower:
                continue

            for marker in footer_markers:

                if lower == marker or lower.startswith(
                    marker
                ):
                    cutoff = index
                    break

            if cutoff is not None:
                break

        if cutoff is None:
            return lines

        return lines[:cutoff]

    # ========================================================
    # DOMAIN FALLBACK
    # ========================================================

    def _domain_from_metadata(
        self,
        metadata: dict,
    ) -> str:

        source_url = (
            metadata.get("url")
            or metadata.get("source_url")
            or ""
        )

        parsed = urlparse(
            source_url
        )

        if parsed.netloc:
            return parsed.netloc

        return "unknown"

    # ========================================================
    # SAFE COMPONENT
    # ========================================================

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