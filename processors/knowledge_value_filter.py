"""Stable public API for the Command 3 value filter."""

from processors.knowledge_value_classifier import KnowledgeValueClassifier

KEEP = "KEEP"
CONSOLIDATE = "CONSOLIDATE"
EXCLUDE = "EXCLUDE"
REVIEW = "REVIEW"

TIER_A = "A"
TIER_B = "B"
TIER_C = "C"
TIER_D = "D"
TIER_REVIEW = "REVIEW"


class KnowledgeValueFilter(KnowledgeValueClassifier):
    """Stable public entry point used by downstream pipeline code."""
    pass