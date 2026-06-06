from __future__ import annotations

import re

from pagemd.config import MarkdownConfig
from pagemd.models import Article


def _quote(value: str) -> str:
    return '"' + value.replace('"', '\\"') + '"'


def _heading(level: int, text: str, offset: int) -> str:
    return f"{'#' * min(6, max(1, level + offset))} {text}"


def _shift_body_headings(markdown: str, offset: int) -> str:
    if offset == 0:
        return markdown

    def replace(match: re.Match[str]) -> str:
        hashes = match.group("hashes")
        return f"{'#' * min(6, max(1, len(hashes) + offset))}{match.group('space')}"

    return re.sub(r"(?m)^(?P<hashes>#{1,6})(?P<space>\s+)", replace, markdown)


def render_markdown(article: Article, markdown_config: MarkdownConfig | None = None) -> str:
    config = markdown_config or MarkdownConfig()
    offset = config.heading_offset
    body = _shift_body_headings(article.content_markdown.strip(), offset)

    lines: list[str] = []
    if config.front_matter != "none":
        lines.extend(
            [
                "---",
                f"title: {_quote(article.title)}",
                f"author: {_quote(article.author)}",
                f"platform: {_quote(article.platform)}",
                f"source_url: {_quote(article.source_url)}",
                f"published_at: {_quote(article.published_at)}",
                "---",
                "",
            ]
        )

    lines.extend([_heading(1, article.title, offset), ""])
    if config.include_source_block and config.template != "clean":
        lines.extend(
            [
                f"> Source: {article.platform}",
                f"> Author: {article.author}" if article.author else "> Author:",
                f"> Original: {article.source_url}",
                "",
                "---",
                "",
            ]
        )

    lines.extend([body, ""])
    return "\n".join(lines)
