from __future__ import annotations

from bs4 import BeautifulSoup

from magicmd.models import Article, ExtractionInfo
from magicmd.platforms.base import clean_content_element, html_to_markdown, meta_content, normalize_text


def parse_csdn_html(html: str, url: str) -> Article:
    soup = BeautifulSoup(html, "html.parser")
    warnings: list[str] = []
    content_el = (
        soup.select_one("#content_views")
        or soup.select_one("article")
        or soup.select_one(".blog-content-box")
        or soup.select_one(".article_content")
    )

    title = (
        meta_content(soup, "og:title", "twitter:title")
        or normalize_text((soup.select_one(".title-article") or soup.select_one("h1") or soup.new_tag("span")).get_text())
        or url
    )
    author = meta_content(soup, "author") or normalize_text(
        (soup.select_one(".follow-nickName") or soup.select_one(".name") or soup.new_tag("span")).get_text()
    )
    excerpt = meta_content(soup, "description", "og:description")
    published_at = meta_content(soup, "article:published_time")

    if content_el:
        content_html, images, code_blocks = clean_content_element(content_el)
        content_markdown = html_to_markdown(content_html, code_blocks)
    else:
        warnings.append("csdn_content_not_found")
        content_html = ""
        images = []
        content_markdown = ""

    if not excerpt and content_markdown:
        excerpt = content_markdown[:240]

    return Article(
        title=title,
        author=author,
        platform="csdn",
        source_url=url,
        canonical_url=url,
        published_at=published_at,
        excerpt=excerpt,
        content_html=content_html,
        content_markdown=content_markdown,
        images=images,
        extraction=ExtractionInfo(platform="csdn", parser="csdn", warnings=warnings),
    )

