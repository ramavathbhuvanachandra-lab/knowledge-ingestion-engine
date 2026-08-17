from crawler.crawl_policy import CrawlPolicy
from models.crawl_plan import (
    CrawlAction,
    CrawlPriority,
)
from models.url import URLInfo, URLType


SOURCE_URL = "https://gwpgc.ac.in/"


def make_url_info(
    url: str,
    url_type: URLType,
    depth: int = 0,
) -> URLInfo:

    return URLInfo(
        raw_url=url,
        normalized_url=url,
        url_type=url_type,
        discovered_from=SOURCE_URL,
        depth=depth,
    )


def test_webpage_policy():

    policy = CrawlPolicy()

    info = make_url_info(
        "https://gwpgc.ac.in/admission",
        URLType.WEBPAGE,
        depth=1,
    )

    plan = policy.create_plan(info)

    assert plan.action == CrawlAction.CRAWL
    assert plan.priority == CrawlPriority.HIGH
    assert plan.depth == 1


def test_pdf_policy():

    policy = CrawlPolicy()

    info = make_url_info(
        "https://gwpgc.ac.in/brochure.pdf",
        URLType.PDF,
        depth=2,
    )

    plan = policy.create_plan(info)

    assert plan.action == CrawlAction.DOCUMENT
    assert plan.priority == CrawlPriority.NORMAL
    assert plan.depth == 2


def test_image_policy():

    policy = CrawlPolicy()

    info = make_url_info(
        "https://gwpgc.ac.in/logo.png",
        URLType.IMAGE,
        depth=1,
    )

    plan = policy.create_plan(info)

    assert plan.action == CrawlAction.RESOURCE
    assert plan.priority == CrawlPriority.LOW


def test_external_policy():

    policy = CrawlPolicy()

    info = make_url_info(
        "https://ugc.gov.in",
        URLType.EXTERNAL,
        depth=1,
    )

    plan = policy.create_plan(info)

    assert plan.action == CrawlAction.IGNORE
    assert plan.priority == CrawlPriority.LOW


def test_invalid_policy():

    policy = CrawlPolicy()

    info = make_url_info(
        "https://example.com/bad",
        URLType.INVALID,
        depth=1,
    )

    plan = policy.create_plan(info)

    assert plan.action == CrawlAction.IGNORE


def test_webpage_crawling_can_be_disabled():

    policy = CrawlPolicy(
        crawl_webpages=False,
    )

    info = make_url_info(
        "https://gwpgc.ac.in/admission",
        URLType.WEBPAGE,
    )

    plan = policy.create_plan(info)

    assert plan.action == CrawlAction.IGNORE


def test_document_processing_can_be_disabled():

    policy = CrawlPolicy(
        process_documents=False,
    )

    info = make_url_info(
        "https://gwpgc.ac.in/brochure.pdf",
        URLType.PDF,
    )

    plan = policy.create_plan(info)

    assert plan.action == CrawlAction.IGNORE


def test_resource_processing_can_be_disabled():

    policy = CrawlPolicy(
        process_resources=False,
    )

    info = make_url_info(
        "https://gwpgc.ac.in/logo.png",
        URLType.IMAGE,
    )

    plan = policy.create_plan(info)

    assert plan.action == CrawlAction.IGNORE


def test_external_crawling_can_be_enabled():

    policy = CrawlPolicy(
        allow_external=True,
    )

    info = make_url_info(
        "https://library.gwpgc.ac.in",
        URLType.EXTERNAL,
    )

    plan = policy.create_plan(info)

    assert plan.action == CrawlAction.CRAWL
    assert plan.priority == CrawlPriority.LOW


def test_explicit_depth_overrides_url_info():

    policy = CrawlPolicy()

    info = make_url_info(
        "https://gwpgc.ac.in/admission",
        URLType.WEBPAGE,
        depth=1,
    )

    plan = policy.create_plan(
        info,
        depth=5,
    )

    assert plan.depth == 5


if __name__ == "__main__":

    test_webpage_policy()
    test_pdf_policy()
    test_image_policy()
    test_external_policy()
    test_invalid_policy()
    test_webpage_crawling_can_be_disabled()
    test_document_processing_can_be_disabled()
    test_resource_processing_can_be_disabled()
    test_external_crawling_can_be_enabled()
    test_explicit_depth_overrides_url_info()

    print("CRAWL POLICY TESTS: PASS")