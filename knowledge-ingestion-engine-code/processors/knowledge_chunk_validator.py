from pathlib import Path
import json
import re


class KnowledgeChunkValidator:
    """
    Validates retrieval-ready knowledge chunks.

    Phase 7.6 responsibilities:

    - Validate chunk structure.
    - Validate required metadata.
    - Detect duplicate chunks.
    - Detect obvious noise.
    - Detect navigation-heavy chunks.
    - Validate chunk size.
    - Preserve warnings separately from errors.
    - Do NOT modify chunks.
    - Do NOT generate embeddings.
    """

    REQUIRED_METADATA = {
        "source_url",
        "domain",
        "category",
        "document_type",
        "source_document",
        "page_number",
        "section",
    }

    NOISE_PATTERNS = (
        "###147852369",
        "arrow_downward",
        "accessibility options",
    )

    def __init__(
        self,
        min_chunk_size: int = 80,
        max_chunk_size: int = 1200,
        navigation_ratio_threshold: float = 0.70,
    ):
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.navigation_ratio_threshold = (
            navigation_ratio_threshold
        )

    # ========================================================
    # PUBLIC API
    # ========================================================

    def validate(
        self,
        chunk_path: str | Path,
    ) -> dict:

        chunk_path = Path(chunk_path)

        if not chunk_path.exists():
            raise FileNotFoundError(
                f"Chunk file does not exist: {chunk_path}"
            )

        if not chunk_path.is_file():
            raise ValueError(
                f"Chunk path is not a file: {chunk_path}"
            )

        if chunk_path.suffix.lower() != ".json":
            raise ValueError(
                f"Expected JSON file: {chunk_path}"
            )

        data = json.loads(
            chunk_path.read_text(
                encoding="utf-8"
            )
        )

        chunks = data.get("chunks", [])

        if not isinstance(chunks, list):
            raise ValueError(
                "Invalid chunk file: 'chunks' must be a list"
            )

        errors = []
        warnings = []

        seen_ids = set()
        seen_text = set()

        for index, chunk in enumerate(chunks, start=1):

            prefix = f"Chunk #{index}"

            if not isinstance(chunk, dict):
                errors.append(
                    f"{prefix}: chunk is not an object"
                )
                continue

            self._validate_id(
                chunk,
                prefix,
                seen_ids,
                errors,
            )

            text = chunk.get("text")

            self._validate_text(
                text,
                prefix,
                seen_text,
                errors,
                warnings,
            )

            metadata = chunk.get(
                "metadata",
                {}
            )

            self._validate_metadata(
                metadata,
                prefix,
                errors,
                warnings,
            )

            if isinstance(text, str):

                self._validate_size(
                    text,
                    prefix,
                    warnings,
                )

                self._detect_noise(
                    text,
                    prefix,
                    warnings,
                )

                self._detect_navigation(
                    text,
                    prefix,
                    warnings,
                )

        result = {
            "chunk_file": str(chunk_path),
            "chunk_count": len(chunks),
            "errors": errors,
            "warnings": warnings,
            "valid": len(errors) == 0,
        }

        return result

    # ========================================================
    # ID VALIDATION
    # ========================================================

    def _validate_id(
        self,
        chunk,
        prefix,
        seen_ids,
        errors,
    ):

        chunk_id = chunk.get("chunk_id")

        if not chunk_id:
            errors.append(
                f"{prefix}: missing chunk_id"
            )
            return

        if not isinstance(chunk_id, str):
            errors.append(
                f"{prefix}: chunk_id must be a string"
            )
            return

        if chunk_id in seen_ids:
            errors.append(
                f"{prefix}: duplicate chunk_id: {chunk_id}"
            )
            return

        seen_ids.add(chunk_id)

    # ========================================================
    # TEXT VALIDATION
    # ========================================================

    def _validate_text(
        self,
        text,
        prefix,
        seen_text,
        errors,
        warnings,
    ):

        if text is None:
            errors.append(
                f"{prefix}: missing text"
            )
            return

        if not isinstance(text, str):
            errors.append(
                f"{prefix}: text must be a string"
            )
            return

        stripped = text.strip()

        if not stripped:
            errors.append(
                f"{prefix}: empty text"
            )
            return

        normalized = re.sub(
            r"\s+",
            " ",
            stripped,
        )

        if normalized in seen_text:
            warnings.append(
                f"{prefix}: duplicate text"
            )
        else:
            seen_text.add(normalized)

    # ========================================================
    # METADATA VALIDATION
    # ========================================================

    def _validate_metadata(
        self,
        metadata,
        prefix,
        errors,
        warnings,
    ):

        if not isinstance(metadata, dict):
            errors.append(
                f"{prefix}: metadata must be an object"
            )
            return

        missing = (
            self.REQUIRED_METADATA
            - set(metadata.keys())
        )

        if missing:
            errors.append(
                f"{prefix}: missing metadata: "
                f"{sorted(missing)}"
            )

        if not metadata.get("source_url"):
            errors.append(
                f"{prefix}: missing source_url"
            )

        if not metadata.get("domain"):
            errors.append(
                f"{prefix}: missing domain"
            )

        if not metadata.get("document_type"):
            warnings.append(
                f"{prefix}: missing document_type"
            )

    # ========================================================
    # SIZE VALIDATION
    # ========================================================

    def _validate_size(
        self,
        text,
        prefix,
        warnings,
    ):

        size = len(text.strip())

        if size < self.min_chunk_size:
            warnings.append(
                f"{prefix}: small chunk "
                f"({size} characters)"
            )

        if size > self.max_chunk_size:
            warnings.append(
                f"{prefix}: oversized chunk "
                f"({size} characters)"
            )

    # ========================================================
    # NOISE DETECTION
    # ========================================================

    def _detect_noise(
        self,
        text,
        prefix,
        warnings,
    ):

        lower = text.lower().strip()

        for pattern in self.NOISE_PATTERNS:

            if pattern.lower() in lower:
                warnings.append(
                    f"{prefix}: possible noise content"
                )
                break

    # ========================================================
    # NAVIGATION DETECTION
    # ========================================================

    def _detect_navigation(
        self,
        text,
        prefix,
        warnings,
    ):

        if not text.strip():
            return

        markdown_links = re.findall(
            r"\[[^\]]*\]\([^)]+\)",
            text,
        )

        words = re.findall(
            r"\b[\w'-]+\b",
            text,
        )

        if not words:
            return

        link_ratio = (
            len(markdown_links)
            / max(len(words), 1)
        )

        if (
            link_ratio
            >= self.navigation_ratio_threshold
        ):
            warnings.append(
                f"{prefix}: "
                f"navigation-heavy content"
            )
