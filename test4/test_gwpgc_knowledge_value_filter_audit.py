"""Universal per-college value-filter audit.

Run one college at a time. Never merge different college corpora for this audit.

Example:
    PYTHONPATH=. python test4/audit_real_knowledge_value_filter.py \
      --input storage/test6_iitj_knowledge_units.json \
      --label IITJ
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from processors.knowledge_value_filter import KnowledgeValueFilter

TIERS = ("A", "B", "REVIEW", "C", "D")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--samples", type=int, default=5)
    args = parser.parse_args()

    path = Path(args.input)
    units = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(units, list):
        raise ValueError("Expected a JSON list of knowledge units.")

    classifier = KnowledgeValueFilter()
    tiers = Counter()
    families = Counter()
    genres = Counter()
    tier_families = Counter()
    tier_genres = Counter()
    samples = defaultdict(list)

    for unit in units:
        result = classifier.classify(
            heading=unit.get("heading", ""),
            text=unit.get("content", ""),
            source_name=unit.get("source_file", ""),
            document_title=unit.get("source_title", ""),
            document_url=unit.get("source_url", ""),
            content_type=unit.get("content_type", ""),
        )

        tier = result.get("tier", "UNKNOWN")
        family = result.get("knowledge_family", "UNKNOWN")
        genre = result.get("document_genre", "UNKNOWN")
        tiers[tier] += 1
        families[family] += 1
        genres[genre] += 1
        tier_families[(tier, family)] += 1
        tier_genres[(tier, genre)] += 1

        key = (tier, family, genre)
        if len(samples[key]) < args.samples:
            samples[key].append(
                {
                    "heading": unit.get("heading", "") or "(no heading)",
                    "source": unit.get("source_file", ""),
                    "reason": (result.get("reasons") or [""])[0],
                    "text": unit.get("content", "").replace("\n", " ")[:350],
                }
            )

    total = len(units)
    rag = tiers["A"] + tiers["B"] + tiers["REVIEW"]

    print("\n" + "=" * 110)
    print(f"{args.label} — PRODUCTION VALUE FILTER AUDIT")
    print("=" * 110)
    print("Units:", total)

    print("\nTIER COUNTS")
    for tier in TIERS:
        print(f"{tier:8s}: {tiers[tier]:6d} ({tiers[tier] / total * 100:.2f}%)")
    print(f"\nRAG ELIGIBLE: {rag} ({rag / total * 100:.2f}%)")

    print("\n" + "=" * 110)
    print("TIER / FAMILY")
    print("=" * 110)
    for tier in TIERS:
        print(f"\n[{tier}]")
        rows = sorted(
            ((count, family) for (row_tier, family), count in tier_families.items() if row_tier == tier),
            key=lambda x: (-x[0], x[1]),
        )
        for count, family in rows:
            print(f"{count:6d}  {family}")

    print("\n" + "=" * 110)
    print("TIER / DOCUMENT GENRE")
    print("=" * 110)
    for tier in TIERS:
        print(f"\n[{tier}]")
        rows = sorted(
            ((count, genre) for (row_tier, genre), count in tier_genres.items() if row_tier == tier),
            key=lambda x: (-x[0], x[1]),
        )
        for count, genre in rows:
            print(f"{count:6d}  {genre}")

    print("\n" + "=" * 110)
    print("REPRESENTATIVE RAG SAMPLES")
    print("=" * 110)
    for tier in ("A", "B", "REVIEW"):
        print(f"\n[{tier}]")
        for tier_key, family, genre in sorted(k for k in samples if k[0] == tier):
            print(f"\n{family} | {genre}")
            for item in samples[(tier_key, family, genre)]:
                print("  Heading:", item["heading"])
                print("  Source:", item["source"])
                print("  Reason:", item["reason"])
                print("  Text:", item["text"])

    print("\n" + "=" * 110)
    print("AUDIT COMPLETE")
    print("=" * 110)


if __name__ == "__main__":
    main()