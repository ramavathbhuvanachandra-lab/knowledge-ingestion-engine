import asyncio
from pathlib import Path

from crawler.crawl_engine import CrawlEngine


URL = "https://gwpgc.ac.in/"
MAX_PAGES = 50


async def main():

    print()
    print("=" * 80)
    print("GWPGC — FULL KNOWLEDGE INGESTION TEST")
    print("=" * 80)

    print()
    print("Website  :", URL)
    print("Max pages:", MAX_PAGES)

    # --------------------------------------------------
    # CREATE ENGINE
    # --------------------------------------------------

    engine = CrawlEngine()

    # --------------------------------------------------
    # START REAL CRAWL
    # --------------------------------------------------

    await engine.start(
        start_url=URL,
        max_pages=MAX_PAGES,
    )

    # --------------------------------------------------
    # FINAL SUMMARY
    # --------------------------------------------------

    print()
    print("=" * 80)
    print("FINAL CRAWL SUMMARY")
    print("=" * 80)

    print(
        "Pages crawled        :",
        engine.pages_crawled,
    )

    print(
        "Failed pages         :",
        engine.failed_pages,
    )

    print(
        "Documents discovered :",
        engine.documents_discovered,
    )

    print(
        "Resources discovered :",
        engine.resources_discovered,
    )

    print(
        "Ignored plans        :",
        engine.ignored_plans,
    )

    print(
        "Tracked URLs         :",
        engine.depth_tracker.size(),
    )

    print(
        "Remaining queue      :",
        engine.queue.size(),
    )

    # --------------------------------------------------
    # STORAGE INSPECTION
    # --------------------------------------------------

    output_dir = Path(
        "storage/output/gwpgc.ac.in"
    )

    print()
    print("=" * 80)
    print("STORAGE")
    print("=" * 80)

    if not output_dir.exists():

        print(
            "Storage directory does not exist:"
        )

        print(
            output_dir
        )

        return

    markdown_files = list(
        output_dir.rglob("*.md")
    )

    json_files = list(
        output_dir.rglob("*.json")
    )

    pdf_files = list(
        output_dir.rglob("*.pdf")
    )

    print(
        "Markdown files :",
        len(markdown_files),
    )

    print(
        "JSON files     :",
        len(json_files),
    )

    print(
        "PDF files      :",
        len(pdf_files),
    )

    # --------------------------------------------------
    # STORAGE SIZE
    # --------------------------------------------------

    total_bytes = 0

    for path in output_dir.rglob("*"):

        if path.is_file():

            total_bytes += path.stat().st_size

    print(
        "Storage size   :",
        f"{total_bytes / 1024:.2f} KB",
    )

    # --------------------------------------------------
    # DIRECTORY BREAKDOWN
    # --------------------------------------------------

    print()
    print("=" * 80)
    print("DIRECTORY BREAKDOWN")
    print("=" * 80)

    directories = sorted(
        {
            path.parent
            for path in output_dir.rglob("*")
            if path.is_file()
        }
    )

    for directory in directories:

        md_count = len(
            list(
                directory.glob("*.md")
            )
        )

        json_count = len(
            list(
                directory.glob("*.json")
            )
        )

        pdf_count = len(
            list(
                directory.glob("*.pdf")
            )
        )

        print()
        print(
            directory
        )

        print(
            "  Markdown:",
            md_count,
        )

        print(
            "  JSON    :",
            json_count,
        )

        print(
            "  PDF     :",
            pdf_count,
        )

    # --------------------------------------------------
    # SAMPLE FILES
    # --------------------------------------------------

    print()
    print("=" * 80)
    print("SAMPLE MARKDOWN FILES")
    print("=" * 80)

    for path in sorted(
        markdown_files
    )[:20]:

        print(path)

    print()
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())