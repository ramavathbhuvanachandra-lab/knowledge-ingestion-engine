"""
Command 3 — Baseline Migration Tests.

Purpose:
    Verify that cleaned knowledge can pass through the existing
    structuring and organization architecture.

Pipeline under test:

    02_cleaned
        ↓
    KnowledgeStructurer
        ↓
    structured staging JSON
        ↓
    StructuredKnowledgeOrganizer
        ↓
    03_organized

Important invariants:
    - Command 2 output is treated as the input source of truth.
    - Source provenance survives structuring.
    - One malformed document does not stop the domain run.
    - Intermediate structured files remain isolated from the
      college-facing organized output.
    - The existing organizer is reused rather than rewritten.
"""

import json
from pathlib import Path

from organize_knowledge import run_organization


# ============================================================
# TEST HELPERS
# ============================================================

def _write_markdown(
    path: Path,
    content: str,
) -> None:
    """Write one cleaned Markdown fixture."""

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        content,
        encoding="utf-8",
    )


def _write_metadata(
    path: Path,
    metadata: dict,
) -> None:
    """Write one cleaned metadata fixture."""

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            metadata,
            indent=4,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


# ============================================================
# BASIC MIGRATION
# ============================================================

def test_cleaned_knowledge_reaches_organized_output(
    tmp_path: Path,
):
    """
    A valid cleaned document must travel through 7.4 and 8.3
    and produce an organized knowledge_units.json.
    """

    cleaned_root = (
        tmp_path
        / "02_cleaned"
        / "example.edu"
    )

    structured_root = (
        tmp_path
        / "structured_staging"
    )

    organized_root = (
        tmp_path
        / "03_organized"
    )

    markdown_path = (
        cleaned_root
        / "webpages"
        / "admissions.md"
    )

    metadata_path = (
        cleaned_root
        / "webpages"
        / "admissions.json"
    )

    _write_markdown(
        markdown_path,
        """
# Admissions

## Undergraduate Programs

The college offers undergraduate programmes.

## Eligibility

Applicants must satisfy the eligibility requirements.
""".strip(),
    )

    _write_metadata(
        metadata_path,
        {
            "title": "Admissions",
            "url": (
                "https://example.edu/admissions"
            ),
            "source_url": (
                "https://example.edu/admissions"
            ),
            "document_type": "webpage",
            "knowledge_cleaned": True,
        },
    )

    result = run_organization(
        domain="example.edu",
        cleaned_root=cleaned_root.parent,
        structured_root=structured_root,
        organized_root=organized_root,
    )

    assert result["structured_successfully"] == 1
    assert result["organized_successfully"] == 1

    knowledge_units_path = (
        organized_root
        / "example.edu"
        / "knowledge_units.json"
    )

    assert knowledge_units_path.exists()

    manifest = json.loads(
        knowledge_units_path.read_text(
            encoding="utf-8"
        )
    )

    assert manifest["total_knowledge_units"] > 0


# ============================================================
# PROVENANCE
# ============================================================

def test_source_url_survives_command_3(
    tmp_path: Path,
):
    """
    The original official source URL must remain available after
    structuring and organization.
    """

    cleaned_root = (
        tmp_path
        / "02_cleaned"
        / "example.edu"
    )

    structured_root = (
        tmp_path
        / "structured_staging"
    )

    organized_root = (
        tmp_path
        / "03_organized"
    )

    markdown_path = (
        cleaned_root
        / "documents"
        / "admission-notice.md"
    )

    metadata_path = (
        cleaned_root
        / "documents"
        / "admission-notice.json"
    )

    source_url = (
        "https://example.edu/files/"
        "admission-notice.pdf"
    )

    _write_markdown(
        markdown_path,
        """
# Admission Notice

Applications for the postgraduate programme
are currently open.
""".strip(),
    )

    _write_metadata(
        metadata_path,
        {
            "source_url": source_url,
            "source_file": (
                "storage/documents/"
                "example.edu/"
                "admission-notice.pdf"
            ),
            "document_type": "pdf",
            "knowledge_cleaned": True,
        },
    )

    result = run_organization(
        domain="example.edu",
        cleaned_root=cleaned_root.parent,
        structured_root=structured_root,
        organized_root=organized_root,
    )

    assert result["organized_successfully"] == 1

    knowledge_units_path = (
        organized_root
        / "example.edu"
        / "knowledge_units.json"
    )

    manifest = json.loads(
        knowledge_units_path.read_text(
            encoding="utf-8"
        )
    )

    units = manifest["units"]

    assert units

    assert any(
        unit.get("source_url")
        == source_url
        for unit in units
    )


# ============================================================
# FAILURE ISOLATION
# ============================================================

def test_bad_document_does_not_stop_domain(
    tmp_path: Path,
):
    """
    One malformed cleaned document must not prevent another
    valid document from reaching the organizer.
    """

    cleaned_root = (
        tmp_path
        / "02_cleaned"
        / "example.edu"
    )

    structured_root = (
        tmp_path
        / "structured_staging"
    )

    organized_root = (
        tmp_path
        / "03_organized"
    )

    good_markdown = (
        cleaned_root
        / "webpages"
        / "good.md"
    )

    good_metadata = (
        cleaned_root
        / "webpages"
        / "good.json"
    )

    _write_markdown(
        good_markdown,
        """
# College Overview

The college was established in 1990.
""".strip(),
    )

    _write_metadata(
        good_metadata,
        {
            "title": "College Overview",
            "url": (
                "https://example.edu/overview"
            ),
            "document_type": "webpage",
        },
    )

    bad_markdown = (
        cleaned_root
        / "webpages"
        / "broken.md"
    )

    bad_metadata = (
        cleaned_root
        / "webpages"
        / "broken.json"
    )

    _write_markdown(
        bad_markdown,
        "# Broken",
    )

    bad_metadata.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    bad_metadata.write_text(
        "{invalid-json",
        encoding="utf-8",
    )

    result = run_organization(
        domain="example.edu",
        cleaned_root=cleaned_root.parent,
        structured_root=structured_root,
        organized_root=organized_root,
    )

    assert result["organized_successfully"] == 1
    assert result["failed"] == 1

    knowledge_units_path = (
        organized_root
        / "example.edu"
        / "knowledge_units.json"
    )

    assert knowledge_units_path.exists()