from pathlib import Path

from processors.retrieval_quality_validator import (
    RetrievalQualityValidator,
)


# ============================================================
# PHASE 7.8 — REAL RETRIEVAL QUALITY VALIDATION
# ============================================================

TEST_RETRIEVAL_FILES = [
    Path(
        "storage/retrieval/iitj.ac.in/others/search.json"
    ),
    Path(
        "storage/retrieval/gwpgc.ac.in/others/"
        "government_girls_p_g_college_ghazipur.json"
    ),
    Path(
        "storage/retrieval/home.iitd.ac.in/others/"
        "newsletter-apr-26-issue.json"
    ),
]


# ============================================================
# TEST ONE DATASET
# ============================================================

def test_retrieval_quality(
    validator: RetrievalQualityValidator,
    retrieval_path: Path,
) -> None:

    print("\n" + "=" * 100)
    print("VALIDATING RETRIEVAL QUALITY")
    print("=" * 100)

    print(
        "Input JSON :",
        retrieval_path
    )

    result = validator.validate(
        retrieval_path
    )

    print(
        "Records    :",
        result["record_count"]
    )

    print(
        "Errors     :",
        len(result["errors"])
    )

    print(
        "Warnings   :",
        len(result["warnings"])
    )

    print(
        "Valid      :",
        result["valid"]
    )

    quality = result["quality"]

    print("\nQUALITY")

    print(
        "Minimum size        :",
        quality["minimum_text_size"]
    )

    print(
        "Maximum size        :",
        quality["maximum_text_size"]
    )

    print(
        "Average size        :",
        quality["average_text_size"]
    )

    print(
        "Noise-heavy records :",
        quality["noise_heavy_records"]
    )

    print(
        "Empty records       :",
        quality["empty_records"]
    )

    print(
        "Duplicate IDs       :",
        quality["duplicate_record_ids"]
    )

    # --------------------------------------------------------
    # ERRORS
    # --------------------------------------------------------

    for error in result["errors"]:
        print(
            "ERROR:",
            error
        )

    # --------------------------------------------------------
    # WARNINGS
    # --------------------------------------------------------

    for warning in result["warnings"][:20]:
        print(
            "WARNING:",
            warning
        )

    if len(result["warnings"]) > 20:
        print(
            f"... "
            f"{len(result['warnings']) - 20} "
            f"more warnings"
        )

    # --------------------------------------------------------
    # FINAL ASSERTION
    # --------------------------------------------------------

    assert result["valid"], (
        f"Retrieval quality validation failed: "
        f"{retrieval_path}"
    )

    assert result["record_count"] > 0, (
        f"No retrieval records found: "
        f"{retrieval_path}"
    )

    print("PASS")


# ============================================================
# MAIN
# ============================================================

def main():

    validator = (
        RetrievalQualityValidator()
    )

    passed = 0

    for retrieval_path in (
        TEST_RETRIEVAL_FILES
    ):

        test_retrieval_quality(
            validator,
            retrieval_path,
        )

        passed += 1

    print("\n" + "=" * 100)

    print(
        f"Documents passed: "
        f"{passed} / "
        f"{len(TEST_RETRIEVAL_FILES)}"
    )

    assert passed == len(
        TEST_RETRIEVAL_FILES
    ), (
        "Some retrieval quality tests failed."
    )

    print(
        "PHASE 7.8 RETRIEVAL QUALITY "
        "VALIDATION: PASS"
    )


if __name__ == "__main__":
    main()