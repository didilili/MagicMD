from __future__ import annotations

import shutil
from collections.abc import Iterable
import json
import re
from hashlib import sha256
from pathlib import Path

from magicmd.config import DocxConfig, MarkdownConfig, OutputConfig
from magicmd.models import Article
from magicmd.renderers.docx import write_docx_from_markdown
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
    docx_config: DocxConfig | None = None,
    generated_directories: Iterable[str] | None = None,
) -> Path:
    article = ensure_content_hash(article)
    config = output_config or OutputConfig()
    base = Path(output_dir)
    variables = build_article_template_vars(article)
    package_dir = base / format_template(config.naming.package, variables)
    if package_dir.exists():
        if not overwrite:
            package_dir = package_dir.with_name(f"{package_dir.name}-{article.content_hash[:6]}")
        else:
            _clear_existing_package(
                package_dir,
                base,
                config,
                variables,
                generated_directories or ("images", "videos"),
            )
    package_dir.mkdir(parents=True, exist_ok=overwrite)
    write_article_files(
        article,
        package_dir,
        markdown_config=markdown_config,
        output_config=output_config,
        docx_config=docx_config,
    )
    return package_dir


def _clear_existing_package(
    package_dir: Path,
    base: Path,
    config: OutputConfig,
    variables: dict[str, str],
    generated_directories: Iterable[str],
) -> None:
    package_path = package_dir.resolve()
    base_path = base.resolve()
    if package_path != base_path and package_path.is_relative_to(base_path):
        shutil.rmtree(package_dir)
        return

    generated_files = [
        format_template(config.naming.markdown, variables),
        format_template(config.naming.metadata, variables),
        format_template(config.naming.report, variables),
        format_template(config.naming.docx, variables),
        "debug.html",
    ]
    for filename in generated_files:
        target = package_dir / filename
        if _is_inside(target, package_dir) and target.is_file():
            target.unlink()

    for directory in generated_directories:
        target = package_dir / directory
        if _is_inside(target, package_dir) and target.is_dir():
            shutil.rmtree(target)


def _is_inside(path: Path, directory: Path) -> bool:
    return path.resolve().is_relative_to(directory.resolve())


def write_article_files(
    article: Article,
    package_dir: str | Path,
    markdown_config: MarkdownConfig | None = None,
    output_config: OutputConfig | None = None,
    docx_config: DocxConfig | None = None,
) -> None:
    package_path = Path(package_dir)
    package_path.mkdir(parents=True, exist_ok=True)
    article = ensure_content_hash(article)
    config = output_config or OutputConfig()
    variables = build_article_template_vars(article)
    markdown_path = package_path / format_template(config.naming.markdown, variables)
    markdown_path.write_text(
        render_markdown(article, markdown_config=markdown_config),
        encoding="utf-8",
    )
    (package_path / format_template(config.naming.metadata, variables)).write_text(
        json.dumps(article.to_metadata(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if docx_config and docx_config.enabled:
        docx_path = package_path / format_template(config.naming.docx, variables)
        write_docx_from_markdown(markdown_path, docx_path, docx_config)
