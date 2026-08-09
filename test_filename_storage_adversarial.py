from tempfile import TemporaryDirectory
from types import SimpleNamespace

from processors.filename_generator import FilenameGenerator
from storage.saver import save_page
from utils import get_domain, sanitize_filename


def make_page(url, title="", markdown="test"):
    return SimpleNamespace(
        url=url,
        title=title,
        markdown=markdown,
        success=True,
    )


def test_empty_title():
    generator = FilenameGenerator()

    page = make_page(
        "https://example.com/admissions/programs",
        "",
    )

    result = generator.generate(page)

    assert result == "admissions_programs"


def test_unicode_title():
    generator = FilenameGenerator()

    page = make_page(
        "https://example.com/page",
        "Admissions हिंदी 2026",
    )

    result = generator.generate(page)

    assert result == "admissions_2026"


def test_special_characters():
    generator = FilenameGenerator()

    page = make_page(
        "https://example.com/page",
        "Admissions: Programs / 2026? *",
    )

    result = generator.generate(page)

    assert result == "admissions_programs_2026"


def test_extremely_long_title():
    generator = FilenameGenerator()

    page = make_page(
        "https://example.com/page",
        "A" * 1000,
    )

    result = generator.generate(page)

    assert len(result) <= generator.MAX_LENGTH


def test_query_parameters():
    generator = FilenameGenerator()

    page = make_page(
        "https://example.com/page?id=123&lang=en",
        "",
    )

    result = generator.generate(page)

    assert result == "page_id_123_lang_en"


def test_root_url():
    generator = FilenameGenerator()

    page = make_page(
        "https://example.com/",
        "",
    )

    result = generator.generate(page)

    assert result == "home"


def test_domain_safety():
    dangerous_urls = [
        "https://example.com/page",
        "https://www.example.com/page",
        "https://EXAMPLE.COM/page",
    ]

    for url in dangerous_urls:
        domain = get_domain(url)

        assert "/" not in domain
        assert "\\" not in domain
        assert ":" not in domain


def test_filename_safety():
    dangerous_names = [
        'hello/world',
        'hello\\world',
        'hello:world',
        'hello*world',
        'hello?world',
        'hello<world>',
        'hello|world',
    ]

    for name in dangerous_names:
        result = sanitize_filename(name)

        assert "/" not in result
        assert "\\" not in result
        assert ":" not in result
        assert "*" not in result
        assert "?" not in result
        assert "<" not in result
        assert ">" not in result
        assert "|" not in result


def test_duplicate_title_different_urls():
    with TemporaryDirectory() as temp:

        page_a = make_page(
            "https://example.com/page-a",
            "Admissions",
            "content A",
        )

        page_b = make_page(
            "https://example.com/page-b",
            "Admissions",
            "content B",
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
        assert second.startswith("admissions__")
        assert second != first


def test_repeated_save_same_url():
    with TemporaryDirectory() as temp:

        page = make_page(
            "https://example.com/admissions",
            "Admissions",
            "content",
        )

        filenames = []

        for _ in range(10):
            filenames.append(
                save_page(
                    page=page,
                    domain="example.com",
                    category="admissions",
                    filename="admissions",
                    base_path=temp,
                )
            )

        assert len(set(filenames)) == 1
        assert filenames[0] == "admissions"


def test_collision_is_deterministic():
    with TemporaryDirectory() as temp:

        page_a = make_page(
            "https://example.com/a",
            "Admissions",
        )

        page_b = make_page(
            "https://example.com/b",
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
        assert first.startswith("admissions__")


def test_nested_category():
    with TemporaryDirectory() as temp:

        page = make_page(
            "https://example.com/electrical",
            "Electrical Engineering",
        )

        result = save_page(
            page=page,
            domain="example.com",
            category="departments/electrical",
            filename="electrical_engineering",
            base_path=temp,
        )

        assert result == "electrical_engineering"


def run_all_tests():
    test_empty_title()
    test_unicode_title()
    test_special_characters()
    test_extremely_long_title()
    test_query_parameters()
    test_root_url()
    test_domain_safety()
    test_filename_safety()
    test_duplicate_title_different_urls()
    test_repeated_save_same_url()
    test_collision_is_deterministic()
    test_nested_category()

    print("FILENAME STORAGE ADVERSARIAL TESTS: PASS")


if __name__ == "__main__":
    run_all_tests()