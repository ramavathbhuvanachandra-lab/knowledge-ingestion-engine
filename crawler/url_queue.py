from collections import deque

from models.url import URLInfo


class URLQueue:

    def __init__(self):

        self.queue = deque()

        self.seen_urls = set()


    def enqueue(self, url_info: URLInfo):

       if url_info.normalized_url in self.seen_urls:
            return

       self.queue.append(url_info)

       self.seen_urls.add(url_info.normalized_url)


    def dequeue(self):

        if self.is_empty():
            return None

        return self.queue.popleft()


    def is_empty(self):

        return len(self.queue) == 0


    def size(self):

        return len(self.queue)