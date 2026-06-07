from __future__ import annotations

import re
from collections.abc import Mapping

from magicmd.models import Article


class SafeTemplateVars(dict[str, object]):
    def __missing__(self, key: str) -> str:
        raise KeyError(key)


def _slugify_title(title: str) -> str:
    slug = re.sub(r"[^\w\u4e00-\u9fff]+", "-", title.lower(), flags=re.UNICODE).strip("-")
    return slug[:80] or "article"


def build_article_template_vars(article: Article) -> dict[str, str]:
    date = article.published_at[:10] if article.published_at else "undated"
    content_hash = article.content_hash or ""
    return {
        "title": article.title,
        "slug": _slugify_title(article.title),
        "date": date,
        "published_at": article.published_at,
        "author": article.author,
        "platform": article.platform,
        "source_url": article.source_url,
        "canonical_url": article.canonical_url or article.source_url,
        "content_hash": content_hash,
        "short_hash": content_hash[:6],
    }


def format_template(template: str, variables: Mapping[str, object]) -> str:
    try:
        return template.format_map(SafeTemplateVars(variables))
    except KeyError as exc:
        raise ValueError(f"Unknown template field: {exc.args[0]}") from exc
