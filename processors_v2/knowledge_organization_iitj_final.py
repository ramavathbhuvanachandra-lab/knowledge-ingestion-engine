"""
IIT Jodhpur — Final Knowledge Organizer V2
=========================================

College-specific Command 5 organizer for IIT Jodhpur.

This module deliberately uses an IITJ-specific semantic contract rather than a
universal college taxonomy. Command 1-4 remain upstream; this organizer takes
the accepted A/B/REVIEW units and places every unit into the most appropriate
IITJ domain/entity/topic.

Core invariants
---------------
- Only A/B/REVIEW units may enter.
- Every accepted unit is assigned exactly once.
- No accepted content is deleted or rewritten.
- Department, school, research-platform, program, office and service entities
  have explicit first-class homes.
- Admission content has precedence over program routing.
- Entity documents are created only when an actual entity is detected.
- No artificial part_1 / part_2 fragmentation.
- Legitimate residual content is retained in named fallback buffers.
- Output is deterministic for identical input.

Recommended output
------------------
storage_v2/command5/iitj_final/
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


VERSION = "iitj_command5_final_v2"
ALLOWED_TIERS = {"A", "B", "REVIEW"}


# ---------------------------------------------------------------------------
# IITJ entity contract.
# ---------------------------------------------------------------------------

DEPARTMENT_ALIASES = {
    "aerospace_engineering": (
        "aerospace engineering",
        "aerospace",
    ),
    "bioscience_and_bioengineering": (
        "bioscience and bioengineering",
        "bioscience & bioengineering",
    ),
    "chemical_engineering": (
        "chemical engineering",
    ),
    "chemistry": (
        "chemistry",
    ),
    "civil_and_infrastructure_engineering": (
        "civil and infrastructure engineering",
    ),
    "computer_science_and_engineering": (
        "computer science and engineering",
        "computer science & engineering",
        "cse",
    ),
    "economics": (
        "economics",
    ),
    "electrical_engineering": (
        "electrical engineering",
        "ee",
    ),
    "electronics_engineering": (
        "electronics engineering",
    ),
    "energy_and_automotive_engineering": (
        "energy and automotive engineering",
    ),
    "environmental_and_sustainability_engineering": (
        "environmental and sustainability engineering",
        "env. & sustainability engineering",
        "env & sustainability engineering",
        "environmental engineering",
    ),
    "materials_engineering": (
        "materials engineering",
        "metallurgical and materials engineering",
        "metallurgical & materials engineering",
    ),
    "mathematics": (
        "mathematics",
    ),
    "mechanical_engineering": (
        "mechanical engineering",
        "me",
    ),
    "physics": (
        "physics",
    ),
}

DEPARTMENT_NAMES = {
    "aerospace_engineering": "Aerospace Engineering",
    "bioscience_and_bioengineering": "Bioscience and Bioengineering",
    "chemical_engineering": "Chemical Engineering",
    "chemistry": "Chemistry",
    "civil_and_infrastructure_engineering": "Civil and Infrastructure Engineering",
    "computer_science_and_engineering": "Computer Science and Engineering",
    "economics": "Economics",
    "electrical_engineering": "Electrical Engineering",
    "electronics_engineering": "Electronics Engineering",
    "energy_and_automotive_engineering": "Energy and Automotive Engineering",
    "environmental_and_sustainability_engineering": "Environmental and Sustainability Engineering",
    "materials_engineering": "Materials Engineering",
    "mathematics": "Mathematics",
    "mechanical_engineering": "Mechanical Engineering",
    "physics": "Physics",
}

SCHOOL_ALIASES = {
    "artificial_intelligence_and_data_science": (
        "school of artificial intelligence and data science",
        "school of artificial intelligence & data science",
        "saide",
    ),
    "design": (
        "school of design",
        "sod",
    ),
    "liberal_arts": (
        "school of liberal arts",
        "sola",
    ),
    "management_and_entrepreneurship": (
        "school of management and entrepreneurship",
        "school of management & entrepreneurship",
        "sme",
    ),
}

SCHOOL_NAMES = {
    "artificial_intelligence_and_data_science": "School of Artificial Intelligence and Data Science",
    "design": "School of Design",
    "liberal_arts": "School of Liberal Arts",
    "management_and_entrepreneurship": "School of Management and Entrepreneurship",
}

RESEARCH_PLATFORM_ALIASES = {
    "digital_humanities": (
        "digital humanities",
    ),
    "space_science_and_technology": (
        "space science and technology",
    ),
    "internet_of_things_and_applications": (
        "internet of things and applications",
        "iot and applications",
        "iot",
    ),
    "autonomous_unmanned_vehicles": (
        "autonomous unmanned vehicles",
        "auv",
    ),
    "quantum_information_and_computation": (
        "quantum information and computation",
        "quantum information",
    ),
    "cognitive_science": (
        "cognitive science",
    ),
    "smart_healthcare": (
        "smart healthcare",
    ),
}

RESEARCH_PLATFORM_NAMES = {
    "digital_humanities": "Digital Humanities",
    "space_science_and_technology": "Space Science and Technology",
    "internet_of_things_and_applications": "Internet of Things and Applications",
    "autonomous_unmanned_vehicles": "Autonomous Unmanned Vehicles",
    "quantum_information_and_computation": "Quantum Information and Computation",
    "cognitive_science": "Cognitive Science",
    "smart_healthcare": "Smart Healthcare",
}

PROGRAM_PATTERNS = {
    "btech": (
        r"\bb\.?\s*tech\b",
        r"\bbtech\b",
        r"\bbachelor\s+of\s+technology\b",
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
        r"\bdoctoral\b",
    ),
    "bs": (
        r"\bb\.?\s*s\b",
        r"\bbs\b",
        r"\bbachelor\s+of\s+science\b",
    ),
    "mba": (
        r"\bm\.?\s*b\.?\s*a\b",
        r"\bmba\b",
        r"\bmaster\s+of\s+business\s+administration\b",
    ),
    "bdes": (
        r"\bb\.?\s*des\b",
        r"\bbdes\b",
        r"\bmaster\s+of\s+design\b",
    ),
    "ms_by_research": (
        r"\bm\.?\s*s\.?\s+by\s+research\b",
        r"\bmaster\s+of\s+science\s+by\s+research\b",
    ),
}

PROGRAM_NAMES = {
    "btech": "B.Tech",
    "mtech": "M.Tech",
    "msc": "M.Sc",
    "phd": "Ph.D",
    "bs": "B.S",
    "mba": "MBA",
    "bdes": "B.Des",
    "ms_by_research": "M.S. by Research",
}

OFFICE_ALIASES = {
    "office_of_academics": (
        "office of academics",
        "office of academics affairs",
    ),
    "office_of_accounts": (
        "office of accounts",
    ),
    "office_of_alumni_affairs": (
        "office of alumni affairs",
    ),
    "office_of_corporate_relations": (
        "office of corporate relations",
    ),
    "office_of_deputy_director": (
        "office of deputy director",
        "deputy director",
    ),
    "office_of_director": (
        "office of director",
        "director office",
    ),
    "office_of_estate": (
        "office of estate",
    ),
    "office_of_internal_audit": (
        "office of internal audit",
        "internal audit",
    ),
    "office_of_international_relations": (
        "office of international relations",
        "international relations office",
        "iro",
    ),
    "office_of_registrar": (
        "office of registrar",
        "registrar office",
    ),
    "office_of_research_and_development": (
        "office of research development",
        "office of research and development",
    ),
    "office_of_resources_and_alumni": (
        "office of resources and alumni",
        "dora",
    ),
    "office_of_stores_and_purchase": (
        "office of stores and purchase",
        "stores and purchase",
    ),
}

OFFICE_NAMES = {
    "office_of_academics": "Office of Academics",
    "office_of_accounts": "Office of Accounts",
    "office_of_alumni_affairs": "Office of Alumni Affairs",
    "office_of_corporate_relations": "Office of Corporate Relations",
    "office_of_deputy_director": "Office of Deputy Director",
    "office_of_director": "Office of Director",
    "office_of_estate": "Office of Estate",
    "office_of_internal_audit": "Office of Internal Audit",
    "office_of_international_relations": "Office of International Relations",
    "office_of_registrar": "Office of Registrar",
    "office_of_research_and_development": "Office of Research and Development",
    "office_of_resources_and_alumni": "Office of Resources and Alumni",
    "office_of_stores_and_purchase": "Office of Stores and Purchase",
}

TOPIC_LABELS = {
    "overview": "Overview",
    "faculty": "Faculty",
    "research": "Research",
    "programs": "Programs",
    "curriculum": "Curriculum",
    "courses": "Courses and Curriculum",
    "requirements": "Requirements",
    "admissions": "Admissions",
    "academic_progression": "Academic Progression",
    "registration": "Registration",
    "examinations_and_grading": "Examinations and Grading",
    "academic_calendar": "Academic Calendar and Schedule",
    "attendance_and_leave": "Attendance and Leave",
    "fees_and_finance": "Fees and Finance",
    "scholarships": "Scholarships and Financial Aid",
    "facilities": "Facilities",
    "responsibilities": "Responsibilities and Services",
    "projects": "Projects",
    "positions": "Positions and Opportunities",
    "placements": "Placements and Careers",
    "international_relations": "International Relations",
    "alumni": "Alumni and Engagement",
    "training": "Training and Upskilling",
    "student_services": "Student Services and Welfare",
    "sustainability": "Sustainability",
    "contacts": "Contacts",
    "rules_and_regulations": "Rules and Regulations",
    "general_information": "General Information",
}


@dataclass(frozen=True)
class RoutedUnit:
    unit_id: str
    root: str
    topic: str
    entity_type: str | None
    entity_id: str | None
    entity_name: str | None
    buffer_name: str | None


def _norm(value: Any) -> str:
    text = str(value or "").lower()
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9.\-]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _slug(value: str) -> str:
    text = _norm(value).replace(" and ", "_and_")
    text = re.sub(r"[^a-z0-9_]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "general_information"


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _heading(unit: dict[str, Any]) -> str:
    return str(unit.get("heading", "")).strip()


def _text(unit: dict[str, Any]) -> str:
    return str(
        unit.get(
            "text",
            unit.get("content", ""),
        )
    ).strip()


def _source_file(unit: dict[str, Any]) -> str:
    return str(unit.get("source_file", "")).strip()


def _source_title(unit: dict[str, Any]) -> str:
    return str(unit.get("source_title", "")).strip()


def _source_url(unit: dict[str, Any]) -> str:
    return str(
        unit.get(
            "source_url",
            unit.get("url", ""),
        )
    ).strip()


def _unit_id(unit: dict[str, Any]) -> str:
    return str(unit.get("unit_id", "")).strip()


def _tier(unit: dict[str, Any]) -> str:
    return str(unit.get("tier", "")).strip().upper()


def _context(unit: dict[str, Any], body_limit: int = 2600) -> str:
    return " ".join(
        (
            _heading(unit),
            _source_title(unit),
            _source_url(unit),
            _source_file(unit),
            _text(unit)[:body_limit],
        )
    )


def _strong_context(unit: dict[str, Any]) -> str:
    return " ".join(
        (
            _heading(unit),
            _source_title(unit),
            _source_url(unit),
            _source_file(unit),
        )
    )


def _match_aliases(
    unit: dict[str, Any],
    alias_map: dict[str, tuple[str, ...]],
) -> tuple[str, str] | None:
    """
    Match an IITJ entity using strong structural metadata.

    Priority:
    1. exact/near-exact source filename stem
    2. source title / URL path
    3. heading

    Short aliases are only accepted as whole tokens. This prevents "ee" from
    matching unrelated words such as "electronics" and "me" from matching
    arbitrary text.
    """
    source_file = Path(
        _source_file(unit)
    ).stem

    fields = [
        _norm(source_file),
        _norm(_source_title(unit)),
        _norm(_source_url(unit)),
        _norm(_heading(unit)),
    ]

    if alias_map is DEPARTMENT_ALIASES:
        name_map = DEPARTMENT_NAMES
    elif alias_map is SCHOOL_ALIASES:
        name_map = SCHOOL_NAMES
    elif alias_map is RESEARCH_PLATFORM_ALIASES:
        name_map = RESEARCH_PLATFORM_NAMES
    elif alias_map is OFFICE_ALIASES:
        name_map = OFFICE_NAMES
    else:
        raise ValueError("Unknown IITJ alias map.")

    # Prefer the most specific/longest aliases first.
    candidates = []
    for entity_id, aliases in alias_map.items():
        for alias in aliases:
            candidates.append(
                (
                    len(_norm(alias)),
                    entity_id,
                    alias,
                )
            )

    for _, entity_id, alias in sorted(
        candidates,
        key=lambda item: (-item[0], item[1]),
    ):
        alias_n = _norm(alias)

        if not alias_n:
            continue

        for field_index, field in enumerate(fields):
            if not field:
                continue

            if len(alias_n.split()) == 1 and len(alias_n) <= 3:
                matched = bool(
                    re.search(
                        rf"\b{re.escape(alias_n)}\b",
                        field,
                    )
                )
            else:
                matched = alias_n in field

            if matched:
                return entity_id, name_map[entity_id]

    return None


def _explicit_entity(unit: dict[str, Any]) -> tuple[str, str] | None:
    name = str(
        unit.get(
            "entity",
            unit.get("entity_name", ""),
        )
    ).strip()

    entity_type = str(
        unit.get("entity_type", "")
    ).strip().lower()

    if name:
        return name, entity_type or "entity"

    return None


def _detect_department(unit: dict[str, Any]) -> tuple[str, str] | None:
    explicit = _explicit_entity(unit)

    if explicit:
        name, entity_type = explicit
        if entity_type in {
            "department",
            "school",
            "academic_unit",
        }:
            normalized = _norm(name)
            for key, aliases in DEPARTMENT_ALIASES.items():
                if any(_norm(alias) == normalized for alias in aliases):
                    return key, DEPARTMENT_NAMES[key]

    return _match_aliases(
        unit,
        DEPARTMENT_ALIASES,
    )


def _detect_school(unit: dict[str, Any]) -> tuple[str, str] | None:
    explicit = _explicit_entity(unit)

    if explicit:
        name, entity_type = explicit
        if entity_type in {
            "school",
            "academic_unit",
        }:
            normalized = _norm(name)
            for key, aliases in SCHOOL_ALIASES.items():
                if any(_norm(alias) == normalized for alias in aliases):
                    return key, SCHOOL_NAMES[key]

    return _match_aliases(
        unit,
        SCHOOL_ALIASES,
    )


def _detect_research_platform(
    unit: dict[str, Any]
) -> tuple[str, str] | None:
    return _match_aliases(
        unit,
        RESEARCH_PLATFORM_ALIASES,
    )


def _detect_office(unit: dict[str, Any]) -> tuple[str, str] | None:
    return _match_aliases(
        unit,
        OFFICE_ALIASES,
    )


def _detect_program(unit: dict[str, Any]) -> str | None:
    strong = _norm(_strong_context(unit))

    # Admissions routing uses the same program detection but has higher
    # precedence elsewhere.
    for program_id, patterns in PROGRAM_PATTERNS.items():
        if any(
            re.search(pattern, strong)
            for pattern in patterns
        ):
            return program_id

    return None


def _is_admission(unit: dict[str, Any]) -> bool:
    h = _norm(_heading(unit))
    return bool(
        re.search(
            r"\b(admission|admissions|eligibility for admission|"
            r"application process|how to apply|selection process|"
            r"shortlist|waitlist|seat matrix)\b",
            h,
        )
    )


def _is_hostel(unit: dict[str, Any]) -> bool:
    h = _norm(_heading(unit))
    body = _norm(_text(unit)[:1800])
    signals = (
        "hostel",
        "hostels",
        "accommodation",
        "residence",
        "residential",
        "mess",
        "warden",
        "dining",
    )
    return any(signal in h for signal in signals) or any(
        signal in body for signal in (
            "hostel",
            "accommodation",
            "mess",
        )
    )


def _is_contact(unit: dict[str, Any]) -> bool:
    h = _norm(_heading(unit))
    return any(
        signal in h
        for signal in (
            "contact",
            "contacts",
            "phone",
            "telephone",
            "email",
            "address",
            "emergency",
        )
    )


def _is_scholarship(unit: dict[str, Any]) -> bool:
    h = _norm(_heading(unit))
    return any(
        signal in h
        for signal in (
            "scholarship",
            "fellowship",
            "assistantship",
            "financial aid",
            "financial assistance",
            "student endowment",
            "stipend",
        )
    )


def _is_fee(unit: dict[str, Any]) -> bool:
    h = _norm(_heading(unit))
    return any(
        signal in h
        for signal in (
            "fee",
            "fees",
            "tuition",
            "fee structure",
            "payment",
            "refund",
            "charges",
            "dues",
        )
    )


def _is_placement(unit: dict[str, Any]) -> bool:
    h = _norm(_heading(unit))
    return any(
        signal in h
        for signal in (
            "placement",
            "placements",
            "career",
            "recruitment",
            "recruiter",
            "application process and shortlist",
            "slotting",
        )
    )


def _is_training(unit: dict[str, Any]) -> bool:
    h = _norm(_heading(unit))
    body = _norm(_text(unit)[:1600])

    signals = (
        "training",
        "upskilling",
        "vocational",
        "skill hub",
        "pmkvy",
        "government e marketplace",
        "gem",
        "gfr 2017",
    )

    return any(signal in h for signal in signals) or any(
        signal in body for signal in (
            "vocational",
            "upskilling",
            "skill hub",
        )
    )


def _is_international(unit: dict[str, Any]) -> bool:
    h = _norm(_heading(unit))
    body = _norm(_text(unit)[:1200])

    return any(
        signal in h
        for signal in (
            "international relations",
            "international student",
            "international students",
            "international applicants",
            "exchange program",
            "exchange programmes",
            "mou",
            "international partnership",
        )
    ) or "international students" in body


def _is_alumni(unit: dict[str, Any]) -> bool:
    h = _norm(_heading(unit))
    return any(
        signal in h
        for signal in (
            "alumni",
            "office of alumni affairs",
            "office of resources and alumni",
            "dora",
        )
    )


def _is_sustainability(unit: dict[str, Any]) -> bool:
    h = _norm(_heading(unit))
    return any(
        signal in h
        for signal in (
            "sustainability",
            "waste",
            "water",
            "zero solid waste",
            "zero water",
        )
    )


def _is_facility(unit: dict[str, Any]) -> bool:
    h = _norm(_heading(unit))
    return any(
        signal in h
        for signal in (
            "facility",
            "facilities",
            "laboratory",
            "laboratories",
            "lab",
            "equipment",
            "research facility",
            "prototyping",
            "health center",
            "health centre",
            "co working spaces",
            "co-working spaces",
            "campus infrastructure",
        )
    )


def _is_faculty(unit: dict[str, Any]) -> bool:
    h = _norm(_heading(unit))
    return any(
        signal in h
        for signal in (
            "faculty",
            "faculty members",
            "professor",
            "faculty position",
            "visiting faculty",
            "adjunct faculty",
            "scale of pay",
        )
    )


def _is_research(unit: dict[str, Any]) -> bool:
    h = _norm(_heading(unit))
    return any(
        signal in h
        for signal in (
            "research",
            "research area",
            "research areas",
            "research project",
            "research projects",
            "research position",
            "postdoc",
            "postdoctoral",
            "project position",
            "scholars in residence",
            "research and development",
        )
    )


def _is_registration(unit: dict[str, Any]) -> bool:
    h = _norm(_heading(unit))
    return any(
        signal in h
        for signal in (
            "registration",
            "change of registration",
            "late registration",
            "cancellation of registration",
        )
    )


def _is_exam(unit: dict[str, Any]) -> bool:
    h = _norm(_heading(unit))
    return any(
        signal in h
        for signal in (
            "examination",
            "examinations",
            "exam",
            "grading",
            "evaluation",
            "grade",
            "results",
        )
    )


def _is_calendar(unit: dict[str, Any]) -> bool:
    h = _norm(_heading(unit))
    return any(
        signal in h
        for signal in (
            "academic calendar",
            "academic session",
            "semester schedule",
            "first year class time table",
            "class time table",
            "time table",
        )
    )


def _is_academic_progression(unit: dict[str, Any]) -> bool:
    h = _norm(_heading(unit))
    return any(
        signal in h
        for signal in (
            "academic performance",
            "academic progression",
            "continuation",
            "progress monitoring",
            "progress monitoring meeting",
            "qualifier",
            "candidacy",
            "maximum duration",
            "branch change",
            "withdrawal",
            "termination",
            "appeal against termination",
            "requirements",
        )
    )


def _is_rules(unit: dict[str, Any]) -> bool:
    h = _norm(_heading(unit))
    return any(
        signal in h
        for signal in (
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
        )
    )


def _is_general_overview(unit: dict[str, Any]) -> bool:
    h = _norm(_heading(unit))
    return any(
        signal in h
        for signal in (
            "overview",
            "about",
            "introduction",
            "profile",
            "welcome to",
            "welcome to the",
        )
    )


def _generic_institution_route(
    unit: dict[str, Any]
) -> tuple[str, str]:
    # Stable precedence for institute-wide/process knowledge.
    if _is_registration(unit):
        return "academic_administration", "registration"

    if _is_calendar(unit):
        return "academic_administration", "academic_calendar"

    if _is_exam(unit):
        return "academic_administration", "examinations_and_grading"

    if _is_academic_progression(unit):
        return "academic_administration", "academic_progression"

    if _is_fee(unit):
        return "finance", "fees_and_finance"

    if _is_scholarship(unit):
        return "financial_aid", "scholarships"

    if _is_placement(unit):
        return "placements_and_careers", "placements"

    if _is_training(unit):
        return "training_and_upskilling", "training"

    if _is_international(unit):
        return "international_relations", "international_relations"

    if _is_alumni(unit):
        return "alumni_and_external_relations", "alumni"

    if _is_sustainability(unit):
        return "campus_and_student_services", "sustainability"

    if _is_facility(unit):
        return "research_and_technology_facilities", "facilities"

    if _is_research(unit):
        return "research", "research"

    if _is_faculty(unit):
        return "faculty", "faculty"

    if _is_hostel(unit):
        return "hostel_accommodation", "general_information"

    if _is_contact(unit):
        return "contacts", "contacts"

    if _is_rules(unit):
        return "rules_regulations", "rules_and_regulations"

    if _is_general_overview(unit):
        return "institute_overview", "overview"

    # Generic program/academic structure at institutional level.
    h = _norm(_heading(unit))
    if any(
        signal in h
        for signal in (
            "program",
            "programme",
            "curriculum",
            "course",
            "course code",
            "course type",
            "credit requirements",
            "minor",
            "dual degree",
        )
    ):
        return "programs", "general_information"

    return (
        "fallback",
        "knowledge_buffer_general",
    )


def _topic_for_entity(
    unit: dict[str, Any],
) -> str:
    if _is_admission(unit):
        return "admissions"

    if _is_faculty(unit):
        return "faculty"

    if _is_research(unit):
        return "research"

    h = _norm(_heading(unit))
    if any(
        signal in h
        for signal in (
            "curriculum",
            "course",
            "courses",
            "syllabus",
            "course code",
            "course type",
            "credit requirements",
        )
    ):
        return "curriculum"

    if _is_facility(unit):
        return "facilities"

    if _is_training(unit):
        return "training"

    if _is_international(unit):
        return "international_relations"

    if _is_alumni(unit):
        return "alumni"

    if _is_sustainability(unit):
        return "sustainability"

    if _is_registration(unit):
        return "registration"

    h = _norm(_heading(unit))
    if any(
        signal in h
        for signal in (
            "curriculum",
            "course",
            "courses",
            "syllabus",
            "course code",
            "course type",
            "credit requirements",
        )
    ):
        return "curriculum"

    if _is_exam(unit):
        return "examinations_and_grading"

    if _is_academic_progression(unit):
        return "academic_progression"

    if _is_rules(unit):
        return "rules_and_regulations"

    if _is_contact(unit):
        return "contacts"

    if _is_general_overview(unit):
        return "overview"

    h = _norm(_heading(unit))

    if any(
        signal in h
        for signal in (
            "program",
            "programme",
            "curriculum",
            "course",
            "course code",
            "course type",
            "minor",
            "dual degree",
        )
    ):
        return "programs"

    return "general_information"


def _route_unit(unit: dict[str, Any]) -> RoutedUnit:
    unit_id = _unit_id(unit)

    # --------------------------------------------------------------
    # 1. Admissions ALWAYS wins before program/entity routing.
    # --------------------------------------------------------------
    if _is_admission(unit):
        program = _detect_program(unit)

        if program:
            return RoutedUnit(
                unit_id=unit_id,
                root="admissions",
                topic=f"{program}_admissions",
                entity_type=None,
                entity_id=None,
                entity_name=None,
                buffer_name=None,
            )

        return RoutedUnit(
            unit_id=unit_id,
            root="admissions",
            topic="general_admissions",
            entity_type=None,
            entity_id=None,
            entity_name=None,
            buffer_name=None,
        )

    # --------------------------------------------------------------
    # 2. Strong entity families.
    # --------------------------------------------------------------
    department = _detect_department(unit)
    if department:
        entity_id, entity_name = department
        return RoutedUnit(
            unit_id=unit_id,
            root="departments",
            topic=_topic_for_entity(unit),
            entity_type="department",
            entity_id=entity_id,
            entity_name=entity_name,
            buffer_name=None,
        )

    school = _detect_school(unit)
    if school:
        entity_id, entity_name = school
        return RoutedUnit(
            unit_id=unit_id,
            root="schools",
            topic=_topic_for_entity(unit),
            entity_type="school",
            entity_id=entity_id,
            entity_name=entity_name,
            buffer_name=None,
        )

    platform = _detect_research_platform(unit)
    if platform:
        entity_id, entity_name = platform
        platform_topic = _topic_for_entity(unit)
        if platform_topic == "general_information":
            platform_topic = "research"
        return RoutedUnit(
            unit_id=unit_id,
            root="research_platforms",
            topic=platform_topic,
            entity_type="research_platform",
            entity_id=entity_id,
            entity_name=entity_name,
            buffer_name=None,
        )

    office = _detect_office(unit)
    if office:
        entity_id, entity_name = office
        return RoutedUnit(
            unit_id=unit_id,
            root="offices_and_administration",
            topic=_topic_for_entity(unit),
            entity_type="office",
            entity_id=entity_id,
            entity_name=entity_name,
            buffer_name=None,
        )

    # --------------------------------------------------------------
    # 3. Program entity routing.
    # --------------------------------------------------------------
    program = _detect_program(unit)
    if program:
        # Generic degree/program mention without a program-specific heading
        # remains institutional programs knowledge. This avoids false entity
        # assignment caused by incidental mentions.
        strong = _norm(_strong_context(unit))
        heading = _norm(_heading(unit))

        program_strong = any(
            re.search(
                pattern,
                strong,
            )
            for pattern in PROGRAM_PATTERNS[program]
        )

        program_heading = any(
            re.search(
                pattern,
                heading,
            )
            for pattern in PROGRAM_PATTERNS[program]
        )

        if program_strong and (
            program_heading
            or any(
                term in heading
                for term in (
                    "program",
                    "programme",
                    "curriculum",
                    "course",
                    "requirements",
                    "admission",
                )
            )
        ):
            return RoutedUnit(
                unit_id=unit_id,
                root="programs",
                topic=_topic_for_entity(unit),
                entity_type="program",
                entity_id=program,
                entity_name=PROGRAM_NAMES[program],
                buffer_name=None,
            )

    # --------------------------------------------------------------
    # 4. General institutional domains.
    # --------------------------------------------------------------
    root, topic = _generic_institution_route(unit)

    buffer_name = (
        topic
        if root == "fallback"
        else None
    )

    return RoutedUnit(
        unit_id=unit_id,
        root=root,
        topic=topic,
        entity_type=None,
        entity_id=None,
        entity_name=None,
        buffer_name=buffer_name,
    )


def _path_for(route: RoutedUnit) -> str:
    if route.root in {
        "departments",
        "schools",
        "research_platforms",
        "programs",
        "offices_and_administration",
    }:
        if route.root != "programs" and not route.entity_id:
            raise ValueError(
                "Entity route missing entity_id: "
                f"{route}"
            )

        if route.root == "programs" and not route.entity_id:
            return f"programs/{route.topic}.md"

        return (
            f"{route.root}/"
            f"{route.entity_id}/"
            f"{route.topic}.md"
        )

    return f"{route.root}/{route.topic}.md"


def _title_for(route: RoutedUnit) -> str:
    label = TOPIC_LABELS.get(
        route.topic,
        route.topic.replace("_", " ").title(),
    )

    if route.entity_name:
        return f"{route.entity_name} — {label}"

    return label


class IITJKnowledgeOrganizerV2:
    """
    Final IITJ-specific deterministic organizer.

    It consumes accepted Command-3 units. The organizer is intentionally
    college-specific so the physical structure can follow the actual IITJ
    website/entity model.
    """

    def __init__(
        self,
        *,
        output_root: str | Path = "storage_v2/command5/iitj_final",
    ) -> None:
        self.output_root = Path(output_root)

    def build_plan(
        self,
        units: Iterable[dict[str, Any]],
    ) -> dict[str, Any]:
        normalized = self._normalize_units(units)
        self._validate_input(normalized)

        routes: list[RoutedUnit] = [
            _route_unit(unit)
            for unit in normalized
        ]

        groups: dict[
            tuple[str, str, str | None, str | None, str | None],
            list[str],
        ] = defaultdict(list)

        for route in routes:
            groups[
                (
                    route.root,
                    route.topic,
                    route.entity_type,
                    route.entity_id,
                    route.buffer_name,
                )
            ].append(route.unit_id)

        documents = []

        for key, unit_ids in sorted(
            groups.items(),
            key=lambda item: (
                item[0][0],
                item[0][3] or "",
                item[0][1],
            ),
        ):
            root, topic, entity_type, entity_id, buffer_name = key

            path_route = RoutedUnit(
                unit_id="",
                root=root,
                topic=topic,
                entity_type=entity_type,
                entity_id=entity_id,
                entity_name=(
                    self._entity_name_from_id(
                        root,
                        entity_id,
                    )
                    if entity_id
                    else None
                ),
                buffer_name=buffer_name,
            )

            path = _path_for(path_route)

            document_id = (
                "doc-"
                + _hash(
                    path
                    + "|"
                    + "|".join(sorted(unit_ids))
                )[:16]
            )

            documents.append(
                {
                    "document_id": document_id,
                    "title": _title_for(path_route),
                    "path": path,
                    "scope_type": (
                        entity_type
                        if entity_type
                        else "domain"
                    ),
                    "scope_id": (
                        entity_id
                        if entity_id
                        else root
                    ),
                    "topic": topic,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "entity_name": path_route.entity_name,
                    "buffer_name": buffer_name,
                    "unit_ids": sorted(unit_ids),
                }
            )

        self._validate_coverage(
            normalized,
            documents,
        )

        return {
            "version": VERSION,
            "college": "IIT Jodhpur",
            "phase": "college_specific_knowledge_organization",
            "policy": {
                "allowed_tiers": sorted(ALLOWED_TIERS),
                "lossless": True,
                "entity_aware": True,
                "college_specific": True,
                "buffer_fallback": True,
            },
            "unit_count": len(normalized),
            "document_count": len(documents),
            "documents": documents,
        }

    def write_output(
        self,
        *,
        units: Iterable[dict[str, Any]],
        output_root: str | Path | None = None,
    ) -> dict[str, Any]:
        normalized = self._normalize_units(units)
        plan = self.build_plan(normalized)

        root = Path(
            output_root or self.output_root
        )
        root.mkdir(
            parents=True,
            exist_ok=True,
        )

        unit_map = {
            unit["unit_id"]: unit
            for unit in normalized
        }

        written_files = []
        assignments = []

        for document in plan["documents"]:
            path = root / document["path"]
            path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            markdown = self._render_document(
                document,
                unit_map,
            )

            path.write_text(
                markdown,
                encoding="utf-8",
            )

            written_files.append(
                str(path.relative_to(root))
            )

            for unit_id in document["unit_ids"]:
                unit = unit_map[unit_id]
                assignments.append(
                    {
                        "unit_id": unit_id,
                        "document_id": document["document_id"],
                        "path": document["path"],
                        "tier": unit["tier"],
                        "source_file": unit.get(
                            "source_file",
                            "",
                        ),
                        "source_url": unit.get(
                            "source_url",
                            "",
                        ),
                        "content_sha256": _hash(
                            unit["text"]
                        ),
                    }
                )

        assignments.sort(
            key=lambda row: (
                row["path"],
                row["unit_id"],
            )
        )

        manifest = {
            "version": VERSION,
            "college": "IIT Jodhpur",
            "unit_count": len(normalized),
            "document_count": len(plan["documents"]),
            "written_files": sorted(written_files),
            "coverage": {
                "input_unit_count": len(normalized),
                "assigned_unit_count": len(assignments),
                "missing_unit_ids": [],
                "unassigned_unit_ids": [],
                "duplicate_unit_ids": [],
                "extra_unit_ids": [],
            },
            "assignments": assignments,
        }

        (root / "iitj_organization_plan.json").write_text(
            json.dumps(
                plan,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        (root / "iitj_organization_manifest.json").write_text(
            json.dumps(
                manifest,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        return manifest

    @staticmethod
    def _normalize_units(
        units: Iterable[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        normalized = []

        for raw in units:
            unit = dict(raw)

            unit["unit_id"] = _unit_id(unit)
            unit["tier"] = _tier(unit)
            unit["heading"] = _heading(unit)
            unit["text"] = _text(unit)
            unit["source_file"] = _source_file(unit)
            unit["source_url"] = _source_url(unit)

            normalized.append(unit)

        return sorted(
            normalized,
            key=lambda unit: unit["unit_id"],
        )

    @staticmethod
    def _validate_input(
        units: list[dict[str, Any]],
    ) -> None:
        if not units:
            raise ValueError(
                "No accepted IITJ units supplied."
            )

        ids = [
            unit["unit_id"]
            for unit in units
        ]

        if any(not unit_id for unit_id in ids):
            raise ValueError(
                "Accepted unit missing unit_id."
            )

        duplicate_ids = sorted(
            unit_id
            for unit_id, count in Counter(
                ids
            ).items()
            if count > 1
        )

        if duplicate_ids:
            raise ValueError(
                "Duplicate input unit IDs: "
                + ", ".join(duplicate_ids)
            )

        invalid_tiers = sorted(
            {
                unit["tier"]
                for unit in units
                if unit["tier"]
                not in ALLOWED_TIERS
            }
        )

        if invalid_tiers:
            raise ValueError(
                "Invalid Command-3 tiers: "
                + ", ".join(invalid_tiers)
            )

        empty = sorted(
            unit["unit_id"]
            for unit in units
            if not unit["text"]
        )

        if empty:
            raise ValueError(
                "Accepted units with empty content: "
                + ", ".join(empty)
            )

    def _entity_name_from_id(
        self,
        root: str,
        entity_id: str,
    ) -> str | None:
        if root == "departments":
            return DEPARTMENT_NAMES.get(entity_id)

        if root == "schools":
            return SCHOOL_NAMES.get(entity_id)

        if root == "research_platforms":
            return RESEARCH_PLATFORM_NAMES.get(entity_id)

        if root == "offices_and_administration":
            return OFFICE_NAMES.get(entity_id)

        if root == "programs":
            return PROGRAM_NAMES.get(entity_id)

        return None

    @staticmethod
    def _validate_coverage(
        units: list[dict[str, Any]],
        documents: list[dict[str, Any]],
    ) -> None:
        expected = {
            unit["unit_id"]
            for unit in units
        }

        assigned = [
            unit_id
            for document in documents
            for unit_id in document["unit_ids"]
        ]

        counts = Counter(assigned)

        missing = sorted(
            expected - set(assigned)
        )

        extra = sorted(
            set(assigned) - expected
        )

        duplicate = sorted(
            unit_id
            for unit_id, count in counts.items()
            if count > 1
        )

        if (
            missing
            or extra
            or duplicate
        ):
            raise ValueError(
                "IITJ Command 5 coverage failure: "
                f"missing={missing}, "
                f"extra={extra}, "
                f"duplicates={duplicate}"
            )

        paths = [
            document["path"]
            for document in documents
        ]

        if len(paths) != len(set(paths)):
            raise ValueError(
                "Duplicate output path detected."
            )

    @staticmethod
    def _render_document(
        document: dict[str, Any],
        unit_map: dict[str, dict[str, Any]],
    ) -> str:
        lines = [
            "---",
            f"id: {document['document_id']}",
            f"title: {json.dumps(document['title'], ensure_ascii=False)}",
            f"scope_type: {document['scope_type']}",
            f"scope_id: {json.dumps(document['scope_id'], ensure_ascii=False)}",
            f"topic: {json.dumps(document['topic'], ensure_ascii=False)}",
            f"organization_version: {VERSION}",
            "unit_ids:",
        ]

        for unit_id in document["unit_ids"]:
            lines.append(
                f"  - {unit_id}"
            )

        lines.extend(
            [
                "---",
                "",
                f"# {document['title']}",
                "",
            ]
        )

        for unit_id in document["unit_ids"]:
            unit = unit_map[unit_id]
            heading = unit["heading"] or "Knowledge Unit"

            lines.extend(
                [
                    f"## {heading}",
                    "",
                    unit["text"],
                    "",
                ]
            )

        lines.extend(
            [
                "## Source Traceability",
                "",
            ]
        )

        for unit_id in document["unit_ids"]:
            unit = unit_map[unit_id]
            source = unit.get("source_file", "")
            url = unit.get("source_url", "")

            trace = f"- `{unit_id}` — {source}"
            if url:
                trace += f" — {url}"

            lines.append(trace)

        lines.append("")
        return "\n".join(lines)


__all__ = [
    "IITJKnowledgeOrganizerV2",
    "RoutedUnit",
    "VERSION",
]