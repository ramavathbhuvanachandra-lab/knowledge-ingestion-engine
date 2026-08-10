from processors.knowledge_input_discovery import (
    KnowledgeInputDiscovery,
)

from processors.knowledge_validator import (
    KnowledgeValidator,
)


def main():

    print("=" * 100)
    print("PHASE 7.2 — KNOWLEDGE CONTENT VALIDATION")
    print("=" * 100)

    discovery = KnowledgeInputDiscovery(
        "storage/output"
    )

    inputs = discovery.discover()

    validator = KnowledgeValidator()

    valid_count = 0
    warning_count = 0
    invalid_count = 0

    warning_documents = []
    invalid_documents = []

    for item in inputs:

        result = validator.validate(
            markdown_path=item.markdown_path,
            metadata_path=item.metadata_path,
        )

        if result.valid:

            valid_count += 1

        else:

            invalid_count += 1

            invalid_documents.append(
                result
            )

        if result.warnings:

            warning_count += 1

            warning_documents.append(
                result
            )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print("\nVALIDATION RESULTS")
    print("-" * 100)

    print(
        "Documents discovered :",
        len(inputs),
    )

    print(
        "Valid documents      :",
        valid_count,
    )

    print(
        "Documents with warnings:",
        warning_count,
    )

    print(
        "Invalid documents    :",
        invalid_count,
    )

    # --------------------------------------------------------
    # WARNINGS
    # --------------------------------------------------------

    if warning_documents:

        print("\nWARNINGS")
        print("-" * 100)

        for result in warning_documents[:20]:

            print(
                "\n",
                result.markdown_path,
            )

            for warning in result.warnings:

                print(
                    "  WARNING:",
                    warning,
                )

    # --------------------------------------------------------
    # INVALID
    # --------------------------------------------------------

    if invalid_documents:

        print("\nINVALID DOCUMENTS")
        print("-" * 100)

        for result in invalid_documents:

            print(
                "\n",
                result.markdown_path,
            )

            for error in result.errors:

                print(
                    "  ERROR:",
                    error,
                )

    # --------------------------------------------------------
    # HARD VALIDATION
    # --------------------------------------------------------

    assert len(inputs) > 0, (
        "No documents discovered."
    )

    assert invalid_count == 0, (
        f"{invalid_count} invalid knowledge documents found."
    )

    assert valid_count == len(inputs), (
        "Not all discovered documents are valid."
    )

    print("\nCONTENT VALIDATION")
    print("-" * 100)

    print(
        "Total documents:",
        len(inputs),
    )

    print(
        "Valid:",
        valid_count,
    )

    print(
        "Invalid:",
        invalid_count,
    )

    print(
        "\nPHASE 7.2 KNOWLEDGE CONTENT VALIDATION: PASS"
    )


if __name__ == "__main__":
    main()