"""
Command 3 — Real IITJ Knowledge Value Filter Validation.

This test runs the value filter against the real structured IITJ
corpus used by the Command 3 migration tests.

It does NOT modify the source corpus.

The generated report is only for inspection and debugging.
"""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

from processors.knowledge_value_filter import (
    KnowledgeValueFilter,
)


# ======================================================================
# REAL TEST CORPUS
# ======================================================================

STRUCTURED_ROOT = Path(
    "storage/test3_structured_v2"
)

DOMAIN = "www.iitj.ac.in"

REPORT_PATH = Path(
    "storage/test4_value_filter_report.json"
)


# ======================================================================
# JSON HELPERS
# ======================================================================


def _load_json(
    path: Path,
) -> dict:
    """Load one structured JSON document."""

    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def _extract_document_metadata(
    data: dict,
) -> dict:
    """Extract structured document metadata."""

    metadata = data.get(
        "document",
        {},
    )

    if not isinstance(
        metadata,
        dict,
    ):
        return {}

    return metadata


def _extract_sections(
    data: dict,
) -> list[dict]:
    """
    Extract all structured sections from a document.
    """

    sections: list[dict] = []

    pages = data.get(
        "pages",
        [],
    )

    if not isinstance(
        pages,
        list,
    ):
        return sections

    for page in pages:

        if not isinstance(
            page,
            dict,
        ):
            continue

        page_sections = page.get(
            "sections",
            [],
        )

        if not isinstance(
            page_sections,
            list,
        ):
            continue

        for section in page_sections:

            if isinstance(
                section,
                dict,
            ):
                sections.append(
                    section
                )

    return sections


def _section_text(
    section: dict,
) -> str:
    """
    Convert structured section content into plain text.
    """

    content = section.get(
        "content",
        [],
    )

    if isinstance(
        content,
        str,
    ):
        return content

    if not isinstance(
        content,
        list,
    ):
        return ""

    parts: list[str] = []

    for item in content:

        if isinstance(
            item,
            str,
        ):
            parts.append(
                item
            )

            continue

        if not isinstance(
            item,
            dict,
        ):
            continue

        value = item.get(
            "text"
        )

        if isinstance(
            value,
            str,
        ):
            parts.append(
                value
            )

    return "\n".join(
        parts
    )


# ======================================================================
# REAL-DATA TEST
# ======================================================================


def test_real_iitj_value_filter():
    """
    Run the value filter over the complete real IITJ corpus.

    The test itself only verifies that the filter can process the
    corpus and produce meaningful decisions.

    Classification quality is inspected through the generated report.
    """

    domain_root = (
        STRUCTURED_ROOT
        / DOMAIN
    )

    assert domain_root.exists(), (
        "Missing structured IITJ corpus: "
        f"{domain_root}"
    )

    assert domain_root.is_dir(), (
        "Structured IITJ corpus is not a directory: "
        f"{domain_root}"
    )

    json_files = sorted(
        domain_root.rglob(
            "*.json"
        )
    )

    assert json_files, (
        "No structured JSON files found in: "
        f"{domain_root}"
    )

    value_filter = (
        KnowledgeValueFilter()
    )

    decision_counts = Counter()

    examples = {
        "KEEP": [],
        "CONSOLIDATE": [],
        "EXCLUDE": [],
        "REVIEW": [],
    }

    processing_failures = []

    total_sections = 0

    # --------------------------------------------------------------
    # Process every structured document.
    # --------------------------------------------------------------

    for json_path in json_files:

        try:

            data = _load_json(
                json_path
            )

            metadata = (
                _extract_document_metadata(
                    data
                )
            )

            title = str(
                metadata.get(
                    "title",
                    "",
                )
            )

            url = str(
                metadata.get(
                    "url",
                    metadata.get(
                        "source_url",
                        "",
                    ),
                )
            )

            document_type = str(
                metadata.get(
                    "document_type",
                    "",
                )
            )

            sections = (
                _extract_sections(
                    data
                )
            )

            for section in sections:

                total_sections += 1

                heading = str(
                    section.get(
                        "heading",
                        "",
                    )
                )

                text = _section_text(
                    section
                )

                section_path = (
                    section.get(
                        "section_path",
                        [],
                    )
                )

                if not isinstance(
                    section_path,
                    list,
                ):
                    section_path = []

                result = (
                    value_filter.classify(
                        heading=heading,
                        text=text,
                        source_name=(
                            json_path.name
                        ),
                        document_title=title,
                        document_url=url,
                        content_type=(
                            document_type
                        ),
                        section_path=(
                            section_path
                        ),
                    )
                )

                decision = result[
                    "decision"
                ]

                decision_counts[
                    decision
                ] += 1

                # --------------------------------------------------
                # Keep representative examples for inspection.
                # --------------------------------------------------

                if (
                    decision in examples
                    and len(
                        examples[
                            decision
                        ]
                    ) < 50
                ):

                    examples[
                        decision
                    ].append(
                        {
                            "source": str(
                                json_path
                            ),
                            "title": title,
                            "url": url,
                            "heading": heading,
                            "text": text[:800],
                            "confidence": (
                                result[
                                    "confidence"
                                ]
                            ),
                            "score": (
                                result[
                                    "score"
                                ]
                            ),
                            "reasons": (
                                result[
                                    "reasons"
                                ]
                            ),
                        }
                    )

        except Exception as error:

            processing_failures.append(
                {
                    "file": str(
                        json_path
                    ),
                    "error": (
                        f"{type(error).__name__}: "
                        f"{error}"
                    ),
                }
            )

    # ==================================================================
    # REPORT
    # ==================================================================

    report = {
        "test": (
            "real_iitj_knowledge_value_filter"
        ),
        "domain": DOMAIN,
        "structured_root": str(
            domain_root
        ),
        "structured_files": len(
            json_files
        ),
        "total_sections": (
            total_sections
        ),
        "decision_counts": dict(
            decision_counts
        ),
        "processing_failures": (
            processing_failures
        ),
        "examples": examples,
    }

    REPORT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_PATH.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    # ==================================================================
    # CONSOLE OUTPUT
    # ==================================================================

    print(
        "\n"
        "============================================================"
    )

    print(
        "REAL IITJ KNOWLEDGE VALUE FILTER"
    )

    print(
        "============================================================"
    )

    print(
        "\nStructured files:",
        len(json_files),
    )

    print(
        "Total sections:",
        total_sections,
    )

    print(
        "\nDecision counts:"
    )

    for decision in (
        "KEEP",
        "CONSOLIDATE",
        "EXCLUDE",
        "REVIEW",
    ):

        print(
            f"  {decision:<14}",
            decision_counts[
                decision
            ],
        )

    print(
        "\nProcessing failures:",
        len(
            processing_failures
        ),
    )

    print(
        "\nReport:",
        REPORT_PATH,
    )

    # --------------------------------------------------------------
    # We only require that the real corpus was actually processed.
    #
    # We deliberately do NOT assert percentages here.
    #
    # The purpose of this test is to expose real classification
    # behavior for inspection before production integration.
    # --------------------------------------------------------------

    assert total_sections > 0, (
        "No structured sections were processed."
    )

    assert decision_counts, (
        "The value filter produced no decisions."
    )