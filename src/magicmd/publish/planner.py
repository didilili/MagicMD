from __future__ import annotations

import re

from magicmd.publish.errors import PublishPlanError
from magicmd.sdk import ArticleConversionResult
from magicmd.template_vars import format_template


def slugify_publish_title(title: str) -> str:
    slug = re.sub(r"[^\w\u4e00-\u9fff]+", "-", title.lower(), flags=re.UNICODE).strip("-")
    return slug[:80] or "article"


def build_publish_template_vars(result: ArticleConversionResult) -> dict[str, str]:
    date = result.published_at[:10] if result.published_at else "undated"
    content_hash = result.content_hash or ""
    return {
        "title": result.title,
        "slug": slugify_publish_title(result.title),
        "date": date,
        "published_at": result.published_at,
        "author": result.author,
        "platform": result.platform,
        "source_url": result.source_url,
        "canonical_url": result.canonical_url or result.source_url,
        "content_hash": content_hash,
        "short_hash": content_hash[:6],
    }


def sanitize_branch_name(branch: str) -> str:
    sanitized = re.sub(r"\s+", "-", branch.strip())
    sanitized = re.sub(r"[~^:?*\[\]\\]+", "-", sanitized)
    sanitized = sanitized.replace("..", "-").replace("@{", "-")
    sanitized = sanitized.strip("/.")
    if not sanitized:
        raise PublishPlanError("Branch template produced an empty branch name")
    return sanitized


def render_publish_template(template: str, result: ArticleConversionResult) -> str:
    return format_template(template, build_publish_template_vars(result))
