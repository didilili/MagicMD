from __future__ import annotations

from pagemd.models import Article


def _quote(value: str) -> str:
    return '"' + value.replace('"', '\\"') + '"'


def render_markdown(article: Article) -> str:
    lines = [
        "---",
        f"title: {_quote(article.title)}",
        f"author: {_quote(article.author)}",
        f"platform: {_quote(article.platform)}",
        f"source_url: {_quote(article.source_url)}",
        f"published_at: {_quote(article.published_at)}",
        "---",
        "",
        f"# {article.title}",
        "",
    ]
    lines.extend(
        [
            f"> Source: {article.platform}",
            f"> Author: {article.author}" if article.author else "> Author:",
            f"> Original: {article.source_url}",
            "",
            "---",
            "",
            article.content_markdown.strip(),
            "",
        ]
    )
    return "\n".join(lines)

