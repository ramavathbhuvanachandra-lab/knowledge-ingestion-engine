from pathlib import Path
import json
import shutil

from processors.document_integrator import (
    DocumentIntegrator,
)


TEST_DOCUMENTS = [
    {
        "markdown": (
            "storage/"
            "test_crawl_engine_documents/"
            "processed/"
            "home.iitd.ac.in/"
            "newsletter-apr-26-issue.md"
        ),
        "metadata": (
            "storage/"
            "test_crawl_engine_documents/"
            "processed/"
            "home.iitd.ac.in/"
            "newsletter-apr-26-issue.json"
        ),
        "domain": "home.iitd.ac.in",
    },
]


TEST_OUTPUT = Path(
    "storage/test_document_integration"
)


def test_document(
    integrator: DocumentIntegrator,
    document: dict,
):
    markdown_path = Path(
        document["markdown"]
    )

    metadata_path = Path(
        document["metadata"]
    )

    domain = document[
        "domain"
    ]

    print(
        "\n" + "=" * 90
    )

    print(
        "TESTING DOCUMENT INTEGRATION"
    )

    print(
        "=" * 90
    )

    print(
        "Markdown:",
        markdown_path,
    )

    print(
        "Metadata:",
        metadata_path,
    )

    # --------------------------------------------------------
    # INTEGRATE
    # --------------------------------------------------------

    output_markdown, output_metadata = (
        integrator.integrate(
            markdown_path=markdown_path,
            metadata_path=metadata_path,
            domain=domain,
        )
    )

    # --------------------------------------------------------
    # FILE EXISTENCE
    # --------------------------------------------------------

    assert output_markdown.exists(), (
        f"Markdown was not integrated: "
        f"{output_markdown}"
    )

    assert output_metadata.exists(), (
        f"Metadata was not integrated: "
        f"{output_metadata}"
    )

    # --------------------------------------------------------
    # FILE TYPE
    # --------------------------------------------------------

    assert output_markdown.suffix == ".md"

    assert output_metadata.suffix == ".json"

    # --------------------------------------------------------
    # MARKDOWN CONTENT
    # --------------------------------------------------------

    source_text = markdown_path.read_text(
        encoding="utf-8"
    )

    output_text = output_markdown.read_text(
        encoding="utf-8"
    )

    assert output_text == source_text, (
        "Integrated Markdown content "
        "does not match source content"
    )

    assert len(output_text) > 0, (
        "Integrated Markdown is empty"
    )

    # --------------------------------------------------------
    # METADATA
    # --------------------------------------------------------

    metadata = json.loads(
        output_metadata.read_text(
            encoding="utf-8"
        )
    )

    assert metadata[
        "document_type"
    ] == "pdf"

    assert metadata[
        "extraction_success"
    ] is True

    assert metadata[
        "storage_domain"
    ] == domain

    assert metadata[
        "storage_category"
    ] == "others"

    assert (
        metadata["storage_path"]
        == str(output_markdown)
    )

    # --------------------------------------------------------
    # SOURCE URL
    # --------------------------------------------------------

    assert metadata[
        "source_url"
    ], "Missing source URL"

    print(
        "\nIntegrated Markdown:",
        output_markdown,
    )

    print(
        "Integrated Metadata:",
        output_metadata,
    )

    print(
        "Source URL:",
        metadata["source_url"],
    )

    print(
        "PASS"
    )


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

    integrator = DocumentIntegrator(
        output_path=TEST_OUTPUT
    )

    passed = 0

    # --------------------------------------------------------
    # TEST
    # --------------------------------------------------------

    for document in TEST_DOCUMENTS:

        try:

            test_document(
                integrator,
                document,
            )

            passed += 1

        except Exception as error:

            print(
                "\nFAILED"
            )

            print(
                f"{type(error).__name__}: "
                f"{error}"
            )

            raise

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    print(
        "\n" + "=" * 90
    )

    print(
        "DOCUMENT INTEGRATION RESULTS"
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
        "\nPHASE 6.7 "
        "EXTERNAL CONTENT INTEGRATION: PASS"
    )


if __name__ == "__main__":
    main()