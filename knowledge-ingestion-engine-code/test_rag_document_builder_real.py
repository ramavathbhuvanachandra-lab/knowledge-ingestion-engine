from pathlib import Path

from processors.rag_document_builder import (
    RAGDocumentBuilder,
)


TEST_DOMAINS = [
    {
        "path": Path(
            "storage/organized_knowledge/"
            "www.iitj.ac.in"
        ),
        "reason": (
            "IITJ targeted Phase 8.3/8.4 "
            "validation dataset."
        ),
    },
]


def test_domain(
    builder: RAGDocumentBuilder,
    test_case: dict,
) -> None:

    organized_root = test_case[
        "path"
    ]

    print()
    print("=" * 100)

    print(
        "INPUT :",
        organized_root,
    )

    print(
        "Reason:",
        test_case[
            "reason"
        ],
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

    print(
        "Input units:",
        result["input_units"],
    )

    print(
        "Output units:",
        result["output_units"],
    )

    print()
    print(
        "GENERATED FILES"
    )

    if not result[
        "category_files"
    ]:

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
                f"{category:30s}: {path}"
            )

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    assert result[
        "files"
    ] > 0, (
        "Expected RAG DOCX files "
        "but none were generated."
    )

    assert result[
        "sections"
    ] > 0, (
        "Expected RAG sections "
        "but none were generated."
    )

    assert result[
        "input_units"
    ] == result[
        "output_units"
    ], (
        "RAG unit count mismatch."
    )

    assert result[
        "coverage"
    ][
        "coverage_complete"
    ], (
        "RAG DOCX coverage validation failed."
    )

    # --------------------------------------------------------
    # VERIFY FILES
    # --------------------------------------------------------

    for path in result[
        "category_files"
    ].values():

        path = Path(
            path
        )

        assert path.exists(), (
            f"Generated DOCX does not exist: "
            f"{path}"
        )

        assert path.stat().st_size > 0, (
            f"Generated DOCX is empty: "
            f"{path}"
        )

    print()
    print(
        "PASS"
    )


def main():

    builder = RAGDocumentBuilder(
        output_root=(
            "storage/rag_knowledge"
        )
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
        f"Domains passed: "
        f"{passed} / "
        f"{len(TEST_DOMAINS)}"
    )

    print()

    print(
        "PHASE 8.5 RAG DOCUMENT BUILDER: PASS"
    )

    print("=" * 100)


if __name__ == "__main__":
    main()