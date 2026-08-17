from pathlib import Path
import json

from processors.retrieval_record_builder import (
    RetrievalRecordBuilder,
)


# ============================================================
# PHASE 7.7 — REAL RETRIEVAL RECORD TEST
# ============================================================

TEST_CHUNKS = [
    
    Path(
        "storage/chunks/gwpgc.ac.in/others/"
        "government_girls_p_g_college_ghazipur.json"
    ),
    Path(
        "storage/chunks/home.iitd.ac.in/others/"
        "newsletter-apr-26-issue.json"
    ),
]


# ============================================================
# TEST ONE DOCUMENT
# ============================================================

def test_retrieval_records(
    builder: RetrievalRecordBuilder,
    chunk_path: Path,
) -> None:

    print("\n" + "=" * 100)
    print("TESTING RETRIEVAL RECORD BUILDER")
    print("=" * 100)

    print("Input JSON :", chunk_path)

    # --------------------------------------------------------
    # INPUT VALIDATION
    # --------------------------------------------------------

    assert chunk_path.exists(), (
        f"Chunk file does not exist: {chunk_path}"
    )

    assert chunk_path.is_file(), (
        f"Chunk path is not a file: {chunk_path}"
    )

    # --------------------------------------------------------
    # LOAD SOURCE CHUNKS
    # --------------------------------------------------------

    source_data = json.loads(
        chunk_path.read_text(
            encoding="utf-8"
        )
    )

    source_document = source_data.get(
        "document",
        {}
    )

    source_chunks = source_data.get(
        "chunks",
        []
    )

    assert source_chunks, (
        f"No chunks found: {chunk_path}"
    )

    # --------------------------------------------------------
    # PROCESS
    # --------------------------------------------------------

    retrieval_path = builder.process(
        chunk_path
    )

    # --------------------------------------------------------
    # OUTPUT VALIDATION
    # --------------------------------------------------------

    assert retrieval_path.exists(), (
        f"Retrieval output missing: "
        f"{retrieval_path}"
    )

    assert retrieval_path.is_file(), (
        f"Retrieval output is not a file: "
        f"{retrieval_path}"
    )

    print(
        "Retrieval JSON :",
        retrieval_path
    )

    # --------------------------------------------------------
    # LOAD RETRIEVAL DATA
    # --------------------------------------------------------

    retrieval_data = json.loads(
        retrieval_path.read_text(
            encoding="utf-8"
        )
    )

    records = retrieval_data.get(
        "records",
        []
    )

    retrieval_info = retrieval_data.get(
        "retrieval",
        {}
    )

    # --------------------------------------------------------
    # RECORD COUNT
    # --------------------------------------------------------

    assert len(records) == len(
        source_chunks
    ), (
        "Retrieval record count does not "
        "match source chunk count."
    )

    assert (
        retrieval_info["record_count"]
        == len(records)
    )

    # --------------------------------------------------------
    # DOCUMENT METADATA
    # --------------------------------------------------------

    output_document = retrieval_data.get(
        "document",
        {}
    )

    assert (
        output_document.get("url")
        == source_document.get("url")
    )

    assert (
        output_document.get("domain")
        == source_document.get("domain")
    )

    assert (
        output_document.get("category")
        == source_document.get("category")
    )

    assert (
        output_document.get("document_type")
        == source_document.get("document_type")
    )

    # --------------------------------------------------------
    # RETRIEVAL FLAGS
    # --------------------------------------------------------

    assert (
        retrieval_info.get(
            "embedding_ready"
        )
        is False
    )

    assert (
        retrieval_info.get(
            "vector_store_ready"
        )
        is False
    )

    # --------------------------------------------------------
    # RECORD VALIDATION
    # --------------------------------------------------------

    source_ids = []

    for index, record in enumerate(
        records,
        start=1,
    ):

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

        # ----------------------------------------------------
        # ID
        # ----------------------------------------------------

        assert record_id, (
            f"Missing record_id at record {index}"
        )

        source_ids.append(
            record_id
        )

        # ----------------------------------------------------
        # TEXT
        # ----------------------------------------------------

        assert isinstance(
            text,
            str,
        ), (
            f"Record text is not a string: "
            f"{record_id}"
        )

        assert text.strip(), (
            f"Record text is empty: "
            f"{record_id}"
        )

        # ----------------------------------------------------
        # METADATA
        # ----------------------------------------------------

        assert isinstance(
            metadata,
            dict,
        ), (
            f"Invalid metadata: "
            f"{record_id}"
        )

        assert metadata.get(
            "source_url"
        ), (
            f"Missing source URL: "
            f"{record_id}"
        )

        assert metadata.get(
            "domain"
        ), (
            f"Missing domain: "
            f"{record_id}"
        )

        assert metadata.get(
            "category"
        ), (
            f"Missing category: "
            f"{record_id}"
        )

        assert metadata.get(
            "document_type"
        ), (
            f"Missing document type: "
            f"{record_id}"
        )

        assert metadata.get(
            "source_document"
        ), (
            f"Missing source document: "
            f"{record_id}"
        )

        assert (
            "page_number" in metadata
        ), (
            f"Missing page_number field: "
            f"{record_id}"
        )

        assert (
            "section" in metadata
        ), (
            f"Missing section field: "
            f"{record_id}"
        )

        # ----------------------------------------------------
        # RETRIEVAL METADATA
        # ----------------------------------------------------

        assert isinstance(
            retrieval_metadata,
            dict,
        ), (
            f"Invalid retrieval metadata: "
            f"{record_id}"
        )

        assert (
            retrieval_metadata.get(
                "source_chunk_id"
            )
            == record_id
        ), (
            f"Chunk-to-record mapping broken: "
            f"{record_id}"
        )

        assert (
            retrieval_metadata.get(
                "record_index"
            )
            == index
        ), (
            f"Incorrect record index: "
            f"{record_id}"
        )

    # --------------------------------------------------------
    # UNIQUE IDS
    # --------------------------------------------------------

    assert len(source_ids) == len(
        set(source_ids)
    ), (
        f"Duplicate record IDs found: "
        f"{chunk_path}"
    )

    # --------------------------------------------------------
    # SOURCE URL CONSISTENCY
    # --------------------------------------------------------

    source_url = source_document.get(
        "url"
    )

    for record in records:

        assert (
            record["metadata"]["source_url"]
            == source_url
        ), (
            "Record source URL does not "
            "match document source URL."
        )

    # --------------------------------------------------------
    # SAMPLE RECORDS
    # --------------------------------------------------------

    print(
        "Records       :",
        len(records)
    )

    print(
        "Source URL    :",
        source_url
    )

    print("\nSAMPLE RECORDS")

    for record in records[:3]:

        print("\n---")

        print(
            "Record ID :",
            record["record_id"]
        )

        print(
            "Domain    :",
            record["metadata"]["domain"]
        )

        print(
            "Page      :",
            record["metadata"]["page_number"]
        )

        print(
            "Section   :",
            record["metadata"]["section"]
        )

        print(
            "Text      :",
            record["text"][:300]
        )

    print("\nPASS")


# ============================================================
# MAIN
# ============================================================

def main():

    builder = RetrievalRecordBuilder()

    passed = 0

    for chunk_path in TEST_CHUNKS:

        test_retrieval_records(
            builder,
            chunk_path,
        )

        passed += 1

    print("\n" + "=" * 100)

    print(
        f"Documents passed: "
        f"{passed} / {len(TEST_CHUNKS)}"
    )

    assert passed == len(
        TEST_CHUNKS
    ), (
        "Some retrieval record tests failed."
    )

    print(
        "PHASE 7.7 RETRIEVAL RECORD "
        "PREPARATION: PASS"
    )


if __name__ == "__main__":
    main()