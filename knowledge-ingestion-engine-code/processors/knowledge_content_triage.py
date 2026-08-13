from pathlib import Path
import re


class KnowledgeContentTriage:
    """
    Deterministic triage of extracted knowledge sections.

    Decisions:
        KEEP   -> likely useful knowledge
        NOISE  -> obvious UI/navigation/boilerplate
        REVIEW -> ambiguous; preserve for later LLM classification

    This stage NEVER modifies the canonical Markdown.
    """

    NOISE_HEADINGS = (
        "accessibility",
        "accessibility options",
        "main menu",
        "menu",
        "navigation",
        "search here",
        "footer",
        "login",
        "student login",
        "students login",
        "students' login",
        "admin login",
        "please wait",
        "created by",
        "important links",
        "quick links",
    )

    NOISE_PHRASES = (
        "arrow_downward",
        "ux4g",
        "accessibility options",
        "students login",
        "students' login",
        "admin login",
        "login close",
        "javascript",
        "skip to main content",
        "back to top",
    )

    NAVIGATION_LINK_THRESHOLD = 0.70

    MIN_USEFUL_TEXT = 80

    def classify(self, section: dict) -> dict:
        """
        Classify one extracted section.

        Returns the original section plus:
            decision
            reasons
        """

        heading = str(
            section.get("heading") or ""
        ).strip()

        text = str(
            section.get("text") or ""
        ).strip()

        lower_heading = heading.lower()
        lower_text = text.lower()

        reasons = []

        # ----------------------------------------------------
        # EMPTY
        # ----------------------------------------------------

        if not text:
            return self._result(
                section,
                "NOISE",
                ["empty section"],
            )

        # ----------------------------------------------------
        # KNOWN NOISE HEADING
        # ----------------------------------------------------

        if self._matches_noise_heading(
            lower_heading
        ):
            reasons.append(
                "known UI/navigation heading"
            )

            return self._result(
                section,
                "NOISE",
                reasons,
            )

        # ----------------------------------------------------
        # KNOWN NOISE CONTENT
        # ----------------------------------------------------

        for phrase in self.NOISE_PHRASES:

            if phrase in lower_text:
                reasons.append(
                    f"contains UI/noise marker: {phrase}"
                )

                return self._result(
                    section,
                    "NOISE",
                    reasons,
                )

        # ----------------------------------------------------
        # IMAGE-ONLY / EXTRACTION FAILURE
        # ----------------------------------------------------

        normalized = re.sub(
            r"[\s\[\]\(\)_\-:.,]+",
            "",
            text,
        )

        if not normalized:
            return self._result(
                section,
                "NOISE",
                ["no meaningful extracted text"],
            )

        # ----------------------------------------------------
        # MARKDOWN LINK RATIO
        # ----------------------------------------------------

        words = re.findall(
            r"\b[\w'-]+\b",
            text,
        )

        links = re.findall(
            r"\[[^\]]*\]\([^)]+\)",
            text,
        )

        if words:

            link_ratio = (
                len(links)
                / len(words)
            )

            if (
                link_ratio
                >= self.NAVIGATION_LINK_THRESHOLD
            ):
                return self._result(
                    section,
                    "NOISE",
                    [
                        "navigation-heavy content",
                        f"link ratio: {link_ratio:.2f}",
                    ],
                )

        # ----------------------------------------------------
        # VERY SHORT CONTENT
        # ----------------------------------------------------

        if len(text) < self.MIN_USEFUL_TEXT:

            reasons.append(
                f"very short content ({len(text)} characters)"
            )

            return self._result(
                section,
                "REVIEW",
                reasons,
            )

        # ----------------------------------------------------
        # TABLE OF CONTENTS / INDEX
        # ----------------------------------------------------

        toc_markers = (
            "table of contents",
            "contents",
        )

        if any(
            marker in lower_text
            for marker in toc_markers
        ):

            reasons.append(
                "possible table of contents/index"
            )

            return self._result(
                section,
                "REVIEW",
                reasons,
            )

        # ----------------------------------------------------
        # DEFAULT
        # ----------------------------------------------------

        return self._result(
            section,
            "KEEP",
            ["contains substantial content"],
        )

    # --------------------------------------------------------
    # CLASSIFY ALL
    # --------------------------------------------------------

    def classify_all(
        self,
        sections: list[dict],
    ) -> list[dict]:

        return [
            self.classify(section)
            for section in sections
        ]

    # --------------------------------------------------------
    # NOISE HEADING MATCH
    # --------------------------------------------------------

    def _matches_noise_heading(
        self,
        heading: str,
    ) -> bool:

        for pattern in self.NOISE_HEADINGS:

            if heading == pattern:
                return True

            if heading.startswith(
                pattern + " "
            ):
                return True

        return False

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    def _result(
        self,
        section: dict,
        decision: str,
        reasons: list[str],
    ) -> dict:

        result = dict(section)

        result["triage"] = {
            "decision": decision,
            "reasons": reasons,
        }

        return result
