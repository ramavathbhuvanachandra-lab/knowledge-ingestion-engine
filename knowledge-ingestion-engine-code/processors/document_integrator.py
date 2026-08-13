from pathlib import Path
import json
import shutil


class DocumentIntegrator:
    """
    Integrates processed external documents into
    the main knowledge storage.

    Phase 6.7 responsibilities:

    - Take a processed Markdown document.
    - Take its processing metadata.
    - Store both inside the main storage/output tree.
    - Preserve the original source URL.
    - Keep PDF processing separate from webpage processing.
    - Do not chunk.
    - Do not embed.
    - Do not modify the crawler.
    """

    def __init__(
        self,
        output_path: str | Path = "storage/output",
    ):
        self.output_path = Path(output_path)

    # ------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------

    def integrate(
        self,
        markdown_path: str | Path,
        metadata_path: str | Path,
        domain: str,
        category: str = "others",
    ) -> tuple[Path, Path]:
        """
        Integrate a processed document into the main
        knowledge output directory.

        Returns:
            (output_markdown_path, output_metadata_path)
        """

        markdown_path = Path(markdown_path)
        metadata_path = Path(metadata_path)

        # --------------------------------------------------------
        # VALIDATION
        # --------------------------------------------------------

        if not markdown_path.exists():
            raise FileNotFoundError(
                f"Markdown file does not exist: "
                f"{markdown_path}"
            )

        if not markdown_path.is_file():
            raise ValueError(
                f"Markdown path is not a file: "
                f"{markdown_path}"
            )

        if metadata_path.exists() is False:
            raise FileNotFoundError(
                f"Metadata file does not exist: "
                f"{metadata_path}"
            )

        if not metadata_path.is_file():
            raise ValueError(
                f"Metadata path is not a file: "
                f"{metadata_path}"
            )

        # --------------------------------------------------------
        # DOMAIN / CATEGORY
        # --------------------------------------------------------

        domain = self._clean_component(
            domain
        )

        category = self._clean_component(
            category
        )

        output_dir = (
            self.output_path
            / domain
            / category
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        # --------------------------------------------------------
        # FILENAMES
        # --------------------------------------------------------

        markdown_output = (
            output_dir
            / markdown_path.name
        )

        metadata_output = (
            output_dir
            / metadata_path.name
        )

        # --------------------------------------------------------
        # COPY MARKDOWN
        # --------------------------------------------------------

        shutil.copy2(
            markdown_path,
            markdown_output,
        )

        # --------------------------------------------------------
        # COPY / ENRICH METADATA
        # --------------------------------------------------------

        metadata = json.loads(
            metadata_path.read_text(
                encoding="utf-8"
            )
        )

        metadata[
            "storage_domain"
        ] = domain

        metadata[
            "storage_category"
        ] = category

        metadata[
            "storage_path"
        ] = str(
            markdown_output
        )

        metadata_output.write_text(
            json.dumps(
                metadata,
                indent=4,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        # --------------------------------------------------------
        # LOGGING
        # --------------------------------------------------------

        print(
            f"Integrated Markdown : "
            f"{markdown_output}"
        )

        print(
            f"Integrated Metadata : "
            f"{metadata_output}"
        )

        return (
            markdown_output,
            metadata_output,
        )

    # ------------------------------------------------------------
    # SAFE COMPONENT
    # ------------------------------------------------------------

    def _clean_component(
        self,
        value: str,
    ) -> str:
        value = (
            value or ""
        ).strip().lower()

        cleaned = []

        for character in value:

            if (
                character.isalnum()
                or character in "._-"
            ):
                cleaned.append(
                    character
                )
            else:
                cleaned.append("_")

        result = "".join(
            cleaned
        )

        while "__" in result:
            result = result.replace(
                "__",
                "_",
            )

        return (
            result.strip("._-")
            or "unknown"
        )