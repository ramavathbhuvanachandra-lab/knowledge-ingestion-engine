from pathlib import Path
from urllib.parse import urlparse
import json
import re

import requests


class DocumentDownloader:
    """
    Downloads external documents discovered during crawling.

    Responsibilities:
    - Download supported documents.
    - Validate HTTP response.
    - Validate basic file content.
    - Store raw documents locally.
    - Store metadata beside the raw document.

    Document processing is handled separately.
    """

    SUPPORTED_TYPES = {
        ".pdf": "pdf",
        ".xlsx": "xlsx",
    }

    def __init__(
        self,
        base_path: str | Path = "storage/documents",
        timeout: int = 30,
    ):
        self.base_path = Path(base_path)
        self.timeout = timeout

    # ------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------

    def download(
        self,
        url: str,
        domain: str | None = None,
    ) -> Path:

        url = (url or "").strip()

        if not url:
            raise ValueError(
                "Document URL cannot be empty"
            )

        parsed = urlparse(url)

        if parsed.scheme not in (
            "http",
            "https",
        ):
            raise ValueError(
                f"Unsupported URL scheme: {url}"
            )

        if not parsed.netloc:
            raise ValueError(
                f"Invalid document URL: {url}"
            )

        # --------------------------------------------------------
        # DOCUMENT TYPE
        # --------------------------------------------------------

        document_type = self._detect_document_type(
            url
        )

        # --------------------------------------------------------
        # DOMAIN
        # --------------------------------------------------------

        if domain is None:
            domain = parsed.netloc

        domain = self._clean_component(
            domain
        )

        # --------------------------------------------------------
        # FILENAME
        # --------------------------------------------------------

        filename = self._build_filename(
            url
        )

        output_dir = (
            self.base_path
            / domain
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path = (
            output_dir
            / filename
        )

        # --------------------------------------------------------
        # DOWNLOAD
        # --------------------------------------------------------

        response = requests.get(
            url,
            timeout=self.timeout,
            allow_redirects=True,
        )

        response.raise_for_status()

        content = response.content

        if not content:
            raise RuntimeError(
                f"Downloaded document is empty: {url}"
            )

        # --------------------------------------------------------
        # VALIDATE CONTENT
        # --------------------------------------------------------

        if document_type == "pdf":

            if not self._looks_like_pdf(
                content
            ):
                raise ValueError(
                    f"Downloaded content is not a valid PDF: {url}"
                )

        elif document_type == "xlsx":

            if not self._looks_like_xlsx(
                content
            ):
                raise ValueError(
                    f"Downloaded content is not a valid XLSX: {url}"
                )

        # --------------------------------------------------------
        # SAVE RAW DOCUMENT
        # --------------------------------------------------------

        output_path.write_bytes(
            content
        )

        # --------------------------------------------------------
        # SAVE METADATA
        # --------------------------------------------------------

        metadata = {
            "source_url": url,
            "local_file": str(output_path),
            "domain": domain,
            "document_type": document_type,
            "size_bytes": len(content),
            "success": True,
        }

        metadata_path = (
            output_path.with_suffix(".json")
        )

        metadata_path.write_text(
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
            f"Downloaded Document : {output_path}"
        )

        print(
            f"Saved Metadata      : {metadata_path}"
        )

        print(
            f"Source URL          : {url}"
        )

        print(
            f"Document Type       : {document_type}"
        )

        print(
            f"Size                : {len(content)} bytes"
        )

        return output_path

    # ------------------------------------------------------------
    # DOCUMENT TYPE
    # ------------------------------------------------------------

    def _detect_document_type(
        self,
        url: str,
    ) -> str:

        parsed = urlparse(url)

        suffix = Path(
            parsed.path
        ).suffix.lower()

        document_type = (
            self.SUPPORTED_TYPES.get(
                suffix
            )
        )

        if document_type is None:

            raise ValueError(
                f"Unsupported document type: {url}"
            )

        return document_type

    # ------------------------------------------------------------
    # FILENAME
    # ------------------------------------------------------------

    def _build_filename(
        self,
        url: str,
    ) -> str:

        parsed = urlparse(url)

        raw_name = Path(
            parsed.path
        ).name

        if not raw_name:
            raw_name = "document"

        raw_name = raw_name.lower()

        raw_name = re.sub(
            r"[^a-z0-9._-]+",
            "_",
            raw_name,
        )

        raw_name = re.sub(
            r"_+",
            "_",
            raw_name,
        )

        return raw_name

    # ------------------------------------------------------------
    # PDF VALIDATION
    # ------------------------------------------------------------

    def _looks_like_pdf(
        self,
        content: bytes,
    ) -> bool:

        return content.startswith(
            b"%PDF-"
        )

    # ------------------------------------------------------------
    # XLSX VALIDATION
    # ------------------------------------------------------------

    def _looks_like_xlsx(
        self,
        content: bytes,
    ) -> bool:

        # XLSX files are ZIP containers.
        return content.startswith(
            b"PK"
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