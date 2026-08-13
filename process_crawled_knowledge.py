from pathlib import Path
import json
import shutil
import sys

from processors.knowledge_structurer import KnowledgeStructurer
from processors.knowledge_organizer import KnowledgeOrganizer
from processors.rag_document_builder import RAGDocumentBuilder


# ============================================================
# CONFIGURATION
# ============================================================

OUTPUT_ROOT = Path(
    "storage/output"
)

KNOWLEDGE_ROOT = Path(
    "storage/knowledge"
)

STRUCTURED_ROOT = Path(
    "storage/structured_knowledge"
)

ORGANIZED_ROOT = Path(
    "storage/organized_knowledge"
)

RAG_ROOT = Path(
    "storage/rag_knowledge"
)


# ============================================================
# HELPERS
# ============================================================

def load_metadata(
    metadata_path: Path,
) -> dict:

    if not metadata_path.exists():
        return {}

    try:
        data = json.loads(
            metadata_path.read_text(
                encoding="utf-8"
            )
        )

        if isinstance(data, dict):
            return data

    except (
        json.JSONDecodeError,
        OSError,
    ):
        pass

    return {}


def copy_crawled_data(
    source_root: Path,
    knowledge_root: Path,
) -> list[tuple[Path, Path, Path]]:
    """
    Mirror crawled Markdown + metadata from:

        storage/output/<domain>/

    into:

        storage/knowledge/<domain>/

    This gives downstream processors the canonical
    knowledge path they already expect.

    Returns:
        list of tuples:
        (knowledge_markdown, knowledge_metadata, source_markdown)
    """

    documents = []

    markdown_files = sorted(
        source_root.rglob("*.md")
    )

    for source_markdown in markdown_files:

        relative_path = (
            source_markdown.relative_to(
                source_root
            )
        )

        target_markdown = (
            knowledge_root
            / relative_path
        )

        target_metadata = (
            target_markdown.with_suffix(
                ".json"
            )
        )

        source_metadata = (
            source_markdown.with_suffix(
                ".json"
            )
        )

        target_markdown.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.copy2(
            source_markdown,
            target_markdown,
        )

        if source_metadata.exists():

            shutil.copy2(
                source_metadata,
                target_metadata,
            )

        documents.append(
            (
                target_markdown,
                target_metadata,
                source_markdown,
            )
        )

    return documents


# ============================================================
# MAIN PIPELINE
# ============================================================

def process_domain(
    domain: str,
) -> None:

    domain = domain.strip()

    if not domain:
        raise ValueError(
            "Domain cannot be empty."
        )

    source_root = (
        OUTPUT_ROOT
        / domain
    )

    knowledge_domain_root = (
        KNOWLEDGE_ROOT
        / domain
    )

    organized_domain_root = (
        ORGANIZED_ROOT
        / domain
    )

    rag_domain_root = (
        RAG_ROOT
        / domain
    )

    if not source_root.exists():
        raise FileNotFoundError(
            f"Crawled domain does not exist: "
            f"{source_root}"
        )

    print("=" * 100)
    print(
        "KNOWLEDGE PIPELINE"
    )
    print("=" * 100)

    print(
        "Domain:",
        domain,
    )

    print(
        "Crawled source:",
        source_root,
    )

    # --------------------------------------------------------
    # RESET DOWNSTREAM OUTPUT FOR THIS DOMAIN
    # --------------------------------------------------------

    if knowledge_domain_root.exists():
        shutil.rmtree(
            knowledge_domain_root
        )

    if organized_domain_root.exists():
        shutil.rmtree(
            organized_domain_root
        )

    if rag_domain_root.exists():
        shutil.rmtree(
            rag_domain_root
        )

    # --------------------------------------------------------
    # MIRROR CRAWLED DATA
    # --------------------------------------------------------

    print()
    print("=" * 100)
    print(
        "STEP 1 — CRAWLED MARKDOWN → KNOWLEDGE"
    )
    print("=" * 100)

    documents = copy_crawled_data(
        source_root,
        knowledge_domain_root,
    )

    if not documents:
        raise AssertionError(
            f"No Markdown documents found "
            f"under {source_root}"
        )

    print(
        "Documents copied:",
        len(documents),
    )

    # --------------------------------------------------------
    # INITIALIZE PROCESSORS
    # --------------------------------------------------------

    structurer = KnowledgeStructurer(
        output_path=STRUCTURED_ROOT
    )

    organizer = KnowledgeOrganizer(
        output_path=ORGANIZED_ROOT
    )

    builder = RAGDocumentBuilder(
        output_root=RAG_ROOT
    )

    structured_count = 0
    organized_count = 0

    # --------------------------------------------------------
    # PROCESS EVERY DOCUMENT
    # --------------------------------------------------------

    print()
    print("=" * 100)
    print(
        "STEP 2 — STRUCTURE + ORGANIZE"
    )
    print("=" * 100)

    for index, (
        markdown_path,
        metadata_path,
        source_markdown,
    ) in enumerate(
        documents,
        start=1,
    ):

        print()
        print("-" * 100)
        print(
            f"[{index}/{len(documents)}]"
        )

        print(
            "Markdown:",
            markdown_path,
        )

        # ----------------------------------------------------
        # METADATA CHECK
        # ----------------------------------------------------

        if not metadata_path.exists():

            print(
                "WARNING: Metadata missing."
            )

            print(
                "Skipping structure test "
                "for this document."
            )

            continue

        # ----------------------------------------------------
        # 7.4 STRUCTURE
        # ----------------------------------------------------

        try:

            structured_result = (
                structurer.structure(
                    markdown_path=(
                        markdown_path
                    ),
                    metadata_path=(
                        metadata_path
                    ),
                )
            )

            print(
                "Structured:",
                structured_result,
            )

            structured_count += 1

        except Exception as exc:

            print(
                "STRUCTURE FAILED:",
                exc,
            )

            # Do not silently continue on
            # real knowledge failures.
            raise

        # ----------------------------------------------------
        # 8.3 ORGANIZATION
        # ----------------------------------------------------

        try:

            organized_result = (
                organizer.organize(
                    markdown_path
                )
            )

            print(
                "Organized sections:",
                organized_result.get(
                    "organized_sections",
                    0,
                ),
            )

            print(
                "Written files:",
                len(
                    organized_result.get(
                        "written_files",
                        [],
                    )
                ),
            )

            organized_count += 1

        except Exception as exc:

            print(
                "ORGANIZATION FAILED:",
                exc,
            )

            raise

    # --------------------------------------------------------
    # 8.5 BUILD FINAL RAG DOCX
    # --------------------------------------------------------

    print()
    print("=" * 100)
    print(
        "STEP 3 — FINAL RAG DOCX"
    )
    print("=" * 100)

    result = builder.build_domain(
        organized_domain_root
    )

    print()
    print(
        "Final RAG categories:",
        result["categories"],
    )

    print(
        "Final RAG DOCX files:",
        result["files"],
    )

    print(
        "Final RAG sections:",
        result["sections"],
    )

    print()
    print(
        "GENERATED RAG FILES"
    )

    for category, path in sorted(
        result[
            "category_files"
        ].items()
    ):

        print(
            f"{category:25s}: {path}"
        )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print()
    print("=" * 100)
    print(
        "PIPELINE COMPLETE"
    )
    print("=" * 100)

    print(
        "Domain:",
        domain,
    )

    print(
        "Crawled Markdown:",
        len(documents),
    )

    print(
        "Structured:",
        structured_count,
    )

    print(
        "Organized:",
        organized_count,
    )

    print(
        "Final RAG DOCX:",
        result["files"],
    )

    print()
    print(
        "KNOWLEDGE:",
        knowledge_domain_root,
    )

    print(
        "STRUCTURED:",
        STRUCTURED_ROOT / domain,
    )

    print(
        "ORGANIZED:",
        organized_domain_root,
    )

    print(
        "FINAL RAG:",
        rag_domain_root,
    )

    print("=" * 100)


# ============================================================
# CLI
# ============================================================

def main():

    if len(sys.argv) != 2:

        print(
            "Usage:"
        )

        print(
            "  python process_crawled_knowledge.py "
            "<domain>"
        )

        print()
        print(
            "Example:"
        )

        print(
            "  python process_crawled_knowledge.py "
            "www.iitj.ac.in"
        )

        raise SystemExit(1)

    process_domain(
        sys.argv[1]
    )


if __name__ == "__main__":
    main()