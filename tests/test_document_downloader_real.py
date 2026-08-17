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
        "document_type": "pdf",
    },
    {
        "url": (
            "https://home.iitd.ac.in/"
            "uploads/Newsletter-Apr-26-Issue.pdf"
        ),
        "domain": "home.iitd.ac.in",
        "document_type": "pdf",
    },
    {
        "url": (
            "https://gwpgc.ac.in/DynImg/files/"
            "5_2_1_1%20Student%20Progression%20Report.xlsx"
        ),
        "domain": "gwpgc.ac.in",
        "document_type": "xlsx",
    },
]


TEST_OUTPUT = Path(
    "storage/test_documents"
)


# ============================================================
# TEST ONE DOCUMENT
# ============================================================

def test_document(
    downloader: DocumentDownloader,
    document: dict,
) -> None:

    print(
        "\n" + "=" * 90
    )

    print(
        "TESTING DOCUMENT"
    )

    print(
        "=" * 90
    )

    url = document["url"]
    domain = document["domain"]
    expected_type = document["document_type"]

    print(
        "URL :",
        url,
    )

    print(
        "Expected Type :",
        expected_type,
    )

    # --------------------------------------------------------
    # DOWNLOAD
    # --------------------------------------------------------

    output_path = downloader.download(
        url=url,
        domain=domain,
    )

    # --------------------------------------------------------
    # OUTPUT FILE
    # --------------------------------------------------------

    assert output_path.exists(), (
        f"Document was not created: {output_path}"
    )

    assert output_path.is_file(), (
        f"Output is not a file: {output_path}"
    )

    # --------------------------------------------------------
    # FILE EXTENSION
    # --------------------------------------------------------

    assert output_path.suffix.lower() == (
        f".{expected_type}"
    ), (
        f"Expected .{expected_type} file: "
        f"{output_path}"
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

    assert expected_domain_dir.is_dir(), (
        f"Domain path is not a directory: "
        f"{expected_domain_dir}"
    )

    # --------------------------------------------------------
    # FILE SIZE
    # --------------------------------------------------------

    size = output_path.stat().st_size

    assert size > 0, (
        f"Downloaded file is empty: "
        f"{output_path}"
    )

    # --------------------------------------------------------
    # CONTENT VALIDATION
    # --------------------------------------------------------

    header = output_path.read_bytes()[:5]

    if expected_type == "pdf":

        assert header == b"%PDF-", (
            f"File does not contain a valid PDF "
            f"header: {output_path}"
        )

    elif expected_type == "xlsx":

        # XLSX is a ZIP-based Office document.
        assert header[:2] == b"PK", (
            f"File does not contain a valid XLSX "
            f"ZIP header: {output_path}"
        )

    else:

        raise AssertionError(
            f"Unsupported test document type: "
            f"{expected_type}"
        )

    # --------------------------------------------------------
    # METADATA
    # --------------------------------------------------------

    metadata_path = (
        output_path.with_suffix(".json")
    )

    assert metadata_path.exists(), (
        f"Metadata file missing: "
        f"{metadata_path}"
    )

    assert metadata_path.is_file(), (
        f"Metadata path is not a file: "
        f"{metadata_path}"
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

    assert metadata["document_type"] == (
        expected_type
    )

    assert metadata["success"] is True

    assert metadata["size_bytes"] == size

    assert metadata["local_file"] == str(
        output_path
    )

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    print(
        "Document :",
        output_path,
    )

    print(
        "Metadata :",
        metadata_path,
    )

    print(
        "Type     :",
        expected_type,
    )

    print(
        "Size     :",
        size,
        "bytes",
    )

    print(
        "Header   :",
        header,
    )

    print(
        "PASS:",
        url,
    )


# ============================================================
# MAIN
# ============================================================

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

    # --------------------------------------------------------
    # CREATE DOWNLOADER
    # --------------------------------------------------------

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