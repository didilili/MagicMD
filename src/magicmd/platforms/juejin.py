from __future__ import annotations

import re

from bs4 import BeautifulSoup

from magicmd.models import Article, ExtractionInfo
from magicmd.platforms.base import (
    clean_content_element,
    html_to_markdown,
    meta_content,
    normalize_text,
)


def _published_at(soup: BeautifulSoup) -> str:
    published = meta_content(soup, "article:published_time")
    if published:
        return published
    time_tag = soup.select_one("time[datetime]") or soup.select_one("time")
    if time_tag:
        value = normalize_text(str(time_tag.get("datetime") or time_tag.get_text()))
        match = re.search(r"\d{4}-\d{2}-\d{2}", value)
        if match:
            return match.group(0)
        return value
    for selector in (".time", ".date", ".publish-time", ".article-time"):
        tag = soup.select_one(selector)
        if not tag:
            continue
        value = normalize_text(tag.get_text())
        match = re.search(r"\d{4}-\d{2}-\d{2}", value)
        if match:
            return match.group(0)
    return ""


def _author(soup: BeautifulSoup) -> str:
    author = meta_content(soup, "author")
    if author:
        return author
    for selector in (
        'a[href*="/team/"] .title',
        'a[href*="/user/"] .name',
        ".team-user .name",
        ".username .name",
        ".author-name",
    ):
        tag = soup.select_one(selector)
        if tag:
            value = normalize_text(tag.get_text())
            if value:
                return value
    return ""


def parse_juejin_html(html: str, url: str) -> Article:
    soup = BeautifulSoup(html, "html.parser")
    warnings: list[str] = []
    content_el = (
        soup.select_one(".markdown-body")
        or soup.select_one(".article-content")
        or soup.select_one(".article")
        or soup.select_one("article")
    )

    title = (
        meta_content(soup, "og:title", "twitter:title")
        or normalize_text((soup.select_one("h1") or soup.new_tag("span")).get_text())
        or url
    )
    author = _author(soup)
    excerpt = meta_content(soup, "og:description", "description")
    published_at = _published_at(soup)

    if content_el:
        content_html, images, code_blocks = clean_content_element(content_el)
        content_markdown = html_to_markdown(content_html, code_blocks)
    else:
        warnings.append("juejin_content_not_found")
        content_html = ""
        images = []
        content_markdown = ""

    if not excerpt and content_markdown:
        excerpt = content_markdown[:240]

    return Article(
        title=title,
        author=author,
        platform="juejin",
        source_url=url,
        canonical_url=url,
        published_at=published_at,
        excerpt=excerpt,
        content_html=content_html,
        content_markdown=content_markdown,
        images=images,
        extraction=ExtractionInfo(platform="juejin", parser="juejin", warnings=warnings),
    )
