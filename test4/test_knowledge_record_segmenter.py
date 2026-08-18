def test_numeric_value_before_next_record_is_not_treated_as_record_id():
    """
    A standalone numeric value followed immediately by another
    numbered record must not steal the record boundary.

    This protects against extracted financial amounts and similar
    numeric values.
    """

    text = """
1019 Previous Project
Sponsor
Department A
1,20,000

945504
1020 Developing Multiagent System
Department B
5,68,72,000

1021 Travel Support
Department C
1,28,893
""".strip()

    segmenter = (
        KnowledgeRecordSegmenter()
    )

    records = segmenter.segment(
        text=text,
        start_line=1,
    )

    assert [
        record["record_index"]
        for record in records
    ] == [
        1019,
        1020,
        1021,
    ]

    assert "945504" in records[0]["text"]
    assert "1020 Developing Multiagent System" in records[1]["text"]