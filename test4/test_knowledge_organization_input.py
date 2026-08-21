"""
Tests for StructuredKnowledgeInputAdapter.

The fixtures mirror the actual IITJ structured-knowledge JSON schema:
document + pages + sections.
"""

from __future__ import annotations

import json

from processors.knowledge_organization_input import (
    StructuredKnowledgeInputAdapter,
)


def record():
    return {
        "document": {
            "title": "About RCRICE",
            "url": "https://www.iitj.ac.in/rcrice/en/About",
            "domain": "www.iitj.ac.in",
            "category": "others",
            "document_type": "webpage",
            "source_file": None,
        },
        "pages": [
            {
                "page_number": None,
                "sections": [
                    {
                        "heading": None,
                        "level": 0,
                        "content": [
                            "Navigation",
                            "Home",
                            "Research",
                            "Contact",
                        ],
                        "content_type": "navigation",
                    },
                    {
                        "heading": "About",
                        "level": 2,
                        "content": [],
                        "content_type": "knowledge",
                    },
                    {
                        "heading": "Vision",
                        "level": 6,
                        "content": [
                            "The Centre will strive to become "
                            "the global destination for research."
                        ],
                        "content_type": "knowledge",
                    },
                    {
                        "heading": "Mission",
                        "level": 6,
                        "content": [
                            "Advance interdisciplinary research.",
                            "Support technology transfer.",
                        ],
                        "content_type": "knowledge",
                    },
                ],
            }
        ],
    }


def test_extracts_only_meaningful_knowledge_sections():

    adapter = StructuredKnowledgeInputAdapter()

    units = adapter.extract_record(
        record(),
        source_file="rcrice.json",
    )

    assert len(units) == 2

    headings = [
        unit.heading
        for unit in units
    ]

    assert headings == [
        "Vision",
        "Mission",
    ]

    assert all(
        unit.content_type == "knowledge"
        for unit in units
    )


def test_navigation_is_not_emitted_as_knowledge():

    adapter = StructuredKnowledgeInputAdapter()

    units = adapter.extract_record(
        record(),
        source_file="rcrice.json",
    )

    assert all(
        unit.heading != "Navigation"
        for unit in units
    )

    assert all(
        "Contact" not in unit.content
        for unit in units
    )


def test_original_content_wording_is_preserved():

    adapter = StructuredKnowledgeInputAdapter()

    units = adapter.extract_record(
        record(),
        source_file="rcrice.json",
    )

    mission = next(
        unit
        for unit in units
        if unit.heading == "Mission"
    )

    assert (
        mission.content
        == "Advance interdisciplinary research.\n"
        "Support technology transfer."
    )


def test_metadata_and_provenance_are_preserved():

    adapter = StructuredKnowledgeInputAdapter()

    units = adapter.extract_record(
        record(),
        source_file="rcrice.json",
    )

    unit = units[0]

    assert (
        unit.source_domain
        == "www.iitj.ac.in"
    )

    assert (
        unit.source_url
        == "https://www.iitj.ac.in/rcrice/en/About"
    )

    assert unit.source_title == "About RCRICE"
    assert unit.source_category == "others"
    assert unit.source_document_type == "webpage"
    assert unit.source_file == "rcrice.json"
    assert unit.page_number is None
    assert unit.section_index == 2


def test_unit_ids_are_stable():

    adapter = StructuredKnowledgeInputAdapter()

    units1 = adapter.extract_record(
        record(),
        source_file="rcrice.json",
    )

    units2 = adapter.extract_record(
        record(),
        source_file="rcrice.json",
    )

    assert [
        unit.unit_id
        for unit in units1
    ] == [
        unit.unit_id
        for unit in units2
    ]


def test_unknown_content_type_with_content_is_preserved():

    data = record()

    data["pages"][0]["sections"].append(
        {
            "heading": "Important Institutional Note",
            "level": 3,
            "content": [
                "This is legitimate content."
            ],
            "content_type": "",
        }
    )

    adapter = StructuredKnowledgeInputAdapter()

    units = adapter.extract_record(
        data,
        source_file="note.json",
    )

    assert any(
        unit.heading
        == "Important Institutional Note"
        for unit in units
    )


def test_empty_sections_are_not_created():

    adapter = StructuredKnowledgeInputAdapter()

    units = adapter.extract_record(
        record(),
        source_file="rcrice.json",
    )

    assert all(
        unit.content.strip()
        for unit in units
    )


def test_json_serializable():

    adapter = StructuredKnowledgeInputAdapter()

    units = adapter.extract_record(
        record(),
        source_file="rcrice.json",
    )

    payload = json.dumps(
        [
            unit.__dict__
            for unit in units
        ],
        ensure_ascii=False,
    )

    assert payload


def test_directory_extraction_is_domain_scoped(tmp_path):

    root = (
        tmp_path
        / "structured_knowledge"
    )

    iitj = (
        root
        / "www.iitj.ac.in"
        / "others"
    )

    gwpgc = (
        root
        / "gwpgc.ac.in"
        / "others"
    )

    iitj.mkdir(
        parents=True
    )

    gwpgc.mkdir(
        parents=True
    )

    (iitj / "a.json").write_text(
        json.dumps(
            record()
        ),
        encoding="utf-8",
    )

    gwpgc_record = record()
    gwpgc_record["document"][
        "domain"
    ] = "gwpgc.ac.in"

    (gwpgc / "b.json").write_text(
        json.dumps(
            gwpgc_record
        ),
        encoding="utf-8",
    )

    adapter = StructuredKnowledgeInputAdapter()

    units = adapter.extract_directory(
        root,
        domain="www.iitj.ac.in",
    )

    assert len(units) == 2

    assert all(
        unit.source_domain
        == "www.iitj.ac.in"
        for unit in units
    )