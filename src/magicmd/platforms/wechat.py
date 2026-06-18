from __future__ import annotations

import re

from bs4 import BeautifulSoup

from magicmd.models import Article, ExtractionInfo, ImageAsset
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
        (
            soup.select_one("#activity-name") or soup.select_one("h1") or soup.new_tag("span")
        ).get_text()
    )
    title = (
        title or meta_content(soup, "og:title") or extract_script_value(html, "msg_title") or url
    )

    author = normalize_text((soup.select_one("#js_name") or soup.new_tag("span")).get_text())
    author = author or meta_content(soup, "author") or extract_script_value(html, "nickname")

    published_at = unix_to_shanghai_iso(extract_script_value(html, "create_time"))
    excerpt = meta_content(soup, "og:description", "description")
    cover_image = _cover_image_asset(
        _extract_wechat_script_url(html, "cdn_url_235_1")
        or meta_content(soup, "og:image", "twitter:image")
        or extract_script_value(html, "msg_cdn_url")
    )
    share_cover_image = _cover_image_asset(
        _extract_wechat_script_url(html, "cdn_url_1_1"), "share cover"
    )

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
        cover_image=cover_image,
        share_cover_image=share_cover_image,
        images=images,
        extraction=ExtractionInfo(platform="wechat", parser="wechat", warnings=warnings),
    )


def _cover_image_asset(url: str, alt: str = "cover") -> ImageAsset | None:
    url = _normalize_cover_url(url)
    if not url:
        return None
    return ImageAsset(source_url=url, alt=alt)


def _extract_wechat_script_url(html: str, name: str) -> str:
    patterns = [
        rf"var\s+{re.escape(name)}\s*=\s*['\"](?P<value>https?://.*?)(?<!\\)['\"]",
        rf"{re.escape(name)}\s*=\s*['\"](?P<value>https?://.*?)(?<!\\)['\"]",
    ]
    for pattern in patterns:
        match = re.search(pattern, html, re.S)
        if match:
            return match.group("value")
    return ""


def _normalize_cover_url(url: str) -> str:
    if not url:
        return ""
    if url.startswith("//"):
        return f"https:{url}"
    if url.startswith("http://"):
        return f"https://{url.removeprefix('http://')}"
    return url
