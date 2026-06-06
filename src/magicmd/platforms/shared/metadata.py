from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

from bs4 import BeautifulSoup


def normalize_text(value: str) -> str:
    lines = [" ".join(line.split()) for line in (value or "").splitlines()]
    return "\n".join(line for line in lines if line).strip()


def meta_content(soup: BeautifulSoup, *names: str) -> str:
    for name in names:
        tag = soup.find("meta", attrs={"property": name}) or soup.find("meta", attrs={"name": name})
        if tag and tag.get("content"):
            return normalize_text(str(tag["content"]))
    return ""


def unix_to_shanghai_iso(value: str) -> str:
    if not value or not value.isdigit():
        return ""
    tz = timezone(timedelta(hours=8))
    return datetime.fromtimestamp(int(value), tz=tz).isoformat()


def extract_script_value(html: str, name: str) -> str:
    patterns = [
        rf"var\s+{re.escape(name)}\s*=\s*['\"](?P<value>.*?)['\"]",
        rf"{re.escape(name)}\s*[:=]\s*['\"]?(?P<value>\d+)['\"]?",
    ]
    for pattern in patterns:
        match = re.search(pattern, html, re.S)
        if match:
            return normalize_text(match.group("value"))
    return ""
