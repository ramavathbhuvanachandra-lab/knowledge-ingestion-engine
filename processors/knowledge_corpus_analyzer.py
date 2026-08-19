"""
Command 3 — Dynamic Knowledge Corpus Analyzer.

Purpose
-------
Analyze the complete structured knowledge corpus before organization
planning begins.

This module is intentionally independent from folder creation.

Responsibilities
----------------
1. Read every structured JSON document in a domain.
2. Profile document structure and content.
3. Detect repeated headings and structural patterns.
4. Detect exact duplicate documents.
5. Discover terminology actually used by the institution.
6. Identify conservative department/school candidates.
7. Preserve source provenance.
8. Produce a deterministic, JSON-serializable corpus profile.

Non-responsibilities
--------------------
This module does NOT:

- create folders
- decide the final folder taxonomy
- write organized Markdown
- delete source documents
- use an LLM
- use embeddings
- use a vector database
- impose an IITJ/engineering/medical/law taxonomy

Important architectural invariant
----------------------------------
The analyzer observes the corpus.

The organization planner will later decide what the observations
mean for the final folder/file structure.

Therefore:

    observed terminology != folder
    repeated heading != folder
    department candidate != confirmed department
    duplicate candidate != automatic deletion

Those decisions belong to later Command 3 stages.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
import hashlib
import json
import re
from typing import Any


# ======================================================================
# TEXT NORMALIZATION
# ======================================================================

_NON_ALNUM_RE = re.compile(
    r"[^a-z0-9\s/&-]+"
)

_WHITESPACE_RE = re.compile(
    r"\s+"
)


def _normalize_text(
    value: Any,
) -> str:
    """
    Normalize text for deterministic comparison.

    This function must never modify source content. It is used only
    for analysis and comparison.
    """

    if value is None:
        return ""

    text = str(value).lower().strip()

    text = _NON_ALNUM_RE.sub(
        " ",
        text,
    )

    text = _WHITESPACE_RE.sub(
        " ",
        text,
    )

    return text.strip()


def _normalize_heading(
    value: Any,
) -> str:
    """Normalize a heading for structural comparison."""

    return _normalize_text(value)


def _tokenize(
    value: str,
) -> list[str]:
    """
    Return deterministic word tokens.

    Very short tokens are ignored because they provide little
    organizational signal.
    """

    return re.findall(
        r"\b[a-z][a-z0-9&-]{2,}\b",
        value.lower(),
    )


def _content_hash(
    text: str,
) -> str:
    """
    Create a stable hash for exact duplicate detection.

    Whitespace and casing differences are ignored.
    """

    normalized = _normalize_text(
        text
    )

    return hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()


# ======================================================================
# DATA MODELS
# ======================================================================


@dataclass
class DocumentProfile:
    """
    Corpus-level summary of one structured document.

    This object describes evidence. It does not assign taxonomy.
    """

    source_file: str
    source_url: str

    title: str
    document_type: str
    original_category: str

    section_count: int
    meaningful_section_count: int

    headings: list[str]
    normalized_headings: list[str]

    word_count: int

    content_hash: str


@dataclass
class HeadingProfile:
    """
    Frequency and document distribution for one heading.
    """

    heading: str
    normalized_heading: str

    occurrences: int
    document_count: int

    source_documents: list[str]


@dataclass
class CorpusProfile:
    """
    Deterministic description of one complete institutional corpus.
    """

    phase: str
    domain: str
    input_root: str

    document_count: int

    total_sections: int
    total_meaningful_sections: int
    total_words: int

    documents: list[DocumentProfile]

    heading_profiles: list[HeadingProfile]
    repeated_headings: list[HeadingProfile]

    document_types: dict[str, int]
    original_categories: dict[str, int]

    token_frequency: dict[str, int]

    exact_duplicate_groups: list[list[str]]

    likely_department_candidates: list[dict[str, Any]]

    terminology_candidates: list[str]


# ======================================================================
# CORPUS ANALYZER
# ======================================================================


class KnowledgeCorpusAnalyzer:
    """
    Analyze a complete structured knowledge corpus.

    The analyzer is intentionally conservative.

    It gathers evidence for the organization planner instead of
    prematurely deciding the final organization.
    """

    # ------------------------------------------------------------------
    # Structural vocabulary only.
    #
    # These are not folder categories.
    #
    # They help recognize phrases that express institutional
    # organizational relationships.
    # ------------------------------------------------------------------

    DEPARTMENT_MARKERS = {
        "department",
        "departments",
        "dept",
        "school",
        "schools",
    }

    DEPARTMENT_SUBTOPICS = {
        "overview",
        "about",
        "faculty",
        "faculties",
        "research",
        "program",
        "programs",
        "programme",
        "programmes",
        "course",
        "courses",
        "admission",
        "admissions",
        "laboratory",
        "laboratories",
        "lab",
        "labs",
        "contact",
    }

    MAX_TERMINOLOGY_ITEMS = 150

    MAX_TOKEN_FREQUENCY_ITEMS = 200

    MAX_HEADING_LENGTH = 8

    def __init__(
        self,
        input_root: str | Path,
    ) -> None:
        self.input_root = Path(
            input_root
        )

    # ==================================================================
    # PUBLIC API
    # ==================================================================

    def analyze(
        self,
        domain: str,
    ) -> dict[str, Any]:
        """
        Analyze every structured JSON document for one domain.

        Returns:
            JSON-serializable corpus profile.

        Raises:
            ValueError:
                If domain is empty or no structured documents exist.

            FileNotFoundError:
                If the domain directory does not exist.
        """

        domain = (
            domain or ""
        ).strip()

        if not domain:
            raise ValueError(
                "Domain cannot be empty."
            )

        domain_root = (
            self.input_root
            / domain
        )

        if not domain_root.exists():
            raise FileNotFoundError(
                "Structured domain does not exist: "
                f"{domain_root}"
            )

        json_files = sorted(
            domain_root.rglob(
                "*.json"
            )
        )

        if not json_files:
            raise ValueError(
                "No structured JSON files found in: "
                f"{domain_root}"
            )

        return self._build_profile(
            domain=domain,
            domain_root=domain_root,
            json_files=json_files,
        )

    # ==================================================================
    # PROFILE CONSTRUCTION
    # ==================================================================

    def _build_profile(
        self,
        *,
        domain: str,
        domain_root: Path,
        json_files: list[Path],
    ) -> dict[str, Any]:
        """
        Build the complete corpus profile.

        All documents are analyzed before any corpus-level conclusion
        is produced.
        """

        documents: list[
            DocumentProfile
        ] = []

        heading_counts: Counter[
            str
        ] = Counter()

        heading_documents: defaultdict[
            str,
            set[str],
        ] = defaultdict(set)

        heading_originals: dict[
            str,
            str,
        ] = {}

        document_type_counts: Counter[
            str
        ] = Counter()

        category_counts: Counter[
            str
        ] = Counter()

        token_counts: Counter[
            str
        ] = Counter()

        content_hash_documents: defaultdict[
            str,
            list[str],
        ] = defaultdict(list)

        total_sections = 0
        total_meaningful_sections = 0
        total_words = 0

        # --------------------------------------------------------------
        # Analyze every source document.
        # --------------------------------------------------------------

        for json_path in json_files:

            try:
                document = self._load_document(
                    json_path
                )

                profile = self._profile_document(
                    json_path=json_path,
                    document=document,
                )

            except Exception as error:
                # One malformed structured document must not destroy
                # the entire domain analysis.
                #
                # The failed file is skipped here. A later validation
                # stage can report structured-input failures explicitly.
                print(
                    "WARNING: Failed to analyze "
                    f"{json_path}: {error}"
                )

                continue

            documents.append(
                profile
            )

            total_sections += (
                profile.section_count
            )

            total_meaningful_sections += (
                profile.meaningful_section_count
            )

            total_words += (
                profile.word_count
            )

            document_type_counts[
                profile.document_type
                or "unknown"
            ] += 1

            category_counts[
                profile.original_category
                or "unknown"
            ] += 1

            content_hash_documents[
                profile.content_hash
            ].append(
                profile.source_file
            )

            # ----------------------------------------------------------
            # Heading evidence.
            # ----------------------------------------------------------

            for (
                normalized_heading,
                heading,
            ) in zip(
                profile.normalized_headings,
                profile.headings,
            ):

                if not normalized_heading:
                    continue

                heading_counts[
                    normalized_heading
                ] += 1

                heading_documents[
                    normalized_heading
                ].add(
                    profile.source_file
                )

                heading_originals.setdefault(
                    normalized_heading,
                    heading,
                )

            # ----------------------------------------------------------
            # Corpus vocabulary evidence.
            #
            # Heading vocabulary is especially useful for later
            # organization planning because headings are normally
            # intentional labels created by the institution.
            # ----------------------------------------------------------

            heading_text = " ".join(
                profile.headings
            )

            for token in _tokenize(
                heading_text
            ):
                token_counts[token] += 1

        heading_profiles = (
            self._build_heading_profiles(
                heading_counts=heading_counts,
                heading_documents=heading_documents,
                heading_originals=heading_originals,
            )
        )

        repeated_headings = [
            profile
            for profile in heading_profiles
            if (
                profile.occurrences >= 2
                and profile.document_count >= 2
            )
        ]

        exact_duplicate_groups = (
            self._build_duplicate_groups(
                content_hash_documents
            )
        )

        department_candidates = (
            self._discover_department_candidates(
                documents=documents,
                heading_profiles=heading_profiles,
            )
        )

        terminology_candidates = (
            self._discover_terminology(
                heading_profiles=heading_profiles,
            )
        )

        profile = CorpusProfile(
            phase=(
                "command_3_corpus_analysis"
            ),
            domain=domain,
            input_root=str(
                domain_root
            ),
            document_count=len(
                documents
            ),
            total_sections=total_sections,
            total_meaningful_sections=(
                total_meaningful_sections
            ),
            total_words=total_words,
            documents=documents,
            heading_profiles=heading_profiles,
            repeated_headings=repeated_headings,
            document_types=dict(
                document_type_counts
            ),
            original_categories=dict(
                category_counts
            ),
            token_frequency=dict(
                token_counts.most_common(
                    self.MAX_TOKEN_FREQUENCY_ITEMS
                )
            ),
            exact_duplicate_groups=(
                exact_duplicate_groups
            ),
            likely_department_candidates=(
                department_candidates
            ),
            terminology_candidates=(
                terminology_candidates
            ),
        )

        return asdict(
            profile
        )

    # ==================================================================
    # DOCUMENT LOADING
    # ==================================================================

    @staticmethod
    def _load_document(
        json_path: Path,
    ) -> dict[str, Any]:
        """Load one structured JSON document."""

        data = json.loads(
            json_path.read_text(
                encoding="utf-8"
            )
        )

        if not isinstance(
            data,
            dict,
        ):
            raise ValueError(
                "Structured document must be a JSON object."
            )

        return data

    # ==================================================================
    # DOCUMENT PROFILING
    # ==================================================================

    def _profile_document(
        self,
        *,
        json_path: Path,
        document: dict[str, Any],
    ) -> DocumentProfile:
        """
        Convert one structured JSON document into a compact profile.
        """

        metadata = document.get(
            "document",
            {},
        )

        if not isinstance(
            metadata,
            dict,
        ):
            metadata = {}

        title = self._first_string(
            metadata,
            "title",
        )

        source_url = (
            self._first_string(
                metadata,
                "url",
            )
            or self._first_string(
                metadata,
                "source_url",
            )
        )

        document_type = self._first_string(
            metadata,
            "document_type",
        )

        original_category = self._first_string(
            metadata,
            "category",
        )

        headings: list[str] = []
        all_text_parts: list[str] = []

        section_count = 0
        meaningful_section_count = 0
        word_count = 0

        pages = document.get(
            "pages",
            [],
        )

        if not isinstance(
            pages,
            list,
        ):
            pages = []

        for page in pages:

            if not isinstance(
                page,
                dict,
            ):
                continue

            sections = page.get(
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

                section_count += 1

                heading = self._first_string(
                    section,
                    "heading",
                )

                if heading:
                    headings.append(
                        heading
                    )

                content = section.get(
                    "content",
                    [],
                )

                text = self._content_to_text(
                    content
                )

                if text.strip():
                    meaningful_section_count += 1

                    all_text_parts.append(
                        text
                    )

                    word_count += len(
                        _tokenize(text)
                    )

        normalized_headings = [
            _normalize_heading(
                heading
            )
            for heading in headings
        ]

        canonical_text = "\n".join(
            all_text_parts
        )

        return DocumentProfile(
            source_file=str(
                json_path
            ),
            source_url=source_url,
            title=title,
            document_type=document_type,
            original_category=original_category,
            section_count=section_count,
            meaningful_section_count=(
                meaningful_section_count
            ),
            headings=headings,
            normalized_headings=(
                normalized_headings
            ),
            word_count=word_count,
            content_hash=_content_hash(
                canonical_text
            ),
        )

    # ==================================================================
    # GENERIC VALUE HELPERS
    # ==================================================================

    @staticmethod
    def _first_string(
        mapping: dict[str, Any],
        key: str,
    ) -> str:
        """Return a cleaned string field or an empty string."""

        value = mapping.get(
            key
        )

        if value is None:
            return ""

        return str(
            value
        ).strip()

    # ==================================================================
    # CONTENT EXTRACTION
    # ==================================================================

    @classmethod
    def _content_to_text(
        cls,
        content: Any,
    ) -> str:
        """
        Convert structured section content into plain text.

        This is analysis-only. Source content is never rewritten.
        """

        if isinstance(
            content,
            str,
        ):
            return content

        if not isinstance(
            content,
            list,
        ):
            return ""

        parts: list[str] = []

        for item in content:

            if isinstance(
                item,
                str,
            ):
                parts.append(
                    item
                )
                continue

            if not isinstance(
                item,
                dict,
            ):
                continue

            extracted = cls._extract_content_value(
                item
            )

            if extracted:
                parts.append(
                    extracted
                )

        return "\n".join(
            parts
        )

    @staticmethod
    def _extract_content_value(
        item: dict[str, Any],
    ) -> str:
        """
        Extract text from common structured-content representations.
        """

        for key in (
            "text",
            "value",
            "content",
        ):

            value = item.get(
                key
            )

            if isinstance(
                value,
                str,
            ):
                return value

        return ""

    # ==================================================================
    # HEADING ANALYSIS
    # ==================================================================

    @staticmethod
    def _build_heading_profiles(
        *,
        heading_counts: Counter[str],
        heading_documents: defaultdict[
            str,
            set[str],
        ],
        heading_originals: dict[
            str,
            str,
        ],
    ) -> list[HeadingProfile]:
        """Build heading-level corpus statistics."""

        profiles: list[
            HeadingProfile
        ] = []

        for (
            normalized_heading,
            occurrences,
        ) in heading_counts.most_common():

            source_documents = sorted(
                heading_documents[
                    normalized_heading
                ]
            )

            profiles.append(
                HeadingProfile(
                    heading=heading_originals[
                        normalized_heading
                    ],
                    normalized_heading=(
                        normalized_heading
                    ),
                    occurrences=occurrences,
                    document_count=len(
                        source_documents
                    ),
                    source_documents=(
                        source_documents
                    ),
                )
            )

        return profiles

    # ==================================================================
    # DUPLICATE ANALYSIS
    # ==================================================================

    @staticmethod
    def _build_duplicate_groups(
        content_hash_documents: defaultdict[
            str,
            list[str],
        ],
    ) -> list[list[str]]:
        """
        Return exact duplicate groups.

        Only exact normalized-content matches are returned here.

        Near-duplicate detection will be a separate stage because
        it requires stronger evidence and should not accidentally
        remove legitimate versions of institutional content.
        """

        groups = [
            sorted(
                paths
            )
            for paths in content_hash_documents.values()
            if len(paths) > 1
        ]

        groups.sort(
            key=lambda group: (
                -len(group),
                group[0],
            )
        )

        return groups

    # ==================================================================
    # DEPARTMENT DISCOVERY
    # ==================================================================

    def _discover_department_candidates(
        self,
        *,
        documents: list[DocumentProfile],
        heading_profiles: list[HeadingProfile],
    ) -> list[dict[str, Any]]:
        """
        Detect conservative department/school candidates.

        A candidate is evidence for the planner, not a final decision.

        Strong evidence includes:
            - explicit "Department of X"
            - "X Department"
            - "School of X"
            - repeated appearance across documents
            - co-occurrence with common department-level headings
        """

        candidate_sources: defaultdict[
            str,
            set[str],
        ] = defaultdict(set)

        candidate_display: dict[
            str,
            str,
        ] = {}

        candidate_subtopics: defaultdict[
            str,
            Counter[str],
        ] = defaultdict(Counter)

        # --------------------------------------------------------------
        # Primary signal: explicit structural headings.
        # --------------------------------------------------------------

        for document in documents:

            headings = document.headings

            for index, heading in enumerate(
                headings
            ):

                candidate = (
                    self._extract_department_name(
                        heading
                    )
                )

                if not candidate:
                    continue

                normalized_candidate = (
                    _normalize_text(
                        candidate
                    )
                )

                if not normalized_candidate:
                    continue

                candidate_sources[
                    normalized_candidate
                ].add(
                    document.source_file
                )

                candidate_display.setdefault(
                    normalized_candidate,
                    candidate,
                )

                # ------------------------------------------------------
                # Inspect the next few headings.
                # These are evidence that the candidate behaves like
                # an actual institutional unit.
                # ------------------------------------------------------

                nearby_headings = headings[
                    index + 1:
                    index + 6
                ]

                for nearby_heading in (
                    nearby_headings
                ):

                    normalized_nearby = (
                        _normalize_text(
                            nearby_heading
                        )
                    )

                    if normalized_nearby in (
                        self.DEPARTMENT_SUBTOPICS
                    ):
                        candidate_subtopics[
                            normalized_candidate
                        ][
                            normalized_nearby
                        ] += 1

        candidates: list[
            dict[str, Any]
        ] = []

        for (
            normalized_candidate,
            sources,
        ) in candidate_sources.items():

            subtopics = (
                candidate_subtopics[
                    normalized_candidate
                ]
            )

            evidence_score = (
                len(sources) * 3
                + sum(
                    subtopics.values()
                )
            )

            candidates.append(
                {
                    "name": candidate_display[
                        normalized_candidate
                    ],
                    "normalized_name": (
                        normalized_candidate
                    ),
                    "document_count": len(
                        sources
                    ),
                    "evidence_score": (
                        evidence_score
                    ),
                    "repeated_subtopics": dict(
                        subtopics
                    ),
                    "source_documents": sorted(
                        sources
                    ),
                }
            )

        candidates.sort(
            key=lambda item: (
                -item["evidence_score"],
                -item["document_count"],
                item["normalized_name"],
            )
        )

        return candidates

    @staticmethod
    def _extract_department_name(
        heading: str,
    ) -> str:
        """
        Extract an explicit department/school name from a heading.

        This method recognizes structural language only.

        Examples:
            Department of Electrical Engineering
            Electrical Engineering Department
            School of Computer Science
            School of Law
        """

        text = heading.strip()

        patterns = (
            r"^(?:department|dept\.?)\s+"
            r"(?:of\s+)?(.+)$",

            r"^(.+?)\s+"
            r"(?:department|dept\.?)$",

            r"^(?:school)\s+of\s+(.+)$",

            r"^school\s*:\s*(.+)$",
        )

        for pattern in patterns:

            match = re.match(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if not match:
                continue

            candidate = match.group(
                1
            ).strip()

            if candidate:
                return candidate

        return ""

    # ==================================================================
    # TERMINOLOGY DISCOVERY
    # ==================================================================

    def _discover_terminology(
        self,
        *,
        heading_profiles: list[HeadingProfile],
    ) -> list[str]:
        """
        Discover terminology actually used by the institution.

        Important:
            A term appearing once is still retained.

        Why:
            A unique heading can represent an important institutional
            concept.

        However:
            This list is evidence only.

        The organization planner must decide whether a term deserves
        a folder, file, subsection, or no structural role at all.
        """

        candidates: list[
            tuple[str, int, int]
        ] = []

        for profile in heading_profiles:

            heading = profile.heading.strip()

            if not heading:
                continue

            if len(
                heading.split()
            ) > self.MAX_HEADING_LENGTH:
                continue

            candidates.append(
                (
                    heading,
                    profile.occurrences,
                    profile.document_count,
                )
            )

        # Repeated terms receive higher priority, but single-use
        # headings remain available to the planner.
        candidates.sort(
            key=lambda item: (
                -item[1],
                -item[2],
                item[0].lower(),
            )
        )

        return [
            heading
            for heading, _, _ in candidates[
                : self.MAX_TERMINOLOGY_ITEMS
            ]
        ]


# ======================================================================
# OPTIONAL CLI ENTRY POINT
# ======================================================================


def main() -> None:
    """
    Small manual inspection entry point.

    This is intentionally not wired into the production pipeline yet.
    """

    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Analyze a structured knowledge corpus "
            "for Command 3."
        )
    )

    parser.add_argument(
        "--input-root",
        required=True,
        help=(
            "Root containing structured domain directories."
        ),
    )

    parser.add_argument(
        "--domain",
        required=True,
        help="Domain to analyze.",
    )

    parser.add_argument(
        "--output",
        required=False,
        help=(
            "Optional path for writing the "
            "corpus profile JSON."
        ),
    )

    args = parser.parse_args()

    analyzer = KnowledgeCorpusAnalyzer(
        input_root=args.input_root
    )

    profile = analyzer.analyze(
        args.domain
    )

    serialized = json.dumps(
        profile,
        indent=2,
        ensure_ascii=False,
    )

    if args.output:
        output_path = Path(
            args.output
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path.write_text(
            serialized,
            encoding="utf-8",
        )

        print(
            f"Corpus profile written to: "
            f"{output_path}"
        )

    else:
        print(
            serialized
        )


if __name__ == "__main__":
    main()