from models.crawl_plan import (
    CrawlAction,
    CrawlPlan,
    CrawlPriority,
)
from models.url import URLInfo, URLType


SOURCE_URL = "https://gwpgc.ac.in/"


def build_url_info(
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


def test_webpage_plan():

    url_info = build_url_info(
        url="https://gwpgc.ac.in/admission",
        url_type=URLType.WEBPAGE,
        depth=1,
    )

    plan = CrawlPlan(
        url_info=url_info,
        action=CrawlAction.CRAWL,
        priority=CrawlPriority.HIGH,
        depth=1,
    )

    assert plan.url == (
        "https://gwpgc.ac.in/admission"
    )

    assert plan.url_type == URLType.WEBPAGE

    assert plan.action == CrawlAction.CRAWL

    assert plan.priority == CrawlPriority.HIGH

    assert plan.depth == 1

    assert plan.discovered_from == SOURCE_URL


def test_pdf_plan():

    url_info = build_url_info(
        url="https://gwpgc.ac.in/files/brochure.pdf",
        url_type=URLType.PDF,
        depth=2,
    )

    plan = CrawlPlan(
        url_info=url_info,
        action=CrawlAction.DOCUMENT,
        priority=CrawlPriority.NORMAL,
        depth=2,
    )

    assert plan.url_type == URLType.PDF
    assert plan.action == CrawlAction.DOCUMENT
    assert plan.priority == CrawlPriority.NORMAL
    assert plan.depth == 2


def test_image_plan():

    url_info = build_url_info(
        url="https://gwpgc.ac.in/images/campus.jpg",
        url_type=URLType.IMAGE,
        depth=1,
    )

    plan = CrawlPlan(
        url_info=url_info,
        action=CrawlAction.RESOURCE,
        priority=CrawlPriority.LOW,
        depth=1,
    )

    assert plan.url_type == URLType.IMAGE
    assert plan.action == CrawlAction.RESOURCE
    assert plan.priority == CrawlPriority.LOW


def test_external_plan():

    url_info = build_url_info(
        url="https://ugc.gov.in",
        url_type=URLType.EXTERNAL,
        depth=1,
    )

    plan = CrawlPlan(
        url_info=url_info,
        action=CrawlAction.IGNORE,
        priority=CrawlPriority.LOW,
        depth=1,
    )

    assert plan.url_type == URLType.EXTERNAL
    assert plan.action == CrawlAction.IGNORE


def test_plan_is_immutable():

    url_info = build_url_info(
        url="https://gwpgc.ac.in/contact",
        url_type=URLType.WEBPAGE,
    )

    plan = CrawlPlan(
        url_info=url_info,
        action=CrawlAction.CRAWL,
        priority=CrawlPriority.NORMAL,
        depth=0,
    )

    try:

        plan.priority = CrawlPriority.HIGH

    except Exception:

        pass

    else:

        raise AssertionError(
            "CrawlPlan should be immutable"
        )


if __name__ == "__main__":

    test_webpage_plan()
    test_pdf_plan()
    test_image_plan()
    test_external_plan()
    test_plan_is_immutable()

    print("CRAWL PLAN TESTS: PASS")