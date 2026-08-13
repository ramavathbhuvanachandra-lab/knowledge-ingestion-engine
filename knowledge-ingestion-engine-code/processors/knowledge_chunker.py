from pathlib import Path
import json
import re


class KnowledgeChunker:
    """
    Converts structured knowledge documents into
    retrieval-ready semantic chunks.

    Phase 7.5 responsibilities:

    - Read structured knowledge JSON.
    - Preserve document metadata.
    - Preserve page boundaries.
    - Preserve section information.
    - Remove obvious empty/noise/navigation content.
    - Preserve useful institutional links/content.
    - Split oversized content into smaller chunks.
    - Produce deterministic chunk IDs.
    - Do NOT generate embeddings.
    - Do NOT modify the source document.
    """

    def __init__(
        self,
        output_path: str | Path = "storage/chunks",
        max_chunk_size: int = 1200,
        min_chunk_size: int = 80,
    ):
        self.output_path = Path(output_path)
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size

    # ========================================================
    # PUBLIC API
    # ========================================================

    def process(
        self,
        structured_path: str | Path,
    ) -> Path:
        """
        Convert one structured JSON document into
        chunked JSON.

        Returns:
            Path to generated chunk file.
        """

        structured_path = Path(structured_path)

        if not structured_path.exists():
            raise FileNotFoundError(
                f"Structured document does not exist: "
                f"{structured_path}"
            )

        if not structured_path.is_file():
            raise ValueError(
                f"Structured path is not a file: "
                f"{structured_path}"
            )

        if structured_path.suffix.lower() != ".json":
            raise ValueError(
                f"Expected JSON file: {structured_path}"
            )

        data = json.loads(
            structured_path.read_text(
                encoding="utf-8"
            )
        )

        document = data.get(
            "document",
            {}
        )

        pages = data.get(
            "pages",
            []
        )

        chunks = []

        chunk_counter = 1

        # ====================================================
        # PROCESS PAGES
        # ====================================================

        for page in pages:

            page_number = page.get(
                "page_number"
            )

            sections = page.get(
                "sections",
                []
            )

            for section in sections:  
                if section.get("content_type") != "knowledge":
                    continue

                

                heading = section.get(
                    "heading"
                )

                content = section.get(
                    "content",
                    []
                )

                cleaned_content = (
                    self._clean_content(
                        content
                    )
                )

                if not cleaned_content:
                    continue

                section_text = "\n".join(
                    cleaned_content
                )

                pieces = (
                    self._split_text(
                        section_text
                    )
                )

                for piece in pieces:

                    piece = piece.strip()

                    if not piece:
                        continue

                    if (
                        len(piece)
                        < self.min_chunk_size
                    ):
                        continue

                    chunk = {
                        "chunk_id": (
                            f"{document.get('domain', 'unknown')}"
                            f"_"
                            f"{structured_path.stem}"
                            f"_"
                            f"{chunk_counter:04d}"
                        ),
                        "text": piece,
                        "metadata": {
                            "source_url": document.get(
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
                            "source_document": (
                                structured_path.name
                            ),
                            "page_number": page_number,
                            "section": heading,
                        },
                    }

                    chunks.append(
                        chunk
                    )

                    chunk_counter += 1

        # ====================================================
        # OUTPUT DIRECTORY
        # ====================================================

        domain = str(
            document.get(
                "domain",
                "unknown"
            )
        )

        category = str(
            document.get(
                "category",
                "others"
            )
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

        # ====================================================
        # OUTPUT FILE
        # ====================================================

        output_file = (
            output_dir
            / structured_path.name
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
            "chunking": {
                "chunk_count": len(chunks),
                "max_chunk_size": (
                    self.max_chunk_size
                ),
                "min_chunk_size": (
                    self.min_chunk_size
                ),
            },
            "chunks": chunks,
        }

        output_file.write_text(
            json.dumps(
                output,
                indent=4,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        # ====================================================
        # LOGGING
        # ====================================================

        print(
            f"Chunked JSON : {output_file}"
        )

        print(
            f"Chunks       : {len(chunks)}"
        )

        print(
            f"Source URL   : "
            f"{document.get('url')}"
        )

        return output_file

    # ========================================================
    # CONTENT CLEANING
    # ========================================================

    def _clean_content(
        self,
        content: list,
    ) -> list[str]:
        """
        Clean structured content while preserving
        meaningful institutional information.
        """

        cleaned = []

        for item in content:

            if item is None:
                continue

            text = str(item).strip()

            if not text:
                continue

            # ----------------------------------------------
            # REMOVE KNOWN NOISE
            # ----------------------------------------------

            if self._is_noise(text):
                continue

            # ----------------------------------------------
            # NORMALIZE MARKDOWN LINKS
            # ----------------------------------------------

            text = self._normalize_markdown(
                text
            )

            text = text.strip()

            if not text:
                continue

            # ----------------------------------------------
            # REMOVE NAVIGATION-HEAVY BLOCKS
            # ----------------------------------------------

            if self._is_navigation_block(text):
                continue

            # ----------------------------------------------
            # FINAL EMPTY CHECK
            # ----------------------------------------------

            if not text.strip():
                continue

            cleaned.append(text)

        return cleaned

    # ========================================================
    # MARKDOWN NORMALIZATION
    # ========================================================

    def _normalize_markdown(
        self,
        text: str,
    ) -> str:
        """
        Convert Markdown links/images into readable text.

        Example:

        [Departments](https://example.com/departments)

        becomes:

        Departments
        """

        # ----------------------------------------------------
        # Images
        # ----------------------------------------------------

        text = re.sub(
            r"!\[([^\]]*)\]\([^)]+\)",
            r"\1",
            text,
        )

        # ----------------------------------------------------
        # Markdown links
        # ----------------------------------------------------

        text = re.sub(
            r"\[([^\]]+)\]\([^)]+\)",
            r"\1",
            text,
        )

        # ----------------------------------------------------
        # Bare URLs
        # ----------------------------------------------------

        text = re.sub(
            r"https?://\S+",
            "",
            text,
        )

        # ----------------------------------------------------
        # HTML tags
        # ----------------------------------------------------

        text = re.sub(
            r"<[^>]+>",
            " ",
            text,
        )

        # ----------------------------------------------------
        # Repeated whitespace
        # ----------------------------------------------------

        text = re.sub(
            r"[ \t]+",
            " ",
            text,
        )

        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text,
        )

        return text.strip()

    # ========================================================
    # NOISE DETECTION
    # ========================================================

    def _is_noise(
        self,
        text: str,
    ) -> bool:
        """
        Conservative noise detection.

        We remove obvious technical/UI noise but avoid
        deleting potentially useful institutional information.
        """

        lower = text.lower().strip()

        # ----------------------------------------------------
        # Empty / extraction placeholders
        # ----------------------------------------------------

        if lower in {
            "[no extractable text]",
            "arrow_downward️",
        }:
            return True

        # ----------------------------------------------------
        # Known IITJ technical marker
        # ----------------------------------------------------

        if lower.startswith(
            "###147852369"
        ):
            return True

        # ----------------------------------------------------
        # Data URI / technical image noise
        # ----------------------------------------------------

        if lower.startswith(
            "![icon](data:image/"
        ):
            return True

        # ----------------------------------------------------
        # Accessibility UI noise
        # ----------------------------------------------------

        accessibility_terms = [
            "accessibility options ctrl+f2",
            "open the accessibility option",
            "bigger text",
            "smaller text",
            "text spacing",
            "line height",
            "dyslexia friendly",
            "adhd mode",
            "saturation low saturation high",
            "desaturate",
            "light-dark",
            "invert colors",
            "highlight links",
            "text to speech",
            "pause animation",
            "hide images",
            "reset all settings",
        ]

        if any(
            term in lower
            for term in accessibility_terms
        ):
            return True

        return False

    # ========================================================
    # NAVIGATION DETECTION
    # ========================================================

    def _is_navigation_block(
        self,
        text: str,
    ) -> bool:
        """
        Detect blocks dominated by website navigation.

        This is intentionally conservative.

        We do NOT remove every list or every link.
        We only remove content that strongly resembles
        global website navigation.
        """

        normalized = text.lower().strip()

        if not normalized:
            return True

        words = normalized.split()

        if not words:
            return True

        # ----------------------------------------------------
        # Very short navigation labels
        # ----------------------------------------------------

        navigation_terms = {
            "home",
            "about",
            "about us",
            "academics",
            "admissions",
            "administration",
            "research",
            "students",
            "faculty",
            "contact",
            "sitemap",
            "help",
            "login",
            "search",
            "important links",
            "resources",
            "departments",
            "schools",
            "centers",
            "infrastructure",
            "alumni",
        }

        if normalized in navigation_terms:
            return True

        # ----------------------------------------------------
        # Count navigation labels
        # ----------------------------------------------------

        nav_hits = 0

        for term in navigation_terms:

            if re.search(
                rf"\b{re.escape(term)}\b",
                normalized,
            ):
                nav_hits += 1

        # ----------------------------------------------------
        # Link-heavy original blocks
        #
        # At this point Markdown links have already been
        # converted into labels, so use the number of
        # navigation labels + overall density.
        # ----------------------------------------------------

        if len(words) <= 80:

            if nav_hits >= 5:
                return True

        # ----------------------------------------------------
        # Common global-header pattern
        # ----------------------------------------------------

        header_patterns = [
            "a+ a a-",
            "hindi",
            "follow us",
            "copyright",
            "all rights reserved",
            "designed and developed by",
        ]

        header_hits = sum(
            1
            for pattern in header_patterns
            if pattern in normalized
        )

        if header_hits >= 2:
            return True

        # ----------------------------------------------------
        # Mostly short navigation labels
        # ----------------------------------------------------

        short_words = [
            word
            for word in words
            if len(word) <= 20
        ]

        if (
            len(words) >= 6
            and len(short_words) == len(words)
            and nav_hits >= 4
        ):
            return True

        return False

    # ========================================================
    # TEXT SPLITTING
    # ========================================================

    def _split_text(
        self,
        text: str,
    ) -> list[str]:
        """
        Split text into chunks without breaking words.

        Preference order:

        1. Paragraph boundaries
        2. Sentence boundaries
        3. Word boundaries
        """

        text = text.strip()

        if not text:
            return []

        if len(text) <= self.max_chunk_size:
            return [text]

        # ----------------------------------------------------
        # First split by paragraphs
        # ----------------------------------------------------

        paragraphs = re.split(
            r"\n\s*\n",
            text,
        )

        paragraphs = [
            paragraph.strip()
            for paragraph in paragraphs
            if paragraph.strip()
        ]

        chunks = []

        current = ""

        for paragraph in paragraphs:

            # ----------------------------------------------
            # Paragraph itself fits
            # ----------------------------------------------

            if len(paragraph) <= self.max_chunk_size:

                if not current:

                    current = paragraph

                elif (
                    len(current)
                    + 2
                    + len(paragraph)
                    <= self.max_chunk_size
                ):

                    current += (
                        "\n\n"
                        + paragraph
                    )

                else:

                    chunks.append(
                        current
                    )

                    current = paragraph

                continue

            # ----------------------------------------------
            # Flush current chunk
            # ----------------------------------------------

            if current:

                chunks.append(
                    current
                )

                current = ""

            # ----------------------------------------------
            # Split oversized paragraph
            # ----------------------------------------------

            paragraph_chunks = (
                self._split_large_text(
                    paragraph
                )
            )

            chunks.extend(
                paragraph_chunks
            )

        if current:

            chunks.append(
                current
            )

        return [
            chunk.strip()
            for chunk in chunks
            if chunk.strip()
        ]

    # ========================================================
    # LARGE TEXT SPLITTER
    # ========================================================

    def _split_large_text(
        self,
        text: str,
    ) -> list[str]:
        """
        Split oversized text using sentence boundaries
        and finally word boundaries.
        """

        sentences = re.split(
            r"(?<=[.!?])\s+",
            text,
        )

        sentences = [
            sentence.strip()
            for sentence in sentences
            if sentence.strip()
        ]

        chunks = []

        current = ""

        for sentence in sentences:

            # ------------------------------------------------
            # Sentence itself is too large
            # ------------------------------------------------

            if len(sentence) > self.max_chunk_size:

                if current:

                    chunks.append(
                        current
                    )

                    current = ""

                chunks.extend(
                    self._split_by_words(
                        sentence
                    )
                )

                continue

            # ------------------------------------------------
            # Add sentence to current chunk
            # ------------------------------------------------

            if not current:

                current = sentence

            elif (
                len(current)
                + 1
                + len(sentence)
                <= self.max_chunk_size
            ):

                current += (
                    " "
                    + sentence
                )

            else:

                chunks.append(
                    current
                )

                current = sentence

        if current:

            chunks.append(
                current
            )

        return chunks

    # ========================================================
    # WORD SPLITTER
    # ========================================================

    def _split_by_words(
        self,
        text: str,
    ) -> list[str]:
        """
        Final fallback splitter based on word boundaries.
        """

        words = text.split()

        chunks = []

        current_words = []
        current_length = 0

        for word in words:

            additional_length = (
                len(word)
                if not current_words
                else len(word) + 1
            )

            if (
                current_words
                and
                current_length
                + additional_length
                > self.max_chunk_size
            ):

                chunks.append(
                    " ".join(
                        current_words
                    )
                )

                current_words = [
                    word
                ]

                current_length = len(word)

            else:

                current_words.append(
                    word
                )

                current_length += (
                    additional_length
                )

        if current_words:

            chunks.append(
                " ".join(
                    current_words
                )
            )

        return chunks