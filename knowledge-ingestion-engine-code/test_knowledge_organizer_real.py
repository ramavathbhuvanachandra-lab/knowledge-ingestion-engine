from pathlib import Path
import shutil

from processors.knowledge_organizer import (
    KnowledgeOrganizer,
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


OUTPUT_PATH = Path(
    "storage/organized_knowledge"
)


def test_document(
    organizer: KnowledgeOrganizer,
    path: Path,
) -> None:

    print()
    print("=" * 100)
    print("TESTING KNOWLEDGE ORGANIZATION")
    print("=" * 100)

    print(
        "Input:",
        path,
    )

    assert path.exists(), (
        f"Input does not exist: {path}"
    )

    manifest = organizer.organize(
        path
    )

    assert isinstance(
        manifest,
        dict,
    )

    assert (
        manifest["source_document"]
        == str(path)
    )

    assert (
        manifest["domain"]
    )

    assert (
        manifest["total_sections"]
        >= 0
    )

    assert (
        manifest["organized_sections"]
        <= manifest["total_sections"]
    )

    # --------------------------------------------------------
    # OUTPUT ROOT
    # --------------------------------------------------------

    domain = manifest[
        "domain"
    ]

    domain_root = (
        OUTPUT_PATH
        / domain
    )

    assert domain_root.exists(), (
        f"Domain output missing: "
        f"{domain_root}"
    )

    # --------------------------------------------------------
    # MANIFEST
    # --------------------------------------------------------

    manifest_path = (
        domain_root
        / f"{path.stem}.organization.json"
    )

    assert manifest_path.exists(), (
        f"Manifest missing: "
        f"{manifest_path}"
    )

    # --------------------------------------------------------
    # CATEGORY COUNTS
    # --------------------------------------------------------

    counts = manifest[
        "categories"
    ]

    print()
    print("CATEGORY COUNTS")

    for category, count in counts.items():

        if count > 0:

            print(
                f"{category:20s}: {count}"
            )

            category_dir = (
                domain_root
                / category
            )

            assert category_dir.exists(), (
                f"Category directory missing: "
                f"{category_dir}"
            )

    # --------------------------------------------------------
    # WRITTEN FILES
    # --------------------------------------------------------

    written_files = manifest[
        "written_files"
    ]

    print()
    print(
        "Written files:",
        len(written_files),
    )

    for file_path in written_files:

        output_file = Path(
            file_path
        )

        assert output_file.exists(), (
            f"Output file missing: "
            f"{output_file}"
        )

        assert output_file.is_file(), (
            f"Output is not a file: "
            f"{output_file}"
        )

        content = (
            output_file.read_text(
                encoding="utf-8"
            )
        )

        assert content.strip(), (
            f"Output file is empty: "
            f"{output_file}"
        )

        print(
            "  ",
            output_file,
        )

    print()
    print(
        "Total sections:",
        manifest[
            "total_sections"
        ],
    )

    print(
        "Organized:",
        manifest[
            "organized_sections"
        ],
    )

    print(
        "PASS"
    )


def main():

    print()
    print("=" * 100)
    print(
        "PHASE 8.3 — KNOWLEDGE ORGANIZATION"
    )
    print("=" * 100)

    # --------------------------------------------------------
    # CLEAN ONLY GENERATED ORGANIZED OUTPUT
    #
    # NEVER TOUCH storage/knowledge.
    # --------------------------------------------------------

    if OUTPUT_PATH.exists():

        shutil.rmtree(
            OUTPUT_PATH
        )

    OUTPUT_PATH.mkdir(
        parents=True,
        exist_ok=True,
    )

    organizer = KnowledgeOrganizer(
        output_path=OUTPUT_PATH
    )

    passed = 0

    for document in TEST_DOCUMENTS:

        test_document(
            organizer=organizer,
            path=document,
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
        "PHASE 8.3 "
        "KNOWLEDGE ORGANIZATION: PASS"
    )

    print("=" * 100)


if __name__ == "__main__":
    main()
