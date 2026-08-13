import asyncio

import crawler.crawl_engine as crawl_engine_module
from crawler.crawl_engine import CrawlEngine


async def main():

    original_document_process = (
        CrawlEngine._process_document
    )

    processed_documents = []

    async def tracking_document_process(
        self,
        plan,
    ):
        processed_documents.append(
            plan.url
        )

        return await original_document_process(
            self,
            plan,
        )

    CrawlEngine._process_document = (
        tracking_document_process
    )

    engine = CrawlEngine(
        report_root="storage/crawl_reports"
    )

    report = await engine.start(
        start_url=(
            "https://www.iitj.ac.in/"
            "office-of-director/en/"
            "office-of-director"
        ),
        max_pages=None,
    )

    stats = report["statistics"]

    print()
    print("=" * 100)
    print("DOCUMENT DEDUPLICATION TEST")
    print("=" * 100)

    print(
        "Documents Discovered:",
        stats[
            "documents_discovered"
        ],
    )

    print(
        "Documents Processed :",
        stats[
            "documents_processed"
        ],
    )

    print(
        "Failed Documents    :",
        stats[
            "failed_documents"
        ],
    )

    print()
    print(
        "DOCUMENT PROCESS CALLS"
    )

    for url in processed_documents:

        print(
            url
        )

    unique_processed = set(
        processed_documents
    )

    print()
    print(
        "Unique processed documents:",
        len(unique_processed),
    )

    print(
        "Total document process calls:",
        len(processed_documents),
    )

    print()
    print("=" * 100)

    assert (
        len(processed_documents)
        == len(unique_processed)
    ), (
        "A document was processed more than once."
    )

    assert (
        stats[
            "remaining_queue"
        ]
        == 0
    ), (
        "Queue should be exhausted."
    )

    print(
        "DOCUMENT DEDUPLICATION TEST: PASS"
    )
    print("=" * 100)


if __name__ == "__main__":
    asyncio.run(main())