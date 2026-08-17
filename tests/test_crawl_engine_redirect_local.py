import asyncio
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from crawler.crawl_engine import CrawlEngine


PAGE_TEXT = """
This is a realistic university information page used for crawler
integration testing. The page contains enough structured content
to represent a normal public website page.

The institution provides undergraduate, postgraduate, research,
academic, administrative, student support, library, hostel,
admissions, examination, placement, and campus services.

Students can access information about admissions, academic programs,
departments, faculty members, research activities, scholarships,
examinations, notices, events, campus facilities, accommodation,
transportation, and contact information.
"""


class RedirectHandler(BaseHTTPRequestHandler):

    def do_GET(self):

        if self.path == "/old":
            self.send_response(302)
            self.send_header(
                "Location",
                "/new",
            )
            self.end_headers()
            return

        if self.path == "/new":

            body = f"""
            <!DOCTYPE html>
            <html>
                <head>
                    <title>Redirect Target</title>
                </head>

                <body>
                    <main>

                        <h1>Redirect Target</h1>

                        <p>{PAGE_TEXT}</p>
                        <p>{PAGE_TEXT}</p>
                        <p>{PAGE_TEXT}</p>
                        <p>{PAGE_TEXT}</p>

                        <h2>Navigation</h2>

                        <a href="/new">
                            Redirect Target
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

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        pass


def test_redirect_does_not_create_second_crawl():

    async def run():

        server = HTTPServer(
            ("127.0.0.1", 0),
            RedirectHandler,
        )

        thread = threading.Thread(
            target=server.serve_forever,
            daemon=True,
        )

        thread.start()

        try:

            port = server.server_address[1]

            start_url = (
                f"http://127.0.0.1:{port}/old"
            )

            final_url = (
                f"http://127.0.0.1:{port}/new"
            )

            engine = CrawlEngine()

            report = await engine.start(
                start_url=start_url,
                max_pages=2,
            )

            return (
                server,
                engine,
                report,
                start_url,
                final_url,
            )

        except Exception:
            server.shutdown()
            server.server_close()
            raise

    (
        server,
        engine,
        report,
        start_url,
        final_url,
    ) = asyncio.run(run())

    try:

        stats = report["statistics"]

        print("\n=== REDIRECT DEDUP TEST ===")
        print("Requested :", start_url)
        print("Final URL :", final_url)

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

        inventory_urls = {
            record["normalized_url"]
            for record in engine.url_inventory.values()
        }

        print(
            "Inventory:",
            sorted(inventory_urls),
        )

        assert stats["failed_pages"] == 0

        # /old redirects to /new, so the same actual resource
        # should not be crawled twice.
        assert stats["pages_crawled"] == 1

        # The final URL should be the canonical identity.
        assert final_url in inventory_urls

        # The original redirect source should not remain as a
        # separate canonical inventory entry.
        assert start_url not in inventory_urls

    finally:

        server.shutdown()
        server.server_close()