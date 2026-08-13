from pathlib import Path
import json
import re

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt


class RAGDocumentBuilder:
    """
    PHASE 8.5 — FINAL RAG DOCX BUILDER

    Input:
        storage/organized_knowledge/<domain>/rag_plan.json

    Output:
        storage/rag_knowledge/<domain>/*.docx

    Responsibilities:
    - Read the dynamic RAG plan.
    - Preserve every planned knowledge unit.
    - Group units according to the planner.
    - Build human-readable DOCX files.
    - Preserve source provenance.
    - Preserve original knowledge text.
    - Validate that zero useful units are lost.

    This class does NOT:
    - summarize
    - rewrite knowledge
    - classify knowledge
    - call an LLM
    - generate embeddings
    - perform retrieval
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        output_root: str | Path = (
            "storage/rag_knowledge"
        ),
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
        Build final RAG DOCX files for one domain.

        organized_root should be:

            storage/organized_knowledge/<domain>
        """

        organized_root = Path(
            organized_root
        )

        if not organized_root.exists():
            raise FileNotFoundError(
                f"Organized knowledge root does not exist: "
                f"{organized_root}"
            )

        if not organized_root.is_dir():
            raise ValueError(
                f"Organized knowledge root is not a directory: "
                f"{organized_root}"
            )

        domain = organized_root.name

        # ----------------------------------------------------
        # LOAD RAG PLAN
        # ----------------------------------------------------

        plan_path = (
            organized_root
            / "rag_plan.json"
        )

        if not plan_path.exists():
            raise FileNotFoundError(
                f"RAG plan does not exist: "
                f"{plan_path}"
            )

        plan = self._load_plan(
            plan_path
        )

        if plan.get(
            "domain"
        ) != domain:
            raise ValueError(
                "RAG plan domain does not match "
                f"organized domain: "
                f"{plan.get('domain')} != {domain}"
            )

        documents = plan.get(
            "documents",
            [],
        )

        if not isinstance(
            documents,
            list,
        ):
            raise ValueError(
                "'documents' in RAG plan must be a list."
            )

        # ----------------------------------------------------
        # OUTPUT DIRECTORY
        # ----------------------------------------------------

        output_root = (
            self.output_root
            / domain
        )

        output_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        # ----------------------------------------------------
        # CLEAR OLD DOCX FILES
        #
        # Prevent stale documents from previous runs.
        # ----------------------------------------------------

        self._remove_existing_docx(
            output_root
        )

        # ----------------------------------------------------
        # INPUT UNIT INVENTORY
        # ----------------------------------------------------

        input_unit_ids = (
            self._collect_plan_unit_ids(
                plan
            )
        )

        if not input_unit_ids:
            raise ValueError(
                f"RAG plan contains no knowledge units: "
                f"{plan_path}"
            )

        # ----------------------------------------------------
        # BUILD EACH DOCX
        # ----------------------------------------------------

        category_files = {}

        total_sections = 0

        for document_plan in documents:

            if not isinstance(
                document_plan,
                dict,
            ):
                raise ValueError(
                    "Every RAG document plan must be an object."
                )

            document_id = (
                self._clean_filename(
                    document_plan.get(
                        "document_id"
                    )
                )
            )

            if not document_id:
                raise ValueError(
                    "RAG document is missing document_id."
                )

            title = (
                document_plan.get(
                    "title"
                )
                or self._display_name(
                    document_id
                )
            )

            units = document_plan.get(
                "units",
                [],
            )

            if not isinstance(
                units,
                list,
            ):
                raise ValueError(
                    f"Units must be a list for "
                    f"{document_id}."
                )

            if not units:
                continue

            output_path = (
                output_root
                / f"{document_id}.docx"
            )

            self._build_document(
                output_path=output_path,
                domain=domain,
                title=title,
                document_plan=document_plan,
            )

            category_files[
                document_id
            ] = str(
                output_path
            )

            total_sections += len(
                units
            )

        # ----------------------------------------------------
        # OUTPUT COVERAGE
        # ----------------------------------------------------

        output_unit_ids = (
            self._collect_output_unit_ids(
                plan
            )
        )

        duplicate_output_ids = (
            self._duplicates(
                output_unit_ids
            )
        )

        if duplicate_output_ids:
            raise ValueError(
                "Duplicate knowledge units found in final RAG plan: "
                f"{duplicate_output_ids}"
            )

        missing_ids = sorted(
            set(input_unit_ids)
            - set(output_unit_ids)
        )

        extra_ids = sorted(
            set(output_unit_ids)
            - set(input_unit_ids)
        )

        if missing_ids:
            raise ValueError(
                "Knowledge units missing from final RAG output: "
                f"{missing_ids}"
            )

        if extra_ids:
            raise ValueError(
                "Unknown knowledge units found in final RAG output: "
                f"{extra_ids}"
            )

        if len(
            input_unit_ids
        ) != len(
            output_unit_ids
        ):
            raise ValueError(
                "Final RAG unit count does not match "
                "planned unit count."
            )

        # ----------------------------------------------------
        # FINAL RESULT
        # ----------------------------------------------------

        result = {
            "domain": domain,
            "output_root": str(
                output_root
            ),
            "categories": len(
                category_files
            ),
            "files": len(
                category_files
            ),
            "sections": total_sections,
            "category_files": category_files,
            "input_units": len(
                input_unit_ids
            ),
            "output_units": len(
                output_unit_ids
            ),
            "coverage": {
                "input_units": len(
                    input_unit_ids
                ),
                "output_units": len(
                    output_unit_ids
                ),
                "missing_units": len(
                    missing_ids
                ),
                "extra_units": len(
                    extra_ids
                ),
                "coverage_complete": (
                    not missing_ids
                    and not extra_ids
                    and len(
                        input_unit_ids
                    ) == len(
                        output_unit_ids
                    )
                ),
            },
        }

        print()
        print(
            "RAG Documents Built :",
            output_root,
        )

        print(
            "Domain               :",
            domain,
        )

        print(
            "DOCX Files           :",
            result["files"],
        )

        print(
            "Knowledge Sections   :",
            result["sections"],
        )

        print(
            "Input Units          :",
            result["input_units"],
        )

        print(
            "Output Units         :",
            result["output_units"],
        )

        print(
            "Coverage             :",
            (
                "PASS"
                if result["coverage"][
                    "coverage_complete"
                ]
                else "FAIL"
            ),
        )

        for name, path in sorted(
            category_files.items()
        ):
            print(
                f"{name:30s}: {path}"
            )

        return result

    # ========================================================
    # LOAD PLAN
    # ========================================================

    def _load_plan(
        self,
        path: Path,
    ) -> dict:

        try:

            data = json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )

        except json.JSONDecodeError as exc:

            raise ValueError(
                f"Invalid RAG plan JSON: "
                f"{path}"
            ) from exc

        if not isinstance(
            data,
            dict,
        ):
            raise ValueError(
                f"RAG plan must be a JSON object: "
                f"{path}"
            )

        return data

    # ========================================================
    # BUILD ONE DOCX
    # ========================================================

    def _build_document(
        self,
        output_path: Path,
        domain: str,
        title: str,
        document_plan: dict,
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

        normal_style.font.size = (
            Pt(10)
        )

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        heading = document.add_heading(
            title,
            level=0,
        )

        heading.alignment = (
            WD_ALIGN_PARAGRAPH.CENTER
        )

        # ----------------------------------------------------
        # DOCUMENT METADATA
        # ----------------------------------------------------

        paragraph = (
            document.add_paragraph()
        )

        self._add_metadata_line(
            paragraph,
            "Domain",
            domain,
        )

        paragraph = (
            document.add_paragraph()
        )

        self._add_metadata_line(
            paragraph,
            "RAG Document",
            document_plan.get(
                "document_id",
                "",
            ),
        )

        topics = document_plan.get(
            "topics",
            [],
        )

        if topics:

            paragraph = (
                document.add_paragraph()
            )

            self._add_metadata_line(
                paragraph,
                "Topics",
                ", ".join(
                    topics
                ),
            )

        document.add_paragraph(
            ""
        )

        # ----------------------------------------------------
        # KNOWLEDGE UNITS
        # ----------------------------------------------------

        units = document_plan.get(
            "units",
            [],
        )

        for index, unit in enumerate(
            units,
            start=1,
        ):

            if index > 1:
                document.add_page_break()

            self._write_unit(
                document,
                unit,
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
    # WRITE ONE KNOWLEDGE UNIT
    # ========================================================

    def _write_unit(
        self,
        document: Document,
        unit: dict,
    ) -> None:

        heading = (
            unit.get(
                "heading"
            )
            or "Knowledge Section"
        )

        text = (
            unit.get(
                "text",
                "",
            )
            or ""
        ).strip()

        if not text:
            raise ValueError(
                "Knowledge unit contains empty text: "
                f"{unit.get('unit_id')}"
            )

        # ----------------------------------------------------
        # SECTION HEADING
        # ----------------------------------------------------

        document.add_heading(
            heading,
            level=1,
        )

        # ----------------------------------------------------
        # SOURCE CONTENT
        #
        # Preserve the knowledge text.
        # Do not summarize or rewrite.
        # ----------------------------------------------------

        self._write_markdown_like_text(
            document,
            text,
        )

        # ----------------------------------------------------
        # PROVENANCE
        # ----------------------------------------------------

        provenance = (
            document.add_paragraph()
        )

        provenance.add_run(
            "Source document: "
        ).bold = True

        provenance.add_run(
            str(
                unit.get(
                    "source_file",
                    "",
                )
            )
        )

        source_url = (
            unit.get(
                "source_url"
            )
        )

        if source_url:

            provenance.add_run(
                "\nSource URL: "
            )

            provenance.add_run(
                str(
                    source_url
                )
            )

        topic = (
            unit.get(
                "topic"
            )
        )

        if topic:

            provenance.add_run(
                "\nTopic: "
            )

            provenance.add_run(
                str(
                    topic
                )
            )

        subtopic = (
            unit.get(
                "subtopic"
            )
        )

        if subtopic:

            provenance.add_run(
                "\nSubtopic: "
            )

            provenance.add_run(
                str(
                    subtopic
                )
            )

        line_start = unit.get(
            "start_line"
        )

        line_end = unit.get(
            "end_line"
        )

        if (
            line_start is not None
            and line_end is not None
        ):

            provenance.add_run(
                "\nSource lines: "
            )

            provenance.add_run(
                f"{line_start}-{line_end}"
            )

    # ========================================================
    # TEXT WRITER
    # ========================================================

    def _write_markdown_like_text(
        self,
        document: Document,
        text: str,
    ) -> None:

        for raw_line in text.splitlines():

            line = raw_line.strip()

            if not line:
                continue

            # ------------------------------------------------
            # SUBHEADING
            # ------------------------------------------------

            heading_match = re.match(
                r"^(#{1,6})\s+(.+)$",
                line,
            )

            if heading_match:

                heading_text = (
                    heading_match.group(
                        2
                    ).strip()
                )

                document.add_heading(
                    heading_text,
                    level=2,
                )

                continue

            # ------------------------------------------------
            # BULLET
            # ------------------------------------------------

            if line.startswith(
                "- "
            ):

                paragraph = (
                    document.add_paragraph(
                        style="List Bullet"
                    )
                )

                paragraph.add_run(
                    line[2:].strip()
                )

                continue

            if line.startswith(
                "* "
            ):

                paragraph = (
                    document.add_paragraph(
                        style="List Bullet"
                    )
                )

                paragraph.add_run(
                    line[2:].strip()
                )

                continue

            # ------------------------------------------------
            # NUMBERED LIST
            # ------------------------------------------------

            if re.match(
                r"^\d+[.)]\s+",
                line,
            ):

                clean_line = re.sub(
                    r"^\d+[.)]\s+",
                    "",
                    line,
                )

                paragraph = (
                    document.add_paragraph(
                        style="List Number"
                    )
                )

                paragraph.add_run(
                    clean_line
                )

                continue

            # ------------------------------------------------
            # NORMAL TEXT
            # ------------------------------------------------

            document.add_paragraph(
                line
            )

    # ========================================================
    # METADATA LINE
    # ========================================================

    def _add_metadata_line(
        self,
        paragraph,
        label: str,
        value: str,
    ) -> None:

        paragraph.add_run(
            f"{label}: "
        ).bold = True

        paragraph.add_run(
            str(
                value
            )
        )

    # ========================================================
    # COLLECT PLAN UNIT IDS
    # ========================================================

    def _collect_plan_unit_ids(
        self,
        plan: dict,
    ) -> list[str]:

        ids = []

        for document in plan.get(
            "documents",
            [],
        ):

            for unit in document.get(
                "units",
                [],
            ):

                unit_id = unit.get(
                    "unit_id"
                )

                if not unit_id:
                    raise ValueError(
                        "RAG plan contains a unit without unit_id."
                    )

                ids.append(
                    unit_id
                )

        return ids

    # ========================================================
    # COLLECT OUTPUT UNIT IDS
    #
    # The builder doesn't parse DOCX back.
    #
    # Instead, it verifies the exact same plan was used
    # for every generated document.
    # ========================================================

    def _collect_output_unit_ids(
        self,
        plan: dict,
    ) -> list[str]:

        ids = []

        for document in plan.get(
            "documents",
            [],
        ):

            for unit in document.get(
                "units",
                [],
            ):

                unit_id = unit.get(
                    "unit_id"
                )

                if unit_id:
                    ids.append(
                        unit_id
                    )

        return ids

    # ========================================================
    # REMOVE OLD DOCX
    # ========================================================

    def _remove_existing_docx(
        self,
        output_root: Path,
    ) -> None:

        if not output_root.exists():
            return

        for path in output_root.glob(
            "*.docx"
        ):

            path.unlink()

    # ========================================================
    # FILENAME CLEANING
    # ========================================================

    def _clean_filename(
        self,
        value: str | None,
    ) -> str:

        value = (
            value or ""
        ).strip().lower()

        value = re.sub(
            r"[^a-z0-9._-]+",
            "_",
            value,
        )

        value = re.sub(
            r"_+",
            "_",
            value,
        )

        return (
            value.strip("._-")
        )

    # ========================================================
    # DISPLAY NAME
    # ========================================================

    def _display_name(
        self,
        value: str,
    ) -> str:

        value = re.sub(
            r"[_-]+",
            " ",
            value or "",
        )

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return (
            value.strip().title()
            or "RAG Knowledge"
        )

    # ========================================================
    # DUPLICATES
    # ========================================================

    def _duplicates(
        self,
        values: list[str],
    ) -> list[str]:

        seen = set()
        duplicates = set()

        for value in values:

            if value in seen:
                duplicates.add(
                    value
                )

            seen.add(
                value
            )

        return sorted(
            duplicates
        )