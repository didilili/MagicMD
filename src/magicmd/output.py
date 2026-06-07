from __future__ import annotations

import json
import re
from hashlib import sha256
from pathlib import Path

from magicmd.config import MarkdownConfig, OutputConfig
from magicmd.models import Article
from magicmd.renderers.markdown import render_markdown
from magicmd.template_vars import build_article_template_vars, format_template


def slugify_title(title: str) -> str:
    slug = re.sub(r"[^\w\u4e00-\u9fff]+", "-", title.lower(), flags=re.UNICODE).strip("-")
    return slug[:80] or "article"


def ensure_content_hash(article: Article) -> Article:
    if article.content_hash:
        return article
    digest = sha256(article.content_markdown.encode("utf-8")).hexdigest()
    return article.model_copy(update={"content_hash": digest})


def write_article_package(
    article: Article,
    output_dir: str | Path,
    overwrite: bool = False,
    markdown_config: MarkdownConfig | None = None,
    output_config: OutputConfig | None = None,
) -> Path:
    article = ensure_content_hash(article)
    config = output_config or OutputConfig()
    base = Path(output_dir)
    variables = build_article_template_vars(article)
    package_dir = base / format_template(config.naming.package, variables)
    if package_dir.exists() and not overwrite:
        package_dir = package_dir.with_name(f"{package_dir.name}-{article.content_hash[:6]}")
    package_dir.mkdir(parents=True, exist_ok=overwrite)
    write_article_files(
        article,
        package_dir,
        markdown_config=markdown_config,
        output_config=output_config,
    )
    return package_dir


def write_article_files(
    article: Article,
    package_dir: str | Path,
    markdown_config: MarkdownConfig | None = None,
    output_config: OutputConfig | None = None,
) -> None:
    package_path = Path(package_dir)
    package_path.mkdir(parents=True, exist_ok=True)
    article = ensure_content_hash(article)
    config = output_config or OutputConfig()
    variables = build_article_template_vars(article)
    (package_path / format_template(config.naming.markdown, variables)).write_text(
        render_markdown(article, markdown_config=markdown_config),
        encoding="utf-8",
    )
    (package_path / format_template(config.naming.metadata, variables)).write_text(
        json.dumps(article.to_metadata(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
