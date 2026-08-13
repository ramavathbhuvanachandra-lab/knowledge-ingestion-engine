from pathlib import Path
import json

from processors.knowledge_cleaner import KnowledgeCleaner


# ============================================================
# PHASE 7.3 — REAL KNOWLEDGE CLEANING TEST
# ============================================================

TEST_DOCUMENTS = [
    {
        "markdown": Path(
            "storage/output/iitj.ac.in/others/search.md"
        ),
        "metadata": Path(
            "storage/output/iitj.ac.in/others/search.json"
        ),
        "name": "IITJ webpage",
    },
    {
        "markdown": Path(
            "storage/output/gwpgc.ac.in/others/"
            "government_girls_p_g_college_ghazipur.md"
        ),
        "metadata": Path(
            "storage/output/gwpgc.ac.in/others/"
            "government_girls_p_g_college_ghazipur.json"
        ),
        "name": "GWPGC webpage",
    },
    {
        "markdown": Path(
            "storage/output/home.iitd.ac.in/others/"
            "newsletter-apr-26-issue.md"
        ),
        "metadata": Path(
            "storage/output/home.iitd.ac.in/others/"
            "newsletter-apr-26-issue.json"
        ),
        "name": "IIT Delhi PDF",
    },
]


# ============================================================
# TEST
# ============================================================

def test_document(
    cleaner: KnowledgeCleaner,
    document: dict,
):
    markdown_path = document["markdown"]
    metadata_path = document["metadata"]
    name = document["name"]

    print("\n" + "=" * 100)
    print(f"TESTING: {name}")
    print("=" * 100)

    # --------------------------------------------------------
    # INPUT VALIDATION
    # --------------------------------------------------------

    assert markdown_path.exists(), (
        f"Markdown missing: {markdown_path}"
    )

    assert metadata_path.exists(), (
        f"Metadata missing: {metadata_path}"
    )

    original_markdown = markdown_path.read_text(
        encoding="utf-8"
    )

    original_metadata = json.loads(
        metadata_path.read_text(
            encoding="utf-8"
        )
    )

    assert original_markdown.strip(), (
        f"Original Markdown is empty: {markdown_path}"
    )

    print(
        "Input Markdown :",
        markdown_path,
    )

    print(
        "Input Metadata :",
        metadata_path,
    )

    print(
        "Original size  :",
        len(original_markdown),
    )

    # --------------------------------------------------------
    # CLEAN
    # --------------------------------------------------------

    cleaned_markdown_path, cleaned_metadata_path = (
        cleaner.clean(
            markdown_path=markdown_path,
            metadata_path=metadata_path,
        )
    )

    # --------------------------------------------------------
    # OUTPUT VALIDATION
    # --------------------------------------------------------

    assert cleaned_markdown_path.exists(), (
        f"Cleaned Markdown missing: "
        f"{cleaned_markdown_path}"
    )

    assert cleaned_metadata_path.exists(), (
        f"Cleaned metadata missing: "
        f"{cleaned_metadata_path}"
    )

    cleaned_markdown = (
        cleaned_markdown_path.read_text(
            encoding="utf-8"
        )
    )

    cleaned_metadata = json.loads(
        cleaned_metadata_path.read_text(
            encoding="utf-8"
        )
    )

    assert cleaned_markdown.strip(), (
        f"Cleaned Markdown is empty: "
        f"{cleaned_markdown_path}"
    )

    # --------------------------------------------------------
    # CONTENT VALIDATION
    # --------------------------------------------------------

    assert (
        "UX4G Accessibility Tool"
        not in cleaned_markdown
    ), (
        "Accessibility boilerplate was not removed"
    )

    assert (
        "Open the accessibility option"
        not in cleaned_markdown
    ), (
        "Accessibility boilerplate was not removed"
    )

    # --------------------------------------------------------
    # METADATA VALIDATION
    # --------------------------------------------------------

    assert (
        cleaned_metadata["knowledge_cleaned"]
        is True
    )

    assert (
        cleaned_metadata["cleaning_version"]
        == "7.3"
    )

    assert (
        cleaned_metadata[
            "original_content_length"
        ]
        == len(original_markdown)
    )

    assert (
        cleaned_metadata[
            "cleaned_content_length"
        ]
        == len(cleaned_markdown)
    )

    # Source URL must survive.
    source_url = (
        original_metadata.get("url")
        or original_metadata.get("source_url")
    )

    cleaned_source_url = (
        cleaned_metadata.get("url")
        or cleaned_metadata.get("source_url")
    )

    assert source_url == cleaned_source_url, (
        "Source URL was not preserved"
    )

    # --------------------------------------------------------
    # OUTPUT
    # --------------------------------------------------------

    print(
        "Cleaned Markdown:",
        cleaned_markdown_path,
    )

    print(
        "Cleaned Metadata:",
        cleaned_metadata_path,
    )

    print(
        "Cleaned size   :",
        len(cleaned_markdown),
    )

    print(
        "Source URL     :",
        cleaned_source_url,
    )

    print(
        "PASS"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    cleaner = KnowledgeCleaner()

    passed = 0

    for document in TEST_DOCUMENTS:

        test_document(
            cleaner,
            document,
        )

        passed += 1

    print("\n" + "=" * 100)
    print("PHASE 7.3 REAL CLEANING TEST")
    print("=" * 100)

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
        "\nPHASE 7.3 KNOWLEDGE CLEANING: PASS"
    )


if __name__ == "__main__":
    main()