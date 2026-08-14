"""
FINAL ENGINEERING-COLLEGE RAG BUILDER

STEP 2
------

Uses EXISTING crawled knowledge inputs.

It does NOT crawl.

Usage:

    python build_rag.py --domain www.iitj.ac.in

Pipeline:

    existing crawled Markdown + metadata
            ↓
        7.4 structured
            ↓
        8.3 organized
            ↓
        A / B / C / REVIEW / D
            ↓
        global RAG quality filter
            ↓
        A + B + C + useful REVIEW
            ↓
        dynamic semantic RAG planning
            ↓
        final DOCX
            ↓
        validation
            ↓
        storage/FINAL_RAG/<domain>/

Next time, for a new college:

    python crawl.py https://college.edu
    python build_rag.py --domain college.edu

Important:
------------
This file does NOT modify the original crawl/source data.
"""

from __future__ import annotations

import argparse
import json
import shutil
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

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

from processors.rag_content_filter import (
    RAGContentFilter,
)


# ============================================================================
# CONFIGURATION
# ============================================================================

STRUCTURED_ROOT = Path(
    "storage/structured_knowledge"
)

ORGANIZED_ROOT = Path(
    "storage/organized_knowledge_8_3_final"
)

FINAL_ORGANIZED_ROOT = Path(
    "storage/final_organized_knowledge"
)

FINAL_RAG_ROOT = Path(
    "storage/FINAL_RAG"
)

PIPELINE_REPORT_ROOT = Path(
    "storage/pipeline_reports"
)


# ============================================================================
# GENERIC HELPERS
# ============================================================================

def write_json(
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


def safe_path(
    value: Any,
) -> Path | None:

    if value is None:
        return None

    try:
        return Path(
            value
        )
    except TypeError:
        return None


def get_attribute(
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


def get_input_paths(
    item: Any,
) -> tuple[
    Path | None,
    Path | None,
]:
    """
    Resolve Markdown and metadata paths from KnowledgeInput.

    Matches the existing run_pipeline.py behavior.
    """

    markdown_path = get_attribute(
        item,
        "markdown_path",
        "retrieval_path",
        "input_path",
        "source_path",
        "path",
    )

    metadata_path = get_attribute(
        item,
        "metadata_path",
        "metadata",
    )

    return (
        safe_path(
            markdown_path
        ),
        safe_path(
            metadata_path
        ),
    )


def discover_metadata_path(
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


# ============================================================================
# INPUT SELECTION
# ============================================================================

def select_existing_inputs(
    inputs: list[Any],
    requested_domain: str,
) -> list[Any]:
    """
    Select already-crawled inputs belonging to the requested domain.

    We intentionally do this BEFORE 7.4 so old/test college data elsewhere
    in storage is not accidentally processed.
    """

    selected = []

    domain_token = (
        requested_domain
        .strip()
        .lower()
        .rstrip("/")
    )

    for item in inputs:

        markdown_path, metadata_path = (
            get_input_paths(
                item
            )
        )

        candidates = []

        if markdown_path is not None:
            candidates.append(
                str(
                    markdown_path
                ).lower()
            )

        if metadata_path is not None:
            candidates.append(
                str(
                    metadata_path
                ).lower()
            )

        matched = any(
            domain_token in value
            for value in candidates
        )

        if matched:
            selected.append(
                item
            )

    return selected


# ============================================================================
# 7.4
# ============================================================================

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
                get_input_paths(
                    item
                )
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
                    discover_metadata_path(
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
                        get_input_paths(item)[0]
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


# ============================================================================
# DOMAIN DISCOVERY
# ============================================================================

def discover_structured_domains() -> list[str]:

    if not STRUCTURED_ROOT.exists():
        return []

    return [
        path.name
        for path in sorted(
            STRUCTURED_ROOT.iterdir()
        )
        if (
            path.is_dir()
            and not path.name.startswith(".")
        )
    ]


# ============================================================================
# 8.3
# ============================================================================

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


# ============================================================================
# FINAL FILTER
# ============================================================================

def run_filter_phase(
    domains: list[str],
) -> dict:

    print()
    print("=" * 100)
    print(
        "FINAL RAG CONTENT QUALITY FILTER"
    )
    print("=" * 100)

    if FINAL_ORGANIZED_ROOT.exists():
        shutil.rmtree(
            FINAL_ORGANIZED_ROOT
        )

    FINAL_ORGANIZED_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    results = []

    total_input = 0
    total_final = 0
    total_excluded = 0
    total_review_input = 0
    total_review_keep = 0
    total_review_exclude = 0
    total_urls_removed = 0

    failed_domains = 0

    for index, domain in enumerate(
        domains,
        start=1,
    ):

        print()
        print(
            f"[FILTER {index}/{len(domains)}] "
            f"{domain}"
        )

        source_domain = (
            ORGANIZED_ROOT
            / domain
        )

        final_domain = (
            FINAL_ORGANIZED_ROOT
            / domain
        )

        if not source_domain.exists():
            raise FileNotFoundError(
                f"Organized domain does not exist: "
                f"{source_domain}"
            )

        try:

            shutil.copytree(
                source_domain,
                final_domain,
            )

            source_manifest = (
                source_domain
                / "knowledge_units.json"
            )

            filter_engine = RAGContentFilter(
                source_manifest=source_manifest,
                output_root=final_domain,
            )

            result = filter_engine.run()

            filter_engine.write_outputs(
                result
            )

            filtered_manifest_path = (
                final_domain
                / "knowledge_units_rag_filtered.json"
            )

            final_manifest_path = (
                final_domain
                / "knowledge_units.json"
            )

            shutil.copy2(
                filtered_manifest_path,
                final_manifest_path,
            )

            report = result[
                "report"
            ]

            total_input += report[
                "input_units"
            ]

            total_final += report[
                "final_rag_units"
            ]

            total_excluded += report[
                "excluded_units"
            ]

            total_review_input += (
                report[
                    "review"
                ][
                    "input"
                ]
            )

            total_review_keep += (
                report[
                    "review"
                ][
                    "keep"
                ]
            )

            total_review_exclude += (
                report[
                    "review"
                ][
                    "exclude"
                ]
            )

            total_urls_removed += (
                report[
                    "url_cleaning"
                ][
                    "urls_removed"
                ]
            )

            print(
                "  Input units:",
                report[
                    "input_units"
                ],
            )

            print(
                "  Final RAG units:",
                report[
                    "final_rag_units"
                ],
            )

            print(
                "  Excluded:",
                report[
                    "excluded_units"
                ],
            )

            print(
                "  REVIEW kept:",
                report[
                    "review"
                ][
                    "keep"
                ],
            )

            print(
                "  REVIEW excluded:",
                report[
                    "review"
                ][
                    "exclude"
                ],
            )

            print(
                "  URLs removed:",
                report[
                    "url_cleaning"
                ][
                    "urls_removed"
                ],
            )

            results.append(
                {
                    "domain": domain,
                    "status": "success",
                    "filter_report": str(
                        final_domain
                        / "rag_content_filter_report.json"
                    ),
                    "exclusion_audit": str(
                        final_domain
                        / "rag_excluded_audit.json"
                    ),
                    "input_units": report[
                        "input_units"
                    ],
                    "final_rag_units": report[
                        "final_rag_units"
                    ],
                    "excluded_units": report[
                        "excluded_units"
                    ],
                    "review": report[
                        "review"
                    ],
                    "url_cleaning": report[
                        "url_cleaning"
                    ],
                }
            )

        except Exception as error:

            failed_domains += 1

            print(
                "[FILTER FAILED]",
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
        "input_units": total_input,
        "final_rag_units": total_final,
        "excluded_units": total_excluded,
        "review_input": total_review_input,
        "review_keep": total_review_keep,
        "review_exclude": total_review_exclude,
        "urls_removed": total_urls_removed,
        "results": results,
    }


# ============================================================================
# REVIEW-AWARE DYNAMIC PLANNER
# ============================================================================

class FinalRAGPlanner(
    KnowledgeRAGPlanner
):
    """
    Existing dynamic planner with one controlled extension.

    Useful REVIEW units produced by rag_content_filter.py can carry:

        rag.final_family_hint

    When that hint exists, it is used before the normal taxonomy fallback.

    A/B/C behavior remains the existing planner behavior.
    """

    def _resolve_family(
        self,
        unit: dict,
    ) -> str:

        rag = unit.get(
            "rag",
            {},
        )

        if isinstance(
            rag,
            dict,
        ):

            final_class = str(
                rag.get(
                    "final_rag_class",
                    "",
                )
            ).upper()

            family_hint = str(
                rag.get(
                    "final_family_hint",
                    "",
                )
            ).strip()

            if (
                final_class == "REVIEW"
                and family_hint
                and family_hint
                != "dynamic_family_required"
            ):
                return family_hint

        return super()._resolve_family(
            unit
        )


# ============================================================================
# 8.4
# ============================================================================

def run_planning_phase(
    domains: list[str],
) -> dict:

    print()
    print("=" * 100)
    print(
        "PHASE 8.4 — FINAL DYNAMIC RAG PLANNING"
    )
    print("=" * 100)

    planner = FinalRAGPlanner(
        organized_root=FINAL_ORGANIZED_ROOT
    )

    results = []

    total_input_units = 0
    total_documents = 0
    total_review = 0
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

            result = planner.plan_domain(
                domain
            )

            manifest_path = (
                FINAL_ORGANIZED_ROOT
                / domain
                / "knowledge_units.json"
            )

            manifest = json.loads(
                manifest_path.read_text(
                    encoding="utf-8"
                )
            )

            review_count = 0

            for unit in manifest.get(
                "units",
                [],
            ):

                unit_rag = unit.get(
                    "rag",
                    {},
                )

                if not isinstance(
                    unit_rag,
                    dict,
                ):
                    continue

                if str(
                    unit_rag.get(
                        "final_rag_class",
                        "",
                    )
                ).upper() == "REVIEW":

                    review_count += 1

            total_input_units += (
                result[
                    "input_units"
                ]
            )

            total_documents += (
                result[
                    "rag_documents"
                ]
            )

            total_review += (
                review_count
            )

            results.append(
                {
                    "domain": domain,
                    "status": "success",
                    "input_units": result[
                        "input_units"
                    ],
                    "rag_documents": result[
                        "rag_documents"
                    ],
                    "review_rag_units": review_count,
                    "coverage": result[
                        "coverage"
                    ],
                    "plan": str(
                        FINAL_ORGANIZED_ROOT
                        / domain
                        / "rag_plan.json"
                    ),
                }
            )

            print(
                "  Input units:",
                result[
                    "input_units"
                ],
            )

            print(
                "  REVIEW RAG units:",
                review_count,
            )

            print(
                "  RAG documents:",
                result[
                    "rag_documents"
                ],
            )

            print(
                "  Coverage:",
                (
                    "PASS"
                    if result[
                        "coverage"
                    ][
                        "coverage_complete"
                    ]
                    else "FAIL"
                ),
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
        "rag_documents": total_documents,
        "review_rag_units": total_review,
        "results": results,
    }


# ============================================================================
# 8.5 BUILD
# ============================================================================

def run_build_phase(
    domains: list[str],
) -> dict:

    print()
    print("=" * 100)
    print(
        "PHASE 8.5 — FINAL RAG DOCX BUILD"
    )
    print("=" * 100)

    if FINAL_RAG_ROOT.exists():
        shutil.rmtree(
            FINAL_RAG_ROOT
        )

    FINAL_RAG_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    builder = RAGDocumentBuilder(
        output_root=FINAL_RAG_ROOT
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

            final_domain = (
                FINAL_ORGANIZED_ROOT
                / domain
            )

            result = (
                builder.build_domain(
                    organized_root=final_domain
                )
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

            results.append(
                {
                    "domain": domain,
                    "status": "success",
                    "files": result[
                        "documents_built"
                    ],
                    "units": result[
                        "output_units"
                    ],
                    "coverage": result[
                        "coverage"
                    ],
                    "manifest": str(
                        FINAL_RAG_ROOT
                        / domain
                        / "rag_build_manifest.json"
                    ),
                }
            )

            print(
                "  DOCX files:",
                result[
                    "documents_built"
                ],
            )

            print(
                "  Output units:",
                result[
                    "output_units"
                ],
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


# ============================================================================
# VALIDATION
# ============================================================================

def run_validation_phase(
    domains: list[str],
) -> dict:

    print()
    print("=" * 100)
    print(
        "FINAL RAG VALIDATION"
    )
    print("=" * 100)

    validator = (
        RAGDocumentValidator()
    )

    results = []

    failed_domains = 0
    passed_domains = 0

    expected_units = 0
    manifest_units = 0

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
                        FINAL_ORGANIZED_ROOT
                        / domain
                    ),
                    rag_root=(
                        FINAL_RAG_ROOT
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

            expected_units += (
                result[
                    "expected_units"
                ]
            )

            manifest_units += (
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
                    "overall_pass": result[
                        "overall_pass"
                    ],
                    "expected_documents": result[
                        "expected_documents"
                    ],
                    "actual_documents": result[
                        "actual_docx_documents"
                    ],
                    "expected_units": result[
                        "expected_units"
                    ],
                    "manifest_units": result[
                        "manifest_units"
                    ],
                    "coverage_complete": result[
                        "coverage_complete"
                    ],
                    "structure_complete": result[
                        "structure_complete"
                    ],
                    "report": str(
                        FINAL_RAG_ROOT
                        / domain
                        / "rag_validation_report.json"
                    ),
                }
            )

            print(
                "  Result:",
                (
                    "PASS"
                    if result[
                        "overall_pass"
                    ]
                    else "FAIL"
                ),
            )

            print(
                "  Expected units:",
                result[
                    "expected_units"
                ],
            )

            print(
                "  Manifest units:",
                result[
                    "manifest_units"
                ],
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
        "expected_units": expected_units,
        "manifest_units": manifest_units,
        "results": results,
    }


# ============================================================================
# FINAL REPORT
# ============================================================================

def build_report(
    *,
    started_at: float,
    requested_domain: str,
    selected_inputs: list[Any],
    structure_result: dict,
    organization_result: dict,
    filter_result: dict,
    planning_result: dict,
    build_result: dict,
    validation_result: dict,
) -> dict:

    duration = (
        time.time()
        - started_at
    )

    return {
        "pipeline": (
            "engineering_college_final_rag"
        ),
        "version": "1.0",
        "status": (
            "COMPLETE"
            if validation_result[
                "failed_domains"
            ] == 0
            else "FAILED"
        ),
        "duration_seconds": round(
            duration,
            2,
        ),
        "domain": requested_domain,
        "selected_crawled_inputs": len(
            selected_inputs
        ),
        "7_4_structured": {
            "inputs": structure_result[
                "inputs"
            ],
            "processed": structure_result[
                "processed"
            ],
            "failed": structure_result[
                "failed"
            ],
        },
        "8_3_organized": {
            "knowledge_units": organization_result[
                "knowledge_units"
            ],
            "review_units": organization_result[
                "review_units"
            ],
            "noise_sections": organization_result[
                "noise"
            ],
        },
        "rag_filter": {
            "input_units": filter_result[
                "input_units"
            ],
            "final_rag_units": filter_result[
                "final_rag_units"
            ],
            "excluded_units": filter_result[
                "excluded_units"
            ],
            "review_input": filter_result[
                "review_input"
            ],
            "review_keep": filter_result[
                "review_keep"
            ],
            "review_exclude": filter_result[
                "review_exclude"
            ],
            "urls_removed": filter_result[
                "urls_removed"
            ],
        },
        "8_4_planning": {
            "input_units": planning_result[
                "input_units"
            ],
            "rag_documents": planning_result[
                "rag_documents"
            ],
            "review_rag_units": planning_result[
                "review_rag_units"
            ],
        },
        "8_5_build": {
            "docx_files": build_result[
                "files"
            ],
            "output_units": build_result[
                "units"
            ],
        },
        "validation": {
            "passed_domains": validation_result[
                "passed_domains"
            ],
            "failed_domains": validation_result[
                "failed_domains"
            ],
            "expected_units": validation_result[
                "expected_units"
            ],
            "manifest_units": validation_result[
                "manifest_units"
            ],
            "complete": (
                validation_result[
                    "failed_domains"
                ] == 0
            ),
        },
        "final_output": str(
            FINAL_RAG_ROOT
            / requested_domain
        ),
    }


# ============================================================================
# MAIN
# ============================================================================

def run_pipeline(
    requested_domain: str,
) -> dict:

    started_at = time.time()

    print()
    print("=" * 100)
    print(
        "FINAL ENGINEERING-COLLEGE RAG BUILDER"
    )
    print("=" * 100)

    print(
        "Domain:",
        requested_domain,
    )

    print()
    print(
        "IMPORTANT:"
    )

    print(
        "Using EXISTING crawled data."
    )

    print(
        "No crawl will be performed."
    )

    # ------------------------------------------------------------------
    # Discover existing crawl inputs
    # ------------------------------------------------------------------

    discovery = (
        KnowledgeInputDiscovery()
    )

    all_inputs = discovery.discover()

    print()
    print(
        "All discovered knowledge inputs:",
        len(all_inputs),
    )

    selected_inputs = (
        select_existing_inputs(
            all_inputs,
            requested_domain,
        )
    )

    print(
        "Inputs selected for domain:",
        len(selected_inputs),
    )

    if not selected_inputs:

        raise RuntimeError(
            "No existing crawled knowledge inputs "
            f"were found for domain: "
            f"{requested_domain}\n\n"
            "Run the crawler first:\n"
            f"  python crawl.py https://{requested_domain}"
        )

    # ------------------------------------------------------------------
    # 7.4
    # ------------------------------------------------------------------

    structure_result = (
        run_structure_phase(
            selected_inputs
        )
    )

    if structure_result[
        "failed"
    ]:

        raise RuntimeError(
            "7.4 failed for "
            f"{structure_result['failed']} inputs."
        )

    # ------------------------------------------------------------------
    # Validate structured domain
    # ------------------------------------------------------------------

    available_domains = (
        discover_structured_domains()
    )

    if requested_domain not in (
        available_domains
    ):

        raise RuntimeError(
            "7.4 completed but the requested "
            f"structured domain was not found: "
            f"{requested_domain}"
        )

    domains = [
        requested_domain
    ]

    # ------------------------------------------------------------------
    # 8.3
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # GLOBAL RAG FILTER
    # ------------------------------------------------------------------

    filter_result = (
        run_filter_phase(
            domains
        )
    )

    if filter_result[
        "failed_domains"
    ]:

        raise RuntimeError(
            "RAG quality filtering failed for "
            f"{filter_result['failed_domains']} domains."
        )

    # ------------------------------------------------------------------
    # 8.4
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # 8.5
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    validation_result = (
        run_validation_phase(
            domains
        )
    )

    report = build_report(
        started_at=started_at,
        requested_domain=requested_domain,
        selected_inputs=selected_inputs,
        structure_result=structure_result,
        organization_result=organization_result,
        filter_result=filter_result,
        planning_result=planning_result,
        build_result=build_result,
        validation_result=validation_result,
    )

    report_path = (
        PIPELINE_REPORT_ROOT
        / "final_rag_pipeline_report.json"
    )

    write_json(
        report_path,
        report,
    )

    # ------------------------------------------------------------------
    # Final terminal summary
    # ------------------------------------------------------------------

    print()
    print("=" * 100)
    print(
        "FINAL ENGINEERING-COLLEGE RAG BUILD"
    )
    print("=" * 100)

    print(
        "Status:",
        report[
            "status"
        ],
    )

    print()
    print(
        "Existing crawled inputs:",
        report[
            "selected_crawled_inputs"
        ],
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
        "  Knowledge units:",
        organization_result[
            "knowledge_units"
        ],
    )

    print(
        "  REVIEW:",
        organization_result[
            "review_units"
        ],
    )

    print()
    print(
        "RAG QUALITY FILTER"
    )

    print(
        "  Input:",
        filter_result[
            "input_units"
        ],
    )

    print(
        "  Final RAG:",
        filter_result[
            "final_rag_units"
        ],
    )

    print(
        "  Excluded:",
        filter_result[
            "excluded_units"
        ],
    )

    print(
        "  REVIEW kept:",
        filter_result[
            "review_keep"
        ],
    )

    print(
        "  REVIEW excluded:",
        filter_result[
            "review_exclude"
        ],
    )

    print(
        "  URLs removed:",
        filter_result[
            "urls_removed"
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
        "  REVIEW RAG units:",
        planning_result[
            "review_rag_units"
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
        "8.5 — FINAL RAG"
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
        "  Passed:",
        validation_result[
            "passed_domains"
        ],
    )

    print(
        "  Failed:",
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
        (
            "PASS"
            if validation_result[
                "failed_domains"
            ] == 0
            else "FAIL"
        ),
    )

    print()
    print(
        "FINAL RAG OUTPUT:"
    )

    print(
        FINAL_RAG_ROOT
        / requested_domain
    )

    print()
    print(
        "PIPELINE REPORT:"
    )

    print(
        report_path
    )

    print()
    print(
        "NO CRAWL WAS PERFORMED."
    )

    print("=" * 100)

    if validation_result[
        "failed_domains"
    ]:

        raise RuntimeError(
            "Final RAG validation failed."
        )

    return report


# ============================================================================
# CLI
# ============================================================================

def build_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        description=(
            "Build final RAG data from an "
            "existing engineering-college crawl."
        )
    )

    parser.add_argument(
        "--domain",
        required=True,
        help=(
            "Existing crawled domain, "
            "for example www.iitj.ac.in"
        ),
    )

    return parser


def main() -> None:

    parser = build_parser()

    args = parser.parse_args()

    run_pipeline(
        requested_domain=args.domain
    )


if __name__ == "__main__":
    main()