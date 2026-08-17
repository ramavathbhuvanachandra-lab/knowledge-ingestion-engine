import asyncio
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from crawler.crawl_engine import CrawlEngine


PAGE_CONTENT = """
This is a university information page used for testing a recursive
website crawler. The institution provides undergraduate and
postgraduate education, research programs, academic departments,
faculty services, student support, library facilities, hostel
services, admissions, examinations, scholarships, placements,
campus facilities, notices, events, and administrative services.

Students can use this website to find information about academic
programs, admission procedures, eligibility requirements, courses,
departments, faculty members, research activities, examination
schedules, scholarships, placements, student services, campus
facilities, accommodation, library resources, transportation,
notices, events, and official contact information.

The page contains meaningful institutional information so that the
crawler's quality validation layer recognizes the response as a
usable webpage during integration testing.

This test intentionally creates a circular navigation structure.
The crawler must follow the links once and then recognize that the
starting URL has already entered the crawl lifecycle.

The expected navigation cycle is:

START -> PAGE A -> PAGE B -> START

The crawler must terminate normally without repeatedly crawling the
same URL.
"""


class CycleHandler(BaseHTTPRequestHandler):

    PAGES = {
        "/start": "/page-a",
        "/page-a": "/page-b",
        "/page-b": "/start",
    }

    def do_GET(self):

        next_path = self.PAGES.get(self.path)

        if next_path is None:

            self.send_response(404)
            self.end_headers()

            return

        body = f"""
        <!DOCTYPE html>

        <html>

            <head>
                <title>University Crawl Cycle Test</title>
            </head>

            <body>

                <main>

                    <h1>University Information</h1>

                    <h2>Crawl Cycle Test Page</h2>

                    <p>
                        Current path: {self.path}
                    </p>

                    <p>
                        {PAGE_CONTENT}
                    </p>

                    <p>
                        {PAGE_CONTENT}
                    </p>

                    <p>
                        {PAGE_CONTENT}
                    </p>

                    <nav>
                        <a href="{next_path}">
                            Continue to next page
                        </a>
                    </nav>

                </main>

            </body>

        </html>
        """.encode("utf-8")

        self.send_response(200)

        self.send_header(
            "Content-Type",
            "text/html; charset=utf-8",
        )

        self.send_header(
            "Content-Length",
            str(len(body)),
        )

        self.end_headers()

        self.wfile.write(body)

    def log_message(
        self,
        format,
        *args,
    ):
        pass


def test_crawl_cycle_does_not_repeat():

    async def run():

        server = HTTPServer(
            ("127.0.0.1", 0),
            CycleHandler,
        )

        thread = threading.Thread(
            target=server.serve_forever,
            daemon=True,
        )

        thread.start()

        try:

            port = server.server_address[1]

            start_url = (
                f"http://127.0.0.1:{port}/start"
            )

            engine = CrawlEngine()

            report = await engine.start(
                start_url=start_url,
                max_pages=10,
            )

            return (
                server,
                engine,
                report,
            )

        except Exception:

            server.shutdown()
            server.server_close()

            raise

    (
        server,
        engine,
        report,
    ) = asyncio.run(
        run()
    )

    try:

        stats = report["statistics"]

        print(
            "\n=== CRAWL CYCLE TEST ==="
        )

        print(
            "Pages attempted:",
            stats["pages_attempted"],
        )

        print(
            "Pages crawled:",
            stats["pages_crawled"],
        )

        print(
            "Duplicate URLs:",
            stats["duplicate_urls_skipped"],
        )

        print(
            "Tracked URLs:",
            stats["tracked_urls"],
        )

        print(
            "Queue exhausted:",
            report["queue_exhausted"],
        )

        inventory_urls = {
            record["normalized_url"]
            for record
            in engine.url_inventory.values()
        }

        print(
            "Inventory:",
            sorted(inventory_urls),
        )

        # ----------------------------------------------------
        # BASIC SUCCESS
        # ----------------------------------------------------

        assert (
            stats["failed_pages"]
            == 0
        )

        # ----------------------------------------------------
        # EXACTLY THREE UNIQUE PAGES
        # ----------------------------------------------------

        assert (
            stats["pages_crawled"]
            == 3
        )

        assert (
            len(inventory_urls)
            == 3
        )

        # ----------------------------------------------------
        # CYCLE MUST BE RECOGNIZED
        # ----------------------------------------------------

        assert (
            stats["duplicate_urls_skipped"]
            >= 1
        )

        # ----------------------------------------------------
        # QUEUE MUST EVENTUALLY EMPTY
        # ----------------------------------------------------

        assert (
            report["queue_exhausted"]
            is True
        )

        assert (
            stats["remaining_queue"]
            == 0
        )

        # ----------------------------------------------------
        # EXPECTED URL SET
        # ----------------------------------------------------

        assert any(
            url.endswith("/start")
            for url in inventory_urls
        )

        assert any(
            url.endswith("/page-a")
            for url in inventory_urls
        )

        assert any(
            url.endswith("/page-b")
            for url in inventory_urls
        )

    finally:

        server.shutdown()
        server.server_close()