from pathlib import Path

from processors.knowledge_cleaner import KnowledgeCleaner


TEST_FILES = [
    (
        "storage/output/www.iitj.ac.in/research/office_of_research_development.md",
        "storage/output/www.iitj.ac.in/research/office_of_research_development.json",
    ),
    (
        "storage/output/www.iitj.ac.in/faculty/faculty_members.md",
        "storage/output/www.iitj.ac.in/faculty/faculty_members.json",
    ),
    (
        "storage/output/www.iitj.ac.in/others/campus_infrastructure.md",
        "storage/output/www.iitj.ac.in/others/campus_infrastructure.json",
    ),
    (
        "storage/output/www.iitj.ac.in/admissions/admission_to_postgraduate_programs.md",
        "storage/output/www.iitj.ac.in/admissions/admission_to_postgraduate_programs.json",
    ),
    (
        "storage/output/www.iitj.ac.in/others/administrative_contact.md",
        "storage/output/www.iitj.ac.in/others/administrative_contact.json",
    ),
    (
        "storage/output/www.iitj.ac.in/pdf/website-research-projects-638772906605230764.md",
        "storage/output/www.iitj.ac.in/pdf/website-research-projects-638772906605230764.json",
    ),
]


def main():

    cleaner = KnowledgeCleaner(
        output_path="storage/knowledge"
    )

    for markdown_path, metadata_path in TEST_FILES:

        markdown_path = Path(markdown_path)
        metadata_path = Path(metadata_path)

        print("\n" + "=" * 100)
        print("TESTING")
        print("=" * 100)

        print("Input Markdown :", markdown_path)
        print("Input Metadata :", metadata_path)

        if not markdown_path.exists():
            print("SKIPPED: Markdown file does not exist")
            continue

        if not metadata_path.exists():
            print("SKIPPED: Metadata file does not exist")
            continue

        output_markdown, output_metadata = cleaner.clean(
            markdown_path,
            metadata_path,
        )

        original_size = markdown_path.stat().st_size
        cleaned_size = output_markdown.stat().st_size

        if original_size:
            reduction = (
                (original_size - cleaned_size)
                / original_size
            ) * 100
        else:
            reduction = 0

        print("Cleaned Markdown :", output_markdown)
        print("Cleaned Metadata :", output_metadata)

        print(
            f"Original bytes : {original_size}"
        )

        print(
            f"Cleaned bytes  : {cleaned_size}"
        )

        print(
            f"Reduction      : {reduction:.2f}%"
        )

        print("STATUS         : PASS")


if __name__ == "__main__":
    main()