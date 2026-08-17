from crawler.url_classifier import (
    classify_url,
)
from models.url import URLType


BASE_DOMAIN = "example.com"
SOURCE_URL = "https://example.com/"


def test_webpage_url():
    info = classify_url(
        raw_url="https://example.com/ece",
        normalized_url="https://example.com/ece",
        base_domain=BASE_DOMAIN,
        discovered_from=SOURCE_URL,
    )

    assert info.url_type == URLType.WEBPAGE


def test_pdf_url():
    info = classify_url(
        raw_url="https://example.com/file.pdf",
        normalized_url="https://example.com/file.pdf",
        base_domain=BASE_DOMAIN,
        discovered_from=SOURCE_URL,
    )

    assert info.url_type == URLType.PDF


def test_xlsx_url():
    info = classify_url(
        raw_url="https://example.com/file.xlsx",
        normalized_url="https://example.com/file.xlsx",
        base_domain=BASE_DOMAIN,
        discovered_from=SOURCE_URL,
    )

    assert info.url_type == URLType.XLSX


def test_image_url():
    info = classify_url(
        raw_url="https://example.com/logo.png",
        normalized_url="https://example.com/logo.png",
        base_domain=BASE_DOMAIN,
        discovered_from=SOURCE_URL,
    )

    assert info.url_type == URLType.IMAGE


def test_external_url():
    info = classify_url(
        raw_url="https://other-example.com/",
        normalized_url="https://other-example.com/",
        base_domain=BASE_DOMAIN,
        discovered_from=SOURCE_URL,
    )

    assert info.url_type == URLType.EXTERNAL


def test_invalid_url():
    info = classify_url(
        raw_url="abc",
        normalized_url="abc",
        base_domain=BASE_DOMAIN,
        discovered_from=SOURCE_URL,
    )

    assert info.url_type == URLType.INVALID


def test_pdf_with_query_string():
    info = classify_url(
        raw_url="https://example.com/file.pdf?version=2",
        normalized_url="https://example.com/file.pdf?version=2",
        base_domain=BASE_DOMAIN,
        discovered_from=SOURCE_URL,
    )

    assert info.url_type == URLType.PDF


def test_xlsx_with_query_string():
    info = classify_url(
        raw_url="https://example.com/file.xlsx?download=true",
        normalized_url="https://example.com/file.xlsx?download=true",
        base_domain=BASE_DOMAIN,
        discovered_from=SOURCE_URL,
    )

    assert info.url_type == URLType.XLSX


def test_image_with_query_string():
    info = classify_url(
        raw_url="https://example.com/image.jpg?width=800",
        normalized_url="https://example.com/image.jpg?width=800",
        base_domain=BASE_DOMAIN,
        discovered_from=SOURCE_URL,
    )

    assert info.url_type == URLType.IMAGE


def test_domain_case_is_not_external():
    info = classify_url(
        raw_url="https://EXAMPLE.COM/ece",
        normalized_url="https://EXAMPLE.COM/ece",
        base_domain="example.com",
        discovered_from=SOURCE_URL,
    )

    assert info.url_type == URLType.WEBPAGE