from __future__ import annotations

import re

from magicmd.config import MarkdownConfig
from magicmd.models import Article
from magicmd.template_vars import build_article_template_vars, format_template


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
    variables = build_article_template_vars(article)
    offset = config.heading_offset
    body = _shift_body_headings(article.content_markdown.strip(), offset)

    lines: list[str] = []
    if config.front_matter != "none":
        lines.append("---")
        for key, value_template in config.front_matter_fields.items():
            value = format_template(value_template, variables)
            lines.append(f"{key}: {_quote(value)}")
        lines.extend(["---", ""])

    if config.include_title:
        lines.extend([_heading(1, article.title, offset), ""])
    if config.include_source_block and config.template != "clean":
        source_block = format_template(config.source_block_template, variables).strip()
        if source_block:
            lines.extend([source_block, "", "---", ""])

    lines.extend([body, ""])
    return "\n".join(lines)
