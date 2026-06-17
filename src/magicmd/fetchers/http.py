from __future__ import annotations

import httpx


DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)


def fetch_http(url: str, timeout_seconds: int = 20, user_agent: str = "default") -> str:
    headers = {"User-Agent": DEFAULT_USER_AGENT if user_agent == "default" else user_agent}
    response = httpx.get(url, timeout=timeout_seconds, follow_redirects=True, headers=headers)
    response.raise_for_status()
    return response.text
