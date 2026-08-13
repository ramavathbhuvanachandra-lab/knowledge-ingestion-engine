from pathlib import Path
import json


class RetrievalRecordBuilder:
    """
    Converts validated knowledge chunks into a stable
    retrieval-record format for downstream RAG systems.

    Phase 7.7 responsibilities:

    - Read chunked knowledge JSON.
    - Preserve chunk text.
    - Preserve chunk identity.
    - Preserve source/provenance metadata.
    - Add stable retrieval metadata.
    - Produce deterministic retrieval records.
    - Do NOT generate embeddings.
    - Do NOT connect to a vector database.
    - Do NOT modify the source chunks.
    """

    def __init__(
        self,
        output_path: str | Path = "storage/retrieval",
    ):
        self.output_path = Path(output_path)

    # ========================================================
    # PUBLIC API
    # ========================================================

    def process(
        self,
        chunk_path: str | Path,
    ) -> Path:
        """
        Convert one chunk JSON document into retrieval records.

        Returns:
            Path to generated retrieval JSON.
        """

        chunk_path = Path(chunk_path)

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

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

        # ----------------------------------------------------
        # LOAD SOURCE
        # ----------------------------------------------------

        data = json.loads(
            chunk_path.read_text(
                encoding="utf-8"
            )
        )

        document = data.get(
            "document",
            {}
        )

        chunks = data.get(
            "chunks",
            []
        )

        if not isinstance(document, dict):
            raise ValueError(
                "Invalid document metadata."
            )

        if not isinstance(chunks, list):
            raise ValueError(
                "Invalid chunks structure."
            )

        # ----------------------------------------------------
        # BUILD RETRIEVAL RECORDS
        # ----------------------------------------------------

        records = []

        for index, chunk in enumerate(
            chunks,
            start=1,
        ):

            if not isinstance(chunk, dict):
                raise ValueError(
                    f"Invalid chunk at index {index}."
                )

            chunk_id = chunk.get(
                "chunk_id"
            )

            text = chunk.get(
                "text"
            )

            metadata = chunk.get(
                "metadata",
                {}
            )

            if not chunk_id:
                raise ValueError(
                    f"Missing chunk_id at index {index}."
                )

            if not text or not str(text).strip():
                raise ValueError(
                    f"Empty chunk text: {chunk_id}"
                )

            if not isinstance(metadata, dict):
                raise ValueError(
                    f"Invalid metadata: {chunk_id}"
                )

            # ------------------------------------------------
            # SOURCE METADATA
            # ------------------------------------------------

            source_url = (
                metadata.get("source_url")
                or document.get("url")
            )

            domain = (
                metadata.get("domain")
                or document.get("domain")
            )

            category = (
                metadata.get("category")
                or document.get("category")
                or "others"
            )

            document_type = (
                metadata.get("document_type")
                or document.get("document_type")
                or "unknown"
            )

            source_document = (
                metadata.get("source_document")
                or chunk_path.name
            )

            page_number = metadata.get(
                "page_number"
            )

            section = metadata.get(
                "section"
            )

            title = (
                document.get("title")
                or ""
            )

            # ------------------------------------------------
            # RETRIEVAL RECORD
            # ------------------------------------------------

            record = {
                "record_id": chunk_id,

                "text": str(text).strip(),

                "metadata": {
                    "source_url": source_url,
                    "domain": domain,
                    "category": category,
                    "document_type": document_type,
                    "source_document": source_document,
                    "page_number": page_number,
                    "section": section,
                    "title": title,
                },

                "retrieval": {
                    "record_index": index,
                    "source_chunk_id": chunk_id,
                },
            }

            records.append(record)

        # ----------------------------------------------------
        # OUTPUT DIRECTORY
        # ----------------------------------------------------

        output_dir = (
            self.output_path
            / self._clean_component(
                document.get(
                    "domain",
                    "unknown"
                )
            )
            / self._clean_component(
                document.get(
                    "category",
                    "others"
                )
            )
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        # ----------------------------------------------------
        # OUTPUT FILE
        # ----------------------------------------------------

        output_file = (
            output_dir
            / chunk_path.name
        )

        output = {
            "document": {
                "title": document.get(
                    "title"
                ),
                "url": document.get(
                    "url"
                ),
                "domain": document.get(
                    "domain"
                ),
                "category": document.get(
                    "category"
                ),
                "document_type": document.get(
                    "document_type"
                ),
            },

            "retrieval": {
                "record_count": len(
                    records
                ),
                "embedding_ready": False,
                "vector_store_ready": False,
            },

            "records": records,
        }

        # ----------------------------------------------------
        # WRITE OUTPUT
        # ----------------------------------------------------

        output_file.write_text(
            json.dumps(
                output,
                indent=4,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        # ----------------------------------------------------
        # LOGGING
        # ----------------------------------------------------

        print(
            f"Retrieval JSON : {output_file}"
        )

        print(
            f"Records        : {len(records)}"
        )

        print(
            f"Source URL     : "
            f"{document.get('url')}"
        )

        return output_file

    # ========================================================
    # SAFE PATH COMPONENT
    # ========================================================

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
                cleaned.append(
                    "_"
                )

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