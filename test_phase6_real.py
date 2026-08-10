import asyncio
import json
import shutil
from pathlib import Path

from crawler.crawl_engine import CrawlEngine


TEST_URL = "https://" + "home.iitd.ac.in/"

TEST_STORAGE = Path(
    "storage/test_phase6_documents"
)

RAW_DIR = (
    TEST_STORAGE / "raw"
)

PROCESSED_DIR = (
    TEST_STORAGE / "processed"
)

INTEGRATED_DIR = (
    TEST_STORAGE / "integrated"
)


async def main():

    print("\n" + "=" * 100)
    print("PHASE 6 — EXTERNAL CONTENT PROCESSING")
    print("FINAL REAL INTEGRATION TEST")
    print("=" * 100)

    # ------------------------------------------------------------
    # CLEAN TEST STORAGE
    # ------------------------------------------------------------

    if TEST_STORAGE.exists():

        shutil.rmtree(
            TEST_STORAGE
        )

    TEST_STORAGE.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(
        "\nTEST URL:",
        TEST_URL,
    )

    # ------------------------------------------------------------
    # CREATE ENGINE
    # ------------------------------------------------------------

    engine = CrawlEngine()

    # ------------------------------------------------------------
    # RUN CRAWL
    # ------------------------------------------------------------

    print(
        "\n[1] RUNNING CRAWL ENGINE"
    )

    await engine.start(
        TEST_URL
    )

    # ------------------------------------------------------------
    # ENGINE VALIDATION
    # ------------------------------------------------------------

    print(
        "\n[2] VALIDATING CRAWL RESULTS"
    )

    print(
        "Pages crawled       :",
        engine.pages_crawled,
    )

    print(
        "Documents discovered:",
        engine.documents_discovered,
    )

    print(
        "Failed pages        :",
        engine.failed_pages,
    )

    assert engine.pages_crawled >= 1, (
        "No pages were crawled"
    )

    assert engine.failed_pages == 0, (
        f"Crawl had failed pages: "
        f"{engine.failed_pages}"
    )

    assert engine.documents_discovered >= 1, (
        "No external document was discovered"
    )

    # ------------------------------------------------------------
    # DOCUMENT INVENTORY
    # ------------------------------------------------------------

    print(
        "\n[3] VALIDATING DOCUMENT INVENTORY"
    )

    assert engine.document_inventory, (
        "Document inventory is empty"
    )

    for index, document in enumerate(
        engine.document_inventory.values(),
        start=1,
    ):

        print(
            f"\nDocument #{index}"
        )

        print(
            "URL   :",
            document["url"],
        )

        print(
            "Type  :",
            document["url_type"],
        )

        print(
            "Depth :",
            document["depth"],
        )

        print(
            "Sources:",
            len(
                document[
                    "discovered_from"
                ]
            ),
        )

    # ------------------------------------------------------------
    # FIND DOWNLOADED PDFs
    # ------------------------------------------------------------

    print(
        "\n[4] VALIDATING DOWNLOADED DOCUMENTS"
    )

    raw_pdfs = list(
        Path(
            "storage/test_crawl_engine_documents/raw"
        ).rglob("*.pdf")
    )

    raw_metadata = list(
        Path(
            "storage/test_crawl_engine_documents/raw"
        ).rglob("*.json")
    )

    print(
        "Raw PDFs     :",
        len(raw_pdfs),
    )

    print(
        "Raw metadata :",
        len(raw_metadata),
    )

    assert raw_pdfs, (
        "Documents were discovered "
        "but no PDF was downloaded"
    )

    assert raw_metadata, (
        "PDF exists but download metadata "
        "was not created"
    )

    # ------------------------------------------------------------
    # VALIDATE RAW PDF
    # ------------------------------------------------------------

    for pdf_file in raw_pdfs:

        print(
            "\nRaw PDF:",
            pdf_file,
        )

        assert pdf_file.is_file(), (
            f"Raw PDF is not a file: "
            f"{pdf_file}"
        )

        size = pdf_file.stat().st_size

        assert size > 0, (
            f"Raw PDF is empty: "
            f"{pdf_file}"
        )

        header = (
            pdf_file.read_bytes()[:5]
        )

        assert header == b"%PDF-", (
            f"Invalid PDF header: "
            f"{pdf_file}"
        )

        print(
            "Size   :",
            size,
        )

        print(
            "Header :",
            header,
        )

        print(
            "Raw PDF: PASS"
        )

    # ------------------------------------------------------------
    # VALIDATE DOWNLOAD METADATA
    # ------------------------------------------------------------

    for metadata_file in raw_metadata:

        metadata = json.loads(
            metadata_file.read_text(
                encoding="utf-8"
            )
        )

        assert metadata.get(
            "source_url"
        ), (
            f"Missing source_url: "
            f"{metadata_file}"
        )

        print(
            "Metadata:",
            metadata_file,
        )

        print(
            "Source URL:",
            metadata["source_url"],
        )

    # ------------------------------------------------------------
    # FIND PROCESSED DOCUMENTS
    # ------------------------------------------------------------

    print(
        "\n[5] VALIDATING PDF EXTRACTION"
    )

    processed_root = Path(
        "storage/test_crawl_engine_documents/processed"
    )

    markdown_files = list(
        processed_root.rglob("*.md")
    )

    processed_metadata = list(
        processed_root.rglob("*.json")
    )

    print(
        "Markdown          :",
        len(markdown_files),
    )

    print(
        "Processing metadata:",
        len(processed_metadata),
    )

    assert markdown_files, (
        "No processed Markdown was created"
    )

    assert processed_metadata, (
        "No processing metadata was created"
    )

    for markdown_file in markdown_files:

        content = markdown_file.read_text(
            encoding="utf-8"
        )

        assert content.strip(), (
            f"Processed Markdown is empty: "
            f"{markdown_file}"
        )

        print(
            "\nMarkdown:",
            markdown_file,
        )

        print(
            "Text size:",
            len(content),
        )

        print(
            "Markdown: PASS"
        )

    # ------------------------------------------------------------
    # VALIDATE PROCESSING METADATA
    # ------------------------------------------------------------

    for metadata_file in processed_metadata:

        metadata = json.loads(
            metadata_file.read_text(
                encoding="utf-8"
            )
        )

        assert metadata.get(
            "document_type"
        ) == "pdf", (
            f"Invalid document type: "
            f"{metadata_file}"
        )

        assert metadata.get(
            "pages"
        ) is not None, (
            f"Missing page count: "
            f"{metadata_file}"
        )

        print(
            "\nProcessing metadata:",
            metadata_file,
        )

        print(
            "Pages:",
            metadata["pages"],
        )

        print(
            "Pages with text:",
            metadata.get(
                "pages_with_text"
            ),
        )

        print(
            "Text length:",
            metadata.get(
                "text_length"
            ),
        )

    # ------------------------------------------------------------
    # FIND INTEGRATED DOCUMENTS
    # ------------------------------------------------------------

    print(
        "\n[6] VALIDATING MAIN PIPELINE INTEGRATION"
    )

    integrated_root = Path(
        "storage/output"
    )

    integrated_markdown = list(
        integrated_root.rglob("*.md")
    )

    integrated_metadata = list(
        integrated_root.rglob("*.json")
    )

    print(
        "Integrated Markdown:",
        len(integrated_markdown),
    )

    print(
        "Integrated metadata:",
        len(integrated_metadata),
    )

    # ------------------------------------------------------------
    # FIND MATCHING SOURCE DOCUMENT
    # ------------------------------------------------------------

    source_document = (
        engine.document_inventory
        and next(
            iter(
                engine.document_inventory.values()
            )
        )
    )

    assert source_document, (
        "No source document available"
    )

    source_url = source_document[
        "url"
    ]

    print(
        "\nSource document:",
        source_url,
    )

    # ------------------------------------------------------------
    # FIND INTEGRATED METADATA BY SOURCE URL
    # ------------------------------------------------------------

    matching_metadata = None

    for metadata_file in integrated_metadata:

        try:

            metadata = json.loads(
                metadata_file.read_text(
                    encoding="utf-8"
                )
            )

        except Exception:

            continue

        if metadata.get(
            "source_url"
        ) == source_url:

            matching_metadata = (
                metadata_file,
                metadata,
            )

            break

    assert matching_metadata is not None, (
        "Processed document was not "
        "integrated into storage/output"
    )

    integrated_metadata_file, metadata = (
        matching_metadata
    )

    integrated_markdown_file = Path(
        metadata[
            "storage_path"
        ]
    )

    assert integrated_markdown_file.exists(), (
        "Integrated Markdown path from "
        "metadata does not exist"
    )

    assert integrated_markdown_file.is_file(), (
        "Integrated Markdown path is not a file"
    )

    integrated_content = (
        integrated_markdown_file.read_text(
            encoding="utf-8"
        )
    )

    assert integrated_content.strip(), (
        "Integrated Markdown is empty"
    )

    print(
        "\nIntegrated Markdown:",
        integrated_markdown_file,
    )

    print(
        "Integrated Metadata:",
        integrated_metadata_file,
    )

    print(
        "Integrated content:",
        len(integrated_content),
        "characters",
    )

    # ------------------------------------------------------------
    # FINAL RELATIONSHIP VALIDATION
    # ------------------------------------------------------------

    print(
        "\n[7] VALIDATING DOCUMENT RELATIONSHIP"
    )

    assert metadata.get(
        "source_url"
    ) == source_url, (
        "Integrated metadata lost source URL"
    )

    assert metadata.get(
        "document_type"
    ) == "pdf", (
        "Integrated metadata has incorrect "
        "document type"
    )

    print(
        "Source URL preserved: PASS"
    )

    print(
        "Document type preserved: PASS"
    )

    print(
        "Processed content integrated: PASS"
    )

    # ------------------------------------------------------------
    # FINAL RESULT
    # ------------------------------------------------------------

    print(
        "\n" + "=" * 100
    )

    print(
        "PHASE 6 FINAL INTEGRATION RESULTS"
    )

    print(
        "=" * 100
    )

    print(
        "Pages crawled       :",
        engine.pages_crawled,
    )

    print(
        "Documents discovered:",
        engine.documents_discovered,
    )

    print(
        "Raw PDFs            :",
        len(raw_pdfs),
    )

    print(
        "Processed Markdown  :",
        len(markdown_files),
    )

    print(
        "Integrated documents:",
        1,
    )

    print(
        "\nDOCUMENT FLOW"
    )

    print(
        "DISCOVER"
        " -> DOWNLOAD"
        " -> STORE"
        " -> EXTRACT"
        " -> INTEGRATE"
    )

    print(
        "\nPHASE 6.8 REAL INTEGRATION TEST: PASS"
    )

    print(
        "\nPHASE 6 — EXTERNAL CONTENT PROCESSING: COMPLETE"
    )


if __name__ == "__main__":
    asyncio.run(main())
