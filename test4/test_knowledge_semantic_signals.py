"""
Command 3 — Semantic Scope Tests.

Purpose
-------
Verify that semantic classification understands the difference between:

    document context
    section context
    record identity

The production engine must remain universal.

Real IITJ wording is used only as adversarial regression data.
"""

from processors.knowledge_semantic_signals import (
    KnowledgeSemanticSignalEngine,
)


# ============================================================
# HELPER
# ============================================================

def make_engine() -> KnowledgeSemanticSignalEngine:
    """Create a fresh semantic engine."""
    return KnowledgeSemanticSignalEngine()


# ============================================================
# RECORD IDENTITY
# ============================================================

def test_consultancy_record_overrides_research_document_context():
    """
    A specific consultancy record inside a research document should
    remain consultancy-primary.
    """

    result = make_engine().analyze(
        record_heading="Project Record",
        record_text=(
            "Creation of Virtual Class-Rooms at IITs "
            "over National Knowledge Network. "
            "National Informatics Centre. "
            "Consultancy. "
            "Computer Science & Engineering."
        ),
        section_context=[
            "Research Projects",
        ],
        document_title="Website Research Projects",
    )

    assert result["primary_type"] == "consultancy"

    assert "consultancy" in (
        result["matched_signals"]
    )

    assert "research projects" in (
        result["matched_signals"]
    )


def test_sponsored_research_record_remains_research():
    """
    A true sponsored research record should remain research-primary
    even when the surrounding document is broad research context.
    """

    result = make_engine().analyze(
        record_heading="Project Record",
        record_text=(
            "Development of advanced energy systems. "
            "DST Sponsored Research Project. "
            "Electrical Engineering."
        ),
        section_context=[
            "Research Projects",
        ],
        document_title="Website Research Projects",
    )

    assert result["primary_type"] == "research"

    assert result["confidence"] == "high"


# ============================================================
# ADMISSION VS FACULTY MENTION
# ============================================================

def test_phd_admission_overrides_incidental_faculty_and_fellowship():
    """
    A PhD admissions record may mention faculty and fellowships,
    but its primary identity should remain admission.
    """

    result = make_engine().analyze(
        record_heading="PhD Admission Details",
        record_text=(
            "Ph.D. Admissions AY 2026-27. "
            "Application Last Date: June 25, 2026. "
            "Department's Faculty Profile. "
            "Attractive fellowships are available."
        ),
        section_context=[
            "Admissions",
        ],
        document_title="PhD Materials",
    )

    assert result["primary_type"] == "admission"


# ============================================================
# STUDENT PROFILE
# ============================================================

def test_student_profile_does_not_become_consultancy():
    """
    Consultancy appearing inside a student's profile is incidental.
    """

    result = make_engine().analyze(
        record_heading="Student MBA Batch Profile",
        record_text=(
            "Interests include consulting and "
            "consultancy-related business strategy."
        ),
        document_title="Student MBA Batch Profile",
    )

    assert result["primary_type"] == "unknown"

    assert result["confidence"] == "low"

    assert "consultancy" in (
        result["matched_signals"]
    )


# ============================================================
# DEPARTMENT DIRECTORY
# ============================================================

def test_department_directory_does_not_become_facility():
    """
    Infrastructure-related department names should not turn a
    department directory into a facility record.
    """

    result = make_engine().analyze(
        record_heading="Departments",
        record_text=(
            "Aerospace Engineering\n"
            "Bioscience and Bioengineering\n"
            "Computer Science and Engineering\n"
            "Civil and Infrastructure Engineering"
        ),
    )

    assert result["primary_type"] == "unknown"


# ============================================================
# OFFICE DIRECTORY
# ============================================================

def test_office_directory_does_not_become_facility():
    """
    Office pages can mention facilities/infrastructure without being
    facility pages.
    """

    result = make_engine().analyze(
        record_heading="Offices",
        record_text=(
            "Office of Director\n"
            "Office of Deputy Director\n"
            "Office of Registrar\n"
            "Office of Administration\n"
            "Infrastructure and facilities information."
        ),
    )

    assert result["primary_type"] == "unknown"


# ============================================================
# EVENT
# ============================================================

def test_workshop_record_is_detected_from_record_content():
    result = make_engine().analyze(
        record_heading="Academic Events",
        record_text=(
            "Two-day international workshop "
            "on artificial intelligence."
        ),
    )

    assert result["primary_type"] == "workshop"

    assert result["confidence"] == "high"


def test_conference_event_is_detected():
    result = make_engine().analyze(
        record_heading="Event",
        record_text=(
            "International Conference on Applied "
            "Materials and Devices."
        ),
        section_context=[
            "Events",
        ],
        document_title="Institute Events",
    )

    assert result["primary_type"] == "symposia"


# ============================================================
# FELLOWSHIP
# ============================================================

def test_fellowship_record_is_detected():
    result = make_engine().analyze(
        record_heading="Research Fellowship",
        record_text=(
            "Doctoral fellowship supporting research "
            "in renewable energy."
        ),
    )

    assert result["primary_type"] == "fellowship"


# ============================================================
# TRAVEL
# ============================================================

def test_travel_record_is_detected():
    result = make_engine().analyze(
        record_heading="Travel Support",
        record_text=(
            "International Travel Support for attending "
            "an academic research conference."
        ),
    )

    assert result["primary_type"] == "travel"


# ============================================================
# MIXED SIGNALS
# ============================================================

def test_multiple_record_level_signals_are_preserved():
    result = make_engine().analyze(
        record_heading="Research Fellowship",
        record_text=(
            "Fellowship project supporting a "
            "sponsored research project."
        ),
    )

    assert result["primary_type"] in {
        "fellowship",
        "research",
    }

    assert result["secondary_types"]

    assert "fellowship" in (
        result["matched_signals"]
    )

    assert (
        "sponsored research project"
        in result["matched_signals"]
    )


# ============================================================
# DOCUMENT CONTEXT MUST REMAIN WEAK
# ============================================================

def test_document_context_alone_does_not_classify_record():
    """
    A document titled "Research Projects" must not automatically turn
    arbitrary record content into research.
    """

    result = make_engine().analyze(
        record_heading="General Information",
        record_text=(
            "The institute provides academic and "
            "student services across multiple areas."
        ),
        document_title="Research Projects",
    )

    assert result["primary_type"] == "unknown"


# ============================================================
# DETERMINISM
# ============================================================

def test_same_input_is_deterministic():
    engine = make_engine()

    first = engine.analyze(
        record_heading="Consultancy Project",
        record_text=(
            "Technical consultancy for an external "
            "industry partner."
        ),
        section_context=[
            "External Engagement",
        ],
        document_title="Institutional Activities",
    )

    second = engine.analyze(
        record_heading="Consultancy Project",
        record_text=(
            "Technical consultancy for an external "
            "industry partner."
        ),
        section_context=[
            "External Engagement",
        ],
        document_title="Institutional Activities",
    )

    assert first == second


# ============================================================
# CONTRACT
# ============================================================

def test_result_contract():
    result = make_engine().analyze(
        record_heading="Consultancy Project",
        record_text=(
            "Technical consultancy for an external "
            "organization."
        ),
    )

    assert set(
        result.keys()
    ) == {
        "primary_type",
        "secondary_types",
        "confidence",
        "matched_signals",
    }

    assert isinstance(
        result["primary_type"],
        str,
    )

    assert isinstance(
        result["secondary_types"],
        list,
    )

    assert isinstance(
        result["confidence"],
        str,
    )

    assert isinstance(
        result["matched_signals"],
        list,
    )