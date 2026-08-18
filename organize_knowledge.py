"""
Command 3 — Knowledge Refinement and Organization.

Current responsibility:
    Connect the new Command 2 cleaned-knowledge layer to the
    existing Phase 7.4 structurer and Phase 8.3 organizer.

Current pipeline:

    02_cleaned
        ↓
    KnowledgeStructurer
        ↓
    structured staging
        ↓
    StructuredKnowledgeOrganizer
        ↓
    03_organized

Important:
    This version intentionally preserves the existing 7.4/8.3
    organization behavior.

    Dynamic entity/relationship organization is a later refinement
    after this migration boundary is proven.
"""

from __future__ import annotations

import json
from pathlib import Path

from processors.knowledge_structurer import (
    KnowledgeStructurer,
)

from processors.structured_knowledge_organizer import (
    StructuredKnowledgeOrganizer,
)


# ============================================================
# INPUT DISCOVERY
# ============================================================

def _discover_inputs(
    cleaned_domain_root: Path,
) -> list[tuple[Path, Path]]:
    """
    Discover Markdown + metadata pairs under the cleaned domain.
    """

    if not cleaned_domain_root.exists():
        raise FileNotFoundError(
            f"Cleaned domain does not exist: "
            f"{cleaned_domain_root}"
        )

    if not cleaned_domain_root.is_dir():
        raise ValueError(
            f"Cleaned domain is not a directory: "
            f"{cleaned_domain_root}"
        )

    inputs = []

    for markdown_path in sorted(
        cleaned_domain_root.rglob("*.md")
    ):
        metadata_path = (
            markdown_path.with_suffix(".json")
        )

        if not metadata_path.exists():
            raise FileNotFoundError(
                "Missing metadata for cleaned Markdown: "
                f"{markdown_path}"
            )

        inputs.append(
            (
                markdown_path,
                metadata_path,
            )
        )

    if not inputs:
        raise ValueError(
            "No cleaned Markdown files found in: "
            f"{cleaned_domain_root}"
        )

    return inputs


# ============================================================
# STRUCTURING
# ============================================================

def _run_structuring(
    *,
    inputs: list[tuple[Path, Path]],
    domain: str,
    structured_root: Path,
) -> dict:
    """
    Convert cleaned Markdown files into structured JSON.

    Each document is processed independently so one bad document
    does not stop the complete domain run.
    """

    domain_inputs = []

    successful = 0
    failed = 0

    failures = []

    structurer = KnowledgeStructurer(
        output_path=structured_root
    )

    for markdown_path, metadata_path in inputs:

        try:
            output_markdown, output_json = (
                structurer.structure(
                    markdown_path=markdown_path,
                    metadata_path=metadata_path,
                )
            )

            domain_inputs.append(
                output_json
            )

            successful += 1

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
                    "error": (
                        f"{type(error).__name__}: "
                        f"{error}"
                    ),
                }
            )

    return {
        "structured_successfully": successful,
        "failed": failed,
        "failures": failures,
        "structured_files": [
            str(path)
            for path in domain_inputs
        ],
    }


# ============================================================
# ORGANIZATION
# ============================================================

def _run_organization(
    *,
    domain: str,
    structured_root: Path,
    organized_root: Path,
) -> dict:
    """
    Run the existing Phase 8.3 organizer on structured JSON.
    """

    organizer = StructuredKnowledgeOrganizer(
        input_root=structured_root,
        output_root=organized_root,
    )

    result = organizer.organize_domain(
        domain
    )

    return result


# ============================================================
# PUBLIC COMMAND API
# ============================================================

def run_organization(
    *,
    domain: str,
    cleaned_root: str | Path,
    structured_root: str | Path,
    organized_root: str | Path,
) -> dict:
    """
    Run the baseline Command 3 migration for one domain.
    """

    cleaned_root = Path(
        cleaned_root
    )

    structured_root = Path(
        structured_root
    )

    organized_root = Path(
        organized_root
    )

    cleaned_domain_root = (
        cleaned_root
        / domain
    )

    structured_domain_root = (
        structured_root
        / domain
    )

    organized_domain_root = (
        organized_root
        / domain
    )

    inputs = _discover_inputs(
        cleaned_domain_root
    )

    # --------------------------------------------------------
    # STRUCTURE CLEANED KNOWLEDGE
    # --------------------------------------------------------

    structuring_result = _run_structuring(
        inputs=inputs,
        domain=domain,
        structured_root=structured_root,
    )

    # --------------------------------------------------------
    # FAIL FAST ONLY IF NOTHING STRUCTURED
    # --------------------------------------------------------

    if (
        structuring_result[
            "structured_successfully"
        ]
        == 0
    ):
        raise RuntimeError(
            "Command 3 could not structure any "
            f"documents for domain: {domain}"
        )

    # --------------------------------------------------------
    # RUN EXISTING ORGANIZER
    # --------------------------------------------------------

    try:

        organization_result = (
            _run_organization(
                domain=domain,
                structured_root=structured_root,
                organized_root=organized_root,
            )
        )

        organized_successfully = 1

    except Exception as error:

        organization_result = {
            "error": (
                f"{type(error).__name__}: "
                f"{error}"
            )
        }

        organized_successfully = 0

    # ========================================================
    # COMMAND 3 MANIFEST
    # ========================================================

    organized_domain_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    manifest = {
        "command": "organize_knowledge",
        "command_version": "1.0",
        "domain": domain,
        "input_documents": len(
            inputs
        ),
        "structured_successfully": (
            structuring_result[
                "structured_successfully"
            ]
        ),
        "organized_successfully": (
            organized_successfully
        ),
        "failed": structuring_result[
            "failed"
        ],
        "failures": structuring_result[
            "failures"
        ],
        "organization_result": {
            "manifest_path": str(
                organization_result.get(
                    "manifest_path",
                    ""
                )
            )
            if isinstance(
                organization_result,
                dict,
            )
            else "",
        },
    }

    manifest_path = (
        organized_domain_root
        / "command_3_manifest.json"
    )

    manifest_path.write_text(
        json.dumps(
            manifest,
            indent=4,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    if organized_successfully == 0:
        raise RuntimeError(
            "Command 3 organization failed: "
            f"{organization_result.get('error', 'unknown error')}"
        )

    return {
        **manifest,
        "structured_files": (
            structuring_result[
                "structured_files"
            ]
        ),
        "organization_result": (
            organization_result
        ),
    }