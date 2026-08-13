import json
import re
from pathlib import Path

from crawler.crawl_engine import CrawlEngine
from crawler.url_classifier import classify_url
from models.url import URLInfo


# ============================================================
# REAL SOURCE FILES
# These are actual crawled IITJ pages that contain the SAME PDF
# ============================================================

SOURCE_DOCUMENTS = [
    Path(
        "storage/output/www.iitj.ac.in/research/"
        "office_of_research_development.md"
    ),
    Path(
        "storage/output/www.iitj.ac.in/others/"
        "indian_institute_of_technology_jodhpur__980be4db.md"
    ),
    Path(
        "storage/output/www.iitj.ac.in/others/"
        "indian_institute_of_technology_jodhpur.md"
    ),
]


TARGET_PDF = (
    "https://www.iitj.ac.in/"
    "PageImages/Gallery/08-2026/"
    "Notice-inviting-quotation-10082026003271.pdf"
)


# ============================================================
# HELPERS
# ============================================================

def load_source_url(
    markdown_path: Path,
) -> str:

    metadata_path = (
        markdown_path.with_suffix(".json")
    )

    assert metadata_path.exists(), (
        f"Metadata file missing: {metadata_path}"
    )

    data = json.loads(
        metadata_path.read_text(
            encoding="utf-8"
        )
    )

    source_url = data.get(
        "url"
        or data.get("source_url")
    )

    assert source_url, (
        f"No source URL found in: {metadata_path}"
    )

    return source_url


def verify_target_pdf_exists(
    markdown_path: Path,
) -> None:

    text = markdown_path.read_text(
        encoding="utf-8"
    )

    assert TARGET_PDF in text, (
        f"Target PDF not found in: "
        f"{markdown_path}"
    )


# ============================================================
# TEST
# ============================================================

def main():

    print()
    print("=" * 100)
    print("REAL DOCUMENT DEDUPLICATION TEST")
    print("=" * 100)

    # --------------------------------------------------------
    # VERIFY ALL THREE REAL SOURCE PAGES
    # --------------------------------------------------------

    for path in SOURCE_DOCUMENTS:

        assert path.exists(), (
            f"Source Markdown does not exist: {path}"
        )

        verify_target_pdf_exists(
            path
        )

        print()
        print(
            "SOURCE PAGE:",
            path,
        )

        print(
            "SOURCE URL :",
            load_source_url(path),
        )

        print(
            "TARGET PDF :",
            TARGET_PDF,
        )

        print(
            "TARGET FOUND: YES"
        )

    # --------------------------------------------------------
    # CREATE ENGINE
    # --------------------------------------------------------

    engine = CrawlEngine(
        report_root="storage/crawl_reports"
    )

    base_domain = "www.iitj.ac.in"

    # --------------------------------------------------------
    # FEED THE SAME REAL PDF THROUGH THE ENGINE
    # THREE SEPARATE TIMES, FROM THREE REAL SOURCE PAGES.
    # --------------------------------------------------------

    for path in SOURCE_DOCUMENTS:

        source_url = (
            load_source_url(path)
        )

        url_info_raw = classify_url(
            TARGET_PDF,
            TARGET_PDF,
            base_domain,
            source_url,
        )

        url_info = URLInfo(
            raw_url=TARGET_PDF,
            normalized_url=(
                url_info_raw.normalized_url
            ),
            url_type=(
                url_info_raw.url_type
            ),
            discovered_from=source_url,
            depth=1,
        )

        print()
        print(
            "=" * 100
        )

        print(
            "ADDING DOCUMENT DISCOVERY"
        )

        print(
            "Source:",
            source_url,
        )

        print(
            "Document:",
            TARGET_PDF,
        )

        engine._create_and_enqueue_plans(
            discovered_urls=[
                url_info
            ],
            source_url=source_url,
        )

    # --------------------------------------------------------
    # VERIFY INVENTORY
    # --------------------------------------------------------

    print()
    print("=" * 100)
    print("DEDUPLICATION RESULTS")
    print("=" * 100)

    print(
        "Unique URLs:",
        engine.unique_urls_discovered,
    )

    print(
        "Queue Enqueued:",
        engine.queue_enqueued,
    )

    print(
        "Duplicate URLs:",
        engine.duplicate_urls_skipped,
    )

    print(
        "Documents Discovered:",
        engine.documents_discovered,
    )

    print(
        "Document Inventory Entries:",
        len(
            engine.document_inventory
        ),
    )

    print(
        "Queue Size:",
        engine.queue.size(),
    )

    # --------------------------------------------------------
    # EXPECTED INVARIANTS
    # --------------------------------------------------------

    assert (
        engine.documents_discovered == 1
    ), (
        "The same PDF must exist as exactly one "
        "unique document."
    )

    assert (
        len(
            engine.document_inventory
        ) == 1
    ), (
        "Document inventory must contain exactly one "
        "entry for the repeated PDF."
    )

    assert (
        engine.queue_enqueued == 1
    ), (
        "The repeated PDF must be enqueued exactly once."
    )

    assert (
        engine.queue.size() == 1
    ), (
        "Exactly one document plan should remain in the queue."
    )

    assert (
        engine.duplicate_urls_skipped == 2
    ), (
        "The second and third discoveries must be "
        "recognized as duplicates."
    )

    # --------------------------------------------------------
    # SHOW INVENTORY
    # --------------------------------------------------------

    print()
    print(
        "DOCUMENT INVENTORY"
    )

    for url, record in (
        engine.document_inventory.items()
    ):

        print()
        print(
            "URL:",
            url,
        )

        print(
            "Type:",
            record["url_type"],
        )

        print(
            "Depth:",
            record["depth"],
        )

        print(
            "Discovered From:",
            record["discovered_from"],
        )

    print()
    print("=" * 100)
    print(
        "REAL DOCUMENT DEDUPLICATION TEST: PASS"
    )
    print("=" * 100)


if __name__ == "__main__":
    main()