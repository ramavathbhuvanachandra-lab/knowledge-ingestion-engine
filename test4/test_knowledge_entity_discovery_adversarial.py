"""
Adversarial tests for universal knowledge entity discovery.

Purpose
-------
Test entity discovery against realistic college-website patterns
before changing production discovery logic.

These tests intentionally include:
    - valid academic schools
    - departments
    - facilities
    - offices
    - programs
    - degrees
    - research centres
    - noisy website text
    - navigation fragments
    - incomplete declarations
    - dynamic/news content

Important:
    These tests do NOT assume IITJ-specific entities.
"""

from __future__ import annotations

from processors.knowledge_entity_discovery import (
    KnowledgeEntityDiscovery,
    DEPARTMENT,
    SCHOOL,
    PROGRAM,
    DEGREE,
    RESEARCH_CENTRE,
    FACILITY,
    OFFICE,
)


# ============================================================
# HELPERS
# ============================================================


def _discover(
    sections: list[dict],
) -> dict:

    documents = [
        {
            "source": "test",
            "title": "Test College",
            "url": "https://example.edu",
            "sections": sections,
        }
    ]

    return KnowledgeEntityDiscovery().discover(
        documents=documents
    )


def _entities(
    result: dict,
) -> list[dict]:

    return result["entities"]


def _has_entity(
    result: dict,
    *,
    name: str,
    entity_type: str,
) -> bool:

    normalized = (
        KnowledgeEntityDiscovery.normalize_name(
            name
        )
    )

    return any(
        entity["normalized_name"] == normalized
        and entity["entity_type"] == entity_type
        for entity in _entities(result)
    )


# ============================================================
# SCHOOLS
# ============================================================


def test_discovers_school_of_liberal_arts():

    result = _discover(
        [
            {
                "heading": "School of Liberal Arts",
                "text": (
                    "The school offers interdisciplinary "
                    "programs in humanities and social sciences."
                ),
            }
        ]
    )

    assert _has_entity(
        result,
        name="Liberal Arts",
        entity_type=SCHOOL,
    )


def test_discovers_school_of_ai_and_data_science():

    result = _discover(
        [
            {
                "heading": (
                    "School of Artificial Intelligence "
                    "and Data Science"
                ),
                "text": (
                    "The school provides academic programs "
                    "in artificial intelligence and data science."
                ),
            }
        ]
    )

    assert _has_entity(
        result,
        name=(
            "Artificial Intelligence and Data Science"
        ),
        entity_type=SCHOOL,
    )


def test_discovers_school_of_management():

    result = _discover(
        [
            {
                "heading": "School of Management",
                "text": (
                    "The school offers management education "
                    "and professional programs."
                ),
            }
        ]
    )

    assert _has_entity(
        result,
        name="Management",
        entity_type=SCHOOL,
    )


# ============================================================
# DEPARTMENTS
# ============================================================


def test_discovers_department_of_electrical_engineering():

    result = _discover(
        [
            {
                "heading": (
                    "Department of Electrical Engineering"
                ),
                "text": (
                    "The department offers undergraduate "
                    "and postgraduate programs."
                ),
            }
        ]
    )

    assert _has_entity(
        result,
        name="Electrical Engineering",
        entity_type=DEPARTMENT,
    )


def test_discovers_department_from_text():

    result = _discover(
        [
            {
                "heading": "Academics",
                "text": (
                    "The Department of Computer Science "
                    "and Engineering offers several programs."
                ),
            }
        ]
    )

    assert _has_entity(
        result,
        name="Computer Science and Engineering",
        entity_type=DEPARTMENT,
    )


# ============================================================
# FACILITIES
# ============================================================


def test_discovers_central_laboratory():

    result = _discover(
        [
            {
                "heading": "Central Laboratory",
                "text": (
                    "The laboratory provides advanced "
                    "research facilities."
                ),
            }
        ]
    )

    assert _has_entity(
        result,
        name="Central Laboratory",
        entity_type=FACILITY,
    )


def test_discovers_advanced_materials_laboratory():

    result = _discover(
        [
            {
                "heading": "Advanced Materials Laboratory",
                "text": (
                    "The laboratory supports advanced "
                    "materials research."
                ),
            }
        ]
    )

    assert _has_entity(
        result,
        name="Advanced Materials Laboratory",
        entity_type=FACILITY,
    )


def test_discovers_laboratory_for_renewable_energy():

    result = _discover(
        [
            {
                "heading": (
                    "Laboratory for Renewable Energy"
                ),
                "text": (
                    "The facility supports renewable "
                    "energy research."
                ),
            }
        ]
    )

    assert _has_entity(
        result,
        name="Laboratory for Renewable Energy",
        entity_type=FACILITY,
    )


# ============================================================
# OFFICES
# ============================================================


def test_discovers_office_of_dean():

    result = _discover(
        [
            {
                "heading": "Office of the Dean",
                "text": (
                    "The Dean oversees academic "
                    "administration."
                ),
            }
        ]
    )

    assert any(
        entity["entity_type"] == OFFICE
        for entity in _entities(result)
    )


def test_discovers_registrar():

    result = _discover(
        [
            {
                "heading": "Registrar",
                "text": (
                    "The Registrar is responsible for "
                    "official academic records."
                ),
            }
        ]
    )

    assert any(
        entity["entity_type"] == OFFICE
        for entity in _entities(result)
    )


# ============================================================
# PROGRAMS
# ============================================================


def test_discovers_program_heading():

    result = _discover(
        [
            {
                "heading": (
                    "B.Tech Computer Science Program"
                ),
                "text": (
                    "The program provides undergraduate "
                    "education in computer science."
                ),
            }
        ]
    )

    assert any(
        entity["entity_type"] in {
            PROGRAM,
            DEGREE,
        }
        for entity in _entities(result)
    )


# ============================================================
# DEGREES
# ============================================================


def test_discovers_btech():

    result = _discover(
        [
            {
                "heading": "Academic Programs",
                "text": (
                    "The institute offers B.Tech programs "
                    "in several disciplines."
                ),
            }
        ]
    )

    assert any(
        entity["entity_type"] == DEGREE
        and "b tech" in entity["normalized_name"]
        for entity in _entities(result)
    )


def test_discovers_mba():

    result = _discover(
        [
            {
                "heading": "Management Education",
                "text": (
                    "The institute offers MBA programs."
                ),
            }
        ]
    )

    assert any(
        entity["entity_type"] == DEGREE
        and entity["normalized_name"] == "mba"
        for entity in _entities(result)
    )


# ============================================================
# RESEARCH CENTRES
# ============================================================


def test_discovers_research_centre():

    result = _discover(
        [
            {
                "heading": (
                    "Research Centre for Clean Energy"
                ),
                "text": (
                    "The centre conducts interdisciplinary "
                    "research in clean energy."
                ),
            }
        ]
    )

    assert any(
        entity["entity_type"] == RESEARCH_CENTRE
        for entity in _entities(result)
    )


# ============================================================
# GARBAGE / FALSE POSITIVES
# ============================================================


def test_does_not_create_entity_from_random_id():

    result = _discover(
        [
            {
                "heading": 'id="cqz324"',
                "text": (
                    'id="13oxk9" class="menu-item" '
                    'data-target="abc123"'
                ),
            }
        ]
    )

    assert not any(
        entity["name"].lower()
        in {
            "cqz324",
            "13oxk9",
            "abc123",
        }
        for entity in _entities(result)
    )


def test_does_not_create_school_from_incomplete_heading():

    result = _discover(
        [
            {
                "heading": "School of",
                "text": (
                    "Academic information is available "
                    "on this page."
                ),
            }
        ]
    )

    assert not any(
        entity["entity_type"] == SCHOOL
        for entity in _entities(result)
    )


def test_does_not_create_department_from_incomplete_heading():

    result = _discover(
        [
            {
                "heading": "Department of",
                "text": (
                    "Information about the institute."
                ),
            }
        ]
    )

    assert not any(
        entity["entity_type"] == DEPARTMENT
        for entity in _entities(result)
    )


def test_does_not_create_entity_from_news_heading():

    result = _discover(
        [
            {
                "heading": "Latest News",
                "text": (
                    "Department of Electrical Engineering "
                    "won an award this week."
                ),
            }
        ]
    )

    # Entity discovery may legitimately find the department
    # from strong textual evidence, but the news heading itself
    # must not become an entity.
    assert not any(
        entity["normalized_name"] == "latest news"
        for entity in _entities(result)
    )


# ============================================================
# POSITION HOLDERS / OFFICIAL INFORMATION
# ============================================================


def test_position_holder_page_can_preserve_office_entity():

    result = _discover(
        [
            {
                "heading": "Dean",
                "text": (
                    "Dr. Example Name is the Dean of the "
                    "School of Engineering. "
                    "Email: dean@example.edu"
                ),
            }
        ]
    )

    assert any(
        entity["entity_type"] == OFFICE
        for entity in _entities(result)
    )


# ============================================================
# MIXED REALISTIC PAGE
# ============================================================


def test_mixed_college_page_discovers_multiple_entity_types():

    result = _discover(
        [
            {
                "heading": (
                    "School of Engineering"
                ),
                "text": (
                    "The Department of Electrical Engineering "
                    "offers B.Tech and M.Tech programs. "
                    "The Central Laboratory supports research."
                ),
            }
        ]
    )

    types = {
        entity["entity_type"]
        for entity in _entities(result)
    }

    assert SCHOOL in types
    assert DEPARTMENT in types
    assert DEGREE in types
    assert FACILITY in types


# ============================================================
# ENTITY NAME PRESERVATION
# ============================================================


def test_entity_name_is_not_replaced_by_generic_label():

    result = _discover(
        [
            {
                "heading": (
                    "Advanced Computing Facility"
                ),
                "text": (
                    "The facility provides high-performance "
                    "computing resources."
                ),
            }
        ]
    )

    assert _has_entity(
        result,
        name="Advanced Computing Facility",
        entity_type=FACILITY,
    )


# ============================================================
# REPETITION / AGGREGATION
# ============================================================


def test_repeated_school_mentions_are_aggregated():

    result = _discover(
        [
            {
                "heading": "School of Management",
                "text": (
                    "The School of Management offers "
                    "management education."
                ),
            },
            {
                "heading": "About the School",
                "text": (
                    "The School of Management provides "
                    "academic programs."
                ),
            },
        ]
    )

    matching = [
        entity
        for entity in _entities(result)
        if (
            entity["entity_type"] == SCHOOL
            and entity["normalized_name"]
            == "management"
        )
    ]

    assert matching
    assert matching[0]["mention_count"] >= 2