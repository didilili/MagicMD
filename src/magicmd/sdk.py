from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, Field

from magicmd.config import MagicMDConfig, load_config
from magicmd.detect import detect_platform
from magicmd.diagnostics import save_debug_html, save_extraction_report
from magicmd.exceptions import (
    ConversionError,
    FetchError,
    MediaDownloadError,
    ParseError,
    UnsupportedPlatformError,
)
from magicmd.fetchers.browser import fetch_browser
from magicmd.fetchers.http import fetch_http
from magicmd.i18n import ui_text
from magicmd.models import Article
from magicmd.output import ensure_content_hash, write_article_files, write_article_package
from magicmd.platforms.registry import get_platform_adapter, platform_names
from magicmd.renderers.markdown import render_markdown
from magicmd.template_vars import build_article_template_vars, format_template


class ConvertedImage(BaseModel):
    source_url: str
    local_path: str = Field(
        default="",
        description="Filesystem path to the downloaded image, empty when no local file is available.",
    )
    markdown_path: str = Field(
        default="",
        description="Path currently referenced by the generated Markdown.",
    )
    alt: str = ""


class ArticleConversionResult(BaseModel):
    title: str
    author: str = ""
    platform: str
    source_url: str
    canonical_url: str = ""
    published_at: str = ""
    excerpt: str = ""
    markdown: str
    content_hash: str
    images: list[ConvertedImage] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    report: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    package_dir: str | None = None


ProgressRunner = Callable[[int, int, str, Callable[[], Any]], Any]
FetchFunc = Callable[[str, str, Optional[Path]], str]
ParseFunc = Callable[[str, str, str], Article]


def fetch_for_platform(url: str, platform: str, config_path: Optional[Path] = None) -> str:
    config = load_config(config_path)
    platform_config = config.platforms.get(platform)
    if platform_config and platform_config.browser == "camoufox":
        return fetch_browser(
            url,
            wait_selector=platform_config.wait_selector,
            timeout_ms=config.fetch.browser_timeout_seconds * 1000,
            attempts=config.fetch.browser_attempts,
        )
    return fetch_http(url, timeout_seconds=config.fetch.timeout_seconds, user_agent=config.fetch.user_agent)


def parse_article(platform: str, html: str, url: str) -> Article:
    try:
        adapter = get_platform_adapter(platform)
    except KeyError as exc:
        supported = ", ".join(platform_names())
        raise UnsupportedPlatformError(
            f"Unsupported platform: {platform}. Supported platforms: {supported}",
            stage="detect",
        ) from exc
    return adapter.parser(html, url)


def convert_article(
    url: str,
    platform: str = "auto",
    output_dir: str | Path | None = None,
    download_images: bool = True,
    config_path: str | Path | None = None,
    *,
    _fetch_for_platform: FetchFunc | None = None,
    _parse_article: ParseFunc | None = None,
    _progress: ProgressRunner | None = None,
    _debug: bool = False,
    _overwrite: bool = False,
) -> ArticleConversionResult:
    """Convert a public article URL into Markdown and optional package files.

    The keyword-only underscored parameters are internal hooks used by the CLI
    tests and command wrapper. Public callers should use the documented
    arguments above.
    """

    config_path_obj = Path(config_path) if config_path is not None else None
    config = _load_config(config_path_obj)
    fetcher = _fetch_for_platform or fetch_for_platform
    parser = _parse_article or parse_article
    language = config.ui.language

    resolved_platform = _run_stage(
        _progress,
        "detect",
        1,
        6,
        ui_text(language, "detecting_platform"),
        lambda: detect_platform(url) if platform == "auto" else platform,
        ConversionError,
    )
    _ensure_platform_supported(resolved_platform)
    _ensure_platform_enabled(resolved_platform, config)

    html = _run_stage(
        _progress,
        "fetch",
        2,
        6,
        ui_text(language, "fetching_article", platform=resolved_platform),
        lambda: fetcher(url, resolved_platform, config_path_obj),
        FetchError,
    )
    article = _run_stage(
        _progress,
        "parse",
        3,
        6,
        ui_text(language, "parsing_article"),
        lambda: parser(resolved_platform, html, url),
        ParseError,
    )

    package_dir: Path | None = None
    if output_dir is not None:
        package_dir = _run_stage(
            _progress,
            "write",
            4,
            6,
            ui_text(language, "writing_package"),
            lambda: write_article_package(
                article,
                output_dir,
                overwrite=_overwrite or config.output.overwrite,
                markdown_config=config.markdown,
                output_config=config.output,
            ),
            ConversionError,
        )
        if _should_save_debug_html(_debug, config.output.save_debug_html, article.extraction.warnings):
            save_debug_html(package_dir, html)
    else:
        article = ensure_content_hash(article)
        _run_stage(
            _progress,
            "write",
            4,
            6,
            ui_text(language, "rendering_markdown"),
            lambda: None,
            ConversionError,
        )

    if package_dir is not None and download_images and (config.images.download or config.videos.download):
        article = _run_stage(
            _progress,
            "media",
            5,
            6,
            ui_text(language, "downloading_media"),
            lambda: download_configured_media(article, package_dir, config),
            MediaDownloadError,
        )
        _run_stage(
            None,
            "write",
            4,
            6,
            ui_text(language, "writing_package"),
            lambda: write_article_files(
                article,
                package_dir,
                markdown_config=config.markdown,
                output_config=config.output,
            ),
            ConversionError,
        )
    else:
        _run_stage(
            _progress,
            "media",
            5,
            6,
            ui_text(language, "skipping_media"),
            lambda: article,
            MediaDownloadError,
        )

    article = ensure_content_hash(article)
    metadata = article.to_metadata()
    report = metadata["extraction"]
    if package_dir is not None:
        _run_stage(
            _progress,
            "report",
            6,
            6,
            ui_text(language, "saving_report"),
            lambda: save_extraction_report(
                package_dir,
                report,
                format_template(config.output.naming.report, build_article_template_vars(article)),
            ),
            ConversionError,
        )
    else:
        _run_stage(
            _progress,
            "report",
            6,
            6,
            ui_text(language, "preparing_report"),
            lambda: None,
            ConversionError,
        )

    try:
        markdown = render_markdown(article, markdown_config=config.markdown)
    except Exception as exc:
        raise ConversionError(str(exc), stage="write") from exc

    return _build_result(article, markdown, metadata, report, package_dir, config)


def download_configured_media(article: Article, package_dir: Path, config: MagicMDConfig) -> Article:
    from magicmd.assets import download_images, download_videos

    next_article = article
    if config.images.download:
        next_article = download_images(
            next_article,
            package_dir,
            config.images.directory,
            config.images.filename_pattern,
            config.images.markdown_path,
        )
    if config.videos.download:
        next_article = download_videos(
            next_article,
            package_dir,
            config.videos.directory,
            config.videos.filename_pattern,
            config.videos.markdown_path,
        )
    return next_article


def _build_result(
    article: Article,
    markdown: str,
    metadata: dict[str, Any],
    report: dict[str, Any],
    package_dir: Path | None,
    config: MagicMDConfig,
) -> ArticleConversionResult:
    return ArticleConversionResult(
        title=article.title,
        author=article.author,
        platform=article.platform,
        source_url=article.source_url,
        canonical_url=article.canonical_url or article.source_url,
        published_at=article.published_at,
        excerpt=article.excerpt,
        markdown=markdown,
        content_hash=article.content_hash,
        images=[
            ConvertedImage(
                source_url=image.source_url,
                local_path=_resolve_image_local_path(image.local_path, package_dir, config),
                markdown_path=image.local_path,
                alt=image.alt,
            )
            for image in article.images
        ],
        warnings=list(article.extraction.warnings),
        report=report,
        metadata=metadata,
        package_dir=str(package_dir) if package_dir is not None else None,
    )


def _resolve_image_local_path(
    markdown_path: str,
    package_dir: Path | None,
    config: MagicMDConfig,
) -> str:
    if not markdown_path or package_dir is None:
        return ""

    direct_path = package_dir / markdown_path
    if direct_path.exists():
        return str(direct_path)

    filename = Path(markdown_path).name
    if filename:
        configured_path = package_dir / config.images.directory / filename
        if configured_path.exists():
            return str(configured_path)

    return ""


def _load_config(config_path: Path | None) -> MagicMDConfig:
    try:
        return load_config(config_path)
    except Exception as exc:
        raise ConversionError(str(exc), stage="config") from exc


def _ensure_platform_supported(platform: str) -> None:
    try:
        get_platform_adapter(platform)
    except KeyError as exc:
        supported = ", ".join(platform_names())
        raise UnsupportedPlatformError(
            f"Unsupported platform: {platform}. Supported platforms: {supported}",
            stage="detect",
        ) from exc


def _ensure_platform_enabled(platform: str, config: MagicMDConfig) -> None:
    platform_config = config.platforms.get(platform)
    if platform_config and not platform_config.enabled:
        raise UnsupportedPlatformError(f"Platform disabled: {platform}", stage="detect")


def _run_stage(
    progress: ProgressRunner | None,
    stage: str,
    index: int,
    total: int,
    message: str,
    operation: Callable[[], Any],
    error_type: type[Exception],
) -> Any:
    try:
        if progress is None:
            return operation()
        return progress(index, total, message, operation)
    except (UnsupportedPlatformError, FetchError, ParseError, MediaDownloadError, ConversionError):
        raise
    except Exception as exc:
        raise error_type(str(exc), stage=stage) from exc


def _should_save_debug_html(debug: bool, save_mode: str, warnings: list[str]) -> bool:
    normalized = save_mode.lower()
    return debug or normalized == "always" or (normalized == "on_failure" and bool(warnings))
