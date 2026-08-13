import asyncio

from crawler.crawler import crawl_page


TEST_URLS = [
    {
        "name": "IITJ Homepage",
        "url": "https://www.iitj.ac.in/",
        "expect_success": True,
    },
    {
        "name": "Office of Administration",
        "url": (
            "https://www.iitj.ac.in/"
            "office-of-administration/en/"
            "office-of-administration"
        ),
        "expect_success": True,
    },
    {
        "name": "Office of Establishment",
        "url": (
            "https://www.iitj.ac.in/"
            "office-of-establishment-nf/en/"
            "office-of-establishment-nf"
        ),
        "expect_success": True,
    },
    {
        "name": "Health Center",
        "url": (
            "https://www.iitj.ac.in/"
            "health-center/en/health-center"
        ),
        "expect_success": True,
    },
    {
        "name": "Departments",
        "url": (
            "https://www.iitj.ac.in/"
            "m/Index/main-departments?lg=en"
        ),
        "expect_success": True,
    },
    {
        "name": "Invalid URL",
        "url": (
            "https://www.iitj.ac.in/"
            "this-page-definitely-does-not-exist-xyz123"
        ),
        "expect_success": False,
    },
]


async def main():

    print()
    print("=" * 100)
    print("CRAWLER RESILIENCE — REAL VARIANT TEST")
    print("=" * 100)

    passed = 0

    for index, test in enumerate(
        TEST_URLS,
        start=1,
    ):

        print()
        print("=" * 100)

        print(
            f"TEST {index}: {test['name']}"
        )

        print(
            "URL:",
            test["url"],
        )

        print("=" * 100)

        page = await crawl_page(
            test["url"]
        )

        success = bool(
            page.success
        )

        html_length = len(
            page.html or ""
        )

        markdown_length = len(
            page.markdown or ""
        )

        print()
        print("RESULT")
        print("Success:", success)
        print("Title:", page.title)
        print("HTML length:", html_length)
        print("Markdown length:", markdown_length)

        # ----------------------------------------------------
        # EXPECTED SUCCESS
        # ----------------------------------------------------

        if test["expect_success"]:

            if (
                success
                and html_length >= 1000
                and markdown_length >= 300
            ):

                print("PASS")
                passed += 1

            else:

                print("FAIL")

        # ----------------------------------------------------
        # EXPECTED FAILURE
        # ----------------------------------------------------

        else:

            if not success:

                print(
                    "PASS: invalid/error page rejected"
                )

                passed += 1

            else:

                print(
                    "FAIL: invalid/error page accepted"
                )

    print()
    print("=" * 100)

    print(
        f"Tests passed: "
        f"{passed} / {len(TEST_URLS)}"
    )

    if passed == len(TEST_URLS):

        print(
            "CRAWLER REAL VARIANT TEST: PASS"
        )

    else:

        raise SystemExit(
            "CRAWLER REAL VARIANT TEST: FAIL"
        )

    print("=" * 100)


if __name__ == "__main__":

    asyncio.run(
        main()
    )