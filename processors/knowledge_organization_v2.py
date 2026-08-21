"""
Command 4 V2 — Lossless Dynamic Knowledge Organizer.

Purpose
-------
Organize ONLY Command-3 accepted A/B/REVIEW knowledge into a dynamic,
human-editable Markdown tree without losing or silently rewriting accepted
content.

Core invariants
---------------
1. Command 4 never performs value classification.
2. Only A/B/REVIEW may enter.
3. Every accepted unit is assigned to exactly one output document.
4. No accepted unit may disappear during planning, merging, or rendering.
5. Original accepted content is preserved verbatim in the Markdown body.
6. Folder/document structure is dynamic and evidence-driven.
7. There is no fixed document-count limit.
8. Small subjects stay consolidated unless a real semantic boundary exists.
9. Large subjects may split into several meaningful documents.
10. Department/school entities get their own top-level entity area when the
    accepted units explicitly identify those entities.
11. JSON records the plan and unit-to-document manifest for auditability.

Non-responsibilities
--------------------
- No embeddings/vector DB.
- No retrieval/chunking.
- No Command-3 reclassification policy.
- No hardcoded IIT Jodhpur departments.
- No summary/rewrite of accepted knowledge.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
import json
import re
from typing import Any, Iterable


ALLOWED_TIERS = {"A", "B", "REVIEW"}

DEPARTMENT_ENTITY_TYPES = {"department", "school", "academic_unit"}
ENTITY_TYPES = {
    "department", "school", "academic_unit", "research_centre", "research_center",
    "facility", "office", "service", "hostel", "centre", "center",
}

# Command 3's frozen semantic families are evidence for Command 4, not a
# mandatory folder count. A family becomes a folder only when accepted content
# needs that semantic area.
FAMILY_ROOTS = {
    "institute college overview": "institute_overview",
    "admissions": "admissions",
    "academics": "academics",
    "programs courses": "programs_courses",
    "departments schools branches": "departments",
    "faculty hod dean key people": "faculty",
    "rules regulations policies": "rules_regulations_policies",
    "fees financial information": "fees_financial_information",
    "hostel accommodation": "hostel_accommodation",
    "student services welfare": "student_services_welfare",
    "scholarships financial aid": "scholarships_financial_aid",
    "placements careers": "placements_careers",
    "infrastructure facilities": "infrastructure_facilities",
    "important contacts emergency": "important_contacts_emergency",
    "relevant institutional research": "research",
}

# Generic semantic intents. These are universal routing concepts, not college-
# specific departments or fixed output folders.
SEMANTIC_RULES = [
    ("admissions", "admission_rules", ("admission", "admissions", "eligibility", "application", "apply", "reservation")),
    ("scholarships_financial_aid", "assistantship_and_fellowship", ("scholarship", "fellowship", "assistantship", "financial aid", "financial assistance")),
    ("fees_financial_information", "fees_and_finance", ("tuition", "fee", "fees", "charges", "refund", "payment")),
    ("hostel_accommodation", "accommodation", ("hostel", "hostels", "accommodation", "residence hall", "residential accommodation", "student residence")),
    ("infrastructure_facilities", "facilities", ("facility", "facilities", "infrastructure", "laboratory", "laboratories", "lab", "library", "libraries", "workshop")),
    ("important_contacts_emergency", "contacts", ("contact", "contacts", "address", "phone", "telephone", "email", "emergency")),
    ("faculty", "faculty", ("faculty", "professor", "professors", "teaching staff", "staff directory", "hod", "head of department", "dean")),
    ("research", "research", ("research", "research area", "research areas", "research interest", "research interests")),
    ("placements_careers", "placements_and_careers", ("placement", "placements", "career", "careers", "recruitment", "recruiters")),
    ("student_services_welfare", "student_services", ("student services", "student support", "student welfare", "counselling", "counseling", "wellbeing", "grievance")),
    ("rules_regulations_policies", "rules_and_regulations", ("rule", "rules", "regulation", "regulations", "policy", "policies", "guideline", "guidelines", "ordinance")),
    ("programs_courses", "course_registration", ("add and drop", "adding and dropping", "withdrawal", "withdrawing", "course registration", "registration of courses", "auditing of courses")),
    ("programs_courses", "courses_and_curriculum", ("course", "courses", "curriculum", "syllabus", "syllabi", "credit", "credits", "course category", "course categories")),
    ("programs_courses", "examinations_and_grading", ("exam", "examination", "evaluation", "grading", "grade", "results", "comprehensive examination")),
    ("programs_courses", "program_requirements", ("academic requirements", "program requirements", "programme requirements", "maximum duration", "graduation requirements", "academic load")),
    ("academics", "academic_calendar_and_schedule", ("academic calendar", "academic session", "semester dates", "term dates", "session dates", "vacation", "recess")),
    ("academics", "attendance_and_leave", ("attendance", "leave of absence", "short leave", "medical leave", "absence")),
    ("academics", "registration", ("registration", "late registration", "cancellation of registration", "change of registration")),
    ("academics", "academic_performance_and_progression", ("academic performance", "continuation", "progress monitoring", "progress monitoring meeting", "qualifier requirements", "candidacy")),
    ("academics", "academic_leave", ("academic leave",)),
    ("academics", "branch_change", ("branch change",)),
    ("academics", "teaching_assignments", ("teaching assignments", "teaching assignment")),
    ("academics", "graduation_and_certification", ("degree certificate", "provisional certificate", "graduation")),
    ("academics", "doctoral_academic_progression", ("ph.d.", "phd", "ph.d", "research supervisor", "supervisor", "synopsis", "doctoral")),
    ("academics", "student_disciplinary_matters", ("disciplinary action", "disciplinary", "termination")),
    ("academics", "academic_requirements", ("academic requirements", "requirements")),
    ("institute_overview", "overview", ("overview", "about the institute", "about the college", "introduction", "profile", "history", "vision", "mission")),
]

PROGRAM_MARKERS = [
    # Specific programme names must be checked before broad level markers.
    ("b.tech", "btech"), ("btech", "btech"), ("m.tech", "mtech"), ("mtech", "mtech"),
    ("m.sc", "msc"), ("msc", "msc"), ("m.b.a", "mba"), ("mba", "mba"),
    ("b.com", "bcom"), ("bcom", "bcom"), ("b.a.", "ba"), ("bba", "bba"),
    ("ph.d", "phd"), ("phd", "phd"),
    ("undergraduate", "undergraduate"), ("postgraduate", "postgraduate"), ("doctoral", "doctoral"),
]

# Size is a safety mechanism, not a page-count rule. A document may exceed
# this when no safe semantic boundary exists; it must never be split randomly.
SOFT_WORD_TARGET = 3500
HARD_WORD_LIMIT = 6000

# Small institution-wide domains stay consolidated when they contain only a
# small amount of accepted content. This is a fragmentation guard, not a fixed
# folder taxonomy.
CONSOLIDATE_SMALL_ROOTS = {
    "hostel_accommodation",
    "faculty",
    "important_contacts_emergency",
    "institute_overview",
    "fees_financial_information",
    "student_services_welfare",
}


def topic_from_heading(heading: str) -> str:
    """Derive a conservative semantic topic from a heading without naming a college."""
    words = [w for w in re.split(r"\s+", heading) if w]
    if not words:
        return ""
    # Prefer meaningful multi-word concepts already expressed by the heading.
    stop = {"the", "and", "of", "for", "to", "in", "on", "a", "an", "with"}
    meaningful = [w for w in words if w not in stop]
    return "_".join(meaningful[:5]) if meaningful else ""


@dataclass(frozen=True)
class OrganizationDocument:
    document_id: str
    title: str
    path: str
    scope_type: str
    scope_id: str
    topic: str
    knowledge_family: str
    unit_ids: tuple[str, ...]


class Command4OrganizationV2:
    """Deterministic, lossless organization of accepted Command-3 units."""

    VERSION = "2.11"
    OUTPUT_ROOT = Path("storage/v2_command4_organized_knowledge")

    def build_plan(
        self,
        *,
        domain: str,
        units: Iterable[dict[str, Any]],
    ) -> dict[str, Any]:
        normalized = self._normalize_units(units)
        self._validate_input_units(normalized)

        groups = self._build_semantic_groups(normalized)
        documents = [
            self._make_document(
                domain=domain,
                scope_type=scope_type,
                scope_id=scope_id,
                topic=topic,
                family=self._family_for_group(group),
                units=group,
            )
            for (scope_type, scope_id, topic), group in sorted(
                groups.items(),
                key=lambda item: item[0],
            )
        ]

        documents = self._deduplicate_paths_losslessly(documents)
        documents.sort(key=lambda doc: (doc.path, doc.document_id))
        self._validate_documents(documents, normalized)

        return {
            "version": self.VERSION,
            "phase": "command_4_dynamic_organization",
            "domain": domain,
            "input_policy": {
                "allowed_tiers": sorted(ALLOWED_TIERS),
                "source_of_value_decision": "command_3",
                "lossless_content_policy": True,
            },
            "roots": sorted({self._root_folder(doc) for doc in documents}),
            "documents": [asdict(doc) for doc in documents],
            "unit_count": len(normalized),
            "document_count": len(documents),
            "assignment": {
                "missing_unit_count": 0,
                "duplicate_unit_count": 0,
                "extra_unit_count": 0,
            },
        }

    def write_output(
        self,
        *,
        domain: str,
        units: Iterable[dict[str, Any]],
        output_root: str | Path | None = None,
    ) -> dict[str, Any]:
        """Write plan, Markdown documents, and a unit-level audit manifest."""
        normalized = self._normalize_units(units)
        plan = self.build_plan(domain=domain, units=normalized)
        root = Path(output_root or self.OUTPUT_ROOT) / self._slug(domain)
        root.mkdir(parents=True, exist_ok=True)

        unit_map = {unit["unit_id"]: unit for unit in normalized}
        documents = plan["documents"]
        written_files: list[str] = []
        unit_manifest: list[dict[str, Any]] = []

        for document in documents:
            path = root / document["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                self._render_markdown(document, unit_map),
                encoding="utf-8",
            )
            written_files.append(str(path.relative_to(root)))

            for unit_id in document["unit_ids"]:
                unit = unit_map[unit_id]
                unit_manifest.append(
                    {
                        "unit_id": unit_id,
                        "document_id": document["document_id"],
                        "path": document["path"],
                        "tier": unit["tier"],
                        "source_file": unit["source_file"],
                        "source_url": unit["source_url"],
                        "content_sha256": self._content_hash(unit["text"]),
                    }
                )

        plan_path = root / "organization_plan.json"
        plan_path.write_text(
            json.dumps(plan, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        unit_manifest.sort(key=lambda row: (row["path"], row["unit_id"]))
        manifest = {
            "version": self.VERSION,
            "phase": "command_4_dynamic_organization",
            "domain": domain,
            "unit_count": len(normalized),
            "document_count": len(documents),
            "written_files": written_files,
            "coverage": {
                "input_unit_count": len(normalized),
                "output_assigned_unit_count": len(unit_manifest),
                "missing_unit_ids": [],
                "unassigned_unit_ids": [],
                "duplicate_unit_ids": [],
                "extra_unit_ids": [],
            },
            "units": unit_manifest,
            "plan_path": "organization_plan.json",
        }

        manifest_path = root / "organization_manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return manifest

    # ------------------------------------------------------------------
    # Input contract
    # ------------------------------------------------------------------

    def _normalize_units(self, units: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for raw in units:
            if not isinstance(raw, dict):
                raise TypeError("Every Command 4 input unit must be a dictionary.")

            unit = dict(raw)
            unit["unit_id"] = str(unit.get("unit_id", "")).strip()
            unit["tier"] = str(unit.get("tier", unit.get("value_tier", ""))).strip().upper()
            unit["heading"] = str(unit.get("heading", unit.get("title", ""))).strip()
            unit["text"] = str(unit.get("text", unit.get("content", ""))).strip()
            unit["knowledge_family"] = str(
                unit.get("knowledge_family", unit.get("family", "Other Institutional Information"))
            ).strip() or "Other Institutional Information"
            unit["source_file"] = str(unit.get("source_file", unit.get("source_document", ""))).strip()
            unit["source_url"] = str(unit.get("source_url", unit.get("url", ""))).strip()
            unit["source_lines"] = unit.get("source_lines", unit.get("start_line"))
            result.append(unit)
        return result

    @staticmethod
    def _validate_input_units(units: list[dict[str, Any]]) -> None:
        seen: set[str] = set()
        for unit in units:
            unit_id = unit["unit_id"]
            if not unit_id:
                raise ValueError("Every accepted unit must have a unit_id.")
            if unit_id in seen:
                raise ValueError(f"Duplicate unit_id: {unit_id}")
            seen.add(unit_id)
            if unit["tier"] not in ALLOWED_TIERS:
                raise ValueError(
                    f"Command 4 received tier {unit['tier']!r} for {unit_id}. "
                    "Only A/B/REVIEW are allowed. C/D must never enter Command 4."
                )
            if not unit["text"]:
                raise ValueError(f"Accepted unit has no content: {unit_id}")

    # ------------------------------------------------------------------
    # Semantic grouping
    # ------------------------------------------------------------------

    def _build_semantic_groups(
        self,
        units: list[dict[str, Any]],
    ) -> dict[tuple[str, str, str], list[dict[str, Any]]]:
        """
        Build deterministic semantic groups and reconcile coverage.

        IMPORTANT INVARIANT:
        Every accepted input unit MUST appear in exactly one final group.

        Semantic refinement is allowed to split or merge groups, but it is
        never allowed to drop a unit. Any unit that cannot survive refinement
        is placed into a local `knowledge_buffer` document under its original
        canonical root/entity. The buffer is a safety net, not a semantic
        classification mechanism.
        """
        groups: dict[
            tuple[str, str, str],
            list[dict[str, Any]],
        ] = defaultdict(list)

        # Keep the original canonical placement for every input unit so that
        # the lossless fallback always has a deterministic semantic home.
        original_placement: dict[
            str,
            tuple[str, str, str],
        ] = {}

        unit_by_id: dict[str, dict[str, Any]] = {}

        for unit in units:
            unit_id = unit["unit_id"]
            unit_by_id[unit_id] = unit

            scope_type, scope_id = self._scope_for_unit(
                unit
            )

            root, topic = self._canonical_placement(
                unit,
                scope_type=scope_type,
            )

            if scope_type in {
                "department",
                "school",
                "academic_unit",
            }:
                key_scope_type = scope_type
                key_scope_id = scope_id
            else:
                key_scope_type = "family"
                key_scope_id = root

            placement = (
                key_scope_type,
                key_scope_id,
                topic,
            )

            original_placement[unit_id] = placement
            groups[placement].append(unit)

        # ------------------------------------------------------------------
        # Consolidate small coherent institution-wide roots.
        # ------------------------------------------------------------------
        merged: dict[
            tuple[str, str],
            list[dict[str, Any]],
        ] = defaultdict(list)

        remaining: dict[
            tuple[str, str, str],
            list[dict[str, Any]],
        ] = {}

        for (
            scope_type,
            scope_id,
            topic,
        ), group in groups.items():

            root = (
                scope_id
                if scope_type == "family"
                else None
            )

            if (
                scope_type == "family"
                and root in CONSOLIDATE_SMALL_ROOTS
            ):
                merged[
                    (scope_type, scope_id)
                ].extend(group)
            else:
                remaining[
                    (
                        scope_type,
                        scope_id,
                        topic,
                    )
                ] = list(group)

        for (
            scope_type,
            scope_id,
        ), group in merged.items():

            total_words = sum(
                len(u["text"].split())
                for u in group
            )

            if (
                len(group) <= 8
                and total_words <= SOFT_WORD_TARGET
            ):
                remaining[
                    (
                        scope_type,
                        scope_id,
                        self._preferred_small_topic(
                            group,
                            scope_id,
                        ),
                    )
                ] = list(group)
            else:
                topic_groups = (
                    self._rebuild_family_topics(
                        group
                    )
                )

                for topic, topic_units in (
                    topic_groups.items()
                ):
                    remaining.setdefault(
                        (
                            scope_type,
                            scope_id,
                            topic,
                        ),
                        [],
                    ).extend(
                        topic_units
                    )

        # ------------------------------------------------------------------
        # Semantic refinement / size splitting.
        # ------------------------------------------------------------------
        refined: dict[
            tuple[str, str, str],
            list[dict[str, Any]],
        ] = defaultdict(list)

        for (
            scope_type,
            scope_id,
            topic,
        ), group in sorted(
            remaining.items(),
            key=lambda item: item[0],
        ):
            split_groups = (
                self._size_aware_split(
                    scope_type=scope_type,
                    scope_id=scope_id,
                    topic=topic,
                    units=group,
                )
            )

            for refined_topic, refined_group in (
                split_groups.items()
            ):
                # CRITICAL:
                # Never assign with "=" here. Multiple intermediate groups
                # can legitimately refine to the same topic.
                refined[
                    (
                        scope_type,
                        scope_id,
                        refined_topic,
                    )
                ].extend(
                    refined_group
                )

        # ------------------------------------------------------------------
        # LOSSLESS RECONCILIATION SAFETY NET.
        #
        # Compare the original accepted-unit set with the refined-unit set.
        # Any unit that disappeared is restored into a deterministic buffer
        # attached to its original semantic root/entity.
        # ------------------------------------------------------------------
        assigned_ids = {
            unit_id
            for group in refined.values()
            for unit_id in (
                unit["unit_id"]
                for unit in group
            )
        }

        expected_ids = set(unit_by_id)

        missing_ids = sorted(
            expected_ids - assigned_ids
        )

        if missing_ids:
            buffer_groups: dict[
                tuple[str, str, str],
                list[dict[str, Any]],
            ] = defaultdict(list)

            for unit_id in missing_ids:
                unit = unit_by_id[unit_id]

                (
                    original_scope_type,
                    original_scope_id,
                    _original_topic,
                ) = original_placement[unit_id]

                buffer_groups[
                    (
                        original_scope_type,
                        original_scope_id,
                        "knowledge_buffer",
                    )
                ].append(unit)

            for key, buffer_units in (
                buffer_groups.items()
            ):
                refined[key].extend(
                    buffer_units
                )

        # ------------------------------------------------------------------
        # Final deterministic normalization.
        # ------------------------------------------------------------------
        final_groups: dict[
            tuple[str, str, str],
            list[dict[str, Any]],
        ] = {}

        for key, value in sorted(
            refined.items(),
            key=lambda item: item[0],
        ):
            # Deduplicate within one document defensively. This does not
            # compensate for cross-document duplicates; the final validator
            # still rejects those.
            unique_units: dict[
                str,
                dict[str, Any],
            ] = {}

            for unit in value:
                unique_units[
                    unit["unit_id"]
                ] = unit

            final_groups[key] = sorted(
                unique_units.values(),
                key=self._unit_sort_key,
            )

        return final_groups

    def _preferred_small_topic(self, units: list[dict[str, Any]], scope_id: str) -> str:
        """Choose one stable human topic for a small consolidated domain."""
        family_topic = {
            "hostel_accommodation": "accommodation",
            "faculty": "faculty",
            "important_contacts_emergency": "contacts",
            "institute_overview": "overview",
            "fees_financial_information": "fees_and_finance",
            "student_services_welfare": "student_services",
        }
        return family_topic.get(scope_id, "general_information")

    def _rebuild_family_topics(
        self,
        units: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for unit in units:
            family_root = self._family_root(
                self._family_for_unit(unit)
            )
            groups[
                self._family_local_topic(unit, family_root)
            ].append(unit)
        return groups

    def _family_local_topics(
        self,
        family_root: str,
        units: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for unit in units:
            groups[
                self._family_local_topic(unit, family_root)
            ].append(unit)
        return groups

    def _family_local_topic(
        self,
        unit: dict[str, Any],
        family_root: str,
    ) -> str:
        """
        Resolve a topic inside an already-selected root.

        Later splitting is root-local: it can create documents within a root,
        but it cannot re-route a unit into another semantic family.
        """
        heading = self._normalize(
            unit.get("heading", "")
        )

        if family_root == "admissions":
            for marker, slug in PROGRAM_MARKERS:
                if marker in f" {heading} ":
                    return f"{slug}_admissions"
            return "admission_rules"

        if family_root == "programs_courses":
            if any(
                signal in heading
                for signal in (
                    "add and drop",
                    "adding and dropping",
                    "course registration",
                    "registration of courses",
                    "withdrawing from a course",
                    "withdrawal from a course",
                    "auditing of courses",
                )
            ):
                return "course_registration"

            if any(
                signal in heading
                for signal in (
                    "examination",
                    "examinations",
                    "exam",
                    "exams",
                    "evaluation",
                    "grading",
                    "grade",
                    "grades",
                    "results",
                    "comprehensive examination",
                )
            ):
                return "examinations_and_grading"

            if any(
                signal in heading
                for signal in (
                    "academic requirements",
                    "program requirements",
                    "programme requirements",
                    "maximum duration",
                    "graduation requirements",
                    "academic load",
                )
            ):
                return "program_requirements"

            if any(
                signal in heading
                for signal in (
                    "course categories",
                    "course category",
                    "curriculum",
                    "curricula",
                    "syllabus",
                    "syllabi",
                    "credit",
                    "credits",
                    "course",
                    "courses",
                )
            ):
                return "courses_and_curriculum"

            return "programs_courses"

        if family_root == "academics":
            academic_topic_rules = (
                ("academic_calendar_and_schedule", ("academic calendar", "academic session", "semester dates", "term dates", "session dates", "vacation", "recess", "semester schedule")),
                ("attendance_and_leave", ("attendance", "leave of absence", "short leave", "medical leave", "absence")),
                ("registration", ("registration", "late registration", "cancellation of registration", "change of registration")),
                ("academic_performance_and_progression", ("academic performance", "continuation", "progress monitoring", "qualifier requirements", "candidacy")),
                ("academic_leave", ("academic leave",)),
                ("branch_change", ("branch change",)),
                ("teaching_assignments", ("teaching assignments", "teaching assignment")),
                ("graduation_and_certification", ("degree certificate", "provisional certificate", "graduation")),
                ("doctoral_academic_progression", ("ph.d.", "phd", "ph.d", "research supervisor", "supervisor", "synopsis", "doctoral")),
                ("student_disciplinary_matters", ("disciplinary action", "disciplinary", "termination")),
                ("academic_requirements", ("academic requirements",)),
            )
            for topic_name, signals in academic_topic_rules:
                if any(signal in heading for signal in signals):
                    return topic_name
            return "academics"

        return self._topic_for_contextual_family(
            unit,
            family_root,
        )

    def _canonical_placement(
        self,
        unit: dict[str, Any],
        *,
        scope_type: str,
    ) -> tuple[str, str]:
        """Choose one canonical semantic home for an accepted unit."""
        heading = self._normalize(unit.get("heading", ""))
        text = self._normalize(str(unit.get("text", ""))[:1800])
        combined = f"{heading} {text}"
        family_root = self._family_root(self._family_for_unit(unit))

        # Explicit academic entities always own their internal documents.
        if scope_type in {"department", "school", "academic_unit"}:
            return "departments", self._entity_topic_for_unit(unit, combined)

        # Strong family context protects small, coherent domains from generic
        # keywords such as dining/contact/facility leaking into another root.
        strong_context_roots = {
            "hostel_accommodation",
            "faculty",
            "student_services_welfare",
            "scholarships_financial_aid",
            "fees_financial_information",
            "placements_careers",
            "important_contacts_emergency",
            "infrastructure_facilities",
            "research",
            "institute_overview",
        }
        if family_root in strong_context_roots and family_root != "institute_overview":
            return family_root, self._topic_for_contextual_family(unit, family_root)

        # Institute overview is a special case: true overview headings stay in
        # overview, but procedural headings must be allowed to find their real
        # semantic destination instead of contaminating overview.md.
        # All routing below uses the heading, never arbitrary body mentions.
        for root, topic, signals in SEMANTIC_RULES:
            if any(signal in heading for signal in signals):
                return root, self._topic_with_program_variant(topic, heading, combined)

        if family_root in strong_context_roots:
            return family_root, self._topic_for_contextual_family(unit, family_root)

        return family_root, self._topic_for_unit(unit)

    def _topic_for_contextual_family(self, unit: dict[str, Any], family_root: str) -> str:
        """Keep specific family context while allowing meaningful internal topics."""
        heading = self._normalize(unit.get("heading", ""))
        text = self._normalize(str(unit.get("text", ""))[:1400])
        combined = f"{heading} {text}"
        contextual_rules = {
            "hostel_accommodation": [
                ("hostel_rules", ("hostel rule", "hostel regulation", "visitor rule", "residence rule")),
                ("hostel_fees", ("hostel fee", "hostel fees", "accommodation fee", "residence fee")),
                ("hostel_facilities", ("hostel facilit", "hostel amenit", "residence facilit")),
                ("hostel_contacts", ("hostel contact", "warden", "hostel office")),
            ],
            "faculty": [("faculty", ("faculty", "professor", "hod", "dean", "teaching staff", "staff"))],
            "student_services_welfare": [("student_services", ("student", "welfare", "support", "grievance", "counselling", "wellbeing"))],
            "scholarships_financial_aid": [("assistantship_and_fellowship", ("assistantship", "fellowship")), ("scholarships", ("scholarship", "financial aid", "financial assistance"))],
            "fees_financial_information": [("fees_and_finance", ("fee", "fees", "tuition", "payment", "refund", "charge"))],
            "placements_careers": [("placements_and_careers", ("placement", "career", "recruitment", "recruiter"))],
            "important_contacts_emergency": [("contacts", ("contact", "phone", "email", "address", "emergency"))],
            "infrastructure_facilities": [("facilities", ("facility", "laboratory", "library", "infrastructure", "workshop", "sports"))],
            "research": [("research", ("research", "research area", "research interest"))],
            "institute_overview": [("overview", ("overview", "about", "vision", "mission", "history", "profile"))],
        }
        for topic, signals in contextual_rules.get(family_root, []):
            if any(signal in heading for signal in signals) or any(signal in combined for signal in signals):
                return topic
        return family_root.replace("_", " ").replace("financial aid", "").strip().replace(" ", "_") or "general_information"

    def _topic_with_program_variant(
        self,
        topic: str,
        heading: str,
        combined: str,
    ) -> str:
        if topic != "admission_rules":
            return topic
        padded = f" {heading} "
        for marker, slug in PROGRAM_MARKERS:
            if marker in padded or marker in combined:
                return f"{slug}_admissions"
        return topic

    def _size_aware_split(
        self,
        *,
        scope_type: str,
        scope_id: str,
        topic: str,
        units: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        """Split only when size or strong semantic subtopics justify it."""
        total_words = sum(len(u["text"].split()) for u in units)

        if (
            scope_type == "family"
            and scope_id in CONSOLIDATE_SMALL_ROOTS
            and len(units) <= 8
            and total_words <= SOFT_WORD_TARGET
        ):
            return {topic: units}

        semantic_groups = self._subtopic_groups(
            units,
            family_root=(
                scope_id
                if scope_type == "family"
                else None
            ),
        )

        # If the accepted units contain real semantic subtopics, split them even
        # when the total text is small. This prevents catch-all documents such as
        # academics/academics.md when the headings clearly describe different topics.
        if len(semantic_groups) >= 2:
            return semantic_groups

        if total_words <= HARD_WORD_LIMIT:
            return {topic: units}

        numbered_groups = self._numbered_heading_groups(units)
        if len(numbered_groups) >= 2:
            return numbered_groups

        # No defensible semantic boundary exists. Preserve coherence rather than
        # creating arbitrary part_1/part_2 files.
        return {topic: units}

    def _numbered_heading_groups(
        self,
        units: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        """Split large generic groups using real numbered heading boundaries."""
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)

        for unit in units:
            heading = str(unit.get("heading", "")).strip()
            match = re.match(r"^\s*(\d+)(?:\.\d+)*\s*(.*)$", heading)
            if not match:
                continue

            label = re.sub(r"\s+", " ", match.group(2)).strip()
            topic = self._slug(label) or f"section_{match.group(1)}"
            groups[topic].append(unit)

        if len(groups) < 2:
            return {}

        return groups

    def _subtopic_groups(
        self,
        units: list[dict[str, Any]],
        family_root: str | None = None,
    ) -> dict[str, list[dict[str, Any]]]:
        if family_root:
            return self._family_local_topics(
                family_root,
                units,
            )

        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for unit in units:
            heading = self._normalize(
                unit.get("heading", "")
            )
            groups[
                topic_from_heading(heading)
                or "general_information"
            ].append(unit)

        strong = {
            key: value
            for key, value in groups.items()
            if len(value) >= 2
        }

        if len(strong) < 2:
            return {}

        weak_units = [
            unit
            for key, value in groups.items()
            if key not in strong
            for unit in value
        ]

        if weak_units:
            dominant = sorted(
                strong.items(),
                key=lambda item: (
                    -len(item[1]),
                    item[0],
                ),
            )[0][0]
            strong[dominant].extend(
                weak_units
            )

        return strong

    def _scope_for_unit(self, unit: dict[str, Any]) -> tuple[str, str]:
        entities = self._extract_entities(unit)
        academic_entities = [
            e for e in entities
            if e["entity_type"] in DEPARTMENT_ENTITY_TYPES
            and self._normalize(e["name"]) not in {"department", "school", "academic unit"}
        ]
        if academic_entities:
            entity = sorted(academic_entities, key=lambda item: (item["entity_type"], self._slug(item["name"])))[0]
            return entity["entity_type"], self._slug(entity["name"])
        family = self._family_for_unit(unit)
        return "family", self._family_root(family)

    def _entity_topic_for_unit(
        self,
        unit: dict[str, Any],
        combined: str,
    ) -> str:
        """Choose a dynamic document topic inside a department/school entity."""
        heading = self._normalize(unit.get("heading", ""))

        if (
            heading.startswith("department of ")
            or heading in {"overview", "department overview", "about the department", "about the school"}
        ):
            return "overview"

        entity_rules = (
            ("faculty", ("faculty", "professor", "professors", "teaching staff", "staff directory", "hod", "dean")),
            ("research", ("research", "research area", "research areas", "research interest", "research interests")),
            ("programs", ("program", "programs", "programme", "programmes", "degree", "degrees")),
            ("courses", ("course", "courses", "curriculum", "curricula", "syllabus", "syllabi")),
            ("facilities", ("facility", "facilities", "infrastructure", "laboratory", "laboratories", "lab", "library")),
            ("admissions", ("admission", "admissions", "eligibility", "application", "apply")),
        )

        for topic, signals in entity_rules:
            if any(signal in heading for signal in signals):
                return topic

        return self._topic_for_unit(unit)

    def _topic_for_unit(self, unit: dict[str, Any]) -> str:
        explicit = str(unit.get("topic", "")).strip()
        if explicit:
            return self._slug(explicit)
        heading = self._normalize(unit.get("heading", ""))
        text = self._normalize(str(unit.get("text", ""))[:1400])
        combined = f"{heading} {text}"
        for root, topic, signals in SEMANTIC_RULES:
            if any(signal in heading for signal in signals):
                return self._topic_with_program_variant(topic, heading, combined)
        return self._slug(self._family_for_unit(unit)) or "general_information"

    @staticmethod
    def _family_root(family: str) -> str:
        normalized = Command4OrganizationV2._normalize(family)
        if normalized in FAMILY_ROOTS:
            return FAMILY_ROOTS[normalized]
        return Command4OrganizationV2._slug(family)

    @staticmethod
    def _family_for_unit(unit: dict[str, Any]) -> str:
        return str(
            unit.get("knowledge_family", unit.get("family", "Other Institutional Information"))
        ).strip() or "Other Institutional Information"

    def _family_for_group(self, group: list[dict[str, Any]]) -> str:
        counts = Counter(self._family_for_unit(unit) for unit in group)
        return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]

    def _make_document(
        self,
        *,
        domain: str,
        scope_type: str,
        scope_id: str,
        topic: str,
        family: str,
        units: list[dict[str, Any]],
    ) -> OrganizationDocument:
        scope_display = self._display(scope_id)
        topic_display = self._display(topic)

        if scope_type in {"department", "school", "academic_unit"}:
            directory = Path("departments") / scope_id
        else:
            directory = Path(scope_id)
        path = directory / f"{topic}.md"

        title = f"{scope_display} — {topic_display}"
        unit_ids = tuple(sorted(unit["unit_id"] for unit in units))
        digest = hashlib.sha1(
            f"{domain}::{path.as_posix()}::{','.join(unit_ids)}".encode("utf-8")
        ).hexdigest()[:12]
        return OrganizationDocument(
            document_id=f"doc-{digest}",
            title=title,
            path=path.as_posix(),
            scope_type=scope_type,
            scope_id=scope_id,
            topic=topic,
            knowledge_family=family,
            unit_ids=unit_ids,
        )

    @staticmethod
    def _deduplicate_paths_losslessly(
        documents: list[OrganizationDocument],
    ) -> list[OrganizationDocument]:
        by_path: dict[str, OrganizationDocument] = {}
        for document in documents:
            existing = by_path.get(document.path)
            if existing is None:
                by_path[document.path] = document
                continue
            merged_ids = tuple(sorted(set(existing.unit_ids) | set(document.unit_ids)))
            family = existing.knowledge_family
            if existing.knowledge_family != document.knowledge_family:
                family = f"{existing.knowledge_family}; {document.knowledge_family}"
            by_path[document.path] = OrganizationDocument(
                document_id=existing.document_id,
                title=existing.title,
                path=existing.path,
                scope_type=existing.scope_type,
                scope_id=existing.scope_id,
                topic=existing.topic,
                knowledge_family=family,
                unit_ids=merged_ids,
            )
        return list(by_path.values())

    # ------------------------------------------------------------------
    # Validation/rendering
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_documents(
        documents: list[OrganizationDocument],
        units: list[dict[str, Any]],
    ) -> None:
        expected = {unit["unit_id"] for unit in units}
        assigned = [unit_id for doc in documents for unit_id in doc.unit_ids]
        assigned_set = set(assigned)

        duplicates = sorted(
            unit_id
            for unit_id, count in Counter(assigned).items()
            if count > 1
        )
        missing = sorted(expected - assigned_set)
        extra = sorted(assigned_set - expected)

        if duplicates or missing or extra:
            raise ValueError(
                "Organization coverage failure. "
                f"missing={missing}, extra={extra}, duplicates={duplicates}"
            )

        paths = [doc.path for doc in documents]
        if len(paths) != len(set(paths)):
            raise ValueError("Duplicate output document path detected.")

        topic_roots: dict[str, set[str]] = defaultdict(set)
        for doc in documents:
            if doc.scope_type != "family":
                continue
            topic_roots[doc.topic].add(
                Command4OrganizationV2._root_folder(doc)
            )

        conflicting_topics = {
            topic: sorted(roots)
            for topic, roots in topic_roots.items()
            if len(roots) > 1
            and topic != "knowledge_buffer"
        }
        if conflicting_topics:
            raise ValueError(
                "Conflicting semantic document roots detected: "
                f"{conflicting_topics}"
            )

    def _render_markdown(
        self,
        document: dict[str, Any],
        unit_map: dict[str, dict[str, Any]],
    ) -> str:
        ordered_units = [unit_map[unit_id] for unit_id in document["unit_ids"]]
        ordered_units.sort(key=self._unit_sort_key)

        source_files = sorted({u["source_file"] for u in ordered_units if u["source_file"]})
        source_urls = sorted({u["source_url"] for u in ordered_units if u["source_url"]})

        lines = [
            "---",
            f"id: {document['document_id']}",
            f"title: {self._yaml_quote(document['title'])}",
            f"scope_type: {document['scope_type']}",
            f"scope_id: {self._yaml_quote(document['scope_id'])}",
            f"topic: {document['topic']}",
            f"knowledge_family: {self._yaml_quote(document['knowledge_family'])}",
            f"organization_version: {self.VERSION}",
            "source_files:",
        ]
        for source in source_files:
            lines.append(f"  - {self._yaml_quote(source)}")
        lines.append("source_urls:")
        for url in source_urls:
            lines.append(f"  - {self._yaml_quote(url)}")
        lines.append("unit_ids:")
        for unit_id in document["unit_ids"]:
            lines.append(f"  - {unit_id}")
        lines.extend(["---", "", f"# {document['title']}", ""])

        for unit in ordered_units:
            heading = unit["heading"] or self._display(document["topic"])
            lines.append(f"## {heading}")
            lines.append("")
            # IMPORTANT: accepted content is written exactly as normalized by
            # the input boundary; Command 4 does not summarize or reinterpret it.
            lines.append(unit["text"].strip())
            lines.append("")

        lines.extend(["## Source Traceability", ""])
        for unit in ordered_units:
            source_file = unit.get("source_file") or "unknown"
            source_url = unit.get("source_url") or ""
            source_lines = unit.get("source_lines")
            suffix = f"; lines {source_lines}" if source_lines else ""
            if source_url:
                lines.append(
                    f"- `{unit['unit_id']}` — {source_file} — {source_url}{suffix}"
                )
            else:
                lines.append(f"- `{unit['unit_id']}` — {source_file}{suffix}")

        return "\n".join(lines).rstrip() + "\n"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_entities(unit: dict[str, Any]) -> list[dict[str, str]]:
        result: list[dict[str, str]] = []
        raw = unit.get("entities", [])
        if isinstance(raw, list):
            for item in raw:
                if isinstance(item, str):
                    if item.strip():
                        result.append({"name": item.strip(), "entity_type": "unknown"})
                elif isinstance(item, dict):
                    name = str(item.get("name", item.get("entity_name", ""))).strip()
                    entity_type = str(
                        item.get("entity_type", item.get("type", "unknown"))
                    ).strip().lower()
                    if name:
                        result.append({"name": name, "entity_type": entity_type})

        direct_name = str(unit.get("entity", unit.get("entity_name", ""))).strip()
        direct_type = str(unit.get("entity_type", "unknown")).strip().lower()
        if direct_name:
            result.append({"name": direct_name, "entity_type": direct_type})

        department = str(unit.get("department", "")).strip()
        if department:
            result.append({"name": department, "entity_type": "department"})

        unique: dict[tuple[str, str], dict[str, str]] = {}
        for item in result:
            key = (Command4OrganizationV2._normalize(item["name"]), item["entity_type"])
            if key[0]:
                unique[key] = item
        return list(unique.values())

    @staticmethod
    def _unit_sort_key(unit: dict[str, Any]) -> tuple[Any, ...]:
        section_path = unit.get("section_path", [])
        if isinstance(section_path, list):
            section_path_value = " / ".join(str(item) for item in section_path)
        else:
            section_path_value = str(section_path or "")
        return (
            section_path_value.lower(),
            int(unit.get("page_number", 0) or 0),
            int(unit.get("section_index", 0) or 0),
            str(unit.get("heading", "")).lower(),
            str(unit.get("unit_id", "")),
        )

    @staticmethod
    def _content_hash(text: str) -> str:
        return hashlib.sha256(str(text).encode("utf-8")).hexdigest()

    @staticmethod
    def _root_folder(document: OrganizationDocument) -> str:
        return document.path.split("/", 1)[0]

    @staticmethod
    def _normalize(value: Any) -> str:
        value = str(value or "").lower()
        value = value.replace("&", " and ")
        value = re.sub(r"[^a-z0-9.]+", " ", value)
        return re.sub(r"\s+", " ", value).strip()

    @classmethod
    def _slug(cls, value: str) -> str:
        value = cls._normalize(value)
        value = value.replace(" and ", " ")
        value = re.sub(r"[^a-z0-9]+", "_", value).strip("_")
        return value or "general_information"

    @staticmethod
    def _display(value: str) -> str:
        text = re.sub(r"\s+", " ", str(value or "").replace("_", " ")).strip()
        return text.title() or "General Information"

    @staticmethod
    def _yaml_quote(value: str) -> str:
        escaped = str(value).replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'