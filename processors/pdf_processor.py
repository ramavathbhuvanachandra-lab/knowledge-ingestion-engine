from pathlib import Path
import json

from pypdf import PdfReader


class PDFProcessor:
    """
    Extract text from downloaded PDF documents.

    Phase 6.4 responsibilities:

    - Open a downloaded PDF.
    - Extract text page by page.
    - Preserve page boundaries.
    - Save extracted content as Markdown.
    - Save extraction metadata.
    - Do NOT perform OCR.
    - Do NOT process images.
    - Do NOT chunk or embed content.
    """

    def __init__(
        self,
        output_path: str | Path = "storage/processed_documents",
    ):
        self.output_path = Path(output_path)

    # ------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------

    def process(
        self,
        pdf_path: str | Path,
        source_url: str | None = None,
    ) -> Path:
        """
        Extract text from a PDF and save the processed document.

        Returns:
            Path to the generated Markdown file.
        """

        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(
                f"PDF file does not exist: {pdf_path}"
            )

        if not pdf_path.is_file():
            raise ValueError(
                f"PDF path is not a file: {pdf_path}"
            )

        if pdf_path.suffix.lower() != ".pdf":
            raise ValueError(
                f"Expected a PDF file: {pdf_path}"
            )

        # --------------------------------------------------------
        # READ PDF
        # --------------------------------------------------------

        reader = PdfReader(
            str(pdf_path)
        )

        total_pages = len(
            reader.pages
        )

        if total_pages == 0:
            raise ValueError(
                f"PDF contains no pages: {pdf_path}"
            )

        # --------------------------------------------------------
        # EXTRACT PAGE TEXT
        # --------------------------------------------------------

        pages = []

        for page_number, page in enumerate(
            reader.pages,
            start=1,
        ):

            text = page.extract_text()

            if text is None:
                text = ""

            text = text.strip()

            pages.append(
                {
                    "page_number": page_number,
                    "text": text,
                }
            )

        # --------------------------------------------------------
        # BUILD MARKDOWN
        # --------------------------------------------------------

        markdown_parts = []

        for page in pages:

            markdown_parts.append(
                f"## Page {page['page_number']}"
            )

            markdown_parts.append("")

            if page["text"]:
                markdown_parts.append(
                    page["text"]
                )
            else:
                markdown_parts.append(
                    "[No extractable text]"
                )

            markdown_parts.append("")

        markdown = "\n".join(
            markdown_parts
        ).strip()

        # --------------------------------------------------------
        # OUTPUT DIRECTORY
        # --------------------------------------------------------

        domain = pdf_path.parent.name

        output_dir = (
            self.output_path
            / domain
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        # --------------------------------------------------------
        # OUTPUT FILE
        # --------------------------------------------------------

        output_filename = (
            pdf_path.stem
            + ".md"
        )

        output_file = (
            output_dir
            / output_filename
        )

        output_file.write_text(
            markdown,
            encoding="utf-8",
        )

        # --------------------------------------------------------
        # METADATA
        # --------------------------------------------------------

        text_length = sum(
            len(page["text"])
            for page in pages
        )

        pages_with_text = sum(
            1
            for page in pages
            if page["text"]
        )

        metadata = {
            "source_url": source_url,
            "source_file": str(pdf_path),
            "document_type": "pdf",
            "pages": total_pages,
            "pages_with_text": pages_with_text,
            "text_length": text_length,
            "extraction_success": True,
        }

        metadata_file = (
            output_dir
            / f"{pdf_path.stem}.json"
        )

        metadata_file.write_text(
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
            f"Processed PDF : {pdf_path}"
        )

        print(
            f"Markdown      : {output_file}"
        )

        print(
            f"Metadata      : {metadata_file}"
        )

        print(
            f"Pages         : {total_pages}"
        )

        print(
            f"Pages w/text  : {pages_with_text}"
        )

        print(
            f"Text length   : {text_length}"
        )

        return output_file