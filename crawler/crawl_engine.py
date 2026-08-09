from urllib.parse import urlparse

from bs4 import BeautifulSoup

from crawler.crawler import crawl_page
from crawler.crawl_policy import CrawlPolicy
from crawler.crawl_queue import CrawlQueue
from crawler.depth_tracker import DepthTracker
from crawler.url_normalizer import normalize_url

from models.crawl_plan import CrawlAction
from models.url import URLInfo

from pipeline.navigation_pipeline import NavigationPipeline
from processors.page_processor import PageProcessor

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
    """

    def __init__(self):
        self.queue = CrawlQueue()
        self.depth_tracker = DepthTracker()
        self.policy = CrawlPolicy()
        self.discovery = URLDiscovery()
        self.processor = PageProcessor()

        self.pages_crawled = 0
        self.documents_discovered = 0
        self.resources_discovered = 0
        self.ignored_plans = 0
        self.failed_pages = 0

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

                depth = self.depth_tracker.register_root(
                    normalized_url
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

            # URLDiscovery intentionally leaves depth at 0.
            # Create a new URLInfo carrying the actual crawl depth.

            planned_url_info = URLInfo(
                raw_url=url_info.raw_url,
                normalized_url=url_info.normalized_url,
                url_type=url_info.url_type,
                discovered_from=url_info.discovered_from,
                depth=depth,
            )

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
            # STATISTICS
            # ----------------------------------------------------------

            if plan.action == CrawlAction.DOCUMENT:

                self.documents_discovered += 1

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

        print("\n======================================")
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
        print("======================================")

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

        # --------------------------------------------------------------
        # PLAN + QUEUE
        # --------------------------------------------------------------

        self._create_and_enqueue_plans(
            discovered_urls=discovered_urls,
            source_url=normalize_url(
                page.url
            ),
        )

        self.pages_crawled += 1

    # ------------------------------------------------------------------
    # DOCUMENT / RESOURCE HANDLING
    # ------------------------------------------------------------------

    async def _handle_non_page_plan(
        self,
        plan,
    ) -> None:
        """
        Phase 5 recognizes DOCUMENT and RESOURCE plans.

        Actual document/resource extraction belongs to the next
        processing phase. We deliberately do not feed PDFs/images
        into crawl_page().
        """

        if plan.action == CrawlAction.DOCUMENT:

            print("\n--------------------------------------")
            print("DOCUMENT PLAN")
            print("URL   :", plan.url)
            print("Depth :", plan.depth)
            print(
                "Status: discovered, processing deferred"
            )
            print("--------------------------------------")

            return

        if plan.action == CrawlAction.RESOURCE:

            print("\n--------------------------------------")
            print("RESOURCE PLAN")
            print("URL   :", plan.url)
            print("Depth :", plan.depth)
            print(
                "Status: discovered, processing deferred"
            )
            print("--------------------------------------")

            return

    # ------------------------------------------------------------------
    # START CRAWL
    # ------------------------------------------------------------------

    async def start(
        self,
        start_url: str,
    ):
        """
        Start crawling from the supplied root URL.
        """

        print(
            "\n========== Starting Crawl =========="
        )

        print(
            "Start URL :",
            start_url,
        )

        # --------------------------------------------------------------
        # NORMALIZE ROOT
        # --------------------------------------------------------------

        normalized_start = normalize_url(
            start_url
        )

        # --------------------------------------------------------------
        # REGISTER ROOT DEPTH
        # --------------------------------------------------------------

        self.depth_tracker.register_root(
            normalized_start
        )

        self.queue.mark_seen(
             normalized_start
        )

        # --------------------------------------------------------------
        # CRAWL HOMEPAGE
        # --------------------------------------------------------------

        try:

            homepage = await crawl_page(
                normalized_start
            )

            if not homepage.success:

                raise RuntimeError(
                    f"Homepage crawl failed: "
                    f"{normalized_start}"
                )

            if not homepage.html:

                raise RuntimeError(
                    "Homepage returned empty HTML"
                )

        except Exception as e:

            print(
                "\nFAILED TO CRAWL ROOT:"
            )

            print(e)

            return

        print(
            "\nHomepage crawled successfully"
        )

        print(
            "Title :",
            homepage.title,
        )

        # --------------------------------------------------------------
        # PROCESS HOMEPAGE
        # --------------------------------------------------------------

        try:

            self.processor.process(
                homepage
            )

        except Exception as e:

            print(
                "\nPage processing failed:"
            )

            print(e)

        # --------------------------------------------------------------
        # DISCOVER HOMEPAGE NAVIGATION
        # --------------------------------------------------------------

        discovered_urls = (
            self._discover_navigation(
                html=homepage.html,
                source_url=homepage.url,
            )
        )

        print(
            "\nHomepage URLs discovered :",
            len(discovered_urls),
        )

        # --------------------------------------------------------------
        # CREATE PLANS
        # --------------------------------------------------------------

        self._create_and_enqueue_plans(
            discovered_urls=discovered_urls,
            source_url=normalize_url(
                homepage.url
            ),
        )

        print(
            "\nInitial CrawlQueue Size :",
            self.queue.size(),
        )

        # --------------------------------------------------------------
        # CRAWL LOOP
        # --------------------------------------------------------------

        while not self.queue.is_empty():

            plan = self.queue.dequeue()

            if plan is None:

                break

            # ----------------------------------------------------------
            # DOCUMENT
            # ----------------------------------------------------------

            if plan.action == CrawlAction.DOCUMENT:

                await self._handle_non_page_plan(
                    plan
                )

                continue

            # ----------------------------------------------------------
            # RESOURCE
            # ----------------------------------------------------------

            if plan.action == CrawlAction.RESOURCE:

                await self._handle_non_page_plan(
                    plan
                )

                continue

            # ----------------------------------------------------------
            # IGNORE
            # ----------------------------------------------------------

            if plan.action == CrawlAction.IGNORE:

                self.ignored_plans += 1

                continue

            # ----------------------------------------------------------
            # WEBPAGE
            # ----------------------------------------------------------

            if plan.action == CrawlAction.CRAWL:

                try:

                    await self._process_page(
                        plan
                    )

                except Exception as e:

                    self.failed_pages += 1

                    print(
                        "\nFailed :",
                        plan.url,
                    )

                    print(
                        "Error :",
                        e,
                    )

            print(
                "\nQueue Size :",
                self.queue.size(),
            )

            # ----------------------------------------------------------
            # SAFETY LIMIT
            # ----------------------------------------------------------

            if self.pages_crawled >= 10:

                print(
                    "\n======================================"
                )

                print(
                    "Reached Test Limit (10 Pages)"
                )

                print(
                    "Stopping Crawl..."
                )

                print(
                    "======================================"
                )

                break

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