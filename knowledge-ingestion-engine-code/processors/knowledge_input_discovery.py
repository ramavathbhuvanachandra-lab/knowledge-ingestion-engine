from dataclasses import dataclass
from pathlib import Path
import json


@dataclass
class KnowledgeInput:
    """
    Represents one knowledge document entering Phase 7.
    """

    markdown_path: Path
    metadata_path: Path
    domain: str
    category: str
    metadata: dict


class KnowledgeInputDiscovery:
    """
    Discovers Markdown + metadata pairs from the
    main knowledge storage.

    Phase 7.1 responsibilities:

    - Discover Markdown files.
    - Find their corresponding JSON metadata.
    - Load and validate metadata.
    - Identify domain and category from storage paths.
    - Do not modify content.
    - Do not clean content.
    - Do not chunk content.
    - Do not embed content.
    """

    def __init__(
        self,
        input_path: str | Path = "storage/output",
    ):
        self.input_path = Path(input_path)

    # --------------------------------------------------------
    # PUBLIC API
    # --------------------------------------------------------

    def discover(self) -> list[KnowledgeInput]:
        """
        Discover all valid Markdown + metadata pairs.

        Returns:
            List of KnowledgeInput objects.
        """

        if not self.input_path.exists():
            raise FileNotFoundError(
                f"Knowledge input directory does not exist: "
                f"{self.input_path}"
            )

        if not self.input_path.is_dir():
            raise ValueError(
                f"Knowledge input path is not a directory: "
                f"{self.input_path}"
            )

        markdown_files = sorted(
            self.input_path.rglob("*.md")
        )

        knowledge_inputs = []

        for markdown_path in markdown_files:

            metadata_path = (
                markdown_path.with_suffix(".json")
            )

            if not metadata_path.exists():
                raise FileNotFoundError(
                    "Missing metadata for Markdown file: "
                    f"{markdown_path}"
                )

            if not metadata_path.is_file():
                raise ValueError(
                    "Metadata path is not a file: "
                    f"{metadata_path}"
                )

            metadata = self._load_metadata(
                metadata_path
            )

            domain = (
                markdown_path.relative_to(
                    self.input_path
                ).parts[0]
            )

            relative_parts = (
                markdown_path.relative_to(
                    self.input_path
                ).parts
            )

            if len(relative_parts) >= 3:
                category = relative_parts[-2]
            else:
                category = "others"

            knowledge_inputs.append(
                KnowledgeInput(
                    markdown_path=markdown_path,
                    metadata_path=metadata_path,
                    domain=domain,
                    category=category,
                    metadata=metadata,
                )
            )

        return knowledge_inputs

    # --------------------------------------------------------
    # METADATA
    # --------------------------------------------------------

    def _load_metadata(
        self,
        metadata_path: Path,
    ) -> dict:

        try:
            metadata = json.loads(
                metadata_path.read_text(
                    encoding="utf-8"
                )
            )

        except json.JSONDecodeError as error:

            raise ValueError(
                f"Invalid JSON metadata: "
                f"{metadata_path}"
            ) from error

        if not isinstance(
            metadata,
            dict,
        ):
            raise ValueError(
                f"Metadata must be a JSON object: "
                f"{metadata_path}"
            )

        return metadata