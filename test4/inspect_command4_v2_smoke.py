from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

INPUT = (
    ROOT
    / "storage"
    / "test6_iitj_knowledge_units.json"
)

SMOKE_MANIFEST = (
    ROOT
    / "storage_v2"
    / "tests"
    / "command4"
    / "iitj_smoke"
    / "www_iitj_ac_in"
    / "organization_manifest.json"
)

OUTPUT = (
    ROOT
    / "storage_v2"
    / "tests"
    / "command4"
    / "iitj_smoke"
    / "semantic_inspection_150.json"
)


def load_json(path: Path):
    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def main():
    print("=" * 90)
    print("COMMAND 4 V2 — 150 UNIT SEMANTIC INSPECTION")
    print("=" * 90)

    # ------------------------------------------------------------------
    # Load normalized Command 2 units.
    # ------------------------------------------------------------------

    units = load_json(INPUT)

    print()
    print(
        "Total normalized units:",
        len(units)
    )

    unit_by_id = {
        str(unit["unit_id"]): unit
        for unit in units
        if unit.get("unit_id")
    }

    # ------------------------------------------------------------------
    # Load the actual Command 4 manifest.
    #
    # IMPORTANT:
    # Current manifest stores per-unit assignment records under
    # manifest["units"], not manifest["documents"].
    # ------------------------------------------------------------------

    manifest = load_json(
        SMOKE_MANIFEST
    )

    manifest_units = manifest.get(
        "units",
        []
    )

    if not isinstance(
        manifest_units,
        list
    ):
        raise ValueError(
            "organization_manifest.json does not contain a valid 'units' list."
        )

    # ------------------------------------------------------------------
    # Build one inspection record per actual smoke-test assignment.
    # ------------------------------------------------------------------

    records = []

    for assignment in manifest_units:

        unit_id = str(
            assignment.get(
                "unit_id",
                ""
            )
        )

        if not unit_id:
            continue

        source_unit = unit_by_id.get(
            unit_id,
            {}
        )

        records.append(
            {
                "unit_id": unit_id,
                "heading": source_unit.get(
                    "heading",
                    ""
                ),
                "section_path": source_unit.get(
                    "section_path",
                    []
                ),
                "source_file": assignment.get(
                    "source_file",
                    source_unit.get(
                        "source_file",
                        ""
                    )
                ),
                "source_title": source_unit.get(
                    "source_title",
                    ""
                ),
                "source_url": assignment.get(
                    "source_url",
                    source_unit.get(
                        "source_url",
                        ""
                    )
                ),
                "tier": assignment.get(
                    "tier",
                    ""
                ),
                "document_id": assignment.get(
                    "document_id",
                    ""
                ),
                "output_path": assignment.get(
                    "path",
                    ""
                ),
                "content_sha256": assignment.get(
                    "content_sha256",
                    ""
                ),
            }
        )

    # ------------------------------------------------------------------
    # Save complete inspection report.
    # ------------------------------------------------------------------

    report = {
        "inspection": {
            "name": (
                "Command 4 V2 "
                "150-unit semantic inspection"
            ),
            "normalized_unit_count": len(
                units
            ),
            "manifest_assignment_count": len(
                records
            ),
            "expected_smoke_unit_count": manifest.get(
                "unit_count",
                0
            ),
        },
        "units": sorted(
            records,
            key=lambda item: (
                item["output_path"],
                item["unit_id"],
            ),
        ),
    }

    OUTPUT.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    # ------------------------------------------------------------------
    # Console summary.
    # ------------------------------------------------------------------

    print()
    print(
        "Smoke units inspected:",
        len(records)
    )

    print(
        "Manifest expected units:",
        manifest.get(
            "unit_count",
            0
        )
    )

    if len(records) != manifest.get(
        "unit_count",
        0
    ):
        raise ValueError(
            "Inspection count does not match "
            "Command 4 manifest unit_count."
        )

    print()
    print(
        "Inspection report:",
        OUTPUT
    )

    print()
    print("=" * 90)
    print(
        "UNIT → OUTPUT DOCUMENT SUMMARY"
    )
    print("=" * 90)

    for record in report["units"]:
        print(
            f"{record['unit_id']} | "
            f"{record['heading'][:70]} | "
            f"{record['tier']} | "
            f"{record['output_path']}"
        )


if __name__ == "__main__":
    main()