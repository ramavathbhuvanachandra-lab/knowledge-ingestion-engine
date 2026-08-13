from pathlib import Path
import json

from processors.knowledge_chunker import KnowledgeChunker


# ============================================================
# PHASE 7.5 — REAL KNOWLEDGE CHUNKING TEST
# ============================================================

TEST_DOCUMENTS = [
    Path(
        "storage/structured_knowledge/"
        "iitj.ac.in/others/search.json"
    ),
    Path(
        "storage/structured_knowledge/"
        "gwpgc.ac.in/others/"
        "government_girls_p_g_college_ghazipur.json"
    ),
    Path(
        "storage/structured_knowledge/"
        "home.iitd.ac.in/others/"
        "newsletter-apr-26-issue.json"
    ),
]


def validate_chunk_file(
    chunk_path: Path,
    source_path: Path,
):
    assert chunk_path.exists(), (
        f"Chunk output missing: {chunk_path}"
    )

    assert chunk_path.is_file(), (
        f"Chunk output is not a file: {chunk_path}"
    )

    data = json.loads(
        chunk_path.read_text(
            encoding="utf-8"
        )
    )

    # ========================================================
    # TOP LEVEL
    # ========================================================

    assert "document" in data, (
        "Missing document metadata"
    )

    assert "chunking" in data, (
        "Missing chunking metadata"
    )

    assert "chunks" in data, (
        "Missing chunks"
    )

    document = data["document"]
    chunks = data["chunks"]

    assert isinstance(
        chunks,
        list,
    ), "chunks must be a list"

    

    # ========================================================
    # DOCUMENT METADATA
    # ========================================================

    required_document_fields = [
        "url",
        "domain",
        "category",
        "document_type",
    ]

    for field in required_document_fields:

        assert field in document, (
            f"Missing document field: {field}"
        )

        assert document[field] is not None, (
            f"Document field is None: {field}"
        )

    # ========================================================
    # CHUNK COUNT
    # ========================================================

    assert (
        data["chunking"]["chunk_count"]
        == len(chunks)
    )

    # ========================================================
    # CHUNK VALIDATION
    # ========================================================

    seen_ids = set()

    for index, chunk in enumerate(chunks):

        assert "chunk_id" in chunk, (
            f"Chunk {index} missing chunk_id"
        )

        assert "text" in chunk, (
            f"Chunk {index} missing text"
        )

        assert "metadata" in chunk, (
            f"Chunk {index} missing metadata"
        )

        chunk_id = chunk["chunk_id"]

        assert chunk_id not in seen_ids, (
            f"Duplicate chunk ID: {chunk_id}"
        )

        seen_ids.add(chunk_id)

        text = chunk["text"]

        assert isinstance(
            text,
            str,
        ), f"Chunk {index} text is not string"

        assert text.strip(), (
            f"Chunk {index} has empty text"
        )

        metadata = chunk["metadata"]

        required_metadata = [
            "source_url",
            "domain",
            "category",
            "document_type",
            "source_document",
            "page_number",
            "section",
        ]

        for field in required_metadata:

            assert field in metadata, (
                f"Chunk {index} missing metadata: "
                f"{field}"
            )

        # ----------------------------------------------------
        # SOURCE URL MUST BE PRESERVED
        # ----------------------------------------------------

        assert (
            metadata["source_url"]
            == document["url"]
        ), (
            f"Chunk {index} source URL mismatch"
        )

        # ----------------------------------------------------
        # DOMAIN MUST BE PRESERVED
        # ----------------------------------------------------

        assert (
            metadata["domain"]
            == document["domain"]
        ), (
            f"Chunk {index} domain mismatch"
        )

        # ----------------------------------------------------
        # CATEGORY MUST BE PRESERVED
        # ----------------------------------------------------

        assert (
            metadata["category"]
            == document["category"]
        ), (
            f"Chunk {index} category mismatch"
        )

        # ----------------------------------------------------
        # DOCUMENT TYPE MUST BE PRESERVED
        # ----------------------------------------------------

        assert (
            metadata["document_type"]
            == document["document_type"]
        ), (
            f"Chunk {index} document type mismatch"
        )

        # ----------------------------------------------------
        # SOURCE DOCUMENT
        # ----------------------------------------------------

        assert (
            metadata["source_document"]
            == source_path.name
        ), (
            f"Chunk {index} source document mismatch"
        )

    print(
        f"Validated chunks : {len(chunks)}"
    )


def test_document(
    chunker: KnowledgeChunker,
    source_path: Path,
):
    print("\n" + "=" * 80)
    print("TESTING KNOWLEDGE CHUNKING")
    print("=" * 80)

    print(
        "Input JSON :",
        source_path,
    )

    assert source_path.exists(), (
        f"Structured input missing: {source_path}"
    )

    # ========================================================
    # CHUNK
    # ========================================================

    output_path = chunker.process(
        structured_path=source_path
    )

    # ========================================================
    # VALIDATE
    # ========================================================

    validate_chunk_file(
        chunk_path=output_path,
        source_path=source_path,
    )

    data = json.loads(
        output_path.read_text(
            encoding="utf-8"
        )
    )

    print(
        "Output JSON :",
        output_path,
    )

    print(
        "Chunks      :",
        len(data["chunks"]),
    )

    print(
        "Source URL  :",
        data["document"]["url"],
    )

    # ========================================================
    # SAMPLE CHUNKS
    # ========================================================

    print("\nSAMPLE CHUNKS")

    for chunk in data["chunks"][:3]:

        print("\n------------------------------")

        print(
            "Chunk ID :",
            chunk["chunk_id"],
        )

        print(
            "Page     :",
            chunk["metadata"]["page_number"],
        )

        print(
            "Section  :",
            chunk["metadata"]["section"],
        )

        print(
            "Text     :",
            chunk["text"][:300]
            .replace("\n", " "),
        )

    print("\nPASS")


def main():

    print(
        "\nPHASE 7.5 — KNOWLEDGE CHUNKING"
    )

    chunker = KnowledgeChunker(
        output_path="storage/chunks",
        max_chunk_size=1200,
        min_chunk_size=80,
    )

    passed = 0

    for document in TEST_DOCUMENTS:

        test_document(
            chunker=chunker,
            source_path=document,
        )

        passed += 1

    print("\n" + "=" * 80)

    print(
        f"Documents passed: "
        f"{passed} / {len(TEST_DOCUMENTS)}"
    )

    assert passed == len(TEST_DOCUMENTS)

    print(
        "PHASE 7.5 KNOWLEDGE CHUNKING: PASS"
    )


if __name__ == "__main__":
    main()