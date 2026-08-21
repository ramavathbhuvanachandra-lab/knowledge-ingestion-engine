"""
Phase 8.3 — Deterministic Dynamic Knowledge Organization.

Purpose
-------
Turn canonical/cleaned Markdown knowledge into organized knowledge using
the generated dynamic taxonomy plan.

Flow
----
Canonical Markdown
      ↓
Parse sections
      ↓
Exclude explicit NOISE only
      ↓
Score each KEEP/REVIEW unit against generated taxonomy
      ↓
Strong match → taxonomy node
No strong match → legitimate buffer
      ↓
Write Markdown groups
      ↓
Write organization manifest

Important invariants
--------------------
- No LLM.
- No fixed IITJ/engineering taxonomy.
- No boilerplate entity subfolders.
- No deletion merely because classification is uncertain.
- Explicit NOISE may be excluded.
- KEEP and REVIEW are preserved.
- Original section text and source-line provenance are preserved.
- Buffers are created only when legitimate unmatched units exist.
- A taxonomy plan is authoritative for folder creation.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import hashlib
import json
import re
from typing import Any

from processors.knowledge_folder_builder import (
    KnowledgeFolderBuilder,
)


class KnowledgeOrganizer:
    """Organize canonical Markdown against a generated taxonomy plan."""

    PHASE = "8.3"

    MIN_NORMAL_MATCH_SCORE = 6.0
    MIN_MATCH_MARGIN = 1.0

    BUFFER_NAMES = {
        "policy": "Policies & Regulations",
        "student": "Student & Campus Information",
        "activity": "Activities & Outreach",
        "general": "General Institutional Information",
        "other": "Other Relevant Institutional Information",
    }

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

    NOISE_EXACT_CONTENT = {
        "accessibility options",
        "created by",
        "arrow downward",
    }

    def __init__(
        self,
        output_path: str | Path = "storage/organized_knowledge",
        organized_root: str | Path | None = None,
        taxonomy_plan_path: str | Path | None = None,
        taxonomy_plan: dict[str, Any] | None = None,
    ) -> None:

        self.output_path = Path(
            organized_root
            if organized_root is not None
            else output_path
        )

        self.taxonomy_plan_path = (
            Path(taxonomy_plan_path)
            if taxonomy_plan_path is not None
            else None
        )

        self.taxonomy_plan = taxonomy_plan

        self.folder_builder = KnowledgeFolderBuilder(
            output_root=self.output_path
        )

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def organize(
        self,
        markdown_path: str | Path,
        *,
        taxonomy_plan_path: str | Path | None = None,
        taxonomy_plan: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        markdown_path = Path(
            markdown_path
        )

        if not markdown_path.exists():
            raise FileNotFoundError(
                f"Knowledge Markdown does not exist: {markdown_path}"
            )

        plan = self._resolve_taxonomy_plan(
            taxonomy_plan_path=taxonomy_plan_path,
            taxonomy_plan=taxonomy_plan,
        )

        content = markdown_path.read_text(
            encoding="utf-8"
        )

        domain = self._extract_domain(
            markdown_path,
            content,
        )

        sections = self._parse_sections(
            content
        )

        # Materialize only taxonomy folders represented in the plan.
        nodes = plan.get(
            "nodes",
            [],
        )

        # Only materialize taxonomy nodes that actually receive knowledge.
        # Ancestors are added automatically by KnowledgeFolderBuilder.
        active_node_ids: set[str] = set()

        folder_manifest = None

        units: list[dict[str, Any]] = []

        noise_count = 0
        matched_count = 0
        review_count = 0
        buffer_count = 0

        for index, section in enumerate(
            sections
        ):

            if section[
                "decision"
            ] == "NOISE":
                noise_count += 1
                continue

            classification = self._classify_unit(
                section=section,
                nodes=nodes,
            )

            unit = {
                "unit_id": self._make_unit_id(
                    markdown_path,
                    index,
                ),

                "source_document": str(
                    markdown_path
                ),

                "source_document_name": markdown_path.name,

                "domain": domain,

                "heading": section[
                    "heading"
                ],

                "level": section[
                    "level"
                ],

                "text": section[
                    "text"
                ],

                "start_line": section[
                    "start_line"
                ],

                "end_line": section[
                    "end_line"
                ],

                "decision": section[
                    "decision"
                ],

                "taxonomy_node_id": classification[
                    "node_id"
                ],

                "taxonomy_path": classification[
                    "taxonomy_path"
                ],

                "taxonomy_domain": classification[
                    "taxonomy_domain"
                ],

                "taxonomy_category": classification[
                    "taxonomy_category"
                ],

                "taxonomy_subcategory": classification[
                    "taxonomy_subcategory"
                ],

                "classification_confidence": classification[
                    "confidence"
                ],

                "classification_score": classification[
                    "score"
                ],

                "classification_reason": classification[
                    "reason"
                ],

                "buffer_name": classification[
                    "buffer_name"
                ],
            }

            units.append(
                unit
            )

            if classification[
                "buffer_name"
            ]:
                buffer_count += 1
            else:
                matched_count += 1

            if (
                unit["decision"]
                == "REVIEW"
            ):
                review_count += 1

            if classification[
                "node_id"
            ] is not None:
                active_node_ids.add(
                    str(
                        classification[
                            "node_id"
                        ]
                    )
                )

        folder_manifest = self.folder_builder.build(
            taxonomy_plan=plan,
            domain=domain,
            active_node_ids=active_node_ids,
        )

        written_files = self._write_units(
            domain=domain,
            units=units,
        )

        category_counts = defaultdict(
            int
        )

        for unit in units:
            path = unit[
                "taxonomy_path"
            ]

            if path:
                category_counts[
                    path
                ] += 1
            else:
                category_counts[
                    f"BUFFER/{unit['buffer_name']}"
                ] += 1

        manifest = {
            "phase": self.PHASE,
            "source_document": str(
                markdown_path
            ),
            "source_document_name": markdown_path.name,
            "domain": domain,

            "taxonomy_plan_version": plan.get(
                "version"
            ),

            "taxonomy_plan_source": (
                str(
                    self.taxonomy_plan_path
                )
                if self.taxonomy_plan_path
                else (
                    "argument"
                    if taxonomy_plan is not None
                    else None
                )
            ),

            "total_sections": len(
                sections
            ),

            "noise_sections": noise_count,
            "organized_sections": len(
                units
            ),

            "matched_sections": matched_count,
            "buffer_sections": buffer_count,
            "review_sections": review_count,

            "classification_coverage": (
                round(
                    matched_count
                    / max(
                        1,
                        len(units),
                    ),
                    4,
                )
            ),

            "buffer_rate": (
                round(
                    buffer_count
                    / max(
                        1,
                        len(units),
                    ),
                    4,
                )
            ),

            "category_counts": dict(
                category_counts
            ),

            "buffer_counts": {
                name: count
                for name, count in sorted(
                    category_counts.items()
                )
                if name.startswith(
                    "BUFFER/"
                )
            },

            "written_files": written_files,

            "folder_manifest": folder_manifest,

            "units": units,
        }

        domain_root = (
            self.output_path
            / self._safe_name(
                domain
            )
        )

        manifest_path = (
            domain_root
            / (
                f"{markdown_path.stem}"
                ".organization.json"
            )
        )

        manifest_path.write_text(
            json.dumps(
                manifest,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        manifest[
            "manifest_path"
        ] = str(
            manifest_path
        )

        return manifest

    # ========================================================================
    # TAXONOMY PLAN
    # ========================================================================

    def _resolve_taxonomy_plan(
        self,
        *,
        taxonomy_plan_path: str | Path | None,
        taxonomy_plan: dict[str, Any] | None,
    ) -> dict[str, Any]:

        if taxonomy_plan is not None:
            plan = taxonomy_plan

        elif taxonomy_plan_path is not None:
            path = Path(
                taxonomy_plan_path
            )

            if not path.exists():
                raise FileNotFoundError(
                    f"Taxonomy plan does not exist: {path}"
                )

            plan = json.loads(
                path.read_text(
                    encoding="utf-8"
                )
            )

        elif self.taxonomy_plan is not None:
            plan = self.taxonomy_plan

        elif self.taxonomy_plan_path is not None:
            if not self.taxonomy_plan_path.exists():
                raise FileNotFoundError(
                    "Taxonomy plan does not exist: "
                    f"{self.taxonomy_plan_path}"
                )

            plan = json.loads(
                self.taxonomy_plan_path.read_text(
                    encoding="utf-8"
                )
            )

        else:
            raise ValueError(
                "A dynamic taxonomy plan is required for Phase 8.3."
            )

        if not isinstance(
            plan,
            dict,
        ):
            raise ValueError(
                "Taxonomy plan must be a dictionary."
            )

        nodes = plan.get(
            "nodes"
        )

        if not isinstance(
            nodes,
            list,
        ):
            raise ValueError(
                "Taxonomy plan must contain a 'nodes' list."
            )

        node_ids = {
            str(
                node.get(
                    "node_id",
                    "",
                )
            )
            for node in nodes
            if isinstance(
                node,
                dict,
            )
        }

        for node in nodes:
            parent_id = node.get(
                "parent_id"
            )

            if (
                parent_id is not None
                and str(
                    parent_id
                ) not in node_ids
            ):
                raise ValueError(
                    "Taxonomy plan contains a node with a missing parent."
                )

        return plan

    # ========================================================================
    # UNIT CLASSIFICATION
    # ========================================================================

    def _classify_unit(
        self,
        *,
        section: dict[str, Any],
        nodes: list[dict[str, Any]],
    ) -> dict[str, Any]:

        heading = str(
            section.get(
                "heading",
                "",
            )
        )

        text = str(
            section.get(
                "text",
                "",
            )
        )

        searchable = self._normalize(
            f"{heading} {text}"
        )

        candidates: list[
            tuple[
                float,
                dict[str, Any],
                str,
            ]
        ] = []

        nodes_by_id = {
            str(
                node.get(
                    "node_id",
                    "",
                )
            ): node
            for node in nodes
            if isinstance(
                node,
                dict,
            )
        }

        for node in nodes:

            if not isinstance(
                node,
                dict,
            ):
                continue

            score, reason = self._score_node(
                node=node,
                nodes_by_id=nodes_by_id,
                searchable=searchable,
                heading=heading,
            )

            if score <= 0:
                continue

            candidates.append(
                (
                    score,
                    node,
                    reason,
                )
            )

        if candidates:

            candidates.sort(
                key=lambda item: (
                    -item[0],
                    int(
                        item[1].get(
                            "level",
                            99,
                        )
                        or 99
                    ),
                    str(
                        item[1].get(
                            "name",
                            "",
                        )
                    ),
                )
            )

            best_score, best_node, reason = candidates[
                0
            ]

            second_score = (
                candidates[1][0]
                if len(
                    candidates
                ) > 1
                else 0.0
            )

            margin = (
                best_score
                - second_score
            )

            # If the winner is weak or nearly tied with another candidate,
            # preserve the unit in a buffer instead of making a brittle guess.
            if (
                best_score
                >= self.MIN_NORMAL_MATCH_SCORE
                and (
                    margin
                    >= self.MIN_MATCH_MARGIN
                    or best_node.get(
                        "node_type"
                    )
                    == "entity"
                )
            ):
                path = self._node_path(
                    best_node,
                    nodes,
                )

                return {
                    "node_id": best_node[
                        "node_id"
                    ],
                    "taxonomy_path": path,
                    "taxonomy_domain": self._path_part(
                        path,
                        0,
                    ),
                    "taxonomy_category": self._path_part(
                        path,
                        1,
                    ),
                    "taxonomy_subcategory": self._path_part(
                        path,
                        2,
                    ),
                    "confidence": self._score_confidence(
                        best_score
                    ),
                    "score": round(
                        best_score,
                        3,
                    ),
                    "reason": reason,
                    "buffer_name": None,
                }

        buffer_name = self._select_buffer(
            heading=heading,
            text=text,
        )

        return {
            "node_id": None,
            "taxonomy_path": None,
            "taxonomy_domain": None,
            "taxonomy_category": None,
            "taxonomy_subcategory": None,
            "confidence": "buffer",
            "score": 0.0,
            "reason": (
                "No taxonomy node reached the minimum deterministic "
                "classification threshold."
            ),
            "buffer_name": buffer_name,
        }

    def _score_node(
        self,
        *,
        node: dict[str, Any],
        nodes_by_id: dict[str, dict[str, Any]],
        searchable: str,
        heading: str,
    ) -> tuple[float, str]:

        name = self._normalize(
            str(
                node.get(
                    "name",
                    "",
                )
            )
        )

        display_name = self._normalize(
            str(
                node.get(
                    "display_name",
                    "",
                )
            )
        )

        node_type = str(
            node.get(
                "node_type",
                "",
            )
        )

        if not name:
            return 0.0, ""

        score = 0.0
        reasons: list[str] = []

        # Exact heading match is extremely strong.
        if (
            self._normalize(
                heading
            )
            == name
            or self._normalize(
                heading
            )
            == display_name
        ):
            score += 12.0
            reasons.append(
                "exact_heading"
            )

        # Entity nodes require the entity itself to be present.
        if node_type == "entity":

            entity_names = [
                self._normalize(
                    str(
                        value
                    )
                )
                for value in node.get(
                    "entity_names",
                    [],
                )
                if str(
                    value
                ).strip()
            ]

            entity_match = any(
                entity
                and entity in searchable
                for entity in entity_names
            )

            if not entity_match:
                return 0.0, ""

            score += 10.0
            reasons.append(
                "entity_match"
            )

        # Entity subcategories require both the entity context and
        # the child concept signal. This prevents a generic "Research"
        # heading from being assigned to the wrong department.
        if node_type == "entity_subcategory":

            path_tokens = self._routing_signals(
                node
            )

            concept_match = any(
                signal in searchable
                for signal in path_tokens
            )

            if not concept_match:
                return 0.0, ""

            parent_id = node.get(
                "parent_id"
            )

            parent = nodes_by_id.get(
                str(parent_id)
            )

            if parent is None:
                return 0.0, ""

            parent_entity_names = [
                self._normalize(
                    str(value)
                )
                for value in parent.get(
                    "entity_names",
                    [],
                )
                if str(
                    value
                ).strip()
            ]

            # The entity node may itself have been produced from one
            # entity name; its entity_names list is the authoritative
            # context.
            if not any(
                entity_name
                and entity_name in searchable
                for entity_name in parent_entity_names
            ):
                # Walk one more level for unusual taxonomy shapes.
                ancestor = parent
                ancestor_seen: set[str] = set()

                found_context = False

                while ancestor is not None:

                    ancestor_id = str(
                        ancestor.get(
                            "node_id",
                            "",
                        )
                    )

                    if ancestor_id in ancestor_seen:
                        break

                    ancestor_seen.add(
                        ancestor_id
                    )

                    names = [
                        self._normalize(
                            str(value)
                        )
                        for value in ancestor.get(
                            "entity_names",
                            [],
                        )
                        if str(
                            value
                        ).strip()
                    ]

                    if any(
                        entity_name
                        and entity_name in searchable
                        for entity_name in names
                    ):
                        found_context = True
                        break

                    ancestor = nodes_by_id.get(
                        str(
                            ancestor.get(
                                "parent_id"
                            )
                        )
                    )

                if not found_context:
                    return 0.0, ""

            score += 16.0
            reasons.append(
                "entity_concept_match"
            )

        # Dynamic routing signals.
        for signal in self._routing_signals(
            node
        ):
            if self._normalize(
                signal
            ) in searchable:
                score += 3.0
                reasons.append(
                    "routing_signal"
                )

        # Name/display-name phrase match.
        if (
            name
            and name in searchable
        ):
            score += 6.0
            reasons.append(
                "name_match"
            )
        elif (
            display_name
            and display_name in searchable
        ):
            score += 6.0
            reasons.append(
                "display_match"
            )

        # Direct concept words from the generated plan.
        concept_tokens = [
            token
            for token in self._tokenize(
                name
            )
            if len(token) >= 4
        ]

        token_hits = sum(
            token in searchable
            for token in concept_tokens
        )

        if token_hits:
            score += min(
                4.0,
                float(token_hits),
            )

            reasons.append(
                "token_match"
            )

        return score, ",".join(
            sorted(
                set(
                    reasons
                )
            )
        )

    # ========================================================================
    # TAXONOMY PATH
    # ========================================================================

    @staticmethod
    def _node_path(
        node: dict[str, Any],
        nodes: list[dict[str, Any]],
    ) -> str:

        by_id = {
            str(
                candidate.get(
                    "node_id",
                    "",
                )
            ): candidate
            for candidate in nodes
            if isinstance(
                candidate,
                dict,
            )
        }

        current = node
        parts: list[str] = []

        visited: set[str] = set()

        while current is not None:

            node_id = str(
                current.get(
                    "node_id",
                    "",
                )
            )

            if node_id in visited:
                raise ValueError(
                    "Circular taxonomy parent relationship."
                )

            visited.add(
                node_id
            )

            parts.append(
                str(
                    current.get(
                        "display_name",
                        current.get(
                            "name",
                            "Unknown",
                        ),
                    )
                )
            )

            parent_id = current.get(
                "parent_id"
            )

            if parent_id is None:
                break

            current = by_id.get(
                str(
                    parent_id
                )
            )

            if current is None:
                raise ValueError(
                    "Taxonomy parent node is missing."
                )

        parts.reverse()

        return "/".join(
            parts
        )

    @staticmethod
    def _path_part(
        path: str | None,
        index: int,
    ) -> str | None:

        if not path:
            return None

        parts = path.split(
            "/"
        )

        return (
            parts[index]
            if index < len(parts)
            else None
        )

    # ========================================================================
    # BUFFERS
    # ========================================================================

    def _select_buffer(
        self,
        *,
        heading: str,
        text: str,
    ) -> str:

        searchable = self._normalize(
            f"{heading} {text}"
        )

        if any(
            token in searchable
            for token in {
                "policy",
                "policies",
                "regulation",
                "regulations",
                "ordinance",
                "rule",
                "rules",
                "guideline",
                "guidelines",
            }
        ):
            return self.BUFFER_NAMES[
                "policy"
            ]

        if any(
            token in searchable
            for token in {
                "student",
                "students",
                "campus",
                "club",
                "clubs",
                "nss",
                "ncc",
                "welfare",
                "counselling",
                "counseling",
            }
        ):
            return self.BUFFER_NAMES[
                "student"
            ]

        if any(
            token in searchable
            for token in {
                "activity",
                "activities",
                "seminar",
                "seminars",
                "workshop",
                "workshops",
                "outreach",
                "festival",
                "conference",
            }
        ):
            return self.BUFFER_NAMES[
                "activity"
            ]

        # Legitimate unmatched content is never dropped.
        return self.BUFFER_NAMES[
            "general"
        ]

    # ========================================================================
    # WRITING
    # ========================================================================

    def _write_units(
        self,
        *,
        domain: str,
        units: list[dict[str, Any]],
    ) -> list[str]:

        grouped: dict[
            str,
            list[dict[str, Any]],
        ] = defaultdict(list)

        for unit in units:

            path = unit[
                "taxonomy_path"
            ]

            if path:
                grouped[
                    f"TAXONOMY::{path}"
                ].append(
                    unit
                )
            else:
                grouped[
                    f"BUFFER::{unit['buffer_name']}"
                ].append(
                    unit
                )

        written_files: list[str] = []

        for group_key in sorted(
            grouped
        ):

            group_units = grouped[
                group_key
            ]

            if group_key.startswith(
                "BUFFER::"
            ):

                buffer_name = group_key[
                    len(
                        "BUFFER::"
                    ):
                ]

                output_dir = (
                    self.folder_builder.create_buffer_folder(
                        domain=domain,
                        buffer_name=buffer_name,
                    )
                )

                output_file = (
                    output_dir
                    / "knowledge.md"
                )

                self._write_group_file(
                    output_file=output_file,
                    title=buffer_name,
                    domain=domain,
                    path=(
                        f"BUFFER/{buffer_name}"
                    ),
                    source_units=group_units,
                )

            else:

                taxonomy_path = group_key[
                    len(
                        "TAXONOMY::"
                    ):
                ]

                parts = taxonomy_path.split(
                    "/"
                )

                # Use the full generated taxonomy path as folders. The
                # taxonomy plan has already bounded depth and validated
                # parents.
                output_dir = (
                    self.output_path
                    / self._safe_name(
                        domain
                    )
                )

                for part in parts:
                    output_dir = (
                        output_dir
                        / self._safe_name(
                            part
                        )
                    )

                output_dir.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                output_file = (
                    output_dir
                    / "knowledge.md"
                )

                self._write_group_file(
                    output_file=output_file,
                    title=parts[-1],
                    domain=domain,
                    path=taxonomy_path,
                    source_units=group_units,
                )

            written_files.append(
                str(
                    output_file
                )
            )

        return written_files

    def _write_group_file(
        self,
        *,
        output_file: Path,
        title: str,
        domain: str,
        path: str,
        source_units: list[dict[str, Any]],
    ) -> None:

        lines = [
            f"# {title}",
            "",
            f"**Domain:** {domain}",
            f"**Knowledge Path:** {path}",
            "",
            "---",
            "",
        ]

        for unit in source_units:

            lines.extend(
                [
                    f"## {unit['heading']}",
                    "",
                    unit["text"],
                    "",
                    "---",
                    "",
                    (
                        "<!-- "
                        f"Unit ID: {unit['unit_id']} | "
                        f"Source lines: "
                        f"{unit['start_line']}-"
                        f"{unit['end_line']} | "
                        f"Decision: {unit['decision']} | "
                        f"Classification: "
                        f"{unit['taxonomy_path'] or 'BUFFER'}"
                        " -->"
                    ),
                    "",
                ]
            )

        output_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_file.write_text(
            "\n".join(
                lines
            ),
            encoding="utf-8",
        )

    # ========================================================================
    # MARKDOWN PARSING
    # ========================================================================

    def _parse_sections(
        self,
        content: str,
    ) -> list[dict[str, Any]]:

        lines = content.splitlines()

        sections: list[
            dict[str, Any]
        ] = []

        current: dict[str, Any] | None = None
        pending_decision: str | None = None

        for line_number, line in enumerate(
            lines,
            start=1,
        ):

            # Document metadata such as **Domain:** is not knowledge
            # content and must not become an artificial "Document Overview"
            # section.
            if self._is_metadata_line(
                line
            ):
                continue

            decision = self._parse_decision(
                line
            )

            if decision:
                pending_decision = decision

                if current is not None:
                    current[
                        "end_line"
                    ] = line_number - 1

                    self._finalize_section(
                        sections,
                        current,
                    )

                    current = None

                continue

            heading_match = re.match(
                r"^(#{1,6})\s+(.+?)\s*$",
                line,
            )

            if heading_match:

                if current is not None:
                    current[
                        "end_line"
                    ] = line_number - 1

                    self._finalize_section(
                        sections,
                        current,
                    )

                current = {
                    "heading": (
                        heading_match
                        .group(2)
                        .strip()
                    ),
                    "level": len(
                        heading_match.group(1)
                    ),
                    "lines": [],
                    "start_line": line_number,
                    "end_line": line_number,
                    "decision": (
                        pending_decision
                        or "KEEP"
                    ),
                }

                pending_decision = None
                continue

            if current is None:

                if not line.strip():
                    continue

                current = {
                    "heading": "Document Overview",
                    "level": 1,
                    "lines": [],
                    "start_line": line_number,
                    "end_line": line_number,
                    "decision": (
                        pending_decision
                        or "KEEP"
                    ),
                }

                pending_decision = None

            current[
                "lines"
            ].append(line)

            current[
                "end_line"
            ] = line_number

        if current is not None:
            self._finalize_section(
                sections,
                current,
            )

        return sections

    def _finalize_section(
        self,
        sections: list[dict[str, Any]],
        section: dict[str, Any],
    ) -> None:

        text = "\n".join(
            section[
                "lines"
            ]
        ).strip()

        heading = section[
            "heading"
        ]

        if not text:
            return

        decision = section[
            "decision"
        ]

        if self._is_noise_heading(
            heading
        ):
            decision = "NOISE"

        elif self._is_noise_content(
            text
        ):
            decision = "NOISE"

        sections.append(
            {
                "heading": heading,
                "level": section[
                    "level"
                ],
                "text": text,
                "start_line": section[
                    "start_line"
                ],
                "end_line": section[
                    "end_line"
                ],
                "decision": decision,
            }
        )

    # ========================================================================
    # NOISE / DOMAIN
    # ========================================================================

    @staticmethod
    def _is_metadata_line(
        line: str,
    ) -> bool:
        """Return True for pipeline metadata that should not be organized."""

        stripped = line.strip()

        if not stripped:
            return False

        return bool(
            re.match(
                r"^\*\*[A-Za-z][A-Za-z _-]*:\*\*\s*.+$",
                stripped,
            )
        )

    def _parse_decision(
        self,
        line: str,
    ) -> str | None:

        value = (
            line.strip()
            .upper()
        )

        if value in {
            "[KEEP]",
            "KEEP",
            "<KEEP>",
        }:
            return "KEEP"

        if value in {
            "[REVIEW]",
            "REVIEW",
            "<REVIEW>",
        }:
            return "REVIEW"

        if value in {
            "[NOISE]",
            "NOISE",
            "<NOISE>",
        }:
            return "NOISE"

        return None

    def _is_noise_heading(
        self,
        heading: str,
    ) -> bool:

        return (
            self._normalize(
                heading
            )
            in self.NOISE_HEADINGS
        )

    def _is_noise_content(
        self,
        text: str,
    ) -> bool:

        return (
            self._normalize(
                text
            )
            in self.NOISE_EXACT_CONTENT
        )

    def _extract_domain(
        self,
        markdown_path: Path,
        content: str,
    ) -> str:

        match = re.search(
            r"\*\*Domain:\*\*\s*(.+)",
            content,
            flags=re.IGNORECASE,
        )

        if match:
            value = self._safe_name(
                match.group(1)
            )

            if value:
                return value

        return (
            self._safe_name(
                markdown_path.parent.name
            )
            or "unknown"
        )

    # ========================================================================
    # HELPERS
    # ========================================================================

    @staticmethod
    def _routing_signals(
        node: dict[str, Any],
    ) -> list[str]:

        values: list[str] = []

        raw = node.get(
            "routing_signals",
            [],
        )

        if isinstance(
            raw,
            list,
        ):
            for signal in raw:
                value = str(
                    signal
                ).strip()

                if not value:
                    continue

                # Convert planner signal prefixes into searchable phrases.
                if ":" in value:
                    value = value.split(
                        ":",
                        1,
                    )[1]

                values.append(
                    value.lower().replace(
                        "_",
                        " ",
                    )
                )

        return values

    @staticmethod
    def _tokenize(
        value: str,
    ) -> list[str]:
        return re.findall(
            r"\b[a-z][a-z0-9-]{2,}\b",
            value.lower(),
        )

    @staticmethod
    def _score_confidence(
        score: float,
    ) -> str:

        if score >= 14:
            return "high"

        if score >= 9:
            return "medium"

        return "low"

    @staticmethod
    def _make_unit_id(
        markdown_path: Path,
        index: int,
    ) -> str:

        raw = (
            f"{markdown_path.resolve()}"
            f"::{index}"
        )

        return hashlib.sha1(
            raw.encode(
                "utf-8"
            )
        ).hexdigest()[:16]

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
    def _safe_name(
        value: str,
    ) -> str:

        value = (
            value or ""
        ).strip().lower()

        value = re.sub(
            r"[^a-z0-9._-]+",
            "_",
            value,
        )

        value = re.sub(
            r"_+",
            "_",
            value,
        )

        return (
            value.strip(
                "._-"
            )
            or "unknown"
        )


if __name__ == "__main__":
    print(
        "KnowledgeOrganizer is a Phase 8.3 processor."
    )
    print(
        "Use: KnowledgeOrganizer(...).organize(path)"
    )