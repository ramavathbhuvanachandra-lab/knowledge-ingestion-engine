from __future__ import annotations

import asyncio
import re
import ssl
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from crawl4ai import (
    AsyncWebCrawler,
    CacheMode,
    CrawlerRunConfig,
)

from models.page import PageData


# ============================================================
# CONFIGURATION
# ============================================================

NORMAL_WAIT_STRATEGY = "domcontentloaded"
FALLBACK_WAIT_STRATEGY = "commit"

NORMAL_PAGE_TIMEOUT = 20_000
FALLBACK_PAGE_TIMEOUT = 15_000

HTTP_TIMEOUT = 15

MIN_HTML_LENGTH = 1_000
MIN_HTTP_TEXT_LENGTH = 300

STRONG_QUALITY_SCORE = 70
ACCEPTABLE_QUALITY_SCORE = 45

HTTP_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/145.0.0.0 Safari/537.36"
)


# ============================================================
# INTERNAL RESULT MODEL
# ============================================================

class FetchCandidate:

    def __init__(
        self,
        *,
        url: str,
        title: str = "",
        markdown: str = "",
        html: str = "",
        success: bool = False,
        method: str = "",
        status_code: int | None = None,
        error: str | None = None,
    ) -> None:

        self.url = url
        self.title = title or ""
        self.markdown = markdown or ""
        self.html = html or ""
        self.success = bool(success)
        self.method = method
        self.status_code = status_code
        self.error = error


# ============================================================
# VISIBLE TEXT
# ============================================================

def _extract_visible_text(
    html: str,
) -> str:

    if not html:
        return ""

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    for element in soup(
        [
            "script",
            "style",
            "noscript",
            "template",
            "svg",
            "canvas",
        ]
    ):
        element.decompose()

    text = soup.get_text(
        separator=" ",
        strip=True,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# ============================================================
# ERROR PAGE DETECTION
# ============================================================

def _is_probable_error_page(
    html: str,
    title: str,
    text: str,
    status_code: int | None,
    markdown: str,
) -> bool:

    title_normalized = (
        (title or "")
        .strip()
        .lower()
    )

    text_normalized = (
        (text or "")
        .strip()
        .lower()
    )

    markdown_normalized = (
        (markdown or "")
        .strip()
        .lower()
    )

    html_normalized = (
        (html or "")
        .strip()
        .lower()
    )

    generic_error_titles = (
        "error",
        "error...",
        "404",
        "404 not found",
        "page not found",
        "not found",
        "access denied",
        "forbidden",
        "bad request",
        "server error",
        "internal server error",
        "403 forbidden",
        "500 internal server error",
    )

    title_is_generic_error = (
        title_normalized
        in generic_error_titles
        or title_normalized.startswith(
            "error"
        )
    )

    error_phrases = (
        "404 not found",
        "page not found",
        "requested page could not be found",
        "the page you are looking for",
        "access denied",
        "forbidden",
        "internal server error",
        "bad request",
        "something went wrong",
        "an error occurred",
        "error occurred while processing",
        "requested url was not found",
        "the requested url was not found",
    )

    phrase_hits = sum(
        1
        for phrase in error_phrases
        if (
            phrase in text_normalized
            or phrase in markdown_normalized
        )
    )

    if (
        title_is_generic_error
        and len(text_normalized) < 1_000
    ):
        return True

    if phrase_hits >= 2:
        return True

    if (
        status_code is not None
        and status_code >= 400
        and len(text_normalized) < 500
        and len(markdown_normalized) < 300
    ):
        return True

    if (
        title_is_generic_error
        and len(html_normalized) < 12_000
        and len(text_normalized) < 1_500
    ):
        return True

    return False


# ============================================================
# NORMALIZE CRAWL4AI RESULT
# ============================================================

def _normalize_crawl4ai_result(
    result: Any,
    url: str,
    method: str,
) -> FetchCandidate:

    if result is None:

        return FetchCandidate(
            url=url,
            method=method,
            error="No result returned.",
        )

    metadata = (
        result.metadata
        if getattr(
            result,
            "metadata",
            None,
        )
        else {}
    )

    if not isinstance(
        metadata,
        dict,
    ):
        metadata = {}

    return FetchCandidate(
        url=(
            getattr(
                result,
                "redirected_url",
                None,
            )
            or getattr(
                result,
                "url",
                None,
            )

            or url
        ),
        title=metadata.get(
            "title",
            "",
        ),
        markdown=(
            getattr(
                result,
                "markdown",
                "",
            )
            or ""
        ),
        html=(
            getattr(
                result,
                "html",
                "",
            )
            or ""
        ),
        success=bool(
            getattr(
                result,
                "success",
                False,
            )
        ),
        method=method,
        status_code=getattr(
            result,
            "status_code",
            None,
        ),
    )


# ============================================================
# QUALITY SCORE
# ============================================================

def calculate_quality_score(
    result: Any,
) -> int:

    if result is None:
        return 0

    if isinstance(
        result,
        FetchCandidate,
    ):

        html = result.html
        markdown = result.markdown
        title = result.title
        success = result.success
        status_code = result.status_code

    else:

        metadata = (
            result.metadata
            if getattr(
                result,
                "metadata",
                None,
            )
            else {}
        )

        if not isinstance(
            metadata,
            dict,
        ):
            metadata = {}

        html = (
            getattr(
                result,
                "html",
                "",
            )
            or ""
        )

        markdown = (
            getattr(
                result,
                "markdown",
                "",
            )
            or ""
        )

        title = (
            metadata.get(
                "title",
                "",
            )
            or ""
        )

        success = bool(
            getattr(
                result,
                "success",
                False,
            )
        )

        status_code = getattr(
            result,
            "status_code",
            None,
        )

    if not html:
        return 0

    text = _extract_visible_text(
        html
    )

    if _is_probable_error_page(
        html=html,
        title=title,
        text=text,
        status_code=status_code,
        markdown=markdown,
    ):
        return 0

    html_lower = html.lower()

    score = 0

    if len(html) >= MIN_HTML_LENGTH:
        score += 20

    if title.strip():
        score += 10

    if "<body" in html_lower:
        score += 10

    text_length = len(
        text.strip()
    )

    if text_length >= 300:
        score += 15

    if text_length >= 1_000:
        score += 10

    if text_length >= 3_000:
        score += 10

    if text_length >= 10_000:
        score += 5

    markdown_length = len(
        markdown.strip()
    )

    if markdown_length >= 500:
        score += 10

    if "<a " in html_lower:
        score += 5

    structure_indicators = (
        "<main",
        "<article",
        "<section",
        "<nav",
        "<header",
        "<footer",
    )

    if any(
        indicator in html_lower
        for indicator in structure_indicators
    ):
        score += 5

    if success:
        score += 5

    return min(
        score,
        100,
    )


# ============================================================
# PAGE DATA
# ============================================================

def _build_page_data(
    candidate: FetchCandidate,
) -> PageData:

    return PageData(
        url=candidate.url,
        title=candidate.title,
        markdown=candidate.markdown,
        html=candidate.html,
        success=candidate.success,
    )


# ============================================================
# CRAWL4AI STRATEGY
# ============================================================

async def _crawl_with_strategy(
    url: str,
    wait_strategy: str,
    timeout_ms: int,
) -> FetchCandidate:

    config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        wait_until=wait_strategy,
        page_timeout=timeout_ms,
        delay_before_return_html=0.75,
    )

    try:

        async with AsyncWebCrawler() as crawler:

            result = await crawler.arun(
                url=url,
                config=config,
            )
            print(
                "[REDIRECT DEBUG] result.url:",
                getattr(result, "url", None),
            )
            print(
                "[REDIRECT DEBUG] result.redirected_url:",
                getattr(result, "redirected_url", None),
            )
            print(
                "[REDIRECT DEBUG] result.status_code:",
                getattr(result, "status_code", None),
            )



        candidate = (
            _normalize_crawl4ai_result(
                result=result,
                url=url,
                method=(
                    f"crawl4ai:{wait_strategy}"
                ),
            )
        )

        print(
            "[FETCH] Crawl4AI",
            wait_strategy,
            f"quality={calculate_quality_score(candidate)}",
            f"url={url}",
        )

        return candidate

    except Exception as error:

        print(
            "[FETCH] Crawl4AI",
            wait_strategy,
            "failed:",
            f"{type(error).__name__}: {error}",
        )

        return FetchCandidate(
            url=url,
            method=(
                f"crawl4ai:{wait_strategy}"
            ),
            error=(
                f"{type(error).__name__}: "
                f"{error}"
            ),
        )


# ============================================================
# SSL CONTEXT
# ============================================================

def _build_ssl_context() -> ssl.SSLContext:
    """
    Build a proper certificate-verifying SSL context.

    Preferred:
        certifi CA bundle.

    Fallback:
        system Python CA store.

    Never disables certificate verification.
    """

    try:

        import certifi

        return ssl.create_default_context(
            cafile=certifi.where()
        )

    except ImportError:

        return ssl.create_default_context()


# ============================================================
# HTTP FALLBACK
# ============================================================

def _http_fetch_sync(
    url: str,
) -> FetchCandidate:

    from urllib.request import (
        Request,
        urlopen,
    )

    ssl_context = (
        _build_ssl_context()
    )

    request = Request(
        url,
        headers={
            "User-Agent": HTTP_USER_AGENT,
            "Accept": (
                "text/html,"
                "application/xhtml+xml,"
                "*/*;q=0.8"
            ),
            "Accept-Language": (
                "en-US,en;q=0.9"
            ),
            "Connection": "close",
        },
        method="GET",
    )

    try:

        with urlopen(
            request,
            timeout=HTTP_TIMEOUT,
            context=ssl_context,
        ) as response:

            final_url = (
                response.geturl()
                or url
            )

            status_code = getattr(
                response,
                "status",
                None,
            )

            raw = response.read()

            charset = (
                response.headers.get_content_charset()
                or "utf-8"
            )

            html = raw.decode(
                charset,
                errors="replace",
            )

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        title = ""

        if soup.title:

            title = (
                soup.title.get_text(
                    " ",
                    strip=True,
                )
            )

        markdown = _html_to_markdown(
            html=html,
            base_url=final_url,
        )

        return FetchCandidate(
            url=final_url,
            title=title,
            markdown=markdown,
            html=html,
            success=True,
            method="http",
            status_code=status_code,
        )

    except Exception as error:

        return FetchCandidate(
            url=url,
            method="http",
            error=(
                f"{type(error).__name__}: "
                f"{error}"
            ),
        )


async def _crawl_with_http_fallback(
    url: str,
) -> FetchCandidate:

    candidate = await asyncio.to_thread(
        _http_fetch_sync,
        url,
    )

    score = (
        calculate_quality_score(
            candidate
        )
    )

    text_length = len(
        _extract_visible_text(
            candidate.html
        )
    )

    if (
        score > 0
        and text_length >= MIN_HTTP_TEXT_LENGTH
    ):

        print(
            "[FETCH] HTTP fallback",
            f"quality={score}",
            f"text={text_length}",
            f"status={candidate.status_code}",
            f"url={url}",
        )

        return candidate

    if candidate.error:

        print(
            "[FETCH] HTTP fallback failed:",
            candidate.error,
        )

    else:

        print(
            "[FETCH] HTTP fallback rejected",
            f"quality={score}",
            f"text={text_length}",
            f"status={candidate.status_code}",
            f"url={url}",
        )

    return FetchCandidate(
        url=url,
        method="http",
        error=(
            candidate.error
            or "HTTP result was not usable."
        ),
    )


# ============================================================
# HTML → MARKDOWN FALLBACK
# ============================================================

def _html_to_markdown(
    html: str,
    base_url: str,
) -> str:

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    for element in soup(
        [
            "script",
            "style",
            "noscript",
            "template",
            "svg",
            "canvas",
        ]
    ):
        element.decompose()

    container = None

    for selector in (
        "main",
        "article",
        "[role='main']",
        ".main-content",
        "#main-content",
        ".content",
        "#content",
    ):

        container = soup.select_one(
            selector
        )

        if container is not None:
            break

    if container is None:

        container = (
            soup.body
            or soup
        )

    lines = []

    for element in container.find_all(
        [
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "p",
            "li",
            "blockquote",
            "table",
        ],
        recursive=True,
    ):

        tag = element.name

        if tag.startswith(
            "h"
        ):

            level = int(
                tag[1]
            )

            text = (
                element.get_text(
                    " ",
                    strip=True,
                )
            )

            if text:
                lines.append(
                    f"{'#' * level} {text}"
                )

            continue

        if tag == "li":

            text = (
                element.get_text(
                    " ",
                    strip=True,
                )
            )

            if text:
                lines.append(
                    f"- {text}"
                )

            continue

        if tag == "blockquote":

            text = (
                element.get_text(
                    " ",
                    strip=True,
                )
            )

            if text:
                lines.append(
                    f"> {text}"
                )

            continue

        if tag == "table":

            for row in element.find_all(
                "tr"
            ):

                cells = [
                    cell.get_text(
                        " ",
                        strip=True,
                    )
                    for cell in row.find_all(
                        ["th", "td"]
                    )
                ]

                if cells:
                    lines.append(
                        " | ".join(
                            cells
                        )
                    )

            continue

        text_parts = []

        for child in element.children:

            child_name = getattr(
                child,
                "name",
                None,
            )

            if child_name == "a":

                anchor_text = (
                    child.get_text(
                        " ",
                        strip=True,
                    )
                )

                href = (
                    child.get(
                        "href",
                        "",
                    )
                    or ""
                )

                if href:

                    absolute_url = (
                        urljoin(
                            base_url,
                            href,
                        )
                    )

                    if anchor_text:

                        text_parts.append(
                            f"[{anchor_text}]"
                            f"({absolute_url})"
                        )

                    else:

                        text_parts.append(
                            absolute_url
                        )

                elif anchor_text:

                    text_parts.append(
                        anchor_text
                    )

            elif child_name == "img":

                alt = (
                    child.get(
                        "alt",
                        "",
                    )
                    or ""
                )

                src = (
                    child.get(
                        "src",
                        "",
                    )
                    or ""
                )

                if alt and src:

                    text_parts.append(
                        f"![{alt}]"
                        f"({urljoin(base_url, src)})"
                    )

            else:

                if hasattr(
                    child,
                    "get_text",
                ):

                    value = (
                        child.get_text(
                            " ",
                            strip=True,
                        )
                    )

                else:

                    value = str(
                        child
                    )

                if value.strip():

                    text_parts.append(
                        value.strip()
                    )

        text = " ".join(
            text_parts
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

        if text:
            lines.append(
                text
            )

    cleaned = []

    previous = None

    for line in lines:

        line = line.strip()

        if not line:
            continue

        if line == previous:
            continue

        cleaned.append(
            line
        )

        previous = line

    if not cleaned:
        return ""

    return (
        "\n\n".join(
            cleaned
        )
        + "\n"
    )


# ============================================================
# MAIN API
# ============================================================

async def crawl_page(
    url: str,
) -> PageData:
    """
    Resilient single-page fetcher.

    Priority:

        1. Crawl4AI DOMContentLoaded
        2. Crawl4AI commit
        3. Direct HTTP
        4. Explicit failure

    This function does NOT manage:
        - URL queue
        - page limits
        - knowledge organization
        - RAG
    """

    normalized_url = (
        (url or "")
        .strip()
    )

    if not normalized_url:

        return PageData(
            url=url,
            title="",
            markdown="",
            html="",
            success=False,
        )

    print()
    print(
        "------------------------------------------------------------"
    )

    print(
        "FETCH PAGE:",
        normalized_url,
    )

    # ========================================================
    # ATTEMPT 1
    # ========================================================

    normal_result = (
        await _crawl_with_strategy(
            url=normalized_url,
            wait_strategy=NORMAL_WAIT_STRATEGY,
            timeout_ms=NORMAL_PAGE_TIMEOUT,
        )
    )

    normal_score = (
        calculate_quality_score(
            normal_result
        )
    )

    if normal_score >= STRONG_QUALITY_SCORE:

        print(
            "[ACCEPT] Primary Crawl4AI result"
        )

        print(
            "------------------------------------------------------------"
        )

        return _build_page_data(
            normal_result
        )

    # ========================================================
    # ATTEMPT 2
    # ========================================================

    fallback_result = (
        await _crawl_with_strategy(
            url=normalized_url,
            wait_strategy=FALLBACK_WAIT_STRATEGY,
            timeout_ms=FALLBACK_PAGE_TIMEOUT,
        )
    )

    fallback_score = (
        calculate_quality_score(
            fallback_result
        )
    )

    best_browser = (
        normal_result
        if normal_score >= fallback_score
        else fallback_result
    )

    best_browser_score = max(
        normal_score,
        fallback_score,
    )

    if (
        best_browser_score
        >= ACCEPTABLE_QUALITY_SCORE
    ):

        print(
            "[ACCEPT] Crawl4AI result"
        )

        print(
            "Method:",
            best_browser.method,
        )

        print(
            "Quality:",
            best_browser_score,
        )

        print(
            "------------------------------------------------------------"
        )

        return _build_page_data(
            best_browser
        )

    # ========================================================
    # ATTEMPT 3
    # ========================================================

    http_result = (
        await _crawl_with_http_fallback(
            normalized_url
        )
    )

    http_score = (
        calculate_quality_score(
            http_result
        )
    )

    if http_score > 0:

        print(
            "[ACCEPT] Direct HTTP recovery"
        )

        print(
            "Quality:",
            http_score,
        )

        print(
            "Status:",
            http_result.status_code,
        )

        print(
            "------------------------------------------------------------"
        )

        return _build_page_data(
            http_result
        )

    # ========================================================
    # TOTAL FAILURE
    # ========================================================

    print(
        "[FAIL] All fetch strategies failed"
    )

    print(
        "Normal quality  :",
        normal_score,
    )

    print(
        "Fallback quality:",
        fallback_score,
    )

    print(
        "HTTP quality    :",
        http_score,
    )

    print(
        "------------------------------------------------------------"
    )

    return PageData(
        url=normalized_url,
        title="",
        markdown="",
        html="",
        success=False,
    )