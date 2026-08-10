from dataclasses import dataclass
from pathlib import Path
import json
import re


@dataclass
class KnowledgeValidationResult:
    """
    Validation result for one knowledge document.
    """

    markdown_path: Path
    metadata_path: Path

    valid: bool
    warnings: list[str]
    errors: list[str]

    text_length: int
    line_count: int

    title: str | None
    source_url: str | None
    document_type: str | None


class KnowledgeValidator:
    """
    Validates knowledge documents before Phase 7
    cleaning and chunking.

    Phase 7.2 responsibilities:

    - Validate Markdown content.
    - Validate required metadata.
    - Detect empty or extremely small documents.
    - Detect missing source information.
    - Detect obvious extraction failures.
    - Report warnings separately from errors.
    - Do not modify files.
    - Do not clean content.
    - Do not chunk content.
    """

    MIN_TEXT_LENGTH = 20

    REQUIRED_METADATA_FIELDS = (
    
    )

    def validate(
        self,
        markdown_path: str | Path,
        metadata_path: str | Path,
    ) -> KnowledgeValidationResult:

        markdown_path = Path(
            markdown_path
        )

        metadata_path = Path(
            metadata_path
        )

        warnings = []
        errors = []

        # ----------------------------------------------------
        # FILE VALIDATION
        # ----------------------------------------------------

        if not markdown_path.exists():

            errors.append(
                "Markdown file does not exist"
            )

            return self._result(
                markdown_path,
                metadata_path,
                False,
                warnings,
                errors,
                "",
                {},
            )

        if not markdown_path.is_file():

            errors.append(
                "Markdown path is not a file"
            )

            return self._result(
                markdown_path,
                metadata_path,
                False,
                warnings,
                errors,
                "",
                {},
            )

        if not metadata_path.exists():

            errors.append(
                "Metadata file does not exist"
            )

            return self._result(
                markdown_path,
                metadata_path,
                False,
                warnings,
                errors,
                "",
                {},
            )

        if not metadata_path.is_file():

            errors.append(
                "Metadata path is not a file"
            )

            return self._result(
                markdown_path,
                metadata_path,
                False,
                warnings,
                errors,
                "",
                {},
            )

        # ----------------------------------------------------
        # READ MARKDOWN
        # ----------------------------------------------------

        try:

            text = markdown_path.read_text(
                encoding="utf-8"
            )

        except UnicodeDecodeError as error:

            errors.append(
                f"Markdown is not valid UTF-8: {error}"
            )

            return self._result(
                markdown_path,
                metadata_path,
                False,
                warnings,
                errors,
                "",
                {},
            )

        stripped_text = text.strip()

        text_length = len(
            stripped_text
        )

        line_count = len(
            text.splitlines()
        )

        # ----------------------------------------------------
        # CONTENT VALIDATION
        # ----------------------------------------------------

        if text_length == 0:

            errors.append(
                "Markdown content is empty"
            )

        elif text_length < self.MIN_TEXT_LENGTH:

            warnings.append(
                "Markdown content is extremely small"
            )

        # ----------------------------------------------------
        # METADATA
        # ----------------------------------------------------

        try:

            metadata = json.loads(
                metadata_path.read_text(
                    encoding="utf-8"
                )
            )

        except UnicodeDecodeError as error:

            errors.append(
                f"Metadata is not valid UTF-8: {error}"
            )

            metadata = {}

        except json.JSONDecodeError as error:

            errors.append(
                f"Metadata contains invalid JSON: {error}"
            )

            metadata = {}

        if not isinstance(
            metadata,
            dict,
        ):

            errors.append(
                "Metadata must be a JSON object"
            )

            metadata = {}

        # ----------------------------------------------------
        # REQUIRED METADATA
        # ----------------------------------------------------
        source_url = (
            metadata.get("url")
               or metadata.get("source_url")
        )

        if not source_url:

           errors.append(
                "Missing source URL metadata "
                 "(expected 'url' or 'source_url')"
            )

        # ----------------------------------------------------
        # OPTIONAL METADATA WARNINGS
        # ----------------------------------------------------

        title = metadata.get(
            "title"
        )

        if not title:

            warnings.append(
                "Metadata does not contain a title"
            )

        document_type = metadata.get(
            "document_type"
        )

        if not document_type:

            warnings.append(
                "Metadata does not contain document_type"
            )

        # ----------------------------------------------------
        # OBVIOUS EXTRACTION FAILURE
        # ----------------------------------------------------

        if (
            "extraction_success" in metadata
            and metadata["extraction_success"] is False
        ):

            errors.append(
                "Document extraction was marked as unsuccessful"
            )

        # ----------------------------------------------------
        # OBVIOUS PLACEHOLDER CONTENT
        # ----------------------------------------------------

        placeholder_patterns = [
            r"^\[no extractable text\]$",
            r"^error$",
            r"^not found$",
        ]

        if stripped_text:

            normalized = (
                stripped_text
                .lower()
                .strip()
            )

            for pattern in placeholder_patterns:

                if re.fullmatch(
                    pattern,
                    normalized,
                ):

                    errors.append(
                        "Markdown contains only placeholder content"
                    )

                    break

        # ----------------------------------------------------
        # FINAL STATUS
        # ----------------------------------------------------

        valid = len(errors) == 0

        return self._result(
            markdown_path,
            metadata_path,
            valid,
            warnings,
            errors,
            stripped_text,
            metadata,
        )

    # --------------------------------------------------------
    # RESULT BUILDER
    # --------------------------------------------------------

    def _result(
        self,
        markdown_path,
        metadata_path,
        valid,
        warnings,
        errors,
        text,
        metadata,
    ):

        return KnowledgeValidationResult(
            markdown_path=markdown_path,
            metadata_path=metadata_path,
            valid=valid,
            warnings=warnings,
            errors=errors,
            text_length=len(text),
            line_count=len(
                text.splitlines()
            ),
            title=metadata.get(
                "title"
            ),
            source_url=(
                metadata.get("url")
                or metadata.get("source_url")
            ),
            document_type=metadata.get(
                "document_type"
            ),
        )