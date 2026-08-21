"""
Command 3 — Dynamic Knowledge Taxonomy Planner.

Purpose
-------
Build a deterministic, institution-specific taxonomy from:

1. Corpus Analyzer output
2. Entity Discovery output

This module DOES NOT:
- use an LLM
- delete legitimate unmatched knowledge
- use embeddings
- use a vector database
- create folders
- move/write knowledge units
- rewrite source knowledge
- assume IITJ / engineering / medical / law taxonomy

Architecture
------------
Corpus Evidence
      +
Discovered Entities
      ↓
Dynamic Taxonomy Planner
      ↓
Validated Taxonomy Plan
      ↓
Later: Knowledge Organizer

Important invariants
--------------------
The planner discovers a useful taxonomy from evidence.

It does NOT equate:
    entity == folder
    heading == folder
    repeated term == folder

The final taxonomy is generated deterministically from corpus-wide
evidence and discovered entities.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
import json
import re
from typing import Any


# ============================================================================
# TEXT NORMALIZATION
# ============================================================================

_NON_ALNUM_RE = re.compile(r"[^a-z0-9\s/&-]+")
_WHITESPACE_RE = re.compile(r"\s+")


def _normalize_text(value: Any) -> str:
    """Normalize text for deterministic matching."""
    if value is None:
        return ""

    text = str(value).lower().strip()
    text = _NON_ALNUM_RE.sub(" ", text)
    text = _WHITESPACE_RE.sub(" ", text)

    return text.strip()


def _safe_name(value: str) -> str:
    """
    Convert a taxonomy label into a stable filesystem-safe name.

    This is only used for generated identifiers.
    """
    normalized = _normalize_text(value)

    if not normalized:
        return "unknown"

    normalized = normalized.replace("&", "and")
    normalized = normalized.replace("/", " ")

    normalized = re.sub(
        r"[^a-z0-9]+",
        "_",
        normalized,
    )

    normalized = re.sub(
        r"_+",
        "_",
        normalized,
    ).strip("_")

    return normalized or "unknown"


def _display_name(value: str) -> str:
    """Return a readable display label without changing its meaning."""
    text = str(value).strip()

    if not text:
        return "Unknown"

    return text


# ============================================================================
# GENERIC SEMANTIC SIGNALS
# ============================================================================

class TaxonomySignals:

    STRUCTURAL_ENTITY_TYPES = {
        "department",
        "school",
        "academic_unit",
    }

    PROGRAMMATIC_ENTITY_TYPES = {
        "program",
        "degree",
    }

    RESOURCE_ENTITY_TYPES = {
        "facility",
        "research_centre",
        "office",
        "service",
        "hostel",
    }

    """
    Generic semantic signal vocabulary.

    IMPORTANT:
    These are routing signals, not permanently fixed folders.

    The actual taxonomy is still generated from corpus evidence.
    """

    CONCEPT_ALIASES = {
        "admissions": {
            "admission",
            "admissions",
            "admission_rules",
            "admission_process",
            "admission_policy",
            "application",
            "applications",
        },
        "academics": {
            "academic",
            "academics",
            "academic_affairs",
            "academic_calendar",
            "course",
            "courses",
            "curriculum",
            "curricula",
            "programme",
            "programmes",
            "program",
            "programs",
        },
        "faculty": {
            "faculty",
            "faculties",
            "professor",
            "professors",
            "teaching_staff",
            "staff",
        },
        "research": {
            "research",
            "researches",
            "research_project",
            "research_projects",
            "research_centre",
            "research_center",
            "laboratory",
            "laboratories",
            "lab",
            "labs",
        },
        "courses": {
            "course",
            "courses",
            "course_structure",
            "course_scheme",
            "scheme",
        },
        "syllabus": {
            "syllabus",
            "syllabi",
            "curriculum",
        },
        "examinations": {
            "exam",
            "exams",
            "examination",
            "examinations",
            "result",
            "results",
            "time_table",
            "timetable",
        },
        "fees": {
            "fee",
            "fees",
            "tuition",
            "charges",
            "payment",
        },
        "scholarships": {
            "scholarship",
            "scholarships",
            "fellowship",
            "fellowships",
            "financial_aid",
        },
        "hostels": {
            "hostel",
            "hostels",
            "residence",
            "residential",
            "accommodation",
            "hall",
            "halls",
        },
        "placements": {
            "placement",
            "placements",
            "career",
            "careers",
            "recruitment",
            "recruiters",
        },
        "facilities": {
            "facility",
            "facilities",
            "infrastructure",
            "laboratory",
            "laboratories",
            "lab",
            "labs",
            "workshop",
            "workshops",
            "library",
            "libraries",
            "sports",
            "gym",
        },
        "student_services": {
            "student_services",
            "student_support",
            "student_affairs",
            "student_welfare",
            "student_welfare_services",
            "counselling",
            "counseling",
            "wellbeing",
            "welfare",
        },
        "administration": {
            "administration",
            "administrative",
            "office",
            "offices",
            "registrar",
            "director",
            "dean",
            "committee",
            "committees",
            "minutes",
            "policy",
            "policies",
            "rules",
            "ordinance",
        },
        "events": {
            "event",
            "events",
            "seminar",
            "seminars",
            "workshop",
            "workshops",
            "conference",
            "conferences",
            "activity",
            "activities",
        },
        "contact": {
            "contact",
            "contacts",
            "address",
            "phone",
            "telephone",
            "email",
            "location",
        },
    }


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class TaxonomyEvidence:
    """One deterministic piece of evidence supporting a taxonomy concept."""

    signal_type: str
    value: str
    count: int
    document_count: int
    score: float


@dataclass
class TaxonomyNode:
    """
    One node in the generated taxonomy.

    Nodes are logical organization concepts, not physical folders yet.
    """

    node_id: str
    name: str
    display_name: str

    level: int
    parent_id: str | None

    node_type: str
    entity_type: str | None = None

    confidence: str = "low"
    score: float = 0.0

    evidence: list[TaxonomyEvidence] = field(
        default_factory=list
    )

    routing_signals: list[str] = field(
        default_factory=list
    )

    entity_names: list[str] = field(
        default_factory=list
    )


@dataclass
class BufferPolicy:
    """
    Fallback routing policy for legitimate unmatched knowledge.

    Buffers are NOT pre-created folders and are NOT junk bins.
    The organizer should create a buffer only when a legitimate unit
    cannot be assigned confidently to the generated taxonomy.
    """

    enabled: bool = True
    max_buffers: int = 5

    preferred_names: list[str] = field(
        default_factory=lambda: [
            "General Institutional Information",
            "Policies & Regulations",
            "Student & Campus Information",
            "Activities & Outreach",
            "Other Relevant Institutional Information",
        ]
    )

    rule: str = (
        "Preserve legitimate unmatched knowledge. Never discard useful "
        "content merely because classification is uncertain."
    )


@dataclass
class TaxonomyPlan:
    """Complete deterministic taxonomy plan."""

    phase: str
    domain: str

    version: str

    max_depth: int
    node_count: int

    root_nodes: list[str]

    nodes: list[TaxonomyNode]

    buffer_policy: BufferPolicy

    statistics: dict[str, Any]

    warnings: list[str] = field(
        default_factory=list
    )


# ============================================================================
# TAXONOMY PLANNER
# ============================================================================

class KnowledgeTaxonomyPlanner:
    """
    Build a deterministic taxonomy from corpus evidence.

    The planner is intentionally conservative.

    It prefers:
        strong repeated evidence
        >
        weak one-off evidence

    It also separates:

        institution-wide concepts

    from:

        entity-scoped structures.
    """

    PHASE = "command_3_dynamic_taxonomy"
    VERSION = "2.0"

    MAX_DEPTH = 4
    MIN_GLOBAL_DOCUMENTS = 2
    MIN_GLOBAL_DOCUMENT_RATIO = 0.01
    MIN_ENTITY_DOCUMENTS = 2

    MAX_ROOT_NODES = 20
    MAX_ENTITY_CHILDREN = 12
    MIN_ENTITY_FAMILY_SIZE = 2
    MIN_ENTITY_RELEVANCE_SCORE = 6.0

    STOP_CONCEPTS = {
        "about",
        "overview",
        "details",
        "information",
        "information_on",
        "general",
        "home",
        "main",
        "page",
        "pages",
        "document",
        "documents",
        "content",
        "index",
    }

    def __init__(
        self,
        *,
        max_depth: int = MAX_DEPTH,
    ) -> None:
        self.max_depth = max(
            2,
            min(
                int(max_depth),
                self.MAX_DEPTH,
            ),
        )

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def plan(
        self,
        *,
        corpus_profile: dict[str, Any],
        entity_discovery: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Build a deterministic taxonomy plan.

        Accepted entity-discovery formats:

        Direct result:
            {
                "entity_count": ...,
                "entities": [...]
            }

        Wrapped real-data report:
            {
                ...
                "entity_discovery": {
                    "entity_count": ...,
                    "entities": [...]
                }
            }

        Supporting both formats keeps the planner independent from
        test/report wrappers.
        """

        self._validate_inputs(
            corpus_profile,
            entity_discovery,
        )

        domain = str(
            corpus_profile.get(
                "domain",
                "",
            )
        ).strip()

        documents = corpus_profile.get(
            "documents",
            [],
        )

        if not isinstance(
            documents,
            list,
        ):
            documents = []

        # ------------------------------------------------------------
        # Normalize the entity-discovery contract.
        # ------------------------------------------------------------

        normalized_entity_discovery = (
            self._normalize_entity_discovery(
                entity_discovery
            )
        )

        entities = normalized_entity_discovery.get(
            "entities",
            [],
        )

        if not isinstance(
            entities,
            list,
        ):
            raise ValueError(
                "Entity discovery result contains invalid 'entities'."
            )

        document_count = int(
            corpus_profile.get(
                "document_count",
                len(documents),
            )
            or 0
        )

        entity_count = int(
            normalized_entity_discovery.get(
                "entity_count",
                len(entities),
            )
            or 0
        )

        # ------------------------------------------------------------
        # STEP 1 — Discover globally meaningful concepts.
        # ------------------------------------------------------------

        global_candidates = (
            self._discover_global_candidates(
                corpus_profile=corpus_profile,
                document_count=document_count,
            )
        )

        # ------------------------------------------------------------
        # STEP 2 — Discover institution-level entity families.
        # ------------------------------------------------------------

        entity_groups = (
            self._group_entities(
                entities
            )
        )

        accepted_entity_count = sum(
            1
            for entity in entities
            if isinstance(entity, dict)
            and self._entity_is_meaningful(
                entity
            )
        )

        # ------------------------------------------------------------
        # STEP 3 — Build root concepts.
        # ------------------------------------------------------------

        nodes: list[TaxonomyNode] = []

        root_nodes = (
            self._build_root_nodes(
                global_candidates=global_candidates,
                entity_groups=entity_groups,
                nodes=nodes,
            )
        )

        # ------------------------------------------------------------
        # STEP 4 — Build entity-scoped structures.
        # ------------------------------------------------------------

        self._attach_entity_structures(
            nodes=nodes,
            root_nodes=root_nodes,
            entity_groups=entity_groups,
            corpus_profile=corpus_profile,
            documents=documents,
        )

        # ------------------------------------------------------------
        # STEP 5 — Deterministic pruning.
        # ------------------------------------------------------------

        nodes = self._prune_taxonomy(
            nodes
        )

        # ------------------------------------------------------------
        # STEP 6 — Stable ordering and IDs.
        # ------------------------------------------------------------

        nodes = self._reindex_nodes(
            nodes
        )

        root_ids = [
            node.node_id
            for node in nodes
            if node.level == 1
        ]

        warnings = (
            self._build_warnings(
                nodes=nodes,
                document_count=document_count,
                entity_count=entity_count,
            )
        )

        plan = TaxonomyPlan(
            phase=self.PHASE,
            domain=domain,
            version=self.VERSION,
            max_depth=self.max_depth,
            node_count=len(nodes),
            root_nodes=root_ids,
            nodes=nodes,
            buffer_policy=BufferPolicy(),
            statistics={
                "document_count": document_count,
                "entity_count": entity_count,
                "accepted_entity_count": accepted_entity_count,
                "rejected_entity_count": max(
                    0,
                    entity_count - accepted_entity_count,
                ),
                "global_candidate_count": len(
                    global_candidates
                ),
                "taxonomy_node_count": len(nodes),
                "root_node_count": len(root_ids),
                "entity_family_root_count": sum(
                    1
                    for node in nodes
                    if node.node_type == "entity_family"
                ),
                "entity_node_count": sum(
                    1
                    for node in nodes
                    if node.node_type == "entity"
                ),
                "entity_subcategory_count": sum(
                    1
                    for node in nodes
                    if node.node_type == "entity_subcategory"
                ),
            },
            warnings=warnings,
        )

        return asdict(plan)

    # ========================================================================
    # INPUT NORMALIZATION / VALIDATION
    # ========================================================================

    @staticmethod
    def _validate_inputs(
        corpus_profile: dict[str, Any],
        entity_discovery: dict[str, Any],
    ) -> None:
        if not isinstance(
            corpus_profile,
            dict,
        ):
            raise TypeError(
                "corpus_profile must be a dictionary."
            )

        if not isinstance(
            entity_discovery,
            dict,
        ):
            raise TypeError(
                "entity_discovery must be a dictionary."
            )

    @staticmethod
    def _normalize_entity_discovery(
        entity_discovery: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Normalize direct entity-discovery results and wrapped report files.

        Raises ValueError when a wrapper exists but contains malformed
        entity-discovery data. This prevents silent degraded planning.
        """

        nested = entity_discovery.get(
            "entity_discovery"
        )

        if nested is not None:
            if not isinstance(
                nested,
                dict,
            ):
                raise ValueError(
                    "'entity_discovery' must be a dictionary."
                )

            entity_discovery = nested

        entities = entity_discovery.get(
            "entities"
        )

        if entities is None:
            # Permit a genuinely empty direct result, but make the
            # absence explicit rather than silently manufacturing data.
            return {
                "entity_count": 0,
                "evidence_count": 0,
                "entities": [],
            }

        if not isinstance(
            entities,
            list,
        ):
            raise ValueError(
                "'entities' must be a list."
            )

        return {
            "entity_count": int(
                entity_discovery.get(
                    "entity_count",
                    len(entities),
                )
                or 0
            ),
            "evidence_count": int(
                entity_discovery.get(
                    "evidence_count",
                    0,
                )
                or 0
            ),
            "entities": entities,
        }

    # ========================================================================
    # GLOBAL CANDIDATE DISCOVERY
    # ========================================================================

    def _discover_global_candidates(
        self,
        *,
        corpus_profile: dict[str, Any],
        document_count: int,
    ) -> list[dict[str, Any]]:
        """
        Discover institution-wide taxonomy concepts.

        Evidence sources:

        1. Repeated headings
        2. Corpus terminology
        3. Document types
        4. Original categories

        The output is a candidate list, not a final taxonomy.
        """

        candidates: dict[
            str,
            dict[str, Any],
        ] = {}

        repeated_headings = corpus_profile.get(
            "repeated_headings",
            [],
        )

        terminology_candidates = corpus_profile.get(
            "terminology_candidates",
            [],
        )

        document_types = corpus_profile.get(
            "document_types",
            {},
        )

        original_categories = corpus_profile.get(
            "original_categories",
            {},
        )

        for item in repeated_headings:
            if not isinstance(item, dict):
                continue

            heading = str(
                item.get(
                    "normalized_heading",
                    "",
                )
            ).strip()

            if not heading:
                continue

            occurrences = int(
                item.get(
                    "occurrences",
                    0,
                )
                or 0
            )

            documents = int(
                item.get(
                    "document_count",
                    0,
                )
                or 0
            )

            concept = self._map_signal_to_concept(
                heading
            )

            if not concept:
                continue

            self._add_candidate_evidence(
                candidates=candidates,
                concept=concept,
                signal_type="repeated_heading",
                value=heading,
                count=occurrences,
                document_count=documents,
                base_score=6.0,
            )

        for heading in terminology_candidates:
            heading = str(
                heading
            ).strip()

            if not heading:
                continue

            concept = self._map_signal_to_concept(
                heading
            )

            if not concept:
                continue

            self._add_candidate_evidence(
                candidates=candidates,
                concept=concept,
                signal_type="terminology",
                value=heading,
                count=1,
                document_count=1,
                base_score=1.5,
            )

        if isinstance(
            document_types,
            dict,
        ):
            for value, count in document_types.items():

                count = int(
                    count or 0
                )

                concept = self._map_signal_to_concept(
                    str(value)
                )

                if not concept:
                    continue

                self._add_candidate_evidence(
                    candidates=candidates,
                    concept=concept,
                    signal_type="document_type",
                    value=str(value),
                    count=count,
                    document_count=count,
                    base_score=3.0,
                )

        if isinstance(
            original_categories,
            dict,
        ):
            for value, count in original_categories.items():

                count = int(
                    count or 0
                )

                concept = self._map_signal_to_concept(
                    str(value)
                )

                if not concept:
                    continue

                self._add_candidate_evidence(
                    candidates=candidates,
                    concept=concept,
                    signal_type="original_category",
                    value=str(value),
                    count=count,
                    document_count=count,
                    base_score=4.0,
                )

        results: list[dict[str, Any]] = []

        for concept, item in candidates.items():

            document_evidence = int(
                item["document_count"]
            )

            score = float(
                item["score"]
            )

            document_ratio = (
                document_evidence / document_count
                if document_count > 0
                else 0.0
            )

            strong_enough = (
                document_evidence
                >= self.MIN_GLOBAL_DOCUMENTS
            )

            broad_enough = (
                document_ratio
                >= self.MIN_GLOBAL_DOCUMENT_RATIO
            )

            if not (
                strong_enough
                or broad_enough
            ):
                continue

            results.append(
                {
                    "name": concept,
                    "display_name": self._pretty_label(
                        concept
                    ),
                    "score": round(
                        score,
                        3,
                    ),
                    "document_count": document_evidence,
                    "document_ratio": round(
                        document_ratio,
                        4,
                    ),
                    "confidence": self._confidence_from_score(
                        score
                    ),
                    "evidence": item["evidence"],
                }
            )

        results.sort(
            key=lambda item: (
                -item["score"],
                -item["document_count"],
                item["name"],
            )
        )

        return results

    # ========================================================================
    # ENTITY GROUPING
    # ========================================================================

    @staticmethod
    def _group_entities(
        entities: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        """Group discovered entities by entity type."""

        groups: defaultdict[
            str,
            list[dict[str, Any]],
        ] = defaultdict(list)

        for entity in entities:

            if not isinstance(
                entity,
                dict,
            ):
                continue

            entity_type = str(
                entity.get(
                    "entity_type",
                    "unknown",
                )
            ).strip().lower()

            if not entity_type:
                entity_type = "unknown"

            groups[
                entity_type
            ].append(
                entity
            )

        for entity_type in groups:
            groups[entity_type].sort(
                key=lambda item: (
                    str(
                        item.get(
                            "normalized_name",
                            item.get(
                                "name",
                                "",
                            ),
                        )
                    ).lower(),
                )
            )

        return dict(groups)

    # ========================================================================
    # ROOT NODE CREATION
    # ========================================================================

    def _build_root_nodes(
        self,
        *,
        global_candidates: list[dict[str, Any]],
        entity_groups: dict[str, list[dict[str, Any]]],
        nodes: list[TaxonomyNode],
    ) -> list[str]:
        """Build dynamic root concepts."""

        root_candidates: list[
            tuple[
                str,
                str,
                float,
                str,
                list[str],
            ]
        ] = []

        for candidate in global_candidates:
            root_candidates.append(
                (
                    candidate["name"],
                    candidate["display_name"],
                    float(
                        candidate["score"]
                    ),
                    "corpus_concept",
                    [],
                )
            )

        for entity_type, group in (
            entity_groups.items()
        ):

            meaningful_entities = [
                entity
                for entity in group
                if self._entity_is_meaningful(
                    entity
                )
            ]

            if len(
                meaningful_entities
            ) < 2:
                continue

            root_name = self._entity_type_root_name(
                entity_type
            )

            score = (
                8.0
                + min(
                    len(
                        meaningful_entities
                    ),
                    10,
                )
            )

            entity_names = [
                str(
                    entity.get(
                        "name",
                        "",
                    )
                ).strip()
                for entity in meaningful_entities
                if str(
                    entity.get(
                        "name",
                        "",
                    )
                ).strip()
            ]

            root_candidates.append(
                (
                    root_name,
                    self._pretty_label(
                        root_name
                    ),
                    score,
                    "entity_family",
                    entity_names,
                )
            )

        deduped: dict[
            str,
            tuple[
                str,
                str,
                float,
                str,
                list[str],
            ],
        ] = {}

        for candidate in root_candidates:

            key = _normalize_text(
                candidate[0]
            )

            existing = deduped.get(
                key
            )

            if existing is None:
                deduped[key] = candidate
                continue

            if candidate[2] > existing[2]:
                deduped[key] = candidate

        ordered = sorted(
            deduped.values(),
            key=lambda item: (
                -item[2],
                item[0],
            ),
        )[: self.MAX_ROOT_NODES]

        root_ids: list[str] = []

        for (
            name,
            display_name,
            score,
            node_type,
            entity_names,
        ) in ordered:

            node = TaxonomyNode(
                node_id=f"root::{_safe_name(name)}",
                name=_safe_name(
                    name
                ),
                display_name=_display_name(
                    display_name
                ),
                level=1,
                parent_id=None,
                node_type=node_type,
                confidence=self._confidence_from_score(
                    score
                ),
                score=round(
                    score,
                    3,
                ),
                entity_names=sorted(
                    set(
                        entity_names
                    )
                ),
            )

            nodes.append(
                node
            )

            root_ids.append(
                node.name
            )

        return root_ids

    # ========================================================================
    # ENTITY-SCOPED STRUCTURES
    # ========================================================================

    def _attach_entity_structures(
        self,
        *,
        nodes: list[TaxonomyNode],
        root_nodes: list[str],
        entity_groups: dict[str, list[dict[str, Any]]],
        corpus_profile: dict[str, Any],
        documents: list[dict[str, Any]],
    ) -> None:
        """
        Create entity hierarchy only from actual entity evidence.

        No boilerplate subcategories are created.
        """

        node_by_name = {
            node.name: node
            for node in nodes
        }

        structural_types = {
            "department",
            "school",
            "academic_unit",
        }

        for entity_type in structural_types:

            credible_entities = [
                entity
                for entity in entity_groups.get(
                    entity_type,
                    [],
                )
                if self._entity_is_meaningful(
                    entity
                )
            ]

            if len(
                credible_entities
            ) < self.MIN_ENTITY_FAMILY_SIZE:
                continue

            root_name = self._entity_type_root_name(
                entity_type
            )

            root_key = _safe_name(
                root_name
            )

            root_node = node_by_name.get(
                root_key
            )

            if root_node is None:
                root_node = TaxonomyNode(
                    node_id=f"root::{root_key}",
                    name=root_key,
                    display_name=self._pretty_label(
                        root_name
                    ),
                    level=1,
                    parent_id=None,
                    node_type="entity_family",
                    entity_type=entity_type,
                    confidence="high",
                    score=float(
                        8
                        + min(
                            len(
                                credible_entities
                            ),
                            10,
                        )
                    ),
                    entity_names=[],
                )

                nodes.append(
                    root_node
                )

                node_by_name[
                    root_key
                ] = root_node

            for entity in credible_entities:

                entity_name = str(
                    entity.get(
                        "name",
                        "",
                    )
                ).strip()

                entity_key = _safe_name(
                    entity_name
                )

                if not entity_key:
                    continue

                existing = next(
                    (
                        candidate
                        for candidate in nodes
                        if candidate.parent_id
                        == root_node.node_id
                        and candidate.name
                        == entity_key
                    ),
                    None,
                )

                if existing is not None:
                    entity_node = existing
                else:
                    entity_node = self._create_child_node(
                        name=entity_key,
                        display_name=entity_name,
                        parent=root_node,
                        node_type="entity",
                        entity_type=entity_type,
                        entity=entity,
                    )

                    entity_node.score = (
                        self._entity_taxonomy_score(
                            entity
                        )
                    )

                    entity_node.confidence = (
                        self._entity_confidence(
                            entity
                        )
                    )

                    nodes.append(
                        entity_node
                    )

                # Children are generated ONLY when the entity's own
                # documents support them. There is no department template.
                for subtopic in self._discover_entity_subtopics(
                    entity=entity,
                    documents=documents,
                )[: self.MAX_ENTITY_CHILDREN]:

                    child_name = subtopic["name"]

                    if any(
                        candidate.parent_id
                        == entity_node.node_id
                        and candidate.name
                        == child_name
                        for candidate in nodes
                    ):
                        continue

                    child = self._create_child_node(
                        name=child_name,
                        display_name=subtopic[
                            "display_name"
                        ],
                        parent=entity_node,
                        node_type="entity_subcategory",
                        entity_type=None,
                    )

                    child.score = round(
                        subtopic["score"],
                        3,
                    )

                    child.confidence = (
                        self._confidence_from_score(
                            subtopic["score"]
                        )
                    )

                    child.routing_signals = sorted(
                        set(
                            subtopic[
                                "routing_signals"
                            ]
                        )
                    )

                    child.evidence = [
                        TaxonomyEvidence(
                            **evidence
                        )
                        for evidence in subtopic[
                            "evidence"
                        ]
                    ]

                    nodes.append(
                        child
                    )

        # Resource/program families only become roots when multiple
        # credible entities exist. This prevents a single discovery item
        # from manufacturing a folder family.
        lightweight_types = {
            "facility",
            "research_centre",
            "office",
            "service",
            "hostel",
            "program",
            "degree",
        }

        for entity_type in lightweight_types:

            credible_entities = [
                entity
                for entity in entity_groups.get(
                    entity_type,
                    [],
                )
                if self._entity_is_meaningful(
                    entity
                )
            ]

            if len(
                credible_entities
            ) < self.MIN_ENTITY_FAMILY_SIZE:
                continue

            root_name = self._entity_type_root_name(
                entity_type
            )

            root_key = _safe_name(
                root_name
            )

            if root_key in node_by_name:
                continue

            root_node = TaxonomyNode(
                node_id=f"root::{root_key}",
                name=root_key,
                display_name=self._pretty_label(
                    root_name
                ),
                level=1,
                parent_id=None,
                node_type="entity_family",
                entity_type=entity_type,
                confidence="high",
                score=float(
                    8
                    + min(
                        len(
                            credible_entities
                        ),
                        10,
                    )
                ),
                entity_names=[
                    str(
                        entity.get(
                            "name",
                            "",
                        )
                    ).strip()
                    for entity in credible_entities
                    if str(
                        entity.get(
                            "name",
                            "",
                        )
                    ).strip()
                ],
                routing_signals=[
                    f"entity_type:{entity_type}"
                ],
            )

            nodes.append(
                root_node
            )

            node_by_name[
                root_key
            ] = root_node

    # ------------------------------------------------------------------------
    # Entity relevance helpers
    # ------------------------------------------------------------------------

    @staticmethod
    def _entity_taxonomy_score(
        entity: dict[str, Any],
    ) -> float:
        score = 0.0

        if KnowledgeTaxonomyPlanner._has_structural_entity_evidence(
            entity
        ):
            score += 6.0

        mention_count = int(
            entity.get(
                "mention_count",
                0,
            )
            or 0
        )

        if mention_count >= 2:
            score += 2.0

        if mention_count >= 5:
            score += 1.0

        sources = entity.get(
            "sources",
            [],
        )

        if isinstance(
            sources,
            list,
        ):
            source_count = len(
                {
                    str(source).strip()
                    for source in sources
                    if str(source).strip()
                }
            )

            if source_count >= 2:
                score += 2.0

            if source_count >= 5:
                score += 1.0

        confidence = str(
            entity.get(
                "confidence",
                "low",
            )
        ).lower()

        if confidence == "high":
            score += 1.5
        elif confidence == "medium":
            score += 0.75

        return round(
            score,
            3,
        )

    @staticmethod
    def _entity_confidence(
        entity: dict[str, Any],
    ) -> str:
        score = KnowledgeTaxonomyPlanner._entity_taxonomy_score(
            entity
        )

        if score >= 10:
            return "high"

        if score >= 7:
            return "medium"

        return "low"

    # ========================================================================
    # ENTITY SUBTOPIC DISCOVERY
    # ========================================================================

    def _discover_entity_subtopics(
        self,
        *,
        entity: dict[str, Any],
        documents: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Discover children only from repeated evidence attached to the
        current entity.

        This is what prevents a new department from receiving a boilerplate
        set of Research / Faculty / Courses / Admissions / etc.
        """

        entity_name = str(
            entity.get(
                "name",
                "",
            )
        ).strip()

        if not entity_name:
            return []

        normalized_entity = _normalize_text(
            entity_name
        )

        entity_sources = {
            str(source).strip()
            for source in entity.get(
                "sources",
                [],
            )
            if str(source).strip()
        }

        concept_documents: defaultdict[
            str,
            set[str],
        ] = defaultdict(set)

        concept_values: defaultdict[
            str,
            list[str],
        ] = defaultdict(list)

        for document in documents:

            if not isinstance(
                document,
                dict,
            ):
                continue

            source_file = str(
                document.get(
                    "source_file",
                    "",
                )
            ).strip()

            title = str(
                document.get(
                    "title",
                    "",
                )
            ).strip()

            headings = document.get(
                "headings",
                [],
            )

            if not isinstance(
                headings,
                list,
            ):
                headings = []

            values = [
                title,
                *[
                    str(
                        heading
                    ).strip()
                    for heading in headings
                    if str(
                        heading
                    ).strip()
                ],
            ]

            related = (
                source_file
                in entity_sources
            )

            if not related:
                combined = _normalize_text(
                    " ".join(
                        values
                    )
                )

                related = bool(
                    normalized_entity
                    and normalized_entity
                    in combined
                )

            if not related:
                continue

            concepts_in_document: set[str] = set()

            for value in values:

                concept = self._map_signal_to_concept(
                    value
                )

                if concept:
                    concepts_in_document.add(
                        concept
                    )

            source_identity = (
                source_file
                or title
                or "<unknown>"
            )

            for concept in concepts_in_document:

                concept_documents[
                    concept
                ].add(
                    source_identity
                )

                concept_values[
                    concept
                ].extend(
                    values
                )

        results: list[dict[str, Any]] = []

        for concept, sources in concept_documents.items():

            # Repeated support is required. One accidental heading should
            # not create a permanent child folder.
            if len(
                sources
            ) < self.MIN_ENTITY_DOCUMENTS:
                continue

            values = sorted(
                set(
                    value
                    for value in concept_values[
                        concept
                    ]
                    if value
                )
            )

            score = (
                float(
                    len(sources) * 4
                )
                + min(
                    len(values),
                    8,
                )
            )

            results.append(
                {
                    "name": _safe_name(
                        concept
                    ),
                    "display_name": self._pretty_label(
                        concept
                    ),
                    "score": score,
                    "routing_signals": [
                        f"entity_concept:{concept}"
                    ],
                    "evidence": [
                        asdict(
                            TaxonomyEvidence(
                                signal_type=(
                                    "entity_scoped_corpus"
                                ),
                                value=value,
                                count=1,
                                document_count=len(
                                    sources
                                ),
                                score=score,
                            )
                        )
                        for value in values[:8]
                    ],
                }
            )

        results.sort(
            key=lambda item: (
                -item["score"],
                item["name"],
            )
        )

        return results

    # ========================================================================
    # CANDIDATE HELPERS
    # ========================================================================

    @classmethod
    def _add_candidate_evidence(
        cls,
        *,
        candidates: dict[str, dict[str, Any]],
        concept: str,
        signal_type: str,
        value: str,
        count: int,
        document_count: int,
        base_score: float,
    ) -> None:
        concept = _safe_name(
            concept
        )

        if (
            not concept
            or concept in cls.STOP_CONCEPTS
        ):
            return

        item = candidates.setdefault(
            concept,
            {
                "document_count": 0,
                "score": 0.0,
                "evidence": [],
            },
        )

        item["document_count"] = max(
            int(
                item["document_count"]
            ),
            int(
                document_count
            ),
        )

        contribution = (
            base_score
            + min(
                float(count),
                10.0,
            )
        )

        item["score"] += contribution

        item["evidence"].append(
            asdict(
                TaxonomyEvidence(
                    signal_type=signal_type,
                    value=value,
                    count=int(
                        count
                    ),
                    document_count=int(
                        document_count
                    ),
                    score=contribution,
                )
            )
        )

    @classmethod
    def _map_signal_to_concept(
        cls,
        value: str,
    ) -> str | None:
        """Map observed terminology to a deterministic taxonomy concept."""

        normalized = _normalize_text(
            value
        )

        if not normalized:
            return None

        exact_priority = {
            "course": "courses",
            "courses": "courses",
            "faculty": "faculty",
            "faculties": "faculty",
            "research": "research",
            "syllabus": "syllabus",
            "syllabi": "syllabus",
            "admission": "admissions",
            "admissions": "admissions",
            "program": "programs",
            "programs": "programs",
            "programme": "programs",
            "programmes": "programs",
            "degree": "degrees",
            "degrees": "degrees",
            "exam": "examinations",
            "exams": "examinations",
            "examination": "examinations",
            "examinations": "examinations",
            "fee": "fees",
            "fees": "fees",
            "scholarship": "scholarships",
            "scholarships": "scholarships",
            "placement": "placements",
            "placements": "placements",
            "hostel": "hostels",
            "hostels": "hostels",
            "facility": "facilities",
            "facilities": "facilities",
            "event": "events",
            "events": "events",
            "contact": "contact",
            "contacts": "contact",
            "administration": "administration",
        }

        if normalized in exact_priority:
            return exact_priority[
                normalized
            ]

        exact_matches: list[str] = []

        for concept, aliases in (
            TaxonomySignals.CONCEPT_ALIASES.items()
        ):
            if normalized in {
                _normalize_text(alias)
                for alias in aliases
            }:
                exact_matches.append(
                    concept
                )

        if exact_matches:
            return sorted(
                exact_matches
            )[0]

        candidates: list[
            tuple[int, int, str]
        ] = []

        for concept, aliases in (
            TaxonomySignals.CONCEPT_ALIASES.items()
        ):
            for alias in aliases:
                alias_normalized = _normalize_text(
                    alias
                )

                if (
                    alias_normalized
                    and alias_normalized
                    in normalized
                ):
                    candidates.append(
                        (
                            len(
                                alias_normalized.split()
                            ),
                            len(alias_normalized),
                            concept,
                        )
                    )

        if not candidates:
            return None

        candidates.sort(
            key=lambda item: (
                -item[0],
                -item[1],
                item[2],
            )
        )

        return candidates[0][2]

    # ========================================================================
    # ENTITY HELPERS
    # ========================================================================

    @classmethod
    def _entity_is_meaningful(
        cls,
        entity: dict[str, Any],
    ) -> bool:
        """
        Second-stage taxonomy qualification.

        Entity discovery is recall-oriented. Taxonomy qualification is
        precision-oriented. A discovered entity must look like a real
        institutional object before it can influence folder structure.
        """

        name = str(
            entity.get(
                "name",
                "",
            )
        ).strip()

        if not name:
            return False

        entity_type = str(
            entity.get(
                "entity_type",
                "unknown",
            )
        ).strip().lower()

        if entity_type == "unknown":
            return False

        if not cls._clean_entity_label(
            name,
            entity_type=entity_type,
        ):
            return False

        structural = cls._has_structural_entity_evidence(
            entity
        )

        mention_count = int(
            entity.get(
                "mention_count",
                0,
            )
            or 0
        )

        sources = entity.get(
            "sources",
            [],
        )

        source_count = (
            len(
                {
                    str(source).strip()
                    for source in sources
                    if str(source).strip()
                }
            )
            if isinstance(
                sources,
                list,
            )
            else 0
        )

        confidence = str(
            entity.get(
                "confidence",
                "low",
            )
        ).lower()

        scores = entity.get(
            "scores",
            [],
        )

        max_score = max(
            (
                float(score)
                for score in scores
                if isinstance(
                    score,
                    (int, float),
                )
            ),
            default=0.0,
        )

        relevance = 0.0

        if structural:
            relevance += 6.0

        if mention_count >= 2:
            relevance += 2.0

        if source_count >= 2:
            relevance += 2.0

        if confidence == "high":
            relevance += 1.5
        elif confidence == "medium":
            relevance += 0.75

        if max_score >= 95:
            relevance += 1.5
        elif max_score >= 75:
            relevance += 0.75

        if (
            entity_type
            in TaxonomySignals.STRUCTURAL_ENTITY_TYPES
            and not structural
        ):
            if not (
                confidence == "high"
                and mention_count >= 2
                and source_count >= 2
            ):
                return False

        return relevance >= cls.MIN_ENTITY_RELEVANCE_SCORE

    @staticmethod
    def _clean_entity_label(
        name: str,
        *,
        entity_type: str,
    ) -> bool:
        """Reject obvious text-extraction artifacts."""

        normalized = _normalize_text(
            name
        )

        if not normalized:
            return False

        lowered = name.lower()

        if (
            "@" in name
            or "http://" in lowered
            or "https://" in lowered
            or "www." in lowered
            or re.match(
                r"^(?:email|phone|mobile|fax)[a-z0-9._-]*$",
                normalized,
            )
            or re.search(
                r"(?:^|\s)email[a-z0-9]+\b",
                normalized,
            )
        ):
            return False

        words = normalized.split()

        max_words = {
            "department": 5,
            "school": 5,
            "academic_unit": 5,
            "office": 4,
            "service": 5,
            "hostel": 5,
            "facility": 6,
            "research_centre": 7,
            "program": 6,
            "degree": 6,
        }.get(
            entity_type,
            6,
        )

        if len(words) > max_words:
            return False

        affiliation_markers = {
            "iit",
            "university",
            "college",
            "government",
            "bhu",
            "london",
            "bombay",
            "delhi",
            "jodhpur",
        }

        if (
            ","
            in name
            and any(
                token in affiliation_markers
                for token in words
            )
        ):
            return False

        # Reject page numbers, IDs, amounts, dates, etc. from normal
        # institutional entity classes.
        if (
            entity_type
            not in {"degree", "program"}
            and re.search(
                r"\b\d{2,}[\d,]*(?:\.\d+)?\b",
                name,
            )
        ):
            return False

        field_noise_terms = {
            "number",
            "participants",
            "candidate",
            "name",
            "date",
            "details",
            "amount",
            "sanctioned",
            "phone",
            "email",
            "address",
        }

        if (
            entity_type
            not in {"degree", "program"}
            and any(
                token in field_noise_terms
                for token in words
            )
        ):
            return False

        sentence_markers = {
            "also",
            "are",
            "can",
            "could",
            "does",
            "from",
            "has",
            "have",
            "is",
            "maintains",
            "offers",
            "on",
            "provides",
            "promotes",
            "supports",
            "that",
            "the",
            "this",
            "to",
            "will",
            "with",
            "who",
            "where",
            "which",
        }

        marker_count = sum(
            token in sentence_markers
            for token in words
        )

        if marker_count >= 2:
            return False

        if "," in name and marker_count >= 1:
            return False

        if re.search(
            r"(?:₹|rs\.?|inr)\s*\d"
            r"|\d[\d,]*(?:\.\d+)?\s*(?:rs|inr)",
            lowered,
        ):
            return False

        if sum(
            character in ",;:[]{}|"
            for character in name
        ) >= 3:
            return False

        return True

    @staticmethod
    def _has_structural_entity_evidence(
        entity: dict[str, Any],
    ) -> bool:
        """Recognize explicit institutional structure in entity evidence."""

        values: list[str] = []

        headings = entity.get(
            "headings",
            [],
        )

        if isinstance(
            headings,
            list,
        ):
            values.extend(
                str(value)
                for value in headings
                if str(value).strip()
            )

        evidence = entity.get(
            "evidence",
            [],
        )

        if isinstance(
            evidence,
            list,
        ):
            for item in evidence:
                if not isinstance(
                    item,
                    dict,
                ):
                    continue

                for key in (
                    "heading",
                    "source_heading",
                    "context",
                ):
                    value = item.get(
                        key,
                        "",
                    )
                    if value:
                        values.append(
                            str(value)
                        )

        patterns = (
            r"^department\s+of\s+.+$",
            r"^.+\s+department$",
            r"^school\s+of\s+.+$",
            r"^school\s+.+$",
            r"^(?:research\s+)?"
            r"(?:centre|center)"
            r"(?:\s+(?:for|of))?\s+.+$",
            r"^.+\s+"
            r"(?:laboratory|laboratories|lab|facility|workshop)$",
            r"^office\s+of\s+.+$",
            r"^(?:dean|registrar|director)(?:\s+office)?$",
        )

        for value in values:
            normalized = _normalize_text(
                value
            )

            if any(
                re.fullmatch(
                    pattern,
                    normalized,
                    flags=re.IGNORECASE,
                )
                for pattern in patterns
            ):
                return True

        return False

    @staticmethod
    def _entity_type_root_name(
        entity_type: str,
    ) -> str:
        """Convert a discovered entity type to a generic root label."""

        mapping = {
            "department": "departments",
            "school": "schools",
            "program": "programs",
            "degree": "degrees",
            "research_centre": "research_centres",
            "facility": "facilities",
            "office": "offices",
            "service": "services",
            "hostel": "hostels",
            "academic_unit": "academic_units",
        }

        return mapping.get(
            entity_type,
            "institutional_entities",
        )

    # ========================================================================
    # NODE HELPERS
    # ========================================================================

    @staticmethod
    def _create_child_node(
        *,
        name: str,
        display_name: str,
        parent: TaxonomyNode,
        node_type: str,
        entity_type: str | None = None,
        entity: dict[str, Any] | None = None,
    ) -> TaxonomyNode:
        routing_signals: list[str] = []
        entity_names: list[str] = []

        if entity is not None:

            entity_name = str(
                entity.get(
                    "name",
                    "",
                )
            ).strip()

            if entity_name:
                entity_names.append(
                    entity_name
                )

            if entity_type:
                routing_signals.append(
                    f"entity_type:{entity_type}"
                )

            normalized_name = str(
                entity.get(
                    "normalized_name",
                    "",
                )
            ).strip()

            if normalized_name:
                routing_signals.append(
                    f"entity:{normalized_name}"
                )

        node_name = _safe_name(
            name
        )

        return TaxonomyNode(
            node_id=(
                f"{parent.node_id}::{node_name}"
            ),
            name=node_name,
            display_name=_display_name(
                display_name
            ),
            level=parent.level + 1,
            parent_id=parent.node_id,
            node_type=node_type,
            entity_type=entity_type,
            confidence="medium",
            score=0.0,
            routing_signals=routing_signals,
            entity_names=entity_names,
        )

    # ========================================================================
    # PRUNING
    # ========================================================================

    def _prune_taxonomy(
        self,
        nodes: list[TaxonomyNode],
    ) -> list[TaxonomyNode]:
        """
        Remove clearly unusable nodes.

        Ambiguous knowledge is not deleted here.
        """

        pruned: list[
            TaxonomyNode
        ] = []

        for node in nodes:

            if not node.name:
                continue

            if node.level > self.max_depth:
                continue

            if (
                node.node_type
                == "corpus_concept"
                and node.score < 5.0
            ):
                continue

            pruned.append(
                node
            )

        # ------------------------------------------------------------
        # Deduplicate exact sibling identities.
        # ------------------------------------------------------------

        seen: set[
            tuple[str | None, str]
        ] = set()

        deduped: list[
            TaxonomyNode
        ] = []

        for node in sorted(
            pruned,
            key=lambda item: (
                item.level,
                item.parent_id or "",
                -item.score,
                item.name,
            ),
        ):

            key = (
                node.parent_id,
                node.name,
            )

            if key in seen:
                continue

            seen.add(
                key
            )

            deduped.append(
                node
            )

        return deduped

    # ========================================================================
    # REINDEXING
    # ========================================================================

    @staticmethod
    def _reindex_nodes(
        nodes: list[TaxonomyNode],
    ) -> list[TaxonomyNode]:
        """
        Assign stable IDs while preserving exact parent relationships.
        """

        ordered = sorted(
            nodes,
            key=lambda node: (
                node.level,
                node.parent_id or "",
                node.name,
            ),
        )

        old_to_new: dict[str, str] = {}

        for index, node in enumerate(
            ordered,
            start=1,
        ):
            old_id = node.node_id

            if old_id in old_to_new:
                raise ValueError(
                    "Duplicate provisional taxonomy node ID: "
                    f"{old_id}"
                )

            new_id = (
                f"taxonomy_{index:04d}"
            )

            old_to_new[
                old_id
            ] = new_id

            node.node_id = new_id

        for node in ordered:

            if node.parent_id is None:
                continue

            parent_id = old_to_new.get(
                node.parent_id
            )

            if parent_id is None:
                raise ValueError(
                    "Taxonomy parent reference could not be resolved."
                )

            node.parent_id = parent_id

        return ordered

    # ========================================================================
    # CONFIDENCE
    # ========================================================================

    @staticmethod
    def _confidence_from_score(
        score: float,
    ) -> str:
        if score >= 15:
            return "high"

        if score >= 8:
            return "medium"

        return "low"

    # ========================================================================
    # LABELS
    # ========================================================================

    @staticmethod
    def _pretty_label(
        value: str,
    ) -> str:
        normalized = _safe_name(
            value
        )

        if not normalized:
            return "Unknown"

        return " ".join(
            token.capitalize()
            for token in normalized.split(
                "_"
            )
        )

    # ========================================================================
    # WARNINGS
    # ========================================================================

    def _build_warnings(
        self,
        *,
        nodes: list[TaxonomyNode],
        document_count: int,
        entity_count: int,
    ) -> list[str]:
        warnings: list[str] = []

        if document_count == 0:
            warnings.append(
                "No corpus documents were available."
            )

        if entity_count == 0:
            warnings.append(
                "No discovered entities were available."
            )

        root_count = sum(
            1
            for node in nodes
            if node.level == 1
        )

        if root_count == 0:
            warnings.append(
                "No strong taxonomy roots were discovered."
            )

        max_level = max(
            (
                node.level
                for node in nodes
            ),
            default=0,
        )

        if max_level >= self.max_depth:
            warnings.append(
                "Taxonomy reached the configured maximum depth."
            )

        return warnings


# ============================================================================
# SERIALIZATION HELPERS
# ============================================================================

def save_taxonomy_plan(
    plan: dict[str, Any],
    output_path: str | Path,
) -> None:
    """Persist a taxonomy plan for later organizer/validator stages."""

    output_path = Path(
        output_path
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            plan,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def load_taxonomy_plan(
    input_path: str | Path,
) -> dict[str, Any]:
    """Load a previously generated taxonomy plan."""

    input_path = Path(
        input_path
    )

    if not input_path.exists():
        raise FileNotFoundError(
            f"Taxonomy plan does not exist: {input_path}"
        )

    data = json.loads(
        input_path.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(
        data,
        dict,
    ):
        raise ValueError(
            "Taxonomy plan must be a JSON object."
        )

    return data


# ============================================================================
# OPTIONAL CLI
# ============================================================================

def main() -> None:
    """Manual inspection CLI."""

    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Build a deterministic dynamic taxonomy "
            "from corpus and entity-discovery profiles."
        )
    )

    parser.add_argument(
        "--corpus-profile",
        required=True,
        help="Path to corpus profile JSON.",
    )

    parser.add_argument(
        "--entity-discovery",
        required=True,
        help="Path to entity discovery JSON.",
    )

    parser.add_argument(
        "--output",
        required=False,
        help="Optional output path for taxonomy plan JSON.",
    )

    args = parser.parse_args()

    corpus_profile = json.loads(
        Path(
            args.corpus_profile
        ).read_text(
            encoding="utf-8"
        )
    )

    entity_discovery = json.loads(
        Path(
            args.entity_discovery
        ).read_text(
            encoding="utf-8"
        )
    )

    planner = KnowledgeTaxonomyPlanner()

    plan = planner.plan(
        corpus_profile=corpus_profile,
        entity_discovery=entity_discovery,
    )

    serialized = json.dumps(
        plan,
        indent=2,
        ensure_ascii=False,
    )

    if args.output:
        save_taxonomy_plan(
            plan,
            args.output,
        )

        print(
            f"Taxonomy plan written to: {args.output}"
        )
    else:
        print(
            serialized
        )


if __name__ == "__main__":
    main()
