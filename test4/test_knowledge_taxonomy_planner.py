"""
Adversarial tests for the deterministic dynamic taxonomy planner.
"""

from __future__ import annotations

import json

import pytest

from processors.knowledge_taxonomy_planner import (
    KnowledgeTaxonomyPlanner,
)


def make_corpus_profile(
    *,
    domain: str = "test-college.ac.in",
    documents: list[dict] | None = None,
    repeated_headings: list[dict] | None = None,
    terminology_candidates: list[str] | None = None,
    document_types: dict | None = None,
    original_categories: dict | None = None,
) -> dict:

    documents = documents or []
    repeated_headings = repeated_headings or []
    terminology_candidates = terminology_candidates or []
    document_types = document_types or {}
    original_categories = original_categories or {}

    return {
        "phase": "command_3_corpus_analysis",
        "domain": domain,
        "input_root": "storage/structured_knowledge",
        "document_count": len(documents),
        "total_sections": 20,
        "total_meaningful_sections": 18,
        "total_words": 5000,
        "documents": documents,
        "heading_profiles": [],
        "repeated_headings": repeated_headings,
        "document_types": document_types,
        "original_categories": original_categories,
        "token_frequency": {},
        "exact_duplicate_groups": [],
        "likely_department_candidates": [],
        "terminology_candidates": terminology_candidates,
    }


def make_entity(
    *,
    name: str,
    entity_type: str,
    confidence: str = "high",
    mention_count: int = 3,
    sources: list[str] | None = None,
    headings: list[str] | None = None,
) -> dict:

    return {
        "name": name,
        "normalized_name": name.lower(),
        "entity_type": entity_type,
        "mention_count": mention_count,
        "confidence": confidence,
        "scores": [100],
        "sources": sources or [
            "doc1.json",
            "doc2.json",
        ],
        "headings": headings or [],
        "evidence": [],
    }


def make_entity_discovery(
    entities: list[dict],
) -> dict:

    return {
        "entity_count": len(entities),
        "evidence_count": len(entities),
        "entities": entities,
    }


def test_empty_corpus_does_not_crash():

    planner = KnowledgeTaxonomyPlanner()

    plan = planner.plan(
        corpus_profile=make_corpus_profile(),
        entity_discovery=make_entity_discovery([]),
    )

    assert isinstance(plan, dict)
    assert plan["node_count"] == 0
    assert any(
        "No corpus documents" in warning
        for warning in plan["warnings"]
    )


def test_plan_is_json_serializable():

    planner = KnowledgeTaxonomyPlanner()

    corpus = make_corpus_profile(
        documents=[
            {
                "source_file": "doc1.json",
                "source_url": "https://example.com/doc1",
                "title": "Admissions",
                "document_type": "admission rules",
                "original_category": "academics",
                "headings": [
                    "Admissions",
                    "Eligibility",
                    "Application Process",
                ],
            },
            {
                "source_file": "doc2.json",
                "source_url": "https://example.com/doc2",
                "title": "Department",
                "document_type": "academic",
                "original_category": "academics",
                "headings": [
                    "Faculty",
                    "Courses",
                    "Research",
                ],
            },
        ],
        repeated_headings=[
            {
                "heading": "Faculty",
                "normalized_heading": "faculty",
                "occurrences": 4,
                "document_count": 3,
                "source_documents": [
                    "doc1.json",
                    "doc2.json",
                    "doc3.json",
                ],
            }
        ],
        terminology_candidates=[
            "Faculty",
            "Research",
            "Admissions",
        ],
        document_types={
            "academic": 10,
            "admission rules": 3,
        },
    )

    entities = make_entity_discovery(
        [
            make_entity(
                name="English",
                entity_type="department",
            ),
            make_entity(
                name="Economics",
                entity_type="department",
            ),
        ]
    )

    plan = planner.plan(
        corpus_profile=corpus,
        entity_discovery=entities,
    )

    assert json.dumps(
        plan,
        ensure_ascii=False,
    )


def test_same_input_produces_same_taxonomy():

    planner = KnowledgeTaxonomyPlanner()

    corpus = make_corpus_profile(
        documents=[
            {
                "source_file": "a.json",
                "title": "English Department",
                "document_type": "academic",
                "original_category": "academics",
                "headings": [
                    "Faculty",
                    "Research",
                    "Courses",
                ],
            },
            {
                "source_file": "b.json",
                "title": "Economics Department",
                "document_type": "academic",
                "original_category": "academics",
                "headings": [
                    "Faculty",
                    "Research",
                    "Courses",
                ],
            },
        ],
        repeated_headings=[
            {
                "heading": "Faculty",
                "normalized_heading": "faculty",
                "occurrences": 5,
                "document_count": 4,
                "source_documents": [
                    "a.json",
                    "b.json",
                    "c.json",
                    "d.json",
                ],
            },
            {
                "heading": "Research",
                "normalized_heading": "research",
                "occurrences": 5,
                "document_count": 4,
                "source_documents": [
                    "a.json",
                    "b.json",
                    "c.json",
                    "d.json",
                ],
            },
        ],
        terminology_candidates=[
            "Faculty",
            "Research",
        ],
        document_types={
            "academic": 10,
        },
    )

    entities = make_entity_discovery(
        [
            make_entity(
                name="English",
                entity_type="department",
            ),
            make_entity(
                name="Economics",
                entity_type="department",
            ),
        ]
    )

    plan1 = planner.plan(
        corpus_profile=corpus,
        entity_discovery=entities,
    )

    plan2 = planner.plan(
        corpus_profile=corpus,
        entity_discovery=entities,
    )

    assert plan1 == plan2


def test_multiple_departments_create_department_structure():

    planner = KnowledgeTaxonomyPlanner()

    corpus = make_corpus_profile(
        documents=[
            {
                "source_file": "english.json",
                "title": "English Department",
                "headings": [
                    "Faculty",
                    "Courses",
                    "Research",
                    "Syllabus",
                ],
            },
            {
                "source_file": "economics.json",
                "title": "Economics Department",
                "headings": [
                    "Faculty",
                    "Courses",
                    "Research",
                    "Syllabus",
                ],
            },
        ],
        repeated_headings=[
            {
                "heading": "Faculty",
                "normalized_heading": "faculty",
                "occurrences": 5,
                "document_count": 4,
                "source_documents": [],
            },
            {
                "heading": "Courses",
                "normalized_heading": "courses",
                "occurrences": 5,
                "document_count": 4,
                "source_documents": [],
            },
            {
                "heading": "Research",
                "normalized_heading": "research",
                "occurrences": 5,
                "document_count": 4,
                "source_documents": [],
            },
            {
                "heading": "Syllabus",
                "normalized_heading": "syllabus",
                "occurrences": 5,
                "document_count": 4,
                "source_documents": [],
            },
        ],
        terminology_candidates=[
            "Faculty",
            "Courses",
            "Research",
            "Syllabus",
        ],
    )

    entities = make_entity_discovery(
        [
            make_entity(
                name="English",
                entity_type="department",
                sources=[
                    "english.json",
                    "english2.json",
                ],
            ),
            make_entity(
                name="Economics",
                entity_type="department",
                sources=[
                    "economics.json",
                    "economics2.json",
                ],
            ),
        ]
    )

    plan = planner.plan(
        corpus_profile=corpus,
        entity_discovery=entities,
    )

    names = {
        node["display_name"]
        for node in plan["nodes"]
    }

    assert "Departments" in names
    assert "English" in names
    assert "Economics" in names


def test_wrapped_entity_discovery_report_is_supported():

    planner = KnowledgeTaxonomyPlanner()

    corpus = make_corpus_profile(
        documents=[
            {
                "source_file": "english.json",
                "title": "English Department",
                "headings": [
                    "Faculty",
                    "Courses",
                    "Research",
                ],
            },
            {
                "source_file": "economics.json",
                "title": "Economics Department",
                "headings": [
                    "Faculty",
                    "Courses",
                    "Research",
                ],
            },
        ],
        repeated_headings=[
            {
                "heading": "Faculty",
                "normalized_heading": "faculty",
                "occurrences": 5,
                "document_count": 4,
                "source_documents": [],
            }
        ],
        terminology_candidates=[
            "Faculty",
            "Courses",
            "Research",
        ],
    )

    wrapped = {
        "test": "real_test",
        "domain": "example.ac.in",
        "files_found": 2,
        "documents_loaded": 2,
        "loading_failures": 0,
        "failures": [],
        "entity_discovery": {
            "entity_count": 2,
            "evidence_count": 6,
            "entities": [
                make_entity(
                    name="English",
                    entity_type="department",
                ),
                make_entity(
                    name="Economics",
                    entity_type="department",
                ),
            ],
        },
    }

    plan = planner.plan(
        corpus_profile=corpus,
        entity_discovery=wrapped,
    )

    assert plan["statistics"]["entity_count"] == 2

    names = {
        node["display_name"]
        for node in plan["nodes"]
    }

    assert "Departments" in names
    assert "English" in names
    assert "Economics" in names


def test_single_weak_entity_does_not_create_entity_root():

    planner = KnowledgeTaxonomyPlanner()

    entities = make_entity_discovery(
        [
            make_entity(
                name="Random Unit",
                entity_type="department",
                confidence="low",
                mention_count=1,
                sources=["one.json"],
            )
        ]
    )

    plan = planner.plan(
        corpus_profile=make_corpus_profile(),
        entity_discovery=entities,
    )

    names = {
        node["display_name"]
        for node in plan["nodes"]
    }

    assert "Random Unit" not in names


def test_medical_college_like_corpus_is_supported():

    planner = KnowledgeTaxonomyPlanner()

    corpus = make_corpus_profile(
        domain="medical-college.ac.in",
        documents=[
            {
                "source_file": "anatomy.json",
                "title": "Department of Anatomy",
                "headings": [
                    "Faculty",
                    "Courses",
                    "Clinical Training",
                ],
            },
            {
                "source_file": "surgery.json",
                "title": "Department of Surgery",
                "headings": [
                    "Faculty",
                    "Clinical Training",
                    "Research",
                ],
            },
        ],
        repeated_headings=[
            {
                "heading": "Faculty",
                "normalized_heading": "faculty",
                "occurrences": 6,
                "document_count": 4,
                "source_documents": [],
            },
            {
                "heading": "Clinical Training",
                "normalized_heading": "clinical training",
                "occurrences": 5,
                "document_count": 3,
                "source_documents": [],
            },
        ],
        terminology_candidates=[
            "Faculty",
            "Clinical Training",
            "Research",
        ],
    )

    entities = make_entity_discovery(
        [
            make_entity(
                name="Anatomy",
                entity_type="department",
            ),
            make_entity(
                name="Surgery",
                entity_type="department",
            ),
        ]
    )

    plan = planner.plan(
        corpus_profile=corpus,
        entity_discovery=entities,
    )

    names = {
        node["display_name"]
        for node in plan["nodes"]
    }

    assert "Anatomy" in names
    assert "Surgery" in names
    assert "Electrical Engineering" not in names
    assert "MBA" not in names
    assert "B.Tech" not in names


def test_law_college_like_corpus_is_supported():

    planner = KnowledgeTaxonomyPlanner()

    corpus = make_corpus_profile(
        domain="law-college.ac.in",
        documents=[
            {
                "source_file": "law.json",
                "title": "Legal Studies",
                "headings": [
                    "Moot Court",
                    "Legal Clinic",
                    "Faculty",
                ],
            },
            {
                "source_file": "research.json",
                "title": "Legal Research",
                "headings": [
                    "Research",
                    "Faculty",
                ],
            },
        ],
        repeated_headings=[
            {
                "heading": "Faculty",
                "normalized_heading": "faculty",
                "occurrences": 4,
                "document_count": 3,
                "source_documents": [],
            },
            {
                "heading": "Research",
                "normalized_heading": "research",
                "occurrences": 4,
                "document_count": 3,
                "source_documents": [],
            },
        ],
        terminology_candidates=[
            "Moot Court",
            "Legal Clinic",
            "Research",
            "Faculty",
        ],
    )

    entities = make_entity_discovery(
        [
            make_entity(
                name="Legal Studies",
                entity_type="academic_unit",
            ),
        ]
    )

    plan = planner.plan(
        corpus_profile=corpus,
        entity_discovery=entities,
    )

    assert isinstance(
        plan["nodes"],
        list,
    )
    assert plan["domain"] == "law-college.ac.in"


def test_one_off_generic_heading_does_not_become_root():

    planner = KnowledgeTaxonomyPlanner()

    corpus = make_corpus_profile(
        documents=[
            {
                "source_file": "one.json",
                "title": "General Information",
                "headings": [
                    "About",
                ],
            }
        ],
        terminology_candidates=[
            "About",
            "Information",
        ],
    )

    plan = planner.plan(
        corpus_profile=corpus,
        entity_discovery=make_entity_discovery([]),
    )

    names = {
        node["name"]
        for node in plan["nodes"]
    }

    assert "about" not in names
    assert "information" not in names


def test_events_do_not_automatically_create_events_folder_from_one_document():

    planner = KnowledgeTaxonomyPlanner()

    corpus = make_corpus_profile(
        documents=[
            {
                "source_file": "one.json",
                "title": "Annual Seminar",
                "headings": [
                    "Event Details",
                ],
            }
        ],
        terminology_candidates=[
            "Event Details",
        ],
        document_types={
            "report": 1,
        },
    )

    plan = planner.plan(
        corpus_profile=corpus,
        entity_discovery=make_entity_discovery([]),
    )

    assert not [
        node
        for node in plan["nodes"]
        if node["name"] == "events"
    ]


def test_taxonomy_depth_never_exceeds_limit():

    planner = KnowledgeTaxonomyPlanner(
        max_depth=4
    )

    corpus = make_corpus_profile(
        documents=[
            {
                "source_file": "one.json",
                "title": "Department",
                "headings": [
                    "Faculty",
                    "Courses",
                    "Research",
                    "Syllabus",
                ],
            },
            {
                "source_file": "two.json",
                "title": "Department",
                "headings": [
                    "Faculty",
                    "Courses",
                    "Research",
                    "Syllabus",
                ],
            },
        ],
        repeated_headings=[
            {
                "heading": "Faculty",
                "normalized_heading": "faculty",
                "occurrences": 6,
                "document_count": 4,
                "source_documents": [],
            },
            {
                "heading": "Courses",
                "normalized_heading": "courses",
                "occurrences": 6,
                "document_count": 4,
                "source_documents": [],
            },
        ],
        terminology_candidates=[
            "Faculty",
            "Courses",
        ],
    )

    entities = make_entity_discovery(
        [
            make_entity(
                name="English",
                entity_type="department",
            ),
            make_entity(
                name="Economics",
                entity_type="department",
            ),
        ]
    )

    plan = planner.plan(
        corpus_profile=corpus,
        entity_discovery=entities,
    )

    assert all(
        node["level"] <= 4
        for node in plan["nodes"]
    )


def test_entity_is_not_automatically_made_a_top_level_root():

    planner = KnowledgeTaxonomyPlanner()

    entities = make_entity_discovery(
        [
            make_entity(
                name="English",
                entity_type="department",
            ),
            make_entity(
                name="Economics",
                entity_type="department",
            ),
        ]
    )

    plan = planner.plan(
        corpus_profile=make_corpus_profile(),
        entity_discovery=entities,
    )

    root_names = {
        node["display_name"]
        for node in plan["nodes"]
        if node["level"] == 1
    }

    assert "English" not in root_names
    assert "Economics" not in root_names
    assert "Departments" in root_names


def test_invalid_corpus_profile_raises():

    planner = KnowledgeTaxonomyPlanner()

    with pytest.raises(TypeError):
        planner.plan(
            corpus_profile=[],
            entity_discovery={},
        )


def test_invalid_entity_discovery_raises():

    planner = KnowledgeTaxonomyPlanner()

    with pytest.raises(TypeError):
        planner.plan(
            corpus_profile={},
            entity_discovery=[],
        )


def test_node_ids_are_stable_and_unique():

    planner = KnowledgeTaxonomyPlanner()

    corpus = make_corpus_profile(
        documents=[
            {
                "source_file": "a.json",
                "title": "Admissions",
                "headings": [
                    "Eligibility",
                ],
            },
            {
                "source_file": "b.json",
                "title": "Admissions",
                "headings": [
                    "Eligibility",
                ],
            },
        ],
        repeated_headings=[
            {
                "heading": "Admissions",
                "normalized_heading": "admissions",
                "occurrences": 4,
                "document_count": 3,
                "source_documents": [],
            }
        ],
        terminology_candidates=[
            "Admissions",
        ],
    )

    plan = planner.plan(
        corpus_profile=corpus,
        entity_discovery=make_entity_discovery([]),
    )

    ids = [
        node["node_id"]
        for node in plan["nodes"]
    ]

    assert len(ids) == len(set(ids))


def test_entity_children_have_valid_parent_ids():

    planner = KnowledgeTaxonomyPlanner()

    corpus = make_corpus_profile(
        documents=[
            {
                "source_file": "english.json",
                "title": "English Department",
                "headings": [
                    "Faculty",
                    "Research",
                    "Courses",
                ],
            },
            {
                "source_file": "english2.json",
                "title": "English Department",
                "headings": [
                    "Faculty",
                    "Research",
                    "Courses",
                ],
            },
        ],
        repeated_headings=[
            {
                "heading": "Faculty",
                "normalized_heading": "faculty",
                "occurrences": 4,
                "document_count": 3,
                "source_documents": [],
            },
            {
                "heading": "Research",
                "normalized_heading": "research",
                "occurrences": 4,
                "document_count": 3,
                "source_documents": [],
            },
        ],
    )

    entities = make_entity_discovery(
        [
            make_entity(
                name="English",
                entity_type="department",
                sources=[
                    "english.json",
                    "english2.json",
                ],
            ),
            make_entity(
                name="Economics",
                entity_type="department",
                sources=[
                    "economics.json",
                    "economics2.json",
                ],
            ),
        ]
    )

    plan = planner.plan(
        corpus_profile=corpus,
        entity_discovery=entities,
    )

    node_ids = {
        node["node_id"]
        for node in plan["nodes"]
    }

    for node in plan["nodes"]:
        if node["parent_id"] is not None:
            assert node["parent_id"] in node_ids


def test_noisy_entities_are_not_promoted_into_taxonomy():

    planner = KnowledgeTaxonomyPlanner()

    noisy_entities = [
        make_entity(
            name="Direct Approaches to",
            entity_type="department",
            confidence="medium",
            mention_count=2,
            sources=["a.json", "b.json"],
        ),
        make_entity(
            name="2,50,000 925 Socioeconomic Status",
            entity_type="facility",
            confidence="medium",
            mention_count=5,
            sources=["a.json", "b.json"],
        ),
        make_entity(
            name="emailankitasharma",
            entity_type="office",
            confidence="medium",
            mention_count=5,
            sources=["a.json", "b.json"],
        ),
        make_entity(
            name="Engineering",
            entity_type="school",
            confidence="high",
            mention_count=3,
            sources=["a.json", "b.json"],
            headings=["School of Engineering"],
        ),
        make_entity(
            name="Management",
            entity_type="school",
            confidence="high",
            mention_count=3,
            sources=["a.json", "b.json"],
            headings=["School of Management"],
        ),
    ]

    plan = planner.plan(
        corpus_profile=make_corpus_profile(
            documents=[
                {
                    "source_file": "a.json",
                    "title": "School of Engineering",
                    "headings": ["School of Engineering"],
                },
                {
                    "source_file": "b.json",
                    "title": "School of Management",
                    "headings": ["School of Management"],
                },
            ]
        ),
        entity_discovery=make_entity_discovery(noisy_entities),
    )

    names = {
        node["display_name"]
        for node in plan["nodes"]
    }

    assert "Engineering" in names
    assert "Management" in names
    assert "Direct Approaches to" not in names
    assert "emailankitasharma" not in names


def test_entity_nodes_keep_their_correct_parents():

    planner = KnowledgeTaxonomyPlanner()

    corpus = make_corpus_profile(
        documents=[
            {
                "source_file": "english.json",
                "title": "Department of English",
                "headings": [
                    "Department of English",
                    "Faculty",
                ],
            },
            {
                "source_file": "economics.json",
                "title": "Department of Economics",
                "headings": [
                    "Department of Economics",
                    "Faculty",
                ],
            },
        ],
        repeated_headings=[
            {
                "heading": "Faculty",
                "normalized_heading": "faculty",
                "occurrences": 4,
                "document_count": 4,
                "source_documents": [],
            }
        ],
    )

    entities = make_entity_discovery(
        [
            make_entity(
                name="English",
                entity_type="department",
                confidence="high",
                mention_count=4,
                sources=["english.json", "english2.json"],
                headings=["Department of English"],
            ),
            make_entity(
                name="Economics",
                entity_type="department",
                confidence="high",
                mention_count=4,
                sources=["economics.json", "economics2.json"],
                headings=["Department of Economics"],
            ),
        ]
    )

    plan = planner.plan(
        corpus_profile=corpus,
        entity_discovery=entities,
    )

    nodes = plan["nodes"]

    departments = {
        node["display_name"]: node
        for node in nodes
        if node["display_name"] in {
            "English",
            "Economics",
        }
    }

    root = next(
        node
        for node in nodes
        if node["display_name"] == "Departments"
    )

    assert departments["English"]["parent_id"] == root["node_id"]
    assert departments["Economics"]["parent_id"] == root["node_id"]


def test_entity_statistics_report_rejections():

    planner = KnowledgeTaxonomyPlanner()

    entities = [
        make_entity(
            name=f"Research article title with page {index}",
            entity_type="department",
            confidence="medium",
            mention_count=5,
            sources=["a.json", "b.json"],
        )
        for index in range(20)
    ]

    entities.extend(
        [
            make_entity(
                name="English",
                entity_type="department",
                confidence="high",
                mention_count=5,
                sources=["a.json", "b.json"],
                headings=["Department of English"],
            ),
            make_entity(
                name="Economics",
                entity_type="department",
                confidence="high",
                mention_count=5,
                sources=["a.json", "b.json"],
                headings=["Department of Economics"],
            ),
        ]
    )

    plan = planner.plan(
        corpus_profile=make_corpus_profile(
            documents=[
                {
                    "source_file": "a.json",
                    "title": "English",
                    "headings": ["Department of English"],
                },
                {
                    "source_file": "b.json",
                    "title": "Economics",
                    "headings": ["Department of Economics"],
                },
            ]
        ),
        entity_discovery=make_entity_discovery(entities),
    )

    assert plan["statistics"]["rejected_entity_count"] >= 20
    assert plan["statistics"]["accepted_entity_count"] >= 2


def test_buffer_policy_exists_without_creating_empty_buffer_folders():

    planner = KnowledgeTaxonomyPlanner()

    plan = planner.plan(
        corpus_profile=make_corpus_profile(),
        entity_discovery=make_entity_discovery([]),
    )

    assert plan["buffer_policy"]["enabled"] is True
    assert plan["buffer_policy"]["max_buffers"] == 5
    assert all(
        "buffer" not in node["name"]
        for node in plan["nodes"]
    )


def test_new_department_gets_only_evidence_backed_children():

    planner = KnowledgeTaxonomyPlanner()

    corpus = make_corpus_profile(
        documents=[
            {
                "source_file": "a.json",
                "title": "Department of Aeronautical Engineering",
                "headings": [
                    "Department of Aeronautical Engineering",
                    "Faculty",
                ],
            },
            {
                "source_file": "b.json",
                "title": "Department of Aeronautical Engineering",
                "headings": [
                    "Department of Aeronautical Engineering",
                    "Faculty",
                ],
            },
        ],
        repeated_headings=[
            {
                "heading": "Faculty",
                "normalized_heading": "faculty",
                "occurrences": 4,
                "document_count": 2,
                "source_documents": [
                    "a.json",
                    "b.json",
                ],
            }
        ],
    )

    entities = make_entity_discovery(
        [
            make_entity(
                name="Aeronautical Engineering",
                entity_type="department",
                confidence="high",
                mention_count=4,
                sources=["a.json", "b.json"],
                headings=[
                    "Department of Aeronautical Engineering"
                ],
            ),
            make_entity(
                name="Electrical Engineering",
                entity_type="department",
                confidence="high",
                mention_count=5,
                sources=["c.json", "d.json"],
                headings=[
                    "Department of Electrical Engineering"
                ],
            ),
        ]
    )

    plan = planner.plan(
        corpus_profile=corpus,
        entity_discovery=entities,
    )

    aeronautical = next(
        node
        for node in plan["nodes"]
        if node["display_name"]
        == "Aeronautical Engineering"
    )

    children = [
        node
        for node in plan["nodes"]
        if node["parent_id"]
        == aeronautical["node_id"]
    ]

    assert any(
        child["display_name"] == "Faculty"
        for child in children
    )

    assert not any(
        child["display_name"]
        in {
            "Research",
            "Courses",
            "Programs",
            "Placements",
            "Scholarships",
        }
        for child in children
    )


def test_multiple_departments_share_family_but_keep_children_independent():

    planner = KnowledgeTaxonomyPlanner()

    corpus = make_corpus_profile(
        documents=[
            {
                "source_file": "ee1.json",
                "title": "Department of Electrical Engineering",
                "headings": [
                    "Department of Electrical Engineering",
                    "Faculty",
                    "Research",
                    "Courses",
                ],
            },
            {
                "source_file": "ee2.json",
                "title": "Department of Electrical Engineering",
                "headings": [
                    "Department of Electrical Engineering",
                    "Faculty",
                    "Research",
                    "Courses",
                ],
            },
            {
                "source_file": "aero1.json",
                "title": "Department of Aeronautical Engineering",
                "headings": [
                    "Department of Aeronautical Engineering",
                    "Faculty",
                ],
            },
            {
                "source_file": "aero2.json",
                "title": "Department of Aeronautical Engineering",
                "headings": [
                    "Department of Aeronautical Engineering",
                    "Faculty",
                ],
            },
        ],
        repeated_headings=[
            {
                "heading": "Faculty",
                "normalized_heading": "faculty",
                "occurrences": 6,
                "document_count": 4,
                "source_documents": [],
            },
            {
                "heading": "Research",
                "normalized_heading": "research",
                "occurrences": 4,
                "document_count": 2,
                "source_documents": [],
            },
            {
                "heading": "Courses",
                "normalized_heading": "courses",
                "occurrences": 4,
                "document_count": 2,
                "source_documents": [],
            },
        ],
    )

    entities = make_entity_discovery(
        [
            make_entity(
                name="Electrical Engineering",
                entity_type="department",
                confidence="high",
                mention_count=8,
                sources=["ee1.json", "ee2.json"],
                headings=[
                    "Department of Electrical Engineering"
                ],
            ),
            make_entity(
                name="Aeronautical Engineering",
                entity_type="department",
                confidence="high",
                mention_count=4,
                sources=["aero1.json", "aero2.json"],
                headings=[
                    "Department of Aeronautical Engineering"
                ],
            ),
        ]
    )

    plan = planner.plan(
        corpus_profile=corpus,
        entity_discovery=entities,
    )

    departments = [
        node
        for node in plan["nodes"]
        if node["display_name"]
        in {
            "Electrical Engineering",
            "Aeronautical Engineering",
        }
    ]

    assert len(departments) == 2

    electrical = next(
        node
        for node in departments
        if node["display_name"]
        == "Electrical Engineering"
    )

    aeronautical = next(
        node
        for node in departments
        if node["display_name"]
        == "Aeronautical Engineering"
    )

    electrical_children = {
        node["display_name"]
        for node in plan["nodes"]
        if node["parent_id"]
        == electrical["node_id"]
    }

    aeronautical_children = {
        node["display_name"]
        for node in plan["nodes"]
        if node["parent_id"]
        == aeronautical["node_id"]
    }

    assert {
        "Faculty",
        "Research",
        "Courses",
    }.issubset(
        electrical_children
    )

    assert aeronautical_children == {
        "Faculty"
    }


def test_noisy_iitj_style_entities_are_rejected():

    planner = KnowledgeTaxonomyPlanner()

    entities = [
        make_entity(
            name="Electrical Engineering, IIT Jodhpur",
            entity_type="department",
            confidence="high",
            mention_count=5,
            sources=["a.json", "b.json"],
        ),
        make_entity(
            name="Chemistry emailmilanhazra",
            entity_type="department",
            confidence="high",
            mention_count=5,
            sources=["a.json", "b.json"],
        ),
        make_entity(
            name="Physics, who",
            entity_type="department",
            confidence="high",
            mention_count=5,
            sources=["a.json", "b.json"],
        ),
        make_entity(
            name="Number of Participants",
            entity_type="department",
            confidence="high",
            mention_count=5,
            sources=["a.json", "b.json"],
        ),
        make_entity(
            name="Electrical Engineering",
            entity_type="department",
            confidence="high",
            mention_count=5,
            sources=["a.json", "b.json"],
            headings=["Department of Electrical Engineering"],
        ),
        make_entity(
            name="Mechanical Engineering",
            entity_type="department",
            confidence="high",
            mention_count=5,
            sources=["a.json", "b.json"],
            headings=["Department of Mechanical Engineering"],
        ),
    ]

    plan = planner.plan(
        corpus_profile=make_corpus_profile(),
        entity_discovery=make_entity_discovery(
            entities
        ),
    )

    names = {
        node["display_name"]
        for node in plan["nodes"]
    }

    assert "Electrical Engineering" in names
    assert "Mechanical Engineering" in names

    assert "Chemistry emailmilanhazra" not in names
    assert "Physics, who" not in names
    assert "Number of Participants" not in names


def test_parent_relationships_are_unique_and_valid():

    planner = KnowledgeTaxonomyPlanner()

    plan = planner.plan(
        corpus_profile=make_corpus_profile(
            documents=[
                {
                    "source_file": "a.json",
                    "title": "Department of English",
                    "headings": [
                        "Department of English",
                        "Faculty",
                    ],
                },
                {
                    "source_file": "b.json",
                    "title": "Department of Economics",
                    "headings": [
                        "Department of Economics",
                        "Faculty",
                    ],
                },
            ]
        ),
        entity_discovery=make_entity_discovery(
            [
                make_entity(
                    name="English",
                    entity_type="department",
                    confidence="high",
                    mention_count=5,
                    sources=["a.json", "a2.json"],
                    headings=["Department of English"],
                ),
                make_entity(
                    name="Economics",
                    entity_type="department",
                    confidence="high",
                    mention_count=5,
                    sources=["b.json", "b2.json"],
                    headings=["Department of Economics"],
                ),
            ]
        ),
    )

    ids = [
        node["node_id"]
        for node in plan["nodes"]
    ]

    assert len(ids) == len(set(ids))

    id_set = set(ids)

    for node in plan["nodes"]:
        if node["parent_id"] is not None:
            assert node["parent_id"] in id_set


def test_specific_concepts_beat_broader_overlapping_concepts():

    planner = KnowledgeTaxonomyPlanner()

    assert (
        planner._map_signal_to_concept("Courses")
        == "courses"
    )

    assert (
        planner._map_signal_to_concept("Faculty")
        == "faculty"
    )

    assert (
        planner._map_signal_to_concept("Research")
        == "research"
    )


def test_high_confidence_structural_name_can_work_without_headings():

    planner = KnowledgeTaxonomyPlanner()

    entity = make_entity(
        name="Anatomy",
        entity_type="department",
        confidence="high",
        mention_count=4,
        sources=["a.json", "b.json"],
        headings=[],
    )

    assert planner._entity_is_meaningful(entity)
