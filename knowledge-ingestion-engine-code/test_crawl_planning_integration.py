from crawler.crawl_policy import CrawlPolicy
from crawler.crawl_queue import CrawlQueue
from crawler.depth_tracker import DepthTracker

from models.crawl_plan import (
    CrawlAction,
    CrawlPriority,
)

from models.url import URLInfo, URLType


ROOT = "https://gwpgc.ac.in/"

ADMISSION = (
    "https://gwpgc.ac.in/admission"
)

FACULTY = (
    "https://gwpgc.ac.in/faculty"
)

RESEARCH = (
    "https://gwpgc.ac.in/research"
)

BROCHURE = (
    "https://gwpgc.ac.in/brochure.pdf"
)

IMAGE = (
    "https://gwpgc.ac.in/images/campus.jpg"
)

EXTERNAL = (
    "https://ugc.gov.in"
)


def make_url_info(
    url,
    url_type,
    discovered_from,
    depth,
):
    return URLInfo(
        raw_url=url,
        normalized_url=url,
        url_type=url_type,
        discovered_from=discovered_from,
        depth=depth,
    )


def test_full_planning_flow():

    tracker = DepthTracker()
    policy = CrawlPolicy()
    queue = CrawlQueue()

    # --------------------------------------------------
    # ROOT
    # --------------------------------------------------

    root_depth = tracker.register_root(ROOT)

    assert root_depth == 0

    root_info = make_url_info(
        ROOT,
        URLType.WEBPAGE,
        "ROOT",
        root_depth,
    )

    root_plan = policy.create_plan(
        root_info
    )

    assert root_plan.action == CrawlAction.CRAWL
    assert root_plan.priority == CrawlPriority.HIGH
    assert root_plan.depth == 0

    assert queue.enqueue(root_plan) is True

    # --------------------------------------------------
    # DEPTH 1 WEBPAGES
    # --------------------------------------------------

    admission_depth = tracker.register_child(
        ADMISSION,
        ROOT,
    )

    faculty_depth = tracker.register_child(
        FACULTY,
        ROOT,
    )

    assert admission_depth == 1
    assert faculty_depth == 1

    admission_info = make_url_info(
        ADMISSION,
        URLType.WEBPAGE,
        ROOT,
        admission_depth,
    )

    faculty_info = make_url_info(
        FACULTY,
        URLType.WEBPAGE,
        ROOT,
        faculty_depth,
    )

    admission_plan = policy.create_plan(
        admission_info
    )

    faculty_plan = policy.create_plan(
        faculty_info
    )

    assert admission_plan.action == CrawlAction.CRAWL
    assert faculty_plan.action == CrawlAction.CRAWL

    assert admission_plan.priority == CrawlPriority.HIGH
    assert faculty_plan.priority == CrawlPriority.HIGH

    assert queue.enqueue(admission_plan) is True
    assert queue.enqueue(faculty_plan) is True

    # --------------------------------------------------
    # DEPTH 2 WEBPAGE
    # --------------------------------------------------

    research_depth = tracker.register_child(
        RESEARCH,
        FACULTY,
    )

    assert research_depth == 2

    research_info = make_url_info(
        RESEARCH,
        URLType.WEBPAGE,
        FACULTY,
        research_depth,
    )

    research_plan = policy.create_plan(
        research_info
    )

    assert research_plan.action == CrawlAction.CRAWL
    assert research_plan.priority == CrawlPriority.HIGH
    assert research_plan.depth == 2

    assert queue.enqueue(research_plan) is True

    # --------------------------------------------------
    # PDF
    # --------------------------------------------------

    brochure_depth = tracker.register_child(
        BROCHURE,
        ADMISSION,
    )

    assert brochure_depth == 2

    brochure_info = make_url_info(
        BROCHURE,
        URLType.PDF,
        ADMISSION,
        brochure_depth,
    )

    brochure_plan = policy.create_plan(
        brochure_info
    )

    assert brochure_plan.action == CrawlAction.DOCUMENT
    assert brochure_plan.priority == CrawlPriority.NORMAL
    assert brochure_plan.depth == 2

    assert queue.enqueue(brochure_plan) is True

    # --------------------------------------------------
    # IMAGE
    # --------------------------------------------------

    image_depth = tracker.register_child(
        IMAGE,
        ROOT,
    )

    assert image_depth == 1

    image_info = make_url_info(
        IMAGE,
        URLType.IMAGE,
        ROOT,
        image_depth,
    )

    image_plan = policy.create_plan(
        image_info
    )

    assert image_plan.action == CrawlAction.RESOURCE
    assert image_plan.priority == CrawlPriority.LOW
    assert image_plan.depth == 1

    assert queue.enqueue(image_plan) is True

    # --------------------------------------------------
    # EXTERNAL
    # --------------------------------------------------

    external_depth = tracker.register_child(
        EXTERNAL,
        ROOT,
    )

    external_info = make_url_info(
        EXTERNAL,
        URLType.EXTERNAL,
        ROOT,
        external_depth,
    )

    external_plan = policy.create_plan(
        external_info
    )

    # The policy correctly identifies this as
    # something that must not be crawled.
    assert external_plan.action == CrawlAction.IGNORE
    assert external_plan.priority == CrawlPriority.LOW

    # IGNORE plans are deliberately NOT submitted
    # to the execution queue.
    #
    # The planner made the decision.
    # The scheduler only receives executable work.

    # --------------------------------------------------
    # QUEUE SIZE
    # --------------------------------------------------

    assert queue.size() == 6

    # --------------------------------------------------
    # HIGH PRIORITY
    # --------------------------------------------------

    first = queue.dequeue()

    assert first.url == ROOT
    assert first.action == CrawlAction.CRAWL
    assert first.priority == CrawlPriority.HIGH

    second = queue.dequeue()

    assert second.url == ADMISSION
    assert second.action == CrawlAction.CRAWL
    assert second.priority == CrawlPriority.HIGH

    third = queue.dequeue()

    assert third.url == FACULTY
    assert third.action == CrawlAction.CRAWL
    assert third.priority == CrawlPriority.HIGH

    # Research is also HIGH and therefore comes next.
    fourth = queue.dequeue()

    assert fourth.url == RESEARCH
    assert fourth.action == CrawlAction.CRAWL
    assert fourth.priority == CrawlPriority.HIGH

    # --------------------------------------------------
    # NORMAL PRIORITY
    # --------------------------------------------------

    fifth = queue.dequeue()

    assert fifth.url == BROCHURE
    assert fifth.action == CrawlAction.DOCUMENT
    assert fifth.priority == CrawlPriority.NORMAL

    # --------------------------------------------------
    # LOW PRIORITY
    # --------------------------------------------------

    sixth = queue.dequeue()

    assert sixth.url == IMAGE
    assert sixth.action == CrawlAction.RESOURCE
    assert sixth.priority == CrawlPriority.LOW

    # --------------------------------------------------
    # EMPTY
    # --------------------------------------------------

    assert queue.dequeue() is None
    assert queue.is_empty() is True


def test_duplicate_url_cannot_enter_twice():

    tracker = DepthTracker()
    policy = CrawlPolicy()
    queue = CrawlQueue()

    tracker.register_root(ROOT)

    depth = tracker.register_child(
        ADMISSION,
        ROOT,
    )

    info = make_url_info(
        ADMISSION,
        URLType.WEBPAGE,
        ROOT,
        depth,
    )

    plan = policy.create_plan(info)

    assert queue.enqueue(plan) is True

    # Same normalized URL discovered again
    # from another parent.
    duplicate_info = make_url_info(
        ADMISSION,
        URLType.WEBPAGE,
        FACULTY,
        5,
    )

    duplicate_plan = policy.create_plan(
        duplicate_info
    )

    assert queue.enqueue(
        duplicate_plan
    ) is False

    assert queue.size() == 1


def test_depth_is_preserved_through_plan():

    tracker = DepthTracker()
    policy = CrawlPolicy()

    tracker.register_root(ROOT)

    tracker.register_child(
        FACULTY,
        ROOT,
    )

    depth = tracker.register_child(
        RESEARCH,
        FACULTY,
    )

    assert depth == 2

    info = make_url_info(
        RESEARCH,
        URLType.WEBPAGE,
        FACULTY,
        depth,
    )

    plan = policy.create_plan(info)

    assert plan.depth == 2
    assert plan.url == RESEARCH
    assert plan.action == CrawlAction.CRAWL
    assert plan.priority == CrawlPriority.HIGH


if __name__ == "__main__":

    test_full_planning_flow()
    test_duplicate_url_cannot_enter_twice()
    test_depth_is_preserved_through_plan()

    print(
        "CRAWL PLANNING INTEGRATION TESTS: PASS"
    )