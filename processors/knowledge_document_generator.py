from pathlib import Path
import json
import re


class KnowledgeDocumentGenerator:
    """
    Phase 8.1 — Knowledge Document Generator

    Converts validated retrieval JSON files into
    final RAG-ready Markdown documents.

    Responsibilities:
    - Read retrieval JSON.
    - Preserve validated knowledge.
    - Organize records by section.
    - Preserve document-level provenance.
    - Generate deterministic Markdown.
    - Do NOT clean knowledge.
    - Do NOT generate embeddings.
    - Do NOT connect to a vector database.
    """

    def __init__(
        self,
        output_path: str | Path = "storage/knowledge",
    ):
        self.output_path = Path(output_path)

    # ========================================================
    # PUBLIC API
    # ========================================================

    def process(
        self,
        retrieval_path: str | Path,
    ) -> Path:

        retrieval_path = Path(
            retrieval_path
        )

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if not retrieval_path.exists():
            raise FileNotFoundError(
                f"Retrieval file does not exist: "
                f"{retrieval_path}"
            )

        if not retrieval_path.is_file():
            raise ValueError(
                f"Retrieval path is not a file: "
                f"{retrieval_path}"
            )

        if retrieval_path.suffix.lower() != ".json":
            raise ValueError(
                f"Expected JSON retrieval file: "
                f"{retrieval_path}"
            )

        # ----------------------------------------------------
        # LOAD RETRIEVAL DATA
        # ----------------------------------------------------

        data = json.loads(
            retrieval_path.read_text(
                encoding="utf-8"
            )
        )

        document = data.get(
            "document",
            {}
        )

        records = data.get(
            "records",
            []
        )

        if not isinstance(
            document,
            dict,
        ):
            raise ValueError(
                "'document' must be an object"
            )

        if not isinstance(
            records,
            list,
        ):
            raise ValueError(
                "'records' must be a list"
            )

        if not records:
            raise ValueError(
                f"No retrieval records found: "
                f"{retrieval_path}"
            )

        # ----------------------------------------------------
        # OUTPUT DIRECTORY
        # ----------------------------------------------------

        domain = self._clean_component(
            document.get("domain")
        )

        category = self._clean_component(
            document.get(
                "category",
                "others",
            )
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
        # OUTPUT FILE
        # ----------------------------------------------------

        output_path = (
            output_dir
            / f"{retrieval_path.stem}.md"
        )

        # ----------------------------------------------------
        # BUILD MARKDOWN
        # ----------------------------------------------------

        lines = []

        self._add_document_header(
            lines,
            document,
        )

        self._add_records(
            lines,
            records,
        )

        content = (
            "\n".join(lines)
            .strip()
            + "\n"
        )

        # ----------------------------------------------------
        # WRITE
        # ----------------------------------------------------

        output_path.write_text(
            content,
            encoding="utf-8",
        )

        # ----------------------------------------------------
        # LOGGING
        # ----------------------------------------------------

        print(
            "Knowledge Document :",
            output_path,
        )

        print(
            "Records             :",
            len(records),
        )

        print(
            "Source URL          :",
            document.get("url"),
        )

        return output_path

    # ========================================================
    # DOCUMENT HEADER
    # ========================================================

    def _add_document_header(
        self,
        lines: list[str],
        document: dict,
    ) -> None:

        title = (
            document.get("title")
            or document.get("domain")
            or "Knowledge Document"
        )

        source_url = (
            document.get("url")
            or ""
        )

        domain = (
            document.get("domain")
            or ""
        )

        category = (
            document.get("category")
            or ""
        )

        document_type = (
            document.get("document_type")
            or ""
        )

        lines.append(
            f"# {self._clean_heading(title)}"
        )

        lines.append("")

        if source_url:
            lines.append(
                f"**Source:** {source_url}"
            )

        if domain:
            lines.append(
                f"**Domain:** {domain}"
            )

        if category:
            lines.append(
                f"**Category:** {category}"
            )

        if document_type:
            lines.append(
                f"**Document Type:** {document_type}"
            )

        lines.append("")

        lines.append("---")

        lines.append("")

    # ========================================================
    # RECORDS
    # ========================================================

    def _add_records(
        self,
        lines: list[str],
        records: list[dict],
    ) -> None:

        current_section = None

        for index, record in enumerate(
            records,
            start=1,
        ):

            if not isinstance(
                record,
                dict,
            ):
                continue

            text = record.get(
                "text",
                ""
            )

            metadata = record.get(
                "metadata",
                {}
            )

            if not isinstance(
                text,
                str,
            ):
                continue

            text = text.strip()

            if not text:
                continue

            if not isinstance(
                metadata,
                dict,
            ):
                metadata = {}

            # ------------------------------------------------
            # SECTION
            # ------------------------------------------------

            section = metadata.get(
                "section"
            )

            if isinstance(
                section,
                str,
            ):
                section = section.strip()
            else:
                section = None

            # ------------------------------------------------
            # SECTION HEADING
            # ------------------------------------------------

            if section:

                if section != current_section:

                    lines.append(
                        f"## {self._clean_heading(section)}"
                    )

                    lines.append("")

                    current_section = section

            # ------------------------------------------------
            # CONTENT
            # ------------------------------------------------

            lines.extend(
                self._format_text(
                    text
                )
            )

            lines.append("")

            # ------------------------------------------------
            # RECORD SEPARATOR
            # ------------------------------------------------

            if index < len(records):

                lines.append("---")

                lines.append("")

    # ========================================================
    # TEXT FORMATTING
    # ========================================================

    def _format_text(
        self,
        text: str,
    ) -> list[str]:

        text = text.strip()

        if not text:
            return []

        result = []

        for line in text.splitlines():

            line = line.strip()

            if not line:
                continue

            result.append(
                line
            )

        return result

    # ========================================================
    # HEADING CLEANING
    # ========================================================

    def _clean_heading(
        self,
        value: str,
    ) -> str:

        value = (
            value or ""
        ).strip()

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return value

    # ========================================================
    # PATH COMPONENT CLEANING
    # ========================================================

    def _clean_component(
        self,
        value: str | None,
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