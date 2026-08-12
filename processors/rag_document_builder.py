from pathlib import Path
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt


class RAGDocumentBuilder:
    """
    Phase 8.5

    Converts organized Markdown knowledge into
    clean, editable DOCX files for the RAG layer.

    Input:

        storage/organized_knowledge/<domain>/
            admissions/
            academics/
            hostel/
            ...

    Output:

        storage/rag_knowledge/<domain>/
            admissions.docx
            academics.docx
            hostel.docx
            ...

    Responsibilities:

    - Preserve organized knowledge.
    - Create one DOCX per category.
    - Preserve meaningful section headings.
    - Preserve meaningful content.
    - Preserve links as readable text.
    - Remove obvious residual extraction/UI noise.
    - Never rewrite factual content.
    - Never use an LLM.
    - Never modify canonical knowledge.
    - Never chunk.
    - Never embed.
    """

    def __init__(
        self,
        output_root: str | Path = "storage/rag_knowledge",
    ):
        self.output_root = Path(output_root)

    # ========================================================
    # PUBLIC API
    # ========================================================

    def build_domain(
        self,
        organized_root: str | Path,
    ) -> dict:
        """
        Build all RAG DOCX files for one domain.

        Only sections containing usable knowledge are converted.

        Returns summary information.
        """

        organized_root = Path(organized_root)

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if not organized_root.exists():
            raise FileNotFoundError(
                f"Organized knowledge directory "
                f"does not exist: {organized_root}"
            )

        if not organized_root.is_dir():
            raise ValueError(
                f"Organized knowledge path is not "
                f"a directory: {organized_root}"
            )

        domain = organized_root.name

        output_dir = (
            self.output_root
            / domain
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        category_files = {}

        total_sections = 0
        total_files = 0

        # ----------------------------------------------------
        # PROCESS EACH CATEGORY
        # ----------------------------------------------------

        category_dirs = sorted(
            path
            for path in organized_root.iterdir()
            if path.is_dir()
        )

        for category_dir in category_dirs:

            markdown_files = sorted(
                category_dir.glob("*.md")
            )

            if not markdown_files:
                continue

            category = category_dir.name

            sections = []

            for markdown_path in markdown_files:

                file_sections = (
                    self._read_markdown_file(
                        markdown_path
                    )
                )

                sections.extend(
                    file_sections
                )

            # ------------------------------------------------
            # NO USABLE KNOWLEDGE
            # ------------------------------------------------

            if not sections:
                self._remove_stale_output(
                    output_dir / f"{category}.docx"
                )
                continue

            output_path = (
                output_dir
                / f"{category}.docx"
            )

            self._write_docx(
                output_path=output_path,
                domain=domain,
                category=category,
                sections=sections,
            )

            category_files[category] = (
                output_path
            )

            total_sections += len(
                sections
            )

            total_files += 1

        # ----------------------------------------------------
        # RESULT
        # ----------------------------------------------------

        result = {
            "domain": domain,
            "organized_root": str(
                organized_root
            ),
            "output_root": str(
                output_dir
            ),
            "categories": len(
                category_files
            ),
            "files": total_files,
            "sections": total_sections,
            "category_files": category_files,
        }

        return result

    # ========================================================
    # READ MARKDOWN
    # ========================================================

    def _read_markdown_file(
        self,
        markdown_path: Path,
    ) -> list[dict]:
        """
        Read an organized Markdown file and extract
        meaningful H2 knowledge sections.

        Obvious residual website/extraction noise is
        rejected here before DOCX creation.
        """

        content = markdown_path.read_text(
            encoding="utf-8"
        )

        lines = content.splitlines()

        sections = []

        current_heading = None
        current_lines = []

        for line in lines:

            # ------------------------------------------------
            # H2 SECTION
            # ------------------------------------------------

            match = re.match(
                r"^##\s+(.+?)\s*$",
                line,
            )

            if match:

                # Finalize previous section.
                if current_heading is not None:

                    text = "\n".join(
                        current_lines
                    ).strip()

                    section = {
                        "heading": current_heading,
                        "text": text,
                        "source_file": markdown_path.name,
                    }

                    if (
                        text
                        and not self._looks_like_noise(
                            section
                        )
                    ):
                        sections.append(
                            section
                        )

                current_heading = (
                    match.group(1).strip()
                )

                current_lines = []

                continue

            # ------------------------------------------------
            # IGNORE H1
            # ------------------------------------------------

            if re.match(
                r"^#\s+",
                line,
            ):
                continue

            # ------------------------------------------------
            # IGNORE SEPARATOR
            # ------------------------------------------------

            if line.strip() == "---":
                continue

            # ------------------------------------------------
            # IGNORE CONTENT BEFORE FIRST H2
            # ------------------------------------------------

            if current_heading is None:
                continue

            # ------------------------------------------------
            # IGNORE FILE METADATA
            # ------------------------------------------------

            if re.match(
                r"^\*\*Domain:\*\*",
                line,
                flags=re.IGNORECASE,
            ):
                continue

            if re.match(
                r"^\*\*Category:\*\*",
                line,
                flags=re.IGNORECASE,
            ):
                continue

            if re.match(
                r"^\*\*Source Document:\*\*",
                line,
                flags=re.IGNORECASE,
            ):
                continue

            current_lines.append(line)

        # ----------------------------------------------------
        # FINAL SECTION
        # ----------------------------------------------------

        if current_heading is not None:

            text = "\n".join(
                current_lines
            ).strip()

            section = {
                "heading": current_heading,
                "text": text,
                "source_file": markdown_path.name,
            }

            if (
                text
                and not self._looks_like_noise(
                    section
                )
            ):
                sections.append(
                    section
                )

        return sections

    # ========================================================
    # NOISE DETECTION
    # ========================================================

    def _looks_like_noise(
        self,
        section: dict,
    ) -> bool:
        """
        Detect obvious residual website/UI/extraction noise.

        This is intentionally conservative.

        We reject:
        - navigation
        - accessibility controls
        - search UI
        - login/redirect artifacts
        - cookie/UI controls
        - image-only content
        - link-only navigation
        - extremely short meaningless sections

        We do NOT reject normal short factual content
        such as contact numbers, dates, names, etc.
        """

        heading = (
            section.get("heading", "")
            or ""
        ).strip()

        text = (
            section.get("text", "")
            or ""
        ).strip()

        if not heading or not text:
            return True

        normalized_heading = (
            self._normalize_text(
                heading
            )
        )

        normalized_text = (
            self._normalize_text(
                text
            )
        )

        # ----------------------------------------------------
        # OBVIOUS NOISE HEADINGS
        # ----------------------------------------------------

        noise_headings = {
            "menu",
            "navigation",
            "nav",
            "search",
            "search here",
            "search this site",
            "accessibility",
            "accessibility options",
            "skip to content",
            "skip to main content",
            "login",
            "sign in",
            "sign up",
            "register",
            "subscribe",
            "follow us",
            "social media",
            "share",
            "feedback",
            "feedback form",
            "cookie policy",
            "cookies",
            "privacy settings",
            "language",
            "select language",
            "translation",
            "rate this translation",
        }

        if normalized_heading in noise_headings:
            return True

        # ----------------------------------------------------
        # OBVIOUS EXTRACTION / REDIRECT ARTIFACTS
        # ----------------------------------------------------

        noise_patterns = (
            "redirecttologinpage",
            "accessibility options",
            "open the accessibility option",
            "rate this translation",
            "do you like to give feedback",
            "submit",
            "created by",
            "powered by",
            "important links",
            "all rights reserved",
            "javascript required",
            "enable javascript",
            "accept cookies",
            "manage cookies",
        )

        for pattern in noise_patterns:

            if pattern in normalized_text:
                return True

        # ----------------------------------------------------
        # HTML / SVG / DATA-URI NOISE
        # ----------------------------------------------------

        html_noise_patterns = (
            "<svg",
            "</svg>",
            "<path",
            "<script",
            "</script>",
            "data:image/",
            "clip-path",
            "viewbox=",
            "xmlns=",
        )

        lowered_text = text.lower()

        html_hits = sum(
            1
            for pattern in html_noise_patterns
            if pattern in lowered_text
        )

        if html_hits >= 2:
            return True

        # ----------------------------------------------------
        # REDIRECT ARTIFACT
        # ----------------------------------------------------

        if (
            "redirecttologinpage" in normalized_text
            or "147852369" in text
            and "963258741" in text
        ):
            return True

        # ----------------------------------------------------
        # REMOVE MARKDOWN IMAGE-ONLY SECTIONS
        # ----------------------------------------------------

        without_images = re.sub(
            r"!\[[^\]]*\]\([^)]+\)",
            "",
            text,
        ).strip()

        if not without_images:
            return True

        # ----------------------------------------------------
        # LINK / NAVIGATION DENSITY
        # ----------------------------------------------------

        links = re.findall(
            r"\[[^\]]*\]\([^)]+\)",
            text,
        )

        plain_text = re.sub(
            r"\[[^\]]*\]\([^)]+\)",
            "",
            text,
        )

        plain_text = re.sub(
            r"!\[[^\]]*\]\([^)]+\)",
            "",
            plain_text,
        )

        plain_text = re.sub(
            r"https?://\S+",
            "",
            plain_text,
        )

        plain_text = re.sub(
            r"\s+",
            " ",
            plain_text,
        ).strip()

        # If a section consists almost entirely of links,
        # it is probably navigation rather than knowledge.
        if links:
            link_chars = sum(
                len(link)
                for link in links
            )

            total_chars = max(
                len(text),
                1,
            )

            link_ratio = (
                link_chars / total_chars
            )

            if (
                link_ratio >= 0.70
                and len(plain_text) < 80
            ):
                return True

        # ----------------------------------------------------
        # UI-ONLY TEXT
        # ----------------------------------------------------

        ui_phrases = {
            "home",
            "back",
            "next",
            "previous",
            "close",
            "open",
            "menu",
            "more",
            "read more",
            "click here",
            "learn more",
            "submit",
            "cancel",
        }

        if (
            normalized_text in ui_phrases
            and len(normalized_text) < 30
        ):
            return True

        # ----------------------------------------------------
        # VERY SHORT NON-INFORMATIONAL CONTENT
        # ----------------------------------------------------

        alphanumeric = re.sub(
            r"[^a-zA-Z0-9]+",
            "",
            text,
        )

        if len(alphanumeric) < 8:
            return True

        return False

    # ========================================================
    # WRITE DOCX
    # ========================================================

    def _write_docx(
        self,
        output_path: Path,
        domain: str,
        category: str,
        sections: list[dict],
    ) -> None:

        document = Document()

        # ----------------------------------------------------
        # DEFAULT FONT
        # ----------------------------------------------------

        styles = document.styles

        normal_style = styles[
            "Normal"
        ]

        normal_style.font.name = (
            "Arial"
        )

        normal_style.font.size = Pt(
            11
        )

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        title = document.add_heading(
            self._display_category(
                category
            ),
            level=1,
        )

        title.alignment = (
            WD_ALIGN_PARAGRAPH.CENTER
        )

        # ----------------------------------------------------
        # DATASET METADATA
        # ----------------------------------------------------

        self._add_metadata(
            document,
            "Domain",
            domain,
        )

        self._add_metadata(
            document,
            "Category",
            category,
        )

        self._add_metadata(
            document,
            "Source",
            "Knowledge Ingestion Engine",
        )

        document.add_paragraph()

        # ----------------------------------------------------
        # SECTIONS
        # ----------------------------------------------------

        for section in sections:

            document.add_heading(
                section["heading"],
                level=2,
            )

            self._add_markdown_content(
                document,
                section["text"],
            )

            # ------------------------------------------------
            # SOURCE TRACEABILITY
            # ------------------------------------------------

            source_paragraph = (
                document.add_paragraph()
            )

            source_run = (
                source_paragraph.add_run(
                    f"Source: "
                    f"{section['source_file']}"
                )
            )

            source_run.italic = True
            source_run.font.size = Pt(
                9
            )

            document.add_paragraph()

        # ----------------------------------------------------
        # SAVE
        # ----------------------------------------------------

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        document.save(
            output_path
        )

    # ========================================================
    # MARKDOWN CONTENT
    # ========================================================

    def _add_markdown_content(
        self,
        document: Document,
        text: str,
    ) -> None:
        """
        Convert basic Markdown into readable DOCX content.

        The factual text itself is preserved.
        """

        lines = text.splitlines()

        paragraph_buffer = []

        def flush_paragraph():
            if not paragraph_buffer:
                return

            paragraph_text = (
                " ".join(
                    line.strip()
                    for line in paragraph_buffer
                ).strip()
            )

            if paragraph_text:
                self._add_inline_markdown(
                    document,
                    paragraph_text,
                )

            paragraph_buffer.clear()

        for line in lines:

            stripped = line.strip()

            # ------------------------------------------------
            # EMPTY LINE
            # ------------------------------------------------

            if not stripped:
                flush_paragraph()
                continue

            # ------------------------------------------------
            # SUBHEADING
            # ------------------------------------------------

            heading_match = re.match(
                r"^###\s+(.+)$",
                stripped,
            )

            if heading_match:

                flush_paragraph()

                document.add_heading(
                    heading_match.group(1).strip(),
                    level=3,
                )

                continue

            # ------------------------------------------------
            # BULLET LIST
            # ------------------------------------------------

            bullet_match = re.match(
                r"^[-*+]\s+(.+)$",
                stripped,
            )

            if bullet_match:

                flush_paragraph()

                paragraph = (
                    document.add_paragraph(
                        style="List Bullet"
                    )
                )

                self._add_inline_runs(
                    paragraph,
                    bullet_match.group(1),
                )

                continue

            # ------------------------------------------------
            # NUMBERED LIST
            # ------------------------------------------------

            number_match = re.match(
                r"^\d+\.\s+(.+)$",
                stripped,
            )

            if number_match:

                flush_paragraph()

                paragraph = (
                    document.add_paragraph(
                        style="List Number"
                    )
                )

                self._add_inline_runs(
                    paragraph,
                    number_match.group(1),
                )

                continue

            # ------------------------------------------------
            # TABLE
            # ------------------------------------------------

            if "|" in stripped:

                table_lines = [stripped]

                # Collect subsequent table rows.
                # We keep this simple and preserve the
                # Markdown table content as readable text
                # rather than risking data loss.
                flush_paragraph()

                self._add_table_row_as_paragraph(
                    document,
                    stripped,
                )

                continue

            # ------------------------------------------------
            # NORMAL TEXT
            # ------------------------------------------------

            paragraph_buffer.append(
                stripped
            )

        flush_paragraph()

    # ========================================================
    # INLINE MARKDOWN
    # ========================================================

    def _add_inline_markdown(
        self,
        document: Document,
        text: str,
    ) -> None:

        paragraph = (
            document.add_paragraph()
        )

        self._add_inline_runs(
            paragraph,
            text,
        )

    # ========================================================
    # INLINE RUNS
    # ========================================================

    def _add_inline_runs(
        self,
        paragraph,
        text: str,
    ) -> None:
        """
        Preserve readable Markdown links and basic emphasis.
        """

        # ----------------------------------------------------
        # TOKENIZE LINKS
        # ----------------------------------------------------

        pattern = re.compile(
            r"(\[[^\]]+\]\([^)]+\))"
        )

        parts = pattern.split(
            text
        )

        for part in parts:

            if not part:
                continue

            link_match = re.match(
                r"^\[([^\]]+)\]\(([^)]+)\)$",
                part,
            )

            if link_match:

                label = (
                    link_match.group(1)
                )

                url = (
                    link_match.group(2)
                )

                run = (
                    paragraph.add_run(
                        f"{label} ({url})"
                    )
                )

                run.underline = True

                continue

            # ------------------------------------------------
            # BASIC BOLD
            # ------------------------------------------------

            bold_parts = re.split(
                r"(\*\*[^*]+\*\*)",
                part,
            )

            for bold_part in bold_parts:

                if not bold_part:
                    continue

                if (
                    bold_part.startswith("**")
                    and bold_part.endswith("**")
                ):
                    run = (
                        paragraph.add_run(
                            bold_part[2:-2]
                        )
                    )

                    run.bold = True

                else:

                    # ------------------------------------------------
                    # BASIC ITALIC
                    # ------------------------------------------------

                    italic_parts = re.split(
                        r"(\*[^*]+\*)",
                        bold_part,
                    )

                    for italic_part in italic_parts:

                        if not italic_part:
                            continue

                        if (
                            italic_part.startswith("*")
                            and italic_part.endswith("*")
                            and not italic_part.startswith("**")
                        ):
                            run = (
                                paragraph.add_run(
                                    italic_part[1:-1]
                                )
                            )

                            run.italic = True

                        else:
                            paragraph.add_run(
                                italic_part
                            )

    # ========================================================
    # TABLE ROW
    # ========================================================

    def _add_table_row_as_paragraph(
        self,
        document: Document,
        line: str,
    ) -> None:
        """
        Preserve Markdown table rows as readable text.

        We intentionally do not reconstruct a DOCX table here
        because preserving the original extracted values is more
        important than changing their representation.
        """

        cleaned = line.strip()

        # Ignore Markdown separator rows.
        if re.match(
            r"^\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?$",
            cleaned,
        ):
            return

        cells = [
            cell.strip()
            for cell in cleaned.strip("|").split("|")
        ]

        cells = [
            cell
            for cell in cells
            if cell
        ]

        if not cells:
            return

        paragraph = (
            document.add_paragraph()
        )

        paragraph.add_run(
            " | ".join(cells)
        )

    # ========================================================
    # METADATA
    # ========================================================

    def _add_metadata(
        self,
        document: Document,
        key: str,
        value: str,
    ) -> None:

        paragraph = (
            document.add_paragraph()
        )

        key_run = (
            paragraph.add_run(
                f"{key}: "
            )
        )

        key_run.bold = True

        paragraph.add_run(
            str(value)
        )

    # ========================================================
    # STALE OUTPUT CLEANUP
    # ========================================================

    def _remove_stale_output(
        self,
        output_path: Path,
    ) -> None:
        """
        Remove an old DOCX when the current source category
        contains no usable knowledge.

        This prevents stale RAG files from surviving a rebuild.
        """

        if (
            output_path.exists()
            and output_path.is_file()
        ):
            output_path.unlink()

    # ========================================================
    # NORMALIZATION
    # ========================================================

    def _normalize_text(
        self,
        value: str,
    ) -> str:

        value = (
            value or ""
        ).strip().lower()

        # Remove Markdown links.
        value = re.sub(
            r"\[([^\]]+)\]\([^)]+\)",
            r"\1",
            value,
        )

        # Remove Markdown images.
        value = re.sub(
            r"!\[[^\]]*\]\([^)]+\)",
            "",
            value,
        )

        # Remove HTML tags.
        value = re.sub(
            r"<[^>]+>",
            " ",
            value,
        )

        # Normalize whitespace.
        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return value.strip()

    # ========================================================
    # DISPLAY CATEGORY
    # ========================================================

    def _display_category(
        self,
        category: str,
    ) -> str:

        return (
            category
            .replace(
                "_",
                " ",
            )
            .replace(
                "-",
                " ",
            )
            .title()
        )


if __name__ == "__main__":
    builder = RAGDocumentBuilder()

    result = builder.build_domain(
        "storage/organized_knowledge/iitj.ac.in"
    )

    print()
    print("=" * 100)
    print("PHASE 8.5 — RAG DOCUMENT BUILDER")
    print("=" * 100)

    print(
        "Domain    :",
        result["domain"],
    )

    print(
        "Output    :",
        result["output_root"],
    )

    print(
        "Categories:",
        result["categories"],
    )

    print(
        "DOCX files:",
        result["files"],
    )

    print(
        "Sections  :",
        result["sections"],
    )

    print()
    print("GENERATED FILES")

    if not result["category_files"]:
        print(
            "No DOCX files generated."
        )
    else:
        for category, path in sorted(
            result[
                "category_files"
            ].items()
        ):
            print(
                f"{category:25s}: {path}"
            )