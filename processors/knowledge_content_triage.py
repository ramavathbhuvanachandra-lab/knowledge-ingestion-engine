from __future__ import annotations

import re


class KnowledgeContentTriage:
    """
    Deterministic RAG-aware content triage.

    Layer 1 — Content quality
        KEEP
        NOISE
        REVIEW

    Layer 2 — Student RAG classification
        A = ESSENTIAL_STUDENT_KNOWLEDGE
        B = STUDENT_RELEVANT_SUPPORTING_KNOWLEDGE
        C = INSTITUTIONAL_REFERENCE
        D = NON_RAG_CONTENT

    Additional RAG status
        KEEP
        EXCLUDE
        REVIEW
        AGGREGATE_ONLY

    Important:
        - Never modifies canonical content.
        - Never deletes structured source data.
        - Only adds classification metadata.
    """

    # ================================================================
    # WEBSITE / EXTRACTION NOISE
    # ================================================================

    NOISE_HEADINGS = (
        "accessibility",
        "accessibility options",
        "main menu",
        "menu",
        "navigation",
        "search here",
        "footer",
        "login",
        "student login",
        "students login",
        "students' login",
        "admin login",
        "please wait",
        "created by",
        "important links",
        "quick links",
    )

    NOISE_PHRASES = (
        "arrow_downward",
        "ux4g",
        "accessibility options",
        "students login",
        "students' login",
        "admin login",
        "login close",
        "javascript",
        "skip to main content",
        "back to top",
    )

    NAVIGATION_LINK_THRESHOLD = 0.70
    MIN_USEFUL_TEXT = 80

    # ================================================================
    # TIER A — ESSENTIAL STUDENT KNOWLEDGE
    # ================================================================

    TIER_A_PATTERNS = (
        # Admissions
        "admission",
        "admissions",
        "admission process",
        "admission procedure",
        "application process",
        "application procedure",
        "eligibility",
        "eligibility criteria",
        "entrance examination",
        "entrance exam",
        "selection process",
        "admission requirements",

        # Programs
        "academic program",
        "academic programs",
        "academic programme",
        "academic programmes",
        "degree program",
        "degree programs",
        "degree programme",
        "degree programmes",
        "undergraduate program",
        "undergraduate programs",
        "postgraduate program",
        "postgraduate programs",
        "doctoral program",
        "doctoral programs",
        "phd program",
        "ph.d program",
        "b.tech",
        "b.e.",
        "m.tech",
        "m.e.",
        "m.sc",
        "msc",
        "mba",
        "ms by research",
        "master of technology",
        "master of science",
        "master of design",
        "doctor of philosophy",

        # Courses / curriculum
        "course information",
        "courses",
        "curriculum",
        "curricula",
        "syllabus",
        "course structure",

        # Academic operations
        "academic calendar",
        "academic rules",
        "academic regulation",
        "academic regulations",
        "examination",
        "examinations",
        "evaluation",
        "exam schedule",
        "registration",
        "registration guidelines",
        "enrollment",
        "enrolment",
        "transcript",
        "transcripts",
        "certificate",
        "certificates",
        "graduation",

        # Finance
        "fees",
        "fee structure",
        "tuition",
        "scholarship",
        "scholarships",
        "fellowship",
        "fellowships",
        "stipend",
        "stipends",
        "financial assistance",

        # Hostel / dining
        "hostel",
        "hostels",
        "accommodation",
        "residence",
        "residential life",
        "mess",
        "dining",
        "cafeteria",
        "food services",

        # Campus / facilities
        "campus facilities",
        "facility",
        "facilities",
        "transport",
        "transportation",
        "directions",
        "location",
        "locations",
        "campus map",
        "map",

        # Health / safety
        "medical services",
        "health centre",
        "health center",
        "healthcare",
        "counselling",
        "counseling",
        "security",
        "emergency",
        "emergency contacts",
        "safety",
        "anti ragging",
        "anti-ragging",
        "grievance",
        "grievance redressal",

        # Student services
        "student services",
        "student support",
        "student welfare",
        "student affairs",
        "student office",

        # Departments
        "department",
        "departments",
        "school",
        "schools",

        # Contacts
        "contact",
        "contact us",
        "contact details",
        "directory",
        "phone",
        "telephone",
        "email",
        "e-mail",
        "address",

        # Administration
        "administration",
        "administrative office",
        "administrative offices",
        "registrar",
        "director",
        "dean",
        "deputy director",
        "governance",
        "office of registrar",
        "office of director",
        "office of administration",

        # Notices
        "notice",
        "notices",
        "notification",
        "notifications",
        "announcement",
        "announcements",
        "circular",
        "latest news",
        "important notice",
    )

    # ================================================================
    # TIER B — STUDENT-RELEVANT SUPPORTING KNOWLEDGE
    # ================================================================

    TIER_B_PATTERNS = (
        # Research
        "research area",
        "research areas",
        "research group",
        "research groups",
        "research centre",
        "research center",
        "research centres",
        "research centers",
        "research laboratory",
        "research laboratories",
        "research facility",
        "research facilities",
        "research theme",
        "research themes",

        # Labs
        "laboratory",
        "laboratories",
        "lab",
        "labs",

        # Careers
        "placement",
        "placements",
        "career",
        "careers",
        "career services",
        "internship",
        "internships",
        "training",
        "recruitment",
        "recruitment process",
        "job opportunities",

        # Student life
        "student club",
        "student clubs",
        "student society",
        "student societies",
        "society",
        "societies",
        "student activities",
        "student activity",
        "student organization",
        "student organizations",
        "student opportunities",

        # Events
        "event",
        "events",
        "seminar",
        "seminars",
        "workshop",
        "workshops",
        "webinar",
        "webinars",
        "lecture",
        "lecture series",
        "conference",
        "conferences",
        "festival",
        "fest",

        # Innovation
        "innovation",
        "innovations",
        "entrepreneurship",
        "startup",
        "start-up",
        "incubation",
        "incubator",
        "technology transfer",

        # Institutional initiatives
        "sustainability",
        "sustainable development",
        "initiative",
        "initiatives",
        "outreach",
        "community engagement",
        "social responsibility",

        # Research outputs
        "publication",
        "publications",
        "journal",
        "journals",
        "patent",
        "patents",
        "research output",
        "research outputs",
    )

    # ================================================================
    # TIER C — INSTITUTIONAL REFERENCE
    # ================================================================

    TIER_C_PATTERNS = (
        "institutional history",
        "college history",
        "institute history",
        "history",
        "about",
        "about us",
        "overview",
        "institute overview",
        "college overview",
        "institute profile",
        "college profile",
        "vision",
        "mission",
        "motto",
        "objectives",
        "goals",
        "accreditation",
        "accredited",

        "annual report",
        "annual reports",
        "institutional report",
        "institutional reports",
        "newsletter",
        "newsletters",
        "archive",
        "archives",
        "archival",
        "historical",

        "completed project",
        "completed projects",
        "old project",
        "old projects",
        "project archive",
        "project archives",

        "old publication",
        "old publications",
    )

    # ================================================================
    # TIER D — NON-RAG CONTENT
    # ================================================================

    TIER_D_PATTERNS = (
        # Student / batch
        "batch profile",
        "batch profiles",
        "student profile",
        "student profiles",
        "student roster",
        "student rosters",
        "student list",
        "student lists",
        "students list",
        "students lists",
        "list of students",
        "student names",
        "current students",
        "student database",

        # Alumni
        "alumni profile",
        "alumni profiles",
        "alumni list",
        "alumni lists",
        "alumni names",
        "individual alumni",
        "alumni directory",
        "alumni global presence",

        # Exchange / mobility
        "inbound students",
        "outbound students",
        "exchange students",
        "international students list",
        "student exchange list",

        # Individual internship data
        "individual internship",
        "individual internships",
        "internship records",
        "student internship data",
        "student internship records",

        # Galleries / media
        "photo gallery",
        "photo galleries",
        "image gallery",
        "image galleries",
        "video gallery",
        "video galleries",
        "media gallery",
        "photo album",
        "photo albums",
        "photographs",

        # Testimonials
        "testimonial",
        "testimonials",
        "student testimonial",
        "student testimonials",
        "alumni testimonial",
        "alumni testimonials",

        # Participant lists
        "participant list",
        "participant lists",
        "participants list",
        "attendee list",
        "attendees",
    )

    # ================================================================
    # AGGREGATE-ONLY
    # ================================================================

    AGGREGATE_PATTERNS = (
        "batch profile",
        "batch statistics",
        "batch data",
        "batch profile statistics",
        "alumni statistics",
        "student statistics",
        "student demographics",
        "demographics",
        "institutional statistics",
        "statistics",
        "statistical profile",
        "profile statistics",
    )

    # ================================================================
    # INDIVIDUAL RECORD SIGNALS
    # ================================================================

    INDIVIDUAL_RECORD_PATTERNS = (
        r"\bname\s*:",
        r"\bname\s*\|",
        r"\broll\s*number\b",
        r"\broll\s*no\b",
        r"\bregistration\s*number\b",
        r"\bstudent\s*id\b",
        r"\bserial\s*number\b",
        r"\bs\.?\s*no\.?\b",
        r"\byear\s*of\s*graduation\b",
        r"\byear\s*of\s*admission\b",
        r"\bwork\s*experience\b",
        r"\binterests?\s*:",
        r"\beducation\s*:",
        r"\bdegree\s*:",
        r"\bemployer\s*:",
        r"\bcompany\s*:",
        r"\bfellowship\s*:",
        r"\bsupervisor\s*:",
    )

    # ================================================================
    # FACULTY / PROFESSOR
    # ================================================================

    FACULTY_PATTERNS = (
        "faculty",
        "faculty members",
        "faculty profile",
        "faculty profiles",
        "professor",
        "professors",
        "teaching staff",
        "academic staff",
        "faculty directory",
    )

    # ================================================================
    # PUBLIC API
    # ================================================================

    def classify(
        self,
        section: dict,
    ) -> dict:

        heading = str(
            section.get("heading") or ""
        ).strip()

        text = str(
            section.get("text") or ""
        ).strip()

        lower_heading = heading.lower()
        lower_text = text.lower()

        # ------------------------------------------------------------
        # EMPTY
        # ------------------------------------------------------------

        if not text:

            return self._result(
                section,
                "NOISE",
                ["empty section"],
                "D",
                "EXCLUDE",
                "empty_content",
            )

        # ------------------------------------------------------------
        # KNOWN WEBSITE NOISE
        # ------------------------------------------------------------

        if self._matches_noise_heading(
            lower_heading
        ):

            return self._result(
                section,
                "NOISE",
                ["known UI/navigation heading"],
                "D",
                "EXCLUDE",
                "website_ui_or_navigation",
            )

        for phrase in self.NOISE_PHRASES:

            if self._contains_phrase(
                lower_text,
                phrase,
            ):

                return self._result(
                    section,
                    "NOISE",
                    [
                        f"contains UI/noise marker: {phrase}"
                    ],
                    "D",
                    "EXCLUDE",
                    "website_ui_or_navigation",
                )

        # ------------------------------------------------------------
        # EXTRACTION FAILURE
        # ------------------------------------------------------------

        normalized = re.sub(
            r"[\s\[\]\(\)_\-:.,]+",
            "",
            text,
        )

        if not normalized:

            return self._result(
                section,
                "NOISE",
                ["no meaningful extracted text"],
                "D",
                "EXCLUDE",
                "no_meaningful_text",
            )

        # ------------------------------------------------------------
        # NAVIGATION-HEAVY CONTENT
        # ------------------------------------------------------------

        words = re.findall(
            r"\b[\w'-]+\b",
            text,
        )

        links = re.findall(
            r"\[[^\]]*\]\([^)]+\)",
            text,
        )

        if words:

            link_ratio = (
                len(links)
                / len(words)
            )

            if (
                link_ratio
                >= self.NAVIGATION_LINK_THRESHOLD
            ):

                return self._result(
                    section,
                    "NOISE",
                    [
                        "navigation-heavy content",
                        f"link ratio: {link_ratio:.2f}",
                    ],
                    "D",
                    "EXCLUDE",
                    "navigation_heavy_content",
                )

        # ------------------------------------------------------------
        # TIER D — NON-RAG
        # ------------------------------------------------------------

        d_reason = self._detect_tier_d(
            lower_heading,
            lower_text,
        )

        if d_reason:

            return self._result(
                section,
                "KEEP",
                [d_reason],
                "D",
                "EXCLUDE",
                d_reason,
            )

        # ------------------------------------------------------------
        # AGGREGATE-ONLY
        # ------------------------------------------------------------

        aggregate_reason = (
            self._detect_aggregate_only(
                lower_heading,
                lower_text,
            )
        )

        if aggregate_reason:

            return self._result(
                section,
                "KEEP",
                [aggregate_reason],
                None,
                "AGGREGATE_ONLY",
                aggregate_reason,
            )

        # ------------------------------------------------------------
        # FACULTY / PROFESSOR
        # ------------------------------------------------------------

        if self._contains_any_phrase(
            lower_heading,
            self.FACULTY_PATTERNS,
        ):

            return self._result(
                section,
                "KEEP",
                ["faculty/professor information"],
                "A",
                "KEEP",
                "faculty_or_professor_information",
            )

        # Secondary faculty signal from text.
        if self._contains_any_phrase(
            lower_text[:1500],
            self.FACULTY_PATTERNS,
        ):

            return self._result(
                section,
                "KEEP",
                ["faculty/professor information"],
                "A",
                "KEEP",
                "faculty_or_professor_information",
            )

        # ------------------------------------------------------------
        # HEADING-BASED CLASSIFICATION
        #
        # Strongest automatic signal.
        # ------------------------------------------------------------

        matched_a_heading = (
            self._matched_phrase(
                lower_heading,
                self.TIER_A_PATTERNS,
            )
        )

        if matched_a_heading:

            return self._result(
                section,
                "KEEP",
                [
                    (
                        "essential student knowledge: "
                        f"{matched_a_heading}"
                    )
                ],
                "A",
                "KEEP",
                "essential_student_knowledge",
            )

        matched_b_heading = (
            self._matched_phrase(
                lower_heading,
                self.TIER_B_PATTERNS,
            )
        )

        if matched_b_heading:

            return self._result(
                section,
                "KEEP",
                [
                    (
                        "student-relevant supporting "
                        f"knowledge: {matched_b_heading}"
                    )
                ],
                "B",
                "KEEP",
                "student_relevant_supporting_knowledge",
            )

        matched_c_heading = (
            self._matched_phrase(
                lower_heading,
                self.TIER_C_PATTERNS,
            )
        )

        if matched_c_heading:

            return self._result(
                section,
                "KEEP",
                [
                    (
                        "institutional reference knowledge: "
                        f"{matched_c_heading}"
                    )
                ],
                "C",
                "KEEP",
                "institutional_reference",
            )

        # ------------------------------------------------------------
        # CONSERVATIVE TEXT-BASED CLASSIFICATION
        #
        # IMPORTANT:
        # Generic words such as "initiative", "event", "career",
        # "program", or "research" are NOT enough on their own.
        #
        # Only strong multi-word phrases are accepted here.
        # ------------------------------------------------------------

        strong_b_text_patterns = (
            "research area",
            "research areas",
            "research group",
            "research groups",
            "research centre",
            "research center",
            "research centres",
            "research centers",
            "research laboratory",
            "research laboratories",
            "research facility",
            "research facilities",
            "placement process",
            "placement statistics",
            "career services",
            "internship program",
            "internship programme",
            "student clubs",
            "student societies",
            "entrepreneurship program",
            "entrepreneurship programme",
            "technology transfer",
        )

        matched_b_text = self._matched_phrase(
            lower_text[:2500],
            strong_b_text_patterns,
        )

        if matched_b_text:

            return self._result(
                section,
                "KEEP",
                [
                    (
                        "student-relevant supporting "
                        f"knowledge: {matched_b_text}"
                    )
                ],
                "B",
                "KEEP",
                "student_relevant_supporting_knowledge",
            )

        strong_a_text_patterns = (
            "admission process",
            "admission procedure",
            "eligibility criteria",
            "application process",
            "application procedure",
            "academic calendar",
            "examination schedule",
            "exam schedule",
            "registration guidelines",
            "registration process",
            "fee structure",
            "hostel rules",
            "hostel facilities",
            "mess timings",
            "emergency contacts",
            "health services",
            "medical services",
            "student services",
            "student welfare",
            "contact details",
        )

        matched_a_text = self._matched_phrase(
            lower_text[:2500],
            strong_a_text_patterns,
        )

        if matched_a_text:

            return self._result(
                section,
                "KEEP",
                [
                    (
                        "essential student knowledge: "
                        f"{matched_a_text}"
                    )
                ],
                "A",
                "KEEP",
                "essential_student_knowledge",
            )

        strong_c_text_patterns = (
            "institutional history",
            "college history",
            "institute history",
            "annual report",
            "institutional report",
            "institutional profile",
            "institutional overview",
        )

        matched_c_text = self._matched_phrase(
            lower_text[:2500],
            strong_c_text_patterns,
        )

        if matched_c_text:

            return self._result(
                section,
                "KEEP",
                [
                    (
                        "institutional reference knowledge: "
                        f"{matched_c_text}"
                    )
                ],
                "C",
                "KEEP",
                "institutional_reference",
            )

        # ------------------------------------------------------------
        # SHORT CONTENT
        # ------------------------------------------------------------

        if len(text) < self.MIN_USEFUL_TEXT:

            return self._result(
                section,
                "REVIEW",
                [
                    (
                        "very short content "
                        f"({len(text)} characters)"
                    )
                ],
                None,
                "REVIEW",
                "short_or_ambiguous_content",
            )

        # ------------------------------------------------------------
        # TABLE OF CONTENTS
        # ------------------------------------------------------------

        toc_markers = (
            "table of contents",
            "contents",
        )

        if any(
            self._contains_phrase(
                lower_text,
                marker,
            )
            for marker in toc_markers
        ):

            return self._result(
                section,
                "REVIEW",
                ["possible table of contents/index"],
                None,
                "REVIEW",
                "possible_index_or_toc",
            )

        # ------------------------------------------------------------
        # UNKNOWN SUBSTANTIVE CONTENT
        #
        # SAFETY RULE:
        # Unknown ≠ useful.
        # Unknown ≠ trash.
        #
        # It goes to REVIEW.
        # ------------------------------------------------------------

        return self._result(
            section,
            "REVIEW",
            [
                (
                    "substantive content with no "
                    "confident RAG classification"
                )
            ],
            None,
            "REVIEW",
            "unclassified_substantive_content",
        )

    # ================================================================
    # CLASSIFY ALL
    # ================================================================

    def classify_all(
        self,
        sections: list[dict],
    ) -> list[dict]:

        return [
            self.classify(section)
            for section in sections
        ]

    # ================================================================
    # TIER D DETECTION
    # ================================================================

    def _detect_tier_d(
        self,
        heading: str,
        text: str,
    ) -> str | None:

        matched = self._matched_phrase(
            heading,
            self.TIER_D_PATTERNS,
        )

        if matched:

            return (
                "non-RAG individual/archive content: "
                f"{matched}"
            )

        # Alumni with individual-record structure.
        if self._contains_phrase(
            heading,
            "alumni",
        ):

            record_hits = (
                self._count_record_signals(
                    text
                )
            )

            if record_hits >= 2:

                return (
                    "non-RAG individual alumni records"
                )

        # Generic individual records.
        record_hits = (
            self._count_record_signals(
                text
            )
        )

        if record_hits >= 3:

            return (
                "non-RAG individual records "
                f"({record_hits} record-field signals)"
            )

        return None

    # ================================================================
    # AGGREGATE-ONLY DETECTION
    # ================================================================

    def _detect_aggregate_only(
        self,
        heading: str,
        text: str,
    ) -> str | None:

        matched = self._matched_phrase(
            heading,
            self.AGGREGATE_PATTERNS,
        )

        if not matched:
            return None

        record_hits = (
            self._count_record_signals(
                text
            )
        )

        if record_hits >= 2:

            return (
                "institutional aggregate mixed "
                f"with individual records: {matched}"
            )

        return None

    # ================================================================
    # RECORD SIGNAL COUNT
    # ================================================================

    def _count_record_signals(
        self,
        text: str,
    ) -> int:

        hits = 0

        for pattern in (
            self.INDIVIDUAL_RECORD_PATTERNS
        ):

            if re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            ):
                hits += 1

        return hits

    # ================================================================
    # NOISE HEADING MATCH
    # ================================================================

    def _matches_noise_heading(
        self,
        heading: str,
    ) -> bool:

        for pattern in self.NOISE_HEADINGS:

            if heading == pattern:
                return True

            if heading.startswith(
                pattern + " "
            ):
                return True

        return False

    # ================================================================
    # PHRASE MATCHING
    # ================================================================

    def _contains_phrase(
        self,
        text: str,
        phrase: str,
    ) -> bool:

        escaped = re.escape(
            phrase.lower()
        )

        pattern = (
            rf"(?<![a-z0-9])"
            rf"{escaped}"
            rf"(?![a-z0-9])"
        )

        return re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        ) is not None

    def _contains_any_phrase(
        self,
        text: str,
        phrases: tuple[str, ...],
    ) -> bool:

        return any(
            self._contains_phrase(
                text,
                phrase,
            )
            for phrase in phrases
        )

    def _matched_phrase(
        self,
        text: str,
        phrases: tuple[str, ...],
    ) -> str | None:

        ordered = sorted(
            phrases,
            key=len,
            reverse=True,
        )

        for phrase in ordered:

            if self._contains_phrase(
                text,
                phrase,
            ):

                return phrase

        return None

    # ================================================================
    # RESULT
    # ================================================================

    def _result(
        self,
        section: dict,
        decision: str,
        reasons: list[str],
        rag_tier: str | None,
        rag_status: str,
        rag_reason: str,
    ) -> dict:

        result = dict(
            section
        )

        result["triage"] = {
            "decision": decision,
            "reasons": reasons,
        }

        result["rag"] = {
            "tier": rag_tier,
            "status": rag_status,
            "reason": rag_reason,
        }

        return result


if __name__ == "__main__":

    print(
        "KnowledgeContentTriage"
    )

    print(
        "RAG tiers A/B/C/D enabled"
    )
