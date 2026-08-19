"""
Command 3 — Knowledge Value Filter.

Purpose
-------
Determine whether an extracted knowledge unit belongs in the stable
institutional knowledge base.

Possible decisions:

    KEEP
    CONSOLIDATE
    EXCLUDE
    REVIEW

Core design
-----------
The filter evaluates two independent dimensions:

    1. INFORMATION VALUE
    2. TEMPORAL STABILITY

The final RAG corpus is intended to contain stable institutional
knowledge that remains useful for months or years.

Therefore:

    Stable + valuable
        -> KEEP

    Stable + record-heavy
        -> CONSOLIDATE / EXCLUDE

    Volatile/current content
        -> EXCLUDE

    Uncertain substantive content
        -> REVIEW

Important invariants
--------------------
1. This module is college-agnostic.
2. Institutional knowledge is protected.
3. Vision, mission, history, departments, faculty, programs,
   courses, curriculum, research areas, research centres,
   facilities, hostels, admissions, etc. are valuable.
4. News/latest-news/highlights/current research news are volatile
   and are excluded from the final stable RAG corpus.
5. Faculty information itself is stable and should remain.
6. Research areas themselves are stable and should remain.
7. Research news/highlights are volatile and should be excluded.
8. Individual student/batch/alumni records are excluded.
9. Individual student research-project records are excluded or
   consolidated depending on evidence.
10. Unknown substantive information is never silently deleted.
11. This module does not create folders.
12. This module does not perform final deduplication.
13. The original structured data remains available for audit/rebuild.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any


# ======================================================================
# DECISION TYPES
# ======================================================================

KEEP = "KEEP"
CONSOLIDATE = "CONSOLIDATE"
EXCLUDE = "EXCLUDE"
REVIEW = "REVIEW"


# ======================================================================
# DATA MODEL
# ======================================================================


@dataclass
class ValueDecision:
    """
    Explainable classification result.

    score is an internal deterministic score.
    It is NOT a probability.
    """

    decision: str
    confidence: str
    score: int
    reasons: list[str]
    signals: dict[str, Any]


# ======================================================================
# FILTER
# ======================================================================


class KnowledgeValueFilter:
    """
    Deterministic filter for stable institutional knowledge.

    The filter deliberately separates:

        information value
        temporal stability

    This prevents important institutional information from being
    confused with short-lived news/current updates.
    """

    # ==================================================================
    # STABLE INSTITUTIONAL KNOWLEDGE
    # ==================================================================

    INSTITUTIONAL_SIGNALS = (
        "vision",
        "mission",
        "vision and mission",
        "message from head",
        "message from the head",
        "message from director",
        "message from the director",
        "message from dean",
        "message from the dean",
        "from the head",
        "from head",
        "about",
        "overview",
        "history",
        "objectives",
        "goals",
        "leadership",
        "administration",
        "key functionaries",
        "department",
        "departments",
        "school",
        "schools",
        "faculty",
        "faculties",
        "faculty members",
        "program",
        "programs",
        "programme",
        "programmes",
        "degree",
        "degrees",
        "course",
        "courses",
        "curriculum",
        "academic",
        "academics",
        "admission",
        "admissions",
        "eligibility",
        "research area",
        "research areas",
        "research centre",
        "research center",
        "research centres",
        "research centers",
        "research group",
        "research groups",
        "research facility",
        "research facilities",
        "research theme",
        "research themes",
        "research focus",
        "research interests",
        "research program",
        "research programme",
        "research infrastructure",
        "research laboratory",
        "research laboratories",
        "laboratory",
        "laboratories",
        "lab",
        "labs",
        "facility",
        "facilities",
        "infrastructure",
        "hostel",
        "hostels",
        "accommodation",
        "student life",
        "student affairs",
        "fees",
        "fee structure",
        "scholarship",
        "scholarships",
        "placement",
        "placements",
        "career",
        "careers",
        "rules",
        "regulation",
        "regulations",
        "policy",
        "policies",
        "guidelines",
        "code of conduct",
        "contact",
        "contacts",
        "accreditation",
        "collaboration",
        "collaborations",
        "international",
        "innovation",
        "incubation",
        "campus",
    )

    # ==================================================================
    # VOLATILE / TIME-SENSITIVE CONTENT
    #
    # These are intentionally excluded from the stable final RAG.
    # ==================================================================

    VOLATILE_SIGNALS = (
        "latest news",
        "latest news and events",
        "latest updates",
        "recent news",
        "recent update",
        "recent updates",
        "news",
        "news article",
        "news articles",
        "press release",
        "press releases",
        "breaking news",
        "current news",
        "in the news",
        "highlights",
        "latest highlights",
        "recent highlights",
        "research highlights",
        "research news",
        "latest research",
        "latest research news",
        "recent research",
        "recent research news",
        "recent publication",
        "recent publications",
        "latest publication",
        "latest publications",
        "award",
        "awards",
        "recent award",
        "recent awards",
        "faculty award",
        "faculty awards",
        "student award",
        "student awards",
        "achievement",
        "achievements",
        "recent achievement",
        "recent achievements",
        "latest achievement",
        "latest achievements",
        "event",
        "events",
        "upcoming event",
        "upcoming events",
        "past event",
        "past events",
        "announcement",
        "announcements",
        "latest announcement",
        "latest announcements",
        "recent announcement",
        "recent announcements",
        "notice",
        "notices",
        "latest notice",
        "latest notices",
        "recent notice",
        "recent notices",
        "what's new",
        "whats new",
        "new and noteworthy",
        "inauguration",
        "celebration",
        "commemoration",
        "congratulations",
    )

    # ==================================================================
    # PERSONAL / BULK RECORD SIGNALS
    # ==================================================================

    PERSONAL_RECORD_SIGNALS = (
        "student name",
        "student names",
        "student list",
        "students list",
        "student directory",
        "student profile",
        "student profiles",
        "batch profile",
        "batch profiles",
        "batch list",
        "batch lists",
        "alumni directory",
        "alumni directories",
        "alumni list",
        "alumni lists",
        "alumni profile",
        "alumni profiles",
        "individual alumni",
        "individual student",
        "individual students",
        "scholar list",
        "scholar lists",
        "phd scholars",
        "phd scholar list",
        "research scholar list",
        "research scholars",
        "participant list",
        "participant lists",
    )

    PERSON_FIELDS = (
        "name",
        "student",
        "student name",
        "batch",
        "roll number",
        "roll no",
        "registration number",
        "registration no",
        "email",
        "phone",
        "mobile",
        "contact number",
        "linkedin",
        "alumni",
        "year of graduation",
        "graduation year",
        "place",
        "location",
        "current location",
        "company",
        "employer",
        "designation",
        "supervisor",
        "guide",
    )

    BATCH_SIGNALS = (
        "batch",
        "batch profile",
        "batch 20",
        "batch 19",
        "batch 18",
        "batch 17",
        "class of",
        "graduating class",
        "student directory",
        "student profile",
        "students",
    )

    ALUMNI_SIGNALS = (
        "alumni",
        "alumnus",
        "alumna",
        "alumni directory",
        "alumni profile",
        "alumni profiles",
        "alumni association",
        "alumni network",
    )

    # ==================================================================
    # PROJECT / PARTICIPANT SIGNALS
    # ==================================================================

    PROJECT_SIGNALS = (
        "research project",
        "research projects",
        "project title",
        "project details",
        "project investigator",
        "principal investigator",
        "student project",
        "student projects",
        "project student",
    )

    # ==================================================================
    # UI / SCRAPING JUNK
    # ==================================================================

    UI_CONTENT = (
        "no extractable text",
        "skip to main content",
        "skip to content",
        "enable accessibility",
        "disable accessibility",
        "increase text size",
        "decrease text size",
        "print this page",
        "share this page",
        "cookie settings",
        "accept cookies",
        "reject cookies",
    )

    UI_HEADINGS = (
        "rate this translation",
        "accessibility options",
        "site navigation",
        "main navigation",
        "breadcrumb",
    )

    # ==================================================================
    # REGEX
    # ==================================================================

    YEAR_RE = re.compile(
        r"\b(?:19|20)\d{2}\b"
    )

    EMAIL_RE = re.compile(
        r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        re.IGNORECASE,
    )

    PHONE_RE = re.compile(
        r"(?:\+?\d[\d\s().-]{8,}\d)"
    )

    ROLL_NUMBER_RE = re.compile(
        r"\b[A-Z]{1,8}\d{2,}[A-Z0-9-]*\b",
        re.IGNORECASE,
    )

    # ==================================================================
    # PUBLIC API
    # ==================================================================

    def classify(
        self,
        *,
        heading: str = "",
        text: str = "",
        source_name: str = "",
        document_title: str = "",
        document_url: str = "",
        content_type: str = "",
        section_path: list[str] | None = None,
        record_index: int | None = None,
        record_count: int | None = None,
    ) -> dict[str, Any]:
        """
        Classify one knowledge unit.
        """

        heading = self._clean(heading)
        text = self._clean(text)
        source_name = self._clean(source_name)
        document_title = self._clean(document_title)
        document_url = self._clean(document_url)
        content_type = self._clean(content_type)

        section_path = section_path or []

        combined = self._normalize(
            " ".join(
                [
                    heading,
                    text,
                    source_name,
                    document_title,
                    document_url,
                    " ".join(section_path),
                ]
            )
        )

        heading_n = self._normalize(heading)
        text_n = self._normalize(text)
        title_n = self._normalize(document_title)

        signals: dict[str, Any] = {}

        # ==============================================================
        # 1. OBVIOUS WEB/UI JUNK
        # ==============================================================

        ui_reason = self._check_ui_noise(
            heading_n=heading_n,
            text_n=text_n,
            content_type=content_type,
        )

        if ui_reason:
            return self._result(
                decision=EXCLUDE,
                confidence="high",
                score=-250,
                reasons=[ui_reason],
                signals={
                    "ui_noise": True,
                },
            )

        # ==============================================================
        # 2. FIND STABLE INSTITUTIONAL SIGNALS
        # ==============================================================

        institutional_hits = self._find_signals(
            combined,
            self.INSTITUTIONAL_SIGNALS,
        )

        signals[
            "institutional_hits"
        ] = institutional_hits

        # ==============================================================
        # 3. FIND VOLATILE SIGNALS
        # ==============================================================

        volatile_hits = self._find_signals(
            combined,
            self.VOLATILE_SIGNALS,
        )

        signals[
            "volatile_hits"
        ] = volatile_hits

        # ==============================================================
        # 4. PERSONAL/BULK RECORD SIGNALS
        # ==============================================================

        personal_hits = self._find_signals(
            combined,
            self.PERSONAL_RECORD_SIGNALS,
        )

        person_field_hits = self._find_signals(
            combined,
            self.PERSON_FIELDS,
        )

        batch_hits = self._find_signals(
            combined,
            self.BATCH_SIGNALS,
        )

        alumni_hits = self._find_signals(
            combined,
            self.ALUMNI_SIGNALS,
        )

        signals[
            "personal_record_hits"
        ] = personal_hits

        signals[
            "person_field_hits"
        ] = person_field_hits

        signals[
            "batch_hits"
        ] = batch_hits

        signals[
            "alumni_hits"
        ] = alumni_hits

        # ==============================================================
        # 5. PROJECT SIGNALS
        # ==============================================================

        project_hits = self._find_signals(
            combined,
            self.PROJECT_SIGNALS,
        )

        signals[
            "project_hits"
        ] = project_hits

        # ==============================================================
        # 6. RECORD DENSITY
        # ==============================================================

        record_density = self._record_density(
            text=text,
            person_field_hits=len(
                person_field_hits
            ),
        )

        signals[
            "record_density"
        ] = record_density

        # ==============================================================
        # 7. VOLATILITY DECISION
        #
        # Volatile content is excluded from the stable RAG corpus.
        #
        # However, stable institutional information wins over weak
        # volatile keyword matches.
        # ==============================================================

        strong_stable_signal = (
            len(institutional_hits) >= 1
        )

        strong_volatile_signal = (
            len(volatile_hits) >= 1
        )

        # --------------------------------------------------------------
        # Explicit volatile heading is stronger than a generic
        # institutional word appearing somewhere inside the text.
        #
        # Example:
        #
        # Heading: "Latest Research News"
        # Text: "Department of Electrical Engineering..."
        #
        # This is still volatile.
        # --------------------------------------------------------------

        volatile_heading = (
            self._contains_any_phrase(
                heading_n,
                self.VOLATILE_SIGNALS,
            )
        )

        signals[
            "volatile_heading"
        ] = volatile_heading

        if (
            strong_volatile_signal
            and volatile_heading
        ):
            return self._result(
                decision=EXCLUDE,
                confidence="high",
                score=-220,
                reasons=[
                    "Content is explicitly identified as "
                    "news, latest updates, highlights, "
                    "recent research, awards, events, or "
                    "other time-sensitive material."
                ],
                signals=signals,
            )

        # ==============================================================
        # 8. BATCH / ALUMNI RECORD EXCLUSION
        # ==============================================================

        bulk_person_score = 0

        bulk_person_score += (
            len(personal_hits)
            * 45
        )

        if len(person_field_hits) >= 3:
            bulk_person_score += 60

        if len(person_field_hits) >= 5:
            bulk_person_score += 50

        if batch_hits:
            bulk_person_score += (
                len(batch_hits)
                * 35
            )

        if alumni_hits:
            bulk_person_score += (
                len(alumni_hits)
                * 45
            )

        bulk_person_score += record_density

        signals[
            "bulk_person_score"
        ] = bulk_person_score

        if (
            not strong_stable_signal
            and len(personal_hits) >= 1
            and (
                len(person_field_hits) >= 3
                or batch_hits
                or alumni_hits
            )
        ):
            return self._result(
                decision=EXCLUDE,
                confidence="high",
                score=-bulk_person_score,
                reasons=[
                    "Strong evidence of bulk personal, "
                    "batch, alumni, or student records."
                ],
                signals=signals,
            )

        # ==============================================================
        # 9. INDIVIDUAL STUDENT RESEARCH PROJECTS
        # ==============================================================

        if project_hits:

            project_record_score = 0

            if "student" in combined:
                project_record_score += 35

            if "batch" in combined:
                project_record_score += 30

            if (
                "supervisor" in combined
                or "guide" in combined
            ):
                project_record_score += 30

            if "principal investigator" in combined:
                project_record_score += 20

            if "project title" in combined:
                project_record_score += 20

            signals[
                "project_record_score"
            ] = project_record_score

            # Student-specific research record.
            if (
                project_record_score >= 60
                and not self._contains_research_structure(
                    combined
                )
            ):
                return self._result(
                    decision=EXCLUDE,
                    confidence="high",
                    score=-project_record_score,
                    reasons=[
                        "Content is dominated by an individual "
                        "student/project record rather than "
                        "stable institutional research knowledge."
                    ],
                    signals=signals,
                )

        # ==============================================================
        # 10. VOLATILE CONTENT WITHOUT EXPLICIT VOLATILE HEADING
        # ==============================================================

        if strong_volatile_signal:

            # If the content is clearly a stable institutional
            # definition/description and "award", "event", etc.
            # only appears as incidental text, don't automatically
            # throw it away.
            #
            # But if the document is clearly news/update material,
            # exclude it.

            if self._looks_like_current_update(
                heading=heading_n,
                title=title_n,
                text=text_n,
                volatile_hits=volatile_hits,
            ):
                return self._result(
                    decision=EXCLUDE,
                    confidence="high",
                    score=-180,
                    reasons=[
                        "Content appears to be time-sensitive "
                        "institutional news/update material."
                    ],
                    signals=signals,
                )

        # ==============================================================
        # 11. STABLE INSTITUTIONAL CONTENT
        # ==============================================================

        if strong_stable_signal:

            score = (
                len(institutional_hits)
                * 30
            )

            return self._result(
                decision=KEEP,
                confidence="high",
                score=score,
                reasons=[
                    "Contains stable institutional knowledge "
                    "that can remain useful over time."
                ],
                signals=signals,
            )

        # ==============================================================
        # 12. PERSON-RECORD DENSITY
        # ==============================================================

        year_count = len(
            self.YEAR_RE.findall(
                text
            )
        )

        if (
            len(person_field_hits) >= 5
            and year_count >= 1
        ):
            return self._result(
                decision=EXCLUDE,
                confidence="high",
                score=-120,
                reasons=[
                    "High density of individual-person record "
                    "fields detected."
                ],
                signals=signals,
            )

        # ==============================================================
        # 13. EMPTY / VERY SHORT CONTENT
        # ==============================================================

        word_count = len(
            self._tokens(text)
        )

        signals[
            "word_count"
        ] = word_count

        if word_count == 0:
            return self._result(
                decision=REVIEW,
                confidence="medium",
                score=0,
                reasons=[
                    "No substantive text was available "
                    "for classification."
                ],
                signals=signals,
            )

        if word_count < 12:
            return self._result(
                decision=REVIEW,
                confidence="low",
                score=0,
                reasons=[
                    "Content is very short and lacks enough "
                    "evidence for automatic classification."
                ],
                signals=signals,
            )

        # ==============================================================
        # 14. GENERIC SUBSTANTIVE CONTENT
        # ==============================================================

        if self._looks_like_substantive_content(
            text
        ):
            return self._result(
                decision=KEEP,
                confidence="medium",
                score=20,
                reasons=[
                    "Content appears substantive and there is "
                    "no strong evidence that it is junk or volatile."
                ],
                signals=signals,
            )

        # ==============================================================
        # 15. UNKNOWN
        # ==============================================================

        return self._result(
            decision=REVIEW,
            confidence="low",
            score=0,
            reasons=[
                "Insufficient evidence for automatic exclusion."
            ],
            signals=signals,
        )

    # ==================================================================
    # VOLATILITY HELPERS
    # ==================================================================

    def _looks_like_current_update(
        self,
        *,
        heading: str,
        title: str,
        text: str,
        volatile_hits: list[str],
    ) -> bool:
        """
        Determine whether volatile signals represent the actual
        purpose of the content rather than an incidental mention.
        """

        if self._contains_any_phrase(
            heading,
            self.VOLATILE_SIGNALS,
        ):
            return True

        if self._contains_any_phrase(
            title,
            (
                "news",
                "latest",
                "recent",
                "highlights",
                "events",
                "announcement",
                "notice",
                "press release",
            ),
        ):
            return True

        if len(volatile_hits) >= 2:
            return True

        temporal_words = (
            "recently",
            "recent",
            "latest",
            "this month",
            "this year",
            "today",
            "yesterday",
            "upcoming",
            "currently",
            "newly",
            "just",
        )

        if self._contains_any_phrase(
            text,
            temporal_words,
        ):
            return True

        return False

    def _contains_research_structure(
        self,
        text: str,
    ) -> bool:
        """
        Stable research concepts protect research information.

        This is intentionally broad enough to preserve genuine
        research-area/research-centre information.
        """

        research_signals = (
            "research area",
            "research areas",
            "research centre",
            "research center",
            "research group",
            "research groups",
            "research theme",
            "research themes",
            "research focus",
            "research interests",
            "research facility",
            "research facilities",
            "research infrastructure",
            "research laboratory",
            "research laboratories",
        )

        return self._contains_any_phrase(
            text,
            research_signals,
        )

    # ==================================================================
    # UI
    # ==================================================================

    def _check_ui_noise(
        self,
        *,
        heading_n: str,
        text_n: str,
        content_type: str,
    ) -> str | None:

        content_type_n = self._normalize(
            content_type
        )

        if content_type_n in {
            "navigation",
            "accessibility",
        }:
            return (
                "Structured content type is navigation/accessibility."
            )

        if heading_n in {
            self._normalize(value)
            for value in self.UI_HEADINGS
        }:
            return (
                "Heading matches obvious web-interface content."
            )

        for phrase in self.UI_CONTENT:

            phrase_n = self._normalize(
                phrase
            )

            if (
                text_n == phrase_n
                or (
                    phrase_n in text_n
                    and len(text_n)
                    <= len(phrase_n) + 30
                )
            ):
                return (
                    "Content matches obvious web-interface content."
                )

        return None

    # ==================================================================
    # SIGNAL HELPERS
    # ==================================================================

    @staticmethod
    def _find_signals(
        text: str,
        signals: tuple[str, ...],
    ) -> list[str]:

        found = []

        for signal in signals:

            signal_n = (
                KnowledgeValueFilter._normalize(
                    signal
                )
            )

            if not signal_n:
                continue

            pattern = (
                r"(?<!\w)"
                + re.escape(signal_n)
                + r"(?!\w)"
            )

            if re.search(
                pattern,
                text,
            ):
                found.append(
                    signal
                )

        return found

    @staticmethod
    def _contains_any_phrase(
        text: str,
        phrases: tuple[str, ...],
    ) -> bool:

        for phrase in phrases:

            phrase_n = (
                KnowledgeValueFilter._normalize(
                    phrase
                )
            )

            if not phrase_n:
                continue

            pattern = (
                r"(?<!\w)"
                + re.escape(phrase_n)
                + r"(?!\w)"
            )

            if re.search(
                pattern,
                text,
            ):
                return True

        return False

    # ==================================================================
    # RECORD DENSITY
    # ==================================================================

    def _record_density(
        self,
        *,
        text: str,
        person_field_hits: int,
    ) -> int:

        score = 0

        year_count = len(
            self.YEAR_RE.findall(
                text
            )
        )

        email_count = len(
            self.EMAIL_RE.findall(
                text
            )
        )

        phone_count = len(
            self.PHONE_RE.findall(
                text
            )
        )

        roll_count = len(
            self.ROLL_NUMBER_RE.findall(
                text
            )
        )

        if person_field_hits >= 3:
            score += 20

        if person_field_hits >= 5:
            score += 30

        if year_count >= 3:
            score += 15

        if year_count >= 10:
            score += 20

        if email_count >= 2:
            score += 25

        if phone_count >= 2:
            score += 25

        if roll_count >= 2:
            score += 30

        return score

    # ==================================================================
    # SUBSTANTIVE CONTENT
    # ==================================================================

    @staticmethod
    def _looks_like_substantive_content(
        text: str,
    ) -> bool:

        tokens = re.findall(
            r"\b[a-zA-Z]{3,}\b",
            text,
        )

        if len(tokens) < 12:
            return False

        unique_ratio = (
            len(
                set(
                    token.lower()
                    for token in tokens
                )
            )
            / len(tokens)
        )

        if unique_ratio < 0.25:
            return False

        return (
            "."
            in text
            or ":"
            in text
            or ";"
            in text
        )

    # ==================================================================
    # NORMALIZATION
    # ==================================================================

    @staticmethod
    def _normalize(
        value: str,
    ) -> str:

        value = (
            value
            or ""
        ).lower()

        value = value.replace(
            "-",
            " ",
        )

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

    @staticmethod
    def _clean(
        value: str,
    ) -> str:

        if value is None:
            return ""

        return str(
            value
        ).strip()

    @staticmethod
    def _tokens(
        value: str,
    ) -> list[str]:

        return re.findall(
            r"\b[a-zA-Z]{2,}\b",
            value,
        )

    # ==================================================================
    # RESULT
    # ==================================================================

    @staticmethod
    def _result(
        *,
        decision: str,
        confidence: str,
        score: int,
        reasons: list[str],
        signals: dict[str, Any],
    ) -> dict[str, Any]:

        return asdict(
            ValueDecision(
                decision=decision,
                confidence=confidence,
                score=score,
                reasons=reasons,
                signals=signals,
            )
        )


# ======================================================================
# CONVENIENCE API
# ======================================================================


def classify_knowledge_value(
    *,
    heading: str = "",
    text: str = "",
    source_name: str = "",
    document_title: str = "",
    document_url: str = "",
    content_type: str = "",
    section_path: list[str] | None = None,
    record_index: int | None = None,
    record_count: int | None = None,
) -> dict[str, Any]:

    return KnowledgeValueFilter().classify(
        heading=heading,
        text=text,
        source_name=source_name,
        document_title=document_title,
        document_url=document_url,
        content_type=content_type,
        section_path=section_path,
        record_index=record_index,
        record_count=record_count,
    )