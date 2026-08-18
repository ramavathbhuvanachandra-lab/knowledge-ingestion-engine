"""
Universal deterministic semantic signal engine.

Purpose
-------
Determine what kind of knowledge a record represents.

Evidence scopes
---------------
1. Record heading
2. Record body
3. Section context
4. Document context

Precedence
----------
Record > Section > Document

Important
---------
Section/document context cannot create a primary record identity.

The production engine is:
- college-agnostic
- website-agnostic
- deterministic
- explainable
- LLM-free
"""

from __future__ import annotations

from dataclasses import dataclass
import re


# ======================================================================
# RULE MODEL
# ======================================================================


@dataclass(frozen=True)
class SemanticRule:
    """
    One universal semantic rule.
    """

    name: str

    phrase_weights: dict[str, int]

    weak_record_contexts: tuple[str, ...] = ()

    contextual_heading_terms: tuple[str, ...] = ()


# ======================================================================
# UNIVERSAL RULES
# ======================================================================

RULES = (

    # ------------------------------------------------------------------
    # RESEARCH
    # ------------------------------------------------------------------

    SemanticRule(
        name="research",
        phrase_weights={
            "sponsored research project": 120,
            "sponsored research": 110,
            "international research project": 115,
            "research project": 100,
            "research projects": 100,
            "research grant": 100,
            "research initiative": 90,
            "research programme": 90,
            "research program": 90,
        },
        weak_record_contexts=(
            "student profile",
            "student profiles",
            "batch profile",
            "batch profiles",
            "faculty profile",
            "faculty profiles",
            "directory",
            "directories",
            "contact",
            "contacts",
        ),
        contextual_heading_terms=(
            "research",
            "research project",
            "research projects",
        ),
    ),

    # ------------------------------------------------------------------
    # CONSULTANCY
    # ------------------------------------------------------------------

    SemanticRule(
        name="consultancy",
        phrase_weights={
            "consultancy engagement": 120,
            "consultancy project": 120,
            "technical consultancy": 115,
            "consulting project": 110,
            "consulting assignment": 110,
            "consultancy": 90,
        },
        weak_record_contexts=(
            "student profile",
            "student profiles",
            "batch profile",
            "batch profiles",
            "faculty profile",
            "faculty profiles",
            "biography",
            "directory",
            "directories",
            "contact",
            "contacts",
        ),
        contextual_heading_terms=(
            "consultancy",
            "consulting",
            "external engagement",
            "external project",
            "industry project",
            "project",
            "projects",
        ),
    ),

    # ------------------------------------------------------------------
    # FELLOWSHIP
    # ------------------------------------------------------------------

    SemanticRule(
        name="fellowship",
        phrase_weights={
            "doctoral fellowship": 120,
            "research fellowship": 115,
            "academic fellowship": 110,
            "fellowship project": 110,
            "fellowship grant": 110,
            "fellowship": 80,
        },
        contextual_heading_terms=(
            "fellowship",
            "fellowships",
            "research",
            "funding",
        ),
    ),

    # ------------------------------------------------------------------
    # TRAVEL
    # ------------------------------------------------------------------

    SemanticRule(
        name="travel",
        phrase_weights={
            "international travel support": 125,
            "travel support": 120,
            "travel grant": 120,
            "travel assistance": 110,
            "conference travel": 110,
            "travel fellowship": 110,
        },
        contextual_heading_terms=(
            "travel",
            "support",
            "activity",
            "activities",
            "conference",
        ),
    ),

    # ------------------------------------------------------------------
    # WORKSHOP
    # ------------------------------------------------------------------

    SemanticRule(
        name="workshop",
        phrase_weights={
            "training workshop": 115,
            "academic workshop": 115,
            "technical workshop": 115,
            "workshop": 90,
            "workshops": 90,
        },
        weak_record_contexts=(
            "student profile",
            "student profiles",
            "batch profile",
            "batch profiles",
            "faculty profile",
            "faculty profiles",
        ),
        contextual_heading_terms=(
            "event",
            "events",
            "academic event",
            "academic events",
            "activity",
            "activities",
            "training",
            "workshop",
        ),
    ),

    # ------------------------------------------------------------------
    # SYMPOSIA / CONFERENCE
    # ------------------------------------------------------------------

    SemanticRule(
        name="symposia",
        phrase_weights={
            "international symposium": 115,
            "symposium": 90,
            "symposia": 90,
            "seminar": 80,
            "seminars": 80,
            "conference": 80,
            "conferences": 80,
        },
        weak_record_contexts=(
            "student profile",
            "student profiles",
            "batch profile",
            "batch profiles",
        ),
        contextual_heading_terms=(
            "event",
            "events",
            "academic event",
            "academic events",
            "activity",
            "activities",
            "conference",
            "seminar",
            "symposium",
        ),
    ),

    # ------------------------------------------------------------------
    # PROGRAM
    # ------------------------------------------------------------------

    SemanticRule(
        name="program",
        phrase_weights={
            "online executive programme": 120,
            "online executive program": 120,
            "postgraduate programme": 120,
            "postgraduate program": 120,
            "undergraduate programme": 120,
            "undergraduate program": 120,
            "doctoral programme": 120,
            "doctoral program": 120,
            "degree programme": 110,
            "degree program": 110,
            "academic programme": 110,
            "academic program": 110,
        },
        weak_record_contexts=(
            "student profile",
            "student profiles",
            "batch profile",
            "batch profiles",
            "faculty profile",
            "faculty profiles",
        ),
        contextual_heading_terms=(
            "program",
            "programme",
            "degree",
            "academic",
            "curriculum",
            "postgraduate",
            "undergraduate",
            "doctoral",
        ),
    ),

    # ------------------------------------------------------------------
    # ADMISSION
    # ------------------------------------------------------------------

    SemanticRule(
        name="admission",
        phrase_weights={
            "phd admissions": 125,
            "ph d admissions": 125,
            "doctoral admissions": 125,
            "admission process": 110,
            "admission notice": 110,
            "application process": 110,
            "application procedure": 110,
            "eligibility criteria": 110,
            "admissions": 85,
            "admission": 80,
        },
        weak_record_contexts=(
            "student profile",
            "student profiles",
            "batch profile",
            "batch profiles",
        ),
        contextual_heading_terms=(
            "admission",
            "admissions",
            "application",
            "eligibility",
            "applicant",
            "notice",
        ),
    ),

    # ------------------------------------------------------------------
    # PLACEMENT
    # ------------------------------------------------------------------

    SemanticRule(
        name="placement",
        phrase_weights={
            "campus placement": 115,
            "career placement": 115,
            "placement drive": 115,
            "recruitment drive": 115,
            "placements": 80,
            "placement": 80,
        },
        weak_record_contexts=(
            "student profile",
            "student profiles",
            "faculty profile",
            "faculty profiles",
        ),
        contextual_heading_terms=(
            "placement",
            "placements",
            "career",
            "recruitment",
            "employment",
        ),
    ),

    # ------------------------------------------------------------------
    # SCHOLARSHIP
    # ------------------------------------------------------------------

    SemanticRule(
        name="scholarship",
        phrase_weights={
            "student financial aid": 110,
            "financial assistance": 110,
            "fee waiver": 110,
            "scholarships": 80,
            "scholarship": 70,
        },
        weak_record_contexts=(
            "about the institute",
            "about the institution",
            "institute overview",
            "institution overview",
            "overview",
            "mission",
            "vision",
        ),
        contextual_heading_terms=(
            "scholarship",
            "scholarships",
            "financial aid",
            "financial assistance",
            "student support",
        ),
    ),

    # ------------------------------------------------------------------
    # FACULTY
    # ------------------------------------------------------------------

    SemanticRule(
        name="faculty",
        phrase_weights={
            "faculty profile": 100,
            "faculty members": 95,
            "faculty member": 95,
            "assistant professor": 100,
            "associate professor": 100,
            "professors": 65,
            "professor": 60,
        },
        weak_record_contexts=(
            "admission",
            "admissions",
            "admission notice",
            "application",
            "student profile",
            "student profiles",
            "batch profile",
            "batch profiles",
            "overview",
        ),
        contextual_heading_terms=(
            "faculty",
            "faculty profile",
            "faculty members",
            "professor",
            "academic staff",
        ),
    ),

    # ------------------------------------------------------------------
    # FACILITY
    # ------------------------------------------------------------------

    SemanticRule(
        name="facility",
        phrase_weights={
            "research laboratory": 110,
            "research lab": 110,
            "laboratories": 95,
            "laboratory": 90,
            "facilities": 85,
            "facility": 80,
            "infrastructure": 55,
        },
        weak_record_contexts=(
            "department",
            "departments",
            "directory",
            "directories",
            "office",
            "offices",
            "administration",
            "administrative",
            "overview",
        ),
        contextual_heading_terms=(
            "facility",
            "facilities",
            "laboratory",
            "laboratories",
            "lab",
            "infrastructure",
            "equipment",
        ),
    ),
)


# ======================================================================
# ENGINE
# ======================================================================


class KnowledgeSemanticSignalEngine:
    """
    Scope-aware deterministic semantic engine.

    Record evidence is the source of primary identity.

    Section context can support record evidence.

    Document context is retained as audit evidence only.
    """

    RECORD_HEADING_MULTIPLIER = 4

    # Contextual heading support.
    CONTEXTUAL_HEADING_BOOST = 40

    # Section supports record interpretation but never creates
    # classification by itself.
    SECTION_MULTIPLIER = 1

    HIGH_SCORE = 80
    MEDIUM_SCORE = 50

    HIGH_MARGIN = 25
    MEDIUM_MARGIN = 10

    # ==================================================================
    # PUBLIC API
    # ==================================================================

    def analyze(
        self,
        *,
        record_heading: str,
        record_text: str,
        section_context: (
            str
            | list[str]
            | tuple[str, ...]
            | None
        ) = None,
        document_title: str = "",
    ) -> dict:
        """
        Analyze one knowledge record.
        """

        heading = self._normalize(
            record_heading
        )

        text = self._normalize(
            record_text
        )

        section = self._normalize_context(
            section_context
        )

        document = self._normalize(
            document_title
        )

        evidence = self._collect_evidence(
            record_heading=heading,
            record_text=text,
            section_context=section,
            document_title=document,
        )

        if not evidence:
            return self._unknown()

        # --------------------------------------------------------------
        # PRIMARY CANDIDATES MUST HAVE RECORD EVIDENCE
        # --------------------------------------------------------------

        candidates = [
            (name, data)
            for name, data in evidence.items()
            if data["record_score"] > 0
        ]

        if not candidates:
            return {
                "primary_type": "unknown",
                "secondary_types": [],
                "confidence": "low",
                "matched_signals": self._matched_signals(
                    evidence
                ),
            }

        ranked = sorted(
            candidates,
            key=lambda item: (
                -item[1]["record_score"],
                item[0],
            ),
        )

        primary_type, primary_data = ranked[0]

        primary_score = (
            primary_data["record_score"]
        )

        # --------------------------------------------------------------
        # SECONDARY TYPES
        # --------------------------------------------------------------

        secondary_types = [
            name
            for name, data in ranked[1:]
            if data["record_score"]
            >= self.MEDIUM_SCORE
        ]

        second_score = (
            ranked[1][1]["record_score"]
            if len(ranked) > 1
            else 0
        )

        confidence = self._confidence(
            primary_score=primary_score,
            second_score=second_score,
        )

        return {
            "primary_type": primary_type,
            "secondary_types": secondary_types,
            "confidence": confidence,
            "matched_signals": self._matched_signals(
                evidence
            ),
        }

    # ==================================================================
    # EVIDENCE
    # ==================================================================

    def _collect_evidence(
        self,
        *,
        record_heading: str,
        record_text: str,
        section_context: list[str],
        document_title: str,
    ) -> dict[str, dict]:
        """
        Collect semantic evidence by scope.
        """

        evidence: dict[str, dict] = {}

        section_text = " ".join(
            section_context
        )

        for rule in RULES:

            heading_matches = self._find_matches(
                source=record_heading,
                phrase_weights=rule.phrase_weights,
            )

            record_matches = self._find_matches(
                source=record_text,
                phrase_weights=rule.phrase_weights,
            )

            section_matches = self._find_matches(
                source=section_text,
                phrase_weights=rule.phrase_weights,
            )

            document_matches = self._find_matches(
                source=document_title,
                phrase_weights=rule.phrase_weights,
            )

            if not (
                heading_matches
                or record_matches
                or section_matches
                or document_matches
            ):
                continue

            record_score = 0

            matched_signals = []

            # ----------------------------------------------------------
            # RECORD HEADING
            # ----------------------------------------------------------

            for phrase in heading_matches:

                record_score += (
                    rule.phrase_weights[
                        phrase
                    ]
                    * self.RECORD_HEADING_MULTIPLIER
                )

                matched_signals.append(
                    phrase
                )

            # ----------------------------------------------------------
            # CONTEXTUAL HEADING BOOST
            # ----------------------------------------------------------

            if (
                self._contains_context_family(
                    source=record_heading,
                    terms=rule.contextual_heading_terms,
                )
            ):
                record_score += (
                    self.CONTEXTUAL_HEADING_BOOST
                )

            # ----------------------------------------------------------
            # RECORD BODY
            # ----------------------------------------------------------

            structured_record = (
                self._looks_structured_record(
                    record_text
                )
            )

            for phrase in record_matches:

                weight = rule.phrase_weights[
                    phrase
                ]

                # Strong phrases can identify a record directly.
                if weight >= 100:

                    record_score += weight

                # Weaker phrases such as:
                #
                #     consultancy
                #     workshop
                #     conference
                #
                # can identify a record when the record itself has
                # structural or contextual support.
                elif (
                    structured_record
                    or heading_matches
                    or self._contains_context_family(
                        source=record_heading,
                        terms=(
                            rule.contextual_heading_terms
                        ),
                    )
                ):

                    record_score += weight

                # Always preserve the evidence.
                matched_signals.append(
                    phrase
                )

            # ----------------------------------------------------------
            # WEAK RECORD CONTEXT
            # ----------------------------------------------------------

            weak_record_context = (
                self._contains_context_family(
                    source=record_heading,
                    terms=rule.weak_record_contexts,
                )
            )

            has_strong_record_phrase = (
                self._has_strong_phrase(
                    matches=record_matches,
                    rule=rule,
                )
            )

            if (
                weak_record_context
                and not heading_matches
                and not has_strong_record_phrase
            ):
                record_score = 0

            # ----------------------------------------------------------
            # SECTION SUPPORT
            # ----------------------------------------------------------

            section_score = 0

            for phrase in section_matches:

                section_score += (
                    rule.phrase_weights[
                        phrase
                    ]
                    * self.SECTION_MULTIPLIER
                )

                matched_signals.append(
                    phrase
                )

            # ----------------------------------------------------------
            # DOCUMENT EVIDENCE
            # ----------------------------------------------------------

            matched_signals.extend(
                document_matches
            )

            evidence[
                rule.name
            ] = {
                "record_score": max(
                    record_score,
                    0,
                ),
                "section_score": (
                    section_score
                ),
                "record_evidence": (
                    record_score > 0
                ),
                "matched_phrases": list(
                    dict.fromkeys(
                        matched_signals
                    )
                ),
            }

        return evidence

    # ==================================================================
    # STRUCTURED RECORD
    # ==================================================================

    def _looks_structured_record(
        self,
        text: str,
    ) -> bool:
        """
        Detect generic institutional record structure.

        This is universal and contains no college-specific names.
        """

        hints = (
            "project",
            "projects",
            "sponsor",
            "funding",
            "grant",
            "department",
            "school",
            "centre",
            "center",
            "investigator",
            "principal investigator",
            "pi",
            "amount",
            "award",
        )

        for hint in hints:

            normalized_hint = self._normalize(
                hint
            )

            pattern = (
                r"(?<![a-z0-9])"
                + re.escape(
                    normalized_hint
                )
                + r"(?![a-z0-9])"
            )

            if re.search(
                pattern,
                text,
            ):
                return True

        return False

    # ==================================================================
    # STRONG PHRASE
    # ==================================================================

    def _has_strong_phrase(
        self,
        matches: list[str],
        rule: SemanticRule,
    ) -> bool:
        """
        Check whether a strong record phrase exists.
        """

        return any(
            rule.phrase_weights.get(
                phrase,
                0,
            )
            >= 100
            for phrase in matches
        )

    # ==================================================================
    # CONTEXT FAMILY
    # ==================================================================

    def _contains_context_family(
        self,
        *,
        source: str,
        terms: tuple[str, ...],
    ) -> bool:
        """
        Determine whether a generic contextual term is present.
        """

        if not source:
            return False

        for term in terms:

            normalized_term = self._normalize(
                term
            )

            if not normalized_term:
                continue

            pattern = (
                r"(?<![a-z0-9])"
                + re.escape(
                    normalized_term
                )
                + r"(?![a-z0-9])"
            )

            if re.search(
                pattern,
                source,
            ):
                return True

        return False

    # ==================================================================
    # MATCHING
    # ==================================================================

    def _find_matches(
        self,
        *,
        source: str,
        phrase_weights: dict[str, int],
    ) -> list[str]:
        """
        Deterministic exact phrase matching.
        """

        if not source:
            return []

        matches = []

        for phrase in phrase_weights:

            normalized_phrase = (
                self._normalize(
                    phrase
                )
            )

            pattern = (
                r"(?<![a-z0-9])"
                + re.escape(
                    normalized_phrase
                )
                + r"(?![a-z0-9])"
            )

            if re.search(
                pattern,
                source,
            ):
                matches.append(
                    normalized_phrase
                )

        return matches

    # ==================================================================
    # CONFIDENCE
    # ==================================================================

    def _confidence(
        self,
        *,
        primary_score: int,
        second_score: int,
    ) -> str:
        """
        Determine confidence from record-level evidence.
        """

        margin = (
            primary_score
            - second_score
        )

        if (
            primary_score
            >= self.HIGH_SCORE
            and margin
            >= self.HIGH_MARGIN
        ):
            return "high"

        if (
            primary_score
            >= self.MEDIUM_SCORE
            and margin
            >= self.MEDIUM_MARGIN
        ):
            return "medium"

        return "low"

    # ==================================================================
    # MATCHED SIGNALS
    # ==================================================================

    def _matched_signals(
        self,
        evidence: dict[str, dict],
    ) -> list[str]:
        """
        Preserve all semantic evidence.
        """

        return sorted(
            {
                phrase
                for data in evidence.values()
                for phrase in data[
                    "matched_phrases"
                ]
            }
        )

    # ==================================================================
    # NORMALIZATION
    # ==================================================================

    def _normalize_context(
        self,
        context: (
            str
            | list[str]
            | tuple[str, ...]
            | None
        ),
    ) -> list[str]:

        if context is None:
            return []

        if isinstance(
            context,
            str,
        ):
            values = [context]
        else:
            values = list(context)

        return [
            self._normalize(value)
            for value in values
            if self._normalize(value)
        ]

    def _unknown(self) -> dict:
        return {
            "primary_type": "unknown",
            "secondary_types": [],
            "confidence": "low",
            "matched_signals": [],
        }

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