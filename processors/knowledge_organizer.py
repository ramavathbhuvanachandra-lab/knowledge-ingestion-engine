from pathlib import Path
import json
import re


class KnowledgeOrganizer:
    """
    Phase 8.3 — Knowledge Organization.

    Converts canonical knowledge Markdown into
    category-specific Markdown files.

    Responsibilities:

    - Read canonical knowledge Markdown.
    - Determine section decision:
        KEEP
        REVIEW
        NOISE
    - Exclude NOISE from RAG organization.
    - Preserve REVIEW under review/.
    - Deterministically classify KEEP sections.
    - Preserve original section text.
    - Preserve source-line traceability.
    - Write category-specific Markdown files.
    - Generate an organization manifest.

    This processor:

    - Does NOT summarize content.
    - Does NOT rewrite knowledge.
    - Does NOT use an LLM.
    - Does NOT modify source Markdown.
    """

    # ========================================================
    # FINAL KNOWLEDGE TAXONOMY
    # ========================================================

    CATEGORIES = (
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
    )

    # ========================================================
    # KNOWN NOISE HEADINGS
    # ========================================================

    NOISE_HEADINGS = {
        "search here",
        "accessibility options",
        "accessibility",
        "menu",
        "navigation",
    }

    # ========================================================
    # KNOWN NOISE CONTENT
    #
    # These are obvious website UI/navigation signals.
    # Keep this list conservative.
    # ========================================================

    NOISE_PATTERNS = (
        "accessibility options",
        "created by",
        "arrow_downward",
    )

    # ========================================================
    # CATEGORY RULES
    #
    # Heading matches have higher priority than body text.
    # ========================================================

    CATEGORY_RULES = {

        "admissions": (
            "admission",
            "admissions",
            "eligibility",
            "application",
            "entrance",
            "enrolment",
            "enrollment",
            "registration",
            "prospectus",
            "applying",
        ),

        "scholarships": (
            "scholarship",
            "scholarships",
            "fellowship",
            "financial aid",
            "financial assistance",
            "stipend",
        ),

        "hostel": (
            "hostel",
            "accommodation",
            "residence hall",
            "residential",
            "girls hostel",
            "boys hostel",
        ),

        "placements": (
            "placement",
            "placements",
            "career",
            "recruitment",
            "campus recruitment",
            "training and placement",
        ),

        "faculty": (
            "faculty",
            "faculties",
            "professor",
            "professors",
            "teacher",
            "teachers",
            "teaching staff",
            "staff directory",
        ),

        "departments": (
            "department",
            "departments",
            "school of",
            "centre of",
            "center of",
            "academic department",
        ),

        "academics": (
            "academic",
            "academics",
            "course",
            "courses",
            "programme",
            "programmes",
            "program",
            "curriculum",
            "syllabus",
            "degree",
            "degrees",
            "undergraduate",
            "postgraduate",
            "ug",
            "pg",
            "semester",
            "credit",
            "credits",
        ),

        "examinations": (
            "examination",
            "examinations",
            "exam",
            "exams",
            "result",
            "results",
            "question paper",
            "date sheet",
            "timetable",
            "evaluation",
            "assessment",
        ),

        "research": (
            "research",
            "researchers",
            "research project",
            "research projects",
            "publication",
            "publications",
            "innovation",
            "laboratory",
            "laboratories",
            "patent",
            "patents",
        ),

        "facilities": (
            "facility",
            "facilities",
            "infrastructure",
            "library",
            "laboratory",
            "lab",
            "labs",
            "auditorium",
            "gym",
            "sports",
            "cafeteria",
            "mess",
            "transport",
            "campus facilities",
        ),

        "student_services": (
            "student service",
            "student services",
            "student support",
            "student welfare",
            "counselling",
            "counseling",
            "medical",
            "health centre",
            "health center",
            "grievance",
            "anti ragging",
            "ragging",
            "student affairs",
        ),

        "events": (
            "event",
            "events",
            "festival",
            "fest",
            "seminar",
            "conference",
            "workshop",
            "webinar",
            "celebration",
        ),

        "notices": (
            "notice",
            "notices",
            "notification",
            "notifications",
            "circular",
            "announcement",
            "announcements",
            "latest news",
            "news",
        ),

        "contact": (
            "contact",
            "contact us",
            "address",
            "phone",
            "telephone",
            "email",
            "e-mail",
            "reach us",
        ),

        "college_overview": (
            "about",
            "about us",
            "overview",
            "profile",
            "college profile",
            "institute profile",
            "institute overview",
            "college history",
            "history",
            "principal's message",
            "principal message",
            "director's message",
            "director message",
            "vision",
            "mission",
            "motto",
            "objectives",
            "objectives of the college",
        ),
    }

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        output_path: str | Path = (
            "storage/organized_knowledge"
        ),
    ):
        self.output_path = Path(
            output_path
        )

    # ========================================================
    # PUBLIC API
    # ========================================================

    def organize(
        self,
        markdown_path: str | Path,
    ) -> dict:
        """
        Organize one canonical Markdown document.

        Returns:
            Organization manifest dictionary.
        """

        markdown_path = Path(
            markdown_path
        )

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

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

        content = markdown_path.read_text(
            encoding="utf-8"
        )

        # ----------------------------------------------------
        # EXTRACT SECTIONS
        # ----------------------------------------------------

        sections = self._extract_sections(
            content
        )

        # ----------------------------------------------------
        # DOMAIN
        # ----------------------------------------------------

        domain = self._extract_domain(
            markdown_path,
            content,
        )

        document_name = (
            markdown_path.stem
        )

        college_root = (
            self.output_path
            / domain
        )

        college_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        # ----------------------------------------------------
        # CATEGORY COUNTS
        # ----------------------------------------------------

        counts = {
            category: 0
            for category in self.CATEGORIES
        }

        organized_sections = []

        # ----------------------------------------------------
        # PROCESS SECTIONS
        # ----------------------------------------------------

        for index, section in enumerate(
            sections,
            start=1,
        ):

            decision = (
                section["decision"]
            )

            # ------------------------------------------------
            # NOISE
            # ------------------------------------------------

            if decision == "NOISE":
                continue

            # ------------------------------------------------
            # REVIEW
            # ------------------------------------------------

            if decision == "REVIEW":

                category = "review"

            # ------------------------------------------------
            # KEEP
            # ------------------------------------------------

            elif decision == "KEEP":

                category = (
                    self.classify_section(
                        heading=section[
                            "heading"
                        ],
                        text=section[
                            "text"
                        ],
                    )
                )

            else:

                raise ValueError(
                    f"Unknown triage decision: "
                    f"{decision}"
                )

            counts[category] += 1

            organized_sections.append(
                {
                    "index": index,
                    "heading": section[
                        "heading"
                    ],
                    "text": section[
                        "text"
                    ],
                    "decision": decision,
                    "category": category,
                    "start_line": section[
                        "start_line"
                    ],
                    "end_line": section[
                        "end_line"
                    ],
                }
            )

        # ----------------------------------------------------
        # WRITE CATEGORY FILES
        # ----------------------------------------------------

        written_files = []

        for category in self.CATEGORIES:

            category_sections = [
                section
                for section in organized_sections
                if section[
                    "category"
                ] == category
            ]

            if not category_sections:
                continue

            category_dir = (
                college_root
                / category
            )

            category_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            output_file = (
                category_dir
                / f"{document_name}.md"
            )

            self._write_category_file(
                output_file=output_file,
                domain=domain,
                source_document=markdown_path,
                category=category,
                sections=category_sections,
            )

            written_files.append(
                str(output_file)
            )

        # ----------------------------------------------------
        # MANIFEST
        # ----------------------------------------------------

        manifest = {
            "source_document": str(
                markdown_path
            ),
            "domain": domain,
            "document": document_name,
            "categories": counts,
            "total_sections": len(
                sections
            ),
            "organized_sections": len(
                organized_sections
            ),
            "written_files": written_files,
        }

        manifest_path = (
            college_root
            / f"{document_name}.organization.json"
        )

        manifest_path.write_text(
            json.dumps(
                manifest,
                indent=4,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        # ----------------------------------------------------
        # LOGGING
        # ----------------------------------------------------

        print(
            f"Organized Knowledge : "
            f"{college_root}"
        )

        print(
            f"Source              : "
            f"{markdown_path}"
        )

        print(
            f"Sections             : "
            f"{len(sections)}"
        )

        print(
            f"Organized            : "
            f"{len(organized_sections)}"
        )

        print(
            f"Files                : "
            f"{len(written_files)}"
        )

        return manifest

    # ========================================================
    # SECTION DECISION
    # ========================================================

    def _decide_section(
        self,
        heading: str,
        text: str,
    ) -> str:
        """
        Determine whether a section should be:

            KEEP
            REVIEW
            NOISE

        Important:

        REVIEW is NOT inferred from generic phrases such
        as "Read More".

        Generic website phrases can occur inside valid
        college content.

        Therefore:

        - Known UI/navigation content → NOISE
        - Everything else → KEEP
        - REVIEW comes only from explicit markers
        """

        heading_normalized = (
            self._normalize(
                heading
            )
        )

        text_normalized = (
            self._normalize(
                text
            )
        )

        # ----------------------------------------------------
        # NOISE — KNOWN HEADING
        # ----------------------------------------------------

        if (
            heading_normalized
            in self.NOISE_HEADINGS
        ):
            return "NOISE"

        # ----------------------------------------------------
        # NOISE — KNOWN UI CONTENT
        # ----------------------------------------------------

        for pattern in self.NOISE_PATTERNS:

            normalized_pattern = (
                self._normalize(
                    pattern
                )
            )

            if self._keyword_match(
                text_normalized,
                normalized_pattern,
            ):
                return "NOISE"

        # ----------------------------------------------------
        # DEFAULT
        #
        # IMPORTANT:
        # Never discard unknown content here.
        # ----------------------------------------------------

        return "KEEP"

    # ========================================================
    # SECTION CLASSIFICATION
    # ========================================================

    def classify_section(
        self,
        heading: str,
        text: str,
    ) -> str:

        heading_text = self._normalize(
            heading
        )

        content_text = self._normalize(
            text
        )

        combined = (
            heading_text
            + " "
            + content_text
        )

        # ----------------------------------------------------
        # HEADING HAS PRIORITY
        # ----------------------------------------------------

        for category, keywords in (
            self.CATEGORY_RULES.items()
        ):

            for keyword in keywords:

                normalized_keyword = (
                    self._normalize(
                        keyword
                    )
                )

                if self._keyword_match(
                    heading_text,
                    normalized_keyword,
                ):
                    return category

        # ----------------------------------------------------
        # CONTENT FALLBACK
        # ----------------------------------------------------

        scores = {}

        for category, keywords in (
            self.CATEGORY_RULES.items()
        ):

            score = 0

            for keyword in keywords:

                normalized_keyword = (
                    self._normalize(
                        keyword
                    )
                )

                if self._keyword_match(
                    combined,
                    normalized_keyword,
                ):
                    score += 1

            if score:
                scores[category] = score

        if scores:

            return max(
                scores,
                key=scores.get,
            )

        # ----------------------------------------------------
        # SAFE FALLBACK
        # ----------------------------------------------------

        return "other"

    # ========================================================
    # SECTION EXTRACTION
    # ========================================================

    def _extract_sections(
        self,
        markdown: str,
    ) -> list[dict]:

        lines = markdown.splitlines()

        sections = []

        current_heading = None
        current_level = None
        current_lines = []
        current_start_line = None
        current_decision = None

        for line_number, line in enumerate(
            lines,
            start=1,
        ):

            # ------------------------------------------------
            # EXPLICIT DECISION MARKER
            # ------------------------------------------------

            marker = self._parse_decision(
                line
            )

            if marker:

                current_decision = marker
                continue

            # ------------------------------------------------
            # MARKDOWN HEADING
            # ------------------------------------------------

            match = re.match(
                r"^(#{1,6})\s+(.+?)\s*$",
                line,
            )

            if match:

                # --------------------------------------------
                # SAVE PREVIOUS SECTION
                # --------------------------------------------

                if current_heading is not None:

                    section = (
                        self._build_section(
                            heading=(
                                current_heading
                            ),
                            level=(
                                current_level
                            ),
                            lines=(
                                current_lines
                            ),
                            start_line=(
                                current_start_line
                            ),
                            end_line=(
                                line_number - 1
                            ),
                            decision=(
                                current_decision
                            ),
                        )
                    )

                    if section:
                        sections.append(
                            section
                        )

                # --------------------------------------------
                # START NEW SECTION
                # --------------------------------------------

                current_heading = (
                    match.group(2).strip()
                )

                current_level = len(
                    match.group(1)
                )

                current_lines = []

                current_start_line = (
                    line_number
                )

                current_decision = None

                continue

            if current_heading is not None:

                current_lines.append(
                    line
                )

        # ----------------------------------------------------
        # SAVE FINAL SECTION
        # ----------------------------------------------------

        if current_heading is not None:

            section = (
                self._build_section(
                    heading=current_heading,
                    level=current_level,
                    lines=current_lines,
                    start_line=current_start_line,
                    end_line=len(lines),
                    decision=current_decision,
                )
            )

            if section:
                sections.append(
                    section
                )

        return sections

    # ========================================================
    # BUILD SECTION
    # ========================================================

    def _build_section(
        self,
        heading,
        level,
        lines,
        start_line,
        end_line,
        decision,
    ):

        text = "\n".join(
            lines
        ).strip()

        if not text:
            return None

        # ----------------------------------------------------
        # DECIDE ONLY WHEN THERE IS NO EXPLICIT MARKER
        # ----------------------------------------------------

        if decision is None:

            decision = (
                self._decide_section(
                    heading=heading,
                    text=text,
                )
            )

        return {
            "heading": heading,
            "level": level,
            "text": text,
            "start_line": start_line,
            "end_line": end_line,
            "decision": decision,
        }

    # ========================================================
    # PARSE DECISION MARKER
    # ========================================================

    def _parse_decision(
        self,
        line: str,
    ) -> str | None:

        stripped = (
            line.strip()
            .upper()
        )

        if stripped in (
            "[KEEP]",
            "KEEP",
            "<KEEP>",
        ):
            return "KEEP"

        if stripped in (
            "[NOISE]",
            "NOISE",
            "<NOISE>",
        ):
            return "NOISE"

        if stripped in (
            "[REVIEW]",
            "REVIEW",
            "<REVIEW>",
        ):
            return "REVIEW"

        return None

    # ========================================================
    # DOMAIN EXTRACTION
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

            domain = match.group(
                1
            ).strip()

            domain = self._clean_component(
                domain
            )

            if domain:
                return domain

        parts = markdown_path.parts

        try:

            index = parts.index(
                "knowledge"
            )

            if index + 1 < len(parts):

                return self._clean_component(
                    parts[index + 1]
                )

        except ValueError:
            pass

        return "unknown"

    # ========================================================
    # WRITE CATEGORY FILE
    # ========================================================

    def _write_category_file(
        self,
        output_file: Path,
        domain: str,
        source_document: Path,
        category: str,
        sections: list[dict],
    ) -> None:

        lines = []

        lines.append(
            f"# {self._display_category(category)}"
        )

        lines.append("")

        lines.append(
            f"**Domain:** {domain}"
        )

        lines.append(
            f"**Source Document:** "
            f"{source_document.name}"
        )

        lines.append(
            f"**Category:** {category}"
        )

        lines.append("")

        lines.append("---")

        lines.append("")

        for section in sections:

            heading = section[
                "heading"
            ]

            text = section[
                "text"
            ]

            decision = section[
                "decision"
            ]

            lines.append(
                f"## {heading}"
            )

            lines.append("")

            lines.append(text)

            lines.append("")

            lines.append(
                f"<!-- "
                f"Source lines: "
                f"{section['start_line']}-"
                f"{section['end_line']} "
                f"| Decision: {decision}"
                f" -->"
            )

            lines.append("")

            lines.append("---")

            lines.append("")

        output_file.write_text(
            "\n".join(lines),
            encoding="utf-8",
        )

    # ========================================================
    # NORMALIZATION
    # ========================================================

    def _normalize(
        self,
        value: str,
    ) -> str:

        value = (
            value or ""
        ).strip().lower()

        value = re.sub(
            r"[^a-z0-9]+",
            " ",
            value,
        )

        return re.sub(
            r"\s+",
            " ",
            value,
        ).strip()

    # ========================================================
    # KEYWORD MATCH
    # ========================================================

    def _keyword_match(
        self,
        text: str,
        keyword: str,
    ) -> bool:

        if not text or not keyword:
            return False

        return (
            f" {keyword} "
            in f" {text} "
        )

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

                cleaned.append(
                    "_"
                )

        result = "".join(
            cleaned
        )

        result = re.sub(
            r"_+",
            "_",
            result,
        )

        return (
            result.strip("._-")
            or "unknown"
        )

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