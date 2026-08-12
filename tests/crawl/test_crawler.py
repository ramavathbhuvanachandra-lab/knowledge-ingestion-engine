import asyncio

from crawler.crawler import crawl_page


TEST_SITES = [
    (
        "GWPGC",
        "https://gwpgc.ac.in/",
    ),
    (
        "IIT DELHI",
        "https://home.iitd.ac.in/",
    ),
    (
        "VBSPU",
        "https://www.vbspu.ac.in/en",
    ),
]


async def test_site(
    name,
    url,
):

    print()
    print("=" * 70)
    print(name)
    print("=" * 70)

    print(
        "URL     :",
        url
    )

    try:

        page = await crawl_page(
            url
        )

        print()
        print(
            "SUCCESS :",
            page.success
        )

        print(
            "TITLE   :",
            page.title
        )

        print(
            "HTML    :",
            len(page.html or ""),
            "characters"
        )

        print(
            "MARKDOWN:",
            len(page.markdown or ""),
            "characters"
        )

        if page.success:

            print()
            print(
                "RESULT  : PASS"
            )

        else:

            print()
            print(
                "RESULT  : FAIL"
            )

    except Exception as error:

        print()
        print(
            "EXCEPTION:",
            type(error).__name__
        )

        print(
            "MESSAGE  :",
            str(error)
        )


async def main():

    print()
    print("=" * 70)
    print("CRAWLER FALLBACK TEST")
    print("=" * 70)

    for name, url in TEST_SITES:

        await test_site(
            name,
            url
        )

    print()
    print("=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":

    asyncio.run(
        main()
    )