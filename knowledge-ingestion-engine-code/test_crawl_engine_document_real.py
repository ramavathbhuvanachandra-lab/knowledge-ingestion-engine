import asyncio
from pathlib import Path
import shutil
import json

from crawler.crawl_engine import CrawlEngine
from processors.document_downloader import DocumentDownloader
from processors.pdf_processor import PDFProcessor


TEST_URLS = [
    "https://www.iitj.ac.in/",
    "https://home.iitd.ac.in/",
]

TEST_STORAGE = Path(
    "storage/test_crawl_engine_documents"
)

RAW_STORAGE = (
    TEST_STORAGE / "raw"
)

PROCESSED_STORAGE = (
    TEST_STORAGE / "processed"
)


async def test_document_integration(
    start_url: str,
):
    print("\n" + "=" * 100)
    print(
        "REAL CRAWL ENGINE DOCUMENT INTEGRATION"
    )
    print("=" * 100)

    print(
        "START URL:",
        start_url,
    )

    # ------------------------------------------------------------
    # CLEAN TEST STORAGE
    # ------------------------------------------------------------

    if TEST_STORAGE.exists():
        shutil.rmtree(
            TEST_STORAGE
        )

    RAW_STORAGE.mkdir(
        parents=True,
        exist_ok=True,
    )

    PROCESSED_STORAGE.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ------------------------------------------------------------
    # CREATE ENGINE
    # ------------------------------------------------------------

    engine = CrawlEngine()

    # Use isolated test storage.
    engine.document_downloader = (
        DocumentDownloader(
            base_path=RAW_STORAGE
        )
    )

    engine.pdf_processor = (
        PDFProcessor(
            output_path=PROCESSED_STORAGE
        )
    )

    # ------------------------------------------------------------
    # RUN CRAWL
    # ------------------------------------------------------------

    await engine.start(
        start_url,
        max_pages=50,
    )

    # ------------------------------------------------------------
    # ENGINE RESULTS
    # ------------------------------------------------------------

    print("\nENGINE RESULTS")
    print("-" * 100)

    print(
        "Pages crawled       :",
        engine.pages_crawled,
    )

    print(
        "Documents discovered:",
        engine.documents_discovered,
    )

    print(
        "Resources discovered:",
        engine.resources_discovered,
    )

    print(
        "Ignored plans       :",
        engine.ignored_plans,
    )

    print(
        "Failed pages        :",
        engine.failed_pages,
    )

    print(
        "Tracked URLs        :",
        engine.depth_tracker.size(),
    )

    # ------------------------------------------------------------
    # BASIC ENGINE VALIDATION
    # ------------------------------------------------------------

    assert engine.pages_crawled >= 1, (
        f"No pages crawled: {start_url}"
    )

    assert engine.failed_pages == 0, (
        f"Engine reported failed pages: "
        f"{engine.failed_pages}"
    )

    # ------------------------------------------------------------
    # DOCUMENT INVENTORY
    # ------------------------------------------------------------

    print(
        "\nDOCUMENT INVENTORY"
    )

    print("-" * 100)

    for index, document in enumerate(
        engine.document_inventory.values(),
        start=1,
    ):
        print(
            f"\nDocument #{index}"
        )

        print(
            "URL       :",
            document["url"],
        )

        print(
            "Type      :",
            document["url_type"],
        )

        print(
            "Depth     :",
            document["depth"],
        )

        print(
            "Sources   :",
            len(
                document[
                    "discovered_from"
                ]
            ),
        )

    # ------------------------------------------------------------
    # IF NO DOCUMENT WAS DISCOVERED
    # ------------------------------------------------------------

    if engine.documents_discovered == 0:

        print(
            "\nWARNING:"
        )

        print(
            "No document was discovered "
            "during this crawl."
        )

        print(
            "This website did not expose a "
            "document within the current "
            "crawl/test limit."
        )

        return

    # ------------------------------------------------------------
    # FIND TEST OUTPUT
    # ------------------------------------------------------------

    pdf_files = list(
        RAW_STORAGE.rglob("*.pdf")
    )

    raw_metadata_files = list(
        RAW_STORAGE.rglob("*.json")
    )

    markdown_files = list(
        PROCESSED_STORAGE.rglob("*.md")
    )

    processed_metadata_files = list(
        PROCESSED_STORAGE.rglob("*.json")
    )

    print(
        "\nSTORAGE RESULTS"
    )

    print("-" * 100)

    print(
        "Raw PDFs             :",
        len(pdf_files),
    )

    print(
        "Raw metadata         :",
        len(raw_metadata_files),
    )

    print(
        "Processed Markdown   :",
        len(markdown_files),
    )

    print(
        "Processed metadata   :",
        len(processed_metadata_files),
    )

    # ------------------------------------------------------------
    # DOCUMENT COUNT
    # ------------------------------------------------------------

    assert len(pdf_files) >= 1, (
        "Documents were discovered "
        "but no PDF was downloaded"
    )

    assert len(raw_metadata_files) >= 1, (
        "PDF downloaded but raw metadata "
        "was not created"
    )

    assert len(markdown_files) >= 1, (
        "PDF downloaded but Markdown "
        "was not created"
    )

    assert len(
        processed_metadata_files
    ) >= 1, (
        "Processed Markdown exists but "
        "processed metadata was not created"
    )

    # ------------------------------------------------------------
    # VALIDATE EACH PDF
    # ------------------------------------------------------------

    for pdf_file in pdf_files:

        print(
            "\nPDF:",
            pdf_file,
        )

        assert pdf_file.is_file(), (
            f"PDF is not a file: {pdf_file}"
        )

        size = pdf_file.stat().st_size

        assert size > 0, (
            f"PDF is empty: {pdf_file}"
        )

        header = (
            pdf_file.read_bytes()[:5]
        )

        assert header == b"%PDF-", (
            f"Invalid PDF header: "
            f"{pdf_file}"
        )

        # --------------------------------------------------------
        # RAW METADATA
        # --------------------------------------------------------

        raw_metadata = (
            pdf_file.with_suffix(".json")
        )

        assert raw_metadata.exists(), (
            f"Missing raw metadata: "
            f"{raw_metadata}"
        )

        data = json.loads(
            raw_metadata.read_text(
                encoding="utf-8"
            )
        )

        assert data["source_url"], (
            "Raw metadata missing source_url"
        )

        assert data["document_type"] == "pdf"

        assert data["success"] is True

        assert data["size_bytes"] == size

        # --------------------------------------------------------
        # PROCESSED FILE
        # --------------------------------------------------------

        domain = pdf_file.parent.name

        processed_dir = (
            PROCESSED_STORAGE / domain
        )

        processed_markdown = (
            processed_dir
            / f"{pdf_file.stem}.md"
        )

        processed_metadata = (
            processed_dir
            / f"{pdf_file.stem}.json"
        )

        assert processed_markdown.exists(), (
            f"Missing processed Markdown: "
            f"{processed_markdown}"
        )

        assert processed_metadata.exists(), (
            f"Missing processed metadata: "
            f"{processed_metadata}"
        )

        processed_data = json.loads(
            processed_metadata.read_text(
                encoding="utf-8"
            )
        )

        assert (
            processed_data["document_type"]
            == "pdf"
        )

        assert (
            processed_data[
                "extraction_success"
            ]
            is True
        )

        assert processed_data["pages"] >= 1

        # --------------------------------------------------------
        # SOURCE URL
        # --------------------------------------------------------

        assert (
            processed_data["source_url"]
            == data["source_url"]
        ), (
            "Processed metadata source_url "
            "does not match raw metadata"
        )

        print(
            "Raw PDF       : PASS"
        )

        print(
            "Raw metadata  : PASS"
        )

        print(
            "Markdown      : PASS"
        )

        print(
            "Processed meta: PASS"
        )

    # ------------------------------------------------------------
    # SUCCESS
    # ------------------------------------------------------------

    print(
        "\nDOCUMENT PIPELINE:"
        " DOWNLOAD → PROCESS → STORE"
    )

    print(
        "PASS:",
        start_url,
    )


async def main():

    # ------------------------------------------------------------
    # CLEAN ONCE BEFORE TEST SUITE
    # ------------------------------------------------------------

    if TEST_STORAGE.exists():
        shutil.rmtree(
            TEST_STORAGE
        )

    passed = 0

    # ------------------------------------------------------------
    # TEST WEBSITES
    # ------------------------------------------------------------

    for url in TEST_URLS:

        try:

            await test_document_integration(
                url
            )

            passed += 1

        except Exception as error:

            print(
                "\nFAILED:",
                url,
            )

            print(
                f"{type(error).__name__}: "
                f"{error}"
            )

            raise

    # ------------------------------------------------------------
    # FINAL RESULT
    # ------------------------------------------------------------

    print(
        "\n" + "=" * 100
    )

    print(
        "REAL CRAWL ENGINE DOCUMENT "
        "INTEGRATION RESULTS"
    )

    print(
        "=" * 100
    )

    print(
        "Sites passed:",
        passed,
        "/",
        len(TEST_URLS),
    )

    assert passed == len(
        TEST_URLS
    )

    print(
        "\nPHASE 6.6 CRAWL ENGINE "
        "DOCUMENT INTEGRATION: PASS"
    )


if __name__ == "__main__":
    asyncio.run(main())