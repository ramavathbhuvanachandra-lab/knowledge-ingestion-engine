"""
Command 4 V2 — REAL IITJ FULL 855 TEST

Purpose
-------
Run the existing Command 4 V2 organizer against ALL Command-3 accepted
IIT Jodhpur units (A + B + REVIEW).

This script does NOT modify the organizer.
It does NOT include C or D units.
It writes only to storage_v2/command4/iitj/.

The upstream Command-3 decision is reconstructed using the project's existing
KnowledgeValueFilter so the runner remains aligned with the frozen Command 3
policy.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

STRUCTURED_ROOT = (
    PROJECT_ROOT
    / "storage"
    / "structured_knowledge"
)

DOMAIN = "www.iitj.ac.in"

INPUT_UNITS = (
    PROJECT_ROOT
    / "storage"
    / "test6_iitj_knowledge_units.json"
)

OUTPUT_ROOT = (
    PROJECT_ROOT
    / "storage_v2"
    / "command4"
    / "iitj"
)


def _ensure_project_imports() -> None:
    """Allow this script to be run directly from the repository root."""
    project_root = str(PROJECT_ROOT)

    if project_root not in sys.path:
        sys.path.insert(0, project_root)


_ensure_project_imports()

from processors.knowledge_organization_v2 import Command4OrganizationV2
from processors.knowledge_value_filter import KnowledgeValueFilter


ALLOWED_TIERS = {"A", "B", "REVIEW"}


def load_json(path: Path):
    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def _classify_unit(
    value_filter: KnowledgeValueFilter,
    unit: dict,
) -> str:
    """
    Reconstruct the frozen Command-3 decision for one normalized unit.

    The structured unit contains the original heading/content and source
    metadata. Command 4 only accepts A/B/REVIEW.
    """
    heading = str(
        unit.get("heading", "")
    )

    text = str(
        unit.get(
            "text",
            unit.get(
                "content",
                "",
            ),
        )
    )

    source_file = str(
        unit.get(
            "source_file",
            "",
        )
    )

    source_title = str(
        unit.get(
            "source_title",
            "",
        )
    )

    source_url = str(
        unit.get(
            "source_url",
            unit.get(
                "url",
                "",
            ),
        )
    )

    content_type = str(
        unit.get(
            "source_document_type",
            unit.get(
                "content_type",
                "",
            ),
        )
    )

    section_path = unit.get(
        "section_path",
        [],
    )

    if not isinstance(
        section_path,
        list,
    ):
        section_path = []

    result = value_filter.classify(
        heading=heading,
        text=text,
        source_name=(
            Path(source_file).name
            if source_file
            else ""
        ),
        document_title=source_title,
        document_url=source_url,
        content_type=content_type,
        section_path=section_path,
    )

    return str(
        result.get(
            "tier",
            result.get(
                "classification",
                result.get(
                    "decision",
                    "",
                ),
            ),
        )
    ).strip().upper()


def normalize_units(
    units: list[dict],
) -> list[dict]:
    """Normalize the real-unit list for Command 4 input."""
    normalized = []

    for raw in units:
        unit = dict(raw)

        unit["unit_id"] = str(
            unit.get(
                "unit_id",
                "",
            )
        ).strip()

        unit["heading"] = str(
            unit.get(
                "heading",
                unit.get(
                    "title",
                    "",
                ),
            )
        ).strip()

        unit["text"] = str(
            unit.get(
                "text",
                unit.get(
                    "content",
                    "",
                ),
            )
        ).strip()

        unit["source_file"] = str(
            unit.get(
                "source_file",
                "",
            )
        ).strip()

        unit["source_url"] = str(
            unit.get(
                "source_url",
                unit.get(
                    "url",
                    "",
                ),
            )
        ).strip()

        unit["source_title"] = str(
            unit.get(
                "source_title",
                "",
            )
        ).strip()

        normalized.append(unit)

    return normalized


def main() -> None:
    print("=" * 100)
    print("COMMAND 4 V2 — REAL IITJ FULL 855 TEST")
    print("=" * 100)
    print()
    print(
        "Structured root :",
        STRUCTURED_ROOT,
    )
    print(
        "Input units     :",
        INPUT_UNITS,
    )
    print(
        "Domain          :",
        DOMAIN,
    )
    print(
        "Output root     :",
        OUTPUT_ROOT,
    )
    print()

    if not INPUT_UNITS.exists():
        raise FileNotFoundError(
            f"Missing normalized IITJ units: {INPUT_UNITS}"
        )

    # ------------------------------------------------------------------
    # Load all normalized units from the existing real IITJ corpus.
    # ------------------------------------------------------------------
    raw_units = load_json(INPUT_UNITS)

    if not isinstance(raw_units, list):
        raise ValueError(
            "Expected test6_iitj_knowledge_units.json to contain a list."
        )

    units = normalize_units(raw_units)

    print(
        "Normalized units extracted:",
        len(units),
    )
    print()

    # ------------------------------------------------------------------
    # Reconstruct the frozen Command-3 value decision for every unit.
    # ------------------------------------------------------------------
    value_filter = KnowledgeValueFilter()

    tiered_units: list[tuple[str, dict]] = []
    tier_counts = Counter()

    classification_failures = []

    for unit in units:
        try:
            tier = _classify_unit(
                value_filter,
                unit,
            )
        except Exception as exc:
            classification_failures.append(
                {
                    "unit_id": unit.get("unit_id"),
                    "error": repr(exc),
                }
            )
            continue

        tier_counts[tier] += 1
        tiered_units.append(
            (
                tier,
                unit,
            )
        )

    print("Command 3 tier counts:")
    for tier in (
        "A",
        "B",
        "REVIEW",
        "C",
        "D",
    ):
        print(
            f"  {tier:<6}:",
            tier_counts.get(
                tier,
                0,
            ),
        )

    if classification_failures:
        print()
        print(
            "Command 3 classification failures:",
            len(classification_failures),
        )

        for failure in classification_failures[:20]:
            print(
                "  -",
                failure,
            )

        raise RuntimeError(
            "Command 3 classification failed for one or more units."
        )

    # ------------------------------------------------------------------
    # Hard Command-4 boundary: ONLY A/B/REVIEW.
    # ------------------------------------------------------------------
    accepted_units = [
        unit
        for tier, unit in tiered_units
        if tier in ALLOWED_TIERS
    ]

    print()
    print(
        "Command 4 input (A+B+REVIEW):",
        len(accepted_units),
        "units",
    )

    if len(accepted_units) != (
        tier_counts.get("A", 0)
        + tier_counts.get("B", 0)
        + tier_counts.get("REVIEW", 0)
    ):
        raise AssertionError(
            "Accepted-unit count does not match A+B+REVIEW totals."
        )

    if len(accepted_units) != 855:
        raise AssertionError(
            "Expected exactly 855 Command-4-eligible IITJ units, "
            f"but found {len(accepted_units)}."
        )

    # Make the Command-3 tier available to the organizer.
    for tier, unit in tiered_units:
        if tier in ALLOWED_TIERS:
            unit["tier"] = tier

    # ------------------------------------------------------------------
    # Run Command 4 on ALL 855 accepted units.
    # ------------------------------------------------------------------
    organizer = Command4OrganizationV2()

    OUTPUT_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    manifest = organizer.write_output(
        domain=DOMAIN,
        units=accepted_units,
        output_root=OUTPUT_ROOT,
    )

    # ------------------------------------------------------------------
    # Report.
    # ------------------------------------------------------------------
    documents = manifest.get(
        "documents",
        [],
    )

    unit_count = manifest.get(
        "unit_count",
        len(accepted_units),
    )

    document_count = manifest.get(
        "document_count",
        0,
    )

    print()
    print("=" * 100)
    print("COMMAND 4 V2 — FULL IITJ TEST COMPLETE")
    print("=" * 100)
    print(
        "Documents created :",
        document_count,
    )
    print(
        "Units organized   :",
        unit_count,
    )

    if unit_count != 855:
        raise AssertionError(
            "Command 4 manifest did not organize all 855 accepted units."
        )

    coverage = manifest.get(
        "coverage",
        {},
    )

    missing = coverage.get(
        "missing_unit_ids",
        [],
    )

    unassigned = coverage.get(
        "unassigned_unit_ids",
        [],
    )

    duplicates = coverage.get(
        "duplicate_unit_ids",
        [],
    )

    extra = coverage.get(
        "extra_unit_ids",
        [],
    )

    print()
    print("Coverage:")
    print(
        "  Missing    :",
        len(missing),
    )
    print(
        "  Unassigned :",
        len(unassigned),
    )
    print(
        "  Duplicate  :",
        len(duplicates),
    )
    print(
        "  Extra      :",
        len(extra),
    )

    if (
        missing
        or unassigned
        or duplicates
        or extra
    ):
        raise AssertionError(
            "Command 4 full IITJ run has coverage problems."
        )

    print()
    print(
        "Output directory:",
        OUTPUT_ROOT,
    )

    # ------------------------------------------------------------------
    # Print generated Markdown files when available.
    # ------------------------------------------------------------------
    output_domain_root = (
        OUTPUT_ROOT
        / DOMAIN.replace(
            ".",
            "_",
        )
    )

    if output_domain_root.exists():
        markdown_files = sorted(
            output_domain_root.rglob(
                "*.md"
            )
        )

        print()
        print(
            "Generated Markdown files:"
        )

        for path in markdown_files:
            print(
                "  -",
                path.relative_to(
                    OUTPUT_ROOT
                ),
            )

        print()
        print(
            "Generated JSON files:"
        )

        for path in sorted(
            output_domain_root.rglob(
                "*.json"
            )
        ):
            print(
                "  -",
                path.relative_to(
                    OUTPUT_ROOT
                ),
            )

    print()
    print("=" * 100)
    print(
        "FULL IITJ 855-UNIT COMMAND 4 TEST PASSED"
    )
    print("=" * 100)


if __name__ == "__main__":
    main()