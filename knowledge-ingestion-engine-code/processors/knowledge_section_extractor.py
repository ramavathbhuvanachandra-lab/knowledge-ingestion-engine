from pathlib import Path
import re


class KnowledgeSectionExtractor:
    """
    Extract structured sections from the canonical knowledge Markdown.

    This stage:
    - reads the permanent Markdown knowledge base
    - identifies headings and their content
    - preserves source text
    - does NOT classify with an LLM
    - does NOT rewrite knowledge
    - does NOT delete source files
    """

    HEADING_PATTERN = re.compile(
        r"^(#{1,6})\s+(.+?)\s*$"
    )

    def extract(
        self,
        markdown_path: str | Path,
    ) -> list[dict]:

        markdown_path = Path(markdown_path)

        if not markdown_path.exists():
            raise FileNotFoundError(
                f"Markdown file does not exist: {markdown_path}"
            )

        if not markdown_path.is_file():
            raise ValueError(
                f"Markdown path is not a file: {markdown_path}"
            )

        content = markdown_path.read_text(
            encoding="utf-8"
        )

        lines = content.splitlines()

        sections = []

        current_heading = None
        current_level = None
        current_lines = []
        current_start_line = None

        for line_number, line in enumerate(
            lines,
            start=1,
        ):

            match = self.HEADING_PATTERN.match(line)

            if match:

                if current_heading is not None:
                    section = self._build_section(
                        heading=current_heading,
                        level=current_level,
                        lines=current_lines,
                        start_line=current_start_line,
                        end_line=line_number - 1,
                    )

                    if section is not None:
                        sections.append(section)

                current_heading = match.group(2).strip()
                current_level = len(match.group(1))
                current_lines = []
                current_start_line = line_number

                continue

            if current_heading is not None:
                current_lines.append(line)

        # ----------------------------------------------------
        # FINAL SECTION
        # ----------------------------------------------------

        if current_heading is not None:

            section = self._build_section(
                heading=current_heading,
                level=current_level,
                lines=current_lines,
                start_line=current_start_line,
                end_line=len(lines),
            )

            if section is not None:
                sections.append(section)

        return sections

    # --------------------------------------------------------
    # BUILD SECTION
    # --------------------------------------------------------

    def _build_section(
        self,
        heading: str,
        level: int,
        lines: list[str],
        start_line: int,
        end_line: int,
    ) -> dict | None:

        text = "\n".join(lines).strip()

        if not text:
            return None

        cleaned_text = self._clean_text(text)

        if not cleaned_text:
            return None

        return {
            "heading": heading,
            "level": level,
            "text": cleaned_text,
            "character_count": len(cleaned_text),
            "start_line": start_line,
            "end_line": end_line,
        }

    # --------------------------------------------------------
    # TEXT CLEANING
    # --------------------------------------------------------

    def _clean_text(
        self,
        text: str,
    ) -> str:

        lines = []

        for line in text.splitlines():

            line = line.strip()

            if not line:
                continue

            lines.append(line)

        return "\n".join(lines)
