from crawl4ai import AsyncWebCrawler

from models.page import PageData


async def crawl_page(url: str):

    async with AsyncWebCrawler() as crawler:

        result = await crawler.arun(url=url)

        page = PageData(
            url=result.url,
            title=result.metadata.get("title", ""),
            markdown=result.markdown,
            html=result.html,
            success=result.success
        )

        return page