"""
Command 3 — Corpus Analyzer Tests.

The analyzer must discover structure from the corpus without using
a fixed college taxonomy.
"""

import json
from pathlib import Path

from processors.knowledge_corpus_analyzer import (
    KnowledgeCorpusAnalyzer,
)


# ============================================================
# TEST HELPERS
# ============================================================

def _write_structured_document(
    root: Path,
    filename: str,
    title: str,
    sections: list[dict],
) -> None:
    """Write one minimal structured-knowledge fixture."""

    path = root / filename

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = {
        "document": {
            "title": title,
            "url": f"https://example.edu/{filename}",
            "domain": "example.edu",
            "category": "others",
            "document_type": "webpage",
        },
        "pages": [
            {
                "page_number": 1,
                "sections": sections,
            }
        ],
    }

    path.write_text(
        json.dumps(
            payload,
            indent=2,
        ),
        encoding="utf-8",
    )


# ============================================================
# TEST: REPEATED STRUCTURE
# ============================================================

def test_analyzer_discovers_repeated_structure(
    tmp_path: Path,
):
    """Repeated headings and department candidates are detected."""

    root = (
        tmp_path
        / "structured"
        / "example.edu"
    )

    _write_structured_document(
        root,
        "electrical.md.json",
        "Electrical Engineering",
        [
            {
                "heading": "Department of Electrical Engineering",
                "level": 1,
                "content": [
                    {
                        "text": "Department overview."
                    }
                ],
            },
            {
                "heading": "Faculty",
                "level": 2,
                "content": [
                    {
                        "text": "Faculty members."
                    }
                ],
            },
            {
                "heading": "Research",
                "level": 2,
                "content": [
                    {
                        "text": "Research areas."
                    }
                ],
            },
        ],
    )

    _write_structured_document(
        root,
        "computer.md.json",
        "Computer Science",
        [
            {
                "heading": "Department of Computer Science",
                "level": 1,
                "content": [
                    {
                        "text": "Department overview."
                    }
                ],
            },
            {
                "heading": "Faculty",
                "level": 2,
                "content": [
                    {
                        "text": "Faculty members."
                    }
                ],
            },
            {
                "heading": "Research",
                "level": 2,
                "content": [
                    {
                        "text": "Research areas."
                    }
                ],
            },
        ],
    )

    analyzer = KnowledgeCorpusAnalyzer(
        input_root=tmp_path / "structured"
    )

    profile = analyzer.analyze(
        "example.edu"
    )

    assert profile["document_count"] == 2

    assert (
        profile["total_meaningful_sections"]
        == 6
    )

    assert any(
        item["normalized_heading"] == "faculty"
        for item in profile[
            "repeated_headings"
        ]
    )

    assert any(
        item["normalized_name"]
        == "electrical engineering"
        for item in profile[
            "likely_department_candidates"
        ]
    )

    assert any(
        item["normalized_name"]
        == "computer science"
        for item in profile[
            "likely_department_candidates"
        ]
    )


# ============================================================
# TEST: EXACT DUPLICATES
# ============================================================

def test_analyzer_detects_exact_duplicate_documents(
    tmp_path: Path,
):
    """Identical structured documents are grouped as duplicates."""

    root = (
        tmp_path
        / "structured"
        / "example.edu"
    )

    sections = [
        {
            "heading": "Overview",
            "level": 1,
            "content": [
                {
                    "text": (
                        "The same content appears twice."
                    )
                }
            ],
        }
    ]

    _write_structured_document(
        root,
        "one.md.json",
        "One",
        sections,
    )

    _write_structured_document(
        root,
        "two.md.json",
        "Two",
        sections,
    )

    analyzer = KnowledgeCorpusAnalyzer(
        input_root=tmp_path / "structured"
    )

    profile = analyzer.analyze(
        "example.edu"
    )

    assert len(
        profile["exact_duplicate_groups"]
    ) == 1

    assert len(
        profile["exact_duplicate_groups"][0]
    ) == 2


# ============================================================
# TEST: NO FIXED TAXONOMY
# ============================================================

def test_analyzer_does_not_create_fixed_categories(
    tmp_path: Path,
):
    """
    The analyzer observes terminology from the corpus.

    It must not manufacture a fixed taxonomy such as:
        academics
        hostel
        admissions
    """

    root = (
        tmp_path
        / "structured"
        / "medical.example"
    )

    _write_structured_document(
        root,
        "clinical.md.json",
        "Clinical Services",
        [
            {
                "heading": "Clinical Services",
                "level": 1,
                "content": [
                    {
                        "text": (
                            "Hospital clinical services."
                        )
                    }
                ],
            }
        ],
    )

    analyzer = KnowledgeCorpusAnalyzer(
        input_root=tmp_path / "structured"
    )

    profile = analyzer.analyze(
        "medical.example"
    )

    assert profile["document_count"] == 1

    assert "Clinical Services" in (
        profile["terminology_candidates"]
    )