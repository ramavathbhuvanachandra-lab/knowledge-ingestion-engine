from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from crawler.crawler import crawl_page
from crawler.crawl_policy import CrawlPolicy
from crawler.crawl_queue import CrawlQueue
from crawler.depth_tracker import DepthTracker
from crawler.url_classifier import classify_url

from models.crawl_plan import (
    CrawlAction,
)
from models.url import (
    URLInfo,
    URLType,
)

from pipeline.navigation_pipeline import (
    NavigationPipeline,
)

from processors.page_processor import (
    PageProcessor,
)

from processors.document_downloader import (
    DocumentDownloader,
)

from processors.pdf_processor import (
    PDFProcessor,
)

from processors.xlsx_processor import (
    XLSXProcessor,
)

from processors.document_integrator import (
    DocumentIntegrator,
)

from url_discovery import (
    URLDiscovery,
)


class CrawlEngine:
    """
    Production-oriented website crawl execution engine.

    Architecture:

        Start URL
            ↓
        URL Classification
            ↓
        Crawl Policy
            ↓
        Crawl Plan
            ↓
        Crawl Queue
            ↓
        Execute
            ↓
        ┌───────────────────────┐
        │                       │
        │ WEBPAGE               │ DOCUMENT
        │                       │
        ↓                       ↓
    crawl_page()          downloader
        ↓                 processor
    PageProcessor               ↓
        ↓                 integrator
    discover links
        │
        └──────────────→ queue

    Responsibilities:

    - Execute crawl plans.
    - Keep webpage/document/resource execution separate.
    - Prevent duplicate URL execution.
    - Continue crawling after individual failures.
    - Support limited test crawls.
    - Support full crawls with max_pages=None.
    - Track crawl-wide URL state.
    - Track document inventory.
    - Persist a crawl report.
    - Preserve the existing crawler architecture.

    This class does NOT:

    - clean knowledge
    - organize knowledge
    - build RAG documents
    - generate embeddings
    - perform retrieval
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        report_root: str | Path = (
            "storage/crawl_reports"
        ),
    ):

        # ----------------------------------------------------
        # CORE CRAWL COMPONENTS
        # ----------------------------------------------------

        self.queue = CrawlQueue()

        self.depth_tracker = (
            DepthTracker()
        )

        self.policy = CrawlPolicy()

        self.discovery = URLDiscovery()

        self.processor = PageProcessor()

        # ----------------------------------------------------
        # DOCUMENT PROCESSORS
        # ----------------------------------------------------

        self.document_downloader = (
            DocumentDownloader()
        )

        self.pdf_processor = (
            PDFProcessor()
        )

        self.xlsx_processor = (
            XLSXProcessor()
        )

        self.document_integrator = (
            DocumentIntegrator()
        )

        # ----------------------------------------------------
        # REPORTING
        # ----------------------------------------------------

        self.report_root = Path(
            report_root
        )

        # ----------------------------------------------------
        # CRAWL-WIDE URL INVENTORY
        #
        # One entry per unique normalized URL.
        # ----------------------------------------------------

        self.url_inventory = {}

        # ----------------------------------------------------
        # DOCUMENT INVENTORY
        #
        # One entry per unique document URL.
        # ----------------------------------------------------

        self.document_inventory = {}

        # ----------------------------------------------------
        # RESOURCE INVENTORY
        # ----------------------------------------------------

        self.resource_inventory = {}

        # ----------------------------------------------------
        # STATISTICS
        # ----------------------------------------------------

        self.pages_attempted = 0
        self.pages_crawled = 0
        self.failed_pages = 0
        self.pages_skipped_limit = 0

        self.documents_discovered = 0
        self.documents_processed = 0
        self.failed_documents = 0

        self.resources_discovered = 0
        self.ignored_plans = 0

        self.unique_urls_discovered = 0
        self.queue_enqueued = 0
        self.duplicate_urls_skipped = 0

        # ----------------------------------------------------
        # CURRENT CRAWL
        # ----------------------------------------------------

        self.start_url = None
        self.base_domain = None

        self.max_pages = None
        self.crawl_mode = "UNKNOWN"

    # ========================================================
    # RESET STATE
    # ========================================================

    def _reset_state(self) -> None:

        self.queue = CrawlQueue()

        self.depth_tracker = (
            DepthTracker()
        )

        self.url_inventory = {}
        self.document_inventory = {}
        self.resource_inventory = {}

        self.pages_attempted = 0
        self.pages_crawled = 0
        self.failed_pages = 0
        self.pages_skipped_limit = 0

        self.documents_discovered = 0
        self.documents_processed = 0
        self.failed_documents = 0

        self.resources_discovered = 0
        self.ignored_plans = 0

        self.unique_urls_discovered = 0
        self.queue_enqueued = 0
        self.duplicate_urls_skipped = 0

    # ========================================================
    # URL NORMALIZATION
    # ========================================================

    def _normalize_tracking_key(
        self,
        url: str,
    ) -> str:

        return (
            url or ""
        ).strip()

    # ========================================================
    # INVENTORY CREATION
    # ========================================================

    def _register_url(
        self,
        plan,
        source_url: str | None = None,
    ) -> bool:
        """
        Register a URL globally.

        Returns:

            True  = new URL
            False = already known URL

        This is the execution-level deduplication layer.

        It is deliberately independent of college/site-specific
        rules.
        """

        key = (
            self._normalize_tracking_key(
                plan.url
            )
        )

        if not key:

            return False

        existing = (
            self.url_inventory.get(
                key
            )
        )

        if existing is not None:

            discovered_from = (
                existing.get(
                    "discovered_from",
                    [],
                )
            )

            if source_url:

                if (
                    source_url
                    not in discovered_from
                ):

                    discovered_from.append(
                        source_url
                    )

            existing[
                "discovered_from"
            ] = discovered_from

            self.duplicate_urls_skipped += 1

            return False

        self.url_inventory[
            key
        ] = {
            "url": plan.url,
            "normalized_url": (
                plan.url
            ),
            "url_type": (
                plan.url_type.value
            ),
            "action": (
                plan.action.value
            ),
            "priority": (
                plan.priority.name
            ),
            "depth": plan.depth,
            "discovered_from": (
                [source_url]
                if source_url
                else []
            ),
            "status": "discovered",
            "error": None,
            "output": None,
        }

        self.unique_urls_discovered += 1

        return True

    # ========================================================
    # UPDATE URL STATUS
    # ========================================================

    def _set_url_status(
        self,
        url: str,
        status: str,
        *,
        error: str | None = None,
        output: str | None = None,
    ) -> None:

        key = (
            self._normalize_tracking_key(
                url
            )
        )

        record = (
            self.url_inventory.get(
                key
            )
        )

        if record is None:
            return

        record[
            "status"
        ] = status

        record[
            "error"
        ] = error

        if output is not None:

            record[
                "output"
            ] = output

    # ========================================================
    # NAVIGATION DISCOVERY
    # ========================================================

    def _discover_navigation(
        self,
        html: str,
        source_url: str,
    ) -> list[URLInfo]:
        """
        Run navigation extraction followed by URL discovery.
        """

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        navigation_pipeline = (
            NavigationPipeline(
                soup=soup
            )
        )

        navigation_result = (
            navigation_pipeline.run()
        )

        candidates = (
            navigation_result[
                "candidates"
            ]
        )

        return self.discovery.discover(
            candidates=candidates,
            source_url=source_url,
        )

    # ========================================================
    # PLAN CREATION + ENQUEUE
    # ========================================================

    def _create_and_enqueue_plans(
        self,
        discovered_urls: list[URLInfo],
        source_url: str,
    ) -> None:
        """
        Convert discovered URLs into crawl plans.

        Deduplication happens before enqueueing so a URL is not
        executed repeatedly simply because several pages link
        to it.
        """

        for url_info in discovered_urls:

            normalized_url = (
                url_info.normalized_url
            )

            # ------------------------------------------------
            # DEPTH
            # ------------------------------------------------

            if (
                normalized_url
                == source_url
            ):

                depth = (
                    self.depth_tracker.register_root(
                        normalized_url
                    )
                )

            else:

                depth = (
                    self.depth_tracker.register_child(
                        normalized_url,
                        source_url,
                    )
                )

            # ------------------------------------------------
            # URL INFO WITH DEPTH
            # ------------------------------------------------

            planned_url_info = URLInfo(
                raw_url=url_info.raw_url,
                normalized_url=(
                    url_info.normalized_url
                ),
                url_type=url_info.url_type,
                discovered_from=(
                    url_info.discovered_from
                ),
                depth=depth,
            )

            # ------------------------------------------------
            # CREATE PLAN
            # ------------------------------------------------

            plan = self.policy.create_plan(
                planned_url_info,
                depth=depth,
            )

            # ------------------------------------------------
            # GLOBAL URL INVENTORY
            # ------------------------------------------------

            is_new = (
                self._register_url(
                    plan=plan,
                    source_url=source_url,
                )
            )

            if not is_new:

                continue

            # ------------------------------------------------
            # IGNORE
            # ------------------------------------------------

            if (
                plan.action
                == CrawlAction.IGNORE
            ):

                self.ignored_plans += 1

                self._set_url_status(
                    plan.url,
                    "ignored",
                )

                continue

            # ------------------------------------------------
            # DOCUMENT INVENTORY
            # ------------------------------------------------

            if (
                plan.action
                == CrawlAction.DOCUMENT
            ):

                document_url = (
                    plan.url
                )

                self.document_inventory[
                    document_url
                ] = {
                    "url": document_url,
                    "url_type": (
                        plan.url_type.value
                    ),
                    "depth": plan.depth,
                    "discovered_from": [
                        plan.discovered_from
                    ],
                    "status": "discovered",
                    "output": None,
                    "error": None,
                }

                self.documents_discovered = (
                    len(
                        self.document_inventory
                    )
                )

            # ------------------------------------------------
            # RESOURCE INVENTORY
            # ------------------------------------------------

            elif (
                plan.action
                == CrawlAction.RESOURCE
            ):

                self.resource_inventory[
                    plan.url
                ] = {
                    "url": plan.url,
                    "url_type": (
                        plan.url_type.value
                    ),
                    "depth": plan.depth,
                    "discovered_from": [
                        plan.discovered_from
                    ],
                    "status": "discovered",
                }

                self.resources_discovered = (
                    len(
                        self.resource_inventory
                    )
                )

            # ------------------------------------------------
            # ENQUEUE
            # ------------------------------------------------

            self.queue.enqueue(
                plan
            )

            self.queue_enqueued += 1

            self._set_url_status(
                plan.url,
                "queued",
            )

    # ========================================================
    # PROCESS ONE WEBPAGE
    # ========================================================

    async def _process_page(
        self,
        plan,
    ) -> None:
        """
        Crawl and process one webpage.

        A page failure is raised to the crawl loop, where it
        is recorded and the next queued item continues.
        """

        print(
            "\n======================================"
        )

        print(
            f"Crawling Webpage Attempt "
            f"#{self.pages_attempted}"
        )

        print(
            f"URL      : {plan.url}"
        )

        print(
            f"Depth    : {plan.depth}"
        )

        print(
            f"Priority : {plan.priority.name}"
        )

        print(
            "======================================"
        )

        self._set_url_status(
            plan.url,
            "processing",
        )

        page = await crawl_page(
            plan.url
        )

        if not page.success:

            raise RuntimeError(
                f"Page crawl failed: "
                f"{plan.url}"
            )

        if not page.html:

            raise RuntimeError(
                f"Empty HTML returned: "
                f"{plan.url}"
            )

        # ----------------------------------------------------
        # PAGE PROCESSING
        # ----------------------------------------------------

        output = self.processor.process(
            page
        )

        # ----------------------------------------------------
        # DISCOVER NEXT URLs
        # ----------------------------------------------------

        discovered_urls = (
            self._discover_navigation(
                html=page.html,
                source_url=page.url,
            )
        )

        print(
            "Title :",
            page.title,
        )

        print(
            "URLs Discovered :",
            len(discovered_urls),
        )

        self._create_and_enqueue_plans(
            discovered_urls=(
                discovered_urls
            ),
            source_url=page.url,
        )

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        output_path = None

        if output is not None:

            if isinstance(
                output,
                (str, Path),
            ):
                output_path = str(
                    output
                )

        self._set_url_status(
            plan.url,
            "success",
            output=output_path,
        )

    # ========================================================
    # PROCESS ONE DOCUMENT
    # ========================================================

    async def _process_document(
        self,
        plan,
    ) -> None:
        """
        Download and process one discovered document.
        """

        print(
            "\n======================================"
        )

        print(
            "Processing Document"
        )

        print(
            "URL      :",
            plan.url,
        )

        print(
            "Type     :",
            plan.url_type.value,
        )

        print(
            "Depth    :",
            plan.depth,
        )

        print(
            "Priority :",
            plan.priority.name,
        )

        print(
            "======================================"
        )

        self._set_url_status(
            plan.url,
            "processing",
        )

        # ----------------------------------------------------
        # DOWNLOAD
        # ----------------------------------------------------

        document_path = (
            self.document_downloader.download(
                url=plan.url,
            )
        )

        print(
            "Downloaded:",
            document_path,
        )

        # ----------------------------------------------------
        # PROCESS TYPE
        # ----------------------------------------------------

        if (
            plan.url_type
            == URLType.PDF
        ):

            print(
                "Processor  : PDFProcessor"
            )

            markdown_path = (
                self.pdf_processor.process(
                    document_path,
                    source_url=plan.url,
                )
            )

        elif (
            plan.url_type
            == URLType.XLSX
        ):

            print(
                "Processor  : XLSXProcessor"
            )

            markdown_path = (
                self.xlsx_processor.process(
                    document_path,
                    source_url=plan.url,
                )
            )

        else:

            raise ValueError(
                "Unsupported document type: "
                f"{plan.url_type.value}"
            )

        print(
            "Processed Markdown:",
            markdown_path,
        )

        metadata_path = (
            markdown_path.with_suffix(
                ".json"
            )
        )

        domain = urlparse(
            plan.url
        ).netloc

        category = (
            plan.url_type.value
        )

        # ----------------------------------------------------
        # INTEGRATE
        # ----------------------------------------------------

        (
            integrated_markdown,
            integrated_metadata,
        ) = (
            self.document_integrator.integrate(
                markdown_path=(
                    markdown_path
                ),
                metadata_path=(
                    metadata_path
                ),
                domain=domain,
                category=category,
            )
        )

        print(
            "Integrated Markdown:",
            integrated_markdown,
        )

        print(
            "Integrated Metadata:",
            integrated_metadata,
        )

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        self._set_url_status(
            plan.url,
            "success",
            output=str(
                integrated_markdown
            ),
        )

        document_record = (
            self.document_inventory.get(
                plan.url
            )
        )

        if document_record is not None:

            document_record[
                "status"
            ] = "success"

            document_record[
                "output"
            ] = str(
                integrated_markdown
            )

            document_record[
                "error"
            ] = None

    # ========================================================
    # START CRAWL
    # ========================================================

    async def start(
        self,
        start_url: str,
        max_pages: int | None = 50,
    ) -> dict:
        """
        Start the crawl.

        max_pages:

            integer
                TEST/LIMITED mode.

            None
                FULL mode: process webpages until the queue is
                exhausted.

        Important:

        max_pages counts WEBPAGE ATTEMPTS, not only successful
        webpages.

        DOCUMENT plans are not limited by max_pages.
        """

        self._reset_state()

        normalized_start_url = (
            start_url.strip()
        )

        if not normalized_start_url:

            raise ValueError(
                "Start URL cannot be empty."
            )

        # ----------------------------------------------------
        # VALIDATE PAGE LIMIT
        # ----------------------------------------------------

        if (
            max_pages is not None
            and max_pages < 0
        ):

            raise ValueError(
                "max_pages must be >= 0 or None."
            )

        self.start_url = (
            normalized_start_url
        )

        self.max_pages = (
            max_pages
        )

        self.crawl_mode = (
            "FULL"
            if max_pages is None
            else "LIMITED"
        )

        # ----------------------------------------------------
        # ROOT DOMAIN
        # ----------------------------------------------------

        base_domain = (
            urlparse(
                normalized_start_url
            ).netloc
        )

        if not base_domain:

            raise ValueError(
                f"Invalid start URL: "
                f"{normalized_start_url}"
            )

        self.base_domain = (
            base_domain
        )

        # ----------------------------------------------------
        # ROOT URL INFO
        # ----------------------------------------------------

        root_url_info = classify_url(
            normalized_start_url,
            normalized_start_url,
            base_domain,
            normalized_start_url,
        )

        root_info = URLInfo(
            raw_url=(
                normalized_start_url
            ),
            normalized_url=(
                normalized_start_url
            ),
            url_type=(
                root_url_info.url_type
            ),
            discovered_from=(
                normalized_start_url
            ),
            depth=0,
        )

        root_plan = (
            self.policy.create_plan(
                root_info,
                depth=0,
            )
        )

        # ----------------------------------------------------
        # REGISTER ROOT
        # ----------------------------------------------------

        root_is_new = (
            self._register_url(
                plan=root_plan,
                source_url=(
                    normalized_start_url
                ),
            )
        )

        if root_is_new:

            if (
                root_plan.action
                == CrawlAction.IGNORE
            ):

                self.ignored_plans += 1

                self._set_url_status(
                    normalized_start_url,
                    "ignored",
                )

            else:

                self.queue.enqueue(
                    root_plan
                )

                self.queue_enqueued += 1

                self._set_url_status(
                    normalized_start_url,
                    "queued",
                )

                if (
                    root_plan.action
                    == CrawlAction.DOCUMENT
                ):

                    self.document_inventory[
                        normalized_start_url
                    ] = {
                        "url": (
                            normalized_start_url
                        ),
                        "url_type": (
                            root_plan
                            .url_type
                            .value
                        ),
                        "depth": 0,
                        "discovered_from": [
                            normalized_start_url
                        ],
                        "status": "queued",
                        "output": None,
                        "error": None,
                    }

                    self.documents_discovered = (
                        len(
                            self.document_inventory
                        )
                    )

        # ----------------------------------------------------
        # CRAWL LOOP
        # ----------------------------------------------------

        while not self.queue.is_empty():

            plan = (
                self.queue.dequeue()
            )

            if plan is None:
                break

            # =================================================
            # WEBPAGE
            # =================================================

            if (
                plan.action
                == CrawlAction.CRAWL
            ):

                # -------------------------------------------------
                # WEBPAGE LIMIT
                # -------------------------------------------------

                if (
                    max_pages is not None
                    and self.pages_attempted
                    >= max_pages
                ):

                    self.pages_skipped_limit += 1

                    self._set_url_status(
                        plan.url,
                        "skipped_page_limit",
                    )

                    print(
                        "Skipping webpage due to "
                        "max_pages:",
                        plan.url,
                    )

                    continue

                # Count ATTEMPT before executing.
                self.pages_attempted += 1

                try:

                    await self._process_page(
                        plan
                    )

                    self.pages_crawled += 1

                except Exception as error:

                    self.failed_pages += 1

                    error_text = (
                        f"{type(error).__name__}: "
                        f"{error}"
                    )

                    self._set_url_status(
                        plan.url,
                        "failed",
                        error=error_text,
                    )

                    print(
                        "\nPAGE FAILED:",
                        plan.url,
                    )

                    print(
                        error_text
                    )

                    # IMPORTANT:
                    # Do NOT stop the crawl.
                    continue

            # =================================================
            # DOCUMENT
            # =================================================

            elif (
                plan.action
                == CrawlAction.DOCUMENT
            ):

                try:

                    await self._process_document(
                        plan
                    )

                    self.documents_processed += 1

                except Exception as error:

                    self.failed_documents += 1

                    error_text = (
                        f"{type(error).__name__}: "
                        f"{error}"
                    )

                    self._set_url_status(
                        plan.url,
                        "failed",
                        error=error_text,
                    )

                    document_record = (
                        self.document_inventory.get(
                            plan.url
                        )
                    )

                    if (
                        document_record
                        is not None
                    ):

                        document_record[
                            "status"
                        ] = "failed"

                        document_record[
                            "error"
                        ] = error_text

                    print(
                        "\nDOCUMENT FAILED:",
                        plan.url,
                    )

                    print(
                        error_text
                    )

                    # Continue to next queue item.
                    continue

            # =================================================
            # RESOURCE
            # =================================================

            elif (
                plan.action
                == CrawlAction.RESOURCE
            ):

                self._set_url_status(
                    plan.url,
                    "ignored_resource",
                )

                continue

            else:

                self._set_url_status(
                    plan.url,
                    "unknown_action",
                )

        # ----------------------------------------------------
        # FINAL SUMMARY
        # ----------------------------------------------------

        report = (
            self._build_report()
        )

        self._print_summary(
            report
        )

        self._write_report(
            report
        )

        return report

    # ========================================================
    # BUILD REPORT
    # ========================================================

    def _build_report(
        self,
    ) -> dict:

        status_counts = {}

        for record in (
            self.url_inventory.values()
        ):

            status = record.get(
                "status",
                "unknown",
            )

            status_counts[
                status
            ] = (
                status_counts.get(
                    status,
                    0,
                )
                + 1
            )

        report = {
            "crawl": {
                "start_url": self.start_url,
                "base_domain": self.base_domain,
                "mode": self.crawl_mode,
                "max_pages": self.max_pages,
            },

            "statistics": {
                "unique_urls_discovered": (
                    self.unique_urls_discovered
                ),
                "queue_enqueued": (
                    self.queue_enqueued
                ),
                "duplicate_urls_skipped": (
                    self.duplicate_urls_skipped
                ),
                "pages_attempted": (
                    self.pages_attempted
                ),
                "pages_crawled": (
                    self.pages_crawled
                ),
                "failed_pages": (
                    self.failed_pages
                ),
                "pages_skipped_limit": (
                    self.pages_skipped_limit
                ),
                "documents_discovered": (
                    self.documents_discovered
                ),
                "documents_processed": (
                    self.documents_processed
                ),
                "failed_documents": (
                    self.failed_documents
                ),
                "resources_discovered": (
                    self.resources_discovered
                ),
                "ignored_plans": (
                    self.ignored_plans
                ),
                "tracked_urls": (
                    self.depth_tracker.size()
                ),
                "remaining_queue": (
                    self.queue.size()
                ),
            },

            "status_counts": (
                status_counts
            ),

            "queue_exhausted": (
                self.queue.is_empty()
            ),

            "document_inventory": (
                list(
                    self.document_inventory.values()
                )
            ),

            "url_inventory": (
                list(
                    self.url_inventory.values()
                )
            ),
        }

        return report

    # ========================================================
    # PRINT SUMMARY
    # ========================================================

    def _print_summary(
        self,
        report: dict,
    ) -> None:

        stats = report[
            "statistics"
        ]

        print(
            "\n========== Crawl Finished =========="
        )

        print(
            "Mode                :",
            report["crawl"]["mode"],
        )

        print(
            "Start URL           :",
            report["crawl"]["start_url"],
        )

        print(
            "Base Domain         :",
            report["crawl"]["base_domain"],
        )

        print(
            "Unique URLs         :",
            stats[
                "unique_urls_discovered"
            ],
        )

        print(
            "Queue Enqueued      :",
            stats[
                "queue_enqueued"
            ],
        )

        print(
            "Duplicate URLs      :",
            stats[
                "duplicate_urls_skipped"
            ],
        )

        print(
            "Pages Attempted     :",
            stats[
                "pages_attempted"
            ],
        )

        print(
            "Pages Crawled       :",
            stats[
                "pages_crawled"
            ],
        )

        print(
            "Failed Pages        :",
            stats[
                "failed_pages"
            ],
        )

        print(
            "Skipped Page Limit  :",
            stats[
                "pages_skipped_limit"
            ],
        )

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

        print(
            "Resources           :",
            stats[
                "resources_discovered"
            ],
        )

        print(
            "Ignored Plans       :",
            stats[
                "ignored_plans"
            ],
        )

        print(
            "Tracked URLs        :",
            stats[
                "tracked_urls"
            ],
        )

        print(
            "Remaining Queue     :",
            stats[
                "remaining_queue"
            ],
        )

        print(
            "Queue Exhausted     :",
            report[
                "queue_exhausted"
            ],
        )

        print(
            "\n---------- URL STATUS COUNTS ----------"
        )

        for status, count in sorted(
            report[
                "status_counts"
            ].items()
        ):

            print(
                f"{status:24s}: {count}"
            )

    # ========================================================
    # WRITE REPORT
    # ========================================================

    def _write_report(
        self,
        report: dict,
    ) -> Path:

        domain = (
            report["crawl"][
                "base_domain"
            ]
            or "unknown"
        )

        safe_domain = (
            re.sub(
                r"[^a-zA-Z0-9._-]+",
                "_",
                domain,
            )
        )

        output_dir = (
            self.report_root
            / safe_domain
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path = (
            output_dir
            / "crawl_report.json"
        )

        output_path.write_text(
            json.dumps(
                report,
                indent=4,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        print(
            "Crawl Report        :",
            output_path,
        )

        return output_path