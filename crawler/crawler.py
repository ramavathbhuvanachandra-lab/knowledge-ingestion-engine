from crawl4ai import (
    AsyncWebCrawler,
    CrawlerRunConfig,
    CacheMode,
)

from models.page import PageData


# ============================================================
# CONFIGURATION
# ============================================================

NORMAL_WAIT_STRATEGY = "domcontentloaded"
FALLBACK_WAIT_STRATEGY = "commit"

PAGE_TIMEOUT = 60000
MIN_HTML_LENGTH = 1000


# ============================================================
# QUALITY EVALUATION
# ============================================================

def calculate_quality_score(result):
    """
    Calculate a deterministic quality score for a crawl result.

    The score measures whether the returned page contains
    useful information for our knowledge-ingestion pipeline.

    It does NOT use HTML length alone.
    """

    if result is None:
        return 0

    if not result.success:
        return 0

    html = result.html or ""
    markdown = result.markdown or ""

    if not html:
        return 0

    score = 0

    html_lower = html.lower()

    # --------------------------------------------------------
    # HTML exists
    # --------------------------------------------------------

    if len(html) >= MIN_HTML_LENGTH:
        score += 20

    # --------------------------------------------------------
    # Title exists
    # --------------------------------------------------------

    title = ""

    if result.metadata:
        title = result.metadata.get(
            "title",
            "",
        )

    if title.strip():
        score += 10

    # --------------------------------------------------------
    # Body exists
    # --------------------------------------------------------

    if "<body" in html_lower:
        score += 10

    # --------------------------------------------------------
    # Meaningful markdown/text
    # --------------------------------------------------------

    text_length = len(
        markdown.strip()
    )

    if text_length >= 500:
        score += 20

    if text_length >= 2000:
        score += 10

    if text_length >= 5000:
        score += 10

    # --------------------------------------------------------
    # Links
    # --------------------------------------------------------

    if "<a " in html_lower:
        score += 10

    # --------------------------------------------------------
    # Navigation indicators
    # --------------------------------------------------------

    navigation_indicators = [
        "<nav",
        "navigation",
        "navbar",
        "menu",
    ]

    if any(
        indicator in html_lower
        for indicator in navigation_indicators
    ):
        score += 10

    return score


# ============================================================
# PAGE DATA BUILDER
# ============================================================

def build_page_data(result):
    """
    Convert Crawl4AI's result into our PageData model.
    """

    metadata = (
        result.metadata
        if result.metadata
        else {}
    )

    return PageData(
        url=result.url,
        title=metadata.get(
            "title",
            "",
        ),
        markdown=result.markdown,
        html=result.html,
        success=result.success,
    )


# ============================================================
# CRAWL WITH ONE STRATEGY
# ============================================================

async def _crawl_with_strategy(
    url,
    wait_strategy,
):
    """
    Crawl a URL using a completely fresh Crawl4AI
    browser instance.

    A fresh crawler is intentionally created for every
    strategy so that a failed/timeout navigation cannot
    affect the fallback attempt.
    """

    config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        wait_until=wait_strategy,
        page_timeout=PAGE_TIMEOUT,
        delay_before_return_html=1.0,
    )

    try:

        async with AsyncWebCrawler() as crawler:

            result = await crawler.arun(
                url=url,
                config=config,
            )

            return result

    except Exception:

        return None


# ============================================================
# MAIN CRAWLER
# ============================================================

async def crawl_page(url: str):
    """
    Resilient webpage crawler.

    Strategy:

    1. Try normal DOMContentLoaded navigation.
    2. Evaluate the returned page.
    3. If normal navigation fails or produces weak
       content, create a fresh crawler.
    4. Retry using commit.
    5. Compare successful results.
    6. Return the highest-quality page.
    """

    # ========================================================
    # ATTEMPT 1 — NORMAL CRAWL
    # ========================================================

    normal_result = await _crawl_with_strategy(
        url,
        NORMAL_WAIT_STRATEGY,
    )

    normal_score = calculate_quality_score(
        normal_result
    )

    # --------------------------------------------------------
    # Strong normal result
    #
    # If the normal result is clearly useful, don't perform
    # another expensive crawl.
    # --------------------------------------------------------

    if normal_score >= 70:

        return build_page_data(
            normal_result
        )

    # ========================================================
    # ATTEMPT 2 — COMMIT FALLBACK
    # ========================================================

    fallback_result = await _crawl_with_strategy(
        url,
        FALLBACK_WAIT_STRATEGY,
    )

    fallback_score = calculate_quality_score(
        fallback_result
    )

    # ========================================================
    # BOTH FAILED
    # ========================================================

    if (
        normal_score == 0
        and fallback_score == 0
    ):

        return PageData(
            url=url,
            title="",
            markdown="",
            html="",
            success=False,
        )

    # ========================================================
    # ONLY NORMAL RESULT IS VALID
    # ========================================================

    if (
        normal_score > 0
        and fallback_score == 0
    ):

        return build_page_data(
            normal_result
        )

    # ========================================================
    # ONLY FALLBACK RESULT IS VALID
    # ========================================================

    if (
        normal_score == 0
        and fallback_score > 0
    ):

        return build_page_data(
            fallback_result
        )

    # ========================================================
    # BOTH RESULTS ARE VALID
    #
    # Choose the result with better content quality.
    # ========================================================

    if fallback_score > normal_score:

        return build_page_data(
            fallback_result
        )

    return build_page_data(
        normal_result
    )