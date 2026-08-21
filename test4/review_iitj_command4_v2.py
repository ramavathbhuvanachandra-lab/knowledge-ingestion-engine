from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

IITJ_ROOT = (
    ROOT
    / "storage_v2"
    / "tests"
    / "command4"
    / "iitj_smoke"
    / "www_iitj_ac_in"
)

OUTPUT = (
    ROOT
    / "storage_v2"
    / "tests"
    / "command4"
    / "iitj_smoke"
    / "iitj_semantic_review.txt"
)


def main() -> None:
    if not IITJ_ROOT.exists():
        raise FileNotFoundError(
            f"Missing IITJ smoke output: {IITJ_ROOT}"
        )

    markdown_files = sorted(
        IITJ_ROOT.rglob("*.md")
    )

    print("=" * 90)
    print("IIT JODHPUR — COMMAND 4 V2 SEMANTIC REVIEW")
    print("=" * 90)
    print()
    print(f"Markdown documents: {len(markdown_files)}")
    print()

    lines = []

    for md_file in markdown_files:
        relative = md_file.relative_to(IITJ_ROOT)

        text = md_file.read_text(
            encoding="utf-8"
        )

        headings = [
            line.strip()
            for line in text.splitlines()
            if line.startswith("## ")
        ]

        source_lines = [
            line.strip()
            for line in text.splitlines()
            if line.startswith("source_files:")
            or line.startswith("source_urls:")
        ]

        lines.append("=" * 90)
        lines.append(
            f"FILE: {relative}"
        )
        lines.append(
            f"SIZE: {len(text.split())} words"
        )
        lines.append(
            f"SECTION COUNT: {len(headings)}"
        )
        lines.append("")

        lines.append("HEADINGS:")

        for heading in headings:
            lines.append(
                f"  {heading}"
            )

        lines.append("")

        if source_lines:
            lines.append(
                "SOURCE METADATA:"
            )

            for item in source_lines:
                lines.append(
                    f"  {item}"
                )

            lines.append("")

        lines.append("FIRST 20 CONTENT LINES:")

        content_lines = [
            line.rstrip()
            for line in text.splitlines()
            if line.strip()
            and not line.startswith("---")
            and not line.startswith("id:")
            and not line.startswith("title:")
            and not line.startswith("scope_type:")
            and not line.startswith("scope_id:")
            and not line.startswith("topic:")
            and not line.startswith("knowledge_family:")
            and not line.startswith("organization_version:")
            and not line.startswith("source_files:")
            and not line.startswith("source_urls:")
            and not line.startswith("unit_ids:")
        ]

        for line in content_lines[:20]:
            lines.append(
                f"  {line}"
            )

        lines.append("")

    OUTPUT.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    print(
        f"Review report written to:\n{OUTPUT}"
    )

    print()
    print("=" * 90)
    print("DOCUMENT SUMMARY")
    print("=" * 90)

    for md_file in markdown_files:
        relative = md_file.relative_to(
            IITJ_ROOT
        )

        text = md_file.read_text(
            encoding="utf-8"
        )

        headings = [
            line
            for line in text.splitlines()
            if line.startswith("## ")
        ]

        print(
            f"{relative} | "
            f"{len(text.split())} words | "
            f"{len(headings)} sections"
        )


if __name__ == "__main__":
    main()