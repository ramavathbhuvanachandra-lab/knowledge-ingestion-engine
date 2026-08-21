"""
Tests for Phase 8.3 dynamic folder generation and organization.

These tests use a small deterministic taxonomy plan and synthetic Markdown.
They verify the core invariants without touching crawler-specific code.
"""

from __future__ import annotations

import json

from processors.knowledge_folder_builder import (
    KnowledgeFolderBuilder,
)
from processors.knowledge_organizer_dynamic import (
    KnowledgeOrganizer,
)

def taxonomy_plan() -> dict:
    return {
        "phase": "command_3_dynamic_taxonomy",
        "version": "2.0",
        "domain": "example.ac.in",
        "max_depth": 4,
        "root_nodes": [
            "taxonomy_0001",
            "taxonomy_0002",
        ],
        "nodes": [
            {
                "node_id": "taxonomy_0001",
                "name": "departments",
                "display_name": "Departments",
                "level": 1,
                "parent_id": None,
                "node_type": "entity_family",
                "entity_type": "department",
                "confidence": "high",
                "score": 10,
                "routing_signals": [
                    "entity_type:department",
                ],
                "entity_names": [],
            },
            {
                "node_id": "taxonomy_0002",
                "name": "admissions",
                "display_name": "Admissions",
                "level": 1,
                "parent_id": None,
                "node_type": "corpus_concept",
                "entity_type": None,
                "confidence": "high",
                "score": 10,
                "routing_signals": [
                    "concept:admissions",
                ],
                "entity_names": [],
            },
            {
                "node_id": "taxonomy_0003",
                "name": "electrical_engineering",
                "display_name": "Electrical Engineering",
                "level": 2,
                "parent_id": "taxonomy_0001",
                "node_type": "entity",
                "entity_type": "department",
                "confidence": "high",
                "score": 12,
                "routing_signals": [
                    "entity_type:department",
                    "entity:electrical engineering",
                ],
                "entity_names": [
                    "Electrical Engineering",
                ],
            },
            {
                "node_id": "taxonomy_0004",
                "name": "faculty",
                "display_name": "Faculty",
                "level": 3,
                "parent_id": "taxonomy_0003",
                "node_type": "entity_subcategory",
                "entity_type": None,
                "confidence": "high",
                "score": 10,
                "routing_signals": [
                    "entity_concept:faculty",
                ],
                "entity_names": [],
            },
            {
                "node_id": "taxonomy_0005",
                "name": "research",
                "display_name": "Research",
                "level": 3,
                "parent_id": "taxonomy_0003",
                "node_type": "entity_subcategory",
                "entity_type": None,
                "confidence": "high",
                "score": 10,
                "routing_signals": [
                    "entity_concept:research",
                ],
                "entity_names": [],
            },
        ],
        "buffer_policy": {
            "enabled": True,
            "max_buffers": 5,
        },
        "statistics": {},
        "warnings": [],
    }


def test_folder_builder_creates_only_plan_nodes(tmp_path):

    builder = KnowledgeFolderBuilder(
        output_root=tmp_path
    )

    manifest = builder.build(
        taxonomy_plan=taxonomy_plan(),
        domain="example.ac.in",
    )

    assert manifest["taxonomy_node_count"] == 5

    assert (
        tmp_path
        / "example.ac.in"
        / "departments"
        / "electrical_engineering"
        / "faculty"
    ).is_dir()

    assert not (
        tmp_path
        / "example.ac.in"
        / "departments"
        / "electrical_engineering"
        / "courses"
    ).exists()


def test_folder_builder_rejects_invalid_parent(tmp_path):

    builder = KnowledgeFolderBuilder(
        output_root=tmp_path
    )

    plan = taxonomy_plan()
    plan["nodes"][2]["parent_id"] = "missing"

    try:
        builder.build(
            taxonomy_plan=plan,
            domain="example.ac.in",
        )
    except ValueError:
        return

    raise AssertionError(
        "Expected invalid parent to raise ValueError."
    )


def test_organizer_requires_dynamic_taxonomy(tmp_path):

    markdown = tmp_path / "knowledge.md"
    markdown.write_text(
        """
**Domain:** example.ac.in

# Admissions

Admission information.
""".strip(),
        encoding="utf-8",
    )

    organizer = KnowledgeOrganizer(
        organized_root=tmp_path / "organized"
    )

    try:
        organizer.organize(markdown)
    except ValueError:
        return

    raise AssertionError(
        "Organizer must require a dynamic taxonomy plan."
    )


def test_organizer_routes_units_and_preserves_review(tmp_path):

    markdown = tmp_path / "knowledge.md"
    markdown.write_text(
        """
**Domain:** example.ac.in

[KEEP]
# Electrical Engineering Faculty

Faculty members belong to the Electrical Engineering department.

[REVIEW]
# Department Research

Research information for Electrical Engineering.

[KEEP]
# Admissions

Admission process and eligibility.

[KEEP]
# Institutional Anniversary

The institution celebrated its anniversary.
""".strip(),
        encoding="utf-8",
    )

    output = tmp_path / "organized"

    organizer = KnowledgeOrganizer(
        organized_root=output,
        taxonomy_plan=taxonomy_plan(),
    )

    manifest = organizer.organize(
        markdown
    )

    assert manifest["organized_sections"] == 4
    assert manifest["review_sections"] == 1
    assert manifest["matched_sections"] >= 3
    assert manifest["buffer_sections"] >= 1

    assert (
        output
        / "example.ac.in"
        / "departments"
        / "electrical_engineering"
        / "faculty"
        / "knowledge.md"
    ).exists()

    assert (
        output
        / "example.ac.in"
        / "departments"
        / "electrical_engineering"
        / "research"
        / "knowledge.md"
    ).exists()

    assert (
        output
        / "example.ac.in"
        / "admissions"
        / "knowledge.md"
    ).exists()

    assert (
        output
        / "example.ac.in"
        / "buffers"
        / "general_institutional_information"
        / "knowledge.md"
    ).exists()


def test_noise_is_excluded_but_legitimate_unmatched_is_preserved(tmp_path):

    markdown = tmp_path / "knowledge.md"
    markdown.write_text(
        """
**Domain:** example.ac.in

# Accessibility

accessibility options

# Campus Initiative

A legitimate campus initiative that does not fit the current taxonomy.
""".strip(),
        encoding="utf-8",
    )

    organizer = KnowledgeOrganizer(
        organized_root=tmp_path / "organized",
        taxonomy_plan=taxonomy_plan(),
    )

    manifest = organizer.organize(
        markdown
    )

    assert manifest["noise_sections"] == 1
    assert manifest["buffer_sections"] == 1

    buffer_file = (
        tmp_path
        / "organized"
        / "example.ac.in"
        / "buffers"
        / "student_campus_information"
        / "knowledge.md"
    )

    assert buffer_file.exists()

    text = buffer_file.read_text(
        encoding="utf-8"
    )

    assert (
        "A legitimate campus initiative"
        in text
    )

    assert (
        "accessibility options"
        not in text.lower()
    )


def test_plan_and_manifest_are_json_serializable(tmp_path):

    markdown = tmp_path / "knowledge.md"
    markdown.write_text(
        """
**Domain:** example.ac.in

# Admissions

Admission information.
""".strip(),
        encoding="utf-8",
    )

    organizer = KnowledgeOrganizer(
        organized_root=tmp_path / "organized",
        taxonomy_plan=taxonomy_plan(),
    )

    manifest = organizer.organize(
        markdown
    )

    serialized = json.dumps(
        manifest,
        ensure_ascii=False,
    )

    assert serialized


def test_organizer_does_not_create_boilerplate_entity_children(tmp_path):

    # Only Faculty exists in the generated plan under this department.
    # Organizer must not manufacture Research/Courses/Programs.
    markdown = tmp_path / "knowledge.md"
    markdown.write_text(
        """
**Domain:** example.ac.in

# Electrical Engineering Faculty

Faculty information.
""".strip(),
        encoding="utf-8",
    )

    organizer = KnowledgeOrganizer(
        organized_root=tmp_path / "organized",
        taxonomy_plan=taxonomy_plan(),
    )

    organizer.organize(
        markdown
    )

    department_root = (
        tmp_path
        / "organized"
        / "example.ac.in"
        / "departments"
        / "electrical_engineering"
    )

    assert (department_root / "faculty").is_dir()

    assert not (
        department_root / "research"
    ).exists()

    # Folder creation follows the plan. No courses/programs are invented.
    assert not (
        department_root / "courses"
    ).exists()
    assert not (
        department_root / "programs"
    ).exists()