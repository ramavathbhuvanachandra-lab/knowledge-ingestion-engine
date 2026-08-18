"""
Command 3 — Real-Data Semantic Signal Validation.

Runs the universal semantic signal engine against the real structured
knowledge dataset.

This is a diagnostic test only.

It does NOT:
    - modify knowledge units
    - modify production data
    - rewrite documents
    - create organization folders

The production engine remains completely college-agnostic.

IITJ is used only as a real-world stress dataset.
"""

from collections import Counter
import json
from pathlib import Path

from processors.knowledge_semantic_signals import (
    KnowledgeSemanticSignalEngine,
)


# ============================================================
# REAL DATASET
# ============================================================

KNOWLEDGE_UNITS_PATH = Path(
    "storage/test3_organized_v2/"
    "www.iitj.ac.in/"
    "knowledge_units.json"
)


# ============================================================
# VALIDATION LIMIT
# ============================================================

MAX_UNKNOWN_PERCENT = 60.0


# ============================================================
# TEST
# ============================================================

def test_real_semantic_signal_distribution():
    """
    Analyze every real knowledge unit using the scope-aware API.
    """

    assert KNOWLEDGE_UNITS_PATH.exists(), (
        f"Knowledge units file does not exist: "
        f"{KNOWLEDGE_UNITS_PATH}"
    )

    data = json.loads(
        KNOWLEDGE_UNITS_PATH.read_text(
            encoding="utf-8"
        )
    )

    units = data.get(
        "units",
        [],
    )

    assert units, (
        "No knowledge units found."
    )

    engine = KnowledgeSemanticSignalEngine()

    primary_types = Counter()
    confidence_counts = Counter()
    secondary_signal_counts = Counter()

    examples = {}

    analyzed = 0
    unknown = 0
    multi_signal = 0

    # --------------------------------------------------------
    # ANALYZE EVERY REAL UNIT
    # --------------------------------------------------------

    for unit in units:

        record_heading = (
            unit.get("heading")
            or ""
        )

        record_text = (
            unit.get("text")
            or ""
        )

        section_context = (
            unit.get("section_path")
            or []
        )

        document_title = (
            unit.get("document_title")
            or ""
        )

        result = engine.analyze(
            record_heading=record_heading,
            record_text=record_text,
            section_context=section_context,
            document_title=document_title,
        )

        primary_type = (
            result["primary_type"]
        )

        primary_types[
            primary_type
        ] += 1

        confidence_counts[
            result["confidence"]
        ] += 1

        for signal in (
            result["secondary_types"]
        ):
            secondary_signal_counts[
                signal
            ] += 1

        if primary_type == "unknown":
            unknown += 1

        if result["secondary_types"]:
            multi_signal += 1

        # ----------------------------------------------------
        # Store one representative example per primary type
        # ----------------------------------------------------

        if primary_type not in examples:

            examples[
                primary_type
            ] = {
                "heading": record_heading,
                "section_context": section_context,
                "document_title": document_title,
                "text": record_text[:500],
                "matched_signals": (
                    result["matched_signals"]
                ),
                "secondary_types": (
                    result["secondary_types"]
                ),
                "confidence": (
                    result["confidence"]
                ),
            }

        analyzed += 1

    # --------------------------------------------------------
    # BASIC INVARIANTS
    # --------------------------------------------------------

    assert analyzed == len(units)

    unknown_percent = (
        unknown / analyzed
    ) * 100

    assert (
        unknown_percent
        <= MAX_UNKNOWN_PERCENT
    ), (
        "Unexpectedly high unknown rate: "
        f"{unknown_percent:.2f}%"
    )

    # ========================================================
    # OUTPUT
    # ========================================================

    print()
    print("=" * 90)
    print("REAL SEMANTIC SIGNAL VALIDATION")
    print("=" * 90)

    print(
        "Knowledge units:",
        analyzed,
    )

    print(
        "Unknown units:",
        unknown,
    )

    print(
        "Unknown percentage:",
        f"{unknown_percent:.2f}%",
    )

    print(
        "Multi-signal units:",
        multi_signal,
    )

    # --------------------------------------------------------
    # PRIMARY TYPES
    # --------------------------------------------------------

    print()
    print("PRIMARY TYPES")
    print("-" * 90)

    for signal, count in (
        primary_types.most_common()
    ):

        percentage = (
            count / analyzed
        ) * 100

        print(
            f"{signal:30}"
            f"{count:6}"
            f"  {percentage:6.2f}%"
        )

    # --------------------------------------------------------
    # CONFIDENCE
    # --------------------------------------------------------

    print()
    print("CONFIDENCE")
    print("-" * 90)

    for confidence, count in (
        confidence_counts.most_common()
    ):

        percentage = (
            count / analyzed
        ) * 100

        print(
            f"{confidence:30}"
            f"{count:6}"
            f"  {percentage:6.2f}%"
        )

    # --------------------------------------------------------
    # SECONDARY SIGNALS
    # --------------------------------------------------------

    print()
    print("SECONDARY SIGNALS")
    print("-" * 90)

    if secondary_signal_counts:

        for signal, count in (
            secondary_signal_counts.most_common()
        ):
            print(
                f"{signal:30}"
                f"{count:6}"
            )

    else:
        print("None")

    # --------------------------------------------------------
    # REPRESENTATIVE EXAMPLES
    # --------------------------------------------------------

    print()
    print("REPRESENTATIVE EXAMPLES")
    print("-" * 90)

    for signal in sorted(examples):

        example = examples[
            signal
        ]

        print()
        print(
            "TYPE:",
            signal,
        )

        print(
            "CONFIDENCE:",
            example[
                "confidence"
            ],
        )

        print(
            "DOCUMENT:",
            example[
                "document_title"
            ],
        )

        print(
            "SECTION:",
            example[
                "section_context"
            ],
        )

        print(
            "HEADING:",
            example[
                "heading"
            ],
        )

        print(
            "SECONDARY:",
            example[
                "secondary_types"
            ],
        )

        print(
            "MATCHED:",
            example[
                "matched_signals"
            ],
        )

        print(
            "TEXT:",
            example[
                "text"
            ],
        )

    print()
    print("=" * 90)