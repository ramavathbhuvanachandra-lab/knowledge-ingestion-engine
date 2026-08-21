"""
IIT Jodhpur — Command 5 Buffer Inspection V1

Reads only the generated Command 5 output and reports every buffered unit with:
- unit id
- heading
- source file
- source URL
- word count
- likely semantic family signals

No files are modified.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ROOT = PROJECT_ROOT / "storage_v2" / "command5" / "iitj_final"
PLAN = ROOT / "iitj_organization_plan.json"
MANIFEST = ROOT / "iitj_organization_manifest.json"
REPORT = ROOT / "iitj_buffer_inspection.md"
JSON_REPORT = ROOT / "iitj_buffer_inspection.json"

SIGNALS = {
    "department": (
        "department", "engineering", "chemistry", "mathematics",
        "physics", "economics", "faculty", "head of department",
    ),
    "school": (
        "school of", "school",
    ),
    "research_platform": (
        "research platform", "quantum", "iot", "autonomous unmanned",
        "cognitive science", "smart healthcare", "digital humanities",
        "space science",
    ),
    "office": (
        "office of", "registrar", "accounts", "estate", "director",
        "deputy director", "internal audit", "stores and purchase",
        "international relations", "alumni affairs",
    ),
    "program": (
        "b.tech", "btech", "m.tech", "mtech", "m.sc", "msc", "ph.d",
        "phd", "b.s", "bs", "mba", "b.des", "program", "programme",
        "curriculum", "course",
    ),
    "admissions": (
        "admission", "admissions", "eligibility", "application",
        "applicant", "shortlist", "waitlist",
    ),
    "hostel": (
        "hostel", "accommodation", "mess", "warden", "residence",
    ),
    "finance": (
        "fee", "fees", "tuition", "payment", "refund", "charges",
        "scholarship", "fellowship", "assistantship",
    ),
    "training": (
        "training", "upskilling", "vocational", "skill",
        "government e marketplace", "gfr",
    ),
    "international": (
        "international", "exchange", "mou",
    ),
    "alumni": (
        "alumni", "alumni affairs", "dora",
    ),
    "facility": (
        "facility", "facilities", "laboratory", "lab", "equipment",
        "health centre", "health center", "infrastructure",
    ),
    "research": (
        "research", "postdoc", "postdoctoral", "thesis", "project",
        "scholar in residence",
    ),
    "academics": (
        "registration", "academic calendar", "examination", "grading",
        "attendance", "leave", "branch change", "academic performance",
    ),
}


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def classify_signal(text: str) -> list[tuple[str, int]]:
    n = norm(text)
    scores = []
    for family, signals in SIGNALS.items():
        score = sum(1 for signal in signals if signal in n)
        if score:
            scores.append((family, score))
    return sorted(scores, key=lambda x: (-x[1], x[0]))


def main() -> None:
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    docs = plan["documents"]

    buffer_docs = [
        doc for doc in docs
        if doc.get("buffer_name")
    ]

    rows = []
    counts = Counter()

    for doc in buffer_docs:
        for unit_id in doc["unit_ids"]:
            # The Markdown source of the generated document is the canonical
            # place where the exact unit content and traceability remain.
            md_path = ROOT / doc["path"]
            md_text = md_path.read_text(encoding="utf-8", errors="replace")

            marker = f"## "
            # The unit content is already embedded in the document. We use the
            # metadata block and a coarse signal scan across the document text.
            signals = classify_signal(md_text)

            rows.append({
                "unit_id": unit_id,
                "buffer_document": doc["path"],
                "topic": doc.get("topic"),
                "signals": signals[:5],
            })

        counts[doc["path"]] += len(doc["unit_ids"])

    result = {
        "buffer_document_count": len(buffer_docs),
        "buffer_unit_count": sum(counts.values()),
        "documents": sorted(
            [
                {
                    "path": doc["path"],
                    "unit_count": len(doc["unit_ids"]),
                }
                for doc in buffer_docs
            ],
            key=lambda x: x["path"],
        ),
        "units": rows,
    }

    JSON_REPORT.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    lines = [
        "# IITJ Command 5 — Buffer Inspection",
        "",
        f"- Buffer documents: **{len(buffer_docs)}**",
        f"- Buffered units: **{sum(counts.values())}**",
        "",
        "## Buffered documents",
        "",
    ]

    for doc in result["documents"]:
        lines.append(
            f"- `{doc['path']}` — {doc['unit_count']} units"
        )

    lines.extend([
        "",
        "## Buffer unit signal scan",
        "",
    ])

    for row in rows:
        signals = ", ".join(
            f"{name}:{score}"
            for name, score in row["signals"]
        ) or "no strong planning signal"

        lines.append(
            f"- `{row['unit_id']}` — `{row['buffer_document']}` — {signals}"
        )

    REPORT.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    print("=" * 100)
    print("IITJ COMMAND 5 — BUFFER INSPECTION")
    print("=" * 100)
    print("Buffer documents:", len(buffer_docs))
    print("Buffered units:", sum(counts.values()))
    for doc in result["documents"]:
        print(f"  - {doc['path']} : {doc['unit_count']} units")
    print("Report:", REPORT)


if __name__ == "__main__":
    main()