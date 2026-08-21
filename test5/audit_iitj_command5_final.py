"""
IIT Jodhpur — Command 5 Semantic + Buffer Audit V1

Purpose
-------
Audit the REAL 855-unit IITJ Command 5 output before freezing the organizer.

Checks:
- 855/855 lossless coverage from manifest/plan
- duplicate/missing/extra assignments
- document distribution by top-level family
- department entity coverage
- school/platform/office/program entity coverage
- fallback/buffer size and contents
- generic/suspicious document names
- oversized documents
- empty/near-empty documents
- source traceability presence
- simple semantic mismatch signals
- duplicate source-document concentration
- exact unit distribution by document

This is a deterministic audit. It does not mutate the organizer output.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = (
    PROJECT_ROOT / "storage_v2" / "command5" / "iitj_final"
)
PLAN_PATH = OUTPUT_ROOT / "iitj_organization_plan.json"
MANIFEST_PATH = OUTPUT_ROOT / "iitj_organization_manifest.json"

REPORT_JSON = OUTPUT_ROOT / "iitj_semantic_audit.json"
REPORT_MD = OUTPUT_ROOT / "iitj_semantic_audit.md"

# IITJ department map for audit only.
EXPECTED_DEPARTMENTS = {
    "aerospace_engineering",
    "bioscience_and_bioengineering",
    "chemical_engineering",
    "chemistry",
    "civil_and_infrastructure_engineering",
    "computer_science_and_engineering",
    "economics",
    "electrical_engineering",
    "electronics_engineering",
    "energy_and_automotive_engineering",
    "environmental_and_sustainability_engineering",
    "materials_engineering",
    "mathematics",
    "mechanical_engineering",
    "physics",
}

EXPECTED_SCHOOLS = {
    "artificial_intelligence_and_data_science",
    "design",
    "liberal_arts",
    "management_and_entrepreneurship",
}

EXPECTED_PLATFORMS = {
    "digital_humanities",
    "space_science_and_technology",
    "internet_of_things_and_applications",
    "autonomous_unmanned_vehicles",
    "quantum_information_and_computation",
    "cognitive_science",
    "smart_healthcare",
}

EXPECTED_PROGRAMS = {
    "btech",
    "mtech",
    "msc",
    "phd",
    "bs",
    "mba",
    "bdes",
    "ms_by_research",
}

SUSPICIOUS_GENERIC_NAMES = {
    "general_information.md",
}

TOPIC_SIGNALS = {
    "faculty": ("faculty", "professor", "teaching staff"),
    "research": ("research", "thesis", "research project", "postdoc"),
    "programs": ("program", "programme", "course", "curriculum"),
    "admissions": ("admission", "admissions", "eligibility", "application"),
    "facilities": ("facility", "facilities", "laboratory", "lab", "equipment"),
    "rules_and_regulations": ("rule", "regulation", "policy", "guideline"),
    "finance": ("fee", "fees", "tuition", "payment", "refund", "charges"),
    "training": ("training", "upskilling", "vocational", "skill"),
    "international": ("international", "exchange", "mou"),
    "alumni": ("alumni",),
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def words(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def extract_markdown_body(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def audit() -> dict:
    if not PLAN_PATH.exists():
        raise FileNotFoundError(PLAN_PATH)
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(MANIFEST_PATH)

    plan = read_json(PLAN_PATH)
    manifest = read_json(MANIFEST_PATH)

    documents = plan.get("documents", [])
    assignments = manifest.get("assignments", [])
    coverage = manifest.get("coverage", {})

    path_set = {doc["path"] for doc in documents}

    actual_md = {
        str(path.relative_to(OUTPUT_ROOT))
        for path in OUTPUT_ROOT.rglob("*.md")
    }

    actual_md.discard("iitj_semantic_audit.md")

    missing_files = sorted(
        path
        for path in path_set
        if path not in actual_md
    )

    extra_md = sorted(
        path
        for path in actual_md
        if path not in path_set
    )

    assignment_counter = Counter(
        row["unit_id"]
        for row in assignments
    )

    document_units = {
        doc["path"]: list(doc.get("unit_ids", []))
        for doc in documents
    }

    total_words = 0
    empty_docs = []
    tiny_docs = []
    oversized_docs = []
    generic_docs = []
    suspicious_semantic_docs = []

    top_level_counts = Counter()
    entity_counts = Counter()
    buffer_docs = []
    buffer_unit_ids = []

    source_counts = Counter()
    unit_to_docs = defaultdict(list)

    for row in assignments:
        source_counts[row.get("source_file", "")] += 1
        unit_to_docs[row["unit_id"]].append(row["path"])

    for doc in documents:
        rel = doc["path"]
        path = OUTPUT_ROOT / rel

        root = Path(rel).parts[0]
        top_level_counts[root] += 1

        if doc.get("entity_type"):
            entity_counts[doc["entity_type"]] += 1

        if doc.get("buffer_name"):
            buffer_docs.append(rel)
            buffer_unit_ids.extend(doc.get("unit_ids", []))

        if path.exists():
            text = extract_markdown_body(path)
            count = words(text)
        else:
            count = 0

        total_words += count

        if count == 0:
            empty_docs.append(rel)
        elif count < 50:
            tiny_docs.append(
                {"path": rel, "words": count}
            )

        if count > 5000:
            oversized_docs.append(
                {"path": rel, "words": count}
            )

        if path.name in SUSPICIOUS_GENERIC_NAMES:
            generic_docs.append(rel)

        topic = normalize(doc.get("topic", ""))
        body = normalize(
            text if path.exists() else ""
        )

        signals = TOPIC_SIGNALS.get(
            topic,
            (),
        )

        if (
            signals
            and body
            and not any(signal in body for signal in signals)
            and count > 80
        ):
            suspicious_semantic_docs.append(
                {
                    "path": rel,
                    "topic": topic,
                    "words": count,
                    "reason": "No obvious topic signal in document body",
                }
            )

    assignment_duplicates = sorted(
        unit_id
        for unit_id, count in assignment_counter.items()
        if count > 1
    )

    assignment_missing = sorted(
        coverage.get("missing_unit_ids", [])
    )
    assignment_unassigned = sorted(
        coverage.get("unassigned_unit_ids", [])
    )
    assignment_extra = sorted(
        coverage.get("extra_unit_ids", [])
    )

    department_paths = set()
    school_paths = set()
    platform_paths = set()
    program_paths = set()

    for doc in documents:
        parts = Path(doc["path"]).parts
        if len(parts) >= 2:
            if parts[0] == "departments":
                department_paths.add(parts[1])
            elif parts[0] == "schools":
                school_paths.add(parts[1])
            elif parts[0] == "research_platforms":
                platform_paths.add(parts[1])
            elif parts[0] == "programs" and len(parts) >= 2:
                program_paths.add(parts[1])

    missing_department_entities = sorted(
        EXPECTED_DEPARTMENTS - department_paths
    )
    present_department_entities = sorted(
        EXPECTED_DEPARTMENTS & department_paths
    )

    missing_school_entities = sorted(
        EXPECTED_SCHOOLS - school_paths
    )
    missing_platform_entities = sorted(
        EXPECTED_PLATFORMS - platform_paths
    )
    missing_program_entities = sorted(
        EXPECTED_PROGRAMS - program_paths
    )

    fallback_words = 0
    for rel in buffer_docs:
        path = OUTPUT_ROOT / rel
        if path.exists():
            fallback_words += words(
                path.read_text(
                    encoding="utf-8",
                    errors="replace",
                )
            )

    report = {
        "audit_version": "iitj_command5_semantic_audit_v1",
        "input": {
            "plan_path": str(PLAN_PATH),
            "manifest_path": str(MANIFEST_PATH),
            "unit_count": plan.get("unit_count"),
            "document_count": plan.get("document_count"),
        },
        "coverage": {
            "input_unit_count": coverage.get("input_unit_count"),
            "assigned_unit_count": coverage.get("assigned_unit_count"),
            "missing": assignment_missing,
            "unassigned": assignment_unassigned,
            "duplicate": assignment_duplicates,
            "extra": assignment_extra,
            "lossless": not (
                assignment_missing
                or assignment_unassigned
                or assignment_duplicates
                or assignment_extra
            ),
        },
        "document_inventory": {
            "actual_markdown_count": len(actual_md),
            "planned_markdown_count": len(path_set),
            "missing_output_files": missing_files,
            "extra_markdown_files": extra_md,
            "top_level_document_counts": dict(
                sorted(top_level_counts.items())
            ),
            "empty_documents": empty_docs,
            "tiny_documents_under_50_words": tiny_docs,
            "oversized_documents_over_5000_words": oversized_docs,
            "generic_filename_documents": generic_docs,
            "total_words": total_words,
        },
        "entity_audit": {
            "department_entities_present": present_department_entities,
            "department_entities_missing_from_output": missing_department_entities,
            "schools_missing": missing_school_entities,
            "research_platforms_missing": missing_platform_entities,
            "program_entities_missing": missing_program_entities,
            "entity_document_type_counts": dict(
                sorted(entity_counts.items())
            ),
        },
        "buffer_audit": {
            "buffer_document_count": len(buffer_docs),
            "buffer_documents": sorted(buffer_docs),
            "buffer_unit_count": len(set(buffer_unit_ids)),
            "buffer_word_count": fallback_words,
            "buffer_unit_ids": sorted(set(buffer_unit_ids)),
        },
        "semantic_flags": {
            "generic_documents": generic_docs,
            "simple_topic_signal_mismatches": suspicious_semantic_docs,
        },
        "source_audit": {
            "source_document_count": len(source_counts),
            "largest_sources": [
                {
                    "source_file": source,
                    "accepted_unit_count": count,
                }
                for source, count in source_counts.most_common(30)
            ],
        },
    }

    return report


def write_markdown(report: dict) -> None:
    c = report["coverage"]
    d = report["document_inventory"]
    e = report["entity_audit"]
    b = report["buffer_audit"]
    s = report["semantic_flags"]

    lines = [
        "# IIT Jodhpur — Command 5 Semantic + Buffer Audit",
        "",
        "## Verdict",
        "",
        f"- Lossless coverage: **{'PASS' if c['lossless'] else 'FAIL'}**",
        f"- Input units: **{c['input_unit_count']}**",
        f"- Assigned units: **{c['assigned_unit_count']}**",
        f"- Planned documents: **{d['planned_markdown_count']}**",
        f"- Actual Markdown documents: **{d['actual_markdown_count']}**",
        f"- Total output words: **{d['total_words']}**",
        "",
        "## Coverage",
        "",
        f"- Missing: {len(c['missing'])}",
        f"- Unassigned: {len(c['unassigned'])}",
        f"- Duplicates: {len(c['duplicate'])}",
        f"- Extra: {len(c['extra'])}",
        "",
        "## Top-level document distribution",
        "",
    ]

    for key, value in d["top_level_document_counts"].items():
        lines.append(f"- `{key}`: {value} documents")

    lines.extend(
        [
            "",
            "## Department entity audit",
            "",
            f"- Present recognized departments: {len(e['department_entities_present'])}",
            f"- Missing recognized departments: {len(e['department_entities_missing_from_output'])}",
        ]
    )

    if e["department_entities_missing_from_output"]:
        for item in e["department_entities_missing_from_output"]:
            lines.append(f"  - `{item}`")

    lines.extend(
        [
            "",
            "## Other entity-family audit",
            "",
            f"- Missing schools: {len(e['schools_missing'])}",
            f"- Missing research platforms: {len(e['research_platforms_missing'])}",
            f"- Missing program entities: {len(e['program_entities_missing'])}",
        ]
    )

    for title, items in (
        ("Missing schools", e["schools_missing"]),
        ("Missing research platforms", e["research_platforms_missing"]),
        ("Missing program entities", e["program_entities_missing"]),
    ):
        if items:
            lines.append(f"### {title}")
            for item in items:
                lines.append(f"- `{item}`")
            lines.append("")

    lines.extend(
        [
            "## Buffer audit",
            "",
            f"- Buffer documents: {b['buffer_document_count']}",
            f"- Buffered units: {b['buffer_unit_count']}",
            f"- Buffered words: {b['buffer_word_count']}",
        ]
    )

    if b["buffer_documents"]:
        lines.append("- Buffer files:")
        for item in b["buffer_documents"]:
            lines.append(f"  - `{item}`")

    lines.extend(
        [
            "",
            "## Quality flags",
            "",
            f"- Empty documents: {len(d['empty_documents'])}",
            f"- Tiny documents (<50 words): {len(d['tiny_documents_under_50_words'])}",
            f"- Oversized documents (>5000 words): {len(d['oversized_documents_over_5000_words'])}",
            f"- Generic filenames: {len(d['generic_filename_documents'])}",
            f"- Simple semantic signal mismatches: {len(s['simple_topic_signal_mismatches'])}",
            "",
        ]
    )

    if d["generic_filename_documents"]:
        lines.append("### Generic filenames")
        for item in d["generic_filename_documents"]:
            lines.append(f"- `{item}`")
        lines.append("")

    if d["oversized_documents_over_5000_words"]:
        lines.append("### Oversized documents")
        for item in d["oversized_documents_over_5000_words"]:
            lines.append(
                f"- `{item['path']}` — {item['words']} words"
            )
        lines.append("")

    if s["simple_topic_signal_mismatches"]:
        lines.append("### Simple semantic mismatch candidates")
        for item in s["simple_topic_signal_mismatches"][:100]:
            lines.append(
                f"- `{item['path']}` — topic `{item['topic']}` — "
                f"{item['words']} words"
            )
        lines.append("")

    lines.extend(
        [
            "## Largest source contributors",
            "",
        ]
    )

    for item in report["source_audit"]["largest_sources"]:
        lines.append(
            f"- `{item['source_file']}` — "
            f"{item['accepted_unit_count']} accepted units"
        )

    lines.extend(
        [
            "",
            "## Freeze recommendation",
            "",
            (
                "Do not freeze Command 5 until the buffer has been reviewed, "
                "missing entity candidates have been explained, and any "
                "semantic flags that are genuine misroutes have been fixed."
            ),
            "",
        ]
    )

    REPORT_MD.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def main() -> None:
    report = audit()
    REPORT_JSON.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    write_markdown(report)

    print("=" * 100)
    print("IIT JODHPUR — COMMAND 5 SEMANTIC + BUFFER AUDIT")
    print("=" * 100)
    print()
    print("Lossless:", "PASS" if report["coverage"]["lossless"] else "FAIL")
    print(
        "Units:",
        report["input"]["unit_count"],
    )
    print(
        "Documents:",
        report["input"]["document_count"],
    )
    print(
        "Buffer units:",
        report["buffer_audit"]["buffer_unit_count"],
    )
    print(
        "Missing departments:",
        len(
            report["entity_audit"][
                "department_entities_missing_from_output"
            ]
        ),
    )
    print(
        "Generic docs:",
        len(
            report["document_inventory"][
                "generic_filename_documents"
            ]
        ),
    )
    print(
        "Semantic flags:",
        len(
            report["semantic_flags"][
                "simple_topic_signal_mismatches"
            ]
        ),
    )
    print()
    print("JSON:", REPORT_JSON)
    print("MD  :", REPORT_MD)


if __name__ == "__main__":
    main()