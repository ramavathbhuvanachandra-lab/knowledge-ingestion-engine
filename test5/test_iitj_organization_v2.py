"""
IITJ Final Command 5 Organizer Tests
"""

from pathlib import Path

from processors_v2.knowledge_organization_iitj_v2 import (
    IITJKnowledgeOrganizerV2,
)


def unit(
    unit_id,
    heading,
    text,
    tier="A",
    source_file="iitj.json",
    source_url="https://www.iitj.ac.in/test",
):
    return {
        "unit_id": unit_id,
        "heading": heading,
        "text": text,
        "tier": tier,
        "source_file": source_file,
        "source_url": source_url,
    }


def paths(plan):
    return {
        document["path"]
        for document in plan["documents"]
    }


def test_new_department_entities_are_supported():
    units = [
        unit("e1", "Welcome to the Department of Electronics Engineering",
             "Department overview."),
        unit("e2", "Faculty", "Electronics faculty.",
             source_file="electronics_engineering.json"),
        unit("e3", "Research Areas", "Electronics research.",
             source_file="electronics_engineering.json"),
    ]
    plan = IITJKnowledgeOrganizerV2().build_plan(units)
    result = paths(plan)

    assert "departments/electronics_engineering/overview.md" in result
    assert "departments/electronics_engineering/faculty.md" in result
    assert "departments/electronics_engineering/research.md" in result


def test_school_is_not_treated_as_department():
    units = [
        unit("s1", "Welcome to School of Design",
             "Design school overview."),
        unit("s2", "M.Des Program", "M.Des in Smart Product Design."),
    ]
    plan = IITJKnowledgeOrganizerV2().build_plan(units)
    result = paths(plan)

    assert "schools/design/overview.md" in result
    assert "schools/design/programs.md" in result
    assert not any(
        path.startswith("departments/design/")
        for path in result
    )


def test_research_platform_has_own_entity_family():
    units = [
        unit(
            "q1",
            "Quantum Information and Computation",
            "Research platform information.",
        )
    ]
    plan = IITJKnowledgeOrganizerV2().build_plan(units)
    assert (
        "research_platforms/quantum_information_and_computation/research.md"
        in paths(plan)
    )


def test_offices_have_own_entity_family():
    units = [
        unit(
            "o1",
            "Welcome to Office of Accounts",
            "Accounts and financial management services.",
        )
    ]
    plan = IITJKnowledgeOrganizerV2().build_plan(units)
    assert (
        "offices_and_administration/office_of_accounts/overview.md"
        in paths(plan)
    )


def test_admission_beats_program():
    units = [
        unit(
            "a1",
            "Admission to M.Tech Program",
            "M.Tech admission eligibility.",
        )
    ]
    plan = IITJKnowledgeOrganizerV2().build_plan(units)
    assert (
        "admissions/mtech_admissions.md"
        in paths(plan)
    )


def test_btech_program_entity():
    units = [
        unit(
            "b1",
            "B.Tech Curriculum",
            "B.Tech curriculum details.",
        )
    ]
    plan = IITJKnowledgeOrganizerV2().build_plan(units)
    assert (
        "programs/btech/curriculum.md"
        in paths(plan)
    )


def test_hostel_small_topic_stays_together():
    units = [
        unit("h1", "Accommodation", "Hostel accommodation."),
        unit("h2", "Hostel Rules", "Hostel rules."),
        unit("h3", "Dining", "Dining facilities."),
    ]
    plan = IITJKnowledgeOrganizerV2().build_plan(units)
    assert paths(plan) == {
        "hostel_accommodation/general_information.md"
    }


def test_training_is_separate_from_degree_programs():
    units = [
        unit(
            "t1",
            "Specialized Training in Government e-Marketplace",
            "Two-day professional training program.",
        )
    ]
    plan = IITJKnowledgeOrganizerV2().build_plan(units)
    assert (
        "training_and_upskilling/training.md"
        in paths(plan)
    )


def test_health_facility_is_not_generic_infrastructure_only():
    units = [
        unit(
            "h1",
            "Welcome To The Health Center, IIT Jodhpur",
            "Round-the-clock health care facilities.",
        )
    ]
    plan = IITJKnowledgeOrganizerV2().build_plan(units)
    assert (
        "research_and_technology_facilities/facilities.md"
        in paths(plan)
    )


def test_unknown_content_goes_to_named_buffer():
    units = [
        unit(
            "x1",
            "Rare IITJ Topic",
            "Legitimate institutional content not covered by a known family.",
        )
    ]
    plan = IITJKnowledgeOrganizerV2().build_plan(units)

    assert (
        "fallback/knowledge_buffer_general.md"
        in paths(plan)
    )


def test_lossless_assignment():
    units = [
        unit("a1", "B.Tech Curriculum", "Curriculum"),
        unit("a2", "Office of Accounts", "Finance office"),
        unit("a3", "Department of Economics", "Economics department"),
        unit("a4", "Unknown Topic", "Valid content"),
    ]
    plan = IITJKnowledgeOrganizerV2().build_plan(units)

    assigned = [
        unit_id
        for document in plan["documents"]
        for unit_id in document["unit_ids"]
    ]

    assert sorted(assigned) == sorted(
        item["unit_id"]
        for item in units
    )
    assert len(assigned) == len(set(assigned))


def test_deterministic():
    units = [
        unit("d1", "Office of Registrar", "Registrar information"),
        unit("d2", "M.Tech Curriculum", "M.Tech curriculum"),
        unit("d3", "Electrical Engineering Faculty", "EE faculty"),
    ]

    organizer = IITJKnowledgeOrganizerV2()

    first = organizer.build_plan(units)
    second = organizer.build_plan(list(reversed(units)))

    assert first == second