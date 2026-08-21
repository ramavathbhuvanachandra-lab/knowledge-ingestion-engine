"""
Final production-grade deterministic value classifier.

Decision order is strict:
    1. unusable/UI/OCR
    2. hard document genre
    3. structural record detection
    4. family detection with heading-first precedence
    5. publication fingerprint
    6. freshness/archive guard
    7. A/B family tier
    8. C
    9. narrow REVIEW
    10. D fallback

Important invariants:
- Document purpose beats incidental body keywords.
- A source filename can corroborate but never create a family by itself.
- A research paper never becomes a department/faculty/rules page merely because
  it contains those words.
- Research Areas/Research Centre pages remain valid institutional knowledge.
- Heading semantics outrank broad document-title/source semantics.
"""

from __future__ import annotations

import re
from typing import Any

from urllib.parse import unquote

from processors.knowledge_value_policy import (
    CORE_FAMILIES,
    CURRENT_YEAR_WORDS,
    FAMILY_SIGNALS,
    HARD_EXCLUDE_GENRES,
    HISTORICAL_WORDS,
    INSTITUTIONAL_INTENT,
    LOW_PRIORITY_EXTRA,
    PUBLICATION_BODY_SIGNALS,
    RECORD_SIGNALS,
    UI_SIGNALS,
    VOLATILE_PRIMARY_GENRES,
)


class KnowledgeValueClassifier:

    def classify(
        self,
        *,
        heading: str = "",
        text: str = "",
        source_name: str = "",
        document_title: str = "",
        document_url: str = "",
        content_type: str = "",
        section_path: list[str] | None = None,
        record_index: int | None = None,
        record_count: int | None = None,
    ) -> dict[str, Any]:

        section_path = section_path or []

        h = self._normalize(heading)
        t = self._normalize(text)
        title = self._normalize(document_title)
        source = self._normalize(source_name)
        url = self._normalize(document_url)

        metadata = self._normalize(
            " ".join(
                [heading, document_title, source_name, " ".join(section_path)]
            )
        )

        signals: dict[str, Any] = {}

        # --------------------------------------------------------------
        # 1. Unusable / UI / OCR
        # --------------------------------------------------------------
        if not text.strip():
            return self._result(
                "EXCLUDE", "high", -800, ["No usable content."],
                signals, "D", "D / Excluded", "empty"
            )

        if content_type.lower() in {"navigation", "accessibility", "ui"}:
            return self._result(
                "EXCLUDE", "high", -800, ["Navigation/UI content."],
                signals, "D", "D / Excluded", "ui_noise"
            )

        if self._has_ui_noise(h, t):
            return self._result(
                "EXCLUDE", "high", -800, ["Navigation/UI feedback content."],
                signals, "D", "D / Excluded", "ui_noise"
            )

        if self._is_ocr_noise(t):
            return self._result(
                "EXCLUDE", "high", -750, ["OCR/scanning/noise fragment."],
                signals, "D", "D / Excluded", "ocr_noise"
            )

        # --------------------------------------------------------------
        # 2. Hard document genre — before family detection
        # --------------------------------------------------------------
        genre_evidence = " ".join([metadata, source, url])
        hard_hits = self._find(genre_evidence, HARD_EXCLUDE_GENRES)
        signals["hard_exclude_genres"] = hard_hits

        if hard_hits:
            return self._result(
                "EXCLUDE", "high", -900,
                ["Excluded document genre: " + ", ".join(hard_hits[:8])],
                signals, "D", "D / Excluded", "excluded_genre"
            )

        activity_hits = self._find(
            t,
            (
                "number of participants", "ncc cadets", "mission shakti",
                "swachh bharat", "statue cleaning programme",
                "competition & training programme", "competition and training programme",
                "training programme under", "cultural programme", "nss activity",
            ),
        )
        signals["activity_hits"] = activity_hits
        if activity_hits and self._looks_like_activity_document(t, metadata):
            return self._result(
                "EXCLUDE", "high", -850,
                ["Primary content is an event/activity/programme record."],
                signals, "D", "D / Excluded", "activity_record"
            )

        # --------------------------------------------------------------
        # 3. Structural record detection
        # --------------------------------------------------------------
        record_hits = self._find(t, RECORD_SIGNALS)
        signals["record_signals"] = record_hits

        table_shape = t.count("|") >= 4
        table_header_shape = (
            table_shape
            and any(x in t for x in ("name", "student", "alumni"))
            and any(x in t for x in ("roll no", "roll number", "registration number", "batch"))
        )

        alumni_shape = (
            ("alumni name" in t and "year of graduation" in t)
            or ("current job role" in t and "year of graduation" in t)
        )

        student_shape = (
            (
                ("student name" in t or "name of student" in t)
                and any(x in t for x in ("roll number", "roll no", "registration number", "batch"))
            )
            or ("current students" in t and table_shape)
            or ("graduated students" in t and table_shape)
            or table_header_shape
        )

        personal_profile = (
            "name:" in t
            and any(x in t for x in ("email:", "phone:"))
            and any(x in t for x in ("supervisor:", "advisor:", "roll number", "registration number"))
        )

        project_shape = (
            len(
                self._find(
                    t,
                    ("project title", "project name", "principal investigator", "funding agency", "funding amount", "co-pi"),
                )
            ) >= 2
        )

        signals["record_shape"] = {
            "alumni": alumni_shape,
            "student": student_shape,
            "personal_profile": personal_profile,
            "project": project_shape,
            "table_record": table_header_shape,
        }

        # Filename/source corroboration for common rosters when the body has
        # a person-table shape but weak labels.
        source_record = any(
            token in source
            for token in (
                "student list", "students", "student roster", "b tech student",
                "phd student", "phd scholars", "alumni", "admission list",
                "merit list", "result sheet", "student results",
            )
        ) and (table_shape or len(record_hits) >= 1)

        signals["source_record"] = source_record

        if alumni_shape or student_shape or personal_profile or project_shape or source_record:
            return self._result(
                "EXCLUDE", "high", -900,
                ["Personal, student, alumni, roster, result, or project-record content."],
                signals, "D", "D / Excluded", "record"
            )

        # --------------------------------------------------------------
        # 4. Family detection — heading first, then title, then body/source
        # --------------------------------------------------------------
        family, family_hits, family_strength = self._detect_family(
            h, title, source, t
        )
        signals["family_hits"] = family_hits
        signals["family_strength"] = family_strength

        # --------------------------------------------------------------
        # 5. Publication fingerprint
        # --------------------------------------------------------------
        publication_hits = self._find(t, PUBLICATION_BODY_SIGNALS)
        publication_fingerprint = self._publication_fingerprint(t, metadata)
        signals["publication_body"] = publication_hits
        signals["publication_fingerprint"] = publication_fingerprint

        # A research-info family is allowed when the identity is explicit.
        explicit_research_identity = (
            family == "Relevant Institutional Research"
            and family_strength in {"explicit", "strong"}
        )

        if (
            (len(publication_hits) >= 2 or publication_fingerprint >= 3)
            and not explicit_research_identity
        ):
            return self._result(
                "EXCLUDE", "high", -850,
                ["Publication/book-like structure without stable institutional identity."],
                signals, "D", "D / Excluded", "publication"
            )

        # --------------------------------------------------------------
        # 6. Freshness/archive guard
        # --------------------------------------------------------------
        historical = self._historical_years(metadata)
        current = self._current_years(metadata)
        if self._contains_old_year(metadata):
            historical.append("old_year")
        signals["historical_years"] = historical
        signals["current_years"] = current

        if (
            historical
            and not current
            and family in {
                "Admissions",
                "Academics",
                "Fees / Financial Information",
                "Hostel / Accommodation",
                "Placements / Careers",
                "Scholarships / Financial Aid",
            }
            and self._looks_like_time_sensitive_archive(h, title, source)
        ):
            return self._result(
                "EXCLUDE", "high", -650,
                ["Historical version of a time-sensitive institutional topic."],
                signals, "D", "D / Excluded", "historical_archive"
            )

        # --------------------------------------------------------------
        # 7. Volatile primary identity
        # --------------------------------------------------------------
        volatile_hits = self._find(genre_evidence, VOLATILE_PRIMARY_GENRES)
        signals["volatile_primary_hits"] = volatile_hits

        if volatile_hits:
            stable_exception = (
                family in CORE_FAMILIES
                and family_strength in {"explicit", "strong"}
                and not self._looks_like_event_page(h, title)
            )
            if not stable_exception:
                return self._result(
                    "EXCLUDE", "high", -800,
                    ["Primary identity is news/event/award/newsletter/volatile activity."],
                    signals, "D", "D / Excluded", "volatile"
                )

        # --------------------------------------------------------------
        # 8. Family tiering
        # --------------------------------------------------------------
        if family in CORE_FAMILIES:
            if family_strength in {"explicit", "strong"}:
                return self._result(
                    "KEEP", "high", 180,
                    [f"Core assistant family: {family}."],
                    signals, "A", family, "core_family"
                )

            if family_strength == "supporting" and self._supporting_is_safe(
                family, t, family_hits, historical, current
            ):
                return self._result(
                    "KEEP", "medium", 110,
                    [f"Important institutional knowledge: {family}."],
                    signals, "B", family, "supporting_family"
                )

        # --------------------------------------------------------------
        # 9. C — legitimate but lower-priority extras
        # --------------------------------------------------------------
        low_hits = self._find(metadata, LOW_PRIORITY_EXTRA)
        signals["low_priority_extra"] = low_hits
        if low_hits:
            return self._result(
                "CONSOLIDATE", "high", 30,
                ["Legitimate institutional material outside the 15 core families."],
                signals, "C", "Other Institutional Information", "low_priority_extra"
            )

        # --------------------------------------------------------------
        # 10. REVIEW — deliberately narrow
        # --------------------------------------------------------------
        review_score = self._review_score(h, title, t)
        signals["review_score"] = review_score
        if review_score >= 4:
            return self._result(
                "REVIEW", "low", 20,
                ["Potentially useful institutional information without a confident 15-family match."],
                signals, "REVIEW", "Potential Institutional Information", "review"
            )

        return self._result(
            "EXCLUDE", "medium", -400,
            ["Does not fit the stable college-assistant knowledge scope."],
            signals, "D", "D / Excluded", "out_of_scope"
        )

    # ------------------------------------------------------------------
    # Family detection
    # ------------------------------------------------------------------
    def _detect_family_from_text(self, text: str):
        candidates = []
        for family, terms in FAMILY_SIGNALS.items():
            hits = self._find(text, terms)
            if hits:
                candidates.append((len(hits), family, hits))
        if not candidates:
            return "Other", [], "none"
        candidates.sort(key=lambda x: (-x[0], x[1]))
        count, family, hits = candidates[0]
        return family, hits, ("explicit" if count >= 2 else "strong")

    def _detect_family_from_metadata(self, heading: str, title: str):
        # Heading wins. Within a field, the most specific phrase wins.
        for field in (heading, title):
            if not field:
                continue
            matches = []
            for family, terms in FAMILY_SIGNALS.items():
                for term in terms:
                    normalized = self._normalize(term)
                    if normalized in field:
                        matches.append((len(normalized), family, term))
            if matches:
                matches.sort(key=lambda x: (-x[0], x[1]))
                _, family, best_term = matches[0]
                return family, [best_term], "explicit"
        return "Other", [], "none"

    def _detect_family(self, heading: str, title: str, source: str, text: str):
        if "about research" in heading or "research areas" in heading or "current research areas" in heading or "major research areas" in heading:
            return "Relevant Institutional Research", ["research heading"], "explicit"

        family, hits, strength = self._detect_family_from_metadata(heading, title)
        if family != "Other":
            return family, hits, strength

        # Body + source corroboration; source alone never creates a family.
        candidates = []
        for family_name, terms in FAMILY_SIGNALS.items():
            body_hits = self._find(text, terms)
            source_hits = self._find(source, terms)
            if body_hits and source_hits:
                candidates.append((len(body_hits) * 10 + len(source_hits), family_name, body_hits + source_hits))
        if candidates:
            candidates.sort(key=lambda x: (-x[0], x[1]))
            _, family_name, hits = candidates[0]
            return family_name, hits, "supporting"

        # Body-only classification is restricted to distinctive families.
        body_candidates = []
        distinctive = {
            "Relevant Institutional Research",
            "Rules & Regulations / Policies",
            "Hostel / Accommodation",
            "Important Contacts / Emergency",
            "Student Services / Welfare",
            "Scholarships / Financial Aid",
            "Placements / Careers",
        }
        for family_name, terms in FAMILY_SIGNALS.items():
            body_hits = self._find(text, terms)
            if body_hits and family_name in distinctive:
                body_candidates.append((len(body_hits), family_name, body_hits))
        if body_candidates:
            body_candidates.sort(key=lambda x: (-x[0], x[1]))
            count, family_name, hits = body_candidates[0]
            if count >= 3:
                return family_name, hits, "supporting"
        return "Other", [], "none"

    def _looks_like_research_heading(self, heading: str) -> bool:
        return self._contains(
            heading,
            ("about research", "research", "research areas", "research centre", "research center", "major research areas", "current research areas")
        ) and not self._contains(heading, ("department of", "school of"))

    def _research_heading_match(self, heading: str):
        matches = []
        for term in FAMILY_SIGNALS["Relevant Institutional Research"]:
            if self._normalize(term) in heading:
                matches.append(term)
        if matches:
            return "Relevant Institutional Research", matches, ("explicit" if len(matches) >= 2 else "strong")
        return None, [], "none"

    def _supporting_is_safe(self, family, text, hits, historical, current):
        if len(hits) < 2:
            return False
        if len(self._find(text, INSTITUTIONAL_INTENT)) < 1:
            return False
        dangerous = (
            "journal", "article", "paper", "workshop", "seminar", "conference", "proceedings",
            "survey", "feedback", "action taken report", "audit report", "aishe", "nss activity", "ncc activity",
        )
        if sum(1 for term in dangerous if term in text) >= 2:
            return False
        if historical and not current and self._looks_like_time_sensitive_archive(text, "", ""):
            return False
        return True

    # ------------------------------------------------------------------
    # Publication, freshness, review
    # ------------------------------------------------------------------
    def _publication_fingerprint(self, text: str, metadata: str) -> int:
        signals = (
            "issn", "isbn", "doi", "journal", "volume", "issue", "abstract", "references",
            "original article", "research article", "published by", "elsevier", "springer",
            "wiley", "taylor & francis",
        )
        score = sum(1 for s in signals if s in text or s in metadata)
        if "research paper" in metadata:
            score += 2
        return score

    def _historical_years(self, text: str) -> list[str]:
        return self._find(text, HISTORICAL_WORDS)

    def _current_years(self, text: str) -> list[str]:
        return self._find(text, CURRENT_YEAR_WORDS)

    def _contains_old_year(self, text: str) -> bool:
        years = [int(x) for x in re.findall(r"\b(?:19|20)\d{2}\b", text)]
        return any(y <= 2024 for y in years)

    def _looks_like_activity_document(self, text: str, metadata: str) -> bool:
        activity_terms = (
            "competition", "training programme", "cultural programme", "participants",
            "ncc", "nss", "swachh bharat", "mission shakti", "campaign", "rally",
            "cleaning programme", "organised", "organized", "event", "seminar", "workshop",
        )
        score = sum(1 for term in activity_terms if term in text or term in metadata)
        return score >= 2

    def _looks_like_time_sensitive_archive(self, heading: str, title: str, source: str) -> bool:
        value = " ".join([heading, title, source])
        return self._contains(value, ("notice", "calendar", "admission", "fee", "placement", "hostel", "scholarship", "report", "archive", "statistics"))

    def _looks_like_event_page(self, heading: str, title: str) -> bool:
        return self._contains(
            f"{heading} {title}",
            ("event", "events", "seminar", "workshop", "conference", "webinar", "newsletter", "award", "news", "highlights", "campaign"),
        )

    def _review_score(self, heading, title, text):
        score = 0
        for term in (
            "institutional", "institute", "college", "university", "office of", "academic affairs",
            "student affairs", "faculty office", "student support", "administrative office",
        ):
            if term in heading or term in title:
                score += 2
        for term in ("college", "institute", "university", "office", "procedure", "regulation", "student support", "institutional policy"):
            if term in text:
                score += 1
        if any(term in text for term in ("issn", "isbn", "doi", "abstract", "references", "workshop", "seminar", "webinar", "conference", "feedback", "audit report", "aishe")):
            return 0
        return score

    # ------------------------------------------------------------------
    # Junk/utility helpers
    # ------------------------------------------------------------------
    def _has_ui_noise(self, heading: str, text: str) -> bool:
        return any(self._normalize(signal) in heading or self._normalize(signal) in text for signal in UI_SIGNALS)

    def _is_ocr_noise(self, text: str) -> bool:
        if text in {"[no extractable text]", "scanned by camscanner", "scanned by cam scanner", "n", "a", "(a"}:
            return True
        words = re.findall(r"\b[\w'-]+\b", text, re.UNICODE)
        if len(words) <= 8:
            alnum = sum(1 for c in text if c.isalnum())
            alpha = sum(1 for c in text if c.isalpha())
            if alnum and alpha / alnum < 0.45:
                return True
        return False

    def _find(self, text: str, terms: tuple[str, ...]) -> list[str]:
        return [term for term in terms if self._normalize(term) in text]

    def _contains(self, text: str, terms: tuple[str, ...]) -> bool:
        return any(self._normalize(term) in text for term in terms)

    def _normalize(self, value: str) -> str:
        value = unquote(str(value or "")).lower()
        # Crawl filenames frequently encode spaces as _20 / %20.
        value = re.sub(r"(?:_|\s)20(?=[a-z])", " ", value)
        value = value.replace("_", " ")
        value = value.replace("-", " ")
        return re.sub(r"\s+", " ", value).strip()

    def _result(self, decision, confidence, score, reasons, signals, tier, family, genre):
        return {
            "decision": decision,
            "confidence": confidence,
            "score": score,
            "reasons": reasons,
            "signals": signals,
            "tier": tier,
            "knowledge_family": family,
            "document_genre": genre,
            "rag_eligible": tier in {"A", "B", "REVIEW"},
        }