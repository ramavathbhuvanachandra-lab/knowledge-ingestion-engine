"""
Command 2 — Cleaning Boundary Tests

Purpose:
    Define the production contract for Command 2 before
    implementing the command itself.

Pipeline:

    01_crawled + processed_documents
        ↓
    Command 2
        ↓
    02_cleaned

Important invariants:
    - Raw input is never modified.
    - Useful factual content must survive cleaning.
    - Obvious website/UI noise may be removed.
    - Source provenance must survive.
    - Webpages and processed documents use the same
      cleaning contract.
    - One bad input must not destroy the whole run.
"""

import json
from pathlib import Path

import pytest

from clean_knowledge import run_cleaning


# ============================================================
# TEST HELPERS
# ============================================================

def _write_markdown(
    path: Path,
    content: str,
) -> None:
    """Write a UTF-8 Markdown fixture."""
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
    """Write a JSON metadata fixture."""
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
# COMMAND 2 — BASIC WEBPAGE CLEANING
# ============================================================

def test_webpage_is_cleaned_and_preserved(
    tmp_path: Path,
):
    """
    A crawled webpage must produce cleaned Markdown
    while preserving real factual content.
    """

    crawled_root = (
        tmp_path
        / "01_crawled"
        / "example.edu"
        / "pages"
    )

    processed_documents_root = (
        tmp_path
        / "processed_documents"
        / "example.edu"
    )

    output_root = (
        tmp_path
        / "02_cleaned"
    )

    markdown_path = (
        crawled_root
        / "admissions.md"
    )

    metadata_path = (
        crawled_root
        / "admissions.json"
    )

    _write_markdown(
        markdown_path,
        """
# Admissions

Main Menu
Accessibility Options Ctrl+F2

The Bachelor of Technology programme is offered
for eligible students.

Important Links

Application deadlines are published by the
Admissions Office.
""".strip(),
    )

    _write_metadata(
        metadata_path,
        {
            "title": "Admissions",
            "url": (
                "https://example.edu/admissions"
            ),
            "success": True,
        },
    )

    result = run_cleaning(
        domain="example.edu",
        crawled_root=crawled_root.parent.parent,
        processed_documents_root=processed_documents_root.parent,
        output_root=output_root,
    )

    assert result["cleaned_successfully"] == 1

    cleaned_path = (
        output_root
        / "example.edu"
        / "webpages"
        / "admissions.md"
    )

    assert cleaned_path.exists()

    cleaned = cleaned_path.read_text(
        encoding="utf-8"
    )

    # Obvious website machinery must disappear.
    assert "Main Menu" not in cleaned
    assert "Accessibility Options Ctrl+F2" not in cleaned

    # Real factual knowledge must survive.
    assert (
        "Bachelor of Technology programme"
        in cleaned
    )

    assert (
        "Application deadlines"
        in cleaned
    )


# ============================================================
# COMMAND 2 — PROCESSED DOCUMENT INPUT
# ============================================================

def test_processed_document_is_cleaned(
    tmp_path: Path,
):
    """
    Already-extracted PDF/DOCX/etc. Markdown must enter
    the same cleaning contract as webpage Markdown.
    """

    crawled_root = (
        tmp_path
        / "01_crawled"
        / "example.edu"
        / "pages"
    )

    processed_documents_root = (
        tmp_path
        / "processed_documents"
        / "example.edu"
    )

    output_root = (
        tmp_path
        / "02_cleaned"
    )

    markdown_path = (
        processed_documents_root
        / "admission-notice.md"
    )

    metadata_path = (
        processed_documents_root
        / "admission-notice.json"
    )

    _write_markdown(
        markdown_path,
        """
## Page 1

PROVISIONALLY SHORTLISTED CANDIDATES

Application Number
10001
10002
10003
""".strip(),
    )

    source_url = (
        "https://example.edu/files/admission-notice.pdf"
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
            "pages": 1,
            "pages_with_text": 1,
            "text_length": 88,
            "extraction_success": True,
        },
    )

    result = run_cleaning(
        domain="example.edu",
        crawled_root=crawled_root.parent.parent,
        processed_documents_root=processed_documents_root.parent,
        output_root=output_root,
    )

    assert result["cleaned_successfully"] == 1

    cleaned_path = (
        output_root
        / "example.edu"
        / "documents"
        / "admission-notice.md"
    )

    cleaned_metadata_path = (
        output_root
        / "example.edu"
        / "documents"
        / "admission-notice.json"
    )

    assert cleaned_path.exists()
    assert cleaned_metadata_path.exists()

    cleaned = cleaned_path.read_text(
        encoding="utf-8"
    )

    metadata = json.loads(
        cleaned_metadata_path.read_text(
            encoding="utf-8"
        )
    )

    # Command 2 must preserve real document content.
    assert (
        "PROVISIONALLY SHORTLISTED CANDIDATES"
        in cleaned
    )

    assert "10001" in cleaned

    # Official source provenance must survive.
    assert (
        metadata["source_url"]
        == source_url
    )


# ============================================================
# COMMAND 2 — BAD INPUT ISOLATION
# ============================================================

def test_one_bad_document_does_not_stop_the_run(
    tmp_path: Path,
):
    """
    One malformed input must be recorded as a failure
    while valid inputs continue processing.
    """

    crawled_root = (
        tmp_path
        / "01_crawled"
        / "example.edu"
        / "pages"
    )

    processed_documents_root = (
        tmp_path
        / "processed_documents"
        / "example.edu"
    )

    output_root = (
        tmp_path
        / "02_cleaned"
    )

    good_markdown = (
        crawled_root
        / "good.md"
    )

    good_metadata = (
        crawled_root
        / "good.json"
    )

    _write_markdown(
        good_markdown,
        """
# Overview

This university offers undergraduate programmes.
""".strip(),
    )

    _write_metadata(
        good_metadata,
        {
            "title": "Overview",
            "url": (
                "https://example.edu/overview"
            ),
            "success": True,
        },
    )

    bad_markdown = (
        crawled_root
        / "broken.md"
    )

    bad_metadata = (
        crawled_root
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

    result = run_cleaning(
        domain="example.edu",
        crawled_root=crawled_root.parent.parent,
        processed_documents_root=processed_documents_root.parent,
        output_root=output_root,
    )

    assert result["cleaned_successfully"] == 1
    assert result["failed"] == 1

    cleaned_good = (
        output_root
        / "example.edu"
        / "webpages"
        / "good.md"
    )

    assert cleaned_good.exists()


# ============================================================
# COMMAND 2 — RAW INPUT MUST REMAIN UNCHANGED
# ============================================================

def test_raw_input_is_not_modified(
    tmp_path: Path,
):
    """
    Command 2 must never modify the raw crawler source.
    """

    crawled_root = (
        tmp_path
        / "01_crawled"
        / "example.edu"
        / "pages"
    )

    processed_documents_root = (
        tmp_path
        / "processed_documents"
        / "example.edu"
    )

    output_root = (
        tmp_path
        / "02_cleaned"
    )

    markdown_path = (
        crawled_root
        / "page.md"
    )

    metadata_path = (
        crawled_root
        / "page.json"
    )

    original_markdown = """
# College Overview

Main Menu

This college was established in 1990.
""".strip()

    _write_markdown(
        markdown_path,
        original_markdown,
    )

    _write_metadata(
        metadata_path,
        {
            "title": "College Overview",
            "url": (
                "https://example.edu/overview"
            ),
            "success": True,
        },
    )

    run_cleaning(
        domain="example.edu",
        crawled_root=crawled_root.parent.parent,
        processed_documents_root=processed_documents_root.parent,
        output_root=output_root,
    )

    assert (
        markdown_path.read_text(
            encoding="utf-8"
        )
        == original_markdown
    )