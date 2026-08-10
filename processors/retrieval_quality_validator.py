from pathlib import Path
import json
import re


class RetrievalQualityValidator:
    """
    Validates retrieval records before embedding/vector storage.

    Phase 7.8 responsibilities:

    - Validate retrieval-record structure.
    - Check that records contain usable text.
    - Check source/provenance metadata.
    - Detect obvious navigation/footer noise.
    - Detect duplicate records.
    - Calculate basic content-quality statistics.
    - Do NOT generate embeddings.
    - Do NOT call an LLM.
    - Do NOT connect to a vector database.
    """

    REQUIRED_METADATA = {
        "source_url",
        "domain",
        "category",
        "document_type",
        "source_document",
        "page_number",
        "section",
        "title",
    }

    NAVIGATION_PATTERNS = (
        "accessibility options",
        "follow us",
        "quick menu",
        "important links",
        "sitemap",
        "privacy policy",
        "web policy",
        "copyright",
        "created by",
    )

    def validate(
        self,
        retrieval_path: str | Path,
    ) -> dict:
        """
        Validate one retrieval JSON file.

        Returns:
            Validation result dictionary.
        """

        retrieval_path = Path(
            retrieval_path
        )

        if not retrieval_path.exists():
            raise FileNotFoundError(
                f"Retrieval file does not exist: "
                f"{retrieval_path}"
            )

        if not retrieval_path.is_file():
            raise ValueError(
                f"Retrieval path is not a file: "
                f"{retrieval_path}"
            )

        if retrieval_path.suffix.lower() != ".json":
            raise ValueError(
                f"Expected JSON file: "
                f"{retrieval_path}"
            )

        data = json.loads(
            retrieval_path.read_text(
                encoding="utf-8"
            )
        )

        document = data.get(
            "document",
            {}
        )

        retrieval = data.get(
            "retrieval",
            {}
        )

        records = data.get(
            "records",
            []
        )

        errors = []
        warnings = []

        # ----------------------------------------------------
        # TOP LEVEL VALIDATION
        # ----------------------------------------------------

        if not isinstance(
            document,
            dict,
        ):
            errors.append(
                "Document metadata is not an object."
            )

        if not isinstance(
            retrieval,
            dict,
        ):
            errors.append(
                "Retrieval metadata is not an object."
            )

        if not isinstance(
            records,
            list,
        ):
            errors.append(
                "Records is not a list."
            )

            return {
                "valid": False,
                "record_count": 0,
                "errors": errors,
                "warnings": warnings,
                "quality": {},
            }

        # ----------------------------------------------------
        # DOCUMENT METADATA
        # ----------------------------------------------------

        if not document.get("url"):
            errors.append(
                "Document is missing URL."
            )

        if not document.get("domain"):
            errors.append(
                "Document is missing domain."
            )

        if not document.get("category"):
            errors.append(
                "Document is missing category."
            )

        if not document.get("document_type"):
            warnings.append(
                "Document does not contain document_type."
            )

        # ----------------------------------------------------
        # RETRIEVAL FLAGS
        # ----------------------------------------------------

        if (
            retrieval.get(
                "record_count"
            )
            != len(records)
        ):
            errors.append(
                "Retrieval record_count does not "
                "match actual record count."
            )

        if retrieval.get(
            "embedding_ready"
        ) is not False:
            warnings.append(
                "embedding_ready is not False."
            )

        if retrieval.get(
            "vector_store_ready"
        ) is not False:
            warnings.append(
                "vector_store_ready is not False."
            )

        # ----------------------------------------------------
        # RECORD VALIDATION
        # ----------------------------------------------------

        record_ids = []
        text_lengths = []
        noisy_records = 0
        empty_records = 0

        for index, record in enumerate(
            records,
            start=1,
        ):

            prefix = (
                f"Record {index}"
            )

            if not isinstance(
                record,
                dict,
            ):
                errors.append(
                    f"{prefix}: record is not an object."
                )
                continue

            record_id = record.get(
                "record_id"
            )

            text = record.get(
                "text"
            )

            metadata = record.get(
                "metadata"
            )

            retrieval_metadata = record.get(
                "retrieval"
            )

            # ------------------------------------------------
            # ID
            # ------------------------------------------------

            if not record_id:
                errors.append(
                    f"{prefix}: missing record_id."
                )
            else:
                record_ids.append(
                    record_id
                )

            # ------------------------------------------------
            # TEXT
            # ------------------------------------------------

            if not isinstance(
                text,
                str,
            ):
                errors.append(
                    f"{prefix}: text is not a string."
                )
                continue

            text = text.strip()

            if not text:
                errors.append(
                    f"{prefix}: text is empty."
                )
                empty_records += 1
                continue

            text_lengths.append(
                len(text)
            )

            # ------------------------------------------------
            # TEXT QUALITY
            # ------------------------------------------------

            if self._looks_like_noise(
                text
            ):
                noisy_records += 1

                warnings.append(
                    f"{prefix} "
                    f"({record_id}): "
                    f"text appears navigation/noise-heavy."
                )

            # ------------------------------------------------
            # METADATA
            # ------------------------------------------------

            if not isinstance(
                metadata,
                dict,
            ):
                errors.append(
                    f"{prefix}: metadata is not an object."
                )
            else:

                missing_metadata = (
                    self.REQUIRED_METADATA
                    - set(metadata.keys())
                )

                for field in sorted(
                    missing_metadata
                ):
                    errors.append(
                        f"{prefix} "
                        f"({record_id}): "
                        f"missing metadata field: "
                        f"{field}"
                    )

                if not metadata.get(
                    "source_url"
                ):
                    errors.append(
                        f"{prefix} "
                        f"({record_id}): "
                        f"missing source_url."
                    )

                if not metadata.get(
                    "domain"
                ):
                    errors.append(
                        f"{prefix} "
                        f"({record_id}): "
                        f"missing domain."
                    )

            # ------------------------------------------------
            # RETRIEVAL METADATA
            # ------------------------------------------------

            if not isinstance(
                retrieval_metadata,
                dict,
            ):
                errors.append(
                    f"{prefix} "
                    f"({record_id}): "
                    f"retrieval metadata is invalid."
                )

            else:

                if (
                    retrieval_metadata.get(
                        "source_chunk_id"
                    )
                    != record_id
                ):
                    errors.append(
                        f"{prefix} "
                        f"({record_id}): "
                        f"source_chunk_id mismatch."
                    )

                if (
                    retrieval_metadata.get(
                        "record_index"
                    )
                    != index
                ):
                    errors.append(
                        f"{prefix} "
                        f"({record_id}): "
                        f"record_index mismatch."
                    )

        # ----------------------------------------------------
        # DUPLICATE IDs
        # ----------------------------------------------------

        duplicates = (
            len(record_ids)
            != len(set(record_ids))
        )

        if duplicates:
            errors.append(
                "Duplicate record IDs found."
            )

        # ----------------------------------------------------
        # QUALITY STATISTICS
        # ----------------------------------------------------

        if text_lengths:

            minimum_size = min(
                text_lengths
            )

            maximum_size = max(
                text_lengths
            )

            average_size = (
                sum(text_lengths)
                / len(text_lengths)
            )

        else:

            minimum_size = 0
            maximum_size = 0
            average_size = 0.0

        quality = {
            "record_count": len(records),
            "minimum_text_size": minimum_size,
            "maximum_text_size": maximum_size,
            "average_text_size": round(
                average_size,
                2,
            ),
            "noise_heavy_records": (
                noisy_records
            ),
            "empty_records": (
                empty_records
            ),
            "duplicate_record_ids": (
                duplicates
            ),
        }

        # ----------------------------------------------------
        # FINAL RESULT
        # ----------------------------------------------------

        valid = len(errors) == 0

        return {
            "valid": valid,
            "record_count": len(records),
            "errors": errors,
            "warnings": warnings,
            "quality": quality,
        }

    # ========================================================
    # NOISE DETECTION
    # ========================================================

    def _looks_like_noise(
        self,
        text: str,
    ) -> bool:
        """
        Conservative detection of navigation-heavy text.

        This does NOT reject the record.
        It only produces a warning.

        Useful institutional content must never be
        aggressively deleted at this stage.
        """

        normalized = re.sub(
            r"\s+",
            " ",
            text.lower(),
        ).strip()

        if not normalized:
            return True

        # ----------------------------------------------------
        # Strong single-purpose navigation text
        # ----------------------------------------------------

        if normalized in self.NAVIGATION_PATTERNS:
            return True

        # ----------------------------------------------------
        # Count navigation signals
        # ----------------------------------------------------

        signal_count = 0

        for pattern in self.NAVIGATION_PATTERNS:

            if pattern in normalized:
                signal_count += 1

        # ----------------------------------------------------
        # Link-heavy content
        # ----------------------------------------------------

        markdown_links = len(
            re.findall(
                r"\[[^\]]*\]\([^)]+\)",
                text,
            )
        )

        words = re.findall(
            r"\b\w+\b",
            text,
        )

        word_count = len(words)

        if word_count == 0:
            return True

        link_ratio = (
            markdown_links / word_count
        )

        # ----------------------------------------------------
        # Conservative decision
        # ----------------------------------------------------

        if (
            signal_count >= 3
            and link_ratio > 0.15
        ):
            return True

        if (
            signal_count >= 5
            and word_count < 250
        ):
            return True

        return False