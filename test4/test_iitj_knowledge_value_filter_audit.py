"""
IIT Jodhpur — real-data Knowledge Value Filter audit.

Shows:
    A/B/REVIEW/C/D counts
    RAG eligibility
    knowledge_family breakdown per tier
    heading/source examples
    deep REVIEW inspection
    deep C inspection

Audit only. Does not modify corpus or classifier.
"""

import json
from collections import Counter, defaultdict
from pathlib import Path

from processors.knowledge_value_filter import KnowledgeValueFilter


INPUT = Path("storage/test6_iitj_knowledge_units.json")
TIERS = ("A", "B", "REVIEW", "C", "D")
EXAMPLES_PER_FAMILY = 3
REVIEW_EXAMPLES = 20
C_EXAMPLES = 20


def main():
    if not INPUT.exists():
        raise FileNotFoundError(f"Input not found: {INPUT}")

    units = json.loads(
        INPUT.read_text(encoding="utf-8")
    )

    if not isinstance(units, list):
        raise ValueError("Knowledge-unit file must contain a JSON list.")

    flt = KnowledgeValueFilter()

    tier_counts = Counter()
    tier_family_counts = Counter()
    family_counts = Counter()
    examples = defaultdict(list)
    review_items = []
    c_items = []

    for unit in units:
        result = flt.classify(
            heading=unit.get("heading", ""),
            text=unit.get("content", ""),
            source_name=unit.get("source_file", ""),
            document_title=unit.get("source_title", ""),
            document_url=unit.get("source_url", ""),
            content_type=unit.get("content_type", ""),
        )

        tier = result.get("tier", "UNKNOWN")
        family = result.get(
            "knowledge_family",
            "UNKNOWN",
        )

        tier_counts[tier] += 1
        family_counts[family] += 1
        tier_family_counts[(tier, family)] += 1

        example = {
            "heading": unit.get("heading", "") or "(no heading)",
            "source": unit.get("source_file", ""),
            "decision": result.get("decision", ""),
            "confidence": result.get("confidence", ""),
            "reason": (
                result.get("reasons", [""])[0]
                if result.get("reasons")
                else ""
            ),
            "text": unit.get("content", "")
            .replace("\n", " ")[:350],
        }

        key = (tier, family)

        if len(examples[key]) < EXAMPLES_PER_FAMILY:
            examples[key].append(example)

        if tier == "REVIEW" and len(review_items) < REVIEW_EXAMPLES:
            review_items.append({
                **example,
                "family": family,
            })

        if tier == "C" and len(c_items) < C_EXAMPLES:
            c_items.append({
                **example,
                "family": family,
            })

    print("\n" + "=" * 110)
    print("IIT JODHPUR — REAL VALUE FILTER AUDIT")
    print("=" * 110)
    print("Knowledge units:", len(units))

    print("\nTIER COUNTS")
    for tier in TIERS:
        print(f"{tier:8s}: {tier_counts[tier]}")

    rag = (
        tier_counts["A"]
        + tier_counts["B"]
        + tier_counts["REVIEW"]
    )

    print("\nRAG ELIGIBLE (A + B + REVIEW):", rag)
    print(
        "RAG %:",
        round(rag / len(units) * 100, 2),
    )

    for tier in TIERS:
        print("\n" + "=" * 110)
        print(f"{tier} — KNOWLEDGE FAMILY BREAKDOWN")
        print("=" * 110)

        rows = sorted(
            (
                (count, family)
                for (row_tier, family), count
                in tier_family_counts.items()
                if row_tier == tier
            ),
            key=lambda x: (-x[0], x[1]),
        )

        if not rows:
            print("No units.")
            continue

        for count, family in rows:
            print(f"\n{count:6d}  {family}")

            for item in examples[(tier, family)]:
                print("       Heading:", item["heading"])
                print("       Source: ", item["source"])
                print("       Decision:", item["decision"])
                print("       Confidence:", item["confidence"])
                print("       Reason:", item["reason"])
                print("       Text:", item["text"])

    print("\n" + "=" * 110)
    print("REVIEW — DEEP INSPECTION")
    print("=" * 110)

    if not review_items:
        print("REVIEW is empty.")
    else:
        for i, item in enumerate(review_items, 1):
            print(f"\n[{i}] {item['family']}")
            print("Heading:", item["heading"])
            print("Source:", item["source"])
            print("Reason:", item["reason"])
            print("Text:", item["text"])

    print("\n" + "=" * 110)
    print("C — COLLEGE REVIEW ONLY")
    print("=" * 110)

    if not c_items:
        print("C is empty.")
    else:
        for i, item in enumerate(c_items, 1):
            print(f"\n[{i}] {item['family']}")
            print("Heading:", item["heading"])
            print("Source:", item["source"])
            print("Reason:", item["reason"])
            print("Text:", item["text"])

    print("\n" + "=" * 110)
    print("ALL KNOWLEDGE FAMILIES")
    print("=" * 110)

    for family, count in family_counts.most_common():
        print(f"{count:6d}  {family}")

    print("\n" + "=" * 110)
    print("AUDIT COMPLETE")
    print("=" * 110)


if __name__ == "__main__":
    main()