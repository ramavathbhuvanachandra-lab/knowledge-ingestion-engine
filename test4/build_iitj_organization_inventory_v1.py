"""
IIT Jodhpur — Final Organization Inventory V3

Purpose
-------
Produce a deep, evidence-driven inventory of the FULL Command-3 accepted
IIT Jodhpur corpus before the IITJ-specific Command-5 organizer is designed.

This is an INSPECTION / PLANNING tool only.
It does not modify the frozen Command-4 baseline.
It does not create final organization folders.

The report is designed to answer:
1. What broad knowledge domains exist?
2. How much accepted content belongs to each domain?
3. What subtopics exist inside each domain?
4. What programs exist and how much evidence exists for each?
5. What departments/schools/academic units are actually present?
6. Which source documents contribute to each domain?
7. What content remains difficult to classify?

Important metadata rule
-----------------------
The normalized IITJ unit corpus may not preserve the original Command-3
knowledge_family consistently. Therefore family metadata is reported only as
observed metadata, while domain/subdomain inventory is derived from the actual
heading + source title + URL/path + content evidence.

The output is a planning inventory, not a final classifier.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_UNITS = (
    PROJECT_ROOT
    / "storage"
    / "test6_iitj_knowledge_units.json"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "storage_v2"
    / "planning"
    / "iitj_final_inventory"
)

JSON_OUTPUT = OUTPUT_DIR / "iitj_organization_inventory_final.json"
MARKDOWN_OUTPUT = OUTPUT_DIR / "iitj_organization_inventory_final.md"


ALLOWED_TIERS = {"A", "B", "REVIEW"}


# ---------------------------------------------------------------------------
# Broad domain vocabulary.
#
# These are intentionally broad planning categories. They are not the final
# IITJ Command-5 folders. Stronger evidence is obtained from headings/source
# context before a domain is counted.
# ---------------------------------------------------------------------------

DOMAIN_RULES = {
    "institute_overview": (
        "introduction",
        "overview",
        "about the institute",
        "about the college",
        "profile",
        "history",
        "vision",
        "mission",
        "objectives of the institute",
        "graduate attributes",
    ),
    "admissions": (
        "admission",
        "admissions",
        "eligibility for admission",
        "eligibility",
        "application",
        "applicant",
        "candidate",
        "reservation policy",
        "joining",
        "cancellation of admission",
        "special scheme",
        "foreign nationals",
        "inra",
    ),
    "academic_calendar_and_schedule": (
        "academic calendar",
        "academic session",
        "semester schedule",
        "semester dates",
        "session dates",
        "important dates",
        "vacation",
        "recess",
    ),
    "academic_registration_and_progression": (
        "registration",
        "late registration",
        "change of registration",
        "cancellation of registration",
        "academic performance",
        "continuation criteria",
        "continuation",
        "progress monitoring",
        "progress monitoring meeting",
        "qualifier requirements",
        "candidacy",
        "maximum duration",
        "academic load",
        "branch change",
        "academic leave",
        "semester withdrawal",
    ),
    "attendance_and_leave": (
        "attendance",
        "short leave",
        "medical leave",
        "leave of absence",
        "other leave",
        "leave",
    ),
    "courses_and_curriculum": (
        "course",
        "courses",
        "course category",
        "course categories",
        "curriculum",
        "syllabus",
        "credit",
        "credits",
        "course numbering",
        "course level",
        "auditing of courses",
        "student exchange programme",
        "minor",
        "major",
    ),
    "examinations_and_grading": (
        "examination",
        "examinations",
        "exam",
        "evaluation",
        "grading",
        "grade",
        "results",
        "comprehensive examination",
        "qualifying examination",
    ),
    "program_requirements_and_structure": (
        "program requirements",
        "programme requirements",
        "program structure",
        "structure of the program",
        "program objectives",
        "objectives of program",
        "learning outcomes",
        "graduate attributes",
        "degree requirements",
        "graduation requirements",
        "minimum residential requirement",
        "residential requirement",
    ),
    "departments_and_academic_units": (
        "department",
        "departments",
        "departmental",
        "school",
        "schools",
        "branch",
        "branches",
        "academic unit",
        "departmental code",
        "department code",
        "department undergraduate committee",
    ),
    "faculty_and_academic_staff": (
        "faculty",
        "professor",
        "associate professor",
        "assistant professor",
        "faculty advisor",
        "teaching staff",
        "hod",
        "head of department",
        "dean",
        "instructor",
        "faculty development",
    ),
    "research_and_doctoral": (
        "research",
        "research area",
        "research areas",
        "research project",
        "research proposal",
        "research supervisor",
        "supervisor",
        "thesis",
        "synopsis",
        "doctoral",
        "ph.d",
        "phd",
        "qualifier",
        "candidacy",
    ),
    "hostel_and_accommodation": (
        "hostel",
        "hostels",
        "accommodation",
        "residence",
        "residential",
        "mess",
        "warden",
    ),
    "fees_and_finance": (
        "fee",
        "fees",
        "tuition",
        "payment",
        "refund",
        "charge",
        "charges",
        "financial requirement",
        "no dues",
        "dues",
    ),
    "scholarships_assistantship_and_financial_aid": (
        "scholarship",
        "fellowship",
        "assistantship",
        "financial assistance",
        "financial aid",
        "stipend",
    ),
    "placements_and_careers": (
        "placement",
        "placements",
        "career",
        "careers",
        "recruitment",
        "recruiter",
        "employer",
        "campus placement",
    ),
    "infrastructure_facilities_and_equipment": (
        "facility",
        "facilities",
        "infrastructure",
        "laboratory",
        "laboratories",
        "lab",
        "library",
        "workshop",
        "equipment",
        "machine",
        "testing machine",
        "sports",
    ),
    "student_services_and_welfare": (
        "student services",
        "student welfare",
        "student support",
        "grievance",
        "counselling",
        "counseling",
        "wellbeing",
        "well-being",
        "student exchange",
        "visiting students",
    ),
    "rules_regulations_and_policies": (
        "rule",
        "rules",
        "regulation",
        "regulations",
        "policy",
        "policies",
        "guideline",
        "guidelines",
        "ordinance",
        "amendment",
        "amendments",
    ),
    "contacts_and_emergency": (
        "contact",
        "contacts",
        "phone",
        "telephone",
        "email",
        "address",
        "emergency",
    ),
    "other_institutional_information": (),
}


PROGRAM_PATTERNS = {
    "btech": (
        r"\bb\.?\s*tech\b",
        r"\bbtech\b",
        r"\bbachelor\s+of\s+technology\b",
        r"\bbachelor'?s\s+of\s+technology\b",
    ),
    "mtech": (
        r"\bm\.?\s*tech\b",
        r"\bmtech\b",
        r"\bmaster\s+of\s+technology\b",
    ),
    "msc": (
        r"\bm\.?\s*sc\b",
        r"\bmsc\b",
        r"\bmaster\s+of\s+science\b",
    ),
    "phd": (
        r"\bph\.?\s*d\b",
        r"\bphd\b",
        r"\bdoctor(?:al|ate)\b",
    ),
    "mba": (
        r"\bm\.?\s*b\.?\s*a\b",
        r"\bmba\b",
        r"\bmaster\s+of\s+business\s+administration\b",
    ),
    "bcom": (
        r"\bb\.?\s*com\b",
        r"\bbcom\b",
        r"\bbachelor\s+of\s+commerce\b",
    ),
    "ba": (
        r"\bb\.?\s*a\b",
        r"\bbachelor\s+of\s+arts\b",
    ),
    "bba": (
        r"\bb\.?\s*b\.?\s*a\b",
        r"\bbba\b",
        r"\bbachelor\s+of\s+business\s+administration\b",
    ),
    "bdes": (
        r"\bb\.?\s*des\b",
        r"\bbdes\b",
        r"\bmaster\s+of\s+design\b",
        r"\bmaster\s+design\b",
    ),
    "bs": (
        r"\bb\.?\s*s\b",
        r"\bbs\b",
        r"\bbachelor\s+of\s+science\b",
    ),
}


# Generic program terms are useful as a separate measure because they capture
# program-related information that may not name a degree.
PROGRAM_FAMILY_SIGNALS = (
    "program",
    "programme",
    "programs",
    "programmes",
    "dual degree",
    "minor",
    "major",
    "degree",
)


DEPARTMENT_ENTITY_TYPES = {
    "department",
    "school",
    "academic_unit",
}


# ---------------------------------------------------------------------------
# Explicit IITJ-style department names commonly present in institutional
# departmental-code tables. These are ONLY used to detect evidence in the
# corpus, never to create empty output folders.
# ---------------------------------------------------------------------------

KNOWN_IITJ_DEPARTMENT_TERMS = (
    "mechanical engineering",
    "computer science and engineering",
    "electrical engineering",
    "civil and infrastructure engineering",
    "chemical engineering",
    "bioscience and bioengineering",
    "metallurgical and materials engineering",
    "metallurgical & materials engineering",
    "chemistry",
    "mathematics",
    "physics",
    "humanities and social science",
    "humanities and social sciences",
)


def normalize(value: Any) -> str:
    text = str(value or "").lower()
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9.\-]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def load_units() -> list[dict[str, Any]]:
    if not INPUT_UNITS.exists():
        raise FileNotFoundError(
            f"Missing IITJ normalized units: {INPUT_UNITS}"
        )

    data = json.loads(
        INPUT_UNITS.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(data, list):
        raise ValueError(
            "Expected test6_iitj_knowledge_units.json to contain a list."
        )

    return [
        dict(item)
        for item in data
        if isinstance(item, dict)
    ]


def classify_tier(
    value_filter: Any,
    unit: dict[str, Any],
) -> str:
    heading = str(
        unit.get("heading", "")
    ).strip()

    text = str(
        unit.get(
            "text",
            unit.get("content", ""),
        )
    ).strip()

    source_file = str(
        unit.get("source_file", "")
    ).strip()

    source_title = str(
        unit.get("source_title", "")
    ).strip()

    source_url = str(
        unit.get(
            "source_url",
            unit.get("url", ""),
        )
    ).strip()

    content_type = str(
        unit.get(
            "source_document_type",
            unit.get("content_type", ""),
        )
    ).strip()

    section_path = unit.get(
        "section_path",
        [],
    )

    if not isinstance(section_path, list):
        section_path = []

    result = value_filter.classify(
        heading=heading,
        text=text,
        source_name=(
            Path(source_file).name
            if source_file
            else ""
        ),
        document_title=source_title,
        document_url=source_url,
        content_type=content_type,
        section_path=section_path,
    )

    tier = str(
        result.get(
            "tier",
            result.get(
                "classification",
                result.get(
                    "decision",
                    "",
                ),
            ),
        )
    ).strip().upper()

    if tier not in {
        "A",
        "B",
        "REVIEW",
        "C",
        "D",
    }:
        raise ValueError(
            f"Unexpected Command-3 tier {tier!r} for "
            f"{unit.get('unit_id')}"
        )

    return tier


def extract_entities(
    unit: dict[str, Any],
) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []

    raw_entities = unit.get(
        "entities",
        [],
    )

    if isinstance(
        raw_entities,
        list,
    ):
        for item in raw_entities:

            if isinstance(item, str):
                name = item.strip()

                if name:
                    result.append(
                        {
                            "name": name,
                            "entity_type": "unknown",
                        }
                    )

            elif isinstance(item, dict):

                name = str(
                    item.get(
                        "name",
                        item.get(
                            "entity_name",
                            "",
                        ),
                    )
                ).strip()

                entity_type = str(
                    item.get(
                        "entity_type",
                        item.get(
                            "type",
                            "unknown",
                        ),
                    )
                ).strip().lower() or "unknown"

                if name:
                    result.append(
                        {
                            "name": name,
                            "entity_type": entity_type,
                        }
                    )

    direct_name = str(
        unit.get(
            "entity",
            unit.get(
                "entity_name",
                "",
            ),
        )
    ).strip()

    direct_type = str(
        unit.get(
            "entity_type",
            "unknown",
        )
    ).strip().lower() or "unknown"

    if direct_name:
        result.append(
            {
                "name": direct_name,
                "entity_type": direct_type,
            }
        )

    department = str(
        unit.get(
            "department",
            "",
        )
    ).strip()

    if department:
        result.append(
            {
                "name": department,
                "entity_type": "department",
            }
        )

    unique: dict[
        tuple[str, str],
        dict[str, str],
    ] = {}

    for item in result:

        key = (
            normalize(item["name"]),
            item["entity_type"],
        )

        if key[0]:
            unique[key] = item

    return list(
        unique.values()
    )


def domain_scores(
    heading: str,
    title: str,
    url: str,
    text: str,
) -> list[tuple[str, int]]:
    """
    Produce planning-only candidate scores.

    Evidence weight:
        heading      12
        source title  8
        URL/path      6
        body          2

    This ranking is for inventory inspection, not final routing.
    """
    fields = {
        "heading": normalize(heading),
        "title": normalize(title),
        "url": normalize(url),
        "body": normalize(text[:2200]),
    }

    weights = {
        "heading": 12,
        "title": 8,
        "url": 6,
        "body": 2,
    }

    scores = Counter()

    for domain, signals in DOMAIN_RULES.items():

        if not signals:
            continue

        for signal in signals:

            signal_n = normalize(signal)

            if not signal_n:
                continue

            for field_name, field_value in fields.items():

                if signal_n in field_value:
                    scores[domain] += weights[field_name]

    if not scores:
        return [
            (
                "other_institutional_information",
                0,
            )
        ]

    return sorted(
        scores.items(),
        key=lambda item: (
            -item[1],
            item[0],
        ),
    )


def detect_programs(text: str) -> list[str]:
    normalized = text.lower()
    found = []

    for program, patterns in PROGRAM_PATTERNS.items():

        if any(
            re.search(
                pattern,
                normalized,
            )
            for pattern in patterns
        ):
            found.append(
                program
            )

    return sorted(
        set(found)
    )


def detect_department_terms(
    heading: str,
    title: str,
    url: str,
    text: str,
) -> list[str]:
    corpus = normalize(
        " ".join(
            [
                heading,
                title,
                url,
                text[:2500],
            ]
        )
    )

    matches = []

    for department in (
        KNOWN_IITJ_DEPARTMENT_TERMS
    ):

        if normalize(department) in corpus:
            matches.append(
                department
            )

    return sorted(
        set(matches)
    )


def build_inventory(
    units: list[dict[str, Any]],
) -> dict[str, Any]:

    # Import locally so missing project dependencies produce a clear error.
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )

    from processors.knowledge_value_filter import (
        KnowledgeValueFilter,
    )

    value_filter = (
        KnowledgeValueFilter()
    )

    tier_counts = Counter()

    accepted_units = []

    domain_counts = Counter()

    domain_unit_ids = defaultdict(list)

    domain_subtopics = defaultdict(Counter)

    domain_sources = defaultdict(Counter)

    source_counts = Counter()

    source_titles = {}

    explicit_entities = Counter()

    explicit_entity_unit_ids = defaultdict(list)

    department_evidence = Counter()

    department_unit_ids = defaultdict(list)

    program_counts = Counter()

    program_unit_ids = defaultdict(list)

    program_domain_counts = defaultdict(Counter)

    heading_counts = Counter()

    unresolved_units = []

    for unit in units:

        tier = classify_tier(
            value_filter,
            unit,
        )

        tier_counts[tier] += 1

        if tier not in ALLOWED_TIERS:
            continue

        accepted_units.append(
            unit
        )

        unit_id = str(
            unit.get(
                "unit_id",
                "",
            )
        )

        heading = str(
            unit.get(
                "heading",
                "",
            )
        ).strip()

        title = str(
            unit.get(
                "source_title",
                "",
            )
        ).strip()

        url = str(
            unit.get(
                "source_url",
                unit.get(
                    "url",
                    "",
                ),
            )
        ).strip()

        source_file = str(
            unit.get(
                "source_file",
                "",
            )
        ).strip()

        text = str(
            unit.get(
                "text",
                unit.get(
                    "content",
                    "",
                ),
            )
        ).strip()

        source_counts[
            source_file
        ] += 1

        if title:
            source_titles[
                source_file
            ] = title

        heading_n = normalize(
            heading
        )

        if heading_n:
            heading_counts[
                heading_n
            ] += 1

        # --------------------------------------------------------------
        # Candidate domain ranking.
        # --------------------------------------------------------------

        ranked_domains = domain_scores(
            heading,
            title,
            url,
            text,
        )

        top_domain, top_score = (
            ranked_domains[0]
        )

        domain_counts[
            top_domain
        ] += 1

        domain_unit_ids[
            top_domain
        ].append(
            unit_id
        )

        # A more human-readable subtopic label is derived conservatively
        # from the heading. It is used only for inventory counts.
        heading_words = [
            word
            for word in re.split(
                r"\s+",
                heading,
            )
            if word
        ]

        if heading_words:
            subtopic = " ".join(
                heading_words[:8]
            ).strip()

            domain_subtopics[
                top_domain
            ][subtopic] += 1

        domain_sources[
            top_domain
        ][source_file] += 1

        # --------------------------------------------------------------
        # Explicit entity metadata.
        # --------------------------------------------------------------

        entities = extract_entities(
            unit
        )

        for entity in entities:

            key = (
                normalize(
                    entity["name"]
                ),
                entity["entity_type"],
            )

            explicit_entities[
                key
            ] += 1

            explicit_entity_unit_ids[
                key
            ].append(
                unit_id
            )

        # --------------------------------------------------------------
        # Department evidence from actual IITJ department terminology.
        # This is a corpus-evidence report, not a hardcoded output taxonomy.
        # --------------------------------------------------------------

        departments = (
            detect_department_terms(
                heading,
                title,
                url,
                text,
            )
        )

        for department in departments:

            department_evidence[
                department
            ] += 1

            department_unit_ids[
                department
            ].append(
                unit_id
            )

        # --------------------------------------------------------------
        # Program evidence.
        # --------------------------------------------------------------

        programs = detect_programs(
            f"{heading} {title} {url} {text}"
        )

        for program in programs:

            program_counts[
                program
            ] += 1

            program_unit_ids[
                program
            ].append(
                unit_id
            )

            program_domain_counts[
                program
            ][
                top_domain
            ] += 1

        # --------------------------------------------------------------
        # Low-signal / unresolved report.
        # --------------------------------------------------------------

        if (
            top_domain
            == "other_institutional_information"
            or top_score < 8
        ):
            unresolved_units.append(
                {
                    "unit_id": unit_id,
                    "heading": heading,
                    "source_file": source_file,
                    "top_domain": top_domain,
                    "score": top_score,
                    "programs": programs,
                }
            )

    # -----------------------------------------------------------------------
    # Convert counters into deterministic JSON rows.
    # -----------------------------------------------------------------------

    domains = []

    for domain, count in sorted(
        domain_counts.items(),
        key=lambda item: (
            -item[1],
            item[0],
        ),
    ):

        domains.append(
            {
                "domain": domain,
                "unit_count": count,
                "unit_ids": sorted(
                    domain_unit_ids[
                        domain
                    ]
                ),
                "top_subtopics": [
                    {
                        "heading": heading,
                        "unit_count": count,
                    }
                    for heading, count in (
                        domain_subtopics[
                            domain
                        ].most_common(40)
                    )
                ],
                "source_documents": [
                    {
                        "source_file": source,
                        "unit_count": source_count,
                    }
                    for source, source_count in sorted(
                        domain_sources[
                            domain
                        ].items(),
                        key=lambda item: (
                            -item[1],
                            item[0],
                        ),
                    )[:30]
                ],
            }
        )

    department_rows = []

    for department, count in sorted(
        department_evidence.items(),
        key=lambda item: (
            -item[1],
            item[0],
        ),
    ):

        department_rows.append(
            {
                "department": department,
                "unit_count": count,
                "unit_ids": sorted(
                    department_unit_ids[
                        department
                    ]
                ),
            }
        )

    program_rows = []

    for program, count in sorted(
        program_counts.items(),
        key=lambda item: (
            -item[1],
            item[0],
        ),
    ):

        program_rows.append(
            {
                "program": program,
                "unit_count": count,
                "unit_ids": sorted(
                    program_unit_ids[
                        program
                    ]
                ),
                "top_domains": [
                    {
                        "domain": domain,
                        "unit_count": domain_count,
                    }
                    for domain, domain_count in sorted(
                        program_domain_counts[
                            program
                        ].items(),
                        key=lambda item: (
                            -item[1],
                            item[0],
                        ),
                    )
                ],
            }
        )

    entity_rows = []

    for (
        (
            entity_name,
            entity_type,
        ),
        count,
    ) in sorted(
        explicit_entities.items(),
        key=lambda item: (
            -item[1],
            item[0][1],
            item[0][0],
        ),
    ):

        entity_rows.append(
            {
                "name": entity_name,
                "entity_type": entity_type,
                "unit_count": count,
                "unit_ids": sorted(
                    explicit_entity_unit_ids[
                        (
                            entity_name,
                            entity_type,
                        )
                    ]
                ),
            }
        )

    observed_family_metadata = Counter(
        str(
            unit.get(
                "knowledge_family",
                unit.get(
                    "family",
                    "",
                ),
            )
        ).strip()
        or "<missing>"
        for unit in accepted_units
    )

    source_rows = [
        {
            "source_file": source,
            "unit_count": count,
            "source_title": source_titles.get(
                source,
                "",
            ),
        }
        for source, count in sorted(
            source_counts.items(),
            key=lambda item: (
                -item[1],
                item[0],
            ),
        )
    ]

    return {
        "inventory_version": "final-1.0",
        "purpose": (
            "Deep IIT Jodhpur accepted-corpus inventory for designing "
            "the IITJ-specific Command-5 organizer."
        ),
        "input": {
            "source": str(
                INPUT_UNITS
            ),
            "normalized_unit_count": len(
                units
            ),
            "accepted_unit_count": len(
                accepted_units
            ),
        },
        "command3_tiers": {
            tier: tier_counts.get(
                tier,
                0,
            )
            for tier in (
                "A",
                "B",
                "REVIEW",
                "C",
                "D",
            )
        },
        "observed_family_metadata": [
            {
                "family": family,
                "unit_count": count,
            }
            for family, count in sorted(
                observed_family_metadata.items(),
                key=lambda item: (
                    -item[1],
                    item[0],
                ),
            )
        ],
        "domains": domains,
        "departments": department_rows,
        "programs": program_rows,
        "explicit_entities": entity_rows,
        "source_documents": source_rows,
        "top_headings": [
            {
                "heading": heading,
                "unit_count": count,
            }
            for heading, count in (
                heading_counts.most_common(
                    250
                )
            )
        ],
        "unresolved_units": sorted(
            unresolved_units,
            key=lambda item: (
                item["source_file"],
                normalize(
                    item["heading"]
                ),
                item["unit_id"],
            ),
        ),
        "planning_guardrails": [
            "Do not create empty department or program folders.",
            "Do not use body mentions alone as final entity evidence.",
            "A program signal is not automatically a program entity.",
            "A department mention is not automatically department ownership.",
            "The final IITJ organization must be based on the approved specification.",
            "All accepted units must remain traceable and assigned exactly once.",
        ],
    }


def write_markdown(
    report: dict[str, Any]
) -> None:

    lines = [
        "# IIT Jodhpur — Final Organization Inventory V1",
        "",
        "This is the planning baseline for the IITJ-specific Command-5 organizer.",
        "",
        "## 1. Corpus size",
        "",
        f"- Normalized units: **{report['input']['normalized_unit_count']}**",
        f"- Accepted A/B/REVIEW units: **{report['input']['accepted_unit_count']}**",
        "",
        "## 2. Command-3 tiers",
        "",
    ]

    for tier, count in (
        report["command3_tiers"].items()
    ):
        lines.append(
            f"- {tier}: **{count}**"
        )

    lines.extend(
        [
            "",
            "## 3. Candidate domains",
            "",
            "| Domain | Accepted units |",
            "|---|---:|",
        ]
    )

    for domain in report["domains"]:
        lines.append(
            f"| {domain['domain']} | "
            f"{domain['unit_count']} |"
        )

    lines.extend(
        [
            "",
            "## 4. Domain details",
            "",
        ]
    )

    for domain in report["domains"]:

        lines.append(
            f"### {domain['domain']} "
            f"({domain['unit_count']} units)"
        )
        lines.append("")

        lines.append(
            "Top observed headings:"
        )

        for item in domain[
            "top_subtopics"
        ][:20]:
            lines.append(
                f"- {item['heading']} "
                f"({item['unit_count']})"
            )

        lines.append("")
        lines.append(
            "Largest source contributors:"
        )

        for item in domain[
            "source_documents"
        ][:15]:
            lines.append(
                f"- {item['source_file']} "
                f"({item['unit_count']})"
            )

        lines.append("")

    lines.extend(
        [
            "## 5. Departments / academic units",
            "",
        ]
    )

    if report["departments"]:

        lines.append(
            "| Department | Accepted units |"
        )
        lines.append(
            "|---|---:|"
        )

        for item in report["departments"]:

            lines.append(
                f"| {item['department']} | "
                f"{item['unit_count']} |"
            )

    else:
        lines.append(
            "No department evidence detected by the inventory."
        )

    lines.extend(
        [
            "",
            "## 6. Programs",
            "",
            "| Program | Accepted units |",
            "|---|---:|",
        ]
    )

    for program in report["programs"]:

        domains_text = ", ".join(
            f"{item['domain']} ({item['unit_count']})"
            for item in program[
                "top_domains"
            ][:8]
        )

        lines.append(
            f"| {program['program']} | "
            f"{program['unit_count']} |"
        )

        if domains_text:
            lines.append(
                f"  - Main candidate domains: {domains_text}"
            )

    lines.extend(
        [
            "",
            "## 7. Explicit entities",
            "",
        ]
    )

    for entity in report[
        "explicit_entities"
    ][:100]:

        lines.append(
            f"- **{entity['name']}** "
            f"({entity['entity_type']}) — "
            f"{entity['unit_count']} units"
        )

    lines.extend(
        [
            "",
            "## 8. Source documents",
            "",
            "| Source | Units |",
            "|---|---:|",
        ]
    )

    for source in report[
        "source_documents"
    ]:

        lines.append(
            f"| {source['source_file']} | "
            f"{source['unit_count']} |"
        )

    lines.extend(
        [
            "",
            "## 9. Unresolved / weakly signaled units",
            "",
            (
                "These are not rejected. They are simply units for which "
                "the planning inventory did not find strong domain evidence."
            ),
            "",
        ]
    )

    for item in report[
        "unresolved_units"
    ][:300]:

        lines.append(
            f"- `{item['unit_id']}` | "
            f"{item['heading']} | "
            f"{item['source_file']} | "
            f"candidate={item['top_domain']} | "
            f"score={item['score']}"
        )

    lines.extend(
        [
            "",
            "## 10. Planning guardrails",
            "",
        ]
    )

    for guardrail in report[
        "planning_guardrails"
    ]:
        lines.append(
            f"- {guardrail}"
        )

    lines.extend(
        [
            "",
            "## 11. Next step",
            "",
            "Freeze an IITJ-specific Command-5 organization specification "
            "from this inventory. Only then write the IITJ-specific organizer.",
            "",
        ]
    )

    MARKDOWN_OUTPUT.write_text(
        "\n".join(lines).rstrip() + "\n",
        encoding="utf-8",
    )


def main() -> None:

    print("=" * 100)
    print(
        "IIT JODHPUR — FINAL ORGANIZATION INVENTORY V1"
    )
    print("=" * 100)
    print()

    units = load_units()

    report = build_inventory(
        units
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    JSON_OUTPUT.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    write_markdown(
        report
    )

    print(
        "Normalized units:",
        report["input"]["normalized_unit_count"],
    )

    print(
        "Accepted A/B/REVIEW:",
        report["input"]["accepted_unit_count"],
    )

    print()

    print("DOMAIN SUMMARY")
    print("-" * 100)

    for item in report[
        "domains"
    ]:
        print(
            f"{item['unit_count']:>4}  "
            f"{item['domain']}"
        )

    print()

    print("DEPARTMENT EVIDENCE")
    print("-" * 100)

    if report["departments"]:

        for item in report[
            "departments"
        ]:
            print(
                f"{item['unit_count']:>4}  "
                f"{item['department']}"
            )

    else:
        print(
            "No department evidence detected."
        )

    print()

    print("PROGRAM SUMMARY")
    print("-" * 100)

    for item in report[
        "programs"
    ]:
        print(
            f"{item['unit_count']:>4}  "
            f"{item['program']}"
        )

    print()

    print("Reports")
    print(
        JSON_OUTPUT
    )
    print(
        MARKDOWN_OUTPUT
    )

    print()

    print("=" * 100)
    print(
        "FINAL IITJ INVENTORY COMPLETE"
    )
    print("=" * 100)


if __name__ == "__main__":
    main()