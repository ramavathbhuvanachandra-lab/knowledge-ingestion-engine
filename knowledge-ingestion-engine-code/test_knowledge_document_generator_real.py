from pathlib import Path
import json
import shutil

from processors.knowledge_document_generator import (
    KnowledgeDocumentGenerator,
)


TEST_RETRIEVAL_FILES = [
    Path(
        "storage/retrieval/"
        "iitj.ac.in/others/search.json"
    ),
    Path(
        "storage/retrieval/"
        "gwpgc.ac.in/others/"
        "government_girls_p_g_college_ghazipur.json"
    ),
    Path(
        "storage/retrieval/"
        "home.iitd.ac.in/others/"
        "newsletter-apr-26-issue.json"
    ),
]


TEST_OUTPUT = Path(
    "storage/test_knowledge"
)


def validate_output(
    output_path: Path,
    source_path: Path,
) -> None:

    # --------------------------------------------------------
    # FILE
    # --------------------------------------------------------

    assert output_path.exists(), (
        f"Output missing: {output_path}"
    )

    assert output_path.is_file(), (
        f"Output is not a file: {output_path}"
    )

    assert output_path.suffix == ".md", (
        f"Expected Markdown output: {output_path}"
    )

    # --------------------------------------------------------
    # SOURCE
    # --------------------------------------------------------

    source_data = json.loads(
        source_path.read_text(
            encoding="utf-8"
        )
    )

    document = source_data["document"]
    records = source_data["records"]

    assert records, (
        f"No source records: {source_path}"
    )

    # --------------------------------------------------------
    # CONTENT
    # --------------------------------------------------------

    content = output_path.read_text(
        encoding="utf-8"
    )

    assert content.strip(), (
        f"Generated document is empty: {output_path}"
    )

    # --------------------------------------------------------
    # DOCUMENT TITLE
    # --------------------------------------------------------

    title = document.get(
        "title"
    )

    if title:
        assert title in content, (
            f"Document title missing: {output_path}"
        )

    # --------------------------------------------------------
    # SOURCE URL
    # --------------------------------------------------------

    source_url = document.get(
        "url"
    )

    if source_url:
        assert source_url in content, (
            f"Source URL missing: {output_path}"
        )

    # --------------------------------------------------------
    # RECORD CONTENT
    # --------------------------------------------------------

    for record in records:

        text = record.get(
            "text",
            ""
        ).strip()

        if not text:
            continue

        # Check a meaningful portion of the
        # source record exists in the final document.

        sample = text[:100].strip()

        if sample:
            assert sample in content, (
                "Record content missing from "
                f"generated document: {output_path}"
            )

    # --------------------------------------------------------
    # BASIC MARKDOWN STRUCTURE
    # --------------------------------------------------------

    assert content.startswith(
        "# "
    ), (
        f"Missing Markdown title: {output_path}"
    )


def test_document(
    generator: KnowledgeDocumentGenerator,
    source_path: Path,
) -> None:

    print()
    print("=" * 90)
    print("TESTING KNOWLEDGE DOCUMENT")
    print("=" * 90)

    print(
        "Input :",
        source_path,
    )

    assert source_path.exists(), (
        f"Retrieval input missing: {source_path}"
    )

    assert source_path.is_file(), (
        f"Retrieval input is not a file: {source_path}"
    )

    # --------------------------------------------------------
    # PROCESS
    # --------------------------------------------------------

    output_path = generator.process(
        source_path
    )

    # --------------------------------------------------------
    # VALIDATE
    # --------------------------------------------------------

    validate_output(
        output_path=output_path,
        source_path=source_path,
    )

    # --------------------------------------------------------
    # LOAD OUTPUT
    # --------------------------------------------------------

    content = output_path.read_text(
        encoding="utf-8"
    )

    source_data = json.loads(
        source_path.read_text(
            encoding="utf-8"
        )
    )

    records = source_data[
        "records"
    ]

    print(
        "Output:",
        output_path,
    )

    print(
        "Records:",
        len(records),
    )

    print(
        "Characters:",
        len(content),
    )

    print(
        "PASS"
    )


def main():

    print()
    print("=" * 90)
    print(
        "PHASE 8.1 — KNOWLEDGE DOCUMENT GENERATION"
    )
    print("=" * 90)

    # --------------------------------------------------------
    # CLEAN TEST OUTPUT
    # --------------------------------------------------------

    if TEST_OUTPUT.exists():

        shutil.rmtree(
            TEST_OUTPUT
        )

    TEST_OUTPUT.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # GENERATOR
    # --------------------------------------------------------

    generator = KnowledgeDocumentGenerator(
        output_path=TEST_OUTPUT
    )

    passed = 0

    # --------------------------------------------------------
    # TEST DOCUMENTS
    # --------------------------------------------------------

    for source_path in TEST_RETRIEVAL_FILES:

        test_document(
            generator=generator,
            source_path=source_path,
        )

        passed += 1

    # --------------------------------------------------------
    # FINAL
    # --------------------------------------------------------

    print()
    print("=" * 90)
    print(
        "KNOWLEDGE DOCUMENT GENERATION RESULTS"
    )
    print("=" * 90)

    print(
        "Documents passed:",
        passed,
        "/",
        len(TEST_RETRIEVAL_FILES),
    )

    assert passed == len(
        TEST_RETRIEVAL_FILES
    )

    print()
    print(
        "PHASE 8.1 KNOWLEDGE DOCUMENT GENERATION: PASS"
    )


if __name__ == "__main__":
    main()