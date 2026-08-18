"""
Real-data validation for the universal knowledge record segmenter.

This test does not modify production data.

It measures whether the generic record segmentation logic can
recognize repeated records in a real extracted institutional
research document.
"""

from pathlib import Path

from processors.knowledge_record_segmenter import (
    KnowledgeRecordSegmenter,
)


RESEARCH_DOCUMENT = Path(
    "storage/processed_documents/www.iitj.ac.in/"
    "website-research-projects-638772906605230764.md"
)


def test_real_research_document_segmentation():

    assert RESEARCH_DOCUMENT.exists(), (
        f"Missing test document: {RESEARCH_DOCUMENT}"
    )

    text = RESEARCH_DOCUMENT.read_text(
        encoding="utf-8"
    )

    assert text.strip()

    segmenter = (
        KnowledgeRecordSegmenter()
    )

    records = segmenter.segment(
        text=text,
        start_line=1,
    )

    print(
        "\nDetected records:",
        len(records),
    )

    for record in records[:10]:
        print(
            record["record_index"],
            "lines",
            record["start_line"],
            "-",
            record["end_line"],
        )

    assert len(records) >= 2

    assert all(
        record["text"].strip()
        for record in records
    )

    assert all(
        record["record_index"] is not None
        for record in records
    )