from pathlib import Path
import json
import shutil

from processors.xlsx_processor import (
    XLSXProcessor,
)


TEST_DOCUMENTS = [
    {
        "xlsx": (
            "storage/test_documents/"
            "gwpgc.ac.in/"
            "5_2_1_1_20student_20progression_20report.xlsx"
        ),
        "domain": "gwpgc.ac.in",
        "source_url": (
            "https://gwpgc.ac.in/"
            "DynImg/files/"
            "5_2_1_1%20Student%20Progression%20Report.xlsx"
        ),
    },
]


TEST_OUTPUT = Path(
    "storage/test_processed_documents/xlsx_test"
)


def test_xlsx(
    processor: XLSXProcessor,
    document: dict,
):

    xlsx_path = Path(
        document["xlsx"]
    )

    source_url = document[
        "source_url"
    ]

    print(
        "\n" + "=" * 90
    )

    print(
        "TESTING XLSX PROCESSING"
    )

    print(
        "=" * 90
    )

    print(
        "XLSX:",
        xlsx_path,
    )

    # --------------------------------------------------------
    # INPUT VALIDATION
    # --------------------------------------------------------

    assert xlsx_path.exists(), (
        f"Input XLSX does not exist: "
        f"{xlsx_path}"
    )

    assert xlsx_path.is_file(), (
        f"Input XLSX is not a file: "
        f"{xlsx_path}"
    )

    assert (
        xlsx_path.suffix.lower()
        == ".xlsx"
    ), (
        f"Expected XLSX: {xlsx_path}"
    )

    # --------------------------------------------------------
    # PROCESS
    # --------------------------------------------------------

    output_file = processor.process(
        xlsx_path=xlsx_path,
        source_url=source_url,
    )

    # --------------------------------------------------------
    # OUTPUT
    # --------------------------------------------------------

    assert output_file.exists(), (
        f"Markdown output missing: "
        f"{output_file}"
    )

    assert output_file.is_file(), (
        f"Markdown output is not a file: "
        f"{output_file}"
    )

    assert (
        output_file.suffix == ".md"
    ), (
        f"Expected Markdown output: "
        f"{output_file}"
    )

    # --------------------------------------------------------
    # MARKDOWN
    # --------------------------------------------------------

    markdown = output_file.read_text(
        encoding="utf-8"
    )

    assert markdown.strip(), (
        "Extracted Markdown is empty"
    )

    # We know this real workbook has
    # five worksheets.

    assert "# Sheet1" in markdown
    assert "# Sheet2" in markdown
    assert "# Sheet3" in markdown
    assert "# Sheet4" in markdown
    assert "# Sheet5" in markdown

    # Actual knowledge from workbook.

    assert (
        "Name of student enrolling into higher education"
        in markdown
    )

    assert (
        "Program graduated from"
        in markdown
    )

    assert (
        "Name of institution joined"
        in markdown
    )

    assert (
        "Name of programme admitted to"
        in markdown
    )

    # --------------------------------------------------------
    # METADATA
    # --------------------------------------------------------

    metadata_file = (
        output_file.with_suffix(".json")
    )

    assert metadata_file.exists(), (
        f"Metadata file missing: "
        f"{metadata_file}"
    )

    metadata = json.loads(
        metadata_file.read_text(
            encoding="utf-8"
        )
    )

    assert (
        metadata["source_url"]
        == source_url
    )

    assert (
        metadata["source_file"]
        == str(xlsx_path)
    )

    assert (
        metadata["document_type"]
        == "xlsx"
    )

    assert metadata["sheets"] == 5

    assert (
        metadata["sheets_processed"]
        == 5
    )

    assert (
        metadata["rows"] > 0
    )

    assert (
        metadata["non_empty_rows"] > 0
    )

    assert (
        metadata["text_length"] > 0
    )

    assert (
        metadata["extraction_success"]
        is True
    )

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    print(
        "Domain          :",
        document["domain"],
    )

    print(
        "Markdown        :",
        output_file,
    )

    print(
        "Metadata        :",
        metadata_file,
    )

    print(
        "Sheets          :",
        metadata["sheets"],
    )

    print(
        "Rows            :",
        metadata["rows"],
    )

    print(
        "Non-empty rows  :",
        metadata["non_empty_rows"],
    )

    print(
        "Text length     :",
        metadata["text_length"],
    )

    print(
        "PASS:",
        source_url,
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

    processor = XLSXProcessor(
        output_path=TEST_OUTPUT
    )

    passed = 0

    # --------------------------------------------------------
    # TEST DOCUMENTS
    # --------------------------------------------------------

    for document in TEST_DOCUMENTS:

        test_xlsx(
            processor,
            document,
        )

        passed += 1

    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    print(
        "\n" + "=" * 90
    )

    print(
        "XLSX PROCESSING RESULTS"
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

    assert (
        passed
        == len(TEST_DOCUMENTS)
    )

    print(
        "\nPHASE 6.4 XLSX PROCESSING: PASS"
    )


if __name__ == "__main__":
    main()
