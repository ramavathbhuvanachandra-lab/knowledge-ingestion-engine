from __future__ import annotations

import json
import traceback
from pathlib import Path
from typing import Any

from processors.knowledge_input_discovery import (
    KnowledgeInputDiscovery,
)
from processors.knowledge_structurer import (
    KnowledgeStructurer,
)
from processors.knowledge_document_generator import (
    KnowledgeDocumentGenerator,
)
from processors.knowledge_organizer import (
    KnowledgeOrganizer,
)
from processors.knowledge_rag_planner import (
    KnowledgeRAGPlanner,
)
from processors.rag_document_builder import (
    RAGDocumentBuilder,
)


# ============================================================
# PIPELINE CONFIGURATION
# ============================================================

OUTPUT_ROOT = Path(
    "storage/output"
)

STRUCTURED_ROOT = Path(
    "storage/structured_knowledge"
)

KNOWLEDGE_ROOT = Path(
    "storage/knowledge"
)

ORGANIZED_ROOT = Path(
    "storage/organized_knowledge"
)

RAG_ROOT = Path(
    "storage/rag_knowledge"
)

PIPELINE_REPORT_ROOT = Path(
    "storage/pipeline_reports"
)


# ============================================================
# GENERAL HELPERS
# ============================================================

def _safe_path(
    value: Any,
) -> Path | None:

    if value is None:
        return None

    try:
        path = Path(value)

    except TypeError:
        return None

    return path


def _get_attribute(
    obj: Any,
    *names: str,
) -> Any:

    for name in names:

        if hasattr(obj, name):

            value = getattr(
                obj,
                name,
            )

            if value is not None:
                return value

    return None


def _get_input_paths(
    item: Any,
) -> tuple[Path | None, Path | None]:
    """
    Resolve the Markdown/retrieval input and metadata input from
    a KnowledgeInput object without assuming one exact field name.

    This keeps the orchestration layer tolerant of harmless
    naming changes in KnowledgeInput.
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

    # Standard sibling JSON.
    sibling = markdown_path.with_suffix(
        ".json"
    )

    if sibling.exists():

        return sibling

    # Some pipeline stages may use a nearby
    # metadata file with the same stem.
    parent = markdown_path.parent

    candidates = sorted(
        parent.glob(
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

    known_roots = {
        "output",
        "structured_knowledge",
        "knowledge",
        "organized_knowledge",
        "rag_knowledge",
    }

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


# ============================================================
# PHASE 7.4
# ============================================================

def run_structure_phase(
    inputs: list[Any],
) -> dict:

    print()
    print("=" * 100)
    print("PHASE 7.4 — KNOWLEDGE STRUCTURING")
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
                    "Could not resolve input path from "
                    f"KnowledgeInput: {item!r}"
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
                    "Metadata file could not be resolved for: "
                    f"{markdown_path}"
                )

            print(
                f"[7.4 {index}/{len(inputs)}] "
                f"{markdown_path}"
            )

            structured_md, structured_json = (
                structurer.structure(
                    markdown_path=(
                        markdown_path
                    ),
                    metadata_path=(
                        metadata_path
                    ),
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
                    "input": (
                        str(
                            _get_attribute(
                                item,
                                "markdown_path",
                                "retrieval_path",
                                "input_path",
                                "path",
                            )
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


# ============================================================
# PHASE 8.1
# ============================================================

def run_document_generation_phase(
    structure_results: list[dict],
) -> dict:

    print()
    print("=" * 100)
    print("PHASE 8.1 — KNOWLEDGE DOCUMENT GENERATION")
    print("=" * 100)

    generator = KnowledgeDocumentGenerator(
        output_path=KNOWLEDGE_ROOT
    )

    processed = 0
    failed = 0
    results = []

    for index, result in enumerate(
        structure_results,
        start=1,
    ):

        if result.get(
            "status"
        ) != "success":

            continue

        structured_json = _safe_path(
            result.get(
                "structured_json"
            )
        )

        if (
            structured_json is None
            or not structured_json.exists()
        ):

            print(
                "[8.1 SKIP]",
                "Structured JSON missing:",
                structured_json,
            )

            continue

        try:

            print(
                f"[8.1 {index}] "
                f"{structured_json}"
            )

            output_path = (
                generator.process(
                    retrieval_path=(
                        structured_json
                    )
                )
            )

            processed += 1

            results.append(
                {
                    "input": str(
                        structured_json
                    ),
                    "output": str(
                        output_path
                    ),
                    "status": "success",
                }
            )

        except Exception as error:

            failed += 1

            print(
                "[8.1 FAILED]",
                error,
            )

            results.append(
                {
                    "input": str(
                        structured_json
                    ),
                    "status": "failed",
                    "error": (
                        f"{type(error).__name__}: "
                        f"{error}"
                    ),
                }
            )

    return {
        "inputs": len(structure_results),
        "processed": processed,
        "failed": failed,
        "results": results,
    }


# ============================================================
# PHASE 8.3
# ============================================================

def run_organization_phase(
    knowledge_files: list[Path],
) -> dict:

    print()
    print("=" * 100)
    print("PHASE 8.3 — KNOWLEDGE ORGANIZATION")
    print("=" * 100)

    organizer = KnowledgeOrganizer(
        output_path=ORGANIZED_ROOT
    )

    processed = 0
    failed = 0
    results = []

    for index, markdown_path in enumerate(
        knowledge_files,
        start=1,
    ):

        try:

            print(
                f"[8.3 {index}/{len(knowledge_files)}] "
                f"{markdown_path}"
            )

            result = organizer.organize(
                markdown_path
            )

            processed += 1

            results.append(
                {
                    "input": str(
                        markdown_path
                    ),
                    "status": "success",
                    "result": result,
                }
            )

        except Exception as error:

            failed += 1

            print(
                "[8.3 FAILED]",
                markdown_path,
                error,
            )

            results.append(
                {
                    "input": str(
                        markdown_path
                    ),
                    "status": "failed",
                    "error": (
                        f"{type(error).__name__}: "
                        f"{error}"
                    ),
                }
            )

    return {
        "inputs": len(knowledge_files),
        "processed": processed,
        "failed": failed,
        "results": results,
    }


# ============================================================
# PHASE 8.4 + 8.5
# ============================================================

def discover_domains() -> list[str]:

    if not ORGANIZED_ROOT.exists():

        return []

    domains = []

    for path in sorted(
        ORGANIZED_ROOT.iterdir()
    ):

        if (
            path.is_dir()
            and not path.name.startswith(".")
        ):

            domains.append(
                path.name
            )

    return domains


def run_rag_phase(
    domains: list[str],
) -> dict:

    print()
    print("=" * 100)
    print("PHASE 8.4 — DYNAMIC RAG PLANNING")
    print("=" * 100)

    planner = KnowledgeRAGPlanner(
        organized_root=ORGANIZED_ROOT
    )

    planner_results = []

    for index, domain in enumerate(
        domains,
        start=1,
    ):

        try:

            print(
                f"[8.4 {index}/{len(domains)}] "
                f"{domain}"
            )

            result = planner.plan_domain(
                domain
            )

            planner_results.append(
                {
                    "domain": domain,
                    "status": "success",
                    "result": result,
                }
            )

        except Exception as error:

            print(
                "[8.4 FAILED]",
                domain,
                error,
            )

            planner_results.append(
                {
                    "domain": domain,
                    "status": "failed",
                    "error": (
                        f"{type(error).__name__}: "
                        f"{error}"
                    ),
                }
            )

    # --------------------------------------------------------
    # 8.5
    # --------------------------------------------------------

    print()
    print("=" * 100)
    print("PHASE 8.5 — RAG DOCUMENT BUILDING")
    print("=" * 100)

    builder = RAGDocumentBuilder(
        output_root=RAG_ROOT
    )

    builder_results = []

    for index, domain in enumerate(
        domains,
        start=1,
    ):

        try:

            organized_domain_root = (
                ORGANIZED_ROOT
                / domain
            )

            print(
                f"[8.5 {index}/{len(domains)}] "
                f"{domain}"
            )

            result = (
                builder.build_domain(
                    organized_root=(
                        organized_domain_root
                    )
                )
            )

            builder_results.append(
                {
                    "domain": domain,
                    "status": "success",
                    "result": result,
                }
            )

        except Exception as error:

            print(
                "[8.5 FAILED]",
                domain,
                error,
            )

            builder_results.append(
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
        "domains": domains,
        "planner": planner_results,
        "builder": builder_results,
    }


# ============================================================
# FINAL REPORT
# ============================================================

def build_final_report(
    discovery_result: dict,
    structure_result: dict,
    document_result: dict,
    organization_result: dict,
    rag_result: dict,
) -> dict:

    rag_docx_count = _count_files(
        RAG_ROOT,
        ".docx",
    )

    knowledge_md_count = _count_files(
        KNOWLEDGE_ROOT,
        ".md",
    )

    organized_md_count = _count_files(
        ORGANIZED_ROOT,
        ".md",
    )

    report = {
        "status": "completed",
        "pipeline": {
            "source": str(
                OUTPUT_ROOT
            ),
            "structured": str(
                STRUCTURED_ROOT
            ),
            "knowledge": str(
                KNOWLEDGE_ROOT
            ),
            "organized": str(
                ORGANIZED_ROOT
            ),
            "rag": str(
                RAG_ROOT
            ),
        },
        "discovery": discovery_result,
        "phase_7_4": {
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
        "phase_8_1": {
            "inputs": document_result[
                "inputs"
            ],
            "processed": document_result[
                "processed"
            ],
            "failed": document_result[
                "failed"
            ],
        },
        "phase_8_3": {
            "inputs": organization_result[
                "inputs"
            ],
            "processed": organization_result[
                "processed"
            ],
            "failed": organization_result[
                "failed"
            ],
        },
        "phase_8_4": {
            "domains": rag_result[
                "domains"
            ],
            "planner_results": rag_result[
                "planner"
            ],
        },
        "phase_8_5": {
            "builder_results": rag_result[
                "builder"
            ],
        },
        "final_counts": {
            "knowledge_markdown_files": (
                knowledge_md_count
            ),
            "organized_markdown_files": (
                organized_md_count
            ),
            "rag_docx_files": (
                rag_docx_count
            ),
        },
    }

    return report


# ============================================================
# MAIN PIPELINE
# ============================================================

def main() -> None:

    print()
    print("=" * 100)
    print("UNIVERSAL KNOWLEDGE → RAG DOCX PIPELINE")
    print("=" * 100)

    # --------------------------------------------------------
    # CHECK SOURCE
    # --------------------------------------------------------

    if not OUTPUT_ROOT.exists():

        raise FileNotFoundError(
            f"Source directory does not exist: "
            f"{OUTPUT_ROOT}"
        )

    # --------------------------------------------------------
    # DISCOVERY
    # --------------------------------------------------------

    print()
    print("=" * 100)
    print("INPUT DISCOVERY")
    print("=" * 100)

    discovery = KnowledgeInputDiscovery(
        input_path=OUTPUT_ROOT
    )

    inputs = discovery.discover()

    print(
        "Discovered inputs:",
        len(inputs),
    )

    if not inputs:

        raise RuntimeError(
            "No knowledge inputs discovered "
            f"under {OUTPUT_ROOT}"
        )

    # --------------------------------------------------------
    # 7.4
    # --------------------------------------------------------

    structure_result = (
        run_structure_phase(
            inputs
        )
    )

    if (
        structure_result[
            "processed"
        ] == 0
    ):

        raise RuntimeError(
            "Phase 7.4 produced zero successful outputs."
        )

    # --------------------------------------------------------
    # 8.1
    # --------------------------------------------------------

    document_result = (
        run_document_generation_phase(
            structure_result[
                "results"
            ]
        )
    )

    if (
        document_result[
            "processed"
        ] == 0
    ):

        raise RuntimeError(
            "Phase 8.1 produced zero knowledge documents."
        )

    # --------------------------------------------------------
    # FIND GENERATED KNOWLEDGE DOCUMENTS
    # --------------------------------------------------------

    knowledge_files = sorted(
        path
        for path in KNOWLEDGE_ROOT.rglob(
            "*.md"
        )
        if path.is_file()
    )

    print()
    print(
        "Knowledge documents available for 8.3:",
        len(
            knowledge_files
        ),
    )

    if not knowledge_files:

        raise RuntimeError(
            "No knowledge Markdown documents found "
            f"under {KNOWLEDGE_ROOT}"
        )

    # --------------------------------------------------------
    # 8.3
    # --------------------------------------------------------

    organization_result = (
        run_organization_phase(
            knowledge_files
        )
    )

    if (
        organization_result[
            "processed"
        ] == 0
    ):

        raise RuntimeError(
            "Phase 8.3 produced zero successful outputs."
        )

    # --------------------------------------------------------
    # 8.4 + 8.5
    # --------------------------------------------------------

    domains = discover_domains()

    if not domains:

        raise RuntimeError(
            "No organized knowledge domains were found "
            f"under {ORGANIZED_ROOT}"
        )

    rag_result = run_rag_phase(
        domains
    )

    # --------------------------------------------------------
    # FINAL REPORT
    # --------------------------------------------------------

    report = build_final_report(
        discovery_result={
            "discovered_inputs": len(
                inputs
            ),
        },
        structure_result=(
            structure_result
        ),
        document_result=(
            document_result
        ),
        organization_result=(
            organization_result
        ),
        rag_result=rag_result,
    )

    report_path = (
        PIPELINE_REPORT_ROOT
        / "pipeline_report.json"
    )

    _write_json(
        report_path,
        report,
    )

    # --------------------------------------------------------
    # FINAL SUMMARY
    # --------------------------------------------------------

    print()
    print("=" * 100)
    print("PIPELINE COMPLETE")
    print("=" * 100)

    print(
        "Discovered inputs       :",
        report[
            "discovery"
        ][
            "discovered_inputs"
        ],
    )

    print(
        "Phase 7.4 processed     :",
        report[
            "phase_7_4"
        ][
            "processed"
        ],
    )

    print(
        "Phase 8.1 processed     :",
        report[
            "phase_8_1"
        ][
            "processed"
        ],
    )

    print(
        "Phase 8.3 processed     :",
        report[
            "phase_8_3"
        ][
            "processed"
        ],
    )

    print(
        "RAG domains             :",
        len(
            report[
                "phase_8_4"
            ][
                "domains"
            ]
        ),
    )

    print(
        "Knowledge Markdown      :",
        report[
            "final_counts"
        ][
            "knowledge_markdown_files"
        ],
    )

    print(
        "Organized Markdown      :",
        report[
            "final_counts"
        ][
            "organized_markdown_files"
        ],
    )

    print(
        "FINAL RAG DOCX          :",
        report[
            "final_counts"
        ][
            "rag_docx_files"
        ],
    )

    print()
    print(
        "Pipeline Report         :",
        report_path,
    )

    print()
    print(
        "RAG data is COMPLETE through DOCX."
    )

    print(
        "Chunking / embeddings / vector DB were NOT run."
    )

    print("=" * 100)


if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        print(
            "\nPipeline interrupted by user."
        )

        raise SystemExit(130)

    except Exception as error:

        print()
        print("=" * 100)
        print("PIPELINE FAILED")
        print("=" * 100)

        print(
            f"{type(error).__name__}: {error}"
        )

        print()
        traceback.print_exc()

        raise SystemExit(1)