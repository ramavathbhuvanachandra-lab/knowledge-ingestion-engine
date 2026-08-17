import asyncio
from pathlib import Path
import shutil

from crawler.crawler import crawl_page
from processors.page_processor import PageProcessor


TEST_SITES = [
    "https://" + "gwpgc.ac.in/",
    "https://" + "www.iitj.ac.in/",
    "https://" + "www.vbspu.ac.in/en",
    "https://" + "home.iitd.ac.in/",
]

TEST_OUTPUT = Path(
    "storage/test_real_output"
)


async def test_website(url: str):

    print("\n" + "=" * 90)
    print("TESTING:", url)
    print("=" * 90)

    # --------------------------------------------------------
    # URL INPUT VALIDATION
    # --------------------------------------------------------

    assert url.startswith(
        ("http://", "https://")
    ), f"Invalid test URL scheme: {url}"

    assert "[" not in url
    assert "]" not in url
    assert "(" not in url
    assert ")" not in url

    # --------------------------------------------------------
    # CRAWL
    # --------------------------------------------------------

    page = await crawl_page(url)

    # --------------------------------------------------------
    # CRAWL RESULT VALIDATION
    # --------------------------------------------------------

    assert page.success, (
        f"Crawl failed: {url}"
    )

    assert page.url, (
        f"Missing page URL: {url}"
    )

    assert page.title is not None, (
        f"Missing title: {url}"
    )

    assert "[" not in page.url
    assert "]" not in page.url
    assert "(" not in page.url
    assert ")" not in page.url

    # --------------------------------------------------------
    # PROCESS + STORE
    # --------------------------------------------------------

    processor = PageProcessor(
        base_path=TEST_OUTPUT
    )

    filename = processor.process(page)

    # --------------------------------------------------------
    # FILENAME VALIDATION
    # --------------------------------------------------------

    assert filename, (
        f"Filename was empty: {url}"
    )

    assert "/" not in filename
    assert "\\" not in filename

    # --------------------------------------------------------
    # DOMAIN VALIDATION
    # --------------------------------------------------------

    domain = page.url.split("/")[2]

    assert domain, (
        f"Could not determine domain: {page.url}"
    )

    domain_dir = (
        TEST_OUTPUT / domain
    )

    assert domain_dir.exists(), (
        f"Domain directory missing: {domain_dir}"
    )

    # --------------------------------------------------------
    # STORED FILE VALIDATION
    # --------------------------------------------------------

    files = list(
        domain_dir.rglob("*")
    )

    markdown_files = [
        file
        for file in files
        if file.is_file()
        and file.suffix == ".md"
    ]

    metadata_files = [
        file
        for file in files
        if file.is_file()
        and file.suffix == ".json"
    ]

    assert markdown_files, (
        f"No Markdown file created for {url}"
    )

    assert metadata_files, (
        f"No metadata file created for {url}"
    )

    # --------------------------------------------------------
    # OUTPUT PATH VALIDATION
    # --------------------------------------------------------

    for file in files:

        if not file.is_file():
            continue

        file_string = str(file)

        assert "[http" not in file_string
        assert "](" not in file_string

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    print("Title    :", page.title)
    print("URL      :", page.url)
    print("Filename :", filename)
    print("Domain   :", domain)
    print(
        "Stored files:",
        len([
            f
            for f in files
            if f.is_file()
        ])
    )

    print("PASS:", url)


async def main():

    if TEST_OUTPUT.exists():
        shutil.rmtree(TEST_OUTPUT)

    TEST_OUTPUT.mkdir(
        parents=True,
        exist_ok=True,
    )

    passed = 0

    for url in TEST_SITES:

        try:

            await test_website(url)
            passed += 1

        except Exception as exc:

            print(
                "\nFAILED:",
                url
            )

            print(
                type(exc).__name__,
                ":",
                exc,
            )

    print("\n" + "=" * 90)
    print("REAL FILENAME STORAGE RESULTS")
    print("=" * 90)

    print(
        "Sites passed :",
        passed,
        "/",
        len(TEST_SITES),
    )

    assert passed == len(TEST_SITES), (
        "One or more real websites failed"
    )

    print(
        "\nREAL FILENAME STORAGE: PASS"
    )


if __name__ == "__main__":
    asyncio.run(main())
