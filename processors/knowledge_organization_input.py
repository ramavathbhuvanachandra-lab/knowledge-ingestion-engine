"""
Phase 8.3 — Structured Knowledge Input Adapter.

Purpose
-------
Convert structured-knowledge JSON records into normalized Knowledge Units.

Input schema
------------
{
    "document": {
        "title": "...",
        "url": "...",
        "domain": "...",
        "category": "...",
        "document_type": "...",
        "source_file": "..."
    },
    "pages": [
        {
            "page_number": ...,
            "sections": [
                {
                    "heading": "...",
                    "level": 2,
                    "content": ["...", "..."],
                    "content_type": "knowledge"
                }
            ]
        }
    ]
}

Responsibilities
----------------
- Read structured JSON files.
- Preserve original wording.
- Preserve source metadata and provenance.
- Extract knowledge-bearing sections.
- Ignore navigation sections and empty sections by default.
- Produce stable unit IDs.
- Never classify, assign taxonomy, create folders, or delete source JSON.

Important invariant
-------------------
This adapter transforms representation only.

It must not decide:
    "this belongs in Research"
or
    "this belongs in Electrical Engineering"

That belongs to the taxonomy/organization stages.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable
import hashlib
import json
import re


# ============================================================================
# DATA MODEL
# ============================================================================


@dataclass
class KnowledgeUnit:
    """Normalized, provenance-preserving unit extracted from one JSON record."""

    unit_id: str

    source_file: str
    source_domain: str

    source_url: str
    source_title: str
    source_category: str
    source_document_type: str

    page_number: int | None

    section_index: int
    heading: str
    level: int

    content: str
    content_type: str

    source_lineage: dict[str, Any] = field(
        default_factory=dict
    )


# ============================================================================
# ADAPTER
# ============================================================================


class StructuredKnowledgeInputAdapter:
    """
    Convert structured JSON records into normalized knowledge units.

    The adapter is intentionally conservative about what is considered
    knowledge-bearing. It uses the existing structured `content_type`
    signal first, then falls back to conservative structural rules.
    """

    PHASE = "8.3_input_adapter"
    VERSION = "1.0"

    # Existing structured records use "knowledge" vs "navigation".
    DEFAULT_KEEP_CONTENT_TYPES = {
        "knowledge",
    }

    DEFAULT_SKIP_CONTENT_TYPES = {
        "navigation",
    }

    # Obvious website chrome. These are not taxonomy decisions.
    NOISE_HEADINGS = {
        "search here",
        "accessibility options",
        "accessibility",
        "menu",
        "navigation",
        "quick access",
        "quick links",
        "important links",
        "useful links",
    }

    # Scraped UI markers that should never become knowledge units by
    # themselves.
    NOISE_EXACT_CONTENT = {
        "accessibility options",
        "created by",
        "arrow downward",
    }

    def __init__(
        self,
        *,
        keep_content_types: set[str] | None = None,
        skip_content_types: set[str] | None = None,
        keep_empty_sections: bool = False,
    ) -> None:

        self.keep_content_types = {
            value.strip().lower()
            for value in (
                keep_content_types
                or self.DEFAULT_KEEP_CONTENT_TYPES
            )
        }

        self.skip_content_types = {
            value.strip().lower()
            for value in (
                skip_content_types
                or self.DEFAULT_SKIP_CONTENT_TYPES
            )
        }

        self.keep_empty_sections = (
            keep_empty_sections
        )

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def extract_file(
        self,
        json_path: str | Path,
    ) -> list[KnowledgeUnit]:
        """Extract units from one structured JSON record."""

        path = Path(
            json_path
        )

        if not path.exists():
            raise FileNotFoundError(
                f"Structured JSON does not exist: {path}"
            )

        if path.suffix.lower() != ".json":
            raise ValueError(
                f"Expected .json input, got: {path}"
            )

        try:
            data = json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Invalid JSON: {path}: {exc}"
            ) from exc

        return self.extract_record(
            data,
            source_file=path,
        )

    def extract_record(
        self,
        data: dict[str, Any],
        *,
        source_file: str | Path,
    ) -> list[KnowledgeUnit]:
        """
        Extract units from an already-loaded structured record.

        The original `content` wording is preserved; only adjacent content
        items are joined with newlines.
        """

        self._validate_record(
            data
        )

        source_path = Path(
            source_file
        )

        document = data.get(
            "document",
            {},
        )

        pages = data.get(
            "pages",
            [],
        )

        source_title = str(
            document.get(
                "title",
                "",
            )
        ).strip()

        source_url = str(
            document.get(
                "url",
                "",
            )
        ).strip()

        source_domain = str(
            document.get(
                "domain",
                "",
            )
        ).strip()

        source_category = str(
            document.get(
                "category",
                "",
            )
        ).strip()

        source_document_type = str(
            document.get(
                "document_type",
                "",
            )
        ).strip()

        units: list[
            KnowledgeUnit
        ] = []

        for page_index, page in enumerate(
            pages
        ):

            if not isinstance(
                page,
                dict,
            ):
                continue

            page_number = self._page_number(
                page.get(
                    "page_number"
                )
            )

            sections = page.get(
                "sections",
                [],
            )

            if not isinstance(
                sections,
                list,
            ):
                continue

            for section_index, section in enumerate(
                sections
            ):

                if not isinstance(
                    section,
                    dict,
                ):
                    continue

                normalized = (
                    self._normalize_section(
                        section
                    )
                )

                if normalized is None:
                    continue

                heading = normalized[
                    "heading"
                ]

                content = normalized[
                    "content"
                ]

                content_type = normalized[
                    "content_type"
                ]

                if not self._should_keep_section(
                    heading=heading,
                    content=content,
                    content_type=content_type,
                ):
                    continue

                unit_id = self._make_unit_id(
                    source_path=source_path,
                    page_index=page_index,
                    section_index=section_index,
                    heading=heading,
                    content=content,
                )

                units.append(
                    KnowledgeUnit(
                        unit_id=unit_id,
                        source_file=str(
                            source_path
                        ),
                        source_domain=source_domain,
                        source_url=source_url,
                        source_title=source_title,
                        source_category=source_category,
                        source_document_type=source_document_type,
                        page_number=page_number,
                        section_index=section_index,
                        heading=heading,
                        level=normalized[
                            "level"
                        ],
                        content=content,
                        content_type=content_type,
                        source_lineage={
                            "phase": self.PHASE,
                            "adapter_version": self.VERSION,
                            "page_index": page_index,
                            "section_index": section_index,
                            "source_document_title": source_title,
                            "source_url": source_url,
                        },
                    )
                )

        return units

    def extract_directory(
        self,
        input_root: str | Path,
        *,
        domain: str | None = None,
    ) -> list[KnowledgeUnit]:
        """
        Extract all units from one college/domain directory.

        This is deliberately domain-scoped. It will not combine IITJ and
        GWPGC unless the caller explicitly asks for a common directory.
        """

        root = Path(
            input_root
        )

        if not root.exists():
            raise FileNotFoundError(
                f"Structured knowledge root does not exist: {root}"
            )

        if not root.is_dir():
            raise NotADirectoryError(
                f"Structured knowledge root is not a directory: {root}"
            )

        if domain is not None:
            domain_root = (
                root
                / domain
            )

            if domain_root.is_dir():
                root = domain_root
            elif root.name != domain:
                raise FileNotFoundError(
                    f"Domain does not exist under root: {domain}"
                )

        files = sorted(
            root.rglob("*.json")
        )

        all_units: list[
            KnowledgeUnit
        ] = []

        for path in files:
            all_units.extend(
                self.extract_file(
                    path
                )
            )

        return all_units

    def summarize_units(
        self,
        units: Iterable[KnowledgeUnit],
    ) -> dict[str, Any]:
        """Return deterministic extraction statistics."""

        units = list(
            units
        )

        content_type_counts: dict[
            str,
            int,
        ] = {}

        domain_counts: dict[
            str,
            int,
        ] = {}

        document_counts: dict[
            str,
            int,
        ] = {}

        for unit in units:

            content_type_counts[
                unit.content_type
            ] = (
                content_type_counts.get(
                    unit.content_type,
                    0,
                )
                + 1
            )

            domain_counts[
                unit.source_domain
            ] = (
                domain_counts.get(
                    unit.source_domain,
                    0,
                )
                + 1
            )

            document_counts[
                unit.source_file
            ] = (
                document_counts.get(
                    unit.source_file,
                    0,
                )
                + 1
            )

        return {
            "phase": self.PHASE,
            "version": self.VERSION,
            "unit_count": len(
                units
            ),
            "source_document_count": len(
                document_counts
            ),
            "content_type_counts": dict(
                sorted(
                    content_type_counts.items()
                )
            ),
            "domain_counts": dict(
                sorted(
                    domain_counts.items()
                )
            ),
        }

    # ========================================================================
    # SECTION NORMALIZATION
    # ========================================================================

    def _normalize_section(
        self,
        section: dict[str, Any],
    ) -> dict[str, Any] | None:
        heading = self._clean_heading(
            section.get(
                "heading"
            )
        )

        level = self._safe_level(
            section.get(
                "level"
            )
        )

        content_type = (
            str(
                section.get(
                    "content_type",
                    "",
                )
            )
            .strip()
            .lower()
        )

        raw_content = section.get(
            "content",
            [],
        )

        content_items = self._normalize_content_items(
            raw_content
        )

        content = self._join_content(
            content_items
        )

        if (
            not heading
            and not content
        ):
            return None

        # A missing content type is treated as unknown rather than silently
        # being treated as knowledge.
        if not content_type:
            content_type = "unknown"

        return {
            "heading": heading,
            "level": level,
            "content": content,
            "content_type": content_type,
        }

    @staticmethod
    def _normalize_content_items(
        raw_content: Any,
    ) -> list[str]:

        if raw_content is None:
            return []

        if isinstance(
            raw_content,
            str,
        ):
            values = [
                raw_content
            ]
        elif isinstance(
            raw_content,
            list,
        ):
            values = [
                str(
                    item
                )
                for item in raw_content
                if item is not None
            ]
        else:
            values = [
                str(
                    raw_content
                )
            ]

        cleaned: list[str] = []

        for value in values:

            value = value.strip()

            if not value:
                continue

            cleaned.append(
                value
            )

        return cleaned

    @staticmethod
    def _join_content(
        content_items: list[str],
    ) -> str:
        """
        Preserve the original item wording while putting each source
        content item on its own line.
        """

        return "\n".join(
            content_items
        ).strip()

    def _should_keep_section(
        self,
        *,
        heading: str,
        content: str,
        content_type: str,
    ) -> bool:

        normalized_heading = self._normalize(
            heading
        )

        normalized_content = self._normalize(
            content
        )

        if (
            not content
            and not self.keep_empty_sections
        ):
            return False

        if normalized_heading in (
            self.NOISE_HEADINGS
        ):
            return False

        if normalized_content in (
            self.NOISE_EXACT_CONTENT
        ):
            return False

        if content_type in (
            self.skip_content_types
        ):
            return False

        # Existing structured records explicitly label knowledge sections.
        if (
            content_type
            in self.keep_content_types
        ):
            return True

        # Unknown content types are not automatically discarded when they
        # contain meaningful content. This protects against future schema
        # additions and prevents information loss.
        if (
            content_type == "unknown"
            and content
        ):
            return True

        return False

    # ========================================================================
    # VALIDATION
    # ========================================================================

    @staticmethod
    def _validate_record(
        data: dict[str, Any],
    ) -> None:

        if not isinstance(
            data,
            dict,
        ):
            raise TypeError(
                "Structured record must be a dictionary."
            )

        document = data.get(
            "document"
        )

        if not isinstance(
            document,
            dict,
        ):
            raise ValueError(
                "Structured record must contain document as a dictionary."
            )

        pages = data.get(
            "pages"
        )

        if not isinstance(
            pages,
            list,
        ):
            raise ValueError(
                "Structured record must contain pages as a list."
            )

    # ========================================================================
    # HELPERS
    # ========================================================================

    @staticmethod
    def _page_number(
        value: Any,
    ) -> int | None:

        if value is None:
            return None

        try:
            return int(
                value
            )
        except (
            TypeError,
            ValueError,
        ):
            return None

    @staticmethod
    def _safe_level(
        value: Any,
    ) -> int:

        try:
            level = int(
                value
            )
        except (
            TypeError,
            ValueError,
        ):
            return 0

        return max(
            0,
            min(
                level,
                6,
            )
        )

    @staticmethod
    def _clean_heading(
        value: Any,
    ) -> str:

        if value is None:
            return ""

        value = str(
            value
        ).strip()

        # Keep the original wording, but remove surrounding Markdown
        # heading markers if an upstream processor inserted them.
        value = re.sub(
            r"^#{1,6}\s+",
            "",
            value,
        ).strip()

        return value

    @staticmethod
    def _normalize(
        value: str,
    ) -> str:

        value = (
            value or ""
        ).strip().lower()

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

    @staticmethod
    def _make_unit_id(
        *,
        source_path: Path,
        page_index: int,
        section_index: int,
        heading: str,
        content: str,
    ) -> str:

        raw = "::".join(
            [
                str(
                    source_path.resolve()
                ),
                str(
                    page_index
                ),
                str(
                    section_index
                ),
                heading,
                content,
            ]
        )

        return hashlib.sha1(
            raw.encode(
                "utf-8"
            )
        ).hexdigest()[:16]


# ============================================================================
# JSON SERIALIZATION
# ============================================================================


def units_to_dicts(
    units: Iterable[KnowledgeUnit],
) -> list[dict[str, Any]]:
    """Convert units to JSON-serializable dictionaries."""

    return [
        asdict(
            unit
        )
        for unit in units
    ]


def save_units(
    units: Iterable[KnowledgeUnit],
    output_path: str | Path,
) -> None:
    """Persist normalized knowledge units."""

    output = Path(
        output_path
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        json.dumps(
            units_to_dicts(
                units
            ),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


# ============================================================================
# CLI
# ============================================================================


def main() -> None:

    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Extract normalized knowledge units from structured "
            "knowledge JSON."
        )
    )

    parser.add_argument(
        "--input-root",
        required=True,
        help=(
            "Structured knowledge root, or one domain directory."
        ),
    )

    parser.add_argument(
        "--domain",
        required=False,
        help=(
            "Optional domain under --input-root, e.g. "
            "www.iitj.ac.in"
        ),
    )

    parser.add_argument(
        "--output",
        required=False,
        help="Optional output JSON file.",
    )

    args = parser.parse_args()

    adapter = (
        StructuredKnowledgeInputAdapter()
    )

    units = adapter.extract_directory(
        args.input_root,
        domain=args.domain,
    )

    summary = adapter.summarize_units(
        units
    )

    print(
        json.dumps(
            summary,
            indent=2,
            ensure_ascii=False,
        )
    )

    if args.output:
        save_units(
            units,
            args.output,
        )

        print(
            f"\nUnits written to: {args.output}"
        )


if __name__ == "__main__":
    main()