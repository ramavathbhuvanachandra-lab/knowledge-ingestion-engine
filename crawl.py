"""
Engineering College Website Crawler

STEP 1 ONLY
-----------

Usage:

    python crawl.py https://www.iitj.ac.in

This command:
    - crawls the complete website
    - saves the crawled knowledge/source data
    - writes the crawl report

It does NOT:
    - classify A/B/C/REVIEW/D
    - build RAG documents
    - filter RAG content
    - create embeddings
    - build vectors
"""

from __future__ import annotations

import argparse
import asyncio

from crawler.crawl_engine import CrawlEngine


DEFAULT_REPORT_ROOT = (
    "storage/crawl_reports"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Crawl an engineering-college website "
            "and create the source knowledge layer."
        )
    )

    parser.add_argument(
        "start_url",
        help=(
            "Website URL to crawl, for example: "
            "https://www.iitj.ac.in"
        ),
    )

    parser.add_argument(
        "--report-root",
        default=DEFAULT_REPORT_ROOT,
        help=(
            "Directory for crawl reports."
        ),
    )

    return parser


async def run_crawl(
    start_url: str,
    report_root: str,
) -> dict:
    print()
    print("=" * 100)
    print(
        "STEP 1 — ENGINEERING COLLEGE WEBSITE CRAWL"
    )
    print("=" * 100)

    print(
        "Start URL:",
        start_url,
    )

    engine = CrawlEngine(
        report_root=report_root
    )

    report = await engine.start(
        start_url=start_url,
        max_pages=None,
    )

    stats = report[
        "statistics"
    ]

    print()
    print("=" * 100)
    print(
        "CRAWL COMPLETE"
    )
    print("=" * 100)

    print(
        "Mode                 :",
        report["crawl"]["mode"],
    )

    print(
        "Start URL            :",
        report["crawl"]["start_url"],
    )

    print(
        "Unique URLs          :",
        stats["unique_urls_discovered"],
    )

    print(
        "Duplicate URLs       :",
        stats["duplicate_urls_skipped"],
    )

    print(
        "Pages Attempted      :",
        stats["pages_attempted"],
    )

    print(
        "Pages Crawled        :",
        stats["pages_crawled"],
    )

    print(
        "Failed Pages         :",
        stats["failed_pages"],
    )

    print(
        "Documents Discovered :",
        stats["documents_discovered"],
    )

    print(
        "Documents Processed  :",
        stats["documents_processed"],
    )

    print(
        "Failed Documents     :",
        stats["failed_documents"],
    )

    print(
        "Resources            :",
        stats["resources_discovered"],
    )

    print(
        "Ignored Plans        :",
        stats["ignored_plans"],
    )

    print(
        "Tracked URLs         :",
        stats["tracked_urls"],
    )

    print(
        "Remaining Queue      :",
        stats["remaining_queue"],
    )

    print(
        "Queue Exhausted      :",
        report["queue_exhausted"],
    )

    print()
    print(
        "Crawl report:"
    )

    print(
        f"{report_root}/"
    )

    print()
    print("=" * 100)

    return report


def main() -> None:
    parser = build_parser()

    args = parser.parse_args()

    asyncio.run(
        run_crawl(
            start_url=args.start_url,
            report_root=args.report_root,
        )
    )


if __name__ == "__main__":
    main()