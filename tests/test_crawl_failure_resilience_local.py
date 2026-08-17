import asyncio
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from crawler.crawl_engine import CrawlEngine


PAGE_CONTENT = """
This is a realistic university information page used for crawler
failure-resilience testing.

The institution provides undergraduate and postgraduate education,
academic departments, admissions, examinations, research activities,
faculty information, scholarships, placements, library services,
hostel facilities, student support, campus facilities, notices,
events, transportation, and official contact information.

This page contains enough meaningful content for the crawler quality
validation layer to accept the response as a usable webpage.
"""


class FailureHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        if self.path == "/start":

            body = f"""
            <!DOCTYPE html>
            <html>
                <head>
                    <title>Failure Resilience Start</title>
                </head>

                <body>
                    <main>

                        <h1>Failure Resilience Test</h1>

                        <p>{PAGE_CONTENT}</p>
                        <p>{PAGE_CONTENT}</p>

                        <a href="/good">
                            Good Page
                        </a>

                        <a href="/broken">
                            Broken Page
                        </a>

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

            return

        if self.path == "/good":

            body = f"""
            <!DOCTYPE html>
            <html>
                <head>
                    <title>Good Page</title>
                </head>

                <body>

                    <main>

                        <h1>Good Page</h1>

                        <p>{PAGE_CONTENT}</p>
                        <p>{PAGE_CONTENT}</p>
                        <p>{PAGE_CONTENT}</p>

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

            return

        if self.path == "/broken":

            self.send_response(500)

            self.send_header(
                "Content-Type",
                "text/html; charset=utf-8",
            )

            self.end_headers()

            self.wfile.write(
                b"Internal Server Error"
            )

            return

        self.send_response(404)
        self.end_headers()

    def log_message(
        self,
        format,
        *args,
    ):
        pass


def test_failed_page_does_not_stop_crawl():

    async def run():

        server = HTTPServer(
            ("127.0.0.1", 0),
            FailureHandler,
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
            "\n=== FAILURE RESILIENCE TEST ==="
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
            "Failed pages:",
            stats["failed_pages"],
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

        # The start page and good page should succeed.
        assert (
            stats["pages_crawled"]
            == 2
        )

        # The broken page must be recorded as failed.
        assert (
            stats["failed_pages"]
            == 1
        )

        # The failure must not abort the crawl loop.
        assert (
            report["queue_exhausted"]
            is True
        )

        # All three URLs should have entered the crawl lifecycle.
        assert (
            len(inventory_urls)
            == 3
        )

    finally:

        server.shutdown()
        server.server_close()