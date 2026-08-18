"""
Command 2 — Clean Knowledge.

Purpose:
    Convert webpage and processed-document Markdown into the
    canonical cleaned knowledge layer.

Input:
    - 01_crawled/<domain>/pages/
    - processed_documents/<domain>/

Output:
    - 02_cleaned/<domain>/webpages/
    - 02_cleaned/<domain>/documents/
    - cleaning_manifest.json

Important invariants:
    - Raw inputs are never modified.
    - KnowledgeCleaner owns cleaning logic.
    - This command does not perform semantic organization.
    - Source provenance is preserved.
    - One bad input does not stop the complete run.
"""

from __future__ import annotations

import json
from pathlib import Path

from processors.knowledge_cleaner import KnowledgeCleaner


# ============================================================
# INPUT DISCOVERY
# ============================================================

def _discover_inputs(
    root: Path,
) -> list[tuple[Path, Path]]:
    """
    Discover valid Markdown + metadata pairs.
    """

    if not root.exists():
        return []

    if not root.is_dir():
        raise ValueError(
            f"Input path is not a directory: {root}"
        )

    inputs = []

    for markdown_path in sorted(
        root.rglob("*.md")
    ):
        metadata_path = (
            markdown_path.with_suffix(".json")
        )

        if not metadata_path.exists():
            raise FileNotFoundError(
                "Missing metadata for Markdown file: "
                f"{markdown_path}"
            )

        if not metadata_path.is_file():
            raise ValueError(
                "Metadata path is not a file: "
                f"{metadata_path}"
            )

        inputs.append(
            (
                markdown_path,
                metadata_path,
            )
        )

    return inputs


# ============================================================
# METADATA
# ============================================================

def _load_metadata(
    metadata_path: Path,
) -> dict:
    """
    Load and validate one metadata JSON object.
    """

    try:
        metadata = json.loads(
            metadata_path.read_text(
                encoding="utf-8"
            )
        )

    except json.JSONDecodeError as error:

        raise ValueError(
            f"Invalid JSON metadata: "
            f"{metadata_path}"
        ) from error

    if not isinstance(
        metadata,
        dict,
    ):
        raise ValueError(
            f"Metadata must be a JSON object: "
            f"{metadata_path}"
        )

    return metadata


# ============================================================
# SOURCE TYPE
# ============================================================

def _source_type(
    metadata: dict,
) -> str:
    """
    Determine the canonical source type.

    Processed files with document_type are treated as external
    documents. Raw crawler pages are treated as webpages.
    """

    if metadata.get("document_type"):
        return "documents"

    return "webpages"


# ============================================================
# METADATA NORMALIZATION
# ============================================================

def _normalize_metadata(
    metadata: dict,
) -> dict:
    """
    Preserve all existing metadata while ensuring that source_url
    is consistently available when a source URL exists.
    """

    normalized = dict(
        metadata
    )

    source_url = (
        normalized.get("url")
        or normalized.get("source_url")
    )

    if source_url:
        normalized["source_url"] = (
            source_url
        )

    return normalized


# ============================================================
# PUBLIC COMMAND API
# ============================================================

def run_cleaning(
    *,
    domain: str,
    crawled_root: str | Path,
    processed_documents_root: str | Path,
    output_root: str | Path,
) -> dict:
    """
    Run Command 2 for one website/domain.
    """

    crawled_root = Path(
        crawled_root
    )

    processed_documents_root = Path(
        processed_documents_root
    )

    output_root = Path(
        output_root
    )

    crawler_pages_root = (
        crawled_root
        / domain
        / "pages"
    )

    processed_domain_root = (
        processed_documents_root
        / domain
    )

    output_domain_root = (
        output_root
        / domain
    )

    webpage_inputs = _discover_inputs(
        crawler_pages_root
    )

    document_inputs = _discover_inputs(
        processed_domain_root
    )

    inputs = [
        (
            "webpages",
            markdown_path,
            metadata_path,
        )
        for markdown_path, metadata_path
        in webpage_inputs
    ]

    inputs.extend(
        (
            "documents",
            markdown_path,
            metadata_path,
        )
        for markdown_path, metadata_path
        in document_inputs
    )

    cleaned_successfully = 0
    failed = 0
    failures = []

    # --------------------------------------------------------
    # PROCESS EACH INPUT INDEPENDENTLY
    # --------------------------------------------------------

    for source_type, markdown_path, metadata_path in inputs:

        try:
            metadata = _load_metadata(
                metadata_path
            )

            metadata = _normalize_metadata(
                metadata
            )

            resolved_source_type = (
                _source_type(
                    metadata
                )
            )

            # Webpage discovery is always written to webpages.
            # Processed documents are always written to documents.
            if source_type == "documents":
                resolved_source_type = "documents"
            else:
                resolved_source_type = "webpages"

            cleaner = KnowledgeCleaner(
                output_path=output_root
            )

            cleaner.clean(
                markdown_path=markdown_path,
                metadata_path=metadata_path,
                output_domain=domain,
                output_category=resolved_source_type,
            )

            cleaned_successfully += 1

        except Exception as error:

            failed += 1

            failures.append(
                {
                    "markdown": str(
                        markdown_path
                    ),
                    "metadata": str(
                        metadata_path
                    ),
                    "error": str(error),
                }
            )

    # ========================================================
    # CLEANING MANIFEST
    # ========================================================

    output_domain_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    manifest = {
        "command": "clean_knowledge",
        "command_version": "1.0",
        "domain": domain,
        "input_webpages": len(
            webpage_inputs
        ),
        "input_documents": len(
            document_inputs
        ),
        "total_inputs": len(
            inputs
        ),
        "cleaned_successfully": (
            cleaned_successfully
        ),
        "failed": failed,
        "failures": failures,
    }

    manifest_path = (
        output_domain_root
        / "cleaning_manifest.json"
    )

    manifest_path.write_text(
        json.dumps(
            manifest,
            indent=4,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return manifest