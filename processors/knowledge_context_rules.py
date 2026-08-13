"""
Universal deterministic document-context classification.

This module is college-agnostic.

It must NEVER depend on:
- a specific college
- a specific filename
- a specific university centre
- a specific URL path
- IITJ-specific terminology

It uses only generic metadata/content signals.
"""

from __future__ import annotations

from processors.knowledge_taxonomy import classify


def _norm(value: str) -> str:
    return (
        (value or "")
        .lower()
        .replace("-", " ")
    )


def classify_with_context(
    *,
    heading: str,
    text: str,
    source_name: str,
    document_title: str,
    document_url: str,
) -> dict:

    h = _norm(heading)
    t = _norm(text)
    s = _norm(source_name)
    title = _norm(document_title)
    url = _norm(document_url)

    context = " ".join(
        [
            h,
            t,
            s,
            title,
            url,
        ]
    )

    # ==============================================================
    # PROGRAM / DEGREE CONTEXT
    # ==============================================================

    program_signals = (
        "undergraduate program",
        "undergraduate programme",
        "postgraduate program",
        "postgraduate programme",
        "doctoral program",
        "doctoral programme",
        "degree program",
        "degree programme",
        "bachelor",
        "master",
        "phd",
        "doctor of philosophy",
    )

    if any(
        signal in context
        for signal in program_signals
    ):
        if any(
            signal in h
            for signal in (
                "program",
                "programme",
                "introduction",
                "overview",
                "eligibility",
                "curriculum",
                "learning outcome",
                "graduate attribute",
            )
        ):
            return {
                "domain": "academics",
                "category": "programs",
                "subcategory": "programs",
                "confidence": "high",
                "score": 180,
            }

    # ==============================================================
    # REGULATIONS / POLICY DOCUMENTS
    # ==============================================================

    regulation_signals = (
        "regulation",
        "regulations",
        "policy",
        "policies",
        "ordinance",
        "rules",
        "guidelines",
        "code of conduct",
    )

    if any(
        signal in context
        for signal in regulation_signals
    ):
        if any(
            signal in context
            for signal in (
                "academic",
                "course",
                "program",
                "programme",
                "exam",
                "examination",
                "degree",
                "student",
                "faculty",
            )
        ):
            return {
                "domain": "academics",
                "category": "academic_rules_and_regulations",
                "subcategory": "academic_rules_and_regulations",
                "confidence": "high",
                "score": 170,
            }

    # ==============================================================
    # TIMETABLE / SCHEDULE
    # ==============================================================

    schedule_signals = (
        "timetable",
        "time table",
        "class schedule",
        "class timetable",
        "course schedule",
        "semester schedule",
        "academic schedule",
    )

    if any(
        signal in context
        for signal in schedule_signals
    ):
        return {
            "domain": "academics",
            "category": "academic_calendar",
            "subcategory": "academic_calendar",
            "confidence": "high",
            "score": 180,
        }

    # ==============================================================
    # HEALTH
    # ==============================================================

    health_signals = (
        "health centre",
        "health center",
        "medical centre",
        "medical center",
        "clinic",
        "hospital",
        "health service",
        "medical service",
    )

    if any(
        signal in context
        for signal in health_signals
    ):
        return {
            "domain": "health_safety_and_wellbeing",
            "category": "medical_services",
            "subcategory": "medical_services",
            "confidence": "high",
            "score": 180,
        }

    # ==============================================================
    # LAB / FACILITY
    # ==============================================================

    facility_signals = (
        "laboratory",
        "laboratories",
        "laboratory facility",
        "research lab",
        "research laboratory",
        "workshop",
        "instrumentation facility",
        "fabrication facility",
    )

    if any(
        signal in context
        for signal in facility_signals
    ):
        if any(
            signal in h
            for signal in (
                "equipment",
                "laboratory",
                "lab",
                "facility",
                "workshop",
                "instrument",
                "infrastructure",
            )
        ):
            return {
                "domain": "facilities_and_infrastructure",
                "category": "laboratories",
                "subcategory": "laboratories",
                "confidence": "high",
                "score": 170,
            }

    # ==============================================================
    # RESEARCH
    # ==============================================================

    research_signals = (
        "research project",
        "research projects",
        "research laboratory",
        "research laboratories",
        "research centre",
        "research center",
        "research group",
        "research area",
        "research areas",
        "principal investigator",
        "sponsored research",
    )

    if any(
        signal in context
        for signal in research_signals
    ):
        return {
            "domain": "research",
            "category": "research_projects",
            "subcategory": "research_projects",
            "confidence": "high",
            "score": 160,
        }

    # ==============================================================
    # HOSTEL
    # ==============================================================

    hostel_signals = (
        "hostel",
        "hostels",
        "residential hall",
        "student residence",
        "residential accommodation",
    )

    if any(
        signal in context
        for signal in hostel_signals
    ):
        return {
            "domain": "hostels",
            "category": "accommodation",
            "subcategory": "accommodation",
            "confidence": "high",
            "score": 160,
        }

    # ==============================================================
    # TRANSPORT
    # ==============================================================

    transport_signals = (
        "transportation",
        "transport service",
        "bus service",
        "shuttle service",
        "campus transport",
        "parking",
    )

    if any(
        signal in context
        for signal in transport_signals
    ):
        return {
            "domain": "campus",
            "category": "transportation",
            "subcategory": "transportation",
            "confidence": "high",
            "score": 160,
        }

    # ==============================================================
    # FALL BACK TO GENERIC TAXONOMY
    # ==============================================================

    return classify(
        heading=heading,
        text=text,
        source_name=source_name,
        document_title=document_title,
        document_url=document_url,
    )
