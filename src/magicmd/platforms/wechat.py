from __future__ import annotations

from bs4 import BeautifulSoup

from magicmd.models import Article, ExtractionInfo
from magicmd.platforms.base import (
    clean_content_element,
    extract_script_value,
    html_to_markdown,
    meta_content,
    normalize_text,
    unix_to_shanghai_iso,
)


def parse_wechat_html(html: str, url: str) -> Article:
    soup = BeautifulSoup(html, "html.parser")
    content_el = soup.select_one("#js_content")
    warnings: list[str] = []

    title = normalize_text(
        (soup.select_one("#activity-name") or soup.select_one("h1") or soup.new_tag("span")).get_text()
    )
    title = title or meta_content(soup, "og:title") or extract_script_value(html, "msg_title") or url

    author = normalize_text((soup.select_one("#js_name") or soup.new_tag("span")).get_text())
    author = author or meta_content(soup, "author") or extract_script_value(html, "nickname")

    published_at = unix_to_shanghai_iso(extract_script_value(html, "create_time"))
    excerpt = meta_content(soup, "og:description", "description")

    if content_el:
        content_html, images, code_blocks = clean_content_element(content_el)
        content_markdown = html_to_markdown(content_html, code_blocks)
    else:
        warnings.append("wechat_content_not_found")
        content_html = ""
        images = []
        content_markdown = ""

    if not excerpt and content_markdown:
        excerpt = content_markdown[:240]

    return Article(
        title=title,
        author=author,
        platform="wechat",
        source_url=url,
        canonical_url=url,
        published_at=published_at,
        excerpt=excerpt,
        content_html=content_html,
        content_markdown=content_markdown,
        images=images,
        extraction=ExtractionInfo(platform="wechat", parser="wechat", warnings=warnings),
    )

