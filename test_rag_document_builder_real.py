from pathlib import Path

from processors.rag_document_builder import (
    RAGDocumentBuilder,
)


TEST_DOMAINS = [
    {
        "path": Path(
            "storage/organized_knowledge/"
            "iitj.ac.in"
        ),
        "expected_files": 3,
        "reason": (
            "IITJ Office of Research & Development "
            "contains validated knowledge."
        ),
    },
    {
        "path": Path(
            "storage/organized_knowledge/"
            "gwpgc.ac.in"
        ),
        "expected_files": 1,
        "reason": (
            "GWPGC contains validated knowledge."
        ),
    },
    {
        "path": Path(
            "storage/organized_knowledge/"
            "home.iitd.ac.in"
        ),
        "expected_files": 1,
        "reason": (
            "IIT Delhi contains validated knowledge."
        ),
    },
]


def test_domain(
    builder: RAGDocumentBuilder,
    test_case: dict,
) -> None:

    organized_root = test_case["path"]

    print()
    print("=" * 100)

    print(
        "INPUT :",
        organized_root,
    )

    print(
        "Reason:",
        test_case["reason"],
    )

    result = builder.build_domain(
        organized_root
    )

    print(
        "Domain    :",
        result["domain"],
    )

    print(
        "Output    :",
        result["output_root"],
    )

    print(
        "Categories:",
        result["categories"],
    )

    print(
        "DOCX files:",
        result["files"],
    )

    print(
        "Sections  :",
        result["sections"],
    )

    print()
    print("GENERATED FILES")

    if not result["category_files"]:

        print(
            "No DOCX files generated."
        )

    else:

        for category, path in sorted(
            result[
                "category_files"
            ].items()
        ):

            print(
                f"{category:25s}: {path}"
            )

    # ========================================================
    # EXPECTATION
    # ========================================================

    expected_files = (
        test_case["expected_files"]
    )

    # --------------------------------------------------------
    # IITJ CURRENT TEST CASE
    # --------------------------------------------------------

    if expected_files == 0:

        assert (
            result["files"] == 0
        ), (
            "Expected zero RAG DOCX files "
            "for this noise-only test domain."
        )

        assert (
            result["sections"] == 0
        ), (
            "Expected zero RAG sections "
            "for this noise-only test domain."
        )

        print()
        print(
            "PASS — no usable knowledge "
            "was correctly converted."
        )

        return

    # --------------------------------------------------------
    # KNOWLEDGE-BEARING DOMAINS
    # --------------------------------------------------------

    assert (
        result["files"] > 0
    ), (
        "Expected RAG DOCX files "
        "but none were generated."
    )

    assert (
        result["sections"] > 0
    ), (
        "Expected RAG sections "
        "but none were generated."
    )

    # --------------------------------------------------------
    # VERIFY EVERY DOCX
    # --------------------------------------------------------

    for path in (
        result[
            "category_files"
        ].values()
    ):

        path = Path(path)

        assert path.exists(), (
            f"Generated DOCX does not exist: "
            f"{path}"
        )

        assert path.is_file(), (
            f"Generated DOCX is not a file: "
            f"{path}"
        )

        assert (
            path.suffix.lower()
            == ".docx"
        ), (
            f"Invalid output format: "
            f"{path}"
        )

    print()
    print("PASS")


def main():

    print()
    print("=" * 100)

    print(
        "PHASE 8.5 — RAG DOCUMENT BUILDER"
    )

    print("=" * 100)

    builder = (
        RAGDocumentBuilder()
    )

    passed = 0

    for test_case in TEST_DOMAINS:

        test_domain(
            builder=builder,
            test_case=test_case,
        )

        passed += 1

    print()
    print("=" * 100)

    print(
        "Domains passed:",
        passed,
        "/",
        len(TEST_DOMAINS),
    )

    assert (
        passed
        == len(TEST_DOMAINS)
    )

    print()
    print(
        "PHASE 8.5 "
        "RAG DOCUMENT BUILDER: PASS"
    )

    print("=" * 100)


if __name__ == "__main__":
    main()
    