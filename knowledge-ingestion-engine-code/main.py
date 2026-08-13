import asyncio

from crawler import crawl_page
from saver import save_page
from utils import get_domain


async def main():

    url = input("Enter Website URL: ").strip()

    page = await crawl_page(url)
    from link_extractor import extract_internal_links
    links = extract_internal_links(
        page.html,
        page.url
    )
    print("\nInternal Links Found:", len(links))
    for link in links:
        print(link)

    

    domain = get_domain(url)

    save_page(
        page,
       domain,
        "home"
    )

    print("\nTitle:", page.title)




if __name__ == "__main__":
    asyncio.run(main())