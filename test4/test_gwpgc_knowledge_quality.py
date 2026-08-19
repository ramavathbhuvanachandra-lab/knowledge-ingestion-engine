"""
Test 4 — Real GWPGC Knowledge Quality Audit.

Purpose:
    Audit the existing structured GWPGC corpus without rerunning
    crawling, cleaning, or structuring.

This test does NOT modify data.

It checks for:
    - student/batch records
    - roll numbers
    - registration numbers
    - student IDs
    - admission/merit lists
    - alumni records
    - participant lists
    - media/gallery content
    - obvious administrative/archive material

Important:
    This is an AUDIT only.
    It does not delete or modify any knowledge.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

DOMAIN = "gwpgc.ac.in"

STRUCTURED_ROOT = Path(
    "storage/structured_knowledge"
)

DOMAIN_ROOT = (
    STRUCTURED_ROOT / DOMAIN
)

REPORT_PATH = Path(
    "storage/retrieval"
) / DOMAIN / "knowledge_quality_audit.json"


# ============================================================
# STRONG NON-RAG SIGNALS
# ============================================================

STRONG_NON_RAG_PATTERNS = (
    "batch profile",
    "batch profiles",
    "student profile",
    "student profiles",
    "student roster",
    "student rosters",
    "student list",
    "student lists",
    "students list",
    "list of students",
    "student names",
    "student database",
    "alumni profile",
    "alumni profiles",
    "alumni list",
    "alumni lists",
    "alumni names",
    "alumni directory",
    "participant list",
    "participant lists",
    "attendee list",
    "attendees",
    "admission merit list",
    "merit list",
    "merit lists",
)


# ============================================================
# INDIVIDUAL RECORD SIGNALS
# ============================================================

INDIVIDUAL_RECORD_PATTERNS = (
    r"\broll\s*number\b",
    r"\broll\s*no\b",
    r"\bregistration\s*number\b",
    r"\bregistration\s*no\b",
    r"\bstudent\s*id\b",
    r"\bstudent\s*number\b",
    r"\bserial\s*number\b",
    r"\bs\.?\s*no\.?\b",
    r"\byear\s*of\s*graduation\b",
    r"\byear\s*of\s*admission\b",
    r"\bfather'?s\s+name\b",
    r"\bmother'?s\s+name\b",
    r"\bdate\s+of\s+birth\b",
)


# ============================================================
# ARCHIVE / ADMINISTRATIVE SIGNALS
# ============================================================

ARCHIVE_PATTERNS = (
    "annual report",
    "annual reports",
    "institutional report",
    "institutional reports",
    "newsletter",
    "newsletters",
    "archive",
    "archives",
    "archival",
    "old publication",
    "old publications",
    "completed project",
    "completed projects",
)


# ============================================================
# MEDIA SIGNALS
# ============================================================

MEDIA_PATTERNS = (
    "photo gallery",
    "photo galleries",
    "image gallery",
    "image galleries",
    "video gallery",
    "video galleries",
    "media gallery",
    "photo album",
    "photo albums",
    "photographs",
)


# ============================================================
# HELPERS
# ============================================================

def _text(value) -> str:
    """
    Convert arbitrary JSON values into searchable text.
    """

    if value is None:
        return ""

    if isinstance(value, str):
        return value

    if isinstance(value, list):
        return " ".join(
            _text(item)
            for item in value
        )

    if isinstance(value, dict):
        return " ".join(
            _text(item)
            for item in value.values()
        )

    return str(value)


def _contains_any(
    text: str,
    patterns: tuple[str, ...],
) -> list[str]:

    lowered = text.lower()

    return [
        pattern
        for pattern in patterns
        if pattern in lowered
    ]


def _contains_regex(
    text: str,
    patterns: tuple[str, ...],
) -> list[str]:

    matches = []

    for pattern in patterns:

        if re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        ):
            matches.append(pattern)

    return matches


# ============================================================
# DOCUMENT AUDIT
# ============================================================

def _audit_document(
    path: Path,
) -> dict:

    try:

        data = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )

    except Exception as error:

        return {
            "file": str(path),
            "status": "load_error",
            "error": str(error),
        }

    document = data.get(
        "document",
        {},
    )

    title = _text(
        document.get("title")
    )

    url = _text(
        document.get("url")
    )

    # --------------------------------------------------------
    # Build searchable document text.
    # --------------------------------------------------------

    searchable_parts = [
        title,
        url,
    ]

    for page in data.get(
        "pages",
        [],
    ):

        if not isinstance(
            page,
            dict,
        ):
            continue

        searchable_parts.append(
            _text(page)
        )

    text = "\n".join(
        searchable_parts
    )

    # --------------------------------------------------------
    # Detect signals.
    # --------------------------------------------------------

    strong_patterns = _contains_any(
        text,
        STRONG_NON_RAG_PATTERNS,
    )

    record_patterns = _contains_regex(
        text,
        INDIVIDUAL_RECORD_PATTERNS,
    )

    archive_patterns = _contains_any(
        text,
        ARCHIVE_PATTERNS,
    )

    media_patterns = _contains_any(
        text,
        MEDIA_PATTERNS,
    )

    # --------------------------------------------------------
    # Determine severity.
    # --------------------------------------------------------

    reasons = []

    if strong_patterns:
        reasons.append(
            "bulk student/batch/list content"
        )

    if record_patterns:
        reasons.append(
            "individual student record signals"
        )

    if archive_patterns:
        reasons.append(
            "archive/historical/report content"
        )

    if media_patterns:
        reasons.append(
            "media/gallery content"
        )

    if (
        strong_patterns
        or record_patterns
    ):
        classification = "NON_RAG_CANDIDATE"

    elif media_patterns:
        classification = "MEDIA_CANDIDATE"

    elif archive_patterns:
        classification = "REVIEW"

    else:
        classification = "NORMAL"

    return {
        "file": str(path),
        "title": title,
        "url": url,
        "classification": classification,
        "reasons": reasons,
        "strong_patterns": strong_patterns,
        "individual_record_patterns": (
            record_patterns
        ),
        "archive_patterns": archive_patterns,
        "media_patterns": media_patterns,
    }


# ============================================================
# MAIN AUDIT
# ============================================================

def run_audit() -> dict:

    if not DOMAIN_ROOT.exists():

        raise FileNotFoundError(
            "Structured corpus does not exist: "
            f"{DOMAIN_ROOT}"
        )

    files = sorted(
        DOMAIN_ROOT.rglob("*.json")
    )

    if not files:

        raise RuntimeError(
            "No structured JSON files found: "
            f"{DOMAIN_ROOT}"
        )

    results = []

    for index, path in enumerate(
        files,
        start=1,
    ):

        result = _audit_document(
            path
        )

        results.append(
            result
        )

        if index % 100 == 0:

            print(
                f"[AUDIT {index}/{len(files)}]"
            )

    # ========================================================
    # SUMMARY
    # ========================================================

    summary = {
        "total_files": len(files),
        "normal": 0,
        "non_rag_candidates": 0,
        "media_candidates": 0,
        "review": 0,
        "load_errors": 0,
    }

    for result in results:

        classification = result.get(
            "classification"
        )

        if classification == "NORMAL":
            summary["normal"] += 1

        elif (
            classification
            == "NON_RAG_CANDIDATE"
        ):
            summary[
                "non_rag_candidates"
            ] += 1

        elif (
            classification
            == "MEDIA_CANDIDATE"
        ):
            summary[
                "media_candidates"
            ] += 1

        elif classification == "REVIEW":
            summary["review"] += 1

        elif (
            result.get("status")
            == "load_error"
        ):
            summary["load_errors"] += 1

    # ========================================================
    # REPORT
    # ========================================================

    report = {
        "test": (
            "gwpgc_knowledge_quality_audit"
        ),
        "domain": DOMAIN,
        "structured_root": str(
            DOMAIN_ROOT
        ),
        "summary": summary,
        "results": results,
    }

    REPORT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_PATH.write_text(
        json.dumps(
            report,
            indent=4,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    return report


# ============================================================
# PYTEST TEST
# ============================================================

def test_gwpgc_knowledge_quality():

    report = run_audit()

    summary = report[
        "summary"
    ]

    print()
    print("=" * 80)
    print("GWPGC KNOWLEDGE QUALITY AUDIT")
    print("=" * 80)

    print()
    print(
        "Structured files:",
        summary["total_files"],
    )

    print(
        "Normal:",
        summary["normal"],
    )

    print(
        "NON-RAG candidates:",
        summary["non_rag_candidates"],
    )

    print(
        "Media candidates:",
        summary["media_candidates"],
    )

    print(
        "Review:",
        summary["review"],
    )

    print(
        "Load errors:",
        summary["load_errors"],
    )

    print()
    print(
        "Report:",
        REPORT_PATH,
    )

    # --------------------------------------------------------
    # Show the strongest suspicious records.
    # --------------------------------------------------------

    suspicious = [
        result
        for result in report["results"]
        if result.get(
            "classification"
        )
        == "NON_RAG_CANDIDATE"
    ]

    print()
    print(
        "=" * 80
    )
    print(
        "TOP NON-RAG CANDIDATES"
    )
    print(
        "=" * 80
    )

    for result in suspicious[:30]:

        print()
        print(
            "TITLE:",
            result.get(
                "title",
                "",
            ),
        )

        print(
            "FILE:",
            result["file"],
        )

        print(
            "REASONS:",
            ", ".join(
                result["reasons"]
            ),
        )

        if result[
            "strong_patterns"
        ]:

            print(
                "MATCHES:",
                ", ".join(
                    result[
                        "strong_patterns"
                    ]
                ),
            )

        if result[
            "individual_record_patterns"
        ]:

            print(
                "RECORD SIGNALS:",
                ", ".join(
                    result[
                        "individual_record_patterns"
                    ]
                ),
            )

    print()
    print(
        "=" * 80
    )
    print(
        "AUDIT COMPLETE"
    )
    print(
        "=" * 80
    )

    assert summary[
        "total_files"
    ] > 0