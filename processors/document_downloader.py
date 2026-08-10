from pathlib import Path
from urllib.parse import urlparse
import json
import re

import requests


class DocumentDownloader:
    """
    Downloads external documents discovered during crawling.

    Phase 6.2:
        - Download PDF documents.
        - Validate HTTP response.
        - Validate PDF content.
        - Store raw PDF locally.

    Phase 6.3:
        - Store metadata beside the raw PDF.

    PDF extraction and processing are intentionally
    NOT handled here.
    """

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
        """
        Download a PDF and return its local path.
        """

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

        # --------------------------------------------------------
        # VALIDATE CONTENT
        # --------------------------------------------------------

        content = response.content

        if not content:
            raise RuntimeError(
                f"Downloaded document is empty: {url}"
            )

        if not self._looks_like_pdf(
            content
        ):
            raise ValueError(
                f"Downloaded content is not a valid PDF: {url}"
            )

        # --------------------------------------------------------
        # SAVE RAW PDF
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
            "document_type": "pdf",
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
            f"Size                : {len(content)} bytes"
        )

        return output_path

    # ------------------------------------------------------------
    # FILENAME
    # ------------------------------------------------------------

    def _build_filename(
        self,
        url: str,
    ) -> str:
        """
        Build a safe filename from the URL.
        """

        parsed = urlparse(url)

        raw_name = Path(
            parsed.path
        ).name

        if not raw_name:
            raw_name = "document.pdf"

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

        if not raw_name.endswith(".pdf"):
            raw_name += ".pdf"

        return raw_name

    # ------------------------------------------------------------
    # PDF VALIDATION
    # ------------------------------------------------------------

    def _looks_like_pdf(
        self,
        content: bytes,
    ) -> bool:
        """
        Check the PDF magic header.

        Real PDF files normally begin with:

            %PDF-
        """

        return content.startswith(
            b"%PDF-"
        )

    # ------------------------------------------------------------
    # SAFE PATH COMPONENT
    # ------------------------------------------------------------

    def _clean_component(
        self,
        value: str,
    ) -> str:

        value = value.lower()

        value = re.sub(
            r"[^a-z0-9._-]+",
            "_",
            value,
        )

        value = re.sub(
            r"_+",
            "_",
            value,
        )

        return value.strip(
            "._-"
        ) or "unknown"