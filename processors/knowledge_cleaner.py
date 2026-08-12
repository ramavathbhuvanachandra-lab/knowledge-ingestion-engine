from pathlib import Path
import json
import re
from urllib.parse import urlparse


class KnowledgeCleaner:
    """
    PHASE 7.3 — KNOWLEDGE CLEANING

    Purpose:
        Convert crawler-produced Markdown into clean,
        human-verifiable, RAG-ready knowledge Markdown.

    Design principles:
        - Remove obvious website/UI noise.
        - Preserve page-specific knowledge.
        - Preserve headings.
        - Preserve paragraphs.
        - Preserve lists.
        - Preserve tables.
        - Preserve meaningful links.
        - Never aggressively delete unknown content.
        - Never chunk.
        - Never embed.
        - Never modify crawler output.

    Input:
        storage/output/<domain>/<category>/<file>.md
        storage/output/<domain>/<category>/<file>.json

    Output:
        storage/knowledge/<domain>/<category>/<file>.md
        storage/knowledge/<domain>/<category>/<file>.json
    """

    # --------------------------------------------------------
    # CONSTRUCTOR
    # --------------------------------------------------------

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
                f"Markdown file does not exist: {markdown_path}"
            )

        if not metadata_path.exists():
            raise FileNotFoundError(
                f"Metadata file does not exist: {metadata_path}"
            )

        if not markdown_path.is_file():
            raise ValueError(
                f"Markdown path is not a file: {markdown_path}"
            )

        if not metadata_path.is_file():
            raise ValueError(
                f"Metadata path is not a file: {metadata_path}"
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
        # CLEAN
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

        metadata["knowledge_cleaned"] = True
        metadata["cleaning_version"] = "7.3"
        metadata["cleaned_content_length"] = len(cleaned)
        metadata["original_content_length"] = len(markdown)
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
        #
        # These are safe because they do not contain knowledge.
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
            r"^Menu$",
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
        #
        # Important:
        # We only remove clearly identifiable global
        # navigation/footer blocks.
        #
        # Unknown content is preserved.
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
        # 8. REMOVE EMPTY LINK DUPLICATION
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
        Remove the obvious global website header.

        We stop removal once actual page content starts.

        This is intentionally conservative.
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
            #
            # We do NOT aggressively delete it.
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

        # Language selector
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

        # Common global navigation
        navigation_words = [
            "[ home ]",
            "[ sitemap ]",
            "sitemap",
        ]

        if lower in navigation_words:
            return True

        # Accessibility remnants
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
        #
        # Avoid using this too aggressively.
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
            # certainly the global language selector.
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
        Remove the common global footer once a strong footer
        marker is encountered.

        This intentionally removes everything AFTER the
        global footer marker because that region is normally
        site-wide navigation, social links, copyright and
        government/portal logos.

        Page-specific content occurring before this marker
        remains untouched.
        """

        footer_markers = [
            "important links",
            "copyright ©",
            "copyright",
            "for any comments/enquiries/feedback",
            "web information manager",
        ]

        cutoff = None

        for index, line in enumerate(lines):

            lower = line.strip().lower()

            if not lower:
                continue

            for marker in footer_markers:

                if marker in lower:
                    cutoff = index
                    break

            if cutoff is not None:
                break

        if cutoff is None:
            return lines

        # Keep content before footer.
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

        match = re.search(
            r"https?://([^/]+)",
            source_url,
        )

        if match:
            return match.group(1)

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