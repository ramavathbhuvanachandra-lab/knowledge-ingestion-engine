from urllib.parse import urlparse, parse_qs

from models.url_structure import URLStructure


class URLParser:

    def parse(self, url: str) -> URLStructure:

        parsed = urlparse(url)

        segments = [
            segment
            for segment in parsed.path.split("/")
            if segment
        ]

        query = {
            key: value[0]
            for key, value in parse_qs(parsed.query).items()
        }

        return URLStructure(
            scheme=parsed.scheme,
            domain=parsed.netloc,
            segments=segments,
            query=query,
            fragment=parsed.fragment,
            depth=len(segments),
        )