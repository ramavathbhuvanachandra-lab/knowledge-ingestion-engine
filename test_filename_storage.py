from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from processors.filename_generator import FilenameGenerator
from storage.saver import save_page
from utils import get_domain, sanitize_filename


def make_page(
    url: str,
    title: str,
    markdown: str = "test content",
):
    return SimpleNamespace(
        url=url,
        title=title,
        markdown=markdown,
        success=True,
    )


def test_readable_title():
    generator = FilenameGenerator()

    page = make_page(
        "https://iitj.ac.in/admissions/programs",
        "Admission Programs | IIT Jodhpur",
    )

    result = generator.generate(page)

    assert result == "admission_programs"


def test_url_fallback():
    generator = FilenameGenerator()

    page = make_page(
        "https://iitj.ac.in/admissions/programs",
        "",
    )

    result = generator.generate(page)

    assert result == "admissions_programs"


def test_query_url():
    generator = FilenameGenerator()

    page = make_page(
        "https://example.com/page?id=123&lang=en",
        "",
    )

    result = generator.generate(page)

    assert result == "page_id_123_lang_en"


def test_homepage():
    generator = FilenameGenerator()

    page = make_page(
        "https://iitj.ac.in/",
        "",
    )

    result = generator.generate(page)

    assert result == "home"


def test_domain():
    assert (
        get_domain(
            "https://www.iitj.ac.in/admissions"
        )
        == "www.iitj.ac.in"
    )


def test_filename_sanitization():
    assert (
        sanitize_filename(
            'Hello / World: Test?'
        )
        == "hello_world_test"
    )


def test_same_url_does_not_get_hash():
    with TemporaryDirectory() as temp:
        page = make_page(
            "https://example.com/page",
            "Admissions",
        )

        first = save_page(
            page=page,
            domain="example.com",
            category="admissions",
            filename="admissions",
            base_path=temp,
        )

        second = save_page(
            page=page,
            domain="example.com",
            category="admissions",
            filename="admissions",
            base_path=temp,
        )

        assert first == "admissions"
        assert second == "admissions"


def test_collision_gets_hash():
    with TemporaryDirectory() as temp:
        page_a = make_page(
            "https://example.com/page-a",
            "Admissions",
            "A",
        )

        page_b = make_page(
            "https://example.com/page-b",
            "Admissions",
            "B",
        )

        first = save_page(
            page=page_a,
            domain="example.com",
            category="admissions",
            filename="admissions",
            base_path=temp,
        )

        second = save_page(
            page=page_b,
            domain="example.com",
            category="admissions",
            filename="admissions",
            base_path=temp,
        )

        assert first == "admissions"

        assert second.startswith(
            "admissions__"
        )

        assert len(second) == (
            len("admissions__") + 8
        )


def test_collision_is_deterministic():
    with TemporaryDirectory() as temp:
        page_a = make_page(
            "https://example.com/page-a",
            "Admissions",
        )

        page_b = make_page(
            "https://example.com/page-b",
            "Admissions",
        )

        save_page(
            page=page_a,
            domain="example.com",
            category="admissions",
            filename="admissions",
            base_path=temp,
        )

        first = save_page(
            page=page_b,
            domain="example.com",
            category="admissions",
            filename="admissions",
            base_path=temp,
        )

        second = save_page(
            page=page_b,
            domain="example.com",
            category="admissions",
            filename="admissions",
            base_path=temp,
        )

        assert first == second


def run_all_tests():
    test_readable_title()
    test_url_fallback()
    test_query_url()
    test_homepage()
    test_domain()
    test_filename_sanitization()
    test_same_url_does_not_get_hash()
    test_collision_gets_hash()
    test_collision_is_deterministic()

    print(
        "FILENAME AND STORAGE TESTS: PASS"
    )


if __name__ == "__main__":
    run_all_tests()