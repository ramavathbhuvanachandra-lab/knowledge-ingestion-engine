from processors.knowledge_input_discovery import (
    KnowledgeInputDiscovery,
)


def main():

    print("=" * 100)
    print("PHASE 7.1 — KNOWLEDGE INPUT DISCOVERY")
    print("=" * 100)

    discovery = KnowledgeInputDiscovery(
        "storage/output"
    )

    inputs = discovery.discover()

    print(
        "\nDocuments discovered:",
        len(inputs),
    )

    print("\nSAMPLE DOCUMENTS")
    print("-" * 100)

    for index, item in enumerate(
        inputs[:10],
        start=1,
    ):

        print(
            f"\nDocument #{index}"
        )

        print(
            "Markdown :",
            item.markdown_path,
        )

        print(
            "Metadata :",
            item.metadata_path,
        )

        print(
            "Domain   :",
            item.domain,
        )

        print(
            "Category :",
            item.category,
        )

        print(
            "Title    :",
            item.metadata.get(
                "title"
            ),
        )

        print(
            "URL      :",
            item.metadata.get(
                "url"
            )
            or item.metadata.get(
                "source_url"
            ),
        )

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    assert len(inputs) > 0, (
        "No knowledge documents discovered."
    )

    for item in inputs:

        assert item.markdown_path.is_file(), (
            f"Missing Markdown: "
            f"{item.markdown_path}"
        )

        assert item.metadata_path.is_file(), (
            f"Missing metadata: "
            f"{item.metadata_path}"
        )

        assert isinstance(
            item.metadata,
            dict,
        ), (
            f"Invalid metadata: "
            f"{item.metadata_path}"
        )

    print("\nVALIDATION")
    print("-" * 100)

    print(
        "Markdown + metadata pairs:",
        len(inputs),
    )

    print(
        "Missing metadata:",
        0,
    )

    print(
        "Invalid metadata:",
        0,
    )

    print(
        "\nPHASE 7.1 KNOWLEDGE INPUT DISCOVERY: PASS"
    )


if __name__ == "__main__":
    main()