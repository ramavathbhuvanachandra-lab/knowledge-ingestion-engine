"""
Phase 8.3 — Deterministic Knowledge Taxonomy

Purpose
-------
Classify structured college knowledge using a large, manually maintained
vocabulary.

IMPORTANT
---------
No LLM.
No embeddings.
No vector database.
No chunking.
No summarization.
No external knowledge.

The taxonomy is deliberately richer than the final RAG document count.

Architecture:

    domain
        category
            subcategory

Phase 8.4 will later decide how populated taxonomy buckets are grouped
into the final ~20-30-ish RAG documents for a particular website.
"""

from __future__ import annotations

import re


# ============================================================================
# MASTER TAXONOMY
# ============================================================================

TAXONOMY = {

    # ------------------------------------------------------------------------
    # CAMPUS
    # ------------------------------------------------------------------------

    "campus": {

        "campus_overview": {
            "keywords": (
                "campus overview",
                "campus profile",
                "about campus",
                "campus introduction",
                "campus history",
                "history of the institute",
                "institute history",
                "campus layout",
                "campus map",
                "site map",
                "campus plan",
                "campus facilities",
                "campus infrastructure",
            ),
        },

        "locations_and_directions": {
            "keywords": (
                "location",
                "locations",
                "directions",
                "how to reach",
                "reach the institute",
                "getting here",
                "route",
                "address",
                "where is",
                "nearby",
                "landmark",
                "way to campus",
            ),
        },

        "buildings_and_spaces": {
            "keywords": (
                "building",
                "buildings",
                "block",
                "academic block",
                "administrative block",
                "lecture hall",
                "lecture halls",
                "classroom",
                "classrooms",
                "seminar hall",
                "seminar halls",
                "conference hall",
                "academic space",
                "common area",
            ),
        },

        "sports_and_recreation": {
            "keywords": (
                "sports",
                "sports facility",
                "sports facilities",
                "playground",
                "playgrounds",
                "stadium",
                "gymnasium",
                "gym",
                "fitness centre",
                "fitness center",
                "swimming pool",
                "recreation",
                "recreational",
            ),
        },

        "transportation": {
            "keywords": (
                "transport",
                "transportation",
                "campus bus",
                "bus service",
                "bus services",
                "shuttle",
                "shuttle service",
                "parking",
                "vehicle",
                "vehicles",
                "parking facility",
            ),
        },

        "utilities_and_services": {
            "keywords": (
                "electricity",
                "water supply",
                "water facility",
                "internet",
                "wifi",
                "wi fi",
                "network",
                "power",
                "utility",
                "utilities",
                "maintenance",
                "waste management",
            ),
        },

        "accessibility": {
            "keywords": (
                "accessibility",
                "accessible",
                "persons with disabilities",
                "person with disability",
                "disability",
                "wheelchair",
                "barrier free",
                "barrier-free",
            ),
        },

        "environment_and_sustainability": {
            "keywords": (
                "sustainability",
                "sustainable campus",
                "environment",
                "green campus",
                "renewable energy",
                "solar",
                "water conservation",
                "energy conservation",
                "sustainable development",
            ),
        },
    },

    # ------------------------------------------------------------------------
    # ACADEMICS
    # ------------------------------------------------------------------------

    "academics": {

        "programs": {
            "keywords": (
                "academic program",
                "academic programme",
                "undergraduate program",
                "undergraduate programme",
                "postgraduate program",
                "postgraduate programme",
                "doctoral program",
                "doctoral programme",
                "phd program",
                "degree program",
                "degree programme",
                "btech",
                "mtech",
                "msc",
                "mba",
                "phd",
                "master of technology",
                "master of science",
                "master of design",
                "ms by research",
            ),
        },

        "departments_and_schools": {
            "keywords": (
                "department",
                "departments",
                "school of",
                "schools",
                "academic school",
                "academic centre",
                "academic center",
                "academic unit",
            ),
        },

        "courses_and_curriculum": {
            "keywords": (
                "course",
                "courses",
                "curriculum",
                "curricula",
                "syllabus",
                "syllabi",
                "credit",
                "credits",
                "elective",
                "electives",
                "core course",
                "degree requirement",
                "degree requirements",
            ),
        },

        "academic_calendar": {
            "keywords": (
                "academic calendar",
                "semester calendar",
                "semester schedule",
                "academic schedule",
                "academic year",
                "semester dates",
                "term dates",
            ),
        },

        "registration_and_enrolment": {
            "keywords": (
                "registration",
                "course registration",
                "enrolment",
                "enrollment",
                "add drop",
                "academic registration",
                "semester registration",
            ),
        },

        "examinations_and_evaluation": {
            "keywords": (
                "examination",
                "examinations",
                "exam",
                "exams",
                "evaluation",
                "assessment",
                "question paper",
                "date sheet",
                "exam timetable",
                "result",
                "results",
                "grade",
                "grades",
                "grading",
            ),
        },

        "attendance_and_academic_progress": {
            "keywords": (
                "attendance",
                "minimum attendance",
                "academic performance",
                "academic progress",
                "probation",
                "academic standing",
            ),
        },

        "academic_rules_and_regulations": {
            "keywords": (
                "academic regulation",
                "academic regulations",
                "academic rule",
                "academic rules",
                "academic policy",
                "academic policies",
                "academic guideline",
                "academic guidelines",
                "ordinance",
            ),
        },

        "transcripts_and_certificates": {
            "keywords": (
                "transcript",
                "transcripts",
                "certificate",
                "certificates",
                "degree certificate",
                "provisional certificate",
                "migration certificate",
            ),
        },

        "academic_forms": {
            "keywords": (
                "academic form",
                "academic forms",
                "course form",
                "registration form",
            ),
        },
    },

    # ------------------------------------------------------------------------
    # RESEARCH
    # ------------------------------------------------------------------------

    "research": {

        "research_areas": {
            "keywords": (
                "research area",
                "research areas",
                "research interest",
                "research interests",
                "research theme",
                "research themes",
                "research domain",
                "research domains",
                "focus area",
                "focus areas",
                "verticals",
            ),
        },

        "research_centres_and_centers": {
            "keywords": (
                "research centre",
                "research center",
                "research centres",
                "research centers",
                "centre for",
                "center for",
                "centre of excellence",
                "center of excellence",
            ),
        },

        "research_laboratories": {
            "keywords": (
                "research laboratory",
                "research laboratories",
                "research lab",
                "research labs",
            ),
        },

        "research_projects": {
            "keywords": (
                "research project",
                "research projects",
                "project details",
                "ongoing project",
                "ongoing projects",
                "completed project",
                "funded project",
                "sponsored project",
            ),
        },

        "research_groups": {
            "keywords": (
                "research group",
                "research groups",
                "research team",
                "research unit",
            ),
        },

        "research_funding_and_grants": {
            "keywords": (
                "research funding",
                "research grant",
                "research grants",
                "grant",
                "grants",
                "funding agency",
                "funded research",
                "sponsored research",
            ),
        },

        "research_collaborations": {
            "keywords": (
                "research collaboration",
                "research collaborations",
                "joint research",
                "industry collaboration",
                "international collaboration",
                "academic collaboration",
            ),
        },

        "publications": {
            "keywords": (
                "publication",
                "publications",
                "journal",
                "journals",
                "conference paper",
                "research paper",
                "papers",
                "book chapter",
                "articles",
            ),
        },

        "patents_and_innovation": {
            "keywords": (
                "patent",
                "patents",
                "innovation",
                "innovations",
                "technology transfer",
                "intellectual property",
                "startup",
                "startups",
                "incubation",
                "incubator",
            ),
        },

        "doctoral_and_research_opportunities": {
            "keywords": (
                "phd admission",
                "phd admissions",
                "doctoral research",
                "doctoral opportunity",
                "research opportunity",
                "research opportunities",
                "fellowship opportunity",
            ),
        },
    },

    # ------------------------------------------------------------------------
    # PEOPLE
    # ------------------------------------------------------------------------

    "people": {

        "faculty": {
            "keywords": (
                "faculty",
                "faculty members",
                "faculty profile",
                "professor",
                "professors",
                "associate professor",
                "assistant professor",
                "faculty directory",
                "teaching faculty",
            ),
        },

        "researchers": {
            "keywords": (
                "researcher",
                "researchers",
                "scientist",
                "scientists",
                "principal investigator",
                "research scholar",
            ),
        },

        "staff": {
            "keywords": (
                "staff",
                "staff directory",
                "technical staff",
                "administrative staff",
                "support staff",
            ),
        },

        "leadership": {
            "keywords": (
                "director",
                "deputy director",
                "dean",
                "deans",
                "registrar",
                "leadership",
                "institute leadership",
                "chairperson",
                "chairman",
                "co-chairperson",
                "co-chairman",
                "head of department",
                "hod",
                "president",
                "vice president",
                "chief",
            ),
        },

        "position_holders": {
            "keywords": (
                "position holder",
                "position holders",
                "office bearer",
                "office bearers",
                "coordinator",
                "coordinators",
                "officer",
                "officers",
            ),
        },

        "committees_and_boards": {
            "keywords": (
                "committee",
                "committees",
                "board",
                "boards",
                "council",
                "councils",
                "working group",
            ),
        },

        "contact_directory": {
            "keywords": (
                "contact directory",
                "directory",
                "contact details",
                "phone directory",
                "email directory",
            ),
        },
    },

    # ------------------------------------------------------------------------
    # ADMISSIONS
    # ------------------------------------------------------------------------

    "admissions": {

        "admission_overview": {
            "keywords": (
                "admission",
                "admissions",
                "admission process",
                "admission procedure",
                "admission overview",
            ),
        },

        "eligibility": {
            "keywords": (
                "eligibility",
                "eligible",
                "eligibility criteria",
                "qualification",
                "qualifications",
            ),
        },

        "application_process": {
            "keywords": (
                "application process",
                "apply",
                "applying",
                "application procedure",
                "online application",
            ),
        },

        "entrance_examinations": {
            "keywords": (
                "entrance exam",
                "entrance examination",
                "entrance test",
                "jee",
                "gate",
                "jam",
                "cat",
            ),
        },

        "admission_fees": {
            "keywords": (
                "admission fee",
                "admission fees",
                "tuition fee",
                "tuition fees",
                "fee structure",
            ),
        },

        "admission_notices": {
            "keywords": (
                "admission notice",
                "admission notices",
                "admission notification",
                "admission circular",
            ),
        },
    },

    # ------------------------------------------------------------------------
    # STUDENT LIFE
    # ------------------------------------------------------------------------

    "student_life": {

        "student_services": {
            "keywords": (
                "student service",
                "student services",
                "student support",
                "student affairs",
                "student office",
            ),
        },

        "student_welfare": {
            "keywords": (
                "student welfare",
                "welfare",
                "student wellbeing",
                "student well-being",
            ),
        },

        "clubs_and_societies": {
            "keywords": (
                "club",
                "clubs",
                "society",
                "societies",
                "student club",
                "student society",
                "student organisation",
                "student organization",
            ),
        },

        "student_activities": {
            "keywords": (
                "student activity",
                "student activities",
                "extracurricular",
                "co-curricular",
                "student life",
                "student engagement",
            ),
        },

        "student_opportunities": {
            "keywords": (
                "student opportunity",
                "student opportunities",
                "student competition",
                "student exchange",
            ),
        },

        "grievances_and_support": {
            "keywords": (
                "grievance",
                "grievances",
                "complaint",
                "complaints",
                "anti ragging",
                "anti-ragging",
                "ombudsperson",
            ),
        },
    },

    # ------------------------------------------------------------------------
    # HOSTELS
    # ------------------------------------------------------------------------

    "hostels": {

        "accommodation": {
            "keywords": (
                "hostel",
                "hostels",
                "hostel accommodation",
                "residence hall",
                "residential accommodation",
                "student residence",
            ),
        },

        "hostel_rules": {
            "keywords": (
                "hostel rules",
                "hostel regulations",
                "hostel policy",
                "residential rules",
                "residence rules",
                "hostel guidelines",
            ),
        },

        "hostel_fees": {
            "keywords": (
                "hostel fee",
                "hostel fees",
                "hostel charges",
                "residence fee",
                "accommodation fee",
            ),
        },

        "hostel_facilities": {
            "keywords": (
                "hostel facilities",
                "hostel amenities",
                "hostel infrastructure",
                "residence facilities",
            ),
        },

        "hostel_allocation_and_application": {
            "keywords": (
                "hostel allocation",
                "hostel allotment",
                "hostel application",
                "hostel registration",
                "room allocation",
            ),
        },

        "hostel_contacts": {
            "keywords": (
                "hostel office",
                "warden",
                "hostel warden",
                "hostel contact",
            ),
        },
    },

    # ------------------------------------------------------------------------
    # FOOD AND DINING
    # ------------------------------------------------------------------------

    "food_and_dining": {

        "mess_and_dining": {
            "keywords": (
                "mess",
                "messes",
                "mess facility",
                "mess menu",
                "mess timing",
                "mess timings",
                "mess rules",
                "dining",
                "dining hall",
            ),
        },

        "cafeterias_and_food_outlets": {
            "keywords": (
                "cafeteria",
                "cafeterias",
                "canteen",
                "canteens",
                "food outlet",
                "food outlets",
                "food court",
                "restaurant",
                "tea stall",
                "food stall",
            ),
        },

        "food_services_and_rules": {
            "keywords": (
                "food service",
                "food services",
                "dining service",
                "food rules",
                "mess committee",
                "mess management",
            ),
        },
    },

    # ------------------------------------------------------------------------
    # FINANCE
    # ------------------------------------------------------------------------

    "finance_and_fees": {

        "fees": {
            "keywords": (
                "fee",
                "fees",
                "fee structure",
                "tuition",
                "tuition fee",
                "academic fee",
                "semester fee",
            ),
        },

        "scholarships": {
            "keywords": (
                "scholarship",
                "scholarships",
                "merit scholarship",
                "need based scholarship",
            ),
        },

        "fellowships_and_stipends": {
            "keywords": (
                "fellowship",
                "fellowships",
                "stipend",
                "stipends",
                "assistantship",
            ),
        },

        "financial_assistance": {
            "keywords": (
                "financial assistance",
                "financial aid",
                "fee waiver",
                "fee concession",
                "education loan",
            ),
        },
    },

    # ------------------------------------------------------------------------
    # CAREERS
    # ------------------------------------------------------------------------

    "careers_and_placements": {

        "placements": {
            "keywords": (
                "placement",
                "placements",
                "campus placement",
                "campus recruitment",
                "training and placement",
            ),
        },

        "recruitment": {
            "keywords": (
                "recruitment",
                "recruiter",
                "recruiters",
                "hiring",
                "employer",
                "employers",
            ),
        },

        "internships": {
            "keywords": (
                "internship",
                "internships",
                "summer internship",
                "industrial training",
            ),
        },

        "career_services": {
            "keywords": (
                "career service",
                "career services",
                "career development",
                "career guidance",
                "career counselling",
                "career counseling",
            ),
        },

        "training": {
            "keywords": (
                "training",
                "skill development",
                "professional development",
                "aptitude training",
            ),
        },
    },

    # ------------------------------------------------------------------------
    # ADMINISTRATION
    # ------------------------------------------------------------------------

    "administration": {

        "administrative_offices": {
            "keywords": (
                "administrative office",
                "administrative offices",
                "office of administration",
                "administration",
                "administrative services",
            ),
        },

        "registrar_and_establishment": {
            "keywords": (
                "registrar",
                "establishment",
                "establishment section",
                "administrative establishment",
            ),
        },

        "directorate_and_deans": {
            "keywords": (
                "directorate",
                "director office",
                "dean office",
                "office of dean",
                "office of director",
            ),
        },

        "governance": {
            "keywords": (
                "governance",
                "institutional governance",
                "governing body",
                "management",
            ),
        },

        "statutory_bodies": {
            "keywords": (
                "statutory body",
                "statutory bodies",
                "senate",
                "board of governors",
                "academic council",
                "finance committee",
            ),
        },
    },

    # ------------------------------------------------------------------------
    # RULES / POLICIES
    # ------------------------------------------------------------------------

    "rules_policies_and_regulations": {

        "institutional_rules": {
            "keywords": (
                "institutional rules",
                "institute rules",
                "institution rules",
                "general rules",
            ),
        },

        "student_rules": {
            "keywords": (
                "student rules",
                "student regulations",
                "student code",
                "code of conduct",
                "student conduct",
            ),
        },

        "academic_regulations": {
            "keywords": (
                "academic regulations",
                "academic rules",
                "academic policy",
                "academic policies",
            ),
        },

        "hostel_rules": {
            "keywords": (
                "hostel rules",
                "hostel regulations",
                "hostel policy",
            ),
        },

        "security_and_safety_rules": {
            "keywords": (
                "security rules",
                "safety rules",
                "security policy",
                "fire safety rules",
                "emergency rules",
            ),
        },

        "administrative_policies": {
            "keywords": (
                "administrative policy",
                "administrative policies",
                "office rules",
                "administrative regulations",
            ),
        },
    },

    # ------------------------------------------------------------------------
    # FACILITIES
    # ------------------------------------------------------------------------

    "facilities_and_infrastructure": {

        "laboratories": {
            "keywords": (
                "laboratory",
                "laboratories",
                "lab",
                "labs",
                "laboratory facility",
                "laboratory facilities",
                "lab facility",
                "lab facilities",
            ),
        },

        "workshops": {
            "keywords": (
                "workshop",
                "workshops",
                "fabrication workshop",
                "mechanical workshop",
                "engineering workshop",
            ),
        },

        "libraries": {
            "keywords": (
                "library",
                "libraries",
                "central library",
                "reading room",
                "reading rooms",
                "digital library",
            ),
        },

        "classrooms_and_academic_spaces": {
            "keywords": (
                "classroom",
                "classrooms",
                "lecture room",
                "lecture hall",
                "seminar hall",
                "teaching space",
            ),
        },

        "computing_and_digital_facilities": {
            "keywords": (
                "computer centre",
                "computer center",
                "computer lab",
                "computing facility",
                "data centre",
                "data center",
                "server facility",
                "digital infrastructure",
            ),
        },

        "auditoriums_and_conference_spaces": {
            "keywords": (
                "auditorium",
                "auditoriums",
                "conference hall",
                "conference centre",
                "conference center",
                "event space",
            ),
        },

        "specialized_facilities": {
            "keywords": (
                "specialized facility",
                "specialised facility",
                "specialized facilities",
                "specialised facilities",
                "instrumentation",
                "central facility",
                "advanced facility",
            ),
        },

        "utilities_and_services": {
            "keywords": (
                "utility",
                "utilities",
                "water supply",
                "electricity",
                "power supply",
                "internet",
                "wifi",
                "maintenance",
            ),
        },
    },

    # ------------------------------------------------------------------------
    # HEALTH / SAFETY / WELLBEING
    # ------------------------------------------------------------------------

    "health_safety_and_wellbeing": {

        "medical_services": {
            "keywords": (
                "medical centre",
                "medical center",
                "health centre",
                "health center",
                "clinic",
                "doctor",
                "hospital",
                "health service",
            ),
        },

        "counselling_and_mental_wellbeing": {
            "keywords": (
                "counselling",
                "counseling",
                "mental health",
                "wellbeing",
                "well-being",
                "psychological",
                "counsellor",
                "counselor",
            ),
        },

        "emergency_services": {
            "keywords": (
                "emergency",
                "emergency services",
                "emergency contact",
                "ambulance",
                "first aid",
                "disaster management",
            ),
        },

        "security": {
            "keywords": (
                "security",
                "security office",
                "security services",
                "security personnel",
                "surveillance",
            ),
        },

        "fire_and_safety": {
            "keywords": (
                "fire safety",
                "fire protection",
                "fire emergency",
                "safety measures",
                "occupational safety",
            ),
        },
    },

    # ------------------------------------------------------------------------
    # EVENTS
    # ------------------------------------------------------------------------

    "events_and_activities": {

        "events": {
            "keywords": (
                "event",
                "events",
                "activity",
                "activities",
            ),
        },

        "festivals": {
            "keywords": (
                "festival",
                "festivals",
                "fest",
                "celebration",
            ),
        },

        "seminars_and_workshops": {
            "keywords": (
                "seminar",
                "seminars",
                "webinar",
                "lecture series",
            ),
        },

        "conferences": {
            "keywords": (
                "conference",
                "conferences",
                "symposium",
                "symposia",
                "conclave",
            ),
        },

        "outreach_and_public_engagement": {
            "keywords": (
                "outreach",
                "public engagement",
                "community engagement",
                "awareness program",
                "extension activity",
            ),
        },
    },

    # ------------------------------------------------------------------------
    # NOTICES
    # ------------------------------------------------------------------------

    "notices_and_announcements": {

        "academic_notices": {
            "keywords": (
                "academic notice",
                "academic notices",
                "exam notice",
                "examination notice",
                "registration notice",
            ),
        },

        "admission_notices": {
            "keywords": (
                "admission notice",
                "admission notices",
                "admission notification",
            ),
        },

        "student_notices": {
            "keywords": (
                "student notice",
                "student notices",
                "hostel notice",
                "student notification",
            ),
        },

        "administrative_notices": {
            "keywords": (
                "administrative notice",
                "administrative notices",
                "office order",
                "circular",
                "circulars",
            ),
        },

        "general_announcements": {
            "keywords": (
                "announcement",
                "announcements",
                "notice",
                "notices",
                "notification",
                "notifications",
            ),
        },
    },

    # ------------------------------------------------------------------------
    # CONTACTS
    # ------------------------------------------------------------------------

    "contacts_and_directory": {

        "general_contacts": {
            "keywords": (
                "contact",
                "contacts",
                "contact us",
                "contact information",
                "phone",
                "telephone",
                "email",
            ),
        },

        "emergency_contacts": {
            "keywords": (
                "emergency contact",
                "emergency contacts",
                "helpline",
                "help line",
                "emergency number",
            ),
        },

        "office_directory": {
            "keywords": (
                "office directory",
                "directory",
                "office contacts",
                "administrative contacts",
            ),
        },
    },

    # ------------------------------------------------------------------------
    # INSTITUTES / CENTRES / SPECIAL UNITS
    # ------------------------------------------------------------------------

    "institutes_centres_and_units": {

        "centre_overview": {
            "keywords": (
                "about centre",
                "about center",
                "centre overview",
                "center overview",
                "vision",
                "mission",
                "objectives",
                "goals",
                "who we are",
                "about us",
                "overview",
            ),
        },

        "institutes": {
            "keywords": (
                "institute",
                "institutes",
                "institute unit",
            ),
        },

        "centres_and_centers": {
            "keywords": (
                "centre",
                "centres",
                "center",
                "centers",
                "centre for",
                "center for",
            ),
        },

        "special_units": {
            "keywords": (
                "cell",
                "cells",
                "unit",
                "units",
                "initiative",
                "initiatives",
                "program office",
            ),
        },
    },

    # ------------------------------------------------------------------------
    # REVIEW
    # ------------------------------------------------------------------------

    "review": {

        "uncategorized": {
            "keywords": (),
        },

        "ambiguous": {
            "keywords": (),
        },
    },
}


# ============================================================================
# NORMALIZATION
# ============================================================================

def normalize_text(value: str) -> str:
    value = (value or "").lower()

    value = value.replace(
        "-",
        " ",
    )

    value = re.sub(
        r"[^a-z0-9]+",
        " ",
        value,
    )

    return re.sub(
        r"\s+",
        " ",
        value,
    ).strip()


def keyword_match(
    text: str,
    keyword: str,
) -> bool:
    text = normalize_text(text)
    keyword = normalize_text(keyword)

    if not text or not keyword:
        return False

    return (
        f" {keyword} "
        in f" {text} "
    )


# ============================================================================
# CONTEXT OVERRIDES
# ============================================================================

def _explicit_override(
    *,
    heading_n: str,
    text_n: str,
    document_context_n: str,
) -> dict | None:

    # ------------------------------------------------------------------------
    # RESEARCH CENTRE / SPECIAL CENTRE CONTEXT
    # ------------------------------------------------------------------------

    centre_context_terms = (
        "research centre",
        "research center",
        "centre for research",
        "center for research",
        "research and innovation",
        "innovation centre",
        "innovation center",
        "clean energy",
        "technology innovation",
        "rcrice",
        "rcric",
        "technology innovation and start up center",
        "technology innovation and start up centre",
    )

    is_centre_context = any(
        term in document_context_n
        for term in centre_context_terms
    )

    if is_centre_context:

        if heading_n in {
            "about",
            "vision",
            "mission",
            "objectives",
            "goals",
            "who we are",
            "overview",
        }:
            return {
                "domain": "institutes_centres_and_units",
                "category": "centre_overview",
                "subcategory": "centre_overview",
                "confidence": "high",
                "score": 150,
            }

        if heading_n in {
            "verticals",
            "research areas",
            "research area",
            "focus areas",
            "focus area",
        }:
            return {
                "domain": "research",
                "category": "research_areas",
                "subcategory": "research_areas",
                "confidence": "high",
                "score": 150,
            }

    # ------------------------------------------------------------------------
    # HOSTEL SPECIFICITY
    # ------------------------------------------------------------------------

    if (
        "hostel rules" in heading_n
        or "hostel regulations" in heading_n
        or "hostel policy" in heading_n
        or "hostel guidelines" in heading_n
    ):
        return {
            "domain": "hostels",
            "category": "hostel_rules",
            "subcategory": "hostel_rules",
            "confidence": "high",
            "score": 150,
        }

    if (
        "hostel fee" in heading_n
        or "hostel fees" in heading_n
        or "hostel charges" in heading_n
    ):
        return {
            "domain": "hostels",
            "category": "hostel_fees",
            "subcategory": "hostel_fees",
            "confidence": "high",
            "score": 150,
        }

    if (
        "hostel facilities" in heading_n
        or "hostel amenities" in heading_n
        or "hostel infrastructure" in heading_n
    ):
        return {
            "domain": "hostels",
            "category": "hostel_facilities",
            "subcategory": "hostel_facilities",
            "confidence": "high",
            "score": 150,
        }

    # ------------------------------------------------------------------------
    # RESEARCH LABORATORY
    # ------------------------------------------------------------------------

    if (
        "research laboratory" in heading_n
        or "research laboratories" in heading_n
        or "research lab" in heading_n
        or "research labs" in heading_n
    ):
        return {
            "domain": "research",
            "category": "research_laboratories",
            "subcategory": "research_laboratories",
            "confidence": "high",
            "score": 150,
        }

    # ------------------------------------------------------------------------
    # GENERIC LABORATORY
    # ------------------------------------------------------------------------

    if (
        "laboratory facilities" in heading_n
        or "laboratory facility" in heading_n
        or "lab facilities" in heading_n
        or "lab facility" in heading_n
    ):
        return {
            "domain": "facilities_and_infrastructure",
            "category": "laboratories",
            "subcategory": "laboratories",
            "confidence": "high",
            "score": 150,
        }

    # ------------------------------------------------------------------------
    # MESS
    # ------------------------------------------------------------------------

    if (
        "mess" in heading_n
        or "mess timing" in heading_n
        or "mess timings" in heading_n
        or "mess menu" in heading_n
        or "mess rules" in heading_n
    ):
        return {
            "domain": "food_and_dining",
            "category": "mess_and_dining",
            "subcategory": "mess_and_dining",
            "confidence": "high",
            "score": 150,
        }

    # ------------------------------------------------------------------------
    # FACULTY
    # ------------------------------------------------------------------------

    if (
        "faculty profile" in heading_n
        or "faculty directory" in heading_n
        or "faculty members" in heading_n
    ):
        return {
            "domain": "people",
            "category": "faculty",
            "subcategory": "faculty",
            "confidence": "high",
            "score": 150,
        }

    # ------------------------------------------------------------------------
    # LEADERSHIP
    # ------------------------------------------------------------------------

    leadership_terms = (
        "director",
        "dean",
        "registrar",
        "chairperson",
        "chairman",
        "chairwoman",
        "co chairperson",
        "co chairman",
        "head of",
        "president",
        "vice president",
    )

    if any(
        term in heading_n
        for term in leadership_terms
    ):
        return {
            "domain": "people",
            "category": "leadership",
            "subcategory": "leadership",
            "confidence": "high",
            "score": 150,
        }

    leadership_text_signals = (
        "chairperson",
        "chairman",
        "co chairperson",
        "co chairman",
        "director, iit",
        "dean,",
        "registrar,",
    )

    if any(
        signal in text_n
        for signal in leadership_text_signals
    ):
        return {
            "domain": "people",
            "category": "leadership",
            "subcategory": "leadership",
            "confidence": "high",
            "score": 140,
        }

    return None


# ============================================================================
# MAIN CLASSIFIER
# ============================================================================

def classify(
    *,
    heading: str,
    text: str,
    source_name: str = "",
    document_title: str = "",
    document_url: str = "",
) -> dict:

    heading_n = normalize_text(
        heading
    )

    text_n = normalize_text(
        text
    )

    source_n = normalize_text(
        source_name
    )

    document_title_n = normalize_text(
        document_title
    )

    document_url_n = normalize_text(
        document_url
    )

    document_context_n = " ".join(
        [
            document_title_n,
            document_url_n,
            source_n,
        ]
    )

    # Context-aware rules first.
    override = _explicit_override(
        heading_n=heading_n,
        text_n=text_n,
        document_context_n=document_context_n,
    )

    if override is not None:
        return override

    candidates = []

    for domain, categories in TAXONOMY.items():

        # REVIEW buckets are fallback-only.
        if domain == "review":
            continue

        for category, spec in categories.items():

            score = 0

            for keyword in spec[
                "keywords"
            ]:

                keyword_n = normalize_text(
                    keyword
                )

                if not keyword_n:
                    continue

                if keyword_match(
                    heading_n,
                    keyword_n,
                ):
                    score += 12

                elif keyword_match(
                    document_title_n,
                    keyword_n,
                ):
                    score += 8

                elif keyword_match(
                    document_url_n,
                    keyword_n,
                ):
                    score += 6

                elif keyword_match(
                    source_n,
                    keyword_n,
                ):
                    score += 5

                elif keyword_match(
                    text_n,
                    keyword_n,
                ):
                    score += 3

            if score > 0:
                candidates.append(
                    (
                        score,
                        domain,
                        category,
                    )
                )

    if not candidates:
        return {
            "domain": "review",
            "category": "uncategorized",
            "subcategory": "unclassified",
            "confidence": "low",
            "score": 0,
        }

    candidates.sort(
        key=lambda item: (
            -item[0],
            item[1],
            item[2],
        )
    )

    best_score, best_domain, best_category = (
        candidates[0]
    )

    if len(candidates) > 1:

        second_score, second_domain, second_category = (
            candidates[1]
        )

        # Exact cross-domain tie.
        if (
            best_score == second_score
            and best_domain != second_domain
        ):
            return {
                "domain": "review",
                "category": "ambiguous",
                "subcategory": (
                    "multiple_possible_domains"
                ),
                "confidence": "low",
                "score": best_score,
            }

    if best_score >= 12:
        confidence = "high"
    elif best_score >= 6:
        confidence = "medium"
    else:
        confidence = "low"

    if confidence == "low":
        return {
            "domain": "review",
            "category": "ambiguous",
            "subcategory": "weak_classification",
            "confidence": "low",
            "score": best_score,
        }

    return {
        "domain": best_domain,
        "category": best_category,
        "subcategory": best_category,
        "confidence": confidence,
        "score": best_score,
    }


# ============================================================================
# SELF TEST
# ============================================================================

if __name__ == "__main__":

    tests = [
        {
            "heading": "Campus Layout",
            "text": "Campus map and important locations.",
            "title": "IIT Jodhpur Campus",
        },
        {
            "heading": "Laboratory Facilities",
            "text": "Electrical engineering laboratory equipment.",
            "title": "Facilities",
        },
        {
            "heading": "Mess Timings",
            "text": "Breakfast, lunch and dinner timings.",
            "title": "Hostel Mess",
        },
        {
            "heading": "Hostel Rules",
            "text": "Students must follow hostel regulations.",
            "title": "Hostel",
        },
        {
            "heading": "Research Projects",
            "text": "Sponsored research projects.",
            "title": "Research",
        },
        {
            "heading": "Research Laboratory",
            "text": "Advanced research laboratory facilities.",
            "title": "Research Facilities",
        },
        {
            "heading": "Faculty Profile",
            "text": "Professor research interests.",
            "title": "Faculty Directory",
        },
        {
            "heading": "Academic Calendar",
            "text": "Semester dates.",
            "title": "Academics",
        },
        {
            "heading": "Vision",
            "text": "Clean energy research centre vision.",
            "title": (
                "About | Rishabh Centre for Research "
                "and Innovation in Clean Energy (RCRICE)"
            ),
        },
        {
            "heading": "Objectives",
            "text": "Research and innovation objectives.",
            "title": (
                "About | Rishabh Centre for Research "
                "and Innovation in Clean Energy (RCRICE)"
            ),
        },
        {
            "heading": (
                "[Professor Avinash Kumar Agarwal]"
            ),
            "text": (
                "Director, IIT Jodhpur Chairperson, RCRIC"
            ),
            "title": (
                "About | Rishabh Centre for Research "
                "and Innovation in Clean Energy"
            ),
        },
    ]

    for test in tests:

        result = classify(
            heading=test["heading"],
            text=test["text"],
            document_title=test["title"],
        )

        print(
            f"{test['heading']:35} -> "
            f"{result['domain']}/"
            f"{result['category']}/"
            f"{result['subcategory']} "
            f"[{result['confidence']}]"
        )
