"""
Production RAG Content Filter

Purpose
-------
Global quality gate applied after structured/organized knowledge has been
classified into A / B / C / REVIEW / EXCLUDE.

Final RAG eligibility:

    A
    B
    C
    REVIEW units that pass the quality gate

Never include:

    D / original EXCLUDE
    news / newsletters / newspaper-style content
    temporary media/highlight content
    individual person/name lists
    batch profiles / rosters
    individual project records
    historical project databases
    generic non-institutional articles
    donation/payment-only pages
    generic cyber-awareness material
    empty/extraction garbage
    content with no clear student/institute value

Important
---------
1. A/B/C retain their original class/tier.
2. REVIEW remains REVIEW-originated. It is NEVER converted to C.
3. Original EXCLUDE is immutable and can never be resurrected.
4. Raw URLs are removed from the final RAG text.
5. Markdown image/link wrappers are removed while useful visible text
   remains.
6. The filter is engineering-college oriented, not IIT-Jodhpur-specific.
7. No LLM is used here. The filter is deterministic and auditable.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from copy import deepcopy
from pathlib import Path
from typing import Any


# ============================================================================
# CONSTANTS
# ============================================================================

FINAL_RAG_VERSION = "1.0"

STATUS_KEEP = "KEEP"
STATUS_REVIEW = "REVIEW"
STATUS_EXCLUDE = "EXCLUDE"

FINAL_CLASS_A = "A"
FINAL_CLASS_B = "B"
FINAL_CLASS_C = "C"
FINAL_CLASS_REVIEW = "REVIEW"
FINAL_CLASS_D = "D"


# ============================================================================
# ENGINEERING-COLLEGE RELEVANCE SIGNALS
# ============================================================================

STUDENT_SIGNALS = (
    "admission",
    "admissions",
    "eligibility",
    "b.tech",
    "b.e.",
    "b.sc",
    "b.s.",
    "m.tech",
    "m.e.",
    "m.sc",
    "mba",
    "m.b.a",
    "ph.d",
    "phd",
    "programme",
    "program",
    "semester",
    "academic session",
    "academic year",
    "course",
    "courses",
    "curriculum",
    "credit",
    "credits",
    "academic load",
    "academic requirement",
    "academic requirements",
    "registration",
    "enrollment",
    "enrolment",
    "examination",
    "examinations",
    "exam",
    "attendance",
    "grading",
    "grade",
    "sgpa",
    "cgpa",
    "fee",
    "fees",
    "refund",
    "refunds",
    "scholarship",
    "scholarships",
    "fellowship",
    "fellowships",
    "hostel",
    "mess",
    "library",
    "medical",
    "health centre",
    "health center",
    "transport",
    "student service",
    "student services",
    "student support",
    "student affairs",
    "placement",
    "placements",
    "internship",
    "internships",
    "leave rules",
    "leave policy",
    "exchange programme",
    "exchange program",
    "visiting student",
    "minor",
    "major",
    "specialization",
    "specialisation",
    "reservation policy",
    "academic regulation",
    "academic regulations",
    "academic procedure",
    "academic procedures",
    "graduate attributes",
    "course structure",
    "credit structure",
    "timetable",
    "time table",
    "class timetable",
    "class time table",
    "class schedule",
    "section a",
    "section b",
    "seat matrix",
    "total seats",
)

INSTITUTE_SIGNALS = (
    "department",
    "departments",
    "school",
    "schools",
    "centre",
    "centres",
    "center",
    "centers",
    "institute",
    "institution",
    "office",
    "administration",
    "administrative",
    "registrar",
    "director",
    "dean",
    "governance",
    "policy",
    "policies",
    "procedure",
    "procedures",
    "campus",
    "facility",
    "facilities",
    "infrastructure",
    "accreditation",
    "quality assurance",
    "vision",
    "mission",
    "special unit",
    "special units",
)

RESEARCH_SIGNALS = (
    "research area",
    "research areas",
    "research centre",
    "research center",
    "research centres",
    "research centers",
    "research group",
    "research groups",
    "research laboratory",
    "research laboratories",
    "research lab",
    "research labs",
    "research facility",
    "research facilities",
    "research programme",
    "research program",
    "research themes",
    "research focus",
    "focus areas",
    "research expertise",
    "research interests",
    "research domains",
    "technology track",
    "technology tracks",
)

OPERATIONAL_ACADEMIC_SIGNALS = (
    "seat matrix",
    "total seats",
    "waitlist",
    "waitlist for",
    "shortlist",
    "class timetable",
    "time table",
    "timetable",
    "section a",
    "section b",
    "group a1",
    "group a2",
    "group a3",
    "group a4",
    "group a5",
    "group a6",
    "group b1",
    "group b2",
    "group b3",
    "group b4",
    "group b5",
)


# ============================================================================
# CLEAR EXCLUSION SIGNALS
# ============================================================================

NEWS_HEADINGS = (
    "news",
    "latest news",
    "featured news",
    "newsletter",
    "newsletters",
    "press release",
    "press releases",
    "news update",
    "news updates",
)

ROSTER_PHRASES = (
    "batch profile",
    "batch profiles",
    "batch list",
    "batch name list",
    "student roster",
    "student rosters",
    "student name list",
    "candidate list",
    "candidate lists",
    "participant list",
    "participant lists",
    "alumni list",
    "alumni lists",
    "scholar list",
    "scholars list",
    "faculty list",
    "faculty lists",
    "staff list",
    "staff lists",
)

GENERIC_ARTICLE_HEADINGS = (
    "students",
    "educators",
    "education",
)

GENERIC_CYBER_HEADINGS = (
    "juice jacking",
    "blackmail or sextortion emails",
    "blackmail",
    "sextortion",
    "cyber threat",
    "cybersecurity awareness",
    "spam emails",
)

DONATION_MARKERS = (
    "donation form",
    "online donation",
    "donation via qr",
    "payment through net banking",
    "bank account details",
    "donation amount",
    "pan number for tax receipt",
)

TEMPORARY_CONTENT_MARKERS = (
    "distinguished lecture",
    "extra-mural lecture",
    "extra mural lecture",
    "lecture series",
    "faculty development program",
    "faculty development programme",
    "workshop schedule",
    "registration deadline",
    "call for papers",
    "research assistant recruitment",
)

ARCHIVE_SOURCE_MARKERS = (
    "archive_",
    "archived_",
)

MEDIA_ONLY_HEADINGS = (
    "photo gallery",
    "photo galleries",
    "image gallery",
    "video gallery",
    "media gallery",
)

INDIVIDUAL_PROJECT_SOURCE_MARKERS = (
    "ongoing_projects",
    "project_staff",
    "project_staff_appointment",
    "project_staff_members",
)

INDIVIDUAL_PROJECT_HEADINGS = (
    "project staff appointment",
    "project staff members",
    "project description",
    "individual project",
    "project profile",
    "project implementation",
)

HISTORICAL_PROJECT_SOURCE_MARKERS = (
    "website-research-projects-",
    "website_research_projects",
    "website-research-projects",
)

STUDENT_ROSTER_SOURCE_MARKERS = (
    "students__",
    "student_list",
    "students_",
)

GENERIC_RESEARCH_DUMP_HEADINGS = (
    "highlights",
)


# ============================================================================
# TEXT / FIELD HELPERS
# ============================================================================

def normalize(value: Any) -> str:
    """
    Normalize text for rule matching.

    We intentionally preserve the original value elsewhere.
    """
    text = str(value or "").lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def get_heading(unit: dict[str, Any]) -> str:
    return str(
        unit.get("heading", "") or ""
    ).strip()


def get_source(unit: dict[str, Any]) -> str:
    return str(
        unit.get(
            "source_document_name",
            unit.get(
                "source_document",
                "",
            ),
        )
        or ""
    ).strip()


def get_source_url(unit: dict[str, Any]) -> str:
    return str(
        unit.get("source_url", "") or ""
    ).strip()


def get_body(unit: dict[str, Any]) -> str:
    return str(
        unit.get("text", "") or ""
    )


def get_taxonomy(unit: dict[str, Any]) -> str:
    return "/".join(
        [
            normalize(
                unit.get(
                    "taxonomy_domain",
                    "",
                )
            ),
            normalize(
                unit.get(
                    "taxonomy_category",
                    "",
                )
            ),
            normalize(
                unit.get(
                    "taxonomy_subcategory",
                    "",
                )
            ),
        ]
    )


def get_rag(unit: dict[str, Any]) -> dict[str, Any]:
    value = unit.get("rag", {})

    if not isinstance(value, dict):
        return {}

    return value


def get_original_rag_status(
    unit: dict[str, Any],
) -> str:
    rag = get_rag(unit)

    original_status = rag.get(
        "original_status"
    )

    if original_status:
        return str(
            original_status
        ).upper()

    return str(
        rag.get(
            "status",
            "",
        )
    ).upper()


def combined_search_text(
    unit: dict[str, Any],
) -> str:
    return " ".join(
        [
            normalize(
                get_heading(unit)
            ),
            normalize(
                get_source(unit)
            ),
            normalize(
                get_source_url(unit)
            ),
            get_taxonomy(unit),
            normalize(
                get_body(unit)
            ),
        ]
    )


# ============================================================================
# FINAL RAG TEXT SANITIZATION
# ============================================================================

def clean_rag_text(
    text: str,
) -> str:
    """
    Remove URL/image/link clutter while preserving useful visible text.

    Examples
    --------
    ![Research Areas](https://example/image.png)
        -> Research Areas

    [Click here](https://example/page)
        -> Click here

    https://example/page
        -> removed

    Important:
    ---------
    This does not attempt OCR/image understanding.
    Information that exists only inside an image is therefore not
    reconstructed here.
    """

    if not text:
        return ""

    cleaned = str(text)

    # Markdown images: keep alt text, discard destination.
    cleaned = re.sub(
        r"!\[([^\]]*)\]\(\s*[^)]*\)",
        r"\1",
        cleaned,
        flags=re.DOTALL,
    )

    # Markdown links: keep visible text.
    cleaned = re.sub(
        r"\[([^\]]+)\]\(\s*[^)]*\)",
        r"\1",
        cleaned,
        flags=re.DOTALL,
    )

    # Reference-style markdown links.
    cleaned = re.sub(
        r"!\[([^\]]*)\]\[[^\]]*\]",
        r"\1",
        cleaned,
    )

    cleaned = re.sub(
        r"\[([^\]]+)\]\[[^\]]*\]",
        r"\1",
        cleaned,
    )

    # HTML anchors: preserve visible text.
    cleaned = re.sub(
        r'<a\b[^>]*href=["\'][^"\']*["\'][^>]*>(.*?)</a>',
        r"\1",
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # Remove raw URLs.
    cleaned = re.sub(
        r"https?://[^\s<>\]\)\"']+",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    # Remove mailto links.
    cleaned = re.sub(
        r"mailto:[^\s<>\]\)\"']+",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    # Remove obvious HTML tags.
    cleaned = re.sub(
        r"<[^>]+>",
        " ",
        cleaned,
    )

    # Remove empty markdown leftovers.
    cleaned = re.sub(
        r"\[\s*\]",
        "",
        cleaned,
    )

    cleaned = re.sub(
        r"\(\s*\)",
        "",
        cleaned,
    )

    # Remove common raw crawler placeholders.
    cleaned = re.sub(
        r"\b(?:view|visit|click)\s+here\s*:\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    # Normalize whitespace but preserve line breaks.
    cleaned = re.sub(
        r"[ \t]+",
        " ",
        cleaned,
    )

    cleaned = re.sub(
        r"\n{3,}",
        "\n\n",
        cleaned,
    )

    return cleaned.strip()


# ============================================================================
# URL / MARKDOWN HELPERS
# ============================================================================

def count_urls(text: str) -> int:
    return len(
        re.findall(
            r"https?://\S+",
            str(text or ""),
            flags=re.IGNORECASE,
        )
    )


def has_markdown_media_or_links(
    text: str,
) -> bool:
    text = str(text or "")

    return bool(
        re.search(
            r"!\[[^\]]*\]\(",
            text,
        )
        or re.search(
            r"\[[^\]]+\]\(",
            text,
        )
        or re.search(
            r"https?://",
            text,
            flags=re.IGNORECASE,
        )
    )


# ============================================================================
# CONTENT CLASSIFIERS
# ============================================================================

def is_empty_or_garbage(
    unit: dict[str, Any],
) -> bool:
    text = normalize(
        get_body(unit)
    )

    if len(text) < 40:
        return True

    if text in {
        "coming up soon",
        "coming up soon...",
        "n/a",
        "na",
        "not available",
    }:
        return True

    return False


def is_news_or_newsletter(
    unit: dict[str, Any],
) -> bool:
    heading = normalize(
        get_heading(unit)
    )

    source = normalize(
        get_source(unit)
    )

    if heading in NEWS_HEADINGS:
        return True

    if any(
        marker in heading
        for marker in NEWS_HEADINGS
    ):
        return True

    if any(
        marker in source
        for marker in (
            "newsletter",
            "press_release",
            "press-release",
        )
    ):
        return True

    return False


def is_batch_or_roster(
    unit: dict[str, Any],
) -> bool:
    heading = normalize(
        get_heading(unit)
    )

    source = normalize(
        get_source(unit)
    )

    text = normalize(
        get_body(unit)
    )

    if any(
        phrase in heading
        for phrase in ROSTER_PHRASES
    ):
        return True

    if any(
        marker in source
        for marker in (
            "batch_profile",
            "student_roster",
            "candidate_list",
            "alumni_list",
            "faculty_list",
        )
    ):
        return True

    # Strong tabular people-list signature.
    if (
        "full name" in text
        and "email address" in text
        and (
            "education" in text
            or "research area" in text
        )
    ):
        return True

    # Multiple direct IIT people profile URLs are a name directory.
    if text.count(
        "/people/profile/"
    ) >= 3:
        return True

    # A students source containing a Name/Email/Research Area table
    # is a roster, not reusable institutional knowledge.
    if (
        "students" in source
        and "name" in text
        and "email" in text
        and (
            "research area" in text
            or "education" in text
        )
    ):
        return True

    return False


def is_individual_person_record(
    unit: dict[str, Any],
) -> bool:
    heading = normalize(
        get_heading(unit)
    )

    source = normalize(
        get_source(unit)
    )

    text = normalize(
        get_body(unit)
    )

    person_source = any(
        marker in source
        for marker in (
            "faculty",
            "people",
            "profile",
            "profiles",
            "staff",
            "alumni",
            "advisors",
        )
    )

    if not person_source:
        return False

    institutional_heading = any(
        marker in heading
        for marker in (
            "department",
            "school",
            "office",
            "centre",
            "center",
            "laboratory",
            "research group",
            "research area",
            "committee",
        )
    )

    if institutional_heading:
        return False

    # A very short person-specific page with contact details.
    title_signal = any(
        marker in text
        for marker in (
            "professor",
            "prof.",
            "dr.",
            "advisor to the director",
        )
    )

    contact_signal = any(
        marker in text
        for marker in (
            "email",
            "phone",
            "telephone",
            "mobile",
            "@iit",
        )
    )

    if title_signal and contact_signal:
        words = heading.split()

        if 1 <= len(words) <= 7:
            return True

    # Explicit profile-type source names.
    if person_source and any(
        marker in heading
        for marker in (
            "biography",
            "biographical profile",
            "personal profile",
            "profile of",
            "curriculum vitae",
        )
    ):
        return True

    return False


def is_individual_or_historical_project(
    unit: dict[str, Any],
) -> bool:
    """
    Do NOT exclude the entire research_projects taxonomy.

    Keep:
        research areas
        research groups
        laboratories
        department overviews
        research programmes
        broad research themes

    Exclude:
        individual sponsored project records
        historical website project databases
        project staff pages
        project appointment pages
        explicit project-profile records
    """

    heading = normalize(
        get_heading(unit)
    )

    source = normalize(
        get_source(unit)
    )

    text = normalize(
        get_body(unit)
    )

    # ------------------------------------------------------------
    # Explicit historical project database.
    # ------------------------------------------------------------

    if any(
        marker in source
        for marker in HISTORICAL_PROJECT_SOURCE_MARKERS
    ):
        return True

    # ------------------------------------------------------------
    # Explicit project-staff sources.
    # ------------------------------------------------------------

    if any(
        marker in source
        for marker in INDIVIDUAL_PROJECT_SOURCE_MARKERS
    ):
        return True

    # ------------------------------------------------------------
    # Explicit project-record headings.
    # ------------------------------------------------------------

    if any(
        marker in heading
        for marker in INDIVIDUAL_PROJECT_HEADINGS
    ):
        return True

    # ------------------------------------------------------------
    # Strong individual-project record signature.
    # ------------------------------------------------------------

    funding_markers = (
        "funding agency",
        "principal investigator",
        "brief description",
        "core research grant",
        "seed grant",
        "sponsored research project",
        "fellowship project",
        "consultancy",
    )

    if (
        "project" in heading
        and any(
            marker in text
            for marker in funding_markers
        )
    ):
        return True

    return False


def is_temporary_or_highlight_content(
    unit: dict[str, Any],
) -> bool:
    heading = normalize(
        get_heading(unit)
    )

    source = normalize(
        get_source(unit)
    )

    text = normalize(
        get_body(unit)
    )

    if any(
        marker in heading
        for marker in TEMPORARY_CONTENT_MARKERS
    ):
        return True

    if any(
        marker in source
        for marker in (
            "highlights",
            "faculty_development_program",
            "event_schedule",
        )
    ):
        return True

    if (
        "call for papers" in text
        or "research assistant recruitment" in text
    ):
        return True

    # Temporary dated programme/event schedule.
    if (
        "registration deadline" in text
        and (
            "session" in text
            or "inauguration" in text
            or "workshop" in text
            or "lecture" in text
        )
    ):
        return True

    return False


def is_donation_or_payment_content(
    unit: dict[str, Any],
) -> bool:
    heading = normalize(
        get_heading(unit)
    )

    text = normalize(
        get_body(unit)
    )

    if any(
        marker in heading
        for marker in (
            "donation",
            "donate",
        )
    ):
        return True

    return any(
        marker in text
        for marker in DONATION_MARKERS
    )


def is_generic_cyber_awareness(
    unit: dict[str, Any],
) -> bool:
    source = normalize(
        get_source(unit)
    )

    heading = normalize(
        get_heading(unit)
    )

    text = normalize(
        get_body(unit)
    )

    if "cyber_threat" not in source:
        return False

    if any(
        marker in heading
        for marker in GENERIC_CYBER_HEADINGS
    ):
        return True

    return any(
        marker in text
        for marker in GENERIC_CYBER_HEADINGS
    )


def is_generic_non_institutional_article(
    unit: dict[str, Any],
) -> bool:
    heading = normalize(
        get_heading(unit)
    )

    text = normalize(
        get_body(unit)
    )

    taxonomy = get_taxonomy(unit)

    # Protect real engineering-college taxonomy.
    protected_taxonomy = (
        "admissions",
        "academics",
        "academic_calendar",
        "academic_rules",
        "course",
        "curriculum",
        "program",
        "programme",
        "department",
        "school",
        "research",
        "student",
        "campus",
        "infrastructure",
        "facility",
    )

    if any(
        marker in taxonomy
        for marker in protected_taxonomy
    ):
        return False

    if heading in GENERIC_ARTICLE_HEADINGS:
        return True

    # General non-IIT-specific educational article.
    generic_article_markers = (
        "post-covid",
        "post covid",
        "global pandemic",
        "educational institutions",
        "schools and universities",
        "teachers worldwide",
        "worldwide",
        "general public",
        "remote areas",
    )

    return (
        any(
            marker in text
            for marker in generic_article_markers
        )
        and "iit" not in text
    )


def is_media_only_content(
    unit: dict[str, Any],
) -> bool:
    """
    Image URLs inside useful text are NOT a reason to exclude.

    We only exclude when the unit is effectively just media.
    """

    heading = normalize(
        get_heading(unit)
    )

    text = normalize(
        get_body(unit)
    )

    if heading in MEDIA_ONLY_HEADINGS:
        return True

    # Remove URLs and markdown wrappers temporarily.
    cleaned = clean_rag_text(
        text
    )

    # If practically nothing meaningful remains, it is media-only.
    return len(
        normalize(cleaned)
    ) < 25


def has_clear_relevance(
    unit: dict[str, Any],
) -> tuple[bool, list[str]]:
    text = combined_search_text(
        unit
    )

    reasons: list[str] = []

    if any(
        signal in text
        for signal in STUDENT_SIGNALS
    ):
        reasons.append(
            "student_relevance"
        )

    if any(
        signal in text
        for signal in INSTITUTE_SIGNALS
    ):
        reasons.append(
            "institute_relevance"
        )

    if any(
        signal in text
        for signal in RESEARCH_SIGNALS
    ):
        reasons.append(
            "research_relevance"
        )

    if any(
        signal in text
        for signal in OPERATIONAL_ACADEMIC_SIGNALS
    ):
        reasons.append(
            "operational_academic_relevance"
        )

    return (
        bool(reasons),
        reasons,
    )


# ============================================================================
# FAMILY INFERENCE
# ============================================================================

def infer_family_hint(
    unit: dict[str, Any],
) -> str:
    """
    Dynamic semantic family hint.

    This is not a fixed global 17-file taxonomy.
    It only gives the existing planner useful routing information
    for content that survives the quality gate.
    """

    heading = normalize(
        get_heading(unit)
    )

    source = normalize(
        get_source(unit)
    )

    text = combined_search_text(
        unit
    )

    taxonomy = get_taxonomy(unit)

    # ------------------------------------------------------------
    # Admissions
    # ------------------------------------------------------------

    if (
        "admissions" in taxonomy
        or "seat matrix" in text
        or "waitlist" in text
        or "shortlist" in text
    ):
        return "admissions"

    # ------------------------------------------------------------
    # Timetables / operational academic scheduling
    # ------------------------------------------------------------

    if (
        "timetable" in source
        or "time_table" in source
        or "class_schedule" in source
        or heading.startswith("group ")
        or heading.startswith("first year")
        or "section a" in heading
        or "section b" in heading
    ):
        return (
            "academic_calendar_and_timetables"
        )

    # ------------------------------------------------------------
    # Academic rules
    # ------------------------------------------------------------

    if any(
        phrase in text
        for phrase in (
            "attendance requirement",
            "academic load",
            "credit structure",
            "minimum credit",
            "maximum duration",
            "leave rules",
            "semester grade point average",
            "cumulative grade point average",
            "academic regulation",
            "academic regulations",
        )
    ):
        return (
            "academic_rules_and_regulations"
        )

    # ------------------------------------------------------------
    # Academic programmes
    # ------------------------------------------------------------

    if any(
        marker in taxonomy
        for marker in (
            "program",
            "programme",
            "curriculum",
            "course",
        )
    ):
        return "academic_programs"

    if any(
        marker in text
        for marker in (
            "b.tech",
            "m.tech",
            "b.sc",
            "m.sc",
            "ph.d",
            "phd",
            "graduate attributes",
            "course structure",
            "credit structure",
        )
    ):
        return "academic_programs"

    # ------------------------------------------------------------
    # Research areas / groups
    # ------------------------------------------------------------

    if any(
        signal in text
        for signal in RESEARCH_SIGNALS
    ):
        if any(
            marker in text
            for marker in (
                "research laboratory",
                "research lab",
                "laboratory",
                "laboratories",
                "associated labs",
            )
        ):
            return (
                "research_centres_and_labs"
            )

        return (
            "research_areas_and_groups"
        )

    # ------------------------------------------------------------
    # Research outputs / innovation
    # ------------------------------------------------------------

    if any(
        marker in text
        for marker in (
            "patent",
            "intellectual property",
            "technology transfer",
            "innovation output",
            "research output",
        )
    ):
        return (
            "research_outputs_and_innovation"
        )

    # ------------------------------------------------------------
    # Departments / schools
    # ------------------------------------------------------------

    if (
        "department" in taxonomy
        or "school" in taxonomy
        or "department of" in text
        or "school of" in text
    ):
        return (
            "departments_and_schools"
        )

    # ------------------------------------------------------------
    # Student life / residential
    # ------------------------------------------------------------

    if any(
        marker in text
        for marker in (
            "hostel",
            "mess",
            "student services",
            "student support",
            "student affairs",
        )
    ):
        return (
            "student_residential_life"
        )

    # ------------------------------------------------------------
    # Campus / infrastructure / facilities
    # ------------------------------------------------------------

    if any(
        marker in text
        for marker in (
            "campus",
            "facility",
            "facilities",
            "infrastructure",
            "studio",
            "equipment",
        )
    ):
        return (
            "campus_and_infrastructure"
        )

    # ------------------------------------------------------------
    # Institutional offices / centres / units
    # ------------------------------------------------------------

    if any(
        marker in text
        for marker in (
            "office of",
            "nodal office",
            "institute office",
            "centre for",
            "center for",
            "special unit",
            "special units",
        )
    ):
        return (
            "institute_centres_and_units"
        )

    # ------------------------------------------------------------
    # Research/program source family fallback
    # ------------------------------------------------------------

    if "research" in taxonomy:
        return (
            "research_areas_and_groups"
        )

    # ------------------------------------------------------------
    # Generic useful fallback
    # ------------------------------------------------------------

    return "dynamic_family_required"


# ============================================================================
# MAIN DECISION
# ============================================================================

def classify_unit(
    unit: dict[str, Any],
) -> tuple[str, list[str]]:
    """
    Return:
        KEEP
        EXCLUDE

    with deterministic audit reasons.
    """

    original_status = (
        get_original_rag_status(unit)
    )

    # ------------------------------------------------------------
    # Absolute safety rule
    # ------------------------------------------------------------

    if original_status == STATUS_EXCLUDE:
        return (
            STATUS_EXCLUDE,
            [
                "original_exclude_d",
            ],
        )

    # ------------------------------------------------------------
    # Empty / unusable
    # ------------------------------------------------------------

    if is_empty_or_garbage(unit):
        return (
            STATUS_EXCLUDE,
            [
                "empty_or_extraction_garbage",
            ],
        )

    # ------------------------------------------------------------
    # Clear junk
    # ------------------------------------------------------------

    if is_news_or_newsletter(unit):
        return (
            STATUS_EXCLUDE,
            [
                "news_or_newsletter",
            ],
        )

    if is_batch_or_roster(unit):
        return (
            STATUS_EXCLUDE,
            [
                "batch_roster_or_name_list",
            ],
        )

    if is_individual_person_record(unit):
        return (
            STATUS_EXCLUDE,
            [
                "individual_person_record",
            ],
        )

    if is_individual_or_historical_project(unit):
        return (
            STATUS_EXCLUDE,
            [
                "individual_or_historical_project",
            ],
        )

    if is_temporary_or_highlight_content(unit):
        return (
            STATUS_EXCLUDE,
            [
                "temporary_or_highlight_content",
            ],
        )

    if is_donation_or_payment_content(unit):
        return (
            STATUS_EXCLUDE,
            [
                "donation_or_payment_content",
            ],
        )

    if is_generic_cyber_awareness(unit):
        return (
            STATUS_EXCLUDE,
            [
                "generic_cyber_awareness",
            ],
        )

    if is_generic_non_institutional_article(unit):
        return (
            STATUS_EXCLUDE,
            [
                "generic_non_institutional_article",
            ],
        )

    if is_media_only_content(unit):
        return (
            STATUS_EXCLUDE,
            [
                "media_only_content",
            ],
        )

    # ------------------------------------------------------------
    # Useful institutional content
    # ------------------------------------------------------------

    relevant, reasons = has_clear_relevance(
        unit
    )

    if relevant:
        return (
            STATUS_KEEP,
            reasons,
        )

    # ------------------------------------------------------------
    # Strong taxonomy fallback
    # ------------------------------------------------------------

    taxonomy = get_taxonomy(
        unit
    )

    protected_taxonomy_markers = (
        "admissions",
        "academics",
        "academic_calendar",
        "academic_rules",
        "curriculum",
        "course",
        "program",
        "programme",
        "department",
        "school",
        "research",
        "student",
        "campus",
        "infrastructure",
        "facility",
        "institutes_centres",
    )

    if any(
        marker in taxonomy
        for marker in protected_taxonomy_markers
    ):
        return (
            STATUS_KEEP,
            [
                "substantive_institutional_taxonomy",
            ],
        )

    # Unknown content is excluded rather than leaking
    # into final RAG.
    return (
        STATUS_EXCLUDE,
        [
            "no_clear_student_or_institute_value",
        ],
    )


# ============================================================================
# UNIT TRANSFORMATION
# ============================================================================

def transform_unit(
    unit: dict[str, Any],
    decision: str,
    reasons: list[str],
) -> dict[str, Any]:
    """
    Return a new unit. Never mutates the input unit.
    """

    result = deepcopy(
        unit
    )

    rag = deepcopy(
        get_rag(unit)
    )

    original_status = (
        get_original_rag_status(unit)
    )

    if decision == STATUS_KEEP:

        rag["status"] = STATUS_KEEP

        rag[
            "final_rag_decision"
        ] = "INCLUDE"

        rag[
            "final_rag_class"
        ] = (
            FINAL_CLASS_REVIEW
            if original_status == STATUS_REVIEW
            else (
                str(
                    rag.get(
                        "tier",
                        "",
                    )
                ).upper()
            )
        )

        rag[
            "filter_version"
        ] = FINAL_RAG_VERSION

        rag[
            "filter_reasons"
        ] = reasons

        if original_status == STATUS_REVIEW:

            rag[
                "original_status"
            ] = STATUS_REVIEW

            # REVIEW remains REVIEW.
            # Never assign A/B/C here.
            rag.pop(
                "tier",
                None,
            )

            rag[
                "final_family_hint"
            ] = infer_family_hint(
                unit
            )

        # Keep the actual A/B/C tier unchanged.
        result["rag"] = rag

        # Final RAG text must be sanitized.
        result[
            "text"
        ] = clean_rag_text(
            get_body(unit)
        )

        return result

    # ------------------------------------------------------------
    # Excluded unit
    # ------------------------------------------------------------

    rag["status"] = STATUS_EXCLUDE

    rag[
        "tier"
    ] = FINAL_CLASS_D

    rag[
        "final_rag_decision"
    ] = "EXCLUDE"

    rag[
        "filter_version"
    ] = FINAL_RAG_VERSION

    rag[
        "filter_reasons"
    ] = reasons

    result["rag"] = rag

    return result


# ============================================================================
# FILTER ENGINE
# ============================================================================

class RAGContentFilter:
    """
    Production deterministic RAG quality gate.

    Input:
        knowledge_units.json

    Output:
        cleaned RAG-eligible knowledge_units.json
        exclusion audit
        filter report
    """

    def __init__(
        self,
        source_manifest: str | Path,
        output_root: str | Path | None = None,
    ) -> None:

        self.source_manifest = Path(
            source_manifest
        )

        if output_root is None:
            self.output_root = (
                self.source_manifest.parent
            )
        else:
            self.output_root = Path(
                output_root
            )

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------

    def load_manifest(
        self,
    ) -> dict[str, Any]:

        if not self.source_manifest.exists():
            raise FileNotFoundError(
                "Knowledge manifest does not exist: "
                f"{self.source_manifest}"
            )

        try:
            return json.loads(
                self.source_manifest.read_text(
                    encoding="utf-8"
                )
            )
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Knowledge manifest contains invalid JSON: "
                f"{self.source_manifest}"
            ) from exc

    # ------------------------------------------------------------------
    # Validate
    # ------------------------------------------------------------------

    @staticmethod
    def validate_units(
        units: list[dict[str, Any]],
    ) -> None:

        if not isinstance(
            units,
            list,
        ):
            raise ValueError(
                "'units' must be a list."
            )

        seen: set[str] = set()

        for index, unit in enumerate(
            units
        ):
            if not isinstance(
                unit,
                dict,
            ):
                raise ValueError(
                    f"Unit at index {index} "
                    "is not a JSON object."
                )

            unit_id = str(
                unit.get(
                    "unit_id",
                    "",
                )
            ).strip()

            if not unit_id:
                raise ValueError(
                    f"Unit at index {index} "
                    "does not have a unit_id."
                )

            if unit_id in seen:
                raise ValueError(
                    "Duplicate unit_id detected: "
                    f"{unit_id}"
                )

            seen.add(
                unit_id
            )

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def run(
        self,
    ) -> dict[str, Any]:

        manifest = self.load_manifest()

        units = manifest.get(
            "units",
            [],
        )

        self.validate_units(
            units
        )

        original_status_counts = Counter()

        final_status_counts = Counter()

        final_class_counts = Counter()

        transition_counts = Counter()

        reason_counts = Counter()

        review_counts = Counter()

        review_family_counts = Counter()

        excluded_units = []

        included_units = []

        url_stats = {
            "units_with_urls": 0,
            "units_cleaned": 0,
            "urls_removed": 0,
        }

        duplicate_map: dict[
            str,
            str,
        ] = {}

        duplicate_records = []

        for unit in units:

            original_status = (
                get_original_rag_status(
                    unit
                )
            )

            original_status_counts[
                original_status
            ] += 1

            original_text = get_body(
                unit
            )

            original_url_count = count_urls(
                original_text
            )

            if original_url_count:
                url_stats[
                    "units_with_urls"
                ] += 1

            decision, reasons = classify_unit(
                unit
            )

            for reason in reasons:
                reason_counts[
                    reason
                ] += 1

            transition_counts[
                (
                    original_status,
                    decision,
                )
            ] += 1

            if original_status == STATUS_REVIEW:

                review_counts[
                    decision
                ] += 1

            transformed = transform_unit(
                unit,
                decision,
                reasons,
            )

            if decision == STATUS_KEEP:

                included_units.append(
                    transformed
                )

                final_rag = get_rag(
                    transformed
                )

                final_status = str(
                    final_rag.get(
                        "status",
                        "",
                    )
                ).upper()

                final_class = str(
                    final_rag.get(
                        "final_rag_class",
                        final_rag.get(
                            "tier",
                            "",
                        ),
                    )
                ).upper()

                final_status_counts[
                    final_status
                ] += 1

                final_class_counts[
                    final_class
                ] += 1

                if original_status == STATUS_REVIEW:

                    family = final_rag.get(
                        "final_family_hint"
                    )

                    review_family_counts[
                        str(
                            family
                            or "dynamic_family_required"
                        )
                    ] += 1

                cleaned_text = transformed.get(
                    "text",
                    "",
                )

                cleaned_url_count = count_urls(
                    cleaned_text
                )

                removed_urls = (
                    original_url_count
                    - cleaned_url_count
                )

                if removed_urls > 0:
                    url_stats[
                        "units_cleaned"
                    ] += 1

                    url_stats[
                        "urls_removed"
                    ] += removed_urls

                # Duplicate fingerprint AFTER URL cleanup.
                fingerprint_text = (
                    normalize(
                        get_heading(
                            transformed
                        )
                    )
                    + "\n"
                    + normalize(
                        cleaned_text
                    )
                )

                fingerprint = (
                    __import__(
                        "hashlib"
                    )
                    .sha256(
                        fingerprint_text.encode(
                            "utf-8"
                        )
                    )
                    .hexdigest()
                )

                unit_id = str(
                    transformed.get(
                        "unit_id",
                        "",
                    )
                )

                if fingerprint in duplicate_map:

                    duplicate_records.append(
                        {
                            "unit_id": unit_id,
                            "duplicate_of": (
                                duplicate_map[
                                    fingerprint
                                ]
                            ),
                        }
                    )

                else:

                    duplicate_map[
                        fingerprint
                    ] = unit_id

            else:

                excluded_units.append(
                    transformed
                )

                final_status_counts[
                    STATUS_EXCLUDE
                ] += 1

                final_class_counts[
                    FINAL_CLASS_D
                ] += 1

        # --------------------------------------------------------------
        # Final manifest
        # --------------------------------------------------------------

        result_manifest = deepcopy(
            manifest
        )

        # The final filtered manifest contains ONLY RAG-eligible units.
        result_manifest[
            "units"
        ] = included_units

        result_manifest[
            "final_rag"
        ] = {
            "filter_version": FINAL_RAG_VERSION,
            "domain": manifest.get(
                "domain"
            ),
            "source_manifest": str(
                self.source_manifest
            ),
            "input_units": len(
                units
            ),
            "final_rag_units": len(
                included_units
            ),
            "excluded_units": len(
                excluded_units
            ),
            "original_status_counts": dict(
                sorted(
                    original_status_counts.items()
                )
            ),
            "final_status_counts": dict(
                sorted(
                    final_status_counts.items()
                )
            ),
            "final_class_counts": dict(
                sorted(
                    final_class_counts.items()
                )
            ),
            "review": {
                "input_review_units": review_counts.get(
                    STATUS_KEEP,
                    0,
                )
                + review_counts.get(
                    STATUS_EXCLUDE,
                    0,
                ),
                "kept_review_units": review_counts.get(
                    STATUS_KEEP,
                    0,
                ),
                "excluded_review_units": review_counts.get(
                    STATUS_EXCLUDE,
                    0,
                ),
                "family_hints": dict(
                    sorted(
                        review_family_counts.items()
                    )
                ),
            },
            "url_cleaning": url_stats,
            "duplicates_flagged": len(
                duplicate_records
            ),
        }

        # --------------------------------------------------------------
        # Reports
        # --------------------------------------------------------------

        excluded_audit = {
            "filter_version": FINAL_RAG_VERSION,
            "domain": manifest.get(
                "domain"
            ),
            "count": len(
                excluded_units
            ),
            "units": [
                {
                    "unit_id": unit.get(
                        "unit_id"
                    ),
                    "heading": get_heading(
                        unit
                    ),
                    "source_document": get_source(
                        unit
                    ),
                    "source_url": get_source_url(
                        unit
                    ),
                    "taxonomy": get_taxonomy(
                        unit
                    ),
                    "original_status": (
                        get_original_rag_status(
                            unit
                        )
                    ),
                    "filter_reasons": get_rag(
                        unit
                    ).get(
                        "filter_reasons",
                        [],
                    ),
                    "text_preview": normalize(
                        get_body(unit)
                    )[:800],
                }
                for unit in excluded_units
            ],
        }

        report = {
            "filter_version": FINAL_RAG_VERSION,
            "domain": manifest.get(
                "domain"
            ),
            "source_manifest": str(
                self.source_manifest
            ),
            "input_units": len(
                units
            ),
            "final_rag_units": len(
                included_units
            ),
            "excluded_units": len(
                excluded_units
            ),
            "original_status_counts": dict(
                sorted(
                    original_status_counts.items()
                )
            ),
            "final_status_counts": dict(
                sorted(
                    final_status_counts.items()
                )
            ),
            "final_class_counts": dict(
                sorted(
                    final_class_counts.items()
                )
            ),
            "transitions": {
                f"{src}->{dst}": count
                for (
                    (
                        src,
                        dst,
                    ),
                    count,
                ) in sorted(
                    transition_counts.items()
                )
            },
            "reason_counts": dict(
                reason_counts.most_common()
            ),
            "review": {
                "input": (
                    review_counts.get(
                        STATUS_KEEP,
                        0,
                    )
                    + review_counts.get(
                        STATUS_EXCLUDE,
                        0,
                    )
                ),
                "keep": review_counts.get(
                    STATUS_KEEP,
                    0,
                ),
                "exclude": review_counts.get(
                    STATUS_EXCLUDE,
                    0,
                ),
                "family_hints": dict(
                    review_family_counts.most_common()
                ),
            },
            "url_cleaning": url_stats,
            "duplicates": {
                "count": len(
                    duplicate_records
                ),
                "sample": duplicate_records[
                    :100
                ],
            },
        }

        return {
            "manifest": result_manifest,
            "report": report,
            "excluded_audit": excluded_audit,
        }

    # ------------------------------------------------------------------
    # Write output
    # ------------------------------------------------------------------

    def write_outputs(
        self,
        result: dict[str, Any],
    ) -> dict[str, Path]:

        self.output_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        manifest_path = (
            self.output_root
            / "knowledge_units_rag_filtered.json"
        )

        report_path = (
            self.output_root
            / "rag_content_filter_report.json"
        )

        excluded_path = (
            self.output_root
            / "rag_excluded_audit.json"
        )

        manifest_path.write_text(
            json.dumps(
                result["manifest"],
                indent=4,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        report_path.write_text(
            json.dumps(
                result["report"],
                indent=4,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        excluded_path.write_text(
            json.dumps(
                result["excluded_audit"],
                indent=4,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        return {
            "manifest": manifest_path,
            "report": report_path,
            "excluded_audit": excluded_path,
        }


# ============================================================================
# CLI
# ============================================================================

def build_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        description=(
            "Production engineering-college RAG content filter."
        )
    )

    parser.add_argument(
        "--manifest",
        required=True,
        help=(
            "Path to organized knowledge_units.json"
        ),
    )

    parser.add_argument(
        "--output-root",
        required=True,
        help=(
            "Directory where the filtered manifest and audit "
            "reports will be written."
        ),
    )

    return parser


def main() -> int:

    parser = build_parser()

    args = parser.parse_args()

    source_manifest = Path(
        args.manifest
    )

    output_root = Path(
        args.output_root
    )

    print()
    print("=" * 100)
    print(
        "PRODUCTION RAG CONTENT FILTER"
    )
    print("=" * 100)

    print(
        "Source manifest:",
        source_manifest,
    )

    print(
        "Output root:",
        output_root,
    )

    print()

    engine = RAGContentFilter(
        source_manifest=source_manifest,
        output_root=output_root,
    )

    result = engine.run()

    paths = engine.write_outputs(
        result
    )

    report = result[
        "report"
    ]

    print(
        "Input units:",
        report[
            "input_units"
        ],
    )

    print(
        "Final RAG units:",
        report[
            "final_rag_units"
        ],
    )

    print(
        "Excluded units:",
        report[
            "excluded_units"
        ],
    )

    print()
    print(
        "ORIGINAL STATUS"
    )

    for key, value in (
        report[
            "original_status_counts"
        ].items()
    ):
        print(
            f"  {key:8}: {value}"
        )

    print()
    print(
        "FINAL RAG CLASS"
    )

    for key, value in (
        report[
            "final_class_counts"
        ].items()
    ):
        print(
            f"  {key:8}: {value}"
        )

    print()
    print(
        "REVIEW"
    )

    print(
        "  Input   :",
        report[
            "review"
        ][
            "input"
        ],
    )

    print(
        "  Kept    :",
        report[
            "review"
        ][
            "keep"
        ],
    )

    print(
        "  Excluded:",
        report[
            "review"
        ][
            "exclude"
        ],
    )

    print()
    print(
        "URL CLEANING"
    )

    print(
        "  Units with URLs:",
        report[
            "url_cleaning"
        ][
            "units_with_urls"
        ],
    )

    print(
        "  Units cleaned:",
        report[
            "url_cleaning"
        ][
            "units_cleaned"
        ],
    )

    print(
        "  URLs removed:",
        report[
            "url_cleaning"
        ][
            "urls_removed"
        ],
    )

    print()
    print(
        "DUPLICATES FLAGGED:",
        report[
            "duplicates"
        ][
            "count"
        ],
    )

    print()
    print(
        "OUTPUT"
    )

    print(
        "  Filtered manifest:",
        paths[
            "manifest"
        ],
    )

    print(
        "  Filter report:",
        paths[
            "report"
        ],
    )

    print(
        "  Exclusion audit:",
        paths[
            "excluded_audit"
        ],
    )

    print()
    print(
        "=" * 100
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )