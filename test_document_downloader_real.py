from pathlib import Path
import json
import shutil

from processors.document_downloader import (
    DocumentDownloader,
)


TEST_DOCUMENTS = [
    {
        "url": (
            "https://www.iitj.ac.in/"
            "PageImages/Gallery/03-2025/"
            "institute-sustainability-committee-638779148376488067.pdf"
        ),
        "domain": "www.iitj.ac.in",
    },
    {
        "url": (
            "https://home.iitd.ac.in/"
            "uploads/Newsletter-Apr-26-Issue.pdf"
        ),
        "domain": "home.iitd.ac.in",
    },
]


TEST_OUTPUT = Path(
    "storage/test_documents"
)


def test_document(
    downloader: DocumentDownloader,
    document: dict,
):
    url = document["url"]
    domain = document["domain"]

    print("\n" + "=" * 90)
    print("TESTING DOCUMENT")
    print("=" * 90)

    print("URL:", url)

    # --------------------------------------------------------
    # DOWNLOAD
    # --------------------------------------------------------

    output_path = downloader.download(
        url=url,
        domain=domain,
    )

    # --------------------------------------------------------
    # PDF PATH
    # --------------------------------------------------------

    assert output_path.exists(), (
        f"PDF was not created: {output_path}"
    )

    assert output_path.is_file(), (
        f"Output is not a file: {output_path}"
    )

    assert output_path.suffix == ".pdf", (
        f"Expected PDF file: {output_path}"
    )

    # --------------------------------------------------------
    # DOMAIN DIRECTORY
    # --------------------------------------------------------

    expected_domain_dir = (
        TEST_OUTPUT / domain
    )

    assert expected_domain_dir.exists(), (
        f"Domain directory missing: "
        f"{expected_domain_dir}"
    )

    # --------------------------------------------------------
    # FILE SIZE
    # --------------------------------------------------------

    size = output_path.stat().st_size

    assert size > 0, (
        f"Downloaded file is empty: {output_path}"
    )

    # --------------------------------------------------------
    # PDF MAGIC HEADER
    # --------------------------------------------------------

    header = output_path.read_bytes()[:5]

    assert header == b"%PDF-", (
        f"File does not contain a PDF header: "
        f"{output_path}"
    )

    # --------------------------------------------------------
    # METADATA
    # --------------------------------------------------------

    metadata_path = (
        output_path.with_suffix(".json")
    )

    assert metadata_path.exists(), (
        f"Metadata file missing: {metadata_path}"
    )

    assert metadata_path.is_file(), (
        f"Metadata path is not a file: {metadata_path}"
    )

    metadata = json.loads(
        metadata_path.read_text(
            encoding="utf-8"
        )
    )

    # --------------------------------------------------------
    # METADATA VALIDATION
    # --------------------------------------------------------

    assert metadata["source_url"] == url

    assert metadata["domain"] == domain

    assert metadata["document_type"] == "pdf"

    assert metadata["success"] is True

    assert metadata["size_bytes"] == size

    assert metadata["local_file"] == str(
        output_path
    )

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    print("PDF     :", output_path)

    print(
        "Metadata:",
        metadata_path,
    )

    print(
        "Size    :",
        size,
        "bytes",
    )

    print(
        "Header  :",
        header,
    )

    print("PASS:", url)


def main():

    # --------------------------------------------------------
    # CLEAN TEST OUTPUT
    # --------------------------------------------------------

    if TEST_OUTPUT.exists():
        shutil.rmtree(
            TEST_OUTPUT
        )

    TEST_OUTPUT.mkdir(
        parents=True,
        exist_ok=True,
    )

    downloader = DocumentDownloader(
        base_path=TEST_OUTPUT
    )

    passed = 0

    # --------------------------------------------------------
    # TEST DOCUMENTS
    # --------------------------------------------------------

    for document in TEST_DOCUMENTS:

        try:

            test_document(
                downloader,
                document,
            )

            passed += 1

        except Exception as error:

            print(
                "\nFAILED:",
                document["url"],
            )

            print(
                type(error).__name__,
                ":",
                error,
            )

            raise

    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    print(
        "\n" + "=" * 90
    )

    print(
        "DOCUMENT STORAGE + METADATA RESULTS"
    )

    print(
        "=" * 90
    )

    print(
        "Documents passed:",
        passed,
        "/",
        len(TEST_DOCUMENTS),
    )

    assert passed == len(
        TEST_DOCUMENTS
    )

    print(
        "\nPHASE 6.3 DOCUMENT STORAGE + METADATA: PASS"
    )


if __name__ == "__main__":
    main()