from urllib.parse import urlparse

from magicmd.platforms.registry import match_platform_by_host


def detect_platform(url: str) -> str:
    host = urlparse(url).netloc.lower()
    return match_platform_by_host(host)
