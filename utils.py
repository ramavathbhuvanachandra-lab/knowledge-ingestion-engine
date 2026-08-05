from urllib.parse import urlparse
import re


def get_domain(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    return name.strip("_")