from pathlib import Path
import re


class KnowledgeOrganizationValidator:
    """
    Phase 8.4 — Knowledge Organization Validation.

    Validates organized knowledge against the canonical
    knowledge Markdown document.

    Rules:

    - H1 is the canonical document title.
    - H2 sections are actual knowledge sections.
    - Canonical metadata is ignored during content comparison.
    - The document title preserved by the organizer is allowed.
    - NOISE must never appear in organized output.
    - REVIEW and OTHER are allowed but reported.
    - Source traceability must exist.
    - Categories must belong to the approved taxonomy.
    """

    # ========================================================
    # APPROVED TAXONOMY
    # ========================================================

    VALID_CATEGORIES = {
        "college_overview",
        "admissions",
        "academics",
        "departments",
        "faculty",
        "fees",
        "scholarships",
        "hostel",
        "examinations",
        "placements",
        "facilities",
        "student_services",
        "events",
        "notices",
        "research",
        "contact",
        "other",
        "review",
    }

    # ========================================================
    # PUBLIC API
    # ========================================================

    def validate(
        self,
        canonical_path: str | Path,
        organized_root: str | Path,
    ) -> dict:

        canonical_path = Path(canonical_path)
        organized_root = Path(organized_root)

        # ----------------------------------------------------
        # INPUT VALIDATION
        # ----------------------------------------------------

        if not canonical_path.exists():
            raise FileNotFoundError(
                f"Canonical document does not exist: "
                f"{canonical_path}"
            )

        if not canonical_path.is_file():
            raise ValueError(
                f"Canonical path is not a file: "
                f"{canonical_path}"
            )

        if not organized_root.exists():
            raise FileNotFoundError(
                f"Organized knowledge directory does not "
                f"exist: {organized_root}"
            )

        if not organized_root.is_dir():
            raise ValueError(
                f"Organized knowledge path is not a "
                f"directory: {organized_root}"
            )

        # ----------------------------------------------------
        # READ CANONICAL
        # ----------------------------------------------------

        canonical_content = canonical_path.read_text(
            encoding="utf-8"
        )

        canonical_title = (
            self._extract_document_title(
                canonical_content
            )
        )

        canonical_sections = (
            self._extract_sections(
                canonical_content
            )
        )

        domain = self._extract_domain(
            canonical_path,
            canonical_content,
        )

        # ----------------------------------------------------
        # READ ORGANIZED FILES
        # ----------------------------------------------------

        organized_files = sorted(
            organized_root.rglob("*.md")
        )

        errors = []
        warnings = []

        organized_sections = []

        category_counts = {}

        # ----------------------------------------------------
        # DOMAIN ISOLATION
        # ----------------------------------------------------

        actual_domain = organized_root.name

        if actual_domain != domain:

            errors.append(
                "Domain isolation failure: "
                f"expected '{domain}', "
                f"found '{actual_domain}'"
            )

        # ----------------------------------------------------
        # READ CATEGORY FILES
        # ----------------------------------------------------

        for file_path in organized_files:

            relative_parts = (
                file_path.relative_to(
                    organized_root
                ).parts
            )

            if not relative_parts:
                continue

            category = relative_parts[0]

            # ------------------------------------------------
            # CATEGORY VALIDATION
            # ------------------------------------------------

            if category not in self.VALID_CATEGORIES:

                errors.append(
                    f"Invalid category directory: "
                    f"{category}"
                )

                continue

            category_counts[category] = (
                category_counts.get(
                    category,
                    0,
                )
                + 1
            )

            # ------------------------------------------------
            # EMPTY FILE
            # ------------------------------------------------

            content = file_path.read_text(
                encoding="utf-8"
            )

            if not content.strip():

                errors.append(
                    f"Empty organized file: "
                    f"{file_path}"
                )

                continue

            # ------------------------------------------------
            # CATEGORY HEADER
            # ------------------------------------------------

            expected_category_header = (
                "# "
                + self._display_category(
                    category
                )
            )

            if (
                expected_category_header
                not in content
            ):

                errors.append(
                    f"{file_path}: "
                    "missing category header"
                )

            # ------------------------------------------------
            # SOURCE DOCUMENT
            # ------------------------------------------------

            if (
                "**Source Document:**"
                not in content
            ):

                errors.append(
                    f"{file_path}: "
                    "missing source document metadata"
                )

            # ------------------------------------------------
            # ORGANIZED SECTIONS
            # ------------------------------------------------

            sections = (
                self._extract_organized_sections(
                    content,
                    file_path,
                    category,
                )
            )

            organized_sections.extend(
                sections
            )

        # ====================================================
        # REMOVE PRESERVED DOCUMENT TITLE
        # ====================================================

        """
        The organizer may preserve the original H1 document
        title inside an 'other' file as an H2.

        Example:

            Canonical:
                # GOVERNMENT GIRLS' P.G. COLLEGE, GHAZIPUR

            Organized:
                # Other

                ## GOVERNMENT GIRLS' P.G. COLLEGE, GHAZIPUR

        This is metadata preservation, NOT an unexpected
        knowledge section.
        """

        filtered_organized_sections = []

        title_normalized = (
            self._normalize_heading(
                canonical_title
            )
            if canonical_title
            else ""
        )

        for section in organized_sections:

            heading_normalized = (
                self._normalize_heading(
                    section["heading"]
                )
            )

            if (
                title_normalized
                and heading_normalized
                == title_normalized
            ):
                continue

            filtered_organized_sections.append(
                section
            )

        organized_sections = (
            filtered_organized_sections
        )

        # ====================================================
        # DUPLICATE SECTION CHECK
        # ====================================================

        seen = {}

        duplicate_sections = []

        for section in organized_sections:

            normalized = self._normalize_text(
                section["text"]
            )

            if not normalized:
                continue

            if normalized in seen:

                duplicate_sections.append(
                    {
                        "first": seen[normalized],
                        "duplicate": section,
                    }
                )

            else:

                seen[normalized] = section

        for duplicate in duplicate_sections:

            errors.append(
                "Duplicate organized section: "
                f"{duplicate['duplicate']['heading']} "
                f"in "
                f"{duplicate['duplicate']['file']}"
            )

        # ====================================================
        # CANONICAL MAP
        # ====================================================

        canonical_map = {}

        for section in canonical_sections:

            normalized = self._normalize_text(
                section["text"]
            )

            if not normalized:
                continue

            canonical_map[
                normalized
            ] = section

        # ====================================================
        # ORGANIZED MAP
        # ====================================================

        organized_map = {}

        for section in organized_sections:

            normalized = self._normalize_text(
                section["text"]
            )

            if normalized:

                organized_map[
                    normalized
                ] = section

        # ====================================================
        # EXPECTED SECTIONS
        # ====================================================

        expected_sections = []

        for section in canonical_sections:

            if self._looks_like_noise(
                section
            ):
                continue

            expected_sections.append(
                section
            )

        expected_map = {}

        for section in expected_sections:

            normalized = self._normalize_text(
                section["text"]
            )

            if normalized:

                expected_map[
                    normalized
                ] = section

        # ====================================================
        # MISSING CONTENT
        # ====================================================

        missing_sections = []

        for normalized, section in (
            expected_map.items()
        ):

            if normalized in organized_map:
                continue

            candidate = (
                self._find_content_match(
                    section,
                    organized_sections,
                )
            )

            if candidate is not None:
                continue

            missing_sections.append(
                section
            )

            errors.append(
                "Missing non-noise section: "
                f"{section['heading']}"
            )

        # ====================================================
        # UNEXPECTED CONTENT
        # ====================================================

        unexpected_sections = []

        for section in organized_sections:

            normalized = self._normalize_text(
                section["text"]
            )

            if not normalized:
                continue

            if normalized in canonical_map:
                continue

            canonical_match = (
                self._find_canonical_match(
                    section,
                    canonical_sections,
                )
            )

            if canonical_match is not None:
                continue

            unexpected_sections.append(
                section
            )

        # ====================================================
        # NOISE CHECK
        # ====================================================

        noise_in_output = []

        for section in organized_sections:

            if self._looks_like_noise(
                section
            ):

                noise_in_output.append(
                    section
                )

                errors.append(
                    "Noise content found in "
                    "organized output: "
                    f"{section['heading']}"
                )

        # ====================================================
        # TRACEABILITY
        # ====================================================

        for section in organized_sections:

            if not section["source_lines"]:

                errors.append(
                    "Missing source traceability: "
                    f"{section['heading']} "
                    f"in {section['file']}"
                )

        # ====================================================
        # REVIEW / OTHER
        # ====================================================

        review_count = sum(
            1
            for section in organized_sections
            if section["category"] == "review"
        )

        other_count = sum(
            1
            for section in organized_sections
            if section["category"] == "other"
        )

        if other_count > 0:

            warnings.append(
                f"{other_count} section(s) "
                "classified as 'other'."
            )

        if review_count > 0:

            warnings.append(
                f"{review_count} section(s) "
                "classified as 'review'."
            )

        # ====================================================
        # BUILD RESULT
        # ====================================================

        result = {
            "canonical_file": str(
                canonical_path
            ),

            "organized_root": str(
                organized_root
            ),

            "domain": domain,

            "canonical_sections": len(
                canonical_sections
            ),

            "organized_sections": len(
                organized_sections
            ),

            "expected_sections": len(
                expected_sections
            ),

            "missing_sections": len(
                missing_sections
            ),

            "unexpected_sections": len(
                unexpected_sections
            ),

            "duplicate_sections": len(
                duplicate_sections
            ),

            "noise_in_output": len(
                noise_in_output
            ),

            "review_sections": review_count,

            "other_sections": other_count,

            "category_files": category_counts,

            "errors": errors,

            "warnings": warnings,

            "valid": len(errors) == 0,
        }

        return result

    # ========================================================
    # DOCUMENT TITLE
    # ========================================================

    def _extract_document_title(
        self,
        markdown: str,
    ) -> str | None:
        """
        Extract the first H1 title from the canonical
        knowledge document.
        """

        for line in markdown.splitlines():

            match = re.match(
                r"^#\s+(.+?)\s*$",
                line,
            )

            if match:

                return match.group(1).strip()

        return None

    # ========================================================
    # CANONICAL SECTION EXTRACTION
    # ========================================================

    def _extract_sections(
        self,
        markdown: str,
    ) -> list[dict]:

        lines = markdown.splitlines()

        sections = []

        current_heading = None
        current_lines = []
        current_start_line = None

        for line_number, line in enumerate(
            lines,
            start=1,
        ):

            # ------------------------------------------------
            # ONLY H2 = KNOWLEDGE SECTION
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

                    text = (
                        self._clean_canonical_text(
                            text
                        )
                    )

                    if text:

                        sections.append(
                            {
                                "heading":
                                    current_heading,

                                "text":
                                    text,

                                "start_line":
                                    current_start_line,

                                "end_line":
                                    line_number - 1,
                            }
                        )

                current_heading = (
                    match.group(1).strip()
                )

                current_lines = []

                current_start_line = (
                    line_number
                )

                continue

            # ------------------------------------------------
            # IGNORE H1
            # ------------------------------------------------

            if re.match(
                r"^#\s+",
                line,
            ):
                continue

            if current_heading is not None:

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

            text = (
                self._clean_canonical_text(
                    text
                )
            )

            if text:

                sections.append(
                    {
                        "heading":
                            current_heading,

                        "text":
                            text,

                        "start_line":
                            current_start_line,

                        "end_line":
                            len(lines),
                    }
                )

        return sections

    # ========================================================
    # ORGANIZED SECTION EXTRACTION
    # ========================================================

    def _extract_organized_sections(
        self,
        content: str,
        file_path: Path,
        category: str,
    ) -> list[dict]:

        lines = content.splitlines()

        sections = []

        current_heading = None
        current_lines = []
        source_lines = None

        for line in lines:

            # ------------------------------------------------
            # SOURCE LINE MARKER
            # ------------------------------------------------

            source_match = re.search(
                r"Source lines:\s*(\d+)-(\d+)",
                line,
                flags=re.IGNORECASE,
            )

            if source_match:

                source_lines = (
                    int(
                        source_match.group(1)
                    ),
                    int(
                        source_match.group(2)
                    ),
                )

                continue

            # ------------------------------------------------
            # SECTION HEADING
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

                                "category":
                                    category,

                                "file":
                                    str(file_path),

                                "source_lines":
                                    source_lines,
                            }
                        )

                current_heading = (
                    match.group(1).strip()
                )

                current_lines = []

                source_lines = None

                continue

            # ------------------------------------------------
            # IGNORE BEFORE FIRST H2
            # ------------------------------------------------

            if current_heading is None:
                continue

            # ------------------------------------------------
            # IGNORE SEPARATOR
            # ------------------------------------------------

            if line.strip() == "---":
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

                        "category":
                            category,

                        "file":
                            str(file_path),

                        "source_lines":
                            source_lines,
                    }
                )

        return sections

    # ========================================================
    # CANONICAL TEXT CLEANING
    # ========================================================

    def _clean_canonical_text(
        self,
        text: str,
    ) -> str:

        lines = text.splitlines()

        cleaned = []

        for line in lines:

            stripped = line.strip()

            if re.match(
                r"^\*\*Source URL:\*\*",
                stripped,
                flags=re.IGNORECASE,
            ):
                continue

            if re.match(
                r"^\*\*Source Document:\*\*",
                stripped,
                flags=re.IGNORECASE,
            ):
                continue

            if re.match(
                r"^\*\*Section:\*\*",
                stripped,
                flags=re.IGNORECASE,
            ):
                continue

            cleaned.append(line)

        return "\n".join(
            cleaned
        ).strip()

    # ========================================================
    # CONTENT MATCHING
    # ========================================================

    def _find_content_match(
        self,
        canonical_section: dict,
        organized_sections: list[dict],
    ):

        canonical_text = self._normalize_text(
            canonical_section["text"]
        )

        canonical_heading = (
            self._normalize_heading(
                canonical_section["heading"]
            )
        )

        if not canonical_text:
            return None

        for organized in organized_sections:

            organized_heading = (
                self._normalize_heading(
                    organized["heading"]
                )
            )

            if (
                organized_heading
                != canonical_heading
            ):
                continue

            organized_text = (
                self._normalize_text(
                    organized["text"]
                )
            )

            if not organized_text:
                continue

            if organized_text == canonical_text:
                return organized

            if canonical_text in organized_text:
                return organized

            if organized_text in canonical_text:
                return organized

        return None

    def _find_canonical_match(
        self,
        organized_section: dict,
        canonical_sections: list[dict],
    ):

        organized_heading = (
            self._normalize_heading(
                organized_section["heading"]
            )
        )

        organized_text = (
            self._normalize_text(
                organized_section["text"]
            )
        )

        if not organized_text:
            return None

        for canonical in canonical_sections:

            canonical_heading = (
                self._normalize_heading(
                    canonical["heading"]
                )
            )

            if (
                canonical_heading
                != organized_heading
            ):
                continue

            canonical_text = (
                self._normalize_text(
                    canonical["text"]
                )
            )

            if not canonical_text:
                continue

            if organized_text in canonical_text:
                return canonical

            if canonical_text in organized_text:
                return canonical

        return None

    # ========================================================
    # NOISE DETECTION
    # ========================================================

    def _looks_like_noise(
        self,
        section: dict,
    ) -> bool:

        heading = (
            section["heading"]
            .strip()
            .lower()
        )

        text = (
            section["text"]
            .strip()
            .lower()
        )

        noise_headings = {
            "search here",
            "accessibility options",
            "accessibility",
            "menu",
            "navigation",
        }

        if heading in noise_headings:
            return True

        noise_patterns = (
            "accessibility options",
            "created by",
            "important links",
        )

        for pattern in noise_patterns:

            if pattern in text:
                return True

        return False

    # ========================================================
    # DOMAIN
    # ========================================================

    def _extract_domain(
        self,
        markdown_path: Path,
        content: str,
    ) -> str:

        match = re.search(
            r"\*\*Domain:\*\*\s*(.+)",
            content,
            flags=re.IGNORECASE,
        )

        if match:

            domain = (
                match.group(1)
                .strip()
            )

            domain = re.sub(
                r"[^a-zA-Z0-9._-]",
                "",
                domain,
            )

            if domain:
                return domain

        parts = markdown_path.parts

        try:

            index = parts.index(
                "knowledge"
            )

            if (
                index + 1
                < len(parts)
            ):

                return parts[
                    index + 1
                ]

        except ValueError:
            pass

        return "unknown"

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

        value = re.sub(
            r"<!--.*?-->",
            "",
            value,
            flags=re.DOTALL,
        )

        value = re.sub(
            r"\[([^\]]+)\]\([^)]+\)",
            r"\1",
            value,
        )

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return value.strip()

    # ========================================================
    # NORMALIZE HEADING
    # ========================================================

    def _normalize_heading(
        self,
        value: str,
    ) -> str:

        value = (
            value or ""
        ).strip().lower()

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
            .title()
        )