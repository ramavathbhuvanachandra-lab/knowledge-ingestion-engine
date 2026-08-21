"""
Command 4 V2 — Adversarial semantic regression tests.

These tests deliberately target failure modes exposed by real IITJ smoke data:
- broad "academics" catch-all documents
- overview contamination
- department committee contamination
- body-text keyword leakage
- cross-family semantic routing
- dynamic department structure
- large-topic splitting without part_1/part_2 files
- preservation of small coherent areas
- single unknown topics
"""

import json
from pathlib import Path

import pytest

from processors.knowledge_organization_v2 import Command4OrganizationV2


def unit(unit_id, heading, text, family, tier="A", **extra):
    return {
        "unit_id": unit_id,
        "heading": heading,
        "text": text,
        "knowledge_family": family,
        "tier": tier,
        "source_file": f"{unit_id}.json",
        "source_url": f"https://example.edu/{unit_id}",
        **extra,
    }


def paths(plan):
    return {
        document["path"]
        for document in plan["documents"]
    }


def test_academics_mixed_topics_do_not_become_one_generic_file():
    units = [
        unit(
            "ac1",
            "2. Academic Session",
            "Academic calendar and semester schedule.",
            "Academics",
        ),
        unit(
            "ac2",
            "3. Registration",
            "Registration rules and deadlines.",
            "Academics",
        ),
        unit(
            "ac3",
            "11.5 Academic Performance Requirements",
            "Continuation criteria.",
            "Academics",
        ),
        unit(
            "ac4",
            "15.4 Academic Leave",
            "Academic leave policy.",
            "Academics",
        ),
        unit(
            "ac5",
            "16. Branch Change",
            "Branch change procedure.",
            "Academics",
        ),
    ]

    plan = Command4OrganizationV2().build_plan(
        domain="future.edu",
        units=units,
    )

    result = paths(plan)

    assert len(result) >= 3, result
    assert "academics/academics.md" not in result


def test_academics_sections_remain_semantically_separated():
    units = [
        unit(
            "as1",
            "11.5 Academic Performance Requirements",
            "Minimum credits for continuation.",
            "Academics",
        ),
        unit(
            "as2",
            "23.4 Academic Leave",
            "Leave for academic purposes.",
            "Academics",
        ),
        unit(
            "as3",
            "26.6 Candidacy for the Ph.D. Degree",
            "Candidacy requirements.",
            "Academics",
        ),
        unit(
            "as4",
            "4.1.7 Teaching Assignments",
            "Teaching allocation rules.",
            "Academics",
        ),
    ]

    plan = Command4OrganizationV2().build_plan(
        domain="future.edu",
        units=units,
    )

    result = paths(plan)

    assert len(result) >= 3, result


def test_overview_family_does_not_absorb_procedural_registration():
    units = [
        unit(
            "ov1",
            "1. Introduction",
            "About the institution.",
            "Institute / College Overview",
        ),
        unit(
            "ov2",
            "3.1 Provisional Registration",
            "Students complete provisional registration.",
            "Institute / College Overview",
        ),
        unit(
            "ov3",
            "17.6.1 Provisional Certificate",
            "Certificate issued after requirements are met.",
            "Institute / College Overview",
        ),
    ]

    plan = Command4OrganizationV2().build_plan(
        domain="future.edu",
        units=units,
    )

    result = paths(plan)

    assert "institute_overview/overview.md" in result
    assert len(result) >= 2, result


def test_department_committee_does_not_become_department_overview():
    units = [
        unit(
            "dc1",
            "Department of Commerce",
            "Commerce department overview.",
            "Departments / Schools / Branches",
            entity="Commerce",
            entity_type="department",
        ),
        unit(
            "dc2",
            "13.2 Composition of Department Undergraduate Committee",
            "Committee composition and membership.",
            "Departments / Schools / Branches",
            entity="Commerce",
            entity_type="department",
        ),
    ]

    plan = Command4OrganizationV2().build_plan(
        domain="future.edu",
        units=units,
    )

    result = paths(plan)

    assert "departments/commerce/overview.md" in result
    assert len(result) >= 2, result


def test_body_keywords_do_not_reroute_faculty_domain():
    units = [
        unit(
            "bk1",
            "Faculty Development Program",
            (
                "This programme discusses examination procedures, "
                "laboratory facilities, and infrastructure."
            ),
            "Faculty / HOD / Dean / Key People",
        ),
    ]

    plan = Command4OrganizationV2().build_plan(
        domain="future.edu",
        units=units,
    )

    assert paths(plan) == {
        "faculty/faculty.md"
    }


def test_body_keywords_do_not_reroute_institute_overview():
    units = [
        unit(
            "bk2",
            "About the College",
            (
                "The college has laboratories, hostels, "
                "admission procedures, and research facilities."
            ),
            "Institute / College Overview",
        ),
    ]

    plan = Command4OrganizationV2().build_plan(
        domain="future.edu",
        units=units,
    )

    assert paths(plan) == {
        "institute_overview/overview.md"
    }


def test_admission_heading_overrides_broad_program_family():
    units = [
        unit(
            "ad1",
            "M.Tech Admissions",
            "Eligibility and application requirements.",
            "Programs & Courses",
        ),
    ]

    plan = Command4OrganizationV2().build_plan(
        domain="future.edu",
        units=units,
    )

    assert paths(plan) == {
        "admissions/mtech_admissions.md"
    }


def test_same_semantic_topic_from_multiple_families_has_one_root():
    units = [
        unit(
            "ad2",
            "M.Tech Admissions",
            "Admissions information.",
            "Admissions",
        ),
        unit(
            "ad3",
            "M.Tech Admissions",
            "Admission requirements.",
            "Programs & Courses",
        ),
    ]

    plan = Command4OrganizationV2().build_plan(
        domain="future.edu",
        units=units,
    )

    result = paths(plan)

    assert len(result) == 1, result
    assert next(iter(result)).startswith(
        "admissions/"
    )


def test_financial_assistance_stays_out_of_fees():
    units = [
        unit(
            "fa1",
            "Financial Assistance",
            "Assistantship and financial support.",
            "Scholarships / Financial Aid",
        ),
    ]

    plan = Command4OrganizationV2().build_plan(
        domain="future.edu",
        units=units,
    )

    result = paths(plan)

    assert result == {
        "scholarships_financial_aid/assistantship_and_fellowship.md"
    }


def test_small_faculty_domain_remains_one_document():
    units = [
        unit(
            "sf1",
            "Faculty",
            "Professor A.",
            "Faculty / HOD / Dean / Key People",
        ),
        unit(
            "sf2",
            "Professor",
            "Professor B.",
            "Faculty / HOD / Dean / Key People",
        ),
        unit(
            "sf3",
            "Contact",
            "Faculty contact details.",
            "Faculty / HOD / Dean / Key People",
        ),
    ]

    plan = Command4OrganizationV2().build_plan(
        domain="future.edu",
        units=units,
    )

    assert paths(plan) == {
        "faculty/faculty.md"
    }


def test_small_hostel_domain_remains_one_document():
    units = [
        unit(
            "sh1",
            "Accommodation",
            "Hostel accommodation is available.",
            "Hostel / Accommodation",
        ),
        unit(
            "sh2",
            "Hostel Rules",
            "Students must follow hostel rules.",
            "Hostel / Accommodation",
        ),
        unit(
            "sh3",
            "Dining",
            "Dining facilities are available.",
            "Hostel / Accommodation",
        ),
    ]

    plan = Command4OrganizationV2().build_plan(
        domain="future.edu",
        units=units,
    )

    assert paths(plan) == {
        "hostel_accommodation/accommodation.md"
    }


def test_large_topic_splits_without_part_files():
    units = [
        unit(
            f"lg{i}",
            f"{i}. Topic {i}",
            " ".join(
                ["content"] * 3000
            ),
            "Academics",
        )
        for i in range(1, 5)
    ]

    plan = Command4OrganizationV2().build_plan(
        domain="future.edu",
        units=units,
    )

    result = paths(plan)

    assert len(result) >= 2, result
    assert not any(
        "part_" in path
        for path in result
    )


def test_department_structure_is_dynamic():
    units = [
        unit(
            "dd1",
            "Department of Economics",
            "Economics department overview.",
            "Departments / Schools / Branches",
            entity="Economics",
            entity_type="department",
        ),
        unit(
            "dd2",
            "Faculty",
            "Economics faculty.",
            "Faculty / HOD / Dean / Key People",
            entity="Economics",
            entity_type="department",
        ),
        unit(
            "dd3",
            "Research Areas",
            "Economics research areas.",
            "Relevant Institutional Research",
            entity="Economics",
            entity_type="department",
        ),
    ]

    plan = Command4OrganizationV2().build_plan(
        domain="future.edu",
        units=units,
    )

    assert paths(plan) == {
        "departments/economics/overview.md",
        "departments/economics/faculty.md",
        "departments/economics/research.md",
    }


def test_unknown_semantic_topic_gets_one_stable_document():
    units = [
        unit(
            "uk1",
            "Special Initiative",
            "Institutional initiative details.",
            "Other Institutional Information",
        ),
    ]

    plan = Command4OrganizationV2().build_plan(
        domain="future.edu",
        units=units,
    )

    result = paths(plan)

    assert len(result) == 1
    assert next(iter(result))


def test_all_adversarial_units_remain_lossless(tmp_path: Path):
    units = [
        unit(
            "loss1",
            "Academic Leave",
            "Original academic leave content.",
            "Academics",
        ),
        unit(
            "loss2",
            "M.Tech Admissions",
            "Original admission content.",
            "Admissions",
        ),
        unit(
            "loss3",
            "Faculty",
            "Original faculty content.",
            "Faculty / HOD / Dean / Key People",
        ),
    ]

    manifest = Command4OrganizationV2().write_output(
        domain="future.edu",
        units=units,
        output_root=tmp_path,
    )

    assert manifest["coverage"]["missing_unit_ids"] == []
    assert manifest["coverage"]["unassigned_unit_ids"] == []
    assert manifest["coverage"]["duplicate_unit_ids"] == []
    assert manifest["coverage"]["extra_unit_ids"] == []
    assert manifest["unit_count"] == len(units)