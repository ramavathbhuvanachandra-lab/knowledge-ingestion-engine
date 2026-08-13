import asyncio

from crawler.crawler import crawl_page
from extractor.page_context_extractor import PageContextExtractor


TEST_URLS = [

    "https://www.iitb.ac.in/institute-functionaries"
    #"https://iitj.ac.in/electrical-engineering/en/faculty",

   # "https://iitb.ac.in",

   # "https://docs.langchain.com",

    #"https://supabase.com/docs"

]


async def main():

    extractor = PageContextExtractor()

    for url in TEST_URLS:

        print("\n" + "=" * 80)
        print("URL:", url)
        print("=" * 80)

        try:

            page = await crawl_page(url)

            context = extractor.extract(page)

            print("Title         :", context.title)
            print("Heading       :", context.h1)
            print("Breadcrumbs   :", context.breadcrumbs)
            print("Domain        :", context.domain)
            print("Depth         :", context.depth)
            print("URL Parts     :", context.url_segments)

            print("Content Length:", len(context.main_content))

            print("\nContent Preview:")
            print("-" * 80)
            print(repr(context.main_content[:500]))
            print("-" * 80)

        except Exception as e:

            print("FAILED :", e)


if __name__ == "__main__":
    asyncio.run(main())