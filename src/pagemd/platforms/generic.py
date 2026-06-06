from __future__ import annotations

from bs4 import BeautifulSoup

from pagemd.models import Article, ExtractionInfo
from pagemd.platforms.base import clean_content_element, html_to_markdown, meta_content, normalize_text


def parse_generic_html(html: str, url: str) -> Article:
    soup = BeautifulSoup(html, "html.parser")
    warnings: list[str] = []
    content_el = (
        soup.select_one("article")
        or soup.select_one("main")
        or soup.select_one(".post-content")
        or soup.select_one(".content")
        or soup.body
    )

    title = (
        meta_content(soup, "og:title", "twitter:title")
        or normalize_text((soup.select_one("title") or soup.select_one("h1") or soup.new_tag("span")).get_text())
        or url
    )
    author = meta_content(soup, "author")
    excerpt = meta_content(soup, "og:description", "description")
    published_at = meta_content(soup, "article:published_time")

    if content_el:
        content_html, images, code_blocks = clean_content_element(content_el)
        content_markdown = html_to_markdown(content_html, code_blocks)
    else:
        warnings.append("generic_content_not_found")
        content_html = ""
        images = []
        content_markdown = ""

    if not excerpt and content_markdown:
        excerpt = content_markdown[:240]

    return Article(
        title=title,
        author=author,
        platform="generic",
        source_url=url,
        canonical_url=url,
        published_at=published_at,
        excerpt=excerpt,
        content_html=content_html,
        content_markdown=content_markdown,
        images=images,
        extraction=ExtractionInfo(platform="generic", parser="generic", warnings=warnings),
    )

