from pathlib import Path
import json

from processors.knowledge_structurer import KnowledgeStructurer


# ============================================================
# PHASE 7.4 — REAL KNOWLEDGE STRUCTURE TEST
# ============================================================

TEST_DOCUMENTS = [
    {
        "markdown": Path(
            "storage/knowledge/iitj.ac.in/others/search.md"
        ),
        "metadata": Path(
            "storage/knowledge/iitj.ac.in/others/search.json"
        ),
        "name": "IITJ webpage",
    },
    {
        "markdown": Path(
            "storage/knowledge/gwpgc.ac.in/others/"
            "government_girls_p_g_college_ghazipur.md"
        ),
        "metadata": Path(
            "storage/knowledge/gwpgc.ac.in/others/"
            "government_girls_p_g_college_ghazipur.json"
        ),
        "name": "GWPGC webpage",
    },
    {
        "markdown": Path(
            "storage/knowledge/home.iitd.ac.in/others/"
            "newsletter-apr-26-issue.md"
        ),
        "metadata": Path(
            "storage/knowledge/home.iitd.ac.in/others/"
            "newsletter-apr-26-issue.json"
        ),
        "name": "IIT Delhi PDF",
    },
]


# ============================================================
# TEST
# ============================================================

def test_document(
    structurer: KnowledgeStructurer,
    document: dict,
):

    markdown_path = document["markdown"]
    metadata_path = document["metadata"]
    name = document["name"]

    print("\n" + "=" * 100)
    print(f"TESTING: {name}")
    print("=" * 100)

    assert markdown_path.exists(), (
        f"Markdown missing: {markdown_path}"
    )

    assert metadata_path.exists(), (
        f"Metadata missing: {metadata_path}"
    )

    output_path, _ = structurer.structure(
        markdown_path=markdown_path,
        metadata_path=metadata_path,
    )

    assert output_path.exists(), (
        f"Structured output missing: {output_path}"
    )

    structured = json.loads(
        output_path.read_text(
            encoding="utf-8"
        )
    )

    assert "document" in structured

    assert "pages" in structured

    assert isinstance(
        structured["pages"],
        list,
    )

    assert len(
        structured["pages"]
    ) >= 1

    document_data = structured["document"]

    assert (
        document_data.get("url")
    ), "Source URL missing"

    total_sections = sum(
        len(page["sections"])
        for page in structured["pages"]
    )

    assert total_sections >= 1

    print(
        "Structured JSON :",
        output_path,
    )

    print(
        "Pages           :",
        len(structured["pages"]),
    )

    print(
        "Sections        :",
        total_sections,
    )

    print(
        "Source URL      :",
        document_data["url"],
    )

    print("PASS")


# ============================================================
# MAIN
# ============================================================

def main():

    structurer = KnowledgeStructurer()

    passed = 0

    for document in TEST_DOCUMENTS:

        test_document(
            structurer,
            document,
        )

        passed += 1

    print("\n" + "=" * 100)
    print("PHASE 7.4 REAL STRUCTURE TEST")
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
        "\nPHASE 7.4 KNOWLEDGE STRUCTURE: PASS"
    )


if __name__ == "__main__":
    main()
