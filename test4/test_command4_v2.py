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


def test_small_hostel_stays_one_document():
    units = [
        unit("h1", "Accommodation", "Hostels are available for students.", "Hostel / Accommodation"),
        unit("h2", "Hostel Rules", "Students must follow hostel rules.", "Hostel / Accommodation"),
        unit("h3", "Dining", "Dining facilities are available.", "Hostel / Accommodation"),
    ]

    plan = Command4OrganizationV2().build_plan(domain="small.edu", units=units)
    assert plan["document_count"] == 1
    assert plan["documents"][0]["path"] == "hostel_accommodation/accommodation.md"


def test_department_topics_are_grouped_under_department_folder():
    units = [
        unit("e1", "Overview", "Electrical Engineering department overview.", "Departments / Schools / Branches", entity="Electrical Engineering", entity_type="department"),
        unit("e2", "Faculty", "Faculty information.", "Faculty / HOD / Dean / Key People", entity="Electrical Engineering", entity_type="department"),
        unit("e3", "Research Areas", "Research information.", "Relevant Institutional Research", entity="Electrical Engineering", entity_type="department"),
        unit("e4", "Facilities", "Laboratory information.", "Infrastructure / Facilities", entity="Electrical Engineering", entity_type="department"),
    ]

    plan = Command4OrganizationV2().build_plan(domain="iitj.ac.in", units=units)
    paths = {doc["path"] for doc in plan["documents"]}
    assert paths == {
        "departments/electrical_engineering/faculty.md",
        "departments/electrical_engineering/research.md",
        "departments/electrical_engineering/facilities.md",
        "departments/electrical_engineering/overview.md",
    }


def test_admissions_can_split_by_real_program_boundaries():
    units = [
        unit("a1", "B.Tech Admissions", "Undergraduate admission requirements.", "Admissions", entity="Admissions", entity_type="service"),
        unit("a2", "M.Tech Admissions", "Postgraduate admission requirements.", "Admissions", entity="Admissions", entity_type="service"),
        unit("a3", "MBA Admissions", "MBA admission requirements.", "Admissions", entity="Admissions", entity_type="service"),
        unit("a4", "B.Com Admissions", "B.Com admission requirements.", "Admissions", entity="Admissions", entity_type="service"),
    ]
    plan = Command4OrganizationV2().build_plan(domain="college.edu", units=units)
    paths = {doc["path"] for doc in plan["documents"]}
    assert len(paths) == 4
    assert "admissions/btech_admissions.md" in paths
    assert "admissions/mtech_admissions.md" in paths
    assert "admissions/mba_admissions.md" in paths
    assert "admissions/bcom_admissions.md" in paths


def test_c_and_d_are_rejected_before_any_folder_is_created():
    units = [
        unit("c1", "Activities", "Legitimate but lower priority.", "Other Institutional Information", tier="C"),
    ]
    with pytest.raises(ValueError, match="Only A/B/REVIEW are allowed"):
        Command4OrganizationV2().build_plan(domain="college.edu", units=units)


def test_rejected_empty_units_are_not_silently_written():
    units = [
        unit("x1", "Faculty", "", "Faculty / HOD / Dean / Key People"),
    ]
    with pytest.raises(ValueError, match="no content"):
        Command4OrganizationV2().build_plan(domain="college.edu", units=units)


def test_deterministic_for_same_input():
    units = [
        unit("u1", "Faculty", "A", "Faculty / HOD / Dean / Key People", entity="Computer Science", entity_type="department"),
        unit("u2", "Research", "B", "Relevant Institutional Research", entity="Computer Science", entity_type="department"),
    ]
    organizer = Command4OrganizationV2()
    plan1 = organizer.build_plan(domain="college.edu", units=units)
    plan2 = organizer.build_plan(domain="college.edu", units=units)
    assert plan1 == plan2


def test_write_output_contains_json_and_markdown(tmp_path: Path):
    units = [
        unit("u1", "Faculty", "Professor A", "Faculty / HOD / Dean / Key People", entity="Electrical Engineering", entity_type="department", source_lines="12-17"),
    ]
    manifest = Command4OrganizationV2().write_output(
        domain="iitj.ac.in",
        units=units,
        output_root=tmp_path,
    )

    root = tmp_path / "iitj_ac_in"
    assert (root / "organization_plan.json").exists()
    assert (root / "organization_manifest.json").exists()
    md = root / "departments" / "electrical_engineering" / "faculty.md"
    assert md.exists()
    content = md.read_text(encoding="utf-8")
    assert "id:" in content
    assert "title:" in content
    assert "source_files:" in content
    assert "source_urls:" in content
    assert "Professor A" in content
    assert manifest["coverage"]["unassigned_unit_ids"] == []


def test_mixed_college_structure_has_no_fixed_iitj_categories():
    units = [
        unit("g1", "College Overview", "Commerce-focused institution.", "Institute / College Overview"),
        unit("g2", "Department of Commerce", "Commerce department overview.", "Departments / Schools / Branches", entity="Commerce", entity_type="department"),
        unit("g3", "Faculty", "Commerce faculty.", "Faculty / HOD / Dean / Key People", entity="Commerce", entity_type="department"),
        unit("g4", "Department of Economics", "Economics department overview.", "Departments / Schools / Branches", entity="Economics", entity_type="department"),
        unit("g5", "Faculty", "Economics faculty.", "Faculty / HOD / Dean / Key People", entity="Economics", entity_type="department"),
    ]
    plan = Command4OrganizationV2().build_plan(domain="gwpgc.ac.in", units=units)
    paths = {doc["path"] for doc in plan["documents"]}
    assert "departments/commerce/overview.md" in paths
    assert "departments/economics/overview.md" in paths
    assert all("electrical" not in path for path in paths)
    assert all("mechanical" not in path for path in paths)


def test_review_units_are_preserved_and_c_is_not():
    units = [
        unit("r1", "Institutional Policy", "A policy requiring review.", "Potential Institutional Information", tier="REVIEW"),
    ]
    plan = Command4OrganizationV2().build_plan(domain="college.edu", units=units)
    assert plan["unit_count"] == 1
    assert plan["documents"][0]["unit_ids"] == ("r1",)


def test_large_admissions_can_create_many_meaningful_files_without_a_fixed_cap():
    headings = [
        "B.Tech Admissions", "M.Tech Admissions", "MBA Admissions",
        "B.Com Admissions", "B.A. Admissions", "M.Sc Admissions",
    ]
    units = [
        unit(f"a{i}", heading, f"Requirements for {heading}.", "Admissions")
        for i, heading in enumerate(headings, start=1)
    ]
    plan = Command4OrganizationV2().build_plan(domain="future.edu", units=units)
    assert plan["document_count"] == 6


def test_small_faculty_area_does_not_fragment_into_topic_documents():
    units = [
        unit("f1", "Faculty", "Professor A.", "Faculty / HOD / Dean / Key People"),
        unit("f2", "Professor", "Professor B.", "Faculty / HOD / Dean / Key People"),
        unit("f3", "Contact", "Faculty contact details.", "Faculty / HOD / Dean / Key People"),
    ]
    plan = Command4OrganizationV2().build_plan(domain="smallcollege.edu", units=units)
    assert plan["document_count"] == 1


def test_all_output_paths_are_non_empty_and_documents_have_traceability(tmp_path: Path):
    units = [
        unit("t1", "Research Areas", "Power systems research.", "Relevant Institutional Research", entity="Electrical Engineering", entity_type="department", source_lines="10-22"),
        unit("t2", "Faculty", "Professor A.", "Faculty / HOD / Dean / Key People", entity="Electrical Engineering", entity_type="department", source_lines="30-31"),
    ]
    organizer = Command4OrganizationV2()
    organizer.write_output(domain="iitj.ac.in", units=units, output_root=tmp_path)
    root = tmp_path / "iitj_ac_in"
    markdown_files = sorted(root.rglob("*.md"))
    assert markdown_files
    assert all(path.read_text(encoding="utf-8").strip() for path in markdown_files)
    assert all("Source Traceability" in path.read_text(encoding="utf-8") for path in markdown_files)


def test_output_is_byte_for_byte_deterministic(tmp_path: Path):
    units = [
        unit("d1", "Faculty", "A", "Faculty / HOD / Dean / Key People", entity="Electrical Engineering", entity_type="department"),
        unit("d2", "Research", "B", "Relevant Institutional Research", entity="Electrical Engineering", entity_type="department"),
    ]
    organizer = Command4OrganizationV2()
    first = tmp_path / "first"
    second = tmp_path / "second"
    organizer.write_output(domain="iitj.ac.in", units=units, output_root=first)
    organizer.write_output(domain="iitj.ac.in", units=units, output_root=second)

    first_files = sorted(path.relative_to(first).as_posix() for path in first.rglob("*") if path.is_file())
    second_files = sorted(path.relative_to(second).as_posix() for path in second.rglob("*") if path.is_file())
    assert first_files == second_files
    for relative in first_files:
        assert (first / relative).read_bytes() == (second / relative).read_bytes()


def test_every_accepted_unit_has_exactly_one_manifest_assignment(tmp_path: Path):
    units = [
        unit("l1", "3.3 Adding and Dropping of Courses", "Original content A.", "Programs & Courses"),
        unit("l2", "3.4 Withdrawing from a Course", "Original content B.", "Programs & Courses"),
        unit("l3", "10.5 Cancellation of Admission", "Original content C.", "Admissions"),
    ]
    manifest = Command4OrganizationV2().write_output(
        domain="iitj.ac.in",
        units=units,
        output_root=tmp_path,
    )
    rows = manifest["units"]
    assert {row["unit_id"] for row in rows} == {"l1", "l2", "l3"}
    assert len(rows) == 3
    assert len({row["unit_id"] for row in rows}) == 3


def test_accepted_content_is_not_rewritten_or_dropped(tmp_path: Path):
    original = "The Senate approves each course along with its weight in terms of credits."
    units = [
        unit("c1", "4.1.3 Approval of Courses", original, "Programs & Courses"),
    ]
    Command4OrganizationV2().write_output(
        domain="college.edu",
        units=units,
        output_root=tmp_path,
    )
    files = list((tmp_path / "college_edu").rglob("*.md"))
    assert len(files) == 1
    assert original in files[0].read_text(encoding="utf-8")