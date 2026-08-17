from pathlib import Path

from processors.knowledge_organization_validator import (
    KnowledgeOrganizationValidator,
)


TEST_DOCUMENTS = [
    (
        Path(
            "storage/knowledge/"
            "iitj.ac.in/others/search.md"
        ),
        Path(
            "storage/organized_knowledge/"
            "iitj.ac.in"
        ),
    ),
    (
        Path(
            "storage/knowledge/"
            "gwpgc.ac.in/others/"
            "government_girls_p_g_college_ghazipur.md"
        ),
        Path(
            "storage/organized_knowledge/"
            "gwpgc.ac.in"
        ),
    ),
    (
        Path(
            "storage/knowledge/"
            "home.iitd.ac.in/others/"
            "newsletter-apr-26-issue.md"
        ),
        Path(
            "storage/organized_knowledge/"
            "home.iitd.ac.in"
        ),
    ),
]


def test_document(
    validator: KnowledgeOrganizationValidator,
    canonical_path: Path,
    organized_root: Path,
) -> None:

    print()
    print("=" * 100)
    print("VALIDATING ORGANIZED KNOWLEDGE")
    print("=" * 100)

    print(
        "Canonical :",
        canonical_path,
    )

    print(
        "Organized :",
        organized_root,
    )

    result = validator.validate(
        canonical_path=canonical_path,
        organized_root=organized_root,
    )

    print()
    print(
        "Domain                 :",
        result["domain"],
    )

    print(
        "Canonical sections     :",
        result["canonical_sections"],
    )

    print(
        "Organized sections     :",
        result["organized_sections"],
    )

    print(
        "Expected sections      :",
        result["expected_sections"],
    )

    print(
        "Missing sections       :",
        result["missing_sections"],
    )

    print(
        "Unexpected sections    :",
        result["unexpected_sections"],
    )

    print(
        "Duplicate sections     :",
        result["duplicate_sections"],
    )

    print(
        "Noise in output        :",
        result["noise_in_output"],
    )

    print(
        "Review sections        :",
        result["review_sections"],
    )

    print(
        "Other sections         :",
        result["other_sections"],
    )

    print()
    print("CATEGORY FILES")

    for category, count in (
        result["category_files"].items()
    ):

        print(
            f"{category:22s}: {count}"
        )

    # --------------------------------------------------------
    # ERRORS
    # --------------------------------------------------------

    print()
    print("ERRORS")

    for error in result["errors"]:
        print(
            "-",
            error,
        )

    # --------------------------------------------------------
    # WARNINGS
    # --------------------------------------------------------

    print()
    print("WARNINGS")

    for warning in result["warnings"]:
        print(
            "-",
            warning,
        )

    # --------------------------------------------------------
    # FINAL ASSERTION
    # --------------------------------------------------------

    assert result["valid"], (
        "Knowledge organization validation failed"
    )

    assert (
        result["missing_sections"] == 0
    )

    assert (
        result["unexpected_sections"] == 0
    )

    assert (
        result["duplicate_sections"] == 0
    )

    assert (
        result["noise_in_output"] == 0
    )

    print()
    print("PASS")


def main():

    print()
    print("=" * 100)
    print(
        "PHASE 8.4 — KNOWLEDGE ORGANIZATION VALIDATION"
    )
    print("=" * 100)

    validator = (
        KnowledgeOrganizationValidator()
    )

    passed = 0

    for canonical_path, organized_root in (
        TEST_DOCUMENTS
    ):

        test_document(
            validator=validator,
            canonical_path=canonical_path,
            organized_root=organized_root,
        )

        passed += 1

    print()
    print("=" * 100)

    print(
        "Documents passed:",
        passed,
        "/",
        len(TEST_DOCUMENTS),
    )

    assert (
        passed
        == len(TEST_DOCUMENTS)
    )

    print()
    print(
        "PHASE 8.4 "
        "KNOWLEDGE ORGANIZATION VALIDATION: PASS"
    )

    print("=" * 100)


if __name__ == "__main__":
    main()
