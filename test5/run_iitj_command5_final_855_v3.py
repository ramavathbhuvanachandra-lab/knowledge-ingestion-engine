"""
IIT Jodhpur — Final Command 5 Real 855 Runner V3
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_UNITS = PROJECT_ROOT / "storage" / "test6_iitj_knowledge_units.json"
OUTPUT_ROOT = PROJECT_ROOT / "storage_v2" / "command5" / "iitj_final"
ALLOWED_TIERS = {"A", "B", "REVIEW"}

sys.path.insert(0, str(PROJECT_ROOT))

from processors_v2.knowledge_organization_iitj_final import IITJKnowledgeOrganizerV2
from processors.knowledge_value_filter import KnowledgeValueFilter


def classify(vf, unit):
    result = vf.classify(
        heading=str(unit.get("heading", "")),
        text=str(unit.get("text", unit.get("content", ""))),
        source_name=Path(str(unit.get("source_file", ""))).name,
        document_title=str(unit.get("source_title", "")),
        document_url=str(unit.get("source_url", unit.get("url", ""))),
        content_type=str(unit.get("source_document_type", unit.get("content_type", ""))),
        section_path=unit.get("section_path", [])
        if isinstance(unit.get("section_path", []), list) else [],
    )
    return str(
        result.get("tier", result.get("classification", result.get("decision", "")))
    ).strip().upper()


def main():
    print("=" * 100)
    print("IIT JODHPUR — FINAL COMMAND 5 ORGANIZER — FULL 855")
    print("=" * 100)
    print()

    units = json.loads(INPUT_UNITS.read_text(encoding="utf-8"))
    vf = KnowledgeValueFilter()
    tier_counts = Counter()
    accepted = []

    for raw in units:
        unit = dict(raw)
        tier = classify(vf, unit)
        tier_counts[tier] += 1
        if tier in ALLOWED_TIERS:
            unit["tier"] = tier
            accepted.append(unit)

    print("Normalized units:", len(units))
    print()
    print("Command 3 tiers:")
    for tier in ("A", "B", "REVIEW", "C", "D"):
        print(f"  {tier:<6}: {tier_counts.get(tier, 0)}")
    print()
    print("Command 5 accepted input:", len(accepted))

    if len(accepted) != 855:
        raise AssertionError(f"Expected 855 A/B/REVIEW units, got {len(accepted)}")

    manifest = IITJKnowledgeOrganizerV2().write_output(
        units=accepted, output_root=OUTPUT_ROOT
    )
    coverage = manifest["coverage"]

    print()
    print("=" * 100)
    print("IITJ FINAL COMMAND 5 COMPLETE")
    print("=" * 100)
    print("Documents created:", manifest["document_count"])
    print("Units organized:", manifest["unit_count"])
    print()
    print("Coverage:")
    for label, key in (
        ("Missing", "missing_unit_ids"),
        ("Unassigned", "unassigned_unit_ids"),
        ("Duplicate", "duplicate_unit_ids"),
        ("Extra", "extra_unit_ids"),
    ):
        print(f"  {label:<11}:", len(coverage[key]))

    if any(coverage[k] for k in (
        "missing_unit_ids", "unassigned_unit_ids",
        "duplicate_unit_ids", "extra_unit_ids"
    )):
        raise AssertionError("Lossless coverage failed.")

    print()
    print("Output:", OUTPUT_ROOT)
    print()
    print("Top-level folders:")
    for p in sorted(OUTPUT_ROOT.iterdir()):
        if p.is_dir():
            print("  -", p.name)

    print()
    print("=" * 100)
    print("FULL IITJ FINAL COMMAND 5 TEST PASSED")
    print("=" * 100)


if __name__ == "__main__":
    main()