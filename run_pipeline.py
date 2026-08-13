"""
Universal Knowledge Ingestion Pipeline

STEP 1
------
Crawler creates the raw/crawled knowledge inputs.

STEP 2
------
Run:

    python run_pipeline.py

This downstream pipeline performs:

    7.4  -> structured knowledge
    8.3  -> deterministic organization
    8.4  -> universal dynamic RAG planning
    8.5  -> final DOCX generation
    8.5  -> final validation

Final output
------------
storage/rag_knowledge/<domain>/

The pipeline does NOT:
- use an LLM
- summarize knowledge
- chunk
- embed
- create vectors

Those happen later in the chatbot/V1 ingestion layer.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import time

from processors.knowledge_input_discovery import (
    KnowledgeInputDiscovery,
)

from processors.knowledge_structurer import (
    KnowledgeStructurer,
)

from processors.structured_knowledge_organizer import (
    StructuredKnowledgeOrganizer,
)

from processors.knowledge_rag_planner import (
    KnowledgeRAGPlanner,
)

from processors.rag_document_builder import (
    RAGDocumentBuilder,
)

from processors.rag_document_validator import (
    RAGDocumentValidator,
)


# ======================================================================
# PIPELINE CONFIGURATION
# ======================================================================

STRUCTURED_ROOT = Path(
    "storage/structured_knowledge"
)

ORGANIZED_ROOT = Path(
    "storage/organized_knowledge_8_3_final"
)

RAG_ROOT = Path(
    "storage/rag_knowledge"
)

PIPELINE_REPORT_ROOT = Path(
    "storage/pipeline_reports"
)


# ======================================================================
# HELPERS
# ======================================================================

def _safe_path(
    value: Any,
) -> Path | None:

    if value is None:
        return None

    try:
        return Path(value)

    except TypeError:
        return None


def _get_attribute(
    obj: Any,
    *names: str,
) -> Any:

    for name in names:

        if hasattr(
            obj,
            name,
        ):

            value = getattr(
                obj,
                name,
            )

            if value is not None:
                return value

    return None


def _get_input_paths(
    item: Any,
) -> tuple[
    Path | None,
    Path | None,
]:
    """
    Resolve Markdown and metadata paths from KnowledgeInput.

    Kept tolerant because the input-discovery model may use
    slightly different attribute names.
    """

    markdown_path = _get_attribute(
        item,
        "markdown_path",
        "retrieval_path",
        "input_path",
        "source_path",
        "path",
    )

    metadata_path = _get_attribute(
        item,
        "metadata_path",
        "metadata",
    )

    return (
        _safe_path(markdown_path),
        _safe_path(metadata_path),
    )


def _discover_metadata_path(
    markdown_path: Path,
) -> Path | None:

    sibling = markdown_path.with_suffix(
        ".json"
    )

    if sibling.exists():
        return sibling

    candidates = sorted(
        markdown_path.parent.glob(
            f"{markdown_path.stem}*.json"
        )
    )

    if candidates:
        return candidates[0]

    return None


def _extract_domain_from_path(
    path: Path,
) -> str:

    parts = path.parts

    known_roots = (
        "structured_knowledge",
        "knowledge",
        "organized_knowledge",
        "rag_knowledge",
    )

    for marker in known_roots:

        try:
            index = parts.index(
                marker
            )
        except ValueError:
            continue

        if (
            index + 1
            < len(parts)
        ):
            return parts[
                index + 1
            ]

    return "unknown"


def _count_files(
    root: Path,
    suffix: str,
) -> int:

    if not root.exists():
        return 0

    return sum(
        1
        for path in root.rglob(
            f"*{suffix}"
        )
        if path.is_file()
    )


def _write_json(
    path: Path,
    data: dict,
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            data,
            indent=4,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


# ======================================================================
# 7.4
# ======================================================================

def run_structure_phase(
    inputs: list[Any],
) -> dict:

    print()
    print("=" * 100)
    print(
        "PHASE 7.4 — KNOWLEDGE STRUCTURING"
    )
    print("=" * 100)

    structurer = KnowledgeStructurer(
        output_path=STRUCTURED_ROOT
    )

    processed = 0
    failed = 0

    results = []

    for index, item in enumerate(
        inputs,
        start=1,
    ):

        try:

            markdown_path, metadata_path = (
                _get_input_paths(item)
            )

            if markdown_path is None:
                raise ValueError(
                    "Could not resolve input path "
                    f"from KnowledgeInput: {item!r}"
                )

            if not markdown_path.exists():
                raise FileNotFoundError(
                    f"Input does not exist: "
                    f"{markdown_path}"
                )

            if metadata_path is None:

                metadata_path = (
                    _discover_metadata_path(
                        markdown_path
                    )
                )

            if metadata_path is None:
                raise FileNotFoundError(
                    "Metadata file could not be "
                    f"resolved for: {markdown_path}"
                )

            print(
                f"[7.4 {index}/{len(inputs)}] "
                f"{markdown_path}"
            )

            structured_md, structured_json = (
                structurer.structure(
                    markdown_path=markdown_path,
                    metadata_path=metadata_path,
                )
            )

            processed += 1

            results.append(
                {
                    "input": str(
                        markdown_path
                    ),
                    "metadata": str(
                        metadata_path
                    ),
                    "structured_markdown": str(
                        structured_md
                    ),
                    "structured_json": str(
                        structured_json
                    ),
                    "status": "success",
                }
            )

        except Exception as error:

            failed += 1

            print(
                "[7.4 FAILED]",
                error,
            )

            results.append(
                {
                    "input": str(
                        _get_attribute(
                            item,
                            "markdown_path",
                            "retrieval_path",
                            "input_path",
                            "path",
                        )
                    ),
                    "status": "failed",
                    "error": (
                        f"{type(error).__name__}: "
                        f"{error}"
                    ),
                }
            )

    return {
        "inputs": len(inputs),
        "processed": processed,
        "failed": failed,
        "results": results,
    }


# ======================================================================
# 8.3 — FINAL STRUCTURED ORGANIZATION
# ======================================================================

def run_organization_phase(
    domains: list[str],
) -> dict:

    print()
    print("=" * 100)
    print(
        "PHASE 8.3 — STRUCTURED KNOWLEDGE ORGANIZATION"
    )
    print("=" * 100)

    organizer = StructuredKnowledgeOrganizer(
        input_root=STRUCTURED_ROOT,
        output_root=ORGANIZED_ROOT,
    )

    results = []

    total_documents = 0
    total_units = 0
    total_noise = 0
    total_review = 0
    failed_domains = 0

    for index, domain in enumerate(
        domains,
        start=1,
    ):

        print()
        print(
            f"[8.3 {index}/{len(domains)}] "
            f"{domain}"
        )

        try:

            result = (
                organizer.organize_domain(
                    domain
                )
            )

            manifest = result[
                "manifest"
            ]

            total_documents += (
                manifest[
                    "input_documents"
                ]
            )

            total_units += (
                manifest[
                    "total_knowledge_units"
                ]
            )

            total_noise += (
                manifest[
                    "total_noise_sections"
                ]
            )

            total_review += (
                manifest[
                    "review_units"
                ]
            )

            results.append(
                {
                    "domain": domain,
                    "status": "success",
                    "manifest": str(
                        result[
                            "manifest_path"
                        ]
                    ),
                    "audit": str(
                        result[
                            "audit_path"
                        ]
                    ),
                    "input_documents": (
                        manifest[
                            "input_documents"
                        ]
                    ),
                    "knowledge_units": (
                        manifest[
                            "total_knowledge_units"
                        ]
                    ),
                    "review_units": (
                        manifest[
                            "review_units"
                        ]
                    ),
                }
            )

        except Exception as error:

            failed_domains += 1

            print(
                "[8.3 FAILED]",
                domain,
                error,
            )

            results.append(
                {
                    "domain": domain,
                    "status": "failed",
                    "error": (
                        f"{type(error).__name__}: "
                        f"{error}"
                    ),
                }
            )

    return {
        "domains": len(domains),
        "failed_domains": failed_domains,
        "documents": total_documents,
        "knowledge_units": total_units,
        "noise": total_noise,
        "review_units": total_review,
        "results": results,
    }


# ======================================================================
# DISCOVER STRUCTURED DOMAINS
# ======================================================================

def discover_structured_domains() -> list[str]:

    if not STRUCTURED_ROOT.exists():
        return []

    domains = []

    for path in sorted(
        STRUCTURED_ROOT.iterdir()
    ):

        if (
            path.is_dir()
            and not path.name.startswith(".")
        ):
            domains.append(
                path.name
            )

    return domains


# ======================================================================
# 8.4
# ======================================================================

def run_planning_phase(
    domains: list[str],
) -> dict:

    print()
    print("=" * 100)
    print(
        "PHASE 8.4 — UNIVERSAL DYNAMIC RAG PLANNING"
    )
    print("=" * 100)

    planner = KnowledgeRAGPlanner(
        organized_root=ORGANIZED_ROOT
    )

    results = []

    total_input_units = 0
    total_rag_documents = 0
    failed_domains = 0

    for index, domain in enumerate(
        domains,
        start=1,
    ):

        print()
        print(
            f"[8.4 {index}/{len(domains)}] "
            f"{domain}"
        )

        try:

            result = (
                planner.plan_domain(
                    domain
                )
            )

            results.append(
                {
                    "domain": domain,
                    "status": "success",
                    "input_units": (
                        result[
                            "input_units"
                        ]
                    ),
                    "rag_documents": (
                        result[
                            "rag_documents"
                        ]
                    ),
                    "coverage": (
                        result[
                            "coverage"
                        ]
                    ),
                    "plan": str(
                        ORGANIZED_ROOT
                        / domain
                        / "rag_plan.json"
                    ),
                }
            )

            total_input_units += (
                result[
                    "input_units"
                ]
            )

            total_rag_documents += (
                result[
                    "rag_documents"
                ]
            )

        except Exception as error:

            failed_domains += 1

            print(
                "[8.4 FAILED]",
                domain,
                error,
            )

            results.append(
                {
                    "domain": domain,
                    "status": "failed",
                    "error": (
                        f"{type(error).__name__}: "
                        f"{error}"
                    ),
                }
            )

    return {
        "domains": len(domains),
        "failed_domains": failed_domains,
        "input_units": total_input_units,
        "rag_documents": total_rag_documents,
        "results": results,
    }


# ======================================================================
# 8.5 BUILD
# ======================================================================

def run_build_phase(
    domains: list[str],
) -> dict:

    print()
    print("=" * 100)
    print(
        "PHASE 8.5 — FINAL RAG DOCX BUILDING"
    )
    print("=" * 100)

    builder = RAGDocumentBuilder(
        output_root=RAG_ROOT
    )

    results = []

    total_files = 0
    total_units = 0
    failed_domains = 0

    for index, domain in enumerate(
        domains,
        start=1,
    ):

        print()
        print(
            f"[8.5 {index}/{len(domains)}] "
            f"{domain}"
        )

        try:

            organized_domain_root = (
                ORGANIZED_ROOT
                / domain
            )

            result = (
                builder.build_domain(
                    organized_root=(
                        organized_domain_root
                    )
                )
            )

            results.append(
                {
                    "domain": domain,
                    "status": "success",
                    "files": (
                        result[
                            "documents_built"
                        ]
                    ),
                    "units": (
                        result[
                            "output_units"
                        ]
                    ),
                    "coverage": (
                        result[
                            "coverage"
                        ]
                    ),
                    "manifest": str(
                        RAG_ROOT
                        / domain
                        / "rag_build_manifest.json"
                    ),
                }
            )

            total_files += (
                result[
                    "documents_built"
                ]
            )

            total_units += (
                result[
                    "output_units"
                ]
            )

        except Exception as error:

            failed_domains += 1

            print(
                "[8.5 FAILED]",
                domain,
                error,
            )

            results.append(
                {
                    "domain": domain,
                    "status": "failed",
                    "error": (
                        f"{type(error).__name__}: "
                        f"{error}"
                    ),
                }
            )

    return {
        "domains": len(domains),
        "failed_domains": failed_domains,
        "files": total_files,
        "units": total_units,
        "results": results,
    }


# ======================================================================
# 8.5 VALIDATION
# ======================================================================

def run_validation_phase(
    domains: list[str],
) -> dict:

    print()
    print("=" * 100)
    print(
        "PHASE 8.5 — FINAL RAG VALIDATION"
    )
    print("=" * 100)

    validator = RAGDocumentValidator()

    results = []

    failed_domains = 0
    passed_domains = 0

    total_expected_units = 0
    total_manifest_units = 0

    for index, domain in enumerate(
        domains,
        start=1,
    ):

        print()
        print(
            f"[VALIDATE {index}/{len(domains)}] "
            f"{domain}"
        )

        try:

            result = (
                validator.validate_domain(
                    organized_root=(
                        ORGANIZED_ROOT
                        / domain
                    ),
                    rag_root=(
                        RAG_ROOT
                        / domain
                    ),
                )
            )

            if result[
                "overall_pass"
            ]:
                passed_domains += 1
            else:
                failed_domains += 1

            total_expected_units += (
                result[
                    "expected_units"
                ]
            )

            total_manifest_units += (
                result[
                    "manifest_units"
                ]
            )

            results.append(
                {
                    "domain": domain,
                    "status": (
                        "success"
                        if result[
                            "overall_pass"
                        ]
                        else "failed"
                    ),
                    "overall_pass": (
                        result[
                            "overall_pass"
                        ]
                    ),
                    "expected_documents": (
                        result[
                            "expected_documents"
                        ]
                    ),
                    "actual_documents": (
                        result[
                            "actual_docx_documents"
                        ]
                    ),
                    "expected_units": (
                        result[
                            "expected_units"
                        ]
                    ),
                    "manifest_units": (
                        result[
                            "manifest_units"
                        ]
                    ),
                    "coverage_complete": (
                        result[
                            "coverage_complete"
                        ]
                    ),
                    "structure_complete": (
                        result[
                            "structure_complete"
                        ]
                    ),
                    "report": str(
                        RAG_ROOT
                        / domain
                        / "rag_validation_report.json"
                    ),
                }
            )

        except Exception as error:

            failed_domains += 1

            print(
                "[VALIDATION FAILED]",
                domain,
                error,
            )

            results.append(
                {
                    "domain": domain,
                    "status": "failed",
                    "overall_pass": False,
                    "error": (
                        f"{type(error).__name__}: "
                        f"{error}"
                    ),
                }
            )

    return {
        "domains": len(domains),
        "passed_domains": passed_domains,
        "failed_domains": failed_domains,
        "expected_units": total_expected_units,
        "manifest_units": total_manifest_units,
        "results": results,
    }


# ======================================================================
# FINAL PIPELINE REPORT
# ======================================================================

def run_pipeline() -> dict:

    started_at = time.time()

    print()
    print("=" * 100)
    print(
        "UNIVERSAL KNOWLEDGE INGESTION PIPELINE"
    )
    print("=" * 100)

    # ------------------------------------------------------------
    # DISCOVER CURRENT INPUTS
    # ------------------------------------------------------------

    discovery = KnowledgeInputDiscovery()

    inputs = discovery.discover()

    print()
    print(
        "Knowledge inputs discovered:",
        len(inputs),
    )

    if not inputs:
        raise RuntimeError(
            "No knowledge inputs were discovered."
        )

    # ------------------------------------------------------------
    # 7.4
    # ------------------------------------------------------------

    structure_result = (
        run_structure_phase(
            inputs
        )
    )

    if structure_result[
        "failed"
    ]:

        raise RuntimeError(
            "7.4 failed for "
            f"{structure_result['failed']} inputs."
        )

    # ------------------------------------------------------------
    # FIND DOMAINS AFTER 7.4
    # ------------------------------------------------------------

    domains = (
        discover_structured_domains()
    )

    if not domains:

        raise RuntimeError(
            "7.4 completed but no structured "
            "knowledge domains were found."
        )

    print()
    print(
        "Structured domains:"
    )

    for domain in domains:
        print(
            "  -",
            domain,
        )

    # ------------------------------------------------------------
    # 8.3
    # ------------------------------------------------------------

    organization_result = (
        run_organization_phase(
            domains
        )
    )

    if organization_result[
        "failed_domains"
    ]:

        raise RuntimeError(
            "8.3 failed for "
            f"{organization_result['failed_domains']} domains."
        )

    # ------------------------------------------------------------
    # 8.4
    # ------------------------------------------------------------

    planning_result = (
        run_planning_phase(
            domains
        )
    )

    if planning_result[
        "failed_domains"
    ]:

        raise RuntimeError(
            "8.4 failed for "
            f"{planning_result['failed_domains']} domains."
        )

    # ------------------------------------------------------------
    # 8.5 BUILD
    # ------------------------------------------------------------

    build_result = (
        run_build_phase(
            domains
        )
    )

    if build_result[
        "failed_domains"
    ]:

        raise RuntimeError(
            "8.5 build failed for "
            f"{build_result['failed_domains']} domains."
        )

    # ------------------------------------------------------------
    # 8.5 VALIDATION
    # ------------------------------------------------------------

    validation_result = (
        run_validation_phase(
            domains
        )
    )

    if validation_result[
        "failed_domains"
    ]:

        raise RuntimeError(
            "Final RAG validation failed for "
            f"{validation_result['failed_domains']} domains."
        )

    # ------------------------------------------------------------
    # FINAL REPORT
    # ------------------------------------------------------------

    duration = (
        time.time()
        - started_at
    )

    final_report = {
        "pipeline": (
            "universal_knowledge_ingestion"
        ),

        "status": "COMPLETE",

        "duration_seconds": round(
            duration,
            2,
        ),

        "domains": domains,

        "7_4": {
            "inputs": (
                structure_result[
                    "inputs"
                ]
            ),
            "processed": (
                structure_result[
                    "processed"
                ]
            ),
            "failed": (
                structure_result[
                    "failed"
                ]
            ),
        },

        "8_3": {
            "domains": (
                organization_result[
                    "domains"
                ]
            ),
            "source_documents": (
                organization_result[
                    "documents"
                ]
            ),
            "knowledge_units": (
                organization_result[
                    "knowledge_units"
                ]
            ),
            "noise_sections": (
                organization_result[
                    "noise"
                ]
            ),
            "review_units": (
                organization_result[
                    "review_units"
                ]
            ),
        },

        "8_4": {
            "input_units": (
                planning_result[
                    "input_units"
                ]
            ),
            "rag_documents": (
                planning_result[
                    "rag_documents"
                ]
            ),
            "failed_domains": (
                planning_result[
                    "failed_domains"
                ]
            ),
        },

        "8_5": {
            "docx_files": (
                build_result[
                    "files"
                ]
            ),
            "output_units": (
                build_result[
                    "units"
                ]
            ),
            "failed_domains": (
                build_result[
                    "failed_domains"
                ]
            ),
        },

        "validation": {
            "passed_domains": (
                validation_result[
                    "passed_domains"
                ]
            ),
            "failed_domains": (
                validation_result[
                    "failed_domains"
                ]
            ),
            "expected_units": (
                validation_result[
                    "expected_units"
                ]
            ),
            "manifest_units": (
                validation_result[
                    "manifest_units"
                ]
            ),
            "complete": (
                validation_result[
                    "failed_domains"
                ]
                == 0
            ),
        },

        "final_output": {
            "root": str(
                RAG_ROOT
            ),
            "domains": [
                str(
                    RAG_ROOT / domain
                )
                for domain in domains
            ],
        },
    }

    report_path = (
        PIPELINE_REPORT_ROOT
        / "latest_pipeline_report.json"
    )

    _write_json(
        report_path,
        final_report,
    )

    # ------------------------------------------------------------
    # FINAL TERMINAL SUMMARY
    # ------------------------------------------------------------

    print()
    print("=" * 100)
    print(
        "KNOWLEDGE INGESTION PIPELINE COMPLETE"
    )
    print("=" * 100)

    print()
    print(
        "DOMAINS:",
        len(domains),
    )

    print()
    print(
        "7.4 — STRUCTURED"
    )

    print(
        "  Inputs:",
        structure_result[
            "inputs"
        ],
    )

    print(
        "  Processed:",
        structure_result[
            "processed"
        ],
    )

    print(
        "  Failed:",
        structure_result[
            "failed"
        ],
    )

    print()
    print(
        "8.3 — ORGANIZED"
    )

    print(
        "  Source documents:",
        organization_result[
            "documents"
        ],
    )

    print(
        "  Knowledge units:",
        organization_result[
            "knowledge_units"
        ],
    )

    print(
        "  Noise sections:",
        organization_result[
            "noise"
        ],
    )

    print(
        "  Review units:",
        organization_result[
            "review_units"
        ],
    )

    print()
    print(
        "8.4 — RAG PLANNING"
    )

    print(
        "  Input units:",
        planning_result[
            "input_units"
        ],
    )

    print(
        "  RAG documents:",
        planning_result[
            "rag_documents"
        ],
    )

    print()
    print(
        "8.5 — FINAL DOCX"
    )

    print(
        "  DOCX files:",
        build_result[
            "files"
        ],
    )

    print(
        "  Output units:",
        build_result[
            "units"
        ],
    )

    print()
    print(
        "VALIDATION"
    )

    print(
        "  Passed domains:",
        validation_result[
            "passed_domains"
        ],
    )

    print(
        "  Failed domains:",
        validation_result[
            "failed_domains"
        ],
    )

    print(
        "  Expected units:",
        validation_result[
            "expected_units"
        ],
    )

    print(
        "  Manifest units:",
        validation_result[
            "manifest_units"
        ],
    )

    print(
        "  Overall:",
        "PASS"
        if validation_result[
            "failed_domains"
        ] == 0
        else "FAIL",
    )

    print()
    print(
        "FINAL RAG OUTPUT:"
    )

    print(
        f"  {RAG_ROOT}"
    )

    print()
    print(
        "PIPELINE REPORT:"
    )

    print(
        f"  {report_path}"
    )

    print()
    print(
        f"Duration: {duration:.2f} seconds"
    )

    print("=" * 100)

    return final_report


# ======================================================================
# ENTRY POINT
# ======================================================================

if __name__ == "__main__":
    run_pipeline()
