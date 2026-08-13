from pathlib import Path

from processors.knowledge_section_extractor import (
    KnowledgeSectionExtractor,
)

from processors.knowledge_content_triage import (
    KnowledgeContentTriage,
)


# ============================================================
# REAL TEST DOCUMENTS
# ============================================================

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


# ============================================================
# TEST ONE DOCUMENT
# ============================================================

def test_document(
    extractor: KnowledgeSectionExtractor,
    triage: KnowledgeContentTriage,
    path: Path,
) -> None:

    print()
    print("=" * 100)
    print("DOCUMENT")
    print("=" * 100)

    print("Input:", path)

    # --------------------------------------------------------
    # INPUT VALIDATION
    # --------------------------------------------------------

    assert path.exists(), (
        f"Markdown file does not exist: {path}"
    )

    assert path.is_file(), (
        f"Markdown path is not a file: {path}"
    )

    # --------------------------------------------------------
    # EXTRACT SECTIONS
    # --------------------------------------------------------

    sections = extractor.extract(
        path
    )

    assert isinstance(
        sections,
        list,
    ), (
        f"Extractor must return a list: {path}"
    )

    print(
        "Extracted sections:",
        len(sections),
    )

    # --------------------------------------------------------
    # TRIAGE
    # --------------------------------------------------------

    results = triage.classify_all(
        sections
    )

    assert isinstance(
        results,
        list,
    ), (
        f"Triage must return a list: {path}"
    )

    assert len(results) == len(
        sections
    ), (
        f"Triage count mismatch: {path}"
    )

    # --------------------------------------------------------
    # COUNTS
    # --------------------------------------------------------

    counts = {
        "KEEP": 0,
        "NOISE": 0,
        "REVIEW": 0,
    }

    for result in results:

        assert isinstance(
            result,
            dict,
        ), (
            f"Invalid triage result: {path}"
        )

        assert "heading" in result
        assert "text" in result
        assert "triage" in result

        decision = result[
            "triage"
        ].get(
            "decision"
        )

        assert decision in counts, (
            f"Invalid decision '{decision}' "
            f"in {path}"
        )

        reasons = result[
            "triage"
        ].get(
            "reasons"
        )

        assert isinstance(
            reasons,
            list,
        ), (
            f"Triage reasons must be a list: {path}"
        )

        counts[decision] += 1

    # --------------------------------------------------------
    # COUNT INTEGRITY
    #
    # A document is allowed to have:
    #
    #   0 KEEP
    #   0 REVIEW
    #   all NOISE
    #
    # Example:
    # IITJ Search page.
    # --------------------------------------------------------

    assert (
        counts["KEEP"]
        + counts["NOISE"]
        + counts["REVIEW"]
        == len(results)
    ), (
        f"Triage counts do not match "
        f"section count: {path}"
    )

    # --------------------------------------------------------
    # PRINT SUMMARY
    # --------------------------------------------------------

    print()
    print(
        "TOTAL SECTIONS :",
        len(results),
    )

    print(
        "KEEP           :",
        counts["KEEP"],
    )

    print(
        "NOISE          :",
        counts["NOISE"],
    )

    print(
        "REVIEW         :",
        counts["REVIEW"],
    )

    # --------------------------------------------------------
    # PRINT EVERY DECISION
    # --------------------------------------------------------

    print()
    print("-" * 100)
    print("SECTION DECISIONS")
    print("-" * 100)

    for index, result in enumerate(
        results,
        start=1,
    ):

        triage_data = result[
            "triage"
        ]

        decision = triage_data[
            "decision"
        ]

        reasons = triage_data[
            "reasons"
        ]

        print()
        print(
            f"[{index:02d}] {decision}"
        )

        print(
            "Heading:",
            result.get(
                "heading"
            ),
        )

        print(
            "Level:",
            result.get(
                "level"
            ),
        )

        print(
            "Characters:",
            result.get(
                "character_count"
            ),
        )

        print(
            "Lines:",
            result.get(
                "start_line"
            ),
            "-",
            result.get(
                "end_line"
            ),
        )

        print(
            "Reason:",
            "; ".join(reasons),
        )

        preview = (
            result.get(
                "text",
                "",
            )
            .replace(
                "\n",
                " ",
            )
        )

        print(
            "Preview:",
            preview[:250],
        )

    print()
    print("PASS")


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 100)
    print(
        "PHASE 8.2.2 — KNOWLEDGE CONTENT TRIAGE"
    )
    print("=" * 100)

    extractor = (
        KnowledgeSectionExtractor()
    )

    triage = (
        KnowledgeContentTriage()
    )

    passed = 0

    # --------------------------------------------------------
    # TEST ALL REAL DOCUMENTS
    # --------------------------------------------------------

    for document in TEST_DOCUMENTS:

        test_document(
            extractor=extractor,
            triage=triage,
            path=document,
        )

        passed += 1

    # --------------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------------

    print()
    print("=" * 100)

    print(
        "Documents passed:",
        passed,
        "/",
        len(TEST_DOCUMENTS),
    )

    assert passed == len(
        TEST_DOCUMENTS
    ), (
        "One or more documents failed"
    )

    print()
    print(
        "PHASE 8.2.2 "
        "KNOWLEDGE CONTENT TRIAGE: PASS"
    )

    print("=" * 100)


if __name__ == "__main__":
    main()
