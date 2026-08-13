"""
Phase 8.4 — Universal Dynamic RAG Document Planner

This planner is college-agnostic.

Input
-----
8.3 knowledge_units.json

Output
------
rag_plan.json

Core rules
----------
1. No college-specific hardcoding.
2. No fixed final document count.
3. Semantic coherence > unit count.
4. A coherent category may contain hundreds of units.
5. Large mixed groups are split by taxonomy boundaries.
6. Extremely large homogeneous groups are split only at
   source-document boundaries.
7. Tiny groups are merged with compatible families.
8. REVIEW knowledge is preserved in a protected buffer.
9. Every non-NOISE unit appears exactly once.
10. No LLM.
11. No chunking.
12. No embeddings.
13. No vector database.
14. No DOCX generation.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import json
import re


class KnowledgeRAGPlanner:

    # ================================================================
    # UNIVERSAL SIZE POLICY
    # ================================================================

    SOFT_LARGE_THRESHOLD = 300
    HARD_LARGE_THRESHOLD = 500
    SMALL_GROUP_THRESHOLD = 8

    # ================================================================
    # UNIVERSAL SEMANTIC FAMILIES
    #
    # These are based on generic college knowledge concepts.
    # They are NOT tied to any specific institution.
    # ================================================================

    FAMILY_RULES = {

        "academic_programs": {
            "title": "Academic Programs",
            "domains": {
                "academics",
                "admissions",
            },
            "categories": {
                "programs",
                "admission_overview",
                "eligibility",
                "application_process",
                "entrance_examinations",
            },
        },

        "departments_and_schools": {
            "title": "Departments and Schools",
            "domains": {
                "academics",
            },
            "categories": {
                "departments_and_schools",
                "schools",
            },
        },

        "academic_delivery": {
            "title": "Courses, Registration, Calendar and Evaluation",
            "domains": {
                "academics",
            },
            "categories": {
                "courses_and_curriculum",
                "registration_and_enrolment",
                "academic_calendar",
                "examinations_and_evaluation",
                "attendance_and_academic_progress",
                "transcripts_and_certificates",
                "academic_forms",
            },
        },

        "academic_rules_and_regulations": {
            "title": "Academic Rules and Regulations",
            "domains": {
                "academics",
                "rules_policies_and_regulations",
            },
            "categories": {
                "academic_rules_and_regulations",
                "academic_regulations",
            },
        },

        "research_areas_and_groups": {
            "title": "Research Areas and Groups",
            "domains": {
                "research",
            },
            "categories": {
                "research_areas",
                "research_groups",
            },
        },

        "research_projects": {
            "title": "Research Projects",
            "domains": {
                "research",
            },
            "categories": {
                "research_projects",
            },
        },

        "research_centres_and_labs": {
            "title": "Research Centres and Laboratories",
            "domains": {
                "research",
                "institutes_centres_and_units",
            },
            "categories": {
                "research_centres_and_centers",
                "research_laboratories",
                "laboratories",
                "special_units",
            },
        },

        "research_outputs_and_innovation": {
            "title": "Research Outputs and Innovation",
            "domains": {
                "research",
            },
            "categories": {
                "publications",
                "patents_and_innovation",
                "research_funding_and_grants",
                "research_collaborations",
            },
        },

        "institute_centres_and_units": {
            "title": "Institutes, Centres and Units",
            "domains": {
                "institutes_centres_and_units",
            },
            "categories": {
                "centre_overview",
                "centres_and_centers",
                "institutes",
            },
        },

        "campus_and_infrastructure": {
            "title": "Campus and Infrastructure",
            "domains": {
                "campus",
                "facilities_and_infrastructure",
            },
            "categories": {
                "campus_overview",
                "locations_and_directions",
                "buildings_and_spaces",
                "transportation",
                "utilities_and_services",
                "accessibility",
                "specialized_facilities",
                "computing_and_digital_facilities",
                "classrooms_and_academic_spaces",
                "auditoriums_and_conference_spaces",
            },
        },

        "laboratories_and_workshops": {
            "title": "Laboratories and Workshops",
            "domains": {
                "facilities_and_infrastructure",
            },
            "categories": {
                "laboratories",
                "workshops",
            },
        },

        "library_and_learning_facilities": {
            "title": "Library and Learning Facilities",
            "domains": {
                "facilities_and_infrastructure",
            },
            "categories": {
                "libraries",
            },
        },

        "environment_and_sustainability": {
            "title": "Environment and Sustainability",
            "domains": {
                "campus",
                "health_safety_and_wellbeing",
            },
            "categories": {
                "environment_and_sustainability",
            },
        },

        "people_and_leadership": {
            "title": "People and Leadership",
            "domains": {
                "people",
            },
            "categories": {
                "faculty",
                "researchers",
                "staff",
                "leadership",
                "position_holders",
                "committees_and_boards",
            },
        },

        "contacts_and_directory": {
            "title": "Contacts and Directory",
            "domains": {
                "people",
                "contacts_and_directory",
            },
            "categories": {
                "contact_directory",
                "general_contacts",
                "office_directory",
                "emergency_contacts",
            },
        },

        "student_residential_life": {
            "title": "Student Residential Life",
            "domains": {
                "hostels",
                "food_and_dining",
            },
            "categories": {
                "accommodation",
                "hostel_rules",
                "hostel_fees",
                "hostel_facilities",
                "hostel_allocation_and_application",
                "hostel_contacts",
                "mess_and_dining",
                "cafeterias_and_food_outlets",
                "food_services_and_rules",
            },
        },

        "student_life_and_welfare": {
            "title": "Student Life and Welfare",
            "domains": {
                "student_life",
            },
            "categories": {
                "student_services",
                "student_welfare",
                "clubs_and_societies",
                "student_activities",
                "student_opportunities",
                "grievances_and_support",
            },
        },

        "health_safety_and_wellbeing": {
            "title": "Health, Safety and Wellbeing",
            "domains": {
                "health_safety_and_wellbeing",
            },
            "categories": {
                "medical_services",
                "counselling_and_mental_wellbeing",
                "emergency_services",
                "security",
                "fire_and_safety",
            },
        },

        "careers_and_placements": {
            "title": "Careers, Placements and Internships",
            "domains": {
                "careers_and_placements",
            },
            "categories": {
                "placements",
                "recruitment",
                "internships",
                "career_services",
                "training",
            },
        },

        "finance_and_student_finance": {
            "title": "Fees, Scholarships and Finance",
            "domains": {
                "finance_and_fees",
                "admissions",
            },
            "categories": {
                "fees",
                "scholarships",
                "fellowships_and_stipends",
                "financial_assistance",
                "admission_fees",
            },
        },

        "administration_and_governance": {
            "title": "Administration and Governance",
            "domains": {
                "administration",
                "rules_policies_and_regulations",
            },
            "categories": {
                "administrative_offices",
                "registrar_and_establishment",
                "directorate_and_deans",
                "governance",
                "statutory_bodies",
                "institutional_rules",
                "administrative_policies",
            },
        },

        "events_and_notices": {
            "title": "Events, Notices and Announcements",
            "domains": {
                "events_and_activities",
                "notices_and_announcements",
            },
            "categories": {
                "events",
                "festivals",
                "seminars_and_workshops",
                "conferences",
                "outreach_and_public_engagement",
                "academic_notices",
                "admission_notices",
                "student_notices",
                "administrative_notices",
                "general_announcements",
            },
        },
    }

    # ================================================================
    # CONSTRUCTOR
    # ================================================================

    def __init__(
        self,
        organized_root: str | Path = (
            "storage/organized_knowledge"
        ),
    ):
        self.organized_root = Path(
            organized_root
        )

    # ================================================================
    # PUBLIC API
    # ================================================================

    def plan_domain(
        self,
        domain: str,
    ) -> dict:

        domain = (domain or "").strip()

        if not domain:
            raise ValueError(
                "Domain cannot be empty."
            )

        domain_root = (
            self.organized_root / domain
        )

        manifest_path = (
            domain_root / "knowledge_units.json"
        )

        if not manifest_path.exists():
            raise FileNotFoundError(
                f"Knowledge-unit manifest does not exist: "
                f"{manifest_path}"
            )

        data = json.loads(
            manifest_path.read_text(
                encoding="utf-8"
            )
        )

        units = data.get(
            "units",
            [],
        )

        if not isinstance(units, list):
            raise ValueError(
                "'units' must be a list."
            )

        useful_units = []

        for unit in units:

            if not isinstance(unit, dict):
                continue

            if unit.get(
                "decision",
                "KEEP",
            ) == "NOISE":
                continue

            required = (
                "unit_id",
                "source_document",
                "heading",
                "text",
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

            useful_units.append(unit)

        if not useful_units:
            raise ValueError(
                f"No useful knowledge units found for {domain}."
            )

        # ------------------------------------------------------------
        # CREATE INITIAL SEMANTIC FAMILIES
        # ------------------------------------------------------------

        groups = defaultdict(list)

        for unit in useful_units:

            family = self._resolve_family(
                unit
            )

            groups[family].append(unit)

        # ------------------------------------------------------------
        # PROTECT REVIEW
        # ------------------------------------------------------------

        review_units = [
            unit
            for unit in useful_units
            if unit.get(
                "taxonomy_domain"
            ) == "review"
        ]

        if review_units:

            groups = {
                key: value
                for key, value
                in groups.items()
                if key != "review_and_special_content"
            }

            groups[
                "review_and_special_content"
            ] = review_units

        # ------------------------------------------------------------
        # MERGE TINY FAMILIES
        # ------------------------------------------------------------

        groups = (
            self._merge_tiny_families(
                groups
            )
        )

        # ------------------------------------------------------------
        # SPLIT LARGE FAMILIES
        # ------------------------------------------------------------

        groups = (
            self._split_large_families(
                groups
            )
        )

        # ------------------------------------------------------------
        # BUILD DOCUMENTS
        # ------------------------------------------------------------

        documents = (
            self._build_documents(
                groups
            )
        )

        # ------------------------------------------------------------
        # VALIDATE
        # ------------------------------------------------------------

        self._validate_coverage(
            useful_units,
            documents,
        )

        # ------------------------------------------------------------
        # STATISTICS
        # ------------------------------------------------------------

        topic_counts = Counter()
        taxonomy_counts = Counter()

        for unit in useful_units:

            topic_counts[
                unit.get(
                    "topic",
                    "other",
                )
            ] += 1

            taxonomy_counts[
                self._taxonomy_key(unit)
            ] += 1

        # ------------------------------------------------------------
        # PLAN
        # ------------------------------------------------------------

        plan = {
            "version": "4.0",

            "planner": (
                "KnowledgeRAGPlanner"
            ),

            "strategy": (
                "universal_semantic_family_grouping"
            ),

            "domain": domain,

            "input_manifest": str(
                manifest_path
            ),

            "input_units": len(
                useful_units
            ),

            "rag_documents": len(
                documents
            ),

            "document_count_is_dynamic": True,

            "size_policy": {
                "semantic_coherence_first": True,
                "soft_large_threshold": (
                    self.SOFT_LARGE_THRESHOLD
                ),
                "hard_large_threshold": (
                    self.HARD_LARGE_THRESHOLD
                ),
                "small_group_threshold": (
                    self.SMALL_GROUP_THRESHOLD
                ),
            },

            "topic_counts": dict(
                sorted(
                    topic_counts.items()
                )
            ),

            "taxonomy_counts": dict(
                sorted(
                    taxonomy_counts.items()
                )
            ),

            "coverage": {
                "input_units": len(
                    useful_units
                ),

                "planned_units": sum(
                    document[
                        "unit_count"
                    ]
                    for document
                    in documents
                ),

                "missing_units": 0,
                "extra_units": 0,
                "duplicate_units": 0,
                "coverage_complete": True,
            },

            "documents": documents,
        }

        output_path = (
            domain_root / "rag_plan.json"
        )

        output_path.write_text(
            json.dumps(
                plan,
                indent=4,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        # ------------------------------------------------------------
        # LOGGING
        # ------------------------------------------------------------

        print()
        print("=" * 100)
        print(
            "PHASE 8.4 — UNIVERSAL SEMANTIC RAG PLANNER"
        )
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
                if plan["coverage"][
                    "coverage_complete"
                ]
                else "FAIL"
            ),
        )

        print()

        print("RAG DOCUMENT PLAN")

        for document in documents:

            print(
                f"{document['filename']:60}"
                f" → "
                f"{document['unit_count']:4} units"
            )

        print()
        print(
            "Plan:",
            output_path,
        )

        return plan

    # ================================================================
    # FAMILY RESOLUTION
    # ================================================================

    def _resolve_family(
        self,
        unit: dict,
    ) -> str:

        if unit.get(
            "taxonomy_domain"
        ) == "review":
            return (
                "review_and_special_content"
            )

        domain = self._normalize(
            unit.get(
                "taxonomy_domain",
                unit.get(
                    "topic",
                    "other",
                ),
            )
        )

        category = self._normalize(
            unit.get(
                "taxonomy_category",
                unit.get(
                    "subtopic",
                    "other",
                ),
            )
        )

        matches = []

        for family_name, rule in (
            self.FAMILY_RULES.items()
        ):

            if (
                domain in rule["domains"]
                and category
                in rule["categories"]
            ):
                matches.append(
                    family_name
                )

        if matches:

            # More specific families first.
            return sorted(
                matches
            )[0]

        # ------------------------------------------------------------
        # GENERIC DOMAIN FALLBACK
        # ------------------------------------------------------------

        domain_fallbacks = {

            "academics":
                "academic_delivery",

            "admissions":
                "academic_programs",

            "research":
                "research_outputs_and_innovation",

            "people":
                "people_and_leadership",

            "campus":
                "campus_and_infrastructure",

            "facilities_and_infrastructure":
                "campus_and_infrastructure",

            "student_life":
                "student_life_and_welfare",

            "hostels":
                "student_residential_life",

            "food_and_dining":
                "student_residential_life",

            "health_safety_and_wellbeing":
                "health_safety_and_wellbeing",

            "careers_and_placements":
                "careers_and_placements",

            "finance_and_fees":
                "finance_and_student_finance",

            "administration":
                "administration_and_governance",

            "rules_policies_and_regulations":
                "administration_and_governance",

            "events_and_activities":
                "events_and_notices",

            "notices_and_announcements":
                "events_and_notices",

            "contacts_and_directory":
                "contacts_and_directory",

            "institutes_centres_and_units":
                "institute_centres_and_units",
        }

        return domain_fallbacks.get(
            domain,
            "review_and_special_content",
        )

    # ================================================================
    # SMALL GROUP MERGING
    # ================================================================

    def _merge_tiny_families(
        self,
        groups: dict[str, list[dict]],
    ) -> dict[str, list[dict]]:

        result = {
            key: list(value)
            for key, value
            in groups.items()
        }

        changed = True

        while changed:

            changed = False

            small = [
                key
                for key, units
                in result.items()
                if (
                    len(units)
                    <= self.SMALL_GROUP_THRESHOLD
                )
                and key
                != "review_and_special_content"
            ]

            for source_key in small:

                if source_key not in result:
                    continue

                target = (
                    self._nearest_family(
                        source_key,
                        result,
                    )
                )

                if target is None:
                    continue

                result[
                    target
                ].extend(
                    result.pop(
                        source_key
                    )
                )

                changed = True
                break

        return result

    # ================================================================
    # NEAREST FAMILY
    # ================================================================

    def _nearest_family(
        self,
        source_key: str,
        groups: dict[str, list[dict]],
    ) -> str | None:

        source_units = groups.get(
            source_key,
            [],
        )

        if not source_units:
            return None

        source_domain = self._normalize(
            source_units[0].get(
                "taxonomy_domain",
                "",
            )
        )

        best = None
        best_score = -1

        for target_key, target_units in (
            groups.items()
        ):

            if target_key == source_key:
                continue

            if (
                target_key
                == "review_and_special_content"
            ):
                continue

            if not target_units:
                continue

            target_domain = self._normalize(
                target_units[0].get(
                    "taxonomy_domain",
                    "",
                )
            )

            score = 0

            if (
                source_domain
                == target_domain
            ):
                score += 100

            source_categories = {
                self._normalize(
                    unit.get(
                        "taxonomy_category",
                        "",
                    )
                )
                for unit
                in source_units
            }

            target_categories = {
                self._normalize(
                    unit.get(
                        "taxonomy_category",
                        "",
                    )
                )
                for unit
                in target_units
            }

            score += 10 * len(
                source_categories
                & target_categories
            )

            if score > best_score:
                best_score = score
                best = target_key

        return best

    # ================================================================
    # LARGE FAMILY SPLITTING
    # ================================================================

    def _split_large_families(
        self,
        groups: dict[str, list[dict]],
    ) -> dict[str, list[dict]]:

        result = {}

        for family_name, units in (
            groups.items()
        ):

            units = sorted(
                units,
                key=self._unit_sort_key,
            )

            if (
                family_name
                == "review_and_special_content"
            ):
                # Review is intentionally a protected buffer.
                # It is not semantically safe to split by guessing.
                result[
                    family_name
                ] = units

                continue

            # --------------------------------------------------------
            # Coherent family under soft limit:
            # KEEP TOGETHER.
            # --------------------------------------------------------

            if len(units) <= (
                self.SOFT_LARGE_THRESHOLD
            ):
                result[
                    family_name
                ] = units

                continue

            # --------------------------------------------------------
            # Group by actual taxonomy category.
            # --------------------------------------------------------

            category_groups = defaultdict(list)

            for unit in units:

                category = self._normalize(
                    unit.get(
                        "taxonomy_category",
                        unit.get(
                            "subtopic",
                            "other",
                        ),
                    )
                )

                category_groups[
                    category
                ].append(
                    unit
                )

            # --------------------------------------------------------
            # If multiple coherent categories exist,
            # split at category boundaries.
            # --------------------------------------------------------

            if len(category_groups) > 1:

                for category, category_units in (
                    sorted(
                        category_groups.items()
                    )
                ):

                    category_units.sort(
                        key=self._unit_sort_key
                    )

                    key = (
                        f"{family_name}"
                        f"__{category}"
                    )

                    # A category itself can still be very large.
                    if len(category_units) > (
                        self.HARD_LARGE_THRESHOLD
                    ):

                        chunks = (
                            self._split_by_source_document(
                                category_units
                            )
                        )

                        if len(chunks) == 1:
                            chunks = (
                                self._chunk_units(
                                    category_units,
                                    self.HARD_LARGE_THRESHOLD,
                                )
                            )

                        for index, chunk in enumerate(
                            chunks,
                            start=1,
                        ):

                            chunk_key = (
                                key
                                if index == 1
                                else (
                                    f"{key}"
                                    f"__{index:02d}"
                                )
                            )

                            result[
                                chunk_key
                            ] = chunk

                    else:

                        result[
                            key
                        ] = category_units

                continue

            # --------------------------------------------------------
            # One homogeneous category.
            #
            # Don't split at 300.
            #
            # Split only once it becomes genuinely huge (>500).
            # Prefer source-document boundaries.
            # --------------------------------------------------------

            if len(units) <= (
                self.HARD_LARGE_THRESHOLD
            ):
                result[
                    family_name
                ] = units

                continue

            chunks = (
                self._split_by_source_document(
                    units
                )
            )

            if len(chunks) == 1:
                chunks = (
                    self._chunk_units(
                        units,
                        self.HARD_LARGE_THRESHOLD,
                    )
                )

            for index, chunk in enumerate(
                chunks,
                start=1,
            ):

                key = (
                    family_name
                    if index == 1
                    else (
                        f"{family_name}"
                        f"__{index:02d}"
                    )
                )

                result[
                    key
                ] = chunk

        return result

    # ================================================================
    # SOURCE-DOCUMENT SPLIT
    # ================================================================

    def _split_by_source_document(
        self,
        units: list[dict],
    ) -> list[list[dict]]:

        source_groups = defaultdict(list)

        for unit in units:

            source_groups[
                unit.get(
                    "source_document",
                    "",
                )
            ].append(
                unit
            )

        if len(source_groups) <= 1:
            return [units]

        ordered = sorted(
            source_groups.values(),
            key=lambda group: (
                -len(group),
                self._unit_sort_key(
                    group[0]
                ),
            ),
        )

        chunks = []

        current = []
        current_count = 0

        for source_units in ordered:

            size = len(
                source_units
            )

            if (
                current
                and current_count + size
                > self.HARD_LARGE_THRESHOLD
            ):
                chunks.append(
                    current
                )

                current = []
                current_count = 0

            current.extend(
                source_units
            )

            current_count += size

        if current:
            chunks.append(
                current
            )

        return chunks

    # ================================================================
    # FINAL DOCUMENT BUILD
    # ================================================================

    def _build_documents(
        self,
        groups: dict[str, list[dict]],
    ) -> list[dict]:

        documents = []

        for group_key in sorted(
            groups.keys()
        ):

            units = sorted(
                groups[group_key],
                key=self._unit_sort_key,
            )

            family_key = (
                group_key.split(
                    "__",
                    1,
                )[0]
            )

            family_rule = (
                self.FAMILY_RULES.get(
                    family_key
                )
            )

            if family_rule:

                title = family_rule[
                    "title"
                ]

            elif (
                family_key
                == "review_and_special_content"
            ):

                title = (
                    "Review and Special Content"
                )

            else:

                title = (
                    self._display_name(
                        family_key
                    )
                )

            topics = sorted(
                {
                    unit.get(
                        "topic",
                        "other",
                    )
                    for unit in units
                }
            )

            taxonomy_categories = sorted(
                {
                    self._taxonomy_key(
                        unit
                    )
                    for unit in units
                }
            )

            source_documents = sorted(
                {
                    unit[
                        "source_document"
                    ]
                    for unit in units
                }
            )

            documents.append(
                {
                    "document_id": (
                        group_key
                    ),

                    "filename": (
                        f"{group_key}.docx"
                    ),

                    "title": title,

                    "topics": topics,

                    "taxonomy_categories": (
                        taxonomy_categories
                    ),

                    "source_documents": (
                        source_documents
                    ),

                    "unit_count": len(
                        units
                    ),

                    "units": units,
                }
            )

        return documents

    # ================================================================
    # TAXONOMY KEY
    # ================================================================

    def _taxonomy_key(
        self,
        unit: dict,
    ) -> str:

        domain = self._normalize(
            unit.get(
                "taxonomy_domain",
                unit.get(
                    "topic",
                    "other",
                ),
            )
        )

        category = self._normalize(
            unit.get(
                "taxonomy_category",
                unit.get(
                    "subtopic",
                    "other",
                ),
            )
        )

        subcategory = self._normalize(
            unit.get(
                "taxonomy_subcategory",
                category,
            )
        )

        return (
            f"{domain}/"
            f"{category}/"
            f"{subcategory}"
        )

    # ================================================================
    # UNIT SORT
    # ================================================================

    def _unit_sort_key(
        self,
        unit: dict,
    ) -> tuple:

        try:
            page_index = int(
                unit.get(
                    "page_index",
                    0,
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            page_index = 0

        try:
            section_index = int(
                unit.get(
                    "section_index",
                    0,
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            section_index = 0

        return (
            unit.get(
                "source_document",
                "",
            ),
            page_index,
            section_index,
        )

    # ================================================================
    # NORMALIZATION
    # ================================================================

    def _normalize(
        self,
        value: str,
    ) -> str:

        value = (
            value or ""
        ).strip().lower()

        value = re.sub(
            r"[^a-z0-9]+",
            "_",
            value,
        )

        value = re.sub(
            r"_+",
            "_",
            value,
        )

        return (
            value.strip("_")
            or "other"
        )

    # ================================================================
    # DISPLAY NAME
    # ================================================================

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

    # ================================================================
    # UNIT CHUNKING
    # ================================================================

    def _chunk_units(
        self,
        units: list[dict],
        limit: int,
    ) -> list[list[dict]]:

        units = sorted(
            units,
            key=self._unit_sort_key,
        )

        return [
            units[
                start:
                start + limit
            ]
            for start in range(
                0,
                len(units),
                limit,
            )
        ]

    # ================================================================
    # COVERAGE VALIDATION
    # ================================================================

    def _validate_coverage(
        self,
        input_units: list[dict],
        documents: list[dict],
    ) -> None:

        input_ids = [
            unit["unit_id"]
            for unit in input_units
        ]

        planned_ids = [
            unit["unit_id"]
            for document in documents
            for unit in document["units"]
        ]

        duplicates_input = (
            self._duplicates(
                input_ids
            )
        )

        duplicates_planned = (
            self._duplicates(
                planned_ids
            )
        )

        if duplicates_input:
            raise ValueError(
                "Duplicate input unit IDs: "
                f"{duplicates_input}"
            )

        if duplicates_planned:
            raise ValueError(
                "Duplicate planned unit IDs: "
                f"{duplicates_planned}"
            )

        missing = sorted(
            set(input_ids)
            - set(planned_ids)
        )

        extra = sorted(
            set(planned_ids)
            - set(input_ids)
        )

        if missing:
            raise ValueError(
                "Knowledge units were lost: "
                f"{missing}"
            )

        if extra:
            raise ValueError(
                "Unknown units were added: "
                f"{extra}"
            )

        if len(input_ids) != len(
            planned_ids
        ):
            raise ValueError(
                "Coverage mismatch."
            )

    # ================================================================
    # DUPLICATES
    # ================================================================

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


if __name__ == "__main__":

    print(
        "KnowledgeRAGPlanner"
    )

    print(
        "Phase 8.4 — Universal Dynamic RAG Planner"
    )
