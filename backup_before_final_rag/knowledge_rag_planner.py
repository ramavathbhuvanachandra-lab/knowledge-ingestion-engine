from pathlib import Path
import json
import re


class KnowledgeRAGPlanner:
    """
    Phase 8.4 — Dynamic RAG Planning

    Input:
        storage/organized_knowledge/<domain>/knowledge_units.json

    Output:
        storage/organized_knowledge/<domain>/rag_plan.json

    Responsibilities:

    - Read knowledge units produced by Phase 8.3.
    - Ignore only units explicitly marked NOISE.
    - Preserve KEEP and REVIEW units.
    - Dynamically create the set of RAG documents required
      by the actual knowledge present for a college.
    - Group related units without rewriting them.
    - Preserve source provenance.
    - Guarantee zero useful-unit loss.

    This class does NOT:
    - summarize
    - rewrite
    - call an LLM
    - generate embeddings
    - create DOCX
    """

    # ========================================================
    # RELATED TOPIC GROUPS
    #
    # These are ONLY grouping hints.
    #
    # They do NOT mean every college gets these documents.
    # ========================================================

    RELATED_TOPIC_GROUPS = {
        "admissions": {
            "admissions",
        },

        "academics": {
            "academics",
            "examinations",
        },

        "departments": {
            "departments",
            "faculty",
        },

        "research": {
            "research",
        },

        "campus_and_facilities": {
            "facilities",
            "hostel",
            "student_services",
        },

        "student_life": {
            "events",
            "student_services",
            "hostel",
        },

        "administration": {
            "administration",
            "contact",
        },

        "college_overview": {
            "college_overview",
        },

        "career": {
            "placements",
            "scholarships",
        },

        "notices": {
            "notices",
        },
    }

    # ========================================================
    # DISPLAY NAMES
    # ========================================================

    DISPLAY_NAMES = {
        "admissions": "Admissions",
        "academics": "Academics",
        "departments": "Departments",
        "research": "Research",
        "campus_and_facilities": "Campus and Facilities",
        "student_life": "Student Life",
        "administration": "Administration",
        "college_overview": "College Overview",
        "career": "Career and Scholarships",
        "notices": "Notices",
        "other": "Other",
    }

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        organized_root: str | Path = (
            "storage/organized_knowledge"
        ),
    ):
        self.organized_root = Path(
            organized_root
        )

    # ========================================================
    # PUBLIC API
    # ========================================================

    def plan_domain(
        self,
        domain: str,
    ) -> dict:

        domain = domain.strip()

        if not domain:
            raise ValueError(
                "Domain cannot be empty."
            )

        domain_root = (
            self.organized_root
            / domain
        )

        manifest_path = (
            domain_root
            / "knowledge_units.json"
        )

        if not manifest_path.exists():
            raise FileNotFoundError(
                "Knowledge-unit manifest does not exist: "
                f"{manifest_path}"
            )

        data = json.loads(
            manifest_path.read_text(
                encoding="utf-8"
            )
        )

        units = data.get(
            "units",
            []
        )

        if not isinstance(
            units,
            list,
        ):
            raise ValueError(
                "'units' must be a list."
            )

        # ----------------------------------------------------
        # FILTER / VALIDATE UNITS
        # ----------------------------------------------------

        useful_units = []

        for unit in units:

            if not isinstance(
                unit,
                dict,
            ):
                continue

            decision = (
                unit.get(
                    "decision",
                    "KEEP",
                )
            )

            # Only explicit NOISE is excluded.
            if decision == "NOISE":
                continue

            required = (
                "unit_id",
                "source_document",
                "heading",
                "text",
                "topic",
                "subtopic",
            )

            missing = [
                field
                for field in required
                if not unit.get(field)
            ]

            if missing:
                raise ValueError(
                    "Knowledge unit is missing "
                    f"{missing}: {unit}"
                )

            useful_units.append(
                unit
            )

        if not useful_units:
            raise ValueError(
                f"No useful knowledge units found for "
                f"{domain}."
            )

        # ----------------------------------------------------
        # PLAN GROUPS
        # ----------------------------------------------------

        grouped = {}

        for unit in useful_units:

            topic = self._normalize_topic(
                unit.get(
                    "topic",
                    "other",
                )
            )

            rag_document = (
                self._resolve_rag_document(
                    topic
                )
            )

            grouped.setdefault(
                rag_document,
                []
            ).append(
                unit
            )

        # ----------------------------------------------------
        # STABLE SORTING
        # ----------------------------------------------------

        for document_name in grouped:

            grouped[
                document_name
            ].sort(
                key=self._unit_sort_key
            )

        # ----------------------------------------------------
        # BUILD DOCUMENT PLANS
        # ----------------------------------------------------

        documents = []

        for document_name, document_units in sorted(
            grouped.items()
        ):

            topics = sorted(
                {
                    unit["topic"]
                    for unit in document_units
                }
            )

            source_documents = sorted(
                {
                    unit[
                        "source_document"
                    ]
                    for unit in document_units
                }
            )

            documents.append(
                {
                    "document_id": document_name,
                    "filename": (
                        f"{document_name}.docx"
                    ),
                    "title": (
                        self.DISPLAY_NAMES.get(
                            document_name,
                            self._display_name(
                                document_name
                            ),
                        )
                    ),
                    "topics": topics,
                    "source_documents": (
                        source_documents
                    ),
                    "unit_count": len(
                        document_units
                    ),
                    "units": document_units,
                }
            )

        # ----------------------------------------------------
        # COVERAGE VALIDATION
        # ----------------------------------------------------

        planned_unit_ids = []

        for document in documents:

            for unit in document[
                "units"
            ]:

                planned_unit_ids.append(
                    unit["unit_id"]
                )

        input_unit_ids = [
            unit["unit_id"]
            for unit in useful_units
        ]

        duplicate_input_ids = (
            self._duplicates(
                input_unit_ids
            )
        )

        duplicate_planned_ids = (
            self._duplicates(
                planned_unit_ids
            )
        )

        if duplicate_input_ids:
            raise ValueError(
                "Duplicate input knowledge-unit IDs: "
                f"{duplicate_input_ids}"
            )

        if duplicate_planned_ids:
            raise ValueError(
                "Duplicate planned knowledge-unit IDs: "
                f"{duplicate_planned_ids}"
            )

        missing_ids = sorted(
            set(input_unit_ids)
            - set(planned_unit_ids)
        )

        extra_ids = sorted(
            set(planned_unit_ids)
            - set(input_unit_ids)
        )

        if missing_ids:
            raise ValueError(
                "Knowledge units were lost during RAG planning: "
                f"{missing_ids}"
            )

        if extra_ids:
            raise ValueError(
                "RAG plan contains unknown knowledge units: "
                f"{extra_ids}"
            )

        if len(input_unit_ids) != len(
            planned_unit_ids
        ):
            raise ValueError(
                "RAG plan coverage mismatch."
            )

        # ----------------------------------------------------
        # TOPIC STATISTICS
        # ----------------------------------------------------

        topic_counts = {}

        for unit in useful_units:

            topic = unit["topic"]

            topic_counts[
                topic
            ] = (
                topic_counts.get(
                    topic,
                    0,
                )
                + 1
            )

        # ----------------------------------------------------
        # FINAL PLAN
        # ----------------------------------------------------

        plan = {
            "version": "1.0",
            "planner": "KnowledgeRAGPlanner",
            "domain": domain,
            "input_manifest": str(
                manifest_path
            ),
            "source_documents": sorted(
                {
                    unit[
                        "source_document"
                    ]
                    for unit in useful_units
                }
            ),
            "input_units": len(
                useful_units
            ),
            "rag_documents": len(
                documents
            ),
            "topic_counts": topic_counts,
            "coverage": {
                "input_units": len(
                    useful_units
                ),
                "planned_units": len(
                    planned_unit_ids
                ),
                "missing_units": 0,
                "extra_units": 0,
                "coverage_complete": True,
            },
            "documents": documents,
        }

        # ----------------------------------------------------
        # WRITE PLAN
        # ----------------------------------------------------

        output_path = (
            domain_root
            / "rag_plan.json"
        )

        output_path.write_text(
            json.dumps(
                plan,
                indent=4,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        # ----------------------------------------------------
        # LOGGING
        # ----------------------------------------------------

        print()
        print("=" * 100)
        print("PHASE 8.4 — DYNAMIC RAG PLANNER")
        print("=" * 100)

        print(
            "Domain:",
            domain,
        )

        print(
            "Input units:",
            plan["input_units"],
        )

        print(
            "RAG documents:",
            plan["rag_documents"],
        )

        print(
            "Coverage:",
            (
                "PASS"
                if plan[
                    "coverage"
                ][
                    "coverage_complete"
                ]
                else "FAIL"
            ),
        )

        print()
        print("RAG DOCUMENT PLAN")

        for document in documents:

            print(
                f"{document['filename']:35s}"
                f" → {document['unit_count']} units"
            )

        print()
        print(
            "Plan:",
            output_path,
        )

        return plan

    # ========================================================
    # TOPIC NORMALIZATION
    # ========================================================

    def _normalize_topic(
        self,
        topic: str,
    ) -> str:

        topic = (
            topic or "other"
        ).strip().lower()

        topic = re.sub(
            r"[^a-z0-9_]+",
            "_",
            topic,
        )

        topic = re.sub(
            r"_+",
            "_",
            topic,
        )

        return (
            topic.strip("_")
            or "other"
        )

    # ========================================================
    # RAG DOCUMENT RESOLUTION
    # ========================================================

    def _resolve_rag_document(
        self,
        topic: str,
    ) -> str:
        """
        Decide which final RAG document receives a topic.

        Priority:

        1. Explicit related-topic group.
        2. Original topic.

        This allows topic merging where useful while keeping
        the number of final documents dynamic.
        """

        topic = self._normalize_topic(
            topic
        )

        for document_name, topics in (
            self.RELATED_TOPIC_GROUPS.items()
        ):

            if topic in topics:
                return document_name

        return topic

    # ========================================================
    # UNIT SORT
    # ========================================================

    def _unit_sort_key(
        self,
        unit: dict,
    ) -> tuple:

        return (
            unit.get(
                "source_document",
                "",
            ),
            int(
                unit.get(
                    "section_index",
                    0,
                )
            ),
        )

    # ========================================================
    # DISPLAY NAME
    # ========================================================

    def _display_name(
        self,
        value: str,
    ) -> str:

        value = re.sub(
            r"[_\-]+",
            " ",
            value,
        )

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return value.strip().title()

    # ========================================================
    # DUPLICATE DETECTION
    # ========================================================

    def _duplicates(
        self,
        values: list[str],
    ) -> list[str]:

        seen = set()
        duplicates = set()

        for value in values:

            if value in seen:
                duplicates.add(
                    value
                )

            seen.add(
                value
            )

        return sorted(
            duplicates
        )