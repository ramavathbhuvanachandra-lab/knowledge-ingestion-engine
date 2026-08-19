"""
Real IIT Jodhpur Entity Discovery Validation.

Purpose
-------
Run KnowledgeEntityDiscovery against the complete real IIT Jodhpur
Phase 7.4 structured corpus.

Real Phase 7.4 schema:

    {
        "document": {
            "title": "...",
            "url": "...",
            "domain": "...",
            "category": "...",
            "document_type": "...",
            "source_file": "..."
        },
        "pages": [
            {
                "page_number": 1,
                "sections": [
                    {
                        "heading": "...",
                        "level": 1,
                        "content": [...],
                        "content_type": "...",
                        "content_length": ...
                    }
                ]
            }
        ]
    }

KnowledgeEntityDiscovery receives a generic representation:

    {
        "source": "...",
        "title": "...",
        "url": "...",
        "sections": [
            {
                "heading": "...",
                "text": "..."
            }
        ]
    }

Important
---------
This test only adapts the real structured corpus into the generic
entity-discovery input contract.

It does NOT:
    - modify production data
    - modify KnowledgeEntityDiscovery
    - create folders
    - create taxonomy
    - filter source knowledge
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

DOMAIN = (
    "www.iitj.ac.in"
)

REPORT_PATH = Path(
    "storage/test4_iitj_entity_discovery_report.json"
)


# ============================================================
# CONTENT NORMALIZATION
# ============================================================

def _content_to_text(
    content,
) -> str:
    """
    Convert structured section content into plain text.

    Supported forms:
        - string
        - list of strings
        - list of dictionaries
        - mixed lists

    The real Phase 7.4 corpus primarily uses list[str].
    """

    if content is None:
        return ""

    # --------------------------------------------------------
    # Direct string.
    # --------------------------------------------------------

    if isinstance(
        content,
        str,
    ):

        return content.strip()

    # --------------------------------------------------------
    # List content.
    # --------------------------------------------------------

    if isinstance(
        content,
        list,
    ):

        parts = []

        for item in content:

            # ------------------------------------------------
            # Normal string item.
            # ------------------------------------------------

            if isinstance(
                item,
                str,
            ):

                value = item.strip()

                if value:
                    parts.append(
                        value
                    )

                continue

            # ------------------------------------------------
            # Dictionary content item.
            # ------------------------------------------------

            if isinstance(
                item,
                dict,
            ):

                value = item.get(
                    "text",
                    "",
                )

                if value is None:
                    value = ""

                value = str(
                    value
                ).strip()

                if value:
                    parts.append(
                        value
                    )

        return "\n".join(
            parts
        )

    # --------------------------------------------------------
    # Defensive fallback.
    # --------------------------------------------------------

    return str(
        content
    ).strip()


# ============================================================
# SINGLE DOCUMENT ADAPTER
# ============================================================

def _load_document(
    path: Path,
) -> dict:
    """
    Load one real Phase 7.4 JSON file and convert it into the
    generic document representation expected by entity discovery.
    """

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

    # --------------------------------------------------------
    # Document metadata.
    # --------------------------------------------------------

    metadata = data.get(
        "document",
        {},
    )

    if not isinstance(
        metadata,
        dict,
    ):
        metadata = {}

    title = str(
        metadata.get(
            "title",
            "",
        )
        or ""
    ).strip()

    url = str(
        metadata.get(
            "url",
            "",
        )
        or ""
    ).strip()

    source_file = metadata.get(
        "source_file"
    )

    if source_file:

        source = str(
            source_file
        ).strip()

    elif url:

        source = url

    else:

        source = str(
            path
        )

    # --------------------------------------------------------
    # Pages.
    # --------------------------------------------------------

    pages = data.get(
        "pages",
        [],
    )

    if not isinstance(
        pages,
        list,
    ):
        raise ValueError(
            "Structured document 'pages' must be a list."
        )

    sections = []

    # --------------------------------------------------------
    # Extract sections from every page.
    # --------------------------------------------------------

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
            ).strip()

            text = _content_to_text(
                section.get(
                    "content",
                    [],
                )
            )

            # ------------------------------------------------
            # Preserve a heading even when content is empty.
            #
            # This matters because headings such as:
            #     Vision
            #     Mission
            #     Departments
            #     Faculty
            #
            # can carry semantic information even when the
            # extractor produced little body text.
            # ------------------------------------------------

            if (
                not heading
                and not text
            ):
                continue

            sections.append(
                {
                    "heading": heading,
                    "text": text,
                }
            )

    return {
        "source": source,
        "title": title,
        "url": url,
        "sections": sections,
        "_file": str(path),
    }


# ============================================================
# COMPLETE CORPUS LOADER
# ============================================================

def _load_documents(
    domain_root: Path,
) -> tuple[
    list[dict],
    list[dict],
]:
    """
    Load every structured JSON document.

    One malformed file must not stop the entire real-data test.
    """

    documents = []

    failures = []

    files = sorted(
        domain_root.rglob(
            "*.json"
        )
    )

    for path in files:

        try:

            document = _load_document(
                path
            )

            # ------------------------------------------------
            # Completely empty documents are ignored.
            # ------------------------------------------------

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
                    "file": str(
                        path
                    ),
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
    """
    Print discovered entities grouped by type.
    """

    entities = result.get(
        "entities",
        [],
    )

    print()
    print(
        "=" * 80
    )
    print(
        "ENTITY DISCOVERY AUDIT"
    )
    print(
        "=" * 80
    )

    print()

    print(
        "Total entities discovered:",
        len(
            entities
        ),
    )

    # --------------------------------------------------------
    # Entity counts.
    # --------------------------------------------------------

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
            f"  {entity_type:<30} {count}"
        )

    # --------------------------------------------------------
    # Group entities.
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

    # --------------------------------------------------------
    # Detailed audit.
    # --------------------------------------------------------

    for entity_type in sorted(
        grouped
    ):

        print()

        print(
            "-" * 80
        )

        print(
            entity_type.upper()
        )

        print(
            "-" * 80
        )

        items = sorted(
            grouped[
                entity_type
            ],
            key=lambda entity: (
                -entity.get(
                    "mention_count",
                    0,
                ),
                str(
                    entity.get(
                        "normalized_name",
                        entity.get(
                            "name",
                            "",
                        ),
                    )
                ),
            ),
        )

        for entity in items:

            print(
                f"  {entity.get('name', '')}"
                f" | mentions="
                f"{entity.get('mention_count', 0)}"
                f" | confidence="
                f"{entity.get('confidence', 'unknown')}"
                f" | score="
                f"{entity.get('max_score', 0)}"
            )


# ============================================================
# REPORT
# ============================================================

def _write_report(
    *,
    result: dict,
    files_found: int,
    documents_loaded: int,
    failures: list[dict],
) -> None:
    """
    Save the complete real-data entity discovery audit.
    """

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
    """
    Run entity discovery over the complete real IITJ corpus.
    """

    domain_root = (
        STRUCTURED_ROOT
        / DOMAIN
    )

    # --------------------------------------------------------
    # Corpus existence.
    # --------------------------------------------------------

    assert domain_root.exists(), (
        "Missing structured corpus: "
        f"{domain_root}"
    )

    files = sorted(
        domain_root.rglob(
            "*.json"
        )
    )

    assert files, (
        "No structured JSON files found: "
        f"{domain_root}"
    )

    # --------------------------------------------------------
    # Load real corpus.
    # --------------------------------------------------------

    documents, failures = (
        _load_documents(
            domain_root
        )
    )

    print()

    print(
        "=" * 80
    )

    print(
        "REAL IITJ KNOWLEDGE ENTITY DISCOVERY"
    )

    print(
        "=" * 80
    )

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
    # Discovery must have usable input.
    # --------------------------------------------------------

    assert documents, (
        "No usable structured documents "
        "were loaded."
    )

    # --------------------------------------------------------
    # Create universal discovery engine.
    # --------------------------------------------------------

    discovery = (
        KnowledgeEntityDiscovery()
    )

    # --------------------------------------------------------
    # Discover entities.
    # --------------------------------------------------------

    result = discovery.discover(
        documents=documents
    )

    # --------------------------------------------------------
    # Print audit.
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

    print(
        "=" * 80
    )

    print(
        "REPORT"
    )

    print(
        "=" * 80
    )

    print(
        REPORT_PATH
    )

    print()

    print(
        "=" * 80
    )

    print(
        "TEST COMPLETE"
    )

    print(
        "=" * 80
    )

    # --------------------------------------------------------
    # Generic integrity checks.
    #
    # We deliberately do NOT assert an exact entity count.
    # The system is supposed to work across different
    # institutions and therefore the count must remain dynamic.
    # --------------------------------------------------------

    assert result[
        "entity_count"
    ] > 0

    assert result[
        "evidence_count"
    ] > 0

    assert isinstance(
        result[
            "entities"
        ],
        list,
    )