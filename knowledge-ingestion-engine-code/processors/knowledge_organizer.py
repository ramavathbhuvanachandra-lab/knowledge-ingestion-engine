from pathlib import Path
from urllib.parse import urlparse
import json
import re


class KnowledgeOrganizer:
    """
    PHASE 8.3 — CLEAN + ORGANIZE KNOWLEDGE

    Pipeline:

        Canonical Markdown
              ↓
        Main-content isolation
              ↓
        Noise cleanup
              ↓
        Section extraction
              ↓
        KEEP / REVIEW / NOISE
              ↓
        Knowledge units
              ↓
        Dynamic RAG planner

    HARD RULES:

    1. Never lose useful content.
    2. Preserve source-document boundaries.
    3. Remove only obvious website noise.
    4. Preserve content before the first heading.
    5. Preserve REVIEW content.
    6. Do not merge source documents here.
    7. Classification must consider document context.
    8. A program name inside an admissions page is admissions
       knowledge, even when the program is "MS by Research".
    """

    # ========================================================
    # TOPIC RULES
    # ========================================================

    TOPIC_RULES = {

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
            "admission process",
            "application process",
        ),

        "scholarships": (
            "scholarship",
            "scholarships",
            "fellowship",
            "financial aid",
            "financial assistance",
            "stipend",
            "fee waiver",
        ),

        "hostel": (
            "hostel",
            "hostels",
            "accommodation",
            "residence hall",
            "residential life",
            "residential",
            "girls hostel",
            "boys hostel",
            "student housing",
            "campus housing",
        ),

        "placements": (
            "placement",
            "placements",
            "career",
            "careers",
            "recruitment",
            "campus recruitment",
            "training and placement",
            "internship",
            "internships",
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
            "faculty members",
        ),

        "departments": (
            "department",
            "departments",
            "school of",
            "academic department",
            "faculty of",
        ),

        "academics": (
            "academic",
            "academics",
            "curriculum",
            "syllabus",
            "degree",
            "degrees",
            "undergraduate",
            "postgraduate",
            "doctoral",
            "phd",
            "semester",
            "credit",
            "credits",
            "academic program",
            "academic programmes",
            "academic affairs",
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
            "grading",
            "grade",
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
            "lab",
            "labs",
            "patent",
            "patents",
            "research centre",
            "research center",
        ),

        "facilities": (
            "facility",
            "facilities",
            "infrastructure",
            "library",
            "auditorium",
            "gym",
            "sports",
            "cafeteria",
            "mess",
            "transport",
            "campus facilities",
            "campus infrastructure",
            "security",
            "parking",
            "computer center",
            "computer centre",
            "digital infrastructure",
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
            "healthcare",
            "grievance",
            "anti ragging",
            "ragging",
            "student affairs",
            "student office",
        ),

        "administration": (
            "administration",
            "administrative",
            "registrar",
            "director",
            "dean",
            "deputy director",
            "office of administration",
            "office of director",
            "office of registrar",
            "governance",
            "statutory body",
            "statutory bodies",
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
            "lecture",
            "lecture series",
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
            "order",
            "orders",
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
            "contact details",
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
            "accreditation",
            "accredited",
            "motto",
            "naac",
            "ugc",
            "goal",
            "goals",
            "objective",
            "objectives",
        ),
    }

    # ========================================================
    # DOCUMENT-LEVEL ANCHORS
    # ========================================================

    DOCUMENT_ANCHORS = {

        "admissions": (
            "admission",
            "admissions",
            "admission_process",
            "admission_links",
            "admission_program",
            "admission_programs",
        ),

        "administration": (
            "administration",
            "administrative",
            "registrar",
            "office_of_administration",
            "office_of_registrar",
            "office_of_director",
            "office_of_deputy_director",
        ),

        "departments": (
            "department",
            "departments",
        ),

        "faculty": (
            "faculty",
            "faculties",
            "faculty_members",
            "faculty_positions",
        ),

        "research": (
            "research",
            "research_project",
            "research_projects",
            "research_development",
            "office_of_research",
        ),

        "hostel": (
            "hostel",
            "hostels",
            "residence",
            "residential",
        ),

        "placements": (
            "placement",
            "placements",
            "career",
            "careers",
            "internship",
        ),

        "scholarships": (
            "scholarship",
            "scholarships",
            "fellowship",
        ),

        "student_services": (
            "student_service",
            "student_services",
            "student_wellbeing",
            "student_welfare",
            "health_center",
            "health_centre",
            "office_of_students",
            "grievance",
        ),

        "facilities": (
            "infrastructure",
            "facilities",
            "facility",
            "library",
            "computer_center",
            "computer_centre",
            "digital_infrastructure",
            "transport",
            "sports",
        ),

        "college_overview": (
            "about",
            "about_iitj",
            "overview",
            "history",
            "vision",
            "mission",
            "vision_and_mission",
            "profile",
        ),

        "academics": (
            "academic",
            "academics",
            "academic_program",
            "academic_programs",
            "academic_affairs",
            "courses",
            "curriculum",
            "syllabus",
        ),

        "events": (
            "event",
            "events",
            "festival",
            "seminar",
            "conference",
            "workshop",
            "lecture",
        ),

        "notices": (
            "notice",
            "notices",
            "notification",
            "news",
            "announcement",
        ),

        "contact": (
            "contact",
            "contacts",
            "administrative_contact",
        ),
    }

    # ========================================================
    # NOISE HEADINGS
    # ========================================================

    NOISE_HEADINGS = {
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
        "select language",
        "translation",
        "rate this translation",
    }

    # ========================================================
    # NOISE LINE PATTERNS
    # ========================================================

    NOISE_LINE_PATTERNS = (
        r"redirecttologinpage",
        r"translation-plugin\.bhashini\.co\.in",
        r"powered by.*bhashini",
        r"feedback\.svg",
        r"arrow_downward",
        r"ux4g accessibility tool",
        r"created by.*ux4g",
        r"open the accessibility option",
        r"rate this translation",
        r"do you like to give feedback",
        r"^submit$",
        r"^accessibility options",
        r"^bigger text$",
        r"^smaller text$",
        r"^text spacing$",
        r"^line height$",
        r"^dyslexia friendly$",
        r"^adhd mode$",
        r"^saturation low",
        r"^light-dark$",
        r"^invert colors$",
        r"^highlight links$",
        r"^text to speech$",
        r"^cursor$",
        r"^pause animation$",
        r"^hide images$",
        r"^reset all settings$",
        r"^ctrl\+f2$",
    )

    # ========================================================
    # LANGUAGE MENU
    # ========================================================

    LANGUAGE_LINES = {
        "english",
        "assamese",
        "bengali",
        "bodo",
        "dogri",
        "goan konkani",
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
    # LEGACY CRAWLER COMPATIBILITY
    # ========================================================

    def get_save_location(
        self,
        page,
    ):

        url = (
            page.url or ""
        ).lower()

        category = "others"
        filename = "page"

        if "electrical" in url:
            category = "departments/electrical"

        elif (
            "computer" in url
            or "cse" in url
        ):
            category = "departments/cse"

        elif "hostel" in url:
            category = "hostel"

        elif "admission" in url:
            category = "admissions"

        elif "academics" in url:
            category = "academics"

        elif "faculty" in url:
            category = "faculty"

        elif "research" in url:
            category = "research"

        parsed = urlparse(url)

        parts = [
            part
            for part in parsed.path.split("/")
            if part
        ]

        if parts:
            filename = "_".join(parts)

        return category, filename

    # ========================================================
    # PUBLIC API
    # ========================================================

    def organize(
        self,
        markdown_path: str | Path,
    ) -> dict:

        markdown_path = Path(
            markdown_path
        )

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

        domain = self._extract_domain(
            markdown_path,
            content,
        )

        document_name = (
            markdown_path.stem
        )

        document_anchor = (
            self._document_anchor(
                markdown_path
            )
        )

        sections = self._extract_sections(
            content,
            document_name,
        )

        college_root = (
            self.output_path
            / domain
        )

        source_root = (
            college_root
            / "source_documents"
        )

        units_root = (
            college_root
            / "knowledge_units"
        )

        source_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        units_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        kept_units = []
        review_units = []
        noise_units = []

        for index, section in enumerate(
            sections,
            start=1,
        ):

            decision = section[
                "decision"
            ]

            if decision == "NOISE":

                noise_units.append(
                    self._build_unit(
                        domain=domain,
                        source_document=markdown_path,
                        document_name=document_name,
                        section_index=index,
                        section=section,
                        topic="noise",
                        subtopic="website_noise",
                    )
                )

                continue

            if decision == "REVIEW":

                topic = (
                    self._classify_section(
                        heading=section["heading"],
                        text=section["text"],
                        document_anchor=document_anchor,
                        document_name=document_name,
                        markdown_path=markdown_path,
                    )
                )

                review_units.append(
                    self._build_unit(
                        domain=domain,
                        source_document=markdown_path,
                        document_name=document_name,
                        section_index=index,
                        section=section,
                        topic=topic,
                        subtopic="review",
                    )
                )

                continue

            if decision != "KEEP":
                raise ValueError(
                    f"Unknown decision: {decision}"
                )

            topic = (
                self._classify_section(
                    heading=section["heading"],
                    text=section["text"],
                    document_anchor=document_anchor,
                    document_name=document_name,
                    markdown_path=markdown_path,
                )
            )

            subtopic = (
                self._derive_subtopic(
                    section["heading"],
                    topic,
                )
            )

            kept_units.append(
                self._build_unit(
                    domain=domain,
                    source_document=markdown_path,
                    document_name=document_name,
                    section_index=index,
                    section=section,
                    topic=topic,
                    subtopic=subtopic,
                )
            )

        useful_units = (
            kept_units
            + review_units
        )

        # ----------------------------------------------------
        # WRITE CLEAN SOURCE
        # ----------------------------------------------------

        clean_source_path = (
            source_root
            / f"{document_name}.md"
        )

        self._write_clean_source(
            output_file=clean_source_path,
            domain=domain,
            source_document=markdown_path,
            sections=sections,
        )

        # ----------------------------------------------------
        # WRITE SOURCE UNIT MANIFEST
        # ----------------------------------------------------

        source_units_path = (
            units_root
            / f"{document_name}.json"
        )

        source_manifest = {
            "domain": domain,
            "source_document": str(
                markdown_path
            ),
            "clean_document": str(
                clean_source_path
            ),
            "document": document_name,
            "document_anchor": document_anchor,
            "total_sections": len(
                sections
            ),
            "keep_sections": len(
                kept_units
            ),
            "review_sections": len(
                review_units
            ),
            "noise_sections": len(
                noise_units
            ),
            "knowledge_units": useful_units,
        }

        source_units_path.write_text(
            json.dumps(
                source_manifest,
                indent=4,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        # ----------------------------------------------------
        # UPDATE DOMAIN MANIFEST
        # ----------------------------------------------------

        domain_manifest_path = (
            self._update_domain_manifest(
                domain=domain,
                source_document=markdown_path,
                clean_document=clean_source_path,
                units=useful_units,
                total_sections=len(sections),
                keep_sections=len(kept_units),
                review_sections=len(review_units),
                noise_sections=len(noise_units),
            )
        )

        # ----------------------------------------------------
        # TOPIC COUNTS
        # ----------------------------------------------------

        topic_counts = {}

        for unit in useful_units:

            topic = unit[
                "topic"
            ]

            topic_counts[topic] = (
                topic_counts.get(
                    topic,
                    0,
                )
                + 1
            )

        result = {
            "source_document": str(
                markdown_path
            ),
            "domain": domain,
            "document": document_name,
            "document_anchor": document_anchor,
            "categories": topic_counts,
            "total_sections": len(
                sections
            ),
            "organized_sections": len(
                useful_units
            ),
            "kept_sections": len(
                kept_units
            ),
            "review_sections": len(
                review_units
            ),
            "noise_sections": len(
                noise_units
            ),
            "knowledge_units": len(
                useful_units
            ),
            "clean_document": str(
                clean_source_path
            ),
            "source_unit_manifest": str(
                source_units_path
            ),
            "domain_manifest": str(
                domain_manifest_path
            ),
            "written_files": [
                str(
                    clean_source_path
                ),
                str(
                    source_units_path
                ),
            ],
        }

        print(
            "Organized Knowledge :",
            college_root,
        )

        print(
            "Source              :",
            markdown_path,
        )

        print(
            "Document Anchor     :",
            document_anchor or "none",
        )

        print(
            "Sections            :",
            len(sections),
        )

        print(
            "KEEP                :",
            len(kept_units),
        )

        print(
            "REVIEW              :",
            len(review_units),
        )

        print(
            "NOISE               :",
            len(noise_units),
        )

        print(
            "Knowledge Units     :",
            len(useful_units),
        )

        print(
            "Clean Document      :",
            clean_source_path,
        )

        return result

    # ========================================================
    # DOCUMENT ANCHOR
    # ========================================================

    def _document_anchor(
        self,
        markdown_path: Path,
    ) -> str | None:
        """
        Determine the strongest semantic context from
        the source path and filename.

        Filename match is stronger than directory match.
        """

        filename = self._normalize(
            markdown_path.stem
        )

        path_text = self._normalize(
            " ".join(
                markdown_path.parts
            )
        )

        candidates = []

        for topic, anchors in (
            self.DOCUMENT_ANCHORS.items()
        ):

            score = 0

            for anchor in anchors:

                normalized_anchor = (
                    self._normalize(
                        anchor
                    )
                )

                if not normalized_anchor:
                    continue

                if self._keyword_match(
                    filename,
                    normalized_anchor,
                ):
                    score = max(
                        score,
                        100,
                    )

                elif self._keyword_match(
                    path_text,
                    normalized_anchor,
                ):
                    score = max(
                        score,
                        50,
                    )

            if score:
                candidates.append(
                    (
                        score,
                        topic,
                    )
                )

        if not candidates:
            return None

        candidates.sort(
            key=lambda item: (
                -item[0],
                item[1],
            )
        )

        return candidates[0][1]

    # ========================================================
    # SECTION EXTRACTION
    # ========================================================

    def _extract_sections(
        self,
        markdown: str,
        document_name: str,
    ) -> list[dict]:

        raw_lines = markdown.splitlines()

        content_lines = (
            self._isolate_main_content(
                raw_lines
            )
        )

        cleaned_lines = (
            self._clean_noise_lines(
                content_lines
            )
        )

        sections = []

        current_heading = None
        current_level = None
        current_lines = []
        current_start_line = None

        for item in cleaned_lines:

            line_number = item[
                "line_number"
            ]

            line = item[
                "line"
            ]

            match = re.match(
                r"^(#{1,6})\s+(.+?)\s*$",
                line,
            )

            if match:

                if (
                    current_heading
                    is not None
                ):

                    section = (
                        self._build_section(
                            heading=current_heading,
                            level=current_level,
                            lines=current_lines,
                            start_line=current_start_line,
                            end_line=line_number - 1,
                        )
                    )

                    if section:
                        sections.append(
                            section
                        )

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

                continue

            current_lines.append(
                line
            )

        if (
            current_heading
            is not None
        ):

            section = (
                self._build_section(
                    heading=current_heading,
                    level=current_level,
                    lines=current_lines,
                    start_line=current_start_line,
                    end_line=len(raw_lines),
                )
            )

            if section:
                sections.append(
                    section
                )

        elif current_lines:

            text = "\n".join(
                current_lines
            ).strip()

            if text:

                title = (
                    self._document_title(
                        document_name
                    )
                )

                section = (
                    self._build_section(
                        heading=title,
                        level=1,
                        lines=current_lines,
                        start_line=1,
                        end_line=len(raw_lines),
                    )
                )

                if section:
                    sections.append(
                        section
                    )

        return sections

    # ========================================================
    # MAIN CONTENT ISOLATION
    # ========================================================

    def _isolate_main_content(
        self,
        lines: list[str],
    ) -> list[dict]:

        breadcrumb_end = (
            self._find_breadcrumb_end(
                lines
            )
        )

        if breadcrumb_end is None:
            start_index = 0
        else:
            start_index = (
                breadcrumb_end + 1
            )

        footer_start = (
            self._find_footer_start(
                lines,
                start_index,
            )
        )

        if footer_start is None:
            end_index = len(lines)
        else:
            end_index = footer_start

        result = []

        for index in range(
            start_index,
            end_index,
        ):

            result.append(
                {
                    "line_number": index + 1,
                    "line": lines[index].strip(),
                }
            )

        return result

    # ========================================================
    # BREADCRUMB
    # ========================================================

    def _find_breadcrumb_end(
        self,
        lines: list[str],
    ) -> int | None:

        for index, raw_line in enumerate(
            lines
        ):

            line = raw_line.strip()

            if re.search(
                r"\b1\.\s*\[",
                line,
            ):

                end = index

                for next_index in range(
                    index,
                    min(
                        len(lines),
                        index + 10,
                    ),
                ):

                    if re.search(
                        r"\b\d+\.\s*\[",
                        lines[next_index],
                    ):
                        end = next_index
                    else:
                        if next_index > index:
                            break

                return end

            if (
                " > " in line
                and "home" in line.lower()
                and len(line) < 300
            ):
                return index

        return None

    # ========================================================
    # FOOTER
    # ========================================================

    def _find_footer_start(
        self,
        lines: list[str],
        start_index: int,
    ) -> int | None:

        for index in range(
            start_index,
            len(lines),
        ):

            raw_line = lines[
                index
            ].strip()

            plain_text = re.sub(
                r"\[([^\]]+)\]\([^)]+\)",
                r"\1",
                raw_line,
            )

            normalized = (
                self._normalize(
                    plain_text
                )
            )

            if normalized == "important links":

                if self._looks_like_footer_block(
                    lines,
                    index,
                ):
                    return index

            if re.search(
                r"copyright\s*©?",
                raw_line,
                flags=re.IGNORECASE,
            ):
                return index

        return None

    # ========================================================
    # FOOTER BLOCK
    # ========================================================

    def _looks_like_footer_block(
        self,
        lines: list[str],
        start_index: int,
    ) -> bool:

        window = lines[
            start_index:
            min(
                len(lines),
                start_index + 20,
            )
        ]

        link_like_count = 0

        for raw_line in window:

            line = raw_line.strip()

            if not line:
                continue

            if re.fullmatch(
                r"\[[^\]]+\]\([^)]+\)",
                line,
            ):
                link_like_count += 1
                continue

            if re.fullmatch(
                r"\[[^\]]*\]\([^)]+\)",
                line,
            ):
                link_like_count += 1

        return link_like_count >= 3

    # ========================================================
    # NOISE CLEANUP
    # ========================================================

    def _clean_noise_lines(
        self,
        items: list[dict],
    ) -> list[dict]:

        cleaned = []

        accessibility_mode = False

        for item in items:

            line_number = item[
                "line_number"
            ]

            line = item[
                "line"
            ].strip()

            if not line:

                cleaned.append(
                    item
                )

                continue

            normalized = self._normalize(
                line
            )

            heading_text = re.sub(
                r"^#{1,6}\s+",
                "",
                line,
            ).strip()

            normalized_heading = (
                self._normalize(
                    heading_text
                )
            )

            if (
                normalized_heading.startswith(
                    "accessibility options"
                )
                or "ux4g accessibility"
                in normalized
            ):

                accessibility_mode = True
                continue

            if accessibility_mode:
                continue

            if self._is_noise_line(
                line
            ):
                continue

            if (
                normalized
                in self.LANGUAGE_LINES
            ):
                continue

            if self._is_image_only(
                line
            ):
                continue

            cleaned.append(
                {
                    "line_number": line_number,
                    "line": line,
                }
            )

        return cleaned

    # ========================================================
    # NOISE LINE TEST
    # ========================================================

    def _is_noise_line(
        self,
        line: str,
    ) -> bool:

        stripped = line.strip()

        if not stripped:
            return True

        heading_text = re.sub(
            r"^#{1,6}\s+",
            "",
            stripped,
        ).strip()

        normalized = (
            self._normalize(
                heading_text
            )
        )

        if normalized in (
            self.NOISE_HEADINGS
        ):
            return True

        for pattern in (
            self.NOISE_LINE_PATTERNS
        ):

            if re.search(
                pattern,
                stripped,
                flags=re.IGNORECASE,
            ):
                return True

        return False

    # ========================================================
    # IMAGE ONLY
    # ========================================================

    def _is_image_only(
        self,
        line: str,
    ) -> bool:

        stripped = line.strip()

        if re.fullmatch(
            r"!\[[^\]]*\]\([^)]+\)",
            stripped,
        ):
            return True

        if re.fullmatch(
            r"\[\s*!\[[^\]]*\]\([^)]+\)\s*\]\([^)]+\)",
            stripped,
        ):
            return True

        return False

    # ========================================================
    # SECTION DECISION
    # ========================================================

    def _decide_section(
        self,
        heading: str,
        text: str,
    ) -> str:

        normalized_heading = (
            self._normalize(
                heading
            )
        )

        normalized_text = (
            self._normalize(
                text
            )
        )

        if (
            normalized_heading
            in self.NOISE_HEADINGS
        ):
            return "NOISE"

        if not normalized_text:
            return "NOISE"

        meaningful_lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        if meaningful_lines:

            link_like_count = sum(
                1
                for line in meaningful_lines
                if self._is_navigation_like(
                    line
                )
            )

            ratio = (
                link_like_count
                / len(
                    meaningful_lines
                )
            )

            if (
                len(
                    meaningful_lines
                ) >= 3
                and ratio >= 0.95
            ):
                return "NOISE"

        return "KEEP"

    # ========================================================
    # NAVIGATION-LIKE
    # ========================================================

    def _is_navigation_like(
        self,
        line: str,
    ) -> bool:

        stripped = line.strip()

        if re.fullmatch(
            r"\[[^\]]+\]\([^)]+\)",
            stripped,
        ):
            return True

        if (
            "javascript:void"
            in stripped.lower()
        ):
            return True

        return False

    # ========================================================
    # CLASSIFICATION
    # ========================================================

    def _classify_section(
        self,
        heading: str,
        text: str,
        document_anchor: str | None,
        document_name: str,
        markdown_path: Path,
    ) -> str:
        """
        Classification priority:

        1. Admissions program-context rule.
        2. Strong section heading.
        3. Strong document/page context.
        4. Content fallback.
        5. Other.

        This prevents:

            "MS by Research Programs"
                -> research

        when the source page is clearly:

            admission_to_postgraduate_programs.md
        """

        heading_text = (
            self._normalize(
                heading
            )
        )

        content_text = (
            self._normalize(
                text
            )
        )

        # ----------------------------------------------------
        # 1. PROGRAM HEADINGS ON ADMISSIONS PAGES
        # ----------------------------------------------------

        if (
            document_anchor == "admissions"
            and self._is_generic_program_heading(
                heading_text
            )
        ):
            return "admissions"

        # ----------------------------------------------------
        # 2. STRONG EXPLICIT HEADING
        # ----------------------------------------------------

        heading_topic = (
            self._strong_heading_topic(
                heading_text
            )
        )

        if heading_topic is not None:

            # A generic program heading on an admissions
            # source page always stays under admissions.
            if (
                document_anchor == "admissions"
                and self._is_generic_program_heading(
                    heading_text
                )
            ):
                return "admissions"

            return heading_topic

        # ----------------------------------------------------
        # 3. STRONG DOCUMENT CONTEXT
        # ----------------------------------------------------

        if document_anchor:

            if document_anchor == "admissions":
                return "admissions"

            if document_anchor in {
                "administration",
                "departments",
                "faculty",
                "research",
                "hostel",
                "placements",
                "scholarships",
                "student_services",
                "facilities",
                "college_overview",
                "academics",
                "events",
                "notices",
                "contact",
            }:
                return document_anchor

        # ----------------------------------------------------
        # 4. CONTENT FALLBACK
        # ----------------------------------------------------

        combined = (
            heading_text
            + " "
            + content_text
        )

        scores = {}

        for topic, keywords in (
            self.TOPIC_RULES.items()
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
                scores[
                    topic
                ] = score

        if scores:

            return sorted(
                scores.items(),
                key=lambda item: (
                    -item[1],
                    item[0],
                ),
            )[0][0]

        return "other"

    # ========================================================
    # STRONG HEADING TOPIC
    # ========================================================

    def _strong_heading_topic(
        self,
        heading_text: str,
    ) -> str | None:

        strong_heading_keywords = {

            "admissions": (
                "admission",
                "admissions",
                "eligibility",
                "application process",
                "admission process",
            ),

            "administration": (
                "administration",
                "administrative",
                "registrar",
                "dean of administration",
                "office of administration",
                "office of registrar",
                "office of director",
                "director's office",
            ),

            "departments": (
                "department",
                "departments",
                "school of",
            ),

            "faculty": (
                "faculty",
                "faculty members",
                "faculty positions",
                "professor",
                "professors",
            ),

            "research": (
                "research",
                "research projects",
                "research project",
                "research and development",
                "innovation",
                "publications",
                "laboratory",
                "laboratories",
                "patents",
            ),

            "hostel": (
                "hostel",
                "hostels",
                "residential life",
                "student housing",
                "accommodation",
            ),

            "placements": (
                "placement",
                "placements",
                "career services",
                "career",
                "internships",
                "internship",
            ),

            "scholarships": (
                "scholarship",
                "scholarships",
                "fellowship",
                "financial aid",
            ),

            "student_services": (
                "student services",
                "student service",
                "student welfare",
                "student wellbeing",
                "health center",
                "health centre",
                "counselling",
                "counseling",
                "grievance",
            ),

            "facilities": (
                "facilities",
                "facility",
                "infrastructure",
                "library",
                "transport",
                "sports facilities",
                "computer center",
                "computer centre",
                "digital infrastructure",
            ),

            "college_overview": (
                "about",
                "about us",
                "vision",
                "mission",
                "goals",
                "history",
                "overview",
                "profile",
            ),

            "examinations": (
                "examination",
                "examinations",
                "exam",
                "results",
                "grading",
                "assessment",
            ),

            "events": (
                "events",
                "event",
                "seminar",
                "conference",
                "workshop",
                "lecture",
                "celebration",
            ),

            "notices": (
                "notice",
                "notices",
                "notification",
                "latest news",
                "news",
                "announcements",
            ),

            "contact": (
                "contact",
                "contact us",
                "contact details",
            ),
        }

        # Exact heading first.
        for topic, keywords in (
            strong_heading_keywords.items()
        ):

            for keyword in keywords:

                normalized_keyword = (
                    self._normalize(
                        keyword
                    )
                )

                if (
                    heading_text
                    == normalized_keyword
                ):
                    return topic

        # Phrase containment second.
        for topic, keywords in (
            strong_heading_keywords.items()
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
                    return topic

        return None

    # ========================================================
    # PROGRAM HEADING
    # ========================================================

    def _is_generic_program_heading(
        self,
        heading_text: str,
    ) -> bool:
        """
        Identifies degree/program offering headings.

        Examples:

            Doctor of Philosophy Programs
            Master of Technology Programs
            Master of Science Programs
            MS by Research Programs
            Master of Design
        """

        program_tokens = (
            "program",
            "programs",
            "programme",
            "programmes",
        )

        if any(
            token in heading_text.split()
            for token in program_tokens
        ):
            return True

        degree_patterns = (
            "master of design",
            "master of technology",
            "master of science",
            "master of engineering",
            "doctor of philosophy",
            "ms by research",
            "mtech",
            "m tech",
            "msc",
            "m sc",
            "phd",
        )

        for pattern in degree_patterns:

            if self._keyword_match(
                heading_text,
                self._normalize(pattern),
            ):
                return True

        return False

    # ========================================================
    # SUBTOPIC
    # ========================================================

    def _derive_subtopic(
        self,
        heading: str,
        topic: str,
    ) -> str:

        normalized = (
            self._normalize(
                heading
            )
        )

        if not normalized:
            return topic

        words = normalized.split()

        if len(words) > 8:
            words = words[:8]

        return (
            "_".join(words)
            or topic
        )

    # ========================================================
    # BUILD UNIT
    # ========================================================

    def _build_unit(
        self,
        domain: str,
        source_document: Path,
        document_name: str,
        section_index: int,
        section: dict,
        topic: str,
        subtopic: str,
    ) -> dict:

        return {
            "unit_id": (
                f"{document_name}"
                f"::section_{section_index:04d}"
            ),
            "domain": domain,
            "source_document": str(
                source_document
            ),
            "source_file": (
                source_document.name
            ),
            "source_url": (
                self._extract_source_url(
                    source_document
                )
            ),
            "document": document_name,
            "section_index": section_index,
            "heading": section[
                "heading"
            ],
            "text": section[
                "text"
            ],
            "level": section[
                "level"
            ],
            "decision": section[
                "decision"
            ],
            "topic": topic,
            "subtopic": subtopic,
            "start_line": section[
                "start_line"
            ],
            "end_line": section[
                "end_line"
            ],
        }

    # ========================================================
    # WRITE CLEAN SOURCE
    # ========================================================

    def _write_clean_source(
        self,
        output_file: Path,
        domain: str,
        source_document: Path,
        sections: list[dict],
    ) -> None:

        lines = []

        title = (
            self._document_title(
                source_document.stem
            )
        )

        lines.append(
            f"# {title}"
        )

        lines.append("")

        lines.append(
            f"**Domain:** {domain}"
        )

        lines.append(
            f"**Source Document:** "
            f"{source_document.name}"
        )

        source_url = (
            self._extract_source_url(
                source_document
            )
        )

        if source_url:
            lines.append(
                f"**Source URL:** "
                f"{source_url}"
            )

        lines.append("")

        lines.append("---")

        lines.append("")

        for section in sections:

            if (
                section["decision"]
                == "NOISE"
            ):
                continue

            lines.append(
                f"## {section['heading']}"
            )

            lines.append("")

            lines.append(
                section["text"]
            )

            lines.append("")

            lines.append(
                "<!-- "
                f"Source lines: "
                f"{section['start_line']}-"
                f"{section['end_line']} "
                f"| Decision: "
                f"{section['decision']}"
                " -->"
            )

            lines.append("")

            lines.append("---")

            lines.append("")

        output_file.write_text(
            "\n".join(lines),
            encoding="utf-8",
        )

    # ========================================================
    # DOMAIN MANIFEST
    # ========================================================

    def _update_domain_manifest(
        self,
        domain: str,
        source_document: Path,
        clean_document: Path,
        units: list[dict],
        total_sections: int,
        keep_sections: int,
        review_sections: int,
        noise_sections: int,
    ) -> Path:

        domain_root = (
            self.output_path
            / domain
        )

        manifest_path = (
            domain_root
            / "knowledge_units.json"
        )

        if manifest_path.exists():

            try:
                payload = json.loads(
                    manifest_path.read_text(
                        encoding="utf-8"
                    )
                )
            except (
                json.JSONDecodeError,
                OSError,
            ):
                payload = {}

        else:
            payload = {}

        if not isinstance(
            payload,
            dict,
        ):
            payload = {}

        documents = payload.get(
            "documents",
            {},
        )

        if not isinstance(
            documents,
            dict,
        ):
            documents = {}

        source_key = str(
            source_document
        )

        documents[
            source_key
        ] = {
            "source_document": source_key,
            "clean_document": str(
                clean_document
            ),
            "total_sections": total_sections,
            "keep_sections": keep_sections,
            "review_sections": review_sections,
            "noise_sections": noise_sections,
            "knowledge_units": len(
                units
            ),
        }

        existing_units = payload.get(
            "units",
            [],
        )

        if not isinstance(
            existing_units,
            list,
        ):
            existing_units = []

        existing_units = [
            unit
            for unit in existing_units
            if unit.get(
                "source_document"
            ) != source_key
        ]

        existing_units.extend(
            units
        )

        topic_counts = {}

        for unit in existing_units:

            topic = unit.get(
                "topic",
                "other",
            )

            topic_counts[
                topic
            ] = (
                topic_counts.get(
                    topic,
                    0,
                )
                + 1
            )

        payload = {
            "domain": domain,
            "documents": documents,
            "total_documents": len(
                documents
            ),
            "total_units": len(
                existing_units
            ),
            "topic_counts": topic_counts,
            "units": existing_units,
        }

        manifest_path.write_text(
            json.dumps(
                payload,
                indent=4,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        return manifest_path

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
    ):

        text = "\n".join(
            lines
        ).strip()

        if not text:
            return None

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
    # DOCUMENT TITLE
    # ========================================================

    def _document_title(
        self,
        value: str,
    ) -> str:

        value = (
            value or ""
        ).strip()

        value = re.sub(
            r"[_\-]+",
            " ",
            value,
        )

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return (
            value.strip().title()
            or "Document"
        )

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
                match.group(1).strip()
            )

            cleaned = (
                self._clean_component(
                    domain
                )
            )

            if cleaned:
                return cleaned

        parts = (
            markdown_path.parts
        )

        try:

            index = parts.index(
                "knowledge"
            )

            if (
                index + 1
                < len(parts)
            ):

                return (
                    self._clean_component(
                        parts[
                            index + 1
                        ]
                    )
                )

        except ValueError:
            pass

        return "unknown"

    # ========================================================
    # SOURCE URL
    # ========================================================

    def _extract_source_url(
        self,
        markdown_path: Path,
    ) -> str | None:

        try:

            content = (
                markdown_path.read_text(
                    encoding="utf-8"
                )
            )

        except OSError:

            return None

        match = re.search(
            r"\*\*(?:Source|Source URL):\*\*\s*(\S+)",
            content,
            flags=re.IGNORECASE,
        )

        if match:

            return (
                match.group(1).strip()
            )

        return None

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

        return (
            re.sub(
                r"\s+",
                " ",
                value,
            ).strip()
        )

    # ========================================================
    # KEYWORD MATCH
    # ========================================================

    def _keyword_match(
        self,
        text: str,
        keyword: str,
    ) -> bool:

        if (
            not text
            or not keyword
        ):
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