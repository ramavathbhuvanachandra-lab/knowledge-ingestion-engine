"""
Universal Knowledge Entity Discovery.

Purpose
-------
Discover institution-specific entities from structured knowledge
without relying on a fixed college taxonomy.

Important invariants
--------------------
1. College-agnostic.
2. No fixed department/school lists.
3. Entity names come from corpus evidence.
4. Discovery does not create folders.
5. Discovery is separate from taxonomy planning.
6. Strong structural signals take priority over weak signals.
7. Structural prefixes are removed where appropriate.
8. Generic words must not become entities.
9. Facility names remain complete.
10. Incomplete structural headings are rejected.
11. Textual entity discovery continues even when a heading itself
    produces a strong structural entity.
12. Entity naming is normalized without destroying the real name.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import re
from typing import Any


# ======================================================================
# ENTITY TYPES
# ======================================================================

DEPARTMENT = "department"
SCHOOL = "school"
PROGRAM = "program"
DEGREE = "degree"
RESEARCH_CENTRE = "research_centre"
FACILITY = "facility"
OFFICE = "office"
SERVICE = "service"
HOSTEL = "hostel"
ACADEMIC_UNIT = "academic_unit"
UNKNOWN = "unknown"


# ======================================================================
# DATA MODELS
# ======================================================================

@dataclass
class EntityEvidence:
    """One piece of evidence supporting an entity."""

    name: str
    entity_type: str
    source: str
    heading: str
    text: str
    score: int


@dataclass
class DiscoveredEntity:
    """Aggregated entity discovered across the corpus."""

    name: str
    normalized_name: str
    entity_type: str

    mention_count: int = 0
    confidence: str = "low"

    scores: list[int] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    headings: list[str] = field(default_factory=list)
    evidence: list[EntityEvidence] = field(default_factory=list)


# ======================================================================
# ENTITY DISCOVERY
# ======================================================================

class KnowledgeEntityDiscovery:
    """
    Discover institution-specific entities from structured knowledge.

    The system does not know the institution beforehand.

    Discovery sources:
        - headings
        - explicit declarations
        - textual mentions
        - facility patterns
        - degree/program signals

    Folder taxonomy is handled elsewhere.
    """

    # ==================================================================
    # GENERIC ENTITY INDICATORS
    # ==================================================================

    TYPE_SIGNALS = {
        DEPARTMENT: (
            "department",
            "dept",
        ),
        SCHOOL: (
            "school",
        ),
        RESEARCH_CENTRE: (
            "research centre",
            "research center",
            "research institute",
            "research laboratory",
            "research lab",
        ),
        FACILITY: (
            "facility",
            "laboratory",
            "laboratories",
            "lab",
            "workshop",
            "infrastructure",
        ),
        OFFICE: (
            "office",
            "dean",
            "registrar",
            "director",
            "administration",
            "academic affairs",
        ),
        SERVICE: (
            "service",
            "services",
            "student support",
            "student affairs",
        ),
        HOSTEL: (
            "hostel",
            "hostels",
            "residence",
            "residential",
            "hall",
            "accommodation",
        ),
        PROGRAM: (
            "program",
            "programme",
        ),
        DEGREE: (
            "bachelor",
            "master",
            "doctor of philosophy",
            "phd",
            "m.tech",
            "b.tech",
            "m.sc",
            "b.sc",
            "b.a.",
            "b.com",
            "bba",
            "mba",
            "m.com",
        ),
    }

    # ==================================================================
    # EXPLICIT DECLARATION PATTERNS
    # ==================================================================

    DECLARATION_PATTERNS = (
        (
            DEPARTMENT,
            r"\bdepartment\s+of\s+"
            r"([A-Za-z][A-Za-z0-9&,\- ]{2,80})",
        ),
        (
            SCHOOL,
            r"\bschool\s+of\s+"
            r"([A-Za-z][A-Za-z0-9&,\- ]{2,80})",
        ),
        (
            RESEARCH_CENTRE,
            r"\bresearch\s+centre\s+for\s+"
            r"([A-Za-z][A-Za-z0-9&,\- ]{2,80})",
        ),
        (
            RESEARCH_CENTRE,
            r"\bresearch\s+center\s+for\s+"
            r"([A-Za-z][A-Za-z0-9&,\- ]{2,80})",
        ),
        (
            ACADEMIC_UNIT,
            r"\bcentre\s+for\s+"
            r"([A-Za-z][A-Za-z0-9&,\- ]{2,80})",
        ),
        (
            ACADEMIC_UNIT,
            r"\bcenter\s+for\s+"
            r"([A-Za-z][A-Za-z0-9&,\- ]{2,80})",
        ),
    )

    # ==================================================================
    # DEGREE PATTERN
    # ==================================================================

    DEGREE_PATTERN = re.compile(
        r"(?<![A-Za-z])("
        r"B\.?\s*Tech\.?|"
        r"M\.?\s*Tech\.?|"
        r"B\.?\s*Sc\.?|"
        r"M\.?\s*Sc\.?|"
        r"B\.?\s*A\.?|"
        r"M\.?\s*A\.?|"
        r"B\.?\s*Com\.?|"
        r"M\.?\s*Com\.?|"
        r"BBA|"
        r"MBA|"
        r"Ph\.?\s*D\.?"
        r")(?![A-Za-z])",
        flags=re.IGNORECASE,
    )

    # ==================================================================
    # FACILITY PATTERNS
    # ==================================================================

    FACILITY_PREFIX_PATTERN = re.compile(
        r"^(?:laboratory|laboratories|lab|facility|workshop)"
        r"(?:\s+(?:of|for))?"
        r"(?:\s+.+)?$",
        flags=re.IGNORECASE,
    )

    FACILITY_SUFFIX_PATTERN = re.compile(
        r"^.+?\s+"
        r"(?:laboratory|laboratories|lab|facility|workshop)$",
        flags=re.IGNORECASE,
    )

    FACILITY_TEXT_PATTERNS = (
        re.compile(
            r"\b(?:the\s+)?"
            r"([A-Z][A-Za-z0-9&,\-]*(?:\s+[A-Z][A-Za-z0-9&,\-]*){0,8})"
            r"\s+(Laboratory|Laboratories|Lab|Facility|Workshop)\b"
        ),
        re.compile(
            r"\b(?:Laboratory|Laboratories|Lab|Facility|Workshop)"
            r"(?:\s+(?:of|for))?\s+"
            r"([A-Z][A-Za-z0-9&,\-]*(?:\s+[A-Z][A-Za-z0-9&,\-]*){0,8})"
        ),
    )

    # ==================================================================
    # NOISE
    # ==================================================================

    NOISE_TERMS = (
        "latest",
        "recent",
        "news",
        "highlight",
        "highlights",
        "announcement",
        "announcements",
        "event",
        "events",
        "notice",
        "notices",
        "faculty members",
        "faculty profile",
        "faculty profiles",
        "student list",
        "students list",
        "alumni list",
        "alumni profiles",
        "batch profile",
        "batch profiles",
    )

    # ==================================================================
    # PUBLIC API
    # ==================================================================

    def discover(
        self,
        *,
        documents: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Discover entities from structured document records.
        """

        entities: dict[
            tuple[str, str],
            DiscoveredEntity,
        ] = {}

        evidence_count = 0

        for document in documents:

            source = str(
                document.get(
                    "source",
                    "",
                )
            )

            sections = document.get(
                "sections",
                [],
            )

            if not isinstance(
                sections,
                list,
            ):
                continue

            for section in sections:

                if not isinstance(
                    section,
                    dict,
                ):
                    continue

                heading = self.clean_text(
                    str(
                        section.get(
                            "heading",
                            "",
                        )
                    )
                )

                text = self.clean_text(
                    str(
                        section.get(
                            "text",
                            "",
                        )
                    )
                )

                discoveries: list[
                    tuple[str, str, int]
                ] = []

                # ------------------------------------------------------
                # Heading discovery.
                # ------------------------------------------------------

                discoveries.extend(
                    self._discover_from_heading(
                        heading=heading,
                        text=text,
                    )
                )

                # ------------------------------------------------------
                # Explicit declarations.
                # ------------------------------------------------------

                discoveries.extend(
                    self._discover_from_declarations(
                        text=text,
                    )
                )

                # ------------------------------------------------------
                # Text discovery.
                # ------------------------------------------------------

                discoveries.extend(
                    self._discover_from_text(
                        text=text,
                    )
                )

                # ------------------------------------------------------
                # Aggregate.
                # ------------------------------------------------------

                for (
                    name,
                    entity_type,
                    score,
                ) in discoveries:

                    name = self.clean_name(
                        name
                    )

                    if not self._valid_entity_name(
                        name,
                        entity_type=entity_type,
                    ):
                        continue

                    normalized_name = (
                        self.normalize_name(
                            name
                        )
                    )

                    key = (
                        normalized_name,
                        entity_type,
                    )

                    if key not in entities:

                        entities[key] = (
                            DiscoveredEntity(
                                name=name,
                                normalized_name=(
                                    normalized_name
                                ),
                                entity_type=(
                                    entity_type
                                ),
                            )
                        )

                    entity = entities[key]

                    entity.mention_count += 1
                    entity.scores.append(
                        score
                    )

                    if source:
                        entity.sources.append(
                            source
                        )

                    if heading:
                        entity.headings.append(
                            heading
                        )

                    entity.evidence.append(
                        EntityEvidence(
                            name=name,
                            entity_type=entity_type,
                            source=source,
                            heading=heading,
                            text=text[:1000],
                            score=score,
                        )
                    )

                    evidence_count += 1

        # --------------------------------------------------------------
        # Calculate confidence.
        # --------------------------------------------------------------

        for entity in entities.values():

            entity.confidence = (
                self._confidence(
                    mention_count=(
                        entity.mention_count
                    ),
                    max_score=max(
                        entity.scores,
                        default=0,
                    ),
                )
            )

        ordered_entities = sorted(
            entities.values(),
            key=lambda entity: (
                self._type_order(
                    entity.entity_type
                ),
                entity.normalized_name,
            ),
        )

        return {
            "entity_count": len(
                ordered_entities
            ),
            "evidence_count": (
                evidence_count
            ),
            "entities": [
                self._serialize_entity(
                    entity
                )
                for entity in ordered_entities
            ],
        }

    # ==================================================================
    # HEADING DISCOVERY
    # ==================================================================

    def _discover_from_heading(
        self,
        *,
        heading: str,
        text: str,
    ) -> list[
        tuple[str, str, int]
    ]:

        results: list[
            tuple[str, str, int]
        ] = []

        heading = self.clean_name(
            heading
        )

        if not heading:
            return results

        # --------------------------------------------------------------
        # Strong structural heading.
        # --------------------------------------------------------------

        structural = (
            self._discover_structural_heading(
                heading
            )
        )

        if structural:
            results.extend(
                structural
            )

        # --------------------------------------------------------------
        # Facility heading.
        # --------------------------------------------------------------

        if self._is_facility_heading(
            heading
        ):

            if self._valid_entity_name(
                heading,
                entity_type=FACILITY,
            ):

                results.append(
                    (
                        heading,
                        FACILITY,
                        100,
                    )
                )

        # --------------------------------------------------------------
        # Program heading.
        # --------------------------------------------------------------

        if self._looks_like_program_heading(
            heading
        ):

            program_name = (
                self._program_name_from_heading(
                    heading
                )
            )

            if self._valid_entity_name(
                program_name,
                entity_type=PROGRAM,
            ):

                results.append(
                    (
                        program_name,
                        PROGRAM,
                        110,
                    )
                )

        # --------------------------------------------------------------
        # Degree heading.
        # --------------------------------------------------------------

        if (
            not structural
            and not self._is_facility_heading(
                heading
            )
        ):

            for match in (
                self.DEGREE_PATTERN.finditer(
                    heading
                )
            ):

                degree = self.clean_name(
                    match.group(1)
                )

                if degree:

                    results.append(
                        (
                            degree,
                            DEGREE,
                            95,
                        )
                    )

        return results

    # ==================================================================
    # STRUCTURAL HEADING DISCOVERY
    # ==================================================================

    def _discover_structural_heading(
        self,
        heading: str,
    ) -> list[
        tuple[str, str, int]
    ]:

        heading = self.clean_name(
            heading
        )

        # --------------------------------------------------------------
        # Department.
        # --------------------------------------------------------------

        match = re.fullmatch(
            r"department\s+of\s+(.+)",
            heading,
            flags=re.IGNORECASE,
        )

        if match:

            candidate = self.clean_name(
                match.group(1)
            )

            if self._valid_entity_name(
                candidate,
                entity_type=DEPARTMENT,
            ):

                return [
                    (
                        candidate,
                        DEPARTMENT,
                        100,
                    )
                ]

            return []

        # --------------------------------------------------------------
        # School of X.
        # --------------------------------------------------------------

        match = re.fullmatch(
            r"school\s+of\s+(.+)",
            heading,
            flags=re.IGNORECASE,
        )

        if match:

            candidate = self.clean_name(
                match.group(1)
            )

            if self._valid_entity_name(
                candidate,
                entity_type=SCHOOL,
            ):

                return [
                    (
                        candidate,
                        SCHOOL,
                        100,
                    )
                ]

            return []

        # --------------------------------------------------------------
        # School X.
        # --------------------------------------------------------------

        match = re.fullmatch(
            r"school\s+(.+)",
            heading,
            flags=re.IGNORECASE,
        )

        if match:

            candidate = self.clean_name(
                match.group(1)
            )

            if self._valid_entity_name(
                candidate,
                entity_type=SCHOOL,
            ):

                return [
                    (
                        candidate,
                        SCHOOL,
                        95,
                    )
                ]

            return []

        # --------------------------------------------------------------
        # Research centre.
        # --------------------------------------------------------------

        match = re.fullmatch(
            r"(?:research\s+)?"
            r"(?:centre|center)"
            r"(?:\s+(?:for|of))?\s+(.+)",
            heading,
            flags=re.IGNORECASE,
        )

        if match:

            candidate = self.clean_name(
                match.group(1)
            )

            if self._valid_entity_name(
                candidate,
                entity_type=RESEARCH_CENTRE,
            ):

                return [
                    (
                        candidate,
                        RESEARCH_CENTRE,
                        100,
                    )
                ]

            return []

        # --------------------------------------------------------------
        # Office.
        # --------------------------------------------------------------

        office_match = re.fullmatch(
            r"office\s+of\s+(?:the\s+)?"
            r"(dean|registrar|director|"
            r"administration|academic affairs)",
            heading,
            flags=re.IGNORECASE,
        )

        if office_match:

            return [
                (
                    self.clean_name(
                        office_match.group(1)
                    ),
                    OFFICE,
                    100,
                )
            ]

        office_match = re.fullmatch(
            r"(dean|registrar|director)"
            r"(?:\s+office)?",
            heading,
            flags=re.IGNORECASE,
        )

        if office_match:

            return [
                (
                    self.clean_name(
                        office_match.group(1)
                    ),
                    OFFICE,
                    95,
                )
            ]

        # --------------------------------------------------------------
        # Hostel.
        # --------------------------------------------------------------

        hostel_match = re.fullmatch(
            r"(?:hostel|residence|"
            r"residential\s+hall)"
            r"(?:\s+(?:of|for))?\s*(.*)",
            heading,
            flags=re.IGNORECASE,
        )

        if hostel_match:

            candidate = self.clean_name(
                hostel_match.group(1)
            )

            if candidate:

                if self._valid_entity_name(
                    candidate,
                    entity_type=HOSTEL,
                ):

                    return [
                        (
                            candidate,
                            HOSTEL,
                            90,
                        )
                    ]

            elif self._valid_entity_name(
                heading,
                entity_type=HOSTEL,
            ):

                return [
                    (
                        heading,
                        HOSTEL,
                        85,
                    )
                ]

            return []

        return []

    # ==================================================================
    # DECLARATION DISCOVERY
    # ==================================================================

    def _discover_from_declarations(
        self,
        *,
        text: str,
    ) -> list[
        tuple[str, str, int]
    ]:

        results: list[
            tuple[str, str, int]
        ] = []

        for (
            entity_type,
            pattern,
        ) in self.DECLARATION_PATTERNS:

            for match in re.finditer(
                pattern,
                text,
                flags=re.IGNORECASE,
            ):

                name = (
                    self._trim_entity_name(
                        match.group(1)
                    )
                )

                if self._valid_entity_name(
                    name,
                    entity_type=entity_type,
                ):

                    results.append(
                        (
                            name,
                            entity_type,
                            75,
                        )
                    )

        return results

    # ==================================================================
    # TEXT DISCOVERY
    # ==================================================================

    def _discover_from_text(
        self,
        *,
        text: str,
    ) -> list[
        tuple[str, str, int]
    ]:

        results: list[
            tuple[str, str, int]
        ] = []

        if not text:
            return results

        # --------------------------------------------------------------
        # Department.
        # --------------------------------------------------------------

        department_pattern = (
            r"\b(?:department|dept\.?)"
            r"\s+(?:of\s+)?"
            r"([A-Za-z][A-Za-z0-9&,\- ]{2,70})"
        )

        for match in re.finditer(
            department_pattern,
            text,
            flags=re.IGNORECASE,
        ):

            name = (
                self._trim_entity_name(
                    match.group(1)
                )
            )

            if self._valid_entity_name(
                name,
                entity_type=DEPARTMENT,
            ):

                results.append(
                    (
                        name,
                        DEPARTMENT,
                        60,
                    )
                )

        # --------------------------------------------------------------
        # School.
        # --------------------------------------------------------------

        school_pattern = (
            r"\bschool\s+(?:of\s+)?"
            r"([A-Za-z][A-Za-z0-9&,\- ]{2,70})"
        )

        for match in re.finditer(
            school_pattern,
            text,
            flags=re.IGNORECASE,
        ):

            name = (
                self._trim_entity_name(
                    match.group(1)
                )
            )

            if self._valid_entity_name(
                name,
                entity_type=SCHOOL,
            ):

                results.append(
                    (
                        name,
                        SCHOOL,
                        60,
                    )
                )

        # --------------------------------------------------------------
        # Research centre.
        # --------------------------------------------------------------

        research_pattern = (
            r"\b(?:research\s+)"
            r"(?:centre|center)"
            r"(?:\s+(?:for|of))?\s+"
            r"([A-Za-z][A-Za-z0-9&,\- ]{2,70})"
        )

        for match in re.finditer(
            research_pattern,
            text,
            flags=re.IGNORECASE,
        ):

            name = (
                self._trim_entity_name(
                    match.group(1)
                )
            )

            if self._valid_entity_name(
                name,
                entity_type=RESEARCH_CENTRE,
            ):

                results.append(
                    (
                        name,
                        RESEARCH_CENTRE,
                        60,
                    )
                )

        # --------------------------------------------------------------
        # Facilities.
        # --------------------------------------------------------------

        results.extend(
            self._discover_facilities_from_text(
                text
            )
        )

        # --------------------------------------------------------------
        # Offices.
        # --------------------------------------------------------------

        office_pattern = (
            r"\b(?:office\s+of\s+(?:the\s+)?)"
            r"(dean|registrar|director|"
            r"administration|academic affairs)\b"
        )

        for match in re.finditer(
            office_pattern,
            text,
            flags=re.IGNORECASE,
        ):

            name = self.clean_name(
                match.group(1)
            )

            if self._valid_entity_name(
                name,
                entity_type=OFFICE,
            ):

                results.append(
                    (
                        name,
                        OFFICE,
                        55,
                    )
                )

        # --------------------------------------------------------------
        # Degrees.
        # --------------------------------------------------------------

        for match in (
            self.DEGREE_PATTERN.finditer(
                text
            )
        ):

            degree = self.clean_name(
                match.group(1)
            )

            if degree:

                results.append(
                    (
                        degree,
                        DEGREE,
                        55,
                    )
                )

        return results

    # ==================================================================
    # FACILITY TEXT DISCOVERY
    # ==================================================================

    def _discover_facilities_from_text(
        self,
        text: str,
    ) -> list[
        tuple[str, str, int]
    ]:

        results: list[
            tuple[str, str, int]
        ] = []

        # --------------------------------------------------------------
        # Pattern 1:
        #
        # The Central Laboratory
        # Advanced Materials Laboratory
        # --------------------------------------------------------------

        pattern = self.FACILITY_TEXT_PATTERNS[0]

        for match in pattern.finditer(
            text
        ):

            prefix = self.clean_name(
                match.group(1)
            )

            suffix = self.clean_name(
                match.group(2)
            )

            # ----------------------------------------------------------
            # IMPORTANT:
            #
            # The regex intentionally allows "the" outside the capture,
            # but we also defensively remove it here.
            # ----------------------------------------------------------

            prefix = re.sub(
                r"^the\s+",
                "",
                prefix,
                flags=re.IGNORECASE,
            )

            candidate = self.clean_name(
                f"{prefix} {suffix}"
            )

            if self._valid_entity_name(
                candidate,
                entity_type=FACILITY,
            ):

                results.append(
                    (
                        candidate,
                        FACILITY,
                        65,
                    )
                )

        # --------------------------------------------------------------
        # Pattern 2:
        #
        # Laboratory for Renewable Energy
        # Facility for Advanced Computing
        # --------------------------------------------------------------

        pattern = self.FACILITY_TEXT_PATTERNS[1]

        for match in pattern.finditer(
            text
        ):

            prefix = self.clean_name(
                match.group(1)
            )

            suffix_match = re.search(
                r"(Laboratory|Laboratories|Lab|Facility|Workshop)",
                match.group(0),
                flags=re.IGNORECASE,
            )

            if not suffix_match:
                continue

            suffix = self.clean_name(
                suffix_match.group(1)
            )

            candidate = self.clean_name(
                f"{prefix} {suffix}"
            )

            candidate = re.sub(
                r"^the\s+",
                "",
                candidate,
                flags=re.IGNORECASE,
            )

            if self._valid_entity_name(
                candidate,
                entity_type=FACILITY,
            ):

                results.append(
                    (
                        candidate,
                        FACILITY,
                        65,
                    )
                )

        return results

    # ==================================================================
    # PROGRAM DETECTION
    # ==================================================================

    def _looks_like_program_heading(
        self,
        heading: str,
    ) -> bool:

        normalized = self.normalize_name(
            heading
        )

        if not normalized:
            return False

        return bool(
            re.search(
                r"\bprogram\b|\bprogramme\b",
                normalized,
            )
        )

    def _program_name_from_heading(
        self,
        heading: str,
    ) -> str:

        name = re.sub(
            r"\bprogram(?:me)?\b",
            "",
            heading,
            flags=re.IGNORECASE,
        )

        return self.clean_name(
            name
        )

    # ==================================================================
    # HEADING CLASSIFICATION
    # ==================================================================

    def _classify_heading_type(
        self,
        heading: str,
    ) -> str | None:

        normalized = self.normalize_name(
            heading
        )

        if not normalized:
            return None

        if re.fullmatch(
            r"school\s+of\s+.+",
            normalized,
        ):
            return SCHOOL

        if re.fullmatch(
            r"school\s+.+",
            normalized,
        ):
            return SCHOOL

        if re.fullmatch(
            r"department\s+of\s+.+",
            normalized,
        ):
            return DEPARTMENT

        if re.fullmatch(
            r"dept\s+(?:of\s+)?(.+)",
            normalized,
        ):
            return DEPARTMENT

        if re.search(
            r"\bresearch\s+(?:centre|center)\b",
            normalized,
        ):
            return RESEARCH_CENTRE

        if re.fullmatch(
            r"office\s+of\s+.+",
            normalized,
        ):
            return OFFICE

        if re.search(
            r"\bprogram\b|\bprogramme\b",
            normalized,
        ):
            return PROGRAM

        if self.DEGREE_PATTERN.search(
            heading
        ):
            return DEGREE

        return None

    # ==================================================================
    # FACILITY HEADING
    # ==================================================================

    def _is_facility_heading(
        self,
        heading: str,
    ) -> bool:

        normalized = self.clean_name(
            heading
        )

        if not normalized:
            return False

        return bool(
            self.FACILITY_PREFIX_PATTERN.fullmatch(
                normalized
            )
            or self.FACILITY_SUFFIX_PATTERN.fullmatch(
                normalized
            )
        )

    # ==================================================================
    # NORMALIZATION
    # ==================================================================

    @staticmethod
    def normalize_name(
        value: str,
    ) -> str:

        value = (
            value
            or ""
        ).lower()

        value = value.replace(
            "&",
            " and ",
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

    @staticmethod
    def clean_name(
        value: str,
    ) -> str:

        value = (
            value
            or ""
        ).strip()

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        value = value.strip(
            " :-|,.;"
        )

        return value

    @staticmethod
    def clean_text(
        value: str,
    ) -> str:

        value = (
            value
            or ""
        ).strip()

        return re.sub(
            r"\s+",
            " ",
            value,
        )

    # ==================================================================
    # ENTITY VALIDATION
    # ==================================================================

    def _is_noise(
        self,
        normalized_name: str,
    ) -> bool:

        if not normalized_name:
            return True

        if len(
            normalized_name.split()
        ) > 12:
            return True

        if self._contains_any(
            normalized_name,
            self.NOISE_TERMS,
        ):
            return True

        return False

    @staticmethod
    def _contains_any(
        text: str,
        terms: tuple[str, ...],
    ) -> bool:

        for term in terms:

            term_n = (
                KnowledgeEntityDiscovery
                .normalize_name(
                    term
                )
            )

            if (
                term_n
                and term_n in text
            ):
                return True

        return False

    def _valid_entity_name(
        self,
        name: str,
        entity_type: str | None = None,
    ) -> bool:

        name = self.clean_name(
            name
        )

        if not name:
            return False

        normalized = (
            self.normalize_name(
                name
            )
        )

        if self._is_noise(
            normalized
        ):
            return False

        # --------------------------------------------------------------
        # Structural leftovers.
        # --------------------------------------------------------------

        if normalized in {
            "of",
            "the",
            "for",
            "and",
            "or",
        }:
            return False

        # --------------------------------------------------------------
        # Incomplete structural headings.
        # --------------------------------------------------------------

        if normalized in {
            "school of",
            "department of",
            "dept of",
            "school",
            "department",
            "dept",
        }:
            return False

        words = normalized.split()

        if not words:
            return False

        if len(words) > 10:
            return False

        # --------------------------------------------------------------
        # Reject generic structural words as entities.
        # --------------------------------------------------------------

        if entity_type in {
            SCHOOL,
            DEPARTMENT,
            RESEARCH_CENTRE,
            FACILITY,
        }:

            if len(words) == 1 and words[0] in {
                "school",
                "department",
                "facility",
                "laboratory",
                "laboratories",
                "lab",
                "centre",
                "center",
                "workshop",
            }:
                return False

        return True

    # ==================================================================
    # TEXT TRIMMING
    # ==================================================================

    @staticmethod
    def _trim_entity_name(
        value: str,
    ) -> str:

        value = value.strip()

        stop_patterns = (
            r"\s+(?:offers|provides|has|"
            r"is|are|was|were|supports|"
            r"support|includes|include)\b.*$",

            r"\s+(?:with|where|which|that)\b.*$",

            r"\s*[\.:;].*$",
        )

        for pattern in stop_patterns:

            value = re.sub(
                pattern,
                "",
                value,
                flags=re.IGNORECASE,
            )

        return value.strip()

    # ==================================================================
    # CONFIDENCE
    # ==================================================================

    @staticmethod
    def _confidence(
        *,
        mention_count: int,
        max_score: int,
    ) -> str:

        if (
            max_score >= 100
            and mention_count >= 2
        ):
            return "high"

        if max_score >= 75:
            return "high"

        if (
            max_score >= 50
            and mention_count >= 2
        ):
            return "medium"

        return "low"

    # ==================================================================
    # SORTING
    # ==================================================================

    @staticmethod
    def _type_order(
        entity_type: str,
    ) -> int:

        order = {
            DEPARTMENT: 1,
            SCHOOL: 2,
            ACADEMIC_UNIT: 3,
            PROGRAM: 4,
            DEGREE: 5,
            RESEARCH_CENTRE: 6,
            FACILITY: 7,
            OFFICE: 8,
            SERVICE: 9,
            HOSTEL: 10,
            UNKNOWN: 99,
        }

        return order.get(
            entity_type,
            99,
        )

    # ==================================================================
    # SERIALIZATION
    # ==================================================================

    @staticmethod
    def _serialize_entity(
        entity: DiscoveredEntity,
    ) -> dict[str, Any]:

        return asdict(
            entity
        )