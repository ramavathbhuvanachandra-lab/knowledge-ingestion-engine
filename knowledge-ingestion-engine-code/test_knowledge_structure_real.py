import json
from pathlib import Path

from processors.knowledge_structurer import KnowledgeStructurer


# ============================================================
# PHASE 7.4 — REAL KNOWLEDGE STRUCTURE TEST
# ============================================================

BASE_KNOWLEDGE = Path(
    "storage/knowledge/iitj.ac.in"
)

OUTPUT_ROOT = Path(
    "storage/structured_knowledge"
)


TEST_DOCUMENTS = [
    {
        "name": "Office of Research & Development",
        "markdown": (
            BASE_KNOWLEDGE
            / "others"
            / "office_of_research_development.md"
        ),
        "metadata": (
            BASE_KNOWLEDGE
            / "others"
            / "office_of_research_development.json"
        ),
    },
]
TEST_DOCUMENTS = [
    {
        "name": "Office of Research & Development",
        "markdown": (
            BASE_KNOWLEDGE
            / "others"
            / "office_of_research_development.md"
        ),
        "metadata": (
            BASE_KNOWLEDGE
            / "others"
            / "office_of_research_development.json"
        ),
    },
    {
        "name": "IIT Delhi Newsletter — April 2026",
        "markdown": (
            Path(
                "storage/test_knowledge/"
                "home.iitd.ac.in/"
                "others/"
                "newsletter-apr-26-issue.md"
            )
        ),
        "metadata": (
            Path(
                "storage/test_processed_documents/"
                "home.iitd.ac.in/"
                "newsletter-apr-26-issue.json"
            )
        ),
    },
]


# ============================================================
# HELPERS
# ============================================================

def load_json(path: Path) -> dict:

    assert path.exists(), (
        f"Metadata file does not exist: {path}"
    )

    assert path.is_file(), (
        f"Metadata path is not a file: {path}"
    )

    data = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    assert isinstance(data, dict), (
        f"Metadata must be a JSON object: {path}"
    )

    return data


def load_markdown(path: Path) -> str:

    assert path.exists(), (
        f"Markdown file does not exist: {path}"
    )

    assert path.is_file(), (
        f"Markdown path is not a file: {path}"
    )

    text = path.read_text(
        encoding="utf-8"
    )

    assert text.strip(), (
        f"Markdown file is empty: {path}"
    )

    return text


def collect_sections(pages):

    sections = []

    for page_index, page in enumerate(
        pages,
        start=1,
    ):

        assert isinstance(
            page,
            dict,
        ), (
            f"Page #{page_index} must be an object"
        )

        page_sections = page.get(
            "sections"
        )

        assert page_sections is not None, (
            f"Page #{page_index} sections field missing"
        )

        assert isinstance(
            page_sections,
            list,
        ), (
            f"Page #{page_index} sections must be a list"
        )

        sections.extend(
            page_sections
        )

    return sections


# ============================================================
# SECTION VALIDATION
# ============================================================

def validate_section(section, index):

    assert isinstance(
        section,
        dict,
    ), (
        f"Section #{index} must be an object"
    )

    # --------------------------------------------------------
    # HEADING
    # --------------------------------------------------------

    heading = section.get(
        "heading"
    )

    # heading=None is valid for content that appears
    # before the first Markdown heading.
    if heading is not None:

        assert isinstance(
            heading,
            str,
        ), (
            f"Section #{index} heading must be "
            "a string or null"
        )

        assert heading.strip(), (
            f"Section #{index} heading cannot be empty"
        )

    # --------------------------------------------------------
    # LEVEL
    # --------------------------------------------------------

    level = section.get(
        "level"
    )

    assert level is not None, (
        f"Section #{index} level missing"
    )

    # Accept integer or numeric string.
    try:

        numeric_level = int(
            level
        )

    except (
        TypeError,
        ValueError,
    ):

        raise AssertionError(
            f"Section #{index} level must be numeric"
        )

    # Level 0 is valid for content that appears
    # before the first Markdown heading.
    assert numeric_level >= 0, (
        f"Section #{index} level must be >= 0"
    )

    # If a section has a heading, it should have
    # a normal Markdown heading level.
    if heading is not None:

        assert numeric_level >= 1, (
            f"Section #{index} headed section "
            "must have level >= 1"
        )

    # --------------------------------------------------------
    # CONTENT
    # --------------------------------------------------------

    content = section.get(
        "content"
    )

    assert content is not None, (
        f"Section #{index} content missing"
    )

    assert isinstance(
        content,
        list,
    ), (
        f"Section #{index} content must be a list"
    )

    for item_index, item in enumerate(
        content
    ):

        assert isinstance(
            item,
            str,
        ), (
            f"Section #{index} content item "
            f"#{item_index} must be string"
        )

    # --------------------------------------------------------
    # CONTENT LENGTH
    # --------------------------------------------------------

    content_length = section.get(
        "content_length"
    )

    assert content_length is not None, (
        f"Section #{index} content_length missing"
    )

    try:

        numeric_length = int(
            content_length
        )

    except (
        TypeError,
        ValueError,
    ):

        raise AssertionError(
            f"Section #{index} content_length "
            f"must be numeric"
        )

    assert numeric_length >= 0, (
        f"Section #{index} content_length "
        f"cannot be negative"
    )

    # --------------------------------------------------------
    # OPTIONAL CONTENT ITEMS
    # --------------------------------------------------------

    content_items = section.get(
        "content_items"
    )

    if content_items is not None:

        try:

            numeric_items = int(
                content_items
            )

        except (
            TypeError,
            ValueError,
        ):

            raise AssertionError(
                f"Section #{index} content_items "
                f"must be numeric"
            )

        assert numeric_items >= 0, (
            f"Section #{index} content_items "
            f"cannot be negative"
        )

        assert numeric_items == len(
            content
        ), (
            f"Section #{index} content_items "
            f"does not match content list length"
        )

    # --------------------------------------------------------
    # OPTIONAL CONTENT TYPE
    # --------------------------------------------------------

    content_type = section.get(
        "content_type"
    )

    if content_type is not None:

        assert isinstance(
            content_type,
            str,
        ), (
            f"Section #{index} content_type "
            f"must be string"
        )


# ============================================================
# DOCUMENT TEST
# ============================================================

def test_document(
    structurer,
    document,
):

    name = document["name"]

    markdown_path = Path(
        document["markdown"]
    )

    metadata_path = Path(
        document["metadata"]
    )

    print()
    print("=" * 100)
    print(
        "TESTING:",
        name,
    )
    print("=" * 100)

    print(
        "Input Markdown :",
        markdown_path,
    )

    print(
        "Input Metadata :",
        metadata_path,
    )

    # --------------------------------------------------------
    # LOAD INPUTS
    # --------------------------------------------------------

    markdown = load_markdown(
        markdown_path
    )

    metadata = load_json(
        metadata_path
    )

    # --------------------------------------------------------
    # STRUCTURE DOCUMENT
    # --------------------------------------------------------

    result = structurer.structure(
        markdown_path=markdown_path,
        metadata_path=metadata_path,
    )

    assert result is not None, (
        f"Structurer returned None: {name}"
    )

    # --------------------------------------------------------
    # RESOLVE OUTPUT PATH
    # --------------------------------------------------------

    if isinstance(
        result,
        tuple,
    ):

        assert len(result) >= 1, (
            f"Invalid structurer result: {name}"
        )

        output_path = Path(
            result[0]
        )

    else:

        output_path = Path(
            result
        )

    assert output_path.exists(), (
        f"Structured output missing: "
        f"{output_path}"
    )

    assert output_path.is_file(), (
        f"Structured output is not a file: "
        f"{output_path}"
    )

    print(
        "Structured JSON :",
        output_path,
    )

    # --------------------------------------------------------
    # LOAD STRUCTURED JSON
    # --------------------------------------------------------

    structured = json.loads(
        output_path.read_text(
            encoding="utf-8"
        )
    )

    assert isinstance(
        structured,
        dict,
    ), (
        "Structured output must be JSON object"
    )

    # --------------------------------------------------------
    # DOCUMENT
    # --------------------------------------------------------

    document_data = structured.get(
        "document"
    )

    assert document_data is not None, (
        "document field missing"
    )

    assert isinstance(
        document_data,
        dict,
    ), (
        "document must be an object"
    )

    # --------------------------------------------------------
    # PAGES
    # --------------------------------------------------------

    pages = structured.get(
        "pages"
    )

    assert pages is not None, (
        "pages field missing"
    )

    assert isinstance(
        pages,
        list,
    ), (
        "pages must be a list"
    )

    assert pages, (
        "No pages produced"
    )

    # --------------------------------------------------------
    # VALIDATE PAGES
    # --------------------------------------------------------

    for page_index, page in enumerate(
        pages,
        start=1,
    ):

        assert isinstance(
            page,
            dict,
        ), (
            f"Page #{page_index} must be an object"
        )

        assert "page_number" in page, (
            f"Page #{page_index} page_number missing"
        )

        page_number = page.get(
            "page_number"
        )

        # Webpages may legitimately have no
        # explicit page number.
        if page_number is not None:

            try:

                numeric_page_number = int(
                    page_number
                )

            except (
                TypeError,
                ValueError,
            ):

                raise AssertionError(
                    f"Page #{page_index} "
                    "page_number must be numeric "
                    "or null"
                )

            assert numeric_page_number >= 1, (
                f"Page #{page_index} "
                "page_number must be >= 1"
            )

        assert "sections" in page, (
            f"Page #{page_index} sections missing"
        )

        assert isinstance(
            page["sections"],
            list,
        ), (
            f"Page #{page_index} sections "
            "must be a list"
        )

        assert page["sections"], (
            f"Page #{page_index} contains "
            "no sections"
        )

    # --------------------------------------------------------
    # COLLECT ALL SECTIONS
    # --------------------------------------------------------

    sections = collect_sections(
        pages
    )

    assert sections, (
        "No sections produced"
    )

    print(
        "Pages           :",
        len(pages),
    )

    print(
        "Sections        :",
        len(sections),
    )

    # --------------------------------------------------------
    # VALIDATE SECTIONS
    # --------------------------------------------------------

    for index, section in enumerate(
        sections,
        start=1,
    ):

        validate_section(
            section,
            index,
        )

    # --------------------------------------------------------
    # SOURCE URL
    # --------------------------------------------------------

    source_url = (
        document_data.get("url")
        or structured.get("source_url")
        or structured.get("url")
        or metadata.get("source_url")
        or metadata.get("url")
    )

    assert source_url, (
        "Structured document has no source URL"
    )

    assert isinstance(
        source_url,
        str,
    ), (
        "Structured source URL must be a string"
    )

    # --------------------------------------------------------
    # CONTENT PRESERVATION
    # --------------------------------------------------------
    #
    # Phase 7.4 must structure the cleaned content.
    # It should NOT aggressively destroy knowledge.
    #
    # We perform a lightweight preservation check.
    #
    # --------------------------------------------------------

    input_words = [
        word.lower().strip(
            ".,;:!?()[]{}\"'"
        )
        for word in markdown.split()
        if len(
            word.strip(
                ".,;:!?()[]{}\"'"
            )
        ) >= 5
    ]

    structured_parts = []

    for section in sections:

        heading = section.get(
            "heading"
        )

        if isinstance(
            heading,
            str,
        ):

            structured_parts.append(
                heading
            )

        content = section.get(
            "content",
            [],
        )

        if isinstance(
            content,
            list,
        ):

            structured_parts.extend(
                item
                for item in content
                if isinstance(
                    item,
                    str,
                )
            )

    structured_text = (
        "\n".join(
            structured_parts
        ).lower()
    )

    sample_words = input_words[:30]

    matched_words = sum(
        1
        for word in sample_words
        if word in structured_text
    )

    if sample_words:

        preservation_ratio = (
            matched_words
            / len(sample_words)
        )

        print(
            "Sample preservation:",
            f"{preservation_ratio:.1%}",
        )

        assert preservation_ratio > 0.30, (
            "Structured output appears to have "
            "lost too much source content"
        )

    # --------------------------------------------------------
    # SECTION SUMMARY
    # --------------------------------------------------------

    print()
    print(
        "FIRST SECTIONS"
    )
    print("-" * 100)

    for index, section in enumerate(
        sections[:10],
        start=1,
    ):

        heading = section.get(
            "heading",
            "",
        )

        level = section.get(
            "level",
            "",
        )

        content = section.get(
            "content",
            [],
        )

        print(
            f"{index:02d}. "
            f"[H{level}] "
            f"{heading}"
        )

        if content:

            preview = " ".join(
                str(item)
                for item in content[:2]
            )

            if len(preview) > 220:

                preview = (
                    preview[:220]
                    + "..."
                )

            print(
                "    ",
                preview,
            )

    print()
    print(
        "PASS:",
        name,
    )

    return output_path


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 100)
    print(
        "PHASE 7.4 — IITJ REAL KNOWLEDGE STRUCTURE TEST"
    )
    print("=" * 100)

    structurer = KnowledgeStructurer(
        output_path=OUTPUT_ROOT
    )

    passed = 0

    for document in TEST_DOCUMENTS:

        test_document(
            structurer,
            document,
        )

        passed += 1

    print()
    print("=" * 100)
    print(
        "PHASE 7.4 TEST RESULT"
    )
    print("=" * 100)

    print(
        "Documents tested :",
        len(TEST_DOCUMENTS),
    )

    print(
        "Documents passed :",
        passed,
    )

    assert passed == len(
        TEST_DOCUMENTS
    ), (
        "One or more documents failed"
    )

    print()
    print(
        "PHASE 7.4 REAL KNOWLEDGE STRUCTURE TEST: PASS"
    )
    print("=" * 100)


if __name__ == "__main__":
    main()