"""
Real-data comparison test for the universal Knowledge Value Filter.

Runs the SAME input adapter + SAME value filter independently on:
    1. www.iitj.ac.in
    2. gwpgc.ac.in

It produces:
    - A/B/REVIEW/C/D counts
    - RAG eligibility counts
    - representative examples per tier
    - source-independent leakage suspects
    - an IITJ vs GWPGC comparison table

This script does NOT modify the corpus or filter.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from processors.knowledge_organization_input import (
    StructuredKnowledgeInputAdapter,
)
from processors.knowledge_value_filter import (
    KnowledgeValueFilter,
)


DOMAINS = (
    "www.iitj.ac.in",
    "gwpgc.ac.in",
)

TIERS = (
    "A",
    "B",
    "REVIEW",
    "C",
    "D",
)

RAG_TIERS = {
    "A",
    "B",
    "REVIEW",
}


# ---------------------------------------------------------------------------
# Source-independent leakage detector
# ---------------------------------------------------------------------------

# This detector is intentionally NOT the classifier.
# It is a test oracle for obvious record-shaped content that should usually
# be D. It must use generic structure, not college-specific filenames.
LEAKAGE_PATTERNS = {
    "student_roster": (
        "student name",
        "student names",
        "roll number",
        "roll no",
        "registration number",
        "batch:",
        "current year",
    ),
    "person_record": (
        "email:",
        "linkedin",
        "supervisor:",
        "supervisor name:",
        "advisor:",
        "designation:",
    ),
    "project_record": (
        "project title:",
        "project name:",
        "principal investigator:",
        "funding agency:",
        "funding amount:",
        "brief description:",
        "co-pi:",
    ),
    "event_record": (
        "speaker:",
        "talk title:",
        "venue:",
        "registration deadline:",
        "attendee:",
        "participant:",
    ),
    "gallery_person": (
        "![",
        ".jpg",
        ".jpeg",
        ".png",
    ),
}


def classify_leakage_signals(
    heading: str,
    content: str,
) -> list[str]:
    text = (
        f"{heading}\n{content}"
    ).lower()

    matched = []

    for label, patterns in LEAKAGE_PATTERNS.items():
        hits = sum(
            1
            for pattern in patterns
            if pattern in text
        )

        if hits:
            matched.append(
                label
            )

    return matched


def looks_like_person_roster(
    heading: str,
    content: str,
) -> bool:
    text = (
        f"{heading}\n{content}"
    ).lower()

    has_person_fields = (
        ("name" in text or "student name" in text)
        and (
            "roll no" in text
            or "roll number" in text
            or "registration number" in text
        )
    )

    has_table_shape = (
        content.count("|") >= 8
    )

    return (
        has_person_fields
        and has_table_shape
    )


def looks_like_project_record(
    heading: str,
    content: str,
) -> bool:
    text = (
        f"{heading}\n{content}"
    ).lower()

    strong_project_fields = sum(
        field in text
        for field in (
            "project title:",
            "principal investigator:",
            "funding agency:",
            "funding amount:",
            "brief description:",
        )
    )

    return (
        strong_project_fields >= 2
    )


def looks_like_event_record(
    heading: str,
    content: str,
) -> bool:
    text = (
        f"{heading}\n{content}"
    ).lower()

    return (
        (
            "speaker:" in text
            or "talk title:" in text
            or "registration deadline:" in text
        )
        and (
            "event" in text
            or "seminar" in text
            or "workshop" in text
            or "conference" in text
            or "lecture" in text
        )
    )


def is_obvious_record_leak(
    heading: str,
    content: str,
) -> tuple[bool, list[str]]:

    signals = classify_leakage_signals(
        heading,
        content,
    )

    reasons = []

    if looks_like_person_roster(
        heading,
        content,
    ):
        reasons.append(
            "person_roster_shape"
        )

    if looks_like_project_record(
        heading,
        content,
    ):
        reasons.append(
            "project_record_shape"
        )

    if looks_like_event_record(
        heading,
        content,
    ):
        reasons.append(
            "event_record_shape"
        )

    # Gallery markers by themselves are NOT leakage. A lab/facility page can
    # legitimately contain images. Only combine gallery signals with person
    # or event evidence.
    if (
        "gallery_person" in signals
        and (
            "person_record" in signals
            or "event_record" in signals
        )
    ):
        reasons.append(
            "person_or_event_with_media"
        )

    return (
        bool(reasons),
        reasons,
    )


# ---------------------------------------------------------------------------
# Domain run
# ---------------------------------------------------------------------------


def run_domain(
    *,
    domain: str,
    adapter: StructuredKnowledgeInputAdapter,
    value_filter: KnowledgeValueFilter,
    structured_root: Path,
    examples_per_tier: int,
) -> dict[str, Any]:

    units = adapter.extract_directory(
        structured_root,
        domain=domain,
    )

    counts = Counter()
    examples = defaultdict(list)
    leakage = defaultdict(list)

    for unit in units:

        result = value_filter.classify(
            heading=unit.heading,
            text=unit.content,
            source_name=unit.source_file,
            document_title=unit.source_title,
            document_url=unit.source_url,
            content_type=unit.content_type,
        )

        tier = str(
            result["tier"]
        )

        counts[tier] += 1

        if len(
            examples[tier]
        ) < examples_per_tier:
            examples[tier].append(
                {
                    "heading": unit.heading,
                    "source": unit.source_file,
                    "decision": result["decision"],
                    "confidence": result["confidence"],
                    "reason": (
                        result["reasons"][0]
                        if result["reasons"]
                        else ""
                    ),
                    "text": unit.content[
                        :450
                    ].replace(
                        "\n",
                        " ",
                    ),
                }
            )

        obvious_leak, leak_reasons = (
            is_obvious_record_leak(
                unit.heading,
                unit.content,
            )
        )

        if (
            obvious_leak
            and tier != "D"
            and len(leakage[tier]) < 100
        ):
            leakage[tier].append(
                {
                    "heading": unit.heading,
                    "source": unit.source_file,
                    "tier": tier,
                    "decision": result["decision"],
                    "signals": leak_reasons,
                    "text": unit.content[
                        :450
                    ].replace(
                        "\n",
                        " ",
                    ),
                }
            )

    rag_count = sum(
        counts[tier]
        for tier in RAG_TIERS
    )

    return {
        "domain": domain,
        "unit_count": len(units),
        "tier_counts": {
            tier: counts[tier]
            for tier in TIERS
        },
        "rag_eligible": rag_count,
        "rag_percent": (
            round(
                (rag_count / len(units)) * 100,
                2,
            )
            if units
            else 0.0
        ),
        "examples": {
            tier: examples[tier]
            for tier in TIERS
        },
        "leakage": {
            tier: leakage[tier]
            for tier in (
                "A",
                "B",
                "REVIEW",
                "C",
            )
        },
        "leakage_count": sum(
            len(
                leakage[tier]
            )
            for tier in (
                "A",
                "B",
                "REVIEW",
                "C",
            )
        ),
    }


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def print_domain_report(
    result: dict[str, Any],
    *,
    examples_per_tier: int,
) -> None:

    print("\n" + "=" * 110)
    print(
        f"{result['domain']} — REAL DATA VALUE FILTER"
    )
    print("=" * 110)

    print(
        "Units:",
        result["unit_count"],
    )

    print("\nTIER COUNTS")

    for tier in TIERS:
        print(
            f"{tier:8s}: "
            f"{result['tier_counts'][tier]}"
        )

    print(
        "\nRAG ELIGIBLE (A + B + REVIEW):",
        result["rag_eligible"],
        f"({result['rag_percent']}%)",
    )

    print(
        "\nPOSSIBLE RECORD LEAKAGE:",
        result["leakage_count"],
    )

    for tier in (
        "A",
        "B",
        "REVIEW",
        "C",
    ):
        items = result["leakage"][tier]

        if not items:
            continue

        print(
            f"\n--- {tier} LEAKAGE SUSPECTS "
            f"({len(items)}) ---"
        )

        for index, item in enumerate(
            items[:examples_per_tier],
            start=1,
        ):
            print(
                f"\n[{index}] "
                f"{item['heading']}"
            )
            print(
                "Source:",
                item["source"],
            )
            print(
                "Tier:",
                item["tier"],
            )
            print(
                "Decision:",
                item["decision"],
            )
            print(
                "Signals:",
                ", ".join(
                    item["signals"]
                ),
            )
            print(
                "Text:",
                item["text"],
            )

    for tier in TIERS:
        print(
            "\n" + "-" * 100
        )
        print(
            f"{tier} EXAMPLES"
        )

        for index, item in enumerate(
            result["examples"][tier],
            start=1,
        ):
            print(
                f"\n[{index}] "
                f"{item['heading']}"
            )
            print(
                "Source:",
                item["source"],
            )
            print(
                "Decision:",
                item["decision"],
            )
            print(
                "Confidence:",
                item["confidence"],
            )
            print(
                "Reason:",
                item["reason"],
            )
            print(
                "Text:",
                item["text"],
            )


def print_comparison(
    results: dict[str, dict[str, Any]],
) -> None:

    iitj = results["www.iitj.ac.in"]
    gwpgc = results["gwpgc.ac.in"]

    print("\n" + "=" * 110)
    print("IITJ vs GWPGC — UNIVERSAL FILTER COMPARISON")
    print("=" * 110)

    print(
        f"{'Tier':<10}"
        f"{'IITJ':>12}"
        f"{'GWPGC':>12}"
        f"{'IITJ %':>12}"
        f"{'GWPGC %':>12}"
    )

    print("-" * 58)

    for tier in TIERS:

        i_count = iitj[
            "tier_counts"
        ][tier]

        g_count = gwpgc[
            "tier_counts"
        ][tier]

        i_pct = (
            i_count
            / iitj["unit_count"]
            * 100
            if iitj["unit_count"]
            else 0
        )

        g_pct = (
            g_count
            / gwpgc["unit_count"]
            * 100
            if gwpgc["unit_count"]
            else 0
        )

        print(
            f"{tier:<10}"
            f"{i_count:>12}"
            f"{g_count:>12}"
            f"{i_pct:>11.2f}%"
            f"{g_pct:>11.2f}%"
        )

    print("-" * 58)

    print(
        f"{'RAG A+B+REVIEW':<10}"
        f"{iitj['rag_eligible']:>12}"
        f"{gwpgc['rag_eligible']:>12}"
        f"{iitj['rag_percent']:>11.2f}%"
        f"{gwpgc['rag_percent']:>11.2f}%"
    )

    print(
        "\nPOSSIBLE LEAKAGE:"
    )

    print(
        f"IITJ   : {iitj['leakage_count']}"
    )

    print(
        f"GWPGC  : {gwpgc['leakage_count']}"
    )

    print(
        "\nInterpretation:"
    )

    print(
        "Different distributions are expected."
    )

    print(
        "The goal is NOT equal percentages."
    )

    print(
        "The goal is sensible classification on both "
        "independent corpora without college-specific rules."
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--structured-root",
        default="storage/structured_knowledge",
    )

    parser.add_argument(
        "--report",
        default="storage/test7_iitj_gwpgc_value_filter_comparison.json",
    )

    parser.add_argument(
        "--examples-per-tier",
        type=int,
        default=8,
    )

    args = parser.parse_args()

    structured_root = Path(
        args.structured_root
    )

    adapter = (
        StructuredKnowledgeInputAdapter()
    )

    value_filter = (
        KnowledgeValueFilter()
    )

    results = {}

    for domain in DOMAINS:

        results[domain] = run_domain(
            domain=domain,
            adapter=adapter,
            value_filter=value_filter,
            structured_root=structured_root,
            examples_per_tier=args.examples_per_tier,
        )

        print_domain_report(
            results[domain],
            examples_per_tier=args.examples_per_tier,
        )

    print_comparison(
        results
    )

    report_path = Path(
        args.report
    )

    report_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    report_path.write_text(
        json.dumps(
            results,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print(
        "\nComparison report written to:",
        report_path,
    )


if __name__ == "__main__":
    main()