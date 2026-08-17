from pathlib import Path
import json
import shutil

from processors.pdf_processor import PDFProcessor


TEST_DOCUMENTS = [
    {
        "pdf": (
            "storage/test_documents/"
            "www.iitj.ac.in/"
            "institute-sustainability-committee-638779148376488067.pdf"
        ),
        "domain": "www.iitj.ac.in",
        "source_url": (
            "https://www.iitj.ac.in/"
            "PageImages/Gallery/03-2025/"
            "institute-sustainability-committee-638779148376488067.pdf"
        ),
    },
    {
        "pdf": (
            "storage/test_documents/"
            "home.iitd.ac.in/"
            "newsletter-apr-26-issue.pdf"
        ),
        "domain": "home.iitd.ac.in",
        "source_url": (
            "https://home.iitd.ac.in/"
            "uploads/Newsletter-Apr-26-Issue.pdf"
        ),
    },
]


TEST_OUTPUT = Path(
    "storage/test_processed_documents"
)


def test_pdf(
    processor: PDFProcessor,
    document: dict,
):
    pdf_path = Path(
        document["pdf"]
    )

    domain = document["domain"]

    source_url = document["source_url"]

    print("\n" + "=" * 90)
    print("TESTING PDF PROCESSING")
    print("=" * 90)

    print(
        "PDF:",
        pdf_path,
    )

    # --------------------------------------------------------
    # INPUT VALIDATION
    # --------------------------------------------------------

    assert pdf_path.exists(), (
        f"Input PDF does not exist: {pdf_path}"
    )

    assert pdf_path.is_file(), (
        f"Input PDF is not a file: {pdf_path}"
    )

    assert pdf_path.suffix.lower() == ".pdf", (
        f"Expected PDF: {pdf_path}"
    )

    # --------------------------------------------------------
    # PROCESS
    # --------------------------------------------------------

    output_file = processor.process(
        pdf_path=pdf_path,
        source_url=source_url,
    )

    # --------------------------------------------------------
    # OUTPUT MARKDOWN
    # --------------------------------------------------------

    assert output_file.exists(), (
        f"Markdown output missing: {output_file}"
    )

    assert output_file.is_file(), (
        f"Markdown output is not a file: {output_file}"
    )

    assert output_file.suffix == ".md", (
        f"Expected Markdown output: {output_file}"
    )

    # --------------------------------------------------------
    # MARKDOWN CONTENT
    # --------------------------------------------------------

    markdown = output_file.read_text(
        encoding="utf-8"
    )

    assert markdown.strip(), (
        f"Extracted Markdown is empty: {output_file}"
    )

    assert "## Page 1" in markdown, (
        f"Page boundary missing: {output_file}"
    )

    # --------------------------------------------------------
    # METADATA
    # --------------------------------------------------------

    metadata_file = (
        output_file.with_suffix(".json")
    )

    assert metadata_file.exists(), (
        f"Metadata file missing: {metadata_file}"
    )

    metadata = json.loads(
        metadata_file.read_text(
            encoding="utf-8"
        )
    )

    # --------------------------------------------------------
    # METADATA VALIDATION
    # --------------------------------------------------------

    assert metadata["source_url"] == source_url

    assert metadata["source_file"] == str(
        pdf_path
    )

    assert metadata["document_type"] == "pdf"

    assert metadata["pages"] >= 1

    assert metadata["pages_with_text"] >= 0

    assert metadata["text_length"] >=0

    assert metadata["extraction_success"] is True

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    print(
        "Domain          :",
        domain,
    )

    print(
        "Markdown        :",
        output_file,
    )

    print(
        "Metadata        :",
        metadata_file,
    )

    print(
        "Pages           :",
        metadata["pages"],
    )

    print(
        "Pages w/text    :",
        metadata["pages_with_text"],
    )

    print(
        "Text length     :",
        metadata["text_length"],
    )

    print(
        "PASS:",
        source_url,
    )


def main():

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

    processor = PDFProcessor(
        output_path=TEST_OUTPUT
    )

    passed = 0

    # --------------------------------------------------------
    # PROCESS TEST DOCUMENTS
    # --------------------------------------------------------

    for document in TEST_DOCUMENTS:

        try:

            test_pdf(
                processor,
                document,
            )

            passed += 1

        except Exception as error:

            print(
                "\nFAILED:",
                document["source_url"],
            )

            print(
                type(error).__name__,
                ":",
                error,
            )

            raise

    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    print(
        "\n" + "=" * 90
    )

    print(
        "PDF PROCESSING RESULTS"
    )

    print(
        "=" * 90
    )

    print(
        "Documents passed:",
        passed,
        "/",
        len(TEST_DOCUMENTS),
    )

    assert passed == len(
        TEST_DOCUMENTS
    )

    print(
        "\nPHASE 6.4 PDF PROCESSING: PASS"
    )


if __name__ == "__main__":
    main()
