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
    - Preserve section headings.
    - Preserve source information.
    - Preserve links as readable text.
    - Never rewrite factual content.
    - Never use an LLM.
    - Never modify canonical knowledge.
    """

    def __init__(
        self,
        output_root: str | Path = "storage/rag_knowledge",
    ):
        self.output_root = Path(
            output_root
        )

    # ========================================================
    # PUBLIC API
    # ========================================================

    def build_domain(
        self,
        organized_root: str | Path,
    ) -> dict:
        """
        Build all RAG DOCX files for one domain.

        Returns summary information.
        """

        organized_root = Path(
            organized_root
        )

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

        # ----------------------------------------------------
        # PROCESS EACH CATEGORY
        # ----------------------------------------------------

        category_dirs = sorted(
            path
            for path in organized_root.iterdir()
            if path.is_dir()
        )

        total_sections = 0
        total_files = 0

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

            if not sections:
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
        its H2 knowledge sections.
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

                if current_heading is not None:

                    text = "\n".join(
                        current_lines
                    ).strip()

                    if text:

                        sections.append(
                            {
                                "heading":
                                    current_heading,

                                "text":
                                    text,

                                "source_file":
                                    markdown_path.name,
                            }
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
            # IGNORE FILE METADATA
            # ------------------------------------------------

            if (
                current_heading is None
            ):
                continue

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

            current_lines.append(
                line
            )

        # ----------------------------------------------------
        # FINAL SECTION
        # ----------------------------------------------------

        if current_heading is not None:

            text = "\n".join(
                current_lines
            ).strip()

            if text:

                sections.append(
                    {
                        "heading":
                            current_heading,

                        "text":
                            text,

                        "source_file":
                            markdown_path.name,
                    }
                )

        return sections

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

        for index, section in enumerate(
            sections,
            start=1,
        ):

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
                    f"Source file: "
                    f"{section['source_file']}"
                )
            )

            source_run.italic = True

            source_run.font.size = Pt(
                9
            )

            # ------------------------------------------------
            # SECTION SEPARATOR
            # ------------------------------------------------

            if index < len(sections):

                document.add_paragraph(
                    "—" * 40
                )

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
    # MARKDOWN → DOCX CONTENT
    # ========================================================

    def _add_markdown_content(
        self,
        document: Document,
        text: str,
    ) -> None:

        lines = text.splitlines()

        paragraph_lines = []

        def flush_paragraph():

            if not paragraph_lines:
                return

            paragraph_text = " ".join(
                paragraph_lines
            ).strip()

            if paragraph_text:

                self._add_formatted_paragraph(
                    document,
                    paragraph_text,
                )

            paragraph_lines.clear()

        for line in lines:

            stripped = line.strip()

            # ------------------------------------------------
            # EMPTY LINE
            # ------------------------------------------------

            if not stripped:

                flush_paragraph()

                continue

            # ------------------------------------------------
            # BULLET
            # ------------------------------------------------

            if stripped.startswith(
                "- "
            ):

                flush_paragraph()

                bullet_text = (
                    stripped[2:].strip()
                )

                paragraph = (
                    document.add_paragraph(
                        style="List Bullet"
                    )
                )

                self._add_inline_formatting(
                    paragraph,
                    bullet_text,
                )

                continue

            # ------------------------------------------------
            # NUMBERED LIST
            # ------------------------------------------------

            numbered_match = re.match(
                r"^\d+\.\s+(.+)",
                stripped,
            )

            if numbered_match:

                flush_paragraph()

                numbered_text = (
                    numbered_match.group(1)
                )

                paragraph = (
                    document.add_paragraph(
                        style="List Number"
                    )
                )

                self._add_inline_formatting(
                    paragraph,
                    numbered_text,
                )

                continue

            # ------------------------------------------------
            # TABLE
            # ------------------------------------------------

            if stripped.startswith(
                "|"
            ) and stripped.endswith(
                "|"
            ):

                flush_paragraph()

                # Tables are handled conservatively
                # later. For now preserve the row as
                # readable text instead of losing data.

                table_row = (
                    stripped.strip("|")
                )

                table_row = (
                    table_row.replace(
                        "|",
                        "    ",
                    )
                )

                document.add_paragraph(
                    table_row
                )

                continue

            # ------------------------------------------------
            # NORMAL TEXT
            # ------------------------------------------------

            paragraph_lines.append(
                stripped
            )

        flush_paragraph()

    # ========================================================
    # FORMATTED PARAGRAPH
    # ========================================================

    def _add_formatted_paragraph(
        self,
        document: Document,
        text: str,
    ) -> None:

        paragraph = (
            document.add_paragraph()
        )

        self._add_inline_formatting(
            paragraph,
            text,
        )

    # ========================================================
    # INLINE MARKDOWN
    # ========================================================

    def _add_inline_formatting(
        self,
        paragraph,
        text: str,
    ) -> None:

        # ----------------------------------------------------
        # Protect markdown links first
        # ----------------------------------------------------

        pattern = re.compile(
            r"(\*\*.*?\*\*|\*.*?\*|\[[^\]]+\]\([^)]+\))"
        )

        position = 0

        for match in pattern.finditer(
            text
        ):

            # Normal text before match
            if match.start() > position:

                paragraph.add_run(
                    text[
                        position:
                        match.start()
                    ]
                )

            token = match.group(0)

            # ------------------------------------------------
            # BOLD
            # ------------------------------------------------

            if (
                token.startswith(
                    "**"
                )
                and token.endswith(
                    "**"
                )
            ):

                run = paragraph.add_run(
                    token[2:-2]
                )

                run.bold = True

            # ------------------------------------------------
            # ITALIC
            # ------------------------------------------------

            elif (
                token.startswith("*")
                and token.endswith("*")
            ):

                run = paragraph.add_run(
                    token[1:-1]
                )

                run.italic = True

            # ------------------------------------------------
            # MARKDOWN LINK
            # ------------------------------------------------

            elif token.startswith(
                "["
            ):

                link_match = re.match(
                    r"\[([^\]]+)\]\(([^)]+)\)",
                    token,
                )

                if link_match:

                    label = (
                        link_match.group(1)
                    )

                    url = (
                        link_match.group(2)
                    )

                    run = paragraph.add_run(
                        f"{label} ({url})"
                    )

            else:

                paragraph.add_run(
                    token
                )

            position = match.end()

        # ----------------------------------------------------
        # Remaining text
        # ----------------------------------------------------

        if position < len(text):

            paragraph.add_run(
                text[position:]
            )

    # ========================================================
    # METADATA
    # ========================================================

    def _add_metadata(
        self,
        document: Document,
        label: str,
        value: str,
    ) -> None:

        paragraph = (
            document.add_paragraph()
        )

        label_run = (
            paragraph.add_run(
                f"{label}: "
            )
        )

        label_run.bold = True

        paragraph.add_run(
            str(value)
        )

    # ========================================================
    # CATEGORY DISPLAY
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
            .title()
        )