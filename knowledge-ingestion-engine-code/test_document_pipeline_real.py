from pathlib import Path
import json
import shutil

from processors.document_downloader import DocumentDownloader
from processors.pdf_processor import PDFProcessor


# ============================================================
# REAL DOCUMENT PIPELINE TEST
# ============================================================

TEST_DOCUMENTS = [
    {
        "url": (
            "https://www.iitj.ac.in/"
            "PageImages/Gallery/03-2025/"
            "institute-sustainability-committee-638779148376488067.pdf"
        ),
        "domain": "www.iitj.ac.in",
    },
    {
        "url": (
            "https://home.iitd.ac.in/"
            "uploads/Newsletter-Apr-26-Issue.pdf"
        ),
        "domain": "home.iitd.ac.in",
    },
]


# ============================================================
# TEST STORAGE
# ============================================================

RAW_OUTPUT = Path(
    "storage/test_pipeline_documents"
)

PROCESSED_OUTPUT = Path(
    "storage/test_pipeline_processed_documents"
)


# ============================================================
# TEST ONE DOCUMENT
# ============================================================

def test_document_pipeline(
    downloader: DocumentDownloader,
    processor: PDFProcessor,
    document: dict,
):
    url = document["url"]
    domain = document["domain"]

    print("\n" + "=" * 100)
    print("TESTING DOCUMENT PIPELINE")
    print("=" * 100)

    print("Source URL :", url)
    print("Domain     :", domain)

    # ========================================================
    # STEP 1 — DOWNLOAD
    # ========================================================

    print("\n[1] DOWNLOADING DOCUMENT")

    pdf_path = downloader.download(
        url=url,
        domain=domain,
    )

    # --------------------------------------------------------
    # RAW PDF VALIDATION
    # --------------------------------------------------------

    assert pdf_path.exists(), (
        f"Downloaded PDF missing: {pdf_path}"
    )

    assert pdf_path.is_file(), (
        f"Downloaded path is not a file: {pdf_path}"
    )

    assert pdf_path.suffix.lower() == ".pdf", (
        f"Expected PDF file: {pdf_path}"
    )

    pdf_size = pdf_path.stat().st_size

    assert pdf_size > 0, (
        f"Downloaded PDF is empty: {pdf_path}"
    )

    header = pdf_path.read_bytes()[:5]

    assert header == b"%PDF-", (
        f"Downloaded file is not a PDF: {pdf_path}"
    )

    print("PDF        :", pdf_path)
    print("PDF size   :", pdf_size)
    print("PDF header :", header)

    # ========================================================
    # STEP 2 — DOWNLOADER METADATA
    # ========================================================

    print("\n[2] VALIDATING DOWNLOAD METADATA")

    download_metadata_path = (
        pdf_path.with_suffix(".json")
    )

    assert download_metadata_path.exists(), (
        "Downloader metadata missing: "
        f"{download_metadata_path}"
    )

    download_metadata = json.loads(
        download_metadata_path.read_text(
            encoding="utf-8"
        )
    )

    assert (
        download_metadata["source_url"] == url
    )

    assert (
        download_metadata["domain"] == domain
    )

    assert (
        download_metadata["document_type"] == "pdf"
    )

    assert (
        download_metadata["success"] is True
    )

    assert (
        download_metadata["size_bytes"]
        == pdf_size
    )

    assert (
        download_metadata["local_file"]
        == str(pdf_path)
    )

    print(
        "Download metadata:",
        download_metadata_path,
    )

    # ========================================================
    # STEP 3 — PDF PROCESSING
    # ========================================================

    print("\n[3] PROCESSING PDF")

    markdown_path = processor.process(
        pdf_path=pdf_path,
        source_url=url,
    )

    # --------------------------------------------------------
    # MARKDOWN VALIDATION
    # --------------------------------------------------------

    assert markdown_path.exists(), (
        f"Processed Markdown missing: "
        f"{markdown_path}"
    )

    assert markdown_path.is_file(), (
        f"Processed output is not a file: "
        f"{markdown_path}"
    )

    assert markdown_path.suffix == ".md", (
        f"Expected Markdown output: "
        f"{markdown_path}"
    )

    markdown = markdown_path.read_text(
        encoding="utf-8"
    )

    assert markdown.strip(), (
        f"Processed Markdown is empty: "
        f"{markdown_path}"
    )

    assert "## Page 1" in markdown, (
        f"Page boundary missing: "
        f"{markdown_path}"
    )

    print(
        "Markdown   :",
        markdown_path,
    )

    print(
        "Text size  :",
        len(markdown),
    )

    # ========================================================
    # STEP 4 — PROCESSOR METADATA
    # ========================================================

    print("\n[4] VALIDATING PROCESSING METADATA")

    processing_metadata_path = (
        markdown_path.with_suffix(".json")
    )

    assert processing_metadata_path.exists(), (
        "Processing metadata missing: "
        f"{processing_metadata_path}"
    )

    processing_metadata = json.loads(
        processing_metadata_path.read_text(
            encoding="utf-8"
        )
    )

    assert (
        processing_metadata["source_url"]
        == url
    )

    assert (
        processing_metadata["source_file"]
        == str(pdf_path)
    )

    assert (
        processing_metadata["document_type"]
        == "pdf"
    )

    assert (
        processing_metadata["pages"]
        >= 1
    )

    assert (
        processing_metadata["pages_with_text"]
        >= 0
    )

    assert (
        processing_metadata["text_length"]
        >= 0
    )

    assert (
        processing_metadata["extraction_success"]
        is True
    )

    print(
        "Processing metadata:",
        processing_metadata_path,
    )

    print(
        "Pages       :",
        processing_metadata["pages"],
    )

    print(
        "Pages text  :",
        processing_metadata["pages_with_text"],
    )

    print(
        "Text length :",
        processing_metadata["text_length"],
    )

    # ========================================================
    # STEP 5 — DOMAIN STORAGE VALIDATION
    # ========================================================

    print("\n[5] VALIDATING DOMAIN STORAGE")

    expected_raw_domain = (
        RAW_OUTPUT / domain
    )

    expected_processed_domain = (
        PROCESSED_OUTPUT / domain
    )

    assert expected_raw_domain.exists(), (
        f"Raw domain directory missing: "
        f"{expected_raw_domain}"
    )

    assert expected_processed_domain.exists(), (
        f"Processed domain directory missing: "
        f"{expected_processed_domain}"
    )

    # ========================================================
    # STEP 6 — PIPELINE RELATIONSHIP
    # ========================================================

    print("\n[6] VALIDATING PIPELINE RELATIONSHIP")

    assert pdf_path.parent == (
        expected_raw_domain
    )

    assert markdown_path.parent == (
        expected_processed_domain
    )

    assert pdf_path.stem == (
        markdown_path.stem
    )

    print(
        "Raw PDF and processed Markdown "
        "belong to the same document."
    )

    print(
        "PASS:",
        url,
    )


# ============================================================
# MAIN
# ============================================================

def main():

    # --------------------------------------------------------
    # CLEAN TEST OUTPUT
    # --------------------------------------------------------

    if RAW_OUTPUT.exists():
        shutil.rmtree(
            RAW_OUTPUT
        )

    if PROCESSED_OUTPUT.exists():
        shutil.rmtree(
            PROCESSED_OUTPUT
        )

    RAW_OUTPUT.mkdir(
        parents=True,
        exist_ok=True,
    )

    PROCESSED_OUTPUT.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # CREATE COMPONENTS
    # --------------------------------------------------------

    downloader = DocumentDownloader(
        base_path=RAW_OUTPUT
    )

    processor = PDFProcessor(
        output_path=PROCESSED_OUTPUT
    )

    # --------------------------------------------------------
    # RUN TESTS
    # --------------------------------------------------------

    passed = 0

    for document in TEST_DOCUMENTS:

        try:

            test_document_pipeline(
                downloader=downloader,
                processor=processor,
                document=document,
            )

            passed += 1

        except Exception as error:

            print(
                "\nFAILED:",
                document["url"],
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
        "\n" + "=" * 100
    )

    print(
        "DOCUMENT PIPELINE INTEGRATION RESULTS"
    )

    print(
        "=" * 100
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
        "\nPHASE 6.5 DOCUMENT PIPELINE "
        "INTEGRATION: PASS"
    )


if __name__ == "__main__":
    main()