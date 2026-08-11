from pathlib import Path

from processors.knowledge_section_extractor import (
    KnowledgeSectionExtractor,
)


TEST_DOCUMENTS = [
    Path(
        "storage/knowledge/"
        "iitj.ac.in/others/search.md"
    ),
    Path(
        "storage/knowledge/"
        "gwpgc.ac.in/others/"
        "government_girls_p_g_college_ghazipur.md"
    ),
    Path(
        "storage/knowledge/"
        "home.iitd.ac.in/others/"
        "newsletter-apr-26-issue.md"
    ),
]


def test_document(
    extractor: KnowledgeSectionExtractor,
    path: Path,
):

    print()
    print("=" * 90)
    print("DOCUMENT")
    print("=" * 90)

    print("Input:", path)

    assert path.exists(), (
        f"Input Markdown missing: {path}"
    )

    sections = extractor.extract(path)

    print("Sections:", len(sections))

    assert sections, (
        f"No sections extracted: {path}"
    )

    for index, section in enumerate(
        sections[:10],
        start=1,
    ):

        print()
        print("-" * 90)
        print("SECTION:", index)
        print("Heading:", section["heading"])
        print("Level:", section["level"])
        print(
            "Characters:",
            section["character_count"],
        )
        print(
            "Lines:",
            section["start_line"],
            "-",
            section["end_line"],
        )

        print("Text:")
        print(
            section["text"][:500]
        )

    print()
    print("PASS")


def main():

    print()
    print("=" * 90)
    print("PHASE 8.2.1 — KNOWLEDGE SECTION EXTRACTION")
    print("=" * 90)

    extractor = KnowledgeSectionExtractor()

    passed = 0

    for document in TEST_DOCUMENTS:

        test_document(
            extractor,
            document,
        )

        passed += 1

    print()
    print("=" * 90)
    print(
        "Documents passed:",
        passed,
        "/",
        len(TEST_DOCUMENTS),
    )
    print(
        "PHASE 8.2.1 KNOWLEDGE SECTION EXTRACTION: PASS"
    )
    print("=" * 90)


if __name__ == "__main__":
    main()
