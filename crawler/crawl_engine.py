from urllib.parse import urlparse

from bs4 import BeautifulSoup

from crawler.crawler import crawl_page
from crawler.crawl_policy import CrawlPolicy
from crawler.crawl_queue import CrawlQueue
from crawler.depth_tracker import DepthTracker
from crawler.url_classifier import classify_url

from models.crawl_plan import CrawlAction
from models.url import URLInfo

from pipeline.navigation_pipeline import NavigationPipeline

from processors.page_processor import PageProcessor
from processors.document_downloader import DocumentDownloader
from processors.pdf_processor import PDFProcessor
from processors.document_integrator import DocumentIntegrator

from url_discovery import URLDiscovery


class CrawlEngine:
    """
    Main crawl execution engine.

    Phase 5 architecture:

        Page
          ↓
        NavigationPipeline
          ↓
        URLDiscovery
          ↓
        DepthTracker
          ↓
        CrawlPolicy
          ↓
        CrawlPlan
          ↓
        CrawlQueue
          ↓
        Execute plan

    Phase 6 document flow:

        DOCUMENT plan
          ↓
        DocumentDownloader
          ↓
        PDFProcessor
          ↓
        Processed Markdown + Metadata
    """

    def __init__(self):
        self.queue = CrawlQueue()
        self.depth_tracker = DepthTracker()
        self.policy = CrawlPolicy()
        self.discovery = URLDiscovery()

        self.processor = PageProcessor()

        # ----------------------------------------------------------
        # PHASE 6
        # ----------------------------------------------------------

        self.document_downloader = DocumentDownloader()
        self.pdf_processor = PDFProcessor()
        self.document_integrator = DocumentIntegrator()

        # ----------------------------------------------------------
        # STATISTICS
        # ----------------------------------------------------------

        self.pages_crawled = 0
        self.documents_discovered = 0
        self.resources_discovered = 0
        self.ignored_plans = 0
        self.failed_pages = 0

        # ----------------------------------------------------------
        # DOCUMENT INVENTORY
        #
        # One inventory entry per unique document URL.
        # ----------------------------------------------------------

        self.document_inventory = {}

    # ------------------------------------------------------------------
    # NAVIGATION DISCOVERY
    # ------------------------------------------------------------------

    def _discover_navigation(
        self,
        html: str,
        source_url: str,
    ) -> list[URLInfo]:
        """
        Run the Phase 3 navigation pipeline followed by
        Phase 4 URL discovery.
        """

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        navigation_pipeline = NavigationPipeline(
            soup=soup
        )

        navigation_result = (
            navigation_pipeline.run()
        )

        candidates = navigation_result[
            "candidates"
        ]

        return self.discovery.discover(
            candidates=candidates,
            source_url=source_url,
        )

    # ------------------------------------------------------------------
    # PLAN DISCOVERY
    # ------------------------------------------------------------------

    def _create_and_enqueue_plans(
        self,
        discovered_urls: list[URLInfo],
        source_url: str,
    ) -> None:
        """
        Convert discovered URLs into CrawlPlans and enqueue them.

        Crawl depth is assigned here, not during URL discovery.
        """

        for url_info in discovered_urls:

            normalized_url = (
                url_info.normalized_url
            )

            # ----------------------------------------------------------
            # ROOT
            # ----------------------------------------------------------

            if normalized_url == source_url:

                depth = (
                    self.depth_tracker.register_root(
                        normalized_url
                    )
                )

            # ----------------------------------------------------------
            # CHILD
            # ----------------------------------------------------------

            else:

                depth = (
                    self.depth_tracker.register_child(
                        normalized_url,
                        source_url,
                    )
                )

            # ----------------------------------------------------------
            # CREATE URL INFO WITH DEPTH
            # ----------------------------------------------------------

            planned_url_info = URLInfo(
                raw_url=url_info.raw_url,
                normalized_url=url_info.normalized_url,
                url_type=url_info.url_type,
                discovered_from=url_info.discovered_from,
                depth=depth,
            )

            # ----------------------------------------------------------
            # CREATE PLAN
            # ----------------------------------------------------------

            plan = self.policy.create_plan(
                planned_url_info,
                depth=depth,
            )

            # ----------------------------------------------------------
            # IGNORE
            # ----------------------------------------------------------

            if plan.action == CrawlAction.IGNORE:

                self.ignored_plans += 1

                continue

            # ----------------------------------------------------------
            # DOCUMENT INVENTORY
            # ----------------------------------------------------------

            if plan.action == CrawlAction.DOCUMENT:

                document_url = plan.url

                if (
                    document_url
                    not in self.document_inventory
                ):

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
                    }

                else:

                    source_pages = (
                        self.document_inventory[
                            document_url
                        ][
                            "discovered_from"
                        ]
                    )

                    if (
                        plan.discovered_from
                        not in source_pages
                    ):

                        source_pages.append(
                            plan.discovered_from
                        )

                # Count unique documents.
                self.documents_discovered = (
                    len(
                        self.document_inventory
                    )
                )

            # ----------------------------------------------------------
            # RESOURCE
            # ----------------------------------------------------------

            elif plan.action == CrawlAction.RESOURCE:

                self.resources_discovered += 1

            # ----------------------------------------------------------
            # QUEUE
            # ----------------------------------------------------------

            self.queue.enqueue(plan)

    # ------------------------------------------------------------------
    # PROCESS ONE PAGE
    # ------------------------------------------------------------------

    async def _process_page(
        self,
        plan,
    ) -> None:
        """
        Crawl and process one WEBPAGE plan.
        """

        print(
            "\n======================================"
        )

        print(
            f"Crawling Page #{self.pages_crawled + 1}"
        )

        print(
            f"URL   : {plan.url}"
        )

        print(
            f"Depth : {plan.depth}"
        )

        print(
            f"Priority : {plan.priority.name}"
        )

        print(
            "======================================"
        )

        page = await crawl_page(
            plan.url
        )

        if not page.success:

            raise RuntimeError(
                f"Page crawl failed: {plan.url}"
            )

        if not page.html:

            raise RuntimeError(
                f"Empty HTML returned: {plan.url}"
            )

        # --------------------------------------------------------------
        # EXISTING PAGE PROCESSING
        # --------------------------------------------------------------

        self.processor.process(
            page
        )

        print(
            "Title :",
            page.title,
        )

        # --------------------------------------------------------------
        # DISCOVER NEXT URLs
        # --------------------------------------------------------------

        discovered_urls = (
            self._discover_navigation(
                html=page.html,
                source_url=page.url,
            )
        )

        print(
            "URLs Discovered :",
            len(discovered_urls),
        )

        self._create_and_enqueue_plans(
            discovered_urls=discovered_urls,
            source_url=page.url,
        )

    # ------------------------------------------------------------------
    # PROCESS ONE DOCUMENT
    # ------------------------------------------------------------------

    async def _process_document(
        self,
        plan,
    ) -> None:
        """
        Download and process one discovered PDF document.

        Phase 6 flow:

            DOCUMENT plan
                ↓
            DocumentDownloader
                ↓
            PDFProcessor
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

        # --------------------------------------------------------------
        # DOWNLOAD
        # --------------------------------------------------------------

        pdf_path = (
            self.document_downloader.download(
                url=plan.url,
            )
        )

        # --------------------------------------------------------------
        # PROCESS PDF
        # --------------------------------------------------------------

        result = (
            self.pdf_processor.process(
                pdf_path,
                source_url=plan.url,
            )
        )

        print(
            "Processed PDF:",
            pdf_path,
        )

        # --------------------------------------------------------------
        # PHASE 6.7 — INTEGRATE INTO MAIN STORAGE
        # --------------------------------------------------------------

        markdown_path = result

        metadata_path = (
            markdown_path.with_suffix(".json")
        )

        domain = urlparse(
            plan.url
        ).netloc

        integrated_markdown, integrated_metadata = (
            self.document_integrator.integrate(
                markdown_path=markdown_path,
                metadata_path=metadata_path,
                domain=domain,
                category="others",
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

    # ------------------------------------------------------------------
    # START CRAWL
    # ------------------------------------------------------------------

    async def start(
        self,
        start_url: str,
        max_pages: int | None = 50,
    ) -> None:
        """
        Start crawling from the supplied root URL.

        max_pages limits WEBPAGE crawling.

        Important:
        DOCUMENT plans already discovered in the queue
        are still processed after the page limit is reached.
        """

        normalized_start_url = (
            start_url.strip()
        )

        # --------------------------------------------------------------
        # ROOT URL
        # --------------------------------------------------------------

        base_domain = urlparse(
            normalized_start_url
        ).netloc

        root_url_info = classify_url(
            normalized_start_url,
            normalized_start_url,
            base_domain,
            normalized_start_url,
        )

        root_info = URLInfo(
            raw_url=normalized_start_url,
            normalized_url=normalized_start_url,
            url_type=root_url_info.url_type,
            discovered_from=normalized_start_url,
            depth=0,
        )

        root_plan = self.policy.create_plan(
            root_info,
            depth=0,
        )

        if (
            root_plan.action
            == CrawlAction.IGNORE
        ):

            self.ignored_plans += 1

        else:

            self.queue.enqueue(
                root_plan
            )

        # --------------------------------------------------------------
        # CRAWL LOOP
        # --------------------------------------------------------------

        while not self.queue.is_empty():

            plan = self.queue.dequeue()

            if plan is None:
                break

            # ----------------------------------------------------------
            # WEBPAGE
            # ----------------------------------------------------------

            if plan.action == CrawlAction.CRAWL:

                # ------------------------------------------------------
                # PAGE LIMIT
                #
                # Do NOT break the entire queue.
                #
                # Skip additional WEBPAGE plans only.
                # DOCUMENT plans must still be processed.
                # ------------------------------------------------------

                if (
                    max_pages is not None
                    and self.pages_crawled >= max_pages
                ):

                    continue

                try:

                    await self._process_page(
                        plan
                    )

                    self.pages_crawled += 1

                except Exception as error:

                    self.failed_pages += 1

                    print(
                        "\nPAGE FAILED:",
                        plan.url,
                    )

                    print(
                        f"{type(error).__name__}: "
                        f"{error}"
                    )

            # ----------------------------------------------------------
            # DOCUMENT
            # ----------------------------------------------------------

            elif plan.action == CrawlAction.DOCUMENT:

                try:

                    await self._process_document(
                        plan
                    )

                except Exception as error:

                    print(
                        "\nDOCUMENT FAILED:",
                        plan.url,
                    )

                    print(
                        f"{type(error).__name__}: "
                        f"{error}"
                    )

            # ----------------------------------------------------------
            # RESOURCE
            # ----------------------------------------------------------

            elif plan.action == CrawlAction.RESOURCE:

                # Images/resources remain intentionally ignored.
                continue

        # --------------------------------------------------------------
        # FINAL STATISTICS
        # --------------------------------------------------------------

        print(
            "\n========== Crawl Finished =========="
        )

        print(
            "Pages Crawled       :",
            self.pages_crawled,
        )

        print(
            "Documents Discovered:",
            self.documents_discovered,
        )

        print(
            "Resources Discovered:",
            self.resources_discovered,
        )

        print(
            "Ignored Plans       :",
            self.ignored_plans,
        )

        print(
            "Failed Pages        :",
            self.failed_pages,
        )

        print(
            "Tracked URLs        :",
            self.depth_tracker.size(),
        )

        print(
            "Remaining Queue     :",
            self.queue.size(),
        )

        # --------------------------------------------------------------
        # DOCUMENT INVENTORY
        # --------------------------------------------------------------

        if self.document_inventory:

            print(
                "\n---------- DOCUMENT INVENTORY ----------"
            )

            for index, document in enumerate(
                self.document_inventory.values(),
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
                    "Source Pages:",
                    len(
                        document[
                            "discovered_from"
                        ]
                    ),
                )

                for source_page in document[
                    "discovered_from"
                ]:

                    print(
                        "  -",
                        source_page,
                    )

            print(
                "\n----------------------------------------"
            )                                                         
