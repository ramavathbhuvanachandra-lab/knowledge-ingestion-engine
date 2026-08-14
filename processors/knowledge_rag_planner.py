"""
Phase 8.4 — Universal Dynamic RAG Document Planner

This planner is college-agnostic.

Input
-----
8.3 knowledge_units.json

Output
------
rag_plan.json
rag_review_report.json

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
8. Only RAG-eligible units are planned into Stage 3.
9. EXCLUDE units never enter the Stage 3 RAG plan.
10. REVIEW / AGGREGATE_ONLY units are preserved in a review report,
    but are not silently placed into the final RAG.
11. Every eligible RAG unit appears exactly once.
12. No LLM.
13. No chunking for normal groups.
14. No embeddings.
15. No vector database.
16. No DOCX generation.
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
            },
            "categories": {
                "fees",
                "fellowships_and_stipends",
                "financial_assistance",
                "scholarships",
                "finance",
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
                "governance",
                "administration",
            },
        },

        "events_and_notices": {
            "title": "Events and Notices",
            "domains": {
                "events_and_activities",
                "notices_and_announcements",
            },
            "categories": {
                "events",
                "seminars_and_workshops",
                "general_announcements",
                "notices",
            },
        },

        "college_overview": {
            "title": "Institute Overview",
            "domains": {
                "college_overview",
                "institutes_centres_and_units",
            },
            "categories": {
                "college_overview",
                "institute_overview",
            },
        },

        # Kept as a compatibility fallback only.
        # REVIEW units are no longer planned here.
        "review_and_special_content": {
            "title": "Review and Special Content",
            "domains": {
                "review",
            },
            "categories": {
                "ambiguous",
                "uncategorized",
                "weak_classification",
            },
        },
    }

    # ================================================================
    # INITIALIZATION
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

        domain_root = (
            self.organized_root / domain
        )

        if not domain_root.exists():
            raise FileNotFoundError(
                f"Organized domain does not exist: "
                f"{domain_root}"
            )

        if not domain_root.is_dir():
            raise ValueError(
                f"Organized domain is not a directory: "
                f"{domain_root}"
            )

        manifest_path = (
            domain_root / "knowledge_units.json"
        )

        if not manifest_path.exists():
            raise FileNotFoundError(
                f"Knowledge manifest does not exist: "
                f"{manifest_path}"
            )

        manifest = self._load_json(
            manifest_path
        )

        all_units = manifest.get(
            "units",
            [],
        )

        if not isinstance(
            all_units,
            list,
        ):
            raise ValueError(
                "'units' in knowledge_units.json "
                "must be a list."
            )

        # ------------------------------------------------------------
        # RAG ELIGIBILITY GATE
        # ------------------------------------------------------------

        eligible_units = []
        excluded_units = []
        review_units = []
        aggregate_units = []
        unknown_status_units = []

        rag_tier_counts = Counter()
        rag_status_counts = Counter()

        for unit in all_units:

            rag = unit.get(
                "rag",
                {},
            )

            if not isinstance(
                rag,
                dict,
            ):
                rag = {}

            status = str(
                rag.get(
                    "status",
                    "",
                )
            ).upper()

            tier = rag.get(
                "tier"
            )

            if status == "KEEP":

                eligible_units.append(
                    unit
                )

                if tier:
                    rag_tier_counts[
                        str(tier)
                    ] += 1

                rag_status_counts[
                    "KEEP"
                ] += 1

            elif status == "EXCLUDE":

                excluded_units.append(
                    unit
                )

                rag_status_counts[
                    "EXCLUDE"
                ] += 1

                if tier:
                    rag_tier_counts[
                        str(tier)
                    ] += 1

            elif status == "REVIEW":

                review_units.append(
                    unit
                )

                rag_status_counts[
                    "REVIEW"
                ] += 1

            elif status == "AGGREGATE_ONLY":

                aggregate_units.append(
                    unit
                )

                rag_status_counts[
                    "AGGREGATE_ONLY"
                ] += 1

            else:

                unknown_status_units.append(
                    unit
                )

                rag_status_counts[
                    "UNKNOWN"
                ] += 1

                # Safety-first behavior:
                # unknown RAG status never silently enters
                # the final student RAG.
                review_units.append(
                    unit
                )

        # ------------------------------------------------------------
        # HARD SAFETY CHECK
        # ------------------------------------------------------------

        if unknown_status_units:

            unit_ids = [
                unit.get(
                    "unit_id"
                )
                for unit in unknown_status_units
            ]

            raise ValueError(
                "Knowledge units contain unknown/missing "
                f"RAG status: {unit_ids[:20]}"
            )

        # ------------------------------------------------------------
        # DEDUPLICATION CHECK
        # ------------------------------------------------------------

        self._validate_unique_ids(
            all_units,
            label="input knowledge units",
        )

        self._validate_unique_ids(
            eligible_units,
            label="RAG eligible units",
        )

        # ------------------------------------------------------------
        # BUILD SEMANTIC GROUPS
        # ------------------------------------------------------------

        groups: dict[
            str,
            list[dict]
        ] = defaultdict(list)

        for unit in eligible_units:

            family = self._resolve_family(
                unit
            )

            groups[
                family
            ].append(
                unit
            )

        groups = self._merge_tiny_families(
            groups
        )

        groups = self._split_large_families(
            groups
        )

        documents = self._build_documents(
            groups
        )

        # ------------------------------------------------------------
        # ELIGIBLE UNIT COVERAGE
        # ------------------------------------------------------------

        self._validate_coverage(
            eligible_units,
            documents,
        )

        # ------------------------------------------------------------
        # REVIEW REPORT
        # ------------------------------------------------------------

        review_report = (
            self._build_review_report(
                domain=domain,
                all_units=all_units,
                excluded_units=excluded_units,
                review_units=review_units,
                aggregate_units=aggregate_units,
                rag_tier_counts=rag_tier_counts,
                rag_status_counts=rag_status_counts,
            )
        )

        review_path = (
            domain_root
            / "rag_review_report.json"
        )

        review_path.write_text(
            json.dumps(
                review_report,
                indent=4,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        # ------------------------------------------------------------
        # FINAL PLAN
        # ------------------------------------------------------------

        plan = {
            "phase": "8.4",
            "planner": (
                "universal_dynamic_rag_planner"
            ),
            "domain": domain,

            "input_units": len(
                all_units
            ),

            "rag_eligible_units": len(
                eligible_units
            ),

            "excluded_units": len(
                excluded_units
            ),

            "review_units": len(
                review_units
            ),

            "aggregate_only_units": len(
                aggregate_units
            ),

            "rag_documents": len(
                documents
            ),

            "rag_tier_counts": dict(
                sorted(
                    rag_tier_counts.items()
                )
            ),

            "rag_status_counts": dict(
                sorted(
                    rag_status_counts.items()
                )
            ),

            "taxonomy_counts": dict(
                sorted(
                    self._taxonomy_counts(
                        eligible_units
                    ).items()
                )
            ),

            "coverage": {
                "input_units": len(
                    all_units
                ),

                "eligible_units": len(
                    eligible_units
                ),

                "planned_units": sum(
                    document[
                        "unit_count"
                    ]
                    for document in documents
                ),

                "excluded_units": len(
                    excluded_units
                ),

                "review_units": len(
                    review_units
                ),

                "aggregate_only_units": len(
                    aggregate_units
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
            plan[
                "input_units"
            ],
        )

        print(
            "RAG eligible units:",
            plan[
                "rag_eligible_units"
            ],
        )

        print(
            "Tier A kept:",
            plan[
                "rag_tier_counts"
            ].get(
                "A",
                0,
            ),
        )

        print(
            "Tier B kept:",
            plan[
                "rag_tier_counts"
            ].get(
                "B",
                0,
            ),
        )

        print(
            "Tier C kept:",
            plan[
                "rag_tier_counts"
            ].get(
                "C",
                0,
            ),
        )

        print(
            "Tier D excluded:",
            plan[
                "rag_tier_counts"
            ].get(
                "D",
                0,
            ),
        )

        print(
            "Review:",
            plan[
                "review_units"
            ],
        )

        print(
            "Aggregate-only:",
            plan[
                "aggregate_only_units"
            ],
        )

        print(
            "Excluded:",
            plan[
                "excluded_units"
            ],
        )

        print(
            "RAG documents:",
            plan[
                "rag_documents"
            ],
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
        print(
            "RAG DOCUMENT PLAN"
        )

        for document in documents:

            print(
                f"{document['filename']:60}"
                f" → "
                f"{document['unit_count']:4} units"
            )

        print()

        print(
            "Review report:",
            review_path,
        )

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
                domain
                in rule[
                    "domains"
                ]
                and category
                in rule[
                    "categories"
                ]
            ):

                matches.append(
                    family_name
                )

        if matches:

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
            "college_overview",
        )

    # ================================================================
    # SMALL GROUP MERGING
    # ================================================================

    def _merge_tiny_families(
        self,
        groups: dict[
            str,
            list[dict]
        ],
    ) -> dict[
        str,
        list[dict]
    ]:

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
        groups: dict[
            str,
            list[dict]
        ],
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
                for unit in source_units
            }

            target_categories = {
                self._normalize(
                    unit.get(
                        "taxonomy_category",
                        "",
                    )
                )
                for unit in target_units
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
        groups: dict[
            str,
            list[dict]
        ],
    ) -> dict[
        str,
        list[dict]
    ]:

        result = {}

        for family_name, units in (
            groups.items()
        ):

            units = sorted(
                units,
                key=self._unit_sort_key,
            )

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

            category_groups = defaultdict(
                list
            )

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
            # Multiple coherent categories.
            # --------------------------------------------------------

            if len(category_groups) > 1:

                for (
                    category,
                    category_units,
                ) in sorted(
                    category_groups.items()
                ):

                    category_units.sort(
                        key=self._unit_sort_key
                    )

                    key = (
                        f"{family_name}"
                        f"__{category}"
                    )

                    if len(
                        category_units
                    ) > (
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
            # Split only if genuinely huge.
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
    ) -> list[
        list[dict]
    ]:

        source_groups = defaultdict(
            list
        )

        for unit in units:

            source_groups[
                unit.get(
                    "source_document",
                    "",
                )
            ].append(
                unit
            )

        if len(
            source_groups
        ) <= 1:

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
        groups: dict[
            str,
            list[dict]
        ],
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
                    unit.get(
                        "source_document",
                        "",
                    )
                    for unit in units
                }
            )

            tier_counts = Counter()

            for unit in units:

                rag = unit.get(
                    "rag",
                    {},
                )

                tier = rag.get(
                    "tier"
                )

                if tier:

                    tier_counts[
                        str(tier)
                    ] += 1

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

                    "tier_counts": dict(
                        sorted(
                            tier_counts.items()
                        )
                    ),

                    "unit_count": len(
                        units
                    ),

                    "units": units,
                }
            )

        return documents

    # ================================================================
    # REVIEW REPORT
    # ================================================================

    def _build_review_report(
        self,
        *,
        domain: str,
        all_units: list[dict],
        excluded_units: list[dict],
        review_units: list[dict],
        aggregate_units: list[dict],
        rag_tier_counts: Counter,
        rag_status_counts: Counter,
    ) -> dict:

        def compact_unit(
            unit: dict,
        ) -> dict:

            rag = unit.get(
                "rag",
                {},
            )

            return {
                "unit_id": unit.get(
                    "unit_id"
                ),

                "heading": unit.get(
                    "heading"
                ),

                "source_document": unit.get(
                    "source_document_name",
                    unit.get(
                        "source_document"
                    ),
                ),

                "source_url": unit.get(
                    "source_url"
                ),

                "taxonomy_domain": unit.get(
                    "taxonomy_domain"
                ),

                "taxonomy_category": unit.get(
                    "taxonomy_category"
                ),

                "taxonomy_subcategory": unit.get(
                    "taxonomy_subcategory"
                ),

                "rag_tier": rag.get(
                    "tier"
                ),

                "rag_status": rag.get(
                    "status"
                ),

                "rag_reason": rag.get(
                    "reason"
                ),

                "text_preview": (
                    str(
                        unit.get(
                            "text",
                            "",
                        )
                    ).strip()[:500]
                ),
            }

        return {
            "phase": "8.4",
            "domain": domain,

            "input_units": len(
                all_units
            ),

            "excluded_units": len(
                excluded_units
            ),

            "review_units": len(
                review_units
            ),

            "aggregate_only_units": len(
                aggregate_units
            ),

            "rag_tier_counts": dict(
                sorted(
                    rag_tier_counts.items()
                )
            ),

            "rag_status_counts": dict(
                sorted(
                    rag_status_counts.items()
                )
            ),

            "review": [
                compact_unit(
                    unit
                )
                for unit in review_units
            ],

            "aggregate_only": [
                compact_unit(
                    unit
                )
                for unit in aggregate_units
            ],

            "excluded_summary": [
                compact_unit(
                    unit
                )
                for unit in excluded_units
            ],
        }

    # ================================================================
    # TAXONOMY COUNTS
    # ================================================================

    def _taxonomy_counts(
        self,
        units: list[dict],
    ) -> Counter:

        counts = Counter()

        for unit in units:

            key = self._taxonomy_key(
                unit
            )

            counts[
                key
            ] += 1

        return counts

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

        return (
            value
            .strip()
            .title()
        )

    # ================================================================
    # UNIT CHUNKING
    # ================================================================

    def _chunk_units(
        self,
        units: list[dict],
        limit: int,
    ) -> list[
        list[dict]
    ]:

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
            unit[
                "unit_id"
            ]
            for unit in input_units
        ]

        planned_ids = [
            unit[
                "unit_id"
            ]
            for document in documents
            for unit in document[
                "units"
            ]
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
                "Duplicate eligible input "
                f"unit IDs: {duplicates_input}"
            )

        if duplicates_planned:

            raise ValueError(
                "Duplicate planned "
                f"unit IDs: {duplicates_planned}"
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
                "Eligible knowledge units "
                "were lost: "
                f"{missing}"
            )

        if extra:

            raise ValueError(
                "Unknown units were added: "
                f"{extra}"
            )

        if len(
            input_ids
        ) != len(
            planned_ids
        ):

            raise ValueError(
                "Eligible-unit coverage mismatch."
            )

    # ================================================================
    # UNIQUE IDS
    # ================================================================

    def _validate_unique_ids(
        self,
        units: list[dict],
        *,
        label: str,
    ) -> None:

        ids = [
            unit.get(
                "unit_id"
            )
            for unit in units
        ]

        duplicates = (
            self._duplicates(
                ids
            )
        )

        if duplicates:

            raise ValueError(
                f"Duplicate {label} IDs: "
                f"{duplicates}"
            )

    # ================================================================
    # JSON
    # ================================================================

    def _load_json(
        self,
        path: Path,
    ) -> dict:

        try:

            return json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )

        except json.JSONDecodeError as error:

            raise ValueError(
                f"Invalid JSON: {path}"
            ) from error

    # ================================================================
    # DUPLICATES
    # ================================================================

    def _duplicates(
        self,
        values: list[str | None],
    ) -> list[str]:

        seen = set()
        duplicates = set()

        for value in values:

            if value is None:
                continue

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
