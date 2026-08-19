"""
Real IIT Jodhpur entity-discovery validation.

Reads the actual Phase 7.4 structured JSON schema:

    {
        "document": {...},
        "pages": [
            {
                "page_number": ...,
                "sections": [...]
            }
        ]
    }

The test converts the real structured representation into the
generic document representation expected by KnowledgeEntityDiscovery.

This test does NOT modify production data.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from processors.knowledge_entity_discovery import (
    KnowledgeEntityDiscovery,
)


# ============================================================
# CONFIGURATION
# ============================================================

STRUCTURED_ROOT = Path(
    "storage/structured_knowledge"
)

DOMAIN = "gwpgc.ac.in"

REPORT_PATH = Path(
    "storage/test4_gwpgc_entity_discovery_report.json"
)


# ============================================================
# LOAD ONE STRUCTURED DOCUMENT
# ============================================================

def _load_document(
    path: Path,
) -> dict:

    data = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(
        data,
        dict,
    ):
        raise ValueError(
            "Structured JSON root must be an object."
        )

    document_metadata = data.get(
        "document",
        {},
    )

    if not isinstance(
        document_metadata,
        dict,
    ):
        document_metadata = {}

    pages = data.get(
        "pages",
        [],
    )

    if not isinstance(
        pages,
        list,
    ):
        pages = []

    sections = []

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

            if not isinstance(
                section,
                dict,
            ):
                continue

            heading = str(
                section.get(
                    "heading",
                    "",
                )
                or ""
            )

            content = section.get(
                "content",
                [],
            )

            # ----------------------------------------------------
            # Real structured corpus stores section content as a
            # list of strings.
            # ----------------------------------------------------

            if isinstance(
                content,
                list,
            ):

                text_parts = []

                for item in content:

                    if isinstance(
                        item,
                        str,
                    ):

                        value = item.strip()

                        if value:
                            text_parts.append(
                                value
                            )

                    elif isinstance(
                        item,
                        dict,
                    ):

                        value = str(
                            item.get(
                                "text",
                                "",
                            )
                            or ""
                        ).strip()

                        if value:
                            text_parts.append(
                                value
                            )

                text = "\n".join(
                    text_parts
                )

            else:

                text = str(
                    content
                    or ""
                )

            if (
                not heading.strip()
                and not text.strip()
            ):
                continue

            sections.append(
                {
                    "heading": heading,
                    "text": text,
                }
            )

    title = str(
        document_metadata.get(
            "title",
            "",
        )
        or ""
    )

    url = str(
        document_metadata.get(
            "url",
            "",
        )
        or ""
    )

    source = str(
        document_metadata.get(
            "source_file",
            url,
        )
        or url
        or path,
    )

    return {
        "source": source,
        "title": title,
        "url": url,
        "sections": sections,
        "_structured_file": str(path),
    }


# ============================================================
# LOAD COMPLETE CORPUS
# ============================================================

def _load_corpus(
    domain_root: Path,
) -> tuple[list[dict], list[dict]]:

    documents = []
    failures = []

    files = sorted(
        domain_root.rglob("*.json")
    )

    for path in files:

        try:

            document = _load_document(
                path
            )

            if not document[
                "sections"
            ]:

                continue

            documents.append(
                document
            )

        except Exception as error:

            failures.append(
                {
                    "file": str(path),
                    "error": (
                        f"{type(error).__name__}: "
                        f"{error}"
                    ),
                }
            )

    return (
        documents,
        failures,
    )


# ============================================================
# ENTITY AUDIT
# ============================================================

def _print_entity_audit(
    result: dict,
) -> None:

    entities = result.get(
        "entities",
        [],
    )

    print()
    print("=" * 80)
    print("ENTITY DISCOVERY AUDIT")
    print("=" * 80)

    print()
    print(
        "Total entities discovered:",
        len(entities),
    )

    counts = Counter(
        entity.get(
            "entity_type",
            "unknown",
        )
        for entity in entities
    )

    print()
    print(
        "Entities by type:"
    )

    for entity_type, count in sorted(
        counts.items()
    ):

        print(
            f"  {entity_type:<25} {count}"
        )

    # --------------------------------------------------------
    # Detailed output.
    # --------------------------------------------------------

    grouped = {}

    for entity in entities:

        entity_type = entity.get(
            "entity_type",
            "unknown",
        )

        grouped.setdefault(
            entity_type,
            [],
        ).append(
            entity
        )

    for entity_type in sorted(
        grouped
    ):

        print()
        print("-" * 80)
        print(
            entity_type.upper()
        )
        print("-" * 80)

        items = sorted(
            grouped[
                entity_type
            ],
            key=lambda item: (
                -item.get(
                    "mention_count",
                    0,
                ),
                item.get(
                    "normalized_name",
                    "",
                ),
            ),
        )

        for entity in items:

            print(
                f"  {entity['name']}"
                f" | mentions="
                f"{entity.get('mention_count', 0)}"
                f" | confidence="
                f"{entity.get('confidence', 'unknown')}"
                f" | score="
                f"{entity.get('max_score', 0)}"
            )


# ============================================================
# WRITE REPORT
# ============================================================

def _write_report(
    *,
    result: dict,
    files_found: int,
    documents_loaded: int,
    failures: list[dict],
) -> None:

    REPORT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    report = {
        "test": (
            "real_iitj_knowledge_entity_discovery"
        ),
        "domain": DOMAIN,
        "structured_root": str(
            STRUCTURED_ROOT
        ),
        "files_found": files_found,
        "documents_loaded": documents_loaded,
        "loading_failures": len(
            failures
        ),
        "failures": failures,
        "entity_discovery": result,
    }

    REPORT_PATH.write_text(
        json.dumps(
            report,
            indent=4,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


# ============================================================
# REAL IITJ TEST
# ============================================================

def test_real_iitj_entity_discovery():

    domain_root = (
        STRUCTURED_ROOT
        / DOMAIN
    )

    assert domain_root.exists(), (
        f"Missing structured corpus: "
        f"{domain_root}"
    )

    files = sorted(
        domain_root.rglob("*.json")
    )

    assert files, (
        f"No structured JSON files found: "
        f"{domain_root}"
    )

    documents, failures = (
        _load_corpus(
            domain_root
        )
    )

    print()
    print("=" * 80)
    print("REAL IITJ KNOWLEDGE ENTITY DISCOVERY")
    print("=" * 80)

    print()
    print(
        "Structured files:",
        len(files),
    )

    print(
        "Documents loaded:",
        len(documents),
    )

    print(
        "Loading failures:",
        len(failures),
    )

    # --------------------------------------------------------
    # Discovery.
    # --------------------------------------------------------

    discovery = (
        KnowledgeEntityDiscovery()
    )

    result = discovery.discover(
        documents=documents
    )

    # --------------------------------------------------------
    # Print results.
    # --------------------------------------------------------

    _print_entity_audit(
        result
    )

    # --------------------------------------------------------
    # Save report.
    # --------------------------------------------------------

    _write_report(
        result=result,
        files_found=len(files),
        documents_loaded=len(
            documents
        ),
        failures=failures,
    )

    print()
    print("=" * 80)
    print("REPORT")
    print("=" * 80)

    print(
        REPORT_PATH
    )

    print()
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

    # --------------------------------------------------------
    # Basic integrity checks.
    #
    # We deliberately do NOT assert an exact entity count.
    # This is real institutional data and the taxonomy is
    # intentionally dynamic.
    # --------------------------------------------------------

    assert documents

    assert result[
        "entity_count"
    ] > 0

    assert result[
        "evidence_count"
    ] > 0