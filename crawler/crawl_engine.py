from urllib.parse import urlparse

from crawler.crawler import crawl_page
from crawler.link_extractor import extract_internal_links
from crawler.url_normalizer import normalize_url
from crawler.url_validator import is_valid_url
from crawler.url_classifier import classify_url
from crawler.url_queue import URLQueue
from models.url import URLType
from processors.page_processor import PageProcessor
from models.page import PageData

class CrawlEngine:

    def __init__(self):
        self.queue = URLQueue()
        self.processor = PageProcessor()

    def _process_links(self, links, source_url, base_domain):
        """
        Normalize, validate, classify and enqueue webpage URLs.
        """

        for link in links:

            normalized = normalize_url(link)

            if not is_valid_url(normalized):
                continue

            url_info = classify_url(
                raw_url=link,
                normalized_url=normalized,
                base_domain=base_domain,
                discovered_from=source_url
            )

            if url_info.url_type == URLType.WEBPAGE:
                self.queue.enqueue(url_info)

    async def start(self, start_url: str):

        print(f"\n========== Starting Crawl ==========")
        print(start_url)

        # Normalize homepage URL
        normalized_start = normalize_url(start_url)

        # Prevent homepage from being re-added
        self.queue.seen_urls.add(normalized_start)

        base_domain = urlparse(start_url).netloc

        # -----------------------------
        # Crawl Homepage
        # -----------------------------

        homepage = await crawl_page(start_url)

        homepage_links = extract_internal_links(
            homepage.html,
            homepage.url
        )

        self._process_links(
            homepage_links,
            homepage.url,
            base_domain
        )

        print(f"\nInitial Queue Size : {self.queue.size()}")

        # -----------------------------
        # Recursive Crawl Loop
        # -----------------------------

        pages_crawled = 0

        while not self.queue.is_empty():

            current = self.queue.dequeue()

            if current is None:
                break

            print("\n======================================")
            print(f"Crawling Page #{pages_crawled + 1}")
            print(current.normalized_url)
            print("======================================")

            try:

                page = await crawl_page(
                    current.normalized_url
                )
                self.processor.process(page)
                from processors.page_processor import PageProcessor
                processor = PageProcessor()
                

                print("Title :", page.title)

                new_links = extract_internal_links(
                    page.html,
                    page.url
                )

                print(f"Links Found : {len(new_links)}")

                self._process_links(
                    new_links,
                    page.url,
                    base_domain
                )

            except Exception as e:

                print(f"Failed : {current.normalized_url}")
                print(e)

            pages_crawled += 1

            print(f"Queue Size : {self.queue.size()}")

            # -----------------------------------
            # SAFETY LIMIT (REMOVE LATER)
            # -----------------------------------

            if pages_crawled >= 10:

                print("\n======================================")
                print("Reached Test Limit (10 Pages)")
                print("Stopping Crawl...")
                print("======================================")

                break

        print("\n========== Crawl Finished ==========")
        print(f"Pages Crawled : {pages_crawled}")
        print(f"Remaining Queue : {self.queue.size()}")