
"""
Command 4 V2 — Real IITJ Smoke Test

Flow
----
Current Command 2 structured knowledge
    -> Frozen Command 3 classifier
    -> Keep ONLY A / B / REVIEW
    -> Command 4 V2
    -> storage/tests/command4/iitj_smoke/

This is ONLY a test/integration runner.

It never:
- modifies Command 3
- sends C/D into Command 4
- writes into production V2 storage
"""

from __future__ import annotations

import json
import shutil
import sys

from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Any


# ============================================================================
# Project root
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from processors.knowledge_organization_input import (
    StructuredKnowledgeInputAdapter,
)

from processors.knowledge_value_filter import KnowledgeValueFilter

from processors.knowledge_organization_v2 import Command4OrganizationV2


# ============================================================================
# Paths
# ============================================================================

STRUCTURED_ROOT = PROJECT_ROOT / "storage" / "structured_knowledge"

DOMAIN = "www.iitj.ac.in"

TEST_ROOT = (
    PROJECT_ROOT
    / "storage_v2"
    / "tests"
    / "command4"
    / "iitj_smoke"
)

ALLOWED_TIERS = {"A", "B", "REVIEW"}


# ============================================================================
# Command 3 Classification
# ============================================================================

def classify_units(
    units: list[Any],
) -> tuple[
    list[dict[str, Any]],
    Counter,
    dict[str, list[dict[str, Any]]],
]:

    value_filter = KnowledgeValueFilter()

    tier_counts: Counter = Counter()

    accepted_units: list[dict[str, Any]] = []

    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for unit in units:

        result = value_filter.classify(
            heading=str(unit.heading or ""),
            text=str(unit.content or ""),
            source_name=Path(str(unit.source_file or "")).name,
            document_title=str(unit.source_title or ""),
            document_url=str(unit.source_url or ""),
            content_type=str(unit.content_type or ""),
            section_path=[],
        )

        tier = str(
            result.get("tier", "")
        ).strip().upper()

        tier_counts[tier] += 1

        if tier not in ALLOWED_TIERS:
            continue

        payload = asdict(unit)

        # ------------------------------------------------------------
        # Preserve frozen Command 3 metadata.
        # Command 4 receives canonical `tier`.
        # ------------------------------------------------------------

        payload["tier"] = tier
        payload["value_tier"] = tier
        payload["value_decision"] = result.get("decision", "")
        payload["knowledge_family"] = result.get("knowledge_family", "")
        payload["value_confidence"] = result.get("confidence", "")
        payload["value_score"] = result.get("score", 0)
        payload["value_reasons"] = result.get("reasons", [])

        accepted_units.append(payload)

        by_source[
            str(unit.source_file)
        ].append(payload)

    return (
        accepted_units,
        tier_counts,
        by_source,
    )


# ============================================================================
# Source scoring helpers
# ============================================================================

def source_text(
    source_units: list[dict[str, Any]],
) -> str:

    parts: list[str] = []

    for unit in source_units:

        parts.extend(
            [
                str(unit.get("source_title", "")),
                str(unit.get("heading", "")),
                str(unit.get("content", "")),
                str(unit.get("knowledge_family", "")),
            ]
        )

    return " ".join(parts).lower()


def choose_source(
    by_source: dict[str, list[dict[str, Any]]],
    keywords: tuple[str, ...],
    used: set[str],
) -> str | None:

    candidates: list[
        tuple[int, int, str]
    ] = []

    for source, source_units in by_source.items():

        if source in used:
            continue

        text = source_text(source_units)

        hits = sum(
            1
            for keyword in keywords
            if keyword in text
        )

        if hits <= 0:
            continue

        content_size = sum(
            len(
                str(unit.get("content", ""))
            )
            for unit in source_units
        )

        candidates.append(
            (
                hits,
                content_size,
                source,
            )
        )

    candidates.sort(
        key=lambda item: (
            -item[0],
            -item[1],
            item[2],
        )
    )

    if not candidates:
        return None

    return candidates[0][2]


# ============================================================================
# Select representative real sources
# ============================================================================

def choose_smoke_sources(
    by_source: dict[str, list[dict[str, Any]]],
) -> list[str]:

    selected: list[str] = []

    used: set[str] = set()

    targets = (
        (
            "small_subject",
            (
                "hostel",
                "accommodation",
                "library",
                "student welfare",
                "student support",
                "contact",
                "medical",
            ),
        ),
        (
            "department_subject",
            (
                "department of",
                "department",
                "electrical engineering",
                "computer science",
                "mechanical engineering",
                "school of",
            ),
        ),
        (
            "large_subject",
            (
                "admission",
                "admissions",
                "undergraduate",
                "postgraduate",
                "phd",
                "mba",
                "b.tech",
                "m.tech",
                "program",
                "programme",
            ),
        ),
    )

    for _label, keywords in targets:

        chosen = choose_source(
            by_source,
            keywords,
            used,
        )

        if chosen is not None:

            selected.append(chosen)

            used.add(chosen)

    # ------------------------------------------------------------
    # Fill remaining slots with largest real sources.
    # ------------------------------------------------------------

    remaining = []

    for source, units in by_source.items():

        if source in used:
            continue

        size = sum(
            len(
                str(unit.get("content", ""))
            )
            for unit in units
        )

        remaining.append(
            (
                size,
                source,
            )
        )

    remaining.sort(
        key=lambda item: (
            -item[0],
            item[1],
        )
    )

    for _, source in remaining:

        if len(selected) >= min(
            3,
            len(by_source),
        ):
            break

        selected.append(source)

    return selected[
        : min(
            3,
            len(selected),
        )
    ]


# ============================================================================
# Main
# ============================================================================

def main() -> None:

    print("=" * 88)
    print("COMMAND 4 V2 — REAL IITJ SMOKE TEST")
    print("=" * 88)

    print(
        f"Structured root : {STRUCTURED_ROOT}"
    )

    print(
        f"Domain          : {DOMAIN}"
    )

    print(
        f"Test output     : {TEST_ROOT}"
    )

    domain_root = STRUCTURED_ROOT / DOMAIN

    if not domain_root.exists():

        raise FileNotFoundError(
            f"Current IITJ structured corpus not found: {domain_root}"
        )

    # ------------------------------------------------------------------------
    # Load Command 2 structured knowledge
    # ------------------------------------------------------------------------

    adapter = StructuredKnowledgeInputAdapter()

    units = adapter.extract_directory(
        STRUCTURED_ROOT,
        domain=DOMAIN,
    )

    if not units:

        raise RuntimeError(
            "No normalized IITJ knowledge units were extracted."
        )

    print()

    print(
        f"Normalized units extracted: {len(units)}"
    )

    # ------------------------------------------------------------------------
    # Frozen Command 3
    # ------------------------------------------------------------------------

    (
        accepted_units,
        tier_counts,
        by_source,
    ) = classify_units(units)

    print()

    print("Command 3 tier counts:")

    for tier in (
        "A",
        "B",
        "REVIEW",
        "C",
        "D",
    ):

        print(
            f"  {tier:<7}: {tier_counts.get(tier, 0)}"
        )

    unexpected_tiers = sorted(
        tier
        for tier in tier_counts
        if tier not in {
            "A",
            "B",
            "REVIEW",
            "C",
            "D",
            "",
        }
    )

    if unexpected_tiers:

        raise AssertionError(
            f"Unexpected Command 3 tiers detected: {unexpected_tiers}"
        )

    print()

    print(
        "Command 4 input (A+B+REVIEW): "
        f"{len(accepted_units)} units"
    )

    if not accepted_units:

        raise RuntimeError(
            "Command 3 produced zero A/B/REVIEW units."
        )

    # ------------------------------------------------------------------------
    # Hard safety boundary
    # ------------------------------------------------------------------------

    invalid_input = [
        unit["unit_id"]
        for unit in accepted_units
        if unit.get("tier")
        not in ALLOWED_TIERS
    ]

    if invalid_input:

        raise AssertionError(
            f"C/D reached Command 4: {invalid_input[:10]}"
        )

    # ------------------------------------------------------------------------
    # Select smoke-test documents
    # ------------------------------------------------------------------------

    selected_sources = choose_smoke_sources(
        by_source
    )

    if not selected_sources:

        raise RuntimeError(
            "Could not select real IITJ source documents."
        )

    smoke_units = [
        unit
        for unit in accepted_units
        if unit["source_file"]
        in selected_sources
    ]

    print()

    print("Real source documents selected:")

    for source in selected_sources:

        count = len(
            by_source[source]
        )

        print(
            f"  - {source} ({count} accepted units)"
        )

    print()

    print(
        f"Smoke-test units passed to Command 4: {len(smoke_units)}"
    )

    smoke_tiers = Counter(
        str(
            unit.get("tier", "")
        ).upper()
        for unit in smoke_units
    )

    if any(
        tier not in ALLOWED_TIERS
        for tier in smoke_tiers
    ):

        raise AssertionError(
            f"Smoke payload contains invalid tiers: {dict(smoke_tiers)}"
        )

    # ------------------------------------------------------------------------
    # Clean previous TEST output only
    # ------------------------------------------------------------------------

    if TEST_ROOT.exists():

        shutil.rmtree(TEST_ROOT)

    TEST_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ------------------------------------------------------------------------
    # Write audit JSON
    # ------------------------------------------------------------------------

    audit = {
        "test": "command4_v2_iitj_smoke",
        "domain": DOMAIN,
        "structured_root": str(domain_root),
        "normalized_unit_count": len(units),
        "command3_tier_counts": dict(
            sorted(
                tier_counts.items()
            )
        ),
        "command4_input_count": len(smoke_units),
        "selected_sources": selected_sources,
        "command4_input_tiers": dict(
            sorted(
                smoke_tiers.items()
            )
        ),
    }

    (
        TEST_ROOT
        / "test_audit.json"
    ).write_text(
        json.dumps(
            audit,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    # ------------------------------------------------------------------------
    # Run Command 4
    # ------------------------------------------------------------------------

    organizer = Command4OrganizationV2()

    manifest = organizer.write_output(
        domain=DOMAIN,
        units=smoke_units,
        output_root=TEST_ROOT,
    )

    # ------------------------------------------------------------------------
    # Final reporting
    # ------------------------------------------------------------------------

    print()

    print("=" * 88)
    print("COMMAND 4 V2 — SMOKE TEST COMPLETE")
    print("=" * 88)

    print(
        f"Documents created : {manifest['document_count']}"
    )

    print(
        f"Units organized   : {manifest['unit_count']}"
    )

    print()

    print("Generated Markdown files:")

    output_domain = TEST_ROOT / DOMAIN.replace(".", "_")

    markdown_files = sorted(
        output_domain.rglob("*.md")
    )

    for md in markdown_files:

        print(
            "  - "
            + str(
                md.relative_to(TEST_ROOT)
            )
        )

    print()

    print("Generated JSON files:")

    json_files = sorted(
        output_domain.glob("*.json")
    )

    for js in json_files:

        print(
            "  - "
            + str(
                js.relative_to(TEST_ROOT)
            )
        )

    print()

    print("Inspect test output here:")

    print(
        f"  {TEST_ROOT}"
    )


if __name__ == "__main__":
    main()