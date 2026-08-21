"""
Phase 8.3 — Dynamic Knowledge Folder Builder.

Purpose
-------
Execute a generated taxonomy plan into a physical folder tree.

This component is deliberately separate from the crawler's legacy
URL-based processors.folder_builder.FolderBuilder.

Responsibilities
----------------
- Read a generated taxonomy plan.
- Create only folders represented in that plan.
- Preserve taxonomy node IDs in a manifest.
- Create buffer folders only when the organizer explicitly requests them.

This module does NOT:
- discover taxonomy
- classify knowledge
- delete knowledge
- use an LLM
- interpret URLs
"""

from __future__ import annotations

from pathlib import Path
import json
import re
from typing import Any


class KnowledgeFolderBuilder:
    """Deterministically materialize a dynamic taxonomy plan."""

    PHASE = "8.3"

    def __init__(
        self,
        output_root: str | Path = "storage/organized_knowledge",
    ) -> None:
        self.output_root = Path(output_root)

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def build(
        self,
        *,
        taxonomy_plan: dict[str, Any],
        domain: str,
        active_node_ids: set[str] | None = None,
    ) -> dict[str, Any]:
        """
        Materialize the generated taxonomy.

        If active_node_ids is supplied, only those nodes and their required
        ancestors are created. This is what prevents empty boilerplate
        folders when a taxonomy plan contains a node that has no assigned
        knowledge units.
        """

        self._validate_plan(
            taxonomy_plan
        )

        domain_name = self._safe_name(
            domain
        )

        domain_root = (
            self.output_root
            / domain_name
        )

        domain_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        nodes = taxonomy_plan.get(
            "nodes",
            [],
        )

        all_nodes_by_id = {
            str(
                node["node_id"]
            ): node
            for node in nodes
        }

        if active_node_ids is None:
            materialize_ids = set(
                all_nodes_by_id
            )
        else:
            materialize_ids = set(
                str(node_id)
                for node_id in active_node_ids
            )

            # Always materialize ancestors required to reach an active node.
            expanded = set(
                materialize_ids
            )

            changed = True

            while changed:
                changed = False

                for node_id in list(
                    expanded
                ):
                    node = all_nodes_by_id.get(
                        node_id
                    )

                    if node is None:
                        raise ValueError(
                            "Active taxonomy node does not exist: "
                            f"{node_id}"
                        )

                    parent_id = node.get(
                        "parent_id"
                    )

                    if (
                        parent_id is not None
                        and str(
                            parent_id
                        ) not in expanded
                    ):
                        expanded.add(
                            str(parent_id)
                        )
                        changed = True

            materialize_ids = expanded

        created: list[dict[str, Any]] = []

        node_path_by_id: dict[str, Path] = {}

        ordered_nodes = sorted(
            nodes,
            key=lambda node: (
                int(
                    node.get(
                        "level",
                        1,
                    )
                    or 1
                ),
                str(
                    node.get(
                        "node_id",
                        "",
                    )
                ),
            ),
        )

        for node in ordered_nodes:

            node_id = str(
                node.get(
                    "node_id",
                    "",
                )
            ).strip()

            if not node_id:
                raise ValueError(
                    "Taxonomy node has no node_id."
                )

            if node_id not in materialize_ids:
                continue

            name = self._safe_name(
                str(
                    node.get(
                        "name",
                        "",
                    )
                )
            )

            if not name:
                raise ValueError(
                    f"Taxonomy node {node_id} has no valid name."
                )

            parent_id = node.get(
                "parent_id"
            )

            if parent_id is None:
                node_path = (
                    domain_root
                    / name
                )
            else:
                parent_key = str(
                    parent_id
                )

                parent_path = node_path_by_id.get(
                    parent_key
                )

                if parent_path is None:
                    raise ValueError(
                        "Taxonomy parent was not materialized before child: "
                        f"{node_id} -> {parent_id}"
                    )

                node_path = (
                    parent_path
                    / name
                )

            node_path.mkdir(
                parents=True,
                exist_ok=True,
            )

            node_path_by_id[
                node_id
            ] = node_path

            created.append(
                {
                    "node_id": node_id,
                    "name": name,
                    "display_name": node.get(
                        "display_name",
                        name,
                    ),
                    "level": node.get(
                        "level",
                        1,
                    ),
                    "node_type": node.get(
                        "node_type",
                        "unknown",
                    ),
                    "path": str(
                        node_path
                    ),
                    "parent_id": parent_id,
                }
            )

        manifest = {
            "phase": self.PHASE,
            "domain": domain,
            "taxonomy_version": taxonomy_plan.get(
                "version"
            ),
            "taxonomy_node_count": len(
                created
            ),
            "materialized_node_ids": sorted(
                materialize_ids
            ),
            "folders": created,
        }

        manifest_path = (
            domain_root
            / "taxonomy_folder_manifest.json"
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

    def create_buffer_folder(
        self,
        *,
        domain: str,
        buffer_name: str,
    ) -> Path:
        """
        Create one buffer folder on demand.

        Buffers are created only when the organizer has legitimate
        unmatched knowledge for that buffer.
        """

        domain_root = (
            self.output_root
            / self._safe_name(
                domain
            )
        )

        path = (
            domain_root
            / "buffers"
            / self._safe_name(
                buffer_name
            )
        )

        path.mkdir(
            parents=True,
            exist_ok=True,
        )

        return path

    # ========================================================================
    # VALIDATION
    # ========================================================================

    @staticmethod
    def _validate_plan(
        taxonomy_plan: dict[str, Any],
    ) -> None:

        if not isinstance(
            taxonomy_plan,
            dict,
        ):
            raise TypeError(
                "taxonomy_plan must be a dictionary."
            )

        nodes = taxonomy_plan.get(
            "nodes"
        )

        if not isinstance(
            nodes,
            list,
        ):
            raise ValueError(
                "taxonomy_plan.nodes must be a list."
            )

        node_ids = {
            str(
                node.get(
                    "node_id",
                    ""
                )
            )
            for node in nodes
            if isinstance(
                node,
                dict,
            )
        }

        if len(node_ids) != len(nodes):
            raise ValueError(
                "Taxonomy plan contains duplicate or missing node IDs."
            )

        for node in nodes:

            if not isinstance(
                node,
                dict,
            ):
                raise ValueError(
                    "Every taxonomy node must be a dictionary."
                )

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
                    "Taxonomy node references a missing parent."
                )

    # ========================================================================
    # HELPERS
    # ========================================================================

    @staticmethod
    def _safe_name(
        value: str,
    ) -> str:
        value = str(
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
            value.strip("._-")
            or "unknown"
        )


if __name__ == "__main__":
    print(
        "KnowledgeFolderBuilder is a Phase 8.3 processor."
    )
