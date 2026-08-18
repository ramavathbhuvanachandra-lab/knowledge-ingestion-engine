"""
Universal deterministic knowledge-record segmentation.

Purpose:
    Split structured knowledge sections into independent records when
    strong generic structural evidence indicates repeated entries.

This component does NOT:
    - classify knowledge
    - organize knowledge
    - delete knowledge
    - rewrite knowledge
    - use an LLM
    - depend on a specific college
    - depend on a specific URL

Important invariants:
    - Ambiguous structure is preserved.
    - Record text is never rewritten.
    - Ordering is deterministic.
    - Line provenance is preserved.
    - Standalone numeric values are not treated as record IDs
      without sufficient structural evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class KnowledgeRecord:
    """
    One independently segmentable knowledge record.
    """

    record_index: int | None
    text: str
    start_line: int
    end_line: int
    segmented: bool


class KnowledgeRecordSegmenter:
    """
    Detect and split strongly structured repeated records.

    Supported record forms:

        886 Project Alpha
        886. Project Alpha
        886) Project Alpha

    PDF/OCR-style records are also supported:

        886
        Project Alpha

    Standalone numbers require additional contextual evidence so
    that financial amounts, dates, quantities, and other numeric
    values are not mistaken for record identifiers.
    """

    NUMBERED_RECORD_PATTERN = re.compile(
        r"^\s*(\d{1,6})"
        r"(?:[.)]\s+|\s+)"
        r".+?"
        r"\s*$"
    )

    STANDALONE_NUMBER_PATTERN = re.compile(
        r"^\s*(\d{1,6})\s*$"
    )

    MIN_RECORDS_FOR_SEGMENTATION = 2

    # ========================================================
    # PUBLIC API
    # ========================================================

    def segment(
        self,
        *,
        text: str,
        start_line: int = 1,
    ) -> list[dict]:
        """
        Segment one section into deterministic records.
        """

        if not text or not text.strip():
            return []

        lines = text.splitlines()

        boundaries = self._find_numbered_boundaries(
            lines
        )

        if (
            len(boundaries)
            < self.MIN_RECORDS_FOR_SEGMENTATION
        ):
            return [
                self._build_unsplit_record(
                    text=text,
                    start_line=start_line,
                )
            ]

        records = self._build_records(
            lines=lines,
            boundaries=boundaries,
            start_line=start_line,
        )

        if (
            len(records)
            < self.MIN_RECORDS_FOR_SEGMENTATION
        ):
            return [
                self._build_unsplit_record(
                    text=text,
                    start_line=start_line,
                )
            ]

        return records

    # ========================================================
    # NUMBERED RECORD DETECTION
    # ========================================================

    def _find_numbered_boundaries(
        self,
        lines: list[str],
    ) -> list[tuple[int, int]]:
        """
        Find strong numbered record boundaries.

        Inline numbered records are strong evidence.

        Standalone numbers require contextual validation.
        """

        boundaries = []

        for index, line in enumerate(lines):

            inline_match = (
                self.NUMBERED_RECORD_PATTERN.match(
                    line
                )
            )

            if inline_match:
                boundaries.append(
                    (
                        index,
                        int(
                            inline_match.group(1)
                        ),
                    )
                )
                continue

            standalone_match = (
                self.STANDALONE_NUMBER_PATTERN.fullmatch(
                    line.strip()
                )
            )

            if not standalone_match:
                continue

            record_number = int(
                standalone_match.group(1)
            )

            if self._is_valid_standalone_boundary(
                lines=lines,
                index=index,
            ):
                boundaries.append(
                    (
                        index,
                        record_number,
                    )
                )

        return self._filter_boundaries(
            boundaries
        )

    # ========================================================
    # STANDALONE NUMBER VALIDATION
    # ========================================================

    def _is_valid_standalone_boundary(
        self,
        *,
        lines: list[str],
        index: int,
    ) -> bool:
        """
        Determine whether a standalone number is likely a record ID.

        A standalone number is rejected when the next substantive line
        is itself an explicit numbered record. This prevents values such
        as:

            945504
            1020 Project ...

        from being interpreted as a record boundary.

        We also require a following substantive line because a standalone
        number at the end of a section is unlikely to be a complete
        record boundary.
        """

        next_index = self._next_non_empty_line(
            lines,
            index + 1,
        )

        if next_index is None:
            return False

        next_line = lines[
            next_index
        ].strip()

        # Another explicit numbered record immediately follows.
        # The current standalone number is therefore much more likely
        # to be a numeric value belonging to the previous record.
        if self.NUMBERED_RECORD_PATTERN.match(
            next_line
        ):
            return False

        # Another standalone number immediately follows.
        # There is not enough evidence that the first value starts
        # substantive knowledge.
        if self.STANDALONE_NUMBER_PATTERN.fullmatch(
            next_line
        ):
            return False

        return True

    def _next_non_empty_line(
        self,
        lines: list[str],
        start_index: int,
    ) -> int | None:
        """
        Return the next non-empty line index.
        """

        for index in range(
            start_index,
            len(lines),
        ):

            if lines[index].strip():
                return index

        return None

    # ========================================================
    # BOUNDARY VALIDATION
    # ========================================================

    def _filter_boundaries(
        self,
        boundaries: list[tuple[int, int]],
    ) -> list[tuple[int, int]]:
        """
        Keep monotonically increasing record identifiers.

        Real documents may skip record numbers, so consecutive numbering
        is not required.
        """

        if not boundaries:
            return []

        filtered = [
            boundaries[0]
        ]

        for current in boundaries[1:]:

            previous_index, previous_number = (
                filtered[-1]
            )

            current_index, current_number = (
                current
            )

            if current_index <= previous_index:
                continue

            if current_number <= previous_number:
                continue

            filtered.append(
                current
            )

        return filtered

    # ========================================================
    # RECORD BUILDING
    # ========================================================

    def _build_records(
        self,
        *,
        lines: list[str],
        boundaries: list[tuple[int, int]],
        start_line: int,
    ) -> list[dict]:
        """
        Build one record for each detected boundary.
        """

        records = []

        for index, (
            boundary_line,
            record_number,
        ) in enumerate(boundaries):

            if index + 1 < len(boundaries):
                next_boundary_line = (
                    boundaries[index + 1][0]
                )
            else:
                next_boundary_line = len(lines)

            record_lines = lines[
                boundary_line:next_boundary_line
            ]

            record_text = (
                "\n".join(
                    record_lines
                ).strip()
            )

            if not record_text:
                continue

            records.append(
                {
                    "record_index": record_number,
                    "text": record_text,
                    "start_line": (
                        start_line
                        + boundary_line
                    ),
                    "end_line": (
                        start_line
                        + next_boundary_line
                        - 1
                    ),
                    "segmented": True,
                }
            )

        return records

    # ========================================================
    # UNSPLIT FALLBACK
    # ========================================================

    def _build_unsplit_record(
        self,
        *,
        text: str,
        start_line: int,
    ) -> dict:
        """
        Preserve the entire section when segmentation is uncertain.
        """

        line_count = len(
            text.splitlines()
        )

        return {
            "record_index": None,
            "text": text.strip(),
            "start_line": start_line,
            "end_line": (
                start_line
                + line_count
                - 1
            ),
            "segmented": False,
        }