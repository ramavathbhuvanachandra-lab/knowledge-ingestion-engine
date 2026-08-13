from pathlib import Path
import json
import re
import ollama


# ============================================================
# PHASE 8.1 — DYNAMIC KNOWLEDGE ORGANIZATION PLANNER
# ============================================================

MODEL = "qwen3:4b"

INPUT_ROOT = Path(
    "storage/structured_knowledge"
)

OUTPUT_ROOT = Path(
    "storage/organization_plans"
)


# ============================================================
# LLM SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = """
You are a knowledge organization planner for a college
knowledge-ingestion pipeline.

Your ONLY job is to design a sensible organization plan for
the supplied structured college knowledge.

The knowledge has already been:
- scraped
- cleaned
- structurally parsed

DO NOT:
- rewrite content
- summarize content
- delete content
- invent facts
- invent knowledge
- create embeddings
- create chunks
- create Markdown files
- use outside knowledge
- force the document into a predefined category list

You MAY:
- group related sections together
- create sensible knowledge categories
- create sensible document filenames
- decide that multiple documents are appropriate
- keep unrelated knowledge in separate documents

IMPORTANT:

Categories must be determined from the actual supplied
knowledge.

Do NOT assume every college has the same categories.

Use the SMALLEST reasonable number of documents that keeps
distinct knowledge areas understandable.

Each source knowledge section must belong to at most one
output document.

Navigation and accessibility sections should NOT become
knowledge documents.

Return ONLY valid JSON in exactly this shape:

{
  "documents": [
    {
      "category": "string",
      "filename": "string",
      "section_ids": ["S001", "S002"]
    }
  ]
}

Rules:

1. category must be lowercase.
2. category may contain lowercase letters, numbers,
   underscores, and hyphens only.
3. filename must be lowercase.
4. filename must contain no extension.
5. section_ids must refer only to supplied section IDs.
6. Every knowledge section should be assigned exactly once.
7. Navigation/accessibility sections should normally be
   excluded.
8. Do not create empty documents.
9. Do not create a category merely because it sounds useful.
10. Do not create one document per section unless the sections
    are genuinely unrelated.
"""


# ============================================================
# LOAD STRUCTURED DOCUMENT
# ============================================================

def load_structured_document(
    path: Path,
) -> dict:

    if not path.exists():
        raise FileNotFoundError(
            f"Structured JSON does not exist: {path}"
        )

    if not path.is_file():
        raise ValueError(
            f"Structured path is not a file: {path}"
        )

    data = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(
        data,
        dict,
    ):
        raise AssertionError(
            "Structured document must be a JSON object"
        )

    pages = data.get(
        "pages"
    )

    if not isinstance(
        pages,
        list,
    ):
        raise AssertionError(
            "Structured document pages must be a list"
        )

    return data


# ============================================================
# COLLECT SECTIONS
# ============================================================

def collect_sections(
    structured: dict,
) -> list[dict]:

    sections = []

    counter = 1

    for page in structured.get(
        "pages",
        [],
    ):

        page_number = page.get(
            "page_number"
        )

        page_sections = page.get(
            "sections",
            [],
        )

        if not isinstance(
            page_sections,
            list,
        ):
            continue

        for section in page_sections:

            if not isinstance(
                section,
                dict,
            ):
                continue

            section_id = (
                f"S{counter:03d}"
            )

            content = section.get(
                "content",
                [],
            )

            if not isinstance(
                content,
                list,
            ):
                content = []

            sections.append(
                {
                    "id": section_id,
                    "page_number": page_number,
                    "heading": section.get(
                        "heading"
                    ),
                    "level": section.get(
                        "level"
                    ),
                    "content_type": section.get(
                        "content_type",
                        "knowledge",
                    ),
                    "content": content,
                }
            )

            counter += 1

    return sections


# ============================================================
# BUILD COMPACT LLM INPUT
# ============================================================

def build_planning_input(
    sections: list[dict],
) -> list[dict]:

    result = []

    for section in sections:

        content = section.get(
            "content",
            [],
        )

        content_text = " ".join(
            str(item)
            for item in content
        ).strip()

        # ----------------------------------------------------
        # IMPORTANT:
        #
        # The LLM is only planning organization.
        # It does NOT need the full section content.
        #
        # Keep the context deliberately small.
        # ----------------------------------------------------

        preview = content_text[:300]

        result.append(
            {
                "id": section["id"],
                "page_number": section[
                    "page_number"
                ],
                "heading": section[
                    "heading"
                ],
                "level": section[
                    "level"
                ],
                "content_type": section[
                    "content_type"
                ],
                "content_preview": preview,
            }
        )

    return result


# ============================================================
# SAFE COMPONENT
# ============================================================

def clean_component(
    value: str,
) -> str:

    value = (
        value or ""
    ).strip().lower()

    value = re.sub(
        r"[^a-z0-9_-]+",
        "_",
        value,
    )

    value = re.sub(
        r"_+",
        "_",
        value,
    )

    return (
        value.strip("_-")
        or "other"
    )


# ============================================================
# CREATE ORGANIZATION PLAN WITH LLM
# ============================================================

def create_plan(
    structured: dict,
    sections: list[dict],
) -> dict:

    planning_sections = (
        build_planning_input(
            sections
        )
    )

    prompt = f"""
Create an organization plan for this college knowledge
document.

DOCUMENT METADATA:

{json.dumps(
    structured.get(
        "document",
        {},
    ),
    indent=2,
    ensure_ascii=False,
)}

STRUCTURED SECTIONS:

{json.dumps(
    planning_sections,
    indent=2,
    ensure_ascii=False,
)}
"""

    print(
        "Calling Qwen..."
    )

    response = ollama.chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        format="json",
        options={
            "temperature": 0,
        },
    )

    raw = response[
        "message"
    ][
        "content"
    ]

    print(
        "Qwen response received."
    )

    try:

        plan = json.loads(
            raw
        )

    except json.JSONDecodeError as exc:

        raise AssertionError(
            "LLM returned invalid JSON:\n"
            f"{raw}"
        ) from exc

    return plan


# ============================================================
# VALIDATE ORGANIZATION PLAN
# ============================================================

def validate_plan(
    plan: dict,
    sections: list[dict],
) -> dict:

    if not isinstance(
        plan,
        dict,
    ):
        raise AssertionError(
            "Organization plan must be a JSON object"
        )

    documents = plan.get(
        "documents"
    )

    if not isinstance(
        documents,
        list,
    ):
        raise AssertionError(
            "Organization plan 'documents' "
            "must be a list"
        )

    section_map = {
        section["id"]: section
        for section in sections
    }

    assigned = set()

    validated_documents = []

    for index, document in enumerate(
        documents,
        start=1,
    ):

        if not isinstance(
            document,
            dict,
        ):
            raise AssertionError(
                f"Document #{index} must be an object"
            )

        category = clean_component(
            document.get(
                "category"
            )
        )

        filename = clean_component(
            document.get(
                "filename"
            )
        )

        section_ids = document.get(
            "section_ids"
        )

        if not isinstance(
            section_ids,
            list,
        ):
            raise AssertionError(
                f"Document #{index} "
                "section_ids must be a list"
            )

        if not section_ids:
            raise AssertionError(
                f"Document #{index} "
                "cannot contain zero sections"
            )

        validated_ids = []

        for section_id in section_ids:

            if section_id not in section_map:

                raise AssertionError(
                    f"Document #{index} references "
                    f"unknown section: {section_id}"
                )

            if section_id in assigned:

                raise AssertionError(
                    f"Section assigned more than once: "
                    f"{section_id}"
                )

            section = section_map[
                section_id
            ]

            content_type = section.get(
                "content_type",
                "knowledge",
            )

            if content_type in (
                "navigation",
                "accessibility",
            ):

                raise AssertionError(
                    f"Non-knowledge section assigned "
                    f"to document: {section_id} "
                    f"(type={content_type})"
                )

            assigned.add(
                section_id
            )

            validated_ids.append(
                section_id
            )

        validated_documents.append(
            {
                "category": category,
                "filename": filename,
                "section_ids": validated_ids,
            }
        )

    # --------------------------------------------------------
    # CHECK ALL KNOWLEDGE SECTIONS
    # --------------------------------------------------------

    knowledge_ids = {
        section["id"]
        for section in sections
        if section.get(
            "content_type",
            "knowledge",
        )
        not in (
            "navigation",
            "accessibility",
        )
    }

    missing = (
        knowledge_ids
        - assigned
    )

    if missing:

        raise AssertionError(
            "Knowledge sections were not assigned "
            "to an organization document: "
            f"{sorted(missing)}"
        )

    # --------------------------------------------------------
    # CHECK FOR DUPLICATE OUTPUT PATHS
    # --------------------------------------------------------

    output_paths = set()

    for document in validated_documents:

        output_key = (
            document["category"],
            document["filename"],
        )

        if output_key in output_paths:

            raise AssertionError(
                "Duplicate organization document: "
                f"{document['category']}/"
                f"{document['filename']}"
            )

        output_paths.add(
            output_key
        )

    return {
        "documents": validated_documents
    }


# ============================================================
# SELECT TEST DOCUMENT
# ============================================================

def find_test_documents() -> list[Path]:

    files = sorted(
        INPUT_ROOT.rglob("*.json")
    )

    if not files:

        raise FileNotFoundError(
            f"No structured JSON files found in "
            f"{INPUT_ROOT}"
        )

    # --------------------------------------------------------
    # PHASE 8.1 FIRST REAL TEST
    #
    # Process ONE known real document.
    # Once this passes, we will remove this restriction
    # and process all documents.
    # --------------------------------------------------------

    target_name = (
        "government_girls_p_g_college_ghazipur.json"
    )

    selected = [
        path
        for path in files
        if path.name == target_name
    ]

    if not selected:

        raise FileNotFoundError(
            "Phase 8.1 test document not found: "
            f"{target_name}"
        )

    return selected


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 100)
    print(
        "PHASE 8.1 — DYNAMIC KNOWLEDGE ORGANIZATION PLANNER"
    )
    print("=" * 100)

    print(
        "Model:",
        MODEL,
    )

    files = find_test_documents()

    print(
        "Structured documents:",
        len(files),
    )

    OUTPUT_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    passed = 0

    for path in files:

        print()
        print("-" * 100)

        print(
            "INPUT:",
            path,
        )

        structured = (
            load_structured_document(
                path
            )
        )

        sections = (
            collect_sections(
                structured
            )
        )

        print(
            "Sections:",
            len(sections),
        )

        knowledge_count = sum(
            1
            for section in sections
            if section.get(
                "content_type",
                "knowledge",
            )
            not in (
                "navigation",
                "accessibility",
            )
        )

        print(
            "Knowledge sections:",
            knowledge_count,
        )

        print(
            "Navigation/UI sections:",
            len(sections)
            - knowledge_count,
        )

        # ----------------------------------------------------
        # LLM PLAN
        # ----------------------------------------------------

        plan = create_plan(
            structured,
            sections,
        )

        # ----------------------------------------------------
        # DETERMINISTIC VALIDATION
        # ----------------------------------------------------

        validated_plan = (
            validate_plan(
                plan,
                sections,
            )
        )

        # ----------------------------------------------------
        # OUTPUT
        # ----------------------------------------------------

        domain = clean_component(
            structured.get(
                "document",
                {},
            ).get(
                "domain",
                path.parent.name,
            )
        )

        output_file = (
            OUTPUT_ROOT
            / domain
            / f"{path.stem}.organization.json"
        )

        output_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_file.write_text(
            json.dumps(
                validated_plan,
                indent=4,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        # ----------------------------------------------------
        # DISPLAY PLAN
        # ----------------------------------------------------

        print()
        print(
            "ORGANIZATION PLAN:"
        )

        print(
            json.dumps(
                validated_plan,
                indent=2,
                ensure_ascii=False,
            )
        )

        print()
        print(
            "PLAN:",
            output_file,
        )

        passed += 1

    print()
    print("=" * 100)
    print(
        "PHASE 8.1 TEST RESULT"
    )
    print("=" * 100)

    print(
        "Documents tested :",
        len(files),
    )

    print(
        "Documents passed :",
        passed,
    )

    assert passed == len(
        files
    ), (
        "One or more Phase 8.1 documents failed"
    )

    print()
    print(
        "PHASE 8.1 DYNAMIC KNOWLEDGE "
        "ORGANIZATION PLANNER: PASS"
    )
    print("=" * 100)


if __name__ == "__main__":
    main()