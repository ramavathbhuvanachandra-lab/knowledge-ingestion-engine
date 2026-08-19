"""
Command 3 — Knowledge Value Filter Tests.

These tests encode the actual chatbot knowledge policy.

The goal is to protect valuable institutional knowledge while
removing/consolidating genuinely low-value bulk records.
"""

from processors.knowledge_value_filter import (
    CONSOLIDATE,
    EXCLUDE,
    KEEP,
    REVIEW,
    KnowledgeValueFilter,
)


def test_vision_and_mission_is_kept():
    result = KnowledgeValueFilter().classify(
        heading="Vision and Mission",
        text=(
            "The institute aims to create an environment "
            "for education, research and innovation."
        ),
    )

    assert result["decision"] == KEEP


def test_message_from_head_is_kept():
    result = KnowledgeValueFilter().classify(
        heading="Message from the Head",
        text=(
            "Welcome to the Department of Electrical Engineering. "
            "Our department is committed to education and research."
        ),
    )

    assert result["decision"] == KEEP


def test_highlights_are_excluded_as_volatile():
    result = KnowledgeValueFilter().classify(
        heading="Highlights",
        text=(
            "The institute has established several new "
            "academic and research initiatives."
        ),
    )

    assert result["decision"] == EXCLUDE

def test_faculty_information_is_kept():
    result = KnowledgeValueFilter().classify(
        heading="Faculty Members",
        text=(
            "The department has faculty members working "
            "in power systems, VLSI and signal processing."
        ),
    )

    assert result["decision"] == KEEP


def test_research_areas_are_kept():
    result = KnowledgeValueFilter().classify(
        heading="Research Areas",
        text=(
            "Research areas include power systems, "
            "embedded systems, signal processing and VLSI."
        ),
    )

    assert result["decision"] == KEEP


def test_research_centres_are_kept():
    result = KnowledgeValueFilter().classify(
        heading="Research Centre",
        text=(
            "The centre supports interdisciplinary research "
            "and advanced research infrastructure."
        ),
    )

    assert result["decision"] == KEEP


def test_department_overview_is_kept():
    result = KnowledgeValueFilter().classify(
        heading="Department Overview",
        text=(
            "The department offers undergraduate and "
            "postgraduate education and conducts research."
        ),
    )

    assert result["decision"] == KEEP


def test_student_batch_list_is_excluded():
    result = KnowledgeValueFilter().classify(
        heading="Batch 2024 Student List",
        text=(
            "Student Name: Rahul Kumar | "
            "Roll Number: B24EE1001 | "
            "Batch: 2024 | "
            "Email: rahul@example.com"
        ),
    )

    assert result["decision"] == EXCLUDE


def test_alumni_directory_is_excluded():
    result = KnowledgeValueFilter().classify(
        heading="Alumni Directory",
        text=(
            "Name: Rahul Kumar | "
            "Graduation Year: 2020 | "
            "Company: ABC Corp | "
            "Location: Bengaluru"
        ),
    )

    assert result["decision"] == EXCLUDE


def test_individual_project_record_is_consolidated():
    result = KnowledgeValueFilter().classify(
        heading="Research Project",
        text=(
            "Project Title: Smart Grid Optimization. "
            "Student: Rahul Kumar. "
            "Batch: 2024. "
            "Supervisor: Professor X. "
            "Project details are available in the student record."
        ),
    )

    assert result["decision"] in {
        CONSOLIDATE,
        EXCLUDE,
    }


def test_institutional_research_is_not_excluded():
    result = KnowledgeValueFilter().classify(
        heading="Research Areas",
        text=(
            "The department conducts research in power systems, "
            "renewable energy, smart grids and embedded systems."
        ),
    )

    assert result["decision"] == KEEP


def test_short_important_content_is_not_deleted():
    result = KnowledgeValueFilter().classify(
        heading="Emergency Contact",
        text="Campus emergency services: 100.",
    )

    assert result["decision"] != EXCLUDE


def test_unknown_substantive_content_is_preserved():
    result = KnowledgeValueFilter().classify(
        heading="Special Initiative",
        text=(
            "The institute launched a new interdisciplinary "
            "initiative to support collaboration between "
            "academic departments and external organizations."
        ),
    )

    assert result["decision"] in {
        KEEP,
        REVIEW,
    }

def test_department_highlights_are_excluded_as_volatile():
    result = KnowledgeValueFilter().classify(
        heading="Department Highlights",
        text=(
            "The department has expanded its research "
            "facilities and introduced new academic programs. "
            "The department also maintains records of students "
            "from the 2024 batch."
        ),
    )

    assert result["decision"] == EXCLUDE

def test_obvious_navigation_is_excluded():
    result = KnowledgeValueFilter().classify(
        heading="Rate this translation",
        text="Rate this translation",
    )

    assert result["decision"] == EXCLUDE


def test_accessibility_ui_is_excluded():
    result = KnowledgeValueFilter().classify(
        heading="Accessibility Options",
        text="Enable accessibility options",
        content_type="accessibility",
    )

    assert result["decision"] == EXCLUDE