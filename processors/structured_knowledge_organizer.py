"""
Phase 8.3 — Structured Knowledge Organizer

Input
-----
storage/structured_knowledge/<domain>/*.json

Structured document format
--------------------------
{
    "document": {
        "title": "...",
        "url": "...",
        "domain": "...",
        "category": "...",
        "document_type": "...",
        "source_file": ...
    },
    "pages": [
        {
            "page_number": ...,
            "sections": [
                {
                    "heading": "...",
                    "level": ...,
                    "content": [...],
                    "content_type": "knowledge|navigation|..."
                }
            ]
        }
    ]
}

Responsibilities
----------------
- Process structured JSON directly.
- Preserve source-document identity.
- Preserve section hierarchy.
- Remove obvious navigation/UI noise.
- Remove empty/unextractable document shells.
- Preserve meaningful heading-less content.
- Generate deterministic fallback headings when necessary.
- Preserve REVIEW content.
- Apply deterministic manual taxonomy/context rules.
- Generate knowledge_units.json.

This phase does NOT:
- use an LLM
- summarize
- rewrite
- chunk
- embed
- create vectors
- create final DOCX
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import hashlib
import json
import re

from processors.knowledge_context_rules import (
    classify_with_context,
)


from processors.knowledge_content_triage import KnowledgeContentTriage


class StructuredKnowledgeOrganizer:

    # ==================================================================
    # NOISE DEFINITIONS
    # ==================================================================

    NOISE_HEADINGS = {
        "search here",
        "search",
        "accessibility options",
        "accessibility",
        "menu",
        "navigation",
        "quick access",
        "quick links",
        "important links",
        "useful links",
        "rate this translation",
        "do you like to give feedback",
        "submit",
        "cookie",
        "cookies",
        "login",
        "sign in",
        "sign up",
        "skip to content",
    }

    NOISE_EXACT_CONTENT = {
        "submit",
        "created by",
        "arrow downward",
        "arrow down",
        "do you like to give feedback submit",
        "no extractable text",
    }

    NOISE_PHRASES = (
        "accessibility options",
        "open the accessibility option",
        "bigger text",
        "smaller text",
        "text spacing",
        "dyslexia friendly",
        "adhd mode",
        "saturation low saturation high saturation",
        "desaturate",
        "invert colors",
        "highlight links",
        "text to speech",
        "pause animation",
        "hide images",
        "reset all settings",
    )

    # ==================================================================
    # CONSTRUCTOR
    # ==================================================================

    def __init__(
        self,
        input_root: str | Path = (
            "storage/structured_knowledge"
        ),
        output_root: str | Path = (
            "storage/organized_knowledge_8_3_test"
        ),
    ):
        self.input_root = Path(input_root)
        self.output_root = Path(output_root)

    # ==================================================================
    # ONE DOCUMENT
    # ==================================================================

        self.rag_triage = KnowledgeContentTriage()


    def organize_document(
        self,
        json_path: str | Path,
    ) -> dict:

        json_path = Path(json_path)

        if not json_path.exists():
            raise FileNotFoundError(
                f"Structured JSON does not exist: {json_path}"
            )

        data = json.loads(
            json_path.read_text(
                encoding="utf-8"
            )
        )

        self._validate_document(
            data,
            json_path,
        )

        document = data.get(
            "document",
            {},
        )

        title = (
            document.get("title", "")
            or ""
        )

        url = (
            document.get("url", "")
            or ""
        )

        source_domain = (
            document.get("domain", "")
            or ""
        )

        original_category = (
            document.get("category", "")
            or ""
        )

        document_type = (
            document.get("document_type", "")
            or ""
        )

        units = []

        sections_seen = 0
        noise_sections = 0
        empty_sections = 0

        for page_index, page in enumerate(
            data.get("pages", []),
            start=1,
        ):

            if not isinstance(page, dict):
                continue

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

            # Each page gets its own hierarchy stack.
            hierarchy_stack = []

            for section_index, section in enumerate(
                page_sections,
                start=1,
            ):

                if not isinstance(
                    section,
                    dict,
                ):
                    continue

                sections_seen += 1

                original_heading = section.get(
                    "heading"
                )

                heading = original_heading

                level = section.get(
                    "level",
                    0,
                )

                content_type = (
                    section.get(
                        "content_type",
                        "knowledge",
                    )
                    or "knowledge"
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

                text = self._content_to_text(
                    content
                )

                # ------------------------------------------------------
                # IMPORTANT:
                #
                # Update hierarchy BEFORE filtering the section.
                #
                # Therefore an empty parent such as:
                #
                #   About
                #       Vision
                #
                # still becomes part of Vision's section_path.
                # ------------------------------------------------------

                section_path = (
                    self._build_section_path(
                        hierarchy_stack=hierarchy_stack,
                        heading=heading,
                        level=level,
                    )
                )

                decision = self._decide_section(
                    heading=heading,
                    text=text,
                    content_type=content_type,
                )

                if decision == "NOISE":
                    noise_sections += 1
                    continue

                if not text.strip():
                    empty_sections += 1
                    continue

                # ------------------------------------------------------
                # Meaningful content with no explicit heading.
                #
                # Do NOT delete it.
                #
                # Give it a deterministic structural heading while
                # preserving original_heading=None.
                # ------------------------------------------------------

                if not heading or not str(
                    heading
                ).strip():

                    heading = self._fallback_heading(
                        json_path=json_path,
                        document_title=title,
                    )

                classification = (
                    classify_with_context(
                        heading=heading,
                        text=text,
                        source_name=(
                            json_path.name
                            + "\n"
                            + original_category
                        ),
                        document_title=title,
                        document_url=url,
                    )
                )

                # ------------------------------------------------------
                # STUDENT RAG ELIGIBILITY
                #
                # This does NOT delete or modify source knowledge.
                # It only determines whether the unit belongs in the
                # final student-support RAG candidate.
                # ------------------------------------------------------

                rag_classification = (
                    self.rag_triage.classify(
                        {
                            "heading": heading,
                            "text": text,
                            "section_path": section_path,
                            "document_title": title,
                            "source_document_name": (
                                json_path.name
                            ),
                            "source_url": url,
                            "original_category": (
                                original_category
                            ),
                            "topic": (
                                classification["domain"]
                            ),
                            "subtopic": (
                                classification["category"]
                            ),
                        }
                    )
                )

                unit = {
                    # --------------------------------------------------
                    # IDENTITY
                    # --------------------------------------------------

                    "unit_id": (
                        self._make_unit_id(
                            json_path,
                            page_index,
                            section_index,
                        )
                    ),

                    "source_document": str(
                        json_path
                    ),

                    "source_document_name": (
                        json_path.name
                    ),

                    "source_url": url,

                    "document_title": title,

                    "domain": source_domain,

                    "original_category": (
                        original_category
                    ),

                    "document_type": document_type,

                    # --------------------------------------------------
                    # ORIGINAL STRUCTURE
                    # --------------------------------------------------

                    "page_index": page_index,

                    "page_number": page_number,

                    "section_index": section_index,

                    "heading": heading,

                    "original_heading": (
                        original_heading
                    ),

                    "level": level,

                    "section_path": (
                        section_path
                    ),

                    "content_type": (
                        content_type
                    ),

                    "text": text,

                    "decision": decision,

                    # --------------------------------------------------
                    # 8.4 CONTRACT
                    # --------------------------------------------------

                    "topic": (
                        classification["domain"]
                    ),

                    "subtopic": (
                        classification["category"]
                    ),

                    # --------------------------------------------------
                    # EXTENDED TAXONOMY
                    # --------------------------------------------------

                    "taxonomy_domain": (
                        classification[
                            "domain"
                        ]
                    ),

                    "taxonomy_category": (
                        classification[
                            "category"
                        ]
                    ),

                    "taxonomy_subcategory": (
                        classification[
                            "subcategory"
                        ]
                    ),

                    "classification_confidence": (
                        classification[
                            "confidence"
                        ]
                    ),

                    "classification_score": (
                        classification[
                            "score"
                        ]
                    ),

                    # --------------------------------------------------
                    # STUDENT RAG ELIGIBILITY
                    # --------------------------------------------------

                    "rag": (
                        rag_classification[
                            "rag"
                        ]
                    ),
                }

                units.append(unit)

        review_count = sum(
            1
            for unit in units
            if (
                unit["decision"] == "REVIEW"
                or unit[
                    "taxonomy_domain"
                ] == "review"
            )
        )

        return {
            "phase": "8.3",

            "source_document": str(
                json_path
            ),

            "source_document_name": (
                json_path.name
            ),

            "source_url": url,

            "document_title": title,

            "domain": source_domain,

            "original_category": (
                original_category
            ),

            "document_type": document_type,

            "total_sections_seen": (
                sections_seen
            ),

            "noise_sections": (
                noise_sections
            ),

            "empty_sections": (
                empty_sections
            ),

            "knowledge_units": len(
                units
            ),

            "review_units": review_count,

            "units": units,
        }

    # ==================================================================
    # FULL DOMAIN
    # ==================================================================

    def organize_domain(
        self,
        domain: str,
    ) -> dict:

        domain = (
            domain or ""
        ).strip()

        if not domain:
            raise ValueError(
                "Domain cannot be empty."
            )

        input_domain = (
            self.input_root / domain
        )

        if not input_domain.exists():
            raise FileNotFoundError(
                f"Structured domain does not exist: "
                f"{input_domain}"
            )

        files = sorted(
            input_domain.rglob("*.json")
        )

        if not files:
            raise ValueError(
                f"No structured JSON files found in: "
                f"{input_domain}"
            )

        all_units = []
        document_reports = []
        failures = []

        processed_documents = 0
        failed_documents = 0

        total_sections_seen = 0
        total_noise_sections = 0
        total_empty_sections = 0

        for index, json_path in enumerate(
            files,
            start=1,
        ):

            try:

                result = (
                    self.organize_document(
                        json_path
                    )
                )

                processed_documents += 1

                all_units.extend(
                    result["units"]
                )

                total_sections_seen += (
                    result[
                        "total_sections_seen"
                    ]
                )

                total_noise_sections += (
                    result[
                        "noise_sections"
                    ]
                )

                total_empty_sections += (
                    result[
                        "empty_sections"
                    ]
                )

                document_reports.append(
                    {
                        "source_document": str(
                            json_path
                        ),
                        "title": result[
                            "document_title"
                        ],
                        "sections_seen": result[
                            "total_sections_seen"
                        ],
                        "noise_sections": result[
                            "noise_sections"
                        ],
                        "empty_sections": result[
                            "empty_sections"
                        ],
                        "knowledge_units": result[
                            "knowledge_units"
                        ],
                        "review_units": result[
                            "review_units"
                        ],
                    }
                )

                print(
                    f"[8.3 {index}/{len(files)}] "
                    f"OK "
                    f"{json_path.name} "
                    f"units="
                    f"{result['knowledge_units']}"
                )

            except Exception as error:

                failed_documents += 1

                failures.append(
                    {
                        "file": str(
                            json_path
                        ),
                        "error": (
                            f"{type(error).__name__}: "
                            f"{error}"
                        ),
                    }
                )

                print(
                    f"[8.3 {index}/{len(files)}] "
                    f"FAILED "
                    f"{json_path.name}"
                )

                print(
                    f"    {type(error).__name__}: "
                    f"{error}"
                )

        # --------------------------------------------------------------
        # AGGREGATED COUNTS
        # --------------------------------------------------------------

        category_counts = Counter()
        domain_counts = Counter()
        confidence_counts = Counter()
        decision_counts = Counter()

        rag_tier_counts = Counter()

        rag_status_counts = Counter()

        for unit in all_units:

            category_key = "/".join(
                [
                    unit[
                        "taxonomy_domain"
                    ],
                    unit[
                        "taxonomy_category"
                    ],
                    unit[
                        "taxonomy_subcategory"
                    ],
                ]
            )

            category_counts[
                category_key
            ] += 1

            domain_counts[
                unit[
                    "taxonomy_domain"
                ]
            ] += 1

            confidence_counts[
                unit[
                    "classification_confidence"
                ]
            ] += 1

            decision_counts[
                unit[
                    "decision"
                ]
            ] += 1

            rag = unit.get(
                "rag",
                {},
            )

            rag_tier = rag.get(
                "tier"
            )

            rag_status = rag.get(
                "status"
            )

            if rag_tier:
                rag_tier_counts[
                    rag_tier
                ] += 1

            if rag_status:
                rag_status_counts[
                    rag_status
                ] += 1

        review_units = sum(
            1
            for unit in all_units
            if (
                unit[
                    "taxonomy_domain"
                ] == "review"
            )
        )

        # --------------------------------------------------------------
        # OUTPUT
        # --------------------------------------------------------------

        domain_output = (
            self.output_root / domain
        )

        domain_output.mkdir(
            parents=True,
            exist_ok=True,
        )

        # --------------------------------------------------------------
        # KNOWLEDGE UNITS MANIFEST
        # --------------------------------------------------------------

        manifest = {
            "phase": "8.3",

            "domain": domain,

            "input_root": str(
                input_domain
            ),

            "input_documents": len(
                files
            ),

            "processed_documents": (
                processed_documents
            ),

            "failed_documents": (
                failed_documents
            ),

            "total_sections_seen": (
                total_sections_seen
            ),

            "total_noise_sections": (
                total_noise_sections
            ),

            "total_empty_sections": (
                total_empty_sections
            ),

            "total_knowledge_units": (
                len(all_units)
            ),

            "review_units": review_units,

            "domain_counts": dict(
                domain_counts
            ),

            "category_counts": dict(
                category_counts
            ),

            "confidence_counts": dict(
                confidence_counts
            ),

            "decision_counts": dict(
                decision_counts
            ),

            "rag_tier_counts": dict(
                rag_tier_counts
            ),

            "rag_status_counts": dict(
                rag_status_counts
            ),

            "document_reports": (
                document_reports
            ),

            "failures": failures,

            "units": all_units,
        }

        manifest_path = (
            domain_output
            / "knowledge_units.json"
        )

        manifest_path.write_text(
            json.dumps(
                manifest,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        # --------------------------------------------------------------
        # TAXONOMY AUDIT
        # --------------------------------------------------------------

        low_confidence_units = [
            {
                "unit_id": unit[
                    "unit_id"
                ],

                "heading": unit[
                    "heading"
                ],

                "original_heading": unit.get(
                    "original_heading"
                ),

                "source_document": unit[
                    "source_document"
                ],

                "document_title": unit[
                    "document_title"
                ],

                "taxonomy_domain": unit[
                    "taxonomy_domain"
                ],

                "taxonomy_category": unit[
                    "taxonomy_category"
                ],

                "taxonomy_subcategory": unit[
                    "taxonomy_subcategory"
                ],
            }
            for unit in all_units
            if (
                unit[
                    "classification_confidence"
                ] == "low"
            )
        ]

        audit = {
            "phase": "8.3",

            "domain": domain,

            "input_documents": len(
                files
            ),

            "processed_documents": (
                processed_documents
            ),

            "failed_documents": (
                failed_documents
            ),

            "total_sections_seen": (
                total_sections_seen
            ),

            "total_noise_sections": (
                total_noise_sections
            ),

            "total_empty_sections": (
                total_empty_sections
            ),

            "total_knowledge_units": (
                len(all_units)
            ),

            "review_units": (
                review_units
            ),

            "domain_counts": dict(
                domain_counts
            ),

            "category_counts": dict(
                category_counts
            ),

            "confidence_counts": dict(
                confidence_counts
            ),

            "decision_counts": dict(
                decision_counts
            ),

            "rag_tier_counts": dict(
                rag_tier_counts
            ),

            "rag_status_counts": dict(
                rag_status_counts
            ),

            "low_confidence_units": (
                low_confidence_units
            ),

            "failures": failures,
        }

        audit_path = (
            domain_output
            / "taxonomy_audit.json"
        )

        audit_path.write_text(
            json.dumps(
                audit,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        return {
            "manifest": manifest,

            "manifest_path": str(
                manifest_path
            ),

            "audit_path": str(
                audit_path
            ),
        }

    # ==================================================================
    # VALIDATION
    # ==================================================================

    def _validate_document(
        self,
        data: dict,
        path: Path,
    ) -> None:

        if not isinstance(
            data,
            dict,
        ):
            raise ValueError(
                f"Structured document must be "
                f"a JSON object: {path}"
            )

        document = data.get(
            "document"
        )

        if not isinstance(
            document,
            dict,
        ):
            raise ValueError(
                f"Missing document metadata: {path}"
            )

        pages = data.get(
            "pages"
        )

        if not isinstance(
            pages,
            list,
        ):
            raise ValueError(
                f"'pages' must be a list: {path}"
            )

    # ==================================================================
    # SECTION DECISION
    # ==================================================================

    def _decide_section(
        self,
        *,
        heading: str | None,
        text: str,
        content_type: str,
    ) -> str:

        heading_n = self._normalize(
            heading or ""
        )

        text_n = self._normalize(
            text
        )

        content_type_n = self._normalize(
            content_type
        )

        # --------------------------------------------------------------
        # EMPTY / UNEXTRACTABLE SHELL
        # --------------------------------------------------------------
        #
        # If there is no heading AND there is no useful text, this is
        # not a knowledge unit.
        #
        # Example:
        #     heading = None
        #     text = "[No extractable text]"
        #
        # Do NOT invent a heading for this case.
        # --------------------------------------------------------------

        if (
            not (heading or "").strip()
            and text_n in {
                "",
                "no extractable text",
            }
        ):
            return "NOISE"

        # --------------------------------------------------------------
        # STRUCTURED NAVIGATION
        # --------------------------------------------------------------

        if content_type_n in {
            "navigation",
            "accessibility",
        }:
            return "NOISE"

        # --------------------------------------------------------------
        # KNOWN UI HEADINGS
        # --------------------------------------------------------------

        normalized_noise_headings = {
            self._normalize(value)
            for value
            in self.NOISE_HEADINGS
        }

        if (
            heading_n
            in normalized_noise_headings
        ):
            return "NOISE"

        # --------------------------------------------------------------
        # KNOWN UI CONTENT
        # --------------------------------------------------------------

        normalized_exact_content = {
            self._normalize(value)
            for value
            in self.NOISE_EXACT_CONTENT
        }

        if (
            text_n
            in normalized_exact_content
        ):
            return "NOISE"

        # --------------------------------------------------------------
        # ACCESSIBILITY / FEEDBACK UI
        # --------------------------------------------------------------

        for phrase in self.NOISE_PHRASES:

            phrase_n = self._normalize(
                phrase
            )

            if (
                phrase_n
                in text_n
            ):
                if (
                    heading_n
                    in {
                        "rate this translation",
                        "accessibility",
                        "accessibility options",
                    }
                ):
                    return "NOISE"

        return "KEEP"

    # ==================================================================
    # CONTENT -> TEXT
    # ==================================================================

    def _content_to_text(
        self,
        content: list,
    ) -> str:

        parts = []

        for item in content:

            if item is None:
                continue

            if isinstance(
                item,
                str,
            ):
                value = item.strip()

            else:
                value = str(
                    item
                ).strip()

            if value:
                parts.append(
                    value
                )

        return "\n".join(
            parts
        ).strip()

    # ==================================================================
    # HIERARCHY
    # ==================================================================

    def _build_section_path(
        self,
        *,
        hierarchy_stack: list,
        heading: str | None,
        level,
    ) -> list[str]:

        # No explicit heading:
        # preserve current parent hierarchy.
        if not heading:
            return [
                entry[1]
                for entry in hierarchy_stack
            ]

        try:
            safe_level = int(
                level
            )
        except (
            TypeError,
            ValueError,
        ):
            safe_level = 0

        heading_clean = (
            str(
                heading
            ).strip()
        )

        if not heading_clean:
            return [
                entry[1]
                for entry in hierarchy_stack
            ]

        # Remove siblings and deeper headings.
        while (
            hierarchy_stack
            and hierarchy_stack[-1][0]
            >= safe_level
        ):
            hierarchy_stack.pop()

        hierarchy_stack.append(
            (
                safe_level,
                heading_clean,
            )
        )

        return [
            entry[1]
            for entry in hierarchy_stack
        ]

    # ==================================================================
    # FALLBACK HEADING
    # ==================================================================

    def _fallback_heading(
        self,
        *,
        json_path: Path,
        document_title: str,
    ) -> str:
        """
        Give meaningful heading-less knowledge a deterministic
        structural heading.

        Priority:
            1. document title
            2. filename
            3. generic fallback

        This does NOT invent factual content.
        """

        title = (
            document_title or ""
        ).strip()

        if title:
            return title

        stem = json_path.stem

        # Remove crawler hash suffixes such as:
        #
        #   __638772906605230764
        #   __abcdef12
        #
        stem = re.sub(
            r"__+[a-f0-9]{8,}$",
            "",
            stem,
            flags=re.IGNORECASE,
        )

        # Convert crawler filename formatting to readable text.
        stem = stem.replace(
            "-",
            " ",
        )

        stem = stem.replace(
            "_",
            " ",
        )

        stem = re.sub(
            r"\s+",
            " ",
            stem,
        ).strip()

        if stem:
            return stem.title()

        return "Document Content"

    # ==================================================================
    # UNIT ID
    # ==================================================================

    def _make_unit_id(
        self,
        path: Path,
        page_index: int,
        section_index: int,
    ) -> str:

        raw = (
            f"{path.resolve()}::"
            f"{page_index}::"
            f"{section_index}"
        )

        return hashlib.sha1(
            raw.encode(
                "utf-8"
            )
        ).hexdigest()[:16]

    # ==================================================================
    # NORMALIZATION
    # ==================================================================

    def _normalize(
        self,
        value: str,
    ) -> str:

        value = (
            value
            or ""
        ).lower()

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


if __name__ == "__main__":

    print(
        "StructuredKnowledgeOrganizer"
    )

    print(
        "Phase 8.3 processor"
    )
