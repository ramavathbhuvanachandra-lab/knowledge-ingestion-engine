from url_queue import URLQueue

from models.url import URLInfo, URLType


queue = URLQueue()


queue.enqueue(

    URLInfo(
        raw_url="https://iitj.ac.in",
        normalized_url="https://iitj.ac.in",
        url_type=URLType.WEBPAGE,
        discovered_from="ROOT"
    )

)

queue.enqueue(

    URLInfo(
        raw_url="https://iitj.ac.in",
        normalized_url="https://iitj.ac.in",
        url_type=URLType.WEBPAGE,
        discovered_from="ROOT"
    )

)

print("Queue Size:", queue.size())

page = queue.dequeue()

print(page)

print("Queue Size:", queue.size())